# Odoo HA Addon - 全面代碼審查報告

**審查日期**: 2025-11-13
**審查範圍**: 完整代碼庫
**審查者**: Claude Code (code-reviewer-pro agent)
**總體評分**: 8.5/10 ⭐

---

## ✅ 後續更新 (2025-11-17)

**Critical Issue #2 (權限控制過於寬鬆) 已修復**:

- ✅ 創建專屬 `group_ha_user` 權限組（遵循 Point of Sale 模組模式）
- ✅ 實施最小權限原則：用戶需明確授權才能訪問 HA 功能
- ✅ 更新 12 條 `ir.rule` 規則綁定至 `group_ha_user`
- ✅ 簡化 `ir.model.access.csv` 從 19 行至 12 行
- ✅ 支持 Portal 用戶訪問（`group_ha_user` 不包含 `implied_ids`）

詳見：
- `docs/tech/security-architecture.md` - 完整安全架構說明
- `docs/migration/instance-to-group-based-permissions.md` - 遷移指南

---

## 執行摘要

這是一個**架構設計優秀、代碼品質高**的專業 Odoo 18 addon 項目，展現了對 Odoo 框架和 Home Assistant 整合的深刻理解。代碼整體質量優秀，有清晰的架構設計和詳盡的文檔。

### 問題統計
- **Critical Issues**: 2 個（必須在合併前修復）
- **High Priority Warnings**: 5 個（應儘快解決）
- **Medium Priority Warnings**: 4 個（計劃中）
- **Suggestions**: 12 個（改進項目）

---

## 📋 目錄

1. [優點列表](#優點列表)
2. [Critical Issues](#critical-issues-)
3. [High Priority Warnings](#high-priority-warnings-)
4. [Medium Priority Warnings](#medium-priority-warnings-)
5. [Suggestions](#suggestions-)
6. [架構建議](#架構建議)
7. [重構優先級](#重構優先級)
8. [總結](#總結)

---

## 優點列表

### 1. 架構設計優秀 🏗️

- **Session-Based Instance Architecture**: 設計清晰的多實例架構，session 存儲當前實例 ID，避免每次 API 調用都傳遞參數
- **Service Layer Pattern**: 前端使用 `HaDataService` 和 `ChartService` 統一管理，避免組件直接調用 RPC
- **Bus Bridge Pattern**: 集中式 Bus 訂閱，避免重複訂閱和內存洩漏
- **HAInstanceHelper**: 統一的實例選擇邏輯，4-level fallback mechanism 設計合理

### 2. 代碼組織結構清晰 📁

- 前端代碼分層明確：services → components → views → actions
- 後端模型職責分明：models/common/ 存放共享邏輯
- WebSocket 整合使用獨立的 thread manager，避免阻塞主進程
- 完整的 uninstall hook，確保模組卸載時清理所有數據

### 3. 錯誤處理完善 ✅

- Controller 使用統一的 `_standardize_response()` 確保 API 響應格式一致
- 前端 HaDataService 整合 notification 服務，自動顯示錯誤提示
- WebSocket 服務有完整的重試機制（最多 5 次，指數退避）
- 實例驗證有結構化的錯誤類型（`instance_not_found`, `instance_inactive`, `instance_not_configured`）

### 4. 文檔完整且專業 📚

- `CLAUDE.md` 提供完整的開發指南和最佳實踐
- 技術文檔目錄組織良好（`docs/tech/`）
- 代碼註釋詳細，說明設計決策和實現細節
- Phase 標記清晰，易於追蹤功能演進

### 5. 安全意識良好 🔒

- API token 使用 `password="True"` 隱藏輸入
- 所有 token 存儲和傳輸都避免打印到日誌
- WebSocket 使用正確的認證流程
- 使用 `sudo()` 時有明確的權限控制考量

### 6. 性能優化到位 ⚡

- 前端使用 30 秒緩存策略
- 實體同步使用 savepoint 隔離更新，避免序列化衝突
- Chart.js 使用服務層統一管理，避免重複創建實例
- WebSocket 使用心跳機制檢測連接狀態

---

## Critical Issues 🚨

### 1. Subprocess 安全風險 - Python 依賴自動安裝

**嚴重程度**: 🔴 Critical
**位置**: `hooks.py:31-46`

#### 問題描述

使用 `subprocess.check_call()` 執行 `pip install --break-system-packages`，存在多個安全風險：

1. `--break-system-packages` 可能破壞系統 Python 環境
2. 如果 `package` 變數被惡意注入，可能執行任意命令
3. 在生產環境自動安裝依賴不符合最佳實踐
4. 沒有驗證安裝來源（PyPI），可能安裝惡意包

#### 當前代碼

```python
# hooks.py:31-46
def _check_and_install_dependency(package):
    """檢查並安裝必要的 Python 套件"""
    try:
        __import__(package)
        _logger.info(f"✓ Python 套件 '{package}' 已安裝")
        return True
    except ImportError:
        _logger.warning(f"✗ 未找到 Python 套件 '{package}'，嘗試自動安裝...")
        try:
            import subprocess
            import sys
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install',
                '--break-system-packages', package
            ])
            _logger.info(f"✓ 成功安裝 Python 套件 '{package}'")
            return True
        except Exception as e:
            _logger.error(f"✗ 安裝 Python 套件 '{package}' 失敗: {e}")
            return False
```

#### 建議修復方案

```python
# 方案 1: 使用 __manifest__.py 聲明依賴（推薦）
# __manifest__.py
{
    'name': 'Awesome Dashboard',
    'external_dependencies': {
        'python': ['websockets'],
    },
    # ...
}

# hooks.py - 只檢查，不安裝
def pre_init_hook(cr):
    """檢查必要的依賴"""
    try:
        __import__('websockets')
    except ImportError:
        raise ImportError(
            "Missing required package: websockets\n"
            "Please install manually:\n"
            "  pip install websockets\n"
            "Or add to requirements.txt for automated deployment"
        )
```

```python
# 方案 2: 提供 requirements.txt（用於部署）
# requirements.txt
websockets>=10.0

# README.md 中說明安裝步驟
## Installation
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Install Odoo addon:
   ```bash
   odoo -d dbname -i odoo_ha_addon
   ```
```

#### 修復理由

- ✅ 避免系統環境污染
- ✅ 符合 Odoo 最佳實踐（使用 external_dependencies）
- ✅ 防止生產環境自動執行未審查的安裝操作
- ✅ 提供明確的依賴聲明，便於容器化部署

#### 影響範圍

- **檔案**: `hooks.py`
- **行數**: 31-46
- **受影響功能**: WebSocket 服務啟動

---

### 2. 權限控制過於寬鬆

**嚴重程度**: 🔴 Critical
**位置**: `security/ir.model.access.csv`

#### 問題描述

所有模型給 `base.group_user`（普通用戶）賦予了完整的 CRUD 權限（1,1,1,1），導致：

1. **`ha.instance`**: 普通用戶可以創建/刪除實例，可能洩漏其他實例的 API token
2. **`ha.entity`**: 普通用戶可以修改實體狀態，破壞數據一致性
3. **`ha.ws.request.queue`**: 普通用戶可以操作 WebSocket 隊列，可能干擾系統運行
4. **`ha.realtime.update`**: 普通用戶可以修改通知系統

#### 當前代碼

```csv
# security/ir.model.access.csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_ha_instance,access.ha.instance,odoo_ha_addon.model_ha_instance,base.group_user,1,1,1,1
access_ha_entity,access.ha.entity,odoo_ha_addon.model_ha_entity,base.group_user,1,1,1,1
access_ha_entity_history,access.ha.entity.history,odoo_ha_addon.model_ha_entity_history,base.group_user,1,1,1,1
access_ha_area,access.ha.area,odoo_ha_addon.model_ha_area,base.group_user,1,1,1,1
access_ha_entity_group,access.ha.entity.group,odoo_ha_addon.model_ha_entity_group,base.group_user,1,1,1,1
access_ha_entity_group_tag,access.ha.entity.group.tag,odoo_ha_addon.model_ha_entity_group_tag,base.group_user,1,1,1,1
access_ha_ws_request_queue,access.ha.ws.request.queue,odoo_ha_addon.model_ha_ws_request_queue,base.group_user,1,1,1,1
access_ha_realtime_update,access.ha.realtime.update,odoo_ha_addon.model_ha_realtime_update,base.group_user,1,1,1,1
```

#### 建議修復方案

```csv
# security/ir.model.access.csv

# ========================================
# 1. 創建專用權限組
# ========================================
# 在 security/security.xml 中定義：
# <record id="group_ha_manager" model="res.groups">
#     <field name="name">Home Assistant Manager</field>
#     <field name="category_id" ref="base.module_category_hidden"/>
#     <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
# </record>

# ========================================
# 2. 實例管理 - 分級權限
# ========================================
# Manager: 完整權限（創建、編輯、刪除實例）
access_ha_instance_manager,access.ha.instance.manager,odoo_ha_addon.model_ha_instance,odoo_ha_addon.group_ha_manager,1,1,1,1
# User: 只讀（查看實例列表，切換實例）
access_ha_instance_user,access.ha.instance.user,odoo_ha_addon.model_ha_instance,base.group_user,1,0,0,0

# ========================================
# 3. 實體數據 - 只讀訪問
# ========================================
# 實體數據應該由 WebSocket 服務自動同步，用戶不應直接修改
access_ha_entity,access.ha.entity,odoo_ha_addon.model_ha_entity,base.group_user,1,0,0,0
access_ha_entity_history,access.ha.entity.history,odoo_ha_addon.model_ha_entity_history,base.group_user,1,0,0,0
access_ha_area,access.ha.area,odoo_ha_addon.model_ha_area,base.group_user,1,0,0,0

# Manager 可以手動清理數據
access_ha_entity_manager,access.ha.entity.manager,odoo_ha_addon.model_ha_entity,odoo_ha_addon.group_ha_manager,1,1,1,1
access_ha_entity_history_manager,access.ha.entity.history.manager,odoo_ha_addon.model_ha_entity_history,odoo_ha_addon.group_ha_manager,1,1,1,1

# ========================================
# 4. 實體分組 - 用戶可編輯
# ========================================
# 用戶可以創建自己的分組和標籤
access_ha_entity_group,access.ha.entity.group,odoo_ha_addon.model_ha_entity_group,base.group_user,1,1,1,1
access_ha_entity_group_tag,access.ha.entity.group.tag,odoo_ha_addon.model_ha_entity_group_tag,base.group_user,1,1,1,1

# ========================================
# 5. WebSocket 隊列 - 僅系統訪問
# ========================================
# WebSocket 隊列應該只有系統管理員可以查看（用於調試）
access_ha_ws_request_queue_system,access.ha.ws.request.queue.system,odoo_ha_addon.model_ha_ws_request_queue,base.group_system,1,1,1,1

# ========================================
# 6. 即時更新通知 - 內部使用
# ========================================
# 通知系統應該由後端自動觸發，用戶不應直接操作
# 但需要讀取權限以便前端訂閱 Bus 通知
access_ha_realtime_update,access.ha.realtime.update,odoo_ha_addon.model_ha_realtime_update,base.group_user,1,0,0,0
```

#### 額外需要創建的文件

```xml
<!-- security/security.xml -->
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="0">
        <!-- Home Assistant Manager 群組 -->
        <record id="group_ha_manager" model="res.groups">
            <field name="name">Home Assistant Manager</field>
            <field name="category_id" ref="base.module_category_hidden"/>
            <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
            <field name="comment">可以管理 Home Assistant 實例、配置和高級設定</field>
        </record>

        <!-- 記錄規則: 用戶只能看到有權限的實例 -->
        <record id="ha_instance_user_rule" model="ir.rule">
            <field name="name">HA Instance: User Access</field>
            <field name="model_id" ref="model_ha_instance"/>
            <field name="domain_force">[
                '|',
                ('user_ids', '=', False),
                ('user_ids', 'in', [user.id])
            ]</field>
            <field name="groups" eval="[(4, ref('base.group_user'))]"/>
        </record>

        <!-- 記錄規則: Manager 可以看到所有實例 -->
        <record id="ha_instance_manager_rule" model="ir.rule">
            <field name="name">HA Instance: Manager Full Access</field>
            <field name="model_id" ref="model_ha_instance"/>
            <field name="domain_force">[(1, '=', 1)]</field>
            <field name="groups" eval="[(4, ref('group_ha_manager'))]"/>
        </record>
    </data>
</odoo>
```

#### 在 `__manifest__.py` 中更新

```python
{
    # ...
    'data': [
        'security/security.xml',  # ← 必須在 ir.model.access.csv 之前
        'security/ir.model.access.csv',
        # ... 其他 data 文件
    ],
    # ...
}
```

#### 修復理由

- ✅ **防止數據洩漏**: 普通用戶無法查看其他實例的 API token
- ✅ **保護數據一致性**: 實體數據只能由 WebSocket 服務同步，用戶無法手動修改
- ✅ **職責分離**: Manager 負責實例管理，普通用戶只使用現有實例
- ✅ **符合最小權限原則**: 用戶只獲得完成工作所需的最小權限
- ✅ **支持多租戶**: 透過 ir.rule 實現實例級別的訪問控制

#### 影響範圍

- **檔案**: `security/ir.model.access.csv`, 新增 `security/security.xml`
- **受影響功能**: 所有模型的訪問權限
- **需要測試**:
  - 普通用戶能否切換實例（應該可以）
  - 普通用戶能否查看實體數據（應該可以）
  - 普通用戶能否修改實例配置（應該不行）
  - Manager 能否完整管理實例（應該可以）

---

## High Priority Warnings ⚠️

### 3. API Token 可能在日誌中洩漏

**嚴重程度**: 🟠 High
**位置**: `models/ha_instance.py:346-377`

#### 問題描述

`test_connection()` 方法在日誌中可能打印包含 token 的 payload 或響應。雖然代碼中有 `SENSITIVE_KEYS` 過濾，但在某些錯誤情況下仍可能洩漏。

#### 當前代碼

```python
# models/ha_instance.py:346-377
async def _test_connection_async(self):
    """非同步測試 WebSocket 連線"""
    try:
        # 建立 WebSocket 連線
        websocket = await websockets.connect(
            self.ws_url,
            ping_interval=20,
            ping_timeout=10
        )

        # 發送認證訊息
        auth_payload = {
            'type': 'auth',
            'access_token': self.api_token  # ← 敏感數據
        }
        await websocket.send(json.dumps(auth_payload))

        # 接收認證結果
        auth_result = json.loads(await websocket.recv())
        _logger.info(f"Auth result: {auth_result}")  # ← 可能包含敏感數據

        if auth_result.get('type') != 'auth_ok':
            raise Exception(f"Authentication failed: {auth_result}")

        # 成功後關閉連線
        await websocket.close()
        return True

    except Exception as e:
        _logger.error(f"WebSocket connection test failed: {e}")  # ← 異常訊息可能包含 token
        return False
```

#### 建議修復方案

```python
# models/ha_instance.py
def _sanitize_log_data(self, data):
    """過濾日誌中的敏感數據"""
    if not isinstance(data, dict):
        return data

    SENSITIVE_KEYS = ['access_token', 'api_token', 'token', 'password', 'secret']
    sanitized = {}
    for key, value in data.items():
        if key in SENSITIVE_KEYS:
            sanitized[key] = '***REDACTED***'
        elif isinstance(value, dict):
            sanitized[key] = self._sanitize_log_data(value)
        else:
            sanitized[key] = value
    return sanitized

async def _test_connection_async(self):
    """非同步測試 WebSocket 連線"""
    try:
        # 建立 WebSocket 連線
        websocket = await websockets.connect(
            self.ws_url,
            ping_interval=20,
            ping_timeout=10
        )

        # 發送認證訊息（不記錄）
        auth_payload = {
            'type': 'auth',
            'access_token': self.api_token
        }
        await websocket.send(json.dumps(auth_payload))
        _logger.debug("Sent authentication payload")  # ← 只記錄動作，不記錄內容

        # 接收認證結果
        auth_result = json.loads(await websocket.recv())

        # 過濾敏感數據後記錄
        safe_result = self._sanitize_log_data(auth_result)
        _logger.info(f"Auth result: {safe_result}")

        if auth_result.get('type') != 'auth_ok':
            # 只記錄錯誤類型，不記錄完整響應
            error_type = auth_result.get('type', 'unknown')
            raise Exception(f"Authentication failed: {error_type}")

        await websocket.close()
        return True

    except Exception as e:
        # 確保異常訊息不包含敏感數據
        _logger.error(f"WebSocket connection test failed: {type(e).__name__}")
        _logger.debug(f"Error details: {str(e)}")  # 詳細錯誤只在 DEBUG 級別記錄
        return False
```

#### 額外檢查位置

需要同樣處理的其他位置：

1. `models/common/hass_rest_api.py` - REST API 調用日誌
2. `models/common/hass_websocket_service.py` - WebSocket 服務日誌
3. `controllers/controllers.py` - Controller 錯誤日誌

#### 修復理由

- ✅ 防止 token 在日誌文件中洩漏
- ✅ 符合 GDPR 和數據保護法規
- ✅ 降低內部威脅風險（日誌可能被多人查看）
- ✅ 保持調試能力（DEBUG 級別仍有詳細信息）

---

### 4. Session 失效後未清理用戶偏好設定

**嚴重程度**: 🟠 High
**位置**: `models/common/instance_helper.py:73-86`

#### 問題描述

當 session 中的實例失效時，只清除 session，沒有檢查 `res.users.current_ha_instance_id` 是否也需要更新。這會導致用戶下次登入時再次嘗試使用無效實例。

#### 觸發場景

1. 用戶設定偏好實例 A（儲存在 `res.users.current_ha_instance_id`）
2. 系統將實例 A 設為當前實例（儲存在 `request.session['current_ha_instance_id']`）
3. 管理員刪除或停用實例 A
4. 下次 API 調用時，`HAInstanceHelper.get_current_instance()` 檢測到 session 中的實例失效
5. **問題**: 清除 session 並發送通知，但 `res.users.current_ha_instance_id` 仍指向實例 A
6. 用戶下次登入時，系統會從用戶偏好設定讀取實例 A（Level 2 fallback）
7. 再次檢測失效，進入循環

#### 當前代碼

```python
# models/common/instance_helper.py:73-86
# Level 1: Session
if request and hasattr(request, 'session'):
    session_instance_id = request.session.get('current_ha_instance_id')
    if session_instance_id:
        instance = env['ha.instance'].sudo().browse(session_instance_id)
        if instance.exists() and instance.active and instance.is_configured:
            logger.debug(f"使用 Session 實例: {instance.name} (ID: {instance.id})")
            return instance.id
        else:
            # 實例失效，清除 session
            request.session.pop('current_ha_instance_id', None)
            logger.warning(f"Session 中的實例 (ID: {session_instance_id}) 已失效，已清除")

            # 發送 Bus 通知
            env['ha.realtime.update'].notify_instance_invalidated(
                instance_id=session_instance_id,
                message=f"Session 中的實例已失效"
            )
            # ← 問題: 沒有檢查並清除用戶偏好設定
```

#### 建議修復方案

```python
# models/common/instance_helper.py
# Level 1: Session
if request and hasattr(request, 'session'):
    session_instance_id = request.session.get('current_ha_instance_id')
    if session_instance_id:
        instance = env['ha.instance'].sudo().browse(session_instance_id)
        if instance.exists() and instance.active and instance.is_configured:
            logger.debug(f"使用 Session 實例: {instance.name} (ID: {instance.id})")
            return instance.id
        else:
            # 實例失效，清除 session
            request.session.pop('current_ha_instance_id', None)
            logger.warning(f"Session 中的實例 (ID: {session_instance_id}) 已失效，已清除")

            # **新增**: 檢查並清除用戶偏好設定
            try:
                current_user = env.user
                if current_user.current_ha_instance_id.id == session_instance_id:
                    current_user.sudo().write({'current_ha_instance_id': False})
                    logger.info(
                        f"已清除用戶 '{current_user.name}' 的失效實例偏好設定 "
                        f"(ID: {session_instance_id})"
                    )
            except Exception as e:
                logger.warning(f"清除用戶偏好設定時發生錯誤: {e}")

            # 發送 Bus 通知（增強訊息）
            env['ha.realtime.update'].notify_instance_invalidated(
                instance_id=session_instance_id,
                message=f"您偏好的實例已被停用或刪除，系統將自動選擇其他實例"
            )

# Level 2: 用戶偏好設定（也需要驗證）
user_instance_id = env.user.current_ha_instance_id.id
if user_instance_id:
    instance = env['ha.instance'].sudo().browse(user_instance_id)
    if instance.exists() and instance.active and instance.is_configured:
        # 更新 session 為用戶偏好設定
        if request and hasattr(request, 'session'):
            request.session['current_ha_instance_id'] = instance.id
        logger.debug(f"使用用戶偏好實例: {instance.name} (ID: {instance.id})")
        return instance.id
    else:
        # **新增**: 用戶偏好設定的實例也失效了，清除它
        logger.warning(
            f"用戶 '{env.user.name}' 偏好的實例 (ID: {user_instance_id}) 已失效"
        )
        try:
            env.user.sudo().write({'current_ha_instance_id': False})
            logger.info(f"已清除用戶偏好設定")
        except Exception as e:
            logger.warning(f"清除用戶偏好設定時發生錯誤: {e}")
```

#### 額外改進：前端提示

```javascript
// static/src/services/ha_data_service.js
// 在接收到 instance_invalidated 通知時
this.busSubscriptionCallbacks['instance_invalidated'] = (data) => {
    console.warn('[HaDataService] Instance invalidated:', data);

    // 顯示友好的通知
    this.notificationService.add(
        '您偏好的 Home Assistant 實例已被停用或刪除，系統已自動切換到其他實例。',
        {
            type: 'warning',
            title: '實例已變更',
            sticky: false,
        }
    );

    // 觸發全域回調，讓組件重新加載數據
    this.triggerGlobalCallbacks('instance_invalidated', data);
};
```

#### 修復理由

- ✅ 防止用戶偏好設定永久指向失效實例
- ✅ 避免每次登入都檢測失效的循環
- ✅ 提供更好的用戶體驗（清楚的通知訊息）
- ✅ 保持數據一致性（session 和用戶偏好設定同步）

---

### 5. WebSocket 重連邏輯可能導致服務永久停止

**嚴重程度**: 🟠 High
**位置**: `models/common/hass_websocket_service.py:185-200`

#### 問題描述

當前的重連機制有以下問題：

1. 重試次數有限（5次），超過後 loop 結束，服務永久停止
2. 沒有全域冷卻期（cooldown period），可能在短時間內耗盡重試次數
3. Cron job 每分鐘檢查，但不會重置失敗計數器
4. 如果所有實例都連續失敗 5 次，整個 WebSocket 服務會完全停止

#### 當前代碼

```python
# models/common/hass_websocket_service.py:185-200
async def _run_forever(self):
    """主循環：連接並處理訊息"""
    while self._running and self._consecutive_failures < self._max_retries:
        try:
            async with websockets.connect(
                self._ws_url,
                ping_interval=20,
                ping_timeout=10
            ) as websocket:
                self._websocket = websocket
                self._connected = True
                self._consecutive_failures = 0  # 重置失敗計數

                # 認證
                await self._authenticate(websocket)

                # 訂閱事件
                await self._subscribe_events(websocket)

                # 處理訊息
                await self._message_loop(websocket)

        except Exception as e:
            self._connected = False
            self._consecutive_failures += 1
            _logger.error(
                f"WebSocket error (attempt {self._consecutive_failures}/{self._max_retries}): {e}"
            )

            if self._consecutive_failures < self._max_retries:
                # 指數退避
                delay = min(2 ** self._consecutive_failures, 60)
                await asyncio.sleep(delay)

    # ← 問題: loop 結束後，服務永久停止
    _logger.error("WebSocket service stopped due to max retries exceeded")
```

#### 建議修復方案

```python
# models/common/hass_websocket_service.py

async def _run_forever(self):
    """主循環：連接並處理訊息，帶有全域冷卻期"""

    # 配置參數
    max_retries = 5
    cooldown_period = 600  # 10 分鐘冷卻期

    while self._running:
        try:
            # 檢查是否超過最大重試次數
            if self._consecutive_failures >= max_retries:
                _logger.warning(
                    f"達到最大重試次數 ({max_retries})，進入冷卻期 "
                    f"({cooldown_period} 秒)"
                )

                # 進入冷卻期
                await asyncio.sleep(cooldown_period)

                # 冷卻期結束後，重置計數器
                _logger.info("冷卻期結束，重置失敗計數器並嘗試重新連線")
                self._consecutive_failures = 0
                continue

            # 正常連線邏輯
            async with websockets.connect(
                self._ws_url,
                ping_interval=20,
                ping_timeout=10
            ) as websocket:
                self._websocket = websocket
                self._connected = True
                self._consecutive_failures = 0  # 連線成功，重置計數

                _logger.info(f"WebSocket 連線成功: {self._ws_url}")

                # 認證
                await self._authenticate(websocket)

                # 訂閱事件
                await self._subscribe_events(websocket)

                # 處理訊息（這會阻塞直到連線中斷）
                await self._message_loop(websocket)

        except asyncio.CancelledError:
            # 服務被要求停止
            _logger.info("WebSocket 服務收到停止信號")
            break

        except Exception as e:
            self._connected = False
            self._consecutive_failures += 1

            _logger.error(
                f"WebSocket 錯誤 (嘗試 {self._consecutive_failures}/{max_retries}): "
                f"{type(e).__name__}: {str(e)}"
            )

            if self._consecutive_failures < max_retries:
                # 指數退避（但限制最大延遲為 60 秒）
                delay = min(2 ** self._consecutive_failures, 60)
                _logger.info(f"將在 {delay} 秒後重試...")
                await asyncio.sleep(delay)
            # 如果 >= max_retries，下次迴圈會進入冷卻期

    # 服務正常停止
    _logger.info("WebSocket 服務已停止")
    self._connected = False
```

#### 額外改進：Cron Job 強制重啟

```python
# models/ha_entity.py (或其他合適的位置)

@api.model
def _cron_ensure_websocket_service(self):
    """
    Cron Job: 確保 WebSocket 服務運行
    每分鐘執行一次，檢查服務狀態並在必要時重啟
    """
    try:
        instances = self.env['ha.instance'].sudo().search([
            ('active', '=', True),
            ('is_configured', '=', True)
        ])

        for instance in instances:
            manager = WebSocketThreadManager()

            # 檢查服務狀態
            status = manager.get_service_status(instance.id)

            # 如果服務長時間失敗（例如超過 10 分鐘都是 disconnected）
            # 可以考慮強制重啟
            if status['status'] == 'disconnected':
                # 檢查上次成功連線時間（需要在 WebSocketService 中記錄）
                # 如果超過 10 分鐘沒有成功連線，強制重啟服務
                _logger.warning(
                    f"實例 '{instance.name}' 的 WebSocket 服務長時間斷線，"
                    f"嘗試強制重啟"
                )

                # 停止舊服務
                manager.stop_service(instance.id)

                # 等待 2 秒讓舊服務完全停止
                import time
                time.sleep(2)

                # 啟動新服務（這會重置失敗計數器）
                manager.ensure_service_running(
                    instance.id,
                    instance.ws_url,
                    instance.api_token
                )

                _logger.info(f"已強制重啟實例 '{instance.name}' 的 WebSocket 服務")

    except Exception as e:
        _logger.error(f"Cron Job 執行失敗: {e}", exc_info=True)
```

#### 額外改進：記錄上次成功連線時間

```python
# models/common/hass_websocket_service.py

class HomeAssistantWebSocketService:
    def __init__(self, instance_id, ws_url, api_token):
        # ... 現有代碼 ...
        self._last_successful_connection = None  # 記錄上次成功連線時間

    async def _run_forever(self):
        # ... 在連線成功後 ...
        self._connected = True
        self._consecutive_failures = 0
        self._last_successful_connection = time.time()  # 記錄時間
        _logger.info(
            f"WebSocket 連線成功: {self._ws_url} "
            f"(上次連線: {time.ctime(self._last_successful_connection)})"
        )
```

#### 監控面板改進

在前端顯示更詳細的服務狀態：

```javascript
// static/src/components/websocket_status/websocket_status.js

// 顯示資訊：
// - 狀態: 已連線 / 斷線中 (重試 3/5) / 冷卻期 (剩餘 8:32)
// - 上次成功連線: 2 分鐘前
// - 重試次數: 3/5
// - 下次重試: 8 秒後
```

#### 修復理由

- ✅ 防止服務永久停止，確保長期穩定運行
- ✅ 提供自動恢復能力（冷卻期後重試）
- ✅ 避免短時間內過度重試（指數退避 + 冷卻期）
- ✅ Cron Job 可以檢測並修復長時間失敗的服務
- ✅ 更好的監控和調試能力（記錄上次連線時間）

---

## Medium Priority Warnings 🟡

### 6. 前端 Debounce 機制可能丟失事件

**嚴重程度**: 🟡 Medium
**位置**: `static/src/services/ha_data_service.js:873-930`

#### 問題描述

300ms debounce 期間，只保留最後一次 `instance_switched` 事件數據。如果用戶快速切換 A → B → C，最終只執行 C 的回調，但 B 的切換可能已經更新了 session，導致狀態不一致。

#### 當前代碼

```javascript
// static/src/services/ha_data_service.js:873-930
_setupDebouncedTrigger(eventType, delay = 300) {
    // 儲存 debounced callback
    this.debouncedCallbacks[eventType] = null;

    // 返回 debounced 函數
    return (data) => {
        // 儲存最新的切換數據（覆蓋前一次）← 問題：丟失中間事件
        this.debouncedCallbacks[eventType] = data;

        // 清除之前的 timer
        if (this.debouncedTimers[eventType]) {
            clearTimeout(this.debouncedTimers[eventType]);
        }

        // 設定新的 timer
        this.debouncedTimers[eventType] = setTimeout(() => {
            const latestData = this.debouncedCallbacks[eventType];
            if (latestData) {
                this.triggerGlobalCallbacks(eventType, latestData);
            }
        }, delay);
    };
}
```

#### 建議修復方案

```javascript
// static/src/services/ha_data_service.js

setup() {
    // ... 現有代碼 ...

    // 增加 instance switch 版本控制
    this.instanceSwitchVersion = 0;
    this.latestSwitchVersion = 0;
}

async switchInstance(instanceId) {
    try {
        // 分配新的 switch version
        const switchVersion = ++this.instanceSwitchVersion;
        console.log(`[HaDataService] Switch instance version: ${switchVersion}`);

        // 調用後端 API
        const result = await rpc("/odoo_ha_addon/switch_instance", {
            instance_id: instanceId
        });

        if (result.success) {
            // 更新最新版本號
            this.latestSwitchVersion = switchVersion;

            // 清除快取
            this.clearCache();

            // 顯示成功通知
            this.showSuccess(`已切換到實例: ${result.data.instance_name}`);

            // 觸發全域事件（帶版本號）
            this.triggerGlobalCallbacks('instance_switched', {
                instanceId: result.data.instance_id,
                instanceName: result.data.instance_name,
                switchVersion: switchVersion  // ← 新增版本號
            });

            return result.data;
        } else {
            this.showError(`切換實例失敗: ${result.error}`);
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('[HaDataService] Switch instance failed:', error);
        this.showError('切換實例時發生錯誤');
        throw error;
    }
}

_setupDebouncedTrigger(eventType, delay = 300) {
    // 儲存 debounced callback 和版本號
    this.debouncedCallbacks[eventType] = null;

    return (data) => {
        // 儲存最新的數據和版本號
        this.debouncedCallbacks[eventType] = data;

        // 清除之前的 timer
        if (this.debouncedTimers[eventType]) {
            clearTimeout(this.debouncedTimers[eventType]);
        }

        // 設定新的 timer
        this.debouncedTimers[eventType] = setTimeout(() => {
            const latestData = this.debouncedCallbacks[eventType];
            if (latestData) {
                // **新增**: 版本檢查（只適用於 instance_switched）
                if (eventType === 'instance_switched') {
                    if (latestData.switchVersion !== this.latestSwitchVersion) {
                        console.log(
                            `[HaDataService] Skipping outdated switch event ` +
                            `(version ${latestData.switchVersion}, current ${this.latestSwitchVersion})`
                        );
                        return;
                    }
                }

                // 觸發回調
                this.triggerGlobalCallbacks(eventType, latestData);
            }
        }, delay);
    };
}
```

#### 額外改進：在組件中使用版本號

```javascript
// 組件範例
setup() {
    const haDataService = useService("ha_data");
    const state = useState({ currentSwitchVersion: 0 });

    this.instanceSwitchedHandler = ({ instanceId, instanceName, switchVersion }) => {
        // 檢查版本號，避免處理過期的切換事件
        if (switchVersion < state.currentSwitchVersion) {
            console.log('Ignoring outdated instance switch event');
            return;
        }

        state.currentSwitchVersion = switchVersion;
        console.log(`Instance switched to: ${instanceName} (v${switchVersion})`);

        // 重新載入數據
        this.reloadAllData();
    };

    haDataService.onGlobalState('instance_switched', this.instanceSwitchedHandler);
}
```

#### 修復理由

- ✅ 防止處理過期的切換事件
- ✅ 確保 UI 始終顯示最新實例的數據
- ✅ 避免狀態不一致（session 是 C，但 UI 顯示 B 的數據）
- ✅ 提供更好的調試能力（版本號追蹤）

---

### 7. Cron Job 可能造成數據庫連接池耗盡

**嚴重程度**: 🟡 Medium
**位置**: `hooks.py:217-224` 和 `models/ha_entity.py:484-545`

#### 問題描述

當前的 Cron Job 實現在高並發情況下可能耗盡數據庫連接池。

#### 修復建議

詳細內容省略（字數限制），主要改進：

1. 使用批次處理，減少數據庫連接
2. 加入連接池監控
3. 實現限流機制

---

### 8. 記憶體洩漏風險 - 未清理 Chart 實例

**嚴重程度**: 🟡 Medium
**位置**: 所有使用 Chart.js 的組件

#### 問題描述

需要驗證所有使用圖表的組件是否正確清理 Chart.js 實例。

#### 修復建議

確保所有組件都實現 `willUnmount()` 清理邏輯。

---

### 9. 未處理 WebSocket 消息 ID 衝突

**嚴重程度**: 🟡 Medium
**位置**: `models/common/hass_websocket_service.py:53-54`

#### 問題描述

WebSocket 重連時 message ID 會重置，可能與舊請求衝突。

#### 修復建議

在重連時清理所有 pending requests。

---

## Suggestions 💡

### 10. 增強日誌等級控制

建議統一日誌格式和等級使用。

### 11. 加入 API 速率限制

使用 Odoo 的 rate limiting decorator 保護 API。

### 12. 優化緩存失效策略

使用 LRU cache 和差異化 TTL。

### 13. 加入健康檢查端點

提供 `/odoo_ha_addon/health` 用於監控。

### 14. 改進實例切換用戶體驗

顯示 loading overlay 和進度提示。

### 15. 使用 TypeScript 定義前端接口

提供編譯時類型檢查。

### 16. 實現批次 Service Call

減少 HTTP 請求數量。

### 17. 加入單元測試和集成測試

確保核心功能穩定性。

### 18. 優化數據庫查詢

使用 `search_count()` 替代 `search()`。

### 19. 改進錯誤訊息國際化

使用 Odoo 的 `_()` 翻譯函數。

### 20. 加入性能監控

識別性能瓶頸。

### 21. 前端錯誤邊界處理

使用 ErrorBoundary 組件。

---

## 架構建議

### 1. 考慮引入狀態管理模式

實現 Vuex-like 的狀態管理或簡單的 Store pattern。

### 2. 實現事件溯源模式用於審計

記錄關鍵操作的事件日誌（實例切換、service call）。

### 3. 考慮微服務化 WebSocket 服務

將 WebSocket 服務獨立為單獨的服務，使用 Redis 通信。

### 4. 加入 API 版本控制

在 HTTP endpoints 中加入版本號（`/v1/`, `/v2/`）。

---

## 重構優先級

### P0 - Critical（必須修復）

1. ✅ **移除自動安裝依賴的 subprocess 調用**（安全風險）
   - 影響: 系統安全性
   - 工作量: 1-2 小時
   - 檔案: `hooks.py`, `__manifest__.py`

2. ✅ **加強權限控制**（`ir.model.access.csv` 過於寬鬆）
   - 影響: 數據安全性、多租戶隔離
   - 工作量: 2-3 小時
   - 檔案: `security/ir.model.access.csv`, `security/security.xml`

### P1 - High（應儘快解決）

3. ⚠️ **修復 API token 可能在日誌中洩漏**
   - 影響: 敏感數據保護
   - 工作量: 1-2 小時
   - 檔案: `models/ha_instance.py`, `models/common/hass_rest_api.py`

4. ⚠️ **實現 Session 失效後清理用戶偏好設定**
   - 影響: 用戶體驗、狀態一致性
   - 工作量: 1 小時
   - 檔案: `models/common/instance_helper.py`

5. ⚠️ **改進 WebSocket 重連邏輯**（防止服務永久停止）
   - 影響: 系統穩定性、長期運行能力
   - 工作量: 2-3 小時
   - 檔案: `models/common/hass_websocket_service.py`

### P2 - Medium（計劃中）

6. 🟡 **優化前端 Debounce 機制**（防止狀態不一致）
   - 工作量: 1 小時

7. 🟡 **加入 Cron job 限流機制**（防止連接池耗盡）
   - 工作量: 2 小時

8. 🟡 **驗證並修復 Chart 實例清理**（防止記憶體洩漏）
   - 工作量: 1-2 小時

9. 🟡 **處理 WebSocket 消息 ID 衝突**
   - 工作量: 1 小時

### P3 - Low（改進項目）

10-21. 各種改進項目（詳見 Suggestions 章節）

---

## 總結

### 整體評價

這是一個**架構設計優秀、代碼品質高**的專業項目，展現了：

✅ **優秀的架構設計**
- Session-Based Instance Architecture 清晰合理
- Service Layer Pattern 降低耦合度
- Bus Bridge Pattern 避免重複訂閱
- HAInstanceHelper 統一實例選擇邏輯

✅ **高質量的代碼**
- 錯誤處理完善
- 日誌記錄詳細
- 代碼組織清晰
- 註釋和文檔完整

✅ **良好的工程實踐**
- 統一的 API 響應格式
- WebSocket 重連機制
- 前端緩存策略
- 完整的卸載清理

### 主要需要改進的方面

⚠️ **安全性加固**
- Subprocess 調用風險
- 權限控制過於寬鬆
- Token 洩漏風險

⚠️ **資源管理優化**
- WebSocket 重連邏輯
- 數據庫連接池管理
- 記憶體洩漏預防

⚠️ **容錯性增強**
- 失敗處理機制
- 降級策略
- 監控機制

### 建議行動計劃

#### 第一週（Critical Issues）
- [ ] 移除 subprocess 自動安裝，改用 external_dependencies
- [ ] 重新設計權限模型，創建專用權限組
- [ ] 全面審查日誌，過濾敏感數據

#### 第二週（High Priority）
- [ ] 實現 Session 失效清理機制
- [ ] 改進 WebSocket 重連邏輯（冷卻期 + 強制重啟）
- [ ] 優化前端 Debounce 機制（版本控制）

#### 第三週（Medium Priority + Testing）
- [ ] 加入 Cron job 限流
- [ ] 驗證 Chart 實例清理
- [ ] 處理 WebSocket 消息 ID 衝突
- [ ] 建立單元測試套件
- [ ] 進行完整的安全審計

#### 長期改進（1-3 個月）
- [ ] 實現 API 速率限制
- [ ] 加入健康檢查端點
- [ ] 建立監控和告警系統
- [ ] 考慮微服務化 WebSocket 服務
- [ ] 實現事件溯源和審計日誌

### 特別讚賞 🎉

1. **HAInstanceHelper** - 統一的實例選擇邏輯避免了大量代碼重複
2. **Bus Bridge Pattern** - 展現了對 Odoo Bus 機制的深刻理解
3. **Session-Based Instance** - 架構設計合理，平衡了易用性和可維護性
4. **完整技術文檔** - `docs/tech/` 目錄為團隊協作提供了堅實基礎
5. **Service Layer** - 前端架構清晰，組件與 API 解耦良好

---

## 附錄

### A. 檢查清單

在修復完 Critical 和 High Priority 問題後，使用以下清單驗證：

- [ ] 所有模型的權限符合最小權限原則
- [ ] 日誌中沒有敏感數據（token, password）
- [ ] WebSocket 服務可以從長期失敗中恢復
- [ ] Session 失效後用戶偏好設定會同步清理
- [ ] 前端事件處理使用版本控制，避免過期事件
- [ ] 所有 Chart 組件都實現了清理邏輯
- [ ] 數據庫連接池監控正常
- [ ] API 調用有速率限制保護

### B. 測試建議

#### 安全測試
1. 嘗試用普通用戶賬號查看其他實例的 API token
2. 檢查日誌文件中是否有 token 洩漏
3. 測試 SQL injection 和 XSS 攻擊向量

#### 壓力測試
1. 同時連接 10 個 Home Assistant 實例
2. 快速切換實例（1 秒內切換 5 次）
3. 長時間運行（24 小時）觀察 WebSocket 服務穩定性

#### 用戶體驗測試
1. 刪除用戶當前使用的實例，觀察前端反應
2. WebSocket 斷線時的用戶提示是否友好
3. 實例切換是否流暢，沒有閃爍或錯誤

### C. 相關資源

- **Odoo 18 Security Guide**: https://www.odoo.com/documentation/18.0/developer/reference/backend/security.html
- **WebSocket Best Practices**: https://websockets.readthedocs.io/en/stable/
- **Python Logging**: https://docs.python.org/3/library/logging.html
- **Chart.js Memory Management**: https://www.chartjs.org/docs/latest/developers/api.html

---

**報告結束**

如需進一步分析或針對特定問題的詳細修復計劃，請隨時提出。
