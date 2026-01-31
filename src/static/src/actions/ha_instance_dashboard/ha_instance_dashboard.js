/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { _t } from "@web/core/l10n/translation";
import { debug } from "../../util/debug";

/**
 * HA Instance Dashboard - 入口頁
 *
 * 顯示所有 HA Instance 的卡片式瀏覽頁面。
 * 每個卡片包含實例資訊和兩個按鈕：
 * - "HA Info" 按鈕：跳轉到該實例的 HA Info 頁面
 * - "分區" 按鈕：跳轉到該實例的分區頁面
 *
 * 特點：
 * - 不依賴 systray instance 切換器
 * - 通過 doAction() 導航並傳遞 instance_id 參數
 * - 卡片式設計，適合多實例瀏覽
 */
export class HaInstanceDashboard extends Component {
    static template = "odoo_ha_addon.HaInstanceDashboard";
    static components = {};

    setup() {
        this.haDataService = useService("ha_data");
        this.actionService = useService("action");
        this.orm = useService("orm");

        this.state = useState({
            instances: [],
            loading: true,
            error: null,
            isHaManager: false,
        });

        onWillStart(async () => {
            // Odoo 18: 使用 user.hasGroup() 檢查權限
            this.state.isHaManager = await user.hasGroup('odoo_ha_addon.group_ha_manager');
            debug('[HaInstanceDashboard] User is HA Manager:', this.state.isHaManager);

            await this.loadInstances();
        });
    }

    /**
     * 載入所有 HA Instance 列表
     */
    async loadInstances() {
        try {
            this.state.loading = true;
            this.state.error = null;

            const result = await this.haDataService.getInstances();

            if (result.success) {
                this.state.instances = result.data.instances;
                debug('[HaInstanceDashboard] Loaded instances:', this.state.instances.length);
            } else {
                this.state.error = result.error || '無法載入實例列表';
                console.error('[HaInstanceDashboard] Failed to load instances:', result.error);
            }
        } catch (error) {
            this.state.error = error.message || '載入失敗';
            console.error('[HaInstanceDashboard] Error loading instances:', error);
        } finally {
            this.state.loading = false;
        }
    }

    /**
     * 跳轉到 HA Info 頁面（指定 instance）
     *
     * @param {number} instanceId - 實例 ID
     * @param {string} instanceName - 實例名稱（用於顯示）
     */
    openHaInfo(instanceId, instanceName) {
        debug('[HaInstanceDashboard] Opening HA Info for instance:', instanceName);

        this.actionService.doAction({
            type: 'ir.actions.client',
            tag: 'odoo_ha_addon.ha_info_dashboard',
            name: `HA Info - ${instanceName}`,
            context: {
                ha_instance_id: instanceId,
            },
        });
    }

    /**
     * 跳轉到分區頁面（指定 instance）
     *
     * @param {number} instanceId - 實例 ID
     * @param {string} instanceName - 實例名稱（用於顯示）
     */
    openAreaDashboard(instanceId, instanceName) {
        debug('[HaInstanceDashboard] Opening Areas for instance:', instanceName);

        this.actionService.doAction({
            type: 'ir.actions.client',
            tag: 'odoo_ha_addon.ha_area_dashboard',
            name: `分區 - ${instanceName}`,
            context: {
                ha_instance_id: instanceId,
            },
        });
    }

    /**
     * 獲取 WebSocket 狀態的 CSS class
     * @param {string} status - WebSocket 狀態
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
     * 獲取 WebSocket 狀態的顯示文字
     * @param {string} status - WebSocket 狀態
     * @returns {string} 顯示文字
     */
    getStatusText(status) {
        const statusMap = {
            'connected': '已連線',
            'connecting': '連線中',
            'disconnected': '未連線',
            'error': '錯誤',
        };
        return statusMap[status] || '未知';
    }

    /**
     * 開啟新增 HA Instance 的 Modal Form
     *
     * 當使用者點擊 Empty State 的「新增實例」按鈕時呼叫。
     * 打開與 Settings 頁面 "+ New Instance" 按鈕相同的簡易 Modal Form。
     */
    async openInstanceSettings() {
        debug('[HaInstanceDashboard] Opening create instance modal...');

        try {
            // 呼叫 Python 方法取得 action
            const action = await this.orm.call('ha.instance', 'action_open_create_modal', []);

            // 執行 action 並在關閉後重新載入實例列表
            await this.actionService.doAction(action, {
                onClose: async () => {
                    debug('[HaInstanceDashboard] Modal closed, reloading instances...');
                    try {
                        await this.loadInstances();
                    } catch (error) {
                        console.error('[HaInstanceDashboard] Failed to reload instances after modal close:', error);
                        // loadInstances() 已有內部錯誤處理，這裡只做日誌記錄
                    }
                },
            });
        } catch (error) {
            console.error('[HaInstanceDashboard] Failed to open create instance modal:', error);
            this.haDataService.showError(_t("無法開啟新增實例視窗：") + (error.message || error));
        }
    }
}

registry.category("actions").add("odoo_ha_addon.ha_instance_dashboard", HaInstanceDashboard);
