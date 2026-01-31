from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class HaRealtimeUpdate(models.Model):
    """
    Home Assistant 即時更新處理（使用 bus.listener.mixin 最佳實踐）
    廣播通知到所有登入用戶的前端
    """
    _name = 'ha.realtime.update'
    _description = 'Home Assistant Realtime Update Handler'
    _inherit = ['bus.listener.mixin']

    name = fields.Char(string='Name', default='HA Bus Notifier')

    def _bus_channel(self):
        """
        定義 bus channel - 返回當前用戶的 partner
        Odoo 會自動為每個登入用戶訂閱其 partner channel
        """
        return self.env.user.partner_id

    @api.model
    def _broadcast_to_users(self, notification_type, message):
        """
        廣播通知到所有在線用戶

        :param notification_type: 通知類型
        :param message: 通知內容
        """
        users = self.env['res.users'].search([('id', '!=', 1)])  # 排除 admin 超級用戶
        for user in users:
            try:
                # 切換到該用戶的環境來發送通知
                user.partner_id._bus_send(notification_type, message)
            except Exception as e:
                _logger.error(f"Failed to send notification to user {user.login}: {e}")

    @api.model
    def notify_entity_state_change(self, entity_id, old_state, new_state, ha_instance_id=None):
        """
        通知前端實體狀態變更

        :param entity_id: 實體 ID
        :param old_state: 舊狀態值
        :param new_state: 新狀態值
        :param ha_instance_id: HA 實例 ID (可選，用於多實例支援)
        """
        try:
            message = {
                'entity_id': entity_id,
                'old_state': old_state,
                'new_state': new_state,
                'timestamp': new_state.get('last_changed') if new_state else None,
                'ha_instance_id': ha_instance_id  # 新增：實例 ID
            }
            self._broadcast_to_users('ha_state_changed', message)
            _logger.debug(f"Broadcast state change: {entity_id} (instance: {ha_instance_id})")
        except Exception as e:
            _logger.error(f"Failed to broadcast state change: {e}")

    @api.model
    def notify_ha_websocket_status(self, status, message, ha_instance_id=None, instance_name=None):
        """
        通知前端 Home Assistant WebSocket 服務狀態

        :param status: 狀態 ('connected', 'disconnected', 'error', 'reconnecting')
        :param message: 狀態訊息
        :param ha_instance_id: HA 實例 ID (可選，用於多實例支援)
        :param instance_name: HA 實例名稱 (可選)
        """
        try:
            from datetime import datetime
            payload = {
                'status': status,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'ha_instance_id': ha_instance_id,  # 新增：實例 ID
                'instance_name': instance_name      # 新增：實例名稱
            }
            self._broadcast_to_users('ha_websocket_status', payload)
            instance_info = f" ({instance_name or ha_instance_id})" if ha_instance_id else ""
            _logger.info(f"Broadcast WebSocket status{instance_info}: {status} - {message}")
        except Exception as e:
            _logger.error(f"Failed to broadcast service status: {e}")

    @api.model
    def notify_instance_invalidated(self, instance_id, reason):
        """
        Phase 3.1: 通知前端實例失效

        當 session 中的實例失效時（不存在或未啟用），通知前端清除相關快取

        :param instance_id: 失效的實例 ID
        :param reason: 失效原因
        """
        try:
            from datetime import datetime
            payload = {
                'instance_id': instance_id,
                'reason': reason,
                'timestamp': datetime.now().isoformat(),
            }
            self._broadcast_to_users('instance_invalidated', payload)
            _logger.warning(f"Broadcast instance invalidated: ID {instance_id} - {reason}")
        except Exception as e:
            _logger.error(f"Failed to broadcast instance_invalidated: {e}")

    @api.model
    def notify_instance_fallback(self, from_instance_id, to_instance_id, to_instance_name, fallback_type):
        """
        Phase 3.1: 通知前端實例降級

        當系統從無效的實例降級到備用實例時，通知前端更新 UI

        :param from_instance_id: 原實例 ID（失效的）
        :param to_instance_id: 目標實例 ID（降級到的）
        :param to_instance_name: 目標實例名稱
        :param fallback_type: 降級類型 ('default', 'first_active')
        """
        try:
            from datetime import datetime
            payload = {
                'from_instance_id': from_instance_id,
                'to_instance_id': to_instance_id,
                'to_instance_name': to_instance_name,
                'fallback_type': fallback_type,
                'timestamp': datetime.now().isoformat(),
            }
            self._broadcast_to_users('instance_fallback', payload)
            _logger.warning(
                f"Broadcast instance fallback: {from_instance_id} -> {to_instance_name} "
                f"(ID: {to_instance_id}, type: {fallback_type})"
            )
        except Exception as e:
            _logger.error(f"Failed to broadcast instance_fallback: {e}")

    @api.model
    def notify_instance_switched(self, instance_id, instance_name, user_id=None):
        """
        Phase 3.3: 通知前端實例切換（多標籤頁同步）

        當使用者主動切換實例時，通知所有標籤頁更新到新實例

        :param instance_id: 新實例 ID
        :param instance_name: 新實例名稱
        :param user_id: 觸發切換的使用者 ID（可選，用於避免迴圈）
        """
        try:
            from datetime import datetime
            payload = {
                'instance_id': instance_id,
                'instance_name': instance_name,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
            }
            self._broadcast_to_users('instance_switched', payload)
            _logger.info(
                f"Broadcast instance switched: {instance_name} (ID: {instance_id})"
            )
        except Exception as e:
            _logger.error(f"Failed to broadcast instance_switched: {e}")

    @api.model
    def notify_device_registry_update(self, action, device_id, ha_instance_id=None):
        """
        通知前端設備註冊變更（用於 Glances 快取失效）

        當 Home Assistant 的設備註冊發生變更時，通知前端清除相關快取

        :param action: 變更動作 ('create', 'update', 'remove')
        :param device_id: 設備 ID
        :param ha_instance_id: HA 實例 ID
        """
        try:
            from datetime import datetime
            payload = {
                'action': action,
                'device_id': device_id,
                'ha_instance_id': ha_instance_id,
                'timestamp': datetime.now().isoformat(),
            }
            self._broadcast_to_users('ha_device_registry_updated', payload)
            _logger.info(
                f"Broadcast device registry update: {action} - {device_id} "
                f"(instance: {ha_instance_id})"
            )
        except Exception as e:
            _logger.error(f"Failed to broadcast device_registry_update: {e}")

    @api.model
    def notify_area_registry_update(self, action, area_id, ha_instance_id=None):
        """
        通知前端區域註冊變更（用於 Area Dashboard 快取失效）

        當 Home Assistant 的區域註冊發生變更時，通知前端清除相關快取

        :param action: 變更動作 ('create', 'update', 'remove')
        :param area_id: 區域 ID
        :param ha_instance_id: HA 實例 ID
        """
        try:
            from datetime import datetime
            payload = {
                'action': action,
                'area_id': area_id,
                'ha_instance_id': ha_instance_id,
                'timestamp': datetime.now().isoformat(),
            }
            self._broadcast_to_users('ha_area_registry_updated', payload)
            _logger.info(
                f"Broadcast area registry update: {action} - {area_id} "
                f"(instance: {ha_instance_id})"
            )
        except Exception as e:
            _logger.error(f"Failed to broadcast area_registry_update: {e}")