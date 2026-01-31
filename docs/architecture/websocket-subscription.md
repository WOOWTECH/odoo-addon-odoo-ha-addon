# WebSocket 訂閱機制技術文件

## 概述

本文件說明 Odoo HA Addon 中 WebSocket 訂閱機制的完整實現，用於從 Home Assistant 訂閱並收集即時歷史資料流。

### 用途

- **即時歷史資料查詢**：使用 `history/stream` API 訂閱實體的狀態變化
- **批次事件收集**：在指定時間範圍內收集所有狀態變化事件
- **自動資源管理**：訂閱完成後自動取消訂閱，釋放 Home Assistant 資源

### 應用場景

- 取得實體的歷史狀態資料（替代 REST API）
- 需要完整時間範圍內的所有狀態變化
- 優先使用 WebSocket 以減少 HTTP 請求開銷

---

## 架構設計

### 跨進程通信架構

```
┌─────────────────┐         ┌───────────────────┐         ┌─────────────────┐
│  Odoo Model     │ create  │ha.ws.request.queue│  poll   │  WebSocket      │
│  (Main Process) │────────>│  (Database)       │<────────│  Service Thread │
│                 │         │                   │         │                 │
│  fetch_history()│         │  is_subscription  │         │  _handle_msg()  │
│                 │         │  subscription_id  │         │  _add_event()   │
│                 │  wait   │  events (JSON)    │ update  │                 │
│  (polling)      │<────────│  event_count      │<────────│  (async)        │
│                 │         │  state            │         │                 │
└─────────────────┘         └───────────────────┘         └─────────────────┘
        │                            │                            │
        │                            │                            │
        v                            v                            v
   等待完成                      狀態管理                    事件接收
   (timeout 60s)              (pending → subscribed         (from Home
                              → collecting → done)           Assistant)
```

### 訂閱生命週期

```
1. 創建請求
   └─> ha.ws.request.queue.create({'is_subscription': True, 'state': 'pending'})

2. WebSocket 發送訂閱
   └─> send({'type': 'history/stream', 'entity_ids': [...], ...})

3. 接收訂閱確認
   └─> 收到 {'type': 'result', 'success': True, 'result': {'subscription': 123}}
   └─> 更新狀態為 'subscribed'，記錄 subscription_id

4. 收集事件
   └─> 持續接收 {'type': 'event', 'event': {'states': {...}}}
   └─> 每個事件調用 ws_request.add_event()
   └─> 更新狀態為 'collecting'，累計 event_count

5. 完成訂閱
   └─> 5 秒無新事件 → 調用 ws_request.complete_subscription()
   └─> 或達到 timeout → 標記為 'timeout'
   └─> 發送 unsubscribe_events 清理資源

6. 清理記錄
   └─> 返回結果後刪除 ha.ws.request.queue 記錄
```

---

## 核心組件

### 1. `ha.ws.request.queue` 模型

位置：`models/ha_ws_request_queue.py`

#### 訂閱相關欄位

```python
class HAWebSocketRequestQueue(models.Model):
    _name = 'ha.ws.request.queue'

    # 訂閱標記
    is_subscription = fields.Boolean(
        string='Is Subscription',
        default=False,
        help='標記此請求為訂閱類型'
    )

    # Home Assistant 返回的訂閱 ID
    subscription_id = fields.Integer(
        string='Subscription ID',
        help='用於取消訂閱時指定目標'
    )

    # 收集的事件（JSON 陣列）
    events = fields.Text(
        string='Events',
        help='收集的事件 JSON 陣列，格式：[{event1}, {event2}, ...]'
    )

    # 事件數量
    event_count = fields.Integer(
        string='Event Count',
        default=0,
        help='已收集的事件數量'
    )

    # 狀態（擴充支援訂閱）
    state = fields.Selection([
        ('pending', 'Pending'),      # 等待處理
        ('processing', 'Processing'), # 處理中
        ('subscribed', 'Subscribed'), # ✨ 已訂閱
        ('collecting', 'Collecting'), # ✨ 收集事件中
        ('done', 'Done'),            # 完成
        ('failed', 'Failed'),        # 失敗
        ('timeout', 'Timeout')       # 超時
    ])
```

#### 關鍵方法

**`add_event(event_data)`**

添加事件到訂閱記錄：

```python
def add_event(self, event_data):
    """
    添加事件到訂閱請求

    Args:
        event_data (dict): Home Assistant 事件數據
    """
    self.ensure_one()

    if not self.is_subscription:
        return

    # 解析現有事件
    events = json.loads(self.events) if self.events else []

    # 添加新事件
    events.append(event_data)

    # 更新記錄
    self.write({
        'events': json.dumps(events),
        'event_count': len(events),
        'state': 'collecting'
    })
```

**`complete_subscription()`**

完成訂閱，將事件轉為結果：

```python
def complete_subscription(self):
    """
    完成訂閱，將收集的事件設為結果
    """
    self.ensure_one()

    if not self.is_subscription:
        return

    events = json.loads(self.events) if self.events else []

    self.write({
        'result': json.dumps(events),
        'state': 'done'
    })
```

---

### 2. `WebSocketClient` 客戶端

位置：`models/common/websocket_client.py`

#### 訂閱方法

**`subscribe_history_stream(entity_ids, start_time, end_time, timeout=60)`**

訂閱歷史資料流（採用重構後的簡化實現）：

```python
def subscribe_history_stream(self, entity_ids, start_time, end_time, timeout=60):
    """
    訂閱歷史資料流 (history/stream)

    Args:
        entity_ids (list): 實體 ID 列表，如 ['sensor.temperature']
        start_time (str): 開始時間 (ISO 8601 格式)
        end_time (str): 結束時間 (ISO 8601 格式)
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
```

**設計理念**：

- ✅ **職責單一**：只負責構建 `history/stream` 專屬的 payload
- ✅ **代碼重用**：訂閱流程由通用函數 `_create_subscription_request()` 處理
- ✅ **易於擴展**：新增其他訂閱類型（如 `subscribe_events`）遵循相同模式

#### 通用訂閱函數

**`_create_subscription_request(message_type, payload, timeout=60, description=None)`**

所有訂閱類型共用的核心邏輯：

```python
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
        })

        self.env.cr.commit()

        self._logger.info(f"Created subscription request: {request_id} (type: {message_type})")

        # 等待訂閱完成並收集事件
        result = self._wait_for_subscription_complete(ws_request, request_id, timeout)

        return result

    except Exception as e:
        self._logger.error(f"Subscription failed ({desc}): {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
```

**未來擴展範例**：

新增其他訂閱類型非常簡單：

```python
def subscribe_events(self, event_type, timeout=60):
    """訂閱特定類型的事件"""
    payload = {'event_type': event_type}
    return self._create_subscription_request(
        message_type='subscribe_events',
        payload=payload,
        timeout=timeout,
        description=f"events for {event_type}"
    )

def subscribe_trigger(self, trigger_config, timeout=60):
    """訂閱觸發器狀態變化"""
    return self._create_subscription_request(
        message_type='subscribe_trigger',
        payload=trigger_config,
        timeout=timeout,
        description="trigger subscription"
    )
```

#### 等待訂閱完成

**`_wait_for_subscription_complete(ws_request, request_id, timeout)`**

```python
def _wait_for_subscription_complete(self, ws_request, request_id, timeout):
    """
    等待訂閱完成並收集所有事件

    完成條件：
    - 狀態變為 'done'
    - 5 秒內無新事件（自動完成）
    - 達到 timeout（超時）
    """
    start_time = time.time()
    poll_interval = 0.5  # 500ms 輪詢間隔
    last_event_time = start_time
    no_event_timeout = 5  # 5 秒無新事件則認為完成
    last_event_count = 0  # 追蹤上一次的事件數量

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

        # ✓ 檢查是否完成
        if current_state == 'done':
            result = json.loads(ws_request.result) if ws_request.result else []

            # 確保 result 不是 None（處理 json.loads 可能返回 null 的情況）
            if result is None:
                result = []

            # 清理訂閱
            self._unsubscribe(ws_request.subscription_id)
            ws_request.unlink()

            return {
                'success': True,
                'data': result
            }

        # ✗ 檢查是否失敗
        if current_state in ('failed', 'timeout'):
            error = ws_request.error or 'Unknown error'
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
    if ws_request.subscription_id:
        self._unsubscribe(ws_request.subscription_id)

    ws_request.write({'state': 'timeout', 'error': 'Subscription timeout'})

    return {'success': False, 'error': '訂閱超時'}
```

#### 取消訂閱

**`_unsubscribe(subscription_id)`**

```python
def _unsubscribe(self, subscription_id):
    """
    取消訂閱，釋放 Home Assistant 資源

    Args:
        subscription_id (int): Home Assistant 訂閱 ID
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
```

---

### 3. `HassWebSocketService` 處理服務

位置：`models/common/hass_websocket_service.py`

#### 訂閱追蹤

在 `__init__` 中初始化訂閱字典：

```python
def __init__(self, db_name):
    self.db_name = db_name
    self._subscriptions = {}  # {message_id: {'request_id': str, 'subscription_id': int}}
    # ...
```

#### 訂閱請求處理

**`_process_subscription_request(request_data, payload)`**

```python
async def _process_subscription_request(self, request_data, payload):
    """
    處理訂閱請求（history/stream）

    1. 發送訂閱請求到 Home Assistant
    2. 追蹤 message_id 和 request_id 的映射
    3. 等待訂閱確認（result 訊息）
    """
    message_id = self._next_id
    self._next_id += 1

    # 追蹤訂閱
    self._subscriptions[message_id] = {
        'request_id': request_data.request_id,
        'subscription_id': None  # 待 result 訊息填入
    }

    # 發送訂閱請求
    message = {
        'id': message_id,
        'type': request_data.message_type,  # 'history/stream'
        **payload
    }

    await self._ws.send(json.dumps(message))

    # 更新請求狀態為 processing
    self._update_request_status(request_data.request_id, 'processing')
```

#### 訂閱結果處理

**`_handle_subscription_result(message_id, data)`**

接收訂閱確認：

```python
async def _handle_subscription_result(self, message_id, data):
    """
    處理訂閱的 result 訊息（訂閱確認）

    收到格式：
    {
      "id": 49,
      "type": "result",
      "success": true,
      "result": {
        "subscription": 123  // ← Home Assistant 訂閱 ID
      }
    }
    """
    subscription_info = self._subscriptions.get(message_id)
    if not subscription_info:
        return

    request_id = subscription_info['request_id']

    if data.get('success', True):
        # 訂閱成功，記錄 subscription_id
        subscription_id = data.get('result', {}).get('subscription')

        # 更新訂閱字典
        self._subscriptions[message_id]['subscription_id'] = subscription_id

        # 更新數據庫記錄
        self._update_subscription_status(request_id, subscription_id, 'subscribed')
    else:
        # 訂閱失敗
        error_msg = data.get('error', {}).get('message', 'Unknown error')
        self._subscription_failed(request_id, error_msg)

        # 移除訂閱追蹤
        del self._subscriptions[message_id]
```

#### 事件接收處理

**`_handle_subscription_event(message_id, data)`**

接收並保存事件：

```python
async def _handle_subscription_event(self, message_id, data):
    """
    處理訂閱的 event 訊息

    收到格式：
    {
      "id": 49,
      "type": "event",
      "event": {
        "states": {
          "sensor.temperature": [
            {"state": "22.5", "last_changed": "...", ...}
          ]
        },
        "start_time": 1760957597.057,
        "end_time": 1761043997.057
      }
    }
    """
    subscription_info = self._subscriptions.get(message_id)
    if not subscription_info:
        return

    request_id = subscription_info['request_id']
    event_data = data.get('event', {})

    # 將事件添加到訂閱記錄
    self._add_event_to_subscription(request_id, event_data)
```

#### 更新訂閱狀態

**`_update_subscription_status(request_id, subscription_id, status)`**

```python
def _update_subscription_status(self, request_id, message_id, status):
    """
    更新訂閱狀態並記錄 subscription_id
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
                    'subscription_id': message_id  # 記錄 HA 的 subscription_id
                })
                cr.commit()

    except Exception as e:
        self._logger.error(f"Failed to update subscription status: {e}")
```

**`_add_event_to_subscription(request_id, event_data)`**

```python
def _add_event_to_subscription(self, request_id, event_data):
    """
    添加事件到訂閱記錄
    """
    try:
        with db.db_connect(self.db_name).cursor() as cr:
            env = api.Environment(cr, 1, {})

            ws_request = env['ha.ws.request.queue'].sudo().search([
                ('request_id', '=', request_id)
            ], limit=1)

            if ws_request:
                ws_request.add_event(event_data)  # 調用模型方法
                cr.commit()

    except Exception as e:
        self._logger.error(f"Failed to add event: {e}")
```

---

### 4. 應用層使用

位置：`models/ha_entity_history.py`

#### 歷史資料查詢

**`_fetch_history_via_websocket(entity_id)`**

```python
def _fetch_history_via_websocket(self, entity_id):
    """
    使用 WebSocket API 取得歷史資料
    使用 history/stream 訂閱機制
    """
    try:
        from odoo.addons.odoo_ha_addon.models.common.websocket_client import get_websocket_client

        client = get_websocket_client(self.env)

        # 使用 history/stream 訂閱 API
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        # 使用訂閱方法（會自動收集事件並取消訂閱）
        result = client.subscribe_history_stream(
            entity_ids=[entity_id],
            start_time=yesterday.isoformat(),
            end_time=today.isoformat(),
            timeout=60  # 60 秒 timeout
        )

        if result['success']:
            events = result['data']
            self._logger.info(
                f"WebSocket history stream successful for {entity_id}, "
                f"received {len(events)} events"
            )

            # 轉換事件格式為歷史資料格式
            return self._convert_stream_events_to_history(events, entity_id)
        else:
            self._logger.warning(
                f"WebSocket history stream failed for {entity_id}: "
                f"{result.get('error')}"
            )
            return None

    except Exception as e:
        self._logger.warning(f"WebSocket history query failed for {entity_id}: {e}")
        return None
```

#### 格式標準化

**`_normalize_state_format(state_item, entity_id)`**

處理 Home Assistant WebSocket API 的縮寫格式：

```python
def _normalize_state_format(self, state_item, entity_id):
    """
    標準化狀態項目格式（處理 HA WebSocket API 的縮寫格式）

    HA WebSocket API 可能返回縮寫格式：
    {'s': 'on', 'a': {...}, 'lu': 1761002858.785457, 'lc': 1761002858.785457}

    需要轉換為完整格式：
    {'state': 'on', 'attributes': {...}, 'last_updated': '2025-10-21T...', ...}

    Args:
        state_item: 狀態項目（可能是縮寫或完整格式）
        entity_id: 實體 ID（用於日誌）

    Returns:
        dict or None: 標準化後的狀態項目，失敗時返回 None
    """
    if not isinstance(state_item, dict):
        return None

    # 檢測是否為縮寫格式（'s' 欄位存在）
    if 's' in state_item:
        # 縮寫格式轉換
        try:
            normalized = {
                'state': state_item.get('s'),
                'attributes': state_item.get('a', {}),
                'entity_id': entity_id,
            }

            # 轉換 Unix timestamp 為 ISO 格式
            if 'lu' in state_item:
                normalized['last_updated'] = datetime.fromtimestamp(
                    state_item['lu'], tz=timezone.utc
                ).isoformat()

            if 'lc' in state_item:
                normalized['last_changed'] = datetime.fromtimestamp(
                    state_item['lc'], tz=timezone.utc
                ).isoformat()
            else:
                # 如果沒有 last_changed，使用 last_updated
                normalized['last_changed'] = normalized.get('last_updated')

            self._logger.debug(f"Converted abbreviated format for {entity_id}: {state_item['s']}")
            return normalized

        except Exception as e:
            self._logger.error(f"Failed to convert abbreviated format for {entity_id}: {e}")
            return None

    # 完整格式（REST API 或已標準化格式）
    elif 'state' in state_item:
        # 確保包含 entity_id
        if 'entity_id' not in state_item:
            state_item['entity_id'] = entity_id
        return state_item

    else:
        # 無法識別的格式
        return None
```

**縮寫格式欄位對應**：

- `'s'` → `'state'`
- `'a'` → `'attributes'`
- `'lu'` → `'last_updated'` (Unix timestamp 轉 ISO 8601)
- `'lc'` → `'last_changed'` (Unix timestamp 轉 ISO 8601)

**使用場景**：

- WebSocket API 返回縮寫格式以減少傳輸量
- 自動檢測並轉換為標準格式
- 統一處理兩種格式，無需呼叫方關心差異

#### 事件格式轉換

**`_convert_stream_events_to_history(events, entity_id)`**

```python
def _convert_stream_events_to_history(self, events, entity_id):
    """
    將 history/stream 事件轉換為歷史資料格式

    根據文件，每個事件格式：
    {
      "states": {
        "entity_id": [
          {"state": "...", "last_changed": "...", ...}
        ]
      },
      "start_time": 1760957597.057,  // Unix timestamp (秒)
      "end_time": 1761043997.057
    }

    實際上 HA WebSocket API 返回的是縮寫格式：
    {"states": {"entity_id": [{"s": "on", "a": {...}, "lu": 123.456, "lc": 123.456}]}}

    此方法會自動處理兩種格式（通過 _normalize_state_format）。

    Args:
        events: history/stream 返回的事件列表
        entity_id: 實體 ID

    Returns:
        list: 轉換後的歷史資料（與 REST API 格式相同）[[...]]
    """
    if not events:
        return None

    history_records = []

    for event in events:
        states = event.get('states', {})

        if not states:
            continue

        # states 是字典，key 是 entity_id
        if entity_id in states:
            state_list = states[entity_id]

            # state_list 是該實體的狀態列表
            if isinstance(state_list, list):
                for state_item in state_list:
                    # 確保 state_item 包含必要欄位
                    if isinstance(state_item, dict):
                        # 處理縮寫格式（HA WebSocket API 返回）或完整格式（REST API）
                        normalized_item = self._normalize_state_format(state_item, entity_id)
                        if normalized_item:
                            history_records.append(normalized_item)
                        else:
                            self._logger.warning(f"Invalid state item format: {state_item}")

    if not history_records:
        self._logger.warning(
            f"No valid history records extracted from {len(events)} events "
            f"for {entity_id}"
        )
        return None

    self._logger.info(f"Converted {len(history_records)} history records for {entity_id}")

    # 返回與 REST API 相同的格式：[[...]]
    return [history_records]
```

---

## Home Assistant API 規範

本實現使用 Home Assistant 的 `history/stream` WebSocket API。

### 完整 API 規範

詳細的 API 參數、請求格式、回應結構、使用案例等，請參閱：

**📄 [`docs/homeassistant-api/homeassistant-websocket-history.md`](../homeassistant-api/homeassistant-websocket-history.md)**

該文件包含：

- `history/stream` API 完整規範
- 請求參數說明與預設值
- 請求與回應範例
- 事件格式結構
- API 已知問題與注意事項
- 與其他歷史 API 的比較

### 快速參考

#### 訂閱請求

```json
{
  "id": 49,
  "type": "history/stream",
  "entity_ids": ["sensor.temperature"],
  "start_time": "2025-10-21T00:00:00+00:00",
  "end_time": "2025-10-22T00:00:00+00:00",
  "no_attributes": false
}
```

#### 事件格式

```json
{
  "type": "event",
  "event": {
    "states": {
      "sensor.temperature": [
        {"state": "22.5", "last_changed": "...", "attributes": {...}}
      ]
    }
  }
}
```

#### ⚠️ 重要提醒

務必明確設定 `no_attributes: false`，避免單一實體返回空結果的已知問題。詳見 API 規範文件。

---

## 使用範例

### 基本使用

```python
from odoo.addons.odoo_ha_addon.models.common.websocket_client import get_websocket_client

# 在 Odoo 模型中
client = get_websocket_client(self.env)

# 訂閱歷史資料
result = client.subscribe_history_stream(
    entity_ids=['sensor.temperature'],
    start_time='2025-10-21T00:00:00+00:00',
    end_time='2025-10-22T00:00:00+00:00',
    timeout=60
)

if result['success']:
    events = result['data']
    print(f"收集到 {len(events)} 個事件")

    for event in events:
        states = event.get('states', {})
        # 處理狀態資料...
else:
    print(f"訂閱失敗: {result['error']}")
```

### 批次查詢多個實體

```python
result = client.subscribe_history_stream(
    entity_ids=[
        'sensor.temperature',
        'sensor.humidity',
        'sensor.pressure'
    ],
    start_time=yesterday.isoformat(),
    end_time=today.isoformat(),
    timeout=120  # 增加 timeout 以應對大量數據
)
```

### 降級策略（WebSocket → REST）

```python
def _fetch_entity_history(self, entity_id):
    """
    取得實體歷史，優先 WebSocket，失敗則用 REST
    """
    # 嘗試 WebSocket
    history_data = self._fetch_history_via_websocket(entity_id)

    # 失敗則降級為 REST API
    if history_data is None:
        self._logger.info(f"WebSocket failed, falling back to REST API")
        history_data = self._fetch_history_via_rest(entity_id)

    return history_data
```

---

## 最佳實踐

### 1. 參數設定

#### ⚠️ 避免已知問題

**問題**：單一實體且省略 `no_attributes` 參數時可能返回空結果

**解決方案**：明確設定所有參數

```python
payload = {
    'entity_ids': entity_ids,
    'start_time': start_time,
    'end_time': end_time,
    'include_start_time_state': True,
    'significant_changes_only': False,
    'minimal_response': False,
    'no_attributes': False,  # ← 關鍵：明確設為 False
}
```

### 2. Timeout 設定

根據查詢範圍調整 timeout：

```python
# 短期查詢（1 天）
timeout = 60  # 60 秒

# 長期查詢（7 天）
timeout = 180  # 3 分鐘

# 大量實體
timeout = 300  # 5 分鐘
```

### 3. 資源清理

**自動清理**：訂閱完成後自動取消訂閱

```python
# 在 _wait_for_subscription_complete 中
if current_state == 'done':
    # 清理訂閱
    self._unsubscribe(ws_request.subscription_id)
    ws_request.unlink()  # 刪除請求記錄
```

**定期清理**：清理舊請求記錄

```python
# 設定 cron job
self.env['ha.ws.request.queue'].cleanup_old_requests()
```

### 4. 錯誤處理

```python
try:
    result = client.subscribe_history_stream(...)

    if result['success']:
        # 處理成功
        pass
    else:
        # 記錄錯誤
        self._logger.error(f"Subscription failed: {result['error']}")

        # 降級策略
        fallback_data = self._fetch_via_rest()

except Exception as e:
    self._logger.error(f"Unexpected error: {e}", exc_info=True)
    # 降級處理
```

### 5. 日誌記錄

適當的日誌層級：

```python
# INFO: 訂閱生命週期事件
self._logger.info(f"Starting subscription for {entity_id}")
self._logger.info(f"Subscription completed with {len(events)} events")

# DEBUG: 詳細處理過程
self._logger.debug(f"Received event: {event_data}")
self._logger.debug(f"Current state: {current_state}, events: {event_count}")

# WARNING: 非致命問題
self._logger.warning(f"Empty states in event for {entity_id}")

# ERROR: 錯誤和異常
self._logger.error(f"Subscription failed: {error}", exc_info=True)
```

---

## 故障排除

### 問題 1: 訂閱一直處於 'pending' 狀態

**可能原因**：

- WebSocket 服務未啟動
- 請求未被 WebSocket 服務讀取

**排查步驟**：

```python
# 檢查 WebSocket 服務狀態
env['ha.entity'].check_websocket_status()

# 檢查請求隊列
env['ha.ws.request.queue'].search([('state', '=', 'pending')])

# 重啟 WebSocket 服務
env['ha.entity'].restart_websocket_service()
```

### 問題 2: 收集到的事件為空

**可能原因**：

- 時間範圍內無狀態變化
- 參數設定錯誤（觸發已知問題）
- entity_id 不存在

**排查步驟**：

```python
# 檢查事件收集情況
ws_request = env['ha.ws.request.queue'].search([
    ('request_id', '=', request_id)
])
print(f"State: {ws_request.state}")
print(f"Event count: {ws_request.event_count}")
print(f"Events: {ws_request.events}")

# 確認參數設定
payload = json.loads(ws_request.payload)
print(f"no_attributes: {payload.get('no_attributes')}")  # 應為 False
```

### 問題 3: 訂閱超時

**可能原因**：

- 查詢範圍過大
- Home Assistant 回應緩慢
- 網路問題

**解決方案**：

```python
# 增加 timeout
result = client.subscribe_history_stream(
    entity_ids=[entity_id],
    start_time=start_time,
    end_time=end_time,
    timeout=180  # 增加到 3 分鐘
)

# 縮小查詢範圍
# 改為查詢最近 12 小時而非 24 小時
```

### 問題 4: subscription_id 為 None

**可能原因**：

- 未收到訂閱確認（result 訊息）
- 訂閱請求失敗

**排查步驟**：

```python
# 檢查 WebSocket 日誌
docker compose -f docker-compose-18.yml logs -f web | grep "subscription"

# 檢查訂閱追蹤
# 在 hass_websocket_service.py 中添加日誌
self._logger.debug(f"Current subscriptions: {self._subscriptions}")
```

### 問題 5: 取消訂閱失敗

**可能原因**：

- subscription_id 無效
- Home Assistant 已自動清理訂閱

**處理**：

```python
def _unsubscribe(self, subscription_id):
    if not subscription_id:
        return

    try:
        self.call_websocket_api('unsubscribe_events', {
            'subscription': subscription_id
        }, timeout=5)
    except Exception as e:
        # 記錄警告但不中斷流程
        self._logger.warning(f"Failed to unsubscribe: {e}")
```

### 問題 6: 事件格式無法識別（縮寫格式）

**症狀**：

- 日誌顯示 `Invalid state item format: {'s': 'on', 'a': {...}, 'lu': ...}`
- 或 `No valid history records extracted from N events`

**原因**：

- Home Assistant WebSocket API 返回縮寫格式
- `_normalize_state_format()` 方法未正確處理

**解決方案**：

已在 v1.2 版本中修復，確保使用最新版本的代碼。

**驗證修復**：

```python
# 檢查日誌應該看到成功轉換的訊息
# DEBUG: Converted abbreviated format for switch.test_switch: on
# INFO: Converted 2 history records for switch.test_switch
# INFO: Batch create completed: 1 created, 1 skipped
```

**縮寫格式欄位對應**：

- `'s'` → `'state'`
- `'a'` → `'attributes'`
- `'lu'` → `'last_updated'` (Unix timestamp)
- `'lc'` → `'last_changed'` (Unix timestamp)

---

## 性能優化建議

### 1. 批次處理

一次訂閱多個實體，而非逐個訂閱：

```python
# ✓ 好的做法
result = client.subscribe_history_stream(
    entity_ids=['sensor.temp1', 'sensor.temp2', 'sensor.temp3'],
    ...
)

# ✗ 避免
for entity_id in entity_ids:
    result = client.subscribe_history_stream(entity_ids=[entity_id], ...)
```

### 2. 最小化回應

當只需要狀態值時：

```python
payload = {
    'minimal_response': True,   # 只返回 state 和 last_changed
    'no_attributes': True,       # 不返回 attributes
    'significant_changes_only': True,  # 過濾微小變化
}
```

### 3. 合理設定查詢範圍

```python
# 根據需求選擇合適的時間範圍

# 即時監控：最近 1 小時
start_time = (datetime.now() - timedelta(hours=1)).isoformat()

# 短期分析：最近 1 天
start_time = (datetime.now() - timedelta(days=1)).isoformat()

# 週報：最近 7 天（考慮使用 statistics_during_period）
start_time = (datetime.now() - timedelta(days=7)).isoformat()
```

### 4. 並行處理

在 WebSocket 服務中使用 asyncio 並行處理多個訂閱。

---

## 相關文件

- **API 規範**：`docs/homeassistant-api/homeassistant-websocket-history.md`
- **WebSocket 整合計劃**：`docs/tasks/websocket-integration-plan.md`
- **REST API 文件**：`docs/homeassistant-api/HA_串接文件/HA 串接文件.md`

---

## 版本歷史

- **v1.2** (2025-10-22): 修復訂閱完成檢測邏輯，新增縮寫格式支持

  - 修復訂閱卡在 'collecting' 狀態的問題
    - 改用 event_count 追蹤來判斷是否有新事件
    - 修正完成邏輯：只在事件數量增加時更新 last_event_time
  - 新增 `_normalize_state_format()` 處理 HA WebSocket API 縮寫格式
    - 支持縮寫欄位：'s', 'a', 'lu', 'lc'
    - 自動將 Unix timestamp 轉換為 ISO 8601 格式
    - 透明處理兩種格式，無需呼叫方關心差異
  - 新增 None 值防護（處理 `json.loads("null")` 返回 None）
  - 文件同步更新，確保與實際實現一致

- **v1.1** (2025-10-22): 架構重構，提升可擴展性

  - 抽離通用訂閱函數 `_create_subscription_request()`
  - `subscribe_history_stream()` 簡化為只構建 payload
  - 遵循單一職責原則和 DRY 原則
  - 為未來其他訂閱類型（如 `subscribe_events`）提供可重用架構
  - 減少代碼重複約 50%

- **v1.0** (2025-10-22): 初始版本，完整訂閱機制實現
  - 支援 `history/stream` API
  - 自動事件收集和清理
  - 完整錯誤處理和降級策略
