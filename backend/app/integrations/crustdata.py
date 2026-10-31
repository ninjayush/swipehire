import asyncio
import time
import logging
from typing import Any
import httpx
from app.config import settings

logger = logging.getLogger("crustdata")

class CrustdataError(Exception):
    """Custom exception for Crustdata API interactions."""
    def __init__(self, message: str, status_code: int | None = None, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details

class CrustdataClient:
    """
    Robust, typed client for Crustdata API with retries, caching,
    timeout management, and sanitized error reporting.
    """
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        api_version: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ):
        self.api_key = api_key or settings.api_key
        self.base_url = (base_url or settings.CRUSTDATA_BASE_URL).rstrip("/")
        self.api_version = api_version or settings.CRUSTDATA_API_VERSION
        self.timeout = timeout or settings.CRUSTDATA_TIMEOUT_SECONDS
        self.max_retries = max_retries or settings.CRUSTDATA_MAX_RETRIES

        # In-memory prototype cache: key -> data
        self._person_cache: dict[str, dict[str, Any]] = {}
        self._company_cache: dict[str, dict[str, Any]] = {}

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "x-api-version": self.api_version,
        }

    async def _post(self, endpoint: str, json_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a POST request with exponential backoff on retryable errors."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        last_error = None

        for attempt in range(self.max_retries + 1):
            start_time = time.time()
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=json_data, headers=headers)
                    latency = time.time() - start_time
                    logger.info(f"Crustdata POST {endpoint} returned status {response.status_code} in {latency:.2f}s")

                    # Handle successful response
                    if response.status_code in (200, 201):
                        data = response.json()
                        return data if isinstance(data, dict) else {"data": data}

                    # Handle 401 / 403 Authentication / Authorization
                    if response.status_code in (401, 403):
                        logger.error(f"Crustdata authentication failure: {response.status_code}")
                        raise CrustdataError(
                            "Crustdata authentication failed. Please verify CRUSTDATA_API_KEY.",
                            status_code=response.status_code
                        )

                    # Handle Rate Limits (429) & Server Errors (500, 502, 503, 504)
                    if response.status_code in (429, 500, 502, 503, 504):
                        if attempt < self.max_retries:
                            backoff = (2 ** attempt) * 0.5
                            logger.warning(
                                f"Crustdata {response.status_code} on {endpoint}. Retrying in {backoff}s (attempt {attempt+1}/{self.max_retries})."
                            )
                            await asyncio.sleep(backoff)
                            continue
                        raise CrustdataError(
                            f"Crustdata request failed with status {response.status_code} after {self.max_retries} retries.",
                            status_code=response.status_code,
                            details=response.text[:200]
                        )

                    # Other client errors (400, 404, etc.)
                    raise CrustdataError(
                        f"Crustdata error {response.status_code}: {response.text[:200]}",
                        status_code=response.status_code,
                        details=response.text[:200]
                    )

            except httpx.TimeoutException as e:
                logger.warning(f"Crustdata request timeout on {endpoint} (attempt {attempt+1}/{self.max_retries})")
                last_error = CrustdataError(f"Request timeout while calling Crustdata: {endpoint}", status_code=408)
                if attempt < self.max_retries:
                    await asyncio.sleep((2 ** attempt) * 0.5)
                    continue
                raise last_error
            except httpx.RequestError as e:
                logger.error(f"Crustdata network request error on {endpoint}: {str(e)}")
                last_error = CrustdataError(f"Network error communicating with Crustdata: {str(e)}", status_code=500)
                if attempt < self.max_retries:
                    await asyncio.sleep((2 ** attempt) * 0.5)
                    continue
                raise last_error

        raise last_error or CrustdataError("Unknown Crustdata error occurred.")

    # -------------------------------------------------------------
    # 1. POST /person/enrich
    # -------------------------------------------------------------
    async def enrich_person(self, profile_url: str) -> dict[str, Any]:
        """Enrich a candidate from their professional network profile URL."""
        profile_url = profile_url.strip()
        if not profile_url:
            raise CrustdataError("profile_url must not be empty", status_code=400)

        # Cache check
        if profile_url in self._person_cache:
            return self._person_cache[profile_url]

        payload = {"profile_url": profile_url}
        result = await self._post("/person/enrich", payload)
        self._person_cache[profile_url] = result
        return result

    # -------------------------------------------------------------
    # 2. POST /person/search
    # -------------------------------------------------------------
    async def search_persons(
        self,
        query: dict[str, Any] | None = None,
        limit: int = 10,
        cursor: str | None = None
    ) -> dict[str, Any]:
        """Search for external candidate profiles matching query criteria."""
        payload: dict[str, Any] = {
            "limit": limit,
            **(query or {})
        }
        if cursor:
            payload["cursor"] = cursor

        return await self._post("/person/search", payload)

    # -------------------------------------------------------------
    # 3. POST /company/identify
    # -------------------------------------------------------------
    async def identify_company(
        self,
        company_name: str | None = None,
        domain: str | None = None
    ) -> dict[str, Any]:
        """Resolve a company name or domain to canonical identity."""
        payload: dict[str, Any] = {}
        if company_name:
            payload["company_name"] = company_name.strip()
        if domain:
            payload["domain"] = domain.strip()

        if not payload:
            raise CrustdataError("Either company_name or domain is required", status_code=400)

        cache_key = f"{company_name}:{domain}"
        if cache_key in self._company_cache:
            return self._company_cache[cache_key]

        result = await self._post("/company/identify", payload)
        self._company_cache[cache_key] = result
        return result

    # -------------------------------------------------------------
    # 4. POST /company/enrich
    # -------------------------------------------------------------
    async def enrich_company(
        self,
        company_id: int | str | None = None,
        domain: str | None = None
    ) -> dict[str, Any]:
        """Enrich company details given company ID or domain."""
        payload: dict[str, Any] = {}
        if company_id:
            payload["company_id"] = company_id
        elif domain:
            payload["domain"] = domain.strip()
        else:
            raise CrustdataError("Either company_id or domain is required", status_code=400)

        cache_key = f"enrich:{company_id}:{domain}"
        if cache_key in self._company_cache:
            return self._company_cache[cache_key]

        result = await self._post("/company/enrich", payload)
        self._company_cache[cache_key] = result
        return result

    # -------------------------------------------------------------
    # Diagnostics / Smoke Test
    # -------------------------------------------------------------
    async def diagnostics(self) -> dict[str, Any]:
        """Safe diagnostics probe to verify API key and reachability."""
        if not self.api_key:
            return {"status": "unconfigured", "error": "No CRUSTDATA_API_KEY configured."}

        try:
            # Safe probe using identify for a well-known test domain
            res = await self.identify_company(domain="google.com")
            return {"status": "connected", "sample": res}
        except CrustdataError as e:
            return {"status": "error", "error": str(e), "status_code": e.status_code}
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Global client singleton
crustdata_client = CrustdataClient()
