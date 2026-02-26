/** @odoo-module */

import { Component, useState, onWillStart, onWillUpdateProps } from "@odoo/owl";
import { HaHistoryModel } from "./hahistory_model";
import { UnifiedChart } from "../../components/charts/unified_chart/unified_chart";
import { debug } from "../../util/debug";
import { isLightColor } from "../../util/color";
import {
  MIN_BAR_WIDTH_FOR_LABEL,
  TIMELINE_BAR_PERCENTAGE,
  TIMELINE_CATEGORY_PERCENTAGE,
  TIMELINE_MAX_BAR_THICKNESS,
  TIMELINE_LABEL_FONT_SIZE,
  UNAVAILABLE_DASH_PATTERN,
} from "../../constants";

// ============================================================================
// Domain 分類常數
// ============================================================================

const NUMERIC_DOMAINS = new Set([
  "sensor",
  "input_number",
  "number",
  "counter",
]);

const BINARY_DOMAINS = new Set([
  "binary_sensor",
  "switch",
  "light",
  "input_boolean",
]);

const CATEGORICAL_DOMAINS = new Set([
  "climate",
  "fan",
  "cover",
  "lock",
  "media_player",
  "vacuum",
]);

// 二元狀態：返回 1 的狀態值
const BINARY_ON_STATES = new Set([
  "on",
  "home",
  "true",
  "open",
  "locked",
  "playing",
  "cleaning",
]);

// 無效狀態集合（設備離線或狀態未知）
const UNAVAILABLE_STATES = new Set([
  "unavailable",
  "unknown",
]);

// Unavailable 狀態視覺化配置
const UNAVAILABLE_COLOR = "#bdbdbd";  // 灰色
const UNAVAILABLE_VALUE = -999;  // 特殊標記值（用於 binary/categorical 圖表）

// 分類狀態映射表
const CATEGORICAL_STATE_MAPS = {
  climate: {
    off: 0,
    cool: 1,
    heat: 2,
    auto: 3,
    dry: 4,
    fan_only: 5,
    heat_cool: 6,
  },
  fan: { off: 0, low: 1, medium: 2, high: 3, auto: 4 },
  cover: { closed: 0, closing: 1, opening: 2, open: 3 },
  lock: { unlocked: 0, unlocking: 1, locking: 2, locked: 3 },
  media_player: { off: 0, idle: 1, paused: 2, playing: 3, standby: 4, on: 5 },
  vacuum: { docked: 0, idle: 1, returning: 2, cleaning: 3, error: 4, paused: 5 },
};

// 分類狀態顏色映射 (Material Design 風格)
const CATEGORICAL_COLOR_MAPS = {
  climate: {
    0: "#9E9E9E", // off - 灰色
    1: "#2196F3", // cool - 藍色
    2: "#FF9800", // heat - 橙色
    3: "#4CAF50", // auto - 綠色
    4: "#FFC107", // dry - 黃色
    5: "#00BCD4", // fan_only - 青色
    6: "#4CAF50", // heat_cool - 綠色
  },
  fan: {
    0: "#9E9E9E", // off - 灰色
    1: "#81C784", // low - 淺綠
    2: "#4CAF50", // medium - 綠色
    3: "#2E7D32", // high - 深綠
    4: "#9C27B0", // auto - 紫色
  },
  cover: {
    0: "#9E9E9E", // closed - 灰色
    1: "#BDBDBD", // closing - 淺灰
    2: "#81C784", // opening - 淺綠
    3: "#4CAF50", // open - 綠色
  },
  lock: {
    0: "#F44336", // unlocked - 紅色
    1: "#FF9800", // unlocking - 橙色
    2: "#2196F3", // locking - 藍色
    3: "#4CAF50", // locked - 綠色
  },
  media_player: {
    0: "#9E9E9E", // off - 灰色
    1: "#BDBDBD", // idle - 淺灰
    2: "#FF9800", // paused - 橙色
    3: "#4CAF50", // playing - 綠色
    4: "#2196F3", // standby - 藍色
    5: "#9C27B0", // on - 紫色
  },
  vacuum: {
    0: "#4CAF50", // docked - 綠色
    1: "#9E9E9E", // idle - 灰色
    2: "#2196F3", // returning - 藍色
    3: "#F44336", // cleaning - 紅色
    4: "#D32F2F", // error - 深紅
    5: "#FF9800", // paused - 橙色
  },
};

// ============================================================================
// 輔助函數
// ============================================================================

/**
 * 根據 domain 判斷狀態類型
 * @param {string} domain
 * @returns {'numeric'|'binary'|'categorical'|'text'}
 */
function getStateType(domain) {
  if (NUMERIC_DOMAINS.has(domain)) return "numeric";
  if (BINARY_DOMAINS.has(domain)) return "binary";
  if (CATEGORICAL_DOMAINS.has(domain)) return "categorical";
  return "text";
}

/**
 * 檢查狀態是否為無效狀態（unavailable/unknown）
 * @param {string} state
 * @returns {boolean}
 */
function isUnavailableState(state) {
  const normalizedState = state?.toLowerCase?.() || state;
  return UNAVAILABLE_STATES.has(normalizedState);
}

/**
 * 將 entity_state 轉換為數值
 * @param {string} state
 * @param {string} domain
 * @param {'numeric'|'binary'|'categorical'|'text'} stateType
 * @returns {number}
 */
function stateToValue(state, domain, stateType) {
  // 先檢查是否為無效狀態
  if (isUnavailableState(state)) {
    // Numeric 使用 null（斷開線條），Binary/Categorical 使用特殊標記值
    return stateType === "numeric" ? null : UNAVAILABLE_VALUE;
  }

  if (stateType === "numeric") {
    const num = parseFloat(state);
    return isNaN(num) ? null : num;
  }
  if (stateType === "binary") {
    return BINARY_ON_STATES.has(state?.toLowerCase?.() || state) ? 1 : 0;
  }
  if (stateType === "categorical") {
    const map = CATEGORICAL_STATE_MAPS[domain] || {};
    return map[state] ?? -1;
  }
  return null;
}

/**
 * 取得分類狀態的標籤映射 (value -> label)
 * @param {string} domain
 * @returns {Record<number, string>}
 */
function getStateLabels(domain) {
  const map = CATEGORICAL_STATE_MAPS[domain] || {};
  const reversed = {};
  for (const [label, value] of Object.entries(map)) {
    reversed[value] = label;
  }
  return reversed;
}

/**
 * 將 ISO 日期字串轉換為毫秒時間戳
 * @param {string} dateString - ISO 8601 時間字串
 * @returns {number} 毫秒時間戳
 */
function parseTimestamp(dateString) {
  const date = new Date(dateString);
  if (isNaN(date.getTime())) {
    throw new Error("Invalid date string");
  }
  return date.getTime();
}

/**
 * 生成 Time Scale X 軸配置
 * @returns {object} X 軸 time scale 配置
 */
function getTimeScaleConfig() {
  return {
    type: "time",
    time: {
      // 不指定 unit，讓 Chart.js 自動根據數據範圍選擇合適的單位
      displayFormats: {
        second: "HH:mm:ss",
        minute: "HH:mm",
        hour: "MM-dd HH:mm",
        day: "yyyy-MM-dd",
      },
    },
    title: { display: false },
  };
}

/**
 * 將狀態變化數據點擴展為階梯圖格式
 * 狀態型數據每個點代表「變化開始」，需要持續到下一個變化
 * @param {Array<{x: number, y: number}>} dataPoints - 原始數據點
 * @param {boolean} extendToNow - 是否將最後一個狀態延伸到現在
 * @returns {Array<{x: number, y: number}>} 擴展後的數據點
 */
function expandStateDataPoints(dataPoints, extendToNow = true) {
  if (dataPoints.length === 0) return dataPoints;

  const expanded = [];
  for (let i = 0; i < dataPoints.length; i++) {
    const current = dataPoints[i];
    expanded.push(current);

    // 在下一個變化點之前插入持續點（保持相同的 y 值）
    if (i < dataPoints.length - 1) {
      const next = dataPoints[i + 1];
      // 在下一個點之前 1ms 插入持續點
      expanded.push({ x: next.x - 1, y: current.y });
    }
  }

  // 將最後一個狀態延伸到現在
  if (extendToNow && dataPoints.length > 0) {
    const lastPoint = dataPoints[dataPoints.length - 1];
    expanded.push({ x: Date.now(), y: lastPoint.y });
  }

  return expanded;
}

// ============================================================================
// Timeline 區塊風格圖表函數
// ============================================================================

/**
 * 將狀態記錄轉換為時間區段
 * @param {Array} records - 按時間排序的狀態記錄
 * @param {number} endTime - 結束時間（預設為現在）
 * @returns {Array} 時間區段 [{state, start, end}]
 */
function recordsToTimelineSegments(records, endTime = Date.now()) {
  if (records.length === 0) return [];

  const segments = [];
  for (let i = 0; i < records.length; i++) {
    const current = records[i];
    const next = records[i + 1];

    segments.push({
      state: current.entity_state,
      start: parseTimestamp(current.last_changed),
      end: next ? parseTimestamp(next.last_changed) : endTime,
    });
  }
  return segments;
}

/**
 * 格式化持續時間
 * @param {number} ms - 毫秒數
 * @returns {string}
 */
function formatDuration(ms) {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}d ${hours % 24}h`;
  if (hours > 0) return `${hours}h ${minutes % 60}m`;
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
  return `${seconds}s`;
}

/**
 * 生成 Timeline 圖表的 datalabels 配置
 * @returns {object}
 */
/**
 * 截斷過長的狀態文字
 * @param {string} text - 原始文字
 * @param {number} maxLength - 最大長度（預設 4）
 * @returns {string} 截斷後的文字
 */
function truncateStateText(text, maxLength = 4) {
  if (!text || typeof text !== 'string') return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 1) + '...';
}

/**
 * 確保 label 是字串格式
 * @param {*} label - 可能是字串、物件或其他類型
 * @returns {string}
 */
function ensureStringLabel(label) {
  if (label === null || label === undefined) return '';
  if (typeof label === 'object') {
    // 如果是物件，嘗試取得 name 或 display_name
    return label.name || label.display_name || String(label);
  }
  return String(label);
}

function getTimelineDataLabelsConfig() {
  return {
    display: (ctx) => {
      // 計算區塊寬度（像素），只在足夠寬時顯示文字
      const chart = ctx.chart;
      const xScale = chart.scales.x;
      if (!ctx.raw || !Array.isArray(ctx.raw)) return false;
      const barStart = ctx.raw[0];
      const barEnd = ctx.raw[1];
      const startPixel = xScale.getPixelForValue(barStart);
      const endPixel = xScale.getPixelForValue(barEnd);
      const barWidth = Math.abs(endPixel - startPixel);
      return barWidth > MIN_BAR_WIDTH_FOR_LABEL;
    },
    formatter: (value, ctx) => {
      const label = ensureStringLabel(ctx.dataset.label);
      // 截斷過長的文字（超過 4 字顯示前 3 字 + ...）
      return truncateStateText(label, 4);
    },
    color: (ctx) => {
      const bgColor = ctx.dataset.backgroundColor;
      if (typeof bgColor !== 'string') return '#fff';
      return isLightColor(bgColor) ? '#000' : '#fff';
    },
    anchor: 'center',
    align: 'center',
    font: { size: TIMELINE_LABEL_FONT_SIZE, weight: 'bold' },
    clip: true,  // 裁剪超出區塊的文字
  };
}

/**
 * 生成 Timeline 圖表的基本配置
 * @param {number} minTime - X 軸最小時間
 * @param {number} maxTime - X 軸最大時間
 * @param {number} segmentCount - segment 數量（用於計算 bar 厚度）
 * @returns {object}
 */
function getTimelineChartOptions(minTime, maxTime, segmentCount = 1) {
  const xConfig = getTimeScaleConfig();
  // 設定明確的時間範圍
  if (minTime && maxTime) {
    xConfig.min = minTime;
    xConfig.max = maxTime;
  }

  return {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    // Bar 尺寸設定
    barPercentage: TIMELINE_BAR_PERCENTAGE,
    categoryPercentage: TIMELINE_CATEGORY_PERCENTAGE,
    maxBarThickness: TIMELINE_MAX_BAR_THICKNESS,
    scales: {
      x: xConfig,
      y: {
        display: false,  // 隱藏 Y 軸
        stacked: true,   // 堆疊讓所有 bars 在同一 category 位置
        grid: {
          display: false,
        },
      },
    },
    plugins: {
      legend: {
        display: false,  // 隱藏 legend
      },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            if (!ctx.raw || !Array.isArray(ctx.raw)) return '';
            const duration = ctx.raw[1] - ctx.raw[0];
            const label = ensureStringLabel(ctx.dataset.label);
            return `${label}: ${formatDuration(duration)}`;
          },
        },
      },
      datalabels: getTimelineDataLabelsConfig(),
    },
  };
}

/**
 * Binary 狀態顏色
 */
const BINARY_COLORS = {
  on: '#4CAF50',   // 綠色 (Material Design)
  off: '#9E9E9E',  // 灰色 (Material Design)
  unavailable: UNAVAILABLE_COLOR,
};

/**
 * 根據字串生成穩定的顏色（用於文字狀態）
 * @param {string} str - 狀態文字
 * @returns {string} HSL 顏色字串
 */
function stringToColor(str) {
  if (!str) return '#9E9E9E';
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash % 360);
  return `hsl(${hue}, 70%, 50%)`;
}

/**
 * 將單一 entity 的 records 轉為 Binary Timeline 圖表資料
 * 使用多 datasets 方式（每個 segment 一個 dataset），透過 stacking 合併到同一行
 * @param {object[]} records
 * @param {string} entityLabel
 * @returns {object}
 */
function parseBinaryTimelineData(records, entityLabel) {
  // 1. 排序
  records.sort(
    (a, b) =>
      new Date(a.last_changed).getTime() - new Date(b.last_changed).getTime()
  );

  // 2. 轉換為區段
  const segments = recordsToTimelineSegments(records);

  // 3. 計算時間範圍
  let minTime = Infinity;
  let maxTime = -Infinity;
  for (const seg of segments) {
    if (seg.start < minTime) minTime = seg.start;
    if (seg.end > maxTime) maxTime = seg.end;
  }

  // 4. 每個 segment 創建一個 dataset，所有共用相同的 stack
  const datasets = segments.map((seg) => {
    const state = seg.state?.toLowerCase?.() || seg.state;
    let color, label;
    if (isUnavailableState(state)) {
      color = BINARY_COLORS.unavailable;
      label = 'Unavailable';
    } else if (BINARY_ON_STATES.has(state)) {
      color = BINARY_COLORS.on;
      label = 'On';
    } else {
      color = BINARY_COLORS.off;
      label = 'Off';
    }

    return {
      label: label,
      data: [[seg.start, seg.end]],
      backgroundColor: color,
    };
  });

  return {
    type: 'bar',
    data: {
      labels: [entityLabel],
      datasets,
    },
    options: getTimelineChartOptions(minTime, maxTime, segments.length),
  };
}

/**
 * 將單一 entity 的 records 轉為 Categorical Timeline 圖表資料
 * 使用多 datasets 方式（每個 segment 一個 dataset）
 * @param {object[]} records
 * @param {string} entityLabel
 * @param {string} domain
 * @returns {object}
 */
function parseCategoricalTimelineData(records, entityLabel, domain) {
  // 1. 排序
  records.sort(
    (a, b) =>
      new Date(a.last_changed).getTime() - new Date(b.last_changed).getTime()
  );

  // 2. 轉換為區段
  const segments = recordsToTimelineSegments(records);

  // 3. 計算時間範圍
  let minTime = Infinity;
  let maxTime = -Infinity;
  for (const seg of segments) {
    if (seg.start < minTime) minTime = seg.start;
    if (seg.end > maxTime) maxTime = seg.end;
  }

  // 4. 取得顏色映射
  const colorMap = CATEGORICAL_COLOR_MAPS[domain] || {};
  const stateMap = CATEGORICAL_STATE_MAPS[domain] || {};
  const stateLabels = getStateLabels(domain);

  // 5. 每個 segment 創建一個 dataset
  const datasets = segments.map((seg) => {
    const state = seg.state;
    const stateKey = state?.toLowerCase?.() || state;

    let color, label;
    if (isUnavailableState(stateKey)) {
      color = UNAVAILABLE_COLOR;
      label = 'Unavailable';
    } else {
      const stateValue = stateMap[state];
      color = colorMap[stateValue] || '#95a5a6';
      label = stateLabels[stateValue] || state;
    }

    return {
      label: label,
      data: [[seg.start, seg.end]],
      backgroundColor: color,
    };
  });

  return {
    type: 'bar',
    data: {
      labels: [entityLabel],
      datasets,
    },
    options: getTimelineChartOptions(minTime, maxTime, segments.length),
  };
}

/**
 * 將單一 entity 的 records 轉為文字狀態 Timeline 圖表資料
 * 使用動態顏色（根據狀態文字生成）
 * @param {object[]} records
 * @param {string} entityLabel
 * @returns {object}
 */
function parseTextTimelineData(records, entityLabel) {
  // 1. 排序
  records.sort(
    (a, b) =>
      new Date(a.last_changed).getTime() - new Date(b.last_changed).getTime()
  );

  // 2. 轉換為區段
  const segments = recordsToTimelineSegments(records);

  // 3. 計算時間範圍
  let minTime = Infinity;
  let maxTime = -Infinity;
  for (const seg of segments) {
    if (seg.start < minTime) minTime = seg.start;
    if (seg.end > maxTime) maxTime = seg.end;
  }

  // 4. 每個 segment 創建一個 dataset，使用動態顏色
  const datasets = segments.map((seg) => {
    const state = seg.state;
    const stateKey = state?.toLowerCase?.() || state;

    let color, label;
    if (isUnavailableState(stateKey)) {
      color = UNAVAILABLE_COLOR;
      label = 'N/A';
    } else {
      // 使用狀態文字生成顏色
      color = stringToColor(state);
      label = state || '';
    }

    return {
      label: label,
      data: [[seg.start, seg.end]],
      backgroundColor: color,
    };
  });

  return {
    type: 'bar',
    data: {
      labels: [entityLabel],
      datasets,
    },
    options: getTimelineChartOptions(minTime, maxTime, segments.length),
  };
}

/**
 * 將 records 按 domain 分組
 * @param {object[]} records
 * @returns {Record<string, object[]>}
 */
function groupRecordsByDomain(records) {
  return records.reduce((acc, record) => {
    const domain = record.domain;
    if (!acc[domain]) {
      acc[domain] = [];
    }
    acc[domain].push(record);
    return acc;
  }, {});
}

/**
 * 合併模式的 Timeline 圖表配置
 * @param {number} minTime
 * @param {number} maxTime
 * @param {number} entityCount - entity 數量（影響 bar 厚度）
 * @returns {object}
 */
function getCombinedTimelineChartOptions(minTime, maxTime, entityCount = 1) {
  const xConfig = getTimeScaleConfig();
  if (minTime && maxTime) {
    xConfig.min = minTime;
    xConfig.max = maxTime;
  }

  return {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    barPercentage: 0.9,
    categoryPercentage: 0.9,
    scales: {
      x: xConfig,
      y: {
        // stacked: true 讓同一 label 的 bar 重疊在同一 Y 位置
        stacked: true,
        grid: { display: false },
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          title: (ctx) => ctx[0]?.label || '',
          label: (ctx) => {
            if (!ctx.raw || !Array.isArray(ctx.raw)) return '';
            const duration = ctx.raw[1] - ctx.raw[0];
            const label = ensureStringLabel(ctx.dataset.label);
            return `${label}: ${formatDuration(duration)}`;
          },
        },
      },
      datalabels: getTimelineDataLabelsConfig(),
    },
  };
}

/**
 * 將同一 stateType 的 Binary/Categorical records 合併為 Timeline 圖表
 * 每個 entity 一行，狀態用顏色區分
 * @param {object[]} records
 * @param {'binary'|'categorical'} stateType
 * @returns {object}
 */
function parseCombinedTimelineData(records, stateType) {
  // 1. 按 entity 分組
  const entityGroups = groupRecordsByEntity(records);
  const entityIds = Object.keys(entityGroups);

  // 2. 為每個 entity 計算 segments
  const entitySegmentsMap = {}; // { entityId: segments[] }
  let globalMinTime = Infinity;
  let globalMaxTime = -Infinity;

  const domain = records[0]?.domain;

  for (const [entityId, entityRecords] of Object.entries(entityGroups)) {
    // 排序
    entityRecords.sort((a, b) =>
      new Date(a.last_changed).getTime() - new Date(b.last_changed).getTime()
    );
    const segments = recordsToTimelineSegments(entityRecords);
    entitySegmentsMap[entityId] = segments;

    // 更新全局時間範圍
    for (const seg of segments) {
      if (seg.start < globalMinTime) globalMinTime = seg.start;
      if (seg.end > globalMaxTime) globalMaxTime = seg.end;
    }
  }

  // 3. 為每個 segment 創建 dataset（不使用 stacking，讓 bar 在同一 Y 位置重疊）
  const datasets = [];

  for (const [entityIndex, entityId] of entityIds.entries()) {
    const segments = entitySegmentsMap[entityId];

    for (const seg of segments) {
      const state = seg.state;
      const normalizedState = state?.toLowerCase?.() || state;

      // 決定顏色和標籤
      let color, label;
      if (isUnavailableState(normalizedState)) {
        color = UNAVAILABLE_COLOR;
        label = 'Unavailable';
      } else if (stateType === 'binary') {
        if (BINARY_ON_STATES.has(normalizedState)) {
          color = BINARY_COLORS.on;
          label = 'On';
        } else {
          color = BINARY_COLORS.off;
          label = 'Off';
        }
      } else {
        // categorical
        const colorMap = CATEGORICAL_COLOR_MAPS[domain] || {};
        const stateMap = CATEGORICAL_STATE_MAPS[domain] || {};
        const stateIndex = stateMap[state];
        const stateLabels = getStateLabels(domain);
        color = colorMap[stateIndex] || '#95a5a6';
        label = stateLabels[stateIndex] || state;
      }

      // 創建 data 陣列：每個 entity 對應一個位置，只有當前 entity 有值
      const data = new Array(entityIds.length).fill(null);
      data[entityIndex] = [seg.start, seg.end];

      datasets.push({
        label: label,
        data: data,
        backgroundColor: color,
        // 不使用 stack，讓 bar 在同一 Y 位置重疊顯示
      });
    }
  }

  // 4. labels 是 entity 名稱列表
  const labels = entityIds;

  return {
    type: 'bar',
    data: { labels, datasets },
    options: getCombinedTimelineChartOptions(globalMinTime, globalMaxTime, entityIds.length),
  };
}

/**
 * 將同一 stateType 的 records 合併為單一圖表資料（多條線在同一圖表）
 * @param {object[]} records
 * @param {'numeric'|'binary'|'categorical'} stateType
 * @returns {object}
 */
function parseCombinedChartData(records, stateType) {
  // Binary/Categorical 使用 Timeline 風格
  if (stateType === 'binary' || stateType === 'categorical') {
    return parseCombinedTimelineData(records, stateType);
  }

  // Numeric 保持使用 Line Chart
  // 1. 按時間排序
  records.sort(
    (a, b) =>
      new Date(a.last_changed).getTime() - new Date(b.last_changed).getTime()
  );

  // 2. 按 entity 分組，收集每個 entity 的數據點
  const entityDataMap = {}; // { entityId: { domain, dataPoints: [{x, y}] } }
  let hasUnavailable = false;

  for (const record of records) {
    const entityId = `${record.entity_name || "unknown"}(${record.entity_id_string})`;
    const timestamp = parseTimestamp(record.last_changed);

    if (!entityDataMap[entityId]) {
      entityDataMap[entityId] = {
        domain: record.domain,
        dataPoints: [],
      };
    }

    // 根據 stateType 計算值，並處理 unavailable 狀態
    let value;
    const state = record.entity_state;

    if (isUnavailableState(state)) {
      hasUnavailable = true;
      value = stateType === "numeric" ? null : UNAVAILABLE_VALUE;
    } else if (stateType === "numeric") {
      value = parseFloat(state);
      if (isNaN(value)) value = null;
    } else if (stateType === "binary") {
      const normalizedState = state?.toLowerCase?.() || state;
      value = BINARY_ON_STATES.has(normalizedState) ? 1 : 0;
    } else if (stateType === "categorical") {
      const stateMap = CATEGORICAL_STATE_MAPS[record.domain] || {};
      value = stateMap[state] ?? -1;
    } else {
      value = null;
    }

    entityDataMap[entityId].dataPoints.push({ x: timestamp, y: value });
  }

  // 3. 為每個 entity 創建 dataset（使用 {x, y} 格式支援 Time Scale）
  const chartDatasets = Object.entries(entityDataMap).map(
    ([entityId, { domain, dataPoints }]) => {
      // 對於狀態型數據（binary/categorical），擴展數據點以正確顯示持續時間
      const expandedData =
        stateType === "binary" || stateType === "categorical"
          ? expandStateDataPoints(dataPoints)
          : dataPoints;

      const baseDataset = {
        label: entityId,
        data: expandedData,
        spanGaps: stateType === "numeric" ? false : true,  // numeric 不連接 null
      };

      // 根據 stateType 添加特定配置
      if (stateType === "binary") {
        return {
          ...baseDataset,
          stepped: "before",
          fill: false,
          borderWidth: 2,
          pointRadius: 0,
          segment: {
            borderColor: (ctx) => {
              if (!ctx.p0) return "rgba(46, 204, 113, 1)";
              const value = ctx.p0.parsed.y;
              if (value === UNAVAILABLE_VALUE || value <= -1) return UNAVAILABLE_COLOR;
              return "rgba(46, 204, 113, 1)";
            },
            borderDash: (ctx) => {
              if (!ctx.p0) return [];
              const value = ctx.p0.parsed.y;
              if (value === UNAVAILABLE_VALUE || value <= -1) return UNAVAILABLE_DASH_PATTERN;
              return [];
            },
          },
        };
      } else if (stateType === "categorical") {
        const colorMap = CATEGORICAL_COLOR_MAPS[domain] || {};
        return {
          ...baseDataset,
          stepped: "before",
          fill: false,
          borderWidth: 2,
          pointRadius: 3,
          segment: {
            borderColor: (ctx) => {
              if (!ctx.p0) return "#95a5a6";
              const value = Math.round(ctx.p0.parsed.y);
              if (value === UNAVAILABLE_VALUE || value < 0) return UNAVAILABLE_COLOR;
              return colorMap[value] || "#95a5a6";
            },
            borderDash: (ctx) => {
              if (!ctx.p0) return [];
              const value = Math.round(ctx.p0.parsed.y);
              if (value === UNAVAILABLE_VALUE || value < 0) return UNAVAILABLE_DASH_PATTERN;
              return [];
            },
          },
        };
      }
      return baseDataset;
    }
  );

  // 4. 根據 stateType 生成不同的圖表配置
  let chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: getTimeScaleConfig(),
    },
  };

  if (stateType === "binary") {
    const yMin = hasUnavailable ? -1.5 : -0.1;
    chartOptions.scales.y = {
      min: yMin,
      max: 1.1,
      ticks: {
        stepSize: 1,
        callback: (value) => {
          if (value === 1) return "On";
          if (value === 0) return "Off";
          if (value <= UNAVAILABLE_VALUE || value === -1) return "N/A";
          return "";
        },
      },
    };
    chartOptions.plugins = {
      tooltip: {
        callbacks: {
          label: (context) => {
            const y = context.parsed.y;
            if (y === UNAVAILABLE_VALUE || y <= -1) return `${context.dataset.label}: Unavailable`;
            const state = y === 1 ? "On" : "Off";
            return `${context.dataset.label}: ${state}`;
          },
        },
      },
    };
  } else if (stateType === "categorical") {
    // 收集所有出現的狀態值（排除 unavailable）
    const allValues = chartDatasets.flatMap((ds) =>
      ds.data.map((p) => p.y).filter((v) => v !== null && v >= 0)
    );
    const minVal = allValues.length > 0 ? Math.min(...allValues) : 0;
    const maxVal = allValues.length > 0 ? Math.max(...allValues) : 1;
    const yMin = hasUnavailable ? -1.5 : minVal - 0.5;

    // 收集所有 domain 的 state labels
    const allStateLabels = {};
    for (const { domain } of Object.values(entityDataMap)) {
      const labels = getStateLabels(domain);
      Object.assign(allStateLabels, labels);
    }

    chartOptions.scales.y = {
      min: yMin,
      max: maxVal + 0.5,
      ticks: {
        stepSize: 1,
        callback: (value) => {
          if (value === UNAVAILABLE_VALUE || value === -1) return "N/A";
          return allStateLabels[value] || "";
        },
      },
    };
    chartOptions.plugins = {
      tooltip: {
        callbacks: {
          label: (context) => {
            const y = context.parsed.y;
            if (y === UNAVAILABLE_VALUE || y < 0) return `${context.dataset.label}: Unavailable`;
            const stateName = allStateLabels[y] || y;
            return `${context.dataset.label}: ${stateName}`;
          },
        },
      },
    };
  } else if (stateType === "numeric") {
    // Numeric 類型添加 tooltip 處理
    chartOptions.plugins = {
      tooltip: {
        callbacks: {
          label: (context) => {
            const y = context.parsed.y;
            if (y === null) return `${context.dataset.label}: Unavailable`;
            return `${context.dataset.label}: ${y}`;
          },
        },
      },
    };
  }

  return {
    type: "line",
    options: chartOptions,
    data: {
      datasets: chartDatasets,
    },
  };
}

/**
 * Domain 的顯示標題
 */
const DOMAIN_TITLES = {
  sensor: "Sensors",
  input_number: "Input Numbers",
  number: "Numbers",
  counter: "Counters",
  binary_sensor: "Binary Sensors",
  switch: "Switches",
  light: "Lights",
  input_boolean: "Input Booleans",
  climate: "Climate",
  fan: "Fans",
  cover: "Covers",
  lock: "Locks",
  media_player: "Media Players",
  vacuum: "Vacuums",
};

/**
 * 將單一 entity 的 records 轉為數值型圖表資料 (Line Chart)
 * @param {object[]} records
 * @param {string} entityLabel
 * @returns {object}
 */
function parseNumericChartData(records, entityLabel) {
  records.sort(
    (a, b) =>
      new Date(a.last_changed).getTime() - new Date(b.last_changed).getTime()
  );

  // 使用 {x, y} 格式支援 Time Scale
  // unavailable 狀態會產生 null 值，造成線條斷開
  const dataPoints = records.map((record) => {
    const state = record.entity_state;
    // 檢查 unavailable 狀態
    if (isUnavailableState(state)) {
      return {
        x: parseTimestamp(record.last_changed),
        y: null,
      };
    }
    const num = parseFloat(state);
    return {
      x: parseTimestamp(record.last_changed),
      y: isNaN(num) ? null : num,
    };
  });

  return {
    type: "line",
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: getTimeScaleConfig(),
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: function (context) {
              const y = context.parsed.y;
              if (y === null) {
                return `${context.dataset.label}: Unavailable`;
              }
              return `${context.dataset.label}: ${y}`;
            },
          },
        },
      },
    },
    data: {
      datasets: [
        {
          label: entityLabel,
          data: dataPoints,
          spanGaps: false,  // 不連接 null 值，讓 unavailable 區間顯示為斷開
        },
      ],
    },
  };
}

/**
 * 將單一 entity 的 records 轉為二元狀態圖表資料 (Stepped Area Chart)
 * @param {object[]} records
 * @param {string} entityLabel
 * @returns {object}
 */
function parseBinaryChartData(records, entityLabel) {
  records.sort(
    (a, b) =>
      new Date(a.last_changed).getTime() - new Date(b.last_changed).getTime()
  );

  // 使用 {x, y} 格式支援 Time Scale，並處理 unavailable 狀態
  const rawDataPoints = records.map((record) => {
    const state = record.entity_state?.toLowerCase?.() || record.entity_state;
    let yValue;
    if (isUnavailableState(state)) {
      yValue = UNAVAILABLE_VALUE;
    } else {
      yValue = BINARY_ON_STATES.has(state) ? 1 : 0;
    }
    return {
      x: parseTimestamp(record.last_changed),
      y: yValue,
    };
  });

  // 擴展數據點以正確顯示狀態持續時間
  const dataPoints = expandStateDataPoints(rawDataPoints);

  // 檢查是否有 unavailable 狀態，決定 Y 軸範圍
  const hasUnavailable = rawDataPoints.some((p) => p.y === UNAVAILABLE_VALUE);
  const yMin = hasUnavailable ? -1.5 : -0.1;

  return {
    type: "line",
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: getTimeScaleConfig(),
        y: {
          min: yMin,
          max: 1.1,
          ticks: {
            stepSize: 1,
            callback: function (value) {
              if (value === 1) return "On";
              if (value === 0) return "Off";
              if (value <= UNAVAILABLE_VALUE || value === -1) return "N/A";
              return "";
            },
          },
        },
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: function (context) {
              const y = context.parsed.y;
              let state;
              if (y === UNAVAILABLE_VALUE || y <= -1) {
                state = "Unavailable";
              } else {
                state = y === 1 ? "On" : "Off";
              }
              return `${context.dataset.label}: ${state}`;
            },
          },
        },
      },
    },
    data: {
      datasets: [
        {
          label: entityLabel,
          data: dataPoints,
          stepped: "before",
          fill: false,
          borderWidth: 2,
          pointRadius: 0,
          // 使用 segment 配置動態設定顏色和虛線
          segment: {
            borderColor: (ctx) => {
              if (!ctx.p0) return "rgba(46, 204, 113, 1)";
              const value = ctx.p0.parsed.y;
              if (value === UNAVAILABLE_VALUE || value <= -1) return UNAVAILABLE_COLOR;
              return "rgba(46, 204, 113, 1)";
            },
            borderDash: (ctx) => {
              if (!ctx.p0) return [];
              const value = ctx.p0.parsed.y;
              if (value === UNAVAILABLE_VALUE || value <= -1) return UNAVAILABLE_DASH_PATTERN;
              return [];
            },
          },
        },
      ],
    },
  };
}

/**
 * 將單一 entity 的 records 轉為分類狀態圖表資料 (Stepped Line with Colors)
 * @param {object[]} records
 * @param {string} entityLabel
 * @param {string} domain
 * @returns {object}
 */
function parseCategoricalChartData(records, entityLabel, domain) {
  records.sort(
    (a, b) =>
      new Date(a.last_changed).getTime() - new Date(b.last_changed).getTime()
  );

  const stateMap = CATEGORICAL_STATE_MAPS[domain] || {};
  const colorMap = CATEGORICAL_COLOR_MAPS[domain] || {};
  const stateLabels = getStateLabels(domain);

  // 使用 {x, y} 格式支援 Time Scale，並處理 unavailable 狀態
  const rawDataPoints = records.map((record) => {
    const state = record.entity_state;
    let yValue;
    if (isUnavailableState(state)) {
      yValue = UNAVAILABLE_VALUE;
    } else {
      yValue = stateMap[state] ?? -1;
    }
    return {
      x: parseTimestamp(record.last_changed),
      y: yValue,
    };
  });

  // 擴展數據點以正確顯示狀態持續時間
  const dataPoints = expandStateDataPoints(rawDataPoints);

  // 計算 Y 軸範圍（排除 unavailable 值）
  const validValues = rawDataPoints.map((p) => p.y).filter((v) => v >= 0);
  const hasUnavailable = rawDataPoints.some((p) => p.y === UNAVAILABLE_VALUE);
  const minVal = validValues.length > 0 ? Math.min(...validValues) : 0;
  const maxVal = validValues.length > 0 ? Math.max(...validValues) : 1;
  // 如果有 unavailable 狀態，擴展 Y 軸下限以顯示
  const yMin = hasUnavailable ? -1.5 : minVal - 0.5;

  return {
    type: "line",
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: getTimeScaleConfig(),
        y: {
          min: yMin,
          max: maxVal + 0.5,
          ticks: {
            stepSize: 1,
            callback: function (value) {
              if (value === UNAVAILABLE_VALUE || value === -1) return "N/A";
              return stateLabels[value] || "";
            },
          },
        },
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: function (context) {
              const stateValue = context.parsed.y;
              if (stateValue === UNAVAILABLE_VALUE || stateValue < 0) {
                return `${context.dataset.label}: Unavailable`;
              }
              const stateName = stateLabels[stateValue] || stateValue;
              return `${context.dataset.label}: ${stateName}`;
            },
          },
        },
      },
    },
    data: {
      datasets: [
        {
          label: entityLabel,
          data: dataPoints,
          stepped: "before",
          fill: false,
          borderWidth: 3,
          pointRadius: 4,
          pointHoverRadius: 6,
          segment: {
            borderColor: (ctx) => {
              if (!ctx.p0) return colorMap[0] || "#95a5a6";
              const value = Math.round(ctx.p0.parsed.y);
              // unavailable 狀態使用灰色
              if (value === UNAVAILABLE_VALUE || value < 0) return UNAVAILABLE_COLOR;
              return colorMap[value] || "#95a5a6";
            },
            borderDash: (ctx) => {
              if (!ctx.p0) return [];
              const value = Math.round(ctx.p0.parsed.y);
              // unavailable 狀態使用虛線
              if (value === UNAVAILABLE_VALUE || value < 0) return UNAVAILABLE_DASH_PATTERN;
              return [];
            },
          },
          pointBackgroundColor: (ctx) => {
            const value = ctx.parsed?.y;
            if (value === UNAVAILABLE_VALUE || value < 0) return UNAVAILABLE_COLOR;
            return colorMap[value] || "#95a5a6";
          },
        },
      ],
    },
  };
}

/**
 * 根據 domain 自動選擇圖表類型並渲染
 * @param {object[]} records
 * @param {string} entityLabel
 * @returns {object}
 */
function parseRecordToSingleChartData(records, entityLabel) {
  if (!records || records.length === 0) {
    return null;
  }

  // 從第一筆記錄取得 domain
  const domain = records[0]?.domain;
  const stateType = getStateType(domain);

  debug(
    "<HaHistoryRenderer/>",
    "parseRecordToSingleChartData",
    "domain",
    domain,
    "stateType",
    stateType
  );

  switch (stateType) {
    case "binary":
      return parseBinaryTimelineData(records, entityLabel);  // 使用 Timeline 區塊風格
    case "categorical":
      return parseCategoricalTimelineData(records, entityLabel, domain);  // 使用 Timeline 區塊風格
    case "text":
      return parseTextTimelineData(records, entityLabel);  // 文字狀態使用動態顏色 Timeline
    case "numeric":
    default:
      return parseNumericChartData(records, entityLabel);  // 保持 Line Chart
  }
}

/**
 * 將 records 按 entity 分組
 * @param {{entity_name: string, entity_id_string: string}[]} records
 * @returns {Record<string, object[]>}
 */
function groupRecordsByEntity(records) {
  return records.reduce((acc, record) => {
    const entityId = `${record.entity_name || "unknown"}(${record.entity_id_string})`;
    if (!acc[entityId]) {
      acc[entityId] = [];
    }
    acc[entityId].push(record);
    return acc;
  }, {});
}

export class HaHistoryRenderer extends Component {
  static template = "odoo_ha_addon.HaHistoryRenderer";
  static props = {
    model: HaHistoryModel,
    displayMode: { type: String, optional: true },
    setDisplayMode: { type: Function, optional: true },
    updateKey: { type: Number, optional: true },
  };
  static components = { UnifiedChart };
  setup() {
    // displayMode 現在從 props 來（由 Controller 管理）
    this.state = useState({
      // 合併模式：按 domain 分組的圖表 { domain: { title, data } }
      combinedCharts: {},
      // 分開模式：{ entityId: chartData }
      lineCharts: {},
    });

    onWillStart(async () => {
      debug("onWillStart", this.props.model.records);
      this.renderRecords(this.props.model.records);
    });

    onWillUpdateProps(async (nextProps) => {
      // 當 updateKey 或 displayMode 變化時重新渲染
      debug("onWillUpdateProps", "updateKey:", nextProps.updateKey, "records:", nextProps.model.records.length);
      this.renderRecords(nextProps.model.records, nextProps.displayMode);
    });
  }

  toggleDisplayMode() {
    const newMode = this.props.displayMode === "combined" ? "separate" : "combined";
    this.props.setDisplayMode?.(newMode);
    this.renderRecords(this.props.model.records, newMode);
  }

  renderRecords(records, displayModeOverride = null) {
    const displayMode = displayModeOverride || this.props.displayMode || "separate";
    if (displayMode === "combined") {
      // 合併模式：按 domain 分組，同 domain 的 entity 合併到同一個圖表
      const groupedByDomain = groupRecordsByDomain(records);
      const combinedCharts = {};

      for (const [domain, domainRecords] of Object.entries(groupedByDomain)) {
        if (domainRecords.length === 0) continue;

        const stateType = getStateType(domain);
        combinedCharts[domain] = {
          title: DOMAIN_TITLES[domain] || domain,
          data: parseCombinedChartData(domainRecords, stateType),
        };
      }

      debug(
        "<HaHistoryRenderer/>",
        "combined mode",
        "records",
        records,
        "groupedByDomain",
        groupedByDomain,
        "combinedCharts",
        combinedCharts
      );
      this.state.combinedCharts = combinedCharts;
    } else {
      // 分開模式：每個 entity 一個圖表
      const groupedRecords = groupRecordsByEntity(records);
      const lineCharts = {};
      for (const [entityId, entityRecords] of Object.entries(groupedRecords)) {
        lineCharts[entityId] = parseRecordToSingleChartData(
          entityRecords,
          entityId
        );
      }
      debug(
        "<HaHistoryRenderer/>",
        "separate mode",
        "records",
        records,
        "lineCharts",
        lineCharts
      );
      this.state.lineCharts = lineCharts;
    }
  }
}
