---
name: share-wizard-ui-fix
description: 修復 Entity Share Wizard 的已分享使用者提示訊息顯示為多行的 UI 問題
status: complete
created: 2026-01-18T14:25:51Z
priority: P2
type: bug-fix
---

# PRD: Share Wizard UI 跑版修復

## Executive Summary

Entity Share Wizard 的「已分享使用者」提示訊息區塊（alert-info）目前顯示為多行，影響視覺一致性。此區塊應該與其他 alert 區塊（如 Permission Levels 說明）一樣顯示為單行。

## Problem Statement

### 問題現象

在 Share Wizard 對話框中，當已有分享使用者時，「Already shared with」提示訊息區塊內的元素被強制分行顯示，而非預期的單行顯示。

### 問題根因

**檔案**：`views/ha_entity_share_wizard_views.xml`
**行號**：20-27

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

外層的 `<group>` 標籤會導致 Odoo 的 group 佈局系統介入，使內部的 div 產生非預期的分行行為。

### 對比參考

同一檔案的第 43-50 行（Permission Levels 說明區塊）沒有使用外層 `<group>`，顯示正確：

```xml
<div class="alert alert-secondary mt-3" role="status">
    <i class="fa fa-lightbulb-o me-2" title="Tip"/>
    <strong>Permission Levels:</strong>
    ...
</div>
```

## User Stories

### US1: 管理者查看分享狀態

```
As a HA Manager sharing an entity or group
I want to see the "Already shared with" info in a clean, single-line format
So that the dialog looks professional and is easy to scan
```

**Acceptance Criteria:**
- 「Already shared with」提示訊息顯示為單行
- icon、文字、使用者名稱、數量在同一行
- 與 Permission Levels 說明區塊的風格一致

## Requirements

### Functional Requirements

| ID | 需求 | 優先順序 |
|----|------|---------|
| FR1 | 移除外層 `<group>` 標籤 | P0 |
| FR2 | 保留 `invisible` 條件控制顯示邏輯 | P0 |
| FR3 | 確保 alert 區塊正確顯示為單行 | P0 |

### Non-Functional Requirements

| ID | 需求 | 目標 |
|----|------|------|
| NFR1 | 視覺一致性 | 與其他 alert 區塊風格一致 |
| NFR2 | 向後相容 | 不破壞現有功能 |

## Technical Solution

### 修改方案

將 `invisible` 屬性移到 `<div>` 標籤上，移除外層 `<group>`：

**修改前：**
```xml
<group invisible="existing_share_count == 0">
    <div class="alert alert-info" role="status">
        ...
    </div>
</group>
```

**修改後：**
```xml
<div class="alert alert-info" role="status" invisible="existing_share_count == 0">
    ...
</div>
```

### 相關檔案

| 檔案 | 說明 |
|------|------|
| `views/ha_entity_share_wizard_views.xml` | Share Wizard 視圖定義（行 20-27） |

## Success Criteria

| 驗收項目 | 驗證方式 |
|---------|---------|
| 提示訊息顯示為單行 | Playwright MCP E2E 測試 |
| 隱藏邏輯仍正常運作 | 確認當 existing_share_count == 0 時不顯示 |
| 不影響其他 wizard 功能 | 手動測試分享流程 |

## Test Plan

### Playwright MCP 測試步驟

1. 以 admin 登入
2. 導航到已有分享記錄的 Entity 或 Entity Group
3. 點擊 Share 按鈕開啟 wizard
4. 使用 browser_snapshot 確認「Already shared with」區塊顯示格式
5. 驗證所有元素在同一行

### 負面測試

| 測試案例 | 預期結果 |
|---------|---------|
| 無分享記錄時 | 提示區塊應隱藏 |
| 有分享記錄時 | 提示區塊應顯示為單行 |

## Out of Scope

- Share Wizard 的其他功能修改
- user_ids 欄位的刪除功能（已在 Sharing 分頁提供）
- 其他 UI 元件的風格調整

## Dependencies

- 無外部依賴
- 需要有已分享記錄的測試資料

## Constraints

- 必須保持 `invisible` 條件邏輯正常運作
- 不能影響 Share Wizard 的其他功能

## Risk Assessment

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| invisible 屬性在 div 上不生效 | 低 | 中 | 測試驗證，Odoo 18 支援此語法 |
| 其他瀏覽器顯示不一致 | 低 | 低 | 使用 Bootstrap 標準類別 |

## Estimated Effort

| 任務 | 預估 |
|------|------|
| 修改 XML | 5 分鐘 |
| 測試驗證 | 15 分鐘 |
| **總計** | **20 分鐘** |
