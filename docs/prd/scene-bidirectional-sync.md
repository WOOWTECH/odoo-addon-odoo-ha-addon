# PRD: Scene Bidirectional Sync (場景雙向同步)

## Overview

實現 Odoo 與 Home Assistant 之間的場景 (Scene) 雙向同步功能，包含完整的 CRUD 操作。

## Problem Statement

目前場景管理存在以下問題：
1. 場景實體選擇器顯示「裝置」而非「實體」
2. 需要確保 Odoo 和 HA 之間的場景資料保持同步
3. 在 Odoo 建立的場景需要正確同步到 HA
4. 在 HA 建立的場景需要正確同步到 Odoo

## Goals

1. **雙向同步**: Odoo ↔ HA 場景資料完全同步
2. **正確的實體選擇**: 場景應該包含實體 (entities) 而非裝置 (devices)
3. **完整 CRUD 支援**: 新增、查詢、編輯、刪除操作都能正確同步

## User Stories

### US1: 在 Odoo 新增場景
- 用戶在 Odoo 建立新場景
- 選擇要包含的實體 (如 light.*, switch.* 等)
- 儲存後場景自動同步到 HA

### US2: 在 Odoo 編輯場景
- 用戶修改場景名稱或包含的實體
- 儲存後變更同步到 HA

### US3: 在 Odoo 刪除場景
- 用戶刪除場景
- HA 中對應的場景也被刪除

### US4: 從 HA 同步場景
- HA 中新建/修改的場景同步到 Odoo
- 場景包含的實體正確對應

## Technical Requirements

### Scene Entity Selector
- 必須顯示 `ha.entity` 記錄而非 `ha.device`
- 過濾條件: `domain in ['light', 'switch', 'cover', 'fan', 'climate', 'input_boolean', 'input_number', 'media_player']`
- 使用輕量級視圖減少資料傳輸

### Sync Mechanism
- Odoo → HA: 使用 HA REST API `/api/config/scene/config/{id}`
- HA → Odoo: 透過 WebSocket 訂閱或手動同步

### Data Mapping
| Odoo Field | HA Field |
|------------|----------|
| name | name (friendly_name) |
| entity_id | scene.{id} |
| scene_entity_ids | entities (包含狀態快照) |
| ha_scene_id | id (timestamp format) |

## Test Plan

### Test 1: Odoo → HA 新增場景
1. 在 Odoo 建立場景，選擇實體
2. 驗證 HA 中出現對應場景
3. 驗證場景包含正確的實體

### Test 2: Odoo → HA 編輯場景
1. 修改 Odoo 中的場景名稱
2. 驗證 HA 中場景名稱更新

### Test 3: Odoo → HA 刪除場景
1. 刪除 Odoo 中的場景
2. 驗證 HA 中場景被移除

### Test 4: HA → Odoo 同步
1. 在 HA 建立場景
2. 觸發同步
3. 驗證 Odoo 中出現場景

### Test 5: 實體選擇器驗證
1. 開啟場景編輯表單
2. 確認 Scene Entities 分頁顯示實體而非裝置
3. 確認可以正常新增/移除實體

## Success Criteria

- [ ] 場景 CRUD 操作雙向同步正常
- [ ] 場景實體選擇器顯示實體 (entity_id 格式)
- [ ] 無連線斷開或超時問題
- [ ] 同步後資料一致性 100%

## Timeline

- Phase 1: 修復實體選擇器 (已完成視圖優化)
- Phase 2: 測試雙向同步
- Phase 3: 修復發現的問題
