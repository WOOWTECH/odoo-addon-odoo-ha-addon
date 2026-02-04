# WebSocket 自動重連問題：詳細技術指南

## 執行摘要

重啟 Odoo 服務後，WebSocket 連接沒有自動重新建立。通過深入代碼分析，我們發現有 **4 個主要的根本原因**，其中最可能的是 **實例配置不完整導致的啟動失敗**。

本文檔提供：
- 完整的問題根本原因分析
- 代碼層級的診斷指南
- 4 個遞進式的修復方案（從簡單到複雜）

---

## 第一部分：問題根本原因分析

### 問題概述

**症狀：**
- Odoo 重啟後，前端無法接收 WebSocket 實時數據
- 查看 Home Assistant 實例狀態顯示 "Disconnected"
- 日誌中沒有 WebSocket 連接錯誤（可能根本沒有嘗試連接）

**影響範圍：**
- 儀表板無法顯示即時數據
- 實體狀態不更新
- 歷史圖表可能顯示舊數據

### 根本原因 1：實例配置檢查失敗（最可能）

**位置：** `models/common/websocket_thread_manager.py:144-153`

```python
# 取得實例配置
ha_url = instance.api_url
ha_token = instance.api_token

if not ha_url or not ha_token:
    _logger.warning(
        f"HA instance {instance.id} ({instance.name}) configuration incomplete, "
        f"cannot start WebSocket service"
    )
    continue  # ← 無聲跳過！沒有啟動 WebSocket
```

**問題細節：**

1. **條件太嚴格**
   - `if not ha_url or not ha_token:` 只要其中一個為空就跳過
   - 空字符串 `""` 被視為 False
   - None 也被視為 False
   - 只有空格的字符串 `" "` 會通過（但實際無效）

2. **缺乏反饋機制**
   - 使用 `_logger.warning()` 記錄，但用户可能看不到
   - 沒有 UI 反饋告訴用户配置不完整
   - 用户重啟後看不到任何錯誤，認為一切正常

3. **典型場景**
   ```
   場景 A: 新用户建立實例但忘記填寫 Token
   ├─ admin 建立實例，名稱="My HA"
   ├─ 設置 api_url="http://ha.local:8123"
   ├─ 但忘記設置 api_token（留空）
   ├─ 重啟 Odoo
   ├─ post_load_hook 執行，發現 api_token 為空
   └─ ✗ WebSocket 服務跳過啟動，無聲失敗
   
   場景 B: 實例配置後被意外清空
   ├─ 實例之前正常工作
   ├─ 某次操作意外清空了 api_token（例如批量編輯）
   ├─ 重啟 Odoo
   └─ ✗ WebSocket 服務無法啟動
   
   場景 C: 資料庫遷移或備份恢復
   ├─ 從另一個 Odoo 實例恢復數據庫
   ├─ 實例配置丟失或損壞
   ├─ 重啟 Odoo
   └─ ✗ WebSocket 服務無法啟動
   ```

### 根本原因 2：Post-Load Hook 執行時序問題

**位置：** `hooks.py:186-247`

```python
def post_load_hook():
    """在 Odoo 模組載入後執行的 Hook"""
    # ...
    for db_name in db_names:
        try:
            registry = odoo.registry(db_name)
            with registry.cursor() as cr:  # ← 臨時遊標
                env = api.Environment(cr, SUPERUSER_ID, {})
                
                # ...
                start_websocket_service(env)  # ← 在 with block 內
        # ← with block 結束，遊標關閉！
```

**潛在問題：**

1. **資料庫遊標生命週期**
   - `with registry.cursor() as cr:` 中的遊標在 block 結束時自動關閉
   - 如果後續操作需要資料庫訪問，會失敗
   - 雖然 `_run_websocket_in_thread` 會建立新遊標，但時序不確定

2. **模型初始化順序**
   - post_load_hook 的執行時間相對於模型 `__init__` 不確定
   - 可能某些模型的初始化邏輯還未完成
   - 資料庫表可能還在初始化中

3. **ORM 限制**
   - Odoo ORM 的某些操作在跨執行緒訪問時可能失敗
   - 雖然代碼已通過 `env=None` 避免了這個問題，但仍有邊界情況

### 根本原因 3：Daemon 執行緒管理不當

**位置：** `websocket_thread_manager.py:159-163`

```python
thread = threading.Thread(
    target=_run_websocket_in_thread,
    args=(db_name, instance.id, ha_url, ha_token, stop_event),
    daemon=True,  # ← Daemon 執行緒
    name=f"HomeAssistantWebSocket-{db_name}-Instance-{instance.id}"
)
```

**Daemon 執行緒的特性：**

| 特性 | 詳情 |
|------|------|
| **自動終止** | 主程序退出時立即被殺死（不等待） |
| **無清理時間** | 沒有機會執行清理代碼 |
| **資源洩漏** | WebSocket 連接未正確關閉 |
| **事務不完整** | 資料庫事務可能被強制回滾 |

**問題場景：**

```
Odoo 進程運行中
├─ Main Thread (Odoo Server)
└─ WebSocket Daemon Thread (正在進行 WebSocket 操作)
   ├─ 連接到 HA
   ├─ 接收消息
   ├─ 更新 Odoo 數據庫
   └─ 發送心跳

用户執行 docker-compose restart web
├─ Odoo 進程收到 SIGTERM
├─ Main Thread 開始關閉
├─ WebSocket Daemon Thread 被強制終止 ✗
│  ├─ WebSocket 連接未關閉
│  ├─ 資料庫事務被回滾
│  ├─ 心跳時間戳未更新
│  └─ 資源未釋放
└─ Odoo 進程結束

重啟後
├─ post_load_hook() 執行
├─ 檢查心跳時間戳（可能是舊的或丟失的）
└─ 可能導致狀態檢查失誤
```

### 根本原因 4：全域狀態管理不當

**位置：** `websocket_thread_manager.py:12-14`

```python
# 全域變數：儲存多資料庫、多實例的執行緒和停止事件
_websocket_connections = {}
_connections_lock = threading.Lock()
```

**問題：**

1. **重啟時被重置**
   - Python 進程重啟時，全局字典被重置
   - 舊執行緒的信息丟失
   - 無法檢測到舊執行緒是否仍在運行

2. **跨進程孤立**
   - Odoo 在多進程模式下運行（gevent/multiprocessing）
   - 每個進程有自己的 `_websocket_connections` 副本
   - Worker 進程中的連接信息對主進程不可見

3. **資源洩漏風險**
   ```
   情況 1: 普通重啟（graceful）
   T1. Main process 關閉 daemon thread
   T2. daemon thread 被強制終止
   T3. _websocket_connections 被重置
   T4. 舊執行緒的句柄丟失（但執行緒可能仍在系統中）
   
   情況 2: 強制終止（kill -9）
   T1. Odoo 進程被立即殺死
   T2. _websocket_connections 無法清理
   T3. 孤立的執行緒仍在系統中消耗資源
   ```

---

## 第二部分：代碼層級診斷指南

### 診斷工具和命令

#### 1. 檢查實例配置

```bash
# 進入 Odoo 容器
docker compose exec web bash

# 查看所有實例的配置
odoo shell -d odoo
>>> env = api.Environment(cr, SUPERUSER_ID, {})
>>> instances = env['ha.instance'].sudo().search([])
>>> for inst in instances:
...     print(f"Instance: {inst.name}")
...     print(f"  Active: {inst.active}")
...     print(f"  API URL: {inst.api_url or '(empty)'}")
...     print(f"  API Token: {inst.api_token[:20] if inst.api_token else '(empty)'}...")
...     print()
```

#### 2. 檢查 WebSocket 服務狀態

```python
# 在 Odoo shell 中
from odoo.addons.odoo_ha_addon.models.common.websocket_thread_manager import is_websocket_service_running

# 檢查所有實例
instances = env['ha.instance'].sudo().search([])
for inst in instances:
    is_running = is_websocket_service_running(env, instance_id=inst.id)
    print(f"Instance {inst.name} (ID: {inst.id}): {'Running' if is_running else 'Stopped'}")

# 檢查心跳
import os
db_name = env.cr.dbname
for inst in instances:
    heartbeat_key = f'odoo_ha_addon.ws_heartbeat_{db_name}_instance_{inst.id}'
    heartbeat = env['ir.config_parameter'].sudo().get_param(heartbeat_key)
    print(f"Instance {inst.name}: {heartbeat or '(no heartbeat)'}")
```

#### 3. 檢查日誌

```bash
# 查看最後 100 行日誌（包含 post-load hook 信息）
docker compose logs --tail=100 web | grep -E "(post_load|WebSocket|start_websocket|instance.*config)"

# 實時監控日誌
docker compose logs -f web | grep -E "(WebSocket|instance)"

# 查看特定實例的相關日誌
docker compose logs web | grep "instance_id=5"  # 替換為實際實例 ID
```

#### 4. 追蹤執行過程

```python
# 在 hooks.py 或 websocket_thread_manager.py 中添加詳細日誌

import logging
_logger = logging.getLogger(__name__)

def start_websocket_service(env, instance_id=None):
    """啟動 WebSocket 服務"""
    db_name = env.cr.dbname
    
    # Phase 2: 取得要啟動的實例列表
    if instance_id:
        instances = env['ha.instance'].sudo().browse(instance_id)
        _logger.info(f"[DEBUG] Searching for specific instance {instance_id}")
    else:
        instances = env['ha.instance'].sudo().search([('active', '=', True)])
        _logger.info(f"[DEBUG] Searching for all active instances")
    
    _logger.info(f"[DEBUG] Found {len(instances)} instance(s)")
    
    for instance in instances:
        _logger.info(f"[DEBUG] Checking instance: {instance.name} (ID: {instance.id})")
        _logger.info(f"[DEBUG]   - active: {instance.active}")
        _logger.info(f"[DEBUG]   - api_url: {instance.api_url or '(empty)'}")
        _logger.info(f"[DEBUG]   - has_token: {bool(instance.api_token)}")
        
        ha_url = instance.api_url
        ha_token = instance.api_token
        
        if not ha_url or not ha_token:
            _logger.warning(
                f"[CRITICAL] Instance {instance.name} config incomplete! "
                f"url_empty={not ha_url}, token_empty={not ha_token}"
            )
            continue
        
        # 啟動執行緒...
```

---

## 第三部分：修復方案

### 方案 1：改進實例配置檢查和日誌（立即修復）

**難度：** 簡單 | **時間：** 15 分鐘 | **效果：** 提高診斷能力

**修改文件：** `models/common/websocket_thread_manager.py`

```python
def start_websocket_service(env, instance_id=None):
    """啟動 WebSocket 服務
    
    改進點：
    1. 更詳細的日誌
    2. 區分「配置不完整」和「實例不活躍」的情況
    3. 檢查配置的有效性（不只是是否存在）
    """
    db_name = env.cr.dbname
    
    if instance_id:
        instances = env['ha.instance'].sudo().browse(instance_id)
        if not instances.exists():
            _logger.warning(f"HA instance {instance_id} not found")
            return
    else:
        instances = env['ha.instance'].sudo().search([('active', '=', True)])
    
    if not instances:
        _logger.info(f"No active HA instances found for database {db_name}")  # ← 改為 info
        return
    
    _logger.info(f"[start_websocket_service] Found {len(instances)} active instance(s)")
    
    with _connections_lock:
        if db_name not in _websocket_connections:
            _websocket_connections[db_name] = {}
        
        for instance in instances:
            # 檢查現有連接
            if instance.id in _websocket_connections[db_name]:
                conn = _websocket_connections[db_name][instance.id]
                if conn['thread'].is_alive():
                    _logger.info(f"WebSocket already running for {db_name} instance {instance.id} ({instance.name})")
                    continue
            
            # 檢查配置
            ha_url = instance.api_url
            ha_token = instance.api_token
            
            # 改進的檢查邏輯
            if not ha_url:
                _logger.error(
                    f"[CRITICAL] Instance {instance.id} ({instance.name}): API URL is empty! "
                    f"Cannot start WebSocket service. Please configure the instance."
                )
                continue
            
            if not ha_token:
                _logger.error(
                    f"[CRITICAL] Instance {instance.id} ({instance.name}): API Token is empty! "
                    f"Cannot start WebSocket service. Please configure the instance."
                )
                continue
            
            # 檢查 URL 格式
            if not (ha_url.startswith('http://') or ha_url.startswith('https://')):
                _logger.error(
                    f"[CRITICAL] Instance {instance.id} ({instance.name}): Invalid URL format: {ha_url} "
                    f"URL must start with http:// or https://"
                )
                continue
            
            # 檢查 Token 最小長度（HA tokens 通常很長）
            if len(ha_token.strip()) < 10:
                _logger.error(
                    f"[CRITICAL] Instance {instance.id} ({instance.name}): Token too short (len={len(ha_token)})! "
                    f"Please check the token configuration."
                )
                continue
            
            _logger.info(f"Instance {instance.id} ({instance.name}) configuration OK. Starting WebSocket service...")
            
            # 建立執行緒...
            stop_event = threading.Event()
            thread = threading.Thread(
                target=_run_websocket_in_thread,
                args=(db_name, instance.id, ha_url.strip(), ha_token, stop_event),
                daemon=True,
                name=f"HomeAssistantWebSocket-{db_name}-Instance-{instance.id}"
            )
            
            _websocket_connections[db_name][instance.id] = {
                'thread': thread,
                'stop_event': stop_event,
                'config': {'ha_url': ha_url, 'ha_token': ha_token},
                'instance_name': instance.name,
                'start_time': time.time()  # ← 記錄啟動時間
            }
            
            thread.start()
            _logger.info(
                f"WebSocket thread started for {db_name} instance {instance.id} ({instance.name}) "
                f"with URL: {ha_url}"
            )
```

**預期日誌輸出：**

```
[INFO] [start_websocket_service] Found 2 active instance(s)
[INFO] Instance 1 (My HA) configuration OK. Starting WebSocket service...
[ERROR] [CRITICAL] Instance 2 (Guest HA): API URL is empty! Cannot start WebSocket service. Please configure the instance.
[INFO] WebSocket thread started for odoo instance 1 (My HA) with URL: http://ha.local:8123
```

### 方案 2：實例配置變更監視機制（短期修復）

**難度：** 中等 | **時間：** 30 分鐘 | **效果：** 自動啟動/重啟 WebSocket

**修改文件：** `models/ha_instance.py`

```python
def write(self, vals):
    """
    更新實例時的處理
    
    改進點：
    1. 檢測配置變更
    2. 自動啟動/重啟 WebSocket
    3. 記錄配置變更歷史
    """
    result = super(HAInstance, self).write(vals)
    
    # 檢查是否有相關配置被修改
    config_changed = any(field in vals for field in ['api_url', 'api_token', 'active'])
    
    if config_changed:
        from .common.websocket_thread_manager import restart_websocket_service, start_websocket_service
        
        for record in self:
            if not record.active:
                # 實例被停用，停止 WebSocket 服務
                _logger.info(f"Instance {record.name} deactivated. Stopping WebSocket service...")
                # 停止邏輯...
                continue
            
            # 檢查配置是否完整
            if not record.api_url or not record.api_token:
                _logger.warning(
                    f"Instance {record.name} configuration incomplete. "
                    f"WebSocket service will not start until configuration is complete."
                )
                continue
            
            # 配置已完成，啟動或重啟 WebSocket
            if 'api_url' in vals or 'api_token' in vals:
                _logger.info(f"Instance {record.name} configuration changed. Restarting WebSocket service...")
                restart_websocket_service(self.env, instance_id=record.id, force=True)
            elif 'active' in vals and record.active:
                _logger.info(f"Instance {record.name} activated. Starting WebSocket service...")
                start_websocket_service(self.env, instance_id=record.id)
    
    return result
```

### 方案 3：改進 Graceful Shutdown 機制（中期修復）

**難度：** 中等 | **時間：** 45 分鐘 | **效果：** 防止資源洩漏

**修改文件：** `models/common/websocket_thread_manager.py`

```python
import atexit
import signal

# 在模組級別註冊清理函數
def _cleanup_on_exit():
    """Odoo 進程退出時的清理"""
    _logger.info("Cleaning up WebSocket connections on process exit...")
    stop_websocket_service()  # 停止所有連接

# 註冊清理函數
atexit.register(_cleanup_on_exit)

# 如果需要，也可以處理 signal
def _handle_signal(signum, frame):
    """處理 SIGTERM/SIGINT"""
    _logger.info(f"Received signal {signum}. Cleaning up...")
    _cleanup_on_exit()

signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)
```

同時修改執行緒定義，支持非 daemon 執行緒：

```python
# 在 start_websocket_service 中
thread = threading.Thread(
    target=_run_websocket_in_thread,
    args=(db_name, instance.id, ha_url, ha_token, stop_event),
    daemon=False,  # ← 改為非 daemon，等待清理
    name=f"HomeAssistantWebSocket-{db_name}-Instance-{instance.id}"
)

# 設置執行緒為守護執行緒（可等待主線程優雅結束）
thread.daemon = False
```

### 方案 4：完整的服務監視和自動恢復（長期修復）

**難度：** 複雜 | **時間：** 2-3 小時 | **效果：** 生產就緒的自動恢復

這個方案需要實現一個專用的監視服務：

```python
# 新文件：models/common/websocket_monitor_service.py

class WebSocketMonitorService:
    """WebSocket 服務監視和自動恢復"""
    
    def __init__(self):
        self._monitor_thread = None
        self._running = False
    
    def start_monitoring(self, env):
        """啟動監視執行緒"""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(env,),
            daemon=False,
            name="WebSocketMonitor"
        )
        self._monitor_thread.start()
    
    def _monitor_loop(self, env):
        """監視迴圈"""
        while self._running:
            try:
                # 每 30 秒檢查一次所有實例
                time.sleep(30)
                
                instances = env['ha.instance'].sudo().search([('active', '=', True)])
                
                for instance in instances:
                    # 檢查心跳
                    is_running = is_websocket_service_running(env, instance_id=instance.id)
                    
                    if not is_running and instance.api_url and instance.api_token:
                        _logger.warning(f"Instance {instance.name} WebSocket stopped. Restarting...")
                        start_websocket_service(env, instance_id=instance.id)
                    
            except Exception as e:
                _logger.error(f"Error in monitor loop: {e}")

# 在 post_load_hook 中
monitor_service = WebSocketMonitorService()
monitor_service.start_monitoring(env)
```

---

## 第四部分：驗證和測試

### 測試清單

- [ ] 檢查日誌中是否有 post_load_hook 相關信息
- [ ] 確認所有實例配置完整
- [ ] 驗證 WebSocket 連接狀態
- [ ] 測試配置變更後的自動重啟
- [ ] 檢查心跳更新是否正常
- [ ] 驗證資料庫數據是否正常同步

### 驗證命令

```bash
# 1. 查看實例配置
docker compose exec web odoo shell -d odoo << 'PYEOF'
from odoo import api, SUPERUSER_ID
env = api.Environment(cr, SUPERUSER_ID, {})
instances = env['ha.instance'].sudo().search([])
for inst in instances:
    print(f"✓ {inst.name}: active={inst.active}, url_ok={bool(inst.api_url)}, token_ok={bool(inst.api_token)}")
PYEOF

# 2. 檢查 WebSocket 狀態
docker compose logs --tail=50 web | grep -E "(WebSocket|start_websocket|thread started)"

# 3. 驗證心跳
docker compose exec web odoo shell -d odoo << 'PYEOF'
from datetime import datetime, timezone
db_name = env.cr.dbname
instances = env['ha.instance'].sudo().search([])
for inst in instances:
    key = f'odoo_ha_addon.ws_heartbeat_{db_name}_instance_{inst.id}'
    hb = env['ir.config_parameter'].sudo().get_param(key)
    if hb:
        hb_time = datetime.strptime(hb, '%Y-%m-%d %H:%M:%S')
        age_sec = (datetime.now(timezone.utc) - hb_time.replace(tzinfo=timezone.utc)).total_seconds()
        print(f"✓ {inst.name}: heartbeat age={age_sec:.0f}s")
    else:
        print(f"✗ {inst.name}: no heartbeat")
PYEOF
```

---

## 總結和建議

### 立即行動（今天）

1. **檢查實例配置**
   - 進入 Odoo，查看每個實例是否有完整的 API URL 和 Token
   - 使用「Test Connection」按鈕驗證配置有效性

2. **查看日誌**
   - 檢查容器日誌是否有配置不完整的警告

### 短期改進（本週）

3. **應用方案 1（改進日誌）**
   - 更清晰的錯誤消息幫助診斷問題

4. **應用方案 2（配置監視）**
   - 實例配置變更時自動重啟 WebSocket

### 中期優化（本月）

5. **應用方案 3（Graceful Shutdown）**
   - 防止 Odoo 重啟時資源洩漏

### 長期完善（下個季度）

6. **應用方案 4（自動監視）**
   - 實現生產級的自動恢復機制

---

**文檔版本：** 1.0  
**更新日期：** 2024-11-08  
**相關文件：**
- `hooks.py`
- `models/common/websocket_thread_manager.py`
- `models/ha_instance.py`
- `models/common/hass_websocket_service.py`

