---
issue: 3
title: Model Layer - Add portal.mixin
created: 2026-01-02T17:00:00Z
---

# Issue #3 Analysis: Model Layer - Add portal.mixin

## Scope

為 `ha.entity` 和 `ha.entity.group` 新增 `portal.mixin` 繼承，啟用 Portal 分享功能。

## Work Streams

由於這是基礎任務且涉及的檔案有明確區分，可以拆分為單一執行流程：

### Stream A: Complete Implementation
- **Files**: `__manifest__.py`, `models/ha_entity.py`, `models/ha_entity_group.py`
- **Work**: 新增 portal 依賴、繼承 portal.mixin、實作 _compute_access_url

## Implementation Steps

1. **Update `__manifest__.py`**
   - 在 `depends` 列表新增 `'portal'`

2. **Update `models/ha_entity.py`**
   - 在 `_inherit` 列表末尾新增 `'portal.mixin'`
   - 新增 `_compute_access_url` 方法

3. **Update `models/ha_entity_group.py`**
   - 在 `_inherit` 列表末尾新增 `'portal.mixin'`
   - 新增 `_compute_access_url` 方法

## Files to Modify

| File | Change |
|------|--------|
| `__manifest__.py` | Add 'portal' to depends |
| `models/ha_entity.py` | Add portal.mixin, _compute_access_url |
| `models/ha_entity_group.py` | Add portal.mixin, _compute_access_url |

## Verification

- Token 可透過 `_portal_ensure_token()` 正確產生
- `access_url` 計算正確
- 現有功能不受影響

## Notes

- `portal.mixin` 必須放在繼承列表最後
- 不需要手動定義 `access_token` 欄位（由 mixin 提供）
