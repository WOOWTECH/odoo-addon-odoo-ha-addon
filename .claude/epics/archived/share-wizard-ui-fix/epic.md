---
name: share-wizard-ui-fix
status: completed
created: 2026-01-18T14:34:18Z
progress: 100%
prd: .claude/prds/share-wizard-ui-fix.md
github: [Will be updated when synced to GitHub]
---

# Epic: Share Wizard UI 跑版修復

## Overview

修復 Entity Share Wizard 對話框中「Already shared with」提示訊息區塊的 UI 跑版問題。問題根因是外層使用了 `<group>` 標籤導致 Odoo 的 group 佈局系統干預，將內容強制分行顯示。

## Architecture Decisions

| 決策 | 說明 |
|------|------|
| 移除外層 `<group>` | 避免 Odoo group 佈局系統干預 div 顯示 |
| 保留 `invisible` 屬性 | 將 `invisible` 屬性直接放在 `<div>` 標籤上，Odoo 18 支援此語法 |
| 沿用 Bootstrap 類別 | 使用 `alert alert-info` 保持樣式一致 |

## Technical Approach

### 修改檔案

| 檔案 | 行號 | 修改內容 |
|------|------|----------|
| `views/ha_entity_share_wizard_views.xml` | 20-27 | 移除 `<group>` wrapper，將 `invisible` 移至 `<div>` |

### 修改前後對比

**修改前：**
```xml
<group invisible="existing_share_count == 0">
    <div class="alert alert-info" role="status">
        <i class="fa fa-info-circle me-2" title="Info"/>
        <strong>Already shared with:</strong>
        <span><field name="existing_share_users" nolabel="1"/></span>
        (<field name="existing_share_count" nolabel="1"/> users)
    </div>
</group>
```

**修改後：**
```xml
<div class="alert alert-info" role="status" invisible="existing_share_count == 0">
    <i class="fa fa-info-circle me-2" title="Info"/>
    <strong>Already shared with:</strong>
    <span><field name="existing_share_users" nolabel="1"/></span>
    (<field name="existing_share_count" nolabel="1"/> users)
</div>
```

## Implementation Strategy

這是一個簡單的單檔修改，無需分階段：
1. 修改 XML 視圖定義
2. 同步到 main project 並重啟 Docker
3. 使用 Playwright MCP 驗證 UI 顯示

## Task Breakdown Preview

此 bug fix 非常簡單，僅需 2 個任務：

- [ ] Task 1: 修改 XML 視圖定義，移除外層 group 標籤
- [ ] Task 2: E2E 測試驗證 UI 顯示正確

## Dependencies

- 無外部依賴
- 測試需要有已分享記錄的 Entity 或 Entity Group

## Success Criteria (Technical)

| 驗收項目 | 驗證方式 |
|---------|---------|
| 「Already shared with」區塊顯示為單行 | Playwright MCP browser_snapshot |
| `invisible` 條件正常運作 | 當 existing_share_count == 0 時不顯示區塊 |
| 不影響 Share Wizard 其他功能 | 完整執行分享流程 |

## Estimated Effort

| 任務 | 預估 |
|------|------|
| 修改 XML | 5 分鐘 |
| 測試驗證 | 15 分鐘 |
| **總計** | **20 分鐘** |

## Tasks Created

- [x] 001.md - 修改 XML 視圖定義，移除外層 group 標籤 (parallel: false)
- [x] 002.md - E2E 測試驗證 UI 顯示正確 (parallel: false, depends_on: 001)

Total tasks: 2
Parallel tasks: 0
Sequential tasks: 2
Estimated total effort: 0.35 hours (~20 minutes)
