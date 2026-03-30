# -*- coding: utf-8 -*-
# Part of odoo_ha_addon. See LICENSE file for full copyright and licensing details.

"""
Permission tests for share functionality.

This module tests that the Share button is only accessible to users with
the group_ha_manager group, not regular group_ha_user users.
"""

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install')
class TestShareButtonPermissions(TransactionCase):
    """Test cases for Share button visibility and access control"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test HA instance
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Permission Test HA Instance',
            'api_url': 'http://permission-test.local:8123',
            'api_token': 'permission_test_token_12345',
            'active': True,
        })

        # Create HA Manager user
        cls.ha_manager_user = cls.env['res.users'].create({
            'name': 'Test HA Manager',
            'login': 'test_ha_manager',
            'email': 'ha_manager@test.local',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('odoo_ha_addon.group_ha_manager').id
            ])]
        })

        # Create HA User (read-only user)
        cls.ha_user = cls.env['res.users'].create({
            'name': 'Test HA User',
            'login': 'test_ha_user',
            'email': 'ha_user@test.local',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('odoo_ha_addon.group_ha_user').id
            ])]
        })

    def test_ha_manager_can_share_entity(self):
        """Test that HA Manager can access action_share on entity"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Manager Share Entity',
            'entity_id': 'sensor.manager_share',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })

        # Switch to manager user context
        entity_as_manager = entity.with_user(self.ha_manager_user)

        # action_share should work without raising AccessError
        try:
            action = entity_as_manager.action_share()
            self.assertEqual(
                action['res_model'],
                'portal.share',
                "HA Manager should be able to call action_share"
            )
        except AccessError:
            self.fail("HA Manager should be able to access action_share")

    def test_ha_manager_can_share_group(self):
        """Test that HA Manager can access action_share on entity group"""
        group = self.env['ha.entity.group'].sudo().create({
            'name': 'Manager Share Group',
            'ha_instance_id': self.ha_instance.id,
        })

        # Switch to manager user context
        group_as_manager = group.with_user(self.ha_manager_user)

        # action_share should work without raising AccessError
        try:
            action = group_as_manager.action_share()
            self.assertEqual(
                action['res_model'],
                'portal.share',
                "HA Manager should be able to call action_share on groups"
            )
        except AccessError:
            self.fail("HA Manager should be able to access action_share on groups")

    def test_share_button_visibility_in_entity_view(self):
        """Test that Share button has correct groups attribute in entity form view"""
        view = self.env.ref('odoo_ha_addon.ha_entity_view_form')
        arch = view.arch

        # The Share button should be restricted to group_ha_manager
        self.assertIn(
            'groups="odoo_ha_addon.group_ha_manager"',
            arch,
            "Share button in entity form should be restricted to HA Manager group"
        )
        self.assertIn(
            'action_share',
            arch,
            "Share button should reference action_share method"
        )

    def test_share_button_visibility_in_group_view(self):
        """Test that Share button has correct groups attribute in group form view"""
        view = self.env.ref('odoo_ha_addon.ha_entity_group_view_form')
        arch = view.arch

        # The Share button should be restricted to group_ha_manager
        self.assertIn(
            'groups="odoo_ha_addon.group_ha_manager"',
            arch,
            "Share button in entity group form should be restricted to HA Manager group"
        )
        self.assertIn(
            'action_share',
            arch,
            "Share button should reference action_share method"
        )


@tagged('post_install', '-at_install')
class TestShareWizardPermissions(TransactionCase):
    """Test cases for portal.share wizard access control"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Wizard Test HA Instance',
            'api_url': 'http://wizard-test.local:8123',
            'api_token': 'wizard_test_token_12345',
            'active': True,
        })

        cls.ha_manager_user = cls.env['res.users'].create({
            'name': 'Wizard Test Manager',
            'login': 'wizard_test_manager',
            'email': 'wizard_manager@test.local',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('odoo_ha_addon.group_ha_manager').id
            ])]
        })

    def test_share_wizard_context_for_entity(self):
        """Test that share wizard receives correct context for entity"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Wizard Context Entity',
            'entity_id': 'sensor.wizard_context',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })

        entity_as_manager = entity.with_user(self.ha_manager_user)
        action = entity_as_manager.action_share()

        # Verify the wizard receives correct model and record info
        self.assertEqual(
            action['context']['default_res_model'],
            'ha.entity',
            "Wizard should receive correct model name"
        )
        self.assertEqual(
            action['context']['default_res_id'],
            entity.id,
            "Wizard should receive correct record ID"
        )
        self.assertEqual(
            action['target'],
            'new',
            "Wizard should open in a new dialog window"
        )

    def test_share_wizard_context_for_group(self):
        """Test that share wizard receives correct context for entity group"""
        group = self.env['ha.entity.group'].sudo().create({
            'name': 'Wizard Context Group',
            'ha_instance_id': self.ha_instance.id,
        })

        group_as_manager = group.with_user(self.ha_manager_user)
        action = group_as_manager.action_share()

        # Verify the wizard receives correct model and record info
        self.assertEqual(
            action['context']['default_res_model'],
            'ha.entity.group',
            "Wizard should receive correct model name for groups"
        )
        self.assertEqual(
            action['context']['default_res_id'],
            group.id,
            "Wizard should receive correct record ID for groups"
        )


@tagged('post_install', '-at_install')
class TestTokenGenerationPermissions(TransactionCase):
    """Test cases for token generation permissions"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Token Gen Test HA Instance',
            'api_url': 'http://token-gen-test.local:8123',
            'api_token': 'token_gen_test_12345',
            'active': True,
        })

        cls.ha_manager_user = cls.env['res.users'].create({
            'name': 'Token Gen Manager',
            'login': 'token_gen_manager',
            'email': 'token_gen_manager@test.local',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('odoo_ha_addon.group_ha_manager').id
            ])]
        })

    def test_manager_can_generate_token(self):
        """Test that HA Manager can generate access tokens"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Token Gen Entity',
            'entity_id': 'sensor.token_gen',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })

        entity_as_manager = entity.with_user(self.ha_manager_user)

        # Token generation should work via action_share
        # action_share calls _portal_ensure_token internally
        try:
            entity_as_manager.action_share()
            # Reload to see if token was set
            entity.invalidate_recordset()
            self.assertTrue(
                entity.access_token,
                "Token should be generated when HA Manager calls action_share"
            )
        except AccessError:
            self.fail("HA Manager should be able to trigger token generation")

    def test_multiple_share_calls_same_token(self):
        """Test that multiple share calls return same token"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Same Token Entity',
            'entity_id': 'sensor.same_token',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })

        entity_as_manager = entity.with_user(self.ha_manager_user)

        # First call
        entity_as_manager.action_share()
        first_token = entity.access_token

        # Second call
        entity_as_manager.action_share()
        second_token = entity.access_token

        self.assertEqual(
            first_token,
            second_token,
            "Multiple share calls should return the same token"
        )


@tagged('post_install', '-at_install')
class TestGroupMembershipHierarchy(TransactionCase):
    """Test cases for group membership hierarchy"""

    def test_ha_manager_implies_ha_user(self):
        """Test that group_ha_manager implies group_ha_user"""
        manager_group = self.env.ref('odoo_ha_addon.group_ha_manager')
        user_group = self.env.ref('odoo_ha_addon.group_ha_user')

        # Check implied_ids
        self.assertIn(
            user_group,
            manager_group.implied_ids,
            "group_ha_manager should imply group_ha_user"
        )

    def test_manager_has_user_permissions(self):
        """Test that HA Manager inherits HA User permissions"""
        manager_user = self.env['res.users'].create({
            'name': 'Hierarchy Test Manager',
            'login': 'hierarchy_test_manager',
            'email': 'hierarchy_manager@test.local',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('odoo_ha_addon.group_ha_manager').id
            ])]
        })

        # Manager should have HA User group via implied_ids
        self.assertTrue(
            manager_user.has_group('odoo_ha_addon.group_ha_user'),
            "HA Manager should also have HA User group (implied)"
        )
        self.assertTrue(
            manager_user.has_group('odoo_ha_addon.group_ha_manager'),
            "HA Manager should have HA Manager group"
        )
