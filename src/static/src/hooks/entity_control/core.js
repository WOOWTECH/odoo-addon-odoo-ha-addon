/** @odoo-module **/

import { debug } from "../../util/debug";
import { getDomainConfig } from "./domain_config";

/**
 * Creates an action executor function with shared loading/error handling
 *
 * @param {Function} serviceCaller - Async function (domain, service, serviceData) => result
 * @param {Object} stateRef - Reactive state reference with isLoading/loading and error properties
 * @param {Object} options - Configuration options
 * @param {Function} [options.getState] - Get current entity state for optimistic updates
 * @param {Function} [options.setState] - Set entity state for optimistic updates
 * @param {Function} [options.onSuccess] - Callback on successful action
 * @param {Function} [options.onError] - Callback on failed action
 * @param {string} [options.loadingKey='isLoading'] - Key name for loading state
 * @returns {Function} executeAction(actionConfig, additionalData) => Promise
 */
export function createActionExecutor(serviceCaller, stateRef, options = {}) {
    const {
        getState = null,
        setState = null,
        onSuccess = null,
        onError = null,
        loadingKey = "isLoading",
    } = options;

    return async function executeAction(actionConfig, additionalData = {}) {
        const { domain, service, serviceData = {}, optimisticUpdate } = actionConfig;

        // Set loading state
        stateRef[loadingKey] = true;
        stateRef.error = null;

        // Apply optimistic update if configured
        let previousState = null;
        if (optimisticUpdate && getState && setState) {
            previousState = getState();
            const newState = optimisticUpdate(previousState);
            setState(newState);
            debug(`[EntityControl] Optimistic update: ${previousState} -> ${newState}`);
        }

        try {
            const result = await serviceCaller(domain, service, {
                ...serviceData,
                ...additionalData,
            });

            if (onSuccess) {
                onSuccess(result, actionConfig);
            }

            return result;
        } catch (error) {
            stateRef.error = error.message || String(error);

            // Revert optimistic update on error
            if (previousState !== null && setState) {
                setState(previousState);
                debug(`[EntityControl] Reverted optimistic update to: ${previousState}`);
            }

            if (onError) {
                onError(error, actionConfig);
            }

            throw error;
        } finally {
            stateRef[loadingKey] = false;
        }
    };
}

/**
 * Creates a generic callService method
 *
 * @param {Function} executor - The action executor
 * @param {string} domain - Entity domain
 * @param {string} entityId - Entity ID
 * @returns {Function} callService(service, serviceData) => Promise
 */
export function createGenericCallService(executor, domain, entityId) {
    return async function callService(service, serviceData = {}) {
        return executor({
            domain,
            service,
            serviceData: { entity_id: entityId, ...serviceData },
        });
    };
}

/**
 * Build actions object from DOMAIN_CONFIGS
 *
 * Unified action builder for both useEntityControl (Backend) and
 * usePortalEntityControl (Portal). Uses DOMAIN_CONFIGS as the single
 * source of truth for action definitions.
 *
 * @param {Function} executor - Action executor from createActionExecutor
 * @param {string|number} entityId - Entity ID (HA string or Odoo integer)
 * @param {string} domain - Entity domain (e.g., "switch", "light")
 * @param {Object} options - Configuration options
 * @param {boolean} [options.enableOptimistic=true] - Enable optimistic updates
 * @param {Object} [options.stateRef=null] - State reference for buildParams
 * @param {Object} [options.specialHandlers={}] - Override handlers for specific actions
 * @returns {Object} Actions object with all domain-specific methods + callService
 */
export function buildActionsFromConfig(executor, entityId, domain, options = {}) {
    const {
        enableOptimistic = true,
        stateRef = null,
        specialHandlers = {},
    } = options;

    const domainConfig = getDomainConfig(domain);
    if (!domainConfig) {
        // Unknown domain - only provide generic callService
        return {
            callService: createGenericCallService(executor, domain, entityId),
        };
    }

    const actions = {};

    for (const [actionName, config] of Object.entries(domainConfig.actions)) {
        // Check for special handler override
        if (specialHandlers[actionName]) {
            actions[actionName] = specialHandlers[actionName];
            continue;
        }

        actions[actionName] = async (param) => {
            let serviceData = { entity_id: entityId };
            if (config.buildParams) {
                serviceData = { ...serviceData, ...config.buildParams(param, stateRef) };
            }

            return executor({
                domain,
                service: config.service,
                serviceData,
                optimisticUpdate: enableOptimistic ? config.optimistic : null,
            });
        };
    }

    // Add generic callService for unsupported actions
    actions.callService = createGenericCallService(executor, domain, entityId);

    return actions;
}
