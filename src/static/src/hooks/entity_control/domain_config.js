/** @odoo-module **/

/**
 * Domain Action Configuration Registry
 *
 * Defines available actions for each Home Assistant domain.
 * Used by both useEntityControl (Odoo) and usePortalEntityControl (Portal).
 *
 * Configuration format:
 * - service: HA service name to call
 * - optimistic: Function to compute optimistic state update (prev => newState)
 * - buildParams: Function to transform action arguments to service_data
 */

export const DOMAIN_CONFIGS = {
    switch: {
        domain: "switch",
        actions: {
            toggle: {
                service: "toggle",
                optimistic: (prev) => (prev === "on" ? "off" : "on"),
            },
            turnOn: {
                service: "turn_on",
                optimistic: () => "on",
            },
            turnOff: {
                service: "turn_off",
                optimistic: () => "off",
            },
        },
    },

    light: {
        domain: "light",
        actions: {
            toggle: {
                service: "toggle",
                optimistic: (prev) => (prev === "on" ? "off" : "on"),
            },
            turnOn: {
                service: "turn_on",
                optimistic: () => "on",
            },
            turnOff: {
                service: "turn_off",
                optimistic: () => "off",
            },
            setBrightness: {
                service: "turn_on",
                buildParams: (brightness) => ({ brightness: parseInt(brightness) }),
            },
            setColorTemp: {
                service: "turn_on",
                buildParams: (colorTemp) => ({ color_temp: colorTemp }),
            },
        },
    },

    climate: {
        domain: "climate",
        actions: {
            setTemperature: {
                service: "set_temperature",
                buildParams: (temperature) => ({ temperature: parseFloat(temperature) }),
            },
            setHvacMode: {
                service: "set_hvac_mode",
                buildParams: (mode) => ({ hvac_mode: mode }),
            },
            setFanMode: {
                service: "set_fan_mode",
                buildParams: (fanMode) => ({ fan_mode: fanMode }),
            },
        },
    },

    automation: {
        domain: "automation",
        actions: {
            toggle: {
                service: "toggle",
                optimistic: (prev) => (prev === "on" ? "off" : "on"),
            },
            turnOn: {
                service: "turn_on",
                optimistic: () => "on",
            },
            turnOff: {
                service: "turn_off",
                optimistic: () => "off",
            },
            trigger: {
                service: "trigger",
                buildParams: () => ({ skip_condition: true }),
            },
        },
    },

    scene: {
        domain: "scene",
        actions: {
            activate: {
                service: "turn_on",
            },
        },
    },

    script: {
        domain: "script",
        actions: {
            run: {
                service: "turn_on",
            },
            toggle: {
                service: "toggle",
                optimistic: (prev) => (prev === "on" ? "off" : "on"),
            },
        },
    },

    cover: {
        domain: "cover",
        actions: {
            openCover: {
                service: "open_cover",
            },
            closeCover: {
                service: "close_cover",
            },
            stopCover: {
                service: "stop_cover",
            },
            setCoverPosition: {
                service: "set_cover_position",
                buildParams: (position) => ({ position: parseInt(position) }),
            },
        },
    },

    fan: {
        domain: "fan",
        actions: {
            toggle: {
                service: "toggle",
                optimistic: (prev) => (prev === "on" ? "off" : "on"),
            },
            turnOn: {
                service: "turn_on",
                optimistic: () => "on",
            },
            turnOff: {
                service: "turn_off",
                optimistic: () => "off",
            },
            setPercentage: {
                service: "set_percentage",
                buildParams: (percentage) => ({ percentage: parseInt(percentage) }),
                // Special handling for percentage=0 (turn off) is done in the hook
            },
            setDirection: {
                service: "set_direction",
                buildParams: (direction) => ({ direction }),
            },
            oscillate: {
                service: "oscillate",
                buildParams: (oscillating) => ({ oscillating }),
            },
            setPresetMode: {
                service: "set_preset_mode",
                buildParams: (presetMode) => ({ preset_mode: presetMode }),
            },
        },
    },
};

/**
 * Get domain configuration
 * @param {string} domain - Domain name (e.g., "switch", "light")
 * @returns {Object|null} Domain configuration or null if not found
 */
export function getDomainConfig(domain) {
    return DOMAIN_CONFIGS[domain] || null;
}

/**
 * Check if domain supports a specific action
 * @param {string} domain - Domain name
 * @param {string} action - Action name
 * @returns {boolean}
 */
export function domainSupportsAction(domain, action) {
    const config = DOMAIN_CONFIGS[domain];
    return config && config.actions && action in config.actions;
}

/**
 * Get all supported domains
 * @returns {string[]} Array of domain names
 */
export function getSupportedDomains() {
    return Object.keys(DOMAIN_CONFIGS);
}
