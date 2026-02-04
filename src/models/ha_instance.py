# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError
import logging

_logger = logging.getLogger(__name__)


class HAInstance(models.Model):
    """
    Home Assistant Instance Model
    支援多個 HA 實例配置，每個實例可以有獨立的 API URL 和 Token
    """
    _name = 'ha.instance'
    _description = 'Home Assistant Instance'
    _order = 'sequence, name'

    # ==================== 基本欄位 ====================

    name = fields.Char(
        string='Instance Name',
        required=True,
        help='易於識別的實例名稱，例如：Home HA, Office HA'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='排序順序，數字越小越靠前'
    )

    api_url = fields.Char(
        string='API URL',
        required=True,
        help='Home Assistant API URL，例如：http://homeassistant.local:8123'
    )

    api_token = fields.Char(
        string='Access Token',
        required=True,
        help='Home Assistant Long-Lived Access Token'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='是否啟用此實例'
    )

    # ==================== 計算欄位 ====================

    ws_url = fields.Char(
        string='WebSocket URL',
        compute='_compute_ws_url',
        store=False,
        help='WebSocket 連接 URL（從 API URL 自動計算）'
    )

    entity_count = fields.Integer(
        string='Entity Count',
        compute='_compute_entity_count',
        store=False,
        help='此實例下的實體數量'
    )

    area_count = fields.Integer(
        string='Area Count',
        compute='_compute_area_count',
        store=False,
        help='此實例下的區域數量'
    )

    websocket_status = fields.Selection(
        [
            ('disconnected', 'Disconnected'),
            ('connecting', 'Connecting'),
            ('connected', 'Connected'),
            ('error', 'Error')
        ],
        string='WebSocket Status',
        compute='_compute_websocket_status',
        store=False,
        help='WebSocket 連接狀態（即時檢查心跳）'
    )

    last_sync_date = fields.Datetime(
        string='Last Sync',
        copy=False,
        help='最後一次同步實體數據的時間'
    )

    # ==================== 統計欄位 ====================

    description = fields.Text(
        string='Description',
        help='實例描述或備註'
    )

    # ==================== Custom Properties Definition ====================
    # PropertiesDefinition fields - define custom properties for entities and groups
    # These are the "container" definitions that entity/group properties reference

    entity_properties_definition = fields.PropertiesDefinition(
        'Entity Properties Definition',
        help='Define custom properties available for all entities in this instance'
    )

    group_properties_definition = fields.PropertiesDefinition(
        'Group Properties Definition',
        help='Define custom properties available for all entity groups in this instance'
    )

    # ==================== 實例識別欄位 ====================

    ha_instance_uuid = fields.Char(
        string='HA Instance UUID',
        help='Home Assistant 實例的唯一識別碼（從 API URL 計算 SHA256 hash）',
        readonly=True,
        copy=False,
        index=True
    )

    last_api_url = fields.Char(
        string='Previous API URL',
        help='上次使用的 API URL（用於追蹤 URL 變更）',
        readonly=True,
        copy=False
    )

    # ==================== Compute Methods ====================

    @api.depends('api_url')
    def _compute_ws_url(self):
        """計算 WebSocket URL"""
        for record in self:
            if record.api_url:
                # 將 http:// 或 https:// 轉換為 ws:// 或 wss://
                ws_url = record.api_url.replace('http://', 'ws://').replace('https://', 'wss://')
                # 移除末尾的斜線
                ws_url = ws_url.rstrip('/')
                # 加上 WebSocket 路徑
                record.ws_url = f"{ws_url}/api/websocket"
            else:
                record.ws_url = False

    def _compute_entity_count(self):
        """計算此實例下的實體數量"""
        for record in self:
            record.entity_count = self.env['ha.entity'].search_count([
                ('ha_instance_id', '=', record.id)
            ])

    def _compute_area_count(self):
        """計算此實例下的區域數量"""
        for record in self:
            record.area_count = self.env['ha.area'].search_count([
                ('ha_instance_id', '=', record.id)
            ])

    def _compute_websocket_status(self):
        """
        計算 WebSocket 連接狀態
        Phase 2: 透過心跳機制檢查特定實例的 WebSocket 狀態

        修復: 直接信任 is_websocket_service_running() 的結果
        該方法已經檢查了 heartbeat（15秒閾值），避免 transaction isolation 問題
        """
        from .common.websocket_thread_manager import is_websocket_service_running
        import os

        for record in self:
            try:
                # 檢查該實例的 WebSocket 服務是否在運行（透過 heartbeat）
                # is_websocket_service_running() 使用獨立的 DB cursor，
                # 能看到最新的 heartbeat 數據（避免 transaction isolation）
                is_running = is_websocket_service_running(
                    env=self.env,
                    instance_id=record.id
                )

                if is_running:
                    record.websocket_status = 'connected'
                    _logger.info(
                        f"[PID {os.getpid()}] ✅ Instance {record.id} ({record.name}): Connected"
                    )
                else:
                    record.websocket_status = 'disconnected'
                    _logger.info(
                        f"[PID {os.getpid()}] ❌ Instance {record.id} ({record.name}): Disconnected"
                    )

            except Exception as e:
                _logger.error(f"Failed to compute WebSocket status for instance {record.id}: {e}")
                record.websocket_status = 'error'

    # ==================== Constraints ====================

    @api.constrains('api_url')
    def _check_api_url_format(self):
        """檢查 API URL 格式"""
        for record in self:
            if record.api_url:
                url = record.api_url.strip()
                if not (url.startswith('http://') or url.startswith('https://')):
                    raise ValidationError(
                        _("Invalid API URL format: %s\n"
                          "URL must start with http:// or https://") % url
                    )

    # ==================== CRUD Overrides ====================

    @api.model_create_multi
    def create(self, vals_list):
        """創建實例時的處理"""
        instances = super(HAInstance, self).create(vals_list)

        # 自動計算並設置 fingerprint
        for instance in instances:
            if instance.api_url:
                fingerprint = instance._compute_instance_fingerprint()
                if fingerprint:
                    # 使用 with_context 設置 flag 避免觸發 write() 的 fingerprint 更新邏輯
                    instance.with_context(skip_fingerprint_update=True).write({
                        'ha_instance_uuid': fingerprint,
                        'last_api_url': instance.api_url
                    })
                    _logger.debug(f"Set initial fingerprint for instance {instance.id}: {fingerprint[:16]}...")

            _logger.info(f"Created HA instance: {instance.name} (ID: {instance.id})")

        return instances

    def write(self, vals):
        """更新實例時的處理"""
        result = super(HAInstance, self).write(vals)

        # 如果修改了 API URL，自動更新 fingerprint
        # 使用 context flag 避免無限遞迴
        if 'api_url' in vals and not self.env.context.get('skip_fingerprint_update'):
            for record in self:
                if record.api_url:
                    fingerprint = record._compute_instance_fingerprint()
                    if fingerprint:
                        # 使用 with_context 設置 flag 避免無限遞迴
                        record.with_context(skip_fingerprint_update=True).write({
                            'ha_instance_uuid': fingerprint,
                            'last_api_url': record.api_url
                        })
                        _logger.info(f"Updated fingerprint for instance {record.id} ({record.name}): {fingerprint[:16]}...")

        # 如果修改了 API URL 或 Token，標記需要重新連接 WebSocket
        if 'api_url' in vals or 'api_token' in vals:
            for record in self:
                _logger.info(f"HA instance configuration changed: {record.name}")
                # TODO: 觸發 WebSocket 重新連接
                # record.restart_websocket_connection()

        return result

    def unlink(self):
        """刪除實例前的檢查"""
        db_name = self.env.cr.dbname
        instance_ids_to_delete = []

        for record in self:
            # 檢查是否有關聯的實體
            entity_count = self.env['ha.entity'].search_count([
                ('ha_instance_id', '=', record.id)
            ])
            if entity_count > 0:
                raise ValidationError(
                    _("Cannot delete instance '%s' because it has %d associated entities.\n"
                      "Please delete all associated entities first.") % (record.name, entity_count)
                )

            instance_ids_to_delete.append(record.id)
            _logger.info(f"Deleting HA instance: {record.name} (ID: {record.id})")

        result = super(HAInstance, self).unlink()

        # 清除已刪除實例的心跳參數
        for instance_id in instance_ids_to_delete:
            heartbeat_key = f'odoo_ha_addon.ws_heartbeat_{db_name}_instance_{instance_id}'
            self.env['ir.config_parameter'].sudo().search([
                ('key', '=', heartbeat_key)
            ]).unlink()
            _logger.info(f"Cleared heartbeat parameter: {heartbeat_key}")

        return result

    # ==================== Business Methods ====================

    def _compute_instance_fingerprint(self):
        """
        計算 HA 實例的唯一指紋（fingerprint）

        使用 API URL 的 SHA256 hash 作為唯一識別碼。
        當 URL 改變時，fingerprint 也會改變，用於檢測實例變更。

        Returns:
            str: 64 字元的 hex hash，若無 URL 則返回 None

        Security:
            - 移除 URL 中的危險字元（null bytes, 控制字符）
            - 驗證 URL 格式合法性
            - 限制 URL 長度防止 DoS

        範例：
            http://homeassistant.local:8123 → 'a1b2c3d4...'
        """
        import hashlib
        import re

        self.ensure_one()

        if not self.api_url:
            return None

        # 安全性：移除 null bytes 和控制字符
        url = self.api_url.replace('\x00', '').strip()

        # 安全性：移除控制字符（ASCII 0-31 和 127）
        url = re.sub(r'[\x00-\x1f\x7f]', '', url)

        # 安全性：限制 URL 長度（防止 DoS）
        # Note: We raise an error instead of silently truncating, as truncated URLs
        # are almost certainly invalid and would cause confusing errors later.
        if len(url) > 2048:
            _logger.error(f"API URL too long ({len(url)} chars), maximum allowed is 2048")
            raise ValidationError(
                _("API URL is too long (%d characters). Maximum allowed is 2048 characters.") % len(url)
            )

        # 驗證 URL 格式（基本檢查）
        if not url.startswith(('http://', 'https://')):
            _logger.error(f"Invalid API URL format: {url[:100]}...")
            return None

        # 正規化 URL（移除末尾斜線、轉小寫、移除協議差異）
        url = url.rstrip('/').lower()

        # 移除協議前綴，只保留 host:port 部分
        # 這樣 http:// 和 https:// 指向同一個 host 會被視為同一個實例
        for prefix in ['https://', 'http://']:
            if url.startswith(prefix):
                url = url[len(prefix):]
                break

        # 計算 SHA256 hash
        fingerprint = hashlib.sha256(url.encode('utf-8')).hexdigest()

        _logger.debug(f"Computed fingerprint for {self.api_url}: {fingerprint[:16]}...")

        return fingerprint

    @api.model
    def get_accessible_instances(self, user_id=None):
        """
        取得當前用戶可存取的實例列表

        透過 Entity Groups 的權限控制自動過濾可訪問的實例。
        用戶可以訪問其 ha_entity_group_ids 所關聯的實例。

        Args:
            user_id: 用戶 ID（可選，預設為當前用戶）

        Returns:
            recordset: 可存取的 HA 實例列表
        """
        if user_id is None:
            user = self.env.user
        else:
            user = self.env['res.users'].browse(user_id)

        # 查找條件：實例必須啟用 (active=True)
        # ir.rule 會自動過濾用戶可訪問的實例（透過 ha_entity_group_ids）
        instances = self.with_user(user).search([
            ('active', '=', True)
        ], order='sequence, name')

        _logger.debug(f"User {user.id} has access to {len(instances)} HA instances (via entity groups)")

        return instances

    def get_default_instance(self):
        """
        取得第一個可存取的實例（按 sequence, name 排序）

        Returns:
            record: 第一個可存取的實例，如果沒有則返回空 recordset
        """
        # 返回第一個可存取的實例
        accessible = self.get_accessible_instances()
        if accessible:
            return accessible[0]

        return self.browse()

    def test_connection(self):
        """
        測試與 Home Assistant 的 WebSocket 連接

        Returns:
            dict: 測試結果 {success: bool, message: str, data: dict}
        """
        self.ensure_one()

        try:
            import asyncio
            import websockets
            import json

            async def test_websocket():
                """異步測試 WebSocket 連接"""
                # 計算 WebSocket URL
                api_url = self.api_url.rstrip('/')
                if api_url.startswith('https://'):
                    ws_url = api_url.replace('https://', 'wss://') + '/api/websocket'
                elif api_url.startswith('http://'):
                    ws_url = api_url.replace('http://', 'ws://') + '/api/websocket'
                else:
                    return {
                        'success': False,
                        'message': f'Invalid API URL format: {api_url}',
                        'data': {}
                    }

                _logger.info(f"Testing WebSocket connection to: {ws_url}")

                try:
                    # 連接到 WebSocket（10秒超時）
                    async with websockets.connect(ws_url, ping_interval=None, close_timeout=5) as websocket:
                        # 1. 接收 auth_required 訊息
                        auth_required = await asyncio.wait_for(websocket.recv(), timeout=5)
                        auth_msg = json.loads(auth_required)

                        _logger.info(f"Received auth_required: {auth_msg}")

                        if auth_msg.get('type') != 'auth_required':
                            return {
                                'success': False,
                                'message': f"Expected auth_required, got {auth_msg.get('type')}",
                                'data': {}
                            }

                        ha_version = auth_msg.get('ha_version', 'Unknown')

                        # 2. 發送認證
                        auth_payload = {
                            'type': 'auth',
                            'access_token': self.api_token
                        }
                        await websocket.send(json.dumps(auth_payload))

                        # 3. 接收認證結果
                        auth_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                        auth_result = json.loads(auth_response)

                        _logger.info(f"Auth result: {auth_result}")

                        if auth_result.get('type') == 'auth_ok':
                            return {
                                'success': True,
                                'message': 'WebSocket connection and authentication successful',
                                'data': {
                                    'version': ha_version,
                                    'websocket_url': ws_url
                                }
                            }
                        else:
                            return {
                                'success': False,
                                'message': f"Authentication failed: {auth_result.get('message', 'Unknown error')}",
                                'data': {}
                            }

                except asyncio.TimeoutError:
                    return {
                        'success': False,
                        'message': 'Connection timeout (10 seconds)',
                        'data': {}
                    }
                except websockets.exceptions.WebSocketException as e:
                    return {
                        'success': False,
                        'message': f'WebSocket error: {str(e)}',
                        'data': {}
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'message': f'Connection error: {str(e)}',
                        'data': {}
                    }

            # 運行異步測試
            result = asyncio.run(test_websocket())

            _logger.info(f"Connection test result for {self.name}: {result}")
            return result

        except Exception as e:
            _logger.error(f"Failed to test HA connection: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'data': {}
            }

    def action_test_connection(self):
        """
        按鈕動作：測試連接
        在 Form view 中使用

        Phase X: 檢查 HA Instance Fingerprint，警告用戶 URL 是否已變更

        Note: 此方法只測試連接，不會寫入資料庫。
              Fingerprint 會在 Save 時自動更新（透過 write() 方法）。
        """
        self.ensure_one()

        # 計算當前 URL 的 fingerprint
        new_fingerprint = self._compute_instance_fingerprint()

        # 測試連接
        result = self.test_connection()

        if result['success']:
            # 取得版本資訊
            version = result.get('data', {}).get('version', 'Unknown') if result.get('data') else 'Unknown'

            # 檢查 URL 是否改變（fingerprint 不同）
            url_changed = False
            old_url = self.last_api_url
            old_fingerprint = self.ha_instance_uuid

            if self.ha_instance_uuid and new_fingerprint and self.ha_instance_uuid != new_fingerprint:
                url_changed = True
                _logger.info(
                    f"Instance {self.id} ({self.name}) URL change detected (will update on save):\n"
                    f"  Old URL: {old_url}\n"
                    f"  New URL: {self.api_url}\n"
                    f"  Old Fingerprint: {old_fingerprint[:16] if old_fingerprint else 'None'}...\n"
                    f"  New Fingerprint: {new_fingerprint[:16]}..."
                )

            # 如果 URL 改變，顯示警告（但不寫入資料庫）
            if url_changed:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('⚠️ API URL Changed'),
                        'message': _("Connection successful!\n\n"
                                   "⚠️ URL change detected:\n"
                                   "Old: %s\n"
                                   "New: %s\n\n"
                                   "If this is a different Home Assistant instance, it is recommended to clear old data to avoid data confusion.\n"
                                   "Please use the 'Clear Instance Data' button.\n\n"
                                   "If this is just a URL change (e.g., from HTTP to HTTPS), no need to clear data.\n\n"
                                   "⚠️ Please click SAVE to confirm the URL change.\n"
                                   "Fingerprint will be updated automatically on save.") % (
                                       old_url or 'Unknown',
                                       self.api_url
                                   ),
                        'type': 'warning',
                        'sticky': True,
                    }
                }

            # URL 沒有改變，顯示成功訊息
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('✓ Connection Successful'),
                    'message': _("Connected to Home Assistant %s") % version,
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('✗ Connection Failed'),
                    'message': result['message'],
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def action_sync_registry(self):
        """
        按鈕動作：同步 Registry（Labels, Areas, Devices）
        從 Home Assistant 同步所有 Labels, Areas, Devices 到 Odoo

        執行順序（有相依性）：
        1. Labels（Area/Device 需要 Label 存在）
        2. Areas（Device 需要 Area 存在）
        3. Devices
        """
        self.ensure_one()

        try:
            _logger.info(f"=== Starting registry sync for instance: {self.name} (ID: {self.id}) ===")

            # Step 1: Sync Labels
            _logger.info("Step 1: Syncing Labels...")
            self.env['ha.label'].sudo().sync_labels_from_ha(instance_id=self.id)
            label_count = self.env['ha.label'].sudo().search_count([
                ('ha_instance_id', '=', self.id)
            ])

            # Step 2: Sync Areas
            _logger.info("Step 2: Syncing Areas...")
            self.env['ha.area'].sudo().sync_areas_from_ha(instance_id=self.id)
            area_count = self.env['ha.area'].sudo().search_count([
                ('ha_instance_id', '=', self.id)
            ])

            # Step 3: Sync Devices
            _logger.info("Step 3: Syncing Devices...")
            self.env['ha.device'].sudo().sync_devices_from_ha(instance_id=self.id)
            device_count = self.env['ha.device'].sudo().search_count([
                ('ha_instance_id', '=', self.id)
            ])

            _logger.info(f"Registry sync completed for {self.name}")

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Registry Synced'),
                    'message': _("Successfully synced from %s:\n"
                               "• Labels: %d\n"
                               "• Areas: %d\n"
                               "• Devices: %d") % (
                                   self.name,
                                   label_count,
                                   area_count,
                                   device_count
                               ),
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            _logger.error(f"Failed to sync registry for {self.name}: {str(e)}", exc_info=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Registry Sync Failed'),
                    'message': _("Failed to sync registry: %s") % str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def action_sync_entities(self):
        """
        按鈕動作：同步實體
        從 Home Assistant 同步所有實體到 Odoo（包含 Entity-Area 關聯）

        Phase 3: 支援多實例，自動同步 Entity-Area 關聯
        """
        self.ensure_one()

        try:
            _logger.info(f"=== Starting entity sync for instance: {self.name} (ID: {self.id}) ===")

            # 調用 sync_entity_states_from_ha 方法
            # sync_area_relations=True 會自動同步 Entity-Area 關聯
            # Note: 不使用 cr.commit()，讓 Odoo ORM 自動管理 transaction
            # sudo: 系統層級同步，需要建立/更新所有用戶可見的 entities
            self.env['ha.entity'].sudo().sync_entity_states_from_ha(
                instance_id=self.id,
                sync_area_relations=True
            )

            # 更新 last_sync_date
            self.write({'last_sync_date': fields.Datetime.now()})

            # 讀取同步後的 entities 數量
            # sudo: 統計所有 entities，不受用戶權限限制
            entity_count = self.env['ha.entity'].sudo().search_count([
                ('ha_instance_id', '=', self.id)
            ])

            _logger.info(f"Entity sync completed for {self.name}: {entity_count} entities")

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Entities Synced',
                    'message': f"Successfully synced {entity_count} entities from {self.name}",
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            _logger.error(f"Failed to sync entities for {self.name}: {str(e)}", exc_info=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Entity Sync Failed',
                    'message': f"Failed to sync entities: {str(e)}",
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def action_sync_history(self):
        """
        按鈕動作：同步歷史數據
        從 Home Assistant 同步已啟用實體的歷史數據（近 1 天）

        只同步 enable_record=True 的實體
        """
        self.ensure_one()

        try:
            _logger.info(f"=== Starting history sync for instance: {self.name} (ID: {self.id}) ===")

            # 檢查是否有啟用記錄的實體
            # sudo: 統計所有啟用的 entities，不受用戶權限限制
            enabled_count = self.env['ha.entity'].sudo().search_count([
                ('ha_instance_id', '=', self.id),
                ('enable_record', '=', True)
            ])

            if enabled_count == 0:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'No Entities Enabled',
                        'message': f"No entities are enabled for history recording in {self.name}. "
                                   f"Please enable entities first.",
                        'type': 'warning',
                        'sticky': False,
                    }
                }

            # 調用 sync_entity_history_from_ha 標準方法，傳入當前實例 ID
            # Phase 4 完成：已支援 instance_id 參數，只同步該實例的實體
            # Note: 不使用 cr.commit()，讓 Odoo ORM 自動管理 transaction
            # sudo: 系統層級同步，需要寫入所有用戶可見的歷史記錄
            self.env['ha.entity.history'].sudo().sync_entity_history_from_ha(instance_id=self.id)

            # 讀取此實例的歷史記錄數量
            # sudo: 統計所有歷史記錄，不受用戶權限限制
            history_count = self.env['ha.entity.history'].sudo().search_count([
                ('entity_id.ha_instance_id', '=', self.id)
            ])

            _logger.info(f"History sync completed for {self.name}: {history_count} records")

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'History Synced',
                    'message': f"Successfully synced history for {enabled_count} entities from {self.name}. "
                               f"Total {history_count} history records.",
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            _logger.error(f"Failed to sync history for {self.name}: {str(e)}", exc_info=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'History Sync Failed',
                    'message': f"Failed to sync history: {str(e)}",
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def action_restart_websocket(self):
        """
        按鈕動作：重啟 WebSocket 服務

        Phase 2: 支援多實例重啟
        - 可以在 Form view 中單獨重啟一個實例
        - 可以在 List view 中多選實例批次重啟

        Returns:
            dict: ir.actions.client notification
        """
        from .common.websocket_thread_manager import restart_websocket_service

        success_count = 0
        failed_instances = []
        total_count = len(self)

        _logger.info(f"Restarting WebSocket service for {total_count} instance(s)")

        for instance in self:
            try:
                _logger.info(f"Restarting WebSocket for instance {instance.id}: {instance.name}")

                # Phase 2: 重啟特定實例
                result = restart_websocket_service(
                    env=self.env,
                    instance_id=instance.id,
                    force=True  # 強制重啟
                )

                if result.get('success'):
                    success_count += 1
                    _logger.info(f"Successfully restarted WebSocket for instance {instance.id}")
                else:
                    error_msg = result.get('message', 'Unknown error')
                    failed_instances.append(f"{instance.name} ({error_msg})")
                    _logger.warning(f"Failed to restart WebSocket for instance {instance.id}: {error_msg}")

            except Exception as e:
                error_str = str(e)
                failed_instances.append(f"{instance.name} (Exception: {error_str})")
                _logger.error(f"Exception while restarting WebSocket for instance {instance.id}: {error_str}")

        # 構建通知訊息
        if total_count == 1:
            # 單一實例
            if success_count == 1:
                message = f"WebSocket 服務已重啟：{self.name}"
                title = 'WebSocket 重啟成功'
                msg_type = 'success'
            else:
                message = f"重啟失敗：{failed_instances[0]}"
                title = 'WebSocket 重啟失敗'
                msg_type = 'danger'
        else:
            # 多個實例
            title = 'WebSocket 批次重啟結果'
            message = f"成功重啟 {success_count}/{total_count} 個實例"

            if failed_instances:
                message += f"\n\n失敗的實例：\n" + "\n".join(f"• {name}" for name in failed_instances)
                msg_type = 'warning' if success_count > 0 else 'danger'
            else:
                msg_type = 'success'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': msg_type,
                'sticky': len(failed_instances) > 0,  # 有失敗時保持顯示
            }
        }

    def get_websocket_config(self):
        """
        取得此實例的 WebSocket 配置

        Returns:
            dict: WebSocket 配置 {url: str, token: str}
        """
        self.ensure_one()

        return {
            'url': self.ws_url,
            'token': self.api_token,
            'instance_id': self.id,
            'instance_name': self.name
        }

    def _clear_instance_data(self):
        """
        清除此實例的所有關聯資料

        清除順序（遵循外鍵依賴關係）：
        1. ha.entity.history (依賴 ha.entity)
        2. ha.entity.group.tag (依賴 ha.entity.group)
        3. ha.entity.group (依賴 ha.entity, ha.instance)
        4. ha.entity.tag (Many2many 關聯 ha.entity)
        5. ha.entity (依賴 ha.device, ha.area, ha.label, ha.instance)
        6. ha.device (依賴 ha.area, ha.label, ha.instance)
        7. ha.label (被 device/area/entity 參照，ha.instance)
        8. ha.area (依賴 ha.instance)
        9. ha.ws.request.queue (依賴 ha.instance)

        ⚠️ 此操作不可逆！
        """
        self.ensure_one()

        _logger.warning(f"=== 開始清除實例資料: {self.name} (ID: {self.id}) ===")

        # sudo: 批次刪除需要完整存取權限，繞過用戶的 ir.rule 限制
        # 使用特殊 context 來避免觸發 compute fields 和其他副作用
        # from_ha_sync: 避免觸發雙向同步到 HA
        ctx = {
            'active_test': False,  # 包含已停用的記錄
            'tracking_disable': True,  # 停用追蹤
            'mail_notrack': True,  # 停用郵件追蹤
            'no_recompute': True,  # 停用自動重新計算
            'from_ha_sync': True,  # 避免同步回 HA
        }

        try:
            # 1. 清除歷史記錄
            history_records = self.env['ha.entity.history'].with_context(**ctx).sudo().search([
                ('entity_id.ha_instance_id', '=', self.id)
            ])
            history_count = len(history_records)
            if history_count > 0:
                history_records.unlink()
            _logger.info(f"✓ 已刪除 {history_count} 筆歷史記錄")

            # 2. 清除 Entity Group Tags
            group_tag_records = self.env['ha.entity.group.tag'].with_context(**ctx).sudo().search([
                ('ha_instance_id', '=', self.id)
            ])
            group_tag_count = len(group_tag_records)
            if group_tag_count > 0:
                group_tag_records.unlink()
            _logger.info(f"✓ 已刪除 {group_tag_count} 筆 Entity Group Tags")

            # 3. 清除 Entity Groups
            group_records = self.env['ha.entity.group'].with_context(**ctx).sudo().search([
                ('ha_instance_id', '=', self.id)
            ])
            group_count = len(group_records)
            if group_count > 0:
                group_records.unlink()
            _logger.info(f"✓ 已刪除 {group_count} 筆 Entity Groups")

            # 4. 清除 Entity Tags (Odoo 側標籤)
            entity_tag_records = self.env['ha.entity.tag'].with_context(**ctx).sudo().search([
                ('ha_instance_id', '=', self.id)
            ])
            entity_tag_count = len(entity_tag_records)
            if entity_tag_count > 0:
                entity_tag_records.unlink()
            _logger.info(f"✓ 已刪除 {entity_tag_count} 筆 Entity Tags")

            # 5. 清除 Entities
            entity_records = self.env['ha.entity'].with_context(**ctx).sudo().search([
                ('ha_instance_id', '=', self.id)
            ])
            entity_count = len(entity_records)
            if entity_count > 0:
                entity_records.unlink()
            _logger.info(f"✓ 已刪除 {entity_count} 筆 Entities")

            # 6. 清除 Devices (HA 設備)
            device_records = self.env['ha.device'].with_context(**ctx).sudo().search([
                ('ha_instance_id', '=', self.id)
            ])
            device_count = len(device_records)
            if device_count > 0:
                device_records.unlink()
            _logger.info(f"✓ 已刪除 {device_count} 筆 Devices")

            # 7. 清除 Labels (HA 標籤)
            label_records = self.env['ha.label'].with_context(**ctx).sudo().search([
                ('ha_instance_id', '=', self.id)
            ])
            label_count = len(label_records)
            if label_count > 0:
                label_records.unlink()
            _logger.info(f"✓ 已刪除 {label_count} 筆 Labels")

            # 8. 清除 Areas
            area_records = self.env['ha.area'].with_context(**ctx).sudo().search([
                ('ha_instance_id', '=', self.id)
            ])
            area_count = len(area_records)
            if area_count > 0:
                area_records.unlink()
            _logger.info(f"✓ 已刪除 {area_count} 筆 Areas")

            # 9. 清除 WebSocket Queue
            queue_records = self.env['ha.ws.request.queue'].with_context(**ctx).sudo().search([
                ('ha_instance_id', '=', self.id)
            ])
            queue_count = len(queue_records)
            if queue_count > 0:
                queue_records.unlink()
            _logger.info(f"✓ 已刪除 {queue_count} 筆 WebSocket Queue")

            # 清除 UUID 和 last_api_url（重置追蹤）
            self.write({
                'ha_instance_uuid': False,
                'last_api_url': False,
                'last_sync_date': False
            })

            total_count = (history_count + group_tag_count + group_count + entity_tag_count +
                          entity_count + device_count + label_count + area_count + queue_count)

            _logger.warning(f"=== 實例資料清除完成: {self.name} ===")
            _logger.info(f"總計刪除: {total_count} 筆記錄")

            return {
                'success': True,
                'deleted': {
                    'history': history_count,
                    'group_tags': group_tag_count,
                    'groups': group_count,
                    'entity_tags': entity_tag_count,
                    'entities': entity_count,
                    'devices': device_count,
                    'labels': label_count,
                    'areas': area_count,
                    'queue': queue_count
                }
            }

        except Exception as e:
            _logger.error(f"清除實例資料失敗: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def action_clear_data(self):
        """
        按鈕動作：清除實例資料

        提供確認對話框後清除此實例的所有關聯資料
        適用於：
        1. URL 改變後指向不同的 HA 實例
        2. 需要重新同步資料
        3. 資料損壞需要重置

        ⚠️ 此操作不可逆！
        """
        self.ensure_one()

        # 返回確認 wizard
        return {
            'name': _('Confirm Clear Instance Data'),
            'type': 'ir.actions.act_window',
            'res_model': 'ha.instance.clear.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_instance_id': self.id,
                'default_instance_name': self.name,
            }
        }

    def action_create_and_select(self):
        """
        建立 Instance 後關閉 modal 並刷新頁面

        此方法用於 modal form view 的 Create 按鈕。
        建立後會關閉 modal 並重新載入 Settings 頁面，
        新建的 instance 會自動被選擇。
        """
        self.ensure_one()

        _logger.info(f"Created HA instance via modal: {self.name} (ID: {self.id})")

        # 關閉 modal 並重新打開 Settings 頁面，自動選擇新建的 instance
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.config.settings',
            'view_mode': 'form',
            'target': 'inline',
            'context': {
                'active_model': 'ha.instance',
                'active_id': self.id,
            }
        }

    @api.model
    def action_open_create_modal(self):
        """
        返回打開新建 Instance Modal 的 action

        此方法可從 JavaScript 呼叫，用於在 Dashboard 等頁面
        打開與 Settings 頁面 "+ New Instance" 按鈕相同的簡易 Modal Form。

        Returns:
            dict: ir.actions.act_window action

        Raises:
            AccessError: 如果使用者不是 HA Manager
        """
        # 權限檢查：只有 HA Manager 可以建立新實例
        if not self.env.user.has_group('odoo_ha_addon.group_ha_manager'):
            raise AccessError(_('只有 Home Assistant 管理者可以建立新實例'))

        view_id = self.env.ref('odoo_ha_addon.view_ha_instance_form_modal').id
        return {
            'name': _('New Home Assistant Instance'),
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
