/** @odoo-module */

import { registry } from "@web/core/registry";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { EntityKanbanController } from "./entity_kanban_controller";

export const entityKanbanView = {
  ...kanbanView, // contains the default Renderer/Controller/Model
  Controller: EntityKanbanController,
};

// Register it to the views registry
registry.category("views").add("entity_kanban", entityKanbanView);
