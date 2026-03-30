# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

class HAEntityTag(models.Model):
    _logger = logging.getLogger(__name__)
    _name = 'ha.entity.tag'
    _inherit = ['ha.current.instance.filter.mixin']
    _description = 'Home Assistant Entity Tag'
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

    # Many2many relationship with ha.entity
    entity_ids = fields.Many2many(
        'ha.entity',
        'ha_entity_tag_rel',  # 關聯表名稱
        'tag_id',             # 此 model 的 ID 欄位
        'entity_id',          # ha.entity 的 ID 欄位
        string='Entities',
        help='Entities with this tag'
    )

    # Computed field: entity count
    entity_count = fields.Integer(
        string='Entity Count',
        compute='_compute_entity_count',
        store=True
    )

    @api.depends('entity_ids')
    def _compute_entity_count(self):
        """計算此標籤關聯的實體數量"""
        for tag in self:
            tag.entity_count = len(tag.entity_ids)

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

    @api.constrains('ha_instance_id', 'entity_ids')
    def _check_instance_consistency(self):
        """
        確保標籤關聯的所有實體都屬於同一個 HA 實例
        這是資料完整性的關鍵約束
        """
        for tag in self:
            if tag.entity_ids:
                mismatched_entities = tag.entity_ids.filtered(
                    lambda e: e.ha_instance_id.id != tag.ha_instance_id.id
                )
                if mismatched_entities:
                    entity_names = ', '.join(mismatched_entities.mapped('name')[:3])
                    if len(mismatched_entities) > 3:
                        entity_names += _(' (and %d more)') % (len(mismatched_entities) - 3)
                    raise ValidationError(
                        _('Tag "%s" belongs to instance "%s",\n'
                          'but the following entities belong to different instances: %s\n'
                          'A tag can only be associated with entities from the same instance.') % (
                              tag.name,
                              tag.ha_instance_id.name,
                              entity_names
                          )
                    )

    def action_view_entities(self):
        """開啟此標籤關聯的實體列表"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'odoo_ha_addon.ha_entity_tag_view_entities_action'
        )
        action['name'] = f'{self.name} - Entities'
        action['domain'] = [('id', 'in', self.entity_ids.ids)]
        action['context'] = {'default_tag_ids': [(4, self.id)]}
        return action
