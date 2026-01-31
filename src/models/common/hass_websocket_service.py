import asyncio
import json
import logging
import time
from typing import List, Dict, Optional, Any
# Note: websockets is imported lazily in connect_and_listen() to allow auto-installation
from datetime import datetime
from odoo import api
from odoo.service import db
import traceback

class HassWebSocketService:
    """
    Home Assistant WebSocket 服務
    處理與 Home Assistant 的即時 WebSocket 連線

    Phase 2 重構：支援多 HA 實例
    - 移除單例模式限制
    - 每個實例獨立管理 WebSocket 連接
    """

    def __init__(self, env=None, db_name=None, ha_url=None, ha_token=None, instance_id=None):
        """
        初始化 WebSocket 服務

        支援兩種初始化方式:
        1. 傳入 env + instance_id (從 Odoo 環境初始化，從 ha.instance 讀取配置)
        2. 傳入 db_name, ha_url, ha_token, instance_id (從 threading 環境初始化)

        Args:
            env: Odoo environment (可選)
            db_name: 資料庫名稱 (threading 模式必需)
            ha_url: HA API URL (threading 模式必需)
            ha_token: HA Access Token (threading 模式必需)
            instance_id: HA Instance ID (必需，用於多實例支援)
        """
        self.env = env
        self.instance_id = instance_id  # ← 新增：實例 ID

        if env is not None:
            self.db_name = env.cr.dbname
            # 從 ha.instance 模型讀取配置（而非全局配置）
            self.ha_url = None  # 稍後從 ha.instance 取得
            self.ha_token = None  # 稍後從 ha.instance 取得
        else:
            # Threading 模式：直接使用傳入的參數
            self.db_name = db_name
            self.ha_url = ha_url
            self.ha_token = ha_token

        self._logger = logging.getLogger(__name__)
        self._running = False
        self._websocket = None
        self._message_id = 1
        self._pending_requests = {}  # {message_id: asyncio.Future}

        # 訂閱管理
        self._subscriptions = {}  # {message_id: {'request_id': str, 'subscription_id': int}}

        # 訂閱清理機制（防止 stale subscriptions 堆積）
        self._last_subscription_cleanup = 0  # 上次清理時間
        self._subscription_cleanup_interval = 30  # 清理間隔（秒）

        # 連線重試機制
        self._consecutive_failures = 0  # 連續失敗次數
        self._max_retries = 5  # 最大重試次數
        self._retry_delays = [5, 10, 15, 30, 60]  # 每次重試的等待時間（秒）

        # Area sync debounce 機制
        self._pending_area_syncs: dict = {}  # {area_id: asyncio.Task}
        self._area_sync_debounce_delay = 0.5  # 500ms

        # Area sync timeout 常數
        self._area_list_timeout = 15  # 取得 area list 的 timeout（秒）
        self._area_create_timeout = 10  # 建立 area 的 timeout（秒）

        # Device sync debounce 機制
        self._pending_device_syncs: dict = {}  # {device_id: asyncio.Task}
        self._device_sync_debounce_delay = 0.5  # 500ms

        # Device sync timeout 常數
        self._device_list_timeout = 15  # 取得 device list 的 timeout（秒）

    async def _run_sync(self, func, *args):
        """
        在 executor 中執行同步方法

        用於在 async context 中執行阻塞的同步操作（如資料庫操作）

        Args:
            func: 要執行的同步函數
            *args: 傳給函數的參數

        Returns:
            函數的返回值
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)

    def get_websocket_url(self) -> Optional[str]:
        """
        從 HA Instance 配置推導 WebSocket URL
        Phase 2: 從 ha.instance 模型讀取，而非全局配置
        例: http://192.168.1.100:8123/ -> ws://192.168.1.100:8123/api/websocket
        """
        # 優先使用已設定的 ha_url，否則從 ha.instance 取得
        if self.ha_url:
            ha_url = self.ha_url
        elif self.env and self.instance_id:
            # Phase 2: 從 ha.instance 模型讀取特定實例的 URL
            try:
                instance = self.env['ha.instance'].sudo().browse(self.instance_id)
                if not instance.exists():
                    self._logger.error(f"HA instance {self.instance_id} not found")
                    return None
                ha_url = instance.api_url
            except Exception as e:
                self._logger.error(f"Failed to read HA instance config: {e}")
                return None
        else:
            self._logger.error(f"No HA URL available (env={self.env}, instance_id={self.instance_id}, ha_url={self.ha_url})")
            return None

        if not ha_url:
            self._logger.error(f"Home Assistant API URL not configured for instance {self.instance_id}")
            return None

        # 轉換 HTTP/HTTPS 到 WS/WSS
        if ha_url.startswith('https://'):
            ws_url = ha_url.replace('https://', 'wss://')
        elif ha_url.startswith('http://'):
            ws_url = ha_url.replace('http://', 'ws://')
        else:
            self._logger.error(f"Invalid HA URL format: {ha_url}")
            return None

        # 確保 URL 以 / 結尾，然後加入 WebSocket 端點
        ws_url = ws_url.rstrip('/') + '/api/websocket'
        self._logger.info(f"WebSocket URL (instance {self.instance_id}): {ws_url}")
        return ws_url

    def get_access_token(self) -> Optional[str]:
        """
        取得 Home Assistant 存取權杖
        Phase 2: 從 ha.instance 模型讀取，而非全局配置

        Returns:
            str: HA Access Token，或 None（配置錯誤時）
        """
        # 優先使用已設定的 ha_token，否則從 ha.instance 取得
        if self.ha_token:
            return self.ha_token
        elif self.env and self.instance_id:
            # Phase 2: 從 ha.instance 模型讀取特定實例的 Token
            try:
                instance = self.env['ha.instance'].sudo().browse(self.instance_id)
                if not instance.exists():
                    self._logger.error(f"HA instance {self.instance_id} not found")
                    return None
                token = instance.api_token
                if not token:
                    self._logger.error(f"Home Assistant API token not configured for instance {self.instance_id}")
                return token
            except Exception as e:
                self._logger.error(f"Failed to read HA instance token: {e}")
                return None
        else:
            self._logger.error(f"No HA token available (env={self.env}, instance_id={self.instance_id}, ha_token={self.ha_token})")
            return None

    def get_heartbeat_interval(self) -> int:
        """
        取得 WebSocket 心跳間隔（秒）
        從 ir.config_parameter 讀取配置值，無配置時使用默認值 10 秒

        Returns:
            int: 心跳間隔秒數（1-60 之間）
        """
        default_interval = 10

        try:
            # 使用新的資料庫連線讀取配置
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})
                interval_str = env['ir.config_parameter'].sudo().get_param(
                    'odoo_ha_addon.ha_ws_heartbeat_interval',
                    default=str(default_interval)
                )

                try:
                    interval = int(interval_str)

                    # 驗證範圍：1-60 秒
                    if interval < 1 or interval > 60:
                        self._logger.warning(
                            f"Heartbeat interval {interval} out of range (1-60), using default {default_interval}s"
                        )
                        return default_interval

                    return interval

                except (ValueError, TypeError):
                    self._logger.warning(
                        f"Invalid heartbeat interval value '{interval_str}', using default {default_interval}s"
                    )
                    return default_interval

        except Exception as e:
            self._logger.error(f"Failed to get heartbeat interval: {e}, using default {default_interval}s")
            return default_interval

    async def connect_and_listen(self) -> None:
        """
        主要的 WebSocket 連線和監聽邏輯
        包含重試機制：最多重試 5 次，連線成功後重置計數器
        """
        # Lazy import: websockets is auto-installed by pre_init_hook
        import websockets

        ws_url = self.get_websocket_url()
        token = self.get_access_token()

        if not ws_url or not token:
            self._logger.error("WebSocket configuration incomplete")
            return

        self._running = True
        self._logger.info("Starting WebSocket service...")

        while self._running and self._consecutive_failures < self._max_retries:
            try:
                self._logger.info(
                    f"Connecting to WebSocket: {ws_url} "
                    f"(attempt {self._consecutive_failures + 1}/{self._max_retries})"
                )
                async with websockets.connect(ws_url) as websocket:
                    self._websocket = websocket

                    # 執行 Home Assistant WebSocket 認證流程
                    if await self._authenticate(websocket, token):
                        self._logger.info("WebSocket authentication successful")

                        # ✓ 連線成功，重置失敗計數器
                        self._consecutive_failures = 0

                        # 🔔 通知前端：WebSocket 連線成功
                        await self._run_sync(
                            self._notify_status_with_env,
                            'connected',
                            'WebSocket connected successfully'
                        )

                        # 訂閱狀態變更事件
                        await self._subscribe_to_events(websocket)

                        # 啟動背景任務
                        queue_task = asyncio.create_task(self._process_request_queue())
                        heartbeat_task = asyncio.create_task(self._heartbeat_loop())

                        # 主要任務：監聽 WebSocket 訊息
                        try:
                            await self._listen_messages(websocket)
                        finally:
                            # WebSocket 斷線時取消背景任務
                            queue_task.cancel()
                            heartbeat_task.cancel()
                            try:
                                await queue_task
                            except asyncio.CancelledError:
                                pass
                            try:
                                await heartbeat_task
                            except asyncio.CancelledError:
                                pass
                    else:
                        self._logger.error("WebSocket authentication failed")
                        self._consecutive_failures += 1

                        # 🔔 通知前端：認證失敗
                        await self._run_sync(
                            self._notify_status_with_env,
                            'disconnected',
                            'WebSocket authentication failed'
                        )

            except websockets.exceptions.ConnectionClosed:
                self._consecutive_failures += 1
                self._logger.warning(
                    f"WebSocket connection closed (failure {self._consecutive_failures}/{self._max_retries})"
                )

                # 🔔 通知前端：連線關閉
                await self._run_sync(
                    self._notify_status_with_env,
                    'disconnected',
                    f'Connection closed (attempt {self._consecutive_failures}/{self._max_retries})'
                )

            except Exception as e:
                self._consecutive_failures += 1
                self._logger.error(
                    f"WebSocket error (failure {self._consecutive_failures}/{self._max_retries}): {e}"
                )

                # 🔔 通知前端：連線錯誤
                await self._run_sync(
                    self._notify_status_with_env,
                    'error',
                    f'Connection error: {str(e)}'
                )
            finally:
                self._websocket = None

                # 檢查是否達到重試上限
                if self._consecutive_failures >= self._max_retries:
                    error_msg = (
                        f"WebSocket service stopped after {self._max_retries} consecutive failures. "
                        f"Please check your Home Assistant configuration and restart the service."
                    )
                    self._logger.error(error_msg)

                    # 🔔 通知前端：達到最大重試次數，服務停止
                    await self._run_sync(
                        self._notify_status_with_env,
                        'error',
                        f'Service stopped after {self._max_retries} failures'
                    )

                    self._running = False
                    break

                # 如果還在運行且未達上限，等待後重試
                if self._running and self._consecutive_failures < self._max_retries:
                    # 使用遞增的延遲時間
                    delay_index = min(self._consecutive_failures - 1, len(self._retry_delays) - 1)
                    retry_delay = self._retry_delays[delay_index]
                    self._logger.info(f"Retrying in {retry_delay} seconds...")

                    # 🔔 通知前端：重新連線中
                    await self._run_sync(
                        self._notify_status_with_env,
                        'reconnecting',
                        f'Reconnecting in {retry_delay} seconds (attempt {self._consecutive_failures + 1}/{self._max_retries})'
                    )

                    await asyncio.sleep(retry_delay)

        if self._consecutive_failures >= self._max_retries:
            self._logger.error(
                f"WebSocket service permanently stopped due to {self._max_retries} consecutive failures"
            )
        else:
            self._logger.info("WebSocket service stopped")

    async def _authenticate(self, websocket, token):
        """
        Home Assistant WebSocket 認證流程
        參考: https://developers.home-assistant.io/docs/api/websocket/
        """
        try:
            # 第一步：接收認證要求
            auth_required = await websocket.recv()
            auth_data = json.loads(auth_required)

            if auth_data.get('type') != 'auth_required':
                self._logger.error(f"Expected auth_required, got: {auth_data}")
                return False

            self._logger.info(f"HA Version: {auth_data.get('ha_version')}")

            # 第二步：發送認證訊息
            auth_message = {
                'type': 'auth',
                'access_token': token
            }
            await websocket.send(json.dumps(auth_message))

            # 第三步：接收認證結果
            auth_result = await websocket.recv()
            result_data = json.loads(auth_result)

            if result_data.get('type') == 'auth_ok':
                self._logger.info("Authentication successful")
                return True
            else:
                self._logger.error(f"Authentication failed: {result_data}")
                return False

        except Exception as e:
            self._logger.error(f"Authentication error: {e}")
            return False

    async def _subscribe_to_events(self, websocket):
        """
        訂閱 Home Assistant 事件
        """
        try:
            # 訂閱狀態變更事件
            subscribe_message = {
                'id': self._get_next_id(),
                'type': 'subscribe_events',
                'event_type': 'state_changed'
            }
            await websocket.send(json.dumps(subscribe_message))
            self._logger.info("Subscribed to state_changed events")

            # 訂閱設備註冊變更事件（用於 Glances 快取失效）
            device_registry_message = {
                'id': self._get_next_id(),
                'type': 'subscribe_events',
                'event_type': 'device_registry_updated'
            }
            await websocket.send(json.dumps(device_registry_message))
            self._logger.info("Subscribed to device_registry_updated events")

            # 訂閱 Area 註冊變更事件（用於雙向同步）
            area_registry_message = {
                'id': self._get_next_id(),
                'type': 'subscribe_events',
                'event_type': 'area_registry_updated'
            }
            await websocket.send(json.dumps(area_registry_message))
            self._logger.info("Subscribed to area_registry_updated events")

            # 訂閱 Entity 註冊變更事件（用於 entity area_id 雙向同步）
            entity_registry_message = {
                'id': self._get_next_id(),
                'type': 'subscribe_events',
                'event_type': 'entity_registry_updated'
            }
            await websocket.send(json.dumps(entity_registry_message))
            self._logger.info("Subscribed to entity_registry_updated events")

            # 訂閱 Label 註冊變更事件（用於 label 雙向同步）
            label_registry_message = {
                'id': self._get_next_id(),
                'type': 'subscribe_events',
                'event_type': 'label_registry_updated'
            }
            await websocket.send(json.dumps(label_registry_message))
            self._logger.info("Subscribed to label_registry_updated events")

            # 連線成功後，執行初始同步（Label → Area → Device）
            asyncio.create_task(self._initial_label_area_and_device_sync())

        except Exception as e:
            self._logger.error(f"Failed to subscribe to events: {e}")

    async def _listen_messages(self, websocket):
        """
        監聽 WebSocket 訊息
        支援單一訊息或陣列回應
        """
        import websockets

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)

                    # 處理陣列回應（根據文檔，server 可能回傳陣列）
                    # 使用 create_task 讓消息處理非阻塞，避免死鎖
                    # （當消息處理中需要發送請求並等待結果時）
                    if isinstance(data, list):
                        self._logger.debug(f"Received array response with {len(data)} messages")
                        for item in data:
                            asyncio.create_task(self._handle_message(item))
                    else:
                        asyncio.create_task(self._handle_message(data))

                except json.JSONDecodeError:
                    self._logger.error(f"Invalid JSON message: {message}")
                except Exception as e:
                    self._logger.error(f"Error handling message: {e}")

        except websockets.exceptions.ConnectionClosed:
            self._logger.info("WebSocket connection closed during message listening")
        except Exception as e:
            self._logger.error(f"Error in message listening: {e}")

    async def _handle_message(self, data):
        """
        處理接收到的 WebSocket 訊息（單一訊息）
        可能來自陣列或單一回應
        """
        message_type = data.get('type')
        message_id = data.get('id')

        # 印出完整的 data variable debug log（僅在 DEBUG level 啟用時）
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug("=== WebSocket Message Debug ===")
            self._logger.debug(f"Message Type: {message_type}")
            self._logger.debug(f"Message ID: {message_id}")
            self._logger.debug(f"Complete Message Data: {data}")
            self._logger.debug(f"Data Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            if isinstance(data, dict):
                for key, value in data.items():
                    if key in ['result', 'event', 'error']:
                        # 限制大型資料的輸出長度
                        value_str = str(value)
                        if len(value_str) > 500:
                            self._logger.debug(f"  {key}: {value_str[:500]}... (truncated, full length: {len(value_str)})")
                        else:
                            self._logger.debug(f"  {key}: {value}")
                    else:
                        self._logger.debug(f"  {key}: {value}")
            self._logger.debug("=== End WebSocket Message Debug ===")

        # 處理訂閱的 result 訊息
        if message_id is not None and message_id in self._subscriptions:
            if message_type == 'result':
                await self._handle_subscription_result(message_id, data)
                return
            elif message_type == 'event':
                await self._handle_subscription_event(message_id, data)
                return

        # 優先處理請求-回應模式（有 ID 且在 pending 中）
        if message_id is not None and message_id in self._pending_requests:
            future = self._pending_requests.pop(message_id)

            if message_type == 'result':
                if data.get('success', True):
                    future.set_result(data.get('result'))
                    self._logger.debug(f"Request {message_id} completed successfully")
                else:
                    error_info = data.get('error', {})
                    error_msg = error_info.get('message', 'Unknown error')
                    future.set_exception(Exception(error_msg))
                    self._logger.error(f"Request {message_id} failed: {error_msg}")
            else:
                # 非 result 類型但有 ID，記錄但不處理
                self._logger.warning(f"Received unexpected type '{message_type}' for request {message_id}")
            return

        # 處理事件類型訊息（無 ID 或不在 pending 中）
        if message_type == 'event':
            await self._handle_event(data)
        elif message_type == 'result':
            # result 類型但沒有對應的 pending request
            self._logger.debug(f"Received result for unknown/expired request {message_id}: {data}")
        elif message_type == 'pong':
            self._logger.debug("Received pong")
        else:
            self._logger.debug(f"Unhandled message type '{message_type}': {data}")

    async def _handle_subscription_result(self, message_id, data):
        """
        處理訂閱的 result 訊息

        Args:
            message_id: WebSocket 訊息 ID
            data: 訊息數據
        """
        try:
            subscription_info = self._subscriptions.get(message_id)
            if not subscription_info:
                self._logger.warning(f"Subscription {message_id} not found in subscriptions")
                return

            request_id = subscription_info['request_id']

            if data.get('success', True):
                self._logger.info(f"Subscription {request_id} confirmed, message_id={message_id}")

                # 訂閱成功，更新狀態為 subscribed
                await self._run_sync(
                    self._update_subscription_status,
                    request_id,
                    message_id,
                    'subscribed'
                )
            else:
                error_info = data.get('error', {})
                error_msg = error_info.get('message', 'Unknown error')
                self._logger.error(f"Subscription {request_id} failed: {error_msg}")

                # 訂閱失敗
                await self._run_sync(
                    self._subscription_failed,
                    request_id,
                    error_msg
                )

                # 從訂閱列表移除
                if message_id in self._subscriptions:
                    del self._subscriptions[message_id]

        except Exception as e:
            self._logger.error(f"Error handling subscription result: {e}", exc_info=True)

    async def _handle_subscription_event(self, message_id, data):
        """
        處理訂閱的 event 訊息

        Args:
            message_id: WebSocket 訊息 ID
            data: 事件數據
        """
        try:
            subscription_info = self._subscriptions.get(message_id)
            if not subscription_info:
                self._logger.warning(f"Subscription {message_id} not found for event")
                return

            request_id = subscription_info['request_id']
            event_data = data.get('event', {})

            self._logger.debug(f"Received event for subscription {request_id}: {event_data}")

            # 將事件添加到訂閱記錄
            await self._run_sync(
                self._add_event_to_subscription,
                request_id,
                event_data
            )

        except Exception as e:
            self._logger.error(f"Error handling subscription event: {e}", exc_info=True)

    def _update_subscription_status(self, request_id, message_id, status):
        """
        更新訂閱狀態

        Args:
            request_id: 請求 ID
            message_id: WebSocket 訊息 ID
            status: 新狀態
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})

                ws_request = env['ha.ws.request.queue'].sudo().search([
                    ('request_id', '=', request_id)
                ], limit=1)

                if ws_request:
                    ws_request.write({
                        'state': status,
                        'subscription_id': message_id
                    })
                    cr.commit()
                    self._logger.debug(f"Updated subscription {request_id} to status {status}")

        except Exception as e:
            self._logger.error(f"Failed to update subscription status: {e}")

    def _subscription_failed(self, request_id, error_msg):
        """
        標記訂閱失敗

        Args:
            request_id: 請求 ID
            error_msg: 錯誤訊息
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})

                ws_request = env['ha.ws.request.queue'].sudo().search([
                    ('request_id', '=', request_id)
                ], limit=1)

                if ws_request:
                    ws_request.write({
                        'state': 'failed',
                        'error': error_msg
                    })
                    cr.commit()

        except Exception as e:
            self._logger.error(f"Failed to mark subscription as failed: {e}")

    def _add_event_to_subscription(self, request_id, event_data):
        """
        添加事件到訂閱記錄

        Args:
            request_id: 請求 ID
            event_data: 事件數據
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})

                ws_request = env['ha.ws.request.queue'].sudo().search([
                    ('request_id', '=', request_id)
                ], limit=1)

                if ws_request:
                    ws_request.add_event(event_data)
                    cr.commit()
                    self._logger.debug(f"Added event to subscription {request_id}")

        except Exception as e:
            self._logger.error(f"Failed to add event to subscription: {e}")

    async def _handle_event(self, event_data):
        """
        處理 Home Assistant 事件
        """
        try:
            event = event_data.get('event', {})
            event_type = event.get('event_type')

            if event_type == 'state_changed':
                await self._handle_state_changed(event.get('data', {}))
            elif event_type == 'device_registry_updated':
                await self._handle_device_registry_updated(event.get('data', {}))
            elif event_type == 'area_registry_updated':
                await self._handle_area_registry_updated(event.get('data', {}))
            elif event_type == 'entity_registry_updated':
                await self._handle_entity_registry_updated(event.get('data', {}))
            elif event_type == 'label_registry_updated':
                await self._handle_label_registry_updated(event.get('data', {}))
            else:
                self._logger.debug(f"Unhandled event type: {event_type}")

        except Exception as e:
            self._logger.error(f"Error handling event: {e}")

    async def _handle_state_changed(self, state_data):
        """
        處理狀態變更事件
        """
        try:
            entity_id = state_data.get('entity_id')
            new_state = state_data.get('new_state')
            old_state = state_data.get('old_state')

            if not entity_id or not new_state:
                return

            self._logger.debug(f"State changed: {entity_id} -> {new_state.get('state')}")

            # 在新的資料庫連線中更新實體狀態
            await self._update_entity_in_odoo(entity_id, new_state, old_state)

        except Exception as e:
            self._logger.error(f"Error handling state change: {e}")

    async def _handle_device_registry_updated(self, event_data):
        """
        處理設備註冊變更事件
        用於 HA → Odoo 的雙向同步以及前端 Glances 快取失效

        事件格式:
        {
            "action": "create" | "update" | "remove",
            "device_id": "device_id_string"
        }
        """
        try:
            action = event_data.get('action')
            device_id = event_data.get('device_id')

            if not action or not device_id:
                self._logger.warning(f"Invalid device_registry_updated event: {event_data}")
                return

            self._logger.info(
                f"Device registry updated: {action} - {device_id} (instance {self.instance_id})"
            )

            if action == 'remove':
                # 刪除事件：直接在 Odoo 中刪除，然後立即通知前端
                await self._run_sync(
                    self._sync_device_remove_from_ha,
                    device_id
                )
                # Remove 是同步操作，可以立即通知
                await self._run_sync(
                    self._notify_device_registry_update,
                    action,
                    device_id
                )
            elif action in ('create', 'update'):
                # 建立/更新事件：使用 debounce 機制
                # 通知會在 debounce 內部的 sync 完成後發送
                await self._debounced_fetch_and_sync_device(device_id, action)

        except Exception as e:
            self._logger.error(f"Error handling device registry update: {e}", exc_info=True)

    def _notify_device_registry_update(self, action, device_id):
        """
        同步方法：通知前端設備註冊變更（在背景執行緒中執行）
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})
                realtime_service = env['ha.realtime.update']
                realtime_service.notify_device_registry_update(
                    action=action,
                    device_id=device_id,
                    ha_instance_id=self.instance_id
                )
                cr.commit()
                self._logger.debug(
                    f"Broadcast device registry update: {action} - {device_id} "
                    f"(instance {self.instance_id})"
                )
        except Exception as e:
            self._logger.error(
                f"Failed to notify device registry update for instance {self.instance_id}: {e}"
            )

    def _notify_area_registry_update(self, action, area_id):
        """
        同步方法：通知前端區域註冊變更（在背景執行緒中執行）
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})
                realtime_service = env['ha.realtime.update']
                realtime_service.notify_area_registry_update(
                    action=action,
                    area_id=area_id,
                    ha_instance_id=self.instance_id
                )
                cr.commit()
                self._logger.debug(
                    f"Broadcast area registry update: {action} - {area_id} "
                    f"(instance {self.instance_id})"
                )
        except Exception as e:
            self._logger.error(
                f"Failed to notify area registry update for instance {self.instance_id}: {e}"
            )

    async def _handle_area_registry_updated(self, event_data):
        """
        處理 Area 註冊變更事件
        用於 HA → Odoo 的雙向同步

        事件格式:
        {
            "action": "create" | "update" | "remove",
            "area_id": "area_id_string"
        }
        """
        try:
            action = event_data.get('action')
            area_id = event_data.get('area_id')

            if not action or not area_id:
                self._logger.warning(f"Invalid area_registry_updated event: {event_data}")
                return

            self._logger.info(
                f"Area registry updated: {action} - {area_id} (instance {self.instance_id})"
            )

            if action == 'remove':
                # 刪除事件：直接在 Odoo 中刪除，然後立即通知前端
                await self._run_sync(
                    self._sync_area_remove_from_ha,
                    area_id
                )
                # Remove 是同步操作，可以立即通知
                await self._run_sync(
                    self._notify_area_registry_update,
                    action,
                    area_id
                )
            elif action in ('create', 'update'):
                # 建立/更新事件：使用 debounce 機制
                # 通知會在 debounce 內部的 sync 完成後發送
                await self._debounced_fetch_and_sync_area(area_id, action)

        except Exception as e:
            self._logger.error(f"Error handling area registry update: {e}", exc_info=True)

    async def _handle_entity_registry_updated(self, event_data):
        """
        處理 Entity 註冊變更事件
        用於 HA → Odoo 的 entity area_id 和 name 雙向同步

        事件格式:
        {
            "action": "create" | "update" | "remove",
            "entity_id": "switch.test_switch",
            "changes": {"area_id": "old_area_id", "name": "old_name"}  # 僅 update 時有此欄位
        }

        重要：changes 中的值是「舊值」而非新值！
        因此需要從 HA 查詢最新的 entity registry 來獲取正確的新值。

        目前處理的情況：
        - update action 且 changes 中包含 area_id: 同步 area 到 Odoo
        - update action 且 changes 中包含 name: 同步 name 到 Odoo
        - update action 且 changes 中包含 labels: 同步 labels 到 Odoo
        """
        try:
            action = event_data.get('action')
            entity_id = event_data.get('entity_id')
            changes = event_data.get('changes', {})

            if not action or not entity_id:
                self._logger.warning(f"Invalid entity_registry_updated event: {event_data}")
                return

            self._logger.debug(
                f"Entity registry updated: {action} - {entity_id} (instance {self.instance_id})"
            )

            # 只處理 update action
            if action == 'update':
                # 檢查是否有我們關心的欄位變更
                area_changed = 'area_id' in changes
                name_changed = 'name' in changes
                labels_changed = 'labels' in changes

                if area_changed or name_changed or labels_changed:
                    changed_fields = []
                    if area_changed:
                        changed_fields.append('area_id')
                    if name_changed:
                        changed_fields.append('name')
                    if labels_changed:
                        changed_fields.append('labels')

                    self._logger.info(
                        f"Entity registry changed in HA: {entity_id}, "
                        f"fields: {', '.join(changed_fields)} (instance {self.instance_id})"
                    )

                    # 查詢 HA 獲取最新的 entity 資料並同步到 Odoo
                    # 注意：changes 中的是舊值，需要從 HA 查詢新值
                    await self._fetch_and_sync_entity_registry(
                        entity_id,
                        sync_area=area_changed,
                        sync_name=name_changed,
                        sync_labels=labels_changed
                    )

        except Exception as e:
            self._logger.error(f"Error handling entity registry update: {e}", exc_info=True)

    async def _handle_label_registry_updated(self, event_data):
        """
        Handle Label registry update event
        Used for HA → Odoo bidirectional sync

        Event format:
        {
            "action": "create" | "update" | "remove",
            "label_id": "label_id_string"
        }
        """
        try:
            action = event_data.get('action')
            label_id = event_data.get('label_id')

            if not action or not label_id:
                self._logger.warning(f"Invalid label_registry_updated event: {event_data}")
                return

            self._logger.info(
                f"Label registry updated: {action} - {label_id} (instance {self.instance_id})"
            )

            if action == 'remove':
                # Delete event: delete from Odoo directly
                await self._run_sync(
                    self._sync_label_remove_from_ha,
                    label_id
                )
            elif action in ('create', 'update'):
                # Create/update event: fetch label data and sync
                await self._fetch_and_sync_label(label_id)

        except Exception as e:
            self._logger.error(f"Error handling label registry update: {e}", exc_info=True)

    async def _fetch_and_sync_label(self, label_id: str):
        """
        Fetch label data from HA and sync to Odoo

        Args:
            label_id: HA label_id
        """
        try:
            # Get label list from HA (no single label get API)
            label_list = await self.send_request('config/label_registry/list', timeout=10)

            if label_list and isinstance(label_list, list):
                # Find target label
                label_data = None
                for label in label_list:
                    if label.get('label_id') == label_id:
                        label_data = label
                        break

                if label_data:
                    # Sync to Odoo in background thread
                    await self._run_sync(
                        self._sync_label_create_or_update_from_ha,
                        label_data
                    )
                else:
                    self._logger.warning(f"Label {label_id} not found in HA label list")
            else:
                self._logger.warning(f"Failed to get label list from HA")

        except asyncio.TimeoutError:
            self._logger.error(f"Timeout fetching label {label_id} from HA")
        except Exception as e:
            self._logger.error(f"Failed to fetch and sync label {label_id}: {e}", exc_info=True)

    def _sync_label_remove_from_ha(self, label_id: str):
        """
        Sync method: Delete label from Odoo (executed in background thread)

        Args:
            label_id: HA label_id
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})

                existing_label = env['ha.label'].sudo().search([
                    ('label_id', '=', label_id),
                    ('ha_instance_id', '=', self.instance_id)
                ], limit=1)

                if existing_label:
                    label_name = existing_label.name
                    # Use from_ha_sync to prevent sync loop
                    existing_label.with_context(from_ha_sync=True).unlink()
                    cr.commit()
                    self._logger.info(
                        f"Deleted label from Odoo: {label_name} (label_id={label_id}, instance {self.instance_id})"
                    )
                else:
                    self._logger.debug(
                        f"Label {label_id} not found in Odoo, skipping delete (instance {self.instance_id})"
                    )

        except Exception as e:
            self._logger.error(
                f"Failed to delete label from Odoo for instance {self.instance_id}: {e}",
                exc_info=True
            )

    def _sync_label_create_or_update_from_ha(self, label_data: dict):
        """
        Sync method: Create or update label from HA to Odoo (executed in background thread)

        Uses ha.label.sync_label_from_ha_data unified method

        Args:
            label_data: Complete label data from HA
        """
        try:
            label_id = label_data.get('label_id')
            if not label_id:
                return

            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})
                action, label = env['ha.label'].sync_label_from_ha_data(
                    label_data, self.instance_id
                )
                cr.commit()

                if action and label:
                    self._logger.info(
                        f"{action.capitalize()} label from HA: {label.name} "
                        f"(label_id={label_id}, instance {self.instance_id})"
                    )

        except Exception as e:
            self._logger.error(
                f"Failed to sync label to Odoo for instance {self.instance_id}: {e}",
                exc_info=True
            )

    async def _fetch_and_sync_entity_area(self, entity_id: str):
        """
        從 HA 查詢 entity 的最新 area_id 並同步到 Odoo
        （保留此方法以維持向後相容性，實際調用 _fetch_and_sync_entity_registry）

        Args:
            entity_id: HA 的 entity_id（如 "switch.test_switch"）
        """
        await self._fetch_and_sync_entity_registry(entity_id, sync_area=True, sync_name=False)

    async def _fetch_and_sync_entity_registry(
        self,
        entity_id: str,
        sync_area: bool = False,
        sync_name: bool = False,
        sync_labels: bool = False
    ):
        """
        從 HA 查詢 entity 的最新資料並同步指定欄位到 Odoo

        Args:
            entity_id: HA 的 entity_id（如 "switch.test_switch"）
            sync_area: 是否同步 area_id
            sync_name: 是否同步 name
            sync_labels: 是否同步 labels
        """
        if not sync_area and not sync_name and not sync_labels:
            self._logger.warning(
                f"_fetch_and_sync_entity_registry called without any sync flags for {entity_id}"
            )
            return

        try:
            # 使用 config/entity_registry/get 取得最新資料
            result = await self.send_request(
                'config/entity_registry/get',
                entity_id=entity_id,
                timeout=10
            )

            if result and isinstance(result, dict):
                fields_to_log = []

                if sync_area:
                    new_area_id = result.get('area_id')
                    fields_to_log.append(f"area_id={new_area_id}")
                    # 在背景執行緒中更新 Odoo area
                    await self._run_sync(
                        self._sync_entity_area_from_ha,
                        entity_id,
                        new_area_id
                    )

                if sync_name:
                    # HA Entity Registry 的 name 欄位可能為 null（使用 original_name）
                    # 我們需要取得最終顯示名稱，優先順序：name > original_name
                    ha_registry_name = result.get('name')
                    original_name = result.get('original_name')

                    # 計算最終顯示名稱
                    # 注意：這裡我們存儲的是使用者在 HA 設定的自訂名稱，
                    # 而非 friendly_name（friendly_name 還會加上 device name）
                    # 當 ha_registry_name 為 null 時，使用 original_name
                    display_name = ha_registry_name if ha_registry_name else original_name

                    fields_to_log.append(f"name={display_name!r}")
                    # 在背景執行緒中更新 Odoo name
                    await self._run_sync(
                        self._sync_entity_name_from_ha,
                        entity_id,
                        display_name
                    )

                if sync_labels:
                    # HA Entity Registry 的 labels 是 label_id 的列表
                    ha_labels = result.get('labels', [])
                    fields_to_log.append(f"labels={ha_labels}")
                    # 在背景執行緒中更新 Odoo labels
                    await self._run_sync(
                        self._sync_entity_labels_from_ha,
                        entity_id,
                        ha_labels
                    )

                self._logger.debug(
                    f"Fetched entity {entity_id} from HA: {', '.join(fields_to_log)}"
                )
            else:
                self._logger.warning(
                    f"Failed to get entity {entity_id} from HA: unexpected result {result}"
                )

        except asyncio.TimeoutError:
            self._logger.error(f"Timeout fetching entity {entity_id} from HA")
        except Exception as e:
            self._logger.error(
                f"Failed to fetch entity {entity_id} from HA: {e}",
                exc_info=True
            )

    def _sync_entity_area_from_ha(self, entity_id: str, ha_area_id: str):
        """
        同步方法：從 HA 更新 Entity 的 area_id 到 Odoo（在背景執行緒中執行）

        Args:
            entity_id: HA 的 entity_id（如 "switch.test_switch"）
            ha_area_id: HA 的 area_id 字串（可能為 None，表示取消區域關聯）
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})

                # 查找 Odoo 中的 entity
                entity = env['ha.entity'].sudo().search([
                    ('entity_id', '=', entity_id),
                    ('ha_instance_id', '=', self.instance_id)
                ], limit=1)

                if not entity:
                    self._logger.debug(
                        f"Entity {entity_id} not found in Odoo, skipping area sync "
                        f"(instance {self.instance_id})"
                    )
                    return

                # 根據 ha_area_id 查找對應的 Odoo area record
                if ha_area_id:
                    area = env['ha.area'].sudo().search([
                        ('area_id', '=', ha_area_id),
                        ('ha_instance_id', '=', self.instance_id)
                    ], limit=1)
                    odoo_area_id = area.id if area else False
                else:
                    odoo_area_id = False

                # 檢查是否需要更新
                current_area_id = entity.area_id.id if entity.area_id else False
                if current_area_id != odoo_area_id:
                    # 使用 from_ha_sync 防止循環同步
                    entity.with_context(from_ha_sync=True).write({
                        'area_id': odoo_area_id
                    })
                    cr.commit()

                    area_name = area.name if ha_area_id and area else 'None'
                    self._logger.info(
                        f"Updated entity area from HA: {entity_id} -> {area_name} "
                        f"(instance {self.instance_id})"
                    )
                else:
                    self._logger.debug(
                        f"Entity {entity_id} area unchanged, skipping update "
                        f"(instance {self.instance_id})"
                    )

        except Exception as e:
            self._logger.error(
                f"Failed to sync entity area from HA for instance {self.instance_id}: {e}",
                exc_info=True
            )

    def _sync_entity_name_from_ha(self, entity_id: str, ha_name: str):
        """
        同步方法：從 HA 更新 Entity 的 name 到 Odoo（在背景執行緒中執行）

        Args:
            entity_id: HA 的 entity_id（如 "switch.test_switch"）
            ha_name: HA 的顯示名稱
                - 如果 Entity Registry 有自訂 name，則為自訂 name
                - 如果沒有自訂，則為 original_name（整合提供的原始名稱）
                - 可能為 None（雖然少見，但需要處理）

        關於 HA Entity Registry 的 name 欄位與 friendly_name 的關係：
        - Entity Registry 的 name 是「使用者自訂的覆蓋名稱」
        - friendly_name 是「計算後的顯示名稱」，可能包含 device name
        - 我們在 Odoo 中存儲的是使用者可辨識的名稱（優先順序：name > original_name）
        - 這與 _process_entity_states 中使用 attributes.friendly_name 的行為保持一致
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})

                # 查找 Odoo 中的 entity
                entity = env['ha.entity'].sudo().search([
                    ('entity_id', '=', entity_id),
                    ('ha_instance_id', '=', self.instance_id)
                ], limit=1)

                if not entity:
                    self._logger.debug(
                        f"Entity {entity_id} not found in Odoo, skipping name sync "
                        f"(instance {self.instance_id})"
                    )
                    return

                # 正規化空值（None 和空字串都視為 False）
                new_name = ha_name if ha_name else False
                current_name = entity.name if entity.name else False

                # 檢查是否需要更新
                if current_name != new_name:
                    # 使用 from_ha_sync 防止循環同步
                    entity.with_context(from_ha_sync=True).write({
                        'name': new_name
                    })
                    cr.commit()

                    self._logger.info(
                        f"Updated entity name from HA: {entity_id} -> {new_name!r} "
                        f"(instance {self.instance_id})"
                    )
                else:
                    self._logger.debug(
                        f"Entity {entity_id} name unchanged, skipping update "
                        f"(instance {self.instance_id})"
                    )

        except Exception as e:
            self._logger.error(
                f"Failed to sync entity name from HA for instance {self.instance_id}: {e}",
                exc_info=True
            )

    def _sync_entity_labels_from_ha(self, entity_id: str, ha_label_ids: list):
        """
        同步方法：從 HA 更新 Entity 的 labels 到 Odoo（在背景執行緒中執行）

        Args:
            entity_id: HA 的 entity_id（如 "switch.test_switch"）
            ha_label_ids: HA 的 label_id 列表（如 ["label_1", "label_2"]）
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})

                # 查找 Odoo 中的 entity
                entity = env['ha.entity'].sudo().search([
                    ('entity_id', '=', entity_id),
                    ('ha_instance_id', '=', self.instance_id)
                ], limit=1)

                if not entity:
                    self._logger.debug(
                        f"Entity {entity_id} not found in Odoo, skipping labels sync "
                        f"(instance {self.instance_id})"
                    )
                    return

                # 使用 ha.label 的 get_or_create_labels 取得對應的 label records
                labels = env['ha.label'].get_or_create_labels(
                    ha_label_ids,
                    self.instance_id
                )
                new_label_ids = set(labels.ids)
                current_label_ids = set(entity.label_ids.ids)

                # 檢查是否需要更新
                if current_label_ids != new_label_ids:
                    # 使用 from_ha_sync 防止循環同步
                    entity.with_context(from_ha_sync=True).write({
                        'label_ids': [(6, 0, list(new_label_ids))]
                    })
                    cr.commit()

                    self._logger.info(
                        f"Updated entity labels from HA: {entity_id} -> {ha_label_ids} "
                        f"(instance {self.instance_id})"
                    )
                else:
                    self._logger.debug(
                        f"Entity {entity_id} labels unchanged, skipping update "
                        f"(instance {self.instance_id})"
                    )

        except Exception as e:
            self._logger.error(
                f"Failed to sync entity labels from HA for instance {self.instance_id}: {e}",
                exc_info=True
            )

    async def _initial_label_area_and_device_sync(self):
        """
        WebSocket connection successful, perform initial Label, Area and Device sync

        Execution order:
        1. Sync Labels first (labels must exist before areas/devices can reference them)
        2. Sync Areas (areas must exist before devices can reference them)
        3. Then sync Devices
        """
        self._logger.info(f"Starting initial label, area and device sync for instance {self.instance_id}")

        try:
            # Step 1: Sync Labels first (required for area/device label references)
            await self._initial_label_sync()

            # Step 2: Sync Areas (required for device area references)
            await self._initial_area_sync()

            # Step 3: Sync Devices (after labels and areas are synced)
            await self._initial_device_sync()

        except Exception as e:
            self._logger.error(f"Failed to perform initial sync: {e}", exc_info=True)

    async def _initial_label_sync(self):
        """
        Initial Label sync after WebSocket connection (HA → Odoo)

        Execution:
        1. HA → Odoo: Fetch all labels and sync to Odoo
        """
        self._logger.info(f"Starting initial label sync for instance {self.instance_id}")

        try:
            # Fetch all labels from HA
            label_list = await self.send_request(
                'config/label_registry/list',
                timeout=15
            )

            if label_list and isinstance(label_list, list):
                self._logger.info(f"Received {len(label_list)} labels from HA for initial sync")

                # HA → Odoo sync
                await self._run_sync(
                    self._batch_sync_labels_from_ha,
                    label_list
                )
                self._logger.info(f"Initial label sync (HA → Odoo) completed for instance {self.instance_id}")

            else:
                self._logger.warning(f"No labels received from HA for initial sync")

        except asyncio.TimeoutError:
            self._logger.error(f"Timeout during initial label sync for instance {self.instance_id}")
        except Exception as e:
            self._logger.error(f"Failed to perform initial label sync: {e}", exc_info=True)

    def _batch_sync_labels_from_ha(self, labels_data):
        """
        Batch sync all labels from HA to Odoo (executed in background thread)

        Uses ha.label.sync_label_from_ha_data unified method

        Args:
            labels_data: List of label data from HA
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})
                created_count = 0
                updated_count = 0
                failed_count = 0

                for label_data in labels_data:
                    label_id = label_data.get('label_id', 'unknown')
                    safe_id = ''.join(c if c.isalnum() else '_' for c in str(label_id))
                    savepoint = f"label_sync_{safe_id}"

                    try:
                        cr.execute(f"SAVEPOINT {savepoint}")

                        action, _ = env['ha.label'].sync_label_from_ha_data(
                            label_data, self.instance_id
                        )
                        if action == 'created':
                            created_count += 1
                        elif action == 'updated':
                            updated_count += 1

                        cr.execute(f"RELEASE SAVEPOINT {savepoint}")

                    except Exception as e:
                        cr.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                        failed_count += 1
                        self._logger.warning(
                            f"Failed to sync label {label_id}: {e}"
                        )

                cr.commit()
                self._logger.info(
                    f"Initial label sync (instance {self.instance_id}): "
                    f"{created_count} created, {updated_count} updated, {failed_count} failed"
                )

        except Exception as e:
            self._logger.error(
                f"Failed to batch sync labels for instance {self.instance_id}: {e}",
                exc_info=True
            )

    async def _initial_area_sync(self):
        """
        WebSocket 連線成功後的初始 Area 同步（合併模式）

        執行順序：
        1. HA → Odoo: 從 HA 取得所有 areas 並同步到 Odoo
        2. Odoo → HA: 將 Odoo 有但 HA 沒有的 areas 推送到 HA
        """
        self._logger.info(f"Starting initial area sync (merge mode) for instance {self.instance_id}")

        try:
            # Step 1: 從 HA 取得所有 areas
            area_list = await self.send_request(
                'config/area_registry/list',
                timeout=self._area_list_timeout
            )

            if area_list and isinstance(area_list, list):
                self._logger.info(f"Received {len(area_list)} areas from HA for initial sync")

                # Step 2: HA → Odoo 同步
                await self._run_sync(
                    self._batch_sync_areas_from_ha,
                    area_list
                )
                self._logger.info(f"Initial area sync (HA → Odoo) completed for instance {self.instance_id}")

                # Step 3: Odoo → HA 同步（合併模式）
                await self._sync_odoo_areas_to_ha(area_list)

            else:
                self._logger.warning(f"No areas received from HA for initial sync")
                # 即使 HA 沒有 areas，也要檢查 Odoo 是否有需要推送的
                await self._sync_odoo_areas_to_ha([])

        except asyncio.TimeoutError:
            self._logger.error(f"Timeout during initial area sync for instance {self.instance_id}")
        except Exception as e:
            self._logger.error(f"Failed to perform initial area sync: {e}", exc_info=True)

    async def _initial_device_sync(self):
        """
        Initial Device sync after WebSocket connection (HA → Odoo only)

        Note: Unlike areas, devices are managed by HA integrations and cannot be created from Odoo.
        Only HA → Odoo sync is performed during initial sync.

        Execution:
        1. HA → Odoo: Fetch all devices and sync to Odoo
        """
        self._logger.info(f"Starting initial device sync for instance {self.instance_id}")

        try:
            # Fetch all devices from HA
            device_list = await self.send_request(
                'config/device_registry/list',
                timeout=self._device_list_timeout
            )

            if device_list and isinstance(device_list, list):
                self._logger.info(f"Received {len(device_list)} devices from HA for initial sync")

                # HA → Odoo sync
                await self._run_sync(
                    self._batch_sync_devices_from_ha,
                    device_list
                )
                self._logger.info(f"Initial device sync (HA → Odoo) completed for instance {self.instance_id}")

            else:
                self._logger.warning(f"No devices received from HA for initial sync")

        except asyncio.TimeoutError:
            self._logger.error(f"Timeout during initial device sync for instance {self.instance_id}")
        except Exception as e:
            self._logger.error(f"Failed to perform initial device sync: {e}", exc_info=True)

    def _batch_sync_devices_from_ha(self, devices_data):
        """
        Batch sync all devices from HA to Odoo (executed in background thread)

        Uses ha.device.sync_device_from_ha_data unified method
        Uses Savepoint to ensure partial success: single device failure doesn't affect others

        Args:
            devices_data: List of device data from HA
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})
                created_count = 0
                updated_count = 0
                failed_count = 0

                for device_data in devices_data:
                    device_id = device_data.get('id', 'unknown')
                    # Use safe savepoint name (alphanumeric and underscore only)
                    safe_id = ''.join(c if c.isalnum() else '_' for c in str(device_id))
                    savepoint = f"device_sync_{safe_id}"

                    try:
                        cr.execute(f"SAVEPOINT {savepoint}")

                        action, _ = env['ha.device'].sync_device_from_ha_data(
                            device_data, self.instance_id
                        )
                        if action == 'created':
                            created_count += 1
                        elif action == 'updated':
                            updated_count += 1

                        cr.execute(f"RELEASE SAVEPOINT {savepoint}")

                    except Exception as e:
                        # Rollback to savepoint, continue with next device
                        cr.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                        failed_count += 1
                        self._logger.warning(
                            f"Failed to sync device {device_id}: {e}"
                        )

                cr.commit()
                self._logger.info(
                    f"Initial device sync (instance {self.instance_id}): "
                    f"{created_count} created, {updated_count} updated, {failed_count} failed"
                )

        except Exception as e:
            self._logger.error(
                f"Failed to batch sync devices for instance {self.instance_id}: {e}",
                exc_info=True
            )

    def _batch_sync_areas_from_ha(self, areas_data):
        """
        批次同步所有 areas 從 HA 到 Odoo（在背景執行緒中執行）

        使用 ha.area.sync_area_from_ha_data 統一方法
        使用 Savepoint 確保部分成功：單一 area 失敗不影響其他 areas

        Args:
            areas_data: HA 回傳的 area 資料列表
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})
                created_count = 0
                updated_count = 0
                failed_count = 0

                for area_data in areas_data:
                    area_id = area_data.get('area_id', 'unknown')
                    # 使用安全的 savepoint 名稱（只保留英數字和底線）
                    safe_id = ''.join(c if c.isalnum() else '_' for c in str(area_id))
                    savepoint = f"area_sync_{safe_id}"

                    try:
                        cr.execute(f"SAVEPOINT {savepoint}")

                        action, _ = env['ha.area'].sync_area_from_ha_data(
                            area_data, self.instance_id
                        )
                        if action == 'created':
                            created_count += 1
                        elif action == 'updated':
                            updated_count += 1

                        cr.execute(f"RELEASE SAVEPOINT {savepoint}")

                    except Exception as e:
                        # 回滾到 savepoint，繼續處理下一個 area
                        cr.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                        failed_count += 1
                        self._logger.warning(
                            f"Failed to sync area {area_id}: {e}"
                        )

                cr.commit()
                self._logger.info(
                    f"Initial area sync (instance {self.instance_id}): "
                    f"{created_count} created, {updated_count} updated, {failed_count} failed"
                )

        except Exception as e:
            self._logger.error(
                f"Failed to batch sync areas for instance {self.instance_id}: {e}",
                exc_info=True
            )

    async def _sync_odoo_areas_to_ha(self, ha_areas: List[Dict[str, Any]]) -> None:
        """
        Odoo → HA 同步：將 Odoo 有但 HA 沒有的 areas 推送到 HA（合併模式）

        Args:
            ha_areas: HA 目前的 area 列表（用於比對）
        """
        self._logger.debug(f"Starting Odoo → HA area sync for instance {self.instance_id}")

        try:
            # 建立 HA area_id 集合（用於快速查找）
            ha_area_ids = {area.get('area_id') for area in ha_areas if area.get('area_id')}

            # 在背景執行緒取得 Odoo areas
            odoo_areas = await self._run_sync(self._get_odoo_areas_for_sync)

            pushed_count = 0
            failed_count = 0

            for odoo_area in odoo_areas:
                odoo_area_id = odoo_area.get('area_id')

                if odoo_area_id and odoo_area_id not in ha_area_ids:
                    # Odoo 有 area_id 但 HA 沒有這個 area（可能 HA 被重置或刪除）
                    # 在 HA 重新創建
                    success = await self._create_area_in_ha_and_update_odoo(odoo_area)
                    if success:
                        pushed_count += 1
                    else:
                        failed_count += 1

                elif not odoo_area_id:
                    # Odoo area 沒有 area_id（從未成功同步到 HA）
                    # 在 HA 創建並更新 Odoo 的 area_id
                    success = await self._create_area_in_ha_and_update_odoo(odoo_area)
                    if success:
                        pushed_count += 1
                    else:
                        failed_count += 1

            self._logger.info(
                f"Initial area sync (Odoo → HA) completed for instance {self.instance_id}: "
                f"{pushed_count} pushed, {failed_count} failed"
            )

        except Exception as e:
            self._logger.error(
                f"Failed to sync Odoo areas to HA for instance {self.instance_id}: {e}",
                exc_info=True
            )

    def _get_odoo_areas_for_sync(self) -> List[Dict[str, Any]]:
        """
        取得 Odoo 中該 instance 的所有 areas（在背景執行緒中執行）

        Returns:
            List[Dict[str, Any]]: area 資料列表，包含 id, area_id, name, aliases, labels
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})
                areas = env['ha.area'].sudo().search([
                    ('ha_instance_id', '=', self.instance_id)
                ])
                return [{
                    'id': area.id,
                    'area_id': area.area_id,
                    'name': area.name,
                    'aliases': area.aliases or [],
                    'labels': area.labels or [],
                } for area in areas]
        except Exception as e:
            self._logger.error(f"Failed to get Odoo areas for sync: {e}", exc_info=True)
            return []

    async def _create_area_in_ha_and_update_odoo(self, odoo_area: dict) -> bool:
        """
        在 HA 創建 area 並更新 Odoo 的 area_id

        Args:
            odoo_area: Odoo area 資料 dict

        Returns:
            bool: 是否成功
        """
        try:
            payload = {
                'name': odoo_area['name'],
                'aliases': odoo_area.get('aliases', []),
                'labels': odoo_area.get('labels', []),
            }

            result = await self.send_request(
                'config/area_registry/create',
                timeout=self._area_create_timeout,
                **payload
            )

            if result and result.get('area_id'):
                new_area_id = result['area_id']

                # 在背景執行緒更新 Odoo 的 area_id
                await self._run_sync(
                    self._update_odoo_area_id,
                    odoo_area['id'],
                    new_area_id
                )

                self._logger.info(
                    f"Created area in HA and updated Odoo: {odoo_area['name']} "
                    f"(area_id={new_area_id})"
                )
                return True
            else:
                self._logger.warning(
                    f"Failed to create area in HA: {odoo_area['name']} - no area_id returned"
                )
                return False

        except Exception as e:
            self._logger.error(
                f"Failed to create area {odoo_area['name']} in HA: {e}",
                exc_info=True
            )
            return False

    def _update_odoo_area_id(self, odoo_area_id: int, ha_area_id: str) -> bool:
        """
        更新 Odoo area 的 area_id（在背景執行緒中執行）

        Args:
            odoo_area_id: Odoo area 的資料庫 ID
            ha_area_id: HA 回傳的 area_id

        Returns:
            bool: 是否成功更新
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})
                area = env['ha.area'].sudo().browse(odoo_area_id)
                if area.exists():
                    # 使用 from_ha_sync 避免觸發 Odoo→HA 同步
                    area.with_context(from_ha_sync=True).write({
                        'area_id': ha_area_id
                    })
                    cr.commit()
                    self._logger.debug(
                        f"Updated Odoo area_id: {odoo_area_id} -> {ha_area_id}"
                    )
                    return True
                else:
                    self._logger.warning(
                        f"Area {odoo_area_id} not found in Odoo, skipping update"
                    )
                    return False
        except Exception as e:
            self._logger.error(
                f"Failed to update Odoo area_id for area {odoo_area_id}: {e}",
                exc_info=True
            )
            return False

    async def _debounced_fetch_and_sync_area(self, area_id: str, action: str = 'update'):
        """
        Debounce 版本的 area 同步

        同一 area_id 在 500ms 內的多次呼叫只會執行最後一次
        避免快速連續事件造成重複 API 呼叫和資料庫寫入

        Args:
            area_id: HA 的 area_id
            action: 'create' | 'update' - 用於通知前端
        """
        # 如果已有該 area 的待處理 task，取消它
        if area_id in self._pending_area_syncs:
            self._pending_area_syncs[area_id].cancel()
            self._logger.debug(f"Cancelled pending sync for area {area_id} (debounce)")

        # 建立新的 debounced task
        async def delayed_sync():
            try:
                await asyncio.sleep(self._area_sync_debounce_delay)
                # 從 pending 中移除
                self._pending_area_syncs.pop(area_id, None)
                # 執行實際同步
                self._logger.debug(f"Executing debounced sync for area {area_id}")
                await self._fetch_and_sync_area(area_id)

                # Sync 完成後，通知前端快取失效
                await self._run_sync(
                    self._notify_area_registry_update,
                    action,
                    area_id
                )
            except asyncio.CancelledError:
                # 被新事件取消，正常情況
                self._logger.debug(f"Debounced sync for area {area_id} was cancelled")

        task = asyncio.create_task(delayed_sync())
        self._pending_area_syncs[area_id] = task

    async def _fetch_and_sync_area(self, area_id):
        """
        非阻塞地從 HA 取得 area 資料並同步到 Odoo

        Args:
            area_id: HA 的 area_id
        """
        try:
            # 使用已建立的 WebSocket 連線發送請求
            area_list = await self.send_request('config/area_registry/list', timeout=10)

            if area_list and isinstance(area_list, list):
                # 找到目標 area
                area_data = None
                for area in area_list:
                    if area.get('area_id') == area_id:
                        area_data = area
                        break

                if area_data:
                    # 在背景執行緒中同步到 Odoo
                    await self._run_sync(
                        self._sync_area_create_or_update_from_ha,
                        area_data
                    )
                else:
                    self._logger.warning(f"Area {area_id} not found in HA area list")
            else:
                self._logger.warning(f"Failed to get area list from HA")

        except asyncio.TimeoutError:
            self._logger.error(f"Timeout fetching area {area_id} from HA")
        except Exception as e:
            self._logger.error(f"Failed to fetch and sync area {area_id}: {e}", exc_info=True)

    def _sync_area_remove_from_ha(self, area_id):
        """
        同步方法：從 Odoo 刪除 Area（在背景執行緒中執行）

        Args:
            area_id: HA 的 area_id
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})

                existing_area = env['ha.area'].sudo().search([
                    ('area_id', '=', area_id),
                    ('ha_instance_id', '=', self.instance_id)
                ], limit=1)

                if existing_area:
                    area_name = existing_area.name
                    # 使用 from_ha_sync 防止循環同步
                    existing_area.with_context(from_ha_sync=True).unlink()
                    cr.commit()
                    self._logger.info(
                        f"Deleted area from Odoo: {area_name} (area_id={area_id}, instance {self.instance_id})"
                    )
                else:
                    self._logger.debug(
                        f"Area {area_id} not found in Odoo, skipping delete (instance {self.instance_id})"
                    )

        except Exception as e:
            self._logger.error(
                f"Failed to delete area from Odoo for instance {self.instance_id}: {e}",
                exc_info=True
            )

    def _sync_area_create_or_update_from_ha(self, area_data):
        """
        同步方法：從 HA 建立或更新 Area 到 Odoo（在背景執行緒中執行）

        使用 ha.area.sync_area_from_ha_data 統一方法

        Args:
            area_data: HA 回傳的完整 area 資料
        """
        try:
            area_id = area_data.get('area_id')
            if not area_id:
                return

            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})
                action, area = env['ha.area'].sync_area_from_ha_data(
                    area_data, self.instance_id
                )
                cr.commit()

                if action and area:
                    self._logger.info(
                        f"{action.capitalize()} area from HA: {area.name} "
                        f"(area_id={area_id}, instance {self.instance_id})"
                    )

        except Exception as e:
            self._logger.error(
                f"Failed to sync area to Odoo for instance {self.instance_id}: {e}",
                exc_info=True
            )

    # ========== Device Sync Methods (HA → Odoo) ==========

    async def _debounced_fetch_and_sync_device(self, device_id: str, action: str = 'update'):
        """
        Debounce version of device sync

        Same device_id within 500ms will only execute the last call
        Prevents duplicate API calls and database writes from rapid consecutive events

        Args:
            device_id: HA device_id
            action: 'create' | 'update' - 用於通知前端
        """
        # Cancel existing pending task for this device if any
        if device_id in self._pending_device_syncs:
            self._pending_device_syncs[device_id].cancel()
            self._logger.debug(f"Cancelled pending sync for device {device_id} (debounce)")

        # Create new debounced task
        async def delayed_sync():
            try:
                await asyncio.sleep(self._device_sync_debounce_delay)
                # Remove from pending
                self._pending_device_syncs.pop(device_id, None)
                # Execute actual sync
                self._logger.debug(f"Executing debounced sync for device {device_id}")
                await self._fetch_and_sync_device(device_id)

                # 同步該 device 下的 entities 關聯（確保 entity.device_id 正確）
                await self._sync_device_entities_relationship(device_id)

                # Sync 完成後，通知前端快取失效
                await self._run_sync(
                    self._notify_device_registry_update,
                    action,
                    device_id
                )
            except asyncio.CancelledError:
                # Cancelled by new event, normal situation
                self._logger.debug(f"Debounced sync for device {device_id} was cancelled")

        task = asyncio.create_task(delayed_sync())
        self._pending_device_syncs[device_id] = task

    async def _fetch_and_sync_device(self, device_id):
        """
        Non-blocking fetch device data from HA and sync to Odoo

        Args:
            device_id: HA device_id
        """
        try:
            # Use established WebSocket connection to send request
            device_list = await self.send_request('config/device_registry/list', timeout=10)

            if device_list and isinstance(device_list, list):
                # Find target device
                device_data = None
                for device in device_list:
                    if device.get('id') == device_id:
                        device_data = device
                        break

                if device_data:
                    # Sync to Odoo in background thread
                    await self._run_sync(
                        self._sync_device_create_or_update_from_ha,
                        device_data
                    )
                else:
                    self._logger.warning(f"Device {device_id} not found in HA device list")
            else:
                self._logger.warning(f"Failed to get device list from HA")

        except asyncio.TimeoutError:
            self._logger.error(f"Timeout fetching device {device_id} from HA")
        except Exception as e:
            self._logger.error(f"Failed to fetch and sync device {device_id}: {e}", exc_info=True)

    async def _sync_device_entities_relationship(self, device_id: str):
        """
        同步指定 device 下的 entities 的 device_id 關聯

        當 device 被創建或更新後呼叫，確保相關 entities 的 device_id 正確設置。
        這比全量 _sync_entity_registry_relations 更有效率。

        Args:
            device_id: HA 的 device_id
        """
        try:
            # 從 HA 查詢 entity registry
            entity_list = await self.send_request(
                'config/entity_registry/list',
                timeout=15
            )

            if not entity_list or not isinstance(entity_list, list):
                self._logger.warning(
                    f"Failed to get entity registry from HA for device {device_id}"
                )
                return

            # 過濾出屬於此 device 的 entities
            device_entities = [
                e for e in entity_list
                if e.get('device_id') == device_id
            ]

            if not device_entities:
                self._logger.debug(
                    f"No entities found for device {device_id}"
                )
                return

            self._logger.info(
                f"Syncing {len(device_entities)} entities for device {device_id}"
            )

            # 在 Odoo 中更新這些 entities 的 device_id
            await self._run_sync(
                self._update_entities_device_relationship,
                device_id,
                [e.get('entity_id') for e in device_entities]
            )

        except asyncio.TimeoutError:
            self._logger.error(
                f"Timeout fetching entity registry for device {device_id}"
            )
        except Exception as e:
            self._logger.error(
                f"Failed to sync device entities relationship for {device_id}: {e}",
                exc_info=True
            )

    def _update_entities_device_relationship(self, ha_device_id: str, entity_ids: list):
        """
        同步方法：更新 entities 的 device_id 關聯（在背景執行緒中執行）

        Args:
            ha_device_id: HA 的 device_id
            entity_ids: 要更新的 entity_id 列表
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})

                # 查找 Odoo 中的 device
                odoo_device = env['ha.device'].sudo().search([
                    ('device_id', '=', ha_device_id),
                    ('ha_instance_id', '=', self.instance_id)
                ], limit=1)

                if not odoo_device:
                    self._logger.warning(
                        f"Device {ha_device_id} not found in Odoo, "
                        f"cannot update entity relationships"
                    )
                    return

                # 查找需要更新的 entities
                entities = env['ha.entity'].sudo().search([
                    ('entity_id', 'in', entity_ids),
                    ('ha_instance_id', '=', self.instance_id)
                ])

                updated_count = 0
                for entity in entities:
                    if entity.device_id.id != odoo_device.id:
                        entity.with_context(from_ha_sync=True).write({
                            'device_id': odoo_device.id
                        })
                        updated_count += 1

                if updated_count > 0:
                    cr.commit()
                    self._logger.info(
                        f"Updated {updated_count} entities' device_id to {odoo_device.name} "
                        f"(device_id={ha_device_id}, instance {self.instance_id})"
                    )

        except Exception as e:
            self._logger.error(
                f"Failed to update entities device relationship: {e}",
                exc_info=True
            )

    def _sync_device_remove_from_ha(self, device_id):
        """
        Sync method: Delete device from Odoo (executed in background thread)

        使用重試機制處理 PostgreSQL serialization conflict。
        當 CASCADE 刪除 entity 時，若有其他 transaction 正在更新同一 entity，
        會發生 serialization conflict，需要重試。

        Args:
            device_id: HA device_id
        """
        max_retries = 3
        retry_delay = 0.5  # 500ms

        for attempt in range(max_retries):
            try:
                with db.db_connect(self.db_name).cursor() as cr:
                    env = api.Environment(cr, 1, {})

                    existing_device = env['ha.device'].sudo().search([
                        ('device_id', '=', device_id),
                        ('ha_instance_id', '=', self.instance_id)
                    ], limit=1)

                    if existing_device:
                        device_name = existing_device.name
                        # Use from_ha_sync to prevent sync loop
                        existing_device.with_context(from_ha_sync=True).unlink()
                        cr.commit()
                        self._logger.info(
                            f"Deleted device from Odoo: {device_name} (device_id={device_id}, instance {self.instance_id})"
                        )
                    else:
                        self._logger.debug(
                            f"Device {device_id} not found in Odoo, skipping delete (instance {self.instance_id})"
                        )
                    # 成功，跳出重試迴圈
                    return

            except Exception as e:
                error_msg = str(e)
                is_serialization_error = 'serialize' in error_msg.lower() or 'concurrent' in error_msg.lower()

                if is_serialization_error and attempt < max_retries - 1:
                    self._logger.warning(
                        f"Serialization conflict deleting device {device_id}, "
                        f"retrying ({attempt + 1}/{max_retries})..."
                    )
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    self._logger.error(
                        f"Failed to delete device from Odoo for instance {self.instance_id}: {e}",
                        exc_info=True
                    )
                    return

    def _sync_device_create_or_update_from_ha(self, device_data):
        """
        Sync method: Create or update device from HA to Odoo (executed in background thread)

        Uses ha.device.sync_device_from_ha_data unified method

        Args:
            device_data: Complete device data from HA
        """
        try:
            device_id = device_data.get('id')
            if not device_id:
                return

            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})
                action, device = env['ha.device'].sync_device_from_ha_data(
                    device_data, self.instance_id
                )
                cr.commit()

                if action and device:
                    self._logger.info(
                        f"{action.capitalize()} device from HA: {device.name} "
                        f"(device_id={device_id}, instance {self.instance_id})"
                    )

        except Exception as e:
            self._logger.error(
                f"Failed to sync device to Odoo for instance {self.instance_id}: {e}",
                exc_info=True
            )

    async def _update_entity_in_odoo(
        self,
        entity_id: str,
        new_state_data: Dict[str, Any],
        old_state_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        在 Odoo 中更新實體狀態（非阻塞版本）

        Args:
            entity_id: Home Assistant entity ID
            new_state_data: 新的狀態資料
            old_state_data: 舊的狀態資料（可選）
        """
        try:
            await self._run_sync(
                self._sync_update_entity,
                entity_id,
                new_state_data,
                old_state_data
            )
        except Exception as e:
            self._logger.error(f"Failed to update entity in Odoo: {e}")

    def _sync_update_entity(self, entity_id, new_state_data, old_state_data=None):
        """
        同步版本的實體更新（在背景執行緒中執行）
        Phase 2: 加入 ha_instance_id 過濾和設定
        """
        try:
            # 建立新的資料庫連線和環境
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})  # 使用 admin 用戶

                # Phase 2: 查找實體時加上 ha_instance_id 過濾
                entity = env['ha.entity'].search([
                    ('entity_id', '=', entity_id),
                    ('ha_instance_id', '=', self.instance_id)
                ], limit=1)

                entity_values = {
                    'entity_id': entity_id,
                    'domain': entity_id.split('.')[0],
                    'entity_state': new_state_data.get('state'),
                    'last_changed': datetime.now(),
                    'attributes': new_state_data.get('attributes', {}),
                    'ha_instance_id': self.instance_id  # Phase 2: 新增實例 ID
                }

                if entity:
                    # 更新現有實體
                    entity.write({
                        'entity_state': entity_values['entity_state'],
                        'last_changed': entity_values['last_changed'],
                        'attributes': entity_values['attributes']
                    })
                    self._logger.debug(f"Updated entity: {entity_id} (instance {self.instance_id})")
                else:
                    # 建立新實體
                    entity = env['ha.entity'].create(entity_values)
                    self._logger.info(f"Created new entity: {entity_id} (instance {self.instance_id})")

                # 如果啟用歷史記錄，則建立歷史記錄
                if entity.enable_record:
                    env['ha.entity.history'].create({
                        'entity_id': entity.id,
                        'domain': entity_values['domain'],
                        'entity_state': entity_values['entity_state'],
                        'last_changed': entity_values['last_changed'],
                        'last_updated': entity_values['last_changed'],
                        'attributes': entity_values['attributes']
                    })

                # 🔔 通知前端：實體狀態變更（Phase 2: 附加 instance_id）
                try:
                    realtime_service = env['ha.realtime.update']
                    realtime_service.notify_entity_state_change(
                        entity_id,
                        old_state_data,
                        new_state_data,
                        ha_instance_id=self.instance_id  # Phase 2: 附加實例 ID
                    )
                    self._logger.debug(f"Broadcast state change notification for: {entity_id} (instance {self.instance_id})")
                except Exception as notify_error:
                    self._logger.error(f"Failed to notify state change: {notify_error}")

                # 提交事務
                cr.commit()

        except Exception as e:
            self._logger.error(f"Error in sync entity update for instance {self.instance_id}: {e}")

    def _get_next_id(self) -> int:
        """取得下一個訊息 ID"""
        message_id = self._message_id
        self._message_id += 1
        return message_id

    def stop(self) -> None:
        """停止 WebSocket 服務"""
        self._running = False

        # 取消所有 pending area sync tasks
        for task in self._pending_area_syncs.values():
            task.cancel()
        self._pending_area_syncs.clear()

        # 取消所有 pending device sync tasks
        for task in self._pending_device_syncs.values():
            task.cancel()
        self._pending_device_syncs.clear()

        # 清理 pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()

        # 清理 subscriptions
        self._subscriptions.clear()

        if self._websocket:
            asyncio.create_task(self._websocket.close())

    def is_running(self) -> bool:
        """檢查服務是否運行中"""
        return self._running

    def _notify_status_with_env(self, status: str, message: str) -> None:
        """
        建立 env 並通知前端 WebSocket 狀態（同步版本，用於在背景執行緒中調用）
        Phase 2: 附加 instance_id 資訊

        Args:
            status: 狀態字串 ('connected', 'disconnected', 'error', 'reconnecting')
            message: 狀態訊息
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})  # 使用 admin 用戶
                realtime_service = env['ha.realtime.update']
                # Phase 2: 附加 instance_id 參數
                realtime_service.notify_ha_websocket_status(status, message, ha_instance_id=self.instance_id)
                cr.commit()
                self._logger.debug(f"Notified frontend: {status} - {message} (instance {self.instance_id})")
        except Exception as e:
            self._logger.error(f"Failed to notify status with env (instance {self.instance_id}): {e}")

    async def send_request(
        self,
        message_type: str,
        timeout: int = 10,
        **kwargs: Any
    ) -> Any:
        """
        發送請求並等待回應

        Args:
            message_type: 訊息類型 (例如: 'supervisor/api', 'call_service')
            timeout: 等待回應的超時時間（秒）
            **kwargs: 其他訊息參數

        Returns:
            WebSocket 回應的 result 資料

        Raises:
            Exception: WebSocket 未連線或請求失敗
            asyncio.TimeoutError: 請求超時
        """
        if not self._websocket or not self._running:
            raise Exception("WebSocket not connected")

        # 建立請求訊息
        message_id = self._get_next_id()
        message = {
            'id': message_id,
            'type': message_type,
            **kwargs
        }

        # 建立 Future 來等待回應
        future = asyncio.Future()
        self._pending_requests[message_id] = future

        try:
            # 發送請求
            await self._websocket.send(json.dumps(message))
            self._logger.debug(f"Sent request {message_id}: {message_type}")

            # 等待回應（帶超時）
            result = await asyncio.wait_for(future, timeout=timeout)
            self._logger.debug(f"Received response for request {message_id}")
            return result

        except asyncio.TimeoutError:
            # 清理超時的請求
            self._pending_requests.pop(message_id, None)
            self._logger.error(f"Request {message_id} timed out")
            raise
        except Exception as e:
            # 清理失敗的請求
            self._pending_requests.pop(message_id, None)
            self._logger.error(f"Request {message_id} failed: {e}")
            raise

    # Phase 2: 移除單例模式的 get_instance() 方法
    # 每個實例獨立創建，不再使用全局單例

    async def _process_subscription_request(self, request_data, payload):
        """
        處理訂閱請求

        Args:
            request_data: 請求數據
            payload: 請求 payload
        """
        try:
            # 發送訂閱訊息
            message_id = self._get_next_id()

            message = {
                'id': message_id,
                'type': request_data['message_type'],
                **payload
            }

            self._logger.info(f"Sending subscription message: {message}")
            await self._websocket.send(json.dumps(message))

            # 註冊訂閱（等待 result 和 event）
            self._subscriptions[message_id] = {
                'request_id': request_data['request_id'],
                'subscription_id': None  # 稍後從 result 中取得
            }

            self._logger.info(f"Subscription {request_data['request_id']} registered with message_id={message_id}")

        except Exception as e:
            self._logger.error(f"Failed to send subscription request: {e}", exc_info=True)
            raise

    async def _process_request_queue(self):
        """
        處理請求隊列（從資料庫）
        這個方法運行在 WebSocket worker process 中
        定期檢查是否有來自其他 process 的請求
        """
        self._logger.info("Starting request queue processor")

        while self._running:
            try:
                # 使用 run_in_executor 在背景執行同步的資料庫操作
                pending_requests = await self._run_sync(self._get_pending_requests)

                if pending_requests:
                    for request_data in pending_requests:
                        try:
                            # 標記為處理中
                            await self._run_sync(
                                self._mark_request_processing,
                                request_data['id']
                            )

                            self._logger.debug(f"Processing request {request_data['request_id']}: {request_data['message_type']}")

                            # 解析 payload
                            payload = json.loads(request_data['payload']) if request_data['payload'] else {}

                            # 檢查是否為訂閱請求
                            if request_data.get('is_subscription'):
                                self._logger.info(f"Detected subscription request: {request_data['request_id']}")
                                await self._process_subscription_request(request_data, payload)
                            else:
                                # 一般請求：發送並等待結果
                                result = await self.send_request(
                                    message_type=request_data['message_type'],
                                    timeout=10,
                                    **payload
                                )

                                # 寫入結果
                                await self._run_sync(
                                    self._mark_request_done,
                                    request_data['id'],
                                    json.dumps(result)
                                )

                                self._logger.debug(f"Request {request_data['request_id']} completed successfully")

                        except asyncio.TimeoutError:
                            await self._run_sync(
                                self._mark_request_timeout,
                                request_data['id']
                            )
                            self._logger.error(f"Request {request_data['request_id']} timed out")

                        except Exception as e:
                            error_msg = f"{str(e)}\n{traceback.format_exc()}"
                            await self._run_sync(
                                self._mark_request_failed,
                                request_data['id'],
                                error_msg
                            )
                            self._logger.error(f"Request {request_data['request_id']} failed: {error_msg}")

                # 定期清理過期訂閱（每 30 秒）
                current_time = time.time()
                if current_time - self._last_subscription_cleanup > self._subscription_cleanup_interval:
                    await self._cleanup_stale_subscriptions()
                    self._last_subscription_cleanup = current_time

                # 等待一段時間後再檢查
                await asyncio.sleep(0.5)

            except Exception as e:
                self._logger.error(f"Error in request queue processor: {e}")
                await asyncio.sleep(1)

        self._logger.info("Request queue processor stopped")

    async def _heartbeat_loop(self):
        """
        心跳循環：定期更新心跳時間戳記
        這讓其他 process 可以檢查 WebSocket 服務是否正常運行

        心跳間隔可通過配置調整，建議設定小於 API timeout (15秒) 內能檢測到服務狀態
        配置會在每次循環時動態讀取，修改後無需重啟服務即可生效
        """
        self._logger.info("Starting heartbeat loop with dynamic interval")

        while self._running:
            try:
                # 每次循環都重新讀取配置的心跳間隔（動態生效）
                heartbeat_interval = self.get_heartbeat_interval()

                # 使用 run_in_executor 在背景執行同步的資料庫操作
                await self._run_sync(self._update_heartbeat)

                self._logger.debug(f"Heartbeat updated, next update in {heartbeat_interval}s")

                # 使用配置的心跳間隔
                await asyncio.sleep(heartbeat_interval)

            except Exception as e:
                self._logger.error(f"Error in heartbeat loop: {e}")
                # 發生錯誤時使用默認間隔
                default_interval = 10
                await asyncio.sleep(default_interval)

        self._logger.info("Heartbeat loop stopped")

    async def _cleanup_stale_subscriptions(self):
        """
        清理已過期的訂閱

        當 queue 記錄已經 timeout/failed/deleted 時，
        對應的 _subscriptions 項目也需要清理，避免內存洩漏

        這個方法定期執行（每 30 秒），確保 stale subscriptions 被清理
        """
        if not self._subscriptions:
            return

        stale_message_ids = []

        # 建立 message_id -> request_id 映射
        message_to_request = {}
        for message_id, info in list(self._subscriptions.items()):
            request_id = info.get('request_id')
            if request_id:
                message_to_request[message_id] = request_id

        if not message_to_request:
            return

        # 批次檢查所有訂閱的有效性（單次 DB 查詢）
        request_ids = list(message_to_request.values())
        valid_request_ids = await self._run_sync(
            self._check_subscriptions_validity_batch, request_ids
        )

        # 找出無效的訂閱
        for message_id, request_id in message_to_request.items():
            if request_id not in valid_request_ids:
                stale_message_ids.append(message_id)

        # 清理 stale subscriptions
        for mid in stale_message_ids:
            # 防止 asyncio 協程並發問題：await 期間其他協程可能已刪除此 key
            if mid not in self._subscriptions:
                self._logger.debug(f"Subscription {mid} already removed by another coroutine")
                continue

            self._logger.info(f"Cleaning stale subscription: message_id={mid}")

            # 嘗試發送 unsubscribe 給 HA
            subscription_id = self._subscriptions[mid].get('subscription_id')
            if subscription_id:
                try:
                    await self._send_unsubscribe_message(subscription_id)
                except Exception as e:
                    self._logger.warning(f"Failed to unsubscribe {subscription_id}: {e}")

            # 從內存中移除（再次檢查，因為 await 後可能被刪除）
            if mid in self._subscriptions:
                del self._subscriptions[mid]

        if stale_message_ids:
            self._logger.info(f"Cleaned {len(stale_message_ids)} stale subscriptions")

    def _check_subscription_valid(self, request_id):
        """
        檢查訂閱是否仍有效

        訂閱有效條件：queue 記錄存在且狀態為 pending/subscribed/collecting

        Args:
            request_id: 請求 ID

        Returns:
            bool: True 如果訂閱仍有效
        """
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})
                record = env['ha.ws.request.queue'].search([
                    ('request_id', '=', request_id),
                    ('state', 'in', ['pending', 'subscribed', 'collecting'])
                ], limit=1)
                return bool(record)
        except Exception as e:
            self._logger.warning(f"Error checking subscription validity: {e}")
            # 如果查詢失敗，假設訂閱仍有效（保守策略）
            return True

    def _check_subscriptions_validity_batch(self, request_ids):
        """
        批次檢查多個訂閱的有效性（單次 DB 查詢）

        訂閱有效條件：queue 記錄存在且狀態為 pending/subscribed/collecting

        Args:
            request_ids: 請求 ID 列表

        Returns:
            set: 仍有效的 request_id 集合
        """
        if not request_ids:
            return set()

        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})
                valid_records = env['ha.ws.request.queue'].search([
                    ('request_id', 'in', request_ids),
                    ('state', 'in', ['pending', 'subscribed', 'collecting'])
                ])
                return set(valid_records.mapped('request_id'))
        except Exception as e:
            self._logger.warning(f"Error checking subscriptions validity batch: {e}")
            # 如果查詢失敗，假設所有訂閱仍有效（保守策略）
            return set(request_ids)

    async def _send_unsubscribe_message(self, subscription_id):
        """
        發送 unsubscribe 訊息給 Home Assistant

        Args:
            subscription_id: HA 訂閱 ID
        """
        if not self._websocket or not subscription_id:
            return

        try:
            message_id = self._get_next_id()
            message = {
                'id': message_id,
                'type': 'unsubscribe_events',
                'subscription': subscription_id
            }
            await self._websocket.send(json.dumps(message))
            self._logger.debug(f"Sent unsubscribe for subscription {subscription_id}")
        except Exception as e:
            self._logger.warning(f"Failed to send unsubscribe message: {e}")

    def _update_heartbeat(self):
        """
        同步方法：更新心跳時間戳記到資料庫
        Phase 2: 心跳 key 包含 instance_id
        """
        try:
            from datetime import datetime, timezone

            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})

                # Phase 2: 心跳 key 包含 db_name 和 instance_id
                heartbeat_key = f'odoo_ha_addon.ws_heartbeat_{self.db_name}_instance_{self.instance_id}'
                now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

                env['ir.config_parameter'].sudo().set_param(heartbeat_key, now_utc)
                cr.commit()

                self._logger.debug(f"Heartbeat updated for instance {self.instance_id}: {now_utc}")

        except Exception as e:
            self._logger.error(f"Failed to update heartbeat for instance {self.instance_id}: {e}")

    def _get_pending_requests(self):
        """
        同步方法：取得待處理的請求
        Phase 2: 過濾特定實例的請求
        """
        with db.db_connect(self.db_name).cursor() as cr:
            env = api.Environment(cr, 1, {})

            # ✓ 先 commit 以確保能看到其他 process 的最新記錄
            cr.commit()

            # Phase 2: 過濾特定實例的待處理請求
            records = env['ha.ws.request.queue'].search([
                ('state', '=', 'pending'),
                ('ha_instance_id', '=', self.instance_id)  # Phase 2: 過濾實例
            ], limit=10, order='create_date asc')

            return [{
                'id': r.id,
                'request_id': r.request_id,
                'message_type': r.message_type,
                'payload': r.payload,
                'is_subscription': r.is_subscription  # ← 關鍵：必須讀取此欄位以正確識別訂閱請求
            } for r in records]

    def _update_request_with_retry(self, record_id, values, operation_name='update'):
        """
        通用方法：更新 ha.ws.request.queue 記錄（含 retry 機制）

        Args:
            record_id: 記錄 ID
            values: 要更新的欄位字典 (e.g., {'state': 'done', 'result': '...'})
            operation_name: 操作名稱（用於日誌）

        Returns:
            bool: 是否成功
        """
        import time
        from psycopg2 import OperationalError
        from psycopg2.extensions import TransactionRollbackError

        max_retries = 3
        base_delay = 0.05  # 50ms

        for attempt in range(max_retries):
            try:
                with db.db_connect(self.db_name).cursor() as cr:
                    env = api.Environment(cr, 1, {})
                    record = env['ha.ws.request.queue'].browse(record_id)

                    if not record.exists():
                        self._logger.warning(f"Record {record_id} not found for {operation_name}")
                        return False

                    record.write(values)
                    cr.commit()
                    return True

            except (OperationalError, TransactionRollbackError) as e:
                # SerializationFailure 或其他 transaction 衝突
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff: 50ms, 100ms, 200ms
                    self._logger.warning(
                        f"{operation_name} failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {delay*1000:.0f}ms: {e}"
                    )
                    time.sleep(delay)
                else:
                    self._logger.error(
                        f"{operation_name} failed after {max_retries} attempts: {e}"
                    )
                    return False
            except Exception as e:
                self._logger.error(f"Unexpected error in {operation_name}: {e}")
                return False

        return False

    def _mark_request_processing(self, record_id):
        """同步方法：標記請求為處理中"""
        self._update_request_with_retry(
            record_id,
            {'state': 'processing'},
            'mark_as_processing'
        )

    def _mark_request_done(self, record_id, result):
        """同步方法：標記請求完成"""
        self._update_request_with_retry(
            record_id,
            {'state': 'done', 'result': result},
            'mark_as_done'
        )

    def _mark_request_timeout(self, record_id):
        """同步方法：標記請求超時"""
        self._update_request_with_retry(
            record_id,
            {'state': 'timeout', 'error': 'Request timed out'},
            'mark_as_timeout'
        )

    def _mark_request_failed(self, record_id, error):
        """同步方法：標記請求失敗"""
        self._update_request_with_retry(
            record_id,
            {'state': 'failed', 'error': error},
            'mark_as_failed'
        )