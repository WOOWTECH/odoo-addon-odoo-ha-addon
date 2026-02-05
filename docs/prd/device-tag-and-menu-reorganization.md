# PRD: Device Tag 功能與選單重組

## 概述

### 目標
1. 將 Entity Tag 和 Entity Group Tag 從 Model 選單移至 Configuration 選單
2. 新增 Device Tag 功能，實作邏輯與 Entity Tag 相同
3. 在 Device 表單中新增 tag_ids 欄位

### 背景
目前 Entity Tag 和 Entity Group Tag 被放在 Model 選單下，但它們本質上是配置資料（用於分類管理），應該放在 Configuration 選單下。同時，Device 模型缺少 Tag 功能，需要補齊。

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
    help='Tags for this device',
    tracking=True
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
- 更新 `_check_instance_consistency()` - 驗證 tag 與 device 屬於同一實例

### 4. 更新 Device 表單視圖

**新增內容**：
1. Button Box 中新增 Tags 統計按鈕
2. 新增 Tags 區塊，使用 `many2many_tags` widget

---

## 實作計畫

### Phase 1: 選單重組
**檔案**：`src/views/dashboard_menu.xml`

**變更**：
1. 移除 Model 選單下的 Entity Tag 和 Entity Group Tag
2. 在 Configuration 選單下新增這兩個項目

```xml
<!-- Configuration 選單新增 -->
<menuitem name="Entity Tag"
          id="odoo_ha_addon.config_entity_tag_menu"
          action="odoo_ha_addon.ha_entity_tag_action"
          parent="odoo_ha_addon.configuration_top_menu"
          sequence="10"/>
<menuitem name="Entity Group Tag"
          id="odoo_ha_addon.config_entity_group_tag_menu"
          action="odoo_ha_addon.ha_entity_group_tag_action"
          parent="odoo_ha_addon.configuration_top_menu"
          sequence="11"/>
```

### Phase 2: Device Tag 模型
**新增檔案**：`src/models/ha_device_tag.py`

**參照**：`src/models/ha_entity_tag.py`

**核心實作**：
```python
class HADeviceTag(models.Model):
    _name = 'ha.device.tag'
    _description = 'HA Device Tag'
    _inherit = ['ha.current.instance.filter.mixin']
    _order = 'sequence, name'

    ha_instance_id = fields.Many2one(
        'ha.instance',
        string='HA Instance',
        required=True,
        index=True,
        ondelete='cascade'
    )
    name = fields.Char(string='Tag Name', required=True, index=True)
    color = fields.Integer(string='Color', default=0)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    device_ids = fields.Many2many(
        'ha.device',
        'ha_device_tag_rel',
        'tag_id',
        'device_id',
        string='Devices'
    )

    device_count = fields.Integer(
        string='Device Count',
        compute='_compute_device_count',
        store=True
    )
```

### Phase 3: Device Tag 視圖
**新增檔案**：`src/views/ha_device_tag_views.xml`

**參照**：`src/views/ha_entity_tag_views.xml`

**視圖類型**：
- List View（可編輯，支援拖曳排序）
- Form View（含 Devices 頁籤）
- Kanban View
- Search View

### Phase 4: 更新 Device 模型
**檔案**：`src/models/ha_device.py`

**新增**：
1. `tag_ids` Many2many 欄位
2. `tag_count` 計算欄位
3. `_compute_tag_count()` 方法
4. `action_view_tags()` 方法
5. 更新 `_check_instance_consistency()` 約束

### Phase 5: 更新 Device 視圖
**檔案**：`src/views/ha_device_views.xml`

**新增**：
1. Button Box 中的 Tags 按鈕
2. Tags 欄位區塊

```xml
<!-- Button Box -->
<button name="action_view_tags"
        type="object"
        class="oe_stat_button"
        icon="fa-tags"
        invisible="tag_count == 0">
    <field name="tag_count" widget="statinfo" string="Tags"/>
</button>

<!-- Tags 區塊 -->
<group string="Tags">
    <field name="tag_ids" widget="many2many_tags"
           domain="[('ha_instance_id', '=', ha_instance_id)]"
           options="{'color_field': 'color', 'no_create': False}"
           context="{'default_ha_instance_id': ha_instance_id}"/>
</group>
```

### Phase 6: 選單新增 Device Tag
**檔案**：`src/views/dashboard_menu.xml`

```xml
<menuitem name="Device Tag"
          id="odoo_ha_addon.config_device_tag_menu"
          action="odoo_ha_addon.ha_device_tag_action"
          parent="odoo_ha_addon.configuration_top_menu"
          sequence="12"/>
```

### Phase 7: 模組註冊
**檔案**：`src/models/__init__.py`

新增：
```python
from . import ha_device_tag
```

### Phase 8: 翻譯更新
**檔案**：`src/i18n/zh_TW.po`

新增 Device Tag 相關翻譯。

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
| `src/i18n/zh_TW.po` | 修改 | 新增翻譯 |

---

## 驗收標準

### 功能驗收
- [ ] Entity Tag 和 Entity Group Tag 出現在 Configuration 選單下
- [ ] Entity Tag 和 Entity Group Tag 不再出現在 Model 選單下
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
- [ ] ha_admin 群組可完整操作 Device Tag
- [ ] ha_user 群組可查看 Device Tag

---

## 參考資料

- Entity Tag 實作：`src/models/ha_entity_tag.py`
- Entity Tag 視圖：`src/views/ha_entity_tag_views.xml`
- Entity 表單 Tags：`src/views/ha_entity_views.xml` (行 105-116)
