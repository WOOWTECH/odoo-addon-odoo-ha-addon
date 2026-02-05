# PRD: Device Tag 功能與選單重組

## 概述

### 目標
1. 將 Entity Tag 和 Entity Group Tag 從 Model 選單移至 Configuration 選單
2. 新增 Device Tag 功能，實作邏輯與 Entity Tag 相同
3. 在 Device 表單中新增 tag_ids 欄位

### 背景
目前 Entity Tag 和 Entity Group Tag 被放在 Model 選單下，但它們本質上是配置資料（用於分類管理），應該放在 Configuration 選單下。同時，Device 模型缺少 Tag 功能，需要補齊。

---

## 實作狀態

| Phase | 說明 | 狀態 | 檔案 |
|-------|------|------|------|
| 1 | 選單重組 | ✅ 完成 | `src/views/dashboard_menu.xml` |
| 2 | Device Tag 模型 | ✅ 完成 | `src/models/ha_device_tag.py` |
| 3 | Device Tag 視圖 | ✅ 完成 | `src/views/ha_device_tag_views.xml` |
| 4 | Device 模型更新 | ✅ 完成 | `src/models/ha_device.py` |
| 5 | Device 視圖更新 | ✅ 完成 | `src/views/ha_device_views.xml` |
| 6 | 選單項目新增 | ✅ 完成 | `src/views/dashboard_menu.xml` |
| 7 | 模組註冊 | ✅ 完成 | `src/models/__init__.py` |
| 8 | 權限設定 | ✅ 完成 | `src/security/ir.model.access.csv` |

### 已發現並修復的問題

| 問題 | 檔案 | 修復 |
|------|------|------|
| `custom_name` 欄位名稱錯誤 | `ha_device_tag_views.xml:67` | 改為 `name_by_user` |

---

## 變更範圍

### 1. 選單重組

**現狀**：
```
WOOW Dashboard
├── Dashboard
├── Model
│   ├── Area
│   ├── Device
│   ├── Label
│   ├── Entity
│   ├── History
│   ├── Entity Group
│   ├── Entity Group Tag  ← 需移動
│   └── Entity Tag        ← 需移動
└── Configuration
    ├── HA Instances
    └── Setting
```

**目標**：
```
WOOW Dashboard
├── Dashboard
├── Model
│   ├── Area
│   ├── Device
│   ├── Label
│   ├── Entity
│   ├── History
│   └── Entity Group
└── Configuration
    ├── HA Instances
    ├── Entity Tag        ← 移到這裡
    ├── Entity Group Tag  ← 移到這裡
    ├── Device Tag        ← 新增
    └── Setting
```

### 2. 新增 Device Tag 模型

**模型名稱**：`ha.device.tag`

**欄位定義**（參照 ha.entity.tag）：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `ha_instance_id` | Many2one | 關聯 HA Instance（必填） |
| `name` | Char | 標籤名稱（必填） |
| `color` | Integer | 顏色索引（預設 0） |
| `description` | Text | 描述 |
| `sequence` | Integer | 排序（預設 10） |
| `active` | Boolean | 啟用狀態（預設 True） |
| `device_ids` | Many2many | 關聯的 Device 列表 |
| `device_count` | Integer | Device 數量（計算欄位） |

**關聯表**：`ha_device_tag_rel`
- `device_id` → ha.device
- `tag_id` → ha.device.tag

### 3. 更新 Device 模型

**新增欄位**：

```python
# 在 ha_device.py 新增
tag_ids = fields.Many2many(
    'ha.device.tag',
    'ha_device_tag_rel',
    'device_id',
    'tag_id',
    string='Tags',
    domain="[('ha_instance_id', '=', ha_instance_id)]",
    help='Tags for this device (Odoo-only, not synced with HA)'
)

tag_count = fields.Integer(
    string='Tag Count',
    compute='_compute_tag_count',
    store=True
)
```

**新增方法**：
- `_compute_tag_count()` - 計算標籤數量
- `action_view_tags()` - 開啟標籤列表

**更新 `_USER_EDITABLE_FIELDS`**：加入 `tag_ids`

### 4. 更新 Device 表單視圖

**新增內容**：
1. Button Box 中新增 Tags 統計按鈕
2. Editable Fields 區塊新增 `tag_ids` 欄位
3. Search View 新增 `tag_ids` 欄位

---

## 檔案變更清單

| 檔案 | 操作 | 說明 |
|------|------|------|
| `src/models/ha_device_tag.py` | 新增 | Device Tag 模型 |
| `src/models/ha_device.py` | 修改 | 新增 tag_ids 欄位 |
| `src/models/__init__.py` | 修改 | 註冊新模型 |
| `src/views/ha_device_tag_views.xml` | 新增 | Device Tag 視圖 |
| `src/views/ha_device_views.xml` | 修改 | 新增 Tags 區塊 |
| `src/views/dashboard_menu.xml` | 修改 | 選單重組 |
| `src/security/ir.model.access.csv` | 修改 | 新增權限 |
| `src/__manifest__.py` | 修改 | 新增視圖檔案 |

---

## 測試計畫

### 功能測試

| 測試項目 | 步驟 | 預期結果 |
|----------|------|----------|
| 選單重組 - Entity Tag | 點擊 Configuration 選單 | 看到 Entity Tag 選項 |
| 選單重組 - Entity Group Tag | 點擊 Configuration 選單 | 看到 Entity Group Tag 選項 |
| 選單重組 - Model 選單 | 點擊 Model 選單 | 不再看到 Entity Tag 和 Entity Group Tag |
| Device Tag 頁面 | 點擊 Configuration > Device Tag | 正常顯示 Kanban 視圖 |
| Device Tag 新增 | 建立新的 Device Tag | 成功建立，顯示在列表中 |
| Device Tag 編輯 | 修改 Device Tag | 成功儲存修改 |
| Device Tag 刪除 | 刪除 Device Tag | 成功刪除 |
| Device 表單 Tags | 開啟 Device 表單 | 看到 Tags 欄位在 Editable Fields 區塊 |
| Device 新增 Tag | 在 Device 表單新增 Tag | Tag 成功關聯 |
| Device 移除 Tag | 在 Device 表單移除 Tag | Tag 成功移除 |
| Tags 統計按鈕 | Device 有 Tag 時 | 顯示 Tags 統計按鈕 |
| Tags 搜尋 | 使用 tag_ids 搜尋 Device | 正確篩選結果 |

### 資料驗證測試

| 測試項目 | 步驟 | 預期結果 |
|----------|------|----------|
| Tag 名稱唯一性 | 建立同名 Tag | 顯示驗證錯誤 |
| Instance 一致性 | 關聯不同 Instance 的 Device | 顯示驗證錯誤 |

### 權限測試

| 角色 | 預期權限 |
|------|----------|
| ha_manager | 完整 CRUD |
| ha_user | 完整 CRUD |

---

## 驗收標準

### 功能驗收
- [x] Entity Tag 和 Entity Group Tag 出現在 Configuration 選單下
- [x] Entity Tag 和 Entity Group Tag 不再出現在 Model 選單下
- [ ] Device Tag 頁面可正常存取
- [ ] Device Tag 的 CRUD 操作正常
- [ ] Device 表單顯示 Tags 區塊
- [ ] Device 表單可新增/移除 Tags
- [ ] Tags 統計按鈕正確顯示數量
- [ ] Tags 顏色正確顯示

### 資料驗證
- [ ] Tag 與 Device 必須屬於同一 HA Instance
- [ ] 同一 Instance 內 Tag 名稱唯一

### 權限驗證
- [ ] ha_user 群組可完整操作 Device Tag

---

## 部署指南

```bash
# 重啟 Odoo 服務
docker compose restart web

# 升級模組
docker compose exec web odoo -c /etc/odoo/odoo.conf -d odoo -u odoo_ha_addon --stop-after-init
```

---

## 參考資料

- Entity Tag 實作：`src/models/ha_entity_tag.py`
- Entity Tag 視圖：`src/views/ha_entity_tag_views.xml`
- Entity 表單 Tags：`src/views/ha_entity_views.xml`
