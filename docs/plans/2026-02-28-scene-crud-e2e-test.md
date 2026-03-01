# Scene CRUD E2E 測試 PRD

**Created:** 2026-02-28T08:55:25Z
**Status:** Active
**Author:** Claude Code Assistant

---

## 1. 概述與目標

**目標**：建立完整的前端 E2E 測試流程，驗證 Odoo 與 Home Assistant 之間 Scene（情境）的雙向 CRUD 同步功能。

### 測試範圍

| 操作 | Odoo 動作 | 驗證方式 |
|------|----------|---------|
| Create | 在 Odoo 建立新 Scene | 同步後在 Entity 列表確認存在 |
| Read | 檢視 Scene 表單 | 確認資料正確載入、無無限載入 |
| Update | 編輯 Scene 實體清單 | 同步後確認實體數量更新 |
| Delete | 刪除 Scene | 確認從列表消失 |

### 測試工具
- **Playwright MCP**（Claude Code 內建）
- 手動觸發，即時驗證

### 測試資料策略
- Scene 命名：`E2E Test Scene {timestamp}`
- 實體選擇：light 和 switch 類型（2-3 個）
- 測試後清理：刪除測試建立的 Scene

---

## 2. 測試案例

### TC-01: Create Scene（建立情境）

**前置條件**：已登入 Odoo，在 Scene 列表頁

**步驟**：
1. 點擊「新增」按鈕
2. 填寫 Scene 名稱：`E2E Test Scene {timestamp}`
3. 切換到「Scene Entities」Tab
4. 選擇 2-3 個 light/switch 實體
5. 點擊「儲存」

**預期結果**：
- Scene 建立成功，無錯誤訊息
- 自動跳轉到表單視圖
- Entity Count 顯示正確數量
- 在 Scene 列表可找到新建立的 Scene

---

### TC-02: Read Scene（讀取情境）

**前置條件**：已有測試 Scene 存在

**步驟**：
1. 在 Scene 列表點擊目標 Scene
2. 等待表單載入

**預期結果**：
- 表單在 5 秒內載入完成（無無限載入）
- 所有欄位正確顯示：Name、Scene ID、Area
- Scene Entities Tab 顯示已選實體
- Chatter 區域正常載入

---

### TC-03: Update Scene（更新情境）

**前置條件**：已開啟測試 Scene 表單

**步驟**：
1. 切換到「Scene Entities」Tab
2. 新增或移除一個實體
3. 點擊「儲存」

**預期結果**：
- 儲存成功，無錯誤訊息
- Entity Count 更新為新數量
- 返回列表後，實體數量欄位顯示正確

---

### TC-04: Delete Scene（刪除情境）

**前置條件**：已有測試 Scene 存在於列表

**步驟**：
1. 在 Scene 列表勾選目標 Scene
2. 點擊「動作」下拉選單
3. 選擇「刪除」
4. 在確認對話框點擊「刪除」

**預期結果**：
- 刪除操作在 3 秒內完成（無阻塞）
- Scene 從列表消失
- 列表計數正確減少
- 無錯誤訊息

---

## 3. 驗證檢查點

| 檢查點 | 驗證方式 | 通過標準 |
|--------|---------|---------|
| 表單載入速度 | 計時 | < 5 秒 |
| 刪除操作速度 | 計時 | < 3 秒 |
| Entity Count | UI 顯示 | 數字正確 |
| Scene 列表更新 | 搜尋確認 | 存在/消失正確 |
| 無錯誤訊息 | Console/UI | 無紅色錯誤 |
| HA 同步 | Entity 同步後列表 | Scene 出現在 HA |

---

## 4. 測試執行流程

1. **準備**：登入 Odoo → 進入 Scene 列表
2. **執行 TC-01**：建立 Scene，記錄 timestamp
3. **執行 TC-02**：重新開啟驗證載入
4. **執行 TC-03**：編輯實體清單
5. **執行 TC-04**：刪除測試 Scene
6. **清理**：確認無殘留測試資料

---

## 5. 測試環境

| 項目 | 值 |
|------|-----|
| Odoo URL | http://localhost:8069 |
| Database | woowtech |
| 帳號 | admin |
| 密碼 | admin |
| HA Instance | woowtech show |

### 測試實體選擇建議

從現有實體中選擇穩定的 light/switch：
- 優先選擇有明確 Area 的實體
- 避免選擇 unavailable 狀態的實體
- 建議選 2-3 個即可

---

## 6. 成功標準

### 必須通過
- [ ] TC-01: 建立 Scene 成功
- [ ] TC-02: 表單載入 < 5 秒
- [ ] TC-03: 更新 Scene 成功
- [ ] TC-04: 刪除 Scene < 3 秒

### 整體驗收
- 所有 4 個測試案例通過
- 無 Console 錯誤
- 無 UI 錯誤訊息
- 測試資料已清理

---

## 7. 相關文件

- Scene Manager 設計：`docs/plans/2026-02-27-scene-manager-design.md`
- E2E 測試設定：`tests/e2e_tests/e2e_config.yaml`
- Scene 視圖定義：`src/views/ha_scene_views.xml`
