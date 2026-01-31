/** @odoo-module **/
import { loadJS } from "@web/core/assets";
import {
  Component,
  onMounted,
  useRef,
  onWillStart,
  onWillUpdateProps,
} from "@odoo/owl";

// import { Chart } from "chart.js/auto";

export class HAChart extends Component {
  static template = "odoo_ha_addon.HAChart";
  static props = {
    data: Object,
    options: Object,
  };
  canvasRef = useRef("canvas_root");

  setup() {
    this.chart = null;

    onWillStart(() => loadJS(["/web/static/lib/Chart/Chart.js"]));

    onMounted(() => this.renderChart(this.props));

    onWillUpdateProps(async (nextProps) => {
      if (JSON.stringify(nextProps) !== JSON.stringify(this.props)) {
        this.renderChart(nextProps);
      }
    });
  }

  renderChart(props) {
    const ctx = this.canvasRef.el.getContext("2d");
    this.chart = new Chart(ctx, {
      type: "line",
      data: props.data,
      options: props.options,
    });
  }
}
