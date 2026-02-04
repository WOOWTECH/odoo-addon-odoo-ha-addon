# 權限架構遷移指南：Instance-based → Group-based + 兩層權限組

**遷移日期**: 2025-11-16 (Group-based), 2025-11-17 (兩層權限組)
**影響範圍**: 所有使用 odoo_ha_addon 的系統
**遷移複雜度**: 中等（需要數據庫遷移 + 測試）

## ⚠️ 最新變更 (2025-11-17)

在 Group-based 權限架構之上，新增**兩層權限組設計**：

- ✅ 創建專屬 `group_ha_user` 遵循 Point of Sale 模組模式
- ✅ 實施最小權限原則：用戶需明確授權才能訪問 HA 功能
- ✅ 支持 Portal 用戶：`group_ha_user` 不包含 `implied_ids`
- ✅ 簡化訪問控制：`ir.model.access.csv` 從 19 行精簡至 12 行

**影響**：現有 Internal User 和 Portal 用戶需要**明確添加** `group_ha_user` 權限才能繼續訪問 HA 功能。

## 概述

本次遷移包含兩個階段的架構重構：

### 階段 1: Group-based 權限 (2025-11-16)
將權限控制從**實例級別**改為**分組級別**，實現更細粒度的權限控制並符合資料庫正規化。

### 階段 2: 兩層權限組 (2025-11-17)
創建專屬 HA 權限組，遵循 Odoo 標準模組模式（如 Point of Sale），不再自動綁定到 `base.group_user`/`base.group_portal`。

### 架構變更對比

| 項目 | 舊架構 (Instance-based) | 中期架構 (Group-based) | **最新架構 (Two-Tier Groups)** |
|------|------------------------|---------------------|----------------------------|
| 權限組 | base.group_user (自動) | base.group_user (自動) | **group_ha_user (明確授權)** |
| 權限核心 | ha.instance.user_ids | ha.entity.group.user_ids | ha.entity.group.user_ids |
| 權限路徑 | User → Instance → Entity | User → Group → Entity | **User → HA Group → Entity Group → Entity** |
| 粒度 | 實例級別（粗） | 分組級別（細） | 分組級別（細） |
| 正規化 | ❌ 有冗餘關聯 | ✅ 符合 3NF | ✅ 符合 3NF |
| 使用場景 | 多租戶隔離 | 同實例內分組共享 | 同實例內分組共享 |
| Portal 用戶 | ❌ 自動可訪問 | ❌ 自動可訪問 | **✅ 需明確授權** |

### 關鍵變更

#### 階段 1: Group-based 權限 (2025-11-16)

1. **新增欄位**:
   - `ha.entity.group.user_ids` (Many2many to res.users)
   - `res.users.ha_entity_group_ids` (反向關聯)

2. **權限規則**:
   - 從 10 條規則 → 12 條規則
   - 全部改為基於 `user.ha_entity_group_ids` 的訪問控制

3. **ha.instance.user_ids**:
   - 舊架構：控制用戶訪問實例及其所有數據
   - 新架構：可選保留（只給 Manager 用），或完全移除

#### 階段 2: 兩層權限組 (2025-11-17)

1. **新增權限組**:
   - `group_ha_user`: 基礎 HA 訪問權限（不包含 implied_ids）
   - `group_ha_manager`: 完整管理權限（implied_ids: base.group_user + group_ha_user）

2. **權限規則更新**:
   - 12 條 `ir.rule` 全部從 `base.group_user` 改綁 `group_ha_user`
   - Manager 規則維持綁定 `group_ha_manager`

3. **訪問控制簡化**:
   - `ir.model.access.csv` 從 19 行精簡至 12 行
   - 移除 7 條 Portal 專屬訪問記錄（統一使用 `group_ha_user`）

4. **用戶授權變更**:
   - ⚠️ **Breaking Change**: 所有用戶需明確添加 `group_ha_user` 才能訪問 HA 功能
   - Internal User: 添加 `group_ha_user`
   - Portal User: 添加 `group_ha_user`（允許查看儀表板）
   - Manager: 添加 `group_ha_manager`（自動包含 `group_ha_user`）

5. **移除冗餘欄位** (2025-11-17):
   - ❌ **完全移除** `ha.instance.user_ids` 欄位及關聯表 `ha_instance_user_rel`
   - ❌ **移除** Settings 界面中的 `ha_user_ids` 欄位和 "Access Control" 區塊
   - ✅ 權限控制完全由 `ha.entity.group.user_ids` 負責（單一來源）

## 遷移前準備

### 1. 備份數據庫

```bash
# 備份當前數據庫
docker compose exec -e PGHOST=db -e PGUSER=odoo -e PGPASSWORD=odoo web \
  pg_dump -d odoo > odoo_backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. 檢查當前數據

```python
# 在 Odoo shell 中執行
env = self.env

# 檢查有多少實例有用戶授權
instances_with_users = env['ha.instance'].search([('user_ids', '!=', False)])
print(f"有用戶授權的實例: {len(instances_with_users)}")

# 檢查有多少用戶被授權訪問實例
users_with_instances = env['res.users'].search([
    ('id', 'in', instances_with_users.mapped('user_ids').ids)
])
print(f"被授權的用戶: {len(users_with_instances)}")

# 檢查有多少 entity groups
groups = env['ha.entity.group'].search([])
print(f"現有 Entity Groups: {len(groups)}")
```

### 3. 記錄當前權限設置

```python
# 導出當前權限映射
import json

permission_map = {}
for instance in instances_with_users:
    permission_map[instance.id] = {
        'name': instance.name,
        'users': instance.user_ids.mapped('login'),
        'entities_count': len(instance.entity_ids)
    }

# 保存到文件
with open('/tmp/permission_map.json', 'w') as f:
    json.dump(permission_map, f, indent=2)

print("權限映射已保存到 /tmp/permission_map.json")
```

## 遷移步驟

### 步驟 1: 更新模組代碼

```bash
cd /Users/eugene/Documents/woow/AREA-odoo/odoo-server/data/18/addons/odoo_ha_addon

# 1. 確認所有修改已完成
git status

# 2. 查看變更
git diff

# 應該看到以下變更：
# - models/ha_entity_group.py (新增 user_ids)
# - models/res_users.py (新增 ha_entity_group_ids)
# - security/security.xml (重寫 12 條規則)
```

### 步驟 2: 升級模組（會自動創建新欄位）

```bash
# 重啟 Odoo 並升級模組
docker compose restart web

# 升級模組
docker compose exec -e PGHOST=db -e PGUSER=odoo -e PGPASSWORD=odoo web \
  odoo -d odoo -u odoo_ha_addon --stop-after-init

# 檢查日誌確認沒有錯誤
docker compose logs web --tail=100 | grep -i error
```

### 步驟 3: 執行數據遷移腳本

**方案 A: 為每個實例創建對應的 Entity Group（推薦）**

```python
# 在 Odoo shell 中執行
# docker compose exec web odoo shell -d odoo

env = self.env

# 1. 獲取所有有用戶授權的實例
instances_with_users = env['ha.instance'].search([('user_ids', '!=', False)])

print(f"開始遷移 {len(instances_with_users)} 個實例的權限...")

# 2. 為每個實例創建一個 "全部設備" group
for instance in instances_with_users:
    # 創建 group
    group = env['ha.entity.group'].create({
        'name': f'{instance.name} - 全部設備',
        'description': f'自動遷移：包含 {instance.name} 的所有實體',
        'ha_instance_id': instance.id,
        'user_ids': [(6, 0, instance.user_ids.ids)],  # 複製用戶授權
        'entity_ids': [(6, 0, instance.entity_ids.ids)],  # 包含所有實體
        'sequence': 1,
    })

    print(f"✓ 創建 Group: {group.name}")
    print(f"  - 授權用戶: {', '.join(instance.user_ids.mapped('login'))}")
    print(f"  - 包含實體: {len(group.entity_ids)} 個")

env.cr.commit()
print("✅ 遷移完成！")
```

**方案 B: 按 domain 創建 Groups（更細粒度）**

```python
# 在 Odoo shell 中執行
env = self.env

instances_with_users = env['ha.instance'].search([('user_ids', '!=', False)])

for instance in instances_with_users:
    # 按 domain 分組實體
    domains = instance.entity_ids.mapped('domain')
    unique_domains = list(set(domains))

    print(f"\n實例: {instance.name}")
    print(f"發現 {len(unique_domains)} 個 domains")

    for domain in unique_domains:
        entities = instance.entity_ids.filtered(lambda e: e.domain == domain)

        # 創建對應的 group
        group = env['ha.entity.group'].create({
            'name': f'{instance.name} - {domain.title()}',
            'description': f'{domain} 類型的設備',
            'ha_instance_id': instance.id,
            'user_ids': [(6, 0, instance.user_ids.ids)],
            'entity_ids': [(6, 0, entities.ids)],
            'sequence': 10,
        })

        print(f"  ✓ 創建 Group: {group.name} ({len(entities)} 個實體)")

env.cr.commit()
print("\n✅ 按 domain 遷移完成！")
```

### 步驟 4: 驗證遷移結果

```python
# 在 Odoo shell 中執行
env = self.env

# 1. 檢查所有 groups 是否都有正確的用戶授權
groups = env['ha.entity.group'].search([('user_ids', '!=', False)])
print(f"✓ 有用戶授權的 Groups: {len(groups)}")

# 2. 驗證用戶可以訪問的實體數量
for user in env['res.users'].search([('ha_entity_group_ids', '!=', False)]):
    accessible_entities = user.ha_entity_group_ids.mapped('entity_ids')
    print(f"用戶 {user.login}: 可訪問 {len(accessible_entities)} 個實體")

# 3. 檢查是否有實體沒有被任何 group 包含
all_entities = env['ha.entity'].search([])
grouped_entities = env['ha.entity.group'].search([]).mapped('entity_ids')
ungrouped = all_entities - grouped_entities
if ungrouped:
    print(f"⚠️ 警告: {len(ungrouped)} 個實體沒有被任何 group 包含")
else:
    print("✓ 所有實體都已加入 groups")
```

### 步驟 5: 授予用戶 HA 權限組 (⚠️ 2025-11-17 新增)

**重要**: 從 2025-11-17 開始，用戶需要明確添加 `group_ha_user` 才能訪問 HA 功能。

```python
# 在 Odoo shell 中執行
env = self.env

# 1. 獲取 HA User 群組
ha_user_group = env.ref('odoo_ha_addon.group_ha_user')

# 2. 方案 A: 為所有 Internal User 添加 HA User 權限（謹慎使用！）
internal_users = env['res.users'].search([
    ('groups_id', 'in', [env.ref('base.group_user').id]),
    ('id', '!=', 1)  # 排除 admin
])
print(f"找到 {len(internal_users)} 個 Internal Users")

# 為每個用戶添加 group_ha_user
for user in internal_users:
    user.write({'groups_id': [(4, ha_user_group.id)]})
    print(f"  ✓ {user.login} 已添加 HA User 權限")

# 3. 方案 B: 只為有權限訪問 entity groups 的用戶添加（推薦）
users_with_groups = env['res.users'].search([
    ('ha_entity_group_ids', '!=', False)
])
print(f"\n找到 {len(users_with_groups)} 個有 Entity Groups 授權的用戶")

for user in users_with_groups:
    # 檢查是否已有 HA User 權限
    if ha_user_group not in user.groups_id:
        user.write({'groups_id': [(4, ha_user_group.id)]})
        print(f"  ✓ {user.login} 已添加 HA User 權限")
    else:
        print(f"  ℹ️ {user.login} 已有 HA User 權限")

# 4. 為 Portal 用戶添加權限（如果需要）
portal_users = env['res.users'].search([
    ('groups_id', 'in', [env.ref('base.group_portal').id]),
    ('ha_entity_group_ids', '!=', False)  # 只給有授權 groups 的 Portal 用戶
])
print(f"\n找到 {len(portal_users)} 個有 Entity Groups 授權的 Portal Users")

for user in portal_users:
    if ha_user_group not in user.groups_id:
        user.write({'groups_id': [(4, ha_user_group.id)]})
        print(f"  ✓ {user.login} 已添加 HA User 權限")

env.cr.commit()
print("\n✅ 用戶權限授予完成！")
```

**驗證授權結果**:

```python
# 檢查有 HA User 權限的用戶
ha_users = env['res.users'].search([
    ('groups_id', 'in', [ha_user_group.id])
])
print(f"\n總共 {len(ha_users)} 個用戶擁有 HA User 權限:")
for user in ha_users:
    user_type = "Portal" if env.ref('base.group_portal') in user.groups_id else "Internal"
    is_manager = "Manager" if env.ref('odoo_ha_addon.group_ha_manager') in user.groups_id else "User"
    print(f"  - {user.login} ({user_type}, {is_manager})")
```

### 步驟 6: 測試權限

```python
# 在 Odoo shell 中執行
env = self.env

# 1. 獲取一個普通用戶
user = env['res.users'].search([
    ('groups_id', 'not in', [env.ref('odoo_ha_addon.group_ha_manager').id])
], limit=1)

if not user:
    print("沒有找到普通用戶，跳過測試")
else:
    print(f"\n測試用戶: {user.login}")

    # 2. 測試 entity 訪問
    entities = env['ha.entity'].with_user(user).search([])
    expected_entities = user.ha_entity_group_ids.mapped('entity_ids')

    if set(entities.ids) == set(expected_entities.ids):
        print(f"✅ Entity 權限正確: 可訪問 {len(entities)} 個實體")
    else:
        print(f"❌ Entity 權限錯誤!")
        print(f"   實際: {len(entities)} 個")
        print(f"   預期: {len(expected_entities)} 個")

    # 3. 測試 instance 訪問
    instances = env['ha.instance'].with_user(user).search([])
    expected_instances = user.ha_entity_group_ids.mapped('ha_instance_id')

    if set(instances.ids) == set(expected_instances.ids):
        print(f"✅ Instance 權限正確: 可訪問 {len(instances)} 個實例")
    else:
        print(f"❌ Instance 權限錯誤!")

    # 4. 測試寫入權限（應該被拒絕）
    try:
        entities[0].with_user(user).write({'state': 'test'})
        print("❌ 警告: 用戶不應該能修改 entity！")
    except Exception as e:
        print(f"✅ Entity 寫入權限正確: 被拒絕 ({type(e).__name__})")
```

## 遷移後清理

### ✅ ha.instance.user_ids 已完全移除 (2025-11-17)

**從 v2.0 開始，`ha.instance.user_ids` 欄位已被完全移除**：

- ❌ `models/ha_instance.py` 中的 `user_ids` 欄位定義已刪除
- ❌ `models/res_config_settings.py` 中的 `ha_user_ids` related 欄位已刪除
- ❌ Settings 界面的 "Access Control" 區塊已移除
- ❌ 數據庫中的 `ha_instance_user_rel` 關聯表會在升級模組時自動清理

**理由**：
1. ✅ 消除冗餘，避免混淆（只有一個權限控制點）
2. ✅ 符合 DRY 原則
3. ✅ 強制使用新的 Entity Group 權限系統

**升級後自動清理**：
當您升級模組時，Odoo 會自動：
- 刪除 `ha_instance` 表中的 `user_ids` 欄位
- 刪除 `ha_instance_user_rel` 關聯表
- 刪除相關索引和約束

**無需手動操作** - 模組升級會自動處理所有清理工作

## 回退計劃

如果遷移後發現問題，需要回退：

### 回退步驟

```bash
# 1. 恢復數據庫備份
docker compose exec -e PGHOST=db -e PGUSER=odoo -e PGPASSWORD=odoo web \
  psql -d odoo < odoo_backup_YYYYMMDD_HHMMSS.sql

# 2. 回退代碼
cd /Users/eugene/Documents/woow/AREA-odoo/odoo-server/data/18/addons/odoo_ha_addon
git checkout HEAD~1 -- models/ha_entity_group.py
git checkout HEAD~1 -- models/res_users.py
git checkout HEAD~1 -- security/security.xml

# 3. 重啟服務
docker compose restart web

# 4. 降級模組
docker compose exec web odoo -d odoo -u odoo_ha_addon --stop-after-init
```

## 常見問題 (FAQ)

### Q1: 遷移會影響現有數據嗎？

**A**: 不會。遷移只是創建新的 entity groups 並授權用戶，不會修改或刪除任何 entities、instances 或用戶數據。

### Q2: 用戶會失去訪問權限嗎？

**A**: 不會。遷移腳本會自動為每個實例創建 groups 並複製用戶授權，確保用戶可以訪問和之前一樣的數據。

### Q3: 可以手動授權用戶到 groups 嗎？

**A**: 可以！遷移完成後，Manager 可以：
- 創建新的 entity groups
- 修改 group 的 user_ids 來授權用戶
- 調整 group 的 entity_ids 來控制包含的實體

### Q4: 公開 groups 如何設置？

**A**: 將 group 的 `user_ids` 設為空（False 或 []），所有用戶都可以看到。

```python
group.write({'user_ids': [(5, 0, 0)]})  # 清空，變成公開
```

### Q5: 如何批量授權多個用戶？

**A**:
```python
group.write({
    'user_ids': [(6, 0, [user1.id, user2.id, user3.id])]
})
```

### Q6: 遷移需要停機嗎？

**A**: 不需要完全停機，但建議：
1. 選擇低峰時段執行
2. 提前通知用戶可能有短暫不穩定
3. 準備好回退計劃

### Q7: Manager 權限有變化嗎？

**A**: 沒有。Manager 仍然可以：
- 看到所有實例、groups、entities
- 管理實例和 groups
- 授權用戶訪問 groups
- **唯一限制**: 不能手動修改 entities（由 WebSocket 服務同步）

## 遷移檢查清單

執行遷移前，請確認以下項目：

- [ ] 已備份數據庫
- [ ] 已記錄當前權限設置
- [ ] 已測試在開發環境
- [ ] 已通知相關用戶
- [ ] 已準備回退計劃
- [ ] 已更新所有代碼
- [ ] 已升級模組
- [ ] 已執行遷移腳本
- [ ] 已驗證權限正確性
- [ ] 已測試普通用戶訪問
- [ ] 已測試 Manager 訪問
- [ ] 已檢查 WebSocket 服務正常
- [ ] 已更新相關文檔

## 支援與協助

如果遷移過程中遇到問題：

1. **檢查日誌**: `docker compose logs web --tail=200`
2. **查看錯誤**: 在 Odoo 界面檢查 Settings > Technical > Database Structure > Models
3. **執行測試**: 使用本文檔的驗證腳本
4. **回退系統**: 使用回退計劃恢復到舊版本

## 參考文檔

- **新架構說明**: `docs/tech/security-architecture.md`
- **權限規則**: `security/security.xml`
- **模型定義**: `models/ha_entity_group.py`, `models/res_users.py`

---

**文檔版本**: 2.0
**最後更新**: 2025-11-17 (新增兩層權限組設計)
**適用版本**: odoo_ha_addon v18.0

**變更記錄**:
- v2.0 (2025-11-17): 新增步驟 5 - 授予用戶 HA 權限組，更新架構對比表
- v1.0 (2025-11-16): 初版 - Instance-based → Group-based 遷移
