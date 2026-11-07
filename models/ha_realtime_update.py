from odoo import models, api, fields, SUPERUSER_ID
from odoo.osv import expression
from odoo.addons.odoo_ha_addon.models.common.attribute_policy import sanitize_state
import logging

_logger = logging.getLogger(__name__)


class HaRealtimeUpdate(models.Model):
    """
    Home Assistant 即時更新處理（使用 bus.listener.mixin 最佳實踐）
    只把通知送給有權限的使用者（manager、entity group 成員、未過期分享對象）
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

    # ------------------------------------------------------------------
    # Recipient resolution (security: only authorised users get payloads)
    # ------------------------------------------------------------------

    @api.model
    def _ha_users_in_groups(self, *xmlids):
        """Return active users belonging to any of the given res.groups xmlids."""
        group_ids = []
        for xmlid in xmlids:
            group = self.env.ref(xmlid, raise_if_not_found=False)
            if group:
                group_ids.append(group.id)
        if not group_ids:
            return self.env['res.users'].sudo().browse()
        return self.env['res.users'].sudo().search([('groups_id', 'in', group_ids)])

    @api.model
    def _ha_users_from_entity_groups(self, entity_groups):
        """
        Users authorised through ha.entity.group membership, as a pair
        ``(members, public_users)``:

        - ``members``: users listed in ``user_ids`` of the groups who still
          belong to group_ha_user (the ha.entity record rules only apply to
          that group).  They can read the entities through the ORM
          (``user.ha_entity_group_ids``), so they get full payloads;
        - ``public_users``: when one of the groups has no ``user_ids``
          ("public" group), every other group_ha_user member.  The ORM record
          rules only follow explicit membership, so these users cannot read
          the entity records; they receive the sanitized (restricted)
          payload instead of the full HA state.
        """
        users = self.env['res.users'].sudo().browse()
        if not entity_groups:
            return users, users
        ha_users = self._ha_users_in_groups('odoo_ha_addon.group_ha_user')
        members = entity_groups.mapped('user_ids') & ha_users
        public_users = users
        if any(not group.user_ids for group in entity_groups):
            public_users = ha_users - members
        return members, public_users

    @api.model
    def _ha_users_from_shares(self, share_domain):
        shares = self.env['ha.entity.share'].sudo().search(
            [('is_expired', '=', False)] + share_domain
        )
        return shares.mapped('user_id')

    @api.model
    def _get_entity_recipient_sets(self, entity_id, ha_instance_id=None):
        """
        Users allowed to receive realtime payloads about one HA entity, split
        in two sets:

        - ``full``: group_ha_manager members and explicit members (user_ids)
          of active ha.entity.group(s) containing the entity; they see the
          entity through the ORM anyway;
        - ``restricted``: other users holding a non-expired ha.entity.share on
          the entity, on a group containing it, or on its device, plus the
          group_ha_user members reached only through a public group (no
          user_ids); they get the same sanitized attributes as the portal
          API.
        """
        full = self._ha_users_in_groups('odoo_ha_addon.group_ha_manager')
        restricted = self.env['res.users'].sudo().browse()
        Entity = self.env['ha.entity'].sudo().with_context(active_test=False)
        domain = [('entity_id', '=', entity_id)]
        if ha_instance_id:
            domain.append(('ha_instance_id', '=', ha_instance_id))
        entities = Entity.search(domain)
        if not entities:
            return full, restricted

        groups = self.env['ha.entity.group'].sudo().search([
            ('entity_ids', 'in', entities.ids),
        ])
        members, public_users = self._ha_users_from_entity_groups(groups)
        full |= members

        share_domains = [[('entity_id', 'in', entities.ids)]]
        if groups:
            share_domains.append([('group_id', 'in', groups.ids)])
        devices = entities.mapped('device_id')
        if devices:
            share_domains.append([('device_id', 'in', devices.ids)])
        restricted = (self._ha_users_from_shares(expression.OR(share_domains)) | public_users) - full
        return full, restricted

    @api.model
    def _get_entity_recipients(self, entity_id, ha_instance_id=None):
        """All users allowed to receive realtime payloads about one entity."""
        full, restricted = self._get_entity_recipient_sets(entity_id, ha_instance_id)
        return full | restricted

    @api.model
    def _get_instance_recipient_sets(self, ha_instance_id=None):
        """(full, restricted) recipients of instance-level notifications."""
        full = self._ha_users_in_groups('odoo_ha_addon.group_ha_manager')
        restricted = self.env['res.users'].sudo().browse()
        if not ha_instance_id:
            return full, restricted
        groups = self.env['ha.entity.group'].sudo().search([
            ('ha_instance_id', '=', ha_instance_id),
        ])
        members, public_users = self._ha_users_from_entity_groups(groups)
        full |= members
        restricted = (self._ha_users_from_shares(
            [('ha_instance_id', '=', ha_instance_id)]) | public_users) - full
        return full, restricted

    @api.model
    def _get_instance_recipients(self, ha_instance_id=None):
        """
        Users allowed to receive instance-level notifications (connection
        status, device/area registry changes): managers, users of entity
        groups on that instance (public group => all HA Users) and users with
        a non-expired share on that instance.
        """
        full, restricted = self._get_instance_recipient_sets(ha_instance_id)
        return full | restricted

    @api.model
    def _send_to_users(self, users, notification_type, message):
        """Send a bus notification to the partner channel of each given user."""
        users = users.sudo().filtered(lambda u: u.active and u.id != SUPERUSER_ID)
        for user in users:
            try:
                user.partner_id._bus_send(notification_type, message)
            except Exception as e:
                _logger.error("Failed to send %s notification to user %s: %s",
                              notification_type, user.id, e)
        return users

    @api.model
    def _current_request_user(self):
        """The user that triggered the current call (sudo keeps the uid)."""
        return self.env['res.users'].sudo().browse(self.env.uid)

    @api.model
    def _notify_entity_state_change(self, entity_id, old_state, new_state, ha_instance_id=None):
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
            full, restricted = self._get_entity_recipient_sets(entity_id, ha_instance_id)
            self._send_to_users(full, 'ha_state_changed', message)
            if restricted:
                # Share-only recipients get the same attribute policy as the
                # portal API (no tokens, credentials or GPS coordinates).
                self._send_to_users(restricted, 'ha_state_changed', dict(
                    message,
                    old_state=sanitize_state(old_state),
                    new_state=sanitize_state(new_state),
                ))
            _logger.debug(f"Broadcast state change: {entity_id} (instance: {ha_instance_id})")
        except Exception as e:
            _logger.error(f"Failed to broadcast state change: {e}")

    @api.model
    def _notify_ha_websocket_status(self, status, message, ha_instance_id=None, instance_name=None):
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
            full, restricted = self._get_instance_recipient_sets(ha_instance_id)
            self._send_to_users(full, 'ha_websocket_status', payload)
            if restricted:
                # Share-only recipients only need the connection status, not
                # the internal message / instance name.
                self._send_to_users(restricted, 'ha_websocket_status', {
                    'status': status,
                    'timestamp': payload['timestamp'],
                    'ha_instance_id': ha_instance_id,
                })
            instance_info = f" ({instance_name or ha_instance_id})" if ha_instance_id else ""
            _logger.info(f"Broadcast WebSocket status{instance_info}: {status} - {message}")
        except Exception as e:
            _logger.error(f"Failed to broadcast service status: {e}")

    @api.model
    def _notify_instance_invalidated(self, instance_id, reason):
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
            # Only the user whose session referenced the instance needs this
            self._send_to_users(self._current_request_user(), 'instance_invalidated', payload)
            _logger.warning(f"Broadcast instance invalidated: ID {instance_id} - {reason}")
        except Exception as e:
            _logger.error(f"Failed to broadcast instance_invalidated: {e}")

    @api.model
    def _notify_instance_fallback(self, from_instance_id, to_instance_id, to_instance_name, fallback_type):
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
            self._send_to_users(self._current_request_user(), 'instance_fallback', payload)
            _logger.warning(
                f"Broadcast instance fallback: {from_instance_id} -> {to_instance_name} "
                f"(ID: {to_instance_id}, type: {fallback_type})"
            )
        except Exception as e:
            _logger.error(f"Failed to broadcast instance_fallback: {e}")

    @api.model
    def _notify_instance_switched(self, instance_id, instance_name, user_id=None):
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
            # Multi-tab sync of the switching user only
            target = self.env['res.users'].sudo().browse(user_id) if user_id else self._current_request_user()
            self._send_to_users(target, 'instance_switched', payload)
            _logger.info(
                f"Broadcast instance switched: {instance_name} (ID: {instance_id})"
            )
        except Exception as e:
            _logger.error(f"Failed to broadcast instance_switched: {e}")

    @api.model
    def _notify_device_registry_update(self, action, device_id, ha_instance_id=None):
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
            self._send_to_users(
                self._get_instance_recipients(ha_instance_id),
                'ha_device_registry_updated', payload)
            _logger.info(
                f"Broadcast device registry update: {action} - {device_id} "
                f"(instance: {ha_instance_id})"
            )
        except Exception as e:
            _logger.error(f"Failed to broadcast device_registry_update: {e}")

    @api.model
    def _notify_area_registry_update(self, action, area_id, ha_instance_id=None):
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
            self._send_to_users(
                self._get_instance_recipients(ha_instance_id),
                'ha_area_registry_updated', payload)
            _logger.info(
                f"Broadcast area registry update: {action} - {area_id} "
                f"(instance: {ha_instance_id})"
            )
        except Exception as e:
            _logger.error(f"Failed to broadcast area_registry_update: {e}")