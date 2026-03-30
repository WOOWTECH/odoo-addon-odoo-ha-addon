/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { CACHE_TIMEOUT_MS } from "../constants";
import { debug, debugWarn, debugInfo } from "../util/debug";

/**
 * Home Assistant 數據服務
 * 統一管理所有 HA 相關的數據請求
 *
 * Phase 2.1: 整合 Odoo notification 服務，提供統一的錯誤提示 UI
 */
export class HaDataService {
  /**
   * @param {Object} env - Odoo 環境對象
   * @param {Object} services - 可用的服務對象
   */
  constructor(env, services) {
    this.env = env;
    this.notification = services.notification; // Phase 2.1: Odoo notification 服務

    this.cache = new Map();
    this.cacheTimeout = CACHE_TIMEOUT_MS;
    this.updateCallbacks = new Map(); // 實體更新回調函數

    // 全域狀態 callbacks（用於非實體相關的狀態，如 WebSocket 狀態）
    this.globalStateCallbacks = {
      websocket_status: [],
      history_update: [],
      entity_update_all: [], // 所有實體更新通知
      instance_switched: [], // Phase 4: 實例切換通知
      device_registry_updated: [], // 設備註冊變更通知（Glances 快取失效）
      area_registry_updated: [], // 區域註冊變更通知（Area Dashboard 快取失效）
    };

    // Phase 4: 實例相關狀態
    this.currentInstanceId = null;
    this.instances = [];

    // Phase 3.2: Debounce 機制
    this.debounceTimers = {}; // 存儲各事件類型的 debounce timer
    this.debouncedCallbacks = {}; // 存儲待執行的 callback 數據
    this.reloadInProgress = false; // 防止重複 reload 標記
  }

  /**
   * Phase 2.1: 顯示成功通知
   * @param {string} message - 通知訊息
   * @param {Object} options - 額外選項
   */
  showSuccess(message, options = {}) {
    if (!this.notification) {
      debugWarn("[HaDataService] Notification service not available");
      return;
    }

    this.notification.add(message, {
      type: "success",
      sticky: false,
      ...options,
    });
  }

  /**
   * Phase 2.1: 顯示錯誤通知
   * @param {string} message - 錯誤訊息
   * @param {Object} options - 額外選項
   */
  showError(message, options = {}) {
    if (!this.notification) {
      console.error(
        "[HaDataService] Notification service not available:",
        message
      );
      return;
    }

    this.notification.add(message, {
      type: "danger",
      sticky: false,
      ...options,
    });
  }

  /**
   * Phase 2.1: 顯示警告通知
   * @param {string} message - 警告訊息
   * @param {Object} options - 額外選項
   */
  showWarning(message, options = {}) {
    if (!this.notification) {
      debugWarn(
        "[HaDataService] Notification service not available:",
        message
      );
      return;
    }

    this.notification.add(message, {
      type: "warning",
      sticky: false,
      ...options,
    });
  }

  /**
   * Phase 2.1: 顯示資訊通知
   * @param {string} message - 資訊訊息
   * @param {Object} options - 額外選項
   */
  showInfo(message, options = {}) {
    if (!this.notification) {
      debugInfo(
        "[HaDataService] Notification service not available:",
        message
      );
      return;
    }

    this.notification.add(message, {
      type: "info",
      sticky: false,
      ...options,
    });
  }

  /**
   * Phase 4: 獲取所有 HA 實例列表
   *
   * Phase 2.1: 新增錯誤通知處理
   *
   * @returns {Promise<Object>} {success, data: {instances, current_instance_id}}
   */
  async getInstances() {
    try {
      const result = await rpc("/odoo_ha_addon/get_instances");
      if (result.success) {
        this.instances = result.data.instances;
        this.currentInstanceId = result.data.current_instance_id;
      } else {
        // Phase 2.1: 顯示錯誤通知
        this.showError(_t("Failed to load HA instance list: ") + result.error);
      }
      return result;
    } catch (error) {
      console.error("Failed to get instances:", error);
      // Phase 2.1: 顯示錯誤通知
      this.showError(_t("Error loading instance list: ") + error.message);
      throw error;
    }
  }

  /**
   * Phase 4: 切換 HA 實例
   *
   * ⚠️ Session-Based Instance Architecture:
   * 此方法會更新後端 session 中的 current_ha_instance_id。
   * 切換後，所有後續的 API 調用（hardware_info, network_info, areas 等）
   * 都會自動使用新的實例，無需在每次調用時明確傳遞 instance_id。
   *
   * 切換流程：
   * 1. 呼叫 /odoo_ha_addon/switch_instance 更新 session
   * 2. 清除前端快取（不同實例的數據不同）
   * 3. 觸發 instance_switched 全域事件
   * 4. 所有訂閱的組件自動重新載入數據
   *
   * Phase 2.1: 新增成功/錯誤通知
   *
   * @param {number} instanceId - 目標實例 ID
   * @returns {Promise<Object>} {success, data: {instance_id, instance_name, message}}
   */
  async switchInstance(instanceId) {
    try {
      const result = await rpc("/odoo_ha_addon/switch_instance", {
        instance_id: instanceId,
      });

      if (result.success) {
        // Phase 3.3: 不在此處立即更新狀態和觸發回調
        // 等待 Bus notification 統一處理，確保所有標籤頁同步
        // handleInstanceSwitched() 會處理：
        // - 更新 currentInstanceId
        // - 清除快取
        // - 觸發 instance_switched 回調

        // Phase 2.1: 顯示成功通知
        this.showSuccess(_t("Switched to instance: ") + result.data.instance_name);
      } else {
        // Phase 2.1: 顯示錯誤通知
        this.showError(_t("Failed to switch instance: ") + result.error);
      }

      return result;
    } catch (error) {
      console.error("Failed to switch instance:", error);
      // Phase 2.1: 顯示錯誤通知
      this.showError(_t("Error switching instance: ") + error.message);
      throw error;
    }
  }

  /**
   * Phase 4: 獲取當前實例 ID
   * @returns {number|null} 當前實例 ID
   */
  getCurrentInstanceId() {
    return this.currentInstanceId;
  }

  /**
   * Phase 4: 清除所有快取
   */
  clearCache() {
    this.cache.clear();
    debug("[HaDataService] Cache cleared");
  }

  /**
   * 獲取 HA 儀表板數據
   * @param {Object} params - 請求參數
   * @param {string} endpoint - API 端點，預設為 /odoo_ha_addon/ha_data
   * @returns {Promise<Object>} HA 數據
   */
  async fetchHaData(params = {}, endpoint = "/odoo_ha_addon/ha_data") {
    const cacheKey = `${endpoint}_${JSON.stringify(params)}`;

    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.data;
      }
    }

    try {
      const data = await rpc(endpoint, params);
      this.cache.set(cacheKey, {
        data,
        timestamp: Date.now(),
      });
      return data;
    } catch (error) {
      console.error(`Failed to fetch data from ${endpoint}:`, error);
      throw error;
    }
  }

  /**
   * 獲取統計數據
   * @param {Object} params - 請求參數
   * @returns {Promise<Object>} 統計數據
   */
  async fetchStatistics(params = {}) {
    return this.fetchHaData(params, "/odoo_ha_addon/statistics");
  }

  /**
   * 獲取歷史數據
   * @param {Array} domain - 搜索域
   * @param {Object} options - 搜索選項
   * @returns {Promise<Array>} 歷史記錄
   */
  async fetchHistoryData(domain, options = {}) {
    const cacheKey = `history_${JSON.stringify({ domain, options })}`;

    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.data;
      }
    }

    try {
      const data = await rpc("/web/dataset/search_read", {
        model: "ha.entity.history",
        domain,
        fields: ["recorded_at", "entity_state", "entity_id", "friendly_name"],
        ...options,
      });

      this.cache.set(cacheKey, {
        data: data.records,
        timestamp: Date.now(),
      });

      return data.records;
    } catch (error) {
      console.error("Failed to fetch history data:", error);
      throw error;
    }
  }

  /**
   * 獲取實體列表
   * @param {Array} domain - 搜索域
   * @returns {Promise<Array>} 實體列表
   */
  async fetchEntities(domain = []) {
    const cacheKey = `entities_${JSON.stringify(domain)}`;

    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.data;
      }
    }

    try {
      const data = await rpc("/web/dataset/search_read", {
        model: "ha.entity",
        domain,
        fields: [
          "entity_id",
          "friendly_name",
          "entity_state",
          "domain",
          "last_seen",
        ],
        order: "friendly_name",
      });

      this.cache.set(cacheKey, {
        data: data.records,
        timestamp: Date.now(),
      });

      return data.records;
    } catch (error) {
      console.error("Failed to fetch entities:", error);
      throw error;
    }
  }

  /**
   * 獲取所有 Home Assistant areas
   *
   * ⚠️ Instance Selection:
   * 此方法不傳遞 ha_instance_id 參數，後端會自動使用
   * session 中的 current_ha_instance_id。
   * 當使用者透過 Systray 切換實例時，session 會自動更新，
   * 後續呼叫此方法將返回新實例的 areas。
   *
   * Phase 2.1: 新增錯誤通知
   *
   * @returns {Promise<Array>} Area 列表
   */
  async getAreas() {
    const cacheKey = "areas_all";

    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.data;
      }
    }

    try {
      const result = await rpc("/odoo_ha_addon/areas", {});

      if (result.success) {
        this.cache.set(cacheKey, {
          data: result.data.areas,
          timestamp: Date.now(),
        });
        return result.data.areas;
      } else {
        // Phase 2.1: 顯示錯誤通知
        this.showError(_t("Failed to load Area list: ") + result.error);
        throw new Error(result.error || "Failed to fetch areas");
      }
    } catch (error) {
      console.error("Failed to fetch areas:", error);
      // Phase 2.1: 顯示錯誤通知（僅在非 RPC 錯誤時顯示，避免重複）
      if (!error.message.includes("Failed to load")) {
        this.showError(_t("Error loading Area list: ") + error.message);
      }
      throw error;
    }
  }

  /**
   * 根據 area_id 獲取 entities
   *
   * ⚠️ Instance Selection:
   * 此方法不傳遞 ha_instance_id 參數，後端會自動使用
   * session 中的 current_ha_instance_id。
   * 返回的 entities 來自當前選中的 HA 實例。
   *
   * Phase 2.1: 新增錯誤通知
   *
   * @param {number} areaId - Area 的 Odoo record ID
   * @returns {Promise<Array>} Entity 列表
   */
  async getEntitiesByArea(areaId) {
    const cacheKey = `entities_area_${areaId}`;

    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.data;
      }
    }

    try {
      const result = await rpc("/odoo_ha_addon/entities_by_area", {
        area_id: areaId,
      });

      if (result.success) {
        this.cache.set(cacheKey, {
          data: result.data.entities,
          timestamp: Date.now(),
        });
        return result.data.entities;
      } else {
        // Phase 2.1: 顯示錯誤通知
        this.showError(_t("Failed to load Area Entity list: ") + result.error);
        throw new Error(result.error || "Failed to fetch entities by area");
      }
    } catch (error) {
      console.error(`Failed to fetch entities for area ${areaId}:`, error);
      // Phase 2.1: 顯示錯誤通知（僅在非 RPC 錯誤時顯示，避免重複）
      if (!error.message.includes("Failed to load")) {
        this.showError(_t("Error loading Entity list: ") + error.message);
      }
      throw error;
    }
  }

  /**
   * 取得 Area Dashboard 完整資料（Device 優先視圖）
   *
   * 此方法返回指定區域的：
   * 1. 區域基本資訊
   * 2. 該區域下的所有 Devices 及其 Entities
   * 3. 獨立 Entities（無 Device 或從其他 Device 移入）
   *
   * Entity Area 覆蓋邏輯：
   * - 若 entity.area_id 與 device.area_id 不同，該 entity 會：
   *   a. 在原 Device Card 中標記「已移至 [其他區域]」(area_override)
   *   b. 在目標區域的獨立實體區塊中顯示（source_device）
   *
   * @param {number} areaId - Area 的 Odoo record ID
   * @param {number|null} instanceId - HA 實例 ID（可選，預設使用 session 實例）
   * @returns {Promise<Object>} {area, devices, standalone_entities}
   */
  async getAreaDashboardData(areaId, instanceId = null) {
    // 使用 instanceId 作為 cache key 的一部分，確保多實例環境下快取正確
    const effectiveInstanceId = instanceId || this.currentInstanceId || 'default';
    const cacheKey = `area_dashboard_${effectiveInstanceId}_${areaId}`;

    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.data;
      }
    }

    try {
      const params = { area_id: areaId };
      if (instanceId) {
        params.ha_instance_id = instanceId;
      }
      const result = await rpc("/odoo_ha_addon/area_dashboard_data", params);

      if (result.success) {
        this.cache.set(cacheKey, {
          data: result.data,
          timestamp: Date.now(),
        });
        return result.data;
      } else {
        this.showError(_t("Failed to load Area Dashboard data: ") + result.error);
        throw new Error(result.error || "Failed to fetch area dashboard data");
      }
    } catch (error) {
      console.error(`Failed to fetch area dashboard data for area ${areaId}:`, error);
      if (!error.message.includes("Failed to load")) {
        this.showError(_t("Error loading Area Dashboard: ") + error.message);
      }
      throw error;
    }
  }

  /**
   * 清除 Area Dashboard 相關快取
   *
   * 當 Area 結構變更（Device/Entity 變更）時呼叫此方法
   */
  clearAreaDashboardCache() {
    const keysToRemove = [];

    for (const [key] of this.cache) {
      if (key.startsWith("area_dashboard_") || key.startsWith("areas_")) {
        keysToRemove.push(key);
      }
    }

    keysToRemove.forEach((key) => this.cache.delete(key));

    if (keysToRemove.length > 0) {
      debug(
        `[HaDataService] Cleared ${keysToRemove.length} area dashboard cache entries`
      );
    }
  }

  /**
   * 呼叫 Home Assistant service
   *
   * ⚠️ Instance Selection:
   * 此方法不傳遞 ha_instance_id 參數，後端會自動使用
   * session 中的 current_ha_instance_id。
   * Service 將在當前選中的 HA 實例上執行。
   *
   * Phase 2.1: 新增成功/錯誤通知
   *
   * @param {string} domain - Entity domain (e.g., 'switch', 'light', 'climate')
   * @param {string} service - Service name (e.g., 'turn_on', 'turn_off', 'toggle')
   * @param {Object} serviceData - Service data (must include entity_id)
   * @param {Object} options - 額外選項 {silent: 是否靜音通知（預設 false）}
   * @returns {Promise<Object>} Service call result
   *
   * @example
   * // Toggle a switch（使用 session 實例）
   * await haDataService.callService('switch', 'toggle', { entity_id: 'switch.living_room' });
   *
   * // Set light brightness
   * await haDataService.callService('light', 'turn_on', {
   *   entity_id: 'light.bedroom',
   *   brightness: 128
   * });
   *
   * // Set climate temperature (without notification)
   * await haDataService.callService('climate', 'set_temperature', {
   *   entity_id: 'climate.living_room',
   *   temperature: 22
   * }, { silent: true });
   */
  async callService(domain, service, serviceData = {}, options = {}) {
    const { silent = false } = options;

    debug(
      `[HaDataService] Calling service: ${domain}.${service}`,
      serviceData
    );

    try {
      const result = await rpc("/odoo_ha_addon/call_service", {
        domain,
        service,
        service_data: serviceData,
      });

      if (result.success) {
        debug(`[HaDataService] Service call succeeded:`, result);

        // 清除相關實體的快取
        if (serviceData.entity_id) {
          this.clearCacheForEntity(serviceData.entity_id);
        }

        // Phase 2.1: 顯示成功通知（除非 silent 模式）
        if (!silent) {
          const entityName = serviceData.entity_id || "entity";
          const actionText = this._getServiceActionText(service);
          this.showSuccess(actionText + " " + entityName + " " + _t("succeeded"));
        }

        return result;
      } else {
        // Phase 2.1: 顯示錯誤通知
        this.showError(_t("Failed to execute %s.%s: ").replace("%s.%s", `${domain}.${service}`) + result.error);
        throw new Error(result.error || "Service call failed");
      }
    } catch (error) {
      console.error(
        `[HaDataService] Service call failed: ${domain}.${service}`,
        error
      );
      // Phase 2.1: 顯示錯誤通知（僅在非 RPC 錯誤時顯示，避免重複）
      if (!error.message.includes("Failed to execute")) {
        this.showError(_t("Error executing service: ") + error.message);
      }
      throw error;
    }
  }

  // ====================================
  // Glances Dashboard Methods
  // ====================================

  /**
   * 取得 Glances 設備列表
   *
   * @param {number} [instanceId] - HA 實例 ID（可選，預設使用 session 實例）
   * @returns {Promise<Object>} {success, data: {devices: [...]}}
   */
  async getGlancesDevices(instanceId = null) {
    const cacheKey = `glances_devices_${instanceId || 'session'}`;

    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.data;
      }
    }

    try {
      const params = instanceId ? { ha_instance_id: instanceId } : {};
      const result = await rpc("/odoo_ha_addon/glances_devices", params);

      if (result.success) {
        this.cache.set(cacheKey, {
          data: result,
          timestamp: Date.now(),
        });
      } else {
        this.showError(_t("Failed to load Glances devices: ") + result.error);
      }

      return result;
    } catch (error) {
      console.error("Failed to get Glances devices:", error);
      this.showError(_t("Error loading Glances devices: ") + error.message);
      throw error;
    }
  }

  /**
   * 取得特定 Glances 設備的實體列表
   *
   * @param {string} deviceId - Glances 設備 ID
   * @param {number} [instanceId] - HA 實例 ID（可選，預設使用 session 實例）
   * @returns {Promise<Object>} {success, data: {device_id, entities: [...]}}
   */
  async getGlancesDeviceEntities(deviceId, instanceId = null) {
    const cacheKey = `glances_device_entities_${deviceId}_${instanceId || 'session'}`;

    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.data;
      }
    }

    try {
      const params = { device_id: deviceId };
      if (instanceId) {
        params.ha_instance_id = instanceId;
      }

      const result = await rpc("/odoo_ha_addon/glances_device_entities", params);

      if (result.success) {
        this.cache.set(cacheKey, {
          data: result,
          timestamp: Date.now(),
        });
      } else {
        this.showError(_t("Failed to load device entities: ") + result.error);
      }

      return result;
    } catch (error) {
      console.error(`Failed to get entities for Glances device ${deviceId}:`, error);
      this.showError(_t("Error loading device entities: ") + error.message);
      throw error;
    }
  }

  // ====================================
  // Entity Related Methods
  // ====================================

  /**
   * 取得 Entity 的相關資訊（Area、Device、Label、Automation）
   *
   * @param {string} entityId - Entity ID (e.g., 'switch.living_room')
   * @param {number} [instanceId] - HA 實例 ID（可選，預設使用 session 實例）
   * @returns {Promise<Object>} {success, data: {area, device, labels, automations}}
   */
  async getEntityRelated(entityId, instanceId = null) {
    if (!entityId) {
      throw new Error("entityId is required");
    }

    try {
      const params = { entity_id: entityId };
      if (instanceId) {
        params.ha_instance_id = instanceId;
      }

      const result = await rpc("/odoo_ha_addon/entity_related", params);

      if (!result.success) {
        this.showError(_t("Failed to load related info: ") + result.error);
      }

      return result;
    } catch (error) {
      console.error(`Failed to get related info for entity ${entityId}:`, error);
      this.showError(_t("Error loading related info: ") + error.message);
      throw error;
    }
  }

  /**
   * Phase 2.1: Get action text for service name
   * @private
   * @param {string} service - Service name
   * @returns {string} Translated action text
   */
  _getServiceActionText(service) {
    const actionMap = {
      turn_on: _t("Turn on"),
      turn_off: _t("Turn off"),
      toggle: _t("Toggle"),
      set_temperature: _t("Set temperature"),
      set_hvac_mode: _t("Set HVAC mode"),
      open: _t("Open"),
      close: _t("Close"),
      stop: _t("Stop"),
      lock: _t("Lock"),
      unlock: _t("Unlock"),
    };

    return actionMap[service] || _t("Execute");
  }

  /**
   * 清理緩存
   */
  clearCache() {
    this.cache.clear();
  }

  /**
   * 處理記錄轉換為圖表數據
   * @param {Array} records - 歷史記錄
   * @param {Object} options - 處理選項
   * @returns {Object} Chart.js 格式的數據
   */
  processRecordsToChartData(records, options = {}) {
    const {
      labelField = "recorded_at",
      valueField = "entity_state",
      label = "Data",
      chartType = "line",
    } = options;

    const labels = records.map((record) => record[labelField]);
    const data = records.map((record) => {
      const value = record[valueField];
      return isNaN(value) ? 0 : parseFloat(value);
    });

    return {
      labels,
      datasets: [
        {
          label,
          data,
          borderColor: "rgb(75, 192, 192)",
          backgroundColor: "rgba(75, 192, 192, 0.2)",
          tension: chartType === "line" ? 0.1 : 0,
        },
      ],
    };
  }

  /**
   * 處理實體更新事件
   * 由 HaBusBridge 調用，接收來自後端的 ha_entity_update 事件
   * @param {Object} data - 更新數據
   */
  handleEntityUpdate(data) {
    const { entity_id, data: entityData } = data;

    debug(`HA Entity Update: ${entity_id}`, entityData);

    // 清除相關的快取
    this.clearCacheForEntity(entity_id);

    // 觸發特定實體的更新回調
    this.triggerUpdateCallbacks(entity_id, entityData);

    // 觸發全域的實體更新回調（用於 Dashboard 等需要知道任何實體更新的組件）
    this.triggerGlobalCallbacks("entity_update_all", {
      entity_id,
      data: entityData,
    });
  }

  /**
   * 處理狀態變更事件
   * @param {Object} data - 狀態變更數據
   */
  handleStateChanged(data) {
    const { entity_id, old_state, new_state } = data;

    debug(`HA State Changed: ${entity_id}`, {
      from: old_state,
      to: new_state,
    });

    // 清除相關的快取
    this.clearCacheForEntity(entity_id);

    // 觸發狀態變更回調
    this.triggerStateChangeCallbacks(entity_id, old_state, new_state);
  }

  /**
   * 處理服務狀態事件
   * 由 HaBusBridge 調用，接收來自後端的 ha_websocket_status 事件
   * @param {Object} data - 服務狀態數據
   */
  handleServiceStatus(data) {
    const { status, message } = data;

    debug(`HA WebSocket Status: ${status} - ${message}`);

    // 觸發全域 websocket_status callbacks（用於 Dashboard 顯示連線狀態）
    this.triggerGlobalCallbacks("websocket_status", { status, message });
  }

  /**
   * 處理歷史記錄更新事件
   * 由 HaBusBridge 調用，接收來自後端的 ha_history_update 事件
   * @param {Object} data - 歷史記錄更新數據
   */
  handleHistoryUpdate(data) {
    const { entity_id, history_count } = data;

    debug(`HA History Update: ${entity_id} (+${history_count} records)`);

    // 清除歷史記錄相關的快取
    this.clearHistoryCacheForEntity(entity_id);

    // 觸發全域 history_update callbacks（用於 HaHistoryController 重新載入）
    this.triggerGlobalCallbacks("history_update", { entity_id, history_count });
  }

  /**
   * Phase 3.1: 處理實例失效事件
   * 由 HaBusBridge 調用，接收來自後端的 instance_invalidated 事件
   * @param {Object} data - 實例失效數據 {instance_id, reason, timestamp}
   */
  handleInstanceInvalidated(data) {
    const { instance_id, reason } = data;

    debugWarn(
      `[HaDataService] Instance invalidated: ID ${instance_id} - ${reason}`
    );

    // 清除所有快取（因為實例已失效）
    this.clearCache();

    // 顯示警告通知
    this.showWarning(_t("Instance invalidated: ") + reason, {
      sticky: false,
    });
  }

  /**
   * Phase 3.1: 處理實例降級事件
   * 由 HaBusBridge 調用，接收來自後端的 instance_fallback 事件
   * @param {Object} data - 實例降級數據
   *   {from_instance_id, to_instance_id, to_instance_name, fallback_type, timestamp}
   */
  handleInstanceFallback(data) {
    const {
      from_instance_id,
      to_instance_id,
      to_instance_name,
      fallback_type,
    } = data;

    debugWarn(
      `[HaDataService] Instance fallback: ${from_instance_id} -> ${to_instance_name} (${fallback_type})`
    );

    // 更新當前實例 ID
    this.currentInstanceId = to_instance_id;

    // 清除所有快取（不同實例的數據不同）
    this.clearCache();

    // 根據 fallback_type 顯示不同的訊息
    const fallbackTypeText = {
      default: _t("default instance"),
      first_active: _t("first active instance"),
    };

    const typeText = fallbackTypeText[fallback_type] || _t("fallback instance");

    // 顯示資訊通知
    this.showInfo(_t("Auto-switched to %s: ").replace("%s", typeText) + to_instance_name, {
      sticky: false,
    });

    // 觸發 instance_switched 事件，讓所有組件重新載入數據
    this.triggerGlobalCallbacks("instance_switched", {
      instanceId: to_instance_id,
      instanceName: to_instance_name,
    });
  }

  /**
   * Phase 3.3: 處理實例切換事件（多標籤頁同步）
   *
   * 當使用者在任一標籤頁切換實例時，透過 Bus notification 同步到所有標籤頁
   */
  handleInstanceSwitched(data) {
    const { instance_id, instance_name, user_id } = data;

    debug(
      `[HaDataService] Instance switched via Bus: ${instance_name} (ID: ${instance_id})`
    );

    // 更新當前實例 ID
    this.currentInstanceId = instance_id;

    // 清除所有快取（不同實例的數據不同）
    this.clearCache();

    // 觸發 instance_switched 事件，讓所有組件重新載入數據
    // 使用 debounce 機制（Phase 3.2）避免多標籤頁重複載入
    this.triggerGlobalCallbacks("instance_switched", {
      instanceId: instance_id,
      instanceName: instance_name,
    });
  }

  /**
   * 處理設備註冊變更事件（用於 Glances 快取失效）
   *
   * 當 Home Assistant 的設備註冊發生變更時，清除 Glances 相關快取
   * 並通知訂閱的組件重新載入數據
   *
   * @param {Object} data - 事件數據 {action, device_id, ha_instance_id, timestamp}
   */
  handleDeviceRegistryUpdated(data) {
    const { action, device_id, ha_instance_id } = data;

    debug(
      `[HaDataService] Device registry updated: ${action} - ${device_id}`
    );

    // 清除 Glances 相關快取
    this.clearGlancesCache(device_id, ha_instance_id);

    // 清除 Area Dashboard 快取（Device 變更可能影響 Area 顯示）
    this.clearAreaDashboardCache();

    // 觸發 device_registry_updated 事件，讓組件重新載入數據
    this.triggerGlobalCallbacks("device_registry_updated", {
      action,
      deviceId: device_id,
      instanceId: ha_instance_id,
    });
  }

  /**
   * 處理區域註冊變更事件
   *
   * 當 Home Assistant 的區域註冊發生變更時，清除 Area Dashboard 快取
   * 並通知訂閱的組件重新載入數據
   *
   * @param {Object} data - 事件數據 {action, area_id, ha_instance_id, timestamp}
   */
  handleAreaRegistryUpdated(data) {
    const { action, area_id, ha_instance_id } = data;

    debug(
      `[HaDataService] Area registry updated: ${action} - ${area_id}`
    );

    // 清除 Area Dashboard 快取
    this.clearAreaDashboardCache();

    // 觸發 area_registry_updated 事件，讓組件重新載入數據
    this.triggerGlobalCallbacks("area_registry_updated", {
      action,
      areaId: area_id,
      instanceId: ha_instance_id,
    });
  }

  /**
   * 清除 Glances 相關快取
   *
   * @param {string} [deviceId] - 特定設備 ID（可選，若提供則只清除該設備相關快取）
   * @param {number} [instanceId] - 實例 ID（可選）
   */
  clearGlancesCache(deviceId = null, instanceId = null) {
    const keysToRemove = [];

    for (const [key] of this.cache) {
      // 清除設備列表快取
      if (key.startsWith("glances_devices_")) {
        keysToRemove.push(key);
      }
      // 清除設備實體快取
      if (key.startsWith("glances_device_entities_")) {
        if (deviceId && key.includes(deviceId)) {
          keysToRemove.push(key);
        } else if (!deviceId) {
          keysToRemove.push(key);
        }
      }
    }

    keysToRemove.forEach((key) => this.cache.delete(key));

    if (keysToRemove.length > 0) {
      debug(
        `[HaDataService] Cleared ${keysToRemove.length} Glances cache entries`
      );
    }
  }

  /**
   * 清除特定實體的快取
   * @param {string} entity_id - 實體 ID
   */
  clearCacheForEntity(entity_id) {
    const keysToRemove = [];

    for (const [key] of this.cache) {
      if (key.includes(entity_id)) {
        keysToRemove.push(key);
      }
    }

    keysToRemove.forEach((key) => this.cache.delete(key));

    if (keysToRemove.length > 0) {
      debug(
        `Cleared ${keysToRemove.length} cache entries for entity: ${entity_id}`
      );
    }
  }

  /**
   * 清除特定實體的歷史記錄快取
   * @param {string} entity_id - 實體 ID
   */
  clearHistoryCacheForEntity(entity_id) {
    const keysToRemove = [];

    for (const [key] of this.cache) {
      if (key.includes("history") && key.includes(entity_id)) {
        keysToRemove.push(key);
      }
    }

    keysToRemove.forEach((key) => this.cache.delete(key));
  }

  /**
   * 註冊實體更新回調
   * @param {string} entity_id - 實體 ID
   * @param {Function} callback - 回調函數
   */
  onEntityUpdate(entity_id, callback) {
    if (!this.updateCallbacks.has(entity_id)) {
      this.updateCallbacks.set(entity_id, []);
    }
    this.updateCallbacks.get(entity_id).push(callback);
  }

  /**
   * 移除實體更新回調
   * @param {string} entity_id - 實體 ID
   * @param {Function} callback - 回調函數
   */
  offEntityUpdate(entity_id, callback) {
    if (this.updateCallbacks.has(entity_id)) {
      const callbacks = this.updateCallbacks.get(entity_id);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  /**
   * 觸發更新回調
   * @param {string} entity_id - 實體 ID
   * @param {Object} data - 更新數據
   */
  triggerUpdateCallbacks(entity_id, data) {
    if (this.updateCallbacks.has(entity_id)) {
      const callbacks = this.updateCallbacks.get(entity_id);
      callbacks.forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error("Error in update callback:", error);
        }
      });
    }
  }

  /**
   * 觸發狀態變更回調
   * @param {string} entity_id - 實體 ID
   * @param {any} oldState - 舊狀態
   * @param {any} newState - 新狀態
   */
  triggerStateChangeCallbacks(entity_id, oldState, newState) {
    // 可以為狀態變更添加特殊的回調處理
    this.triggerUpdateCallbacks(entity_id, {
      old_state: oldState,
      new_state: newState,
    });
  }

  /**
   * 註冊全域狀態回調
   * @param {string} eventType - 事件類型 ('websocket_status', 'history_update', 'entity_update_all', 'instance_switched')
   * @param {Function} callback - 回調函數
   */
  onGlobalState(eventType, callback) {
    if (this.globalStateCallbacks[eventType]) {
      this.globalStateCallbacks[eventType].push(callback);
    } else {
      debugWarn(`Unknown global state event type: ${eventType}`);
    }
  }

  /**
   * 移除全域狀態回調
   * @param {string} eventType - 事件類型
   * @param {Function} callback - 回調函數
   */
  offGlobalState(eventType, callback) {
    if (this.globalStateCallbacks[eventType]) {
      const index = this.globalStateCallbacks[eventType].indexOf(callback);
      if (index > -1) {
        this.globalStateCallbacks[eventType].splice(index, 1);
      }
    }
  }

  /**
   * 觸發全域狀態回調
   *
   * Phase 3.2: 為 instance_switched 事件加入 debounce 機制
   * 防止多標籤頁快速切換實例時產生大量重複 reload
   *
   * @param {string} eventType - 事件類型
   * @param {Object} data - 事件數據
   */
  triggerGlobalCallbacks(eventType, data) {
    if (!this.globalStateCallbacks[eventType]) {
      return;
    }

    // Phase 3.2: 對 instance_switched 事件進行 debounce
    if (eventType === "instance_switched") {
      // 檢查是否有 reload 正在進行
      if (this.reloadInProgress) {
        debug(
          "[HaDataService] Reload already in progress, queueing new instance switch"
        );
      }

      // 儲存最新的切換數據
      this.debouncedCallbacks[eventType] = data;

      // 清除舊的 timer（如果有）
      if (this.debounceTimers[eventType]) {
        clearTimeout(this.debounceTimers[eventType]);
      }

      // 設定新的 debounce timer（300ms）
      this.debounceTimers[eventType] = setTimeout(() => {
        // 檢查是否有 reload 正在進行
        if (this.reloadInProgress) {
          debug(
            "[HaDataService] Skipping debounced callback - reload in progress"
          );
          return;
        }

        // 設定 reload 標記
        this.reloadInProgress = true;

        const debouncedData = this.debouncedCallbacks[eventType];
        debug(
          `[HaDataService] Executing debounced ${eventType} callback:`,
          debouncedData
        );

        // 執行所有 callbacks
        this.globalStateCallbacks[eventType].forEach((callback) => {
          try {
            callback(debouncedData);
          } catch (error) {
            console.error(`Error in ${eventType} callback:`, error);
          }
        });

        // 清除 reload 標記（延遲 500ms，給組件足夠時間完成 reload）
        setTimeout(() => {
          this.reloadInProgress = false;
          debug("[HaDataService] Reload completed, flag cleared");
        }, 500);

        // 清除已執行的數據
        delete this.debouncedCallbacks[eventType];
        delete this.debounceTimers[eventType];
      }, 300); // 300ms debounce

      return;
    }

    // 對於其他事件類型，立即執行 callbacks（無 debounce）
    this.globalStateCallbacks[eventType].forEach((callback) => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in ${eventType} callback:`, error);
      }
    });
  }
}

export const haDataService = {
  dependencies: ["notification"], // Phase 2.1: 依賴 notification 服務
  start(env, services) {
    return new HaDataService(env, services);
  },
};

registry.category("services").add("ha_data", haDataService);
