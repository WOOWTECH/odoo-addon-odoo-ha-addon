/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService, useBus } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { debug } from "../util/debug";

/**
 * Home Assistant Bus Bridge
 * 統一訂閱所有 Odoo Bus 事件，轉發給 HaDataService 處理
 *
 * Phase 3.1: 新增 Session 失效通知訂閱
 *
 * 這個組件在 App 層級只會有一個實例，避免重複訂閱
 * 採用 Bus → Service → Component 的單向資料流架構
 */
export class HaBusBridge extends Component {
  static template = "odoo_ha_addon.HaBusBridge";

  setup() {
    const haDataService = useService("ha_data");
    const busService = useService("bus_service");

    // CRITICAL: Odoo 的 partner channel 會自動訂閱，但我們需要訂閱通知類型
    // 使用 bus_service.subscribe() 而不是 useBus()

    debug('[HaBusBridge] Setting up bus subscriptions...');
    debug('[HaBusBridge] busService:', busService);

    // 訂閱 HA 通知類型
    busService.subscribe('ha_entity_update', (payload) => {
      debug('[HaBusBridge] Received ha_entity_update:', payload);
      haDataService.handleEntityUpdate(payload);
    });

    busService.subscribe('ha_state_changed', (payload) => {
      debug('[HaBusBridge] Received ha_state_changed:', payload);
      haDataService.handleStateChanged(payload);
    });

    busService.subscribe('ha_websocket_status', (payload) => {
      debug('[HaBusBridge] Received ha_websocket_status:', payload);
      haDataService.handleServiceStatus(payload);
    });

    busService.subscribe('ha_history_update', (payload) => {
      debug('[HaBusBridge] Received ha_history_update:', payload);
      haDataService.handleHistoryUpdate(payload);
    });

    // Phase 3.1: 訂閱實例失效通知
    busService.subscribe('instance_invalidated', (payload) => {
      debug('[HaBusBridge] Received instance_invalidated:', payload);
      haDataService.handleInstanceInvalidated(payload);
    });

    // Phase 3.1: 訂閱實例降級通知
    busService.subscribe('instance_fallback', (payload) => {
      debug('[HaBusBridge] Received instance_fallback:', payload);
      haDataService.handleInstanceFallback(payload);
    });

    // Phase 3.3: 訂閱實例切換通知（多標籤頁同步）
    busService.subscribe('instance_switched', (payload) => {
      debug('[HaBusBridge] Received instance_switched (Bus):', payload);
      haDataService.handleInstanceSwitched(payload);
    });

    // 訂閱設備註冊變更通知（用於 Glances 快取失效）
    busService.subscribe('ha_device_registry_updated', (payload) => {
      debug('[HaBusBridge] Received ha_device_registry_updated:', payload);
      haDataService.handleDeviceRegistryUpdated(payload);
    });

    // 訂閱區域註冊變更通知（用於 Area Dashboard 快取失效）
    busService.subscribe('ha_area_registry_updated', (payload) => {
      debug('[HaBusBridge] Received ha_area_registry_updated:', payload);
      haDataService.handleAreaRegistryUpdated(payload);
    });

    // 啟動 bus service
    busService.start();

    debug('[HaBusBridge] Centralized bus listeners setup complete');
  }
}

// 註冊為全域組件，確保在 App 啟動時自動載入
registry.category("main_components").add("ha_bus_bridge", {
  Component: HaBusBridge,
});
