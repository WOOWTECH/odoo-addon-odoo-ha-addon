# -*- coding: utf-8 -*-
# Part of odoo_ha_addon. See LICENSE file for full copyright and licensing details.

"""
Entity Share Wizard

This wizard allows administrators and HA managers to share entities or entity groups
with specific users. It supports:
- Selecting multiple users to share with
- Setting permission levels (view/control)
- Setting optional expiration dates
- Preventing duplicate shares
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class HAEntityShareWizard(models.TransientModel):
    _name = 'ha.entity.share.wizard'
    _description = 'Share Entity/Group Wizard'

    # Context-based fields (populated from active record)
    entity_id = fields.Many2one(
        'ha.entity',
        string='Entity',
        help='The entity to share (set automatically from context)'
    )
    group_id = fields.Many2one(
        'ha.entity.group',
        string='Entity Group',
        help='The entity group to share (set automatically from context)'
    )

    # Computed field for display
    target_name = fields.Char(
        string='Target',
        compute='_compute_target_name',
        help='Name of the entity/group being shared'
    )

    # Share settings
    user_ids = fields.Many2many(
        'res.users',
        'ha_entity_share_wizard_user_rel',
        'wizard_id',
        'user_id',
        string='Share With Users',
        required=True,
        domain="[('share', '=', False)]",  # Exclude portal users
        help='Select the users to share with'
    )

    permission = fields.Selection([
        ('view', 'View Only'),
        ('control', 'Can Control')
    ], string='Permission', required=True, default='view',
        help='Permission level for shared users:\n'
             '- View Only: Users can only view the entity/group state\n'
             '- Can Control: Users can control the entity/group'
    )

    expiry_date = fields.Datetime(
        string='Expiry Date',
        help='Optional expiration date. Leave empty for no expiration.'
    )

    # Info fields
    existing_share_count = fields.Integer(
        string='Existing Shares',
        compute='_compute_existing_shares',
        help='Number of existing share records for this entity/group'
    )

    existing_share_users = fields.Char(
        string='Already Shared With',
        compute='_compute_existing_shares',
        help='Users who already have access to this entity/group'
    )

    @api.depends('entity_id', 'group_id')
    def _compute_target_name(self):
        """Compute display name for the share target."""
        for wizard in self:
            if wizard.entity_id:
                wizard.target_name = wizard.entity_id.name or wizard.entity_id.entity_id
            elif wizard.group_id:
                wizard.target_name = wizard.group_id.name
            else:
                wizard.target_name = _('Unknown')

    @api.depends('entity_id', 'group_id')
    def _compute_existing_shares(self):
        """Compute existing share records for the entity/group."""
        for wizard in self:
            ShareModel = self.env['ha.entity.share']
            if wizard.entity_id:
                shares = ShareModel.search([('entity_id', '=', wizard.entity_id.id)])
            elif wizard.group_id:
                shares = ShareModel.search([('group_id', '=', wizard.group_id.id)])
            else:
                shares = ShareModel.browse()

            wizard.existing_share_count = len(shares)
            if shares:
                user_names = shares.mapped('user_id.name')
                wizard.existing_share_users = ', '.join(user_names[:5])
                if len(user_names) > 5:
                    wizard.existing_share_users += _(' (and %d more)') % (len(user_names) - 5)
            else:
                wizard.existing_share_users = ''

    @api.model
    def default_get(self, fields_list):
        """
        Populate entity_id or group_id from context.

        Context keys:
        - default_entity_id: Entity ID to share
        - default_group_id: Entity Group ID to share
        - active_model: Model name of the active record
        - active_id: ID of the active record

        Example: using following context:
        {
            'type': 'ir.actions.act_window',
            'name': _('Share Entity'),
            'res_model': 'ha.entity.share.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_entity_id': self.id,
            },
        }
        """
        res = super().default_get(fields_list)
        context = self.env.context

        # Check context for explicit defaults
        if context.get('default_entity_id'):
            res['entity_id'] = context['default_entity_id']
        elif context.get('default_group_id'):
            res['group_id'] = context['default_group_id']
        # Fallback to active_model/active_id
        elif context.get('active_model') and context.get('active_id'):
            active_model = context['active_model']
            active_id = context['active_id']
            if active_model == 'ha.entity':
                res['entity_id'] = active_id
            elif active_model == 'ha.entity.group':
                res['group_id'] = active_id

        return res

    @api.constrains('entity_id', 'group_id')
    def _check_entity_or_group(self):
        """Ensure exactly one of entity_id or group_id is set."""
        for wizard in self:
            if wizard.entity_id and wizard.group_id:
                raise ValidationError(
                    _('Cannot share both an entity and a group at the same time. '
                      'Please select only one.')
                )
            if not wizard.entity_id and not wizard.group_id:
                raise ValidationError(
                    _('Please specify an entity or entity group to share.')
                )

    @api.constrains('user_ids')
    def _check_users_selected(self):
        """Ensure at least one user is selected."""
        for wizard in self:
            if not wizard.user_ids:
                raise ValidationError(_('Please select at least one user to share with.'))

    def action_share(self):
        """
        Create share records for each selected user.

        Returns:
            dict: Action to display notification with results
        """
        self.ensure_one()

        if not self.user_ids:
            raise UserError(_('Please select at least one user to share with.'))

        ShareModel = self.env['ha.entity.share']
        created_count = 0
        skipped_count = 0
        skipped_users = []

        for user in self.user_ids:
            # Check for existing share
            domain = [('user_id', '=', user.id)]
            if self.entity_id:
                domain.append(('entity_id', '=', self.entity_id.id))
            else:
                domain.append(('group_id', '=', self.group_id.id))

            existing = ShareModel.search(domain, limit=1)
            if existing:
                # Update existing share instead of creating duplicate
                existing.write({
                    'permission': self.permission,
                    'expiry_date': self.expiry_date,
                    'notification_sent': False,  # Reset notification flag
                })
                skipped_count += 1
                skipped_users.append(user.name)
                _logger.info(
                    f"Updated existing share for user {user.name}: "
                    f"permission={self.permission}, expiry={self.expiry_date}"
                )
            else:
                # Create new share record
                vals = {
                    'user_id': user.id,
                    'permission': self.permission,
                    'expiry_date': self.expiry_date,
                }
                if self.entity_id:
                    vals['entity_id'] = self.entity_id.id
                else:
                    vals['group_id'] = self.group_id.id

                ShareModel.create(vals)
                created_count += 1
                _logger.info(
                    f"Created share for user {user.name}: "
                    f"target={'entity' if self.entity_id else 'group'}, "
                    f"permission={self.permission}, expiry={self.expiry_date}"
                )

        # Prepare result message
        target_name = self.target_name
        if created_count > 0 and skipped_count > 0:
            message = _(
                'Shared "%(target)s" with %(created)d user(s).\n'
                'Updated %(skipped)d existing share(s): %(users)s'
            ) % {
                'target': target_name,
                'created': created_count,
                'skipped': skipped_count,
                'users': ', '.join(skipped_users),
            }
            msg_type = 'success'
        elif created_count > 0:
            message = _('Successfully shared "%(target)s" with %(count)d user(s).') % {
                'target': target_name,
                'count': created_count,
            }
            msg_type = 'success'
        else:
            message = _(
                'All selected users already have access to "%(target)s". '
                'Updated %(count)d existing share(s).'
            ) % {
                'target': target_name,
                'count': skipped_count,
            }
            msg_type = 'info'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Share Complete'),
                'message': message,
                'type': msg_type,
                'sticky': False,
            }
        }

    def action_cancel(self):
        """Close the wizard without sharing."""
        return {'type': 'ir.actions.act_window_close'}
