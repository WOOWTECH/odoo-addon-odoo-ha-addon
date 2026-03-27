"""
Odoo JSON-RPC Client for Stability Testing

Wraps all Odoo API calls needed for CRUD and sync verification.
Uses JSON-RPC protocol at http://localhost:9077/web/dataset/call_kw
and http://localhost:9077/jsonrpc for generic model access.
"""

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Optional

_logger = logging.getLogger(__name__)

ODOO_URL = "http://localhost:9077"
ODOO_DB = "odoohaiot"
ODOO_LOGIN = "admin"
ODOO_PASSWORD = "admin"


class OdooClient:
    """JSON-RPC client for Odoo 18."""

    def __init__(self, url=ODOO_URL, db=ODOO_DB, login=ODOO_LOGIN, password=ODOO_PASSWORD):
        self.url = url.rstrip("/")
        self.db = db
        self.login = login
        self.password = password
        self.uid = None
        self.session_id = None
        self._rpc_id = 0

    # ------------------------------------------------------------------
    # Low-level RPC
    # ------------------------------------------------------------------

    def _next_id(self):
        self._rpc_id += 1
        return self._rpc_id

    def _rpc(self, endpoint: str, params: dict, timeout: int = 30) -> dict:
        """Send a JSON-RPC 2.0 request and return the result."""
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "id": self._next_id(),
            "params": params,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.url}{endpoint}",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        if self.session_id:
            req.add_header("Cookie", f"session_id={self.session_id}")

        resp = urllib.request.urlopen(req, timeout=timeout)

        # Capture session cookie
        for header in resp.headers.get_all("Set-Cookie") or []:
            if "session_id=" in header:
                self.session_id = header.split("session_id=")[1].split(";")[0]

        body = json.loads(resp.read().decode("utf-8"))
        if "error" in body:
            err = body["error"]
            msg = err.get("data", {}).get("message", err.get("message", str(err)))
            raise OdooRPCError(msg, err)
        return body.get("result")

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self) -> int:
        """Authenticate and return uid."""
        result = self._rpc("/web/session/authenticate", {
            "db": self.db,
            "login": self.login,
            "password": self.password,
        })
        self.uid = result.get("uid")
        if not self.uid:
            raise OdooRPCError("Authentication failed", result)
        _logger.info(f"Authenticated as uid={self.uid}")
        return self.uid

    def ensure_auth(self):
        """Authenticate if not already."""
        if not self.uid:
            self.authenticate()

    # ------------------------------------------------------------------
    # ORM helpers
    # ------------------------------------------------------------------

    def call_kw(self, model: str, method: str, args: list = None,
                kwargs: dict = None, timeout: int = 30) -> Any:
        """Call a model method via /web/dataset/call_kw."""
        self.ensure_auth()
        return self._rpc("/web/dataset/call_kw", {
            "model": model,
            "method": method,
            "args": args or [],
            "kwargs": kwargs or {},
        }, timeout=timeout)

    def search_read(self, model: str, domain: list = None,
                    fields: list = None, limit: int = 0,
                    order: str = "", offset: int = 0) -> list:
        """Search and read records."""
        return self.call_kw(model, "search_read", [], {
            "domain": domain or [],
            "fields": fields or [],
            "limit": limit,
            "order": order,
            "offset": offset,
        })

    def search_count(self, model: str, domain: list = None) -> int:
        """Count matching records."""
        return self.call_kw(model, "search_count", [domain or []])

    def read(self, model: str, ids: list, fields: list = None) -> list:
        """Read specific records by IDs."""
        return self.call_kw(model, "read", [ids], {"fields": fields or []})

    def create(self, model: str, vals: dict) -> int:
        """Create a record. Returns the new record ID."""
        return self.call_kw(model, "create", [vals])

    def write(self, model: str, ids: list, vals: dict) -> bool:
        """Update records."""
        return self.call_kw(model, "write", [ids, vals])

    def unlink(self, model: str, ids: list) -> bool:
        """Delete records."""
        return self.call_kw(model, "unlink", [ids])

    # ------------------------------------------------------------------
    # Controller endpoints (JSON type='json')
    # ------------------------------------------------------------------

    def call_controller(self, route: str, params: dict = None,
                        timeout: int = 30) -> dict:
        """Call an Odoo JSON controller endpoint."""
        self.ensure_auth()
        return self._rpc(route, params or {}, timeout=timeout)

    # ------------------------------------------------------------------
    # Convenience: HA-specific operations
    # ------------------------------------------------------------------

    def get_instance(self, instance_id: int = None) -> dict:
        """Get HA instance. If id is None, return the first one."""
        domain = [("id", "=", instance_id)] if instance_id else []
        results = self.search_read("ha.instance", domain,
                                   ["id", "name", "api_url", "active",
                                    "connection_status", "ha_version"],
                                   limit=1)
        return results[0] if results else None

    def get_areas(self, instance_id: int = None) -> list:
        """Get all areas for an instance."""
        domain = [("ha_instance_id", "=", instance_id)] if instance_id else []
        return self.search_read("ha.area", domain,
                                ["id", "area_id", "name", "ha_instance_id",
                                 "entity_count"])

    def create_area(self, name: str, instance_id: int, **extra) -> int:
        """Create an area in Odoo (triggers HA sync)."""
        vals = {"name": name, "ha_instance_id": instance_id, **extra}
        return self.create("ha.area", vals)

    def get_entities(self, domain_filter: list = None,
                     fields: list = None, limit: int = 0) -> list:
        """Get entities with optional filter."""
        default_fields = ["id", "entity_id", "name", "domain", "entity_state",
                          "area_id", "device_id", "ha_instance_id"]
        return self.search_read("ha.entity", domain_filter or [],
                                fields or default_fields, limit=limit)

    def get_entity_by_entity_id(self, entity_id: str) -> Optional[dict]:
        """Get a single entity by its HA entity_id string."""
        results = self.search_read("ha.entity",
                                   [("entity_id", "=", entity_id)],
                                   limit=1)
        return results[0] if results else None

    def call_service(self, domain: str, service: str,
                     service_data: dict = None,
                     ha_instance_id: int = None) -> dict:
        """Call HA service via controller."""
        params = {
            "domain": domain,
            "service": service,
            "service_data": service_data or {},
        }
        if ha_instance_id:
            params["ha_instance_id"] = ha_instance_id
        return self.call_controller("/odoo_ha_addon/call_service", params)

    def get_labels(self, instance_id: int = None) -> list:
        """Get all labels for an instance."""
        domain = [("ha_instance_id", "=", instance_id)] if instance_id else []
        return self.search_read("ha.label", domain,
                                ["id", "label_id", "name", "ha_instance_id"])

    def get_devices(self, instance_id: int = None, limit: int = 0) -> list:
        """Get devices for an instance."""
        domain = [("ha_instance_id", "=", instance_id)] if instance_id else []
        return self.search_read("ha.device", domain,
                                ["id", "device_id", "name", "manufacturer",
                                 "model", "area_id", "ha_instance_id"],
                                limit=limit)

    def get_scenes(self, instance_id: int = None) -> list:
        """Get scene entities."""
        domain = [("domain", "=", "scene")]
        if instance_id:
            domain.append(("ha_instance_id", "=", instance_id))
        return self.search_read("ha.entity", domain,
                                ["id", "entity_id", "name", "entity_state",
                                 "ha_instance_id"])

    def get_automations(self, instance_id: int = None) -> list:
        """Get automation entities."""
        domain = [("domain", "=", "automation")]
        if instance_id:
            domain.append(("ha_instance_id", "=", instance_id))
        return self.search_read("ha.entity", domain,
                                ["id", "entity_id", "name", "entity_state",
                                 "ha_instance_id"])

    def get_scripts(self, instance_id: int = None) -> list:
        """Get script entities."""
        domain = [("domain", "=", "script")]
        if instance_id:
            domain.append(("ha_instance_id", "=", instance_id))
        return self.search_read("ha.entity", domain,
                                ["id", "entity_id", "name", "entity_state",
                                 "ha_instance_id"])

    def sync_registry(self, instance_id: int) -> dict:
        """Trigger registry sync for an instance."""
        return self.call_kw("ha.instance", "action_sync_registry",
                            [[instance_id]])

    def sync_entities(self, instance_id: int) -> dict:
        """Trigger entity sync for an instance."""
        return self.call_kw("ha.instance", "action_sync_entities",
                            [[instance_id]])

    def get_entity_tags(self, instance_id: int = None) -> list:
        """Get entity tags."""
        domain = [("ha_instance_id", "=", instance_id)] if instance_id else []
        return self.search_read("ha.entity.tag", domain,
                                ["id", "name", "ha_instance_id"])

    def get_entity_groups(self, instance_id: int = None) -> list:
        """Get entity groups."""
        domain = [("ha_instance_id", "=", instance_id)] if instance_id else []
        return self.search_read("ha.entity.group", domain,
                                ["id", "name", "ha_instance_id",
                                 "entity_ids", "user_ids"])

    def get_websocket_status(self, instance_id: int = None) -> dict:
        """Get WebSocket connection status via controller."""
        params = {}
        if instance_id:
            params["ha_instance_id"] = instance_id
        return self.call_controller("/odoo_ha_addon/websocket_status", params)

    def get_areas_via_controller(self, instance_id: int = None) -> dict:
        """Get areas via controller endpoint."""
        params = {}
        if instance_id:
            params["ha_instance_id"] = instance_id
        return self.call_controller("/odoo_ha_addon/areas", params)

    def get_entities_by_area(self, area_id: int,
                             instance_id: int = None) -> dict:
        """Get entities by area via controller."""
        params = {"area_id": area_id}
        if instance_id:
            params["ha_instance_id"] = instance_id
        return self.call_controller("/odoo_ha_addon/entities_by_area", params)

    # ------------------------------------------------------------------
    # Scene-specific operations
    # ------------------------------------------------------------------

    def create_scene(self, name: str, entity_ids: list,
                     instance_id: int, **extra) -> int:
        """Create a scene entity in Odoo (triggers HA sync).

        Args:
            name: Scene display name
            entity_ids: List of Odoo entity record IDs (M2M)
            instance_id: HA instance ID
        Returns:
            New scene record ID
        """
        vals = {
            "name": name,
            "domain": "scene",
            "ha_instance_id": instance_id,
            "scene_entity_ids": [(6, 0, entity_ids)],
            **extra,
        }
        return self.create("ha.entity", vals)

    def get_scene_detail(self, scene_id: int) -> dict:
        """Read full scene details including M2M fields."""
        results = self.read("ha.entity", [scene_id],
                            ["id", "entity_id", "name", "domain",
                             "entity_state", "ha_scene_id", "scene_source",
                             "scene_entity_ids", "scene_entity_count",
                             "area_id", "label_ids", "ha_instance_id"])
        return results[0] if results else {}

    def update_scene_entities(self, scene_id: int, entity_ids: list):
        """Replace scene entity list (M2M replace)."""
        return self.write("ha.entity", [scene_id],
                          {"scene_entity_ids": [(6, 0, entity_ids)]})

    def add_scene_entity(self, scene_id: int, entity_id: int):
        """Add a single entity to a scene."""
        return self.write("ha.entity", [scene_id],
                          {"scene_entity_ids": [(4, entity_id)]})

    def remove_scene_entity(self, scene_id: int, entity_id: int):
        """Remove a single entity from a scene."""
        return self.write("ha.entity", [scene_id],
                          {"scene_entity_ids": [(3, entity_id)]})

    # ------------------------------------------------------------------
    # Automation/Script-specific operations
    # ------------------------------------------------------------------

    def get_automation_detail(self, auto_id: int) -> dict:
        """Read full automation details including blueprint fields."""
        results = self.read("ha.entity", [auto_id],
                            ["id", "entity_id", "name", "domain",
                             "entity_state", "blueprint_path",
                             "blueprint_inputs", "blueprint_metadata",
                             "is_blueprint_based", "ha_automation_id",
                             "area_id", "label_ids", "ha_instance_id"])
        return results[0] if results else {}

    def get_script_detail(self, script_id: int) -> dict:
        """Read full script details including blueprint fields."""
        results = self.read("ha.entity", [script_id],
                            ["id", "entity_id", "name", "domain",
                             "entity_state", "blueprint_path",
                             "blueprint_inputs", "blueprint_metadata",
                             "is_blueprint_based", "ha_automation_id",
                             "area_id", "label_ids", "ha_instance_id"])
        return results[0] if results else {}

    def get_entity_related(self, entity_id: str,
                           ha_instance_id: int = None) -> dict:
        """Get entity's related items (scenes, automations, scripts) via controller."""
        params = {"entity_id": entity_id}
        if ha_instance_id:
            params["ha_instance_id"] = ha_instance_id
        return self.call_controller("/odoo_ha_addon/entity_related", params)

    # ------------------------------------------------------------------
    # Blueprint wizard operations
    # ------------------------------------------------------------------

    def get_blueprint_list(self, domain: str, instance_id: int) -> list:
        """Get available blueprints via the wizard model.

        Creates a transient wizard record, refreshes blueprints from HA,
        then calls get_blueprint_list_for_selector on that record.
        """
        # Create a wizard record (onchange doesn't fire via RPC)
        wiz_id = self.create("ha.blueprint.wizard", {
            "domain": domain,
            "ha_instance_id": instance_id,
        })
        # Trigger blueprint loading (onchange doesn't fire via create)
        self.call_kw("ha.blueprint.wizard", "action_refresh_blueprints",
                      [[wiz_id]])
        # Now fetch the formatted list
        return self.call_kw("ha.blueprint.wizard",
                            "get_blueprint_list_for_selector",
                            [[wiz_id]])

    def create_from_blueprint(self, domain: str, blueprint_path: str,
                              name: str, inputs: dict,
                              instance_id: int) -> dict:
        """Create automation/script from blueprint via wizard.

        Returns wizard action result.
        """
        # Step 1: create wizard
        wiz_id = self.create("ha.blueprint.wizard", {
            "domain": domain,
            "blueprint_path": blueprint_path,
            "name": name,
            "ha_instance_id": instance_id,
        })
        # Step 2: refresh blueprints (populates blueprint_list_json)
        self.call_kw("ha.blueprint.wizard", "action_refresh_blueprints",
                      [[wiz_id]])
        # Step 3: select blueprint (loads schema)
        self.call_kw("ha.blueprint.wizard", "action_select_blueprint",
                      [[wiz_id]])
        # Step 4: set inputs
        import json as _json
        self.write("ha.blueprint.wizard", [wiz_id],
                   {"blueprint_inputs_json": _json.dumps(inputs)})
        # Step 5: create
        return self.call_kw("ha.blueprint.wizard", "action_create",
                            [[wiz_id]])

    # ------------------------------------------------------------------
    # Label operations (extended)
    # ------------------------------------------------------------------

    def create_label(self, name: str, instance_id: int, **extra) -> int:
        """Create a label in Odoo (triggers HA sync)."""
        vals = {"name": name, "ha_instance_id": instance_id, **extra}
        return self.create("ha.label", vals)

    def get_label_detail(self, label_id: int) -> dict:
        """Read full label details."""
        results = self.read("ha.label", [label_id],
                            ["id", "label_id", "name", "icon",
                             "ha_color", "description",
                             "ha_instance_id"])
        return results[0] if results else {}

    # ------------------------------------------------------------------
    # Device operations (extended)
    # ------------------------------------------------------------------

    def get_device_detail(self, device_id: int) -> dict:
        """Read full device details."""
        results = self.read("ha.device", [device_id],
                            ["id", "device_id", "name", "name_by_user",
                             "manufacturer", "model", "area_id",
                             "label_ids", "disabled_by",
                             "ha_instance_id"])
        return results[0] if results else {}

    def sync_device_related(self, device_id: int,
                            instance_id: int = None) -> dict:
        """Sync device related items via controller."""
        params = {"device_id": device_id}
        if instance_id:
            params["ha_instance_id"] = instance_id
        return self.call_controller(
            "/odoo_ha_addon/sync_device_related_items", params)

    # ------------------------------------------------------------------
    # Portal operations
    # ------------------------------------------------------------------

    def portal_get_entity_state(self, entity_id: int,
                                access_token: str) -> dict:
        """Get entity state from portal endpoint (no auth needed)."""
        url = f"{self.url}/portal/entity/{entity_id}/state?access_token={access_token}"
        req = urllib.request.Request(url)
        try:
            resp = urllib.request.urlopen(req, timeout=15)
            return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return {"error": e.code, "reason": str(e.reason)}

    def portal_get_entity_page(self, entity_id: int,
                               access_token: str) -> int:
        """Get portal entity page. Returns HTTP status code."""
        url = f"{self.url}/portal/entity/{entity_id}?access_token={access_token}"
        req = urllib.request.Request(url)
        try:
            resp = urllib.request.urlopen(req, timeout=15)
            return resp.getcode()
        except urllib.error.HTTPError as e:
            return e.code

    def portal_call_service(self, domain: str, service: str,
                            entity_id: int, access_token: str,
                            service_data: dict = None) -> dict:
        """Call service from portal."""
        url = f"{self.url}/portal/call-service"
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "id": self._next_id(),
            "params": {
                "domain": domain,
                "service": service,
                "service_data": {
                    "entity_id": entity_id,
                    **(service_data or {}),
                },
                "access_token": access_token,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            resp = urllib.request.urlopen(req, timeout=15)
            body = json.loads(resp.read().decode("utf-8"))
            return body.get("result", body)
        except urllib.error.HTTPError as e:
            return {"error": e.code, "reason": str(e.reason)}


class OdooRPCError(Exception):
    """Raised when an Odoo JSON-RPC call returns an error."""

    def __init__(self, message: str, raw: dict = None):
        super().__init__(message)
        self.raw = raw or {}
