# -*- coding: utf-8 -*-
"""
HA Instance Helper - 統一的實例選擇邏輯

此模組提供共享的實例獲取方法，避免在 Controller 和 Model 中重複代碼。
整合了以下特性：
- Session validation
- User preference support
- Bus notifications
- Comprehensive logging
- Ordered search
"""
import logging

_logger = logging.getLogger(__name__)


class HAInstanceHelper:
    """
    HA Instance 選擇邏輯的統一實現

    提供 3-level fallback mechanism:
    1. Session 中的 current_ha_instance_id
    2. User preference (res.users.current_ha_instance_id)
    3. 第一個可存取的活躍實例 (ordered by sequence, id, filtered by user permissions)
    """

    @staticmethod
    def get_current_instance(env, logger=None):
        """
        取得當前使用者的目標 HA 實例 ID

        優先順序：
        1. Session 中的 current_ha_instance_id（需要驗證有效性）
        2. 使用者偏好設定 (res.users.current_ha_instance_id)
        3. 第一個可存取的活躍實例（ordered by sequence, id, filtered by user permissions）

        Args:
            env: Odoo environment (self.env or request.env)
            logger: Optional logger instance (默認使用模組 logger)

        Returns:
            int: HA 實例 ID，如果找不到則返回 None
        """
        if logger is None:
            logger = _logger

        # 嘗試獲取 request（在 HTTP 請求上下文中可用）
        request = None
        try:
            from odoo.http import request as http_request
            request = http_request
        except (ImportError, RuntimeError):
            # 不在 HTTP 請求上下文中（例如：cron job, shell）
            pass

        session_instance_id = None

        # 1. 嘗試從 session 讀取（僅在 HTTP 請求上下文中）
        if request and hasattr(request, 'session'):
            session_instance_id = request.session.get('current_ha_instance_id')
            if session_instance_id:
                # 驗證該實例是否存在且活躍
                instance = env['ha.instance'].sudo().search([
                    ('id', '=', session_instance_id),
                    ('active', '=', True)
                ], limit=1)
                if instance:
                    logger.debug(f"Using instance from session: {instance.name} (ID: {instance.id})")
                    return instance.id
                else:
                    # Session 中的實例無效，清除並發送通知
                    logger.warning(f"Session instance ID {session_instance_id} is invalid, clearing session")
                    request.session.pop('current_ha_instance_id', None)

                    # 發送實例失效通知
                    try:
                        env['ha.realtime.update'].sudo().notify_instance_invalidated(
                            instance_id=session_instance_id,
                            reason='實例不存在或已停用'
                        )
                    except Exception as e:
                        logger.error(f"Failed to send instance_invalidated notification: {e}")

        # 2. 嘗試從使用者偏好設定讀取
        user_preference_id = None
        if hasattr(env.user, 'current_ha_instance_id') and env.user.current_ha_instance_id:
            user_preference_id = env.user.current_ha_instance_id.id
            # 驗證該實例是否存在且活躍
            instance = env['ha.instance'].sudo().search([
                ('id', '=', user_preference_id),
                ('active', '=', True)
            ], limit=1)
            if instance:
                # 如果有 session 失效，發送 fallback 通知
                if session_instance_id:
                    logger.info(f"Falling back to user preference: {instance.name}")
                    try:
                        env['ha.realtime.update'].sudo().notify_instance_fallback(
                            from_instance_id=session_instance_id,
                            to_instance_id=instance.id,
                            to_instance_name=instance.name,
                            fallback_type='user_preference'
                        )
                    except Exception as e:
                        logger.error(f"Failed to send instance_fallback notification: {e}")
                else:
                    logger.debug(f"Using instance from user preference: {instance.name} (ID: {instance.id})")

                return instance.id
            else:
                logger.warning(f"User preference instance ID {user_preference_id} is invalid")

        # 3. 使用第一個可存取的活躍實例（按 sequence, id 排序，考慮使用者權限）
        accessible_instances = env['ha.instance'].get_accessible_instances()
        first_instance = accessible_instances[:1] if accessible_instances else env['ha.instance'].browse()
        if first_instance:
            # 如果是從其他來源降級，發送 fallback 通知
            if session_instance_id or user_preference_id:
                from_id = session_instance_id or user_preference_id
                logger.info(f"Falling back to first accessible instance: {first_instance.name}")
                try:
                    env['ha.realtime.update'].sudo().notify_instance_fallback(
                        from_instance_id=from_id,
                        to_instance_id=first_instance.id,
                        to_instance_name=first_instance.name,
                        fallback_type='first_accessible'
                    )
                except Exception as e:
                    logger.error(f"Failed to send instance_fallback notification: {e}")
            else:
                logger.debug(f"Using first accessible instance: {first_instance.name} (ID: {first_instance.id})")

            return first_instance.id

        # 找不到任何實例
        logger.warning("No active HA instance found")
        return None
