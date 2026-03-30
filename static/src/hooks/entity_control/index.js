/** @odoo-module **/

/**
 * Entity Control Core Module
 *
 * Shared logic for entity control hooks.
 * Used by both useEntityControl (Odoo internal) and usePortalEntityControl (Portal public).
 */

// Core functions
export {
    createActionExecutor,
    createGenericCallService,
    buildActionsFromConfig,
} from "./core";

// Domain configuration
export {
    DOMAIN_CONFIGS,
    getDomainConfig,
    domainSupportsAction,
    getSupportedDomains,
} from "./domain_config";
