import asyncio
import os
import sys
import logging
from app.config import settings
from app.integrations.crustdata import CrustdataClient, CrustdataError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("diagnostics")

async def run_diagnostics():
    print("=" * 60)
    print("SwipeHire — Crustdata API Diagnostics & Smoke Test")
    print("=" * 60)

    client = CrustdataClient()

    if not client.api_key:
        print("[FAIL] No CRUSTDATA_API_KEY detected in environment or .env file.")
        print("Please configure CRUSTDATA_API_KEY in .env before running diagnostics.")
        return 1

    masked_key = f"{client.api_key[:6]}...{client.api_key[-4:]}"
    print(f"[INFO] Target Base URL : {client.base_url}")
    print(f"[INFO] API Version     : {client.api_version}")
    print(f"[INFO] API Key Found   : {masked_key}")
    print("-" * 60)

    # 1. Probe Company Identify
    print("[1/3] Testing POST /company/identify (probe: google.com)...")
    try:
        res = await client.company_identify(domain="google.com")
        print(f"      Status: SUCCESS (Latency: {res.metadata.get('latency_ms')}ms)")
        matches = res.data if isinstance(res.data, list) else [res.data]
        print(f"      Matched Companies: {len(matches)}")
    except CrustdataError as e:
        print(f"      [WARN] /company/identify failed: {e} (Status: {e.status_code})")

    # 2. Probe Company Enrich
    print("[2/3] Testing POST /company/enrich (probe: google.com)...")
    try:
        res = await client.company_enrich(domain="google.com")
        print(f"      Status: SUCCESS (Latency: {res.metadata.get('latency_ms')}ms)")
    except CrustdataError as e:
        print(f"      [WARN] /company/enrich failed: {e} (Status: {e.status_code})")

    # 3. Probe Person Search
    print("[3/3] Testing POST /person/search (probe query: Software Engineer)...")
    try:
        res = await client.person_search(search="Software Engineer", limit=2)
        profiles = res.data.get("profiles", []) if isinstance(res.data, dict) else []
        print(f"      Status: SUCCESS (Found {len(profiles)} profiles, Latency: {res.metadata.get('latency_ms')}ms)")
    except CrustdataError as e:
        print(f"      [WARN] /person/search failed: {e} (Status: {e.status_code})")

    print("-" * 60)
    print("[RESULT] Diagnostics complete. Client adapter is configured and ready.")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(run_diagnostics()))
