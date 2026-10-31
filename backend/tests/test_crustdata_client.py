import pytest
from app.integrations.crustdata import CrustdataClient, CrustdataError

def test_client_headers():
    client = CrustdataClient(api_key="test_key_123", api_version="2025-11-01")
    headers = client._get_headers()
    assert headers["Authorization"] == "Bearer test_key_123"
    assert headers["x-api-version"] == "2025-11-01"
    assert headers["Content-Type"] == "application/json"

def test_enrich_empty_url_validation():
    client = CrustdataClient(api_key="test_key_123")
    with pytest.raises(CrustdataError) as exc_info:
        import asyncio
        asyncio.run(client.enrich_person(""))
    assert exc_info.value.status_code == 400

def test_identify_empty_params_validation():
    client = CrustdataClient(api_key="test_key_123")
    with pytest.raises(CrustdataError) as exc_info:
        import asyncio
        asyncio.run(client.identify_company())
    assert exc_info.value.status_code == 400
