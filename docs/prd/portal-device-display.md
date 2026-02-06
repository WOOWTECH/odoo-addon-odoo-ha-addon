# PRD: Portal Device Display 功能

## 概述

### 目標
在 Portal 頁面中新增 Devices 標籤頁，讓被分享 Device 的 Portal 使用者能夠查看和控制設備。

### 背景
目前 `ha.entity.share` 模型已支援 Device 分享功能（`device_id` 欄位），但 Portal 頁面只顯示 Entities 和 Groups 兩個標籤頁。當使用者透過 Device 分享連結進入 Portal 後，無法在 Portal 總覽頁面看到被分享的 Device。

### 問題描述
1. Portal 控制器 (`portal.py`) 的 `_get_user_instances_with_shares()` 方法未處理 `device_id` 分享
2. Portal 控制器的 `portal_my_ha_instance()` 路由未取得 device shares
3. Portal 模板 (`portal_templates.xml`) 缺少 Devices 標籤頁

---

## 實作狀態

| Phase | 說明 | 狀態 | 檔案 |
|-------|------|------|------|
| 1 | 更新 Portal 控制器 | ⬜ 待開始 | `src/controllers/portal.py` |
| 2 | 新增 Devices 標籤頁模板 | ⬜ 待開始 | `src/views/portal_templates.xml` |
| 3 | 新增 Device 詳細頁面 | ⬜ 待開始 | `src/controllers/portal.py`, `src/views/portal_templates.xml` |

---

## 變更範圍

### 1. 更新 Portal 控制器

**檔案**: `src/controllers/portal.py`

#### 1.1 更新 `_get_user_instances_with_shares()` 方法

**現狀** (約 line 566-598):
```python
for share in user_shares:
    instance = share.ha_instance_id
    if instance.id not in instance_data:
        instance_data[instance.id] = {
            'instance': instance,
            'entity_shares': [],
            'group_shares': [],
        }
    if share.entity_id:
        instance_data[instance.id]['entity_shares'].append(share)
    elif share.group_id:
        instance_data[instance.id]['group_shares'].append(share)
```

**目標**:
```python
for share in user_shares:
    instance = share.ha_instance_id
    if instance.id not in instance_data:
        instance_data[instance.id] = {
            'instance': instance,
            'entity_shares': [],
            'group_shares': [],
            'device_shares': [],  # 新增
        }
    if share.entity_id:
        instance_data[instance.id]['entity_shares'].append(share)
    elif share.group_id:
        instance_data[instance.id]['group_shares'].append(share)
    elif share.device_id:  # 新增
        instance_data[instance.id]['device_shares'].append(share)
```

#### 1.2 更新 `portal_my_ha_instance()` 路由

**新增內容**:
```python
# 取得 device shares
device_shares = [s for s in shares if s.device_id]
devices = [s.device_id for s in device_shares]
```

**更新 values dict**:
```python
values.update({
    # ... existing ...
    'devices': devices,
    'device_count': len(devices),
})
```

#### 1.3 新增 Device 詳細頁面路由

**新增路由** (參照 `portal_entity()` 和 `portal_entity_group()` 實作):
```python
@route('/portal/device/<int:device_id>', type='http', auth='user', website=True)
def portal_device(self, device_id, **kw):
    """Portal device detail page."""
    # 驗證使用者有權限存取該 device
    # 取得 device 資料
    # 取得 device 下的所有 entities
    # 渲染模板
```

### 2. 新增 Devices 標籤頁模板

**檔案**: `src/views/portal_templates.xml`

#### 2.1 更新 `portal_my_ha_instance` 模板

在現有的 Groups 標籤旁新增 Devices 標籤:

```xml
<!-- Devices Tab -->
<li class="nav-item" role="presentation">
    <button class="nav-link" id="devices-tab" data-bs-toggle="tab"
            data-bs-target="#devices" type="button" role="tab"
            aria-controls="devices" aria-selected="false">
        <i class="fa fa-puzzle-piece me-1"/>
        <span t-esc="device_count"/> Devices
    </button>
</li>
```

#### 2.2 新增 Devices Tab 內容

參照現有的 Entities 和 Groups tab 內容樣式:

```xml
<!-- Devices Tab Content -->
<div class="tab-pane fade" id="devices" role="tabpanel" aria-labelledby="devices-tab">
    <!-- Desktop Table -->
    <div class="d-none d-md-block">
        <table class="table table-sm">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Area</th>
                    <th>Entities</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                <t t-foreach="devices" t-as="device">
                    <tr>
                        <td t-esc="device.name_by_user or device.name"/>
                        <td t-esc="device.area_id.name or '-'"/>
                        <td t-esc="len(device.entity_ids)"/>
                        <td>
                            <a t-attf-href="/portal/device/#{device.id}?access_token=#{access_token}"
                               class="btn btn-sm btn-primary">
                                View
                            </a>
                        </td>
                    </tr>
                </t>
            </tbody>
        </table>
    </div>

    <!-- Mobile Cards -->
    <div class="d-md-none">
        <t t-foreach="devices" t-as="device">
            <div class="card mb-2">
                <div class="card-body">
                    <h6 class="card-title" t-esc="device.name_by_user or device.name"/>
                    <p class="card-text text-muted small">
                        Area: <span t-esc="device.area_id.name or '-'"/>
                    </p>
                    <a t-attf-href="/portal/device/#{device.id}?access_token=#{access_token}"
                       class="btn btn-sm btn-primary">
                        View Device
                    </a>
                </div>
            </div>
        </t>
    </div>
</div>
```

### 3. 新增 Device 詳細頁面模板

**新增模板**: `portal_device`

參照 `portal_entity` 和 `portal_entity_group` 模板:

```xml
<template id="portal_device" name="Portal Device">
    <t t-call="portal.portal_layout">
        <div class="container py-3">
            <!-- Breadcrumb -->
            <nav aria-label="breadcrumb" class="mb-3">
                <ol class="breadcrumb">
                    <li class="breadcrumb-item">
                        <a t-attf-href="/portal/instance/#{instance.id}?access_token=#{access_token}">
                            <t t-esc="instance.name"/>
                        </a>
                    </li>
                    <li class="breadcrumb-item active">
                        <t t-esc="device.name_by_user or device.name"/>
                    </li>
                </ol>
            </nav>

            <!-- Device Info -->
            <div class="card mb-3">
                <div class="card-header">
                    <h5><i class="fa fa-puzzle-piece me-2"/><t t-esc="device.name_by_user or device.name"/></h5>
                </div>
                <div class="card-body">
                    <dl class="row mb-0">
                        <dt class="col-sm-3">Manufacturer</dt>
                        <dd class="col-sm-9" t-esc="device.manufacturer or '-'"/>
                        <dt class="col-sm-3">Model</dt>
                        <dd class="col-sm-9" t-esc="device.model or '-'"/>
                        <dt class="col-sm-3">Area</dt>
                        <dd class="col-sm-9" t-esc="device.area_id.name or '-'"/>
                    </dl>
                </div>
            </div>

            <!-- Device Entities -->
            <div class="card">
                <div class="card-header">
                    <h6>Entities (<t t-esc="len(entities)"/>)</h6>
                </div>
                <div class="card-body p-0">
                    <t t-foreach="entities" t-as="entity">
                        <!-- Entity control component -->
                    </t>
                </div>
            </div>
        </div>
    </t>
</template>
```

---

## 檔案變更清單

| 檔案 | 操作 | 說明 |
|------|------|------|
| `src/controllers/portal.py` | 修改 | 新增 device shares 處理邏輯和 device 詳細頁面路由 |
| `src/views/portal_templates.xml` | 修改 | 新增 Devices 標籤頁和 Device 詳細頁面模板 |

---

## 測試計畫

### 功能測試

| 測試項目 | 步驟 | 預期結果 |
|----------|------|----------|
| Devices 標籤頁顯示 | 分享 Device 給使用者後，進入 Portal Instance 頁面 | 看到 Devices 標籤頁 |
| Device 數量顯示 | 分享多個 Device 後查看標籤頁 | 顯示正確的 Device 數量 |
| Device 列表顯示 | 點擊 Devices 標籤頁 | 顯示所有被分享的 Device |
| Device 詳細頁面 | 點擊 Device 的 View 按鈕 | 進入 Device 詳細頁面 |
| Device Entity 顯示 | 在 Device 詳細頁面 | 顯示該 Device 下的所有 Entities |
| Entity 控制 | 在 Device 詳細頁面控制 Entity | 成功控制 Entity 狀態 |
| 權限驗證 | 存取未被分享的 Device | 顯示 403 錯誤 |
| Token 驗證 | 使用無效 token 存取 | 顯示 403 錯誤 |

### 響應式測試

| 測試項目 | 步驟 | 預期結果 |
|----------|------|----------|
| 桌面版列表 | 使用桌面瀏覽器查看 Devices 列表 | 顯示表格格式 |
| 手機版列表 | 使用手機瀏覽器查看 Devices 列表 | 顯示卡片格式 |

---

## 驗收標準

### 功能驗收
- [ ] Portal Instance 頁面顯示 Devices 標籤頁
- [ ] Devices 標籤頁顯示正確的數量
- [ ] Devices 列表正確顯示所有被分享的 Device
- [ ] Device 詳細頁面可正常存取
- [ ] Device 詳細頁面顯示 Device 基本資訊
- [ ] Device 詳細頁面顯示相關 Entities
- [ ] Entities 可在 Device 詳細頁面進行控制

### 權限驗證
- [ ] 只能存取被分享的 Device
- [ ] Token 驗證正常運作
- [ ] 未授權存取返回 403 錯誤

### 響應式設計
- [ ] 桌面版顯示表格格式
- [ ] 手機版顯示卡片格式

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

- Portal 控制器：`src/controllers/portal.py`
- Portal 模板：`src/views/portal_templates.xml`
- Entity Share 模型：`src/models/ha_entity_share.py`
- 現有 Entity Portal 實作：`portal_entity()` 路由和 `portal_entity` 模板
- 現有 Entity Group Portal 實作：`portal_entity_group()` 路由和 `portal_entity_group` 模板
