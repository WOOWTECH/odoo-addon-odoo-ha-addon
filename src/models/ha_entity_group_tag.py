# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

class HAEntityGroupTag(models.Model):
    _logger = logging.getLogger(__name__)
    _name = 'ha.entity.group.tag'
    _inherit = ['ha.current.instance.filter.mixin']
    _description = 'Home Assistant Entity Group Tag'
    _order = 'sequence, name'

    ha_instance_id = fields.Many2one(
        'ha.instance',
        string='HA Instance',
        required=True,
        index=True,
        ondelete='cascade',
        help='The Home Assistant instance this tag belongs to'
    )
    name = fields.Char(string='Tag Name', required=True, index=True)
    color = fields.Integer(string='Color', default=0)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    # Many2many relationship with ha.entity.group
    group_ids = fields.Many2many(
        'ha.entity.group',
        'ha_entity_group_tag_rel',  # 關聯表名稱
        'tag_id',                    # 此 model 的 ID 欄位
        'group_id',                  # ha.entity.group 的 ID 欄位
        string='Groups',
        help='Entity groups with this tag'
    )

    # Computed field: group count
    group_count = fields.Integer(
        string='Group Count',
        compute='_compute_group_count',
        store=True
    )

    @api.depends('group_ids')
    def _compute_group_count(self):
        """計算此標籤關聯的群組數量"""
        for tag in self:
            tag.group_count = len(tag.group_ids)

    @api.constrains('name', 'ha_instance_id')
    def _check_name_unique(self):
        """確保同一 HA 實例內標籤名稱唯一"""
        for tag in self:
            if self.search_count([
                ('name', '=', tag.name),
                ('ha_instance_id', '=', tag.ha_instance_id.id),
                ('id', '!=', tag.id)
            ]) > 0:
                raise ValidationError(_('Tag name "%s" already exists in this instance, please use a different name') % tag.name)

    @api.constrains('ha_instance_id', 'group_ids')
    def _check_instance_consistency(self):
        """
        確保標籤關聯的所有群組都屬於同一個 HA 實例
        這是資料完整性的關鍵約束
        """
        for tag in self:
            if tag.group_ids:
                mismatched_groups = tag.group_ids.filtered(
                    lambda g: g.ha_instance_id.id != tag.ha_instance_id.id
                )
                if mismatched_groups:
                    group_names = ', '.join(mismatched_groups.mapped('name')[:3])
                    if len(mismatched_groups) > 3:
                        group_names += _(' (and %d more)') % (len(mismatched_groups) - 3)
                    raise ValidationError(
                        _('Tag "%s" belongs to instance "%s",\n'
                          'but the following groups belong to different instances: %s\n'
                          'A tag can only be associated with groups from the same instance.') % (
                              tag.name,
                              tag.ha_instance_id.name,
                              group_names
                          )
                    )

    def action_view_groups(self):
        """開啟此標籤關聯的群組列表"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'odoo_ha_addon.ha_entity_group_tag_view_groups_action'
        )
        action['name'] = f'{self.name} - Groups'
        action['domain'] = [('id', 'in', self.group_ids.ids)]
        action['context'] = {'default_tag_ids': [(4, self.id)]}
        return action
