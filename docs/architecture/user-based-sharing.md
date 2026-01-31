# 使用者導向的實體分享架構

## 概述

本文件描述 odoo_ha_addon 中實體（Entity）和實體群組（Entity Group）存取的使用者導向分享架構。此系統以更安全的使用者導向方式取代了先前的 Token 驗證機制。

## 核心元件

### 1. ha.entity.share 模型

`ha.entity.share` 模型是追蹤分享關係的核心記錄。

**檔案**：`models/ha_entity_share.py`

```
ha.entity.share
+------------------+
| entity_id (M2O)  | <-- ha.entity（互斥）
| group_id (M2O)   | <-- ha.entity.group（互斥）
| user_id (M2O)    | <-- res.users（必填）
| permission       | <-- 'view' 或 'control'
| expiry_date      | <-- 選填的日期時間
| notification_sent| <-- 追蹤到期通知狀態
| ha_instance_id   | <-- 從 entity/group 計算
| is_expired       | <-- 根據 expiry_date 計算
+------------------+
```

**SQL 約束條件**：
- `entity_or_group_required`：必須指定 entity_id 或 group_id 其中之一
- `unique_entity_user`：實體 + 使用者組合必須唯一
- `unique_group_user`：群組 + 使用者組合必須唯一

### 2. 分享精靈（ha.entity.share.wizard）

精靈提供使用者友善的介面來建立分享。

**檔案**：`wizards/ha_entity_share_wizard.py`

**功能**：
- 透過 Many2many 欄位支援多使用者選擇
- 權限等級選擇（view/control）
- 選填的到期日期
- 情境感知：從表單視圖自動填入 entity/group
- 透過更新現有分享來處理重複項目

### 3. Portal 控制器

Portal 控制器處理使用者驗證的存取。

**檔案**：`controllers/portal.py`

**路由**：
| 路由 | 驗證 | 用途 |
|------|------|------|
| `/portal/entity/<id>` | user | 實體 Portal 頁面 |
| `/portal/entity/<id>/state` | user | 實體狀態輪詢 |
| `/portal/call-service` | user | 裝置控制 API |
| `/portal/entity_group/<id>` | user | 群組 Portal 頁面 |
| `/portal/entity_group/<id>/state` | user | 群組狀態輪詢 |
| `/my/ha` | user | 使用者的分享實例列表 |
| `/my/ha/<instance_id>` | user | 實例的實體/群組分頁 |

## 安全架構

### 驗證流程

```
使用者請求
     |
     v
[auth='user'] -----> 未登入？ -----> 重導向至 /web/login
     |
     v（已登入）
[_check_entity_share_access()]
     |
     v
檢查 ha.entity.share 記錄是否存在（entity_id, user_id）
     |
     v
檢查 expiry_date 是否為空或在未來
     |
     v
如需要則檢查權限等級（'control'）
     |
     v（所有檢查通過）
回傳內容 / 允許操作
```

### 權限等級

| 權限 | 檢視實體 | 控制實體 | 使用 call-service |
|------|----------|----------|-------------------|
| `view` | 是 | 否（隱藏 UI） | 否 |
| `control` | 是 | 是 | 是 |

### 欄位白名單

只有白名單欄位會透過 Portal 端點暴露：

**PORTAL_ENTITY_FIELDS**：
- id, name, entity_id, entity_state, last_changed, area_id, domain, attributes

**PORTAL_GROUP_FIELDS**：
- id, name, description, entity_ids, entity_count

### 服務白名單

控制操作限制於每個 domain 預先定義的服務：

```python
PORTAL_CONTROL_SERVICES = {
    'switch': ['toggle', 'turn_on', 'turn_off'],
    'light': ['toggle', 'turn_on', 'turn_off', 'set_brightness', 'set_color_temp'],
    'fan': ['toggle', 'turn_on', 'turn_off', 'set_percentage', ...],
    'climate': ['set_temperature', 'set_hvac_mode', 'set_fan_mode'],
    'cover': ['open_cover', 'close_cover', 'stop_cover', 'set_cover_position'],
    'scene': ['turn_on'],
    'script': ['toggle', 'turn_on', 'turn_off'],
    'automation': ['toggle', 'trigger', 'turn_on', 'turn_off'],
    'sensor': [],  # 唯讀
}
```

## 到期管理

### 排程工作

**1. _cron_check_expiring_shares**（每日）
- 尋找 7 天內即將到期的分享
- 為分享建立者建立 mail.activity
- 設定 `notification_sent = True`

**2. _cron_cleanup_expired_shares**（每週）
- 尋找已到期超過 30 天的分享
- 刪除過時記錄以保持資料庫整潔

### 存取檢查中的到期處理

```python
share = env['ha.entity.share'].search([
    ('entity_id', '=', entity_id),
    ('user_id', '=', user_id),
    '|',
    ('expiry_date', '=', False),    # 無到期日 = 永久有效
    ('expiry_date', '>', now())     # 到期日在未來 = 有效
], limit=1)
```

## 使用範例

### 建立分享（透過精靈）

```python
# 從實體表單視圖，點擊「分享」按鈕
wizard = env['ha.entity.share.wizard'].with_context(
    default_entity_id=entity.id
).create({
    'user_ids': [(6, 0, [user1.id, user2.id])],
    'permission': 'control',
    'expiry_date': datetime.now() + timedelta(days=30),
})
wizard.action_share()
```

### 程式化檢查存取權限

```python
# 檢查使用者是否有實體存取權
share = env['ha.entity.share'].search([
    ('entity_id', '=', entity_id),
    ('user_id', '=', user_id),
    ('is_expired', '=', False),
], limit=1)

if share:
    can_view = True
    can_control = share.permission == 'control'
```

### 取得使用者的分享實體

```python
# 取得所有分享給當前使用者的實體
entities = env['ha.entity.share'].get_shared_entities_for_user()

# 取得具有控制權限的實體
controllable = env['ha.entity.share'].get_shared_entities_for_user(
    permission='control'
)
```

## 資料流程圖

```
+------------------+     +----------------------+     +------------------+
|    ha.entity     |<----|   ha.entity.share    |---->|    res.users     |
+------------------+     +----------------------+     +------------------+
         |                        |
         |                        |
         v                        v
+------------------+     +----------------------+
| ha.entity.group  |<----| (group_id 參照)       |
+------------------+     +----------------------+
         |
         v
+------------------+
|   ha.instance    |
+------------------+
```

## 與 Token 系統的比較

| 面向 | Token 導向（舊） | 使用者導向（新） |
|------|------------------|------------------|
| 驗證方式 | URL token 參數 | Odoo session |
| 使用者身份 | 匿名 | 已知使用者 |
| 撤銷方式 | 重新產生 token | 刪除分享記錄 |
| 到期機制 | 每個 token 到期 | 每個分享到期 |
| 稽核軌跡 | 有限 | 完整（分享記錄） |
| 權限等級 | 無 | view/control |
| 多使用者 | 每個實體一個 token | 每個實體多個分享 |

## 安全檢查清單

- [x] 所有路由使用 `auth='user'`
- [x] 無法透過 URL 操作存取未分享的實體
- [x] view 權限使用者無法呼叫控制 API
- [x] 已到期的分享被拒絕
- [x] `sudo()` 僅用於讀取，不用於寫入
- [x] 無 SQL 注入風險（僅使用 ORM）
- [x] 無 XSS 風險（QWeb 自動跳脫 + 欄位白名單）

## 相關文件

- [安全架構](security-architecture.md) - 整體安全模型
- [實例輔助器](instance-helper.md) - 實例選擇與篩選
- [Session 實例](session-instance.md) - 基於 Session 的實例管理
