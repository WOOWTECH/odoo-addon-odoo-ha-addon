/** @odoo-module **/

import { useState, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { createActionExecutor, buildActionsFromConfig } from "../../../hooks/entity_control";
import { debug } from "../../../util/debug";

/**
 * Shared hook for entity control logic
 * Handles state management, real-time updates, and device control
 *
 * @param {Object} entityData - Entity data (plain object)
 * @returns {Object} { state, actions, entityId, domain }
 */
export function useEntityControl(entityData) {
    const haDataService = useService("ha_data");
    const entityId = entityData.entity_id;
    const domain = entityData.domain;

    // Reactive state - maintain full entity data for real-time updates
    const state = useState({
        entityState: entityData.entity_state || "unknown",
        attributes: entityData.attributes || {},
        isLoading: false,
        error: null,
    });

    // Subscribe to real-time updates via WebSocket
    const stateChangeHandler = (data) => {
        if (data.new_state) {
            if (typeof data.new_state === "object") {
                if (data.new_state.state) {
                    state.entityState = data.new_state.state;
                }
                if (data.new_state.attributes) {
                    state.attributes = { ...state.attributes, ...data.new_state.attributes };
                    debug(`[useEntityControl] State and attributes updated for ${entityId}:`, {
                        state: state.entityState,
                        attributes: state.attributes,
                    });
                } else {
                    debug(`[useEntityControl] State updated for ${entityId}:`, state.entityState);
                }
            } else {
                state.entityState = data.new_state;
                debug(`[useEntityControl] State updated for ${entityId}:`, state.entityState);
            }
        }
    };

    // Register WebSocket callback
    if (haDataService.onEntityUpdate) {
        haDataService.onEntityUpdate(entityId, stateChangeHandler);

        onWillUnmount(() => {
            if (haDataService.offEntityUpdate) {
                haDataService.offEntityUpdate(entityId, stateChangeHandler);
                debug(`[useEntityControl] Unsubscribed from ${entityId}`);
            }
        });
    }

    // Create service caller using ha_data service
    const serviceCaller = async (domain, service, serviceData) => {
        return haDataService.callService(domain, service, serviceData);
    };

    // Create action executor with optimistic update support
    const executor = createActionExecutor(serviceCaller, state, {
        getState: () => state.entityState,
        setState: (newState) => {
            state.entityState = newState;
        },
        onSuccess: (_result, config) => {
            debug(`[useEntityControl] ${config.service} succeeded for ${entityId}`);
        },
        onError: (error, config) => {
            console.error(`[useEntityControl] ${config.service} failed:`, error);
        },
    });

    // Special handler for setPercentage (complex logic for fan)
    const createSetFanPercentage = () => async (percentage) => {
        const percentValue = parseInt(percentage);
        let service = "set_percentage";
        let serviceData = { entity_id: entityId, percentage: percentValue };

        // Special handling: turn_on if >0 and off, turn_off if 0
        if (percentValue > 0 && state.entityState === "off") {
            service = "turn_on";
            serviceData = { entity_id: entityId, percentage: percentValue };
        } else if (percentValue === 0) {
            service = "turn_off";
            serviceData = { entity_id: entityId };
        }

        return executor({
            domain: "fan",
            service,
            serviceData,
            optimisticUpdate: percentValue === 0 ? () => "off" : percentValue > 0 ? () => "on" : null,
        });
    };

    // Build actions using unified buildActionsFromConfig
    const baseActions = buildActionsFromConfig(executor, entityId, domain, {
        enableOptimistic: true,
        stateRef: state,
        specialHandlers: {
            setPercentage: createSetFanPercentage(),
        },
    });

    // Use baseActions directly (aliases removed in refactoring)
    const actions = baseActions;

    return {
        state,
        actions,
        entityId,
        domain,
    };
}

