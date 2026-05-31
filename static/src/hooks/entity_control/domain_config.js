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
                buildParams: (colorTempKelvin) => ({ color_temp_kelvin: parseInt(colorTempKelvin) }),
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

    // =============================================
    // Phase 1: Toggle / Simple Button Domains
    // =============================================

    input_boolean: {
        domain: "input_boolean",
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

    siren: {
        domain: "siren",
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

    button: {
        domain: "button",
        actions: {
            press: {
                service: "press",
            },
        },
    },

    input_button: {
        domain: "input_button",
        actions: {
            press: {
                service: "press",
            },
        },
    },

    lock: {
        domain: "lock",
        actions: {
            lock: {
                service: "lock",
                optimistic: () => "locked",
            },
            unlock: {
                service: "unlock",
                optimistic: () => "unlocked",
            },
            open: {
                service: "open",
                optimistic: () => "open",
            },
        },
    },

    humidifier: {
        domain: "humidifier",
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
            setHumidity: {
                service: "set_humidity",
                buildParams: (humidity) => ({ humidity: parseInt(humidity) }),
            },
            setMode: {
                service: "set_mode",
                buildParams: (mode) => ({ mode }),
            },
        },
    },

    // =============================================
    // Phase 2: Input / Number / Select / Datetime
    // =============================================

    input_number: {
        domain: "input_number",
        actions: {
            setValue: {
                service: "set_value",
                buildParams: (value) => ({ value: parseFloat(value) }),
            },
            increment: {
                service: "increment",
            },
            decrement: {
                service: "decrement",
            },
        },
    },

    number: {
        domain: "number",
        actions: {
            setValue: {
                service: "set_value",
                buildParams: (value) => ({ value: parseFloat(value) }),
            },
        },
    },

    input_text: {
        domain: "input_text",
        actions: {
            setValue: {
                service: "set_value",
                buildParams: (value) => ({ value }),
            },
        },
    },

    text: {
        domain: "text",
        actions: {
            setValue: {
                service: "set_value",
                buildParams: (value) => ({ value }),
            },
        },
    },

    input_select: {
        domain: "input_select",
        actions: {
            selectOption: {
                service: "select_option",
                buildParams: (option) => ({ option }),
            },
            selectNext: {
                service: "select_next",
            },
            selectPrevious: {
                service: "select_previous",
            },
        },
    },

    select: {
        domain: "select",
        actions: {
            selectOption: {
                service: "select_option",
                buildParams: (option) => ({ option }),
            },
            selectFirst: {
                service: "select_first",
            },
            selectLast: {
                service: "select_last",
            },
            selectNext: {
                service: "select_next",
            },
            selectPrevious: {
                service: "select_previous",
            },
        },
    },

    input_datetime: {
        domain: "input_datetime",
        actions: {
            setDatetime: {
                service: "set_datetime",
                buildParams: (datetime) => ({ datetime }),
            },
        },
    },

    date: {
        domain: "date",
        actions: {
            setValue: {
                service: "set_value",
                buildParams: (date) => ({ date }),
            },
        },
    },

    time: {
        domain: "time",
        actions: {
            setValue: {
                service: "set_value",
                buildParams: (time) => ({ time }),
            },
        },
    },

    datetime: {
        domain: "datetime",
        actions: {
            setValue: {
                service: "set_value",
                buildParams: (datetime) => ({ datetime }),
            },
        },
    },

    // =============================================
    // Phase 3: Complex Control Domains
    // =============================================

    media_player: {
        domain: "media_player",
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
            mediaPlay: {
                service: "media_play",
            },
            mediaPause: {
                service: "media_pause",
            },
            mediaStop: {
                service: "media_stop",
            },
            mediaNextTrack: {
                service: "media_next_track",
            },
            mediaPreviousTrack: {
                service: "media_previous_track",
            },
            setVolume: {
                service: "volume_set",
                buildParams: (volume) => ({ volume_level: parseFloat(volume) }),
            },
            volumeMute: {
                service: "volume_mute",
                buildParams: (mute) => ({ is_volume_muted: mute }),
            },
            selectSource: {
                service: "select_source",
                buildParams: (source) => ({ source }),
            },
        },
    },

    vacuum: {
        domain: "vacuum",
        actions: {
            start: {
                service: "start",
            },
            stop: {
                service: "stop",
            },
            pause: {
                service: "pause",
            },
            returnToBase: {
                service: "return_to_base",
            },
            locate: {
                service: "locate",
            },
            setFanSpeed: {
                service: "set_fan_speed",
                buildParams: (speed) => ({ fan_speed: speed }),
            },
        },
    },

    valve: {
        domain: "valve",
        actions: {
            openValve: {
                service: "open_valve",
            },
            closeValve: {
                service: "close_valve",
            },
            stopValve: {
                service: "stop_valve",
            },
            setValvePosition: {
                service: "set_valve_position",
                buildParams: (position) => ({ position: parseInt(position) }),
            },
        },
    },

    water_heater: {
        domain: "water_heater",
        actions: {
            setTemperature: {
                service: "set_temperature",
                buildParams: (temperature) => ({ temperature: parseFloat(temperature) }),
            },
            setOperationMode: {
                service: "set_operation_mode",
                buildParams: (mode) => ({ operation_mode: mode }),
            },
            setAwayMode: {
                service: "set_away_mode",
                buildParams: (awayMode) => ({ away_mode: awayMode }),
            },
        },
    },

    alarm_control_panel: {
        domain: "alarm_control_panel",
        actions: {
            armHome: {
                service: "alarm_arm_home",
                optimistic: () => "armed_home",
                buildParams: (code) => (code ? { code } : {}),
            },
            armAway: {
                service: "alarm_arm_away",
                optimistic: () => "armed_away",
                buildParams: (code) => (code ? { code } : {}),
            },
            armNight: {
                service: "alarm_arm_night",
                optimistic: () => "armed_night",
                buildParams: (code) => (code ? { code } : {}),
            },
            armVacation: {
                service: "alarm_arm_vacation",
                optimistic: () => "armed_vacation",
                buildParams: (code) => (code ? { code } : {}),
            },
            disarm: {
                service: "alarm_disarm",
                optimistic: () => "disarmed",
                buildParams: (code) => (code ? { code } : {}),
            },
            trigger: {
                service: "alarm_trigger",
            },
        },
    },

    remote: {
        domain: "remote",
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
            sendCommand: {
                service: "send_command",
                buildParams: (command) => ({ command }),
            },
        },
    },

    lawn_mower: {
        domain: "lawn_mower",
        actions: {
            startMowing: {
                service: "start_mowing",
            },
            pause: {
                service: "pause",
            },
            dock: {
                service: "dock",
            },
        },
    },

    // =============================================
    // Phase 4: Read-only Display Domains
    // =============================================

    binary_sensor: {
        domain: "binary_sensor",
        readOnly: true,
        actions: {},
    },

    weather: {
        domain: "weather",
        readOnly: true,
        actions: {},
    },

    device_tracker: {
        domain: "device_tracker",
        readOnly: true,
        actions: {},
    },

    person: {
        domain: "person",
        readOnly: true,
        actions: {},
    },

    calendar: {
        domain: "calendar",
        readOnly: true,
        actions: {},
    },

    event: {
        domain: "event",
        readOnly: true,
        actions: {},
    },

    // =============================================
    // Phase 5: Special Control Domains
    // =============================================

    todo: {
        domain: "todo",
        actions: {
            addItem: {
                service: "add_item",
                buildParams: (item) => ({ item }),
            },
            updateItem: {
                service: "update_item",
                buildParams: (params) => params,
            },
            removeItem: {
                service: "remove_item",
                buildParams: (params) => params,
            },
        },
    },

    update: {
        domain: "update",
        actions: {
            install: {
                service: "install",
            },
            skip: {
                service: "skip",
            },
        },
    },

    camera: {
        domain: "camera",
        readOnly: true,
        actions: {},
    },

    tts: {
        domain: "tts",
        actions: {
            speak: {
                service: "speak",
                buildParams: (params) => params,
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
