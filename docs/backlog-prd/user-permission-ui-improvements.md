# PRD: User Permission 刪除功能 + UI 跑版修復

## 文件資訊

| 項目 | 內容 |
|------|------|
| 版本 | 1.0 |
| 建立日期 | 2026-01-18 |
| 類型 | 功能增強 + Bug 修復 |

---

## 項目 A: User Permission 刪除功能

**優先順序**：P1（高）| **複雜度**：低

### 問題描述

Entity Group 的授權使用者 (`user_ids`) 使用 `many2many_tags` widget，無法逐個刪除授權使用者。

### 現狀分析

**Entity 分享**（已完整實作）：
- 使用 `ha.entity.share` 模型
- 視圖中有 "Revoke" 按鈕

**Entity Group 使用者授權**（缺少刪除功能）：
- 使用 `many2many` 欄位 `user_ids`
- 目前視圖使用 `many2many_tags` widget

### 相關檔案

**位置**：`views/ha_entity_group_views.xml:104-112`

```xml
<page string="Authorized Users" name="authorized_users">
    <field name="user_ids" widget="many2many_tags"
           placeholder="Click to add authorized users"
           options="{'no_create': True}">
        <list string="Authorized Users">
            <field name="name"/>
            <field name="login"/>
            <field name="email"/>
            <field name="active"/>
        </list>
    </field>
    ...
</page>
```

### 解決方案

**方案 1**（推薦）：改用標準 `many2many` widget

```xml
<page string="Authorized Users" name="authorized_users">
    <field name="user_ids">
        <list string="Authorized Users" editable="bottom">
            <field name="name"/>
            <field name="login"/>
            <field name="email"/>
            <field name="active"/>
        </list>
    </field>
</page>
```

標準列表視圖會自動提供刪除按鈕（垃圾桶圖標）。

**方案 2**：保留 `many2many_tags` 但確保 X 按鈕可用

`many2many_tags` widget 預設應支援點擊 X 刪除標籤。需檢查是否有 CSS 或配置隱藏了此功能。

### 驗收標準

- [ ] 可以在 Entity Group 表單中逐個刪除授權使用者
- [ ] 刪除操作有視覺反饋（如確認或動畫）
- [ ] 刪除後，使用者立即失去該 Entity Group 的存取權
- [ ] 操作記錄在 chatter 中（`user_ids` 已有 `tracking=True`）

---

## 項目 B: UI 跑版修復

**優先順序**：P2（中）| **複雜度**：低

### 問題描述

Entity Share Wizard 的提示訊息區塊（已分享使用者資訊）顯示為多行，應為單行。

### 問題位置

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

### 問題分析

1. `<group>` 元素內包含 `<div>` 可能導致 Odoo 的佈局機制產生非預期行為
2. 欄位標籤和值可能被強制換行

### 解決方案

調整 HTML 結構，使用 flexbox 確保單行顯示：

```xml
<group invisible="existing_share_count == 0">
    <div class="alert alert-info d-flex align-items-center flex-wrap" role="status">
        <i class="fa fa-info-circle me-2" title="Info"/>
        <span class="me-1"><strong>Already shared with:</strong></span>
        <field name="existing_share_users" nolabel="1" class="me-1"/>
        <span>(<field name="existing_share_count" nolabel="1" class="d-inline"/> users)</span>
    </div>
</group>
```

**變更說明**：
- 新增 `d-flex align-items-center flex-wrap` 確保內容水平排列
- 使用 `me-1` 控制元素間距
- 新增 `d-inline` 確保欄位內聯顯示

### 驗收標準

- [ ] 「Already shared with」訊息顯示為單行
- [ ] 使用者名稱和數量在同一行
- [ ] 在不同螢幕寬度下保持正確顯示（或優雅換行）
- [ ] 符合 Odoo 18 的 UI 規範

---

## 測試計畫

### 項目 A 測試

**手動測試**：
1. 開啟 Entity Group 表單
2. 在「Authorized Users」tab 中新增使用者
3. 嘗試刪除使用者
4. 確認刪除成功且 chatter 有記錄

**自動化測試**：
```python
def test_can_remove_user_from_entity_group(self):
    """User should be removable from entity group"""
    # 1. Add user to group
    # 2. Remove user from group via UI simulation
    # 3. Verify user no longer in user_ids
```

### 項目 B 測試

**手動測試**：
1. 開啟已有分享記錄的 Entity
2. 點擊「Share」按鈕開啟 Share Wizard
3. 確認「Already shared with」訊息為單行
4. 調整瀏覽器寬度，確認響應式行為

**視覺測試**：
- 使用 Playwright 截圖比對

---

## 相關檔案摘要

| 檔案 | 項目 | 說明 |
|------|------|------|
| `views/ha_entity_group_views.xml:104-112` | A | user_ids 視圖配置 |
| `views/ha_entity_share_wizard_views.xml:20-27` | B | 跑版區塊 |
