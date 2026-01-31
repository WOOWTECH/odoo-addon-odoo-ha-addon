from collections import defaultdict

from odoo import http, _
from odoo.http import request
import logging
import time
from psycopg2 import errors as psycopg2_errors
from odoo.addons.odoo_ha_addon.models.common.instance_helper import HAInstanceHelper

_logger = logging.getLogger(__name__)


class AwesomeDashboard(http.Controller):

    def _get_current_instance(self):
        """
        Phase 3 & 3.1: 取得當前使用者的目標 HA 實例 ID

        使用 HAInstanceHelper 統一實現 (重構後)，支持：
        - Session validation (Phase 3.1: 失效自動清除 + Bus notification)
        - User preference support (res.users.current_ha_instance_id)
        - Bus notifications (失效 + fallback 通知)
        - Comprehensive logging (DEBUG/INFO/WARNING/ERROR)
        - Ordered search (sequence, id)

        3-level fallback 優先順序：
        1. Session 中的 current_ha_instance_id（驗證存在且活躍）
        2. 使用者偏好設定 (res.users.current_ha_instance_id)
        3. 第一個可存取的活躍實例（ordered by sequence, id, filtered by user permissions）

        實現位置：models/common/instance_helper.py::HAInstanceHelper
        重構文檔：docs/tech/instance-helper-refactoring.md

        Returns:
            int: HA 實例 ID，如果找不到則返回 None
        """
        return HAInstanceHelper.get_current_instance(request.env, logger=_logger)

    def _validate_instance(self, instance_id):
        """
        Phase 2.2: 驗證 HA 實例的有效性

        驗證項目：
        1. 實例是否存在（並且用戶有權限訪問，透過 ir.rule）
        2. 實例是否活躍（active=True）
        3. 實例是否已配置（有 API URL 和 token）

        ⚠️ Permission Check:
        - 移除 .sudo() 以尊重 ir.rule 權限控制
        - HA User 只能驗證他們有權限的實例（透過 entity groups）
        - HA Manager 可以驗證所有實例

        Args:
            instance_id (int): 要驗證的實例 ID

        Returns:
            dict: 驗證結果
                {
                    'valid': bool,          # 是否有效
                    'error_type': str,      # 錯誤類型（如果 valid=False）
                    'error_message': str,   # 錯誤訊息（如果 valid=False）
                    'instance': recordset   # 實例記錄（如果 valid=True）
                }

        Error Types:
            - 'instance_not_found': 實例不存在或用戶無權訪問
            - 'instance_inactive': 實例未啟用
            - 'instance_not_configured': 實例未配置完整（缺少 API URL 或 token）
        """
        if not instance_id:
            return {
                'valid': False,
                'error_type': 'instance_not_found',
                'error_message': _('Instance ID not specified')
            }

        # 檢查實例是否存在（ir.rule 會自動檢查權限）
        # 移除 .sudo() 以確保只能訪問授權的實例
        instance = request.env['ha.instance'].search([
            ('id', '=', instance_id)
        ], limit=1)

        if not instance:
            _logger.warning(f"Instance ID {instance_id} not found")
            return {
                'valid': False,
                'error_type': 'instance_not_found',
                'error_message': _('Instance not found (ID: %s)') % instance_id
            }

        # 檢查實例是否活躍
        if not instance.active:
            _logger.warning(f"Instance {instance.name} (ID: {instance_id}) is inactive")
            return {
                'valid': False,
                'error_type': 'instance_inactive',
                'error_message': _('Instance "%s" is inactive') % instance.name
            }

        # 檢查實例是否已配置（有 API URL 和 token）
        if not instance.api_url or not instance.api_token:
            missing_fields = []
            if not instance.api_url:
                missing_fields.append('API URL')
            if not instance.api_token:
                missing_fields.append('API Token')

            missing = ', '.join(missing_fields)
            _logger.warning(f"Instance {instance.name} (ID: {instance_id}) missing configuration: {missing}")
            return {
                'valid': False,
                'error_type': 'instance_not_configured',
                'error_message': _('Instance "%s" is not fully configured (missing: %s)') % (instance.name, missing)
            }

        # 驗證通過
        _logger.debug(f"Instance {instance.name} (ID: {instance_id}) validation passed")
        return {
            'valid': True,
            'instance': instance
        }

    def _call_websocket_api(self, message_type, payload, timeout=15, instance_id=None):
        """
        通用 WebSocket API 呼叫函數
        現在使用共用的 WebSocketClient 服務
        保證返回標準化的響應格式

        Phase 2.2: 加入實例驗證機制

        Args:
            message_type: WebSocket 訊息類型（如 'supervisor/api', 'call_service' 等）
            payload: 請求的 payload（dict 格式，會自動轉為 JSON）
            timeout: 超時時間（秒），預設 15 秒
            instance_id: HA 實例 ID（Phase 3），如果為 None 則使用 _get_current_instance()

        Returns:
            dict: 保證格式 {'success': bool, 'data': dict, 'error': str, 'error_type': str (optional)}
        """
        _logger.debug(f"=== Controller WebSocket API call: {message_type} ===")
        _logger.debug(f"Payload: {payload}")
        _logger.debug(f"Timeout: {timeout}s")
        _logger.debug(f"Instance ID: {instance_id}")

        from odoo.addons.odoo_ha_addon.models.common.websocket_client import get_websocket_client

        if not request.env:
            _logger.debug("Request environment not available")
            return {
                'success': False,
                'error': 'Request environment not available',
                'error_type': 'system_error'
            }

        # Phase 3: 如果沒指定實例 ID，使用當前實例
        if instance_id is None:
            instance_id = self._get_current_instance()
            if instance_id is None:
                return {
                    'success': False,
                    'error': _('No HA instance available'),
                    'error_type': 'no_instance'
                }

        # Phase 2.2: 驗證實例有效性
        validation = self._validate_instance(instance_id)
        if not validation['valid']:
            return {
                'success': False,
                'error': validation['error_message'],
                'error_type': validation['error_type']
            }

        _logger.debug("Request environment available, creating WebSocket client...")
        _logger.debug(f"User ID: {request.env.user.id}")
        _logger.debug(f"Database: {request.env.cr.dbname}")
        _logger.debug(f"Using HA instance ID: {instance_id}")

        try:
            client = get_websocket_client(request.env, instance_id=instance_id)
            _logger.debug("WebSocket client created, making API call...")

            result = client.call_websocket_api(message_type, payload, timeout)

            # 驗證並標準化返回格式
            if not isinstance(result, dict):
                _logger.error(f"WebSocket client returned invalid format: {type(result)}")
                return {
                    'success': False,
                    'error': 'Invalid response format from WebSocket client'
                }

            # 確保有 success 欄位
            if 'success' not in result:
                _logger.warning("WebSocket client response missing 'success' field")
                return {
                    'success': False,
                    'error': 'Invalid response structure'
                }

            # 確保失敗時有 error 欄位
            if not result.get('success') and 'error' not in result:
                result['error'] = 'Unknown error'

            # 確保成功時有 data 欄位
            if result.get('success') and 'data' not in result:
                result['data'] = {}

            _logger.debug(f"Controller WebSocket call result: success={result.get('success')}")
            if not result.get('success'):
                _logger.debug(f"Error: {result.get('error')}")
            else:
                data_size = len(str(result.get('data', '')))
                _logger.debug(f"Response data size: {data_size} chars")

            return result

        except Exception as e:
            _logger.error(f"Controller WebSocket API call failed: {e}")
            _logger.debug(f"Exception details: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _standardize_response(self, result):
        """
        標準化 API 響應格式
        確保所有響應都遵循統一的格式規範

        Args:
            result: 原始響應（通常來自 WebSocket client 或其他服務）

        Returns:
            dict: 標準格式 {'success': bool, 'data': dict, 'error': str}
        """
        if not isinstance(result, dict):
            _logger.warning(f"Standardizing non-dict response: {type(result)}")
            return {
                'success': False,
                'error': 'Invalid response format'
            }

        success = result.get('success', False)

        if success:
            return {
                'success': True,
                'data': result.get('data', {})
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error')
            }

    @http.route('/odoo_ha_addon/hardware_info', type='json', auth='user')
    def get_hardware_info(self, ha_instance_id=None):
        """
        透過 WebSocket 取得 Home Assistant 硬體資訊

        ⚠️ Instance Selection:
        - 如果提供 ha_instance_id：使用指定的實例
        - 如果為 None：自動使用 session 的 current_ha_instance_id
        - 降級順序：session → 預設實例 → 第一個活躍實例

        Args:
            ha_instance_id (int, optional): HA 實例 ID。預設為 None（使用 session 實例）

        Returns:
            dict: 標準化響應格式
                {
                    'success': bool,
                    'data': {
                        'data': {...}  # Home Assistant 硬體資訊
                    },
                    'error': str  # 僅在 success=False 時存在
                }

        Raises:
            無 - 所有錯誤都轉為 success=False 返回

        Example:
            # 使用 session 實例（推薦）
            result = self.get_hardware_info()

            # 指定實例
            result = self.get_hardware_info(ha_instance_id=2)
        """
        result = self._call_websocket_api(
            message_type='supervisor/api',
            payload={
                'endpoint': '/hardware/info',
                'method': 'get'
            },
            instance_id=ha_instance_id
        )
        return self._standardize_response(result)

    @http.route('/odoo_ha_addon/network_info', type='json', auth='user')
    def get_network_info(self, ha_instance_id=None):
        """
        透過 WebSocket 取得 Home Assistant 網路資訊

        ⚠️ Instance Selection:
        - 如果提供 ha_instance_id：使用指定的實例
        - 如果為 None：自動使用 session 的 current_ha_instance_id
        - 降級順序：session → 預設實例 → 第一個活躍實例

        Args:
            ha_instance_id (int, optional): HA 實例 ID。預設為 None（使用 session 實例）

        Returns:
            dict: 標準化響應格式
                {
                    'success': bool,
                    'data': {
                        'data': {...}  # Home Assistant 網路資訊
                    },
                    'error': str  # 僅在 success=False 時存在
                }

        Raises:
            無 - 所有錯誤都轉為 success=False 返回

        Example:
            # 使用 session 實例（推薦）
            result = self.get_network_info()

            # 指定實例
            result = self.get_network_info(ha_instance_id=2)
        """
        result = self._call_websocket_api(
            message_type='supervisor/api',
            payload={
                'endpoint': '/network/info',
                'method': 'get'
            },
            instance_id=ha_instance_id
        )
        return self._standardize_response(result)

    @http.route('/odoo_ha_addon/ha_urls', type='json', auth='user')
    def get_ha_urls(self, ha_instance_id=None):
        """
        透過 WebSocket 取得 Home Assistant 共享網址資訊
        包含 internal_url、external_url 和 cloud_url

        ⚠️ Instance Selection:
        - 如果提供 ha_instance_id：使用指定的實例
        - 如果為 None：自動使用 session 的 current_ha_instance_id
        - 降級順序：session → 預設實例 → 第一個活躍實例

        Args:
            ha_instance_id (int, optional): HA 實例 ID。預設為 None（使用 session 實例）

        Returns:
            dict: 標準化響應格式
                {
                    'success': bool,
                    'data': {
                        'internal_url': str,  # 內部網址
                        'external_url': str,  # 外部網址
                        'cloud_url': str      # 雲端網址
                    },
                    'error': str  # 僅在 success=False 時存在
                }

        Raises:
            無 - 所有錯誤都轉為 success=False 返回

        Example:
            # 使用 session 實例（推薦）
            result = self.get_ha_urls()

            # 指定實例
            result = self.get_ha_urls(ha_instance_id=2)
        """
        _logger.debug("Getting Home Assistant URLs via WebSocket")

        # 使用 network/url WebSocket API（根據 PDF 文件）
        result = self._call_websocket_api(
            message_type='network/url',
            payload={},
            instance_id=ha_instance_id
        )

        if result.get('success'):
            data = result.get('data', {})
            _logger.debug(f"HA URLs retrieved: {data}")

            # 格式化回傳資料，確保欄位存在
            # 使用標準化的響應格式
            return self._standardize_response({
                'success': True,
                'data': {
                    'internal': data.get('internal_url') or data.get('internal'),
                    'external': data.get('external_url') or data.get('external'),
                    'cloud': data.get('cloud_url') or data.get('cloud'),
                }
            })
        else:
            # 確保失敗時也返回一致的格式
            _logger.error(f"Failed to get HA URLs: {result.get('error')}")
            return self._standardize_response({
                'success': False,
                'error': result.get('error', 'Unknown error')
            })

    @http.route('/odoo_ha_addon/websocket_restart', type='json', auth='user')
    def restart_websocket(self, ha_instance_id=None, force=False):
        """
        重啟 WebSocket 服務

        ⚠️ Instance Selection:
        - 如果提供 ha_instance_id：重啟指定實例的 WebSocket 服務
        - 如果為 None：自動使用 session 的 current_ha_instance_id
        - 降級順序：session → 預設實例 → 第一個活躍實例

        Args:
            ha_instance_id (int, optional): HA 實例 ID。預設為 None（使用 session 實例）
            force (bool, optional): 若為 True，忽略冷卻時間強制重啟。預設為 False

        Returns:
            dict: 標準化響應格式
                {
                    'success': bool,
                    'data': {
                        'message': str,           # 操作結果訊息
                        'instance_id': int,       # 重啟的實例 ID
                        'restart_required': bool  # 是否需要重啟（配置變更時）
                    },
                    'error': str  # 僅在 success=False 時存在
                }

        Raises:
            無 - 所有錯誤都轉為 success=False 返回

        Example:
            # 使用 session 實例（推薦）
            result = self.restart_websocket()

            # 強制重啟（忽略冷卻時間）
            result = self.restart_websocket(force=True)

            # 重啟指定實例
            result = self.restart_websocket(ha_instance_id=2)
        """
        try:
            from odoo.addons.odoo_ha_addon.models.common.websocket_thread_manager import (
                restart_websocket_service
            )

            # Phase 3: 如果沒指定實例 ID，使用當前實例
            if ha_instance_id is None:
                ha_instance_id = self._get_current_instance()
                if ha_instance_id is None:
                    return {
                        'success': False,
                        'error': 'No active HA instance available'
                    }

            _logger.info(f"Manual WebSocket restart requested (instance={ha_instance_id}, force={force})")
            if request.env:
                result = restart_websocket_service(request.env, instance_id=ha_instance_id, force=force)

                if not result['success']:
                    # 重啟失敗或被跳過
                    return {
                        'success': False,
                        'error': result['message'],
                        'skipped': result.get('skipped', False)
                    }

                # 使用標準的 'data' 欄位而非 'message'
                return {
                    'success': True,
                    'data': {
                        'message': result['message']
                    }
                }

            return {
                'success': False,
                'error': _('Unable to get Odoo environment')
            }

        except Exception as e:
            _logger.error(f"Failed to restart WebSocket: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/odoo_ha_addon/websocket_status', type='json', auth='user')
    def get_websocket_status(self, ha_instance_id=None):
        """
        取得 WebSocket 服務狀態
        使用 websocket_thread_manager 的狀態檢查函數

        ⚠️ Instance Selection:
        - 如果提供 ha_instance_id：檢查指定實例的 WebSocket 狀態
        - 如果為 None：自動使用 session 的 current_ha_instance_id
        - 降級順序：session → 預設實例 → 第一個活躍實例

        Args:
            ha_instance_id (int, optional): HA 實例 ID。預設為 None（使用 session 實例）

        Returns:
            dict: 標準化響應格式
                {
                    'success': bool,
                    'data': {
                        'is_running': bool,       # WebSocket 服務是否運行
                        'current_url': str,       # 當前連線的 URL
                        'config_changed': bool    # 配置是否變更
                    },
                    'error': str  # 僅在 success=False 時存在
                }

        Raises:
            無 - 所有錯誤都轉為 success=False 返回

        Example:
            # 使用 session 實例（推薦）
            result = self.get_websocket_status()

            # 指定實例
            result = self.get_websocket_status(ha_instance_id=2)
        """
        try:
            from odoo.addons.odoo_ha_addon.models.common.websocket_thread_manager import (
                is_websocket_service_running,
                is_config_changed
            )

            # Phase 3: 如果沒指定實例 ID，使用當前實例
            if ha_instance_id is None:
                ha_instance_id = self._get_current_instance()
                if ha_instance_id is None:
                    return self._standardize_response({
                        'success': False,
                        'error': 'No active HA instance available'
                    })

            # 取得實例資料（ir.rule 會自動檢查權限）
            # 移除 .sudo() 以確保只能訪問授權的實例
            instance = request.env['ha.instance'].browse(ha_instance_id)
            if not instance.exists():
                return self._standardize_response({
                    'success': False,
                    'error': f'HA instance with ID {ha_instance_id} not found or access denied'
                })

            # 使用 thread manager 的狀態檢查（更準確）
            is_running = is_websocket_service_running(request.env, instance_id=ha_instance_id) if request.env else False
            config_synced = not is_config_changed(request.env, instance_id=ha_instance_id) if request.env and is_running else True

            return self._standardize_response({
                'success': True,
                'data': {
                    'is_running': is_running,
                    'config_synced': config_synced,
                    'current_url': instance.api_url,
                    'has_token': bool(instance.api_token),
                    'status_text': _('Connected') if is_running else _('Disconnected'),
                    'instance_id': ha_instance_id,
                    'instance_name': instance.name
                }
            })

        except Exception as e:
            _logger.error(f"Failed to get WebSocket status: {e}")
            return self._standardize_response({
                'success': False,
                'error': str(e)
            })

    @http.route('/odoo_ha_addon/areas', type='json', auth='user')
    def get_areas(self, ha_instance_id=None):
        """
        取得所有 Home Assistant areas

        使用重試機制處理並發更新導致的序列化衝突

        ⚠️ Instance Selection:
        - 如果提供 ha_instance_id：取得指定實例的 areas
        - 如果為 None：自動使用 session 的 current_ha_instance_id
        - 降級順序：session → 預設實例 → 第一個活躍實例

        Args:
            ha_instance_id (int, optional): HA 實例 ID。預設為 None（使用 session 實例）

        Returns:
            dict: 標準化響應格式
                {
                    'success': bool,
                    'data': {
                        'areas': [
                            {
                                'id': str,            # Area ID
                                'name': str,          # Area 名稱
                                'entity_count': int   # 該 Area 的實體數量
                            },
                            ...
                        ]
                    },
                    'error': str  # 僅在 success=False 時存在
                }

        Raises:
            無 - 所有錯誤都轉為 success=False 返回

        Example:
            # 使用 session 實例（推薦）
            result = self.get_areas()

            # 指定實例
            result = self.get_areas(ha_instance_id=2)
        """
        max_retries = 3
        retry_delay = 0.5  # 秒

        # Phase 3: 如果沒指定實例 ID，使用當前實例
        if ha_instance_id is None:
            ha_instance_id = self._get_current_instance()
            if ha_instance_id is None:
                return self._standardize_response({
                    'success': False,
                    'error': 'No active HA instance available'
                })

        for attempt in range(max_retries):
            try:
                # Phase 3: 取得實例（ir.rule 會自動檢查權限）
                # 移除 .sudo() 以確保只能訪問授權的實例
                instance = request.env['ha.instance'].browse(ha_instance_id)
                if not instance.exists():
                    return self._standardize_response({
                        'success': False,
                        'error': f'HA instance with ID {ha_instance_id} not found or access denied'
                    })

                # 同步操作：每步驟後 commit 以減少鎖定時間
                # Trade-off: 犧牲原子性換取更好的並發性能
                # - 若中途失敗，已完成的步驟不會回滾
                # - 但其他執行緒（如 WebSocket 更新）不會被長時間阻塞

                # 1. 先同步 areas (Phase 3: 傳入 instance_id)
                # sudo: 系統層級同步，需要寫入所有用戶可見的 areas
                request.env['ha.area'].sudo().sync_areas_from_ha(instance_id=ha_instance_id)
                request.env.cr.commit()  # 釋放 area 表的鎖

                # 2. 同步 entities（不同步 area 關聯）
                # sudo: 系統層級同步，需要建立/更新所有用戶可見的 entities
                request.env['ha.entity'].sudo().sync_entity_states_from_ha(
                    instance_id=ha_instance_id,
                    sync_area_relations=False
                )
                request.env.cr.commit()  # 釋放 entity 表的鎖

                # 3. 獨立同步 entity-area 關聯
                # sudo: 系統層級同步，需要更新所有 entities 的 area 關聯
                request.env['ha.entity'].sudo()._sync_entity_registry_relations(instance_id=ha_instance_id)
                request.env.cr.commit()  # 釋放關聯更新的鎖

                # 4. 讀取該實例的 areas (Phase 3: 過濾 ha_instance_id)
                # 移除 .sudo() 以尊重 ir.rule 權限控制（HA User 只能看到授權的 areas）
                areas = request.env['ha.area'].search([
                    ('ha_instance_id', '=', ha_instance_id)
                ])

                return self._standardize_response({
                    'success': True,
                    'data': {
                        'areas': [{
                            'id': area.id,
                            'area_id': area.area_id,
                            'name': area.name,
                            'icon': area.icon,
                            'entity_count': area.entity_count,
                        } for area in areas]
                    }
                })

            except psycopg2_errors.SerializationFailure as e:
                # 序列化衝突，重試
                _logger.warning(f"Serialization conflict (attempt {attempt + 1}/{max_retries}): {e}")
                request.env.cr.rollback()
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    # 超過最大重試次數
                    _logger.error(f"Failed to get areas after {max_retries} attempts due to serialization conflicts")
                    return self._standardize_response({
                        'success': False,
                        'error': 'Database conflict, please try again'
                    })

            except Exception as e:
                _logger.error(f"Failed to get areas: {e}", exc_info=True)
                request.env.cr.rollback()
                return self._standardize_response({
                    'success': False,
                    'error': str(e)
                })

        # 理論上不會到這裡，但作為安全網保留
        # 如果執行到這裡，表示 for 循環邏輯有問題
        _logger.critical("Unexpected: reached unreachable code in get_areas(). Check retry loop logic.")
        return self._standardize_response({
            'success': False,
            'error': 'Unexpected error'
        })

    @http.route('/odoo_ha_addon/entities_by_area', type='json', auth='user')
    def get_entities_by_area(self, area_id, ha_instance_id=None):
        """
        根據 area_id 取得 entities

        ⚠️ Instance Selection:
        - 如果提供 ha_instance_id：取得指定實例的 area entities
        - 如果為 None：自動使用 session 的 current_ha_instance_id
        - 降級順序：session → 預設實例 → 第一個活躍實例

        Args:
            area_id (int): Odoo record ID of ha.area（必需）
            ha_instance_id (int, optional): HA 實例 ID。預設為 None（使用 session 實例）

        Returns:
            dict: 標準化響應格式
                {
                    'success': bool,
                    'data': {
                        'entities': [
                            {
                                'entity_id': str,     # 實體 ID
                                'name': str,          # 實體名稱
                                'state': str,         # 當前狀態
                                'domain': str,        # 實體類型
                                'area_id': str,       # 所屬 Area ID
                                ...
                            },
                            ...
                        ]
                    },
                    'error': str  # 僅在 success=False 時存在
                }

        Raises:
            無 - 所有錯誤都轉為 success=False 返回

        Example:
            # 使用 session 實例（推薦）
            result = self.get_entities_by_area(area_id=5)

            # 指定實例
            result = self.get_entities_by_area(area_id=5, ha_instance_id=2)
        """
        try:
            if not area_id:
                return self._standardize_response({
                    'success': False,
                    'error': 'area_id is required'
                })

            # Phase 3: 如果沒指定實例 ID，使用當前實例
            if ha_instance_id is None:
                ha_instance_id = self._get_current_instance()
                if ha_instance_id is None:
                    return self._standardize_response({
                        'success': False,
                        'error': 'No active HA instance available'
                    })

            # 查詢該 area 下的所有 entities (Phase 3: 加上 ha_instance_id 過濾)
            # 移除 .sudo() 以尊重 ir.rule 權限控制（HA User 只能看到授權的 entities）
            entities = request.env['ha.entity'].search([
                ('area_id', '=', int(area_id)),
                ('ha_instance_id', '=', ha_instance_id)
            ])

            return self._standardize_response({
                'success': True,
                'data': {
                    'entities': [{
                        'id': entity.id,
                        'entity_id': entity.entity_id,
                        'name': entity.name,
                        'entity_state': entity.entity_state,
                        'domain': entity.domain,
                        'last_changed': entity.last_changed.isoformat() if entity.last_changed else None,
                        'attributes': entity.attributes or {},
                    } for entity in entities]
                }
            })

        except Exception as e:
            _logger.error(f"Failed to get entities by area: {e}", exc_info=True)
            return self._standardize_response({
                'success': False,
                'error': str(e)
            })

    @http.route('/odoo_ha_addon/area_dashboard_data', type='json', auth='user')
    def get_area_dashboard_data(self, area_id=None, ha_instance_id=None):
        """
        取得 Area Dashboard 所需的完整資料（Device 優先視圖）

        此 API 返回指定區域的：
        1. 區域基本資訊
        2. 該區域下的所有 Devices 及其 Entities
        3. 獨立 Entities（無 Device 或從其他 Device 移入）

        Entity Area 覆蓋邏輯：
        - 若 entity.area_id 與 device.area_id 不同，該 entity 會：
          a. 在原 Device Card 中標記「已移至 [其他區域]」
          b. 在目標區域的獨立實體區塊中顯示（標記來源 Device）

        特殊情況：
        - 當 area_id 為 0 或 'unassigned' 時，返回「未分區」的 devices 和 entities

        Args:
            area_id (int|str): Odoo record ID of ha.area，或 0/'unassigned' 表示未分區
            ha_instance_id (int, optional): HA 實例 ID。預設為 None（使用 session 實例）

        Returns:
            dict: 標準化響應格式
                {
                    'success': bool,
                    'data': {
                        'area': {
                            'id': int,
                            'area_id': str,
                            'name': str,
                            'icon': str
                        },
                        'devices': [{
                            'id': int,
                            'device_id': str,
                            'name': str,
                            'name_by_user': str,
                            'manufacturer': str,
                            'model': str,
                            'entity_count': int,
                            'entities': [{
                                'id': int,
                                'entity_id': str,
                                'name': str,
                                'entity_state': str,
                                'domain': str,
                                'attributes': dict,
                                'area_override': null | {'area_id': int, 'area_name': str}
                            }]
                        }],
                        'standalone_entities': [{
                            'id': int,
                            'entity_id': str,
                            'name': str,
                            'entity_state': str,
                            'domain': str,
                            'attributes': dict,
                            'source_device': null | {
                                'device_id': int,
                                'device_name': str,
                                'device_area_name': str
                            }
                        }]
                    },
                    'error': str  # 僅在 success=False 時存在
                }
        """
        try:
            # Phase 3: 如果沒指定實例 ID，使用當前實例
            if ha_instance_id is None:
                ha_instance_id = self._get_current_instance()
                if ha_instance_id is None:
                    return self._standardize_response({
                        'success': False,
                        'error': _('No active HA instance available')
                    })

            # 檢查是否為「未分區」查詢
            is_unassigned = area_id in (0, '0', 'unassigned', None, False)

            if is_unassigned:
                # 「未分區」虛擬區域
                return self._get_unassigned_area_data(ha_instance_id)

            area_id = int(area_id)

            # 取得 Area 資訊
            area = request.env['ha.area'].search([
                ('id', '=', area_id),
                ('ha_instance_id', '=', ha_instance_id)
            ], limit=1)

            if not area:
                return self._standardize_response({
                    'success': False,
                    'error': _('Area not found (ID: %s)') % area_id
                })

            # 1. 取得該 Area 下的所有 Devices
            devices = request.env['ha.device'].search([
                ('area_id', '=', area_id),
                ('ha_instance_id', '=', ha_instance_id)
            ])

            # 批次查詢所有 devices 的 entities（避免 N+1 問題）
            all_entities = request.env['ha.entity'].search([
                ('device_id', 'in', devices.ids),
                ('ha_instance_id', '=', ha_instance_id)
            ]) if devices else request.env['ha.entity']

            # 在 Python 中按 device_id 分組
            entities_by_device = defaultdict(list)
            for entity in all_entities:
                entities_by_device[entity.device_id.id].append(entity)

            devices_data = []
            for device in devices:
                # 使用預先查詢好的 entities（O(1) 查找）
                entities = entities_by_device.get(device.id, [])

                entities_data = []
                for entity in entities:
                    # 檢查 entity 是否有不同的 area_id（area override）
                    area_override = None
                    if entity.area_id and entity.area_id.id != area_id:
                        area_override = {
                            'area_id': entity.area_id.id,
                            'area_name': entity.area_id.name
                        }

                    entities_data.append({
                        'id': entity.id,
                        'entity_id': entity.entity_id,
                        'name': entity.name,
                        'entity_state': entity.entity_state,
                        'domain': entity.domain,
                        'last_changed': entity.last_changed.isoformat() if entity.last_changed else None,
                        'attributes': entity.attributes or {},
                        'area_override': area_override,
                    })

                devices_data.append({
                    'id': device.id,
                    'device_id': device.device_id,
                    'name': device.name,
                    'name_by_user': device.name_by_user,
                    'manufacturer': device.manufacturer,
                    'model': device.model,
                    'entity_count': len(entities_data),
                    'entities': entities_data,
                })

            # 2. 取得獨立 Entities
            # 2.1 直接屬於此 Area 且沒有 Device 的 entities
            standalone_no_device = request.env['ha.entity'].search([
                ('area_id', '=', area_id),
                ('device_id', '=', False),
                ('ha_instance_id', '=', ha_instance_id)
            ])

            # 2.2 從其他 Area 的 Device 移入的 entities
            # (entity.area_id = current_area, 但 device.area_id != current_area)
            moved_in_entities = request.env['ha.entity'].search([
                ('area_id', '=', area_id),
                ('device_id', '!=', False),
                ('device_id.area_id', '!=', area_id),
                ('ha_instance_id', '=', ha_instance_id)
            ])

            standalone_entities_data = []

            # 處理無 Device 的 entities
            for entity in standalone_no_device:
                standalone_entities_data.append({
                    'id': entity.id,
                    'entity_id': entity.entity_id,
                    'name': entity.name,
                    'entity_state': entity.entity_state,
                    'domain': entity.domain,
                    'last_changed': entity.last_changed.isoformat() if entity.last_changed else None,
                    'attributes': entity.attributes or {},
                    'source_device': None,
                })

            # 處理從其他 Device 移入的 entities
            for entity in moved_in_entities:
                device = entity.device_id
                device_area_name = device.area_id.name if device.area_id else _('No Area')

                standalone_entities_data.append({
                    'id': entity.id,
                    'entity_id': entity.entity_id,
                    'name': entity.name,
                    'entity_state': entity.entity_state,
                    'domain': entity.domain,
                    'last_changed': entity.last_changed.isoformat() if entity.last_changed else None,
                    'attributes': entity.attributes or {},
                    'source_device': {
                        'device_id': device.id,
                        'device_name': device.name_by_user or device.name,
                        'device_area_name': device_area_name,
                    },
                })

            return self._standardize_response({
                'success': True,
                'data': {
                    'area': {
                        'id': area.id,
                        'area_id': area.area_id,
                        'name': area.name,
                        'icon': area.icon,
                    },
                    'devices': devices_data,
                    'standalone_entities': standalone_entities_data,
                }
            })

        except Exception as e:
            _logger.error(f"Failed to get area dashboard data: {e}", exc_info=True)
            return self._standardize_response({
                'success': False,
                'error': str(e)
            })

    def _get_unassigned_area_data(self, ha_instance_id):
        """
        取得「未分區」的 devices 和 entities

        「未分區」包含：
        1. area_id 為空的 Devices 及其 Entities
        2. 無 Device 且 area_id 為空的 Entities

        Args:
            ha_instance_id (int): HA 實例 ID

        Returns:
            dict: 與 get_area_dashboard_data 相同格式的響應
        """
        # 1. 取得沒有 Area 的所有 Devices
        devices = request.env['ha.device'].search([
            ('area_id', '=', False),
            ('ha_instance_id', '=', ha_instance_id)
        ])

        # 批次查詢所有 devices 的 entities（避免 N+1 問題）
        all_entities = request.env['ha.entity'].search([
            ('device_id', 'in', devices.ids),
            ('ha_instance_id', '=', ha_instance_id)
        ]) if devices else request.env['ha.entity']

        # 在 Python 中按 device_id 分組
        entities_by_device = defaultdict(list)
        for entity in all_entities:
            entities_by_device[entity.device_id.id].append(entity)

        devices_data = []
        for device in devices:
            # 使用預先查詢好的 entities（O(1) 查找）
            entities = entities_by_device.get(device.id, [])

            entities_data = []
            for entity in entities:
                # 檢查 entity 是否有設定 area_id（area override）
                area_override = None
                if entity.area_id:
                    area_override = {
                        'area_id': entity.area_id.id,
                        'area_name': entity.area_id.name
                    }

                entities_data.append({
                    'id': entity.id,
                    'entity_id': entity.entity_id,
                    'name': entity.name,
                    'entity_state': entity.entity_state,
                    'domain': entity.domain,
                    'last_changed': entity.last_changed.isoformat() if entity.last_changed else None,
                    'attributes': entity.attributes or {},
                    'area_override': area_override,
                })

            devices_data.append({
                'id': device.id,
                'device_id': device.device_id,
                'name': device.name,
                'name_by_user': device.name_by_user,
                'manufacturer': device.manufacturer,
                'model': device.model,
                'entity_count': len(entities_data),
                'entities': entities_data,
            })

        # 2. 取得獨立 Entities（無 Device 且無 Area）
        standalone_no_device = request.env['ha.entity'].search([
            ('area_id', '=', False),
            ('device_id', '=', False),
            ('ha_instance_id', '=', ha_instance_id)
        ])

        standalone_entities_data = []
        for entity in standalone_no_device:
            standalone_entities_data.append({
                'id': entity.id,
                'entity_id': entity.entity_id,
                'name': entity.name,
                'entity_state': entity.entity_state,
                'domain': entity.domain,
                'last_changed': entity.last_changed.isoformat() if entity.last_changed else None,
                'attributes': entity.attributes or {},
                'source_device': None,
            })

        return self._standardize_response({
            'success': True,
            'data': {
                'area': {
                    'id': 0,
                    'area_id': 'unassigned',
                    'name': _('Unassigned'),
                    'icon': 'mdi:help-circle-outline',
                },
                'devices': devices_data,
                'standalone_entities': standalone_entities_data,
            }
        })

    @http.route('/odoo_ha_addon/call_service', type='json', auth='user')
    def call_service(self, domain, service, service_data=None, ha_instance_id=None):
        """
        呼叫 Home Assistant service 來控制裝置

        ⚠️ Instance Selection:
        - 如果提供 ha_instance_id：對指定實例呼叫 service
        - 如果為 None：自動使用 session 的 current_ha_instance_id
        - 降級順序：session → 預設實例 → 第一個活躍實例

        Args:
            domain (str): Entity domain（必需）。例如：'switch', 'light', 'climate'
            service (str): Service name（必需）。例如：'turn_on', 'turn_off', 'toggle'
            service_data (dict, optional): Service data（必需包含 entity_id）
            ha_instance_id (int, optional): HA 實例 ID。預設為 None（使用 session 實例）

        Returns:
            dict: 標準化響應格式
                {
                    'success': bool,
                    'data': {
                        'context': {...},  # Service 執行上下文
                        ...
                    },
                    'error': str  # 僅在 success=False 時存在
                }

        Raises:
            無 - 所有錯誤都轉為 success=False 返回

        Examples:
            # Toggle a switch (使用 session 實例)
            result = self.call_service(
                domain='switch',
                service='toggle',
                service_data={'entity_id': 'switch.living_room'}
            )

            # Set light brightness (指定實例)
            result = self.call_service(
                domain='light',
                service='turn_on',
                service_data={'entity_id': 'light.bedroom', 'brightness': 128},
                ha_instance_id=2
            )

            # Set climate temperature
            {'domain': 'climate', 'service': 'set_temperature', 'service_data': {'entity_id': 'climate.living_room', 'temperature': 22}}
        """
        _logger.info(f"Service call request: {domain}.{service} with data: {service_data}")

        if service_data is None:
            service_data = {}

        try:
            # Validate required parameters
            if not domain or not service:
                return self._standardize_response({
                    'success': False,
                    'error': 'domain and service are required'
                })

            if 'entity_id' not in service_data:
                return self._standardize_response({
                    'success': False,
                    'error': 'entity_id is required in service_data'
                })

            # Call WebSocket API (Phase 3: 傳入 instance_id)
            result = self._call_websocket_api(
                message_type='call_service',
                payload={
                    'domain': domain,
                    'service': service,
                    'service_data': service_data
                },
                instance_id=ha_instance_id
            )

            _logger.info(f"Service {domain}.{service} called: success={result.get('success')}")
            return self._standardize_response(result)

        except Exception as e:
            _logger.error(f"Failed to call service {domain}.{service}: {e}", exc_info=True)
            return self._standardize_response({
                'success': False,
                'error': str(e)
            })

    # ====================================
    # Phase 3: Multi-Instance Management
    # ====================================

    @http.route('/odoo_ha_addon/get_instances', type='json', auth='user')
    def get_instances(self):
        """
        Phase 3: 取得所有可用的 HA 實例列表

        ⚠️ Permission Filtering:
        - HA Manager: 看到所有實例（透過 ir.rule manager rule）
        - HA User: 只看到授權的實例（透過 entity groups，ir.rule user rule）
        - ir.rule 會自動過濾並去重複（.mapped().ids）

        Returns:
            dict: {
                'success': True,
                'data': {
                    'instances': [...],
                    'current_instance_id': int
                }
            }
        """
        try:
            # 查詢活躍的實例（ir.rule 會自動過濾權限）
            # 移除 .sudo() 以尊重 ir.rule 的權限控制
            instances = request.env['ha.instance'].search([
                ('active', '=', True)
            ], order='sequence, id')

            # 取得當前實例 ID
            current_instance_id = self._get_current_instance()

            return self._standardize_response({
                'success': True,
                'data': {
                    'instances': [{
                        'id': inst.id,
                        'name': inst.name,
                        'api_url': inst.api_url,
                        'description': inst.description or '',
                        'is_active': inst.active,
                        'websocket_status': inst.websocket_status,
                        'entity_count': inst.entity_count,
                        'area_count': inst.area_count,
                        'last_sync': inst.last_sync_date.strftime('%Y-%m-%d %H:%M:%S') if inst.last_sync_date else None,
                    } for inst in instances],
                    'current_instance_id': current_instance_id
                }
            })

        except Exception as e:
            _logger.error(f"Failed to get HA instances: {e}", exc_info=True)
            return self._standardize_response({
                'success': False,
                'error': str(e)
            })

    @http.route('/odoo_ha_addon/switch_instance', type='json', auth='user')
    def switch_instance(self, instance_id):
        """
        Phase 3: 切換使用者當前的 HA 實例

        將選擇的實例 ID 存儲在 session 中，後續所有 API 呼叫都會使用這個實例

        Phase 2.2: 使用 _validate_instance() 進行統一驗證

        Args:
            instance_id: 要切換到的 HA 實例 ID

        Returns:
            dict: {
                'success': True,
                'data': {
                    'instance_id': int,
                    'instance_name': str,
                    'message': str
                },
                'error_type': str  # Phase 2.2: 錯誤類型（當 success=False）
            }
        """
        try:
            if not instance_id:
                return self._standardize_response({
                    'success': False,
                    'error': _('instance_id is required'),
                    'error_type': 'validation_error'
                })

            # Phase 2.2: 使用統一的驗證方法
            validation = self._validate_instance(int(instance_id))
            if not validation['valid']:
                return self._standardize_response({
                    'success': False,
                    'error': validation['error_message'],
                    'error_type': validation['error_type']
                })

            instance = validation['instance']

            # 儲存到 session
            request.session['current_ha_instance_id'] = instance.id

            # 同時更新用戶欄位（供 Search View 使用）
            # sudo: 允許用戶更新自己的偏好設定，即使沒有 res.users 寫入權限
            request.env.user.sudo().write({'current_ha_instance_id': instance.id})

            _logger.info(f"User {request.env.user.name} switched to HA instance: {instance.name} (ID: {instance.id})")

            # Phase 3.3: 發送 Bus notification 同步所有標籤頁
            # sudo: 系統廣播通知，需要存取所有用戶的 partner channel
            try:
                request.env['ha.realtime.update'].sudo().notify_instance_switched(
                    instance_id=instance.id,
                    instance_name=instance.name,
                    user_id=request.env.user.id
                )
            except Exception as e:
                _logger.error(f"Failed to send instance_switched notification: {e}")

            return self._standardize_response({
                'success': True,
                'data': {
                    'instance_id': instance.id,
                    'instance_name': instance.name,
                    'message': _('Switched to %s') % instance.name
                }
            })

        except Exception as e:
            _logger.error(f"Failed to switch HA instance: {e}", exc_info=True)
            return self._standardize_response({
                'success': False,
                'error': str(e)
            })

    # ====================================
    # Glances Dashboard APIs
    # ====================================

    @http.route('/odoo_ha_addon/glances_devices', type='json', auth='user')
    def get_glances_devices(self, ha_instance_id=None):
        """
        取得 Glances 設備列表

        透過 WebSocket 呼叫 config/device_registry/list，
        篩選出 domain 為 "glances" 的設備。

        Args:
            ha_instance_id (int, optional): HA 實例 ID。預設為 None（使用 session 實例）

        Returns:
            dict: 標準化響應格式
                {
                    'success': bool,
                    'data': {
                        'devices': [
                            {
                                'id': str,                 # Device ID
                                'name': str,               # Device name
                                'model': str,              # Device model
                                'manufacturer': str,       # Manufacturer
                                'sw_version': str,         # Software version
                                'config_entry_id': str,    # Config entry ID
                            },
                            ...
                        ]
                    },
                    'error': str  # 僅在 success=False 時存在
                }
        """
        _logger.debug("Getting Glances devices via WebSocket")

        # 呼叫 config/device_registry/list WebSocket API
        result = self._call_websocket_api(
            message_type='config/device_registry/list',
            payload={},
            instance_id=ha_instance_id
        )

        if not result.get('success'):
            return self._standardize_response(result)

        # 篩選 glances 設備
        all_devices = result.get('data', [])
        glances_devices = []

        for device in all_devices:
            # 檢查 identifiers 是否包含 glances
            identifiers = device.get('identifiers', [])
            is_glances = False

            for identifier in identifiers:
                # 驗證 identifier 是列表/元組且至少有一個字串元素
                if (isinstance(identifier, (list, tuple)) and
                    len(identifier) >= 1 and
                    isinstance(identifier[0], str) and
                    identifier[0] == 'glances'):
                    is_glances = True
                    break

            if is_glances:
                glances_devices.append({
                    'id': device.get('id'),
                    'name': device.get('name') or device.get('name_by_user') or 'Glances Device',
                    'model': device.get('model'),
                    'manufacturer': device.get('manufacturer'),
                    'sw_version': device.get('sw_version'),
                    'config_entry_id': device.get('config_entries', [None])[0] if device.get('config_entries') else None,
                    'area_id': device.get('area_id'),
                })

        _logger.debug(f"Found {len(glances_devices)} Glances devices")

        return self._standardize_response({
            'success': True,
            'data': {
                'devices': glances_devices
            }
        })

    @http.route('/odoo_ha_addon/glances_device_entities', type='json', auth='user')
    def get_glances_device_entities(self, device_id, ha_instance_id=None):
        """
        取得特定 Glances 設備的所有實體及其狀態

        透過 WebSocket 呼叫 config/entity_registry/list 取得設備的實體列表，
        然後呼叫 get_states 取得每個實體的當前狀態。

        Args:
            device_id (str): Glances 設備的 ID
            ha_instance_id (int, optional): HA 實例 ID。預設為 None（使用 session 實例）

        Returns:
            dict: 標準化響應格式
                {
                    'success': bool,
                    'data': {
                        'device_id': str,
                        'entities': [
                            {
                                'entity_id': str,          # 實體 ID
                                'name': str,               # 實體名稱
                                'state': str,              # 當前狀態
                                'unit_of_measurement': str,# 單位
                                'device_class': str,       # 設備類型
                                'icon': str,               # 圖示
                                'attributes': dict,        # 所有屬性
                            },
                            ...
                        ]
                    },
                    'error': str  # 僅在 success=False 時存在
                }
        """
        if not device_id:
            return self._standardize_response({
                'success': False,
                'error': _('device_id is required')
            })

        _logger.debug(f"Getting entities for Glances device: {device_id}")

        # Step 1: 取得實體註冊表
        entity_result = self._call_websocket_api(
            message_type='config/entity_registry/list',
            payload={},
            instance_id=ha_instance_id
        )

        if not entity_result.get('success'):
            return self._standardize_response(entity_result)

        # 篩選出屬於此設備的實體
        all_entities = entity_result.get('data', [])
        device_entity_ids = []

        for entity in all_entities:
            if entity.get('device_id') == device_id:
                device_entity_ids.append(entity.get('entity_id'))

        if not device_entity_ids:
            return self._standardize_response({
                'success': True,
                'data': {
                    'device_id': device_id,
                    'entities': []
                }
            })

        _logger.debug(f"Found {len(device_entity_ids)} entities for device {device_id}")

        # Step 2: 取得所有實體狀態
        states_result = self._call_websocket_api(
            message_type='get_states',
            payload={},
            instance_id=ha_instance_id
        )

        if not states_result.get('success'):
            return self._standardize_response(states_result)

        # 建立實體 ID 到狀態的映射
        all_states = states_result.get('data', [])
        state_map = {state.get('entity_id'): state for state in all_states}

        # 組合實體資料
        entities = []
        for entity_id in device_entity_ids:
            state_data = state_map.get(entity_id, {})
            attributes = state_data.get('attributes', {})

            entities.append({
                'entity_id': entity_id,
                'name': attributes.get('friendly_name') or entity_id,
                'state': state_data.get('state'),
                'unit_of_measurement': attributes.get('unit_of_measurement'),
                'device_class': attributes.get('device_class'),
                'icon': attributes.get('icon'),
                'state_class': attributes.get('state_class'),
                'last_changed': state_data.get('last_changed'),
                'last_updated': state_data.get('last_updated'),
                'attributes': attributes,
            })

        # 按照 device_class 或名稱排序
        entities.sort(key=lambda e: (e.get('device_class') or 'zzz', e.get('name') or ''))

        return self._standardize_response({
            'success': True,
            'data': {
                'device_id': device_id,
                'entities': entities
            }
        })

    # ====================================
    # Entity Related API
    # ====================================

    @http.route('/odoo_ha_addon/entity_related', type='json', auth='user')
    def get_entity_related(self, entity_id, ha_instance_id=None):
        """
        取得 Entity 的相關資訊（Area、Device、Label、Automation）

        透過 WebSocket 呼叫 search/related API，然後查詢 Odoo 資料庫
        取得完整的記錄資訊。

        Args:
            entity_id (str): Entity ID（必需）。例如：'switch.living_room'
            ha_instance_id (int, optional): HA 實例 ID。預設為 None（使用 session 實例）

        Returns:
            dict: 標準化響應格式
                {
                    'success': bool,
                    'data': {
                        'area': {
                            'id': int,      # Odoo record ID
                            'area_id': str, # HA area_id
                            'name': str,
                            'icon': str
                        } | null,
                        'device': {
                            'id': int,           # Odoo record ID
                            'device_id': str,    # HA device_id
                            'name': str,
                            'manufacturer': str,
                            'model': str
                        } | null,
                        'labels': [
                            {'id': int, 'label_id': str, 'name': str, 'icon': str, 'color': str}
                        ],
                        'automations': [
                            {'id': int, 'entity_id': str, 'name': str, 'state': str}
                        ]
                    },
                    'error': str  # 僅在 success=False 時存在
                }
        """
        if not entity_id:
            return self._standardize_response({
                'success': False,
                'error': _('entity_id is required')
            })

        _logger.debug(f"Getting related info for entity: {entity_id}")

        # Phase 3: 如果沒指定實例 ID，使用當前實例
        if ha_instance_id is None:
            ha_instance_id = self._get_current_instance()
            if ha_instance_id is None:
                return self._standardize_response({
                    'success': False,
                    'error': _('No active HA instance available')
                })

        # 呼叫 search/related WebSocket API
        result = self._call_websocket_api(
            message_type='search/related',
            payload={
                'item_type': 'entity',
                'item_id': entity_id
            },
            instance_id=ha_instance_id
        )

        if not result.get('success'):
            return self._standardize_response(result)

        # 處理 HA 回傳的資料，轉換為 Odoo 可用的格式
        ha_data = result.get('data', {})

        response_data = {
            'area': None,
            'device': None,
            'labels': [],
            'automations': [],
            'scenes': [],
            'scripts': []
        }

        # 處理 Area
        area_ids = ha_data.get('area', [])
        if area_ids:
            # 查詢 Odoo 中的 Area 記錄
            area = request.env['ha.area'].search([
                ('area_id', '=', area_ids[0]),
                ('ha_instance_id', '=', ha_instance_id)
            ], limit=1)
            if area:
                response_data['area'] = {
                    'id': area.id,
                    'area_id': area.area_id,
                    'name': area.name,
                    'icon': area.icon
                }

        # 處理 Device
        device_ids = ha_data.get('device', [])
        if device_ids:
            device = request.env['ha.device'].search([
                ('device_id', '=', device_ids[0]),
                ('ha_instance_id', '=', ha_instance_id)
            ], limit=1)
            if device:
                response_data['device'] = {
                    'id': device.id,
                    'device_id': device.device_id,
                    'name': device.name_by_user or device.name,
                    'manufacturer': device.manufacturer,
                    'model': device.model
                }

        # 處理 Labels
        label_ids = ha_data.get('label', [])
        if label_ids:
            labels = request.env['ha.label'].search([
                ('label_id', 'in', label_ids),
                ('ha_instance_id', '=', ha_instance_id)
            ])
            response_data['labels'] = [{
                'id': label.id,
                'label_id': label.label_id,
                'name': label.name,
                'icon': label.icon,
                'color': label.ha_color
            } for label in labels]

        # 處理 Automations (這些是 entity 類型)
        automation_ids = ha_data.get('automation', [])
        if automation_ids:
            automations = request.env['ha.entity'].search([
                ('entity_id', 'in', automation_ids),
                ('ha_instance_id', '=', ha_instance_id),
                ('domain', '=', 'automation')
            ])
            response_data['automations'] = [{
                'id': automation.id,
                'entity_id': automation.entity_id,
                'name': automation.name or automation.entity_id,
                'state': automation.entity_state
            } for automation in automations]

        # 處理 Scenes (這些也是 entity 類型)
        # Note: Scene 不包含 state 欄位，因為 HA scene 是觸發式的動作，
        # 不像 automation/script 具有持續的 on/off 狀態。前端 UI 也配合此設計不顯示狀態 badge。
        scene_ids = ha_data.get('scene', [])
        if scene_ids:
            scenes = request.env['ha.entity'].search([
                ('entity_id', 'in', scene_ids),
                ('ha_instance_id', '=', ha_instance_id),
                ('domain', '=', 'scene')
            ])
            response_data['scenes'] = [{
                'id': scene.id,
                'entity_id': scene.entity_id,
                'name': scene.name or scene.entity_id
            } for scene in scenes]

        # 處理 Scripts (這些也是 entity 類型)
        script_ids = ha_data.get('script', [])
        if script_ids:
            scripts = request.env['ha.entity'].search([
                ('entity_id', 'in', script_ids),
                ('ha_instance_id', '=', ha_instance_id),
                ('domain', '=', 'script')
            ])
            response_data['scripts'] = [{
                'id': script.id,
                'entity_id': script.entity_id,
                'name': script.name or script.entity_id,
                'state': script.entity_state
            } for script in scripts]

        _logger.debug(f"Related info for {entity_id}: area={bool(response_data['area'])}, "
                     f"device={bool(response_data['device'])}, "
                     f"labels={len(response_data['labels'])}, "
                     f"automations={len(response_data['automations'])}, "
                     f"scenes={len(response_data['scenes'])}, "
                     f"scripts={len(response_data['scripts'])}")

        return self._standardize_response({
            'success': True,
            'data': response_data
        })
