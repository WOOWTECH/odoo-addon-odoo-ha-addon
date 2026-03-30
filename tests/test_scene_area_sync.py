# Part of odoo_ha_addon. See LICENSE file for full copyright and licensing details.
"""
雙向測試：場景分區同步

測試場景：
- Odoo → HA：在 Odoo 中新建/更新場景的 area，應同步到 HA
- HA → Odoo：在 HA 中修改場景的 area，Odoo 應更新

問題背景：
- 在 Odoo 中新增的場景，選擇的分區不會同步到 HA
- 根本原因：_create_scene_in_ha() 只建立 scene config，未呼叫 entity_registry/update 同步 area
"""

from unittest.mock import patch, MagicMock, call
from odoo.tests import TransactionCase, tagged
import time


@tagged('post_install', '-at_install')
class TestSceneAreaSyncOdooToHA(TransactionCase):
    """測試場景分區從 Odoo 同步到 HA"""

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

        # Create test areas
        cls.area_living_room = cls.env['ha.area'].create({
            'ha_instance_id': cls.ha_instance.id,
            'area_id': 'living_room',
            'name': '客廳',
        })

        cls.area_bedroom = cls.env['ha.area'].create({
            'ha_instance_id': cls.ha_instance.id,
            'area_id': 'bedroom',
            'name': '臥室',
        })

        # Create a test entity for scene to include
        cls.test_light = cls.env['ha.entity'].create({
            'ha_instance_id': cls.ha_instance.id,
            'entity_id': 'light.test_light',
            'domain': 'light',
            'name': 'Test Light',
            'state': 'on',
        })

    def setUp(self):
        super().setUp()
        # Clean up any existing test scenes
        self.env['ha.entity'].search([
            ('ha_instance_id', '=', self.ha_instance.id),
            ('domain', '=', 'scene'),
            ('entity_id', 'like', 'scene.test_%'),
        ]).unlink()

    def _mock_rest_api(self):
        """Create a mock REST API client"""
        mock_api = MagicMock()
        mock_api.create_scene_config.return_value = {'result': 'success'}
        mock_api.get_entity_states.return_value = {
            'light.test_light': {'state': 'on', 'brightness': 255}
        }
        return mock_api

    def _mock_websocket_client(self):
        """Create a mock WebSocket client"""
        mock_client = MagicMock()
        mock_client.call_websocket_api_sync.return_value = {
            'entity_entry': {
                'entity_id': 'scene.test_scene',
                'area_id': 'living_room',
            }
        }
        return mock_client

    def test_create_scene_with_area_syncs_to_ha(self):
        """新建場景時設定 area，應同步到 HA"""
        mock_rest_api = self._mock_rest_api()
        mock_ws_client = self._mock_websocket_client()

        with patch(
            'odoo.addons.odoo_ha_addon.models.ha_entity.HassRestApi',
            return_value=mock_rest_api
        ), patch(
            'odoo.addons.odoo_ha_addon.models.common.websocket_client.get_websocket_client',
            return_value=mock_ws_client
        ):
            # Create scene with area
            scene = self.env['ha.entity'].create({
                'ha_instance_id': self.ha_instance.id,
                'entity_id': f'scene.test_scene_{int(time.time())}',
                'domain': 'scene',
                'name': 'Test Scene',
                'state': 'scening',
                'area_id': self.area_living_room.id,
                'scene_entity_ids': [(6, 0, [self.test_light.id])],
            })

            # Trigger postcommit hooks manually (in tests they don't auto-run)
            self.env.cr.postcommit.run()

            # Verify scene config was created
            mock_rest_api.create_scene_config.assert_called_once()

            # Verify entity_registry/update was called with area_id
            # This is the key assertion - area should be synced
            ws_calls = mock_ws_client.call_websocket_api_sync.call_args_list
            area_update_calls = [
                c for c in ws_calls
                if c[0][0] == 'config/entity_registry/update'
            ]

            self.assertGreaterEqual(
                len(area_update_calls), 1,
                "entity_registry/update should be called to sync area"
            )

            # Check that area_id was passed correctly
            area_call = area_update_calls[0]
            payload = area_call[0][1]
            self.assertEqual(
                payload.get('area_id'), 'living_room',
                "area_id should be 'living_room'"
            )

    def test_update_scene_area_syncs_to_ha(self):
        """更新場景的 area，應同步到 HA"""
        mock_rest_api = self._mock_rest_api()
        mock_ws_client = self._mock_websocket_client()

        with patch(
            'odoo.addons.odoo_ha_addon.models.ha_entity.HassRestApi',
            return_value=mock_rest_api
        ), patch(
            'odoo.addons.odoo_ha_addon.models.common.websocket_client.get_websocket_client',
            return_value=mock_ws_client
        ):
            # Create scene without area first
            scene = self.env['ha.entity'].create({
                'ha_instance_id': self.ha_instance.id,
                'entity_id': f'scene.test_scene_{int(time.time())}',
                'domain': 'scene',
                'name': 'Test Scene',
                'state': 'scening',
                'scene_entity_ids': [(6, 0, [self.test_light.id])],
            })
            self.env.cr.postcommit.run()

            # Reset mock to track only update calls
            mock_ws_client.reset_mock()

            # Update area
            scene.write({'area_id': self.area_bedroom.id})

            # Verify entity_registry/update was called
            mock_ws_client.call_websocket_api_sync.assert_called()

            # Find the area update call
            ws_calls = mock_ws_client.call_websocket_api_sync.call_args_list
            area_update_calls = [
                c for c in ws_calls
                if c[0][0] == 'config/entity_registry/update'
            ]

            self.assertGreaterEqual(
                len(area_update_calls), 1,
                "entity_registry/update should be called when area changes"
            )

            payload = area_update_calls[0][0][1]
            self.assertEqual(
                payload.get('area_id'), 'bedroom',
                "area_id should be 'bedroom'"
            )

    def test_clear_scene_area_syncs_null_to_ha(self):
        """清除場景的 area，應同步 null 到 HA"""
        mock_rest_api = self._mock_rest_api()
        mock_ws_client = self._mock_websocket_client()

        with patch(
            'odoo.addons.odoo_ha_addon.models.ha_entity.HassRestApi',
            return_value=mock_rest_api
        ), patch(
            'odoo.addons.odoo_ha_addon.models.common.websocket_client.get_websocket_client',
            return_value=mock_ws_client
        ):
            # Create scene with area
            scene = self.env['ha.entity'].create({
                'ha_instance_id': self.ha_instance.id,
                'entity_id': f'scene.test_scene_{int(time.time())}',
                'domain': 'scene',
                'name': 'Test Scene',
                'state': 'scening',
                'area_id': self.area_living_room.id,
                'scene_entity_ids': [(6, 0, [self.test_light.id])],
            })
            self.env.cr.postcommit.run()

            # Reset mock
            mock_ws_client.reset_mock()

            # Clear area (set to False)
            scene.write({'area_id': False})

            # Verify entity_registry/update was called with null area
            ws_calls = mock_ws_client.call_websocket_api_sync.call_args_list
            area_update_calls = [
                c for c in ws_calls
                if c[0][0] == 'config/entity_registry/update'
            ]

            self.assertGreaterEqual(
                len(area_update_calls), 1,
                "entity_registry/update should be called when area is cleared"
            )

            payload = area_update_calls[0][0][1]
            self.assertIsNone(
                payload.get('area_id'),
                "area_id should be None (null) when cleared"
            )


@tagged('post_install', '-at_install')
class TestSceneAreaSyncHAToOdoo(TransactionCase):
    """測試場景分區從 HA 同步到 Odoo"""

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

        # Create test areas
        cls.area_living_room = cls.env['ha.area'].create({
            'ha_instance_id': cls.ha_instance.id,
            'area_id': 'living_room',
            'name': '客廳',
        })

        cls.area_bedroom = cls.env['ha.area'].create({
            'ha_instance_id': cls.ha_instance.id,
            'area_id': 'bedroom',
            'name': '臥室',
        })

    def setUp(self):
        super().setUp()
        # Clean up any existing test scenes
        self.env['ha.entity'].search([
            ('ha_instance_id', '=', self.ha_instance.id),
            ('domain', '=', 'scene'),
            ('entity_id', 'like', 'scene.test_%'),
        ]).unlink()

    def test_ha_scene_area_change_updates_odoo(self):
        """HA 中修改場景 area，Odoo 應更新"""
        # Create scene in Odoo with area = living_room
        scene = self.env['ha.entity'].with_context(from_ha_sync=True).create({
            'ha_instance_id': self.ha_instance.id,
            'entity_id': 'scene.test_scene_ha_sync',
            'domain': 'scene',
            'name': 'Test Scene',
            'state': 'scening',
            'area_id': self.area_living_room.id,
        })

        self.assertEqual(
            scene.area_id.id, self.area_living_room.id,
            "Initial area should be living_room"
        )

        # Simulate HA sync event - area changed to bedroom
        scene.with_context(from_ha_sync=True).write({
            'area_id': self.area_bedroom.id,
        })

        # Verify Odoo record was updated
        scene.invalidate_recordset()
        self.assertEqual(
            scene.area_id.id, self.area_bedroom.id,
            "Area should be updated to bedroom"
        )

    def test_ha_scene_area_clear_updates_odoo(self):
        """HA 中清除場景 area，Odoo 應更新"""
        # Create scene in Odoo with area = living_room
        scene = self.env['ha.entity'].with_context(from_ha_sync=True).create({
            'ha_instance_id': self.ha_instance.id,
            'entity_id': 'scene.test_scene_ha_clear',
            'domain': 'scene',
            'name': 'Test Scene',
            'state': 'scening',
            'area_id': self.area_living_room.id,
        })

        self.assertEqual(
            scene.area_id.id, self.area_living_room.id,
            "Initial area should be living_room"
        )

        # Simulate HA sync event - area cleared (null)
        scene.with_context(from_ha_sync=True).write({
            'area_id': False,
        })

        # Verify Odoo record was updated
        scene.invalidate_recordset()
        self.assertFalse(
            scene.area_id,
            "Area should be cleared (False)"
        )


@tagged('post_install', '-at_install')
class TestSceneCreateWithAreaIntegration(TransactionCase):
    """整合測試：場景建立時的完整 area 同步流程"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Test HA Instance',
            'api_url': 'http://test-ha.local:8123',
            'api_token': 'test_token_12345',
            'active': True,
        })

        cls.area = cls.env['ha.area'].create({
            'ha_instance_id': cls.ha_instance.id,
            'area_id': 'test_area',
            'name': 'Test Area',
        })

        cls.test_light = cls.env['ha.entity'].create({
            'ha_instance_id': cls.ha_instance.id,
            'entity_id': 'light.integration_test_light',
            'domain': 'light',
            'name': 'Integration Test Light',
            'state': 'on',
        })

    def test_scene_create_calls_both_scene_config_and_area_update(self):
        """
        建立場景時應同時呼叫：
        1. create_scene_config (REST API) - 建立場景配置
        2. entity_registry/update (WebSocket) - 同步 area_id
        """
        mock_rest_api = MagicMock()
        mock_rest_api.create_scene_config.return_value = {'result': 'success'}
        mock_rest_api.get_entity_states.return_value = {
            'light.integration_test_light': {'state': 'on'}
        }

        mock_ws_client = MagicMock()
        mock_ws_client.call_websocket_api_sync.return_value = {
            'entity_entry': {'entity_id': 'scene.integration_test'}
        }

        with patch(
            'odoo.addons.odoo_ha_addon.models.ha_entity.HassRestApi',
            return_value=mock_rest_api
        ), patch(
            'odoo.addons.odoo_ha_addon.models.common.websocket_client.get_websocket_client',
            return_value=mock_ws_client
        ):
            # Create scene with area and entities
            scene = self.env['ha.entity'].create({
                'ha_instance_id': self.ha_instance.id,
                'entity_id': f'scene.integration_test_{int(time.time())}',
                'domain': 'scene',
                'name': 'Integration Test Scene',
                'state': 'scening',
                'area_id': self.area.id,
                'scene_entity_ids': [(6, 0, [self.test_light.id])],
            })

            # Run postcommit hooks
            self.env.cr.postcommit.run()

            # Assertion 1: Scene config was created via REST API
            self.assertTrue(
                mock_rest_api.create_scene_config.called,
                "create_scene_config should be called"
            )

            # Assertion 2: Area was synced via WebSocket API
            ws_calls = mock_ws_client.call_websocket_api_sync.call_args_list
            area_update_called = any(
                c[0][0] == 'config/entity_registry/update' and
                c[0][1].get('area_id') == 'test_area'
                for c in ws_calls
            )

            self.assertTrue(
                area_update_called,
                "entity_registry/update should be called with area_id='test_area'"
            )
