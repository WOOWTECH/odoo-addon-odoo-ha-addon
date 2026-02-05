# Device Form Enhancements - Share, Properties, View Entities

## Overview

在 Device（設備）表單中增加與 Entity Groups 相同的功能，包括：分享功能、自訂屬性、查看實體按鈕。

**Created:** 2026-02-05T03:46:30Z
**Status:** In Progress (部分實作已完成)

---

## 1. Requirements Summary

### 1.1 Share with Users (分享給其他人)

**功能描述：**
- 在 Device 表單的 header 區域新增「Share with Users」按鈕
- 點擊後開啟分享精靈（ha.entity.share.wizard），可選擇用戶、權限、到期日
- 在表單的 notebook 區域新增「Sharing」分頁，顯示現有分享記錄
- 分頁內可延長到期日、撤銷分享

**UI 參考：** Entity Groups 表單的分享功能

### 1.2 Custom Properties (自訂屬性 / 加入屬性)

**功能描述：**
- 使用 Odoo 的 `fields.Properties` 欄位
- 屬性定義在 HA Instance 層級（`ha.instance.device_properties_definition`）
- 所有該 Instance 的設備共用相同的屬性定義
- 在表單中顯示「Custom Properties」區塊
- 齒輪選單中顯示「加入屬性」選項（Odoo 內建行為）

**UI 參考：** Entity 表單的 `properties` 欄位

### 1.3 View Entities Button & Stat Button (查看實體按鈕與數量)

**功能描述：**
- 在 button_box 區域新增 stat button，顯示「Entities」及數量
- 點擊後導航到該設備下的實體列表
- 在 header 區域「Share with Users」按鈕旁新增「View Entities」按鈕

**UI 參考：** Entity Groups 表單的 Entities stat button 和 View Entities 按鈕

---

## 2. Technical Design

### 2.1 Model Changes

#### ha.device (src/models/ha_device.py)

**已完成的變更：**
```python
# Share records - 已新增
share_ids = fields.One2many('ha.entity.share', 'device_id', string='Shares')
share_count = fields.Integer(compute='_compute_share_count')
```

**待新增的變更：**
```python
# Custom Properties - 使用 HA Instance 層級定義
properties = fields.Properties(
    'Properties',
    definition='ha_instance_id.device_properties_definition',
    copy=True,
    help='Custom properties for this device (defined at instance level)'
)

# Methods
def _compute_share_count(self):
    """Compute number of active (non-expired) shares"""

def action_share(self):
    """Open share wizard for this device"""

def action_view_entities(self):
    """Navigate to entity list filtered by this device"""
```

#### ha.instance (src/models/ha_instance.py)

**待新增的變更：**
```python
# Device Properties Definition
device_properties_definition = fields.PropertiesDefinition(
    'Device Properties Definition',
    help='Define custom properties available for all devices in this instance'
)
```

#### ha.entity.share (src/models/ha_entity_share.py)

**已完成的變更：**
- ✅ 新增 `device_id` 欄位
- ✅ 更新 SQL constraints 支援 device
- ✅ 更新 `_compute_ha_instance_id` 支援 device
- ✅ 更新 `_compute_display_name` 支援 device
- ✅ 更新 `_check_entity_group_or_device` constraint
- ✅ 更新 `_check_not_share_to_owner` constraint
- ✅ 更新 `_send_expiry_notification` 支援 device
- ✅ 新增 `get_shared_devices_for_user` 方法

#### ha.entity.share.wizard (src/wizard/ha_entity_share_wizard.py)

**已完成的變更：**
- ✅ 新增 `device_id` 欄位
- ✅ 更新 `_compute_target_name` 支援 device
- ✅ 更新 `_compute_existing_shares` 支援 device
- ✅ 更新 `default_get` 支援 device
- ✅ 更新 `_check_entity_group_or_device` constraint
- ✅ 更新 `action_share` 方法支援 device

### 2.2 View Changes

#### ha_device_views.xml (src/views/ha_device_views.xml)

**待修改的變更：**

```xml
<!-- Form View 結構 -->
<form>
  <header>
    <!-- 新增 Share with Users 按鈕 -->
    <button name="action_share" type="object" string="Share with Users"
            class="btn-secondary"
            groups="odoo_ha_addon.group_ha_manager"/>
    <!-- 新增 View Entities 按鈕 -->
    <button name="action_view_entities" type="object" string="View Entities"
            class="btn-primary"/>
  </header>
  <sheet>
    <div class="oe_button_box" name="button_box">
      <!-- 新增 Entities stat button -->
      <button name="action_view_entities" type="object"
              class="oe_stat_button" icon="fa-cube">
        <field name="entity_count" widget="statinfo" string="Entities"/>
      </button>
    </div>

    <!-- 現有欄位... -->

    <!-- 新增 Custom Properties 區塊 -->
    <group string="Custom Properties">
      <field name="properties" columns="2"/>
    </group>

    <notebook>
      <!-- 現有分頁... -->

      <!-- 新增 Sharing 分頁 -->
      <page string="Sharing" name="sharing" groups="odoo_ha_addon.group_ha_manager">
        <field name="share_ids">
          <list string="Shares" editable="bottom" create="false">
            <field name="user_id" readonly="1"/>
            <field name="permission"/>
            <field name="expiry_date"/>
            <field name="is_expired" widget="boolean"/>
            <button name="action_extend_expiry" type="object"
                    string="Extend 30 days" icon="fa-calendar-plus-o"
                    invisible="not expiry_date"/>
            <button name="unlink" type="object"
                    string="Revoke" icon="fa-trash"
                    confirm="Are you sure you want to revoke this share?"/>
          </list>
        </field>
        <div class="alert alert-info mt-3" role="status"
             invisible="share_ids">
          <i class="fa fa-info-circle me-2"/>
          This device has not been shared with any users yet.
          Click "Share with Users" to share it.
        </div>
      </page>
    </notebook>
  </sheet>
</form>
```

### 2.3 User Editable Fields

**重要：** `properties` 欄位需要加入 `_USER_EDITABLE_FIELDS`：

```python
_USER_EDITABLE_FIELDS = {'area_id', 'name_by_user', 'label_ids', 'properties'}
```

---

## 3. Implementation Tasks

### Phase 1: Model Layer (部分已完成)
- [x] ha.entity.share: 新增 device_id 支援
- [x] ha.entity.share.wizard: 新增 device_id 支援
- [x] ha.device: 新增 share_ids, share_count 欄位
- [ ] ha.device: 實作 `_compute_share_count` 方法
- [ ] ha.device: 實作 `action_share` 方法
- [ ] ha.device: 實作 `action_view_entities` 方法
- [ ] ha.instance: 新增 `device_properties_definition` 欄位
- [ ] ha.device: 新增 `properties` 欄位
- [ ] ha.device: 更新 `_USER_EDITABLE_FIELDS`

### Phase 2: View Layer
- [ ] ha_device_views.xml: 新增 header 按鈕
- [ ] ha_device_views.xml: 新增 stat button
- [ ] ha_device_views.xml: 新增 Custom Properties 區塊
- [ ] ha_device_views.xml: 新增 Sharing 分頁

### Phase 3: Translations
- [ ] i18n/zh_TW.po: 新增繁體中文翻譯

---

## 4. Security Considerations

- **Share with Users 按鈕**：限制 `group_ha_manager` 群組可見
- **Sharing 分頁**：限制 `group_ha_manager` 群組可見
- **Properties**：使用 `_USER_EDITABLE_FIELDS` 控制寫入權限

---

## 5. UI/UX Notes

### 按鈕位置
- **Stat Button (Entities)**：右上角 button_box 區域，顯示圖示 `fa-cube`
- **Share with Users**：header 區域，btn-secondary 樣式
- **View Entities**：header 區域，btn-primary 樣式，位於 Share with Users 旁邊

### 參考截圖
- Entity Groups 表單已實作相同功能，作為 UI 參考

---

## 6. Affected Files

| File | Changes |
|------|---------|
| `src/models/ha_device.py` | 新增 properties, action methods |
| `src/models/ha_instance.py` | 新增 device_properties_definition |
| `src/models/ha_entity_share.py` | ✅ 已完成 device_id 支援 |
| `src/wizard/ha_entity_share_wizard.py` | ✅ 已完成 device_id 支援 |
| `src/views/ha_device_views.xml` | 新增按鈕、分頁、properties |
| `src/i18n/zh_TW.po` | 新增翻譯 |
