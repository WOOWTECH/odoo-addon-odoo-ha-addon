# -*- coding: utf-8 -*-
# Part of odoo_ha_addon. See LICENSE file for full copyright and licensing details.

"""
Security tests for ir.rule and instance access control.

This module tests that:
1. ha_user can access ha.instance after being added to an entity group
2. ha_user cannot access ha.instance without group membership
3. ha_user loses access after being removed from group
4. ha_manager access is not affected by group membership changes
5. Permission changes take effect immediately (Odoo ORM handles cache automatically)
"""

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install')
class TestHAUserPermissions(TransactionCase):
    """Test cases for ha_user instance access via entity groups"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test HA instance
        cls.ha_instance = cls.env['ha.instance'].sudo().create({
            'name': 'Security Test HA Instance',
            'api_url': 'http://security-test.local:8123',
            'api_token': 'security_test_token_12345',
            'active': True,
        })

        # Create test entity
        cls.test_entity = cls.env['ha.entity'].sudo().create({
            'name': 'Security Test Entity',
            'entity_id': 'sensor.security_test',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        # Create test entity group (empty - no users)
        cls.entity_group = cls.env['ha.entity.group'].sudo().create({
            'name': 'Security Test Group',
            'ha_instance_id': cls.ha_instance.id,
            'entity_ids': [(6, 0, [cls.test_entity.id])],
        })

        # Create HA Manager user
        cls.ha_manager_user = cls.env['res.users'].sudo().create({
            'name': 'Security Test Manager',
            'login': 'security_test_manager',
            'email': 'security_manager@test.local',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('odoo_ha_addon.group_ha_manager').id
            ])]
        })

        # Create HA User (no group membership initially)
        cls.ha_user = cls.env['res.users'].sudo().create({
            'name': 'Security Test HA User',
            'login': 'security_test_ha_user',
            'email': 'security_ha_user@test.local',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('odoo_ha_addon.group_ha_user').id
            ])]
        })

    def test_ha_user_cannot_access_instance_without_group(self):
        """ha_user 未加入任何 group 時不應能存取任何 instance"""
        # Ensure user has no entity groups
        self.ha_user.sudo().write({'ha_entity_group_ids': [(5, 0, 0)]})

        # Try to search instances as ha_user
        instances = self.env['ha.instance'].with_user(self.ha_user).search([])

        self.assertEqual(
            len(instances),
            0,
            "ha_user without group membership should not see any instances"
        )

    def test_ha_user_can_access_instance_after_group_assignment(self):
        """ha_user 加入 Entity Group 後應可存取對應的 instance"""
        # Add user to entity group
        self.entity_group.sudo().write({
            'user_ids': [(4, self.ha_user.id)]
        })

        # Verify user is in group
        self.assertIn(
            self.ha_user,
            self.entity_group.user_ids,
            "User should be in entity group's user_ids"
        )

        # Try to search instances as ha_user
        # Permission should be granted immediately
        instances = self.env['ha.instance'].with_user(self.ha_user).search([])

        self.assertEqual(
            len(instances),
            1,
            "ha_user with group membership should see the authorized instance"
        )
        self.assertEqual(
            instances[0].id,
            self.ha_instance.id,
            "ha_user should see the correct instance"
        )

    def test_ha_user_loses_access_after_group_removal(self):
        """ha_user 被移出 group 後應無法存取對應的 instance"""
        # First add user to group
        self.entity_group.sudo().write({
            'user_ids': [(4, self.ha_user.id)]
        })

        # Verify access
        instances = self.env['ha.instance'].with_user(self.ha_user).search([])
        self.assertEqual(len(instances), 1, "Should have access before removal")

        # Remove user from group
        self.entity_group.sudo().write({
            'user_ids': [(3, self.ha_user.id)]
        })

        # Verify access is revoked immediately
        instances = self.env['ha.instance'].with_user(self.ha_user).search([])
        self.assertEqual(
            len(instances),
            0,
            "ha_user should lose access immediately after group removal"
        )

    def test_ha_manager_access_unaffected(self):
        """ha_manager 權限應不受此修復影響"""
        # Manager should always see all instances
        instances = self.env['ha.instance'].with_user(self.ha_manager_user).search([])

        self.assertGreaterEqual(
            len(instances),
            1,
            "ha_manager should see all instances regardless of group membership"
        )

        # Modify entity group - should not affect manager
        self.entity_group.sudo().write({
            'user_ids': [(5, 0, 0)]  # Clear all users
        })

        # Manager should still have access
        instances = self.env['ha.instance'].with_user(self.ha_manager_user).search([])
        self.assertGreaterEqual(
            len(instances),
            1,
            "ha_manager access should not be affected by group changes"
        )


@tagged('post_install', '-at_install')
class TestImmediatePermissionChanges(TransactionCase):
    """Test cases for immediate permission changes on group membership updates.

    Note: Odoo ORM automatically handles ir.rule cache invalidation when
    Many2many fields like user_ids are modified. No explicit cache clearing
    is required.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.ha_instance = cls.env['ha.instance'].sudo().create({
            'name': 'Cache Test HA Instance',
            'api_url': 'http://cache-test.local:8123',
            'api_token': 'cache_test_token_12345',
            'active': True,
        })

        cls.test_entity = cls.env['ha.entity'].sudo().create({
            'name': 'Cache Test Entity',
            'entity_id': 'sensor.cache_test',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.ha_user = cls.env['res.users'].sudo().create({
            'name': 'Cache Test HA User',
            'login': 'cache_test_ha_user',
            'email': 'cache_ha_user@test.local',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('odoo_ha_addon.group_ha_user').id
            ])]
        })

    def test_immediate_access_on_group_create_with_users(self):
        """Test that access is granted immediately when creating group with users"""
        # Verify no access initially
        instances = self.env['ha.instance'].with_user(self.ha_user).search([])
        initial_count = len(instances)

        # Create new group with user
        self.env['ha.entity.group'].sudo().create({
            'name': 'Cache Create Test Group',
            'ha_instance_id': self.ha_instance.id,
            'entity_ids': [(6, 0, [self.test_entity.id])],
            'user_ids': [(6, 0, [self.ha_user.id])],
        })

        # Access should be granted immediately
        instances = self.env['ha.instance'].with_user(self.ha_user).search([])
        self.assertGreater(
            len(instances),
            initial_count,
            "Access should be granted immediately when group is created with user_ids"
        )

    def test_immediate_access_on_write_user_ids(self):
        """Test that access is granted immediately when user_ids is modified"""
        # Create group without users
        group = self.env['ha.entity.group'].sudo().create({
            'name': 'Cache Write Test Group',
            'ha_instance_id': self.ha_instance.id,
            'entity_ids': [(6, 0, [self.test_entity.id])],
        })

        # Verify no access
        instances = self.env['ha.instance'].with_user(self.ha_user).search([])
        initial_count = len(instances)

        # Add user via write
        group.sudo().write({
            'user_ids': [(4, self.ha_user.id)]
        })

        # Access should be granted immediately
        instances = self.env['ha.instance'].with_user(self.ha_user).search([])
        self.assertGreater(
            len(instances),
            initial_count,
            "Access should be granted immediately after user_ids write"
        )


@tagged('post_install', '-at_install')
class TestEntityAccess(TransactionCase):
    """Test cases for entity access via groups"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.ha_instance = cls.env['ha.instance'].sudo().create({
            'name': 'Entity Access Test Instance',
            'api_url': 'http://entity-access-test.local:8123',
            'api_token': 'entity_access_test_12345',
            'active': True,
        })

        cls.entity1 = cls.env['ha.entity'].sudo().create({
            'name': 'Entity Access Test 1',
            'entity_id': 'sensor.entity_access_1',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.entity2 = cls.env['ha.entity'].sudo().create({
            'name': 'Entity Access Test 2',
            'entity_id': 'sensor.entity_access_2',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.group1 = cls.env['ha.entity.group'].sudo().create({
            'name': 'Entity Access Group 1',
            'ha_instance_id': cls.ha_instance.id,
            'entity_ids': [(6, 0, [cls.entity1.id])],
        })

        cls.group2 = cls.env['ha.entity.group'].sudo().create({
            'name': 'Entity Access Group 2',
            'ha_instance_id': cls.ha_instance.id,
            'entity_ids': [(6, 0, [cls.entity2.id])],
        })

        cls.ha_user = cls.env['res.users'].sudo().create({
            'name': 'Entity Access Test User',
            'login': 'entity_access_test_user',
            'email': 'entity_access_user@test.local',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('odoo_ha_addon.group_ha_user').id
            ])]
        })

    def test_user_sees_only_authorized_entities(self):
        """Test that user only sees entities from authorized groups"""
        # Add user to group1 only
        self.group1.sudo().write({
            'user_ids': [(4, self.ha_user.id)]
        })

        # Search entities as user
        entities = self.env['ha.entity'].with_user(self.ha_user).search([])

        self.assertEqual(len(entities), 1, "User should see only 1 entity")
        self.assertEqual(
            entities[0].id,
            self.entity1.id,
            "User should see only entity from authorized group"
        )

    def test_user_sees_entities_from_multiple_groups(self):
        """Test that user sees entities from all authorized groups"""
        # Add user to both groups
        self.group1.sudo().write({'user_ids': [(4, self.ha_user.id)]})
        self.group2.sudo().write({'user_ids': [(4, self.ha_user.id)]})

        # Search entities as user
        entities = self.env['ha.entity'].with_user(self.ha_user).search([])

        self.assertEqual(len(entities), 2, "User should see entities from both groups")
        entity_ids = entities.ids
        self.assertIn(self.entity1.id, entity_ids)
        self.assertIn(self.entity2.id, entity_ids)
