# History 模組優化設計

**建立時間**: 2026-02-26T04:29:35Z
**狀態**: 設計完成

## 1. 問題分析

### 1.1 現有問題

1. **[object Object] 顯示問題**
   - 圖表中的標籤或 tooltip 顯示 `[object Object]`
   - 根因：`dataset.label` 或 `datalabels.formatter` 返回物件而非字串

2. **多實體合併問題**
   - 目前同類型的多個實體合併在一個圖表中
   - 難以閱讀，尤其在手機上

3. **狀態型視覺化不直觀**
   - 目前狀態型實體使用階梯線圖
   - HA 使用水平彩色時間條更直觀

### 1.2 優化目標

| 目標 | 現況 | 目標狀態 |
|------|------|---------|
| 圖表顯示 | 多實體合併 | 每實體獨立圖表卡片 |
| 數值型實體 | 折線圖 ✓ | 保持折線圖 |
| 狀態型實體 | 階梯線圖 | 水平彩色時間條 |
| 標籤顯示 | [object Object] | 正確顯示實體名稱 |

---

## 2. 技術架構

### 2.1 架構變更

**現有架構：**
```
HaHistoryRenderer
  └─ 按 domain 分組 → 同 domain 實體合併一個圖表
```

**新架構：**
```
HaHistoryRenderer
  └─ 按 entity_id 分組 → 每個實體獨立圖表卡片
      ├─ 數值型 (sensor, number...) → LineChart
      └─ 狀態型 (switch, binary_sensor, climate...) → TimelineBar
```

### 2.2 核心修改檔案

| 檔案 | 修改內容 |
|------|---------|
| `hahistory_renderer.js` | 重構分組邏輯、新增 Timeline Bar 渲染 |
| `hahistory_renderer.xml` | 調整卡片布局，每實體一個區塊 |
| `unified_chart.js` | 修復 `[object Object]` 問題 |

---

## 3. 狀態型時間條設計

### 3.1 狀態類型分類

| 類型 | 範例 | 視覺化方式 |
|------|------|-----------|
| **Binary** | switch, light, input_boolean | on/off 兩色時間條 |
| **Categorical** | climate, fan, cover | 多色時間條（每狀態一色）|
| **Text** | input_text, 其他文字狀態 | 多色時間條 + 狀態文字標籤 |

### 3.2 顏色映射

#### Binary 狀態
| 狀態 | 顏色 |
|------|------|
| `on` / `home` / `open` / `playing` | 綠色 (#4CAF50) |
| `off` / `away` / `closed` / `idle` | 灰色 (#9E9E9E) |
| `unavailable` / `unknown` | 淺灰虛線 (#BDBDBD) |

#### Climate 多選狀態
| 狀態 | 顏色 |
|------|------|
| `cool` | 藍色 (#2196F3) |
| `heat` | 橙色 (#FF9800) |
| `heat_cool` / `auto` | 綠色 (#4CAF50) |
| `dry` | 黃色 (#FFC107) |
| `fan_only` | 青色 (#00BCD4) |
| `off` | 灰色 (#9E9E9E) |

#### Fan 多選狀態
| 狀態 | 顏色 |
|------|------|
| `low` | 淺綠 (#81C784) |
| `medium` | 綠色 (#4CAF50) |
| `high` | 深綠 (#2E7D32) |
| `off` | 灰色 (#9E9E9E) |

#### Cover 狀態
| 狀態 | 顏色 |
|------|------|
| `open` | 綠色 (#4CAF50) |
| `closed` | 灰色 (#9E9E9E) |
| `opening` | 淺綠 (#81C784) |
| `closing` | 淺灰 (#BDBDBD) |

#### 文字狀態（動態顏色）
- 使用 hash 函數根據狀態文字生成顏色
- 確保同一狀態文字始終顯示相同顏色

### 3.3 狀態文字顯示規則

| 情況 | 顯示方式 |
|------|---------|
| 文字 ≤ 4 字 | 完整顯示 |
| 文字 > 4 字 | 顯示前 3-4 字 + `...` |
| Tooltip | 完整狀態名稱 + 持續時間 |

### 3.4 顯示範例

```
┌─────────────────────────────────────────────────────────────┐
│  climate.living_room                                         │
├─────────────────────────────────────────────────────────────┤
│  ██ cool ██│████ heat ████│░░ off ░░│██ auto ██            │
│    (藍)        (橙)          (灰)       (綠)                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  input_text.status                                           │
├─────────────────────────────────────────────────────────────┤
│  ██ 工作... ██│████ 休息 ████│██ 開會... ██│███ 外出 ███    │
│                                                              │
│  (懸停顯示: "工作中請勿打擾 - 2小時30分")                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 實作計畫

### 4.1 Phase 1: 修復 [object Object] 問題
- 檢查 `unified_chart.js` 中的 `datalabels.formatter`
- 確保 `dataset.label` 是字串而非物件
- 預估：30 分鐘

### 4.2 Phase 2: 重構為每實體獨立圖表
- 修改 `hahistory_renderer.js` 的分組邏輯
- 按 `entity_id` 分組而非按 `domain`
- 更新 `hahistory_renderer.xml` 卡片布局
- 預估：2 小時

### 4.3 Phase 3: 實現狀態型時間條
- 新增 TimelineBar 圖表類型
- 實現顏色映射邏輯
- 實現狀態文字截斷顯示
- 實現 Tooltip 顯示完整資訊
- 預估：3 小時

### 4.4 Phase 4: 測試與優化
- 手機端響應式測試
- 各種狀態類型測試
- 效能優化
- 預估：1 小時

---

## 5. 技術細節

### 5.1 狀態文字截斷函數

```javascript
function truncateStateText(text, maxLength = 4) {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength - 1) + '...';
}
```

### 5.2 動態顏色生成（文字狀態）

```javascript
function stringToColor(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = hash % 360;
  return `hsl(${hue}, 70%, 50%)`;
}
```

### 5.3 Timeline Bar 資料結構

```javascript
{
  type: 'bar',
  indexAxis: 'y',  // 水平條狀圖
  data: {
    datasets: [{
      label: entityName,
      data: [
        { x: [startTime1, endTime1], y: 0, state: 'on' },
        { x: [startTime2, endTime2], y: 0, state: 'off' },
        // ...
      ],
      backgroundColor: (ctx) => getStateColor(ctx.raw.state),
    }]
  }
}
```
