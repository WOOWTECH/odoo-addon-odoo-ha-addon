# WebSocket 自動重連問題分析

## 核心問題

重啟 Odoo 服務後，WebSocket 連接沒有自動重新建立。前端無法自動連接到 Home Assistant 的實時數據流。

## 根本原因分析

### 1. Post-Load Hook 的執行流程

位置：`hooks.py` 第 186-247 行

```python
def post_load_hook():
    """在 Odoo 模組載入後執行的 Hook"""
    _ensure_python_dependencies()
    
    try:
        from odoo import api, SUPERUSER_ID
        from odoo.addons.odoo_ha_addon.models.common.websocket_thread_manager import start_websocket_service
        
        import odoo
        db_names = odoo.service.db.list_dbs(True)
        
        for db_name in db_names:
            try:
                registry = odoo.registry(db_name)
                with registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    
                    # ✓ 檢查 addon 是否已安裝
                    if 'ha.entity' not in env:
                        continue
                    
                    # ✓ 查找所有活躍實例
                    active_instances = env['ha.instance'].sudo().search([('active', '=', True)])
                    
                    if instance_count == 0:
                        continue
                    
                    # ✓ 啟動 WebSocket 服務
                    start_websocket_service(env)
            except Exception as e:
                _logger.error(f"Failed to start WebSocket service: {e}")
    except Exception as e:
        _logger.error(f"Error in post_load_hook: {e}", exc_info=True)
```

**看起來邏輯是正確的，但有以下潛在問題：**

### 2. 環境初始化時序問題（主要問題）

```
時間線：
T1. post_load_hook() 被調用
T2. start_websocket_service(env) 被調用
T3. ✗ 此時 env.cr 的資料庫事務已經結束（with block 退出）
T4. 在 websocket_thread_manager.py 中，threading.Thread 被創建
T5. ✗ 新執行緒試圖使用已關閉的 env.cr
```

**問題代碼：** `websocket_thread_manager.py` 第 21-52 行

```python
def _run_websocket_in_thread(db_name, instance_id, ha_url, ha_token, stop_event):
    """在執行緒中運行 WebSocket 服務"""
    try:
        from .hass_websocket_service import HassWebSocketService
        
        # ✓ 建立新的 event loop（正確做法）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # ✗ 但是 HassWebSocketService 初始化時期望 db_name + config
        service = HassWebSocketService(
            env=None,                    # ✓ env 被設為 None（正確，避免跨執行緒）
            db_name=db_name,             # ✓ 傳入 db_name（正確）
            ha_url=ha_url,               # ✓ 直接傳入配置（正確）
            ha_token=ha_token,
            instance_id=instance_id
        )
```

這部分看起來是正確的。讓我檢查實際問題...

### 3. 檢查點：實例配置檢查

**潛在問題：** `websocket_thread_manager.py` 第 144-153 行

```python
# 取得實例配置
ha_url = instance.api_url
ha_token = instance.api_token

if not ha_url or not ha_token:
    _logger.warning(
        f"HA instance {instance.id} ({instance.name}) configuration incomplete, "
        f"cannot start WebSocket service"
    )
    continue  # ← 跳過該實例，不啟動 WebSocket
```

**問題：如果實例配置不完整（api_url 或 api_token 為空），該實例的 WebSocket 服務將無法啟動！**

### 4. 檢查點：全域連接狀態管理

**位置：** `websocket_thread_manager.py` 第 12-14 行

```python
# 全域變數：儲存多資料庫、多實例的執行緒和停止事件
_websocket_connections = {}
_connections_lock = threading.Lock()
```

**問題：** 重啟 Odoo 時，這個全域變數會被重置（Python 進程重啟）。但是舊的執行緒可能還在運行，導致：
- 舊執行緒繼續運行但無法與新的全域字典同步
- 新的執行緒被啟動但不知道舊執行緒的存在
- 潛在的資源洩漏（孤立執行緒）

### 5. 檢查點：Daemon Thread 設置

**位置：** `websocket_thread_manager.py` 第 159-163 行

```python
thread = threading.Thread(
    target=_run_websocket_in_thread,
    args=(db_name, instance.id, ha_url, ha_token, stop_event),
    daemon=True,  # ← Daemon 執行緒
    name=f"HomeAssistantWebSocket-{db_name}-Instance-{instance.id}"
)
```

**問題：** Daemon 執行緒在主程序退出時會立即被殺死，不會等待執行緒清理。這導致：
- WebSocket 連接未正確關閉
- 資源未被釋放
- 心跳更新可能被中斷

## 主要根本原因

### ✗ 原因 1：實例配置未初始化

如果 Home Assistant 實例的 `api_url` 和 `api_token` 在 post_load_hook 執行時為空，WebSocket 服務將被跳過啟動。

**解決方案需要：**
- 延遲啟動直到實例配置完整
- 或者使用配置監視機制檢測配置變更後自動啟動

### ✗ 原因 2：Post-Load Hook 時序不確定

Post-load hook 的執行時間相對於模塊初始化完成的時間不確定。可能存在以下情況：
- Model 還未完全初始化
- 資料庫表還未創建
- 先前的連接還未完全關閉

### ✗ 原因 3：沒有自動重連機制（重新啟動時）

雖然 WebSocket 服務本身有重連機制（最多 5 次重試，延遲逐漸增加），但這是針對臨時斷線的情況。對於完全的 Odoo 重啟：
- 全局連接字典被重置
- 沒有「恢復」機制來重新建立連接

### ✗ 原因 4：缺少 Graceful Shutdown

Daemon 執行緒在 Odoo 重啟時可能被強制終止，導致：
- WebSocket 連接未正確關閉
- 資源未被釋放
- 潛在的資源洩漏

## 代碼流程圖

```
Odoo 啟動
    ↓
post_load_hook() 執行 (hooks.py:186)
    ↓
start_websocket_service(env) (websocket_thread_manager.py:102)
    ↓
檢查活躍實例 (line 124)
    ├─ 實例 1: api_url="http://ha.local:8123", api_token="token123"
    │   └─ ✓ 檢查通過，建立執行緒並啟動
    ├─ 實例 2: api_url="", api_token=""
    │   └─ ✗ 檢查失敗，跳過（這是問題！）
    └─ 實例 3: api_url="...", api_token="..."
        └─ ✓ 啟動

WebSocket 服務運行
    ├─ 連接到 Home Assistant
    ├─ 認證成功
    ├─ 訂閱事件
    └─ 監聽消息

Odoo 重啟（或 docker-compose restart）
    ↓
Daemon 執行緒被立即終止 (daemon=True)
    ↓
全局 _websocket_connections 字典被重置
    ↓
post_load_hook() 再次執行
    ↓
start_websocket_service(env) 再次執行
    ↓
如果實例配置完整，✓ 成功啟動
如果實例配置不完整，✗ 失敗，無 WebSocket 服務
```

## 用户的實際情況

根據 CLAUDE.md 的描述，用户說「重啟後 WebSocket 沒有自動重連」。最可能的原因是：

1. **實例配置不完整** - 最可能
   - 實例存在但 `api_url` 或 `api_token` 為空
   - post_load_hook 檢查到配置不完整，跳過啟動
   - 用户看不到任何錯誤信息（因為是 `_logger.warning` 級別）

2. **實例未被標記為活躍** - 其次
   - 實例的 `active=False`
   - post_load_hook 查找活躍實例時找不到

3. **數據庫表未初始化** - 較少可能
   - 雖然 post_load_hook 有檢查 `'ha.entity' not in env`
   - 但可能在某些邊界情況下失敗

## 診斷建議

### 步驟 1: 檢查日誌

```bash
# 在容器中執行
docker compose -f docker-compose-18.yml logs web | grep -E "(post_load_hook|start_websocket|WebSocket|instance)"
```

**預期看到的日誌：**
- `Post-load hook: Initializing Home Assistant WebSocket integration`
- `Found X active HA instance(s) in database`
- `WebSocket service thread started for database: odoo instance X`

**問題日誌：**
- `No active HA instances found in database odoo, skipping`
- `HA instance X configuration incomplete, cannot start WebSocket service`
- `Failed to start WebSocket service for database odoo: ...`

### 步驟 2: 檢查實例配置

進入 Odoo 管理後台：
1. 進入「Settings > Technical > Home Assistant」
2. 檢查每個實例：
   - `Active` 是否被勾選？
   - `API URL` 是否為空？
   - `Access Token` 是否為空？

### 步驟 3: 測試實例連接

在實例表單中，點擊「Test Connection」按鈕，驗證配置是否有效。

## 推薦修復方案

### 方案 1: 更好的錯誤日誌（立即修復）

修改 `hooks.py` 的 post_load_hook，提高日誌級別或添加更詳細的診斷信息。

### 方案 2: 延遲啟動機制（短期修復）

添加監視機制，當實例配置被更新時，自動啟動 WebSocket 服務：
- 在 `ha.instance.write()` 中檢測配置變更
- 觸發 WebSocket 服務啟動

### 方案 3: 改進 Graceful Shutdown（中期修復）

- 使用非 daemon 執行緒並實現適當的清理邏輯
- 在 Odoo 重啟時正確關閉 WebSocket 連接
- 實現「心跳復甦」機制

### 方案 4: 自動重連恢復（長期修復）

- 實現完整的服務監視機制
- 定期檢查 WebSocket 服務狀態
- 自動恢復失敗的連接

## 總結

WebSocket 自動重連失敗的根本原因很可能是：

1. **實例配置在重啟時為空** ← 最高概率
2. **實例未標記為活躍** ← 中等概率
3. **Post-load hook 執行時序問題** ← 低概率
4. **Daemon 執行緒被強制終止** ← 低概率，但影響大

下一步應該是檢查日誌和實例配置，以確認真正的原因。

