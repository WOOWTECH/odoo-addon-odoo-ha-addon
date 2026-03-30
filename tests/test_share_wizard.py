# -*- coding: utf-8 -*-
# Part of odoo_ha_addon. See LICENSE file for full copyright and licensing details.

"""
Unit tests for ha.entity.share.wizard model.

This module tests:
- Wizard creation and default_get behavior
- Context-based entity/group population
- action_share method (creating share records)
- Duplicate share handling (update existing)
- Permission and expiry settings
"""

from datetime import timedelta
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, UserError
from odoo import fields


@tagged('post_install', '-at_install')
class TestShareWizardBasic(TransactionCase):
    """Test cases for share wizard basic operations"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test HA instance
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Wizard Test HA Instance',
            'api_url': 'http://wizard-test.local:8123',
            'api_token': 'wizard_test_token_12345',
            'active': True,
        })

        # Create test entity
        cls.test_entity = cls.env['ha.entity'].sudo().create({
            'name': 'Test Wizard Entity',
            'entity_id': 'sensor.wizard_test',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        # Create test entity group
        cls.test_group = cls.env['ha.entity.group'].sudo().create({
            'name': 'Test Wizard Group',
            'ha_instance_id': cls.ha_instance.id,
        })

        # Create test users
        cls.test_user1 = cls.env['res.users'].create({
            'name': 'Wizard Test User 1',
            'login': 'wizard_test_user1',
            'email': 'wizard_user1@test.local',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('odoo_ha_addon.group_ha_user').id
            ])]
        })

        cls.test_user2 = cls.env['res.users'].create({
            'name': 'Wizard Test User 2',
            'login': 'wizard_test_user2',
            'email': 'wizard_user2@test.local',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('odoo_ha_addon.group_ha_user').id
            ])]
        })

        # Create HA Manager user for wizard testing
        cls.manager_user = cls.env['res.users'].create({
            'name': 'Wizard Manager User',
            'login': 'wizard_manager_user',
            'email': 'wizard_manager@test.local',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('odoo_ha_addon.group_ha_manager').id
            ])]
        })

    def test_wizard_default_get_with_entity_context(self):
        """Test wizard populates entity_id from context"""
        wizard = self.env['ha.entity.share.wizard'].with_context(
            default_entity_id=self.test_entity.id
        ).create({
            'user_ids': [(6, 0, [self.test_user1.id])],
        })

        self.assertEqual(
            wizard.entity_id, self.test_entity,
            "Wizard should populate entity_id from context"
        )
        self.assertFalse(wizard.group_id)

    def test_wizard_default_get_with_group_context(self):
        """Test wizard populates group_id from context"""
        wizard = self.env['ha.entity.share.wizard'].with_context(
            default_group_id=self.test_group.id
        ).create({
            'user_ids': [(6, 0, [self.test_user1.id])],
        })

        self.assertEqual(
            wizard.group_id, self.test_group,
            "Wizard should populate group_id from context"
        )
        self.assertFalse(wizard.entity_id)

    def test_wizard_default_get_with_active_model_entity(self):
        """Test wizard populates entity_id from active_model/active_id"""
        wizard = self.env['ha.entity.share.wizard'].with_context(
            active_model='ha.entity',
            active_id=self.test_entity.id
        ).create({
            'user_ids': [(6, 0, [self.test_user1.id])],
        })

        self.assertEqual(
            wizard.entity_id, self.test_entity,
            "Wizard should populate entity_id from active_model"
        )

    def test_wizard_default_get_with_active_model_group(self):
        """Test wizard populates group_id from active_model/active_id"""
        wizard = self.env['ha.entity.share.wizard'].with_context(
            active_model='ha.entity.group',
            active_id=self.test_group.id
        ).create({
            'user_ids': [(6, 0, [self.test_user1.id])],
        })

        self.assertEqual(
            wizard.group_id, self.test_group,
            "Wizard should populate group_id from active_model"
        )

    def test_wizard_default_permission(self):
        """Test wizard default permission is 'view'"""
        wizard = self.env['ha.entity.share.wizard'].with_context(
            default_entity_id=self.test_entity.id
        ).create({
            'user_ids': [(6, 0, [self.test_user1.id])],
        })

        self.assertEqual(
            wizard.permission, 'view',
            "Default permission should be 'view'"
        )

    def test_wizard_compute_target_name_entity(self):
        """Test target_name is computed from entity name"""
        wizard = self.env['ha.entity.share.wizard'].with_context(
            default_entity_id=self.test_entity.id
        ).create({
            'user_ids': [(6, 0, [self.test_user1.id])],
        })

        self.assertEqual(
            wizard.target_name, self.test_entity.name,
            "target_name should be the entity name"
        )

    def test_wizard_compute_target_name_group(self):
        """Test target_name is computed from group name"""
        wizard = self.env['ha.entity.share.wizard'].with_context(
            default_group_id=self.test_group.id
        ).create({
            'user_ids': [(6, 0, [self.test_user1.id])],
        })

        self.assertEqual(
            wizard.target_name, self.test_group.name,
            "target_name should be the group name"
        )


@tagged('post_install', '-at_install')
class TestShareWizardConstraints(TransactionCase):
    """Test cases for share wizard constraints"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Constraint Wizard Test HA',
            'api_url': 'http://constraint-wizard.local:8123',
            'api_token': 'constraint_wizard_token',
            'active': True,
        })

        cls.test_entity = cls.env['ha.entity'].sudo().create({
            'name': 'Constraint Wizard Entity',
            'entity_id': 'sensor.constraint_wizard',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_group = cls.env['ha.entity.group'].sudo().create({
            'name': 'Constraint Wizard Group',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_user = cls.env['res.users'].create({
            'name': 'Constraint Wizard User',
            'login': 'constraint_wizard_user',
            'email': 'constraint_wizard@test.local',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

    def test_constraint_entity_or_group_not_both(self):
        """Test wizard cannot have both entity_id and group_id"""
        with self.assertRaises(ValidationError):
            self.env['ha.entity.share.wizard'].create({
                'entity_id': self.test_entity.id,
                'group_id': self.test_group.id,
                'user_ids': [(6, 0, [self.test_user.id])],
            })

    def test_constraint_entity_or_group_required(self):
        """Test wizard must have either entity_id or group_id"""
        with self.assertRaises(ValidationError):
            self.env['ha.entity.share.wizard'].create({
                'user_ids': [(6, 0, [self.test_user.id])],
            })


@tagged('post_install', '-at_install')
class TestShareWizardActionShare(TransactionCase):
    """Test cases for share wizard action_share method"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Action Share Test HA',
            'api_url': 'http://action-share.local:8123',
            'api_token': 'action_share_token',
            'active': True,
        })

        cls.test_entity = cls.env['ha.entity'].sudo().create({
            'name': 'Action Share Entity',
            'entity_id': 'sensor.action_share',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_group = cls.env['ha.entity.group'].sudo().create({
            'name': 'Action Share Group',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_user1 = cls.env['res.users'].create({
            'name': 'Action Share User 1',
            'login': 'action_share_user1',
            'email': 'action_share1@test.local',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

        cls.test_user2 = cls.env['res.users'].create({
            'name': 'Action Share User 2',
            'login': 'action_share_user2',
            'email': 'action_share2@test.local',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

    def test_action_share_creates_entity_share(self):
        """Test action_share creates ha.entity.share record for entity"""
        wizard = self.env['ha.entity.share.wizard'].with_context(
            default_entity_id=self.test_entity.id
        ).create({
            'user_ids': [(6, 0, [self.test_user1.id])],
            'permission': 'view',
        })

        result = wizard.action_share()

        # Verify share was created
        share = self.env['ha.entity.share'].search([
            ('entity_id', '=', self.test_entity.id),
            ('user_id', '=', self.test_user1.id),
        ])
        self.assertTrue(share, "Share record should be created")
        self.assertEqual(share.permission, 'view')

        # Verify result is a notification
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')

    def test_action_share_creates_group_share(self):
        """Test action_share creates ha.entity.share record for group"""
        wizard = self.env['ha.entity.share.wizard'].with_context(
            default_group_id=self.test_group.id
        ).create({
            'user_ids': [(6, 0, [self.test_user1.id])],
            'permission': 'control',
        })

        wizard.action_share()

        # Verify share was created
        share = self.env['ha.entity.share'].search([
            ('group_id', '=', self.test_group.id),
            ('user_id', '=', self.test_user1.id),
        ])
        self.assertTrue(share, "Share record should be created")
        self.assertEqual(share.permission, 'control')

    def test_action_share_multiple_users(self):
        """Test action_share creates shares for multiple users"""
        wizard = self.env['ha.entity.share.wizard'].with_context(
            default_entity_id=self.test_entity.id
        ).create({
            'user_ids': [(6, 0, [self.test_user1.id, self.test_user2.id])],
            'permission': 'view',
        })

        wizard.action_share()

        # Verify shares were created for both users
        shares = self.env['ha.entity.share'].search([
            ('entity_id', '=', self.test_entity.id),
            ('user_id', 'in', [self.test_user1.id, self.test_user2.id]),
        ])
        self.assertEqual(len(shares), 2, "Shares should be created for both users")

    def test_action_share_with_expiry(self):
        """Test action_share sets expiry_date correctly"""
        future_date = fields.Datetime.now() + timedelta(days=30)

        wizard = self.env['ha.entity.share.wizard'].with_context(
            default_entity_id=self.test_entity.id
        ).create({
            'user_ids': [(6, 0, [self.test_user1.id])],
            'permission': 'view',
            'expiry_date': future_date,
        })

        wizard.action_share()

        # Verify share has correct expiry
        share = self.env['ha.entity.share'].search([
            ('entity_id', '=', self.test_entity.id),
            ('user_id', '=', self.test_user1.id),
        ])
        self.assertEqual(share.expiry_date, future_date)

    def test_action_share_updates_existing(self):
        """Test action_share updates existing share instead of creating duplicate"""
        # Create existing share
        existing_share = self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user1.id,
            'permission': 'view',
        })

        # Run wizard to update
        wizard = self.env['ha.entity.share.wizard'].with_context(
            default_entity_id=self.test_entity.id
        ).create({
            'user_ids': [(6, 0, [self.test_user1.id])],
            'permission': 'control',  # Different permission
        })

        wizard.action_share()

        # Verify only one share exists and it's updated
        shares = self.env['ha.entity.share'].search([
            ('entity_id', '=', self.test_entity.id),
            ('user_id', '=', self.test_user1.id),
        ])
        self.assertEqual(len(shares), 1, "Should still be only one share")
        self.assertEqual(shares.permission, 'control', "Permission should be updated")

    def test_action_share_mixed_new_and_existing(self):
        """Test action_share handles mix of new and existing users"""
        # Create existing share for user1
        self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user1.id,
            'permission': 'view',
        })

        # Run wizard for both users
        wizard = self.env['ha.entity.share.wizard'].with_context(
            default_entity_id=self.test_entity.id
        ).create({
            'user_ids': [(6, 0, [self.test_user1.id, self.test_user2.id])],
            'permission': 'control',
        })

        result = wizard.action_share()

        # Verify user1's share was updated
        share1 = self.env['ha.entity.share'].search([
            ('entity_id', '=', self.test_entity.id),
            ('user_id', '=', self.test_user1.id),
        ])
        self.assertEqual(share1.permission, 'control')

        # Verify user2's share was created
        share2 = self.env['ha.entity.share'].search([
            ('entity_id', '=', self.test_entity.id),
            ('user_id', '=', self.test_user2.id),
        ])
        self.assertTrue(share2)
        self.assertEqual(share2.permission, 'control')


@tagged('post_install', '-at_install')
class TestShareWizardExistingShares(TransactionCase):
    """Test cases for wizard computed fields about existing shares"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Existing Shares Test HA',
            'api_url': 'http://existing-shares.local:8123',
            'api_token': 'existing_shares_token',
            'active': True,
        })

        cls.test_entity = cls.env['ha.entity'].sudo().create({
            'name': 'Existing Shares Entity',
            'entity_id': 'sensor.existing_shares',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_user1 = cls.env['res.users'].create({
            'name': 'Existing Share User 1',
            'login': 'existing_share_user1',
            'email': 'existing1@test.local',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

        cls.test_user2 = cls.env['res.users'].create({
            'name': 'Existing Share User 2',
            'login': 'existing_share_user2',
            'email': 'existing2@test.local',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

    def test_existing_share_count_zero(self):
        """Test existing_share_count is 0 when no shares exist"""
        wizard = self.env['ha.entity.share.wizard'].with_context(
            default_entity_id=self.test_entity.id
        ).create({
            'user_ids': [(6, 0, [self.test_user1.id])],
        })

        self.assertEqual(wizard.existing_share_count, 0)
        self.assertEqual(wizard.existing_share_users, '')

    def test_existing_share_count_with_shares(self):
        """Test existing_share_count shows correct count"""
        # Create existing shares
        self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user1.id,
            'permission': 'view',
        })
        self.env['ha.entity.share'].create({
            'entity_id': self.test_entity.id,
            'user_id': self.test_user2.id,
            'permission': 'control',
        })

        wizard = self.env['ha.entity.share.wizard'].with_context(
            default_entity_id=self.test_entity.id
        ).create({
            'user_ids': [(6, 0, [self.test_user1.id])],
        })

        self.assertEqual(wizard.existing_share_count, 2)
        self.assertIn(self.test_user1.name, wizard.existing_share_users)
        self.assertIn(self.test_user2.name, wizard.existing_share_users)


@tagged('post_install', '-at_install')
class TestShareWizardFromAction(TransactionCase):
    """Test cases for wizard opened from entity/group action_share method"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ha_instance = cls.env['ha.instance'].create({
            'name': 'Action Test HA',
            'api_url': 'http://action-test.local:8123',
            'api_token': 'action_test_token',
            'active': True,
        })

        cls.test_entity = cls.env['ha.entity'].sudo().create({
            'name': 'Action Test Entity',
            'entity_id': 'sensor.action_test',
            'domain': 'sensor',
            'ha_instance_id': cls.ha_instance.id,
        })

        cls.test_group = cls.env['ha.entity.group'].sudo().create({
            'name': 'Action Test Group',
            'ha_instance_id': cls.ha_instance.id,
        })

    def test_entity_action_share_returns_wizard(self):
        """Test entity.action_share() returns wizard action"""
        result = self.test_entity.action_share()

        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'ha.entity.share.wizard')
        self.assertEqual(result['target'], 'new')
        self.assertEqual(result['context']['default_entity_id'], self.test_entity.id)

    def test_group_action_share_returns_wizard(self):
        """Test group.action_share() returns wizard action"""
        result = self.test_group.action_share()

        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'ha.entity.share.wizard')
        self.assertEqual(result['target'], 'new')
        self.assertEqual(result['context']['default_group_id'], self.test_group.id)