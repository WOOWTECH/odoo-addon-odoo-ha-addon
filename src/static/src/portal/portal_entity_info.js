/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { fetchState } from "./portal_entity_service";

/**
 * PortalEntityInfo - Entity information display component for Portal pages
 *
 * This component displays entity information with real-time state updates.
 * It handles polling internally and provides reactive state updates.
 * Authentication is handled via Odoo session cookie (no token needed).
 *
 * Features:
 * - Entity Info Card (ID, state, domain, area)
 * - Live Status Card (large state display)
 * - Attributes Card (dynamic attributes table)
 * - Auto-polling with visibility control
 *
 * Usage:
 *   <owl-component
 *       name="odoo_ha_addon.PortalEntityInfo"
 *       props="{entity: {...}}"/>
 */
export class PortalEntityInfo extends Component {
    static template = "odoo_ha_addon.PortalEntityInfo";
    static props = {
        entity: { type: Object },
    };

    setup() {
        // Reactive state for real-time updates
        this.state = useState({
            entityState: this.props.entity.entity_state || "unknown",
            lastChanged: this.props.entity.last_changed || null,
            attributes: this.props.entity.attributes || {},
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
    // Computed Properties
    // ========================================

    get entity() {
        return this.props.entity;
    }

    get entityId() {
        return this.props.entity.entity_id;
    }

    get entityName() {
        return this.props.entity.name || this.props.entity.entity_id;
    }

    get domain() {
        return this.props.entity.domain;
    }

    get area() {
        return this.props.entity.area_name || null;
    }

    get hasAttributes() {
        return this.state.attributes && Object.keys(this.state.attributes).length > 0;
    }

    get attributeEntries() {
        if (!this.state.attributes) return [];
        return Object.entries(this.state.attributes);
    }

    // ========================================
    // Polling Methods
    // ========================================

    async fetchAndUpdate() {
        try {
            const result = await fetchState(this.props.entity.id);

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
                this.state.lastChanged = result.data.last_changed;
                this.state.attributes = result.data.attributes || {};
            }
        } catch (error) {
            console.warn("[PortalEntityInfo] Polling error:", error);
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
    "odoo_ha_addon.PortalEntityInfo",
    PortalEntityInfo
);
