/** @odoo-module **/

import { useState } from "@odoo/owl";
import { callService as portalCallService, fetchState } from "../portal_entity_service";
import { createActionExecutor, buildActionsFromConfig } from "../../hooks/entity_control";

/**
 * Portal-specific Entity Control Hook
 * Uses callService style, consistent with HA API
 * Authentication via Odoo session cookie (no token needed)
 *
 * API unified with useEntityControl:
 * - state: { entityState, attributes, isLoading, error }
 * - actions: { toggle, turnOn, turnOff, ..., callService }
 * - entityId, domain: metadata
 * - refresh: Portal-specific manual refresh method
 *
 * @param {Object} entityData - Entity initial data { id, domain, entity_state, ... }
 * @returns {Object} { state, actions, entityId, domain, refresh }
 *   - state: Reactive state with entityState, attributes, isLoading, error
 *   - actions: Domain-specific actions plus generic callService(service, additionalData)
 *   - entityId: HA entity_id string for display
 *   - domain: Entity domain string
 *   - refresh: Async function to manually refresh state from server
 */
export function usePortalEntityControl(entityData) {
    // Use Odoo record ID for API calls, HA entity_id for display
    const odooId = entityData.id;  // Odoo record ID (integer)
    const haEntityId = entityData.entity_id;  // HA entity ID string (e.g., "switch.test_switch")
    const domain = entityData.domain;

    const state = useState({
        entityState: entityData.entity_state || "unknown",
        attributes: entityData.attributes || {},
        isLoading: false,
        error: null,
    });

    // Create service caller using portal service (no token needed)
    const serviceCaller = async (serviceDomain, service, serviceData) => {
        const result = await portalCallService(serviceDomain, service, serviceData);

        if (result.success) {
            state.entityState = result.state;
            // Fix: use result.data.attributes instead of result.attributes
            // Backend returns { success, state, data: { attributes, ... } }
            if (result.data && result.data.attributes) {
                state.attributes = { ...state.attributes, ...result.data.attributes };
            }
        } else {
            // Ensure error is a string
            const errorMsg = typeof result.error === 'string'
                ? result.error
                : (result.error?.message || JSON.stringify(result.error) || "Service call failed");
            throw new Error(errorMsg);
        }

        return result;
    };

    // Create action executor (no optimistic updates for portal - wait for server response)
    const executor = createActionExecutor(serviceCaller, state, {
        loadingKey: "isLoading",
    });

    // Build actions using unified buildActionsFromConfig (no optimistic updates for portal)
    const baseActions = buildActionsFromConfig(executor, odooId, domain, {
        enableOptimistic: false,
    });

    // Use baseActions directly (aliases removed in refactoring)
    const actions = { ...baseActions };

    /**
     * Refresh Entity state
     */
    async function refresh() {
        state.isLoading = true;
        state.error = null;

        try {
            const result = await fetchState(odooId);
            if (result.success && result.data) {
                state.entityState = result.data.entity_state;
                state.attributes = result.data.attributes || {};
            } else {
                state.error = result.error;
            }
            return result;
        } catch (e) {
            state.error = e.message;
            return { success: false, error: e.message };
        } finally {
            state.isLoading = false;
        }
    }

    /**
     * Generic callService method
     * @param {string} service - e.g., "turn_on", "set_brightness"
     * @param {Object} additionalData - Additional parameters like { brightness: 255 }
     */
    async function callServiceAction(service, additionalData = {}) {
        return executor({
            domain,
            service,
            serviceData: { entity_id: odooId, ...additionalData },
        });
    }

    // Add callService to actions for consistency with useEntityControl
    actions.callService = callServiceAction;

    return {
        state,
        actions,
        entityId: haEntityId,  // Return HA entity ID for display
        domain,
        refresh,
    };
}
