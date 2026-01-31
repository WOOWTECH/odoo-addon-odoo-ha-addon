# -*- coding: utf-8 -*-
# Part of odoo_ha_addon. See LICENSE file for full copyright and licensing details.

"""
Unit tests for ha.entity.share model.

This module tests:
- Model creation and basic operations
- SQL constraints (entity_or_group_required, unique_entity_user, unique_group_user)
- Computed fields (ha_instance_id, is_expired, display_name)
- Helper methods (get_shares_for_user, cleanup_expired_shares, etc.)
"""

from datetime import timedelta
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError
from odoo import fields
import psycopg2


@tagged('post_install', '-at_install')
class TestEntityShareModel(TransactionCase):
    """Test cases for ha.entity.share model basic operations"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test HA instance
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Share Test HA Instance',
            'api_url': 'http://share-test.local:8123',
            'api_token': 'share_test_token_12345',
            'active': True,
        })

        # Create test entity
        cls.test_entity = cls.env['ha.entity'].sudo().create({
            'name': 'Test Share Entity',
            'entity_id': 'sensor.share_test',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        # Create test entity group
        cls.test_group = cls.env['ha.entity.group'].sudo().create({
            'name': 'Test Share Group',
            'ha_instance_id': cls.ha_instance.id,
        })

        # Create test users
        cls.test_user1 = cls.env['res.users'].create({
            'name': 'Share Test User 1',
            'login': 'share_test_user1',
            'email': 'share_user1@test.local',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('odoo_ha_addon.group_ha_user').id
            ])]
        })

        cls.test_user2 = cls.env['res.users'].create({
            'name': 'Share Test User 2',
            'login': 'share_test_user2',
            'email': 'share_user2@test.local',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('odoo_ha_addon.group_ha_user').id
            ])]
        })

    def test_create_entity_share(self):
        """Test creating a share for an entity"""
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user1.id,
            'permission': 'view',
        })

        self.assertTrue(share.id, "Share should be created")
        self.assertEqual(share.entity_id, self.test_entity)
        self.assertEqual(share.user_id, self.test_user1)
        self.assertEqual(share.permission, 'view')
        self.assertFalse(share.group_id, "group_id should be empty for entity share")

    def test_create_group_share(self):
        """Test creating a share for an entity group"""
        share = self.env['ha.entity.share'].create({
            'group_id': self.test_group.id,
            'user_id': self.test_user1.id,
            'permission': 'control',
        })

        self.assertTrue(share.id, "Share should be created")
        self.assertEqual(share.group_id, self.test_group)
        self.assertEqual(share.user_id, self.test_user1)
        self.assertEqual(share.permission, 'control')
        self.assertFalse(share.entity_id, "entity_id should be empty for group share")

    def test_default_permission_is_view(self):
        """Test that default permission is 'view'"""
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user1.id,
        })

        self.assertEqual(share.permission, 'view', "Default permission should be 'view'")

    def test_expiry_date_optional(self):
        """Test that expiry_date is optional"""
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user1.id,
        })

        self.assertFalse(share.expiry_date, "expiry_date should be optional")
        self.assertFalse(share.is_expired, "Share without expiry_date should not be expired")


@tagged('post_install', '-at_install')
class TestEntityShareConstraints(TransactionCase):
    """Test cases for ha.entity.share SQL constraints"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Constraint Test HA Instance',
            'api_url': 'http://constraint-test.local:8123',
            'api_token': 'constraint_test_token_12345',
            'active': True,
        })

        cls.test_entity = cls.env['ha.entity'].sudo().create({
            'name': 'Constraint Test Entity',
            'entity_id': 'sensor.constraint_test',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_group = cls.env['ha.entity.group'].sudo().create({
            'name': 'Constraint Test Group',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_user = cls.env['res.users'].create({
            'name': 'Constraint Test User',
            'login': 'constraint_test_user',
            'email': 'constraint_user@test.local',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

    def test_constraint_entity_or_group_required_neither(self):
        """Test constraint: must specify either entity_id or group_id"""
        with self.assertRaises((ValidationError, psycopg2.IntegrityError)):
            self.env['ha.entity.share'].create({
                'user_id': self.test_user.id,
                'permission': 'view',
            })

    def test_constraint_entity_or_group_required_both(self):
        """Test constraint: cannot specify both entity_id and group_id"""
        with self.assertRaises((ValidationError, psycopg2.IntegrityError)):
            self.env['ha.entity.share'].create({
                'entity_id': self.test_entity.id,
                'group_id': self.test_group.id,
                'user_id': self.test_user.id,
                'permission': 'view',
            })

    def test_constraint_unique_entity_user(self):
        """Test constraint: same entity + user combination cannot be duplicated"""
        # Create first share
        self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'permission': 'view',
        })

        # Try to create duplicate
        with self.assertRaises(psycopg2.IntegrityError):
            with self.env.cr.savepoint():
                self.env['ha.entity.share'].create({
                    'entity_id': self.test_entity.id,
                    'user_id': self.test_user.id,
                    'permission': 'control',
                })

    def test_constraint_unique_group_user(self):
        """Test constraint: same group + user combination cannot be duplicated"""
        # Create first share
        self.env['ha.entity.share'].create({
            'group_id': self.test_group.id,
            'user_id': self.test_user.id,
            'permission': 'view',
        })

        # Try to create duplicate
        with self.assertRaises(psycopg2.IntegrityError):
            with self.env.cr.savepoint():
                self.env['ha.entity.share'].create({
                    'group_id': self.test_group.id,
                    'user_id': self.test_user.id,
                    'permission': 'control',
                })

    def test_different_users_can_share_same_entity(self):
        """Test that different users can be shared the same entity"""
        user2 = self.env['res.users'].create({
            'name': 'Constraint Test User 2',
            'login': 'constraint_test_user2',
            'email': 'constraint_user2@test.local',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })

        share1 = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'permission': 'view',
        })

        share2 = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': user2.id,
            'permission': 'control',
        })

        self.assertTrue(share1.id and share2.id)


@tagged('post_install', '-at_install')
class TestEntityShareComputedFields(TransactionCase):
    """Test cases for ha.entity.share computed fields"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Computed Test HA Instance',
            'api_url': 'http://computed-test.local:8123',
            'api_token': 'computed_test_token_12345',
            'active': True,
        })

        cls.test_entity = cls.env['ha.entity'].sudo().create({
            'name': 'Computed Test Entity',
            'entity_id': 'sensor.computed_test',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_group = cls.env['ha.entity.group'].sudo().create({
            'name': 'Computed Test Group',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_user = cls.env['res.users'].create({
            'name': 'Computed Test User',
            'login': 'computed_test_user',
            'email': 'computed_user@test.local',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

    def test_compute_ha_instance_id_from_entity(self):
        """Test ha_instance_id is computed from entity"""
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
        })

        self.assertEqual(
            share.ha_instance_id, self.ha_instance,
            "ha_instance_id should be computed from entity"
        )

    def test_compute_ha_instance_id_from_group(self):
        """Test ha_instance_id is computed from group"""
        share = self.env['ha.entity.share'].create({
            'group_id': self.test_group.id,
            'user_id': self.test_user.id,
        })

        self.assertEqual(
            share.ha_instance_id, self.ha_instance,
            "ha_instance_id should be computed from group"
        )

    def test_compute_is_expired_no_expiry(self):
        """Test is_expired when no expiry_date is set"""
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
        })

        self.assertFalse(share.is_expired, "Share without expiry should not be expired")

    def test_compute_is_expired_future_date(self):
        """Test is_expired when expiry_date is in the future"""
        future_date = fields.Datetime.now() + timedelta(days=30)
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': future_date,
        })

        self.assertFalse(share.is_expired, "Share with future expiry should not be expired")

    def test_compute_is_expired_past_date(self):
        """Test is_expired when expiry_date is in the past"""
        past_date = fields.Datetime.now() - timedelta(days=1)
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': past_date,
        })

        self.assertTrue(share.is_expired, "Share with past expiry should be expired")

    def test_compute_display_name_entity(self):
        """Test display_name for entity share"""
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
        })

        self.assertIn(self.test_entity.name, share.display_name)
        self.assertIn(self.test_user.name, share.display_name)

    def test_compute_display_name_group(self):
        """Test display_name for group share"""
        share = self.env['ha.entity.share'].create({
            'group_id': self.test_group.id,
            'user_id': self.test_user.id,
        })

        self.assertIn(self.test_group.name, share.display_name)
        self.assertIn(self.test_user.name, share.display_name)


@tagged('post_install', '-at_install')
class TestEntityShareHelperMethods(TransactionCase):
    """Test cases for ha.entity.share helper methods"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Helper Test HA Instance',
            'api_url': 'http://helper-test.local:8123',
            'api_token': 'helper_test_token_12345',
            'active': True,
        })

        cls.test_entity = cls.env['ha.entity'].sudo().create({
            'name': 'Helper Test Entity',
            'entity_id': 'sensor.helper_test',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_entity2 = cls.env['ha.entity'].sudo().create({
            'name': 'Helper Test Entity 2',
            'entity_id': 'sensor.helper_test2',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_group = cls.env['ha.entity.group'].sudo().create({
            'name': 'Helper Test Group',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_user = cls.env['res.users'].create({
            'name': 'Helper Test User',
            'login': 'helper_test_user',
            'email': 'helper_user@test.local',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

    def test_get_shares_for_user(self):
        """Test get_shares_for_user method"""
        # Create shares for test user
        share1 = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
        })
        share2 = self.env['ha.entity.share'].create({
            'group_id': self.test_group.id,
            'user_id': self.test_user.id,
        })

        shares = self.env['ha.entity.share'].get_shares_for_user(self.test_user.id)

        self.assertEqual(len(shares), 2)
        self.assertIn(share1, shares)
        self.assertIn(share2, shares)

    def test_get_shares_for_user_excludes_expired(self):
        """Test get_shares_for_user excludes expired shares by default"""
        past_date = fields.Datetime.now() - timedelta(days=1)
        future_date = fields.Datetime.now() + timedelta(days=30)

        # Create expired share
        self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': past_date,
        })

        # Create valid share
        valid_share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity2.id,
            'user_id': self.test_user.id,
            'expiry_date': future_date,
        })

        shares = self.env['ha.entity.share'].get_shares_for_user(self.test_user.id)

        self.assertEqual(len(shares), 1)
        self.assertIn(valid_share, shares)

    def test_get_shares_for_user_includes_expired(self):
        """Test get_shares_for_user can include expired shares"""
        past_date = fields.Datetime.now() - timedelta(days=1)

        # Create expired share
        expired_share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': past_date,
        })

        shares = self.env['ha.entity.share'].get_shares_for_user(
            self.test_user.id, include_expired=True
        )

        self.assertIn(expired_share, shares)

    def test_get_shared_entities_for_user(self):
        """Test get_shared_entities_for_user method"""
        self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'permission': 'view',
        })

        entities = self.env['ha.entity.share'].get_shared_entities_for_user(self.test_user.id)

        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0], self.test_entity)

    def test_get_shared_groups_for_user(self):
        """Test get_shared_groups_for_user method"""
        self.env['ha.entity.share'].create({
            'group_id': self.test_group.id,
            'user_id': self.test_user.id,
            'permission': 'control',
        })

        groups = self.env['ha.entity.share'].get_shared_groups_for_user(self.test_user.id)

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0], self.test_group)

    def test_action_extend_expiry(self):
        """Test action_extend_expiry method"""
        future_date = fields.Datetime.now() + timedelta(days=5)
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': future_date,
        })

        share.action_extend_expiry(days=30)

        # Should be extended by 30 days from original expiry
        expected_min = future_date + timedelta(days=29)
        expected_max = future_date + timedelta(days=31)
        self.assertTrue(
            expected_min < share.expiry_date < expected_max,
            f"Expiry should be extended by 30 days. Got: {share.expiry_date}"
        )

    def test_action_revoke(self):
        """Test action_revoke method"""
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
        })
        share_id = share.id

        share.action_revoke()

        # Share should be deleted
        self.assertFalse(
            self.env['ha.entity.share'].search([('id', '=', share_id)]),
            "Share should be deleted after revoke"
        )


@tagged('post_install', '-at_install')
class TestEntityShareRelationships(TransactionCase):
    """Test cases for ha.entity.share relationships with ha.entity and ha.entity.group"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Relationship Test HA Instance',
            'api_url': 'http://relationship-test.local:8123',
            'api_token': 'relationship_test_token_12345',
            'active': True,
        })

        cls.test_user = cls.env['res.users'].create({
            'name': 'Relationship Test User',
            'login': 'relationship_test_user',
            'email': 'relationship_user@test.local',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

    def test_entity_share_ids_field(self):
        """Test that entity has share_ids One2many field"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Entity Share IDs Test',
            'entity_id': 'sensor.share_ids_test',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })

        share = self.env['ha.entity.share'].create({
            'entity_id': entity.id,
            'user_id': self.test_user.id,
        })

        self.assertIn(share, entity.share_ids)
        self.assertEqual(len(entity.share_ids), 1)

    def test_group_share_ids_field(self):
        """Test that entity group has share_ids One2many field"""
        group = self.env['ha.entity.group'].sudo().create({
            'name': 'Group Share IDs Test',
            'ha_instance_id': self.ha_instance.id,
        })

        share = self.env['ha.entity.share'].create({
            'group_id': group.id,
            'user_id': self.test_user.id,
        })

        self.assertIn(share, group.share_ids)
        self.assertEqual(len(group.share_ids), 1)

    def test_cascade_delete_entity(self):
        """Test that shares are deleted when entity is deleted"""
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Cascade Delete Entity',
            'entity_id': 'sensor.cascade_delete',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })

        share = self.env['ha.entity.share'].create({
            'entity_id': entity.id,
            'user_id': self.test_user.id,
        })
        share_id = share.id

        # Delete entity
        entity.unlink()

        # Share should be deleted (cascade)
        self.assertFalse(
            self.env['ha.entity.share'].search([('id', '=', share_id)]),
            "Share should be deleted when entity is deleted"
        )

    def test_cascade_delete_group(self):
        """Test that shares are deleted when group is deleted"""
        group = self.env['ha.entity.group'].sudo().create({
            'name': 'Cascade Delete Group',
            'ha_instance_id': self.ha_instance.id,
        })

        share = self.env['ha.entity.share'].create({
            'group_id': group.id,
            'user_id': self.test_user.id,
        })
        share_id = share.id

        # Delete group
        group.unlink()

        # Share should be deleted (cascade)
        self.assertFalse(
            self.env['ha.entity.share'].search([('id', '=', share_id)]),
            "Share should be deleted when group is deleted"
        )

    def test_cascade_delete_user(self):
        """Test that shares are deleted when user is deleted"""
        test_user = self.env['res.users'].create({
            'name': 'Cascade Delete User',
            'login': 'cascade_delete_user',
            'email': 'cascade_delete@test.local',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })

        entity = self.env['ha.entity'].sudo().create({
            'name': 'Cascade User Entity',
            'entity_id': 'sensor.cascade_user',
            'domain': 'sensor',
            'ha_instance_id': self.ha_instance.id,
        })

        share = self.env['ha.entity.share'].create({
            'entity_id': entity.id,
            'user_id': test_user.id,
        })
        share_id = share.id

        # Delete user
        test_user.unlink()

        # Share should be deleted (cascade)
        self.assertFalse(
            self.env['ha.entity.share'].search([('id', '=', share_id)]),
            "Share should be deleted when user is deleted"
        )


@tagged('post_install', '-at_install')
class TestEntityShareCleanup(TransactionCase):
    """Test cases for ha.entity.share cleanup methods"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Cleanup Test HA Instance',
            'api_url': 'http://cleanup-test.local:8123',
            'api_token': 'cleanup_test_token_12345',
            'active': True,
        })

        cls.test_entity = cls.env['ha.entity'].sudo().create({
            'name': 'Cleanup Test Entity',
            'entity_id': 'sensor.cleanup_test',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_user = cls.env['res.users'].create({
            'name': 'Cleanup Test User',
            'login': 'cleanup_test_user',
            'email': 'cleanup_user@test.local',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

    def test_cleanup_expired_shares_notify(self):
        """Test cleanup_expired_shares marks shares for notification"""
        past_date = fields.Datetime.now() - timedelta(days=1)
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': past_date,
            'notification_sent': False,
        })

        count = self.env['ha.entity.share'].cleanup_expired_shares(delete=False, notify=True)

        self.assertEqual(count, 1)
        self.assertTrue(share.notification_sent)

    def test_cleanup_expired_shares_delete(self):
        """Test cleanup_expired_shares can delete expired shares"""
        past_date = fields.Datetime.now() - timedelta(days=1)
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': past_date,
            'notification_sent': False,
        })
        share_id = share.id

        count = self.env['ha.entity.share'].cleanup_expired_shares(delete=True, notify=True)

        self.assertEqual(count, 1)
        self.assertFalse(
            self.env['ha.entity.share'].search([('id', '=', share_id)]),
            "Expired share should be deleted"
        )

    def test_cleanup_expired_shares_ignores_notified(self):
        """Test cleanup_expired_shares ignores already notified shares"""
        past_date = fields.Datetime.now() - timedelta(days=1)
        self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': past_date,
            'notification_sent': True,  # Already notified
        })

        count = self.env['ha.entity.share'].cleanup_expired_shares(delete=False, notify=True)

        self.assertEqual(count, 0, "Already notified shares should be ignored")


@tagged('post_install', '-at_install')
class TestEntityShareSearch(TransactionCase):
    """Test cases for searching is_expired field"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Search Test HA Instance',
            'api_url': 'http://search-test.local:8123',
            'api_token': 'search_test_token_12345',
            'active': True,
        })

        cls.test_entity = cls.env['ha.entity'].sudo().create({
            'name': 'Search Test Entity',
            'entity_id': 'sensor.search_test',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_entity2 = cls.env['ha.entity'].sudo().create({
            'name': 'Search Test Entity 2',
            'entity_id': 'sensor.search_test2',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_entity3 = cls.env['ha.entity'].sudo().create({
            'name': 'Search Test Entity 3',
            'entity_id': 'sensor.search_test3',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_user = cls.env['res.users'].create({
            'name': 'Search Test User',
            'login': 'search_test_user',
            'email': 'search_user@test.local',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

    def test_search_is_expired_true(self):
        """Test searching for expired shares"""
        past_date = fields.Datetime.now() - timedelta(days=1)
        future_date = fields.Datetime.now() + timedelta(days=30)

        expired_share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': past_date,
        })

        self.env['ha.entity.share'].create({
            'entity_id': self.test_entity2.id,
            'user_id': self.test_user.id,
            'expiry_date': future_date,
        })

        expired_shares = self.env['ha.entity.share'].search([
            ('is_expired', '=', True),
            ('user_id', '=', self.test_user.id)
        ])

        self.assertEqual(len(expired_shares), 1)
        self.assertEqual(expired_shares[0], expired_share)

    def test_search_is_expired_false(self):
        """Test searching for non-expired shares"""
        past_date = fields.Datetime.now() - timedelta(days=1)
        future_date = fields.Datetime.now() + timedelta(days=30)

        self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': past_date,
        })

        valid_share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity2.id,
            'user_id': self.test_user.id,
            'expiry_date': future_date,
        })

        no_expiry_share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity3.id,
            'user_id': self.test_user.id,
            # No expiry date
        })

        non_expired_shares = self.env['ha.entity.share'].search([
            ('is_expired', '=', False),
            ('user_id', '=', self.test_user.id)
        ])

        self.assertEqual(len(non_expired_shares), 2)
        self.assertIn(valid_share, non_expired_shares)
        self.assertIn(no_expiry_share, non_expired_shares)


@tagged('post_install', '-at_install')
class TestEntityShareCronJobs(TransactionCase):
    """Test cases for ha.entity.share cron job methods"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Cron Test HA Instance',
            'api_url': 'http://cron-test.local:8123',
            'api_token': 'cron_test_token_12345',
            'active': True,
        })

        cls.test_entity = cls.env['ha.entity'].sudo().create({
            'name': 'Cron Test Entity',
            'entity_id': 'sensor.cron_test',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_entity2 = cls.env['ha.entity'].sudo().create({
            'name': 'Cron Test Entity 2',
            'entity_id': 'sensor.cron_test2',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_entity3 = cls.env['ha.entity'].sudo().create({
            'name': 'Cron Test Entity 3',
            'entity_id': 'sensor.cron_test3',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_group = cls.env['ha.entity.group'].sudo().create({
            'name': 'Cron Test Group',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_user = cls.env['res.users'].create({
            'name': 'Cron Test User',
            'login': 'cron_test_user',
            'email': 'cron_user@test.local',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

    def test_cron_check_expiring_shares_within_7_days(self):
        """Test that shares expiring within 7 days trigger notifications"""
        # Create a share expiring in 5 days (within threshold)
        expiry_date = fields.Datetime.now() + timedelta(days=5)
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': expiry_date,
            'notification_sent': False,
        })

        # Run the cron job
        self.env['ha.entity.share']._cron_check_expiring_shares()

        # Verify notification_sent is now True
        share.invalidate_recordset()
        self.assertTrue(
            share.notification_sent,
            "Share expiring within 7 days should have notification_sent=True"
        )

    def test_cron_check_expiring_shares_beyond_7_days(self):
        """Test that shares expiring beyond 7 days do not trigger notifications"""
        # Create a share expiring in 10 days (beyond threshold)
        expiry_date = fields.Datetime.now() + timedelta(days=10)
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': expiry_date,
            'notification_sent': False,
        })

        # Run the cron job
        self.env['ha.entity.share']._cron_check_expiring_shares()

        # Verify notification_sent is still False
        share.invalidate_recordset()
        self.assertFalse(
            share.notification_sent,
            "Share expiring beyond 7 days should not trigger notification"
        )

    def test_cron_check_expiring_shares_already_notified(self):
        """Test that already notified shares are skipped"""
        # Create a share that was already notified
        expiry_date = fields.Datetime.now() + timedelta(days=3)
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': expiry_date,
            'notification_sent': True,  # Already notified
        })

        # Count activities before
        activity_count_before = self.env['mail.activity'].search_count([
            ('res_model', '=', 'ha.entity'),
            ('res_id', '=', self.test_entity.id),
        ])

        # Run the cron job
        self.env['ha.entity.share']._cron_check_expiring_shares()

        # Count activities after
        activity_count_after = self.env['mail.activity'].search_count([
            ('res_model', '=', 'ha.entity'),
            ('res_id', '=', self.test_entity.id),
        ])

        # No new activities should be created
        self.assertEqual(
            activity_count_before, activity_count_after,
            "Already notified shares should not create new activities"
        )

    def test_cron_check_expiring_shares_no_expiry(self):
        """Test that shares without expiry_date are not affected"""
        # Create a share without expiry date
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            # No expiry_date
        })

        # Run the cron job
        self.env['ha.entity.share']._cron_check_expiring_shares()

        # Verify notification_sent is still False
        share.invalidate_recordset()
        self.assertFalse(
            share.notification_sent,
            "Share without expiry date should not trigger notification"
        )

    def test_cron_check_expiring_shares_already_expired(self):
        """Test that already expired shares are not notified"""
        # Create an already expired share
        expiry_date = fields.Datetime.now() - timedelta(days=1)
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': expiry_date,
            'notification_sent': False,
        })

        # Run the cron job
        self.env['ha.entity.share']._cron_check_expiring_shares()

        # Verify notification_sent is still False (expired shares are not in scope)
        share.invalidate_recordset()
        self.assertFalse(
            share.notification_sent,
            "Already expired shares should not trigger notification"
        )

    def test_cron_check_expiring_shares_creates_activity(self):
        """Test that the cron job creates mail.activity for expiring shares"""
        # Create a share expiring in 3 days
        expiry_date = fields.Datetime.now() + timedelta(days=3)
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': expiry_date,
            'notification_sent': False,
        })

        # Run the cron job
        self.env['ha.entity.share']._cron_check_expiring_shares()

        # Verify a mail.activity was created for the share creator
        activity = self.env['mail.activity'].search([
            ('res_model', '=', 'ha.entity'),
            ('res_id', '=', self.test_entity.id),
            ('user_id', '=', share.create_uid.id),
        ], limit=1)

        self.assertTrue(activity, "Mail activity should be created for expiring share")
        self.assertIn('Share Expiring', activity.summary)

    def test_cron_check_expiring_shares_for_group(self):
        """Test expiry notification for group shares"""
        # Create a group share expiring in 5 days
        expiry_date = fields.Datetime.now() + timedelta(days=5)
        share = self.env['ha.entity.share'].create({
            'group_id': self.test_group.id,
            'user_id': self.test_user.id,
            'expiry_date': expiry_date,
            'notification_sent': False,
        })

        # Run the cron job
        self.env['ha.entity.share']._cron_check_expiring_shares()

        # Verify notification_sent is now True
        share.invalidate_recordset()
        self.assertTrue(
            share.notification_sent,
            "Group share expiring within 7 days should have notification_sent=True"
        )

        # Verify a mail.activity was created
        activity = self.env['mail.activity'].search([
            ('res_model', '=', 'ha.entity.group'),
            ('res_id', '=', self.test_group.id),
        ], limit=1)

        self.assertTrue(activity, "Mail activity should be created for expiring group share")

    def test_cron_cleanup_expired_shares_old_records(self):
        """Test that shares expired more than 30 days ago are cleaned up"""
        # Create a share that expired 35 days ago
        expiry_date = fields.Datetime.now() - timedelta(days=35)
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': expiry_date,
        })
        share_id = share.id

        # Run the cleanup cron job
        self.env['ha.entity.share']._cron_cleanup_expired_shares()

        # Verify share is deleted
        remaining = self.env['ha.entity.share'].search([('id', '=', share_id)])
        self.assertFalse(remaining, "Share expired 35 days ago should be deleted")

    def test_cron_cleanup_expired_shares_recent_records(self):
        """Test that shares expired less than 30 days ago are NOT cleaned up"""
        # Create a share that expired 10 days ago
        expiry_date = fields.Datetime.now() - timedelta(days=10)
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': expiry_date,
        })
        share_id = share.id

        # Run the cleanup cron job
        self.env['ha.entity.share']._cron_cleanup_expired_shares()

        # Verify share still exists
        remaining = self.env['ha.entity.share'].search([('id', '=', share_id)])
        self.assertTrue(remaining, "Share expired 10 days ago should NOT be deleted")

    def test_cron_cleanup_expired_shares_no_expiry(self):
        """Test that shares without expiry_date are NOT cleaned up"""
        # Create a share without expiry date
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            # No expiry_date
        })
        share_id = share.id

        # Run the cleanup cron job
        self.env['ha.entity.share']._cron_cleanup_expired_shares()

        # Verify share still exists
        remaining = self.env['ha.entity.share'].search([('id', '=', share_id)])
        self.assertTrue(remaining, "Share without expiry_date should NOT be deleted")

    def test_cron_cleanup_multiple_expired_shares(self):
        """Test cleanup of multiple expired shares"""
        # Create several shares with different expiry dates
        old_expiry = fields.Datetime.now() - timedelta(days=40)
        recent_expiry = fields.Datetime.now() - timedelta(days=15)
        future_expiry = fields.Datetime.now() + timedelta(days=10)

        old_share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user.id,
            'expiry_date': old_expiry,
        })

        recent_share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity2.id,
            'user_id': self.test_user.id,
            'expiry_date': recent_expiry,
        })

        future_share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity3.id,
            'user_id': self.test_user.id,
            'expiry_date': future_expiry,
        })

        # Run the cleanup cron job
        self.env['ha.entity.share']._cron_cleanup_expired_shares()

        # Only old_share should be deleted
        self.assertFalse(
            self.env['ha.entity.share'].search([('id', '=', old_share.id)]),
            "Old share (40 days) should be deleted"
        )
        self.assertTrue(
            self.env['ha.entity.share'].search([('id', '=', recent_share.id)]),
            "Recent share (15 days) should NOT be deleted"
        )
        self.assertTrue(
            self.env['ha.entity.share'].search([('id', '=', future_share.id)]),
            "Future share should NOT be deleted"
        )
