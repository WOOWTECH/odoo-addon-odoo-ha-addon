# Code Review Report: HA Instance Dashboard

**Review Date**: 2025-11-12
**Reviewer**: code-reviewer-pro
**Branch**: feature/ha-instance-dashboard
**Commit Range**: Staged Changes

---

## Executive Summary

### Code Review Summary

整體評估: 這是一個深思熟慮的架構重構，從 session-based implicit instance 模式轉為 explicit instance parameter 模式

- **Critical Issues**: 0 (must fix before merge)
- **Warnings**: 3 (should address) → ✅ **3/3 已修正**
- **Suggestions**: 5 (nice to have) → ✅ **4/5 已實現** (1 項已跳過)
- **Bugs Found**: 1 (discovered during testing) → ✅ **1/1 已修正**

### 修正紀錄 (Fix Log)

**修正日期**: 2025-11-12
**修正狀態**: ✅ **所有 Merge Blockers 和 Highly Recommended 項目已完成**

#### Phase 1: Merge Blockers (Priority 1)
- ✅ **Warning #1**: 修正 Empty State 按鈕功能 - 已新增 `openInstanceSettings()` 方法
- ✅ **Warning #3**: 添加 Instance ID 驗證機制 - Dashboard 和 AreaDashboard 均已實現

#### Phase 2: Highly Recommended (Priority 2)
- ✅ **Warning #2**: 註解 Systray Registry 註冊代碼 - 已註解防止意外啟用
- ✅ **Suggestion #2**: 添加麵包屑導航 - Dashboard 和 AreaDashboard 均已實現
- ✅ **Suggestion #5**: 添加錯誤重試機制 - 入口頁錯誤狀態已新增重試按鈕

#### Phase 3: Nice to Have (Priority 3)
- ✅ **Suggestion #1**: 顯示實例統計資訊 - 已實現（entity_count, area_count, last_sync）
- ✅ **Suggestion #3**: 統一命名約定 - 已將 `area_dashboard` 改為 `ha_area_dashboard`
- ⏭️ **Suggestion #4**: 骨架屏載入效果 - 已跳過（實作成本較高，現有 spinner 已足夠）

#### Bug 修正
- ✅ **Bug #1**: 修正 `dashboard.js` 中 `onWillStart` 未 import 的問題
  - 發現時間：2025-11-12 14:47（測試時觸發前端錯誤）
  - 修正方式：在 owl 解構中添加 `onWillStart`
  - 影響：導致 HA Info 頁面無法載入

**結論**: 所有 Merge Blockers、Highly Recommended 項目和測試發現的 Bug 已完成，程式碼已達到合併標準。

### Changes Overview

這是一個重大的架構重構，從 systray 切換模式改為入口頁導航模式：

1. **新增入口頁** (`ha_instance_dashboard`):
   - 顯示所有 HA Instance 的卡片式瀏覽頁面
   - 每個卡片包含實例資訊和兩個按鈕（HA Info、分區）
   - 通過 `doAction()` 導航並傳遞 `instance_id` 參數

2. **重構現有頁面**:
   - `Dashboard` (HA Info) 和 `AreaDashboard` 現在接收 `instance_id` 參數
   - 移除了 `instance_switched` 事件訂閱
   - 改為傳遞明確的 `instance_id` 參數給 API 呼叫

3. **Systray 組件標記為 DEPRECATED**:
   - 不再使用，但保留檔案供參考
   - 已從 __manifest__.py 中註解掉

4. **菜單結構簡化**:
   - 原本的 "Dashboard" -> "HA Info" + "分區" 子菜單
   - 改為單一 "Dashboard" 入口頁

### Files Changed

```
Changes to be committed:
  modified:   __manifest__.py
  modified:   static/src/actions/area_dashboard/area_dashboard.js
  modified:   static/src/actions/dashboard/dashboard.js
  new file:   static/src/actions/ha_instance_dashboard/ha_instance_dashboard.js
  new file:   static/src/actions/ha_instance_dashboard/ha_instance_dashboard.xml
  modified:   static/src/components/ha_instance_systray/ha_instance_systray.js
  modified:   views/dashboard_menu.xml
  new file:   views/ha_instance_dashboard_action.xml
```

---

## Critical Issues 🚨

**無嚴重問題** - 程式碼品質良好，沒有發現安全漏洞或必須修正的問題。

---

## Warnings ⚠️

### Warning #1: 缺少 Empty State 的實際導航

- **Severity**: High
- **Location**: `static/src/actions/ha_instance_dashboard/ha_instance_dashboard.xml:32`
- **Impact**: 使用者體驗受損 - Empty State 無法引導使用者完成設定

**Problem**:
Empty State 的「新增實例」按鈕使用了 `href="#"`，點擊後不會有任何動作。使用者看到「尚未設定任何實例」時，應該能夠立即前往設定頁面。

**Current Code**:

```xml
<a href="#" class="btn btn-primary mt-3">
  <i class="fa fa-plus me-2"/>
  新增實例
</a>
```

**Suggested Fix**:

```xml
<button
  class="btn btn-primary mt-3"
  t-on-click="() => this.openInstanceSettings()">
  <i class="fa fa-plus me-2"/>
  新增實例
</button>
```

```javascript
// In ha_instance_dashboard.js
openInstanceSettings() {
    this.actionService.doAction({
        type: 'ir.actions.act_window',
        res_model: 'ha.instance',
        views: [[false, 'list'], [false, 'form']],
        name: 'Home Assistant Instances',
        target: 'current',
    });
}
```

---

### Warning #2: Systray 元件未完全移除但仍註冊在 Registry

- **Severity**: Medium
- **Location**: `static/src/components/ha_instance_systray/ha_instance_systray.js:172-177`
- **Impact**: 潛在的維護陷阱 - 可能導致意外啟用已廢棄的功能

**Problem**:
雖然在 `__manifest__.py` 中註解掉了載入路徑，但檔案本身仍然包含 `registry.category("systray").add()` 的註冊代碼。如果未來有人誤刪註解，會導致意外行為（systray 會顯示但功能可能不完整）。

**Current Code**:

```javascript
// 檔案末尾仍有註冊代碼
export const systrayItem = {
    Component: HaInstanceSystray,
};

registry.category("systray").add("ha_instance_systray", systrayItem, { sequence: 2 });
```

**Suggested Fix**:

```javascript
// ⚠️ DEPRECATED: Registry registration is commented out
// If you need to re-enable this component, uncomment the following lines:

// export const systrayItem = {
//     Component: HaInstanceSystray,
// };
//
// registry.category("systray").add("ha_instance_systray", systrayItem, { sequence: 2 });
```

---

### Warning #3: 缺少 Instance ID 驗證機制

- **Severity**: High
- **Location**: `static/src/actions/dashboard/dashboard.js:19` 和 `area_dashboard.js:19`
- **Impact**: 使用者體驗混亂 - 點擊的實例和顯示的數據可能不一致

**Problem**:
當從 `action.context` 接收 `instance_id` 時，沒有驗證該 ID 是否有效（存在且啟用）。如果傳入無效的 ID，後端會 fallback 到 session 或 default instance，但使用者不會收到任何提示。這可能導致困惑：使用者點擊「Instance A」的按鈕，卻看到「Instance B」的數據。

**Current Code**:

```javascript
// 直接接收 instance_id，沒有驗證
this.instanceId = this.props.action?.context?.ha_instance_id || null;
console.log('[WoowHaInfoDashboard] Initialized with instance_id:', this.instanceId);
```

**Suggested Fix**:

```javascript
setup() {
    this.instanceId = this.props.action?.context?.ha_instance_id || null;

    onWillStart(async () => {
        // 驗證 instance_id 是否有效
        if (this.instanceId) {
            const isValid = await this.validateInstanceId(this.instanceId);
            if (!isValid) {
                console.warn('[Dashboard] Invalid instance_id:', this.instanceId);
                this.haDataService.showWarning(
                    '您嘗試存取的實例不存在或已停用，已切換至預設實例'
                );
                this.instanceId = null; // 讓後端使用 fallback
            }
        }

        await Promise.all([...]);
    });
}

async validateInstanceId(instanceId) {
    const result = await this.haDataService.getInstances();
    if (result.success) {
        const instance = result.data.instances.find(inst => inst.id === instanceId);
        return instance && instance.is_active;
    }
    return false;
}
```

---

## Suggestions 💡

### Suggestion #1: 入口頁應顯示實例統計資訊

- **Priority**: Medium
- **Location**: `static/src/actions/ha_instance_dashboard/ha_instance_dashboard.xml:45`
- **Benefit**: 提升資訊豐富度，幫助使用者快速了解實例狀態

**Enhancement**:
卡片目前只顯示基本資訊（URL、描述、狀態）。建議增加實例的統計資訊（實體數量、分區數量、上次同步時間等），讓使用者能快速了解每個實例的活躍度。

**Current Code**:

```xml
<!-- Card Body 只有基本資訊 -->
<div class="card-body">
  <!-- Instance URL -->
  <!-- Instance Description -->
  <!-- Instance Status Info -->
</div>
```

**Suggested Code**:

```xml
<div class="card-body">
  <!-- 現有內容... -->

  <!-- Instance Statistics (NEW) -->
  <div class="mb-3" t-if="instance.statistics">
    <small class="text-muted d-block mb-1">
      <i class="fa fa-bar-chart me-1"/>
      統計資訊
    </small>
    <div class="d-flex gap-3 small">
      <span>
        <i class="fa fa-cube me-1"/>
        <span t-esc="instance.statistics.entity_count"/> 實體
      </span>
      <span>
        <i class="fa fa-map-marker me-1"/>
        <span t-esc="instance.statistics.area_count"/> 分區
      </span>
    </div>
    <small class="text-muted d-block mt-1">
      上次同步: <span t-esc="instance.statistics.last_sync"/>
    </small>
  </div>
</div>
```

```javascript
// In backend controller /odoo_ha_addon/get_instances
'statistics': {
    'entity_count': len(instance.entity_ids),
    'area_count': len(instance.area_ids),
    'last_sync': instance.last_sync_date.strftime('%Y-%m-%d %H:%M') if instance.last_sync_date else 'Never',
}
```

---

### Suggestion #2: 新增麵包屑導航（Breadcrumb）

- **Priority**: High
- **Location**: `static/src/actions/dashboard/dashboard.xml` 和 `area_dashboard.xml`
- **Benefit**: 改善導航體驗，使用者能清楚知道當前位置並快速返回

**Enhancement**:
Dashboard 和 AreaDashboard 頁面應該顯示麵包屑導航，讓使用者知道當前在哪個實例下，並能快速返回入口頁。

**Current Code**:

```xml
<!-- Dashboard 頁面沒有顯示當前實例名稱 -->
<div class="o_ha_dashboard_header">
  <h3>HA Info</h3>
</div>
```

**Suggested Code**:

```xml
<div class="o_ha_dashboard_header bg-white border-bottom p-3 mb-4">
  <!-- Breadcrumb Navigation -->
  <nav aria-label="breadcrumb">
    <ol class="breadcrumb mb-2">
      <li class="breadcrumb-item">
        <a href="#" t-on-click="() => this.goBackToInstances()">
          <i class="fa fa-home me-1"/>
          Instances
        </a>
      </li>
      <li class="breadcrumb-item active" t-if="this.currentInstanceName">
        <span t-esc="this.currentInstanceName"/>
      </li>
      <li class="breadcrumb-item active">HA Info</li>
    </ol>
  </nav>
  <h3 class="mb-0">HA Info Dashboard</h3>
</div>
```

```javascript
// In dashboard.js setup()
this.currentInstanceName = null;

onWillStart(async () => {
    // Load instance name if instanceId is provided
    if (this.instanceId) {
        const result = await this.haDataService.getInstances();
        if (result.success) {
            const instance = result.data.instances.find(inst => inst.id === this.instanceId);
            this.currentInstanceName = instance?.name || 'Unknown';
        }
    }
});

goBackToInstances() {
    this.actionService.doAction({
        type: 'ir.actions.client',
        tag: 'odoo_ha_addon.ha_instance_dashboard',
    });
}
```

---

### Suggestion #3: 統一命名約定

- **Priority**: Low
- **Location**: 多個檔案
- **Benefit**: 提升程式碼可讀性和一致性，便於維護

**Enhancement**:
程式碼中混用了中英文命名（例如 `ha_info_dashboard` vs `area_dashboard`），建議統一使用英文 action tag，中文只用於顯示名稱。

**Current Code**:

```javascript
// dashboard_menu.xml
<menuitem name="Dashboard" id="odoo_ha_addon.dashboard_top_menu" action="odoo_ha_addon.ha_instance_dashboard_action"/>

// ha_instance_dashboard.js
tag: 'odoo_ha_addon.ha_info_dashboard',  // HA Info
tag: 'odoo_ha_addon.area_dashboard',      // 分區
```

**Suggested Code**:

```javascript
// 統一 action tag 命名模式
tag: 'odoo_ha_addon.ha_info_dashboard',     // 保持
tag: 'odoo_ha_addon.ha_area_dashboard',     // 改為 ha_area_dashboard（加上 ha_ 前綴）
tag: 'odoo_ha_addon.ha_instance_dashboard', // 保持
```

---

### Suggestion #4: 增加載入骨架屏（Skeleton Loading）

- **Priority**: Low
- **Location**: `static/src/actions/ha_instance_dashboard/ha_instance_dashboard.xml:16-19`
- **Benefit**: 更好的視覺回饋，使用者感知載入速度更快

**Enhancement**:
目前載入狀態只顯示 spinner 和文字，建議使用骨架屏（Skeleton Screen）提升視覺體驗。

**Current Code**:

```xml
<div t-if="state.loading" class="text-center py-5">
  <i class="fa fa-spinner fa-spin fa-3x text-muted"/>
  <p class="mt-3 text-muted">載入實例列表中...</p>
</div>
```

**Suggested Code**:

```xml
<div t-if="state.loading" class="o_ha_instance_cards">
  <div class="container-fluid">
    <div class="row">
      <!-- Skeleton Cards -->
      <t t-foreach="[1, 2, 3]" t-as="skeleton" t-key="skeleton">
        <div class="col-12 col-md-6 col-lg-4 mb-4">
          <div class="card h-100 shadow-sm">
            <div class="card-header bg-light">
              <div class="placeholder-glow">
                <span class="placeholder col-6"></span>
              </div>
            </div>
            <div class="card-body">
              <div class="placeholder-glow">
                <span class="placeholder col-12 mb-2"></span>
                <span class="placeholder col-8"></span>
              </div>
            </div>
            <div class="card-footer">
              <div class="placeholder-glow">
                <span class="placeholder col-12"></span>
              </div>
            </div>
          </div>
        </div>
      </t>
    </div>
  </div>
</div>
```

---

### Suggestion #5: 新增錯誤重試機制

- **Priority**: Medium
- **Location**: `static/src/actions/ha_instance_dashboard/ha_instance_dashboard.js:56`
- **Benefit**: 改善錯誤處理體驗，減少使用者挫折感

**Enhancement**:
當載入失敗時，目前只顯示錯誤訊息，建議新增「重試」按鈕讓使用者能快速重新載入。

**Current Code**:

```javascript
} catch (error) {
    this.state.error = error.message || '載入失敗';
    console.error('[HaInstanceDashboard] Error loading instances:', error);
}
```

```xml
<div t-elif="state.error" class="alert alert-danger m-3" role="alert">
  <i class="fa fa-exclamation-triangle me-2"/>
  <strong>錯誤：</strong>
  <span t-esc="state.error"/>
</div>
```

**Suggested Code**:

```xml
<div t-elif="state.error" class="alert alert-danger m-3" role="alert">
  <div class="d-flex justify-content-between align-items-center">
    <div>
      <i class="fa fa-exclamation-triangle me-2"/>
      <strong>錯誤：</strong>
      <span t-esc="state.error"/>
    </div>
    <button class="btn btn-sm btn-outline-danger" t-on-click="() => this.loadInstances()">
      <i class="fa fa-refresh me-1"/>
      重試
    </button>
  </div>
</div>
```

---

## Testing Recommendations

### 1. 基本功能測試

**入口頁載入**
- [ ] 開啟 Dashboard 選單，應顯示 HA Instance 入口頁
- [ ] 卡片應正確顯示所有啟用的實例
- [ ] WebSocket 狀態圖示應正確顯示（connected/disconnected）
- [ ] 已停用的實例按鈕應該是 disabled 狀態

**導航測試**
- [ ] 點擊「HA Info」按鈕應跳轉到該實例的 HA Info 頁面
- [ ] 點擊「分區」按鈕應跳轉到該實例的分區頁面
- [ ] 頁面標題應正確顯示實例名稱（例如「HA Info - 主宅」）

**Instance ID 傳遞**
- [ ] Dashboard 頁面應載入正確實例的數據（檢查 hardware_info）
- [ ] AreaDashboard 頁面應載入正確實例的分區列表
- [ ] Console log 應顯示正確的 `instance_id` 參數

### 2. 邊界情況測試

**Empty State**
- [ ] 沒有任何實例時，應顯示「尚未設定任何實例」訊息
- [ ] 點擊「新增實例」按鈕應能導航到設定頁面（修正 Warning #1 後）

**錯誤處理**
- [ ] 後端 API 失敗時，應顯示錯誤訊息
- [ ] 傳入無效的 `instance_id` 時，應 fallback 到 default instance
- [ ] 所有實例都停用時，應顯示適當提示

**多實例切換**
- [ ] 開啟實例 A 的 HA Info 頁面
- [ ] 返回入口頁
- [ ] 開啟實例 B 的 HA Info 頁面
- [ ] 數據應正確切換（不應顯示實例 A 的快取數據）

### 3. 向後相容性測試

**Systray 移除**
- [ ] 頂部導覽列不應顯示 HA Instance Systray 組件
- [ ] 現有的 systray 功能（如公司切換器）應正常運作
- [ ] 不應有任何 JavaScript 錯誤

**Session Fallback**
- [ ] 直接呼叫 `/odoo_ha_addon/hardware_info`（不帶 instance_id）應使用 session fallback
- [ ] Standard List Views（Entity/Group/History）應仍然正常運作
- [ ] 其他不使用 instance_id 的舊功能應不受影響

### 4. 效能測試

**多實例情境**
- [ ] 10+ 個實例時，入口頁應流暢載入
- [ ] 卡片網格應正確 responsive（手機/平板/桌面）
- [ ] 不應有明顯的記憶體洩漏（開啟/關閉頁面多次）

**API 快取**
- [ ] `getInstances()` 應使用 HaDataService 的快取機制
- [ ] 短時間內多次開啟入口頁，不應重複呼叫 API

### 5. UI/UX 測試

**響應式設計**
- [ ] 手機版（<768px）：卡片應單欄顯示
- [ ] 平板版（768px-992px）：卡片應兩欄顯示
- [ ] 桌面版（>992px）：卡片應三欄顯示

**視覺一致性**
- [ ] 卡片樣式應與 Odoo 18 設計語言一致
- [ ] Icon 使用應符合 Font Awesome 4.x 規範
- [ ] 顏色應符合 Bootstrap 主題（badge/button）

---

## Strengths ✅

### 1. 架構設計清晰
- 明確的參數傳遞機制（透過 `action.context`）
- 移除隱式依賴（session-based instance），提升可預測性
- 入口頁模式更符合多實例瀏覽的使用情境

### 2. 程式碼品質優秀
- 詳細的註解說明變更原因和影響
- 一致的 console.log 格式便於調試
- 正確的生命週期管理（移除 `instance_switched` 訂閱）

### 3. 向後相容考量周全
- Systray 元件標記為 DEPRECATED 但保留檔案
- 後端 API 仍支援 fallback 機制（`instanceId` 為 null 時）
- 現有的 session-based 功能不受影響

### 4. UI/UX 設計良好
- 卡片式設計直觀易用
- 清楚的狀態指示（Loading/Error/Empty）
- 響應式佈局（Bootstrap Grid）

### 5. 文檔完善
- JSDoc 註解清楚說明方法用途
- DEPRECATED 標記明確
- 變更原因在註解中解釋（`⚠️ Instance Selection (Updated)`）

---

## Overall Assessment

### Recommendation: 有條件合併（Conditional Merge）

這是一個精心設計的架構重構，程式碼品質高，沒有嚴重問題。但建議在合併前處理以下項目：

#### 必須處理（Merge Blockers）
1. ⚠️ **Warning #1**: 修正 Empty State 的「新增實例」按鈕功能
2. ⚠️ **Warning #3**: 新增 Instance ID 驗證機制（避免使用者困惑）

#### 強烈建議處理（Highly Recommended）
3. ⚠️ **Warning #2**: 註解掉 Systray 的 registry 註冊代碼
4. 💡 **Suggestion #2**: 新增麵包屑導航（顯著提升 UX）
5. 💡 **Suggestion #5**: 新增錯誤重試機制

#### 可選處理（Nice to Have）
6. 💡 **Suggestion #1**: 顯示實例統計資訊
7. 💡 **Suggestion #3**: 統一命名約定
8. 💡 **Suggestion #4**: 骨架屏載入效果

---

## Additional Recommendations

### 1. 更新技術文檔

請更新 `CLAUDE.md` 和相關技術文檔，說明新的導航模式：

```markdown
### Navigation Architecture (Updated in v3.1)

**Entry Page Pattern**: The addon uses an Entry Page pattern for multi-instance navigation:

1. User opens "Dashboard" menu → Shows HA Instance Dashboard (entry page)
2. Entry page displays all instances as cards
3. User clicks "HA Info" or "Areas" button → Opens detail page with `instance_id` in context
4. Detail pages receive `instance_id` via `action.context.ha_instance_id`
5. All API calls pass explicit `instance_id` parameter

**Key Differences from Previous Version**:
- ❌ No systray instance switcher
- ❌ No global `instance_switched` event
- ✅ Explicit instance selection via entry page
- ✅ Instance ID passed through action context
- ✅ Each page shows data for specific instance only
```

### 2. 考慮 Migration Path

如果有使用者習慣使用 systray 切換器，建議提供過渡期的通知：

```javascript
// In HaInstanceSystray (if re-enabled temporarily)
setup() {
    // Show deprecation notice
    this.haDataService.showWarning(
        'Systray 實例切換器已停用，請使用 Dashboard 選單選擇實例',
        { sticky: true }
    );
}
```

### 3. 新增單元測試

建議為新的 `HaInstanceDashboard` 元件新增測試：

```javascript
// tests/ha_instance_dashboard_tests.js
QUnit.module('HaInstanceDashboard');

QUnit.test('should load instances on mount', async (assert) => {
    const dashboard = new HaInstanceDashboard();
    await dashboard.setup();
    assert.ok(dashboard.state.instances.length > 0);
});

QUnit.test('should navigate to HA Info with correct context', async (assert) => {
    const dashboard = new HaInstanceDashboard();
    const mockAction = { context: { ha_instance_id: 123 } };
    dashboard.openHaInfo(123, 'Test Instance');
    assert.equal(mockAction.context.ha_instance_id, 123);
});
```

---

## Action Items Summary

### Critical (Must Fix) ✅ 2/2 完成
- [x] **Fix Empty State "Add Instance" button navigation** - Phase 1.1 已修正
- [x] **Add Instance ID validation in Dashboard and AreaDashboard** - Phase 1.2 已實現

### High Priority (Should Fix) ✅ 3/3 完成
- [x] **Comment out Systray registry registration code** - Phase 2.1 已註解
- [x] **Add breadcrumb navigation to detail pages** - Phase 2.2 已實現（Dashboard + AreaDashboard）
- [x] **Add retry button for error states** - Phase 2.3 已實現（入口頁錯誤狀態）

### Medium Priority (Nice to Have) ✅ 2/3 完成
- [x] **Display instance statistics in cards** - Phase 3.1 已實現（entity_count, area_count, last_sync）
- [x] **Unify naming conventions across action tags** - Phase 3.2 已實現（ha_area_dashboard）
- [ ] **Implement skeleton loading screens** - Phase 3.3 已跳過（spinner 已足夠）

### Documentation ⏳ 待處理
- [ ] Update CLAUDE.md with new navigation pattern
- [ ] Add migration guide for systray deprecation
- [ ] Create unit tests for HaInstanceDashboard

---

**Review Completed**: 2025-11-12
**Fix Completed**: 2025-11-12 ✅
**Status**: ✅ **Ready for Merge** - All merge blockers and high-priority items addressed

**修正檔案列表** (11 個檔案):

**前端修正 (7 個)**:
- `ha_instance_dashboard.js` - 新增 `openInstanceSettings()` 方法
- `ha_instance_dashboard.xml` - 修正 Empty State 按鈕、添加錯誤重試按鈕、統計資訊顯示
- `dashboard.js` - 新增 Instance ID 驗證、麵包屑導航、`goBackToInstances()` 方法、**修正 onWillStart import**
- `dashboard.xml` - 添加麵包屑導航區塊
- `area_dashboard.js` - 新增 Instance ID 驗證、麵包屑導航、registry tag 更新為 `ha_area_dashboard`
- `area_dashboard.xml` - 添加麵包屑導航區塊、template 名稱更新
- `area_dashboard_views.xml` - action tag 更新為 `ha_area_dashboard`

**Systray 移除 (1 個)**:
- `ha_instance_systray.js` - 註解 registry 註冊代碼

**後端修正 (2 個)**:
- `ha_instance.py` - 新增 `area_count` 計算欄位和 `_compute_area_count()` 方法
- `controllers.py` - `/get_instances` API 回傳完整統計資訊

**文件更新 (1 個)**:
- `code-review/ha-instance-dashboard.md` - 本報告

### Bug 修正紀錄

#### Bug #1: onWillStart 未 Import 導致前端錯誤 ✅

**發現時間**: 2025-11-12 14:47
**錯誤訊息**:
```
OwlError: An error occured in the owl lifecycle
Caused by: ReferenceError: onWillStart is not defined
    at WoowHaInfoDashboard.setup (dashboard.js:...)
```

**問題原因**:
在 Phase 1.2 和 2.2 修正中，我們在 `dashboard.js` 的 `setup()` 方法中使用了 `onWillStart()` 來進行 Instance ID 驗證和實例名稱載入，但忘記從 `owl` 中 import 該方法。

**受影響代碼**:
```javascript
// ❌ 錯誤的 import（缺少 onWillStart）
const { Component, useState, onMounted, onWillUnmount } = owl;

// 但在 setup() 中使用了 onWillStart
onWillStart(async () => {
    if (this.instanceId && !this.instanceValidated) {
        // ... validation logic
    }
});
```

**修正方案**:
```javascript
// ✅ 正確的 import（包含 onWillStart）
const { Component, useState, onMounted, onWillUnmount, onWillStart } = owl;
```

**影響範圍**:
- `dashboard.js` (WoowHaInfoDashboard) ✅ 已修正
- `area_dashboard.js` (AreaDashboard) ✅ 無問題（使用新 import 語法）

**經驗教訓**:
1. 在使用 OWL lifecycle hooks 時，務必檢查 import 語句
2. `area_dashboard.js` 使用了新的 import 語法（`import { ... } from "@odoo/owl"`），自動包含了所需的 hooks
3. `dashboard.js` 使用舊的解構語法（`const { ... } = owl`），需要手動添加每個使用的 hook

**測試驗證**:
- [x] 瀏覽器刷新後，點擊實例卡片的「HA Info」按鈕
- [x] 確認頁面正常載入，無 JavaScript 錯誤
- [x] 確認 Instance ID 驗證功能正常
- [x] 確認麵包屑導航顯示實例名稱
