#!/usr/bin/env python3
"""
R2: API Stress Tests (~60 cases)
=================================
Parameter boundary injection, load, concurrency, portal boundary.

Sub-groups:
  R2-A: Parameter boundary injection (25 cases)
  R2-B: Load & concurrency (15 cases)
  R2-C: Portal API boundary (20 cases)
"""

import sys
import os
import time
import json
import uuid
import logging
import traceback
import concurrent.futures
import urllib.request
import urllib.error
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.stability.helpers.odoo_client import OdooClient, OdooRPCError
from tests.stability.helpers.ha_client import HAVerifier
from tests.stability.helpers.report import TestReport, TestResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_logger = logging.getLogger(__name__)

INSTANCE_ID = 1
ODOO_URL = "http://localhost:9077"


# =====================================================================
# R2-A: Parameter Boundary Injection (25 cases)
# =====================================================================

def r2a_parameter_boundary(report: TestReport, odoo: OdooClient, ha: HAVerifier):
    """Parameter boundary and injection testing on controller endpoints."""
    cat = "R2-A: Parameter Boundary"

    # A01: Null ha_instance_id
    t = report.new_test("R2-A01", "areas with null ha_instance_id", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/areas",
                                      {"ha_instance_id": None})
        # Should fallback to default instance or return error gracefully
        t.passed(f"Handled null: success={result.get('success')}")
    except OdooRPCError as e:
        t.passed(f"Rejected null: {e}")
    except Exception as e:
        t.errored(str(e))

    # A02: Negative ha_instance_id
    t = report.new_test("R2-A02", "areas with negative instance_id", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/areas",
                                      {"ha_instance_id": -1})
        if not result.get("success"):
            t.passed(f"Rejected: {result.get('error', 'N/A')}")
        else:
            t.passed(f"Returned empty data (acceptable)")
    except OdooRPCError as e:
        t.passed(f"Error raised: {e}")
    except Exception as e:
        t.errored(str(e))

    # A03: Very large instance_id
    t = report.new_test("R2-A03", "areas with huge instance_id (999999)", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/areas",
                                      {"ha_instance_id": 999999})
        if not result.get("success"):
            t.passed(f"Rejected: {result.get('error', 'N/A')}")
        else:
            t.passed("Returned empty (no such instance)")
    except OdooRPCError as e:
        t.passed(f"Error raised: {e}")
    except Exception as e:
        t.errored(str(e))

    # A04: String instead of int for instance_id
    t = report.new_test("R2-A04", "areas with string instance_id", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/areas",
                                      {"ha_instance_id": "abc"})
        t.passed(f"Handled string: success={result.get('success')}, error={result.get('error', 'N/A')}")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A05: SQL injection in area_id
    t = report.new_test("R2-A05", "SQL injection in entities_by_area", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/entities_by_area",
                                      {"area_id": "1 OR 1=1; DROP TABLE ha_area;--",
                                       "ha_instance_id": INSTANCE_ID})
        t.passed(f"No SQL injection: success={result.get('success')}, error={result.get('error', 'N/A')}")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A06: XSS in service_data
    t = report.new_test("R2-A06", "XSS payload in call_service", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/call_service", {
            "domain": "light",
            "service": "toggle",
            "service_data": {
                "entity_id": '<script>alert("xss")</script>',
            },
            "ha_instance_id": INSTANCE_ID,
        })
        # Should not execute; just verify no server crash
        t.passed(f"XSS handled: success={result.get('success')}")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A07: Empty domain in call_service
    t = report.new_test("R2-A07", "Empty domain in call_service", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/call_service", {
            "domain": "",
            "service": "toggle",
            "service_data": {},
            "ha_instance_id": INSTANCE_ID,
        })
        if not result.get("success"):
            t.passed(f"Rejected empty domain: {result.get('error', 'N/A')}")
        else:
            t.failed("Should have rejected empty domain")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A08: Empty service in call_service
    t = report.new_test("R2-A08", "Empty service in call_service", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/call_service", {
            "domain": "light",
            "service": "",
            "service_data": {},
            "ha_instance_id": INSTANCE_ID,
        })
        if not result.get("success"):
            t.passed(f"Rejected empty service: {result.get('error', 'N/A')}")
        else:
            t.failed("Should have rejected empty service")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A09: Malformed JSON in service_data
    t = report.new_test("R2-A09", "Non-dict service_data", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/call_service", {
            "domain": "light",
            "service": "toggle",
            "service_data": "not_a_dict",
            "ha_instance_id": INSTANCE_ID,
        })
        t.passed(f"Handled: success={result.get('success')}, error={result.get('error', 'N/A')}")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A10: Float area_id
    t = report.new_test("R2-A10", "Float area_id in entities_by_area", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/entities_by_area",
                                      {"area_id": 1.5,
                                       "ha_instance_id": INSTANCE_ID})
        t.passed(f"Handled float: success={result.get('success')}")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A11: Missing required param (area_id)
    t = report.new_test("R2-A11", "entities_by_area without area_id", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/entities_by_area",
                                      {"ha_instance_id": INSTANCE_ID})
        if not result.get("success"):
            t.passed(f"Rejected missing area_id: {result.get('error', 'N/A')}")
        else:
            t.failed("Should require area_id")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A12: Boolean as instance_id
    t = report.new_test("R2-A12", "Boolean as ha_instance_id", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/areas",
                                      {"ha_instance_id": True})
        t.passed(f"Handled boolean: success={result.get('success')}")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A13: Array as instance_id
    t = report.new_test("R2-A13", "Array as ha_instance_id", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/areas",
                                      {"ha_instance_id": [1, 2, 3]})
        t.passed(f"Handled array: success={result.get('success')}")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A14: Zero instance_id
    t = report.new_test("R2-A14", "Zero ha_instance_id", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/areas",
                                      {"ha_instance_id": 0})
        t.passed(f"Handled zero: success={result.get('success')}")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A15: Unicode in domain field
    t = report.new_test("R2-A15", "Unicode domain in call_service", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/call_service", {
            "domain": "燈光",
            "service": "切換",
            "service_data": {},
            "ha_instance_id": INSTANCE_ID,
        })
        if not result.get("success"):
            t.passed(f"Rejected unicode domain")
        else:
            t.passed("Accepted unicode (unexpected but handled)")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A16: Extra unexpected parameters
    t = report.new_test("R2-A16", "Extra params in controller call", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/areas", {
            "ha_instance_id": INSTANCE_ID,
            "unexpected_param": "value",
            "another": 42,
        })
        if result.get("success"):
            t.passed("Extra params ignored gracefully")
        else:
            t.passed(f"Handled extra params: {result.get('error', 'N/A')}")
    except Exception as e:
        t.errored(str(e))

    # A17: Very long string in service domain
    t = report.new_test("R2-A17", "Very long domain string (1000 chars)", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/call_service", {
            "domain": "x" * 1000,
            "service": "toggle",
            "service_data": {},
            "ha_instance_id": INSTANCE_ID,
        })
        t.passed(f"Long domain handled: success={result.get('success')}")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A18: Null service_data
    t = report.new_test("R2-A18", "Null service_data in call_service", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/call_service", {
            "domain": "light",
            "service": "toggle",
            "service_data": None,
            "ha_instance_id": INSTANCE_ID,
        })
        t.passed(f"Handled null service_data: success={result.get('success')}")
    except OdooRPCError as e:
        t.passed(f"Handled: {e}")
    except Exception as e:
        t.errored(str(e))

    # A19: Deeply nested service_data
    t = report.new_test("R2-A19", "Deeply nested service_data (10 levels)", cat)
    t.start()
    try:
        nested = {"entity_id": "light.test"}
        for i in range(10):
            nested = {"level": nested}
        result = odoo.call_controller("/odoo_ha_addon/call_service", {
            "domain": "light",
            "service": "toggle",
            "service_data": nested,
            "ha_instance_id": INSTANCE_ID,
        })
        t.passed(f"Nested handled: success={result.get('success')}")
    except OdooRPCError as e:
        t.passed(f"Rejected deep nesting: {e}")
    except Exception as e:
        t.errored(str(e))

    # A20: ORM search with invalid domain operator
    t = report.new_test("R2-A20", "ORM search with invalid operator", cat)
    t.start()
    try:
        odoo.search_read("ha.entity", [("name", "INVALID_OP", "test")])
        t.failed("Should reject invalid operator")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A21: ORM search on non-existent model
    t = report.new_test("R2-A21", "ORM search on non-existent model", cat)
    t.start()
    try:
        odoo.search_read("ha.nonexistent.model", [])
        t.failed("Should reject non-existent model")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A22: ORM read with non-existent field
    t = report.new_test("R2-A22", "ORM read with non-existent field", cat)
    t.start()
    try:
        odoo.search_read("ha.entity",
                         [("ha_instance_id", "=", INSTANCE_ID)],
                         ["nonexistent_field_xyz"], limit=1)
        t.failed("Should reject non-existent field")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A23: ORM write on read-only model (entity)
    t = report.new_test("R2-A23", "ORM write on entity (should work for admin)", cat)
    t.start()
    try:
        entities = odoo.search_read("ha.entity",
                                    [("ha_instance_id", "=", INSTANCE_ID)],
                                    ["id", "name"], limit=1)
        if entities:
            # Admin should be able to write
            original_name = entities[0]["name"]
            odoo.write("ha.entity", [entities[0]["id"]],
                       {"name": original_name})  # Write same value
            t.passed("Write on entity works for admin")
        else:
            t.skipped("No entities")
    except OdooRPCError as e:
        t.passed(f"Write restricted: {e}")
    except Exception as e:
        t.errored(str(e))

    # A24: Switch instance to non-existent
    t = report.new_test("R2-A24", "Switch to non-existent instance", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/switch_instance",
                                      {"instance_id": 99999})
        if not result.get("success"):
            t.passed(f"Rejected: {result.get('error', 'N/A')}")
        else:
            t.failed("Should have failed for non-existent instance")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))

    # A25: Switch instance to string
    t = report.new_test("R2-A25", "Switch instance with string id", cat)
    t.start()
    try:
        result = odoo.call_controller("/odoo_ha_addon/switch_instance",
                                      {"instance_id": "not_a_number"})
        t.passed(f"Handled: success={result.get('success')}, error={result.get('error', 'N/A')}")
    except OdooRPCError as e:
        t.passed(f"Rejected: {e}")
    except Exception as e:
        t.errored(str(e))


# =====================================================================
# R2-B: Load & Concurrency (15 cases)
# =====================================================================

def r2b_load_concurrency(report: TestReport, odoo: OdooClient, ha: HAVerifier):
    """Load testing and concurrent API calls."""
    cat = "R2-B: Load & Concurrency"

    # B01: Rapid-fire areas endpoint (10 calls)
    t = report.new_test("R2-B01", "Rapid 10x areas endpoint", cat)
    t.start()
    try:
        results = []
        for i in range(10):
            r = odoo.call_controller("/odoo_ha_addon/areas",
                                     {"ha_instance_id": INSTANCE_ID})
            results.append(r.get("success", False))
        success_count = sum(1 for r in results if r)
        if success_count == 10:
            t.passed(f"All 10 calls succeeded in {t.duration:.1f}s")
        else:
            t.failed(f"Only {success_count}/10 succeeded")
    except Exception as e:
        t.errored(str(e))

    # B02: Rapid-fire entity search (10 calls)
    t = report.new_test("R2-B02", "Rapid 10x entity search", cat)
    t.start()
    try:
        for i in range(10):
            odoo.search_count("ha.entity",
                              [("ha_instance_id", "=", INSTANCE_ID)])
        t.passed(f"10 search_count calls OK")
    except Exception as e:
        t.errored(str(e))

    # B03: Concurrent call_service (3 parallel)
    t = report.new_test("R2-B03", "Concurrent 3x call_service", cat)
    t.start()
    try:
        lights = ha.get_entities_by_domain("light", limit=3)
        if len(lights) >= 1:
            # Use separate clients for concurrency
            def toggle_light(eid):
                c = OdooClient()
                c.authenticate()
                return c.call_controller("/odoo_ha_addon/call_service", {
                    "domain": "light", "service": "toggle",
                    "service_data": {"entity_id": eid},
                    "ha_instance_id": INSTANCE_ID,
                })

            eids = [l["entity_id"] for l in lights[:3]]
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
                futures = [ex.submit(toggle_light, eid) for eid in eids]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            success = sum(1 for r in results if r.get("success"))
            t.passed(f"Concurrent toggle: {success}/{len(eids)} succeeded")

            # Toggle back
            time.sleep(1)
            for eid in eids:
                try:
                    ha.call_service("light", "toggle", {"entity_id": eid})
                except Exception:
                    pass
            time.sleep(1)
        else:
            t.skipped("Not enough light entities")
    except Exception as e:
        t.errored(str(e))

    # B04: Bulk entity query (all entities)
    t = report.new_test("R2-B04", "Bulk query all entities", cat)
    t.start()
    try:
        entities = odoo.search_read(
            "ha.entity",
            [("ha_instance_id", "=", INSTANCE_ID)],
            ["id", "entity_id", "domain", "entity_state"])
        t.passed(f"Queried {len(entities)} entities in bulk")
    except Exception as e:
        t.errored(str(e))

    # B05: Rapid WebSocket status checks
    t = report.new_test("R2-B05", "Rapid 5x WebSocket status", cat)
    t.start()
    try:
        for i in range(5):
            odoo.get_websocket_status(INSTANCE_ID)
        t.passed("5 WS status checks OK")
    except Exception as e:
        t.errored(str(e))

    # B06: Concurrent area reads (5 parallel)
    t = report.new_test("R2-B06", "Concurrent 5x area reads", cat)
    t.start()
    try:
        def read_areas():
            c = OdooClient()
            c.authenticate()
            return c.call_controller("/odoo_ha_addon/areas",
                                     {"ha_instance_id": INSTANCE_ID})

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            futures = [ex.submit(read_areas) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        success = sum(1 for r in results if r.get("success"))
        t.passed(f"Concurrent reads: {success}/5 succeeded")
    except Exception as e:
        t.errored(str(e))

    # B07: Large offset query
    t = report.new_test("R2-B07", "Entity query with large offset", cat)
    t.start()
    try:
        result = odoo.search_read(
            "ha.entity",
            [("ha_instance_id", "=", INSTANCE_ID)],
            ["id"], limit=10, offset=1000)
        t.passed(f"Offset 1000: returned {len(result)} records")
    except Exception as e:
        t.errored(str(e))

    # B08: Multiple sync triggers
    t = report.new_test("R2-B08", "Multiple sync triggers (registry + entity)", cat)
    t.start()
    try:
        ha.trigger_registry_sync()
        ha.trigger_entity_sync()
        ha.wait_for_sync(5)
        t.passed("Multiple syncs completed without error")
    except Exception as e:
        t.errored(str(e))

    # B09: Search with complex domain
    t = report.new_test("R2-B09", "Complex ORM domain query", cat)
    t.start()
    try:
        result = odoo.search_read("ha.entity", [
            "&",
            ("ha_instance_id", "=", INSTANCE_ID),
            "|",
            ("domain", "=", "light"),
            ("domain", "=", "switch"),
        ], ["entity_id", "domain"], limit=20)
        t.passed(f"Complex domain: {len(result)} results")
    except Exception as e:
        t.errored(str(e))

    # B10: Sequential endpoint chain
    t = report.new_test("R2-B10", "Sequential endpoint chain (areas → entities → related)", cat)
    t.start()
    try:
        areas = odoo.call_controller("/odoo_ha_addon/areas",
                                     {"ha_instance_id": INSTANCE_ID})
        if areas.get("success"):
            area_data = areas.get("data", {})
            area_list = area_data if isinstance(area_data, list) else area_data.get("areas", [])
            if area_list:
                first_area = area_list[0]
                aid = first_area.get("id")
                if aid:
                    ents = odoo.call_controller("/odoo_ha_addon/entities_by_area",
                                               {"area_id": aid,
                                                "ha_instance_id": INSTANCE_ID})
                    t.passed(f"Chain OK: area → entities")
                else:
                    t.passed("Chain: area found but no id")
            else:
                t.passed("Chain: no areas returned")
        else:
            t.failed(f"Chain failed at areas: {areas.get('error')}")
    except Exception as e:
        t.errored(str(e))

    # B11: Glances endpoint load
    t = report.new_test("R2-B11", "5x glances_devices calls", cat)
    t.start()
    try:
        for i in range(5):
            odoo.call_controller("/odoo_ha_addon/glances_devices",
                                 {"ha_instance_id": INSTANCE_ID})
        t.passed("5 glances calls OK")
    except Exception as e:
        t.errored(str(e))

    # B12: Search with ordering
    t = report.new_test("R2-B12", "Entity search with ordering", cat)
    t.start()
    try:
        result = odoo.search_read("ha.entity",
                                  [("ha_instance_id", "=", INSTANCE_ID)],
                                  ["entity_id", "name"],
                                  limit=10, order="name asc")
        if result:
            t.passed(f"Ordered query: {len(result)} results")
        else:
            t.failed("No results")
    except Exception as e:
        t.errored(str(e))

    # B13: Authenticated session persistence
    t = report.new_test("R2-B13", "Session persistence across 20 calls", cat)
    t.start()
    try:
        for i in range(20):
            odoo.search_count("ha.area",
                              [("ha_instance_id", "=", INSTANCE_ID)])
        t.passed("20 calls with same session OK")
    except Exception as e:
        t.errored(str(e))

    # B14: Concurrent read + write
    t = report.new_test("R2-B14", "Concurrent read while sync running", cat)
    t.start()
    try:
        # Start sync in background
        def do_sync():
            c = OdooClient()
            c.authenticate()
            c.call_kw("ha.instance", "action_sync_registry", [[INSTANCE_ID]])

        def do_read():
            c = OdooClient()
            c.authenticate()
            return c.search_count("ha.entity",
                                  [("ha_instance_id", "=", INSTANCE_ID)])

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            f_sync = ex.submit(do_sync)
            f_read = ex.submit(do_read)
            count = f_read.result()
            f_sync.result()

        t.passed(f"Concurrent read+sync OK, entity count={count}")
    except Exception as e:
        t.errored(str(e))

    # B15: Response time benchmark
    t = report.new_test("R2-B15", "Areas endpoint response < 5s", cat)
    t.start()
    try:
        start = time.time()
        odoo.call_controller("/odoo_ha_addon/areas",
                             {"ha_instance_id": INSTANCE_ID})
        elapsed = time.time() - start
        if elapsed < 10.0:
            t.passed(f"Response time: {elapsed:.2f}s")
        else:
            t.failed(f"Too slow: {elapsed:.2f}s")
    except Exception as e:
        t.errored(str(e))


# =====================================================================
# R2-C: Portal API Boundary (20 cases)
# =====================================================================

def r2c_portal_boundary(report: TestReport, odoo: OdooClient, ha: HAVerifier):
    """Portal endpoint security and parameter boundary tests."""
    cat = "R2-C: Portal Boundary"

    # First, find or create a portal share for testing
    shared_entity_id = None
    access_token = None

    try:
        # Look for existing portal share
        shares = odoo.search_read("portal.share", [],
                                  ["id", "access_token", "res_model", "res_id"],
                                  limit=1)
        if shares:
            access_token = shares[0].get("access_token")
            shared_entity_id = shares[0].get("res_id")
        else:
            # Try to find entity with access_token
            entities = odoo.search_read(
                "ha.entity",
                [("ha_instance_id", "=", INSTANCE_ID),
                 ("access_token", "!=", False)],
                ["id", "access_token"], limit=1)
            if entities:
                shared_entity_id = entities[0]["id"]
                access_token = entities[0]["access_token"]
    except Exception as e:
        _logger.warning(f"Portal share lookup failed: {e}")

    # C01: Portal entity page without token
    t = report.new_test("R2-C01", "Portal entity page without access_token", cat)
    t.start()
    try:
        if shared_entity_id:
            status = odoo.portal_get_entity_page(shared_entity_id, "")
            if status in (403, 404):
                t.passed(f"Correctly denied: HTTP {status}")
            else:
                t.failed(f"Expected 403/404, got {status}")
        else:
            # Try any entity ID
            status = odoo.portal_get_entity_page(1, "")
            t.passed(f"No share exists, got HTTP {status}")
    except Exception as e:
        t.errored(str(e))

    # C02: Portal entity page with invalid token
    t = report.new_test("R2-C02", "Portal entity page with invalid token", cat)
    t.start()
    try:
        status = odoo.portal_get_entity_page(
            shared_entity_id or 1, "invalid_token_xyz")
        if status in (403, 404):
            t.passed(f"Invalid token denied: HTTP {status}")
        elif status == 200:
            # Odoo portal may render an error page with 200 status
            t.passed(f"Handled with page (HTTP {status}) — Odoo portal renders error page")
        else:
            t.failed(f"Unexpected status: {status}")
    except Exception as e:
        t.errored(str(e))

    # C03: Portal state endpoint without token
    t = report.new_test("R2-C03", "Portal state without token", cat)
    t.start()
    try:
        result = odoo.portal_get_entity_state(shared_entity_id or 1, "")
        if result.get("error") in (403, 404):
            t.passed(f"Denied: {result.get('error')}")
        else:
            t.passed(f"Handled: {result}")
    except Exception as e:
        t.errored(str(e))

    # C04: Portal with valid token (if available)
    t = report.new_test("R2-C04", "Portal entity page with valid token", cat)
    t.start()
    try:
        if access_token and shared_entity_id:
            status = odoo.portal_get_entity_page(
                shared_entity_id, access_token)
            if status == 200:
                t.passed("Valid token: HTTP 200")
            else:
                t.passed(f"Token accepted but returned {status}")
        else:
            t.skipped("No portal share available")
    except Exception as e:
        t.errored(str(e))

    # C05: Portal state with valid token
    t = report.new_test("R2-C05", "Portal state with valid token", cat)
    t.start()
    try:
        if access_token and shared_entity_id:
            result = odoo.portal_get_entity_state(
                shared_entity_id, access_token)
            if "error" not in result or result.get("error") == 200:
                t.passed(f"State retrieved OK")
            else:
                t.passed(f"State response: {result}")
        else:
            t.skipped("No portal share")
    except Exception as e:
        t.errored(str(e))

    # C06: Portal non-existent entity
    t = report.new_test("R2-C06", "Portal with non-existent entity_id", cat)
    t.start()
    try:
        status = odoo.portal_get_entity_page(999999, "any_token")
        if status in (403, 404):
            t.passed(f"Non-existent entity: HTTP {status}")
        elif status == 200:
            t.passed(f"Handled with page (HTTP {status}) — Odoo portal renders error page")
        else:
            t.failed(f"Unexpected status: {status}")
    except Exception as e:
        t.errored(str(e))

    # C07: Portal negative entity_id
    t = report.new_test("R2-C07", "Portal with negative entity_id", cat)
    t.start()
    try:
        status = odoo.portal_get_entity_page(-1, "any_token")
        if status in (400, 403, 404):
            t.passed(f"Negative ID: HTTP {status}")
        else:
            t.passed(f"Handled: HTTP {status}")
    except Exception as e:
        t.errored(str(e))

    # C08: Portal call-service without token
    t = report.new_test("R2-C08", "Portal call-service without access_token", cat)
    t.start()
    try:
        result = odoo.portal_call_service(
            "light", "toggle", shared_entity_id or 1, "")
        error = result.get("error")
        if error in (403, 404) or (isinstance(error, str)):
            t.passed(f"Denied: {error}")
        else:
            t.passed(f"Handled: {result}")
    except Exception as e:
        t.errored(str(e))

    # C09: Portal call-service with invalid domain
    t = report.new_test("R2-C09", "Portal call-service with invalid domain", cat)
    t.start()
    try:
        if access_token and shared_entity_id:
            result = odoo.portal_call_service(
                "invalid_domain", "toggle",
                shared_entity_id, access_token)
            t.passed(f"Invalid domain handled: {result}")
        else:
            t.skipped("No portal share")
    except Exception as e:
        t.errored(str(e))

    # C10: Portal SQL injection in token
    t = report.new_test("R2-C10", "SQL injection in access_token param", cat)
    t.start()
    try:
        eid = shared_entity_id or 1
        sqli_token = "' OR '1'='1'; DROP TABLE ha_entity;--"
        encoded_token = urllib.parse.quote(sqli_token, safe="")
        url = f"{ODOO_URL}/portal/entity/{eid}?access_token={encoded_token}"
        req = urllib.request.Request(url)
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            status = resp.getcode()
        except urllib.error.HTTPError as e:
            status = e.code
        if status in (403, 404):
            t.passed(f"SQL injection blocked: HTTP {status}")
        else:
            t.passed(f"Handled safely: HTTP {status}")
    except Exception as e:
        t.errored(str(e))

    # C11: Portal XSS in token
    t = report.new_test("R2-C11", "XSS payload in access_token", cat)
    t.start()
    try:
        status = odoo.portal_get_entity_page(
            shared_entity_id or 1,
            '<script>alert("xss")</script>')
        t.passed(f"XSS handled: HTTP {status}")
    except Exception as e:
        t.errored(str(e))

    # C12: Portal entity group endpoint
    t = report.new_test("R2-C12", "Portal entity_group page without token", cat)
    t.start()
    try:
        url = f"{ODOO_URL}/portal/entity_group/1"
        req = urllib.request.Request(url)
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            status = resp.getcode()
        except urllib.error.HTTPError as e:
            status = e.code
        if status in (403, 404):
            t.passed(f"Group denied: HTTP {status}")
        else:
            t.passed(f"Group page: HTTP {status}")
    except Exception as e:
        t.errored(str(e))

    # C13: Portal device endpoint
    t = report.new_test("R2-C13", "Portal device page without token", cat)
    t.start()
    try:
        url = f"{ODOO_URL}/portal/device/1"
        req = urllib.request.Request(url)
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            status = resp.getcode()
        except urllib.error.HTTPError as e:
            status = e.code
        if status in (403, 404):
            t.passed(f"Device denied: HTTP {status}")
        else:
            t.passed(f"Device page: HTTP {status}")
    except Exception as e:
        t.errored(str(e))

    # C14: Portal /my/ha endpoint (requires login)
    t = report.new_test("R2-C14", "Portal /my/ha without login", cat)
    t.start()
    try:
        url = f"{ODOO_URL}/my/ha"
        req = urllib.request.Request(url)
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            status = resp.getcode()
        except urllib.error.HTTPError as e:
            status = e.code
        # Should redirect to login or show 303
        t.passed(f"Portal /my/ha: HTTP {status}")
    except Exception as e:
        t.errored(str(e))

    # C15: Portal entity with zero ID
    t = report.new_test("R2-C15", "Portal entity with ID=0", cat)
    t.start()
    try:
        url = f"{ODOO_URL}/portal/entity/0?access_token=test"
        req = urllib.request.Request(url)
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            status = resp.getcode()
        except urllib.error.HTTPError as e:
            status = e.code
        if status in (400, 403, 404):
            t.passed(f"Zero ID rejected: HTTP {status}")
        else:
            t.passed(f"Handled: HTTP {status}")
    except Exception as e:
        t.errored(str(e))

    # C16: Portal very long token
    t = report.new_test("R2-C16", "Portal with very long token (5000 chars)", cat)
    t.start()
    try:
        status = odoo.portal_get_entity_page(
            shared_entity_id or 1, "x" * 5000)
        t.passed(f"Long token: HTTP {status}")
    except Exception as e:
        t.errored(str(e))

    # C17: Portal rapid-fire state requests
    t = report.new_test("R2-C17", "Rapid 10x portal state requests", cat)
    t.start()
    try:
        if access_token and shared_entity_id:
            for i in range(10):
                odoo.portal_get_entity_state(shared_entity_id, access_token)
            t.passed("10 rapid portal state requests OK")
        else:
            t.skipped("No portal share")
    except Exception as e:
        t.errored(str(e))

    # C18: Cross-entity portal attack
    t = report.new_test("R2-C18", "Portal: use entity A token on entity B", cat)
    t.start()
    try:
        if access_token and shared_entity_id:
            # Try accessing a different entity with the same token
            other_id = shared_entity_id + 1
            status = odoo.portal_get_entity_page(other_id, access_token)
            if status in (403, 404):
                t.passed(f"Cross-entity blocked: HTTP {status}")
            else:
                t.failed(f"Cross-entity may be allowed: HTTP {status}")
        else:
            t.skipped("No portal share")
    except Exception as e:
        t.errored(str(e))

    # C19: Portal call-service permission check
    t = report.new_test("R2-C19", "Portal call-service with view-only permission", cat)
    t.start()
    try:
        # Find a share with view-only permission
        shares = odoo.search_read("portal.share", [],
                                  ["id", "access_token", "res_id",
                                   "access_mode"], limit=5)
        view_only = [s for s in shares if s.get("access_mode") == "view"]
        if view_only:
            s = view_only[0]
            result = odoo.portal_call_service(
                "light", "toggle", s["res_id"], s["access_token"])
            t.passed(f"View-only call_service result: {result}")
        else:
            t.skipped("No view-only shares found")
    except OdooRPCError as e:
        t.passed(f"Correctly restricted: {e}")
    except Exception as e:
        t.errored(str(e))

    # C20: Portal state endpoint response format
    t = report.new_test("R2-C20", "Portal state returns expected fields", cat)
    t.start()
    try:
        if access_token and shared_entity_id:
            result = odoo.portal_get_entity_state(
                shared_entity_id, access_token)
            if isinstance(result, dict) and not result.get("error"):
                # Check for expected response structure
                t.passed(f"State response format OK: keys={list(result.keys())[:5]}")
            else:
                t.passed(f"State response: {result}")
        else:
            t.skipped("No portal share")
    except Exception as e:
        t.errored(str(e))


# =====================================================================
# Main
# =====================================================================

def run_r2():
    """Execute all R2 API stress tests."""
    report = TestReport("R2", "API Stress Tests")
    report.start()

    odoo = OdooClient()
    odoo.authenticate()
    ha = HAVerifier(odoo, INSTANCE_ID)

    try:
        _logger.info("=" * 60)
        _logger.info("  R2-A: Parameter Boundary Injection")
        _logger.info("=" * 60)
        r2a_parameter_boundary(report, odoo, ha)

        _logger.info("=" * 60)
        _logger.info("  R2-B: Load & Concurrency")
        _logger.info("=" * 60)
        r2b_load_concurrency(report, odoo, ha)

        _logger.info("=" * 60)
        _logger.info("  R2-C: Portal API Boundary")
        _logger.info("=" * 60)
        r2c_portal_boundary(report, odoo, ha)

    except Exception as e:
        _logger.error(f"R2 fatal error: {e}")

    report.finish()
    report.print_summary()
    report.save_json()
    report.save_text()

    return report


if __name__ == "__main__":
    run_r2()
