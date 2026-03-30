/** @odoo-module **/

import { loadJS } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { debug, debugWarn } from "../util/debug";

// Chart.js 會在 loadJS 後成為全域變數

/**
 * 圖表服務
 * 統一管理 Chart.js 實例，避免重複創建和銷毀
 */
export class ChartService {
  constructor() {
    this.chartInstances = new Map();
    this.isChartJSLoaded = false;
  }

  /**
   * 確保 Chart.js 已載入
   */
  async ensureChartJSLoaded() {
    if (!this.isChartJSLoaded) {
      try {
        // 載入 Chart.js（必須先載入）
        await loadJS("/web/static/lib/Chart/Chart.js");
        // 載入 luxon adapter（支援 Time Scale，必須在 Chart.js 之後載入）
        await loadJS("/web/static/lib/chartjs-adapter-luxon/chartjs-adapter-luxon.js");
        // 載入 datalabels plugin（支援在圖表上顯示文字標籤）
        await loadJS("/odoo_ha_addon/static/lib/chartjs-plugin-datalabels/chartjs-plugin-datalabels.min.js");

        // 註冊 datalabels plugin（Chart.js 3.x+ 需要明確註冊）
        if (window.Chart && window.ChartDataLabels) {
          window.Chart.register(window.ChartDataLabels);
          debug("ChartDataLabels plugin registered");
        }

        this.isChartJSLoaded = true;
      } catch (error) {
        console.error("Failed to load Chart.js:", error);
        throw error;
      }
    }
  }

  /**
   * 創建圖表 - 支援兩種調用方式
   * 1. createChart(chartId, canvasEl, config) - 傳統方式，需要 chartId
   * 2. createChart(canvasEl, config) - 簡化方式，自動生成 chartId
   * @param {string|HTMLCanvasElement} chartIdOrCanvasEl - 圖表唯一標識或 Canvas 元素
   * @param {HTMLCanvasElement|Object} canvasElOrConfig - Canvas 元素或 Chart.js 配置
   * @param {Object} [config] - Chart.js 配置（當第一個參數是 chartId 時使用）
   * @returns {Object} Chart.js 實例
   */
  async createChart(chartIdOrCanvasEl, canvasElOrConfig, config) {
    await this.ensureChartJSLoaded();

    let chartId, canvasEl, chartConfig;

    // 判斷調用方式
    if (typeof chartIdOrCanvasEl === 'string') {
      // 傳統方式: createChart(chartId, canvasEl, config)
      chartId = chartIdOrCanvasEl;
      canvasEl = canvasElOrConfig;
      chartConfig = config;
    } else {
      // 簡化方式: createChart(canvasEl, config)
      canvasEl = chartIdOrCanvasEl;
      chartConfig = canvasElOrConfig;
      // 自動生成 chartId
      chartId = `chart_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    // 如果已存在，先銷毀
    if (this.chartInstances.has(chartId)) {
      this.destroyChart(chartId);
    }

    // 確保 Chart.js 在全域可用
    if (typeof window.Chart === 'undefined') {
      throw new Error('Chart.js is not loaded or available globally');
    }

    const chart = new window.Chart(canvasEl, chartConfig);
    this.chartInstances.set(chartId, chart);

    // 為 chart 實例添加 chartId 屬性，方便後續銷毀
    chart._chartId = chartId;

    return chart;
  }

  /**
   * 更新圖表數據
   * @param {string} chartId - 圖表 ID
   * @param {Object} newData - 新數據
   * @param {string} animationMode - 動畫模式 ('none', 'active', 'resize')
   */
  updateChart(chartId, newData, animationMode = 'none') {
    const chart = this.chartInstances.get(chartId);
    if (!chart) {
      debugWarn(`Chart with ID ${chartId} not found`);
      return;
    }

    // 深度更新數據
    Object.assign(chart.data, newData);
    chart.update(animationMode);
  }

  /**
   * 更新圖表選項
   * @param {string} chartId - 圖表 ID
   * @param {Object} newOptions - 新選項
   */
  updateChartOptions(chartId, newOptions) {
    const chart = this.chartInstances.get(chartId);
    if (!chart) {
      debugWarn(`Chart with ID ${chartId} not found`);
      return;
    }

    Object.assign(chart.options, newOptions);
    chart.update('none');
  }

  /**
   * 獲取圖表實例
   * @param {string} chartId - 圖表 ID
   * @returns {Object|undefined} Chart.js 實例
   */
  getChart(chartId) {
    return this.chartInstances.get(chartId);
  }

  /**
   * 銷毀圖表 - 支援圖表實例或 chartId
   * @param {string|Object} chartIdOrInstance - 圖表 ID 或圖表實例
   */
  destroyChart(chartIdOrInstance) {
    let chartId, chart;

    if (typeof chartIdOrInstance === 'string') {
      // 傳入的是 chartId
      chartId = chartIdOrInstance;
      chart = this.chartInstances.get(chartId);
    } else if (chartIdOrInstance && chartIdOrInstance._chartId) {
      // 傳入的是圖表實例
      chart = chartIdOrInstance;
      chartId = chart._chartId;
    } else {
      debugWarn('Invalid chart identifier passed to destroyChart');
      return;
    }

    if (chart) {
      chart.destroy();
      this.chartInstances.delete(chartId);
    }
  }

  /**
   * 銷毀所有圖表
   */
  destroyAllCharts() {
    for (const [, chart] of this.chartInstances) {
      chart.destroy();
    }
    this.chartInstances.clear();
  }

  /**
   * 生成預設的圖表配置
   * @param {string} type - 圖表類型
   * @param {Object} data - 數據
   * @param {Object} customOptions - 自定義選項
   * @returns {Object} 圖表配置
   */
  getDefaultConfig(type = 'line', data = {}, customOptions = {}) {
    const defaultOptions = {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index',
      },
      plugins: {
        tooltip: {
          enabled: true,
          position: 'nearest',
        },
        legend: {
          display: true,
          position: 'top',
        }
      },
      scales: {
        x: {
          display: true,
          title: {
            display: false
          }
        },
        y: {
          display: true,
          title: {
            display: false
          }
        }
      }
    };

    // 根據圖表類型調整配置
    if (type === 'line') {
      defaultOptions.elements = {
        line: {
          tension: 0.1
        },
        point: {
          radius: 3,
          hoverRadius: 6
        }
      };
    }

    return {
      type,
      data,
      options: { ...defaultOptions, ...customOptions }
    };
  }
}

export const chartService = {
  dependencies: [],
  start() {
    return new ChartService();
  },
};

registry.category("services").add("chart", chartService);