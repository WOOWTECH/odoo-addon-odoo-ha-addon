# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class HAEntityGroup(models.Model):
    _name = 'ha.entity.group'
    _inherit = ['ha.current.instance.filter.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Home Assistant Entity Group'
    _order = 'sequence, name'

    ha_instance_id = fields.Many2one(
        'ha.instance',
        string='HA Instance',
        required=True,
        index=True,
        ondelete='cascade',
        help='The Home Assistant instance this group belongs to'
    )
    name = fields.Char(string='Group Name', required=True, index=True)
    color = fields.Integer(string='Color', default=0)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    # Many2many relationship with ha.entity
    entity_ids = fields.Many2many(
        'ha.entity',
        'ha_entity_group_entity_rel',  # 關聯表名稱
        'group_id',                     # 此 model 的 ID 欄位
        'entity_id',                    # ha.entity 的 ID 欄位
        string='Entities',
        help='Home Assistant entities in this group',
        tracking=True
    )

    # One2many relationship with ha.entity.share
    share_ids = fields.One2many(
        'ha.entity.share',
        'group_id',
        string='Shares',
        help='Share records for this entity group',
        groups='odoo_ha_addon.group_ha_manager'
    )

    # Many2many relationship with ha.entity.group.tag
    tag_ids = fields.Many2many(
        'ha.entity.group.tag',
        'ha_entity_group_tag_rel',  # 關聯表名稱
        'group_id',                  # 此 model 的 ID 欄位
        'tag_id',                    # ha.entity.group.tag 的 ID 欄位
        string='Tags',
        help='Tags for this entity group',
        tracking=True
    )

    # Many2many relationship with res.users (NEW: 細粒度權限控制)
    user_ids = fields.Many2many(
        'res.users',
        'ha_entity_group_user_rel',  # 關聯表名稱
        'group_id',                   # 此 model 的 ID 欄位
        'user_id',                    # res.users 的 ID 欄位
        string='Authorized Users',
        help='Users who can access this entity group and its entities. '
             'Leave empty to make this group public (accessible by all users with instance access).',
        tracking=True
    )

    # Computed field: entity count
    entity_count = fields.Integer(
        string='Entity Count',
        compute='_compute_entity_count',
        store=True
    )

    # Computed field: tag count
    tag_count = fields.Integer(
        string='Tag Count',
        compute='_compute_tag_count',
        store=True
    )

    # Text field for user notes
    note = fields.Text(
        string='Note',
        groups='odoo_ha_addon.group_ha_user',
        help='Internal notes for this group'
    )

    # Custom properties - definition is stored in ha.instance
    properties = fields.Properties(
        'Properties',
        definition='ha_instance_id.group_properties_definition',
        copy=True,
        help='Custom properties for this group (defined at instance level)'
    )

    # ========================================
    # Computed Fields
    # ========================================

    @api.depends('entity_ids')
    def _compute_entity_count(self):
        """計算群組中的實體數量"""
        for group in self:
            group.entity_count = len(group.entity_ids)

    @api.depends('tag_ids')
    def _compute_tag_count(self):
        """計算群組的標籤數量"""
        for group in self:
            group.tag_count = len(group.tag_ids)

    @api.constrains('name')
    def _check_name_unique(self):
        """確保群組名稱唯一"""
        for group in self:
            if self.search_count([('name', '=', group.name), ('id', '!=', group.id)]) > 0:
                raise ValidationError(_('Group name "%s" already exists, please use a different name') % group.name)

    @api.constrains('ha_instance_id', 'entity_ids', 'tag_ids')
    def _check_instance_consistency(self):
        """
        確保群組的實體和標籤都屬於同一個 HA 實例
        這是資料完整性的關鍵約束
        """
        for group in self:
            # 檢查所有實體是否屬於同一實例
            if group.entity_ids:
                mismatched_entities = group.entity_ids.filtered(
                    lambda e: e.ha_instance_id.id != group.ha_instance_id.id
                )
                if mismatched_entities:
                    entity_names = ', '.join(mismatched_entities.mapped('name')[:3])
                    if len(mismatched_entities) > 3:
                        entity_names += _(' (and %d more)') % (len(mismatched_entities) - 3)
                    raise ValidationError(
                        _('Group "%s" belongs to instance "%s",\n'
                          'but the following entities belong to different instances: %s\n'
                          'All entities in a group must belong to the same instance.') % (
                              group.name,
                              group.ha_instance_id.name,
                              entity_names
                          )
                    )

            # 檢查所有標籤是否屬於同一實例
            if group.tag_ids:
                mismatched_tags = group.tag_ids.filtered(
                    lambda t: t.ha_instance_id.id != group.ha_instance_id.id
                )
                if mismatched_tags:
                    tag_names = ', '.join(mismatched_tags.mapped('name')[:3])
                    if len(mismatched_tags) > 3:
                        tag_names += _(' (and %d more)') % (len(mismatched_tags) - 3)
                    raise ValidationError(
                        _('Group "%s" belongs to instance "%s",\n'
                          'but the following tags belong to different instances: %s\n'
                          'All tags in a group must belong to the same instance.') % (
                              group.name,
                              group.ha_instance_id.name,
                              tag_names
                          )
                    )

    def _compute_access_url(self):
        """Compute the portal access URL for each entity group."""
        for record in self:
            record.access_url = f'/portal/entity_group/{record.id}'

    def action_view_entities(self):
        """開啟群組中的實體列表"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'odoo_ha_addon.ha_entity_group_view_entities_action'
        )
        action['name'] = f'{self.name} - Entities'
        action['domain'] = [('id', 'in', self.entity_ids.ids)]
        action['context'] = {'default_group_ids': [(4, self.id)]}
        return action

    def action_view_tags(self):
        """開啟群組的標籤列表"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'odoo_ha_addon.ha_entity_group_view_tags_action'
        )
        action['name'] = f'{self.name} - Tags'
        action['domain'] = [('id', 'in', self.tag_ids.ids)]
        action['context'] = {'default_group_ids': [(4, self.id)]}
        return action

    def action_share(self):
        """
        Open the entity group share wizard to share this group with specific users.

        This opens a wizard that allows selecting users and setting permissions
        for user-based sharing (not portal token-based).
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Share Entity Group'),
            'res_model': 'ha.entity.share.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_group_id': self.id,
            },
        }

