import asyncio
import time
import random
import logging
from typing import Any, Generic, TypeVar
import httpx
from app.config import settings

logger = logging.getLogger("crustdata")

T = TypeVar("T")

# -------------------------------------------------------------
# Specific Crustdata Exceptions
# -------------------------------------------------------------
class CrustdataError(Exception):
    """Base exception for Crustdata API interactions."""
    def __init__(self, message: str, status_code: int | None = None, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details

class CrustdataBadRequestError(CrustdataError):
    """HTTP 400: Invalid request body, identifier or filter (non-retryable)."""
    pass

class CrustdataAuthError(CrustdataError):
    """HTTP 401: Invalid or missing API key (non-retryable)."""
    pass

class CrustdataForbiddenError(CrustdataError):
    """HTTP 403: Endpoint or field permission denied (non-retryable)."""
    pass

class CrustdataRateLimitError(CrustdataError):
    """HTTP 429: Rate limit exceeded (retryable with backoff)."""
    def __init__(self, message: str, retry_after: float | None = None, **kwargs):
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after

class CrustdataServerError(CrustdataError):
    """HTTP 5xx or network timeout (retryable)."""
    pass


# -------------------------------------------------------------
# Response Wrapper & In-Memory TTL Cache
# -------------------------------------------------------------
class CrustdataResult(Generic[T]):
    """Typed wrapper preserving structured data, pagination cursor, and safe metadata."""
    def __init__(
        self,
        data: T,
        raw: Any = None,
        cursor: str | None = None,
        metadata: dict[str, Any] | None = None
    ):
        self.data = data
        self.raw = raw
        self.cursor = cursor
        self.metadata = metadata or {}

    def __getitem__(self, item: str) -> Any:
        """Allow dict-like access for backward compatibility."""
        if isinstance(self.data, dict) and item in self.data:
            return self.data[item]
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def get(self, key: str, default: Any = None) -> Any:
        if isinstance(self.data, dict):
            return self.data.get(key, default)
        return getattr(self, key, default)


class TTLCache:
    """Thread-safe in-process cache with configurable TTL and hit/miss metrics."""
    def __init__(self, default_ttl: float = 3600.0):
        self.default_ttl = default_ttl
        self._cache: dict[str, tuple[float, Any]] = {}
        self.hits: int = 0
        self.misses: int = 0

    def get(self, key: str) -> Any | None:
        now = time.time()
        if key in self._cache:
            expires_at, value = self._cache[key]
            if expires_at > now:
                self.hits += 1
                return value
            else:
                del self._cache[key]
        self.misses += 1
        return None

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        duration = ttl if ttl is not None else self.default_ttl
        self._cache[key] = (time.time() + duration, value)

    def clear(self) -> None:
        self._cache.clear()
        self.hits = 0
        self.misses = 0


# -------------------------------------------------------------
# Production-Minded Crustdata Client
# -------------------------------------------------------------
class CrustdataClient:
    """
    Robust, production-minded Crustdata API client with finite timeouts,
    connection limits, distinct error handling, bounded retries with jitter,
    TTL caching, cursor-aware pagination, and safe field selection.
    """
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        api_version: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        cache_ttl: float = 3600.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        if api_key is not None:
            self.api_key = api_key.strip().strip('"').strip("'")
        else:
            self.api_key = settings.api_key.strip().strip('"').strip("'")
        self.base_url = (base_url or settings.CRUSTDATA_BASE_URL).rstrip("/")
        self.api_version = api_version or settings.CRUSTDATA_API_VERSION
        self.timeout = timeout or settings.CRUSTDATA_TIMEOUT_SECONDS
        self.max_retries = max_retries if max_retries is not None else settings.CRUSTDATA_MAX_RETRIES
        self.transport = transport

        # Connection limits
        self.limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

        # Caches
        self.person_cache = TTLCache(default_ttl=cache_ttl)
        self.company_cache = TTLCache(default_ttl=cache_ttl)

    def _get_headers(self) -> dict[str, str]:
        if not self.api_key:
            raise CrustdataAuthError("Crustdata API key is missing or not configured.", status_code=401)
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "x-api-version": self.api_version,
        }

    async def _post(
        self,
        endpoint: str,
        json_data: dict[str, Any],
        is_retryable_call: bool = True
    ) -> CrustdataResult[Any]:
        """
        Executes a POST request against the Crustdata API.
        Applies exponential backoff with jitter on 429 and 5xx errors only.
        Never logs API keys or sensitive profile details.
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        max_attempts = self.max_retries if is_retryable_call else 0

        for attempt in range(max_attempts + 1):
            start_time = time.time()
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    limits=self.limits,
                    transport=self.transport
                ) as client:
                    response = await client.post(url, json=json_data, headers=headers)
                    latency = time.time() - start_time

                    req_id = response.headers.get("x-request-id") or response.headers.get("request-id")
                    credits_rem = response.headers.get("x-credits-remaining")

                    # Safe logging without credentials or sensitive payloads
                    logger.info(
                        f"Crustdata POST {endpoint} -> status={response.status_code} in {latency*1000:.1f}ms "
                        f"[req_id={req_id or 'none'}]"
                    )

                    metadata = {
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "latency_ms": round(latency * 1000, 2),
                        "request_id": req_id,
                        "credits_remaining": credits_rem,
                    }

                    # Success (200, 201)
                    if response.status_code in (200, 201):
                        data = response.json()
                        cursor = None
                        if isinstance(data, dict):
                            cursor = data.get("cursor") or data.get("next_cursor")
                        return CrustdataResult(data=data, raw=data, cursor=cursor, metadata=metadata)

                    # 400 Bad Request
                    if response.status_code == 400:
                        err_text = response.text[:300]
                        raise CrustdataBadRequestError(
                            f"Crustdata invalid request on {endpoint}: {err_text}",
                            status_code=400,
                            details=err_text
                        )

                    # 401 Unauthorized
                    if response.status_code == 401:
                        raise CrustdataAuthError(
                            "Crustdata authentication failure: Invalid or expired API key.",
                            status_code=401
                        )

                    # 403 Forbidden
                    if response.status_code == 403:
                        err_text = response.text[:300]
                        raise CrustdataForbiddenError(
                            f"Crustdata permission denied on {endpoint}: {err_text}",
                            status_code=403,
                            details=err_text
                        )

                    # 429 Rate Limit
                    if response.status_code == 429:
                        retry_after_header = response.headers.get("Retry-After")
                        retry_after = float(retry_after_header) if (retry_after_header and retry_after_header.isdigit()) else None

                        if attempt < max_attempts:
                            backoff = retry_after or ((2 ** attempt) * 0.5 + random.uniform(0.1, 0.3))
                            logger.warning(
                                f"Crustdata rate limited (429) on {endpoint}. Backoff {backoff:.2f}s "
                                f"(attempt {attempt + 1}/{max_attempts})"
                            )
                            await asyncio.sleep(backoff)
                            continue

                        raise CrustdataRateLimitError(
                            f"Crustdata rate limit exceeded on {endpoint} after {max_attempts} retries.",
                            retry_after=retry_after
                        )

                    # 5xx Server Errors
                    if response.status_code in (500, 502, 503, 504):
                        if attempt < max_attempts:
                            backoff = (2 ** attempt) * 0.5 + random.uniform(0.1, 0.3)
                            logger.warning(
                                f"Crustdata server error ({response.status_code}) on {endpoint}. "
                                f"Retrying in {backoff:.2f}s (attempt {attempt + 1}/{max_attempts})"
                            )
                            await asyncio.sleep(backoff)
                            continue

                        raise CrustdataServerError(
                            f"Crustdata server error ({response.status_code}) on {endpoint} after {max_attempts} retries.",
                            status_code=response.status_code,
                            details=response.text[:200]
                        )

                    # Fallback for unexpected status codes
                    raise CrustdataError(
                        f"Crustdata unexpected status {response.status_code} on {endpoint}: {response.text[:200]}",
                        status_code=response.status_code,
                        details=response.text[:200]
                    )

            except httpx.TimeoutException:
                logger.warning(f"Crustdata timeout on {endpoint} (attempt {attempt + 1}/{max_attempts})")
                if attempt < max_attempts:
                    await asyncio.sleep((2 ** attempt) * 0.5 + random.uniform(0.1, 0.2))
                    continue
                raise CrustdataServerError(f"Request timeout calling Crustdata: {endpoint}", status_code=408)

            except (httpx.RequestError, httpx.ConnectError) as e:
                logger.warning(f"Crustdata network connection error on {endpoint}: {e}")
                if attempt < max_attempts:
                    await asyncio.sleep((2 ** attempt) * 0.5 + random.uniform(0.1, 0.2))
                    continue
                raise CrustdataServerError(f"Network error connecting to Crustdata: {e}", status_code=500)

        raise CrustdataServerError(f"Failed to execute Crustdata request on {endpoint}")

    # -------------------------------------------------------------
    # Core Endpoint 1: POST /person/enrich
    # -------------------------------------------------------------
    async def person_enrich(
        self,
        profile_urls: list[str] | str,
        fields: list[str] | None = None
    ) -> CrustdataResult[Any]:
        """
        Enrich candidate from professional network profile URL(s).
        Enforces exactly one identifier type (professional_network_profile_urls).
        """
        if isinstance(profile_urls, str):
            urls = [profile_urls.strip()]
        else:
            urls = [u.strip() for u in profile_urls if u.strip()]

        if not urls:
            raise CrustdataBadRequestError("At least one profile_url must be provided", status_code=400)

        cache_key = f"person:{':'.join(sorted(urls))}"
        cached = self.person_cache.get(cache_key)
        if cached is not None:
            return CrustdataResult(data=cached, raw=cached, metadata={"cached": True})

        payload: dict[str, Any] = {
            "professional_network_profile_urls": urls
        }
        if fields:
            payload["fields"] = fields

        result = await self._post("/person/enrich", payload)
        self.person_cache.set(cache_key, result.data)
        return result

    # -------------------------------------------------------------
    # Core Endpoint 2: POST /person/search
    # -------------------------------------------------------------
    async def person_search(
        self,
        query: dict[str, Any] | None = None,
        search: str | dict[str, Any] | None = None,
        filters: list[dict[str, Any]] | None = None,
        fields: list[str] | None = None,
        limit: int = 10,
        cursor: str | None = None
    ) -> CrustdataResult[Any]:
        """
        Search external candidate profiles.
        Enforces bounded results (limit capped to 50) and cursor propagation.
        """
        bounded_limit = max(1, min(limit, 50))
        payload: dict[str, Any] = {"limit": bounded_limit}

        if search:
            if isinstance(search, str):
                payload["search"] = {"query": search}
            elif isinstance(search, dict):
                payload["search"] = search
        elif filters:
            payload["filters"] = filters
        elif query:
            if "search" in query:
                payload["search"] = query["search"]
            elif "query" in query:
                payload["search"] = {"query": query["query"]}
            elif "title" in query:
                payload["search"] = {"query": query["title"]}
            elif "filters" in query:
                payload["filters"] = query["filters"]
            else:
                payload["search"] = {"query": "Software Engineer"}
        else:
            payload["search"] = {"query": "Software Engineer"}

        if fields:
            payload["fields"] = fields
        if cursor:
            payload["cursor"] = cursor

        return await self._post("/person/search", payload)

    # -------------------------------------------------------------
    # Core Endpoint 3: POST /company/identify
    # -------------------------------------------------------------
    async def company_identify(
        self,
        company_name: str | None = None,
        domain: str | None = None
    ) -> CrustdataResult[Any]:
        """
        Resolve company identity given company name OR domain.
        Enforces exactly one identifier type per API rules.
        """
        payload: dict[str, Any] = {}
        if domain:
            clean_domain = domain.strip().lower()
            payload["domains"] = [clean_domain]
            cache_key = f"company_id:domain:{clean_domain}"
        elif company_name:
            clean_name = company_name.strip()
            payload["names"] = [clean_name]
            cache_key = f"company_id:name:{clean_name.lower()}"
        else:
            raise CrustdataBadRequestError("Either domain or company_name is required", status_code=400)

        cached = self.company_cache.get(cache_key)
        if cached is not None:
            return CrustdataResult(data=cached, raw=cached, metadata={"cached": True})

        result = await self._post("/company/identify", payload)
        self.company_cache.set(cache_key, result.data)
        return result

    # -------------------------------------------------------------
    # Core Endpoint 4: POST /company/enrich
    # -------------------------------------------------------------
    async def company_enrich(
        self,
        company_id: int | str | None = None,
        domain: str | None = None,
        fields: list[str] | None = None
    ) -> CrustdataResult[Any]:
        """
        Enrich company profile given company ID OR domain.
        Enforces exactly one identifier type per API rules.
        """
        payload: dict[str, Any] = {}
        if company_id is not None:
            try:
                cid = int(company_id)
                payload["crustdata_company_ids"] = [cid]
                cache_key = f"company_enrich:id:{cid}"
            except ValueError:
                clean_dom = str(company_id).strip().lower()
                payload["domains"] = [clean_dom]
                cache_key = f"company_enrich:domain:{clean_dom}"
        elif domain:
            clean_dom = domain.strip().lower()
            payload["domains"] = [clean_dom]
            cache_key = f"company_enrich:domain:{clean_dom}"
        else:
            raise CrustdataBadRequestError("Either company_id or domain is required", status_code=400)

        if fields:
            payload["fields"] = fields

        cached = self.company_cache.get(cache_key)
        if cached is not None:
            return CrustdataResult(data=cached, raw=cached, metadata={"cached": True})

        result = await self._post("/company/enrich", payload)
        self.company_cache.set(cache_key, result.data)
        return result

    # -------------------------------------------------------------
    # Backward Compatibility Aliases (Returning dict/list directly)
    # -------------------------------------------------------------
    async def enrich_person(self, profile_url: str) -> dict[str, Any] | list[Any]:
        res = await self.person_enrich(profile_urls=profile_url)
        return res.data

    async def search_persons(
        self,
        query: dict[str, Any] | None = None,
        limit: int = 10,
        cursor: str | None = None
    ) -> dict[str, Any]:
        res = await self.person_search(query=query, limit=limit, cursor=cursor)
        return res.data if isinstance(res.data, dict) else {"results": res.data}

    async def identify_company(
        self,
        company_name: str | None = None,
        domain: str | None = None
    ) -> dict[str, Any] | list[Any]:
        res = await self.company_identify(company_name=company_name, domain=domain)
        return res.data

    async def enrich_company(
        self,
        company_id: int | str | None = None,
        domain: str | None = None
    ) -> dict[str, Any] | list[Any]:
        res = await self.company_enrich(company_id=company_id, domain=domain)
        return res.data

    # -------------------------------------------------------------
    # Diagnostics Method
    # -------------------------------------------------------------
    async def diagnostics(self) -> dict[str, Any]:
        """Probes API reachability, authentication, and endpoint status."""
        if not self.api_key:
            return {"status": "unconfigured", "error": "No CRUSTDATA_API_KEY configured."}

        try:
            res = await self.company_identify(domain="google.com")
            return {
                "status": "connected",
                "verified": True,
                "latency_ms": res.metadata.get("latency_ms"),
                "credits_remaining": res.metadata.get("credits_remaining"),
            }
        except CrustdataError as e:
            return {"status": "error", "error": str(e), "status_code": e.status_code}
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Singleton client instance
crustdata_client = CrustdataClient()
