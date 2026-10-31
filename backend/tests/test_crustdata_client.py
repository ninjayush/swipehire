import os
import json
import asyncio
import pytest
import httpx
from app.integrations.crustdata import (
    CrustdataClient,
    CrustdataResult,
    CrustdataError,
    CrustdataBadRequestError,
    CrustdataAuthError,
    CrustdataForbiddenError,
    CrustdataRateLimitError,
    CrustdataServerError,
    TTLCache,
)

# -------------------------------------------------------------
# 1. Headers, Base URL and Payload Shape
# -------------------------------------------------------------
def test_headers_and_base_url():
    client = CrustdataClient(api_key="cd_test_key_abc", api_version="2025-11-01")
    headers = client._get_headers()
    assert headers["Authorization"] == "Bearer cd_test_key_abc"
    assert headers["x-api-version"] == "2025-11-01"
    assert headers["Content-Type"] == "application/json"
    assert client.base_url == "https://api.crustdata.com"

def test_missing_api_key_raises_auth_error():
    client = CrustdataClient(api_key="")
    with pytest.raises(CrustdataAuthError):
        client._get_headers()

@pytest.mark.asyncio
async def test_person_enrich_payload_shape():
    recorded_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json=[{"matched_on": "https://linkedin.com/in/test", "matches": []}])

    transport = httpx.MockTransport(handler)
    client = CrustdataClient(api_key="test_key", transport=transport)

    res = await client.person_enrich("https://linkedin.com/in/test")
    assert len(recorded_requests) == 1
    req = recorded_requests[0]
    assert req.url.path == "/person/enrich"
    body = json.loads(req.content.decode())
    assert body == {"professional_network_profile_urls": ["https://linkedin.com/in/test"]}

@pytest.mark.asyncio
async def test_company_identify_payload_shape():
    recorded_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json=[{"matched_on": "stripe.com", "matches": []}])

    transport = httpx.MockTransport(handler)
    client = CrustdataClient(api_key="test_key", transport=transport)

    await client.company_identify(domain="stripe.com")
    req = recorded_requests[0]
    assert req.url.path == "/company/identify"
    body = json.loads(req.content.decode())
    assert body == {"domains": ["stripe.com"]}

# -------------------------------------------------------------
# 2. Cursor Propagation & Bounded Limit in Person Search
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_person_search_cursor_and_bounds():
    recorded_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json={"profiles": [], "cursor": "next_page_token_xyz"})

    transport = httpx.MockTransport(handler)
    client = CrustdataClient(api_key="test_key", transport=transport)

    # Test limit cap (should be capped at 50) and cursor propagation
    res = await client.person_search(search="Python", limit=100, cursor="initial_token_123")
    assert res.cursor == "next_page_token_xyz"

    body = json.loads(recorded_requests[0].content.decode())
    assert body["limit"] == 50  # Bounded at 50
    assert body["cursor"] == "initial_token_123"
    assert body["search"] == {"query": "Python"}

# -------------------------------------------------------------
# 3. HTTP Error Handling (400, 401, 403, 429, 5xx)
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_error_400_bad_request():
    transport = httpx.MockTransport(lambda req: httpx.Response(400, text="Invalid identifier format"))
    client = CrustdataClient(api_key="test_key", transport=transport, max_retries=0)

    with pytest.raises(CrustdataBadRequestError) as exc_info:
        await client.person_enrich("https://linkedin.com/in/test")
    assert exc_info.value.status_code == 400

@pytest.mark.asyncio
async def test_error_401_unauthorized():
    transport = httpx.MockTransport(lambda req: httpx.Response(401, text="Invalid token"))
    client = CrustdataClient(api_key="test_key", transport=transport, max_retries=0)

    with pytest.raises(CrustdataAuthError) as exc_info:
        await client.company_identify(domain="test.com")
    assert exc_info.value.status_code == 401

@pytest.mark.asyncio
async def test_error_403_forbidden():
    transport = httpx.MockTransport(lambda req: httpx.Response(403, text="Feature not enabled for key"))
    client = CrustdataClient(api_key="test_key", transport=transport, max_retries=0)

    with pytest.raises(CrustdataForbiddenError) as exc_info:
        await client.company_enrich(domain="test.com")
    assert exc_info.value.status_code == 403

@pytest.mark.asyncio
async def test_error_429_bounded_retry():
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(429, headers={"Retry-After": "0"})

    transport = httpx.MockTransport(handler)
    client = CrustdataClient(api_key="test_key", transport=transport, max_retries=2)

    with pytest.raises(CrustdataRateLimitError):
        await client.company_identify(domain="test.com")
    # Initial attempt + 2 retries = 3 attempts total
    assert attempts == 3

@pytest.mark.asyncio
async def test_error_500_server_error_retry():
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            return httpx.Response(502, text="Bad Gateway")
        return httpx.Response(200, json={"domains": ["recovered.com"]})

    transport = httpx.MockTransport(handler)
    client = CrustdataClient(api_key="test_key", transport=transport, max_retries=2)

    res = await client.company_identify(domain="recovered.com")
    assert attempts == 2
    assert res.data == {"domains": ["recovered.com"]}

# -------------------------------------------------------------
# 4. TTL Cache Hit/Miss Behavior
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_ttl_cache_hit_and_miss():
    requests_made = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests_made
        requests_made += 1
        return httpx.Response(200, json=[{"matched_on": "cached.com"}])

    transport = httpx.MockTransport(handler)
    client = CrustdataClient(api_key="test_key", transport=transport, cache_ttl=10.0)

    # First call -> Cache MISS -> HTTP request made
    res1 = await client.company_identify(domain="cached.com")
    assert requests_made == 1
    assert client.company_cache.misses == 1
    assert client.company_cache.hits == 0

    # Second call -> Cache HIT -> No new HTTP request
    res2 = await client.company_identify(domain="cached.com")
    assert requests_made == 1
    assert client.company_cache.hits == 1

# -------------------------------------------------------------
# 5. Opt-in Live Smoke Tests (Controlled by Environment Variable)
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_live_smoke_test_opt_in():
    """
    Runs only when CRUSTDATA_LIVE_TEST=true is set in the environment.
    Guarantees ordinary test suite remains offline and non-flaky.
    """
    if os.getenv("CRUSTDATA_LIVE_TEST", "").lower() not in ("true", "1", "yes"):
        pytest.skip("Skipping live Crustdata smoke test. Set CRUSTDATA_LIVE_TEST=true to run.")

    from app.integrations.crustdata import crustdata_client
    diag = await crustdata_client.diagnostics()
    assert diag.get("status") == "connected"
