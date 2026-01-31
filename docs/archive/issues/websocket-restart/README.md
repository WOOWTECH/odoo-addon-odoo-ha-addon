# WebSocket 自動重連問題

## Issue 概述

**問題**：Odoo 重啟後，WebSocket 連接沒有自動重新建立

**影響**：
- 前端無法接收 Home Assistant 實時數據
- 儀表板無法顯示即時數據
- 實體狀態不更新

**狀態**：✅ 已解決（多個修復方案）

---

## 文檔導航

### 🚀 快速開始

如果你遇到這個問題，最快的解決方案：

👉 **[快速參考指南](WEBSOCKET_RESTART_SUMMARY.md)**
- ⏱️ 閱讀時間：5 分鐘
- 📋 包含：快速診斷步驟、4 種修復方案、常見問題

---

### 📚 完整文檔

按推薦閱讀順序：

1. **[文檔索引](WEBSOCKET_DOCUMENTATION_INDEX.md)**
   - 所有文檔的導航和快速查閱
   - 按使用場景、知識深度、修復難度分類
   - 包含診斷決策樹

2. **[問題分析報告](websocket-restart-analysis.md)**
   - 4 個根本原因的詳細分析
   - 代碼檢查點
   - 完整流程圖
   - 診斷建議

3. **[詳細修復指南](websocket-restart-detailed-guide.md)**
   - 完整的技術分析
   - 4 個遞進式修復方案（簡單到複雜）
   - 代碼層級的診斷工具
   - 驗證和測試清單

---

## 快速診斷

### 步驟 1：檢查實例配置

進入 Odoo 管理後台：
1. Settings → Technical → Home Assistant
2. 檢查每個實例：
   - [ ] Active 是否勾選？
   - [ ] API URL 是否為空？
   - [ ] Access Token 是否為空？

### 步驟 2：查看日誌

```bash
docker compose -f docker-compose-18.yml logs web | grep -i "configuration incomplete"
```

### 步驟 3：測試連接

在實例詳細頁面，點擊「Test Connection」按鈕

---

## 修復方案總覽

| 方案 | 時間 | 難度 | 效果 |
|------|------|------|------|
| [方案 1：改進日誌](websocket-restart-detailed-guide.md#方案-1改進實例配置檢查和日誌立即修復) | 15 分鐘 | ⭐ | 提高診斷能力 |
| [方案 2：配置監視](websocket-restart-detailed-guide.md#方案-2實例配置變更監視機制短期修復) | 30 分鐘 | ⭐⭐ | 自動重啟 |
| [方案 3：Graceful Shutdown](websocket-restart-detailed-guide.md#方案-3改進-graceful-shutdown-機制中期修復) | 45 分鐘 | ⭐⭐ | 防止資源洩漏 |
| [方案 4：自動監視](websocket-restart-detailed-guide.md#方案-4完整的服務監視和自動恢復長期修復) | 2-3 小時 | ⭐⭐⭐ | 生產就緒 |

---

## 根本原因

按發生概率排序：

1. **實例配置不完整**（最可能）
   - `api_url` 或 `api_token` 為空
   - post_load_hook 檢查失敗，跳過啟動

2. **實例未標記為活躍**
   - Instance 的 `active` 字段為 False

3. **Post-Load Hook 執行時序問題**
   - 模型初始化不完整

4. **Daemon 執行緒未正確清理**
   - WebSocket 連接未正確關閉

---

## 相關程式碼

| 文件 | 說明 |
|------|------|
| `hooks.py` | post_load_hook 定義 |
| `models/common/websocket_thread_manager.py` | WebSocket 執行緒管理 |
| `models/common/hass_websocket_service.py` | WebSocket 服務實現 |
| `models/ha_instance.py` | HA 實例模型 |

---

## 更新紀錄

| 日期 | 版本 | 說明 |
|------|------|------|
| 2024-11-08 | 1.0 | 初始文檔（問題分析與修復方案） |
| 2025-11-09 | 1.1 | 重新組織文檔結構 |

---

## 需要幫助？

- **診斷問題**：查看 [快速參考指南](WEBSOCKET_RESTART_SUMMARY.md)
- **理解原因**：閱讀 [問題分析報告](websocket-restart-analysis.md)
- **實施修復**：參考 [詳細修復指南](websocket-restart-detailed-guide.md)
- **查找特定內容**：使用 [文檔索引](WEBSOCKET_DOCUMENTATION_INDEX.md)
