# WebSocket 整合 Home Assistant 實作規劃

## 專案概述

### 目標

將 Odoo HA Addon 從 REST API 輪詢機制升級為 WebSocket 即時連線，實現：

- 即時狀態更新，無需手動同步
- 減少 API 請求頻率，提升效能
- 更好的用戶體驗，即時反映 HA 裝置狀態變化

### 現有架構分析

- **配置**: `res_config_settings.py` 已有 `ha_api_url` 和 `ha_api_token`
- **REST API**: `models/common/hass_rest_api.py` 處理 HTTP 請求
- **資料模型**: `ha.entity` 和 `ha.entity.history` 管理實體和歷史資料
- **前端服務**: `ha_data_service.js` 提供 30 秒快取的資料服務
- **Threading**: 使用 Python threading 執行長時間運行的 WebSocket 服務

### WebSocket URL 推導

- REST API: `http://IP_ADDRESS:8123/`
- WebSocket: `ws://IP_ADDRESS:8123/api/websocket`

---

## 實作階段規劃

### 階段 1: WebSocket 服務核心 (預估: 2 小時)

#### 1.1 建立 WebSocket 服務類別

- **檔案**: `models/common/hass_websocket_service.py`
- **功能**:
  - WebSocket 連線管理
  - HA 認證流程處理
  - 訊息接收和解析
  - 錯誤處理和重連機制

#### 1.2 實作 URL 推導邏輯

- 從現有 `ha_api_url` 推導 WebSocket URL
- 支援 HTTP/HTTPS 到 WS/WSS 的轉換
- 處理不同的 URL 格式

#### 進度追蹤

| 任務                    | 狀態    | 完成時間   | 備註                      |
| ----------------------- | ------- | ---------- | ------------------------- |
| 建立 WebSocket 服務檔案 | ✅ 完成 | 2025-09-29 | hass_websocket_service.py |
| 實作連線管理            | ✅ 完成 | 2025-09-29 | 包含重連機制              |
| 實作 URL 推導           | ✅ 完成 | 2025-09-29 | 自動從 ha_api_url 推導    |
| 實作 HA 認證流程        | ✅ 完成 | 2025-09-29 | 完整 WebSocket 認證       |
| 實作錯誤處理            | ✅ 完成 | 2025-09-29 | 自動重連和日誌            |

---

### 階段 2: Threading 整合 (預估: 1 小時)

#### 2.1 WebSocket Thread Manager

- **檔案**: `models/common/websocket_thread_manager.py`
- **功能**:
  - 管理背景執行緒中的 WebSocket 服務
  - 使用 `threading.Thread` 建立 daemon thread
  - 整合 asyncio 事件循環在執行緒中運行
  - 提供 start/stop/status 控制功能

#### 2.2 Cron Job 監控機制

- **檔案**: `data/websocket_cron.xml`
- **功能**:
  - 每分鐘檢查 WebSocket 服務狀態
  - 自動重啟停止的服務
  - 避免重複啟動

#### 2.3 Post-Load Hook 自動啟動

- **檔案**: `hooks.py`
- **功能**:
  - Odoo 啟動時自動執行 `post_load_hook()`
  - 為每個資料庫啟動 WebSocket 服務
  - 檢查 addon 是否已安裝

#### 進度追蹤

| 任務                          | 狀態    | 完成時間   | 備註                            |
| ----------------------------- | ------- | ---------- | ------------------------------- |
| 建立 websocket_thread_manager | ✅ 完成 | 2025-10-01 | threading 版本                  |
| 實作執行緒管理功能            | ✅ 完成 | 2025-10-01 | start/stop/is_running           |
| 實作服務狀態檢查              | ✅ 完成 | 2025-10-01 | \_cron_ensure_websocket_service |
| 建立 Cron Job                 | ✅ 完成 | 2025-09-29 | websocket_cron.xml              |
| 實作 post_load_hook           | ✅ 完成 | 2025-10-01 | 自動啟動服務                    |
| 測試 Threading 啟動           | ✅ 完成 | 2025-10-01 | 運行 8+ 小時無 timeout          |

---

### 階段 3: 即時資料處理 (預估: 2 小時)

#### 3.1 WebSocket 事件處理

- **功能**:
  - 處理 `state_changed` 事件
  - 更新 `ha.entity` 資料
  - 建立 `ha.entity.history` 記錄

#### 3.2 Odoo Bus 整合

- **檔案**: 新增 `models/ha_realtime_update.py`
- **功能**:
  - 使用 Odoo Bus 推送即時更新
  - 通知前端資料變更
  - 管理訂閱者列表

#### 進度追蹤

| 任務                | 狀態    | 完成時間   | 備註                      |
| ------------------- | ------- | ---------- | ------------------------- |
| 實作事件處理器      | ✅ 完成 | 2025-09-29 | hass_websocket_service.py |
| 整合 ha.entity 更新 | ✅ 完成 | 2025-09-29 | \_update_entity_in_odoo   |
| 整合 history 記錄   | ✅ 完成 | 2025-09-29 | 自動建立歷史記錄          |
| 建立 Bus 通知機制   | ✅ 完成 | 2025-09-29 | ha_realtime_update.py     |

---

### 階段 4: 前端即時整合 (預估: 1 小時)

#### 4.1 升級前端服務

- **檔案**: `static/src/services/ha_data_service.js`
- **功能**:
  - 監聽 Odoo Bus 事件
  - 實作智能快取失效
  - 自動重新載入資料

#### 4.2 組件自動更新

- 確保圖表組件自動重新渲染
- 更新實體狀態顯示
- 保持用戶介面即時性

#### 進度追蹤

| 任務              | 狀態      | 完成時間   | 備註                |
| ----------------- | --------- | ---------- | ------------------- |
| 新增 Bus 事件監聽 | ✅ 完成   | 2025-09-29 | ha_data_service.js  |
| 實作智能快取失效  | ✅ 完成   | 2025-09-29 | clearCacheForEntity |
| 測試組件自動更新  | ⏳ 待開始 |            | 需要實際測試        |

---

### 階段 5: 測試和優化 (預估: 1 小時)

#### 5.1 系統測試

- WebSocket 連線穩定性測試
- 錯誤恢復機制測試
- 效能影響評估

#### 5.2 監控和日誌

- WebSocket 連線狀態監控
- 詳細的錯誤日誌記錄
- 效能指標追蹤

#### 進度追蹤

| 任務           | 狀態      | 完成時間 | 備註 |
| -------------- | --------- | -------- | ---- |
| 連線穩定性測試 | ⏳ 待開始 |          |      |
| 錯誤恢復測試   | ⏳ 待開始 |          |      |
| 效能測試       | ⏳ 待開始 |          |      |
| 加入監控日誌   | ⏳ 待開始 |          |      |

---

## 技術架構設計

### 系統架構總覽

```mermaid
graph TB
    subgraph "Odoo Server"
        subgraph "Main Process"
            PostHook[Post-Load Hook<br/>啟動 WebSocket]
            CronJob[Cron Job<br/>每分鐘檢查]
            Manager[WebSocket Thread Manager<br/>start/stop/status]
        end

        subgraph "Background Thread"
            WSService[WebSocket Service<br/>connect & listen]
            Heartbeat[Heartbeat Loop<br/>每 10 秒更新]
            QueueProcessor[Request Queue Processor<br/>處理 API 請求]
        end

        subgraph "Worker Process"
            Controller[HTTP Controller<br/>API endpoints]
            Models[Odoo Models<br/>ha.entity]
        end

        subgraph "Database"
            ConfigParam[(ir.config_parameter<br/>配置 & 心跳)]
            WSQueue[(ws.request.queue<br/>請求隊列)]
            HAEntity[(ha.entity<br/>實體資料)]
        end
    end

    subgraph "Home Assistant"
        HAWS[WebSocket API<br/>ws://host:8123/api/websocket]
    end

    subgraph "Frontend"
        Dashboard[Dashboard UI]
        Service[HaDataService<br/>資料服務]
    end

    PostHook -->|啟動| Manager
    CronJob -->|檢查 & 重啟| Manager
    Manager -->|建立執行緒| WSService

    WSService <-->|認證 & 訊息| HAWS
    WSService -->|定期更新| Heartbeat
    WSService -->|監聽| QueueProcessor

    Heartbeat -->|寫入時間戳| ConfigParam
    QueueProcessor -->|讀取請求| WSQueue
    QueueProcessor -->|更新結果| WSQueue
    WSService -->|更新狀態| HAEntity

    Controller -->|創建請求| WSQueue
    Controller -->|輪詢結果| WSQueue
    Controller -->|檢查心跳| ConfigParam

    Dashboard -->|RPC 請求| Controller
    Dashboard -->|讀取資料| Service
    Service -->|API 請求| Controller

    Models -->|狀態檢查| ConfigParam
    Models -->|讀取資料| HAEntity

    style WSService fill:#87CEEB
    style Heartbeat fill:#90EE90
    style QueueProcessor fill:#FFE4B5
    style HAWS fill:#DDA0DD
```

### WebSocket 服務架構

```python
class HassWebSocketService:
    def __init__(self, env):
        self.env = env
        self.db_name = env.cr.dbname
        self._running = False
        self._websocket = None

    def get_websocket_url(self):
        """從 ha_api_url 推導 WebSocket URL"""

    async def connect_and_listen(self):
        """主要的 WebSocket 連線邏輯"""

    async def _authenticate(self, websocket, token):
        """HA WebSocket 認證"""

    async def _handle_message(self, message):
        """處理接收到的訊息"""
```

### Threading 整合（支援多資料庫）

```python
# 在 websocket_thread_manager.py 中
# 全域變數：支援多資料庫連線
_websocket_connections = {
    'db_name': {
        'thread': Thread,
        'stop_event': Event,
        'config': {'ha_url': ..., 'ha_token': ...}
    }
}
_connections_lock = threading.Lock()

def _run_websocket_in_thread(db_name, ha_url, ha_token, stop_event):
    """在執行緒中運行 WebSocket 服務"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    service = HassWebSocketService(
        env=None,
        db_name=db_name,
        ha_url=ha_url,
        ha_token=ha_token
    )

    # 運行直到 stop_event 被設置
    loop.run_until_complete(service.connect_and_listen())

    # 清理連線記錄
    with _connections_lock:
        if db_name in _websocket_connections:
            del _websocket_connections[db_name]

def start_websocket_service(env):
    """啟動 WebSocket 服務（支援多資料庫）"""
    db_name = env.cr.dbname

    with _connections_lock:
        # 檢查該資料庫是否已有連線
        if db_name in _websocket_connections:
            conn = _websocket_connections[db_name]
            if conn['thread'].is_alive():
                return

        # 建立該資料庫專用的 stop_event
        stop_event = threading.Event()

        thread = threading.Thread(
            target=_run_websocket_in_thread,
            args=(db_name, ha_url, ha_token, stop_event),
            daemon=True,
            name=f"HomeAssistantWebSocket-{db_name}"
        )

        _websocket_connections[db_name] = {
            'thread': thread,
            'stop_event': stop_event,
            'config': {'ha_url': ha_url, 'ha_token': ha_token}
        }

        thread.start()

def is_websocket_service_running(env=None):
    """
    檢查 WebSocket 服務狀態（支援跨 process）
    使用心跳機制進行可靠的狀態檢查
    """
    import os

    if env is None:
        with _connections_lock:
            return len(_websocket_connections) > 0

    db_name = env.cr.dbname

    # 主 process：直接檢查執行緒（即時）
    with _connections_lock:
        if db_name in _websocket_connections:
            conn = _websocket_connections[db_name]
            is_alive = conn['thread'].is_alive()
            _logger.debug(
                f"[PID {os.getpid()}] Found connection for {db_name}, "
                f"thread is_alive={is_alive}"
            )
            return is_alive

    # Worker process：使用心跳機制（直接 SQL 查詢）
    from datetime import datetime, timezone
    from odoo.sql_db import db_connect

    try:
        heartbeat_key = f'odoo_ha_addon.ws_heartbeat_{db_name}'

        # 直接 SQL 查詢，完全繞過所有快取
        with db_connect(db_name).cursor() as cr:
            cr.execute(
                "SELECT value FROM ir_config_parameter WHERE key = %s",
                (heartbeat_key,)
            )
            result = cr.fetchone()
            last_heartbeat = result[0] if result else None

            if not last_heartbeat:
                return False

            # 解析心跳時間（UTC）
            last_heartbeat_dt = datetime.strptime(last_heartbeat, '%Y-%m-%d %H:%M:%S')
            last_heartbeat_dt = last_heartbeat_dt.replace(tzinfo=timezone.utc)

            # 計算時間差
            now_utc = datetime.now(timezone.utc)
            time_diff = (now_utc - last_heartbeat_dt).total_seconds()

            # 25 秒內有心跳 → 運行中
            return time_diff < 25

    except Exception as e:
        _logger.error(f"[PID {os.getpid()}] Error checking heartbeat: {e}")
        return False

# 在 ha_entity.py 中
@api.model
def _cron_ensure_websocket_service(self):
    """Cron Job: 確保服務運行（支援配置變更檢測）"""
    from .common.websocket_thread_manager import (
        start_websocket_service,
        is_websocket_service_running,
        is_config_changed,
        restart_websocket_service
    )

    if is_websocket_service_running(self.env):
        # 檢查配置是否變更
        if is_config_changed(self.env):
            restart_websocket_service(self.env)
        return

    start_websocket_service(self.env)
```

### WebSocket API 呼叫架構

```python
# 在 controllers.py 中
def _call_websocket_api(self, message_type, payload, timeout=15):
    """
    通用 WebSocket API 呼叫函數

    Args:
        message_type: WebSocket 訊息類型（如 'supervisor/api', 'call_service'）
        payload: 請求的 payload（dict 格式）
        timeout: 超時時間（秒）

    Returns:
        dict: {'success': bool, 'data': dict, 'error': str}
    """
    # 1. 檢查 WebSocket 服務狀態
    # 2. 建立請求記錄到 ws.request.queue
    # 3. 輪詢等待結果
    # 4. 返回結果或錯誤

# 使用範例 1: 取得硬體資訊
@http.route('/odoo_ha_addon/hardware_info', type='json', auth='user')
def get_hardware_info(self):
    return self._call_websocket_api(
        message_type='supervisor/api',
        payload={
            'endpoint': '/hardware/info',
            'method': 'get'
        }
    )

# 使用範例 2: 呼叫 Home Assistant 服務
@http.route('/odoo_ha_addon/call_service', type='json', auth='user')
def call_service(self, domain, service, entity_id, **kwargs):
    return self._call_websocket_api(
        message_type='call_service',
        payload={
            'domain': domain,
            'service': service,
            'service_data': {
                'entity_id': entity_id,
                **kwargs
            }
        }
    )

# 使用範例 3: 取得實體狀態
@http.route('/odoo_ha_addon/get_states', type='json', auth='user')
def get_states(self):
    return self._call_websocket_api(
        message_type='get_states',
        payload={}
    )
```

### 資料流設計

1. **HA → WebSocket → Background Thread**
2. **Background Thread → Odoo Models (ha.entity, ha.entity.history)**
3. **Odoo Models → Bus → Frontend**
4. **Frontend → 自動更新組件**
5. **Controller → ws.request.queue → WebSocket Thread → HA API** (新增)

---

## 進階架構優化

### 連線重試機制

#### 設計動機

在生產環境中，WebSocket 連線可能因為各種原因失敗：

- 網路暫時中斷
- Home Assistant 服務重啟
- 認證 token 過期
- 伺服器負載過高

**問題**：原始設計使用無限重試（每 5 秒固定重試），存在以下問題：

- 當 HA 永久不可達時，無限重試浪費資源
- 固定間隔重試可能加重伺服器負擔
- 缺少清楚的失敗通知機制

#### 重試流程圖

```mermaid
flowchart TD
    Start([WebSocket 服務啟動]) --> Connect[嘗試連線]
    Connect --> Auth{認證成功?}

    Auth -->|成功| Reset[重置失敗計數器<br/>consecutive_failures = 0]
    Reset --> Listen[監聽訊息]
    Listen --> Disconnect{連線中斷?}
    Disconnect -->|是| FailInc1[failures++]
    Disconnect -->|否| Listen

    Auth -->|失敗| FailInc2[failures++]

    FailInc1 --> CheckLimit{failures >= 5?}
    FailInc2 --> CheckLimit

    CheckLimit -->|是| Stop([停止服務<br/>記錄錯誤])
    CheckLimit -->|否| CalcDelay["計算延遲時間<br/>delays[failures-1]"]

    CalcDelay --> Wait[等待延遲]
    Wait --> Retry["重試連線<br/>attempt failures+1/5"]
    Retry --> Connect

    style Reset fill:#90EE90
    style Stop fill:#FFB6C1
    style Listen fill:#87CEEB
```

#### 解決方案：智能重試機制

**核心概念**：

1. **有限重試**：最多連續失敗 5 次後停止
2. **漸進式延遲**：使用 exponential backoff 概念
3. **自動重置**：連線成功後重置失敗計數器
4. **清楚日誌**：詳細記錄每次重試和最終失敗

#### 實作架構

**狀態變數**：

```python
class HassWebSocketService:
    def __init__(self, ...):
        self._consecutive_failures = 0  # 連續失敗次數
        self._max_retries = 5  # 最大重試次數
        self._retry_delays = [5, 10, 15, 30, 60]  # 漸進式延遲（秒）
```

**重試邏輯**：

```python
async def connect_and_listen(self):
    while self._running and self._consecutive_failures < self._max_retries:
        try:
            async with websockets.connect(ws_url) as websocket:
                # 認證成功
                if await self._authenticate(websocket, token):
                    # ✅ 連線成功，重置計數器
                    self._consecutive_failures = 0
                    # 正常處理訊息...
                else:
                    # ❌ 認證失敗
                    self._consecutive_failures += 1

        except websockets.exceptions.ConnectionClosed:
            # ❌ 連線關閉
            self._consecutive_failures += 1

        except Exception as e:
            # ❌ 其他錯誤
            self._consecutive_failures += 1

        finally:
            # 檢查是否達到上限
            if self._consecutive_failures >= self._max_retries:
                self._logger.error(
                    f"WebSocket service stopped after {self._max_retries} "
                    f"consecutive failures. Please check your configuration."
                )
                self._running = False
                break

            # 使用漸進式延遲重試
            if self._running and self._consecutive_failures < self._max_retries:
                delay_index = min(self._consecutive_failures - 1, 4)
                retry_delay = self._retry_delays[delay_index]
                self._logger.info(
                    f"Retrying in {retry_delay} seconds "
                    f"(attempt {self._consecutive_failures + 1}/{self._max_retries})..."
                )
                await asyncio.sleep(retry_delay)
```

#### 重試策略詳解

**延遲時間序列**：

| 失敗次數 | 延遲時間 | 累積等待 | 說明                       |
| -------- | -------- | -------- | -------------------------- |
| 第 1 次  | 5 秒     | 5 秒     | 快速重試（可能是暫時問題） |
| 第 2 次  | 10 秒    | 15 秒    | 適度延遲（網路恢復中）     |
| 第 3 次  | 15 秒    | 30 秒    | 增加延遲（嚴重問題）       |
| 第 4 次  | 30 秒    | 60 秒    | 長延遲（系統問題）         |
| 第 5 次  | 60 秒    | 120 秒   | 最後嘗試                   |
| 停止     | -        | -        | 達到上限，停止服務         |

**重試時間軸視覺化**：

```mermaid
gantt
    title WebSocket 重試時間軸（漸進式延遲策略）
    dateFormat s
    axisFormat %S秒

    section 重試嘗試
    第 1 次失敗 :done, attempt1, 0, 1s
    等待 5 秒 :active, wait1, 1, 5s
    第 2 次嘗試 :crit, attempt2, 6, 1s
    等待 10 秒 :active, wait2, 7, 10s
    第 3 次嘗試 :crit, attempt3, 17, 1s
    等待 15 秒 :active, wait3, 18, 15s
    第 4 次嘗試 :crit, attempt4, 33, 1s
    等待 30 秒 :active, wait4, 34, 30s
    第 5 次嘗試 :crit, attempt5, 64, 1s
    等待 60 秒 :active, wait5, 65, 60s
    停止服務 :milestone, stop, 125, 0s

    section 累積時間
    0-6s :done, total1, 0, 6s
    6-17s :done, total2, 6, 11s
    17-33s :done, total3, 17, 16s
    33-64s :done, total4, 33, 31s
    64-125s :done, total5, 64, 61s
```

**設計考量**：

- **初期快速重試**：網路抖動等暫時問題可快速恢復
- **後期長延遲**：避免對故障系統造成額外負擔
- **總時長適中**：2 分鐘內完成所有重試，避免長時間等待

#### 恢復機制

**自動恢復路徑**：

1. **Cron Job 重啟**：每分鐘檢查服務狀態，自動重啟停止的服務
2. **配置變更重啟**：偵測到配置變更時自動重啟
3. **手動重啟**：Dashboard 提供手動重啟按鈕

**重置計數器**：

```python
if await self._authenticate(websocket, token):
    # 連線成功，立即重置
    self._consecutive_failures = 0
```

這確保服務恢復後可以繼續長期運行，不會因為歷史失敗而停止。

#### 日誌輸出

**重試日誌**：

```
INFO: Connecting to WebSocket: ws://192.168.1.100:8123/api/websocket (attempt 1/5)
WARNING: WebSocket connection closed (failure 1/5)
INFO: Retrying in 5 seconds (attempt 2/5)...
```

**成功日誌**：

```
INFO: WebSocket authentication successful
DEBUG: Consecutive failures reset to 0
```

**失敗日誌**：

```
ERROR: WebSocket service stopped after 5 consecutive failures.
       Please check your Home Assistant configuration and restart the service.
```

#### 效益分析

| 指標       | 改進前           | 改進後         | 改善              |
| ---------- | ---------------- | -------------- | ----------------- |
| 重試次數   | ♾️ 無限          | 5 次上限       | ✅ 避免資源浪費   |
| 總等待時間 | ∞                | ≤ 2 分鐘       | ✅ 快速失敗通知   |
| 伺服器負擔 | 高（每 5 秒）    | 低（漸進式）   | ✅ 減少衝擊       |
| 問題診斷   | 難（無清楚訊息） | 易（詳細日誌） | ✅ 更好維護性     |
| 恢復能力   | 無（需手動）     | 自動           | ✅ 自動重置計數器 |

---

### 並發控制優化

#### 問題背景：SerializationFailure

在跨 process 通訊中，Controller 和 WebSocket thread 會同時更新 `ws.request.queue` 記錄，導致 PostgreSQL SerializationFailure 錯誤：

```
ERROR: could not serialize access due to concurrent update
```

**衝突場景**：

```
Controller (Worker Process):
T=0s:  創建請求記錄
T=1s:  commit
T=2s:  輪詢更新 → 開始 transaction A
T=3s:  commit transaction A

WebSocket Thread:
T=2.5s: 處理完成，更新記錄 → 開始 transaction B
T=3.5s: commit transaction B → ❌ 衝突！(記錄在 T=3s 被 transaction A 修改)
```

#### 解決方案：雙重防護

**方案 1: Controller 輪詢機制優化**

```python
# controllers.py - _call_websocket_api()

# 創建記錄後立即 commit（讓 WebSocket thread 能看到）
ws_request = request.env['ws.request.queue'].sudo().create({
    'request_id': request_id,
    'message_type': message_type,
    'payload': json.dumps(payload),
    'state': 'pending'
})
request.env.cr.commit()  # ← 關鍵：立即 commit

# 輪詢時每次 commit 獲得新 snapshot
while time.time() - start_time < timeout:
    # 每次 commit 開始新 transaction，獲得最新 snapshot
    request.env.cr.commit()  # ← 能看到 WebSocket thread 的更新

    ws_request = request.env['ws.request.queue'].sudo().search([
        ('id', '=', ws_request.id)
    ], limit=1)

    if ws_request.state == 'done':
        return {'success': True, 'data': json.loads(ws_request.result)}

    time.sleep(0.3)  # 300ms 輪詢間隔
```

**方案 2: WebSocket Thread Retry 機制**

```python
# hass_websocket_service.py

def _update_request_with_retry(self, record_id, values, operation_name='update'):
    """
    通用方法：更新 ws.request.queue 記錄（含 retry 機制）
    處理 SerializationFailure 錯誤
    """
    from psycopg2 import OperationalError
    from psycopg2.extensions import TransactionRollbackError

    max_retries = 3
    base_delay = 0.05  # 50ms

    for attempt in range(max_retries):
        try:
            with db.db_connect(self.db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})
                record = env['ws.request.queue'].browse(record_id)

                if not record.exists():
                    return False

                record.write(values)
                cr.commit()
                return True

        except (OperationalError, TransactionRollbackError) as e:
            # SerializationFailure 或其他 transaction 衝突
            if attempt < max_retries - 1:
                # Exponential backoff: 50ms → 100ms → 200ms
                delay = base_delay * (2 ** attempt)
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

    return False

# 簡化所有 mark 方法
def _mark_request_done(self, record_id, result):
    """標記請求完成"""
    self._update_request_with_retry(
        record_id,
        {'state': 'done', 'result': result},
        'mark_as_done'
    )
```

**效果**：

- Controller 頻繁 commit 雖可能觸發衝突，但 WebSocket thread 會自動重試
- Exponential backoff 避免重試風暴
- 最多 3 次重試，總延遲最多 350ms

---

### 心跳機制設計

#### 設計動機

對於 **real-time IoT 系統**，需要精確、即時的服務狀態檢查：

- ❌ 檢查資料庫中實體更新時間：不可靠（依賴 HA 有狀態變更）
- ❌ 檢查請求隊列活動：不可靠（依賴有 API 呼叫）
- ✅ **心跳機制**：主動、定期、可靠

#### 跨 Process 心跳檢查時序圖

```mermaid
sequenceDiagram
    participant Main as Main Process<br/>WebSocket Thread
    participant DB as PostgreSQL<br/>ir.config_parameter
    participant Worker as Worker Process<br/>HTTP Request

    Note over Main: 每 10 秒循環

    loop 心跳更新
        Main->>Main: _heartbeat_loop()
        Main->>Main: 取得當前 UTC 時間
        Note right of Main: datetime.now(timezone.utc)
        Main->>DB: 寫入心跳時間戳<br/>key: ws_heartbeat_dbname<br/>value: 2025-10-08 12:00:00
        DB-->>Main: commit 成功
        Main->>Main: sleep(10s)
    end

    Note over Worker: HTTP 請求進來

    Worker->>Worker: is_websocket_service_running()
    Worker->>Worker: 檢查本地連線<br/>_websocket_connections

    alt 本地有連線記錄
        Worker->>Worker: thread.is_alive()
        Worker-->>Worker: 返回執行緒狀態（即時）
    else 跨 Process 檢查
        Note over Worker: 使用心跳機制

        Worker->>DB: 新連線 + 直接 SQL 查詢<br/>SELECT value WHERE key = 'ws_heartbeat_dbname'
        Note right of Worker: 繞過 ORM 快取<br/>獲得最新 snapshot
        DB-->>Worker: '2025-10-08 12:00:00'

        Worker->>Worker: 解析心跳時間（UTC）
        Worker->>Worker: 計算時間差<br/>now_utc - last_heartbeat

        alt 時間差 < 25 秒
            Worker->>Worker: 服務運行中
            Note right of Worker: 允許 2 次心跳失敗<br/>+ 5 秒緩衝
        else 時間差 >= 25 秒
            Worker->>Worker: 服務已停止
            Note right of Worker: 超過 25 秒未更新<br/>視為服務異常
        end
    end
```

#### 架構設計

**參數設定**：

- **心跳間隔**: 10 秒（適合即時系統）
- **超時閾值**: 25 秒（允許 2 次失敗 + 緩衝）
- **儲存位置**: `ir.config_parameter`
  - Key: `odoo_ha_addon.ws_heartbeat_{db_name}`
  - Value: UTC timestamp (格式: `2025-10-07 08:00:00`)

**WebSocket Thread 心跳更新**：

```python
# hass_websocket_service.py

async def _heartbeat_loop(self):
    """
    心跳循環：定期更新心跳時間戳記
    心跳間隔設為 10 秒，確保在 API timeout (15秒) 內能檢測到服務狀態
    """
    self._logger.info("Starting heartbeat loop (interval: 10s)")

    while self._running:
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._update_heartbeat
            )

            # 每 10 秒更新一次心跳
            await asyncio.sleep(10)

        except Exception as e:
            self._logger.error(f"Error in heartbeat loop: {e}")
            await asyncio.sleep(10)

    self._logger.info("Heartbeat loop stopped")

def _update_heartbeat(self):
    """同步方法：更新心跳時間戳記到資料庫"""
    try:
        from datetime import datetime, timezone

        with db.db_connect(self.db_name).cursor() as cr:
            env = api.Environment(cr, 1, {})

            # 更新心跳時間戳記（UTC）
            heartbeat_key = f'odoo_ha_addon.ws_heartbeat_{self.db_name}'
            now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

            env['ir.config_parameter'].sudo().set_param(heartbeat_key, now_utc)
            cr.commit()

            self._logger.debug(f"Heartbeat updated: {now_utc}")

    except Exception as e:
        self._logger.error(f"Failed to update heartbeat: {e}")
```

**Worker Process 狀態檢查**：

```python
# websocket_thread_manager.py

def is_websocket_service_running(env=None):
    """
    檢查 WebSocket 服務是否在運行
    使用心跳機制進行跨 process 檢查
    """
    import os

    if env is None:
        with _connections_lock:
            return len(_websocket_connections) > 0

    db_name = env.cr.dbname

    # 優先：主 process 直接檢查執行緒狀態（即時）
    with _connections_lock:
        if db_name in _websocket_connections:
            conn = _websocket_connections[db_name]
            is_alive = conn['thread'].is_alive()
            _logger.debug(
                f"[PID {os.getpid()}] Found connection for {db_name}, "
                f"thread is_alive={is_alive}"
            )
            return is_alive

    # 跨 process 檢查：使用心跳機制（直接 SQL 查詢）
    from datetime import datetime, timezone
    from odoo.sql_db import db_connect

    try:
        heartbeat_key = f'odoo_ha_addon.ws_heartbeat_{db_name}'

        # 使用新資料庫連線 + 直接 SQL 查詢，完全繞過快取
        with db_connect(db_name).cursor() as cr:
            cr.execute(
                "SELECT value FROM ir_config_parameter WHERE key = %s",
                (heartbeat_key,)
            )
            result = cr.fetchone()
            last_heartbeat = result[0] if result else None

            _logger.debug(
                f"[PID {os.getpid()}] Heartbeat check for {db_name} (direct SQL): "
                f"key={heartbeat_key}, value={last_heartbeat}"
            )

            if not last_heartbeat:
                return False

            # 解析心跳時間（UTC）
            last_heartbeat_dt = datetime.strptime(last_heartbeat, '%Y-%m-%d %H:%M:%S')
            last_heartbeat_dt = last_heartbeat_dt.replace(tzinfo=timezone.utc)

            # 計算時間差
            now_utc = datetime.now(timezone.utc)
            time_diff = (now_utc - last_heartbeat_dt).total_seconds()

            # 如果最後心跳在 25 秒內，認為服務正在運行
            is_running = time_diff < 25

            _logger.debug(
                f"[PID {os.getpid()}] Heartbeat analysis: "
                f"time_diff={time_diff:.1f}s, threshold=25s, is_running={is_running}"
            )

            return is_running

    except Exception as e:
        _logger.error(f"[PID {os.getpid()}] Error checking heartbeat: {e}")
        return False
```

#### 快取問題解決過程

**問題**: Worker process 讀取到舊的心跳值

**嘗試 1: ORM 快取失效**

```python
env['ir.config_parameter'].invalidate_model(['value'])
last_heartbeat = env['ir.config_parameter'].sudo().get_param(heartbeat_key)
```

❌ 失敗：只清除 ORM 快取，無法解決 transaction snapshot 問題

**嘗試 2: 新資料庫連線**

```python
with db_connect(db_name).cursor() as cr:
    fresh_env = api.Environment(cr, 1, {})
    last_heartbeat = fresh_env['ir.config_parameter'].sudo().get_param(heartbeat_key)
```

❌ 失敗：`get_param()` 有 **process-level 全域快取**，不受 transaction 影響

**嘗試 3: 直接 SQL 查詢**

```python
with db_connect(db_name).cursor() as cr:
    cr.execute(
        "SELECT value FROM ir_config_parameter WHERE key = %s",
        (heartbeat_key,)
    )
    last_heartbeat = cr.fetchone()[0]
```

✅ **成功**：完全繞過 ORM 和 `get_param()` 的快取，每次都查詢資料庫最新值

#### 性能考量

**寫入頻率**: 每 10 秒一次

- 每小時: 360 次
- 每天: 8,640 次
- 單筆小資料，對資料庫負擔極小

**讀取優化**:

- 主 process: 使用 `thread.is_alive()` (零開銷)
- Worker process: 直接 SQL 查詢 (毫秒級)

---

### 跨 Process 通訊機制

#### Transaction Snapshot 問題

**PostgreSQL MVCC (Multi-Version Concurrency Control)**:

- 每個 transaction 開始時獲得一個 **snapshot**
- Snapshot 固定了該 transaction 能看到的資料版本
- 其他 transaction 的 commit **不會影響**當前 snapshot

**問題場景**:

```
Main Process (WebSocket Thread):
T=0s:  更新心跳 → commit
T=10s: 更新心跳 → commit

Worker Process (HTTP Request):
T=0s:  HTTP request 開始 → Transaction 開始 (snapshot @ T=0s)
T=5s:  查詢心跳
       └─ ❌ Snapshot 固定在 T=0s，看不到 T=0s 之後的更新
       └─ ❌ 讀取到舊值或 None
```

#### 解決方案：新連線 + 直接 SQL

```python
# ✓ 正確做法
with db_connect(db_name).cursor() as cr:  # 新連線 = 新 transaction
    cr.execute("SELECT value FROM ir_config_parameter WHERE key = %s", (key,))
    # 新 transaction 的 snapshot 是最新的
    # 完全繞過 ORM 和 get_param() 的快取
```

**為什麼有效**:

1. **新連線** → 新 transaction → 最新 snapshot
2. **直接 SQL** → 繞過 ORM 快取 → 直接讀取資料庫
3. **繞過 get_param()** → 避免 process-level 全域快取

#### 其他應用場景

同樣的模式用於 `_get_pending_requests()`:

```python
def _get_pending_requests(self):
    with db.db_connect(self.db_name).cursor() as cr:
        env = api.Environment(cr, 1, {})

        # 先 commit 建立新 snapshot
        cr.commit()

        # 現在能看到 Controller 創建的最新記錄
        records = env['ws.request.queue'].search([
            ('state', '=', 'pending')
        ])
```

---

### Threading 架構說明

**為什麼選擇 Threading？**

- Queue Job 使用 `asyncio.run()` 會阻塞 Worker 進程
- Worker 無法發送 heartbeat 信號，導致每 120 秒 timeout
- Threading 允許 WebSocket 在獨立執行緒中運行，不影響主進程

**Threading 實作細節：**

- 使用 `threading.Thread` 建立 daemon thread
- 每個執行緒有獨立的 `asyncio` event loop
- `post_load_hook()` 在 Odoo 啟動時自動啟動服務
- Cron Job 每分鐘檢查並重啟服務（如果需要）

---

## 檔案清單

### 新增檔案

- `models/common/hass_websocket_service.py` - WebSocket 服務核心
- `models/common/websocket_thread_manager.py` - Threading 管理器
- `models/ha_realtime_update.py` - 即時更新處理
- `data/websocket_cron.xml` - Cron Job 定義

### 修改檔案

- `models/ha_entity.py` - 新增 Cron Job 方法（Threading 版本）
- `models/__init__.py` - 加入新模型
- `hooks.py` - 新增 `post_load_hook()` 自動啟動
- `static/src/services/ha_data_service.js` - 前端即時更新
- `__manifest__.py` - 新增 `post_load` hook 和相依套件

### 相依套件

- `websockets` - Python WebSocket 客戶端（自動安裝於 `pre_init_hook`）

---

## 測試驗證計劃

### 功能測試

- [ ] WebSocket 連線建立成功
- [ ] HA 認證流程正常
- [ ] 狀態變更事件接收
- [ ] Odoo 資料正確更新
- [ ] 前端即時顯示更新

### 效能測試

- [ ] 連線穩定性 (24 小時)
- [ ] 記憶體使用量
- [ ] CPU 影響評估
- [ ] 資料庫寫入效能

### 錯誤處理測試

- [ ] WebSocket 連線中斷恢復
- [ ] HA 服務重啟恢復
- [ ] 網路異常處理
- [ ] 認證失敗處理

---

## 預期效益

### 技術效益

- **即時性**: 從 30 秒延遲降到即時更新
- **效能**: 減少 REST API 輪詢請求
- **穩定性**: 長連線比短連線更穩定

### 用戶體驗

- **即時反饋**: 裝置狀態變化立即顯示
- **減少等待**: 無需手動重新整理資料
- **更好互動**: 即時圖表和儀表板更新

---

## 快速測試指南

### 1. 安裝依賴

```bash
# 在 Docker 容器中安裝 WebSocket 依賴
cd /Users/eugene/Documents/woow/AREA-odoo/odoo-server
docker compose exec web pip install websockets
```

### 2. 更新 Addon

```bash
# 重啟並更新 addon
docker compose restart web
docker compose exec web odoo -d odoo -u odoo_ha_addon --dev xml --log-handler odoo.tools.convert:DEBUG
```

### 3. 配置 Home Assistant

1. 進入 Odoo > 設定 > 技術 > 參數
2. 確保設定：
   - `odoo_ha_addon.ha_api_url`: `http://YOUR_HA_IP:8123/`
   - `odoo_ha_addon.ha_api_token`: `YOUR_LONG_LIVED_TOKEN`

### 4. 啟動 WebSocket 服務

```bash
# 方法 1: 重啟 Odoo（post_load_hook 自動啟動）
docker compose restart web

# 方法 2: 手動觸發 Cron Job
# 在 Odoo shell 中執行
env['ha.entity']._cron_ensure_websocket_service()
```

### 5. 檢查 Threading 狀態

```python
# 在 Odoo shell 中檢查
from odoo.addons.odoo_ha_addon.models.common.websocket_thread_manager import is_websocket_service_running
is_websocket_service_running()  # 回傳 True 表示運行中
```

### 6. 檢查日誌

```bash
# 查看 Odoo 日誌
docker compose logs web | grep -i websocket
```

### 7. 測試前端即時更新

1. 開啟 Odoo HA Dashboard
2. 在 Home Assistant 中變更實體狀態
3. 查看 Odoo 前端是否即時更新
4. 檢查瀏覽器 Console 是否有即時更新日誌

---

## 實作完成度

**整體進度**: 98% ✅

### ✅ 已完成

- WebSocket 服務核心架構
- Threading 整合（完全替代 Queue Job）
- Threading Manager 實作（start/stop/status）
- Post-Load Hook 自動啟動
- Cron Job 監控機制
- 即時資料處理機制
- Odoo Bus 整合
- 前端即時推送
- 智能快取失效
- WebSocket 協定完整符合（ID 管理、陣列回應、無序處理）
- Worker Timeout 問題已解決（Threading 版本運行 8+ 小時無問題）
- 移除 Queue Job 依賴（不再需要 `queue_job` addon）
- **多資料庫支援**（每個資料庫獨立連線）
- **跨 Process 狀態檢查**（修正時區問題）
- **執行緒安全**（使用 Lock 保護共享資源）
- **配置變更自動重啟**（Cron Job 檢測配置變更）
- **手動重啟按鈕**（Dashboard 提供重啟功能）
- **移除 REST API Fallback**（WebSocket 未連線時直接返回錯誤）
- **智能連線重試機制**（5 次上限 + 漸進式延遲）
- **配置變更偵測增強**（詳細變更資訊 + 安全日誌）
- **防重複重啟機制**（5 秒冷卻時間 + 強制重啟選項）
- **前端智能確認對話框**（冷卻期間提供強制重啟選項）

### ⏳ 待測試

- 實際 Home Assistant 連線測試（需要正確的 API URL 和 Token）
- 前端組件自動更新驗證
- 錯誤恢復機制測試
- 長時間穩定性測試（已初步驗證 8+ 小時）
- 多資料庫同時連線測試

---

**總預估時間**: 7 小時
**實際完成時間**: ~8 小時
**開始日期**: 2025-09-29
**主要實作完成**: 2025-09-29
**Threading 重構完成**: 2025-10-01
**協定完整符合**: 2025-10-03

## 重要里程碑

### 2025-09-29: 初始實作

- WebSocket 服務核心完成
- 首次嘗試使用 Queue Job 整合（後來發現問題）

### 2025-10-01: Threading 重構

- 發現 Queue Job 的 `asyncio.run()` 阻塞 Worker 導致每 120 秒 timeout
- 重構為 Threading 架構，WebSocket 在獨立執行緒運行
- 實作 `websocket_thread_manager.py`
- 新增 `post_load_hook()` 自動啟動機制
- 從 `__manifest__.py` 移除 `queue_job` 依賴
- 測試驗證：運行 8+ 小時無 timeout

### 2025-10-03: 協定完整符合與最佳化

- 實作陣列回應處理（`isinstance(data, list)`）
- 改進無序回應處理邏輯
- WebSocket 協定 100% 符合 Home Assistant 規範
- 文件化並發控制改進方案（5% 待實作）
- 完全移除 Queue Job 依賴，改用 Threading 架構

### 2025-10-06: 多資料庫支援與跨 Process 狀態檢查

- **修正時區問題**: 使用 `datetime.now(timezone.utc)` 取代 deprecated `datetime.utcnow()`
- **多資料庫支援**: 重構全域變數為 dictionary 管理多連線
  - 從單例模式 `_websocket_thread` 改為 `_websocket_connections = {db_name: {...}}`
  - 每個資料庫有獨立的 Thread、stop_event、config
  - 執行緒名稱：`HomeAssistantWebSocket-{db_name}`
  - 支援同時運行多個資料庫的 WebSocket 連線
- **執行緒安全**: 新增 `threading.Lock` 保護共享資源
- **移除 REST API Fallback**: WebSocket 未連線時直接返回錯誤訊息
- **改進日誌**: 所有日誌訊息包含資料庫名稱
- **程式碼重構**: 新增 `_call_websocket_api()` 共用函數
  - 抽取 WebSocket API 呼叫邏輯為可重用函數
  - 統一錯誤處理和超時控制
  - 簡化新 API endpoint 的實作（從 85 行減到 12 行）

### 2025-10-07: 並發控制與心跳機制

#### 核心改進

- **SerializationFailure 並發衝突解決**

  - 雙重防護：Controller 輪詢機制 + WebSocket thread retry 機制
  - Exponential backoff (50ms → 100ms → 200ms)
  - 詳見「進階架構優化 > 並發控制優化」

- **Real-time IoT 心跳機制**

  - 心跳間隔: 10 秒 | 超時閾值: 25 秒
  - 直接 SQL 查詢繞過所有快取（ORM、transaction snapshot、process-level 快取）
  - 詳見「進階架構優化 > 心跳機制設計」

- **跨 Process 通訊優化**
  - 理解 PostgreSQL MVCC 和 transaction snapshot
  - 新連線 + 直接 SQL 查詢模式
  - 詳見「進階架構優化 > 跨 Process 通訊機制」

#### 技術突破

- 解決 Odoo 多層快取問題（ORM → transaction → process-level）
- 首次完整實作跨 process 的即時狀態檢查
- 詳細 debug 日誌（PID、檢查路徑、時間差分析）

### 2025-10-08: 重試機制與配置管理優化

#### 核心功能

- **智能連線重試機制**

  - 最多重試 5 次連續失敗，避免無限重試
  - 漸進式延遲策略（5s → 10s → 15s → 30s → 60s）
  - 連線成功自動重置失敗計數器
  - 達到上限後停止服務並記錄清楚的錯誤訊息
  - **詳見「進階架構優化 > 連線重試機制」** 📖

- **配置變更偵測優化**

  - 新增 `return_details` 參數，返回詳細變更資訊
  - 自動記錄具體變更項目（URL 或 Token）
  - 安全顯示 Token（僅顯示前 10 個字元）
  - 支援跨 process 配置變更偵測
  - 詳細的變更日誌（PID、變更類型、新舊值對比）

- **防止重複重啟機制**
  - 新增 5 秒冷卻時間，防止短時間內重複重啟
  - 記錄最後重啟時間戳（`last_restart`）
  - 支援 `force` 參數強制重啟（忽略冷卻時間）
  - 返回詳細的結果狀態（success、message、skipped）
  - 前端智能確認對話框（冷卻期間詢問是否強制重啟）

#### 效益分析

| 功能     | 改進前      | 改進後            | 效益             |
| -------- | ----------- | ----------------- | ---------------- |
| 連線重試 | ♾️ 無限重試 | ✅ 最多 5 次      | 避免資源浪費     |
| 重試延遲 | 固定 5 秒   | ✅ 漸進式 5→60 秒 | 減少伺服器負擔   |
| 配置偵測 | 僅返回 bool | ✅ 詳細變更資訊   | 更好的除錯能力   |
| 重啟保護 | ❌ 無保護   | ✅ 5 秒冷卻時間   | 防止意外重複重啟 |
| 錯誤訊息 | 簡單日誌    | ✅ 詳細狀態和原因 | 更好的可維護性   |
| 用戶體驗 | 基本重啟    | ✅ 智能確認對話框 | 更友善的互動     |

#### 技術亮點

- **自動重置計數器**：連線成功後立即重置失敗計數器，允許服務長期運行
- **漸進式退避**：使用 exponential backoff 概念，減少重試風暴
- **冷卻期間處理**：前端提供選項讓用戶選擇是否強制重啟
- **安全日誌**：Token 僅顯示前綴，避免敏感資訊洩漏
- **型別安全**：修正 token 型別檢查，避免 Pyright 錯誤

#### 實作檔案

- `models/common/hass_websocket_service.py` - 重試機制實作
- `models/common/websocket_thread_manager.py` - 配置偵測與重啟控制
- `controllers/controllers.py` - 重啟 API endpoint
- `static/src/actions/dashboard/dashboard.js` - 前端智能確認

**完整技術細節、流程圖、時序圖請參考「進階架構優化」章節。** 📊

---

_最後更新: 2025-10-08_
