/** @odoo-module */

import { Layout } from "@web/search/layout";
import { useService } from "@web/core/utils/hooks";
import {
  Component,
  onWillStart,
  onWillUpdateProps,
  onWillUnmount,
  useState,
} from "@odoo/owl";
import { standardViewProps } from "@web/views/standard_view_props";
import { SearchBar } from "@web/search/search_bar/search_bar";
import { useSearchBarToggler } from "@web/search/search_bar/search_bar_toggler";
import { useSetupAction } from "@web/search/action_hook";
import { CogMenu } from "@web/search/cog_menu/cog_menu";
import { debug } from "../../util/debug";

export class HaHistoryController extends Component {
  static template = "odoo_ha_addon.HaHistoryController";
  static props = {
    ...standardViewProps,
    archInfo: Object,
    Model: Function,
    Renderer: Function,
  };

  static components = { Layout, SearchBar, CogMenu };

  setup() {
    this.orm = useService("orm");
    this.haDataService = useService("ha_data");
    this.searchBarToggler = useSearchBarToggler();
    debug("<HaHistoryController/> props:", this.props);

    // 從 props.context 讀取初始 displayMode（Dashboard 恢復時會傳入）
    // updateKey 用於強制 renderer 更新（當 model.records 變化時）
    this.state = useState({
      displayMode: this.props.context?.hahistory_displayMode || "separate",
      updateKey: 0,
    });

    this.model = new this.props.Model(this.orm, this.props.resModel, this.props.archInfo, this.haDataService);

    // 整合 Odoo action 系統，讓 Dashboard 能保存/恢復狀態
    useSetupAction({
      getContext: () => ({
        hahistory_displayMode: this.state.displayMode,
      }),
    });

    // 訂閱歷史記錄更新（通過 Service callback）
    this.historyUpdateHandler = async () => {
      debug("HaHistory: Reloading history data");
      await this.model.loadHistory(this.props.domain);
      this.state.updateKey++; // 強制 renderer 更新
    };
    this.haDataService.onGlobalState(
      "history_update",
      this.historyUpdateHandler
    );

    // 訂閱所有實體更新（也需要重新載入歷史）
    this.entityUpdateHandler = async () => {
      debug("HaHistory: Entity updated, clearing cache and reloading");
      this.haDataService.clearCache();
      await this.model.loadHistory(this.props.domain);
      this.state.updateKey++; // 強制 renderer 更新
    };
    this.haDataService.onGlobalState(
      "entity_update_all",
      this.entityUpdateHandler
    );

    // 訂閱實例切換（需要重新載入該實例的歷史記錄）
    this.instanceSwitchedHandler = async ({ instanceId, instanceName }) => {
      debug(`HaHistory: Instance switched to ${instanceName}, reloading history data`);
      this.haDataService.clearCache();
      await this.model.loadHistory(this.props.domain);
      this.state.updateKey++; // 強制 renderer 更新
    };
    this.haDataService.onGlobalState(
      "instance_switched",
      this.instanceSwitchedHandler
    );

    onWillStart(async () => {
      // 若有設定 search domain 的過濾條件，this.props.domain 就會有值
      await this.model.loadHistory(this.props.domain);
    });

    onWillUpdateProps(async (nextProps) => {
      // 若 search domain 的過濾條件有變化
      if (
        JSON.stringify(nextProps.domain) !== JSON.stringify(this.props.domain)
      ) {
        await this.model.loadHistory(nextProps.domain);
        this.state.updateKey++; // 強制 renderer 更新
      }
    });

    // 清理函數
    onWillUnmount(() => {
      this.haDataService.offGlobalState(
        "history_update",
        this.historyUpdateHandler
      );
      this.haDataService.offGlobalState(
        "entity_update_all",
        this.entityUpdateHandler
      );
      this.haDataService.offGlobalState(
        "instance_switched",
        this.instanceSwitchedHandler
      );
      debug("HaHistory: Cleanup complete");
    });
  }

  /**
   * 設置 displayMode（由 Renderer 調用）
   */
  setDisplayMode(mode) {
    this.state.displayMode = mode;
  }
}
