/** @odoo-module */

import { KanbanController } from "@web/views/kanban/kanban_controller";

// the controller usually contains the Layout and the renderer.
export class EntityKanbanController extends KanbanController {
  static template = "odoo_ha_addon.EntityKanbanView";

  // Your logic here, override or insert new methods...
  // if you override setup(), don't forget to call super.setup()
}
