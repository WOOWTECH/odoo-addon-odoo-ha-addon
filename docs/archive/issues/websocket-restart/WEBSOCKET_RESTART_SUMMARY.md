# WebSocket 自動重連問題 - 快速參考

## 問題症狀

Odoo 重啟後，WebSocket 連接沒有自動重新建立：
- 儀表板無法顯示即時數據
- Home Assistant 實例狀態顯示 "Disconnected"
- 前端無法接收實時更新

## 根本原因（按概率排序）

### 1. 實例配置不完整（最可能）
- `api_url` 為空
- `api_token` 為空
- 配置未保存

**檢查方法：**
```bash
docker compose logs --tail=100 web | grep -i "configuration incomplete"
```

### 2. 實例未標記為活躍（其次可能）
- Instance 的 `active` 字段為 False

### 3. Post-Load Hook 執行時序問題（較少）
- 模型初始化不完整
- 資料庫表未就緒

### 4. Daemon 執行緒未正確清理（最少）
- WebSocket 連接未正確關閉
- 資源洩漏

## 快速診斷步驟

### 步驟 1：檢查實例配置

進入 Odoo 管理後台：
1. 進入 Settings > Technical > Home Assistant
2. 檢查每個實例：
   - [ ] Active 是否勾選？
   - [ ] API URL 是否為空？
   - [ ] Access Token 是否為空？

### 步驟 2：點擊 Test Connection

在實例詳細頁面，點擊「Test Connection」按鈕：
- ✓ 成功 = 配置有效
- ✗ 失敗 = 配置有問題

### 步驟 3：查看日誌

```bash
# 查看 post_load_hook 相關日誌
docker compose logs web | grep -E "(post_load_hook|WebSocket|start_websocket)"
```

預期看到：
- `Post-load hook: Initializing Home Assistant WebSocket integration`
- `Found X active HA instance(s)`
- `WebSocket thread started for...`

## 快速修復

### 修復方案 1：檢查和完成配置（5 分鐘）

1. 進入每個實例
2. 確保 API URL 和 Token 都已填寫
3. 點擊 Save
4. 重啟 Odoo：

```bash
docker compose restart web
```

### 修復方案 2：檢查實例是否活躍（2 分鐘）

1. 進入實例列表
2. 確認 Active 欄位被勾選
3. 如果不是，勾選並保存

### 修復方案 3：重新同步實例（10 分鐘）

1. 進入實例詳細頁面
2. 依次點擊以下按鈕：
   - "Test Connection"（驗證配置）
   - "Sync Areas"（同步區域）
   - "Sync Entities"（同步實體）
   - "Restart WebSocket"（重啟 WebSocket）

### 修復方案 4：強制重啟 WebSocket 服務（5 分鐘）

在實例列表中：
1. 選擇要重啟的實例
2. 點擊 "Restart WebSocket" 按鈕
3. 確認操作

## 驗證修復

重啟後，驗證以下幾點：

### 1. 查看日誌確認啟動

```bash
docker compose logs web | tail -50 | grep "WebSocket thread started"
```

應該看到類似信息：
```
WebSocket thread started for database: odoo, instance: 1
```

### 2. 檢查實例狀態

進入實例列表，檢查 WebSocket Status 欄：
- 應該显示 "Connected" 或 "Connecting"
- 不應該显示 "Disconnected"

### 3. 查看前端數據

打開儀表板：
- 應該显示即時數據
- 圖表應該更新
- 無錯誤通知

## 常見問題

### Q1: 為什麼重啟後 WebSocket 沒有自動啟動？

A: 最可能是實例配置不完整。檢查 API URL 和 Token 是否都已填寫。

### Q2: Test Connection 成功但 WebSocket 仍未啟動？

A: 重啟 Odoo 服務。Post-load hook 只在啟動時執行。

```bash
docker compose restart web
```

### Q3: 如何手動重啟 WebSocket 服務？

A: 在實例詳細頁面點擊「Restart WebSocket」按鈕，或在 Odoo shell 中執行：

```python
from odoo.addons.odoo_ha_addon.models.common.websocket_thread_manager import restart_websocket_service

# 在 Odoo shell 中
restart_websocket_service(env, instance_id=1, force=True)
```

### Q4: 日誌中說「configuration incomplete」怎麼辦？

A: 進入該實例，檢查 api_url 和 api_token 是否為空。填寫完整後重啟 Odoo。

### Q5: 多次重啟後仍未正常？

A: 執行完整的同步流程：
1. Test Connection
2. Sync Areas
3. Sync Entities
4. Sync History
5. Restart WebSocket

## 相關文檔

- **詳細技術指南**：`websocket-restart-detailed-guide.md`
- **完整分析報告**：`websocket-restart-analysis.md`
- **架構文檔**：`docs/tech/instance-switching.md`

## 日期和版本

- **文檔版本**：1.0
- **更新日期**：2024-11-08
- **適用版本**：Odoo 18 + odoo_ha_addon Phase 2+

