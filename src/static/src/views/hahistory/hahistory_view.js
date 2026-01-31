/** @odoo-module */

import { registry } from "@web/core/registry";
import { debug } from "../../util/debug";
import { HaHistoryController } from "./hahistory_controller";
import { HaHistoryArchParser } from "./hahistory_arch_parser";
import { HaHistoryRenderer } from "./hahistory_renderer";
import { HaHistoryModel } from "./hahistory_model";

debug("Loading hahistory view dependencies...");
debug("HaHistoryController:", HaHistoryController);
debug("HaHistoryArchParser:", HaHistoryArchParser);
debug("HaHistoryRenderer:", HaHistoryRenderer);
debug("HaHistoryModel:", HaHistoryModel);

export const haHistoryView = {
  type: "hahistory",
  display_name: "HaHistory",
  icon: "fa fa-line-chart",
  multiRecord: true,
  searchMenuTypes: ["filter", "groupBy", "favorite"], // 這和預設值一樣
  Controller: HaHistoryController,
  ArchParser: HaHistoryArchParser,
  Model: HaHistoryModel,
  Renderer: HaHistoryRenderer,

  props(genericProps, view) {
    debug("hahistory props called with:", genericProps, view);
    const { ArchParser } = view;
    const { arch } = genericProps;
    const archInfo = new ArchParser().parse(arch);

    // 會送給 <HaHistoryController/> 的 props
    return {
      ...genericProps,
      Model: view.Model,
      Renderer: view.Renderer,
      archInfo,
    };
  },
};

debug("About to register hahistory view...");
debug("Registry available:", registry);
debug("Views category:", registry.category("views"));

try {
  registry.category("views").add("hahistory", haHistoryView);
  debug("✅ hahistory view registered successfully!");

  // Verify registration
  const registered = registry.category("views").get("hahistory");
  debug("✅ Verification - registered view:", registered);
} catch (error) {
  console.error("❌ Failed to register hahistory view:", error);
  throw error;
}
