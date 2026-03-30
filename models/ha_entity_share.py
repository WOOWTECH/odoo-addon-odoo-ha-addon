# -*- coding: utf-8 -*-
# Part of odoo_ha_addon. See LICENSE file for full copyright and licensing details.

"""
Entity/Group Share Model

This module defines the ha.entity.share model for tracking share relationships
between entities/groups and users. It supports:
- Sharing individual entities (ha.entity)
- Sharing entity groups (ha.entity.group)
- Permission levels: view-only or control
- Optional expiration dates
- Notification tracking for expiry alerts
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class HAEntityShare(models.Model):
    _name = 'ha.entity.share'
    _description = 'Entity/Group Share Record'
    _rec_name = 'display_name'
    _order = 'create_date desc'

    # Target: entity, group, or device (mutually exclusive)
    entity_id = fields.Many2one(
        'ha.entity',
        string='Entity',
        ondelete='cascade',
        index=True,
        help='The entity being shared. Only one of entity_id, group_id, or device_id must be set.'
    )
    group_id = fields.Many2one(
        'ha.entity.group',
        string='Entity Group',
        ondelete='cascade',
        index=True,
        help='The entity group being shared. Only one of entity_id, group_id, or device_id must be set.'
    )
    device_id = fields.Many2one(
        'ha.device',
        string='Device',
        ondelete='cascade',
        index=True,
        help='The device being shared. Only one of entity_id, group_id, or device_id must be set.'
    )

    # Shared with
    user_id = fields.Many2one(
        'res.users',
        string='Shared With',
        required=True,
        ondelete='cascade',
        index=True,
        help='The user this entity/group is shared with.'
    )

    # Permission level
    permission = fields.Selection([
        ('view', 'View Only'),
        ('control', 'Can Control')
    ], string='Permission', required=True, default='view',
        help='Permission level for the shared user:\n'
             '- View Only: User can only view the entity/group state\n'
             '- Can Control: User can control the entity/group (turn on/off, etc.)'
    )

    # Expiration
    expiry_date = fields.Datetime(
        string='Expiry Date',
        help='Optional expiration date. After this date, the share will be considered expired.'
    )

    # Notification tracking
    notification_sent = fields.Boolean(
        string='Expiry Notification Sent',
        default=False,
        help='Whether an expiry notification has been sent to the user.'
    )

    # Computed fields
    ha_instance_id = fields.Many2one(
        'ha.instance',
        string='HA Instance',
        compute='_compute_ha_instance_id',
        store=True,
        help='The Home Assistant instance this share belongs to (derived from entity/group).'
    )

    is_expired = fields.Boolean(
        string='Is Expired',
        compute='_compute_is_expired',
        search='_search_is_expired',
        help='Whether this share has expired based on expiry_date.'
    )

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )

    # SQL Constraints
    _sql_constraints = [
        # entity_id, group_id, and device_id are mutually exclusive (exactly one must be set)
        ('entity_group_device_exclusive',
         'CHECK('
         '(entity_id IS NOT NULL AND group_id IS NULL AND device_id IS NULL) OR '
         '(entity_id IS NULL AND group_id IS NOT NULL AND device_id IS NULL) OR '
         '(entity_id IS NULL AND group_id IS NULL AND device_id IS NOT NULL)'
         ')',
         'Must specify exactly one of entity_id, group_id, or device_id'),
        # Unique constraint: same entity + user combination
        ('unique_entity_user',
         'UNIQUE(entity_id, user_id)',
         'Entity already shared with this user'),
        # Unique constraint: same group + user combination
        ('unique_group_user',
         'UNIQUE(group_id, user_id)',
         'Group already shared with this user'),
        # Unique constraint: same device + user combination
        ('unique_device_user',
         'UNIQUE(device_id, user_id)',
         'Device already shared with this user'),
    ]

    @api.depends('entity_id', 'entity_id.ha_instance_id',
                 'group_id', 'group_id.ha_instance_id',
                 'device_id', 'device_id.ha_instance_id')
    def _compute_ha_instance_id(self):
        """Compute ha_instance_id from entity, group, or device."""
        for record in self:
            if record.entity_id:
                record.ha_instance_id = record.entity_id.ha_instance_id
            elif record.group_id:
                record.ha_instance_id = record.group_id.ha_instance_id
            elif record.device_id:
                record.ha_instance_id = record.device_id.ha_instance_id
            else:
                record.ha_instance_id = False

    @api.depends('expiry_date')
    def _compute_is_expired(self):
        """Compute whether the share has expired."""
        now = fields.Datetime.now()
        for record in self:
            if record.expiry_date:
                record.is_expired = record.expiry_date < now
            else:
                record.is_expired = False

    def _search_is_expired(self, operator, value):
        """Allow searching for expired/non-expired shares."""
        now = fields.Datetime.now()
        if operator == '=' and value:
            # Search for expired shares
            return ['&', ('expiry_date', '!=', False), ('expiry_date', '<', now)]
        elif operator == '=' and not value:
            # Search for non-expired shares (including those without expiry_date)
            return ['|', ('expiry_date', '=', False), ('expiry_date', '>=', now)]
        elif operator == '!=' and value:
            # Not expired = non-expired
            return ['|', ('expiry_date', '=', False), ('expiry_date', '>=', now)]
        elif operator == '!=' and not value:
            # Not non-expired = expired
            return ['&', ('expiry_date', '!=', False), ('expiry_date', '<', now)]
        return []

    @api.depends('entity_id', 'entity_id.name', 'entity_id.entity_id',
                 'group_id', 'group_id.name',
                 'device_id', 'device_id.name', 'device_id.name_by_user',
                 'user_id', 'user_id.name')
    def _compute_display_name(self):
        """Compute display name for the share record."""
        for record in self:
            if record.entity_id:
                target_name = record.entity_id.name or record.entity_id.entity_id
                target_type = _('Entity')
            elif record.group_id:
                target_name = record.group_id.name
                target_type = _('Group')
            elif record.device_id:
                target_name = record.device_id.name_by_user or record.device_id.name
                target_type = _('Device')
            else:
                target_name = _('Unknown')
                target_type = ''

            user_name = record.user_id.name if record.user_id else _('Unknown User')

            if target_type:
                record.display_name = _('%(target_type)s "%(target)s" shared with %(user)s') % {
                    'target_type': target_type,
                    'target': target_name,
                    'user': user_name,
                }
            else:
                record.display_name = _('Share with %(user)s') % {'user': user_name}

    @api.constrains('entity_id', 'group_id', 'device_id')
    def _check_entity_group_or_device(self):
        """Ensure exactly one of entity_id, group_id, or device_id is set."""
        for record in self:
            set_count = sum([
                bool(record.entity_id),
                bool(record.group_id),
                bool(record.device_id)
            ])
            if set_count > 1:
                raise ValidationError(
                    _('Cannot specify multiple targets. Please choose only one of: entity, group, or device.')
                )
            if set_count == 0:
                raise ValidationError(
                    _('Must specify an entity, group, or device to share.')
                )

    @api.constrains('user_id', 'entity_id', 'group_id', 'device_id')
    def _check_not_share_to_owner(self):
        """Prevent sharing to the record owner (optional business rule)."""
        for record in self:
            # Get the owner (creator) of the entity/group/device
            target = record.entity_id or record.group_id or record.device_id
            if target and target.create_uid == record.user_id:
                _logger.warning(
                    f"Share created for entity/group/device owner: "
                    f"user={record.user_id.name}, target={target._name}:{target.id}"
                )
                # Note: This is just a warning, not a hard constraint
                # Uncomment below to enforce:
                # raise ValidationError(
                #     _('Cannot share with the owner of the entity/group/device.')
                # )

    def action_extend_expiry(self, days=30):
        """
        Extend the expiry date by the specified number of days.

        Args:
            days: Number of days to extend (default: 30)
        """
        self.ensure_one()
        from datetime import timedelta

        if self.expiry_date:
            base_date = max(self.expiry_date, fields.Datetime.now())
        else:
            base_date = fields.Datetime.now()

        self.expiry_date = base_date + timedelta(days=days)
        self.notification_sent = False  # Reset notification flag
        _logger.info(
            f"Extended share expiry: {self.display_name} -> {self.expiry_date}"
        )

    def action_revoke(self):
        """Revoke (delete) this share."""
        self.ensure_one()
        _logger.info(f"Revoking share: {self.display_name}")
        self.unlink()

    @api.model
    def get_shares_for_user(self, user_id=None, include_expired=False):
        """
        Get all shares for a specific user.

        Args:
            user_id: User ID to get shares for (default: current user)
            include_expired: Whether to include expired shares

        Returns:
            Recordset of ha.entity.share records
        """
        if user_id is None:
            user_id = self.env.uid

        domain = [('user_id', '=', user_id)]
        if not include_expired:
            domain.append(('is_expired', '=', False))

        return self.search(domain)

    @api.model
    def get_shared_entities_for_user(self, user_id=None, permission=None):
        """
        Get all entities shared with a specific user.

        Args:
            user_id: User ID (default: current user)
            permission: Filter by permission level ('view' or 'control')

        Returns:
            Recordset of ha.entity records
        """
        domain = [('user_id', '=', user_id or self.env.uid), ('is_expired', '=', False)]
        if permission:
            domain.append(('permission', '=', permission))

        shares = self.search(domain)
        return shares.mapped('entity_id').filtered(lambda e: e)

    @api.model
    def get_shared_groups_for_user(self, user_id=None, permission=None):
        """
        Get all entity groups shared with a specific user.

        Args:
            user_id: User ID (default: current user)
            permission: Filter by permission level ('view' or 'control')

        Returns:
            Recordset of ha.entity.group records
        """
        domain = [('user_id', '=', user_id or self.env.uid), ('is_expired', '=', False)]
        if permission:
            domain.append(('permission', '=', permission))

        shares = self.search(domain)
        return shares.mapped('group_id').filtered(lambda g: g)

    @api.model
    def get_shared_devices_for_user(self, user_id=None, permission=None):
        """
        Get all devices shared with a specific user.

        Args:
            user_id: User ID (default: current user)
            permission: Filter by permission level ('view' or 'control')

        Returns:
            Recordset of ha.device records
        """
        domain = [('user_id', '=', user_id or self.env.uid), ('is_expired', '=', False)]
        if permission:
            domain.append(('permission', '=', permission))

        shares = self.search(domain)
        return shares.mapped('device_id').filtered(lambda d: d)

    @api.model
    def cleanup_expired_shares(self, delete=False, notify=True):
        """
        Cleanup expired shares.

        Args:
            delete: If True, delete expired shares. If False, just mark as expired.
            notify: If True, send notifications for newly expired shares.

        Returns:
            Number of shares processed
        """
        expired_shares = self.search([
            ('is_expired', '=', True),
            ('notification_sent', '=', False)
        ])

        count = len(expired_shares)
        if count == 0:
            return 0

        if notify:
            # Mark as notified (actual notification logic to be implemented later)
            expired_shares.write({'notification_sent': True})
            _logger.info(f"Marked {count} expired shares for notification")

        if delete:
            _logger.info(f"Deleting {count} expired shares")
            expired_shares.unlink()

        return count

    # ============================================
    # Cron Job Methods
    # ============================================

    @api.model
    def _cron_check_expiring_shares(self):
        """
        Cron Job: Check for shares expiring within 7 days and send notifications.

        This method is called by the cron job daily. It finds shares that:
        - Have an expiry_date set
        - Will expire within the next 7 days
        - Have not yet received an expiry notification

        For each such share, it creates a mail.activity for the share creator.
        """
        now = fields.Datetime.now()
        expiry_threshold = now + timedelta(days=7)

        expiring_shares = self.search([
            ('expiry_date', '!=', False),
            ('expiry_date', '<=', expiry_threshold),
            ('expiry_date', '>', now),
            ('notification_sent', '=', False),
        ])

        for share in expiring_shares:
            self._send_expiry_notification(share)
            share.notification_sent = True

        _logger.info(f"Sent expiry notifications for {len(expiring_shares)} shares")
        return True

    def _send_expiry_notification(self, share):
        """
        Send an expiry reminder notification to the share creator.

        Creates a mail.activity on the shared entity/group/device to notify
        the creator that the share will expire soon.

        Args:
            share: The ha.entity.share record to send notification for.
        """
        # Get the shared target (entity, group, or device)
        target = share.entity_id or share.group_id or share.device_id
        if not target:
            _logger.warning(f"Cannot send notification for share {share.id}: no target")
            return

        # Determine target info
        if share.entity_id:
            target_name = share.entity_id.name or share.entity_id.entity_id
            target_type = _('Entity')
            target_model = 'ha.entity'
        elif share.group_id:
            target_name = share.group_id.name
            target_type = _('Entity Group')
            target_model = 'ha.entity.group'
        else:
            target_name = share.device_id.name_by_user or share.device_id.name
            target_type = _('Device')
            target_model = 'ha.device'

        # Get the share creator (who should receive the notification)
        creator = share.create_uid

        # Get the model ID for the activity
        model_id = self.env['ir.model']._get(target_model).id

        # Format expiry date for display
        expiry_display = fields.Datetime.context_timestamp(
            share, share.expiry_date
        ).strftime('%Y-%m-%d %H:%M')

        # Create mail.activity for the creator
        try:
            self.env['mail.activity'].sudo().create({
                'res_model_id': model_id,
                'res_id': target.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': _('Share Expiring Soon'),
                'note': _(
                    '%(target_type)s "%(target_name)s" shared with %(user_name)s '
                    'will expire on %(expiry_date)s'
                ) % {
                    'target_type': target_type,
                    'target_name': target_name,
                    'user_name': share.user_id.name,
                    'expiry_date': expiry_display,
                },
                'user_id': creator.id,
                'date_deadline': share.expiry_date.date(),
            })
            _logger.info(
                f"Sent expiry notification: share_id={share.id}, "
                f"target={target_model}:{target.id}, creator={creator.login}"
            )
        except Exception as e:
            _logger.error(
                f"Failed to send expiry notification for share {share.id}: {e}"
            )

    @api.model
    def _cron_cleanup_expired_shares(self):
        """
        Cron Job: Clean up shares that have been expired for more than 30 days.

        This method is called by the cron job weekly. It finds and deletes shares that:
        - Have an expiry_date set
        - The expiry_date is more than 30 days in the past

        This helps keep the database clean from stale share records.
        """
        cleanup_threshold = fields.Datetime.now() - timedelta(days=30)

        expired_shares = self.search([
            ('expiry_date', '!=', False),
            ('expiry_date', '<', cleanup_threshold),
        ])

        count = len(expired_shares)
        if count > 0:
            # Log details before deletion
            for share in expired_shares:
                _logger.debug(
                    f"Cleaning up expired share: id={share.id}, "
                    f"expiry_date={share.expiry_date}, user={share.user_id.name}"
                )
            expired_shares.unlink()

        _logger.info(f"Cleaned up {count} expired share records")
        return True
