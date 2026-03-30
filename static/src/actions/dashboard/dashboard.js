/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { DashboardItem } from "../../components/dashboard_item/dashboard_item";
import { GlancesBlock } from "../../components/glances_block/glances_block";
import { rpc } from "@web/core/network/rpc";
import {
  WEBSOCKET_STATUS_REFRESH_MS,
  HARDWARE_INFO_REFRESH_MS,
  NETWORK_INFO_REFRESH_MS,
  HA_URLS_REFRESH_MS,
} from "../../constants";
import { debug, debugWarn } from "../../util/debug";

const { Component, useState, onMounted, onWillUnmount, onWillStart } = owl;

class WoowHaInfoDashboard extends Component {
  static template = "odoo_ha_addon.Dashboard";
  static components = { DashboardItem, GlancesBlock };
  static props = {
    action: { type: Object, optional: true },
    "*": true, // Allow additional standard props from Odoo action system
  };

  setup() {
    // 從 action context 接收 instance_id 參數
    this.instanceId = this.props.action?.context?.ha_instance_id || null;
    debug('[WoowHaInfoDashboard] Initialized with instance_id:', this.instanceId);

    // ⚠️ instanceValidated 標記：避免重複驗證
    this.instanceValidated = false;

    // ⚠️ Phase 2.2: Breadcrumb Navigation
    this.actionService = useService("action");
    this.currentInstanceName = null;

    this.state = useState({
      websocket: {
        connected: false,
        url: '載入中...',
        lastUpdate: '載入中...',
        error: null,
        configSynced: true,
        restarting: false,
      },
      hardware: {
        loading: true,
        error: null,
        data: null,
      },
      network: {
        loading: true,
        error: null,
        data: null,
      },
      haUrls: {
        loading: true,
        error: null,
        data: null,
      },
    });
    this.haDataService = useService("ha_data");

    // 訂閱 WebSocket 狀態變更（通過 Service callback）
    this.wsStatusHandler = ({ status, message }) => {
      debug('Dashboard: HA WebSocket Status', status, message);
      if (status === 'connected') {
        this.state.websocket.connected = true;
        this.state.websocket.error = null;
      } else if (status === 'disconnected') {
        this.state.websocket.connected = false;
        this.state.websocket.error = message;
      }
    };
    this.haDataService.onGlobalState('websocket_status', this.wsStatusHandler);

    // 訂閱所有實體更新事件（用於清除快取）
    this.entityUpdateHandler = () => {
      debug('Dashboard: Entity updated, clearing cache');
      this.haDataService.clearCache();
    };
    this.haDataService.onGlobalState('entity_update_all', this.entityUpdateHandler);

    // ⚠️ 移除了 instance_switched 事件訂閱
    // 此頁面現在專注於顯示特定 instance 的數據（通過 context 傳遞）
    // 不再響應 systray 切換事件

    onWillStart(async () => {
      // ⚠️ Phase 1.2: 驗證 instance_id 是否有效
      // 避免用戶點擊 Instance A 卻看到 Instance B 的數據（因為 backend fallback）
      if (this.instanceId && !this.instanceValidated) {
        const isValid = await this.validateInstanceId(this.instanceId);
        if (!isValid) {
          debugWarn('[WoowHaInfoDashboard] Invalid instance_id:', this.instanceId);
          this.haDataService.showWarning(
            '您嘗試存取的實例不存在或已停用，已切換至預設實例'
          );
          this.instanceId = null; // 讓後端使用 fallback
        }
        this.instanceValidated = true;
      }

      // ⚠️ Phase 2.2: 載入實例名稱（用於麵包屑導航）
      if (this.instanceId) {
        const result = await this.haDataService.getInstances();
        if (result.success) {
          const instance = result.data.instances.find(inst => inst.id === this.instanceId);
          this.currentInstanceName = instance?.name || 'Unknown';
          debug('[WoowHaInfoDashboard] Instance name:', this.currentInstanceName);
        }
      }
    });

    onMounted(() => {
      // 並行加載所有初始數據
      Promise.all([
        this.loadWebSocketStatus(),
        this.loadHardwareInfo(),
        this.loadNetworkInfo(),
        this.loadHaUrls(),
      ]).catch((error) => {
        console.error('Failed to load initial dashboard data:', error);
      });

      // 定時更新 WebSocket 狀態
      this.interval = setInterval(() => {
        this.loadWebSocketStatus();
      }, WEBSOCKET_STATUS_REFRESH_MS);

      // 定時更新硬體資訊
      this.hardwareInterval = setInterval(() => {
        this.loadHardwareInfo();
      }, HARDWARE_INFO_REFRESH_MS);

      // 定時更新網路資訊
      this.networkInterval = setInterval(() => {
        this.loadNetworkInfo();
      }, NETWORK_INFO_REFRESH_MS);

      // 定時更新 HA URLs 資訊
      this.haUrlsInterval = setInterval(() => {
        this.loadHaUrls();
      }, HA_URLS_REFRESH_MS);
    });

    // 清理函數
    onWillUnmount(() => {
      // 清理 callbacks
      this.haDataService.offGlobalState('websocket_status', this.wsStatusHandler);
      this.haDataService.offGlobalState('entity_update_all', this.entityUpdateHandler);
      // ⚠️ 已移除 instanceSwitchedHandler 清理（不再訂閱該事件）

      // 清理 intervals
      if (this.interval) {
        clearInterval(this.interval);
      }
      if (this.hardwareInterval) {
        clearInterval(this.hardwareInterval);
      }
      if (this.networkInterval) {
        clearInterval(this.networkInterval);
      }
      if (this.haUrlsInterval) {
        clearInterval(this.haUrlsInterval);
      }

      debug('Dashboard: Cleanup complete');
    });
  }

  // ⚠️ 已移除 reloadAllData() 方法
  // 此頁面現在只顯示特定 instance 的數據，不再響應切換事件

  /**
   * 返回到 HA Instance Dashboard 入口頁
   *
   * ⚠️ Phase 2.2: Breadcrumb Navigation
   * 當用戶點擊麵包屑中的「Instances」鏈接時呼叫。
   */
  goBackToInstances() {
    debug('[WoowHaInfoDashboard] Navigating back to instances...');

    this.actionService.doAction({
      type: 'ir.actions.client',
      tag: 'odoo_ha_addon.ha_instance_dashboard',
      name: 'Home Assistant 實例',
    });
  }

  /**
   * 驗證 instance_id 是否有效
   *
   * ⚠️ Phase 1.2: Instance ID Validation
   * 檢查指定的 instance_id 是否存在且為啟用狀態。
   * 避免用戶點擊實例 A 的按鈕，卻因為 backend fallback 看到實例 B 的數據。
   *
   * @param {number} instanceId - 要驗證的實例 ID
   * @returns {Promise<boolean>} 是否為有效的實例 ID
   */
  async validateInstanceId(instanceId) {
    try {
      const result = await this.haDataService.getInstances();
      if (result.success) {
        const instance = result.data.instances.find(inst => inst.id === instanceId);
        return instance && instance.is_active;
      }
      return false;
    } catch (error) {
      console.error('[WoowHaInfoDashboard] Error validating instance_id:', error);
      return false;
    }
  }

  async loadWebSocketStatus() {
    try {
      // 使用新的 websocket_status API，傳遞 instance_id 參數
      const params = this.instanceId ? { ha_instance_id: this.instanceId } : {};
      const result = await rpc("/odoo_ha_addon/websocket_status", params);

      if (result.success) {
        this.state.websocket.connected = result.data.is_running;
        this.state.websocket.url = result.data.current_url || "未設定";
        this.state.websocket.configSynced = result.data.config_synced;
        this.state.websocket.lastUpdate = result.data.status_text;
        this.state.websocket.error = null;
      } else {
        this.state.websocket.connected = false;
        this.state.websocket.lastUpdate = "未啟動";
        this.state.websocket.error = result.error;
      }

    } catch (error) {
      console.error("Failed to load WebSocket status:", error);
      this.state.websocket.error = error.message;
    }
  }

  async restartWebSocket(force = false) {
    try {
      this.state.websocket.restarting = true;

      // 傳遞 instance_id 參數（如果有）
      const params = { force: force };
      if (this.instanceId) {
        params.ha_instance_id = this.instanceId;
      }

      const result = await rpc("/odoo_ha_addon/websocket_restart", params);

      if (result.success) {
        // 顯示成功訊息（從 data.message 讀取）
        debug(result.data?.message || 'WebSocket restarted successfully');
        // 清除之前的錯誤訊息
        this.state.websocket.error = null;
        // 立即更新狀態
        await this.loadWebSocketStatus();
      } else {
        // 檢查是否因為冷卻時間被跳過
        if (result.skipped) {
          debugWarn(`WebSocket restart skipped: ${result.error}`);
          // 詢問使用者是否要強制重啟
          const userConfirmed = confirm(
            `${result.error}\n\n是否要強制重啟？（忽略冷卻時間）`
          );
          if (userConfirmed) {
            // 遞迴呼叫，但設定 force = true
            return await this.restartWebSocket(true);
          }
        }
        this.state.websocket.error = result.error;
      }
    } catch (error) {
      console.error("Failed to restart WebSocket:", error);
      this.state.websocket.error = error.message;
    } finally {
      this.state.websocket.restarting = false;
    }
  }

  /**
   * 載入硬體資訊
   *
   * ⚠️ Instance Selection (Updated):
   * 此方法現在傳遞明確的 ha_instance_id 參數。
   * 該 instance_id 從 action context 接收，不再依賴 session。
   * 如果 instanceId 為 null，後端會自動使用 session fallback。
   */
  async loadHardwareInfo() {
    try {
      this.state.hardware.loading = true;
      this.state.hardware.error = null;

      const params = this.instanceId ? { ha_instance_id: this.instanceId } : {};
      const result = await rpc("/odoo_ha_addon/hardware_info", params);

      if (result.success) {
        this.state.hardware.data = result.data;
      } else {
        this.state.hardware.error = result.error || '無法取得硬體資訊';
      }
    } catch (error) {
      console.error("Failed to load hardware info:", error);
      this.state.hardware.error = error.message || '載入失敗';
    } finally {
      this.state.hardware.loading = false;
    }
  }

  /**
   * 載入網路資訊
   *
   * ⚠️ Instance Selection (Updated):
   * 此方法現在傳遞明確的 ha_instance_id 參數。
   * 該 instance_id 從 action context 接收，不再依賴 session。
   * 如果 instanceId 為 null，後端會自動使用 session fallback。
   */
  async loadNetworkInfo() {
    try {
      this.state.network.loading = true;
      this.state.network.error = null;

      const params = this.instanceId ? { ha_instance_id: this.instanceId } : {};
      const result = await rpc("/odoo_ha_addon/network_info", params);

      if (result.success) {
        this.state.network.data = result.data;
      } else {
        this.state.network.error = result.error || '無法取得網路資訊';
      }
    } catch (error) {
      console.error("Failed to load network info:", error);
      this.state.network.error = error.message || '載入失敗';
    } finally {
      this.state.network.loading = false;
    }
  }

  /**
   * 載入 HA URLs（internal/external/cloud）
   *
   * ⚠️ Instance Selection (Updated):
   * 此方法現在傳遞明確的 ha_instance_id 參數。
   * 該 instance_id 從 action context 接收，不再依賴 session。
   * 如果 instanceId 為 null，後端會自動使用 session fallback。
   */
  async loadHaUrls() {
    try {
      this.state.haUrls.loading = true;
      this.state.haUrls.error = null;

      const params = this.instanceId ? { ha_instance_id: this.instanceId } : {};
      const result = await rpc("/odoo_ha_addon/ha_urls", params);

      if (result.success) {
        this.state.haUrls.data = result.data;
      } else {
        this.state.haUrls.error = result.error || '無法取得 URL 資訊';
      }
    } catch (error) {
      console.error("Failed to load HA URLs:", error);
      this.state.haUrls.error = error.message || '載入失敗';
    } finally {
      this.state.haUrls.loading = false;
    }
  }

  formatSize(bytes) {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }
}

registry.category("actions").add("odoo_ha_addon.ha_info_dashboard", WoowHaInfoDashboard);
