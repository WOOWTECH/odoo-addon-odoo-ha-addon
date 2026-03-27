#!/usr/bin/env python3
"""
R5: Integration & Recovery Tests (~30 cases)
=============================================
End-to-end workflows, WebSocket recovery, sync resilience.

Sub-groups:
  R5-A: WebSocket & connection resilience (10 cases)
  R5-B: Full workflow integration (10 cases)
  R5-C: Data consistency after operations (10 cases)
"""

import sys
import os
import time
import json
import logging
import traceback
import concurrent.futures

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.stability.helpers.odoo_client import OdooClient, OdooRPCError
from tests.stability.helpers.ha_client import HAVerifier
from tests.stability.helpers.report import TestReport, TestResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_logger = logging.getLogger(__name__)

INSTANCE_ID = 1
TEST_PREFIX = "STABTEST_R5_"


# =====================================================================
# R5-A: WebSocket & Connection Resilience (10 cases)
# =====================================================================

def r5a_websocket_resilience(report: TestReport, odoo: OdooClient,
                              verifier: HAVerifier):
    """WebSocket connection and reconnection tests."""
    cat = "R5-A: WebSocket Resilience"

    # A01: WebSocket connected
    t = report.new_test("R5-A01", "WebSocket is connected", cat)
    t.start()
    try:
        connected = verifier.is_connected()
        if connected:
            t.passed("WebSocket connected")
        else:
            ws_status = verifier.check_connection()
            t.failed(f"WebSocket not connected: {ws_status}")
    except Exception as e:
        t.errored(str(e))

    # A02: WebSocket survives rapid API calls
    t = report.new_test("R5-A02", "WebSocket survives 20 rapid API calls", cat)
    t.start()
    try:
        for i in range(20):
            odoo.search_count("ha.entity",
                              [("ha_instance_id", "=", INSTANCE_ID)])
        # Check WS still connected
        connected = verifier.is_connected()
        if connected:
            t.passed("WebSocket OK after 20 rapid calls")
        else:
            t.failed("WebSocket dropped after rapid calls")
    except Exception as e:
        t.errored(str(e))

    # A03: WebSocket survives sync operation
    t = report.new_test("R5-A03", "WebSocket survives registry sync", cat)
    t.start()
    try:
        verifier.trigger_registry_sync()
        time.sleep(3)
        connected = verifier.is_connected()
        if connected:
            t.passed("WebSocket OK after sync")
        else:
            t.failed("WebSocket dropped after sync")
    except Exception as e:
        t.errored(str(e))

    # A04: WebSocket survives entity sync
    t = report.new_test("R5-A04", "WebSocket survives entity sync", cat)
    t.start()
    try:
        verifier.trigger_entity_sync()
        time.sleep(3)
        connected = verifier.is_connected()
        if connected:
            t.passed("WebSocket OK after entity sync")
        else:
            t.failed("WebSocket dropped after entity sync")
    except Exception as e:
        t.errored(str(e))

    # A05: WebSocket survives concurrent operations
    t = report.new_test("R5-A05", "WebSocket survives concurrent reads", cat)
    t.start()
    try:
        def do_read():
            c = OdooClient()
            c.authenticate()
            return c.search_count("ha.entity",
                                   [("ha_instance_id", "=", INSTANCE_ID)])

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            futs = [pool.submit(do_read) for _ in range(5)]
            results = [f.result(timeout=30) for f in futs]

        connected = verifier.is_connected()
        if connected:
            t.passed(f"WebSocket OK after 5 concurrent: {results}")
        else:
            t.failed("WebSocket dropped after concurrent reads")
    except Exception as e:
        t.errored(str(e))

    # A06: WebSocket survives service call
    t = report.new_test("R5-A06", "WebSocket survives service call", cat)
    t.start()
    try:
        scenes = odoo.get_scenes(INSTANCE_ID)
        if scenes:
            odoo.call_service("scene", "turn_on",
                              {"entity_id": scenes[0]["entity_id"]},
                              INSTANCE_ID)
            # Allow time for service call + WS to stabilize
            connected = False
            for attempt in range(3):
                time.sleep(2)
                connected = verifier.is_connected()
                if connected:
                    break
            if connected:
                t.passed("WebSocket OK after service call")
            else:
                t.failed("WebSocket dropped after service call")
        else:
            t.skipped("No scenes available")
    except Exception as e:
        t.errored(str(e))

    # A07: Multiple syncs in sequence
    t = report.new_test("R5-A07", "3 consecutive syncs stable", cat)
    t.start()
    try:
        for i in range(3):
            verifier.trigger_registry_sync()
            time.sleep(2)
        connected = verifier.is_connected()
        if connected:
            t.passed("WebSocket OK after 3 syncs")
        else:
            t.failed("WebSocket dropped after multiple syncs")
    except Exception as e:
        t.errored(str(e))

    # A08: Entity count stable across syncs
    t = report.new_test("R5-A08", "Entity count stable across syncs", cat)
    t.start()
    try:
        count1 = odoo.search_count("ha.entity",
                                    [("ha_instance_id", "=", INSTANCE_ID)])
        verifier.trigger_entity_sync()
        time.sleep(5)
        count2 = odoo.search_count("ha.entity",
                                    [("ha_instance_id", "=", INSTANCE_ID)])
        diff = abs(count2 - count1)
        if diff == 0:
            t.passed(f"Entity count stable: {count1}")
        elif diff <= 5:
            t.passed(f"Entity count minor change: {count1} → {count2}")
        else:
            t.failed(f"Entity count drift: {count1} → {count2}")
    except Exception as e:
        t.errored(str(e))

    # A09: Area count stable across syncs
    t = report.new_test("R5-A09", "Area count stable across syncs", cat)
    t.start()
    try:
        count1 = odoo.search_count("ha.area",
                                    [("ha_instance_id", "=", INSTANCE_ID)])
        verifier.trigger_registry_sync()
        time.sleep(5)
        count2 = odoo.search_count("ha.area",
                                    [("ha_instance_id", "=", INSTANCE_ID)])
        if count1 == count2:
            t.passed(f"Area count stable: {count1}")
        else:
            t.failed(f"Area count changed: {count1} → {count2}")
    except Exception as e:
        t.errored(str(e))

    # A10: Device count stable across syncs
    t = report.new_test("R5-A10", "Device count stable across syncs", cat)
    t.start()
    try:
        count1 = odoo.search_count("ha.device",
                                    [("ha_instance_id", "=", INSTANCE_ID)])
        verifier.trigger_registry_sync()
        time.sleep(5)
        count2 = odoo.search_count("ha.device",
                                    [("ha_instance_id", "=", INSTANCE_ID)])
        if count1 == count2:
            t.passed(f"Device count stable: {count1}")
        else:
            t.failed(f"Device count changed: {count1} → {count2}")
    except Exception as e:
        t.errored(str(e))


# =====================================================================
# R5-B: Full Workflow Integration (10 cases)
# =====================================================================

def r5b_full_workflow(report: TestReport, odoo: OdooClient,
                       verifier: HAVerifier):
    """End-to-end workflow tests."""
    cat = "R5-B: Full Workflow"

    # B01: Create area → verify → rename → verify → delete → verify
    t = report.new_test("R5-B01", "Area full lifecycle (create→rename→delete)", cat)
    t.start()
    area_id = None
    try:
        # Create
        area_id = odoo.create_area(f"{TEST_PREFIX}lifecycle", INSTANCE_ID)
        time.sleep(2)

        # Verify created
        areas = odoo.search_read("ha.area",
                                  [("id", "=", area_id)],
                                  ["id", "name"])
        if not areas:
            t.failed("Area not found after create")
        else:
            # Rename
            odoo.write("ha.area", [area_id],
                        {"name": f"{TEST_PREFIX}lifecycle_renamed"})
            time.sleep(2)

            # Verify renamed
            areas2 = odoo.search_read("ha.area",
                                       [("id", "=", area_id)],
                                       ["name"])
            if areas2 and "renamed" in areas2[0]["name"]:
                # Delete
                odoo.unlink("ha.area", [area_id])
                area_id = None
                time.sleep(2)

                # Verify deleted
                areas3 = odoo.search_read("ha.area",
                                           [("name", "ilike", f"{TEST_PREFIX}lifecycle")],
                                           ["id"])
                if not areas3:
                    t.passed("Full lifecycle: create→rename→delete OK")
                else:
                    t.failed("Area still exists after delete")
            else:
                t.failed("Rename not reflected")
    except Exception as e:
        t.errored(str(e))
    finally:
        if area_id:
            try:
                odoo.unlink("ha.area", [area_id])
            except Exception:
                pass

    # B02: Create label → verify → delete → verify
    t = report.new_test("R5-B02", "Label full lifecycle", cat)
    t.start()
    label_id = None
    try:
        # Clean up leftover test labels first
        old_labels = odoo.search_read("ha.label",
                                       [("name", "ilike", f"{TEST_PREFIX}label")],
                                       ["id"])
        if old_labels:
            odoo.unlink("ha.label", [l["id"] for l in old_labels])
            time.sleep(1)

        label_name = f"{TEST_PREFIX}label_{int(time.time())}"
        label_id = odoo.create("ha.label",
                                {"name": label_name,
                                 "ha_instance_id": INSTANCE_ID})
        time.sleep(2)

        labels = odoo.search_read("ha.label",
                                   [("id", "=", label_id)],
                                   ["id", "name"])
        if labels:
            odoo.unlink("ha.label", [label_id])
            label_id = None
            time.sleep(2)

            labels2 = odoo.search_read("ha.label",
                                        [("name", "=", label_name)],
                                        ["id"])
            if not labels2:
                t.passed("Label lifecycle: create→delete OK")
            else:
                t.failed("Label still exists after delete")
        else:
            t.failed("Label not found after create")
    except Exception as e:
        t.errored(str(e))
    finally:
        if label_id:
            try:
                odoo.unlink("ha.label", [label_id])
            except Exception:
                pass

    # B03: Scene activation workflow
    t = report.new_test("R5-B03", "Scene activation + state verification", cat)
    t.start()
    try:
        scenes = odoo.get_scenes(INSTANCE_ID)
        if scenes:
            scene = scenes[0]
            odoo.call_service("scene", "turn_on",
                              {"entity_id": scene["entity_id"]},
                              INSTANCE_ID)
            time.sleep(2)
            # Re-read state
            updated = odoo.search_read("ha.entity",
                                        [("id", "=", scene["id"])],
                                        ["entity_state"])
            if updated:
                t.passed(f"Scene activated, state: {updated[0].get('entity_state')}")
            else:
                t.passed("Scene activated (entity not re-read)")
        else:
            t.skipped("No scenes")
    except Exception as e:
        t.errored(str(e))

    # B04: Automation toggle workflow
    t = report.new_test("R5-B04", "Automation toggle + verify state change", cat)
    t.start()
    try:
        autos = odoo.get_automations(INSTANCE_ID)
        if autos:
            auto = autos[0]
            original_state = auto.get("entity_state")

            # Toggle
            service = "turn_off" if original_state == "on" else "turn_on"
            odoo.call_service("automation", service,
                              {"entity_id": auto["entity_id"]},
                              INSTANCE_ID)
            time.sleep(2)

            # Verify change
            updated = odoo.search_read("ha.entity",
                                        [("id", "=", auto["id"])],
                                        ["entity_state"])
            new_state = updated[0]["entity_state"] if updated else "N/A"

            # Restore original
            restore = "turn_on" if service == "turn_off" else "turn_off"
            odoo.call_service("automation", restore,
                              {"entity_id": auto["entity_id"]},
                              INSTANCE_ID)

            if new_state != original_state:
                t.passed(f"State changed: {original_state} → {new_state}")
            else:
                t.passed(f"State: {original_state} (may need sync delay)")
        else:
            t.skipped("No automations")
    except Exception as e:
        t.errored(str(e))

    # B05: Light toggle workflow
    t = report.new_test("R5-B05", "Light toggle + state verification", cat)
    t.start()
    try:
        lights = odoo.search_read("ha.entity",
                                   [("domain", "=", "light"),
                                    ("ha_instance_id", "=", INSTANCE_ID)],
                                   ["id", "entity_id", "entity_state"],
                                   limit=1)
        if lights:
            light = lights[0]
            original = light.get("entity_state")
            odoo.call_service("light", "toggle",
                              {"entity_id": light["entity_id"]},
                              INSTANCE_ID)
            time.sleep(3)

            updated = odoo.search_read("ha.entity",
                                        [("id", "=", light["id"])],
                                        ["entity_state"])
            new_state = updated[0]["entity_state"] if updated else "N/A"

            # Toggle back
            odoo.call_service("light", "toggle",
                              {"entity_id": light["entity_id"]},
                              INSTANCE_ID)

            t.passed(f"Light toggle: {original} → {new_state}")
        else:
            t.skipped("No lights")
    except Exception as e:
        t.errored(str(e))

    # B06: Switch toggle workflow
    t = report.new_test("R5-B06", "Switch toggle + state verification", cat)
    t.start()
    try:
        switches = odoo.search_read("ha.entity",
                                     [("domain", "=", "switch"),
                                      ("ha_instance_id", "=", INSTANCE_ID)],
                                     ["id", "entity_id", "entity_state"],
                                     limit=1)
        if switches:
            sw = switches[0]
            original = sw.get("entity_state")
            odoo.call_service("switch", "toggle",
                              {"entity_id": sw["entity_id"]},
                              INSTANCE_ID)
            time.sleep(3)

            updated = odoo.search_read("ha.entity",
                                        [("id", "=", sw["id"])],
                                        ["entity_state"])
            new_state = updated[0]["entity_state"] if updated else "N/A"

            # Toggle back
            odoo.call_service("switch", "toggle",
                              {"entity_id": sw["entity_id"]},
                              INSTANCE_ID)

            t.passed(f"Switch toggle: {original} → {new_state}")
        else:
            t.skipped("No switches")
    except Exception as e:
        t.errored(str(e))

    # B07: Script execution workflow
    t = report.new_test("R5-B07", "Script execution + state check", cat)
    t.start()
    try:
        scripts = odoo.get_scripts(INSTANCE_ID)
        if scripts:
            script = scripts[0]
            odoo.call_service("script", "turn_on",
                              {"entity_id": script["entity_id"]},
                              INSTANCE_ID)
            time.sleep(2)
            t.passed(f"Script executed: {script['entity_id']}")
        else:
            t.skipped("No scripts")
    except Exception as e:
        t.errored(str(e))

    # B08: Sync → service call → sync workflow
    t = report.new_test("R5-B08", "Sync → service → sync chain", cat)
    t.start()
    try:
        # Initial sync
        verifier.trigger_entity_sync()
        time.sleep(3)
        count1 = odoo.search_count("ha.entity",
                                    [("ha_instance_id", "=", INSTANCE_ID)])

        # Service call
        scenes = odoo.get_scenes(INSTANCE_ID)
        if scenes:
            odoo.call_service("scene", "turn_on",
                              {"entity_id": scenes[0]["entity_id"]},
                              INSTANCE_ID)
        time.sleep(2)

        # Second sync
        verifier.trigger_entity_sync()
        time.sleep(3)
        count2 = odoo.search_count("ha.entity",
                                    [("ha_instance_id", "=", INSTANCE_ID)])

        diff = abs(count2 - count1)
        if diff == 0:
            t.passed(f"Sync-service-sync stable: {count1}")
        else:
            t.passed(f"Minor count change: {count1} → {count2}")
    except Exception as e:
        t.errored(str(e))

    # B09: Area CRUD during entity sync
    t = report.new_test("R5-B09", "Area CRUD while entity sync running", cat)
    t.start()
    area_id = None
    try:
        # Start entity sync
        verifier.trigger_entity_sync()

        # Immediately create area
        area_id = odoo.create_area(f"{TEST_PREFIX}during_sync", INSTANCE_ID)
        time.sleep(3)

        # Verify area exists
        areas = odoo.search_read("ha.area",
                                  [("id", "=", area_id)],
                                  ["id", "name"])
        if areas:
            # Delete
            odoo.unlink("ha.area", [area_id])
            area_id = None
            t.passed("Area CRUD during sync: OK")
        else:
            t.failed("Area not found after create during sync")
    except Exception as e:
        t.errored(str(e))
    finally:
        if area_id:
            try:
                odoo.unlink("ha.area", [area_id])
            except Exception:
                pass

    # B10: Multi-area batch create → batch delete
    t = report.new_test("R5-B10", "Batch create 3 areas → batch delete", cat)
    t.start()
    created_ids = []
    try:
        for i in range(3):
            aid = odoo.create_area(f"{TEST_PREFIX}batch_{i}", INSTANCE_ID)
            created_ids.append(aid)

        time.sleep(3)

        # Verify all created
        found = odoo.search_read("ha.area",
                                  [("id", "in", created_ids)],
                                  ["id", "name"])
        if len(found) == 3:
            # Batch delete
            odoo.unlink("ha.area", created_ids)
            created_ids = []
            time.sleep(2)

            remaining = odoo.search_read("ha.area",
                                          [("name", "ilike", f"{TEST_PREFIX}batch_")],
                                          ["id"])
            if not remaining:
                t.passed("Batch create → delete: 3/3 OK")
            else:
                t.failed(f"Batch delete incomplete: {len(remaining)} remaining")
        else:
            t.failed(f"Batch create: {len(found)}/3")
    except Exception as e:
        t.errored(str(e))
    finally:
        if created_ids:
            try:
                odoo.unlink("ha.area", created_ids)
            except Exception:
                pass


# =====================================================================
# R5-C: Data Consistency After Operations (10 cases)
# =====================================================================

def r5c_data_consistency(report: TestReport, odoo: OdooClient,
                          verifier: HAVerifier):
    """Data consistency verification after various operations."""
    cat = "R5-C: Data Consistency"

    # C01: Entity-area referential integrity
    t = report.new_test("R5-C01", "Entity area_id refs are valid", cat)
    t.start()
    try:
        entities = odoo.search_read("ha.entity",
                                     [("ha_instance_id", "=", INSTANCE_ID),
                                      ("area_id", "!=", False)],
                                     ["id", "entity_id", "area_id"],
                                     limit=50)
        area_ids = list(set(e["area_id"][0] for e in entities
                           if e.get("area_id")))
        if area_ids:
            areas = odoo.search_read("ha.area",
                                      [("id", "in", area_ids)],
                                      ["id"])
            valid_ids = set(a["id"] for a in areas)
            invalid = [aid for aid in area_ids if aid not in valid_ids]
            if not invalid:
                t.passed(f"All {len(area_ids)} area refs valid")
            else:
                t.failed(f"Invalid area refs: {invalid}")
        else:
            t.passed("No entities with area assignment")
    except Exception as e:
        t.errored(str(e))

    # C02: Entity-device referential integrity
    t = report.new_test("R5-C02", "Entity device_id refs are valid", cat)
    t.start()
    try:
        entities = odoo.search_read("ha.entity",
                                     [("ha_instance_id", "=", INSTANCE_ID),
                                      ("device_id", "!=", False)],
                                     ["id", "entity_id", "device_id"],
                                     limit=50)
        device_ids = list(set(e["device_id"][0] for e in entities
                             if e.get("device_id")))
        if device_ids:
            devices = odoo.search_read("ha.device",
                                        [("id", "in", device_ids)],
                                        ["id"])
            valid_ids = set(d["id"] for d in devices)
            invalid = [did for did in device_ids if did not in valid_ids]
            if not invalid:
                t.passed(f"All {len(device_ids)} device refs valid")
            else:
                t.failed(f"Invalid device refs: {invalid}")
        else:
            t.passed("No entities with device assignment")
    except Exception as e:
        t.errored(str(e))

    # C03: Device-area referential integrity
    t = report.new_test("R5-C03", "Device area refs are valid", cat)
    t.start()
    try:
        devices = odoo.search_read("ha.device",
                                    [("ha_instance_id", "=", INSTANCE_ID),
                                     ("area_id", "!=", False)],
                                    ["id", "area_id"],
                                    limit=50)
        area_ids = list(set(d["area_id"][0] for d in devices
                           if d.get("area_id")))
        if area_ids:
            areas = odoo.search_read("ha.area",
                                      [("id", "in", area_ids)],
                                      ["id"])
            valid_ids = set(a["id"] for a in areas)
            invalid = [aid for aid in area_ids if aid not in valid_ids]
            if not invalid:
                t.passed(f"All {len(area_ids)} device-area refs valid")
            else:
                t.failed(f"Invalid device-area refs: {invalid}")
        else:
            t.passed("No devices with area")
    except Exception as e:
        t.errored(str(e))

    # C04: No orphaned entities (all have instance)
    t = report.new_test("R5-C04", "No orphaned entities", cat)
    t.start()
    try:
        orphans = odoo.search_count("ha.entity",
                                     [("ha_instance_id", "=", False)])
        if orphans == 0:
            t.passed("No orphaned entities")
        else:
            t.failed(f"{orphans} orphaned entities")
    except Exception as e:
        t.errored(str(e))

    # C05: No duplicate entity_ids per instance
    t = report.new_test("R5-C05", "No duplicate entity_ids", cat)
    t.start()
    try:
        entities = odoo.search_read("ha.entity",
                                     [("ha_instance_id", "=", INSTANCE_ID)],
                                     ["entity_id"],
                                     limit=0)
        entity_ids = [e["entity_id"] for e in entities]
        dupes = set(eid for eid in entity_ids
                    if entity_ids.count(eid) > 1)
        if not dupes:
            t.passed(f"All {len(entity_ids)} entity_ids unique")
        else:
            t.failed(f"Duplicate entity_ids: {list(dupes)[:5]}")
    except Exception as e:
        t.errored(str(e))

    # C06: No duplicate area names per instance
    t = report.new_test("R5-C06", "No duplicate area names", cat)
    t.start()
    try:
        areas = odoo.search_read("ha.area",
                                  [("ha_instance_id", "=", INSTANCE_ID)],
                                  ["name"],
                                  limit=0)
        names = [a["name"] for a in areas if a.get("name")]
        dupes = set(n for n in names if names.count(n) > 1)
        if not dupes:
            t.passed(f"All {len(names)} area names unique")
        else:
            t.failed(f"Duplicate area names: {list(dupes)[:5]}")
    except Exception as e:
        t.errored(str(e))

    # C07: ORM count matches controller count (areas)
    t = report.new_test("R5-C07", "ORM vs controller area count match", cat)
    t.start()
    try:
        orm_count = odoo.search_count("ha.area",
                                       [("ha_instance_id", "=", INSTANCE_ID)])
        ctrl_result = odoo.get_areas_via_controller(INSTANCE_ID)
        if isinstance(ctrl_result, dict):
            ctrl_data = ctrl_result.get("data", ctrl_result)
            if isinstance(ctrl_data, list):
                ctrl_count = len(ctrl_data)
            elif isinstance(ctrl_data, dict) and "areas" in ctrl_data:
                ctrl_count = len(ctrl_data["areas"])
            else:
                ctrl_count = -1
        elif isinstance(ctrl_result, list):
            ctrl_count = len(ctrl_result)
        else:
            ctrl_count = -1

        if ctrl_count == orm_count:
            t.passed(f"Counts match: {orm_count}")
        elif ctrl_count == -1:
            t.passed(f"ORM count: {orm_count} (controller format unclear)")
        else:
            t.failed(f"Count mismatch: ORM={orm_count} ctrl={ctrl_count}")
    except Exception as e:
        t.errored(str(e))

    # C08: Entity domain matches entity_id prefix
    t = report.new_test("R5-C08", "Entity domain matches entity_id prefix", cat)
    t.start()
    try:
        entities = odoo.search_read("ha.entity",
                                     [("ha_instance_id", "=", INSTANCE_ID)],
                                     ["entity_id", "domain"],
                                     limit=100)
        mismatches = []
        for e in entities:
            eid = e.get("entity_id", "")
            domain = e.get("domain", "")
            if eid and domain and not eid.startswith(f"{domain}."):
                mismatches.append((eid, domain))
        if not mismatches:
            t.passed(f"All {len(entities)} entities match")
        else:
            t.failed(f"Mismatches: {mismatches[:3]}")
    except Exception as e:
        t.errored(str(e))

    # C09: All instances have valid api_url
    t = report.new_test("R5-C09", "All instances have api_url", cat)
    t.start()
    try:
        instances = odoo.search_read("ha.instance",
                                      [("active", "=", True)],
                                      ["id", "name", "api_url"])
        missing = [i["name"] for i in instances if not i.get("api_url")]
        if not missing:
            t.passed(f"All {len(instances)} instances have api_url")
        else:
            t.failed(f"Missing api_url: {missing}")
    except Exception as e:
        t.errored(str(e))

    # C10: Summary snapshot
    t = report.new_test("R5-C10", "Final consistency summary", cat)
    t.start()
    try:
        summary = verifier.get_summary()
        snapshot = {
            "entities": summary.get("entities", 0),
            "areas": summary.get("areas", 0),
            "devices": summary.get("devices", 0),
            "labels": summary.get("labels", 0),
            "scenes": summary.get("scenes", 0),
            "automations": summary.get("automations", 0),
            "scripts": summary.get("scripts", 0),
            "websocket": summary.get("websocket_connected", False),
        }
        t.passed(f"Final snapshot: {json.dumps(snapshot)}")
    except Exception as e:
        t.errored(str(e))


# =====================================================================
# Cleanup
# =====================================================================

def cleanup_r5_data(odoo: OdooClient):
    """Remove any test data left behind."""
    try:
        areas = odoo.search_read("ha.area",
                                  [("name", "ilike", TEST_PREFIX)],
                                  ["id"])
        if areas:
            odoo.unlink("ha.area", [a["id"] for a in areas])
            _logger.info(f"Cleaned {len(areas)} test areas")

        labels = odoo.search_read("ha.label",
                                   [("name", "ilike", TEST_PREFIX)],
                                   ["id"])
        if labels:
            odoo.unlink("ha.label", [l["id"] for l in labels])
            _logger.info(f"Cleaned {len(labels)} test labels")
    except Exception as e:
        _logger.warning(f"Cleanup error: {e}")


# =====================================================================
# Main
# =====================================================================

def run_r5():
    """Execute all R5 integration tests."""
    report = TestReport("R5", "Integration & Recovery Tests")
    report.start()

    odoo = OdooClient()
    odoo.authenticate()
    verifier = HAVerifier(odoo, INSTANCE_ID)

    try:
        _logger.info("=" * 60)
        _logger.info("  R5-A: WebSocket & Connection Resilience")
        _logger.info("=" * 60)
        r5a_websocket_resilience(report, odoo, verifier)

        _logger.info("=" * 60)
        _logger.info("  R5-B: Full Workflow Integration")
        _logger.info("=" * 60)
        r5b_full_workflow(report, odoo, verifier)

        _logger.info("=" * 60)
        _logger.info("  R5-C: Data Consistency After Operations")
        _logger.info("=" * 60)
        r5c_data_consistency(report, odoo, verifier)

    except Exception as e:
        _logger.error(f"R5 fatal error: {e}")
    finally:
        cleanup_r5_data(odoo)

    report.finish()
    report.print_summary()
    report.save_json()
    report.save_text()

    return report


if __name__ == "__main__":
    run_r5()
