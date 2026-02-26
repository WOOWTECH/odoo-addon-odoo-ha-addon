/** @odoo-module */

import { Component, useRef, onMounted, onWillUpdateProps, onPatched, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { debug } from "../../../util/debug";
import { isLightColor } from "../../../util/color";
import { TIMELINE_LABEL_FONT_SIZE } from "../../../constants";

/**
 * 生成 Timeline 圖表的 datalabels 配置
 * 由於 Owl reactive state 會丟失 function，所以在這裡直接定義
 */
function getTimelineDataLabelsConfig() {
  return {
    // 先用 'auto' 讓 plugin 自動決定是否顯示
    // 'auto' 會在空間不足時自動隱藏標籤
    display: 'auto',
    formatter: (value, ctx) => {
      const label = ctx.dataset.label;
      // 確保 label 是字串，避免顯示 [object Object]
      if (label === null || label === undefined) return '';
      if (typeof label === 'object') {
        // 如果是物件，嘗試取得 name 或 display_name
        return label.name || label.display_name || String(label);
      }
      return String(label);
    },
    color: (ctx) => {
      const bgColor = ctx.dataset.backgroundColor;
      return isLightColor(bgColor) ? '#000' : '#fff';
    },
    anchor: 'center',
    align: 'center',
    font: { size: TIMELINE_LABEL_FONT_SIZE, weight: 'bold' },
    clip: true,
  };
}

export class UnifiedChart extends Component {
  static template = "odoo_ha_addon.UnifiedChart";

  static props = {
    type: String,
    data: Object,
    options: Object,
  };

  setup() {
    this.chartRef = useRef("chart");
    this.chartService = useService("chart");
    this.chartInstance = null;

    onMounted(() => {
      debug("UnifiedChart mounted, attempting to render chart...");
      this.tryRenderChart();
    });

    onPatched(() => {
      debug("UnifiedChart patched, checking if chart needs rendering...");
      if (!this.chartInstance && this.props.data) {
        this.tryRenderChart();
      }
    });

    onWillUpdateProps((nextProps) => {
      debug("UnifiedChart props updating...", nextProps);
      if (this.chartInstance) {
        this.updateChart(nextProps);
      } else if (nextProps.data) {
        // If chart doesn't exist but we have data, try to create it
        setTimeout(() => this.tryRenderChart(), 0);
      }
    });

    onWillUnmount(() => {
      debug("UnifiedChart unmounting");
      this.destroyExistingChart();
    });
  }

  /**
   * 確保 canvas 上的圖表被銷毀
   */
  destroyExistingChart() {
    // 1. 先嘗試銷毀我們追蹤的實例
    if (this.chartInstance) {
      debug("Destroying tracked chart instance");
      try {
        this.chartService.destroyChart(this.chartInstance);
      } catch (e) {
        debug("Error destroying tracked chart:", e);
      }
      this.chartInstance = null;
    }

    // 2. 再檢查 canvas 上是否還有殘留的圖表（使用 Chart.getChart）
    if (this.chartRef.el) {
      try {
        const existingChart = Chart.getChart(this.chartRef.el);
        if (existingChart) {
          debug("Found existing chart on canvas, destroying it");
          existingChart.destroy();
        }
      } catch (e) {
        debug("Error checking/destroying canvas chart:", e);
      }
    }
  }

  tryRenderChart() {
    debug("Trying to render chart. El:", this.chartRef.el, "Data:", this.props.data);

    if (!this.chartRef.el) {
      debug("Canvas element not ready");
      return;
    }

    // Time Scale 模式下不需要 labels，只需要 datasets
    if (!this.props.data || !this.props.data.datasets) {
      debug("Chart data not ready or invalid", this.props.data);
      return;
    }

    // 確保銷毀任何現有的圖表
    this.destroyExistingChart();

    try {
      let options = this.props.options || {
        responsive: true,
        maintainAspectRatio: false
      };

      // 對於 Timeline 風格的水平 bar chart，直接套用 datalabels 配置
      // （因為 Owl reactive state 會丟失 function）
      if (this.props.type === 'bar' && options.indexAxis === 'y') {
        options = {
          ...options,
          plugins: {
            ...options.plugins,
            datalabels: getTimelineDataLabelsConfig(),
          },
        };
        debug("Applied Timeline datalabels config");
      }

      const config = {
        type: this.props.type,
        data: this.props.data,
        options: options,
      };

      debug("Creating chart with config:", config);
      this.chartInstance = this.chartService.createChart(this.chartRef.el, config);
      debug("Chart created successfully");
    } catch (error) {
      debug("Failed to create chart:", error);
      console.error("UnifiedChart creation failed:", error);
    }
  }

  updateChart(nextProps) {
    // 檢查 chartInstance 是否有效（有 update 方法）
    if (this.chartInstance && typeof this.chartInstance.update === 'function' && nextProps.data) {
      debug("Updating chart with new data");
      this.chartInstance.data = nextProps.data;
      this.chartInstance.options = nextProps.options || this.chartInstance.options;
      this.chartInstance.update();
    } else if (nextProps.data) {
      // chartInstance 無效，先銷毀再重新創建
      debug("Chart instance invalid, destroying and recreating...");
      this.destroyExistingChart();
      setTimeout(() => this.tryRenderChart(), 0);
    }
  }
}