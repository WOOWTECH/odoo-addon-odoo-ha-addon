# ha.entity 只讀權限修改

**修改日期**: 2025-11-13
**修改原因**: ha.entity 數據從 Home Assistant 自動同步，禁止手動修改以保持數據一致性
**影響範圍**: 所有用戶（包括 Manager）對 ha.entity 的訪問權限

---

## 修改摘要

### 問題背景

`ha.entity` 模型的數據是從 Home Assistant 透過 WebSocket 服務自動同步的，用戶不應該手動創建、更新或刪除這些數據，否則會導致：

1. **數據不一致**: 手動修改的數據會被下次同步覆蓋
2. **同步錯誤**: 可能導致 WebSocket 服務無法正確更新狀態
3. **數據完整性問題**: 破壞 HA 與 Odoo 之間的數據映射關係

### 修改目標

✅ 所有用戶（普通用戶 + Manager）只能**讀取** ha.entity 數據
✅ 只有**系統**（base.group_system）可以執行 CUD 操作
✅ WebSocket 服務以系統權限運行，確保數據同步正常

---

## 修改內容

### 1. security/security.xml

#### 修改前

```xml
<!-- 規則 4: Manager 可以看到所有實體 -->
<record id="ha_entity_manager_rule" model="ir.rule">
    <field name="name">HA Entity: Manager Full Access</field>
    <field name="model_id" ref="model_ha_entity"/>
    <field name="domain_force">[(1, '=', 1)]</field>
    <field name="groups" eval="[(4, ref('group_ha_manager'))]"/>
    <!-- ⚠️ 沒有明確限制權限，默認繼承 ir.model.access 的全權限 -->
</record>
```

#### 修改後

```xml
<!-- ========================================
     記錄規則: 實體數據訪問控制
     ========================================
     實體數據從 Home Assistant 同步而來，所有用戶只能讀取，
     只有系統可以執行 CUD 操作（通過 WebSocket 服務）
-->

<!-- 規則 3: 用戶只能看到有權限實例的實體 -->
<record id="ha_entity_user_rule" model="ir.rule">
    <field name="name">HA Entity: User Access (Read-Only)</field>
    <field name="model_id" ref="model_ha_entity"/>
    <field name="domain_force">[
        '|',
            ('ha_instance_id.user_ids', '=', False),
            ('ha_instance_id.user_ids', 'in', [user.id])
    ]</field>
    <field name="groups" eval="[(4, ref('base.group_user'))]"/>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="False"/>
    <field name="perm_create" eval="False"/>
    <field name="perm_unlink" eval="False"/>
</record>

<!-- 規則 4: Manager 可以看到所有實體（但只能讀取） -->
<record id="ha_entity_manager_rule" model="ir.rule">
    <field name="name">HA Entity: Manager Access (Read-Only)</field>
    <field name="model_id" ref="model_ha_entity"/>
    <field name="domain_force">[(1, '=', 1)]</field>
    <field name="groups" eval="[(4, ref('group_ha_manager'))]"/>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="False"/>      <!-- ✅ 明確禁止寫入 -->
    <field name="perm_create" eval="False"/>     <!-- ✅ 明確禁止創建 -->
    <field name="perm_unlink" eval="False"/>     <!-- ✅ 明確禁止刪除 -->
</record>
```

**變更點**:
- ✅ 添加註釋說明數據來源和權限限制
- ✅ 規則 3 (User) 保持不變（已經是只讀）
- ✅ 規則 4 (Manager) 明確設置 `perm_write/create/unlink=False`

---

### 2. security/ir.model.access.csv

#### 修改前

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
...
access_ha_entity_manager,HA Entity (Manager),odoo_ha_addon.model_ha_entity,odoo_ha_addon.group_ha_manager,1,1,1,1
access_ha_entity_user,HA Entity (User Read-Only),odoo_ha_addon.model_ha_entity,base.group_user,1,0,0,0
```

**問題**: Manager 擁有完整 CRUD 權限 (1,1,1,1)

#### 修改後

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
...
access_ha_entity_manager,HA Entity (Manager Read-Only),odoo_ha_addon.model_ha_entity,odoo_ha_addon.group_ha_manager,1,0,0,0
access_ha_entity_user,HA Entity (User Read-Only),odoo_ha_addon.model_ha_entity,base.group_user,1,0,0,0
```

**變更點**:
- ✅ **修改**: `access_ha_entity_manager` - 名稱改為 "Manager Read-Only"，權限改為 (1,0,0,0)
- ✅ **不變**: `access_ha_entity_user` - 保持只讀
- ✅ **移除**: `access_ha_entity_system` - **不需要**，因為 WebSocket 服務使用 admin user (UID=1) 創建記錄，會自動繞過所有 access rules

---

### 3. docs/tech/security-architecture.md

#### 權限矩陣更新

**修改前**:
```markdown
| 模型 | 代碼行數 | 普通用戶 | Manager |
|------|---------|---------|---------|
| **ha.entity** | 60-81 | 讀取 (實例有權限) | 全權限 |
```

**修改後**:
```markdown
| 模型 | 代碼行數 | 普通用戶 | Manager |
|------|---------|---------|---------|
| **ha.entity** ⚠️ | 60-86 | 讀取 (實例有權限) | **只讀** |

**⚠️ 特殊說明**: `ha.entity` 數據由 WebSocket 服務從 Home Assistant 自動同步（使用 admin user UID=1），禁止所有用戶手動修改以保持數據一致性。
```

#### 架構圖更新

添加了詳細的權限架構圖：

```
所有實體 (ha_entity)
⚠️ 特殊規則：實體數據從 Home Assistant 同步而來
   所有用戶只能讀取，CUD 操作由 WebSocket 服務執行（admin user UID=1）

普通用戶規則                    Manager規則
    │                              │
    ▼                              ▼
權限: 只讀                        權限: 只讀 ⚠️
(Read Only)                      (Read Only)
- 只能讀取有權限的實例           - 可以讀取所有實例
- 不可手動修改                   - 不可手動修改

                 WebSocket 服務
                (Admin User UID=1)
                       │
                       ▼
            自動同步 HA 實體數據 (CRUD)
            - 繞過所有 access rules
            - 無需 group 權限
```

#### 實際案例更新

**案例 2: Manager Alice** 添加了第 5 點：

```
5. 嘗試手動修改實體數據
   → ❌ 拒絕 (perm_write/create/unlink = False)
```

#### 安全保證更新

```markdown
- ✅ **數據一致性**:
  - 子模型自動繼承實例權限
  - **ha.entity 數據只能由 WebSocket 服務修改**（admin user），防止手動破壞數據一致性
- ✅ **同步數據保護**: WebSocket 服務以 admin user (UID=1) 運行，自動繞過 access rules，確保數據完整性
```

---

## 權限對比表

| 操作 | 修改前 | 修改後 | 說明 |
|------|--------|--------|------|
| **普通用戶 - 讀取** | ✅ 可以 | ✅ 可以 | 不變 |
| **普通用戶 - 寫入** | ❌ 不可 | ❌ 不可 | 不變 |
| **Manager - 讀取** | ✅ 可以 | ✅ 可以 | 不變 |
| **Manager - 寫入** | ✅ 可以 ⚠️ | ❌ 不可 ✅ | **變更** |
| **Manager - 創建** | ✅ 可以 ⚠️ | ❌ 不可 ✅ | **變更** |
| **Manager - 刪除** | ✅ 可以 ⚠️ | ❌ 不可 ✅ | **變更** |
| **WebSocket 服務** | ✅ 可以 (admin) | ✅ 可以 (admin) | 程式碼操作，繞過 access rules |

---

## 影響分析

### ✅ 正面影響

1. **數據一致性**: 防止用戶手動修改導致的數據不一致
2. **同步穩定性**: WebSocket 服務不會受到手動修改的干擾
3. **權限清晰**: 明確區分"查看權限"和"操作權限"
4. **系統安全**: 只有 WebSocket 服務（admin user）可以修改數據

### ⚠️ 潛在影響

1. **Manager 權限降低**: Manager 不能再手動創建/修改/刪除實體
   - **解決方案**: 這是設計目標，實體數據應該由 HA 管理

2. **緊急修復困難**: 如果 WebSocket 服務失敗，無法手動修正數據
   - **解決方案**:
     - 透過 Python shell 以 `sudo()` 或 admin user 創建/修改數據
     - 重啟 WebSocket 服務讓它重新同步

3. **測試環境**: 測試時無法手動創建測試數據
   - **解決方案**:
     - 透過 Python shell 以 `sudo()` 創建數據
     - 或讓 WebSocket 服務從 HA 同步真實數據

---

## 測試驗證

### 測試 1: 普通用戶嘗試修改實體

```python
# 以普通用戶登入
user = env['res.users'].browse(2)  # 假設 ID=2 是普通用戶
entity = env['ha.entity'].with_user(user).browse(1)

# 嘗試修改
entity.write({'state': 'new_value'})
# 預期結果: ❌ AccessError: 沒有寫入權限
```

### 測試 2: Manager 嘗試修改實體

```python
# 以 Manager 登入
manager = env['res.users'].browse(3)  # 假設 ID=3 是 Manager
manager.groups_id = [(4, env.ref('odoo_ha_addon.group_ha_manager').id)]
entity = env['ha.entity'].with_user(manager).browse(1)

# 嘗試修改
entity.write({'state': 'new_value'})
# 預期結果: ❌ AccessError: 沒有寫入權限
```

### 測試 3: Admin user 可以修改實體（繞過 access rules）

```python
# 以 Admin user (UID=1) 運行
admin = env['res.users'].browse(1)  # Admin 用戶
entity = env['ha.entity'].with_user(admin).browse(1)

# 修改數據
entity.write({'state': 'new_value'})
# 預期結果: ✅ 成功修改（admin user 繞過所有 access rules）
```

### 測試 4: WebSocket 服務可以同步數據（實際使用方式）

```python
# WebSocket 服務以 sudo() 運行
entity = env['ha.entity'].sudo().search([('entity_id', '=', 'sensor.temperature')])
entity.write({
    'state': '22.5',
    'last_updated': fields.Datetime.now()
})
# 預期結果: ✅ 成功同步
```

---

## 部署建議

### 部署前檢查

1. ✅ 確認 WebSocket 服務正常運行
2. ✅ 確認 admin user (UID=1) 可用
3. ✅ 備份數據庫（以防需要回退）

### 部署步驟

```bash
# 1. 重啟 Odoo 服務（加載新權限）
docker compose -f docker-compose-18.yml restart web

# 2. 檢查日誌確認無錯誤
docker compose -f docker-compose-18.yml logs web --tail=50

# 3. （可選）手動觸發權限更新
docker compose -f docker-compose-18.yml exec -e PGHOST=db -e PGUSER=odoo -e PGPASSWORD=odoo web \
  odoo -d odoo -u odoo_ha_addon --stop-after-init
```

### 部署後驗證

1. 登入系統，檢查實體列表是否正常顯示
2. 以 Manager 賬號嘗試編輯實體（應該失敗）
3. 檢查 WebSocket 服務是否正常同步數據（使用 admin user）
4. 驗證 `access_ha_entity_manager` 和 `access_ha_entity_user` 權限為只讀 (1,0,0,0)

---

## 回退計劃

如果需要回退修改：

```bash
# 1. 回退文件
git checkout HEAD~1 -- security/security.xml
git checkout HEAD~1 -- security/ir.model.access.csv
git checkout HEAD~1 -- docs/tech/security-architecture.md

# 2. 重啟服務
docker compose -f docker-compose-18.yml restart web

# 3. 更新模組
docker compose -f docker-compose-18.yml exec web odoo -d odoo -u odoo_ha_addon --stop-after-init
```

---

## 相關文件

- **修改文件**:
  - `security/security.xml` (規則 3-4)
  - `security/ir.model.access.csv` (ha.entity 權限記錄)
  - `docs/tech/security-architecture.md` (文檔更新)

- **相關文檔**:
  - `docs/code-review/comprehensive-review-2025-11-13.md` (P0 代碼審查)
  - `docs/code-review/p0-fixes-verification.md` (P0 修復驗證)
  - `docs/code-review/p0-test-results.md` (P0 測試結果)

---

**修改完成時間**: 2025-11-13 16:00 UTC
**修改人員**: Claude Code
**審核狀態**: ✅ 已完成修改，等待部署驗證
