# Part of odoo_ha_addon. See LICENSE file for full copyright and licensing details.

from unittest.mock import patch, MagicMock
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestGetAreasController(TransactionCase):
    """Test cases for the get_areas controller endpoint"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a test HA instance
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Test HA Instance',
            'api_url': 'http://test-ha.local:8123',
            'api_token': 'test_token_12345',
            'active': True,
        })

    def setUp(self):
        super().setUp()
        # Clean up any existing areas for the test instance
        self.env['ha.area'].search([
            ('ha_instance_id', '=', self.ha_instance.id)
        ]).unlink()

    def _mock_websocket_client(self, areas_response=None):
        """Create a mock WebSocket client that returns configured responses"""
        mock_client = MagicMock()
        mock_client.call_websocket_api_sync.return_value = areas_response or []
        return mock_client

    def test_sync_areas_from_ha_creates_new_areas(self):
        """Test that sync_areas_from_ha creates new areas correctly"""
        # Prepare mock data
        mock_areas = [
            {
                'area_id': 'living_room',
                'name': 'Living Room',
                'icon': 'mdi:sofa',
                'aliases': ['lounge'],
            },
            {
                'area_id': 'bedroom',
                'name': 'Bedroom',
                'icon': 'mdi:bed',
                'aliases': [],
            },
        ]

        mock_client = self._mock_websocket_client(mock_areas)

        with patch(
            'odoo.addons.odoo_ha_addon.models.common.websocket_client.get_websocket_client',
            return_value=mock_client
        ):
            self.env['ha.area'].sync_areas_from_ha(instance_id=self.ha_instance.id)

        # Verify areas were created
        areas = self.env['ha.area'].search([
            ('ha_instance_id', '=', self.ha_instance.id)
        ])
        self.assertEqual(len(areas), 2, "Should create 2 areas")

        # Verify area data
        living_room = areas.filtered(lambda a: a.area_id == 'living_room')
        self.assertEqual(living_room.name, 'Living Room')
        self.assertEqual(living_room.icon, 'mdi:sofa')

        bedroom = areas.filtered(lambda a: a.area_id == 'bedroom')
        self.assertEqual(bedroom.name, 'Bedroom')
        self.assertEqual(bedroom.icon, 'mdi:bed')

    def test_sync_areas_from_ha_updates_existing_areas(self):
        """Test that sync_areas_from_ha updates existing areas"""
        # Create an existing area
        existing_area = self.env['ha.area'].create({
            'ha_instance_id': self.ha_instance.id,
            'area_id': 'living_room',
            'name': 'Old Living Room Name',
            'icon': 'mdi:old-icon',
        })

        # Prepare mock data with updated info
        mock_areas = [
            {
                'area_id': 'living_room',
                'name': 'Updated Living Room',
                'icon': 'mdi:sofa-outline',
                'aliases': ['main room'],
            },
        ]

        mock_client = self._mock_websocket_client(mock_areas)

        with patch(
            'odoo.addons.odoo_ha_addon.models.common.websocket_client.get_websocket_client',
            return_value=mock_client
        ):
            self.env['ha.area'].sync_areas_from_ha(instance_id=self.ha_instance.id)

        # Verify area was updated (not duplicated)
        areas = self.env['ha.area'].search([
            ('ha_instance_id', '=', self.ha_instance.id),
            ('area_id', '=', 'living_room')
        ])
        self.assertEqual(len(areas), 1, "Should not create duplicate")
        self.assertEqual(areas.name, 'Updated Living Room')
        self.assertEqual(areas.icon, 'mdi:sofa-outline')

    def test_sync_areas_handles_empty_response(self):
        """Test that sync_areas_from_ha handles empty responses gracefully"""
        mock_client = self._mock_websocket_client([])

        with patch(
            'odoo.addons.odoo_ha_addon.models.common.websocket_client.get_websocket_client',
            return_value=mock_client
        ):
            # Should not raise an exception
            self.env['ha.area'].sync_areas_from_ha(instance_id=self.ha_instance.id)

        areas = self.env['ha.area'].search([
            ('ha_instance_id', '=', self.ha_instance.id)
        ])
        self.assertEqual(len(areas), 0)

    def test_sync_areas_handles_invalid_response(self):
        """Test that sync_areas_from_ha handles invalid responses gracefully"""
        mock_client = self._mock_websocket_client(None)

        with patch(
            'odoo.addons.odoo_ha_addon.models.common.websocket_client.get_websocket_client',
            return_value=mock_client
        ):
            # Should not raise an exception
            self.env['ha.area'].sync_areas_from_ha(instance_id=self.ha_instance.id)

    def test_sync_areas_handles_missing_area_id(self):
        """Test that sync_areas_from_ha skips areas without area_id"""
        mock_areas = [
            {
                'name': 'No ID Area',  # Missing area_id
                'icon': 'mdi:error',
            },
            {
                'area_id': 'valid_area',
                'name': 'Valid Area',
            },
        ]

        mock_client = self._mock_websocket_client(mock_areas)

        with patch(
            'odoo.addons.odoo_ha_addon.models.common.websocket_client.get_websocket_client',
            return_value=mock_client
        ):
            self.env['ha.area'].sync_areas_from_ha(instance_id=self.ha_instance.id)

        areas = self.env['ha.area'].search([
            ('ha_instance_id', '=', self.ha_instance.id)
        ])
        self.assertEqual(len(areas), 1, "Should only create area with valid area_id")
        self.assertEqual(areas.area_id, 'valid_area')


@tagged('post_install', '-at_install')
class TestHAInstanceValidation(TransactionCase):
    """Test cases for HA instance validation"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test instances
        cls.active_instance = cls.env['ha.instance'].create({
            'name': 'Active Instance',
            'api_url': 'http://active-ha.local:8123',
            'api_token': 'active_token',
            'active': True,
        })

        cls.inactive_instance = cls.env['ha.instance'].create({
            'name': 'Inactive Instance',
            'api_url': 'http://inactive-ha.local:8123',
            'api_token': 'inactive_token',
            'active': False,
        })

        cls.unconfigured_instance = cls.env['ha.instance'].create({
            'name': 'Unconfigured Instance',
            'api_url': '',  # Missing API URL
            'api_token': '',  # Missing token
            'active': True,
        })

    def test_active_instance_is_valid(self):
        """Test that active, configured instance passes validation"""
        self.assertTrue(self.active_instance.active)
        self.assertTrue(self.active_instance.api_url)
        self.assertTrue(self.active_instance.api_token)

    def test_inactive_instance_validation(self):
        """Test that inactive instance is properly flagged"""
        self.assertFalse(self.inactive_instance.active)

    def test_unconfigured_instance_detection(self):
        """Test that unconfigured instance is properly detected"""
        self.assertFalse(self.unconfigured_instance.api_url)
        self.assertFalse(self.unconfigured_instance.api_token)


@tagged('post_install', '-at_install')
class TestAreaInstanceIsolation(TransactionCase):
    """Test cases for multi-instance area isolation"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create two HA instances
        cls.instance_1 = cls.env['ha.instance'].create({
            'name': 'Instance 1',
            'api_url': 'http://ha1.local:8123',
            'api_token': 'token1',
            'active': True,
        })

        cls.instance_2 = cls.env['ha.instance'].create({
            'name': 'Instance 2',
            'api_url': 'http://ha2.local:8123',
            'api_token': 'token2',
            'active': True,
        })

    def test_areas_are_isolated_between_instances(self):
        """Test that areas from different instances don't interfere"""
        # Create areas for instance 1
        area_1 = self.env['ha.area'].create({
            'ha_instance_id': self.instance_1.id,
            'area_id': 'living_room',
            'name': 'Instance 1 Living Room',
        })

        # Create area with same area_id for instance 2
        area_2 = self.env['ha.area'].create({
            'ha_instance_id': self.instance_2.id,
            'area_id': 'living_room',
            'name': 'Instance 2 Living Room',
        })

        # Verify they are separate records
        self.assertNotEqual(area_1.id, area_2.id)
        self.assertEqual(area_1.name, 'Instance 1 Living Room')
        self.assertEqual(area_2.name, 'Instance 2 Living Room')

        # Verify search by instance filters correctly
        instance_1_areas = self.env['ha.area'].search([
            ('ha_instance_id', '=', self.instance_1.id)
        ])
        instance_2_areas = self.env['ha.area'].search([
            ('ha_instance_id', '=', self.instance_2.id)
        ])

        self.assertEqual(len(instance_1_areas), 1)
        self.assertEqual(len(instance_2_areas), 1)
        self.assertIn(area_1, instance_1_areas)
        self.assertIn(area_2, instance_2_areas)

    def test_area_unique_constraint_per_instance(self):
        """Test that area_id must be unique within an instance"""
        # Create first area
        self.env['ha.area'].create({
            'ha_instance_id': self.instance_1.id,
            'area_id': 'unique_area',
            'name': 'First Area',
        })

        # Attempt to create duplicate should fail
        from psycopg2 import IntegrityError
        with self.assertRaises(IntegrityError):
            self.env['ha.area'].create({
                'ha_instance_id': self.instance_1.id,
                'area_id': 'unique_area',  # Same area_id, same instance
                'name': 'Duplicate Area',
            })
            self.env.cr.commit()  # Force the constraint check
