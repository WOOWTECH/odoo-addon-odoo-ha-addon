#!/usr/bin/env python3
"""
Test Data Generator for E2E Tests

Creates mock entity data for testing entity controllers.
Can create test entities in Odoo or generate mock data for offline testing.

Usage:
    # Create test entities in Odoo
    python e2e_tests/test_data.py create

    # List existing test entities
    python e2e_tests/test_data.py list

    # Clean up test entities
    python e2e_tests/test_data.py cleanup

    # Generate mock data file
    python e2e_tests/test_data.py generate-mock
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

try:
    import xmlrpc.client
except ImportError:
    xmlrpc = None

try:
    from .config import get_config, E2EConfig
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from e2e_tests.config import get_config, E2EConfig


# Test entity definitions for each domain
TEST_ENTITIES = {
    "switch": [
        {
            "entity_id": "switch.e2e_test_switch_1",
            "name": "E2E Test Switch 1",
            "state": "off",
            "attributes": {},
        },
        {
            "entity_id": "switch.e2e_test_switch_2",
            "name": "E2E Test Switch 2",
            "state": "on",
            "attributes": {},
        },
    ],
    "light": [
        {
            "entity_id": "light.e2e_test_light_1",
            "name": "E2E Test Light 1",
            "state": "off",
            "attributes": {
                "brightness": 0,
                "supported_color_modes": ["brightness"],
            },
        },
        {
            "entity_id": "light.e2e_test_light_2",
            "name": "E2E Test Light 2",
            "state": "on",
            "attributes": {
                "brightness": 200,
                "supported_color_modes": ["brightness"],
            },
        },
    ],
    "sensor": [
        {
            "entity_id": "sensor.e2e_test_temperature",
            "name": "E2E Test Temperature Sensor",
            "state": "23.5",
            "attributes": {
                "unit_of_measurement": "°C",
                "device_class": "temperature",
            },
        },
        {
            "entity_id": "sensor.e2e_test_humidity",
            "name": "E2E Test Humidity Sensor",
            "state": "65",
            "attributes": {
                "unit_of_measurement": "%",
                "device_class": "humidity",
            },
        },
        {
            "entity_id": "sensor.e2e_test_power",
            "name": "E2E Test Power Sensor",
            "state": "150.5",
            "attributes": {
                "unit_of_measurement": "W",
                "device_class": "power",
            },
        },
    ],
    "climate": [
        {
            "entity_id": "climate.e2e_test_thermostat",
            "name": "E2E Test Thermostat",
            "state": "heat",
            "attributes": {
                "temperature": 22,
                "current_temperature": 20.5,
                "hvac_action": "heating",
                "hvac_modes": ["off", "heat", "cool", "auto"],
                "fan_modes": ["auto", "low", "medium", "high"],
                "fan_mode": "auto",
            },
        },
    ],
    "cover": [
        {
            "entity_id": "cover.e2e_test_blind",
            "name": "E2E Test Blind",
            "state": "open",
            "attributes": {
                "current_position": 100,
            },
        },
        {
            "entity_id": "cover.e2e_test_garage",
            "name": "E2E Test Garage Door",
            "state": "closed",
            "attributes": {
                "current_position": 0,
            },
        },
    ],
    "fan": [
        {
            "entity_id": "fan.e2e_test_ceiling_fan",
            "name": "E2E Test Ceiling Fan",
            "state": "on",
            "attributes": {
                "percentage": 50,
                "oscillating": False,
                "preset_modes": ["normal", "sleep", "nature"],
                "preset_mode": "normal",
            },
        },
        {
            "entity_id": "fan.e2e_test_desk_fan",
            "name": "E2E Test Desk Fan",
            "state": "off",
            "attributes": {
                "percentage": 0,
                "oscillating": True,
                "preset_modes": ["low", "medium", "high"],
            },
        },
    ],
    "automation": [
        {
            "entity_id": "automation.e2e_test_morning_lights",
            "name": "E2E Test Morning Lights Automation",
            "state": "on",
            "attributes": {},
        },
        {
            "entity_id": "automation.e2e_test_night_mode",
            "name": "E2E Test Night Mode Automation",
            "state": "off",
            "attributes": {},
        },
    ],
    "scene": [
        {
            "entity_id": "scene.e2e_test_movie_mode",
            "name": "E2E Test Movie Mode Scene",
            "state": "scening",
            "attributes": {},
        },
        {
            "entity_id": "scene.e2e_test_party_mode",
            "name": "E2E Test Party Mode Scene",
            "state": "scening",
            "attributes": {},
        },
    ],
    "script": [
        {
            "entity_id": "script.e2e_test_goodnight",
            "name": "E2E Test Goodnight Script",
            "state": "off",
            "attributes": {},
        },
        {
            "entity_id": "script.e2e_test_welcome_home",
            "name": "E2E Test Welcome Home Script",
            "state": "off",
            "attributes": {},
        },
    ],
}


class OdooRPC:
    """Simple Odoo XML-RPC client"""

    def __init__(self, config: E2EConfig):
        self.config = config
        self.url = config.base_url
        self.db = config.odoo_database
        self.username = config.odoo_username
        self.password = config.odoo_password
        self.uid = None

    def connect(self):
        """Authenticate with Odoo"""
        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.uid = common.authenticate(self.db, self.username, self.password, {})
        if not self.uid:
            raise Exception("Authentication failed")
        return self.uid

    def execute(self, model: str, method: str, *args, **kwargs):
        """Execute a method on an Odoo model"""
        if not self.uid:
            self.connect()
        models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        return models.execute_kw(
            self.db, self.uid, self.password,
            model, method,
            list(args), kwargs
        )

    def search(self, model: str, domain: List, fields: List = None):
        """Search records"""
        return self.execute(model, "search_read", domain, {"fields": fields or []})

    def create(self, model: str, values: Dict):
        """Create a record"""
        return self.execute(model, "create", [values])

    def write(self, model: str, ids: List[int], values: Dict):
        """Update records"""
        return self.execute(model, "write", ids, values)

    def unlink(self, model: str, ids: List[int]):
        """Delete records"""
        return self.execute(model, "unlink", ids)


def create_test_entities():
    """Create test entities in Odoo via XML-RPC"""
    config = get_config()
    rpc = OdooRPC(config)

    print("Connecting to Odoo...")
    try:
        rpc.connect()
        print(f"✓ Connected as UID {rpc.uid}")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return

    # Get first HA instance
    instances = rpc.search("ha.instance", [], ["id", "name"])
    if not instances:
        print("✗ No HA instances found. Please create one first.")
        return

    instance_id = instances[0]["id"]
    print(f"Using HA instance: {instances[0]['name']} (ID: {instance_id})")

    created = 0
    skipped = 0

    for domain, entities in TEST_ENTITIES.items():
        print(f"\nProcessing {domain} entities...")

        for entity_data in entities:
            # Check if entity already exists
            existing = rpc.search(
                "ha.entity",
                [("entity_id", "=", entity_data["entity_id"])],
                ["id"]
            )

            if existing:
                print(f"  - {entity_data['entity_id']}: already exists (skipped)")
                skipped += 1
                continue

            # Create entity
            values = {
                "entity_id": entity_data["entity_id"],
                "name": entity_data["name"],
                "domain": domain,
                "state": entity_data["state"],
                "attributes": json.dumps(entity_data["attributes"]),
                "instance_id": instance_id,
            }

            try:
                entity_id = rpc.create("ha.entity", values)
                print(f"  + {entity_data['entity_id']}: created (ID: {entity_id})")
                created += 1
            except Exception as e:
                print(f"  ✗ {entity_data['entity_id']}: failed - {e}")

    print(f"\n✓ Done: {created} created, {skipped} skipped")


def list_test_entities():
    """List existing test entities"""
    config = get_config()
    rpc = OdooRPC(config)

    print("Connecting to Odoo...")
    try:
        rpc.connect()
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return

    # Find all E2E test entities
    entities = rpc.search(
        "ha.entity",
        [("entity_id", "like", "e2e_test")],
        ["entity_id", "name", "domain", "state"]
    )

    if not entities:
        print("No E2E test entities found.")
        return

    print(f"\n{'Domain':<12} {'Entity ID':<35} {'Name':<30} {'State'}")
    print("-" * 90)

    for entity in sorted(entities, key=lambda x: (x["domain"], x["entity_id"])):
        print(f"{entity['domain']:<12} {entity['entity_id']:<35} {entity['name']:<30} {entity['state']}")

    print(f"\nTotal: {len(entities)} test entities")


def cleanup_test_entities():
    """Remove all test entities"""
    config = get_config()
    rpc = OdooRPC(config)

    print("Connecting to Odoo...")
    try:
        rpc.connect()
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return

    # Find all E2E test entities
    entities = rpc.search(
        "ha.entity",
        [("entity_id", "like", "e2e_test")],
        ["id", "entity_id"]
    )

    if not entities:
        print("No E2E test entities found.")
        return

    confirm = input(f"Delete {len(entities)} test entities? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        return

    ids = [e["id"] for e in entities]
    rpc.unlink("ha.entity", ids)
    print(f"✓ Deleted {len(ids)} test entities")


def generate_mock_data():
    """Generate mock data file for offline testing"""
    output_path = Path(__file__).parent / "mock_data.json"

    mock_data = {
        "entities": [],
        "domains": list(TEST_ENTITIES.keys()),
    }

    for domain, entities in TEST_ENTITIES.items():
        for entity in entities:
            mock_data["entities"].append({
                **entity,
                "domain": domain,
            })

    with open(output_path, "w") as f:
        json.dump(mock_data, f, indent=2)

    print(f"✓ Mock data written to: {output_path}")
    print(f"  Total entities: {len(mock_data['entities'])}")


def update_config_with_test_entities():
    """Update e2e_config.yaml with test entity IDs"""
    config_path = Path(__file__).parent / "e2e_config.yaml"

    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        return

    import yaml

    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    # Update test_entities section
    config_data["test_entities"] = {}
    for domain, entities in TEST_ENTITIES.items():
        if entities:
            first_entity = entities[0]
            config_data["test_entities"][domain] = {
                "entity_id": first_entity["entity_id"],
                "name": first_entity["name"],
                "initial_state": first_entity["state"],
                "attributes": first_entity.get("attributes", {}),
            }

    with open(config_path, "w") as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)

    print(f"✓ Config updated: {config_path}")


def main():
    parser = argparse.ArgumentParser(description="Test Data Generator for E2E Tests")
    parser.add_argument(
        "action",
        choices=["create", "list", "cleanup", "generate-mock", "update-config"],
        help="Action to perform",
    )

    args = parser.parse_args()

    if args.action == "create":
        create_test_entities()
    elif args.action == "list":
        list_test_entities()
    elif args.action == "cleanup":
        cleanup_test_entities()
    elif args.action == "generate-mock":
        generate_mock_data()
    elif args.action == "update-config":
        update_config_with_test_entities()


if __name__ == "__main__":
    main()
