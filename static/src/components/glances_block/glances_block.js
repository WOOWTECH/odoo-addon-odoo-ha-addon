/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { GLANCES_REFRESH_MS } from "../../constants";
import { debug } from "../../util/debug";

const { Component, useState, onMounted, onWillUnmount } = owl;

/**
 * GlancesBlock - 顯示 Glances 設備列表的區塊組件
 *
 * 用於在 HA Info 頁面中顯示所有 Glances 設備，
 * 點擊設備卡片可進入該設備的詳細儀表板。
 */
export class GlancesBlock extends Component {
  static template = "odoo_ha_addon.GlancesBlock";
  static props = {
    instanceId: { type: Number, optional: true },
    onDeviceClick: { type: Function, optional: true },
  };

  setup() {
    this.haDataService = useService("ha_data");
    this.actionService = useService("action");

    this.state = useState({
      loading: true,
      error: null,
      devices: [],
    });

    // 定時更新設備狀態
    this.refreshInterval = null;

    // 設備註冊變更回調（用於即時刷新）
    this.onDeviceRegistryUpdate = () => this.loadGlancesDevices();

    onMounted(async () => {
      await this.loadGlancesDevices();

      // 定時刷新設備列表
      this.refreshInterval = setInterval(() => {
        this.loadGlancesDevices();
      }, GLANCES_REFRESH_MS);

      // 訂閱設備註冊變更事件（即時刷新）
      this.haDataService.onGlobalState(
        "device_registry_updated",
        this.onDeviceRegistryUpdate
      );
    });

    onWillUnmount(() => {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
      }

      // 取消訂閱設備註冊變更事件
      this.haDataService.offGlobalState(
        "device_registry_updated",
        this.onDeviceRegistryUpdate
      );
    });
  }

  /**
   * 載入 Glances 設備列表
   */
  async loadGlancesDevices() {
    try {
      this.state.loading = true;
      this.state.error = null;

      const result = await this.haDataService.getGlancesDevices(this.props.instanceId);

      if (result.success) {
        this.state.devices = result.data.devices || [];
      } else {
        this.state.error = result.error || 'Failed to load Glances devices';
      }
    } catch (error) {
      console.error('[GlancesBlock] Failed to load devices:', error);
      this.state.error = error.message || 'Failed to load Glances devices';
    } finally {
      this.state.loading = false;
    }
  }

  /**
   * 處理設備點擊事件
   * @param {Object} device - 被點擊的設備
   */
  onDeviceCardClick(device) {
    debug('[GlancesBlock] Device clicked:', device);

    if (this.props.onDeviceClick) {
      this.props.onDeviceClick(device);
    } else {
      // 導航到 Glances 設備儀表板
      this.actionService.doAction({
        type: 'ir.actions.client',
        tag: 'odoo_ha_addon.glances_device_dashboard',
        name: device.name || 'Glances Dashboard',
        context: {
          ha_instance_id: this.props.instanceId,
          device_id: device.id,
          device_name: device.name,
        },
      });
    }
  }

  /**
   * 取得設備的圖示
   * @param {Object} device - 設備資訊
   * @returns {string} Font Awesome 圖示類名
   */
  getDeviceIcon(device) {
    return 'fa fa-server';
  }

  /**
   * 格式化版本號
   * @param {string} version - 版本號
   * @returns {string} 格式化後的版本號
   */
  formatVersion(version) {
    if (!version) return '';
    return `v${version}`;
  }
}
