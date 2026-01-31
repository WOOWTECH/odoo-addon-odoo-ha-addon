# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class HAInstanceClearWizard(models.TransientModel):
    """
    確認清除 HA Instance 資料的 Wizard

    當用戶更改 HA Instance URL 後，可能需要清除舊資料。
    此 Wizard 提供確認對話框，避免誤刪。
    """
    _name = 'ha.instance.clear.wizard'
    _description = 'Clear HA Instance Data Wizard'

    instance_id = fields.Many2one(
        'ha.instance',
        string='Instance',
        required=True,
        readonly=True
    )

    instance_name = fields.Char(
        string='Instance Name',
        readonly=True
    )

    entity_count = fields.Integer(
        string='Entities',
        compute='_compute_data_stats',
        readonly=True
    )

    history_count = fields.Integer(
        string='History Records',
        compute='_compute_data_stats',
        readonly=True
    )

    area_count = fields.Integer(
        string='Areas',
        compute='_compute_data_stats',
        readonly=True
    )

    group_count = fields.Integer(
        string='Entity Groups',
        compute='_compute_data_stats',
        readonly=True
    )

    group_tag_count = fields.Integer(
        string='Group Tags',
        compute='_compute_data_stats',
        readonly=True
    )

    entity_tag_count = fields.Integer(
        string='Entity Tags',
        compute='_compute_data_stats',
        readonly=True
    )

    device_count = fields.Integer(
        string='Devices',
        compute='_compute_data_stats',
        readonly=True
    )

    label_count = fields.Integer(
        string='Labels',
        compute='_compute_data_stats',
        readonly=True
    )

    queue_count = fields.Integer(
        string='WebSocket Queue',
        compute='_compute_data_stats',
        readonly=True
    )

    @api.depends('instance_id')
    def _compute_data_stats(self):
        """計算此實例的資料統計"""
        for wizard in self:
            if wizard.instance_id:
                instance_id = wizard.instance_id.id

                # 統計各類資料數量
                wizard.entity_count = self.env['ha.entity'].search_count([
                    ('ha_instance_id', '=', instance_id)
                ])

                wizard.history_count = self.env['ha.entity.history'].search_count([
                    ('entity_id.ha_instance_id', '=', instance_id)
                ])

                wizard.area_count = self.env['ha.area'].search_count([
                    ('ha_instance_id', '=', instance_id)
                ])

                wizard.group_count = self.env['ha.entity.group'].search_count([
                    ('ha_instance_id', '=', instance_id)
                ])

                wizard.group_tag_count = self.env['ha.entity.group.tag'].search_count([
                    ('ha_instance_id', '=', instance_id)
                ])

                wizard.entity_tag_count = self.env['ha.entity.tag'].search_count([
                    ('ha_instance_id', '=', instance_id)
                ])

                wizard.device_count = self.env['ha.device'].search_count([
                    ('ha_instance_id', '=', instance_id)
                ])

                wizard.label_count = self.env['ha.label'].search_count([
                    ('ha_instance_id', '=', instance_id)
                ])

                wizard.queue_count = self.env['ha.ws.request.queue'].search_count([
                    ('ha_instance_id', '=', instance_id)
                ])
            else:
                wizard.entity_count = 0
                wizard.history_count = 0
                wizard.area_count = 0
                wizard.group_count = 0
                wizard.group_tag_count = 0
                wizard.entity_tag_count = 0
                wizard.device_count = 0
                wizard.label_count = 0
                wizard.queue_count = 0

    def action_confirm_clear(self):
        """
        確認清除：執行清除操作
        """
        self.ensure_one()

        if not self.instance_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Invalid instance ID'),
                    'type': 'danger',
                    'sticky': True,
                }
            }

        # 執行清除
        result = self.instance_id._clear_instance_data()

        if result.get('success'):
            deleted = result.get('deleted', {})
            total = sum(deleted.values())

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('✓ Data Cleared'),
                    'message': _("Successfully cleared all data for instance '%s'\n\n"
                               "Deletion Statistics:\n"
                               "• Entities: %d\n"
                               "• History: %d\n"
                               "• Areas: %d\n"
                               "• Devices: %d\n"
                               "• Labels: %d\n"
                               "• Groups: %d\n"
                               "• Group Tags: %d\n"
                               "• Entity Tags: %d\n"
                               "• Queue: %d\n"
                               "Total: %d records") % (
                                   self.instance_name,
                                   deleted.get('entities', 0),
                                   deleted.get('history', 0),
                                   deleted.get('areas', 0),
                                   deleted.get('devices', 0),
                                   deleted.get('labels', 0),
                                   deleted.get('groups', 0),
                                   deleted.get('group_tags', 0),
                                   deleted.get('entity_tags', 0),
                                   deleted.get('queue', 0),
                                   total
                               ),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            _logger.error("Failed to clear instance data: %s", error_msg)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('✗ Clear Failed'),
                    'message': _("An error occurred while clearing instance data: %s") % error_msg,
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def action_cancel(self):
        """
        取消清除：關閉對話框
        """
        return {'type': 'ir.actions.act_window_close'}
