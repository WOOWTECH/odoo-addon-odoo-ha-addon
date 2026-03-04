# Blueprint 動態表單欄位系統 PRD

**Created:** 2026-03-04T09:55:49Z
**Status:** Draft
**Author:** Claude Code Assistant

---

## 1. 概述與目標

### 1.1 背景

目前 Automation 和 Script 的 Blueprint Inputs 使用 JSON 編輯器（Ace Editor）讓用戶輸入參數，這對非技術用戶不友善，容易輸入錯誤，且無法利用 Odoo 的關聯欄位特性（如 Entity selector 自動帶出可選項目）。

### 1.2 目標

1. **移除 Blueprint Metadata (Schema) 區塊** - 使用者不需要看到原始 Schema
2. **Blueprint Inputs 改用動態表單欄位** - 根據 Blueprint Schema 自動產生對應的 Odoo 欄位元件
3. **100% 對應 HA Blueprint selector 類型** - 分三階段完整支援所有 selector
4. **新增「新增」按鈕** - Automation/Script 列表頁面左上角增加建立按鈕

### 1.3 範圍

- Automation model
- Script model

### 1.4 不在範圍內

- 其他 entity types 的 Blueprint 支援
- Blueprint 的建立/刪除（這在 HA 端進行）

---

## 2. 功能需求

### 2.1 移除 Blueprint Metadata (Schema)

**現狀**：Blueprint 表單頁籤顯示兩個區塊
- Blueprint Inputs（JSON 編輯器）
- Blueprint Metadata (Schema)（唯讀 JSON）

**目標**：移除 Blueprint Metadata (Schema) 區塊，僅保留 Blueprint Inputs 區塊（但改為動態表單欄位）

### 2.2 Blueprint Inputs 動態表單欄位

**現狀**：使用 Ace Editor 讓用戶手動編輯 JSON

**目標**：根據 Blueprint Schema 的 `input` 定義，動態產生對應的 Odoo 欄位元件

**範例轉換**：
```yaml
# Blueprint Schema 定義
input:
  light_entities:
    name: "燈光（可複選）"
    selector:
      entity:
        multiple: true
        filter:
          - domain: light

# 轉換為 Odoo 欄位
→ Many2many 欄位，domain 過濾 ha.entity 中 domain='light' 的記錄
```

### 2.3 新增表單按鈕（Create）

**現狀**：Automation 和 Script 列表頁面沒有「新增」按鈕

**目標**：在列表頁面左上角增加「新增」按鈕，點擊後：
1. 開啟建立表單
2. 用戶選擇 Blueprint（或不選擇，手動建立）
3. 動態載入該 Blueprint 的欄位
4. 填寫後同步建立到 Home Assistant

---

## 3. Selector 類型對應（三階段實作）

### 3.1 Phase 1 - 基礎類型（優先實作）

| HA Selector | Odoo Widget | 說明 |
|-------------|-------------|------|
| `entity` | Many2one/Many2many + domain filter | 從 ha.entity 選擇，支援 domain/device_class 過濾 |
| `device` | Many2one/Many2many | 從 ha.device 選擇 |
| `area` | Many2one/Many2many | 從 ha.area 選擇 |
| `target` | 自訂複合元件 | 組合 entity + device + area 選擇器 |
| `text` | Char | 文字輸入，支援 multiline |
| `number` | Integer/Float + slider widget | 支援 min/max/step/mode(box/slider) |
| `boolean` | Boolean toggle | 開關切換 |
| `select` | Selection | 下拉選單，options 來自 schema |
| `time` | Float + time widget | 時間選擇 (HH:MM:SS) |
| `date` | Date | 日期選擇 |
| `datetime` | Datetime | 日期時間選擇 |
| `duration` | 自訂元件 | 時間長度 (hours/minutes/seconds) |

### 3.2 Phase 2 - 進階類型

| HA Selector | Odoo Widget | 說明 |
|-------------|-------------|------|
| `action` | 自訂巢狀編輯器 | 動作序列編輯（服務呼叫、延遲等） |
| `condition` | 自訂巢狀編輯器 | 條件編輯（state/numeric_state/template 等） |
| `trigger` | 自訂巢狀編輯器 | 觸發器編輯（state/time/event 等） |
| `template` | Text + Jinja2 語法提示 | Jinja2 模板輸入 |
| `object` | Ace Editor (fallback) | 任意 YAML/JSON 物件 |

### 3.3 Phase 3 - 特殊類型

| HA Selector | Odoo Widget | 說明 |
|-------------|-------------|------|
| `icon` | 自訂圖示選擇器 | mdi: 圖示選擇 |
| `color_rgb` | Color picker | RGB 顏色選擇 |
| `color_temp` | Slider | 色溫選擇 (mired) |
| `media` | 自訂媒體選擇器 | 媒體檔案選擇 |
| `location` | 自訂地圖元件 | GPS 座標選擇 |
| `attribute` | 動態 Selection | 根據 entity 動態載入屬性列表 |
| `theme` | Selection | HA 主題選擇 |
| `addon` | Selection | HA Add-on 選擇 |
| `backup_location` | Selection | 備份位置選擇 |
| `conversation_agent` | Selection | 對話代理選擇 |

---

## 4. UI/UX 設計

### 4.1 Automation/Script 列表頁面

**新增按鈕位置**：左上角，與其他 Odoo model 列表一致

```
┌─────────────────────────────────────────────────────────────┐
│ [+ 新增]                                    Automations     │
├─────────────────────────────────────────────────────────────┤
│ ☐ │ Name                    │ State │ Blueprint │ Area     │
├───┼─────────────────────────┼───────┼───────────┼──────────┤
│ ☐ │ Blueprint Test Sync     │ on    │ ✓         │ 客廳     │
│ ☐ │ Motion Light            │ off   │ ✗         │ 玄關     │
└───┴─────────────────────────┴───────┴───────────┴──────────┘
```

### 4.2 建立表單流程

**Step 1**：點擊「新增」→ 開啟建立表單

**Step 2**：選擇建立方式
- **從 Blueprint 建立**：選擇 Blueprint → 動態載入欄位
- **手動建立**：顯示基本欄位（名稱、描述等）

**Step 3**：填寫欄位 → 儲存 → 同步到 HA

### 4.3 Blueprint 表單欄位區塊（取代 JSON 編輯器）

```
┌─────────────────────────────────────────────────────────────┐
│ Blueprint Information                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Blueprint Path: homeassistant/motion_light.yaml         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ Blueprint Inputs                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 燈光（可複選）*                                          │ │
│ │ [light.living_room ×] [light.bedroom ×] [+ 選擇實體]    │ │
│ │                                                          │ │
│ │ 動作感應器*                                              │ │
│ │ [binary_sensor.motion_detector     ▼]                   │ │
│ │                                                          │ │
│ │ 延遲關閉時間                                             │ │
│ │ [====●============] 120 秒                              │ │
│ │                                                          │ │
│ │ 額外條件（選填）                                         │ │
│ │ [+ 新增條件]                                            │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**欄位顯示規則**：
- 欄位標籤使用 Schema 中的 `name`
- 必填欄位顯示 `*` 標記
- 欄位說明使用 Schema 中的 `description`（hover tooltip）
- 分組顯示（如果 Schema 有定義 `collapsed` section）

---

## 5. E2E 測試計畫

### 5.1 測試環境

| 項目 | 值 |
|------|-----|
| Odoo URL | http://localhost:8069 |
| Database | woowtech |
| 帳號 | woowtech@designsmart.com.tw |
| 密碼 | admin |
| HA Instance | woowtech show |
| 測試工具 | Playwright MCP |

### 5.2 測試資料

使用系統現有的 Blueprint Automation/Script 進行測試：
- `Blueprint Test Sync Automation` (automation.blueprint_test_sync_automation)
- 其他現有的 Blueprint-based Automation/Script

### 5.3 Phase 1 測試案例

#### TC-01: 新增按鈕存在性測試

**步驟**：
1. 進入 Configuration > Automation 列表頁面
2. 檢查左上角是否有「新增」按鈕

**預期結果**：「新增」按鈕存在且可點擊

---

#### TC-02: Blueprint Metadata 移除驗證

**步驟**：
1. 開啟一個 Blueprint-based Automation 表單
2. 切換到 Blueprint 頁籤

**預期結果**：
- ❌ 不顯示 "Blueprint Metadata (Schema)" 區塊
- ✅ 顯示 "Blueprint Inputs" 區塊（動態欄位形式）

---

#### TC-03: Entity Selector 欄位測試

**步驟**：
1. 開啟有 `entity` selector 的 Blueprint Automation
2. 點擊 entity 欄位

**預期結果**：
- 顯示 Odoo Many2one/Many2many 選擇器
- 選項根據 Schema 的 filter（如 domain: light）正確過濾
- 選擇後值正確顯示

**邊緣案例**：
- 選擇不存在的 entity → 應顯示錯誤或不允許選擇
- 清空必填欄位 → 儲存時應顯示驗證錯誤
- 選擇 unavailable 狀態的 entity → 應允許但顯示警告

---

#### TC-04: Number Selector (Slider) 測試

**步驟**：
1. 開啟有 `number` selector (mode: slider) 的 Blueprint
2. 拖動滑桿

**預期結果**：
- 滑桿符合 min/max/step 設定
- 即時顯示數值

**邊緣案例**：
- 輸入超出 min/max 範圍的值 → 應自動校正或顯示錯誤
- 輸入非數字 → 應阻止或顯示錯誤
- step 為小數時 → 應正確處理

---

#### TC-05: Boolean Selector 測試

**步驟**：
1. 開啟有 `boolean` selector 的 Blueprint
2. 切換開關

**預期結果**：
- 顯示為 toggle 開關
- 點擊後狀態切換

---

#### TC-06: Select Selector 測試

**步驟**：
1. 開啟有 `select` selector 的 Blueprint
2. 點擊下拉選單

**預期結果**：
- 選項與 Schema 中的 options 一致
- 選擇後值正確顯示

**邊緣案例**：
- options 為空 → 應顯示空下拉或提示
- 選項包含特殊字元 → 應正確顯示

---

#### TC-07: 建立新 Automation（從 Blueprint）

**步驟**：
1. 在 Automation 列表點擊「新增」
2. 選擇一個 Blueprint
3. 填寫所有必填欄位
4. 點擊儲存

**預期結果**：
- 儲存成功，無錯誤
- 新 Automation 出現在列表中
- HA 同步成功（可透過 Trigger 按鈕驗證）

**邊緣案例**：
- 不填寫必填欄位 → 應顯示驗證錯誤
- 填寫重複名稱 → 應顯示錯誤或允許（依 HA 規則）
- 網路斷線時儲存 → 應顯示錯誤訊息

---

#### TC-08: 編輯現有 Blueprint Automation

**步驟**：
1. 開啟現有 Blueprint Automation
2. 修改 Blueprint Inputs 欄位值
3. 點擊儲存

**預期結果**：
- 儲存成功
- HA 同步成功
- 重新開啟表單，值已更新

**邊緣案例**：
- 修改後不儲存直接離開 → 應提示未儲存變更
- 同時有其他人在 HA 修改 → 應處理衝突

---

### 5.4 Script Model 測試

重複上述 TC-01 ~ TC-08 測試案例，針對 Script model 執行。

---

## 6. 技術架構與實作方向

### 6.1 後端架構

**新增/修改檔案**：

| 檔案 | 說明 |
|------|------|
| `models/ha_automation.py` | Automation model（繼承 ha.entity 或獨立 model） |
| `models/ha_script.py` | Script model |
| `models/ha_blueprint_mixin.py` | Blueprint 共用邏輯 mixin |
| `models/ha_blueprint_field_parser.py` | Schema → Odoo 欄位解析器 |

**Schema 解析流程**：
```
Blueprint Schema (JSON)
    ↓
BlueprintFieldParser.parse()
    ↓
動態產生 Odoo fields（Transient Model 或 Properties）
    ↓
View 渲染
```

### 6.2 前端架構

**新增/修改檔案**：

| 檔案 | 說明 |
|------|------|
| `static/src/components/blueprint_form/` | Blueprint 動態表單元件 |
| `static/src/widgets/blueprint_selectors/` | 各種 Selector widget |
| `views/ha_automation_views.xml` | Automation 專屬視圖 |
| `views/ha_script_views.xml` | Script 專屬視圖 |

### 6.3 HA 同步機制

**建立流程**：
```
Odoo 表單儲存
    ↓
轉換欄位值為 Blueprint input 格式
    ↓
呼叫 HA WebSocket API: automation/config 或 script/config
    ↓
接收回應，更新 Odoo 記錄
```

**更新流程**：
```
Odoo 表單儲存
    ↓
比對變更欄位
    ↓
呼叫 HA API 更新
    ↓
同步狀態回 Odoo
```

---

## 7. 驗收標準

### 7.1 必須通過（Phase 1）

| 項目 | 標準 |
|------|------|
| 新增按鈕 | Automation/Script 列表都有「新增」按鈕 |
| Metadata 移除 | Blueprint 頁籤不顯示 Schema 區塊 |
| 基礎 Selector | 12 種基礎類型全部正確渲染 |
| CRUD 功能 | 新增/讀取/更新/刪除都能同步到 HA |
| E2E 測試 | TC-01 ~ TC-08 全部通過 |

### 7.2 整體驗收

- 所有 Phase 1 測試案例通過
- 無 Console 錯誤
- 無 UI 錯誤訊息
- 效能：表單載入 < 3 秒
- 相容性：現有 Blueprint Automation/Script 可正常顯示和編輯

---

## 8. 相關文件

- Scene CRUD E2E 測試 PRD：`docs/plans/2026-02-28-scene-crud-e2e-test.md`
- HA 串接文件：`docs/homeassistant-api/HA_串接文件/HA 串接文件.md`
- E2E 測試設定：`tests/e2e_tests/e2e_config.yaml`
