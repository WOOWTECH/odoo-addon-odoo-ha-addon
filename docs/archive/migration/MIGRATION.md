# 數據庫遷移指南：`state` → `entity_state`

## 📋 遷移概述

本次重構將 `ha.entity`, `ha.entity.history`, 和 `ha.sensor` 模型中的 `state` 字段重命名為 `entity_state`，以避免與 Odoo 保留字段衝突。

## ⚠️ 重要提示

**在執行模組升級前，必須先執行 SQL 遷移腳本！**

## 🔧 遷移步驟

### 步驟 1：備份數據庫

```bash
# 進入 Docker 容器
docker compose exec db bash

# 備份數據庫
pg_dump -U odoo odoo > /tmp/odoo_backup_$(date +%Y%m%d_%H%M%S).sql
```

### 步驟 2：執行 SQL 遷移

```bash
# 進入 PostgreSQL
docker compose exec db psql -U odoo -d odoo
```

然後執行以下 SQL：

```sql
-- ========================================
-- 遷移腳本：重命名 state 為 entity_state
-- ========================================

BEGIN;

-- 1. 重命名 ha_entity 表的 state 欄位
ALTER TABLE ha_entity
RENAME COLUMN state TO entity_state;

-- 2. 重命名 ha_entity_history 表的 state 欄位
ALTER TABLE ha_entity_history
RENAME COLUMN state TO entity_state;

-- 3. 重命名 ha_sensor 表的 state 欄位
ALTER TABLE ha_sensor
RENAME COLUMN state TO entity_state;

-- 4. 驗證遷移結果
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name IN ('ha_entity', 'ha_entity_history', 'ha_sensor')
AND column_name IN ('state', 'entity_state')
ORDER BY table_name, column_name;

-- 如果一切正常，提交事務
COMMIT;

-- 若有錯誤，可以執行 ROLLBACK; 回滾
```

### 步驟 3：升級模組

```bash
# 重啟並升級模組
docker compose restart web
docker compose exec web odoo -d odoo -u odoo_ha_addon --dev xml
```

## 🔍 驗證遷移

### 檢查數據庫結構

```sql
-- 確認欄位已重命名
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ha_entity'
AND column_name = 'entity_state';

-- 檢查數據完整性
SELECT COUNT(*), COUNT(entity_state)
FROM ha_entity;

SELECT COUNT(*), COUNT(entity_state)
FROM ha_entity_history;

SELECT COUNT(*), COUNT(entity_state)
FROM ha_sensor;
```

### 檢查 Odoo 介面

1. 前往 **Home Assistant > HA Entity**
2. 確認列表視圖顯示 "Entity State" 欄位
3. 打開任一實體，確認表單視圖正常顯示

## 🚨 回滾步驟（如果需要）

如果遷移出現問題，可以回滾：

```sql
BEGIN;

-- 1. 還原 ha_entity
ALTER TABLE ha_entity
RENAME COLUMN entity_state TO state;

-- 2. 還原 ha_entity_history
ALTER TABLE ha_entity_history
RENAME COLUMN entity_state TO state;

-- 3. 還原 ha_sensor
ALTER TABLE ha_sensor
RENAME COLUMN entity_state TO state;

COMMIT;
```

然後還原代碼版本並重啟服務。

## 📝 修改摘要

### 後端 Python（10 個文件）

- `models/ha_entity.py` - 模型定義 + 業務邏輯（6 處）
- `models/ha_entity_history.py` - 模型定義 + 業務邏輯（4 處）
- `models/ha_sensor.py` - 模型定義 + 業務邏輯（2 處）
- `models/common/hass_websocket_service.py` - WebSocket 處理（3 處）
- `controllers/controllers.py` - API 端點（1 處）

### XML 視圖（5 個文件，8 處）

- `views/ha_entity_views.xml`（4 處）
- `views/ha_entity_history_views.xml`（1 處）
- `views/ha_sensor_views.xml`（2 處）
- `views/ha_entity_group_views.xml`（1 處）

### 前端 JavaScript（2 個文件，5 處）

- `static/src/services/ha_data_service.js`（3 處）
- `static/src/components/entity_controller/hooks/useEntityControl.js`（2 處）

## ✅ 預期效果

✅ 避免與 Odoo 工作流狀態字段衝突
✅ 語義更清楚（實體狀態 vs 工作流狀態）
✅ 所有功能正常運作
✅ 前端顯示正確
✅ WebSocket 實時更新正常

## 📞 支援

如有問題，請檢查：
1. 數據庫日誌：`docker compose logs db`
2. Odoo 日誌：`docker compose logs web`
3. 瀏覽器控制台是否有 JavaScript 錯誤
