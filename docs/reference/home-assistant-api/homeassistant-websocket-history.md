# homeassistant websocket history 串接

取得 `fan.test_fan` history

## 核心欄位說明

### `last_changed` vs `last_updated` 差異

在 Home Assistant 的歷史資料中，`last_changed` 和 `last_updated` 是兩個重要的時間戳欄位，理解它們的差異對於正確處理歷史資料至關重要。

#### 欄位定義

| 欄位 | 更新時機 | 說明 |
|------|---------|------|
| **`last_updated`** | 狀態或屬性變更時 | 當實體的**狀態值**或**任何屬性**被寫入狀態機時都會更新（UTC 時區） |
| **`last_changed`** | 僅狀態值變更時 | **僅**當實體的**狀態值本身**改變時才會更新，屬性變更不影響此欄位（UTC 時區） |

#### 實際範例

假設有一個氣候感測器實體，狀態是「溫度」，屬性包含「濕度」：

| 情況 | last_changed | last_updated |
|------|--------------|--------------|
| 溫度改變，濕度改變 | ✅ 更新 | ✅ 更新 |
| 溫度不變，濕度改變 | ❌ 不更新 | ✅ 更新 |
| 溫度改變，濕度不變 | ✅ 更新 | ✅ 更新 |
| 兩者都不變 | ❌ 不更新 | ❌ 不更新 |

#### 應用場景

- **`last_changed`**: 適合追蹤「狀態真正改變」的時間點
  - 範例：開關從 `off` 變成 `on`
  - 範例：感測器數值從 `22.5` 變成 `23.0`

- **`last_updated`**: 適合監控「實體是否還活著」
  - 範例：RF 433 MHz 感測器是否持續回傳數據
  - 範例：即使溫度值未變，但濕度屬性有更新

#### 資料庫儲存優化

Home Assistant 在資料庫層級有空間優化策略：

```python
# 案例 1: 燈泡從 off 變 on（狀態改變）
{
    "state": "on",
    "last_updated_ts": 1729500000.123,
    "last_changed_ts": NULL  # 儲存為 NULL（因為與 last_updated 相同）
}

# 案例 2: 燈泡只改變顏色，state 仍是 on（僅屬性改變）
{
    "state": "on",
    "last_updated_ts": 1729500060.456,  # 更新
    "last_changed_ts": NULL              # 保持 NULL（state 沒變）
}
```

**優化邏輯**：
- 當 `last_changed_ts == last_updated_ts` 時，`last_changed_ts` 儲存為 `NULL`
- 節省約 8 bytes（FLOAT 型別）per record
- 查詢時使用 `COALESCE(last_changed_ts, last_updated_ts)` 取得實際值

#### 注意事項

⚠️ **已知限制**：當 Home Assistant 重啟時，這兩個時間戳會被重置為當前時間，這是一個長期存在的設計限制。

#### 參考資料

- [Home Assistant Community: Difference between "Last Changed" and "Last Updated"](https://community.home-assistant.io/t/difference-between-last-changed-and-last-updated-if-any/527999)
- [Official Documentation: State Objects](https://developers.home-assistant.io/docs/core/entity/state/)

## API 說明

### `recorder/statistics_during_period`

此 API 用於查詢感測器在特定時段內的**歷史統計資料**（如平均值、最小值、最大值、總和等）。

#### 功能特點

- 查詢指定時間範圍內的統計數據
- 支援多種時間粒度（5 分鐘、小時、日、週、月）
- 可進行單位轉換（距離、能量、質量、功率、壓力、速度、溫度、體積等）
- 返回資料包含時間戳和統計值

#### 參數說明

| 參數            | 類型   | 必填 | 說明                                                          |
| --------------- | ------ | ---- | ------------------------------------------------------------- |
| `type`          | string | ✓    | 固定值：`"recorder/statistics_during_period"`                 |
| `start_time`    | string | ✓    | 開始時間（ISO 8601 格式）                                     |
| `end_time`      | string | ✗    | 結束時間（ISO 8601 格式），未指定則使用當前時間               |
| `statistic_ids` | array  | ✓    | 統計 ID 列表（如 `["sensor.temperature"]`）                   |
| `period`        | string | ✓    | 時段粒度：`"5minute"`, `"hour"`, `"day"`, `"week"`, `"month"` |
| `types`         | array  | ✗    | 統計類型：`"mean"`, `"min"`, `"max"`, `"sum"`, `"state"` 等   |
| `units`         | object | ✗    | 單位轉換對應字典                                              |

#### 返回資料結構

返回包含統計資料的字典，每筆資料包含：

- 開始/結束時間戳（**毫秒**，自 Unix epoch 起的整數，可直接傳給 JavaScript `Date()` 建構函數）
- 統計值（依 `types` 參數決定）
- 若包含 `last_reset` 類型，該欄位也會轉換為毫秒時間戳

**範例**（sensor.temperature 的返回）：

```json
{
  "sensor.temperature": [
    {
      "start": 1729500000000, // 毫秒時間戳（13位整數）
      "end": 1729503600000,
      "mean": 22.5,
      "min": 20.0,
      "max": 25.0,
      "state": 22.5
    }
  ]
}
```

**注意**：`fan.test_fan` 因為沒有 `state_class`，所以返回空物件 `{}`

#### 使用案例

- **能源監控**：查詢過去一個月的能源消耗統計
- **溫度追蹤**：查詢一週內的溫度變化趨勢
- **儀表板統計卡片**：在 Home Assistant 前端顯示歷史統計圖表

#### 注意事項

⚠️ **此 API 未出現在官方 WebSocket API 文件中**

- 僅在開發者 blog（2022/09/29）中有簡短提及
- 沒有穩定的 API 規範保證
- 建議謹慎使用，並準備好應對未來可能的破壞性變更

#### 參考來源

- **Source Code**: [homeassistant/components/recorder/websocket_api.py](https://github.com/home-assistant/core/blob/dev/homeassistant/components/recorder/websocket_api.py)
- **Pull Request**: [Add WS API recorder/statistic_during_period #80663](https://github.com/home-assistant/core/pull/80663)
- **開發者 Blog**: [Statistics Refactoring (2022/09/29)](https://developers.home-assistant.io/blog/2022/09/29/statistics_refactoring/)

### `history/history_during_period`

此 API 用於**一次性查詢實體在特定時段內的歷史狀態變化**，從資料庫 states 表中檢索完整解析度的狀態資料。

#### 功能特點

- **完整解析度資料**：返回所有狀態變化，包含完整屬性
- **一次性查詢**：單次請求-回應模式，不建立持續連線
- **資料來源**：僅從資料庫 states 表查詢
- **資料保留期**：受限於 Recorder 保留期限（預設 10 天）

#### 參數說明

| 參數                       | 類型    | 必填 | 預設值 | 說明                                         |
| -------------------------- | ------- | ---- | ------ | -------------------------------------------- |
| `type`                     | string  | ✓    | -      | 固定值：`"history/history_during_period"`    |
| `start_time`               | string  | ✓    | -      | 開始時間（ISO 8601 格式）                    |
| `end_time`                 | string  | ✗    | -      | 結束時間（ISO 8601 格式）                    |
| `entity_ids`               | array   | ✓    | -      | 實體 ID 列表（如 `["sensor.temperature"]`）  |
| `include_start_time_state` | boolean | ✗    | true   | 是否包含開始時間的狀態                       |
| `significant_changes_only` | boolean | ✗    | true   | 僅包含顯著變化（過濾微小波動）               |
| `minimal_response`         | boolean | ✗    | false  | 最小化回應，只返回 `last_changed` 和 `state` |
| `no_attributes`            | boolean | ✗    | false  | 不返回 attributes，大幅提升效能              |

#### 返回資料結構

返回 JSON 格式的顯著狀態字典：

```json
{
  "sensor.temperature": [
    {
      "state": "22.5",
      "last_changed": "2025-10-20T10:53:17.057Z",
      "last_updated": "2025-10-20T10:53:17.057Z",
      "attributes": {
        "unit_of_measurement": "°C",
        "friendly_name": "溫度"
      }
    }
  ]
}
```

#### 使用案例

- **歷史圖表**：繪製指定時段內的狀態變化圖表
- **資料分析**：分析近期（10 天內）的詳細狀態變化
- **問題排查**：檢視特定時段內的狀態轉換
- **報表生成**：產生短期內的狀態變化報表

#### 注意事項

- 查詢時間範圍受限於 Recorder 的資料保留期限（預設 10 天）
- 查詢大量資料或長時間範圍可能影響效能
- 使用 `minimal_response` 和 `no_attributes` 可提升查詢速度
- 若需要長期歷史資料，應使用 `recorder/statistics_during_period`

#### 參考來源

- **Source Code**: [homeassistant/components/history/websocket_api.py](https://github.com/home-assistant/core/blob/dev/homeassistant/components/history/websocket_api.py)
- **官方文件**: [History Integration](https://www.home-assistant.io/integrations/history/)
- **資料庫架構**: [Understanding Home Assistant's Database Model](https://smarthomescene.com/blog/understanding-home-assistants-database-and-statistics-model/)

### `history/stream`

此 API 用於**即時串流實體的歷史狀態變化**，支援歷史資料查詢與即時更新的混合模式。

#### 功能特點

- **即時串流**：當 `end_time` 為未來時間，會持續推送狀態變化
- **歷史回放**：當 `end_time` 已過去，只返回歷史資料
- **效能優化**：支援最小化回應模式，減少資料傳輸量
- **Live 更新**：圖表和儀表板會即時更新，無需重新查詢資料庫

#### 參數說明

| 參數                       | 類型    | 必填 | 預設值   | 說明                                         |
| -------------------------- | ------- | ---- | -------- | -------------------------------------------- |
| `type`                     | string  | ✓    | -        | 固定值：`"history/stream"`                   |
| `start_time`               | string  | ✓    | -        | 開始時間（ISO 8601 格式）                    |
| `end_time`                 | string  | ✗    | 當前時間 | 結束時間（ISO 8601 格式）                    |
| `entity_ids`               | array   | ✓    | -        | 實體 ID 列表（如 `["sensor.temperature"]`）  |
| `include_start_time_state` | boolean | ✗    | true     | 是否包含開始時間的狀態                       |
| `significant_changes_only` | boolean | ✗    | true     | 僅包含顯著變化（過濾微小波動）               |
| `minimal_response`         | boolean | ✗    | false    | 最小化回應，只返回 `last_changed` 和 `state` |
| `no_attributes`            | boolean | ✗    | false    | 不返回 attributes，大幅提升效能              |

#### 工作原理

1. **兩階段處理**：

   - 若 `end_time` 已過去：僅發送歷史資料後結束連線
   - 若 `end_time` 為未來：先發送歷史資料，再建立即時訂閱

2. **即時監聽**：

   - 設置事件佇列監聽狀態變化
   - 持續處理新事件並推送至 WebSocket
   - 實作事件合併邏輯以減少訊息數量

3. **效能優化**：
   - 使用 `minimal_response=true` 減少資料量
   - 使用 `no_attributes=true` 跳過屬性查詢
   - 減少資料庫 I/O，提升系統效能

#### 返回資料結構

返回事件訊息，包含：

```json
{
  "id": 49,
  "type": "event",
  "event": {
    "states": {}, // 狀態變化資料
    "start_time": 1760957597.057, // Unix timestamp
    "end_time": 1761043997.057 // Unix timestamp
  }
}
```

#### 使用案例

- **即時歷史圖表**：Home Assistant 2023.2+ 的 Live History 功能
- **狀態監控儀表板**：即時顯示設備狀態變化，無需輪詢
- **能源監控**：持續追蹤能源消耗變化
- **溫度追蹤**：即時監控溫度感測器數據

#### 效能優化建議

1. **使用最小化回應**：

   ```json
   {
     "minimal_response": true,
     "no_attributes": true
   }
   ```

2. **過濾顯著變化**：

   ```json
   {
     "significant_changes_only": true
   }
   ```

3. **合理設定時間範圍**：避免查詢過長時間範圍的資料

#### 注意事項

- 此 API 引入於 Home Assistant 2023.2，用於實現即時歷史功能
- 搭配 Recorder 的 5 秒提交間隔，大幅減少資料庫寫入次數
- 使用後記得 `unsubscribe_events` 以釋放資源
- 已知問題：單一實體且省略 `no_attributes` 參數時可能返回空結果

#### 參考來源

- **Source Code**: [homeassistant/components/history/websocket_api.py](https://github.com/home-assistant/core/blob/dev/homeassistant/components/history/websocket_api.py)
- **Release Notes**: [Home Assistant 2023.2 Release](https://www.home-assistant.io/blog/2023/02/01/release-20232/)
- **官方文件**: [WebSocket API](https://developers.home-assistant.io/docs/api/websocket/)

## 三個 API 的差異比較

以下表格比較三個歷史相關 API 的特性與適用場景：

| 特性           | history_during_period | statistics_during_period  | history/stream       |
| -------------- | --------------------- | ------------------------- | -------------------- |
| **用途**       | 查詢原始狀態變化      | 查詢統計聚合資料          | 即時串流狀態變化     |
| **資料來源**   | states 表             | statistics 表             | states 表 + 即時事件 |
| **資料解析度** | 完整狀態（毫秒級）    | 聚合資料（5 分鐘/小時）   | 完整狀態 + 即時更新  |
| **保留期限**   | 短期（預設 10 天）    | 長期（永久保留）          | 取決於查詢範圍       |
| **連線類型**   | 單次請求-回應         | 單次請求-回應             | 長期訂閱             |
| **最適用於**   | 短期內的詳細狀態查詢  | 長期趨勢分析              | 即時監控與歷史回放   |
| **實體限制**   | 所有實體              | 僅限有 state_class 的實體 | 所有實體             |

### 選擇建議

**使用 `statistics_during_period`**：

- ✅ 需要長期趨勢分析（超過 10 天）
- ✅ Sensor 類實體（溫度、能源、濕度等）
- ✅ 只需要聚合資料（平均值、最大值、最小值）

**使用 `history_during_period`**：

- ✅ 需要短期內的完整狀態變化（10 天內）
- ✅ 所有類型的實體（包括 Fan、Switch、Light）
- ✅ 需要完整的屬性資料

**使用 `history/stream`**：

- ✅ 需要即時監控狀態變化
- ✅ 需要歷史回放 + 持續更新
- ✅ 圖表需要 Live 更新功能

## 串流串接說明 (streaming history event)

### API 呼叫順序說明

#### 為什麼先查詢 Statistics 再訂閱 Stream？

這是一種**降級策略 (Fallback Strategy)**，原因如下：

**1. 並非所有實體都有統計資料**

- ✅ **Sensor 類實體**（溫度、濕度、能源）：有 `state_class`，會產生統計資料
- ❌ **控制類實體**（開關、風扇、燈光）：無 `state_class`，不產生統計資料

**2. Statistics 優先的原因**

- 📊 統計資料更輕量（聚合後的資料）
- 🚀 查詢速度更快
- 💾 適合長期資料（永久保留）

**3. 降級到 History Stream**

- 當統計資料不存在時（如 `fan.test_fan` 返回 `{}`）
- 使用 `history/stream` 取得完整的狀態變化
- 適用於所有實體類型

#### 實際案例分析

**範例中的 `fan.test_fan`**：

```json
// 查詢統計資料 - 返回空物件
{ "id": 47, "type": "result", "success": true, "result": {} }

// 原因：Fan 是控制設備，沒有 state_class，不會產生統計資料
// 解決：改用 history/stream 取得狀態變化歷史
```

**如果是 `sensor.temperature`**：

```json
// 查詢統計資料 - 返回聚合資料
{
  "id": 47,
  "result": {
    "sensor.temperature": [
      {"mean": 22.5, "min": 20.0, "max": 25.0, ...}
    ]
  }
}

// 然後可以用 history/stream 補充更詳細的變化
```

#### 實體類型與資料來源對應

| 實體類型           | state_class         | Statistics 可用 | History 可用  | 建議使用        |
| ------------------ | ------------------- | --------------- | ------------- | --------------- |
| sensor.temperature | ✅ measurement      | ✅ 有聚合資料   | ✅ 有狀態歷史 | Statistics 優先 |
| sensor.energy      | ✅ total_increasing | ✅ 有累計資料   | ✅ 有狀態歷史 | Statistics 優先 |
| fan.\*             | ❌ 無               | ❌ 空結果 `{}`  | ✅ 有狀態歷史 | History 必須    |
| switch.\*          | ❌ 無               | ❌ 空結果 `{}`  | ✅ 有狀態歷史 | History 必須    |
| light.\*           | ❌ 無               | ❌ 空結果 `{}`  | ✅ 有狀態歷史 | History 必須    |

### Send Messages 範例

以 `fan.test_fan` 為例，展示降級策略的完整流程：

#### 首次串接（無舊訂閱）

1. 查詢統計資料（`recorder/statistics_during_period`）

```json
{
  "type": "recorder/statistics_during_period",
  "start_time": "2025-10-20T10:53:17.057Z",
  "end_time": "2025-10-21T10:53:17.057Z",
  "statistic_ids": ["fan.test_fan"],
  "period": "hour",
  "types": ["mean", "state"],
  "id": 47
}
```

2. 訂閱即時歷史串流（`history/stream`）

```json
{
  "type": "history/stream",
  "entity_ids": ["fan.test_fan"],
  "start_time": "2025-10-20T10:53:17.057Z",
  "end_time": "2025-10-21T10:53:17.057Z",
  "minimal_response": true,
  "no_attributes": true,
  "id": 49
}
```

#### 若已有舊訂閱（需先取消）

如果之前已經訂閱過 `history/stream`（subscription id: 46），需要先取消：

```json
{ "type": "unsubscribe_events", "subscription": 46, "id": 48 }
```

然後再建立新的訂閱（同上）。

### Received Messages

**首次串接的回應**：

```json
// statistics 查詢結果 - 返回空物件（Fan 無統計資料）
{ "id": 47, "type": "result", "success": true, "result": {} }
```

```json
// stream 訂閱確認
{ "id": 49, "type": "result", "success": true, "result": null }
```

```json
// stream 事件推送
{
  "id": 49,
  "type": "event",
  "event": {
    "states": {},
    "start_time": 1760957597.057, // Unix timestamp（秒）
    "end_time": 1761043997.057 // Unix timestamp（秒）
  }
}
```

**若有舊訂閱的回應**：

```json
// 取消訂閱確認
{ "id": 48, "type": "result", "success": true, "result": null }
```

## Home Assistant 歷史記錄去重判斷研究

### 研究背景

在實作 Odoo Home Assistant 整合時，需要從 HA WebSocket API 取得歷史資料並儲存到 Odoo 資料庫中。關鍵問題是：**如何正確判斷歷史記錄是否重複，避免儲存重複資料？**

目前實作（`ha_entity_history.py` lines 410-418）使用 `(entity_id, last_updated)` 作為去重判斷：

```python
exists = self.env[self._name].search([
    ('entity_id', '=', entity_id),
    ('last_updated', '=', last_updated)
], limit=1)
```

本研究旨在驗證此判斷標準是否正確，並探討 Home Assistant 官方的實作方式。

### Home Assistant 資料庫結構

#### States 表結構

```sql
CREATE TABLE states (
    state_id INTEGER PRIMARY KEY,           -- 唯一主鍵（自動遞增）
    metadata_id INTEGER,                    -- FK to states_meta (entity_id)
    state VARCHAR(255),                     -- 狀態值
    last_updated_ts FLOAT,                  -- 任何變更的時間戳（秒）
    last_changed_ts FLOAT,                  -- 狀態值變更的時間戳（可為 NULL）
    attributes_id INTEGER,                  -- FK to state_attributes
    old_state_id INTEGER,                   -- FK to previous state
    context_id_bin BLOB,                    -- 事件 context ID
    ...
)
```

#### 關鍵索引

```sql
-- 主要查詢索引
INDEX ix_states_metadata_id_last_updated_ts ON (metadata_id, last_updated_ts)

-- 其他索引
INDEX ix_states_context_id_bin ON (context_id_bin)
```

#### ⚠️ 重要發現：無 UNIQUE 約束

資料庫層級**沒有**設置 `(entity_id, last_updated_ts)` 或 `(metadata_id, last_updated_ts)` 的 UNIQUE constraint！

這意味著：
- 理論上可以插入相同 `(entity_id, last_updated_ts)` 的多筆記錄
- Home Assistant 依賴應用層邏輯來避免重複，而非資料庫約束

### Home Assistant 官方實作分析

#### 查詢邏輯

根據 `recorder/history/__init__.py` 的實作：

```python
# 官方查詢使用的排序
ORDER BY (metadata_id, last_updated_ts) ASC
```

**官方實作特點**：

1. ✅ 使用 `(metadata_id, last_updated_ts)` 作為排序依據
2. ✅ **不依賴** `state_id` 來過濾重複
3. ✅ 允許同一個 `(entity_id, last_updated_ts)` 有多筆記錄存在
4. ✅ 透過 `limit=1` 或時間排序來處理潛在重複

#### 去重策略

Home Assistant 採用**應用層去重**而非資料庫約束：

1. **StatesManager 快取機制**：
   - 維護 pending 和 committed 狀態記錄
   - 避免短時間內插入相同狀態

2. **時間邊界管理**：
   - WebSocket API 使用 `+1 microsecond` 避免重複查詢
   - 事件過濾器跳過已發送的舊事件

3. **Significant Changes 過濾**：
   - 過濾掉狀態值未改變的更新（只有 attributes 變化）
   - 減少冗餘資料儲存

### 時間戳欄位差異

| 欄位 | 更新時機 | 儲存方式 | 範例 |
|------|---------|---------|------|
| `last_updated_ts` | 任何變更（包含 attributes） | 總是儲存 | `1729500000.123` |
| `last_changed_ts` | **只有** state 值改變 | 與 `last_updated_ts` 相同時儲存為 NULL | `NULL` 或 `1729500000.123` |

**實際範例**：

```python
# 案例 1: 燈泡從 off 變 on（狀態改變）
{
    "state": "on",
    "last_updated_ts": 1729500000.123,
    "last_changed_ts": 1729500000.123  # 儲存為 NULL（因為與 last_updated 相同）
}

# 案例 2: 燈泡只改變顏色，state 仍是 on（僅屬性改變）
{
    "state": "on",
    "last_updated_ts": 1729500060.456,  # 更新
    "last_changed_ts": NULL              # 保持 NULL（state 沒變）
}
```

**空間優化策略**：
- 當 `last_changed_ts == last_updated_ts` 時，`last_changed_ts` 儲存為 NULL
- 節省約 8 bytes（FLOAT 型別）per record
- 查詢時使用 `COALESCE(last_changed_ts, last_updated_ts)` 取得實際值

### 已知問題

#### GitHub Issue #2787：同一 Timestamp 的重複記錄

**問題描述**：
- 某些 sensor 在同一個 timestamp 被記錄多次
- 導致資料庫快速增長（案例：20GB）
- 影響系統效能（Raspberry Pi 4 在 purge 時凍結）

**影響範圍**：
- 跨資料庫系統（SQLite、MariaDB、PostgreSQL）
- 非特定版本問題

**官方回應**：
- ❌ **Closed as Not Planned**（無修復計劃）
- 社群提供的臨時解法：
  1. 手動刪除重複資料
  2. 設定 `exclude` 規則限制記錄範圍
  3. 調整 recorder 保留期限

**結論**：
- 這是 Home Assistant 的已知限制，非 bug
- 官方不認為需要在資料庫層級解決
- 應用層需自行處理潛在重複

### 去重方案比較

| 方案 | 唯一性判斷 | 優點 | 缺點 | 與 HA 官方一致性 | 建議 |
|------|-----------|------|------|----------------|------|
| **方案 1（目前）**<br/>`(entity_id, last_updated)` | ✅ 中 | • 與 HA 官方索引一致<br/>• 查詢效能最佳<br/>• 實作簡單 | • 無法處理同 timestamp 重複<br/>（極罕見，HA 官方也無解） | ⭐⭐⭐⭐⭐ | ⭐ **推薦保持** |
| **方案 2**<br/>`(entity_id, last_updated, state)` | ✅✅ 高 | • 可區分同時間的不同狀態<br/>• 處理更多邊緣情況 | • 增加查詢欄位<br/>• 效能稍差<br/>• state 可能為 NULL | ⭐⭐⭐ | 如擔心重複可用 |
| **方案 3**<br/>`(entity_id, last_updated, last_changed)` | ✅ 中 | • 可區分狀態變更 vs 屬性變更 | • last_changed 可為 NULL<br/>• 過於複雜<br/>• HA 不使用此組合 | ⭐⭐ | ❌ 不建議 |
| **方案 4**<br/>儲存 HA 的 `state_id` | ✅✅✅ 完美 | • 絕對唯一<br/>• 零重複可能 | • 需修改資料模型<br/>• 增加欄位<br/>• HA API 通常不返回 state_id<br/>• 過度設計 | ⭐ | ❌ 過度設計 |
| **方案 5**<br/>`(entity_id, last_updated, attributes_hash)` | ✅✅ 高 | • 完整區分不同記錄<br/>• 包含屬性差異 | • 需計算 hash<br/>• 增加運算開銷<br/>• 複雜度高 | ⭐ | ❌ 過度設計 |

### 實作建議

#### ✅ 結論：保持目前實作不變

**推薦維持現有的 `(entity_id, last_updated)` 去重判斷**

**理由**：

1. **符合官方標準** ⭐
   - Home Assistant 官方查詢也使用 `(metadata_id, last_updated_ts)`
   - 與官方索引 `ix_states_metadata_id_last_updated_ts` 一致
   - 遵循 HA 的設計理念

2. **已知問題已處理** ⭐
   - 程式碼已使用 `limit=1` 處理極罕見的重複情況
   - 即使有重複，也只會取第一筆（與 HA 官方行為一致）

3. **效能最佳** ⭐
   - 最簡單的查詢條件
   - 充分利用資料庫索引
   - 避免不必要的欄位比對

4. **官方無修復計劃** ⭐
   - Issue #2787 被標記為 "Closed as Not Planned"
   - 表示這不是優先問題
   - HA 官方認為應用層處理即可

#### 🔧 程式碼驗證

目前實作（`ha_entity_history.py`）：

```python
def _batch_create_deduplicated(self, records):
    """批次建立記錄，自動去除重複項"""

    # 批次查詢已存在的記錄
    existing_records = set()
    for entity_id, last_updated in check_pairs:
        exists = self.env[self._name].search([
            ('entity_id', '=', entity_id),      # ✅ 正確：使用 entity_id
            ('last_updated', '=', last_updated)  # ✅ 正確：使用 last_updated
        ], limit=1)  # ✅ 正確：使用 limit=1 處理潛在重複

        if exists:
            existing_records.add((entity_id, last_updated))
```

**評估**：
- ✅ 使用正確的欄位組合
- ✅ 使用 `limit=1` 避免多筆重複的效能問題
- ✅ 與 Home Assistant 官方行為一致

#### 📝 未來改進選項

**如果未來真的遇到大量重複**（可能性極低）：

1. **選項 A：升級為方案 2**
   ```python
   exists = self.env[self._name].search([
       ('entity_id', '=', entity_id),
       ('last_updated', '=', last_updated),
       ('entity_state', '=', state),  # 增加 state 判斷
   ], limit=1)
   ```

2. **選項 B：在 Odoo 層級加入 UNIQUE constraint**
   ```python
   _sql_constraints = [
       ('unique_entity_history',
        'UNIQUE(entity_id, last_updated)',
        'History record already exists for this entity and timestamp')
   ]
   ```

3. **選項 C：記錄並監控重複情況**
   ```python
   if exists:
       self._logger.warning(
           f"Duplicate history record detected: "
           f"entity={entity_id}, timestamp={last_updated}"
       )
   ```

#### ⚠️ 不建議的做法

❌ **不要**儲存 HA 的 `state_id`：
- WebSocket API 通常不返回此欄位
- 需額外查詢，增加複雜度
- 過度設計，沒有實際必要

❌ **不要**使用 `(entity_id, last_updated, last_changed)` 組合：
- `last_changed` 可為 NULL，判斷邏輯複雜
- HA 官方不使用此組合
- 無實際效益

### 參考資料

#### 官方文件
- [Home Assistant States Data Model](https://data.home-assistant.io/docs/states/)
- [Recorder Integration](https://www.home-assistant.io/integrations/recorder/)
- [WebSocket API Documentation](https://developers.home-assistant.io/docs/api/websocket/)

#### 原始碼
- [recorder/db_schema.py](https://github.com/home-assistant/core/blob/dev/homeassistant/components/recorder/db_schema.py) - 資料庫結構定義
- [recorder/history/__init__.py](https://github.com/home-assistant/core/blob/dev/homeassistant/components/recorder/history/__init__.py) - 歷史查詢實作
- [recorder/queries.py](https://github.com/home-assistant/core/blob/dev/homeassistant/components/recorder/queries.py) - SQL 查詢建構

#### GitHub Issues
- [Issue #2787](https://github.com/home-assistant/addons/issues/2787) - MariaDB 同 timestamp 重複記錄
- [Issue #90113](https://github.com/home-assistant/core/issues/90113) - get_last_state_changes 效能問題

### 總結

**✅ 目前的 `(entity_id, last_updated)` 去重判斷是正確的，無需修改。**

此方法：
- ✅ 符合 Home Assistant 官方實作標準
- ✅ 充分利用資料庫索引，效能最佳
- ✅ 已處理極罕見的重複情況（`limit=1`）
- ✅ 簡單、可靠、易維護

Home Assistant 官方已接受「同 timestamp 可能有重複記錄」的設計，並透過應用層邏輯處理。我們的實作遵循相同理念，是正確的技術選擇。
