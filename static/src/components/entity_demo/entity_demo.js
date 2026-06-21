/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { Component, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { EntityController } from "../entity_controller/entity_controller";

/**
 * EntityDemo - View widget wrapper for EntityController
 * Used in Odoo views (kanban, list, form) as a widget
 */
export class EntityDemo extends Component {
  static template = "odoo_ha_addon.EntityDemo";
  static components = { EntityController };
  static props = {
    ...standardWidgetProps,
  };

  setup() {
    // Extract entity data from Odoo record format
    const recordData = this.props.record.data;

    // Parse attributes from attributes_str if attributes field is not available
    let attributes = recordData.attributes;
    if (!attributes && recordData.attributes_str) {
      try {
        attributes = JSON.parse(recordData.attributes_str);
      } catch (e) {
        console.warn("[EntityDemo] Failed to parse attributes_str:", e);
        attributes = {};
      }
    }

    this.entityData = {
      ...recordData,
      attributes: attributes || {},
    };

    // Use native DOM to stop click propagation to kanban card.
    // OWL t-on-click.stop is not sufficient because Odoo kanban uses
    // event delegation / global click handlers that bypass OWL propagation.
    this.rootRef = useRef("root");
    this._onClickCapture = (ev) => {
      // Stop the click from reaching the kanban record openRecord handler
      ev.stopPropagation();
    };

    onMounted(() => {
      if (this.rootRef.el) {
        this.rootRef.el.addEventListener("click", this._onClickCapture, true);
      }
    });

    onWillUnmount(() => {
      if (this.rootRef.el) {
        this.rootRef.el.removeEventListener("click", this._onClickCapture, true);
      }
    });
  }
}

export const entityDemo = {
  component: EntityDemo,
};

registry.category("view_widgets").add("entity_demo", entityDemo);
