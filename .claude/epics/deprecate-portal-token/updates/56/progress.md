---
issue: 56
started: 2026-01-17T18:30:35Z
last_sync: 2026-01-18T05:48:22Z
completion: 100%
---

# Issue #56: 更新 View 層 - Progress

## ✅ Completed Work

- [x] `views/ha_entity_views.xml` 移除 "Share via Link" 按鈕
- [x] `views/ha_entity_group_views.xml` 移除 "Share via Link" 按鈕
- [x] 確認 "Share with Users" 按鈕（action_share）保留
- [x] XML 語法正確

## 📦 Deliverables

- `views/ha_entity_views.xml` - header 只保留 "Share with Users" 按鈕
- `views/ha_entity_group_views.xml` - header 只保留 "Share with Users" 按鈕

## 🧪 Testing

- E2E 測試: ✅ 通過 (Playwright MCP)
- Entity Form: ✅ "Share with Users" 按鈕存在
- Entity Group Form: ✅ "Share with Users" 按鈕存在
- Share via Link: ✅ 不存在（已移除）

## 📝 Technical Notes

View 修改內容：
1. `ha_entity_views.xml`: header 中移除 `action_share_portal` 按鈕
2. `ha_entity_group_views.xml`: header 中移除 `action_share_portal` 按鈕
3. 保留的按鈕: `action_share` (user-based sharing)

<!-- SYNCED: 2026-01-18T05:48:22Z -->
