# -*- coding: utf-8 -*-

from odoo import models, fields


class ResUsers(models.Model):
    """擴展 res.users 模型以支援多 HA 實例和細粒度權限控制"""

    _inherit = 'res.users'

    current_ha_instance_id = fields.Many2one(
        'ha.instance',
        string='Current HA Instance',
        help='用戶當前選擇的 Home Assistant 實例（用於 Search View 過濾）',
        ondelete='set null',
    )

    ha_entity_group_ids = fields.Many2many(
        'ha.entity.group',
        'ha_entity_group_user_rel',
        'user_id',
        'group_id',
        string='Authorized Entity Groups',
        help='Entity groups accessible by this user. Users can only view entities within their authorized groups.'
    )
