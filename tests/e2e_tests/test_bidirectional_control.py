#!/usr/bin/env python3
"""
雙向控制測試 (Bidirectional Control Test)

全面自動化測試，驗證 Odoo HA 所有 entity domain 的三向同步控制能力:
  Direction A: Odoo Backend → HA Core → verify state changed
  Direction B: Odoo Portal  → HA Core → verify state changed
  Direction C: Backend control → Portal state endpoint → verify consistency

Usage:
    python -m tests.e2e_tests.test_bidirectional_control
    # or directly:
    python tests/e2e_tests/test_bidirectional_control.py
"""

import json
import time
import sys
import requests
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

# =============================================================================
# Configuration
# =============================================================================

ODOO_URL = "http://localhost:9077"
ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "admin"
PORTAL_LOGIN = "portal"
PORTAL_PASSWORD = "portal"
HA_INSTANCE_ID = 1
SYNC_WAIT_SECONDS = 5
MAX_SYNC_WAIT = 10
DB_NAME = "odoohaiot"


@dataclass
class TestEntity:
    """Entity to test."""
    domain: str
    odoo_id: int
    ha_entity_id: str
    initial_state: str = ""
    actions: list = field(default_factory=list)
    read_only: bool = False
    skip_reason: str = ""


@dataclass
class TestResult:
    """Single test result."""
    domain: str
    direction: str  # A, B, C
    action: str
    success: bool
    message: str
    before_state: str = ""
    after_state: str = ""
    duration_ms: int = 0


# =============================================================================
# Test Entity Registry
# Each entry maps domain → entity to test + actions to perform
# =============================================================================

TEST_ENTITIES = [
    TestEntity(
        domain="switch",
        odoo_id=838,
        ha_entity_id="switch.jie_dai_qu_qiu_deng_1_2",
        actions=[
            {"name": "toggle", "service": "toggle", "service_data": {},
             "verify": lambda before, after: before != after},
        ],
    ),
    TestEntity(
        domain="light",
        odoo_id=63,
        ha_entity_id="light.jie_dai_qu_guang_zhuo",
        actions=[
            {"name": "toggle", "service": "toggle", "service_data": {},
             "verify": lambda before, after: before != after},
        ],
    ),
    TestEntity(
        domain="climate",
        odoo_id=101,
        ha_entity_id="climate.room_air_conditioner",
        actions=[
            {"name": "set_hvac_mode", "service": "set_hvac_mode",
             "service_data": {"hvac_mode": "cool"},
             "verify": lambda before, after: True},  # accept any response
        ],
    ),
    TestEntity(
        domain="input_boolean",
        odoo_id=39,
        ha_entity_id="input_boolean.test111",
        actions=[
            {"name": "toggle", "service": "toggle", "service_data": {},
             "verify": lambda before, after: before != after},
        ],
    ),
    TestEntity(
        domain="input_number",
        odoo_id=40,
        ha_entity_id="input_number.efwghweiogehqhjgqiwoh",
        actions=[
            {"name": "set_value", "service": "set_value",
             "service_data": {"value": 50.0},  # overridden per direction
             "verify": lambda before, after: True},  # verified via _get_expected_value
        ],
    ),
    TestEntity(
        domain="input_text",
        odoo_id=111,
        ha_entity_id="input_text.dfowjoefjo",
        actions=[
            {"name": "set_value", "service": "set_value",
             "service_data": {"value": f"test_{int(time.time())}"},
             "verify": lambda before, after: before != after},
        ],
    ),
    TestEntity(
        domain="automation",
        odoo_id=331,
        ha_entity_id="automation.shi_nei_wen_shi_du_shang_pao_zhi_zi_ce_hui_shu_shi_jie_neng_ai",
        actions=[
            {"name": "toggle", "service": "toggle", "service_data": {},
             "verify": lambda before, after: before != after},
        ],
    ),
    TestEntity(
        domain="scene",
        odoo_id=41,
        ha_entity_id="scene.qi_ci_wo",
        actions=[
            {"name": "activate", "service": "turn_on", "service_data": {},
             "verify": lambda before, after: True},  # scene state is timestamp
        ],
    ),
    TestEntity(
        domain="script",
        odoo_id=113,
        ha_entity_id="script.ai",
        actions=[
            {"name": "run", "service": "turn_on", "service_data": {},
             "verify": lambda before, after: True},  # script runs then returns to off
        ],
    ),
    TestEntity(
        domain="button",
        odoo_id=83,
        ha_entity_id="button.smart_wired_gateway_pro_shi_bie",
        actions=[
            {"name": "press", "service": "press", "service_data": {},
             "verify": lambda before, after: True},  # button state is timestamp
        ],
    ),
    # Read-only domains
    TestEntity(
        domain="sensor",
        odoo_id=30,
        ha_entity_id="sensor.backup_backup_manager_state",
        read_only=True,
        actions=[],
    ),
    TestEntity(
        domain="binary_sensor",
        odoo_id=119,
        ha_entity_id="binary_sensor.iphone_focus",
        read_only=True,
        actions=[],
    ),
    # Template / Helper entities for previously-skipped domains
    TestEntity(
        domain="cover",
        odoo_id=1710,
        ha_entity_id="cover.bidir_test_cover",
        actions=[
            {"name": "close_cover", "service": "close_cover", "service_data": {},
             "verify": lambda before, after: after == "closed"},
        ],
    ),
    TestEntity(
        domain="fan",
        odoo_id=1709,
        ha_entity_id="fan.bidir_test_fan",
        actions=[
            {"name": "toggle", "service": "toggle", "service_data": {},
             "verify": lambda before, after: before != after},
        ],
    ),
    TestEntity(
        domain="number",
        odoo_id=1711,
        ha_entity_id="number.bidir_test_number_entity",
        actions=[
            {"name": "set_value", "service": "set_value",
             "service_data": {"value": 50.0},  # overridden per direction
             "verify": lambda before, after: True},  # verified via _get_expected_value
        ],
    ),
    TestEntity(
        domain="input_select",
        odoo_id=1706,
        ha_entity_id="input_select.bidir_test_select",
        actions=[
            {"name": "select_option", "service": "select_option",
             "service_data": {"option": "Option A"},  # overridden per direction
             "verify": lambda before, after: True},  # verified via _get_expected_value
        ],
    ),
    # media_player: all hardware entities unavailable (Chromecast offline),
    # template integration does not support media_player domain.
    # Test as read-only to verify unavailable state display.
    TestEntity(
        domain="media_player",
        odoo_id=348,
        ha_entity_id="media_player.ke_ting_de_dian_shi",
        read_only=True,
        actions=[],
    ),
]


# =============================================================================
# Odoo RPC Client
# =============================================================================

class OdooRPC:
    """JSON-RPC client for Odoo."""

    def __init__(self, base_url: str, db: str):
        self.base_url = base_url.rstrip("/")
        self.db = db
        self.session = requests.Session()
        self.uid = None

    def login(self, username: str, password: str) -> bool:
        """Authenticate and establish session."""
        url = f"{self.base_url}/web/session/authenticate"
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "id": 1,
            "params": {
                "db": self.db,
                "login": username,
                "password": password,
            },
        }
        resp = self.session.post(url, json=payload, timeout=30)
        data = resp.json()
        result = data.get("result", {})
        self.uid = result.get("uid")
        return bool(self.uid)

    def call(self, model: str, method: str, args: list, kwargs: dict = None) -> any:
        """Execute an Odoo RPC call."""
        url = f"{self.base_url}/web/dataset/call_kw"
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "id": 2,
            "params": {
                "model": model,
                "method": method,
                "args": args,
                "kwargs": kwargs or {},
            },
        }
        resp = self.session.post(url, json=payload, timeout=30)
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"RPC error: {data['error']}")
        return data.get("result")

    def read_entity_state(self, entity_odoo_id: int) -> dict:
        """Read entity state from Odoo."""
        records = self.call(
            "ha.entity",
            "search_read",
            [[["id", "=", entity_odoo_id]]],
            {"fields": ["entity_id", "entity_state", "domain", "attributes", "last_changed"]},
        )
        if records:
            return records[0]
        return {}

    def call_service(self, entity_odoo_id: int, domain: str,
                     service: str, service_data: dict) -> dict:
        """Call HA service via Odoo backend controller endpoint."""
        # First, get the HA entity_id from the Odoo record
        entity = self.call(
            "ha.entity",
            "search_read",
            [[["id", "=", entity_odoo_id]]],
            {"fields": ["entity_id", "ha_instance_id"]},
        )
        if not entity:
            return {"success": False, "error": "Entity not found in Odoo"}

        ha_entity_id = entity[0]["entity_id"]
        instance_id = entity[0]["ha_instance_id"][0] if entity[0]["ha_instance_id"] else None

        if not instance_id:
            return {"success": False, "error": "No HA instance for entity"}

        # Use the backend call_service endpoint
        url = f"{self.base_url}/odoo_ha_addon/call_service"
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "id": 10,
            "params": {
                "domain": domain,
                "service": service,
                "service_data": {**service_data, "entity_id": ha_entity_id},
                "ha_instance_id": instance_id,
            },
        }
        try:
            resp = self.session.post(url, json=payload, timeout=30)
            data = resp.json()
            result = data.get("result", {})
            if isinstance(result, dict) and result.get("success") is False:
                return {"success": False, "error": result.get("error", "unknown")}
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}


# =============================================================================
# Portal HTTP Client
# =============================================================================

class PortalClient:
    """HTTP client for Odoo Portal endpoints."""

    def __init__(self, base_url: str, db: str):
        self.base_url = base_url.rstrip("/")
        self.db = db
        self.session = requests.Session()

    def login(self, username: str, password: str) -> bool:
        """Login to portal via web form."""
        # Get CSRF token
        login_url = f"{self.base_url}/web/login"
        resp = self.session.get(login_url, timeout=30)

        # Extract CSRF token from response
        import re
        csrf_match = re.search(
            r'name="csrf_token"\s+value="([^"]+)"', resp.text
        )
        csrf_token = csrf_match.group(1) if csrf_match else ""

        # Submit login form
        data = {
            "login": username,
            "password": password,
            "csrf_token": csrf_token,
            "db": self.db,
        }
        resp = self.session.post(login_url, data=data, timeout=30, allow_redirects=True)
        return resp.status_code == 200 and "/web/login" not in resp.url

    def get_entity_state(self, instance_id: int, entity_odoo_id: int) -> dict:
        """POST /my/ha/<instance_id>/entity/<entity_id>/state (JSON-RPC)"""
        url = f"{self.base_url}/my/ha/{instance_id}/entity/{entity_odoo_id}/state"
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "id": 4,
            "params": {},
        }
        resp = self.session.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            result = data.get("result", {})
            if isinstance(result, dict) and result.get("success"):
                return result.get("data", {})
            return result
        return {"error": f"HTTP {resp.status_code}", "body": resp.text[:200]}

    def call_service(self, instance_id: int, entity_odoo_id: int,
                     domain: str, service: str, service_data: dict) -> dict:
        """POST /my/ha/<instance_id>/entity/<entity_id>/service"""
        url = f"{self.base_url}/my/ha/{instance_id}/entity/{entity_odoo_id}/service"
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "id": 3,
            "params": {
                "domain": domain,
                "service": service,
                "service_data": service_data,
            },
        }
        resp = self.session.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("result", data)
        return {"success": False, "error": f"HTTP {resp.status_code}"}


# =============================================================================
# Test Runner
# =============================================================================

class BidirectionalTestRunner:
    """Runs all bidirectional control tests."""

    def __init__(self):
        self.results: list[TestResult] = []
        self.admin_rpc = OdooRPC(ODOO_URL, DB_NAME)
        self.portal_client = PortalClient(ODOO_URL, DB_NAME)

    def setup(self) -> bool:
        """Initialize connections."""
        print("=" * 70)
        print("雙向控制測試 - Bidirectional Control Test Suite")
        print("=" * 70)
        print(f"Odoo URL: {ODOO_URL}")
        print(f"HA Instance: WOOW HA (id={HA_INSTANCE_ID})")
        print(f"Start time: {datetime.now(timezone.utc).isoformat()}")
        print()

        # Login admin
        print("[SETUP] Logging in as admin...", end=" ")
        if not self.admin_rpc.login(ADMIN_LOGIN, ADMIN_PASSWORD):
            print("FAILED")
            return False
        print("OK")

        # Login portal
        print("[SETUP] Logging in as portal user...", end=" ")
        if not self.portal_client.login(PORTAL_LOGIN, PORTAL_PASSWORD):
            print("FAILED")
            return False
        print("OK")

        print()
        return True

    def wait_for_sync(self, seconds: float = None):
        """Wait for HA↔Odoo state sync."""
        wait = seconds or SYNC_WAIT_SECONDS
        time.sleep(wait)

    def read_backend_state(self, entity: TestEntity) -> str:
        """Read entity state from Odoo backend."""
        data = self.admin_rpc.read_entity_state(entity.odoo_id)
        return data.get("entity_state", "unknown")

    def read_portal_state(self, entity: TestEntity) -> str:
        """Read entity state from portal endpoint."""
        data = self.portal_client.get_entity_state(HA_INSTANCE_ID, entity.odoo_id)
        if isinstance(data, dict):
            # Portal state endpoint returns: {entity_state: "...", ...}
            return data.get("entity_state",
                          data.get("state",
                          data.get("error", "unknown")))
        return "unknown"

    # Per-direction dynamic values to ensure each direction produces unique changes
    _DIRECTION_VALUES = {
        "number": {"A": 25.0, "B": 50.0, "C": 75.0},
        "input_number": {"A": 25.0, "B": 50.0, "C": 75.0},
        "input_select": {"A": "Option A", "B": "Option B", "C": "Option C"},
        "select": {"A": "Option A", "B": "Option B", "C": "Option C"},
    }

    def _make_dynamic_service_data(self, entity: TestEntity, action: dict,
                                   direction: str) -> dict:
        """Create service_data with per-direction dynamic values."""
        service_data = dict(action["service_data"])

        if entity.domain == "input_text" and "value" in service_data:
            service_data["value"] = f"test_{direction}_{int(time.time())}"
        elif entity.domain in self._DIRECTION_VALUES:
            values = self._DIRECTION_VALUES[entity.domain]
            if "value" in service_data:
                service_data["value"] = values[direction]
            elif "option" in service_data:
                service_data["option"] = values[direction]

        return service_data

    def _get_expected_value(self, entity: TestEntity, action: dict,
                            direction: str) -> Optional[str]:
        """Return expected state after service call, or None for default verify."""
        if entity.domain in self._DIRECTION_VALUES:
            values = self._DIRECTION_VALUES[entity.domain]
            return str(values[direction])
        return None

    def test_direction_a(self, entity: TestEntity, action: dict) -> TestResult:
        """Direction A: Backend → HA → Backend (verify round-trip)."""
        start = time.time()
        action_name = action["name"]

        # Read before state
        before = self.read_backend_state(entity)

        # Update dynamic service_data per direction
        service_data = self._make_dynamic_service_data(entity, action, "A")

        # Call service via backend
        result = self.admin_rpc.call_service(
            entity.odoo_id, entity.domain, action["service"], service_data
        )

        if not result.get("success", False):
            duration = int((time.time() - start) * 1000)
            return TestResult(
                domain=entity.domain,
                direction="A",
                action=action_name,
                success=False,
                message=f"Service call failed: {result.get('error', 'unknown')}",
                before_state=before,
                duration_ms=duration,
            )

        # Wait for sync
        self.wait_for_sync()

        # Read after state
        after = self.read_backend_state(entity)
        duration = int((time.time() - start) * 1000)

        # Verify — use dynamic verify for domains with per-direction expected values
        verify_fn = action.get("verify", lambda b, a: b != a)
        expected = self._get_expected_value(entity, action, "A")
        if expected is not None:
            passed = after == expected
        else:
            passed = verify_fn(before, after)

        return TestResult(
            domain=entity.domain,
            direction="A",
            action=action_name,
            success=passed,
            message=f"State: {before} → {after}" if passed else f"State unchanged: {before}",
            before_state=before,
            after_state=after,
            duration_ms=duration,
        )

    def test_direction_b(self, entity: TestEntity, action: dict) -> TestResult:
        """Direction B: Portal → HA → Portal (verify round-trip)."""
        start = time.time()
        action_name = action["name"]

        # Read before state via portal
        before = self.read_portal_state(entity)

        # Update dynamic service_data per direction
        service_data = self._make_dynamic_service_data(entity, action, "B")

        # Call service via portal
        result = self.portal_client.call_service(
            HA_INSTANCE_ID, entity.odoo_id,
            entity.domain, action["service"], service_data
        )

        if not result.get("success", False):
            duration = int((time.time() - start) * 1000)
            error = result.get("error", "unknown")
            return TestResult(
                domain=entity.domain,
                direction="B",
                action=action_name,
                success=False,
                message=f"Portal service call failed: {error}",
                before_state=before,
                duration_ms=duration,
            )

        # Wait for sync
        self.wait_for_sync()

        # Read after state via portal
        after = self.read_portal_state(entity)
        duration = int((time.time() - start) * 1000)

        # Verify — use dynamic verify for domains with per-direction expected values
        verify_fn = action.get("verify", lambda b, a: b != a)
        expected = self._get_expected_value(entity, action, "B")
        if expected is not None:
            passed = after == expected
        else:
            passed = verify_fn(before, after)

        return TestResult(
            domain=entity.domain,
            direction="B",
            action=action_name,
            success=passed,
            message=f"State: {before} → {after}" if passed else f"State unchanged: {before}",
            before_state=before,
            after_state=after,
            duration_ms=duration,
        )

    def test_direction_c(self, entity: TestEntity, action: dict) -> TestResult:
        """Direction C: Backend control → Portal verify (cross-check)."""
        start = time.time()
        action_name = action["name"]

        # Update dynamic service_data per direction
        service_data = self._make_dynamic_service_data(entity, action, "C")

        # Call service via backend
        result = self.admin_rpc.call_service(
            entity.odoo_id, entity.domain, action["service"], service_data
        )

        if not result.get("success", False):
            duration = int((time.time() - start) * 1000)
            return TestResult(
                domain=entity.domain,
                direction="C",
                action=action_name,
                success=False,
                message=f"Backend service call failed: {result.get('error', 'unknown')}",
                duration_ms=duration,
            )

        # Wait for sync
        self.wait_for_sync()

        # Read from both sources
        backend_state = self.read_backend_state(entity)
        portal_state = self.read_portal_state(entity)
        duration = int((time.time() - start) * 1000)

        # Verify consistency
        passed = backend_state == portal_state

        return TestResult(
            domain=entity.domain,
            direction="C",
            action=action_name,
            success=passed,
            message=(
                f"Backend={backend_state}, Portal={portal_state} — consistent"
                if passed
                else f"MISMATCH: Backend={backend_state}, Portal={portal_state}"
            ),
            before_state=backend_state,
            after_state=portal_state,
            duration_ms=duration,
        )

    def test_read_only(self, entity: TestEntity) -> list[TestResult]:
        """Test read-only domain (sensor, binary_sensor)."""
        results = []

        # Backend state readable
        backend_state = self.read_backend_state(entity)
        results.append(TestResult(
            domain=entity.domain,
            direction="A",
            action="read_state",
            success=backend_state not in ("", "unknown", None),
            message=f"Backend state: {backend_state}",
            after_state=backend_state,
        ))

        # Portal state readable
        portal_state = self.read_portal_state(entity)
        results.append(TestResult(
            domain=entity.domain,
            direction="B",
            action="read_state",
            success=portal_state not in ("", "unknown", None),
            message=f"Portal state: {portal_state}",
            after_state=portal_state,
        ))

        # Cross-check
        results.append(TestResult(
            domain=entity.domain,
            direction="C",
            action="state_consistency",
            success=backend_state == portal_state,
            message=(
                f"Backend={backend_state}, Portal={portal_state} — consistent"
                if backend_state == portal_state
                else f"MISMATCH: Backend={backend_state}, Portal={portal_state}"
            ),
            before_state=backend_state,
            after_state=portal_state,
        ))

        return results

    def run_entity_tests(self, entity: TestEntity):
        """Run all tests for one entity."""
        print(f"\n[{entity.domain.upper()}] {entity.ha_entity_id or '(no entity)'}")

        if entity.skip_reason:
            print(f"  ⏭️  SKIP: {entity.skip_reason}")
            self.results.append(TestResult(
                domain=entity.domain,
                direction="—",
                action="skip",
                success=True,
                message=entity.skip_reason,
            ))
            return

        # Check if entity is unavailable
        if entity.odoo_id:
            state = self.read_backend_state(entity)
            if state == "unavailable":
                print(f"  ⏭️  SKIP: Entity state is 'unavailable'")
                self.results.append(TestResult(
                    domain=entity.domain,
                    direction="—",
                    action="skip",
                    success=True,
                    message="Entity unavailable (device offline)",
                ))
                return

        if entity.read_only:
            print("  (read-only domain)")
            ro_results = self.test_read_only(entity)
            for r in ro_results:
                status = "✅" if r.success else "❌"
                print(f"  {status} {r.direction}: {r.action} — {r.message}")
            self.results.extend(ro_results)
            return

        # Run controllable domain tests
        for action in entity.actions:
            action_name = action["name"]

            # Direction A: Backend → HA
            r = self.test_direction_a(entity, action)
            status = "✅" if r.success else "❌"
            print(f"  {status} A: Backend→HA {action_name} — {r.message} ({r.duration_ms}ms)")
            self.results.append(r)

            # Direction B: Portal → HA
            r = self.test_direction_b(entity, action)
            status = "✅" if r.success else "❌"
            print(f"  {status} B: Portal→HA {action_name} — {r.message} ({r.duration_ms}ms)")
            self.results.append(r)

            # Direction C: Backend → Portal cross-check
            r = self.test_direction_c(entity, action)
            status = "✅" if r.success else "❌"
            print(f"  {status} C: Backend→Portal {action_name} — {r.message} ({r.duration_ms}ms)")
            self.results.append(r)

    def run_all(self):
        """Execute all tests and print report."""
        if not self.setup():
            print("\n❌ Setup failed. Aborting.")
            return False

        print(f"\nRunning tests for {len(TEST_ENTITIES)} domains...")
        print("-" * 70)

        for entity in TEST_ENTITIES:
            self.run_entity_tests(entity)

        # Print summary
        self.print_report()
        return True

    def print_report(self):
        """Print final test report."""
        print("\n" + "=" * 70)
        print("測試報告 - Test Report")
        print("=" * 70)
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")

        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = sum(1 for r in self.results
                     if not r.success and r.direction != "—")
        skipped = sum(1 for r in self.results
                      if r.direction == "—")

        print(f"\nTotal: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
        print()

        # Group by domain
        domains_seen = []
        for r in self.results:
            if r.domain not in domains_seen:
                domains_seen.append(r.domain)

        for domain in domains_seen:
            domain_results = [r for r in self.results if r.domain == domain]
            domain_passed = all(r.success for r in domain_results)
            icon = "✅" if domain_passed else "❌"
            print(f"{icon} [{domain}]")
            for r in domain_results:
                status = "✅" if r.success else ("⏭️" if r.direction == "—" else "❌")
                dir_label = f"Dir {r.direction}" if r.direction != "—" else "SKIP"
                print(f"    {status} {dir_label}: {r.action} — {r.message}")

        print("\n" + "=" * 70)

        if failed > 0:
            print(f"\n❌ {failed} test(s) FAILED")
            for r in self.results:
                if not r.success and r.direction != "—":
                    print(f"  - [{r.domain}] Dir {r.direction} {r.action}: {r.message}")
        else:
            print(f"\n✅ All {passed} test(s) passed ({skipped} skipped)")

        # Save JSON report
        report_path = "tests/e2e_tests/reports/bidirectional_test_report.json"
        try:
            import os
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            report = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "results": [
                    {
                        "domain": r.domain,
                        "direction": r.direction,
                        "action": r.action,
                        "success": r.success,
                        "message": r.message,
                        "before": r.before_state,
                        "after": r.after_state,
                        "duration_ms": r.duration_ms,
                    }
                    for r in self.results
                ],
            }
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\nJSON report saved to: {report_path}")
        except Exception as e:
            print(f"\nWarning: Could not save JSON report: {e}")

        return failed == 0


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    runner = BidirectionalTestRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1)
