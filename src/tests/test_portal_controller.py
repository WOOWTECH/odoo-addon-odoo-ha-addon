# -*- coding: utf-8 -*-
# Part of odoo_ha_addon. See LICENSE file for full copyright and licensing details.

"""
Integration tests for portal controller endpoints with user-based authentication.

This module tests the portal access for entities and entity groups using
ha.entity.share records for authorization:
- Valid share access (200 response)
- No share access (403 response)
- Non-existent record access (404 response)
- Permission level checks (view vs control)
- Expired share handling
- Polling endpoint JSON responses
"""

import json
from datetime import timedelta
from odoo.tests import HttpCase, tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestPortalEntityController(HttpCase):
    """Integration tests for entity portal routes with user-based auth"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a test HA instance
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Portal Test HA Instance',
            'api_url': 'http://portal-test-ha.local:8123',
            'api_token': 'portal_test_token_12345',
            'active': True,
        })

        # Create a test user for portal access
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Portal Test User',
            'login': 'portal_test_user',
            'password': 'portal_test_password',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def test_portal_entity_with_share(self):
        """Test portal entity page loads successfully with valid share"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Portal Test Entity',
            'entity_id': 'sensor.portal_test',
            'domain': 'sensor',
            'entity_state': 'on',
            'ha_instance_id': self.ha_instance.id,
        })

        # Create share for portal user
        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        # Authenticate as portal user
        self.authenticate('portal_test_user', 'portal_test_password')

        url = f'/portal/entity/{entity.id}'
        response = self.url_open(url)

        self.assertEqual(
            response.status_code,
            200,
            "Valid share should grant access to portal page"
        )
        self.assertIn(
            'Portal Test Entity',
            response.text,
            "Portal page should display entity name"
        )

    def test_portal_entity_no_share(self):
        """Test portal entity page returns 403 without share"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'No Share Entity',
            'entity_id': 'sensor.no_share_test',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })

        # Authenticate as portal user (no share created)
        self.authenticate('portal_test_user', 'portal_test_password')

        url = f'/portal/entity/{entity.id}'
        response = self.url_open(url)

        self.assertEqual(
            response.status_code,
            403,
            "Missing share should return 403 status"
        )

    def test_portal_entity_expired_share(self):
        """Test portal entity page returns 403 with expired share"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Expired Share Entity',
            'entity_id': 'sensor.expired_share_test',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })

        # Create expired share
        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
            'expiry_date': fields.Datetime.now() - timedelta(days=1),
        })

        self.authenticate('portal_test_user', 'portal_test_password')

        url = f'/portal/entity/{entity.id}'
        response = self.url_open(url)

        self.assertEqual(
            response.status_code,
            403,
            "Expired share should return 403 status"
        )

    def test_portal_entity_not_found(self):
        """Test portal entity page returns 404 for non-existent entity"""
        self.authenticate('portal_test_user', 'portal_test_password')

        url = '/portal/entity/999999'
        response = self.url_open(url)

        self.assertEqual(
            response.status_code,
            404,
            "Non-existent entity should return 404 status"
        )

    def test_portal_entity_unauthenticated_redirect(self):
        """Test unauthenticated user is redirected to login"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Redirect Test Entity',
            'entity_id': 'sensor.redirect_test',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })

        # Don't authenticate
        url = f'/portal/entity/{entity.id}'
        response = self.url_open(url, allow_redirects=False)

        # Odoo redirects unauthenticated users to login
        self.assertIn(
            response.status_code,
            [302, 303],
            "Unauthenticated user should be redirected"
        )

    def test_portal_entity_state_endpoint_with_share(self):
        """Test polling endpoint returns JSON with valid share"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Polling Test Entity',
            'entity_id': 'sensor.polling_test',
            'domain': 'sensor',
            'entity_state': '42.5',
            'ha_instance_id': self.ha_instance.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        self.authenticate('portal_test_user', 'portal_test_password')

        url = f'/portal/entity/{entity.id}/state'
        response = self.url_open(
            url,
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'id': 1,
                'params': {}
            }),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()

        # JSON-RPC response format
        self.assertIn('result', result, "Response should have 'result' key")

        result_data = result.get('result', {})
        self.assertTrue(
            result_data.get('success'),
            "Response should indicate success"
        )
        self.assertIn('data', result_data, "Response should have 'data' key")

        data = result_data.get('data', {})
        self.assertEqual(
            data.get('entity_state'),
            '42.5',
            "Response should include entity_state"
        )

    def test_portal_entity_state_endpoint_no_share(self):
        """Test polling endpoint returns error without share"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'No Share Polling Entity',
            'entity_id': 'sensor.no_share_polling',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })

        self.authenticate('portal_test_user', 'portal_test_password')

        url = f'/portal/entity/{entity.id}/state'
        response = self.url_open(
            url,
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'id': 1,
                'params': {}
            }),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        result_data = result.get('result', {})

        self.assertIn(
            'error',
            result_data,
            "No share should return error in response"
        )
        self.assertEqual(
            result_data.get('error_code'),
            'access_denied',
            "Error code should be 'access_denied'"
        )


@tagged('post_install', '-at_install')
class TestPortalEntityGroupController(HttpCase):
    """Integration tests for entity group portal routes with user-based auth"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a test HA instance
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Group Portal Test HA Instance',
            'api_url': 'http://group-portal-test.local:8123',
            'api_token': 'group_portal_test_token_12345',
            'active': True,
        })

        # Create a test user for portal access
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Group Portal Test User',
            'login': 'group_portal_test_user',
            'password': 'group_portal_test_password',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def test_portal_entity_group_with_share(self):
        """Test portal entity group page loads successfully with valid share"""
        group = self.env['ha.entity.group'].sudo().create({
            'name': 'Portal Test Group',
            'description': 'A test group for portal access',
            'ha_instance_id': self.ha_instance.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'group_id': group.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        self.authenticate('group_portal_test_user', 'group_portal_test_password')

        url = f'/portal/entity_group/{group.id}'
        response = self.url_open(url)

        self.assertEqual(
            response.status_code,
            200,
            "Valid share should grant access to group portal page"
        )
        self.assertIn(
            'Portal Test Group',
            response.text,
            "Portal page should display group name"
        )

    def test_portal_entity_group_no_share(self):
        """Test portal entity group page returns 403 without share"""
        group = self.env['ha.entity.group'].sudo().create({
            'name': 'No Share Group',
            'ha_instance_id': self.ha_instance.id,
        })

        self.authenticate('group_portal_test_user', 'group_portal_test_password')

        url = f'/portal/entity_group/{group.id}'
        response = self.url_open(url)

        self.assertEqual(
            response.status_code,
            403,
            "Missing share should return 403 status"
        )

    def test_portal_entity_group_not_found(self):
        """Test portal entity group page returns 404 for non-existent group"""
        self.authenticate('group_portal_test_user', 'group_portal_test_password')

        url = '/portal/entity_group/999999'
        response = self.url_open(url)

        self.assertEqual(
            response.status_code,
            404,
            "Non-existent group should return 404 status"
        )

    def test_portal_entity_group_with_entities(self):
        """Test portal group page shows entities when present"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Group Member Entity',
            'entity_id': 'sensor.group_member',
            'domain': 'sensor',
            'entity_state': 'active',
            'ha_instance_id': self.ha_instance.id,
        })

        group = self.env['ha.entity.group'].sudo().create({
            'name': 'Group With Entities',
            'ha_instance_id': self.ha_instance.id,
            'entity_ids': [(6, 0, [entity.id])],
        })

        self.env['ha.entity.share'].sudo().create({
            'group_id': group.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        self.authenticate('group_portal_test_user', 'group_portal_test_password')

        url = f'/portal/entity_group/{group.id}'
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Group Member Entity',
            response.text,
            "Portal page should display member entity name"
        )

    def test_portal_entity_group_state_endpoint_with_share(self):
        """Test group polling endpoint returns JSON with valid share"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Group State Entity',
            'entity_id': 'sensor.group_state',
            'domain': 'sensor',
            'entity_state': '100',
            'ha_instance_id': self.ha_instance.id,
        })

        group = self.env['ha.entity.group'].sudo().create({
            'name': 'State Polling Group',
            'ha_instance_id': self.ha_instance.id,
            'entity_ids': [(6, 0, [entity.id])],
        })

        self.env['ha.entity.share'].sudo().create({
            'group_id': group.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        self.authenticate('group_portal_test_user', 'group_portal_test_password')

        url = f'/portal/entity_group/{group.id}/state'
        response = self.url_open(
            url,
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'id': 1,
                'params': {}
            }),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        result_data = result.get('result', {})

        self.assertTrue(
            result_data.get('success'),
            "Response should indicate success"
        )
        self.assertIn('data', result_data)

        data = result_data.get('data', {})
        self.assertIn(
            'entities',
            data,
            "Response should include entities list"
        )

        entities = data.get('entities', [])
        self.assertEqual(
            len(entities),
            1,
            "Response should include one entity"
        )
        self.assertEqual(
            entities[0].get('entity_state'),
            '100',
            "Entity state should be included in response"
        )


@tagged('post_install', '-at_install')
class TestPortalPermissionLevels(HttpCase):
    """Tests for portal permission levels (view vs control)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Permission Test HA Instance',
            'api_url': 'http://permission-test.local:8123',
            'api_token': 'permission_test_token_12345',
            'active': True,
        })

        cls.portal_user = cls.env['res.users'].create({
            'name': 'Permission Test User',
            'login': 'permission_test_user',
            'password': 'permission_test_password',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def test_view_permission_shows_view_only_notice(self):
        """Test view permission shows view-only notice instead of controls"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'View Permission Entity',
            'entity_id': 'switch.view_permission',
            'domain': 'switch',
            'entity_state': 'off',
            'ha_instance_id': self.ha_instance.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        self.authenticate('permission_test_user', 'permission_test_password')

        url = f'/portal/entity/{entity.id}'
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        # View permission should show view-only notice
        self.assertIn('View Only', response.text, "Should show view-only notice")
        # View permission should NOT show control card
        self.assertNotIn('id="control-card"', response.text, "Should not show control card")

    def test_control_permission_shows_controls(self):
        """Test control permission shows control UI"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Control Permission Entity',
            'entity_id': 'switch.control_permission',
            'domain': 'switch',
            'entity_state': 'off',
            'ha_instance_id': self.ha_instance.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'control',
        })

        self.authenticate('permission_test_user', 'permission_test_password')

        url = f'/portal/entity/{entity.id}'
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        # Control permission should show control card
        self.assertIn('id="control-card"', response.text, "Should show control card")


@tagged('post_install', '-at_install')
class TestPortalCallServiceController(HttpCase):
    """Integration tests for unified /portal/call-service endpoint with user-based auth"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Call Service Test HA Instance',
            'api_url': 'http://call-service-test.local:8123',
            'api_token': 'call_service_test_token_12345',
            'active': True,
        })

        cls.portal_user = cls.env['res.users'].create({
            'name': 'Call Service Test User',
            'login': 'call_service_test_user',
            'password': 'call_service_test_password',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def _make_call_service_request(self, domain, service, service_data):
        """Helper method to make call-service requests"""
        url = '/portal/call-service'
        return self.url_open(
            url,
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'id': 1,
                'params': {
                    'domain': domain,
                    'service': service,
                    'service_data': service_data,
                }
            }),
            headers={'Content-Type': 'application/json'}
        )

    def test_call_service_no_share(self):
        """Test call-service returns error without share"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'No Share Service Entity',
            'entity_id': 'switch.no_share_service',
            'domain': 'switch',
            'entity_state': 'off',
            'ha_instance_id': self.ha_instance.id,
        })

        self.authenticate('call_service_test_user', 'call_service_test_password')

        response = self._make_call_service_request(
            domain='switch',
            service='toggle',
            service_data={'entity_id': entity.id}
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        result_data = result.get('result', {})

        self.assertFalse(result_data.get('success'))
        self.assertEqual(result_data.get('error_code'), 'access_denied')

    def test_call_service_view_permission_denied(self):
        """Test call-service returns error with view-only permission"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'View Only Service Entity',
            'entity_id': 'switch.view_only_service',
            'domain': 'switch',
            'entity_state': 'off',
            'ha_instance_id': self.ha_instance.id,
        })

        # Create view-only share
        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',  # view-only, not control
        })

        self.authenticate('call_service_test_user', 'call_service_test_password')

        response = self._make_call_service_request(
            domain='switch',
            service='toggle',
            service_data={'entity_id': entity.id}
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        result_data = result.get('result', {})

        self.assertFalse(result_data.get('success'))
        self.assertEqual(
            result_data.get('error_code'),
            'access_denied',
            "View-only permission should not allow control"
        )

    def test_call_service_control_permission_allowed(self):
        """Test call-service accepts request with control permission"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Control Service Entity',
            'entity_id': 'switch.control_service',
            'domain': 'switch',
            'entity_state': 'off',
            'ha_instance_id': self.ha_instance.id,
        })

        # Create control share
        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'control',
        })

        self.authenticate('call_service_test_user', 'call_service_test_password')

        response = self._make_call_service_request(
            domain='switch',
            service='toggle',
            service_data={'entity_id': entity.id}
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        result_data = result.get('result', {})

        # Should not be access_denied (might fail for other reasons like no HA)
        self.assertNotEqual(
            result_data.get('error_code'),
            'access_denied',
            "Control permission should allow service calls"
        )

    def test_call_service_missing_params(self):
        """Test call-service returns error when required params are missing"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Missing Params Entity',
            'entity_id': 'switch.missing_params',
            'domain': 'switch',
            'entity_state': 'off',
            'ha_instance_id': self.ha_instance.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'control',
        })

        self.authenticate('call_service_test_user', 'call_service_test_password')

        # Test missing domain
        response = self._make_call_service_request(
            domain=None,
            service='toggle',
            service_data={'entity_id': entity.id}
        )
        result = response.json().get('result', {})
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('error_code'), 'missing_params')

        # Test missing entity_id in service_data
        response = self._make_call_service_request(
            domain='switch',
            service='toggle',
            service_data={}
        )
        result = response.json().get('result', {})
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('error_code'), 'missing_entity_id')

    def test_call_service_domain_not_allowed(self):
        """Test call-service returns error for unsupported domain"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Unsupported Domain Entity',
            'entity_id': 'unknown.unsupported_domain',
            'domain': 'unknown',
            'entity_state': '42',
            'ha_instance_id': self.ha_instance.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'control',
        })

        self.authenticate('call_service_test_user', 'call_service_test_password')

        response = self._make_call_service_request(
            domain='unknown',
            service='toggle',
            service_data={'entity_id': entity.id}
        )

        result = response.json().get('result', {})
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('error_code'), 'domain_denied')

    def test_call_service_service_not_allowed(self):
        """Test call-service returns error for invalid service"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Invalid Service Entity',
            'entity_id': 'switch.invalid_service',
            'domain': 'switch',
            'entity_state': 'off',
            'ha_instance_id': self.ha_instance.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'control',
        })

        self.authenticate('call_service_test_user', 'call_service_test_password')

        response = self._make_call_service_request(
            domain='switch',
            service='set_brightness',  # set_brightness not allowed for switch
            service_data={'entity_id': entity.id}
        )

        result = response.json().get('result', {})
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('error_code'), 'service_denied')

    def test_call_service_entity_not_found(self):
        """Test call-service returns error for non-existent entity"""
        self.authenticate('call_service_test_user', 'call_service_test_password')

        response = self._make_call_service_request(
            domain='switch',
            service='toggle',
            service_data={'entity_id': 999999}
        )

        result = response.json().get('result', {})
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('error_code'), 'not_found')

    def test_call_service_expired_share(self):
        """Test call-service returns error with expired share"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Expired Share Service Entity',
            'entity_id': 'switch.expired_share_service',
            'domain': 'switch',
            'entity_state': 'off',
            'ha_instance_id': self.ha_instance.id,
        })

        # Create expired share with control permission
        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'control',
            'expiry_date': fields.Datetime.now() - timedelta(days=1),
        })

        self.authenticate('call_service_test_user', 'call_service_test_password')

        response = self._make_call_service_request(
            domain='switch',
            service='toggle',
            service_data={'entity_id': entity.id}
        )

        result = response.json().get('result', {})
        self.assertFalse(result.get('success'))
        self.assertEqual(
            result.get('error_code'),
            'access_denied',
            "Expired share should deny access"
        )

    def test_call_service_whitelist_switch(self):
        """Test call-service whitelist for switch domain"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Switch Whitelist Entity',
            'entity_id': 'switch.whitelist_test',
            'domain': 'switch',
            'entity_state': 'off',
            'ha_instance_id': self.ha_instance.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'control',
        })

        self.authenticate('call_service_test_user', 'call_service_test_password')

        allowed_services = ['toggle', 'turn_on', 'turn_off']
        for service in allowed_services:
            response = self._make_call_service_request(
                domain='switch',
                service=service,
                service_data={'entity_id': entity.id}
            )
            result = response.json().get('result', {})
            # Should NOT be service_denied (might fail for other reasons like no HA)
            self.assertNotEqual(
                result.get('error_code'),
                'service_denied',
                f"Service '{service}' should be allowed for switch"
            )

    def test_call_service_sensor_readonly(self):
        """Test call-service returns error for sensor (read-only domain)"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Sensor Read-only Entity',
            'entity_id': 'sensor.readonly_test',
            'domain': 'sensor',
            'entity_state': '25.5',
            'ha_instance_id': self.ha_instance.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'control',
        })

        self.authenticate('call_service_test_user', 'call_service_test_password')

        # Sensor is in whitelist but with empty actions list (read-only)
        for service in ['toggle', 'turn_on', 'turn_off']:
            response = self._make_call_service_request(
                domain='sensor',
                service=service,
                service_data={'entity_id': entity.id}
            )

            result = response.json().get('result', {})
            self.assertFalse(
                result.get('success'),
                f"Sensor should reject '{service}' service"
            )
            self.assertEqual(
                result.get('error_code'),
                'service_denied',
                f"Sensor '{service}' should return 'service_denied'"
            )


@tagged('post_install', '-at_install')
class TestPortalSecurityMeasures(HttpCase):
    """Tests for portal security measures with user-based auth"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Security Test HA Instance',
            'api_url': 'http://security-test.local:8123',
            'api_token': 'security_test_token_12345',
            'active': True,
        })

        cls.portal_user = cls.env['res.users'].create({
            'name': 'Security Test User',
            'login': 'security_test_user',
            'password': 'security_test_password',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def test_field_whitelist_entity(self):
        """Test that only whitelisted fields are exposed for entities"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Whitelist Test Entity',
            'entity_id': 'sensor.whitelist_test',
            'domain': 'sensor',
            'entity_state': 'test_state',
            'note': 'This is a secret note',  # Should NOT be exposed
            'ha_instance_id': self.ha_instance.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        self.authenticate('security_test_user', 'security_test_password')

        url = f'/portal/entity/{entity.id}/state'
        response = self.url_open(
            url,
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'id': 1,
                'params': {}
            }),
            headers={'Content-Type': 'application/json'}
        )

        result = response.json()
        result_data = result.get('result', {})
        data = result_data.get('data', {})

        # Verify whitelisted fields are present
        self.assertIn('entity_id', data)
        self.assertIn('entity_state', data)
        self.assertIn('name', data)

        # Verify non-whitelisted fields are NOT present
        self.assertNotIn(
            'note',
            data,
            "Internal note should not be exposed via portal"
        )
        self.assertNotIn(
            'enable_record',
            data,
            "Internal settings should not be exposed via portal"
        )
