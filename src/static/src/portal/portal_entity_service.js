/** @odoo-module **/

/**
 * Portal Entity Service
 *
 * Portal-specific Entity control service using user-based authentication.
 * Uses HA call_service style API with unified entry point for all control requests.
 * Authentication is handled via Odoo session cookie (no token needed).
 */

/**
 * Generic API request method
 * @param {string} url - API endpoint
 * @param {Object} options - fetch options
 * @param {boolean} isJsonRpc - Whether this is JSON-RPC format (needs result unwrapping)
 * @returns {Promise<Object>} API response
 */
async function _fetch(url, options, isJsonRpc = false) {
    const response = await fetch(url, {
        ...options,
        credentials: 'include',  // Include session cookie for authentication
        headers: {
            ...options.headers,
        }
    });
    const data = await response.json();

    // JSON-RPC format needs result unwrapping
    if (isJsonRpc) {
        if (data.error) {
            // Odoo JSON-RPC error format:
            // { error: { code: 200, message: "Odoo Server Error", data: { message: "actual error", ... } } }
            const odooError = data.error;
            const errorMsg = odooError.data?.message
                || odooError.data?.debug?.split('\n')[0]
                || odooError.message
                || 'RPC Error';
            console.error('[Portal] RPC Error:', odooError);
            return {
                success: false,
                error: errorMsg,
                error_code: odooError.data?.name || 'rpc_error'
            };
        }
        return data.result || data;
    }

    return data;
}

/**
 * Call HA service (unified entry point)
 * @param {string} domain - e.g., "light", "switch", "climate"
 * @param {string} service - e.g., "turn_on", "set_temperature"
 * @param {Object} serviceData - Contains entity_id and other parameters
 * @returns {Promise<Object>} { success, state, last_changed, error }
 */
export async function callService(domain, service, serviceData) {
    return _fetch('/portal/call-service', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            jsonrpc: '2.0',
            params: { domain, service, service_data: serviceData }
        })
    }, true);  // isJsonRpc = true
}

/**
 * Get Entity state
 * @param {number} entityId - Entity ID
 * @returns {Promise<Object>} { success, data: { entity_state, last_changed, attributes }, error }
 */
export async function fetchState(entityId) {
    return _fetch(`/portal/entity/${entityId}/state`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            jsonrpc: '2.0',
            method: 'call',
            params: {},
            id: Date.now()
        })
    }, true);  // isJsonRpc = true
}

/**
 * Get Entity Group state
 * @param {number} groupId - Entity Group ID
 * @returns {Promise<Object>} { success, data: { name, description, entities: [...] }, error }
 */
export async function fetchGroupState(groupId) {
    return _fetch(`/portal/entity_group/${groupId}/state`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            jsonrpc: '2.0',
            method: 'call',
            params: {},
            id: Date.now()
        })
    }, true);  // isJsonRpc = true
}

/**
 * Portal Entity Service Object
 * Provides unified service interface
 */
export const portalEntityService = {
    callService,
    fetchState,
    fetchGroupState,
};
