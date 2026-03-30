/** @odoo-module **/

const { Component } = owl;

export class DashboardItem extends Component {
  static template = "odoo_ha_addon.DashboardItem";
  static props = {
    size: { type: Number, optional: true },
    fullWidth: { type: Boolean, optional: true },
    slots: { type: Object, optional: true },
  };
  static defaultProps = {
    size: 1,
    fullWidth: false,
  };
}
