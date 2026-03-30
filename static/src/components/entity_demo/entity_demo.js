/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { Component } from "@odoo/owl";
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
    // This happens in form views where only attributes_str (Text field) is defined
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
  }
}

export const entityDemo = {
  component: EntityDemo,
};

registry.category("view_widgets").add("entity_demo", entityDemo);
