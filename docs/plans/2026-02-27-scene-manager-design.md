# Scene Manager - 情境管理模組設計文件

**Created:** 2026-02-27T06:41:11Z
**Status:** Draft
**Author:** Claude Code Assistant (Collaborative)

---

## 1. 概述與目標

### 功能名稱
**Scene Manager** - 情境管理模組

### 位置
WOOW Dashboard → Configuration → Scene

### 目標
讓使用者在 Odoo 中統一管理 Home Assistant 的 Scene（情境），包括：
1. 檢視所有 Scene（從 HA 同步）
2. 建立新 Scene 並同步到 HA
3. 編輯任何 Scene 的實體清單
4. 刪除 Scene

### 核心行為
- **統一管理**：所有 Scene 都可以檢視、編輯、執行、刪除
- **立即同步**：儲存時立即同步到 HA，使用所選實體的當前狀態（snapshot）
- **繼承現有 Entity**：Scene 繼承自 `ha.entity`（domain='scene'），在表單下方新增 Tab 管理實體清單

---

## 2. 資料模型

### 方案：擴展現有 `ha.entity` 模型

由於 Scene 本身就是 `ha.entity`（domain='scene'），不需要建立新模型，而是擴展現有模型：

### 新增欄位

```python
# 在 ha.entity 模型中新增，僅適用於 domain='scene' 的 entity
scene_entity_ids = fields.Many2many(
    'ha.entity',
    'ha_scene_entity_rel',
    'scene_id',
    'entity_id',
    string='Scene Entities',
    domain="[('ha_instance_id', '=', ha_instance_id), ('domain', '!=', 'scene')]",
    help='Entities included in this scene'
)

scene_entity_count = fields.Integer(
    string='Entity Count',
    compute='_compute_scene_entity_count',
    help='Number of entities in this scene'
)
```

### 關聯表
- **Table**: `ha_scene_entity_rel`
- **Columns**: `scene_id`, `entity_id`
- **Purpose**: 儲存 Scene 與其包含實體的關係

### 優點
- 不需要新模型，減少複雜度
- 利用現有的 Entity 同步機制
- Scene 繼承所有 Entity 的功能（執行、分享等）

---

## 3. UI 設計

### 3.1 選單入口

在 Configuration 選單下新增 "Scene"：

```
Configuration
├── HA Instances
├── Scene              ← 新增
├── Entity Tag
├── Entity Group Tag
├── Device Tag
├── Setting
```

### 3.2 列表視圖 (List View)

顯示所有 domain='scene' 的 Entity：

| 欄位 | 說明 |
|------|------|
| Name | Scene 名稱 |
| Entity ID | 如 `scene.movie_mode` |
| Area | 所屬區域 |
| Entity Count | 包含的實體數量 |
| State | 狀態（可執行 Activate 按鈕）|

### 3.3 表單視圖 (Form View)

繼承現有 Entity Form，在下方新增 Tab：

```
┌─────────────────────────────────────────────┐
│ [Scene Name]                    [Activate]  │
├─────────────────────────────────────────────┤
│ Entity ID: scene.xxx                        │
│ Area: [Living Room ▼]                       │
│ State: on                                   │
├─────────────────────────────────────────────┤
│ [General] [Scene Entities] [History] [...]  │
├─────────────────────────────────────────────┤
│ Scene Entities (新增的 Tab)                  │
│ ┌─────────────────────────────────────────┐ │
│ │ + Add  ⊕ Add Multiple                   │ │
│ │ ☑ light.living_room      Living Room   │ │
│ │ ☑ switch.tv_power        Entertainment │ │
│ │ ☑ cover.curtain          Living Room   │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 3.4 新增 Scene 流程

1. 點擊「Create」按鈕
2. 填寫 Scene 名稱
3. 在「Scene Entities」Tab 選擇要包含的實體
4. 儲存 → 立即在 HA 建立 Scene（使用所選實體的當前狀態）

---

## 4. 同步機制

### 4.1 HA → Odoo 同步（讀取）

- 現有的 Entity 同步機制已會同步 domain='scene' 的實體
- **新增**：同步時從 HA 取得 Scene 包含的實體清單，更新 `scene_entity_ids`

### 4.2 Odoo → HA 同步（寫入）

#### 建立新 Scene

```python
# 呼叫 HA scene.create 服務
service_data = {
    "domain": "scene",
    "service": "create",
    "service_data": {
        "scene_id": "movie_mode",  # 從 name 轉換
        "snapshot_entities": [
            "light.living_room",
            "switch.tv_power",
            "cover.curtain"
        ]
    }
}
```

#### 更新 Scene

- 刪除舊 Scene → 建立新 Scene
- HA 的 `scene.create` 會覆蓋同名 Scene

#### 刪除 Scene

```python
# 呼叫 HA scene.delete 服務
service_data = {
    "domain": "scene",
    "service": "delete",
    "target": {
        "entity_id": "scene.movie_mode"
    }
}
```

### 4.3 執行 Scene（Activate）

使用現有的 Entity Controller 機制：

```python
# 呼叫 HA scene.turn_on 服務
service_data = {
    "domain": "scene",
    "service": "turn_on",
    "target": {
        "entity_id": "scene.movie_mode"
    }
}
```

---

## 5. 實作步驟

### Phase 1: 資料模型擴展
- [ ] 在 `ha.entity` 新增 `scene_entity_ids` 欄位
- [ ] 新增 `scene_entity_count` 計算欄位（顯示實體數量）
- [ ] 建立資料庫關聯表 `ha_scene_entity_rel`

### Phase 2: 視圖建立
- [ ] 建立 Scene 專用 Action（過濾 domain='scene'）
- [ ] 建立 Scene List View
- [ ] 擴展 Entity Form View，新增「Scene Entities」Tab
- [ ] 在 Configuration 選單新增 Scene 入口

### Phase 3: 同步邏輯（Odoo → HA）
- [ ] 實作 `create_scene_in_ha()` 方法 - 呼叫 `scene.create` 服務
- [ ] 實作 `update_scene_in_ha()` 方法 - 更新 Scene 實體清單
- [ ] 實作 `delete_scene_in_ha()` 方法 - 刪除 Scene
- [ ] 覆寫 `write()` 和 `unlink()` 方法觸發同步

### Phase 4: HA → Odoo 同步
- [ ] 從 HA 取得 Scene 的實體清單（使用 Scene attributes）
- [ ] 在 Entity 同步時更新 `scene_entity_ids`

### Phase 5: 測試與部署
- [ ] 單元測試：建立/編輯/刪除 Scene
- [ ] 整合測試：驗證雙向同步
- [ ] 部署到容器測試

---

## 6. 技術參考

### Home Assistant Scene API

**建立 Scene（snapshot 模式）：**
```yaml
service: scene.create
data:
  scene_id: my_scene
  snapshot_entities:
    - light.living_room
    - switch.tv
```

**執行 Scene：**
```yaml
service: scene.turn_on
target:
  entity_id: scene.my_scene
```

**刪除 Scene：**
```yaml
service: scene.delete
target:
  entity_id: scene.my_scene
```

### 相關文件
- [Home Assistant Scenes Documentation](https://www.home-assistant.io/docs/scene/)
- [Home Assistant WebSocket API](https://developers.home-assistant.io/docs/api/websocket/)

---

## 7. 未來擴展（Out of Scope）

以下功能不在本次實作範圍，可作為未來優化：
- 完整狀態設定模式（為每個實體設定具體狀態值）
- Scene 分組/分類管理
- Scene 執行歷史記錄
- Scene 排程執行
