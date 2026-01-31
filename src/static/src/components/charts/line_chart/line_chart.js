/** @odoo-module */

import { loadJS } from "@web/core/assets";
import {
  Component,
  onWillStart,
  useRef,
  useState,
  onMounted,
  onWillUnmount,
  onWillUpdateProps,
} from "@odoo/owl";

function isEqualData(data1, data2) {
  const keys1 = Object.keys(data1);
  const keys2 = Object.keys(data2);

  if (keys1.length !== keys2.length) {
    return false;
  }

  for (const key of keys1) {
    if (data1[key] !== data2[key]) {
      return false;
    }
  }

  return true;
}
/**
 * data example:
 * {
 *  [label (x axis)]: number
 * }
 *
 * {
 *  '2023-01-01': 10,
 *  '2023-01-02': 20,
 *  '2023-01-03': 30,
 * }
 */
export class LineChart extends Component {
  static template = "odoo_ha_addon.LineChart";
  static props = {
    /**
     * chartjs data
     */
    data: Object,
  };
  setup() {
    this.canvasRef = useRef("canvas");
    this.state = useState({ chart: undefined });
    onWillStart(async () => {
      try {
        await loadJS(["/web/static/lib/Chart/Chart.js"]);
      } catch (error) {
        console.error("Failed to load Chart.js:", error);
      }
    });
    onMounted(() => {
      this.renderChart(this.props, this.state.chart);
    });
    onWillUnmount(() => {
      if (this.state.chart) {
        this.state.chart.destroy();
      }
    });
    onWillUpdateProps((nextProps) => {
      if (isEqualData(this.props.data, nextProps.data)) {
        return;
      }
      this.renderChart(nextProps, this.state.chart);
    });
  }
  renderChart(props, chartRef) {
    const options = props.data;

    if (!chartRef) {
      const newChart = new Chart(this.canvasRef.el, options);
      this.state.chart = newChart;
    } else {
      chartRef.destroy();
      const newChart = new Chart(this.canvasRef.el, options);
      this.state.chart = newChart;
    }
  }
}
