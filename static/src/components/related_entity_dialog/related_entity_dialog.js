/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/**
 * RelatedEntityDialog - 顯示 Entity 相關資訊的 Dialog
 *
 * 顯示與指定 entity 相關的：
 * - Area (區域)
 * - Device (裝置)
 * - Labels (標籤)
 * - Automations (自動化)
 *
 * 點擊各項目可跳轉到對應的 Odoo 記錄
 */
export class RelatedEntityDialog extends Component {
  static template = "odoo_ha_addon.RelatedEntityDialog";
  static components = { Dialog };
  static props = {
    close: { type: Function },
    entityId: { type: String },
    entityName: { type: String, optional: true },
  };

  setup() {
    this.actionService = useService("action");
    this.haDataService = useService("ha_data");

    this.state = useState({
      isLoading: true,
      error: null,
      area: null,
      device: null,
      labels: [],
      automations: [],
      scenes: [],
      scripts: [],
    });

    onWillStart(async () => {
      await this.loadRelatedData();
    });
  }

  async loadRelatedData() {
    try {
      this.state.isLoading = true;
      this.state.error = null;

      const result = await this.haDataService.getEntityRelated(
        this.props.entityId
      );

      if (result.success) {
        this.state.area = result.data.area;
        this.state.device = result.data.device;
        this.state.labels = result.data.labels || [];
        this.state.automations = result.data.automations || [];
        this.state.scenes = result.data.scenes || [];
        this.state.scripts = result.data.scripts || [];
      } else {
        this.state.error = result.error;
      }
    } catch (error) {
      console.error("Failed to load related data:", error);
      this.state.error = error.message;
    } finally {
      this.state.isLoading = false;
    }
  }

  get dialogTitle() {
    const name = this.props.entityName || this.props.entityId;
    return _t("Related: %s").replace("%s", name);
  }

  get hasNoRelatedItems() {
    return (
      !this.state.area &&
      !this.state.device &&
      this.state.labels.length === 0 &&
      this.state.automations.length === 0 &&
      this.state.scenes.length === 0 &&
      this.state.scripts.length === 0
    );
  }

  // 導航方法 - 使用預定義 action ID（F5 refresh 時可從 DB 讀取 action name）
  async onAreaClick() {
    if (this.state.area) {
      this.props.close();
      await this.actionService.doAction("odoo_ha_addon.ha_area_action", {
        props: { resId: this.state.area.id },
        viewType: "form",
      });
    }
  }

  async onDeviceClick() {
    if (this.state.device) {
      this.props.close();
      await this.actionService.doAction("odoo_ha_addon.ha_device_action", {
        props: { resId: this.state.device.id },
        viewType: "form",
      });
    }
  }

  async onLabelClick(label) {
    this.props.close();
    await this.actionService.doAction("odoo_ha_addon.ha_label_action", {
      props: { resId: label.id },
      viewType: "form",
    });
  }

  async onAutomationClick(automation) {
    this.props.close();
    await this.actionService.doAction("odoo_ha_addon.entity_action", {
      props: { resId: automation.id },
      viewType: "form",
    });
  }

  async onSceneClick(scene) {
    this.props.close();
    await this.actionService.doAction("odoo_ha_addon.entity_action", {
      props: { resId: scene.id },
      viewType: "form",
    });
  }

  async onScriptClick(script) {
    this.props.close();
    await this.actionService.doAction("odoo_ha_addon.entity_action", {
      props: { resId: script.id },
      viewType: "form",
    });
  }

  onClose() {
    this.props.close();
  }
}
