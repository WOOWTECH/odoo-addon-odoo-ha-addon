/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { fetchState } from "./portal_entity_service";

/**
 * PortalLiveStatus - Real-time entity state display for Portal sidebar
 *
 * This component displays the current entity state with auto-polling.
 * It's designed for the sidebar Live Status card on portal entity pages.
 *
 * Features:
 * - Large state display
 * - Auto-polling every 5 seconds
 * - Visual feedback on state changes
 * - Visibility-aware polling (pauses when tab is hidden)
 *
 * Usage:
 *   <owl-component
 *       name="odoo_ha_addon.PortalLiveStatus"
 *       props="{entityId: 123, initialState: 'on'}"/>
 */
export class PortalLiveStatus extends Component {
    static template = "odoo_ha_addon.PortalLiveStatus";
    static props = {
        entityId: { type: Number },
        initialState: { type: String, optional: true },
    };

    setup() {
        // Reactive state
        this.state = useState({
            entityState: this.props.initialState || "unknown",
            stateChanged: false,
        });

        // Polling configuration
        this.pollTimer = null;
        this.pollInterval = 5000; // 5 seconds

        // Lifecycle hooks
        onMounted(() => {
            this.startPolling();
            document.addEventListener("visibilitychange", this.onVisibilityChange);
        });

        onWillUnmount(() => {
            this.stopPolling();
            document.removeEventListener("visibilitychange", this.onVisibilityChange);
        });

        // Bind visibility handler
        this.onVisibilityChange = this.onVisibilityChange.bind(this);
    }

    // ========================================
    // Polling Methods
    // ========================================

    async fetchAndUpdate() {
        try {
            const result = await fetchState(this.props.entityId);

            if (result.success && result.data) {
                const newState = result.data.entity_state;

                // Trigger animation on state change
                if (this.state.entityState !== newState) {
                    this.state.stateChanged = true;
                    setTimeout(() => {
                        this.state.stateChanged = false;
                    }, 1000);
                }

                // Update reactive state
                this.state.entityState = newState;
            }
        } catch (error) {
            console.error("[PortalLiveStatus] Polling error:", error);
            // Continue polling even on error
        }
    }

    startPolling() {
        if (this.pollTimer) return; // Avoid duplicate timers

        // Fetch immediately on start
        this.fetchAndUpdate();

        // Set up interval
        this.pollTimer = setInterval(() => {
            this.fetchAndUpdate();
        }, this.pollInterval);
    }

    stopPolling() {
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }
    }

    onVisibilityChange() {
        if (document.hidden) {
            this.stopPolling();
        } else {
            this.startPolling();
        }
    }
}

// Register component for <owl-component> tag usage in portal pages
registry.category("public_components").add(
    "odoo_ha_addon.PortalLiveStatus",
    PortalLiveStatus
);
