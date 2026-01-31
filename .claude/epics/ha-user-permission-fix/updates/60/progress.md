---
stream: Main
started: 2026-01-18T09:50:00Z
completed: 2026-01-18T09:53:21Z
status: completed
---

## Completed
- [x] 分析根因：ir.rule 快取未正確失效
- [x] 修復 `models/ha_entity_group.py`：新增 create/write 方法覆寫
- [x] 在 user_ids 變更時呼叫 `env['ir.rule'].clear_caches()`
- [x] 同步到 main 專案
- [x] 重啟 Docker

## Summary
修復已完成。當 `ha.entity.group` 的 `user_ids` 欄位被修改時，
會自動清除 ir.rule 快取，確保權限變更立即生效。
