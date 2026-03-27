"""
Home Assistant Verification Client for Stability Testing

Since the HA REST API is behind Cloudflare and not directly accessible,
this client verifies HA-side data by:
1. Calling Odoo controller endpoints that proxy to HA via WebSocket
2. Using Odoo ORM to read synced HA data (which reflects HA state)
3. Using ha.instance model methods that internally call HA WebSocket API

Triple-check verification layers:
1. Odoo ORM (direct model reads)
2. Odoo Controller (JSON-RPC endpoints that call HA internally)
3. HA WebSocket via Odoo (model methods that use WebSocket client)
"""

import json
import logging
import time
from typing import Any, Optional

_logger = logging.getLogger(__name__)


class HAVerifier:
    """
    HA data verification via Odoo's WebSocket proxy layer.

    This replaces direct HA REST API calls since the HA instance
    is behind Cloudflare. All verification goes through Odoo which
    has an active WebSocket connection to HA.
    """

    def __init__(self, odoo_client, instance_id: int = 1):
        """
        Args:
            odoo_client: An authenticated OdooClient instance
            instance_id: The HA instance ID in Odoo (default: 1)
        """
        self.odoo = odoo_client
        self.instance_id = instance_id

    # ------------------------------------------------------------------
    # Connection verification
    # ------------------------------------------------------------------

    def check_connection(self) -> dict:
        """Verify HA connection via WebSocket status."""
        return self.odoo.get_websocket_status(self.instance_id)

    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        status = self.check_connection()
        if status.get("success"):
            data = status.get("data", {})
            return data.get("is_running", False)
        return False

    # ------------------------------------------------------------------
    # Area verification
    # ------------------------------------------------------------------

    def get_areas_from_odoo(self) -> list:
        """Get areas as synced in Odoo (reflects HA state)."""
        return self.odoo.get_areas(self.instance_id)

    def get_areas_via_controller(self) -> list:
        """Get areas via controller (internally queries HA)."""
        result = self.odoo.get_areas_via_controller(self.instance_id)
        if result.get("success"):
            data = result.get("data", {})
            return data if isinstance(data, list) else data.get("areas", [])
        return []

    def find_area_in_odoo(self, name: str = None,
                          area_id: str = None) -> Optional[dict]:
        """Find a specific area in Odoo by name or area_id."""
        domain = [("ha_instance_id", "=", self.instance_id)]
        if name:
            domain.append(("name", "=", name))
        if area_id:
            domain.append(("area_id", "=", area_id))
        results = self.odoo.search_read("ha.area", domain,
                                        ["id", "area_id", "name",
                                         "ha_instance_id", "entity_count"],
                                        limit=1)
        return results[0] if results else None

    def verify_area_exists(self, name: str = None,
                           area_id: str = None) -> bool:
        """Check if an area exists in Odoo (synced from HA)."""
        return self.find_area_in_odoo(name=name, area_id=area_id) is not None

    def verify_area_not_exists(self, name: str = None,
                               area_id: str = None) -> bool:
        """Check that an area does NOT exist."""
        return not self.verify_area_exists(name=name, area_id=area_id)

    def count_areas(self) -> int:
        """Count areas in Odoo for this instance."""
        return self.odoo.search_count(
            "ha.area", [("ha_instance_id", "=", self.instance_id)])

    # ------------------------------------------------------------------
    # Entity verification
    # ------------------------------------------------------------------

    def get_entity(self, entity_id: str) -> Optional[dict]:
        """Get entity by HA entity_id string."""
        results = self.odoo.search_read(
            "ha.entity",
            [("entity_id", "=", entity_id),
             ("ha_instance_id", "=", self.instance_id)],
            ["id", "entity_id", "name", "domain", "entity_state",
             "area_id", "device_id", "attributes", "ha_instance_id",
             "tag_ids", "label_ids"],
            limit=1)
        return results[0] if results else None

    def get_entity_state(self, entity_id: str) -> Optional[str]:
        """Get current state of an entity."""
        entity = self.get_entity(entity_id)
        return entity["entity_state"] if entity else None

    def verify_entity_state(self, entity_id: str,
                            expected_state: str,
                            wait_seconds: int = 5,
                            poll_interval: float = 0.5) -> bool:
        """
        Verify entity reaches expected state, with polling.

        Args:
            entity_id: HA entity_id string
            expected_state: Expected state string
            wait_seconds: Max time to wait
            poll_interval: Time between polls
        """
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            state = self.get_entity_state(entity_id)
            if state == expected_state:
                return True
            time.sleep(poll_interval)
        return False

    def get_entity_area_name(self, entity_id: str) -> Optional[str]:
        """Get the area name assigned to an entity."""
        entity = self.get_entity(entity_id)
        if entity and entity.get("area_id"):
            area_id = entity["area_id"]
            if isinstance(area_id, (list, tuple)):
                return area_id[1] if len(area_id) > 1 else None
            return None
        return None

    def count_entities(self, domain_filter: str = None) -> int:
        """Count entities, optionally filtered by domain."""
        domain = [("ha_instance_id", "=", self.instance_id)]
        if domain_filter:
            domain.append(("domain", "=", domain_filter))
        return self.odoo.search_count("ha.entity", domain)

    def get_entities_by_domain(self, domain_name: str,
                               limit: int = 0) -> list:
        """Get entities filtered by domain (light, switch, etc)."""
        return self.odoo.search_read(
            "ha.entity",
            [("ha_instance_id", "=", self.instance_id),
             ("domain", "=", domain_name)],
            ["id", "entity_id", "name", "entity_state", "area_id"],
            limit=limit)

    # ------------------------------------------------------------------
    # Scene verification
    # ------------------------------------------------------------------

    def get_scenes(self) -> list:
        """Get all scene entities."""
        return self.odoo.get_scenes(self.instance_id)

    def find_scene(self, name: str = None,
                   entity_id: str = None) -> Optional[dict]:
        """Find a scene by name or entity_id."""
        domain = [("ha_instance_id", "=", self.instance_id),
                  ("domain", "=", "scene")]
        if name:
            domain.append(("name", "=", name))
        if entity_id:
            domain.append(("entity_id", "=", entity_id))
        results = self.odoo.search_read("ha.entity", domain,
                                        ["id", "entity_id", "name",
                                         "entity_state"],
                                        limit=1)
        return results[0] if results else None

    # ------------------------------------------------------------------
    # Automation verification
    # ------------------------------------------------------------------

    def get_automations(self) -> list:
        """Get all automation entities."""
        return self.odoo.get_automations(self.instance_id)

    def find_automation(self, name: str = None,
                        entity_id: str = None) -> Optional[dict]:
        """Find an automation by name or entity_id."""
        domain = [("ha_instance_id", "=", self.instance_id),
                  ("domain", "=", "automation")]
        if name:
            domain.append(("name", "=", name))
        if entity_id:
            domain.append(("entity_id", "=", entity_id))
        results = self.odoo.search_read("ha.entity", domain,
                                        ["id", "entity_id", "name",
                                         "entity_state"],
                                        limit=1)
        return results[0] if results else None

    # ------------------------------------------------------------------
    # Script verification
    # ------------------------------------------------------------------

    def get_scripts(self) -> list:
        """Get all script entities."""
        return self.odoo.get_scripts(self.instance_id)

    def find_script(self, name: str = None,
                    entity_id: str = None) -> Optional[dict]:
        """Find a script by name or entity_id."""
        domain = [("ha_instance_id", "=", self.instance_id),
                  ("domain", "=", "script")]
        if name:
            domain.append(("name", "=", name))
        if entity_id:
            domain.append(("entity_id", "=", entity_id))
        results = self.odoo.search_read("ha.entity", domain,
                                        ["id", "entity_id", "name",
                                         "entity_state"],
                                        limit=1)
        return results[0] if results else None

    # ------------------------------------------------------------------
    # Device verification
    # ------------------------------------------------------------------

    def get_devices(self, limit: int = 0) -> list:
        """Get all devices."""
        return self.odoo.get_devices(self.instance_id, limit=limit)

    def find_device(self, device_id: str = None,
                    name: str = None) -> Optional[dict]:
        """Find a device by device_id or name."""
        domain = [("ha_instance_id", "=", self.instance_id)]
        if device_id:
            domain.append(("device_id", "=", device_id))
        if name:
            domain.append(("name", "=", name))
        results = self.odoo.search_read(
            "ha.device", domain,
            ["id", "device_id", "name", "manufacturer",
             "model", "area_id", "ha_instance_id"],
            limit=1)
        return results[0] if results else None

    def count_devices(self) -> int:
        """Count devices for this instance."""
        return self.odoo.search_count(
            "ha.device", [("ha_instance_id", "=", self.instance_id)])

    # ------------------------------------------------------------------
    # Label verification
    # ------------------------------------------------------------------

    def get_labels(self) -> list:
        """Get all labels."""
        return self.odoo.get_labels(self.instance_id)

    def find_label(self, name: str = None,
                   label_id: str = None) -> Optional[dict]:
        """Find a label by name or label_id."""
        domain = [("ha_instance_id", "=", self.instance_id)]
        if name:
            domain.append(("name", "=", name))
        if label_id:
            domain.append(("label_id", "=", label_id))
        results = self.odoo.search_read("ha.label", domain,
                                        ["id", "label_id", "name",
                                         "ha_instance_id"],
                                        limit=1)
        return results[0] if results else None

    def count_labels(self) -> int:
        """Count labels for this instance."""
        return self.odoo.search_count(
            "ha.label", [("ha_instance_id", "=", self.instance_id)])

    # ------------------------------------------------------------------
    # Tag verification
    # ------------------------------------------------------------------

    def get_entity_tags(self) -> list:
        """Get all entity tags."""
        return self.odoo.get_entity_tags(self.instance_id)

    def count_entity_tags(self) -> int:
        return self.odoo.search_count(
            "ha.entity.tag", [("ha_instance_id", "=", self.instance_id)])

    # ------------------------------------------------------------------
    # Sync operations (trigger HA sync via Odoo)
    # ------------------------------------------------------------------

    def trigger_registry_sync(self) -> Any:
        """Trigger registry sync (areas, devices, labels)."""
        return self.odoo.sync_registry(self.instance_id)

    def trigger_entity_sync(self) -> Any:
        """Trigger entity sync."""
        return self.odoo.sync_entities(self.instance_id)

    def wait_for_sync(self, seconds: float = 3.0):
        """Wait for sync to propagate."""
        time.sleep(seconds)

    # ------------------------------------------------------------------
    # Service calls (via Odoo controller -> HA WebSocket)
    # ------------------------------------------------------------------

    def call_service(self, domain: str, service: str,
                     service_data: dict = None) -> dict:
        """Call HA service via Odoo controller."""
        return self.odoo.call_service(
            domain, service, service_data,
            ha_instance_id=self.instance_id)

    # ------------------------------------------------------------------
    # Cross-entity consistency checks
    # ------------------------------------------------------------------

    def get_summary(self) -> dict:
        """Get summary counts for all entity types."""
        return {
            "areas": self.count_areas(),
            "entities": self.count_entities(),
            "devices": self.count_devices(),
            "labels": self.count_labels(),
            "scenes": len(self.get_scenes()),
            "automations": len(self.get_automations()),
            "scripts": len(self.get_scripts()),
            "entity_tags": self.count_entity_tags(),
            "connected": self.is_connected(),
        }
