import json
import time
import uuid
import logging
from odoo import api, models

class WebSocketClient:
    """
    通用 WebSocket 客戶端
    提供跨 process 的 WebSocket API 呼叫功能
    消除 Controller 和 Model 中的重複程式碼

    Phase 3 & 3.1: 支援多 HA 實例，使用 HAInstanceHelper 統一實現
    """

    def __init__(self, env, instance_id=None):
        """
        Args:
            env: Odoo 環境物件
            instance_id: HA 實例 ID (Phase 3)，如果為 None 則使用 HAInstanceHelper
                        支持 4-level fallback + session + user preference + notifications
        """
        self.env = env
        self._logger = logging.getLogger(__name__)

        # Phase 3.1: 使用 HAInstanceHelper 統一實現（重構後）
        # 支持：session validation, user preference, bus notifications, logging
        if instance_id is None:
            from .instance_helper import HAInstanceHelper
            self.instance_id = HAInstanceHelper.get_current_instance(env, logger=self._logger)
        else:
            self.instance_id = instance_id
    
    def call_websocket_api(self, message_type, payload=None, timeout=15):
        """
        通用 WebSocket API 呼叫
        
        Args:
            message_type (str): WebSocket 訊息類型 (如 'get_states', 'call_service')
            payload (dict): 請求參數，可選
            timeout (int): 超時時間（秒），預設 15 秒
        
        Returns:
            dict: {'success': bool, 'data': dict, 'error': str}
        """
        self._logger.debug(f"Starting WebSocket API call: {message_type}")
        self._logger.debug(f"Payload: {payload}")
        self._logger.debug(f"Timeout: {timeout}s")
        
        try:
            # 檢查 WebSocket 服務狀態
            self._logger.debug("Checking WebSocket service status...")
            if not self._is_websocket_running():
                self._logger.debug("WebSocket service is not running")
                return {
                    'success': False,
                    'error': 'WebSocket 服務未連線，請確認服務已啟動'
                }
            
            self._logger.debug("WebSocket service is running, proceeding with request")
            
            # 建立請求
            request_id = str(uuid.uuid4())
            self._logger.debug(f"Generated request ID: {request_id}")
            
            ws_request = self._create_request(request_id, message_type, payload)
            
            # 等待結果
            self._logger.debug(f"Waiting for result from request {request_id}...")
            result = self._wait_for_result(ws_request, request_id, timeout)
            
            self._logger.debug(f"WebSocket API call completed: {message_type}, success: {result.get('success')}")
            return result
            
        except Exception as e:
            self._logger.error(f"WebSocket API call failed (type: {message_type}): {e}")
            self._logger.debug(f"Exception details: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def call_websocket_api_sync(self, message_type, payload=None, timeout=10):
        """
        同步版本：返回直接數據或拋出異常
        適用於 model 方法中使用

        Args:
            message_type (str): WebSocket 訊息類型
            payload (dict): 請求參數，可選
            timeout (int): 超時時間（秒），預設 10 秒

        Returns:
            dict/list: WebSocket API 的回應數據

        Raises:
            Exception: 當請求失敗時
        """
        result = self.call_websocket_api(message_type, payload, timeout)

        if result['success']:
            return result['data']
        else:
            raise Exception(result['error'])

    def subscribe_history_stream(self, entity_ids, start_time, end_time, timeout=60):
        """
        訂閱歷史資料流 (history/stream)

        Args:
            entity_ids (list): 實體 ID 列表
            start_time (str): 開始時間 (ISO 8601)
            end_time (str): 結束時間 (ISO 8601)
            timeout (int): 超時時間（秒），預設 60 秒

        Returns:
            dict: {'success': bool, 'data': list, 'error': str}
                data 包含所有收集的事件
        """
        # 構建 history/stream 特定的 payload
        payload = {
            'entity_ids': entity_ids,
            'start_time': start_time,
            'end_time': end_time,
            'include_start_time_state': True,  # 包含開始時間的狀態
            'significant_changes_only': False,  # 包含所有變化（不只顯著變化）
            'minimal_response': False,  # 需要完整回應
            'no_attributes': False,  # 需要屬性資料（明確設定以避免已知問題）
        }

        # 使用通用訂閱函數
        return self._create_subscription_request(
            message_type='history/stream',
            payload=payload,
            timeout=timeout,
            description=f"history/stream for {entity_ids}"
        )

    def _create_subscription_request(self, message_type, payload, timeout=60, description=None):
        """
        通用訂閱請求創建函數

        用於所有 WebSocket 訂閱類型的統一處理邏輯：
        - 檢查服務狀態
        - 創建訂閱記錄
        - 等待訂閱完成
        - 返回標準結果

        Args:
            message_type (str): WebSocket 訊息類型（如 'history/stream'）
            payload (dict): 訂閱參數
            timeout (int): 超時時間（秒），預設 60 秒
            description (str): 訂閱描述（用於日誌），可選

        Returns:
            dict: {'success': bool, 'data': list/dict, 'error': str}
        """
        desc = description or message_type
        self._logger.info(f"Starting subscription: {desc}")

        try:
            # 檢查 WebSocket 服務狀態
            if not self._is_websocket_running():
                return {
                    'success': False,
                    'error': 'WebSocket 服務未連線，請確認服務已啟動'
                }

            # 生成請求 ID
            request_id = str(uuid.uuid4())

            # 創建訂閱記錄
            ws_request = self.env['ha.ws.request.queue'].sudo().create({
                'request_id': request_id,
                'message_type': message_type,
                'payload': json.dumps(payload),
                'state': 'pending',
                'is_subscription': True,
                'ha_instance_id': self.instance_id,  # Phase 3: 指定實例 ID
            })

            self.env.cr.commit()

            self._logger.info(f"Created subscription request: {request_id} (type: {message_type}, instance: {self.instance_id})")

            # 等待訂閱完成並收集事件
            result = self._wait_for_subscription_complete(ws_request, request_id, timeout)

            return result

        except Exception as e:
            self._logger.error(f"Subscription failed ({desc}): {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    # 範例：未來擴展其他訂閱類型
    # =====================================
    # def subscribe_events(self, event_type, timeout=60):
    #     """訂閱特定類型的事件"""
    #     payload = {'event_type': event_type}
    #     return self._create_subscription_request(
    #         message_type='subscribe_events',
    #         payload=payload,
    #         timeout=timeout,
    #         description=f"events for {event_type}"
    #     )
    #
    # def subscribe_trigger(self, trigger_config, timeout=60):
    #     """訂閱觸發器狀態變化"""
    #     return self._create_subscription_request(
    #         message_type='subscribe_trigger',
    #         payload=trigger_config,
    #         timeout=timeout,
    #         description="trigger subscription"
    #     )

    def _wait_for_subscription_complete(self, ws_request, request_id, timeout):
        """
        等待訂閱完成並收集所有事件

        Args:
            ws_request: ha.ws.request.queue 記錄
            request_id: 請求 ID
            timeout: 超時時間（秒）

        Returns:
            dict: {'success': bool, 'data': list, 'error': str}
        """
        start_time = time.time()
        poll_interval = 0.5  # 500ms 輪詢間隔（訂閱比一般請求需要更長時間）
        last_event_time = start_time
        no_event_timeout = 5  # 5 秒無新事件則認為完成
        last_event_count = 0  # 追蹤上一次的事件數量

        self._logger.debug(f"Waiting for subscription {request_id} to complete")

        while time.time() - start_time < timeout:
            # 重新讀取記錄以獲取最新狀態
            self.env.cr.commit()
            ws_request = self.env['ha.ws.request.queue'].sudo().search([
                ('id', '=', ws_request.id)
            ], limit=1)

            if not ws_request:
                return {'success': False, 'error': '訂閱記錄遺失'}

            current_state = ws_request.state
            event_count = ws_request.event_count

            self._logger.debug(f"Subscription {request_id} state: {current_state}, events: {event_count}")

            # 檢查是否完成
            if current_state == 'done':
                result = json.loads(ws_request.result) if ws_request.result else []

                # 確保 result 不是 None（處理 json.loads 可能返回 null 的情況）
                if result is None:
                    result = []

                self._logger.info(f"Subscription {request_id} completed with {len(result)} events")

                # 清理訂閱
                self._unsubscribe(ws_request.subscription_id)
                ws_request.unlink()

                return {
                    'success': True,
                    'data': result
                }

            # 檢查是否失敗
            if current_state in ('failed', 'timeout'):
                error = ws_request.error or 'Unknown error'
                self._logger.error(f"Subscription {request_id} failed: {error}")
                ws_request.unlink()
                return {'success': False, 'error': error}

            # 檢查是否有新事件（比較事件數量是否增加）
            if event_count > last_event_count:
                last_event_time = time.time()
                last_event_count = event_count
                self._logger.debug(f"New event received, total events: {event_count}")

            # 如果已經訂閱並且一段時間沒有新事件，認為完成
            if current_state in ('subscribed', 'collecting'):
                time_since_last_event = time.time() - last_event_time
                if time_since_last_event > no_event_timeout:
                    self._logger.info(f"No new events for {no_event_timeout}s, completing subscription")
                    ws_request.complete_subscription()
                    # 下一次迴圈會進入 done 狀態

            time.sleep(poll_interval)

        # 超時處理
        self._logger.error(f"Subscription {request_id} timed out")

        # 嘗試取消訂閱
        if ws_request.subscription_id:
            self._unsubscribe(ws_request.subscription_id)

        ws_request.write({'state': 'timeout', 'error': 'Subscription timeout'})

        return {'success': False, 'error': '訂閱超時'}

    def _unsubscribe(self, subscription_id):
        """
        取消訂閱

        Args:
            subscription_id: Home Assistant 訂閱 ID
        """
        if not subscription_id:
            return

        try:
            self._logger.info(f"Unsubscribing from subscription {subscription_id}")

            # 發送 unsubscribe_events 請求
            self.call_websocket_api('unsubscribe_events', {
                'subscription': subscription_id
            }, timeout=5)

        except Exception as e:
            self._logger.warning(f"Failed to unsubscribe from {subscription_id}: {e}")
    
    def _is_websocket_running(self):
        """
        檢查 WebSocket 服務是否運行
        Phase 3: 檢查特定實例的 WebSocket 服務狀態
        """
        try:
            from odoo.addons.odoo_ha_addon.models.common.websocket_thread_manager import is_websocket_service_running
            return is_websocket_service_running(self.env, instance_id=self.instance_id)
        except Exception as e:
            self._logger.warning(f"Failed to check WebSocket service status: {e}")
            return False
    
    def _create_request(self, request_id, message_type, payload):
        """
        建立 WebSocket 請求記錄
        Phase 3: 加上 ha_instance_id 欄位
        """
        ws_request = self.env['ha.ws.request.queue'].sudo().create({
            'request_id': request_id,
            'message_type': message_type,
            'payload': json.dumps(payload) if payload else None,
            'state': 'pending',
            'ha_instance_id': self.instance_id,  # Phase 3: 指定實例 ID
        })

        # 立即 commit 讓 WebSocket thread 能看到這筆記錄
        self.env.cr.commit()

        self._logger.info(f"Created WebSocket request: {request_id} (type: {message_type}, instance: {self.instance_id})")
        return ws_request
    
    def _wait_for_result(self, ws_request, request_id, timeout):
        """等待並處理請求結果"""
        start_time = time.time()
        poll_interval = 0.3  # 300ms 輪詢間隔
        poll_count = 0
        
        self._logger.debug(f"Starting polling for request {request_id}, timeout: {timeout}s")
        
        while time.time() - start_time < timeout:
            poll_count += 1
            elapsed = time.time() - start_time
            
            self._logger.debug(f"Poll #{poll_count} for request {request_id} (elapsed: {elapsed:.1f}s)")
            
            # 每次輪詢都 commit 以獲得新的 transaction snapshot
            # 這樣才能看到 WebSocket thread 更新的記錄狀態
            self.env.cr.commit()
            ws_request = self.env['ha.ws.request.queue'].sudo().search([
                ('id', '=', ws_request.id)
            ], limit=1)
            
            if not ws_request:
                self._logger.debug(f"Request record {request_id} not found (deleted)")
                return {'success': False, 'error': '請求記錄遺失'}
            
            self._logger.debug(f"Request {request_id} current state: {ws_request.state}")
            
            if ws_request.state == 'done':
                result = json.loads(ws_request.result) if ws_request.result else None
                self._logger.info(f"Request {request_id} completed successfully")
                self._logger.debug(f"Request {request_id} result data size: {len(str(result)) if result else 0} chars")
                
                # 清理請求記錄
                ws_request.unlink()
                
                return {
                    'success': True,
                    'data': result
                }
            
            elif ws_request.state in ('failed', 'timeout'):
                error = ws_request.error or 'Unknown error'
                self._logger.error(f"Request {request_id} failed: {error}")
                self._logger.debug(f"Request {request_id} failed after {poll_count} polls")
                
                # 清理請求記錄
                ws_request.unlink()
                
                return {
                    'success': False,
                    'error': error
                }
            
            # 等待一段時間再檢查
            self._logger.debug(f"Request {request_id} still {ws_request.state}, waiting {poll_interval}s...")
            time.sleep(poll_interval)
        
        # 超時處理
        elapsed = time.time() - start_time
        self._logger.error(f"Request {request_id} timed out after {elapsed:.1f}s ({poll_count} polls)")
        ws_request.write({'state': 'timeout', 'error': 'Client timeout'})
        
        return {
            'success': False,
            'error': '請求超時'
        }

def get_websocket_client(env, instance_id=None):
    """
    工廠函數：取得 WebSocket 客戶端實例

    Args:
        env: Odoo 環境物件
        instance_id: HA 實例 ID (Phase 3)，如果為 None 則使用預設實例

    Returns:
        WebSocketClient: 客戶端實例
    """
    return WebSocketClient(env, instance_id=instance_id)