/** @odoo-module **/

import { Component, useState, onWillStart, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { DeviceCard } from "../../components/device_card/device_card";
import { StandaloneEntityCard } from "../../components/standalone_entity_card/standalone_entity_card";
import { debug, debugWarn } from "../../util/debug";

/**
 * AreaDashboard - Device-first hierarchical view for Home Assistant areas
 *
 * Features:
 * - Displays devices and their entities grouped by area
 * - Shows standalone entities (no device or moved from other device's area)
 * - Handles entity area override (entity.area_id != device.area_id)
 *
 * View Structure:
 * Area Dashboard
 * └── Area Tabs (area selection)
 *     └── Selected Area
 *         ├── Devices Section
 *         │   └── DeviceCard (collapsible)
 *         │       └── Entity list with area_override badges
 *         └── Standalone Entities Section
 *             └── StandaloneEntityCard (with source_device info)
 */
export class AreaDashboard extends Component {
  static template = "odoo_ha_addon.HaAreaDashboard";
  static components = { DeviceCard, StandaloneEntityCard };
  static props = {
    action: { type: Object, optional: true },
    "*": true, // Allow additional standard props from Odoo action system
  };

  setup() {
    this.haDataService = useService("ha_data");

    // 從 action context 接收 instance_id 參數
    this.instanceId = this.props.action?.context?.ha_instance_id || null;
    debug('[AreaDashboard] Initialized with instance_id:', this.instanceId);

    // ⚠️ instanceValidated 標記：避免重複驗證
    this.instanceValidated = false;

    // ⚠️ Phase 2.2: Breadcrumb Navigation
    this.actionService = useService("action");
    this.currentInstanceName = null;

    this.state = useState({
      areas: [],
      selectedArea: null,
      devices: [],              // Device-first view: devices with their entities
      standaloneEntities: [],   // Standalone entities (no device or moved from other area)
      loading: true,
      error: null,
    });

    onWillStart(async () => {
      // ⚠️ Phase 1.2: 驗證 instance_id 是否有效
      // 避免用戶點擊 Instance A 卻看到 Instance B 的數據（因為 backend fallback）
      if (this.instanceId && !this.instanceValidated) {
        const isValid = await this.validateInstanceId(this.instanceId);
        if (!isValid) {
          debugWarn('[AreaDashboard] Invalid instance_id:', this.instanceId);
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
          debug('[AreaDashboard] Instance name:', this.currentInstanceName);
        }
      }

      await this.loadAreas();
    });

    // 訂閱 area/device registry 變更事件，自動重新載入
    this.areaRegistryHandler = async (data) => {
      debug('[AreaDashboard] Area registry updated, reloading...', data);
      await this.loadAreas();
    };
    this.deviceRegistryHandler = async (data) => {
      debug('[AreaDashboard] Device registry updated, reloading...', data);
      // 只重載當前 area 的數據，不需要重載整個 areas 列表
      if (this.state.selectedArea) {
        await this.selectArea(this.state.selectedArea);
      }
    };

    this.haDataService.onGlobalState('area_registry_updated', this.areaRegistryHandler);
    this.haDataService.onGlobalState('device_registry_updated', this.deviceRegistryHandler);

    // 清理訂閱
    onWillUnmount(() => {
      this.haDataService.offGlobalState('area_registry_updated', this.areaRegistryHandler);
      this.haDataService.offGlobalState('device_registry_updated', this.deviceRegistryHandler);
    });
  }

  /**
   * 返回到 HA Instance Dashboard 入口頁
   *
   * ⚠️ Phase 2.2: Breadcrumb Navigation
   * 當用戶點擊麵包屑中的「Instances」鏈接時呼叫。
   */
  goBackToInstances() {
    debug('[AreaDashboard] Navigating back to instances...');

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
      console.error('[AreaDashboard] Error validating instance_id:', error);
      return false;
    }
  }

  async loadAreas() {
    try {
      this.state.loading = true;
      this.state.error = null;

      // 傳遞 instance_id 參數（如果有）
      const areas = await this.haDataService.getAreas(this.instanceId);

      // 加入「未分區」虛擬區域
      const unassignedArea = {
        id: 0,
        area_id: 'unassigned',
        name: _t('Unassigned'),
        icon: 'fa-question-circle',
      };

      this.state.areas = [...areas, unassignedArea];

      // 選擇 area：優先從 sessionStorage 恢復，否則選第一個
      if (this.state.areas.length > 0) {
        let selectedArea = this.state.areas[0];
        const savedAreaId = sessionStorage.getItem('ha_selected_area_id');
        if (savedAreaId) {
          const found = this.state.areas.find(a => a.id === parseInt(savedAreaId, 10));
          if (found) {
            selectedArea = found;
            debug('[AreaDashboard] Restored area selection from storage:', selectedArea.name);
          }
        }
        await this.selectArea(selectedArea);
      }

      this.state.loading = false;
    } catch (error) {
      console.error("Failed to load areas:", error);
      this.state.error = error.message || "載入分區失敗";
      this.state.loading = false;
    }
  }

  /**
   * 選擇 Area 並載入其 Device-first 數據
   *
   * 使用新的 getAreaDashboardData API，返回：
   * - devices: Area 下的所有 Devices 及其 Entities
   * - standalone_entities: 獨立 Entities（無 Device 或從其他 Device 移入）
   *
   * @param {Object} area - Area object with id, name, etc.
   */
  async selectArea(area) {
    try {
      this.state.selectedArea = area;
      this.state.loading = true;
      this.state.error = null;

      // 保存選擇到 sessionStorage（用於 breadcrumb 返回時恢復）
      sessionStorage.setItem('ha_selected_area_id', area.id.toString());

      // 使用新的 Device-first API（傳遞 instanceId）
      const data = await this.haDataService.getAreaDashboardData(area.id, this.instanceId);

      this.state.devices = data.devices || [];
      this.state.standaloneEntities = data.standalone_entities || [];
      this.state.loading = false;

      debug(`[AreaDashboard] Loaded area "${area.name}":`, {
        devices: this.state.devices.length,
        standaloneEntities: this.state.standaloneEntities.length,
      });
    } catch (error) {
      console.error(`Failed to load data for area ${area.name}:`, error);
      this.state.error = error.message || "載入區域資料失敗";
      this.state.loading = false;
    }
  }

  /**
   * 計算總實體數量
   */
  get totalEntityCount() {
    const deviceEntityCount = this.state.devices.reduce(
      (sum, device) => sum + (device.entities?.length || 0),
      0
    );
    return deviceEntityCount + this.state.standaloneEntities.length;
  }

  /**
   * 是否有任何內容（devices 或 standalone entities）
   */
  get hasContent() {
    return this.state.devices.length > 0 || this.state.standaloneEntities.length > 0;
  }
}

registry.category("actions").add("odoo_ha_addon.ha_area_dashboard", AreaDashboard);
