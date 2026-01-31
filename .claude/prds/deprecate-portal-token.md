---
name: deprecate-portal-token
description: 移除 Portal access token 機制，保留 user-based portal 頁面
status: complete
created: 2026-01-17T18:21:31Z
updated: 2026-01-17T18:30:35Z
---

# PRD: Portal Access Token 機制移除

## 文件資訊

| 項目 | 內容 |
|------|------|
| 版本 | 2.0 |
| 優先順序 | P0（最高） |
| 類型 | 功能移除（小範圍） |
| 建立日期 | 2026-01-18 |
| 預估影響 | 修改 ~5 檔案、刪除 ~1 測試檔案 |

---

## Executive Summary

移除 `portal.mixin` 繼承和 token-based 分享機制（`action_share_portal()`），但**保留** Portal 頁面給已登入用戶使用。

**現況**：Controller 已經使用 user-based sharing（`ha.entity.share` 記錄），但 model 還有舊的 token 機制遺留。

**目標**：清理 model 層的 token 遺留程式碼。

---

## 範圍定義

### 要移除的（Token 機制）

| 項目 | 檔案 | 說明 |
|------|------|------|
| `portal.mixin` 繼承 | ha_entity.py, ha_entity_group.py | 提供 access_token 欄位 |
| `action_share_portal()` | ha_entity.py, ha_entity_group.py | 開啟 portal.share wizard |
| "Share via Link" 按鈕 | ha_entity_views.xml, ha_entity_group_views.xml | UI 觸發點 |
| portal 依賴 | __manifest__.py | portal.share wizard 依賴 |
| Token 測試 | tests/test_portal_mixin.py | 測試 token 機制 |

### 要保留的（User-based Portal）

| 項目 | 檔案 | 說明 |
|------|------|------|
| Portal Controller | controllers/portal.py | ✅ 已是 user-based |
| Portal 模板 | views/portal_templates.xml | ✅ 保留 |
| Portal 前端元件 | static/src/portal/ | ✅ 保留 |
| Portal 樣式 | static/src/scss/portal.scss | ✅ 保留 |
| `/portal/entity/*` 路由 | - | ✅ 保留（需登入） |
| `/my/ha/*` 路由 | - | ✅ 保留 |
| `action_share()` | ha_entity.py, ha_entity_group.py | ✅ User-based sharing |
| Controller 測試 | tests/test_portal_controller.py | ✅ 保留 |
| /my/ha 測試 | tests/test_portal_my_ha.py | ✅ 保留 |

---

## Requirements

### Functional Requirements

#### FR-1: 移除 portal.mixin 繼承
- 從 `ha.entity` 的 `_inherit` 列表移除 `'portal.mixin'`
- 從 `ha.entity_group` 的 `_inherit` 列表移除 `'portal.mixin'`

#### FR-2: 移除 action_share_portal 方法
- 從 `ha.entity` 移除 `action_share_portal()` 方法
- 從 `ha.entity_group` 移除 `action_share_portal()` 方法

#### FR-3: 移除 Share via Link 按鈕
- 從 Entity form view 移除 "Share via Link" 按鈕
- 從 Entity Group form view 移除 "Share via Link" 按鈕

#### FR-4: 更新 Manifest（條件性）
- 評估是否需要從 `depends` 移除 `'portal'`
- 注意：如果 portal templates 仍使用 portal 模組功能，則保留依賴

#### FR-5: 清理測試
- 刪除 `tests/test_portal_mixin.py`（測試 token 機制）
- 保留其他 portal 相關測試

---

## Success Criteria

| 指標 | 目標 |
|------|------|
| portal.mixin 移除 | grep 無 portal.mixin 引用 |
| action_share_portal 移除 | grep 無 action_share_portal 引用 |
| Portal 頁面正常 | `/portal/entity/*` 可正常存取（需登入） |
| User-based sharing 正常 | `action_share()` 功能正常 |
| 測試通過 | 保留的 portal 測試全部通過 |

---

## Out of Scope

1. **不移除 Portal Controller** - `controllers/portal.py` 保留
2. **不移除 Portal 模板** - `views/portal_templates.xml` 保留
3. **不移除 Portal 前端元件** - `static/src/portal/` 保留
4. **不移除 User-based Sharing** - `action_share()` 和 `ha.entity.share` 保留

---

## Detailed File Changes

### 需要編輯的檔案（4 項）

| 檔案路徑 | 修改內容 |
|---------|---------|
| `models/ha_entity.py` | 移除 portal.mixin 繼承、action_share_portal() |
| `models/ha_entity_group.py` | 移除 portal.mixin 繼承、action_share_portal() |
| `views/ha_entity_views.xml` | 移除 Share via Link 按鈕 |
| `views/ha_entity_group_views.xml` | 移除 Share via Link 按鈕 |

### 需要刪除的檔案（1 項）

| 檔案路徑 | 說明 |
|---------|------|
| `tests/test_portal_mixin.py` | Token 機制測試 |

### 可能需要修改（待評估）

| 檔案路徑 | 說明 |
|---------|------|
| `__manifest__.py` | 評估是否移除 portal 依賴 |

---

## Risk Assessment

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|----------|
| 移除 portal 依賴影響模板 | 中 | 高 | 先測試再移除 |
| 遺漏 token 相關程式碼 | 低 | 低 | grep 掃描驗證 |

---

## Estimated Effort

| 項目 | 預估 |
|------|------|
| 總任務數 | 3 |
| 預估時間 | 30 分鐘 |
| 複雜度 | 低 |
