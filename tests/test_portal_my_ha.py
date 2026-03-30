# -*- coding: utf-8 -*-
# Part of odoo_ha_addon. See LICENSE file for full copyright and licensing details.

"""
Integration tests for Portal /my/ha routes.

This module tests the portal integration for accessing shared HA entities
and entity groups via the /my account page:
- /my/ha route (instance list)
- /my/ha/<instance_id> route (entity/group tabs)
- Access control for users with/without shares
- Tab switching functionality
"""

from datetime import timedelta
from odoo.tests import HttpCase, tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestPortalMyHaRoutes(HttpCase):
    """Integration tests for /my/ha portal routes"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test HA instances
        cls.ha_instance_1 = cls.env['ha.instance'].create({
            'name': 'My HA Test Instance 1',
            'api_url': 'http://my-ha-test-1.local:8123',
            'api_token': 'my_ha_test_token_1',
            'active': True,
        })
        cls.ha_instance_2 = cls.env['ha.instance'].create({
            'name': 'My HA Test Instance 2',
            'api_url': 'http://my-ha-test-2.local:8123',
            'api_token': 'my_ha_test_token_2',
            'active': True,
        })

        # Create a portal user
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Portal My HA Test User',
            'login': 'portal_my_ha_user',
            'password': 'portal_my_ha_password',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

        # Create another portal user with no shares
        cls.portal_user_no_shares = cls.env['res.users'].create({
            'name': 'Portal No Shares User',
            'login': 'portal_no_shares_user',
            'password': 'portal_no_shares_password',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def test_my_ha_with_shares(self):
        """Test /my/ha page shows instances when user has shares"""
        # Create an entity and share it
        entity = self.env['ha.entity'].sudo().create({
            'name': 'My HA Test Entity',
            'entity_id': 'sensor.my_ha_test',
            'domain': 'sensor',
            'entity_state': '25.5',
            'ha_instance_id': self.ha_instance_1.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        self.authenticate('portal_my_ha_user', 'portal_my_ha_password')

        url = '/my/ha'
        response = self.url_open(url)

        self.assertEqual(
            response.status_code,
            200,
            "Should be able to access /my/ha with shares"
        )
        self.assertIn(
            'My HA Test Instance 1',
            response.text,
            "Should display instance name"
        )

    def test_my_ha_no_shares(self):
        """Test /my/ha page shows empty state when user has no shares"""
        self.authenticate('portal_no_shares_user', 'portal_no_shares_password')

        url = '/my/ha'
        response = self.url_open(url)

        self.assertEqual(
            response.status_code,
            200,
            "Should load /my/ha page even without shares"
        )
        self.assertIn(
            'No Shared Devices',
            response.text,
            "Should show empty state message"
        )

    def test_my_ha_multiple_instances(self):
        """Test /my/ha page shows multiple instances"""
        # Create entities in both instances
        entity_1 = self.env['ha.entity'].sudo().create({
            'name': 'Multi Instance Entity 1',
            'entity_id': 'sensor.multi_1',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance_1.id,
        })
        entity_2 = self.env['ha.entity'].sudo().create({
            'name': 'Multi Instance Entity 2',
            'entity_id': 'sensor.multi_2',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance_2.id,
        })

        # Share both with the user
        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity_1.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })
        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity_2.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        self.authenticate('portal_my_ha_user', 'portal_my_ha_password')

        url = '/my/ha'
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'My HA Test Instance 1',
            response.text,
            "Should display first instance"
        )
        self.assertIn(
            'My HA Test Instance 2',
            response.text,
            "Should display second instance"
        )

    def test_my_ha_unauthenticated_redirect(self):
        """Test unauthenticated access to /my/ha redirects to login"""
        url = '/my/ha'
        response = self.url_open(url, allow_redirects=False)

        self.assertIn(
            response.status_code,
            [302, 303],
            "Unauthenticated user should be redirected"
        )


@tagged('post_install', '-at_install')
class TestPortalMyHaInstanceDetail(HttpCase):
    """Integration tests for /my/ha/<instance_id> route"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Instance Detail Test',
            'api_url': 'http://instance-detail-test.local:8123',
            'api_token': 'instance_detail_token',
            'active': True,
        })

        cls.portal_user = cls.env['res.users'].create({
            'name': 'Instance Detail Test User',
            'login': 'instance_detail_user',
            'password': 'instance_detail_password',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def test_my_ha_instance_with_entities(self):
        """Test instance detail page shows entities"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Instance Detail Entity',
            'entity_id': 'sensor.instance_detail',
            'domain': 'sensor',
            'entity_state': 'active',
            'ha_instance_id': self.ha_instance.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        self.authenticate('instance_detail_user', 'instance_detail_password')

        url = f'/my/ha/{self.ha_instance.id}'
        response = self.url_open(url)

        self.assertEqual(
            response.status_code,
            200,
            "Should access instance detail page"
        )
        self.assertIn(
            'Instance Detail Entity',
            response.text,
            "Should display entity name"
        )
        self.assertIn(
            'Instance Detail Test',
            response.text,
            "Should display instance name"
        )

    def test_my_ha_instance_with_groups(self):
        """Test instance detail page shows groups"""
        group = self.env['ha.entity.group'].sudo().create({
            'name': 'Instance Detail Group',
            'description': 'Test group for detail page',
            'ha_instance_id': self.ha_instance.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'group_id': group.id,
            'user_id': self.portal_user.id,
            'permission': 'control',
        })

        self.authenticate('instance_detail_user', 'instance_detail_password')

        url = f'/my/ha/{self.ha_instance.id}?tab=groups'
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Instance Detail Group',
            response.text,
            "Should display group name"
        )

    def test_my_ha_instance_no_access(self):
        """Test instance detail page returns 403 when user has no shares"""
        # Create a new user with no shares for this instance
        no_access_user = self.env['res.users'].create({
            'name': 'No Access User',
            'login': 'no_access_instance_user',
            'password': 'no_access_password',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

        self.authenticate('no_access_instance_user', 'no_access_password')

        url = f'/my/ha/{self.ha_instance.id}'
        response = self.url_open(url)

        self.assertEqual(
            response.status_code,
            403,
            "Should return 403 when user has no shares for instance"
        )

    def test_my_ha_instance_not_found(self):
        """Test instance detail page returns 404 for non-existent instance"""
        # Create entity share so user has some access
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Not Found Test Entity',
            'entity_id': 'sensor.not_found_test',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })
        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        self.authenticate('instance_detail_user', 'instance_detail_password')

        url = '/my/ha/999999'
        response = self.url_open(url)

        self.assertEqual(
            response.status_code,
            404,
            "Should return 404 for non-existent instance"
        )

    def test_my_ha_instance_tab_switching(self):
        """Test tab switching between entities and groups"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Tab Test Entity',
            'entity_id': 'sensor.tab_test',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })
        group = self.env['ha.entity.group'].sudo().create({
            'name': 'Tab Test Group',
            'ha_instance_id': self.ha_instance.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })
        self.env['ha.entity.share'].sudo().create({
            'group_id': group.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        self.authenticate('instance_detail_user', 'instance_detail_password')

        # Test entities tab (default)
        url_entities = f'/my/ha/{self.ha_instance.id}?tab=entities'
        response_entities = self.url_open(url_entities)

        self.assertEqual(response_entities.status_code, 200)
        self.assertIn(
            'Tab Test Entity',
            response_entities.text,
            "Entities tab should show entity"
        )

        # Test groups tab
        url_groups = f'/my/ha/{self.ha_instance.id}?tab=groups'
        response_groups = self.url_open(url_groups)

        self.assertEqual(response_groups.status_code, 200)
        self.assertIn(
            'Tab Test Group',
            response_groups.text,
            "Groups tab should show group"
        )


@tagged('post_install', '-at_install')
class TestPortalMyHaExpiredShares(HttpCase):
    """Integration tests for expired shares in /my/ha routes"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Expired Share Test Instance',
            'api_url': 'http://expired-share-test.local:8123',
            'api_token': 'expired_share_token',
            'active': True,
        })

        cls.portal_user = cls.env['res.users'].create({
            'name': 'Expired Share Test User',
            'login': 'expired_share_user',
            'password': 'expired_share_password',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def test_my_ha_excludes_expired_shares(self):
        """Test /my/ha excludes expired shares from count"""
        # Create active share
        active_entity = self.env['ha.entity'].sudo().create({
            'name': 'Active Entity',
            'entity_id': 'sensor.active_entity',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })
        self.env['ha.entity.share'].sudo().create({
            'entity_id': active_entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        # Create expired share
        expired_entity = self.env['ha.entity'].sudo().create({
            'name': 'Expired Entity',
            'entity_id': 'sensor.expired_entity',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })
        self.env['ha.entity.share'].sudo().create({
            'entity_id': expired_entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
            'expiry_date': fields.Datetime.now() - timedelta(days=1),
        })

        self.authenticate('expired_share_user', 'expired_share_password')

        # Check /my/ha
        url = '/my/ha'
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Active Entity',
            response.text,
            "Should show active entity"
        )

        # Check instance detail excludes expired
        url_detail = f'/my/ha/{self.ha_instance.id}'
        response_detail = self.url_open(url_detail)

        self.assertEqual(response_detail.status_code, 200)
        self.assertIn('Active Entity', response_detail.text)
        self.assertNotIn(
            'Expired Entity',
            response_detail.text,
            "Should NOT show expired entity"
        )

    def test_my_ha_instance_only_expired_returns_403(self):
        """Test instance detail returns 403 when all shares are expired"""
        # Create only expired share
        expired_entity = self.env['ha.entity'].sudo().create({
            'name': 'Only Expired Entity',
            'entity_id': 'sensor.only_expired',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })
        self.env['ha.entity.share'].sudo().create({
            'entity_id': expired_entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
            'expiry_date': fields.Datetime.now() - timedelta(days=1),
        })

        # Create a new user specifically for this test
        user_only_expired = self.env['res.users'].create({
            'name': 'Only Expired User',
            'login': 'only_expired_user',
            'password': 'only_expired_password',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

        # Create expired share for this new user
        expired_entity_2 = self.env['ha.entity'].sudo().create({
            'name': 'Only Expired Entity 2',
            'entity_id': 'sensor.only_expired_2',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })
        self.env['ha.entity.share'].sudo().create({
            'entity_id': expired_entity_2.id,
            'user_id': user_only_expired.id,
            'permission': 'view',
            'expiry_date': fields.Datetime.now() - timedelta(days=1),
        })

        self.authenticate('only_expired_user', 'only_expired_password')

        url = f'/my/ha/{self.ha_instance.id}'
        response = self.url_open(url)

        self.assertEqual(
            response.status_code,
            403,
            "Should return 403 when all shares are expired"
        )


@tagged('post_install', '-at_install')
class TestPortalMyHaPermissionDisplay(HttpCase):
    """Integration tests for permission display in /my/ha routes"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Permission Display Test',
            'api_url': 'http://permission-display.local:8123',
            'api_token': 'permission_display_token',
            'active': True,
        })

        cls.portal_user = cls.env['res.users'].create({
            'name': 'Permission Display User',
            'login': 'permission_display_user',
            'password': 'permission_display_password',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def test_my_ha_shows_view_permission(self):
        """Test instance detail shows view permission correctly"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'View Permission Entity',
            'entity_id': 'sensor.view_perm',
            'domain': 'sensor',
            'entity_state': 'on',
            'ha_instance_id': self.ha_instance.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        self.authenticate('permission_display_user', 'permission_display_password')

        url = f'/my/ha/{self.ha_instance.id}'
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        # Check for view permission indicator
        self.assertIn('View', response.text)

    def test_my_ha_shows_control_permission(self):
        """Test instance detail shows control permission correctly"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Control Permission Entity',
            'entity_id': 'switch.control_perm',
            'domain': 'switch',
            'entity_state': 'off',
            'ha_instance_id': self.ha_instance.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'control',
        })

        self.authenticate('permission_display_user', 'permission_display_password')

        url = f'/my/ha/{self.ha_instance.id}'
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        # Check for control permission indicator
        self.assertIn('Control', response.text)

    def test_my_ha_shows_entity_state(self):
        """Test instance detail shows entity state"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'State Display Entity',
            'entity_id': 'sensor.state_display',
            'domain': 'sensor',
            'entity_state': '42.5',
            'ha_instance_id': self.ha_instance.id,
        })

        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        self.authenticate('permission_display_user', 'permission_display_password')

        url = f'/my/ha/{self.ha_instance.id}'
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            '42.5',
            response.text,
            "Should display entity state"
        )
