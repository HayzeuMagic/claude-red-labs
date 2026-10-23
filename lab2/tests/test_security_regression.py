"""
Regression test for Lab 2.

Demonstrates the injection against app.py (vulnerable) and proves app_fixed.py
(the student/AI-proposed fix) closes it, using Flask's test client — no network,
no running server needed, fully offline.

Run from the repo root:
    pip install -r lab2/vuln_app/requirements.txt pytest
    pytest lab2/tests/test_security_regression.py -v
"""
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vuln_app"))

# A payload that, against a string-built query, turns the WHERE clause into
# something that always matches every row (classic boolean-based injection).
INJECTION_PAYLOAD = "' OR '1'='1"


def _make_client(module_name):
    mod = importlib.import_module(module_name)
    mod.init_db()
    mod.app.config["TESTING"] = True
    return mod.app.test_client()


def test_vulnerable_app_leaks_all_users_via_injection():
    """Documents the bug: app.py returns every row, including admin, to an
    unauthenticated request for a single named user. This test is expected to
    FAIL once you point it at app_fixed instead — that's the point."""
    client = _make_client("app")
    resp = client.get(f"/user?username={INJECTION_PAYLOAD}")
    assert resp.status_code == 200
    data = resp.get_json()
    usernames = {row["username"] for row in data}
    # Vulnerable behavior: injection returns ALL users, not just one.
    assert usernames == {"alice", "bob", "admin"}, (
        "expected the vulnerable app to leak all users for this payload "
        f"(got {usernames}) -- if this fails, app.py's query changed"
    )


def test_normal_lookup_still_works_on_vulnerable_app():
    client = _make_client("app")
    resp = client.get("/user?username=alice")
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["username"] == "alice"


def test_fixed_app_blocks_the_same_injection():
    """The actual regression test for the fix: the same payload that leaked
    every user against app.py must return ZERO rows against app_fixed.py,
    because no username actually equals the literal injection string."""
    client = _make_client("app_fixed")
    resp = client.get(f"/user?username={INJECTION_PAYLOAD}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == [], f"fix did not hold -- injection payload returned rows: {data}"


def test_fixed_app_normal_lookup_still_works():
    """The fix must not break legitimate use."""
    client = _make_client("app_fixed")
    resp = client.get("/user?username=alice")
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["username"] == "alice"
    assert data[0]["is_admin"] is False


def test_fixed_app_does_not_leak_admin_for_unrelated_query():
    client = _make_client("app_fixed")
    resp = client.get(f"/user?username=bob{INJECTION_PAYLOAD}")
    data = resp.get_json()
    assert data == []
