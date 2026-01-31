# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ==================== HA Instance 選擇器 ====================

    def _default_ha_instance(self):
        """預設選擇最近修改的 HA Instance"""
        active_model = self.env.context.get('active_model', '')
        if active_model == 'ha.instance':
            return self.env.context.get('active_id')
        return self.env['ha.instance'].search(
            [('active', '=', True)],
            order='write_date desc',
            limit=1
        )

    ha_instance_id = fields.Many2one(
        'ha.instance',
        string="Home Assistant Instance",
        default=lambda self: self._default_ha_instance()
    )

    # ==================== HA Instance 欄位映射 ====================
    # 使用 ha_ 前綴對應到 ha.instance 的欄位
    # 使用 related 欄位 + readonly=False 模式（res.config.settings 標準做法）

    ha_name = fields.Char(
        string='Instance Name',
        related='ha_instance_id.name',
        readonly=False
    )
    ha_sequence = fields.Integer(
        string='Sequence',
        related='ha_instance_id.sequence',
        readonly=False
    )
    ha_api_url = fields.Char(
        string='API URL',
        related='ha_instance_id.api_url',
        readonly=False
    )
    ha_api_token = fields.Char(
        string='Access Token',
        related='ha_instance_id.api_token',
        readonly=False
    )
    ha_active = fields.Boolean(
        string='Active',
        related='ha_instance_id.active',
        readonly=False
    )
    ha_description = fields.Text(
        string='Description',
        related='ha_instance_id.description',
        readonly=False
    )

    # ==================== 唯讀資訊欄位 ====================
    # 使用 related 欄位自動從 ha.instance 讀取，避免 _onchange 觸發昂貴的計算

    ha_ws_url = fields.Char(
        related='ha_instance_id.ws_url',
        string='WebSocket URL',
        readonly=True
    )
    ha_entity_count = fields.Integer(
        related='ha_instance_id.entity_count',
        string='Entity Count',
        readonly=True
    )
    ha_websocket_status = fields.Selection(
        related='ha_instance_id.websocket_status',
        string='WebSocket Status',
        readonly=True
    )
    ha_last_sync_date = fields.Datetime(
        related='ha_instance_id.last_sync_date',
        string='Last Sync',
        readonly=True
    )

    # ==================== 全域設定 ====================

    ha_ws_heartbeat_interval = fields.Integer(
        string='WebSocket Heartbeat Interval (seconds)',
        config_parameter='odoo_ha_addon.ha_ws_heartbeat_interval',
        default=10,
        help='WebSocket service heartbeat update interval. Recommended to set below 15 seconds.'
    )

    ha_history_sync_max_workers = fields.Integer(
        string='History Sync Max Workers',
        config_parameter='odoo_ha_addon.ha_history_sync_max_workers',
        default=5,
        help='Maximum number of parallel workers for history sync. Higher values may improve speed but increase system load.'
    )

    # ==================== 注意 ====================
    # 使用 related 欄位 + readonly=False 後，Odoo 會自動處理欄位的讀取和寫入
    # 不需要額外的 compute, inverse, create, write 方法

    # ==================== 動作方法 ====================

    def action_ha_instance_create_new(self):
        """建立新的 HA Instance"""
        # 使用簡化的 modal form view (view_ha_instance_form_modal)
        view_id = self.env.ref('odoo_ha_addon.view_ha_instance_form_modal').id
        return {
            'name': 'New Home Assistant Instance',
            'view_mode': 'form',
            'res_model': 'ha.instance',
            'views': [(view_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'ha_instance_open_modal': True,
                'ha_instance_create_mode': True,
                'form_view_initial_mode': 'edit',
            },
        }

    def action_test_connection(self):
        """測試連接"""
        self.ensure_one()
        if not self.ha_instance_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Instance Selected',
                    'message': 'Please select a Home Assistant instance first.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # 直接呼叫 ha.instance 的 action_test_connection 方法
        # 該方法已經包含了完整的錯誤處理和通知邏輯
        return self.ha_instance_id.action_test_connection()

    def action_sync_entities(self):
        """同步實體"""
        self.ensure_one()
        if not self.ha_instance_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Instance Selected',
                    'message': 'Please select a Home Assistant instance first.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # 直接呼叫 ha.instance 的 action_sync_entities 方法
        # 該方法已經包含了完整的錯誤處理和通知邏輯
        return self.ha_instance_id.action_sync_entities()

    def action_restart_websocket(self):
        """重啟 WebSocket 服務"""
        self.ensure_one()
        if not self.ha_instance_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Instance Selected',
                    'message': 'Please select a Home Assistant instance first.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # 直接呼叫 ha.instance 的 action_restart_websocket 方法
        # 該方法已經包含了完整的錯誤處理和通知邏輯
        return self.ha_instance_id.action_restart_websocket()

    # ==================== Constraints ====================

    @api.constrains('ha_name', 'ha_api_url', 'ha_api_token')
    def _check_required_fields(self):
        """驗證必填欄位（Python 層級驗證，防止 API 繞過前端驗證）"""
        for record in self:
            if record.ha_instance_id:
                if not record.ha_name:
                    raise ValidationError('Instance name is required')
                if not record.ha_api_url:
                    raise ValidationError('API URL is required')
                if not record.ha_api_token:
                    raise ValidationError('Access token is required')

    @api.constrains('ha_ws_heartbeat_interval')
    def _check_heartbeat_interval(self):
        for record in self:
            if record.ha_ws_heartbeat_interval and (record.ha_ws_heartbeat_interval < 1 or record.ha_ws_heartbeat_interval > 60):
                raise ValidationError('WebSocket heartbeat interval must be between 1 and 60 seconds.')
