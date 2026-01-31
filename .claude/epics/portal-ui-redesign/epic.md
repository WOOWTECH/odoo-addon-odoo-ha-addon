---
name: portal-ui-redesign
status: completed
created: 2026-01-08T17:21:28Z
progress: 100%
prd: .claude/prds/portal-ui-redesign.md
github: https://github.com/WOOWTECH/odoo-addons/issues/11
pr: https://github.com/WOOWTECH/odoo-addons/pull/21
---

# Epic: portal-ui-redesign

## Overview

將現有 Portal Entity 頁面從傳統 Bootstrap 風格升級為現代 IoT 設備控制中心視覺設計。利用現有的 `static/src/scss/portal.scss` 檔案結構，擴展 CSS Custom Properties 主題系統，並更新 OWL 元件模板以使用新的樣式類別。

**核心策略：** 最小化程式碼變動，最大化視覺影響
- 不修改 OWL JS 邏輯，只更新 XML 模板和 SCSS 樣式
- 利用 CSS-only 解決方案實現主題切換
- 保持與現有 Odoo Portal CSS 的相容性

## Architecture Decisions

### 1. CSS Custom Properties 主題系統
**決定：** 使用 CSS Custom Properties（CSS 變數）實現深色/淺色主題切換
**理由：**
- 不需要 JavaScript 介入，純 CSS 解決方案
- `prefers-color-scheme` 媒體查詢自動適應系統設定
- 現代瀏覽器原生支援，無需 polyfill
- 可與現有 Bootstrap 樣式共存

### 2. 擴展現有 portal.scss 而非建立新檔案
**決定：** 在現有 `static/src/scss/portal.scss` 檔案中擴展樣式
**理由：**
- 減少 Odoo assets bundle 複雜度
- 利用現有的 `.portal-entity-grid` 和 `.portal-entity-card` 結構
- 維護單一來源，降低衝突風險

### 3. BEM-like 命名空間
**決定：** 使用 `.portal-` 前綴的 BEM-like 命名慣例
**理由：**
- 避免與 Odoo Portal 和 Bootstrap 類別衝突
- 清晰的作用域界定
- 現有程式碼已遵循此模式

### 4. 控制元件樣式優化而非重寫
**決定：** 保留現有 OWL 元件結構，僅透過 CSS 樣式提升視覺效果
**理由：**
- 現有的 `PortalEntityController.Switch`、`PortalEntityController.Light` 等模板結構完善
- 只需添加新的 CSS 類別和樣式規則
- 減少測試範圍和回歸風險

## Technical Approach

### Frontend Components

#### 現有檔案（更新）
| 檔案 | 修改類型 | 說明 |
|------|----------|------|
| `static/src/scss/portal.scss` | 大量擴展 | 新增主題變數、控制元件樣式、動畫 |
| `static/src/portal/portal_entity_controller.xml` | 小幅更新 | 添加新的樣式類別 |
| `static/src/portal/portal_entity_info.xml` | 小幅更新 | 添加新的樣式類別 |
| `static/src/portal/portal_group_info.xml` | 小幅更新 | 添加新的樣式類別 |
| `views/portal_templates.xml` | 小幅更新 | 添加主題容器類別 |

#### 不新增檔案
PRD 建議的多檔案 SCSS 架構（portal_theme.scss、portal_components.scss 等）簡化為單一 `portal.scss` 擴展，以降低複雜度。

### CSS 架構

```scss
// portal.scss 結構

// ========================================
// Theme Variables (CSS Custom Properties)
// ========================================
:root {
  // 淺色模式（預設）
  --portal-bg-primary: #f8f9fa;
  --portal-bg-card: #ffffff;
  --portal-text-primary: #1f2937;
  // ... 其他變數
}

@media (prefers-color-scheme: dark) {
  :root {
    // 深色模式覆蓋
    --portal-bg-primary: #1a1a2e;
    --portal-bg-card: #0f3460;
    --portal-text-primary: #e4e4e7;
    // ... 其他變數
  }
}

// ========================================
// Base Components (使用 CSS 變數)
// ========================================
.portal-entity-card {
  background: var(--portal-bg-card);
  color: var(--portal-text-primary);
  // ...
}

// ========================================
// Control Elements (IoT 風格)
// ========================================
.portal-iot-toggle { ... }
.portal-value-slider { ... }
.portal-sensor-display { ... }

// ========================================
// Animations (狀態變化)
// ========================================
@keyframes portal-pulse { ... }
.portal-state-changed { ... }

// ========================================
// Responsive (已存在，微調)
// ========================================
@media (max-width: 576px) { ... }
```

### Backend Services
無後端修改需求。此 Epic 純粹為前端 UI 優化。

### Infrastructure
無基礎設施變更。現有 Odoo assets 編譯流程已支援 SCSS。

## Implementation Strategy

### 開發順序
1. **主題變數系統** - 建立 CSS Custom Properties 基礎
2. **卡片樣式升級** - 更新 `.portal-entity-card` 樣式
3. **控制元件美化** - 升級 Toggle、Slider、Sensor 顯示
4. **動畫效果** - 添加狀態變化視覺回饋
5. **響應式微調** - 確保手機/平板/桌面體驗
6. **整合驗證** - 跨瀏覽器和 WCAG 測試

### 風險緩解
| 風險 | 機率 | 緩解措施 |
|------|------|----------|
| CSS 衝突 Odoo Portal | 低 | 使用 `.portal-` 命名空間 |
| 深色模式對比度不足 | 中 | PRD 已提供驗證過的配色 |
| 動畫效能問題 | 低 | 使用 transform/opacity only |
| 瀏覽器相容性 | 低 | CSS Custom Properties 支援度高 |

### 測試方法
- **視覺回歸測試**：截圖比對（手動或 Playwright）
- **對比度驗證**：WCAG Contrast Checker
- **響應式測試**：Chrome DevTools 設備模擬
- **功能測試**：現有 Portal 功能不受影響

## Task Breakdown Preview

| # | 任務 | 優先級 | 預估 |
|---|------|--------|------|
| 1 | 實作 CSS Custom Properties 主題系統（深色/淺色） | P0 | 2h |
| 2 | 升級 `.portal-entity-card` 卡片樣式 | P0 | 2h |
| 3 | 重設計 IoT Toggle Switch 樣式 | P0 | 2h |
| 4 | 優化 Value Slider（亮度/風速）樣式 | P1 | 1.5h |
| 5 | 增強 Sensor 數值顯示元件 | P1 | 1h |
| 6 | 添加狀態變化動畫效果 | P1 | 1h |
| 7 | 更新 OWL 模板添加新樣式類別 | P0 | 1.5h |
| 8 | 響應式斷點微調和觸控目標優化 | P1 | 1h |
| 9 | 整合測試（跨瀏覽器、WCAG、Odoo 共存） | P0 | 2h |

**總計：9 個任務，約 14 工時（~2 工作天）**

## Dependencies

### 先決條件
- `share_entities` PRD 已完成實作 ✅
- 現有 Portal 頁面功能正常運作 ✅

### 外部依賴
| 依賴 | 狀態 | 說明 |
|------|------|------|
| CSS Custom Properties | 原生支援 | Chrome 49+, Firefox 31+, Safari 9.1+ |
| prefers-color-scheme | 原生支援 | Chrome 76+, Firefox 67+, Safari 12.1+ |
| Odoo 18 SCSS 編譯 | 已存在 | 現有 assets 流程 |

### 內部依賴
| 依賴 | 說明 |
|------|------|
| `static/src/scss/portal.scss` | 擴展此檔案 |
| `static/src/portal/*.xml` | 更新模板類別 |
| `views/portal_templates.xml` | 添加主題容器 |

## Success Criteria (Technical)

| 指標 | 目標 | 驗證方式 |
|------|------|----------|
| 深色模式自動切換 | 系統設定變更後 <1s 切換 | 手動測試 |
| WCAG AA 對比度 | 所有文字組合通過 | Contrast Checker |
| CSS 檔案大小增量 | < 10KB (gzip) | 建置輸出比較 |
| 無 JS 錯誤 | 控制台無新錯誤 | 瀏覽器 DevTools |
| 現有功能不受影響 | 所有 Portal 控制正常 | 手動迴歸測試 |
| 響應式佈局 | 3 種斷點正確顯示 | DevTools 模擬 |

## Estimated Effort

| 項目 | 估算 |
|------|------|
| 總工時 | 14 小時 |
| 工作天數 | 2 天 |
| 任務數量 | 9 個 |
| 檔案修改數 | 5 個 |
| 新增檔案數 | 0 個 |

**關鍵路徑：** 主題變數系統 → 卡片樣式 → 控制元件 → 模板更新 → 測試

## Appendix: 現有檔案分析

### portal.scss 現有結構
```
✅ .portal-state-changed - 狀態變化動畫
✅ .portal-entity-grid - CSS Grid 網格（已有響應式）
✅ .portal-entity-card - 卡片基礎結構
✅ .portal-loading-indicator - 載入指示器
⬜ CSS Custom Properties - 待新增
⬜ 深色模式樣式 - 待新增
⬜ 控制元件 IoT 風格 - 待新增
```

### OWL 模板現有結構
```
portal_entity_controller.xml
├── PortalEntityController.Switch (btn + form-switch)
├── PortalEntityController.Light (btn + form-range)
├── PortalEntityController.Fan (btn + form-range)
├── PortalEntityController.Climate (btn-group + form-control)
├── PortalEntityController.Cover (btn + form-range)
├── PortalEntityController.Sensor (badge + text)
└── PortalEntityController.Generic (badge only)
```

所有控制元件已使用 Bootstrap 類別，可透過 CSS 覆蓋升級視覺效果。

## Tasks Created

- [x] [#12](https://github.com/WOOWTECH/odoo-addons/issues/12) - 實作 CSS Custom Properties 主題系統 (parallel: false)
- [x] [#13](https://github.com/WOOWTECH/odoo-addons/issues/13) - 升級 Portal Entity Card 卡片樣式 (parallel: true, depends_on: #12)
- [x] [#14](https://github.com/WOOWTECH/odoo-addons/issues/14) - 重設計 IoT Toggle Switch 樣式 (parallel: true, depends_on: #12)
- [x] [#15](https://github.com/WOOWTECH/odoo-addons/issues/15) - 優化 Value Slider 樣式 (parallel: true, depends_on: #12)
- [x] [#16](https://github.com/WOOWTECH/odoo-addons/issues/16) - 增強 Sensor 數值顯示元件 (parallel: true, depends_on: #12)
- [x] [#17](https://github.com/WOOWTECH/odoo-addons/issues/17) - 添加狀態變化動畫效果 (parallel: false, depends_on: #12,#13,#14)
- [x] [#18](https://github.com/WOOWTECH/odoo-addons/issues/18) - 更新 OWL 模板添加新樣式類別 (parallel: false, depends_on: #13,#14,#15,#16)
- [x] [#19](https://github.com/WOOWTECH/odoo-addons/issues/19) - 響應式斷點微調和觸控目標優化 (parallel: true, depends_on: #13,#14,#15)
- [x] [#20](https://github.com/WOOWTECH/odoo-addons/issues/20) - 整合測試 (parallel: false, depends_on: all)

**Total tasks:** 9
**Parallel tasks:** 5 (#13, #14, #15, #16, #19)
**Sequential tasks:** 4 (#12, #17, #18, #20)
**Estimated total effort:** 14 hours

### Dependency Graph

```
#12 (主題系統)
 ├─→ #13 (卡片)  ─┬─→ #17 (動畫) ───┐
 ├─→ #14 (Toggle) ┤                │
 ├─→ #15 (Slider) ┼─→ #18 (模板) ──┼─→ #20 (測試)
 └─→ #16 (Sensor) ┘                │
                   └─→ #19 (響應式)─┘
```
