/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { fetchGroupState } from "./portal_entity_service";
import { PortalEntityController } from "./portal_entity_controller";

/**
 * PortalGroupInfo - Entity group information display component for Portal pages
 *
 * This component displays entity group information with real-time state updates
 * for all entities in the group. Authentication is handled via Odoo session cookie.
 *
 * Features:
 * - Group Header Card (name, description, entity count)
 * - Entities Table (with per-entity state updates)
 * - Statistics Cards (total, online, offline counts)
 * - Auto-polling with visibility control
 * - Permission-based control display
 *
 * Usage:
 *   <owl-component
 *       name="odoo_ha_addon.PortalGroupInfo"
 *       props="{group: {...}, permission: 'view', controllableDomains: [...]}"/>
 */
export class PortalGroupInfo extends Component {
    static template = "odoo_ha_addon.PortalGroupInfo";
    static components = { PortalEntityController };
    static props = {
        group: { type: Object },
        permission: { type: String, optional: true },
        controllableDomains: { type: Array, optional: true },
    };

    setup() {
        // Initialize entities from props
        const initialEntities = (this.props.group.entities || []).map(e => ({
            ...e,
            stateChanged: false,
        }));

        // Reactive state for real-time updates
        this.state = useState({
            entities: initialEntities,
            lastStates: {}, // Track previous states for change detection
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

    get group() {
        return this.props.group;
    }

    get groupName() {
        return this.props.group.name;
    }

    get groupDescription() {
        return this.props.group.description || null;
    }

    get entityCount() {
        return this.state.entities.length;
    }

    get onlineCount() {
        return this.state.entities.filter(
            e => e.entity_state !== "unavailable" && e.entity_state !== "unknown"
        ).length;
    }

    get offlineCount() {
        return this.state.entities.filter(
            e => e.entity_state === "unavailable" || e.entity_state === "unknown"
        ).length;
    }

    get hasEntities() {
        return this.state.entities.length > 0;
    }

    get permission() {
        return this.props.permission || 'view';
    }

    get controllableDomains() {
        return this.props.controllableDomains || [];
    }

    get canControl() {
        return this.permission === 'control';
    }

    /**
     * Check if an entity can be controlled
     * @param {Object} entity - Entity object
     * @returns {boolean} True if entity can be controlled
     */
    canControlEntity(entity) {
        return this.canControl && this.controllableDomains.includes(entity.domain);
    }

    // ========================================
    // Polling Methods
    // ========================================

    async fetchAndUpdate() {
        try {
            const result = await fetchGroupState(this.props.group.id);

            if (result.success && result.data) {
                const newEntities = result.data.entities || [];

                // Update each entity and detect state changes
                const updatedEntities = newEntities.map(entity => {
                    const previousState = this.state.lastStates[entity.id];
                    const stateChanged = previousState !== undefined && previousState !== entity.entity_state;

                    // Update last known state
                    this.state.lastStates[entity.id] = entity.entity_state;

                    return {
                        ...entity,
                        stateChanged,
                    };
                });

                // Update entities array
                this.state.entities = updatedEntities;

                // Clear stateChanged flags after animation
                setTimeout(() => {
                    this.state.entities = this.state.entities.map(e => ({
                        ...e,
                        stateChanged: false,
                    }));
                }, 1000);
            }
        } catch (error) {
            console.warn("[PortalGroupInfo] Polling error:", error);
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
    "odoo_ha_addon.PortalGroupInfo",
    PortalGroupInfo
);
