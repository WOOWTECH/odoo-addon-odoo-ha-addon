/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { DashboardItem } from "../../components/dashboard_item/dashboard_item";
import { GLANCES_DEVICE_REFRESH_MS } from "../../constants";
import { debug, debugWarn } from "../../util/debug";

const { Component, useState, onMounted, onWillUnmount, onWillStart } = owl;

/**
 * GlancesDeviceDashboard - 顯示特定 Glances 設備的詳細儀表板
 *
 * 顯示設備下所有實體的狀態，按照類型分組（CPU、記憶體、磁碟、網路等）
 */
class GlancesDeviceDashboard extends Component {
  static template = "odoo_ha_addon.GlancesDeviceDashboard";
  static components = { DashboardItem };
  static props = {
    action: { type: Object, optional: true },
    "*": true, // Allow additional standard props from Odoo action system
  };

  setup() {
    // 從 action context 取得參數
    this.instanceId = this.props.action?.context?.ha_instance_id || null;
    this.deviceId = this.props.action?.context?.device_id || null;
    this.deviceName = this.props.action?.context?.device_name || 'Glances Device';

    debug('[GlancesDeviceDashboard] Initialized:', {
      instanceId: this.instanceId,
      deviceId: this.deviceId,
      deviceName: this.deviceName,
    });

    this.haDataService = useService("ha_data");
    this.actionService = useService("action");

    this.state = useState({
      loading: true,
      error: null,
      entities: [],
      groupedEntities: {},
      lastUpdate: null,
    });

    // 定時更新
    this.refreshInterval = null;

    onWillStart(async () => {
      // 載入實例名稱（用於麵包屑）
      if (this.instanceId) {
        const result = await this.haDataService.getInstances();
        if (result.success) {
          const instance = result.data.instances.find(inst => inst.id === this.instanceId);
          this.currentInstanceName = instance?.name || 'Unknown';
        }
      }
    });

    onMounted(async () => {
      await this.loadDeviceEntities();

      // 定時刷新設備實體資料
      this.refreshInterval = setInterval(() => {
        this.loadDeviceEntities();
      }, GLANCES_DEVICE_REFRESH_MS);
    });

    onWillUnmount(() => {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
      }
    });
  }

  /**
   * 載入設備的所有實體
   */
  async loadDeviceEntities() {
    if (!this.deviceId) {
      this.state.error = 'No device ID specified';
      this.state.loading = false;
      return;
    }

    try {
      this.state.error = null;

      const result = await this.haDataService.getGlancesDeviceEntities(
        this.deviceId,
        this.instanceId
      );

      if (result.success) {
        this.state.entities = result.data.entities || [];
        this.state.groupedEntities = this.groupEntitiesByType(this.state.entities);

        // 警告：如果有實體但分組後為空（所有實體都無法歸類）
        if (Object.keys(this.state.groupedEntities).length === 0 && this.state.entities.length > 0) {
          debugWarn('[GlancesDeviceDashboard] All entities were filtered out during grouping');
        }

        this.state.lastUpdate = new Date().toLocaleTimeString();
      } else {
        this.state.error = result.error || 'Failed to load device entities';
      }
    } catch (error) {
      console.error('[GlancesDeviceDashboard] Failed to load entities:', error);
      this.state.error = error.message || 'Failed to load device entities';
    } finally {
      this.state.loading = false;
    }
  }

  /**
   * 按照類型分組實體
   * @param {Array} entities - 實體列表
   * @returns {Object} 分組後的實體 {groupName: [entities]}
   */
  groupEntitiesByType(entities) {
    const groups = {
      cpu: { name: _t('CPU'), icon: 'fa-microchip', entities: [] },
      memory: { name: _t('Memory'), icon: 'fa-tasks', entities: [] },
      disk: { name: _t('Disk'), icon: 'fa-hdd-o', entities: [] },
      network: { name: _t('Network'), icon: 'fa-wifi', entities: [] },
      temperature: { name: _t('Temperature'), icon: 'fa-thermometer-half', entities: [] },
      battery: { name: _t('Battery'), icon: 'fa-battery-full', entities: [] },
      process: { name: _t('Process'), icon: 'fa-cogs', entities: [] },
      other: { name: _t('Other'), icon: 'fa-cube', entities: [] },
    };

    for (const entity of entities) {
      const entityId = entity.entity_id || '';
      const deviceClass = entity.device_class || '';
      const name = (entity.name || '').toLowerCase();

      // 根據 entity_id 或 device_class 判斷類型
      if (entityId.includes('cpu') || name.includes('cpu')) {
        groups.cpu.entities.push(entity);
      } else if (entityId.includes('memory') || entityId.includes('ram') ||
                 name.includes('memory') || name.includes('ram') ||
                 deviceClass === 'data_size') {
        groups.memory.entities.push(entity);
      } else if (entityId.includes('disk') || entityId.includes('storage') ||
                 name.includes('disk') || name.includes('storage') ||
                 name.includes('filesystem')) {
        groups.disk.entities.push(entity);
      } else if (entityId.includes('network') || entityId.includes('eth') ||
                 entityId.includes('wlan') || name.includes('network') ||
                 name.includes('bandwidth') || name.includes('rx') || name.includes('tx')) {
        groups.network.entities.push(entity);
      } else if (entityId.includes('temp') || deviceClass === 'temperature' ||
                 name.includes('temperature')) {
        groups.temperature.entities.push(entity);
      } else if (entityId.includes('battery') || deviceClass === 'battery' ||
                 name.includes('battery')) {
        groups.battery.entities.push(entity);
      } else if (entityId.includes('process') || name.includes('process') ||
                 name.includes('running')) {
        groups.process.entities.push(entity);
      } else {
        groups.other.entities.push(entity);
      }
    }

    // 移除空的群組
    const result = {};
    for (const [key, group] of Object.entries(groups)) {
      if (group.entities.length > 0) {
        result[key] = group;
      }
    }

    return result;
  }

  /**
   * 返回到 HA Info 頁面
   */
  goBackToHaInfo() {
    debug('[GlancesDeviceDashboard] Navigating back to HA Info...');

    this.actionService.doAction({
      type: 'ir.actions.client',
      tag: 'odoo_ha_addon.ha_info_dashboard',
      name: 'HA Info',
      context: {
        ha_instance_id: this.instanceId,
      },
    });
  }

  /**
   * 返回到實例列表
   */
  goBackToInstances() {
    debug('[GlancesDeviceDashboard] Navigating back to instances...');

    this.actionService.doAction({
      type: 'ir.actions.client',
      tag: 'odoo_ha_addon.ha_instance_dashboard',
      name: 'Home Assistant 實例',
    });
  }

  /**
   * 格式化數值
   * @param {string|number} value - 數值
   * @param {string} unit - 單位
   * @returns {string} 格式化後的字串
   */
  formatValue(value, unit) {
    if (value === null || value === undefined || value === 'unavailable' || value === 'unknown') {
      return 'N/A';
    }

    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
      return String(value);
    }

    // 根據單位格式化
    if (unit === '%') {
      return `${numValue.toFixed(1)}%`;
    } else if (unit === 'GiB' || unit === 'GB') {
      return `${numValue.toFixed(2)} ${unit}`;
    } else if (unit === 'MiB' || unit === 'MB') {
      return `${numValue.toFixed(1)} ${unit}`;
    } else if (unit === 'KiB/s' || unit === 'KB/s' || unit === 'kB/s') {
      return `${numValue.toFixed(1)} ${unit}`;
    } else if (unit === 'MiB/s' || unit === 'MB/s') {
      return `${numValue.toFixed(2)} ${unit}`;
    } else if (unit === 'C' || unit === '°C') {
      return `${numValue.toFixed(1)}°C`;
    } else if (unit) {
      return `${numValue} ${unit}`;
    }

    return String(value);
  }

  /**
   * 取得狀態的顏色類別
   * @param {Object} entity - 實體
   * @returns {string} Bootstrap 顏色類別
   */
  getStateClass(entity) {
    const value = parseFloat(entity.state);
    const unit = entity.unit_of_measurement;

    if (isNaN(value)) {
      return '';
    }

    // CPU 或記憶體百分比
    if (unit === '%') {
      if (value >= 90) return 'text-danger';
      if (value >= 70) return 'text-warning';
      return 'text-success';
    }

    // 溫度
    if (entity.device_class === 'temperature' || unit === '°C' || unit === 'C') {
      if (value >= 80) return 'text-danger';
      if (value >= 60) return 'text-warning';
      return 'text-success';
    }

    return '';
  }

  /**
   * 取得實體的圖示
   * @param {Object} entity - 實體
   * @returns {string} Font Awesome 類名
   */
  getEntityIcon(entity) {
    if (entity.icon) {
      // 將 mdi: 前綴轉換為 fa
      const icon = entity.icon.replace('mdi:', '');
      return `fa fa-${icon}`;
    }

    const deviceClass = entity.device_class || '';
    const iconMap = {
      temperature: 'fa fa-thermometer-half',
      data_size: 'fa fa-database',
      data_rate: 'fa fa-exchange',
      power: 'fa fa-bolt',
      battery: 'fa fa-battery-full',
      timestamp: 'fa fa-clock-o',
    };

    return iconMap[deviceClass] || 'fa fa-cube';
  }
}

registry.category("actions").add("odoo_ha_addon.glances_device_dashboard", GlancesDeviceDashboard);
