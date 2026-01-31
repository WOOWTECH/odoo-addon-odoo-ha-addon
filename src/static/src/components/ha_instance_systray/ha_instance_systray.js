/** @odoo-module **/

// ⚠️ DEPRECATED: 此組件已不再使用
// 重構後採用入口頁導航模式，不再使用 systray 切換器
// 檔案保留以便未來參考或向後相容需求

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { debug } from "../../util/debug";

/**
 * HA Instance Systray Component (DEPRECATED)
 *
 * 顯示在頂部導覽列（systray）中的 Home Assistant 實例切換器。
 * 提供快速切換不同 HA 實例的功能，在所有頁面都可見。
 *
 * 特點：
 * - 使用 ha_data_service 獲取實例列表
 * - 通過 instance_switched 事件與其他組件同步
 * - 響應式設計（手機版只顯示圖示）
 * - 顯示每個實例的 WebSocket 連線狀態
 */
class HaInstanceSystray extends Component {
    static template = "odoo_ha_addon.HaInstanceSystray";
    static components = {};
    static props = {};  // Systray 組件不接收 props

    setup() {
        // 使用 ha_data service 獲取實例資料
        this.haDataService = useService("ha_data");

        // 本地狀態管理
        this.state = useState({
            instances: [],
            currentId: null,
            loading: true,
            error: null,
        });

        // 訂閱實例切換事件（與其他組件同步）
        this.instanceSwitchedHandler = ({ instanceId, instanceName }) => {
            debug('[HaInstanceSystray] Instance switched to:', instanceName);
            this.state.currentId = instanceId;
        };
        this.haDataService.onGlobalState('instance_switched', this.instanceSwitchedHandler);

        // 組件掛載時載入實例列表
        onMounted(async () => {
            await this.loadInstances();
        });

        // 組件卸載時清理事件監聽
        onWillUnmount(() => {
            this.haDataService.offGlobalState('instance_switched', this.instanceSwitchedHandler);
            debug('[HaInstanceSystray] Cleanup complete');
        });
    }

    /**
     * 從 backend 載入 HA 實例列表
     *
     * Phase 2.1: 錯誤通知已由 HaDataService 自動處理
     */
    async loadInstances() {
        try {
            this.state.loading = true;
            this.state.error = null;

            const result = await this.haDataService.getInstances();

            if (result.success) {
                this.state.instances = result.data.instances;
                this.state.currentId = result.data.current_instance_id;
                debug('[HaInstanceSystray] Loaded instances:', this.state.instances.length);
            } else {
                this.state.error = result.error;
                console.error('[HaInstanceSystray] Failed to load instances:', result.error);
                // Phase 2.1: 錯誤通知已由 HaDataService 自動處理
            }
        } catch (error) {
            this.state.error = error.message;
            console.error('[HaInstanceSystray] Error loading instances:', error);
            // Phase 2.1: 錯誤通知已由 HaDataService 自動處理
        } finally {
            this.state.loading = false;
        }
    }

    /**
     * 切換到指定的 HA 實例
     *
     * ⚠️ Session-Based Instance Architecture:
     * 此方法會呼叫 HaDataService.switchInstance()，該方法會：
     * 1. 更新後端 session 的 current_ha_instance_id
     * 2. 清除前端快取
     * 3. 觸發 instance_switched 全域事件
     * 4. 所有訂閱的組件（Dashboard 等）會自動重新載入數據
     *
     * 切換後，所有 API 調用（hardware_info, network_info 等）
     * 都會自動使用新實例，無需明確傳遞 instance_id。
     *
     * @param {number} instanceId - 目標實例 ID
     */
    async selectInstance(instanceId) {
        if (instanceId === this.state.currentId) {
            debug('[HaInstanceSystray] Already on this instance');
            return;
        }

        try {
            debug('[HaInstanceSystray] Switching to instance:', instanceId);

            const result = await this.haDataService.switchInstance(instanceId);

            if (result.success) {
                debug('[HaInstanceSystray] Successfully switched to:', result.data.instance_name);
                // state 會由 instanceSwitchedHandler 自動更新
                // Phase 2.1: 錯誤通知已由 HaDataService 自動處理

                // Phase 4.1: 自動重新載入頁面以更新 Standard List Views
                // Custom views (Dashboard/hahistory) 會在事件中重新載入
                // Standard views (Entity/Group/History) 需要頁面重新載入才能應用新過濾器
                debug('[HaInstanceSystray] Reloading page to update filters...');
                window.location.reload();
            } else {
                console.error('[HaInstanceSystray] Failed to switch instance:', result.error);
                // Phase 2.1: 錯誤通知已由 HaDataService 自動處理
            }
        } catch (error) {
            console.error('[HaInstanceSystray] Error switching instance:', error);
            // Phase 2.1: 錯誤通知已由 HaDataService 自動處理
        }
    }

    /**
     * 獲取當前選中的實例對象
     * @returns {Object|null} 當前實例對象
     */
    get currentInstance() {
        if (!this.state.currentId || !this.state.instances.length) {
            return null;
        }
        return this.state.instances.find(inst => inst.id === this.state.currentId);
    }

    /**
     * 根據 WebSocket 狀態返回對應的 CSS class
     * @param {string} status - WebSocket 狀態 (connected/connecting/disconnected/error)
     * @returns {string} CSS class
     */
    getStatusClass(status) {
        const statusMap = {
            'connected': 'text-success',
            'connecting': 'text-warning',
            'disconnected': 'text-muted',
            'error': 'text-danger',
        };
        return statusMap[status] || 'text-muted';
    }

    /**
     * 檢查指定實例是否為當前實例
     * @param {number} instanceId - 實例 ID
     * @returns {boolean} 是否為當前實例
     */
    isCurrentInstance(instanceId) {
        return instanceId === this.state.currentId;
    }
}

// ⚠️ DEPRECATED: Registry registration is commented out
// If you need to re-enable this component, uncomment the following lines:

// // 註冊到 systray registry
// // sequence: 2 表示顯示在公司切換器（sequence: 1）之後
// export const systrayItem = {
//     Component: HaInstanceSystray,
// };
//
// registry.category("systray").add("ha_instance_systray", systrayItem, { sequence: 2 });
