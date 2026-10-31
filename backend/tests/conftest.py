"""Shared test configuration: keeps the suite offline and isolated.

- Uses a throwaway SQLite database instead of the developer's ``swipehire.db``.
- Stubs the shared ``crustdata_client`` singleton so API tests never need a live key.
  Set ``CRUSTDATA_LIVE_TEST=true`` to talk to the real Crustdata API instead.
- Never calls Anthropic: the AI key is cleared so parsers/explanations use their
  deterministic fallbacks.
"""
import os
import tempfile
import zlib

# Must run before `app.config` is imported anywhere.
_TMP_DIR = tempfile.mkdtemp(prefix="swipehire-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_TMP_DIR, 'test.db')}"
os.environ["UPLOAD_DIR"] = os.path.join(_TMP_DIR, "uploads")
os.environ["ANTHROPIC_API_KEY"] = ""

import pytest  # noqa: E402

LIVE = os.environ.get("CRUSTDATA_LIVE_TEST", "").lower() == "true"


@pytest.fixture(autouse=True)
def offline_crustdata(monkeypatch):
    if LIVE:
        yield
        return

    from app.integrations.crustdata import crustdata_client

    async def identify_company(company_name=None, domain=None):
        key = (domain or company_name or "").lower()
        return {
            "matches": [
                {
                    "confidence_score": 0.95,
                    "company_data": {
                        "crustdata_company_id": zlib.crc32(key.encode()),
                        "basic_info": {
                            "name": company_name or domain,
                            "primary_domain": domain,
                        },
                    },
                }
            ]
        }

    async def enrich_company(company_id=None, domain=None):
        return {"basic_info": {"primary_domain": domain}, "headcount": {"total": 100}}

    class _Result:
        def __init__(self, data):
            self.data = data
            self.raw = data
            self.cursor = None
            self.metadata = {}

    async def person_search(*args, **kwargs):
        return _Result({"profiles": []})

    async def diagnostics():
        return {"status": "unconfigured", "error": "stubbed in tests"}

    monkeypatch.setattr(crustdata_client, "identify_company", identify_company)
    monkeypatch.setattr(crustdata_client, "enrich_company", enrich_company)
    monkeypatch.setattr(crustdata_client, "person_search", person_search)
    monkeypatch.setattr(crustdata_client, "diagnostics", diagnostics)
    yield
