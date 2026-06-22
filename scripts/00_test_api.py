"""Step 2 — Verify the OpenElectricity API key works.

Loads the key from .env, makes a tiny call, prints a short result.
Run: python scripts/00_test_api.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (one level up from scripts/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("OPENELECTRICITY_API_KEY")

if not API_KEY or API_KEY.startswith("<"):
    print("ERROR: OPENELECTRICITY_API_KEY is not set in .env (or still a placeholder).")
    print("Edit .env and paste your key from https://platform.openelectricity.org.au/")
    sys.exit(1)


def main() -> int:
    # The client reads OPENELECTRICITY_API_KEY from the environment automatically.
    from openelectricity import OEClient

    try:
        with OEClient() as client:
            # 1) Confirm auth via the current-user endpoint.
            user = client.get_current_user()
            print("Authenticated OK.")
            print("  user:", getattr(user, "email", user))

            # 2) Tiny data call: list a few NEM facilities.
            facilities = client.get_facilities(network_id=["NEM"])
            rows = facilities.data[:5]
            print(f"\nget_facilities returned {len(facilities.data)} facilities. First 5:")
            for f in rows:
                print(f"  - {f.code}: {f.name}")
    except Exception as exc:  # noqa: BLE001 - surface any auth/network error clearly
        print(f"API call FAILED: {type(exc).__name__}: {exc}")
        return 1

    print("\nAPI key works. ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
