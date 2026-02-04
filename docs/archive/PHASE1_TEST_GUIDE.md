# Phase 1 測試指南

## 📋 測試前準備

### 1. 檢查當前狀態

```bash
# 進入專案目錄
cd /Users/eugene/Documents/woow/AREA-odoo/odoo-server

# 檢查 Docker 狀態
docker compose ps
```

### 2. 備份資料庫（建議）

```bash
# 進入 PostgreSQL 容器
docker compose exec db bash

# 備份資料庫
pg_dump -U odoo odoo > /tmp/odoo_backup_before_phase1.sql

# 退出容器
exit

# 將備份複製到本機（可選）
docker compose cp db:/tmp/odoo_backup_before_phase1.sql ./backup/
```

---

## 🚀 執行升級（遷移腳本會自動執行）

### 步驟 1: 重啟 Odoo 並升級 addon

```bash
cd /Users/eugene/Documents/woow/AREA-odoo/odoo-server

# 方法 A: 使用 restart + exec（推薦）
docker compose restart web
docker compose exec web odoo -d odoo -u odoo_ha_addon --dev xml --log-handler odoo.tools.convert:DEBUG
```

**預期輸出**：
```
INFO odoo.modules.loading: loading 1 modules...
INFO odoo.modules.loading: 1 modules loaded in 0.02s, 0 queries
INFO odoo.modules.migration: module odoo_ha_addon: Running migration 18.0.3.0
INFO pre-migrate: ================================================================================
INFO pre-migrate: Starting Multi-HA Instance Migration (18.0.3.0)
INFO pre-migrate: ================================================================================
INFO pre-migrate: Reading existing HA configuration...
INFO pre-migrate: Found config - URL: http://xxx:8123, Token: ***
INFO pre-migrate: Creating default HA instance...
INFO pre-migrate: Created default HA instance with ID: 1
INFO pre-migrate: Migrating existing data to default instance...
INFO pre-migrate: Migrated X areas
INFO pre-migrate: Migrated X entities
INFO pre-migrate: ================================================================================
INFO pre-migrate: Multi-HA Instance Migration completed successfully!
INFO pre-migrate: ================================================================================
```

### 步驟 2: 監控日誌（另開一個終端）

```bash
# 在另一個終端視窗執行
cd /Users/eugene/Documents/woow/AREA-odoo/odoo-server
docker compose logs -f web
```

**尋找這些關鍵日誌**：
- ✅ `Starting Multi-HA Instance Migration`
- ✅ `Created default HA instance with ID: X`
- ✅ `Migrated X entities`
- ✅ `Migration completed successfully`

---

## ✅ 驗證清單

### 1. 後端驗證（透過 Odoo Shell）

```bash
# 進入 Odoo Shell
docker compose exec web odoo shell -d odoo
```

在 Shell 中執行：

```python
# 1. 檢查 ha.instance 模型是否存在
env['ha.instance']
# 預期: <class 'odoo.addons.odoo_ha_addon.models.ha_instance.HAInstance'>

# 2. 查詢第一個實例 (⚠️ 架構更新：已移除 is_default 欄位)
first_instance = env['ha.instance'].get_accessible_instances()[:1]
if first_instance:
    print(f"First Instance: {first_instance.name} (ID: {first_instance.id})")
    print(f"API URL: {first_instance.api_url}")
    print(f"Active: {first_instance.active}")
else:
    print("No accessible instance found")

# 3. 檢查 entities 是否正確關聯
entity_count = env['ha.entity'].search_count([('ha_instance_id', '=', first_instance.id)])
print(f"Entities linked to first instance: {entity_count}")

# 4. 檢查 areas 是否正確關聯
area_count = env['ha.area'].search_count([('ha_instance_id', '=', first_instance.id)])
print(f"Areas linked to first instance: {area_count}")

# 5. 檢查 history 記錄（透過 related field）
history_count = env['ha.entity.history'].search_count([('ha_instance_id', '=', first_instance.id)])
print(f"History records linked to first instance: {history_count}")

# 6. 測試權限方法
accessible = env['ha.instance'].get_accessible_instances()
print(f"Accessible instances: {accessible.mapped('name')}")

# 離開 Shell
exit()
```

**預期結果**：
```
First Instance: Default HA (ID: 1)
API URL: http://homeassistant.local:8123
Active: True
Entities linked to first instance: 500
Areas linked to first instance: 10
History records linked to first instance: 5000
Accessible instances: ['Default HA']
```

> ⚠️ **架構更新 (2025-11-25)**: 已移除 `is_default` 欄位，改用 `get_accessible_instances()` 權限感知查詢

### 2. 前端驗證（透過瀏覽器）

#### Step 1: 登入 Odoo
```
URL: http://localhost:8069
帳號: admin
密碼: admin
```

#### Step 2: 檢查選單

導航到：**Settings > Configuration > HA Instances**

**驗證項目**：
- [ ] 選單項目是否出現
- [ ] 是否顯示 "Default HA" 實例
- [ ] Tree view 是否正常顯示

#### Step 3: 檢查 Form View

點擊 "Default HA" 進入詳細頁面：

**驗證項目**：
- [ ] ~~是否顯示 "Default" 徽章（ribbon）~~ (⚠️ 已移除 `is_default` 欄位)
- [ ] API URL 欄位是否正確
- [ ] WebSocket URL 是否自動計算
- [ ] 是否顯示 "Test Connection" 按鈕
- [ ] 是否顯示 "Sync Entities" 按鈕
- [ ] Entity Count 統計按鈕是否顯示正確數字

#### Step 4: 測試 Test Connection 按鈕

點擊 "Test Connection" 按鈕：

**預期結果**：
- ✅ 如果 HA 可連接：顯示綠色通知 "Connection Successful"
- ❌ 如果 HA 無法連接：顯示紅色通知 "Connection Failed"

#### Step 5: 檢查 Entity 關聯

導航到：**Home Assistant > Entities**

**驗證項目**：
- [ ] 所有 entities 是否仍然存在
- [ ] Entity 的詳細頁面是否顯示 "HA Instance" 欄位
- [ ] HA Instance 欄位是否指向 "Default HA"

#### Step 6: 測試新增實例

回到 **Settings > Configuration > HA Instances**，點擊 "Create"：

**測試輸入**：
- Name: Test HA
- API URL: http://test.local:8123
- Access Token: test_token_12345

**驗證項目**：
- [ ] 是否可以成功創建
- [ ] Sequence 欄位是否可拖曳排序
- [ ] WebSocket URL 是否自動計算為 `ws://test.local:8123/api/websocket`
- [ ] 可以設定 "Allowed Users"
- [ ] 可以切換 "Active" 狀態

#### Step 7: 測試複合唯一約束

嘗試在同一實例下創建重複的 entity：

**透過 Odoo Shell 測試**：
```python
docker compose exec web odoo shell -d odoo
```

```python
# 獲取第一個可存取實例 (⚠️ 架構更新：已移除 is_default 欄位)
instance = env['ha.instance'].get_accessible_instances()[:1]

# 嘗試創建重複的 entity（應該失敗）
try:
    env['ha.entity'].create({
        'ha_instance_id': instance.id,
        'entity_id': 'sensor.test_duplicate',
        'domain': 'sensor',
        'name': 'Test Duplicate 1'
    })

    # 嘗試創建相同的 entity_id（應該失敗）
    env['ha.entity'].create({
        'ha_instance_id': instance.id,
        'entity_id': 'sensor.test_duplicate',  # 相同
        'domain': 'sensor',
        'name': 'Test Duplicate 2'
    })
    print("ERROR: Should have failed!")
except Exception as e:
    print(f"✅ Constraint working: {e}")

exit()
```

**預期結果**：
```
✅ Constraint working: duplicate key value violates unique constraint "ha_entity_entity_instance_unique"
```

---

## 🔍 常見問題排查

### 問題 1: 遷移腳本沒有執行

**症狀**：
- 日誌中沒有看到 "Starting Multi-HA Instance Migration"
- `ha.instance` 表是空的

**原因**：
- `__manifest__.py` 的 version 沒有更新到 `18.0.3.0`

**解決方法**：
```bash
# 檢查版本
grep "version" /Users/eugene/Documents/woow/AREA-odoo/odoo-server/data/18/addons/odoo_ha_addon/__manifest__.py

# 如果不是 18.0.3.0，手動更新
# 'version': '18.0.3.0',

# 然後重新升級
docker compose restart web
docker compose exec web odoo -d odoo -u odoo_ha_addon
```

### 問題 2: 找不到 HA Instances 選單

**症狀**：
- Settings 下沒有 "HA Instances" 選項

**原因**：
- 可能是快取問題或權限問題

**解決方法**：
```bash
# 1. 強制刷新瀏覽器（Ctrl+Shift+R 或 Cmd+Shift+R）

# 2. 清除 Odoo 快取並重啟
docker compose exec web odoo -d odoo --dev xml

# 3. 檢查使用者是否有權限（在 Odoo Shell）
docker compose exec web odoo shell -d odoo
```

```python
# 檢查選單
menu = env['ir.ui.menu'].search([('name', '=', 'HA Instances')])
print(f"Menu found: {menu.name if menu else 'NOT FOUND'}")

# 檢查使用者權限
user = env.user
print(f"User: {user.name}")
print(f"Groups: {user.groups_id.mapped('name')}")

exit()
```

### 問題 3: Test Connection 按鈕無反應

**症狀**：
- 點擊 "Test Connection" 按鈕後沒有通知

**原因**：
- JavaScript 錯誤或 API 路徑問題

**解決方法**：
```bash
# 1. 檢查瀏覽器控制台（F12）看是否有 JavaScript 錯誤

# 2. 檢查 API 是否正常
curl http://localhost:8069/web/webclient/version_info

# 3. 在 Odoo Shell 手動測試
docker compose exec web odoo shell -d odoo
```

```python
# ⚠️ 架構更新 (2025-11-25): 已移除 is_default 欄位
instance = env['ha.instance'].get_accessible_instances()[:1]
if instance:
    result = instance.test_connection()
    print(result)
exit()
```

### 問題 4: Entity 沒有關聯到實例

**症狀**：
- Entity 的 `ha_instance_id` 欄位是空的

**原因**：
- 遷移腳本可能執行失敗或被跳過

**解決方法**：
```bash
# 在 Odoo Shell 手動執行遷移邏輯
docker compose exec web odoo shell -d odoo
```

```python
# 1. 檢查第一個可存取實例 (⚠️ 架構更新：已移除 is_default 欄位)
first_instance = env['ha.instance'].get_accessible_instances()[:1]
print(f"First instance: {first_instance.name if first_instance else 'NOT FOUND'}")

# 2. 檢查未關聯的 entities
orphans = env['ha.entity'].search([('ha_instance_id', '=', False)])
print(f"Orphaned entities: {len(orphans)}")

# 3. 如果有未關聯的 entities，手動關聯
if orphans and first_instance:
    orphans.write({'ha_instance_id': first_instance.id})
    print(f"✅ Linked {len(orphans)} entities to {first_instance.name}")

exit()
```

---

## 📊 測試完成檢查表

請確認所有項目都已勾選：

### 後端驗證
- [ ] 遷移腳本成功執行（日誌顯示成功）
- [ ] 第一個實例已創建（Default HA）
- [ ] 所有 entities 已關聯到第一個實例
- [ ] 所有 areas 已關聯到第一個實例
- [ ] History 記錄自動繼承實例關聯
- [ ] `get_accessible_instances()` 方法正常運作

> ⚠️ **架構更新 (2025-11-25)**: 已移除 `is_default` 欄位，改用權限感知的實例選擇

### 前端驗證
- [ ] HA Instances 選單出現在 Settings
- [ ] Tree view 正常顯示實例列表
- [ ] Form view 完整顯示所有欄位
- [ ] "Test Connection" 按鈕正常運作
- [ ] "Sync Entities" 按鈕出現（即使功能未完成）
- [ ] Entity Count 統計正確
- [ ] 可以新增/編輯/刪除實例
- [ ] Allowed Users 權限設定正常

### 數據完整性驗證
- [ ] 複合唯一約束正常運作
- [ ] ~~預設實例約束正常（只能有一個預設實例）~~ (⚠️ 已移除 `is_default` 欄位)
- [ ] Entity 與 History 的關聯正確
- [ ] 刪除實例時有正確的警告訊息

### 回歸測試
- [ ] 現有 Dashboard 功能正常
- [ ] Entity 列表頁面正常
- [ ] History 記錄顯示正常
- [ ] 沒有 JavaScript 錯誤

---

## 🎉 測試成功標準

如果以上**所有項目都通過**，則 Phase 1 測試成功，可以進入 Phase 2！

---

## 📝 測試結果記錄

請在測試後填寫：

**測試日期**: ___________
**測試者**: ___________
**Odoo 版本**: 18.0
**模組版本**: 18.0.3.0

**測試結果**：
- [ ] ✅ 全部通過
- [ ] ⚠️ 部分通過（請記錄問題）
- [ ] ❌ 測試失敗（請記錄錯誤）

**問題記錄**：
```
（如有問題，請在此記錄）
```

**備註**：
```
（其他觀察或建議）
```

---

**最後更新**: 2025-10-31 12:30
**整理者**: Claude Code
