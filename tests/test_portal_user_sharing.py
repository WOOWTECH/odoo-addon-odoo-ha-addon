# -*- coding: utf-8 -*-
# Part of odoo_ha_addon. See LICENSE file for full copyright and licensing details.

"""
Tests for Portal User Sharing functionality.

This module tests that:
1. Portal users can be selected in the share wizard
2. Share records can be created for portal users
3. Portal users can access shared entities via portal routes
4. Permission levels (view/control) work correctly for portal users
5. Expiry dates work correctly for portal users
"""

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, AccessError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'ha_portal_sharing')
class TestPortalUserSharing(TransactionCase):
    """Test portal user sharing functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a test HA instance
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Test HA Instance',
            'api_url': 'http://test-ha.local:8123',
            'api_token': 'test_token_12345',
        })

        # Create a test entity
        cls.test_entity = cls.env['ha.entity'].create({
            'name': 'Test Light',
            'entity_id': 'light.test_light',
            'domain': 'light',
            'entity_state': 'on',
            'ha_instance_id': cls.ha_instance.id,
        })

        # Create a test entity group
        cls.test_group = cls.env['ha.entity.group'].create({
            'name': 'Test Group',
            'ha_instance_id': cls.ha_instance.id,
            'entity_ids': [(6, 0, [cls.test_entity.id])],
        })

        # Create an internal user (share=False)
        cls.internal_user = cls.env['res.users'].create({
            'name': 'Internal Test User',
            'login': 'internal_test_user',
            'email': 'internal@test.com',
            'groups_id': [(6, 0, [cls.env.ref('odoo_ha_addon.group_ha_user').id])],
        })

        # Create a portal user (share=True)
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Portal Test User',
            'login': 'portal_test_user',
            'email': 'portal@test.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def test_01_portal_user_is_share_true(self):
        """Test that portal user has share=True flag."""
        self.assertTrue(
            self.portal_user.share,
            "Portal user should have share=True"
        )
        self.assertFalse(
            self.internal_user.share,
            "Internal user should have share=False"
        )

    def test_02_wizard_domain_includes_portal_users(self):
        """Test that share wizard domain includes portal users."""
        # Create wizard for entity
        wizard = self.env['ha.entity.share.wizard'].create({
            'entity_id': self.test_entity.id,
            'user_ids': [(6, 0, [self.portal_user.id])],
            'permission': 'view',
        })

        # Portal user should be selectable
        self.assertIn(
            self.portal_user,
            wizard.user_ids,
            "Portal user should be selectable in wizard"
        )

    def test_03_wizard_domain_includes_internal_users(self):
        """Test that share wizard still includes internal users."""
        # Create wizard for entity with internal user
        wizard = self.env['ha.entity.share.wizard'].create({
            'entity_id': self.test_entity.id,
            'user_ids': [(6, 0, [self.internal_user.id])],
            'permission': 'view',
        })

        self.assertIn(
            self.internal_user,
            wizard.user_ids,
            "Internal user should be selectable in wizard"
        )

    def test_04_wizard_accepts_mixed_users(self):
        """Test that wizard accepts both portal and internal users together."""
        wizard = self.env['ha.entity.share.wizard'].create({
            'entity_id': self.test_entity.id,
            'user_ids': [(6, 0, [self.internal_user.id, self.portal_user.id])],
            'permission': 'view',
        })

        self.assertEqual(len(wizard.user_ids), 2, "Should have 2 users selected")
        self.assertIn(self.internal_user, wizard.user_ids)
        self.assertIn(self.portal_user, wizard.user_ids)

    def test_05_user_types_display_computed(self):
        """Test that user_types_display is computed correctly."""
        # Only internal user
        wizard1 = self.env['ha.entity.share.wizard'].create({
            'entity_id': self.test_entity.id,
            'user_ids': [(6, 0, [self.internal_user.id])],
            'permission': 'view',
        })
        self.assertIn('1 internal', wizard1.user_types_display)

        # Only portal user
        wizard2 = self.env['ha.entity.share.wizard'].create({
            'entity_id': self.test_entity.id,
            'user_ids': [(6, 0, [self.portal_user.id])],
            'permission': 'view',
        })
        self.assertIn('1 portal', wizard2.user_types_display)

        # Both users
        wizard3 = self.env['ha.entity.share.wizard'].create({
            'entity_id': self.test_entity.id,
            'user_ids': [(6, 0, [self.internal_user.id, self.portal_user.id])],
            'permission': 'view',
        })
        self.assertIn('1 internal', wizard3.user_types_display)
        self.assertIn('1 portal', wizard3.user_types_display)

    def test_06_share_created_for_portal_user(self):
        """Test that share record is created successfully for portal user."""
        wizard = self.env['ha.entity.share.wizard'].create({
            'entity_id': self.test_entity.id,
            'user_ids': [(6, 0, [self.portal_user.id])],
            'permission': 'view',
        })

        # Execute share action
        wizard.action_share()

        # Verify share record created
        share = self.env['ha.entity.share'].search([
            ('entity_id', '=', self.test_entity.id),
            ('user_id', '=', self.portal_user.id),
        ])

        self.assertTrue(share, "Share record should be created for portal user")
        self.assertEqual(share.permission, 'view')

    def test_07_share_with_control_permission(self):
        """Test portal user share with control permission."""
        wizard = self.env['ha.entity.share.wizard'].create({
            'entity_id': self.test_entity.id,
            'user_ids': [(6, 0, [self.portal_user.id])],
            'permission': 'control',
        })

        wizard.action_share()

        share = self.env['ha.entity.share'].search([
            ('entity_id', '=', self.test_entity.id),
            ('user_id', '=', self.portal_user.id),
        ])

        self.assertEqual(share.permission, 'control')

    def test_08_share_with_expiry_date(self):
        """Test portal user share with expiry date."""
        future_date = datetime.now() + timedelta(days=7)

        wizard = self.env['ha.entity.share.wizard'].create({
            'entity_id': self.test_entity.id,
            'user_ids': [(6, 0, [self.portal_user.id])],
            'permission': 'view',
            'expiry_date': future_date,
        })

        wizard.action_share()

        share = self.env['ha.entity.share'].search([
            ('entity_id', '=', self.test_entity.id),
            ('user_id', '=', self.portal_user.id),
        ])

        self.assertFalse(share.is_expired, "Share should not be expired yet")

    def test_09_expired_share_is_detected(self):
        """Test that expired share is correctly detected."""
        past_date = datetime.now() - timedelta(days=1)

        # Create share directly with past expiry
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
            'expiry_date': past_date,
        })

        self.assertTrue(share.is_expired, "Share should be expired")

    def test_10_group_share_for_portal_user(self):
        """Test sharing entity group with portal user."""
        wizard = self.env['ha.entity.share.wizard'].create({
            'group_id': self.test_group.id,
            'user_ids': [(6, 0, [self.portal_user.id])],
            'permission': 'view',
        })

        wizard.action_share()

        share = self.env['ha.entity.share'].search([
            ('group_id', '=', self.test_group.id),
            ('user_id', '=', self.portal_user.id),
        ])

        self.assertTrue(share, "Group share should be created for portal user")

    def test_11_get_shares_for_portal_user(self):
        """Test retrieving shares for a portal user."""
        # Create shares
        self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        # Get shares for portal user
        shares = self.env['ha.entity.share'].get_shares_for_user(self.portal_user.id)

        self.assertTrue(len(shares) > 0, "Should find shares for portal user")

    def test_12_get_shared_entities_for_portal_user(self):
        """Test retrieving shared entities for a portal user."""
        # Create share
        self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        # Get shared entities
        entities = self.env['ha.entity.share'].get_shared_entities_for_user(
            self.portal_user.id
        )

        self.assertIn(self.test_entity, entities)

    def test_13_update_existing_share_for_portal_user(self):
        """Test updating existing share for portal user via wizard."""
        # Create initial share
        self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        # Update via wizard with different permission
        wizard = self.env['ha.entity.share.wizard'].create({
            'entity_id': self.test_entity.id,
            'user_ids': [(6, 0, [self.portal_user.id])],
            'permission': 'control',
        })

        wizard.action_share()

        # Verify updated (not duplicated)
        shares = self.env['ha.entity.share'].search([
            ('entity_id', '=', self.test_entity.id),
            ('user_id', '=', self.portal_user.id),
        ])

        self.assertEqual(len(shares), 1, "Should have only one share record")
        self.assertEqual(shares.permission, 'control', "Permission should be updated")

    def test_14_revoke_share_for_portal_user(self):
        """Test revoking share for portal user."""
        # Create share
        share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.portal_user.id,
            'permission': 'view',
        })

        share_id = share.id

        # Revoke
        share.action_revoke()

        # Verify deleted
        self.assertFalse(
            self.env['ha.entity.share'].browse(share_id).exists(),
            "Share should be deleted after revoke"
        )
