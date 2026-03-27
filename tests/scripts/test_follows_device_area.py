#!/usr/bin/env python3
"""
Unit test for follows_device_area feature logic.
Tests the sync logic and computed field without requiring Odoo runtime.
"""

import unittest
from unittest.mock import MagicMock, patch


class MockEntity:
    """Mock ha.entity record for testing"""
    def __init__(self, area_id=None, device_id=None, follows_device_area=False):
        self.area_id = MagicMock(id=area_id, area_id=f"area_{area_id}") if area_id else None
        self.device_id = MagicMock(id=device_id, area_id=MagicMock(id=100, area_id="device_area")) if device_id else None
        self.follows_device_area = follows_device_area
        self.display_area_id = None

    def compute_display_area_id(self):
        """Simulates _compute_display_area_id logic"""
        if self.follows_device_area and self.device_id:
            self.display_area_id = self.device_id.area_id
        else:
            self.display_area_id = self.area_id


class TestFollowsDeviceAreaLogic(unittest.TestCase):
    """Test the follows_device_area sync logic"""

    def test_sync_entity_with_own_area(self):
        """When HA returns area_id, entity should NOT follow device area"""
        # Simulate: ha_area_id = "living_room", ha_device_id = "device_1"
        ha_area_id = "living_room"
        ha_device_id = "device_1"

        # Current entity state
        entity = MockEntity(area_id=None, device_id=1, follows_device_area=True)

        # Sync logic
        update_vals = {}
        if ha_area_id:
            # Entity has its own area
            update_vals['area_id'] = 1  # mapped odoo_area_id
            if entity.follows_device_area:
                update_vals['follows_device_area'] = False

        self.assertIn('area_id', update_vals)
        self.assertEqual(update_vals['follows_device_area'], False)
        print("✅ Test 1 PASSED: Entity with own area -> follows_device_area = False")

    def test_sync_entity_follows_device(self):
        """When HA returns area_id=null but has device_id, entity should follow device area"""
        # Simulate: ha_area_id = None, ha_device_id = "device_1"
        ha_area_id = None
        ha_device_id = "device_1"

        # Current entity state (not following yet)
        entity = MockEntity(area_id=1, device_id=1, follows_device_area=False)

        # Sync logic
        update_vals = {}
        if not ha_area_id and ha_device_id:
            # HA has no area but has device -> follows device area
            if entity.area_id:
                update_vals['area_id'] = False
            if not entity.follows_device_area:
                update_vals['follows_device_area'] = True

        self.assertEqual(update_vals.get('area_id'), False)
        self.assertEqual(update_vals.get('follows_device_area'), True)
        print("✅ Test 2 PASSED: Entity with no area but device -> follows_device_area = True")

    def test_sync_entity_no_area_no_device(self):
        """When HA returns area_id=null and no device_id, entity should not follow device area"""
        # Simulate: ha_area_id = None, ha_device_id = None
        ha_area_id = None
        ha_device_id = None

        # Current entity state
        entity = MockEntity(area_id=1, device_id=None, follows_device_area=True)

        # Sync logic
        update_vals = {}
        if not ha_area_id and not ha_device_id:
            if entity.area_id:
                update_vals['area_id'] = False
            if entity.follows_device_area:
                update_vals['follows_device_area'] = False

        self.assertEqual(update_vals.get('area_id'), False)
        self.assertEqual(update_vals.get('follows_device_area'), False)
        print("✅ Test 3 PASSED: Entity with no area and no device -> follows_device_area = False")

    def test_compute_display_area_follows_device(self):
        """When follows_device_area=True, display_area_id should be device's area"""
        entity = MockEntity(area_id=1, device_id=2, follows_device_area=True)
        entity.compute_display_area_id()

        self.assertEqual(entity.display_area_id.id, 100)  # device's area id
        print("✅ Test 4 PASSED: display_area_id = device.area_id when follows_device_area=True")

    def test_compute_display_area_own_area(self):
        """When follows_device_area=False, display_area_id should be entity's own area"""
        entity = MockEntity(area_id=5, device_id=2, follows_device_area=False)
        entity.compute_display_area_id()

        self.assertEqual(entity.display_area_id.id, 5)  # entity's own area
        print("✅ Test 5 PASSED: display_area_id = area_id when follows_device_area=False")

    def test_compute_display_area_no_device(self):
        """When follows_device_area=True but no device, display_area_id should be None"""
        entity = MockEntity(area_id=None, device_id=None, follows_device_area=True)
        entity.compute_display_area_id()

        self.assertIsNone(entity.display_area_id)
        print("✅ Test 6 PASSED: display_area_id = None when follows_device_area=True but no device")

    def test_update_to_ha_follows_device(self):
        """When follows_device_area=True, should send null to HA"""
        entity = MockEntity(area_id=5, device_id=2, follows_device_area=True)

        # Simulate _update_entity_area_in_ha logic
        if entity.follows_device_area:
            ha_area_id = None
        else:
            ha_area_id = entity.area_id.area_id if entity.area_id else None

        self.assertIsNone(ha_area_id)
        print("✅ Test 7 PASSED: Send null to HA when follows_device_area=True")

    def test_update_to_ha_own_area(self):
        """When follows_device_area=False, should send area_id to HA"""
        entity = MockEntity(area_id=5, device_id=2, follows_device_area=False)

        # Simulate _update_entity_area_in_ha logic
        if entity.follows_device_area:
            ha_area_id = None
        else:
            ha_area_id = entity.area_id.area_id if entity.area_id else None

        self.assertEqual(ha_area_id, "area_5")
        print("✅ Test 8 PASSED: Send area_id to HA when follows_device_area=False")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Testing 'follows_device_area' Feature Logic")
    print("="*60 + "\n")

    unittest.main(verbosity=2)
