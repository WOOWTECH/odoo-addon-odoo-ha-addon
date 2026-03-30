/** @odoo-module **/

/**
 * BlueprintInputs - Dynamic form widget for Blueprint input configuration
 *
 * This widget renders a dynamic form based on the Blueprint's input schema,
 * supporting various Home Assistant selector types:
 *
 * Phase 1 (Basic Types):
 * - entity: Entity selector with domain filtering
 * - text: Text input field
 * - number: Number input with range slider
 * - boolean: Toggle switch
 * - select: Dropdown selection
 * - time: Time picker
 * - target: Entity/Area/Device target selector
 *
 * Phase 2+ (Advanced Types - to be implemented):
 * - device, area, action, condition, trigger, template, object
 * - icon, color_rgb, color_temp, media, location, attribute
 * - theme, addon, backup_location, conversation_agent
 */

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

const { Component, useState, onWillUpdateProps } = owl;

export class BlueprintInputs extends Component {
    static template = "odoo_ha_addon.BlueprintInputs";
    static props = {
        ...standardFieldProps,
        schema_field: { type: String, optional: true },
    };

    setup() {
        this.notification = useService("notification");

        this.state = useState({
            schema: {},
            inputValues: {},
            entities: [],
            areas: [],
            devices: [],
            loadingEntities: false,
            loadingAreas: false,
            entitiesLoaded: false,
            areasLoaded: false,
        });

        this._parseSchema();
        this._parseInputValues();

        // Don't load entities/areas on mount - load lazily when needed
        // This significantly improves initial load time
        onWillUpdateProps((nextProps) => {
            this._parseSchema(nextProps);
            this._parseInputValues(nextProps);
        });
    }

    /**
     * Check if schema needs entity data (lazy loading)
     */
    _needsEntityData() {
        const types = ["entity", "target"];
        for (const def of Object.values(this.state.schema)) {
            const selectorType = this.getSelectorType(def.selector);
            if (types.includes(selectorType)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Check if schema needs area data (lazy loading)
     */
    _needsAreaData() {
        const types = ["area", "target"];
        for (const def of Object.values(this.state.schema)) {
            const selectorType = this.getSelectorType(def.selector);
            if (types.includes(selectorType)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Ensure entities are loaded (lazy load on first access)
     */
    async ensureEntitiesLoaded() {
        if (this.state.entitiesLoaded || this.state.loadingEntities) {
            return;
        }
        await this._loadEntities();
    }

    /**
     * Ensure areas are loaded (lazy load on first access)
     */
    async ensureAreasLoaded() {
        if (this.state.areasLoaded || this.state.loadingAreas) {
            return;
        }
        await this._loadAreas();
    }

    _parseSchema(props = this.props) {
        const schemaField = props.schema_field || "blueprint_schema_json";
        const schemaJson = props.record.data[schemaField];

        if (!schemaJson) {
            this.state.schema = {};
            return;
        }

        try {
            const metadata = JSON.parse(schemaJson);
            this.state.schema = metadata.input || {};
        } catch (e) {
            console.error("Failed to parse blueprint schema:", e);
            this.state.schema = {};
        }
    }

    _parseInputValues(props = this.props) {
        const inputsJson = props.record.data[props.name];

        if (!inputsJson) {
            this.state.inputValues = {};
            return;
        }

        try {
            this.state.inputValues = JSON.parse(inputsJson);
        } catch (e) {
            console.error("Failed to parse blueprint inputs:", e);
            this.state.inputValues = {};
        }
    }

    async _loadEntities() {
        if (this.state.entitiesLoaded || this.state.loadingEntities) {
            return;
        }
        this.state.loadingEntities = true;
        try {
            // Get instance ID from record
            const instanceId = this.props.record.data.ha_instance_id?.[0];
            if (!instanceId) {
                this.state.entities = [];
                this.state.entitiesLoaded = true;
                return;
            }

            const result = await rpc("/web/dataset/call_kw/ha.entity/search_read", {
                model: "ha.entity",
                method: "search_read",
                args: [],
                kwargs: {
                    domain: [["ha_instance_id", "=", instanceId]],
                    fields: ["id", "entity_id", "name", "domain", "entity_state", "device_class"],
                    limit: 2000,
                },
            });

            this.state.entities = result || [];
            this.state.entitiesLoaded = true;
        } catch (e) {
            console.error("Failed to load entities:", e);
            this.state.entities = [];
        } finally {
            this.state.loadingEntities = false;
        }
    }

    async _loadAreas() {
        if (this.state.areasLoaded || this.state.loadingAreas) {
            return;
        }
        this.state.loadingAreas = true;
        try {
            const instanceId = this.props.record.data.ha_instance_id?.[0];
            if (!instanceId) {
                this.state.areas = [];
                this.state.areasLoaded = true;
                return;
            }

            const result = await rpc("/web/dataset/call_kw/ha.area/search_read", {
                model: "ha.area",
                method: "search_read",
                args: [],
                kwargs: {
                    domain: [["ha_instance_id", "=", instanceId]],
                    fields: ["id", "area_id", "name"],
                    limit: 500,
                },
            });

            this.state.areas = result || [];
            this.state.areasLoaded = true;
        } catch (e) {
            console.error("Failed to load areas:", e);
            this.state.areas = [];
        } finally {
            this.state.loadingAreas = false;
        }
    }

    get inputFields() {
        const fields = [];
        let needsEntities = false;
        let needsAreas = false;

        for (const [key, def] of Object.entries(this.state.schema)) {
            const selectorType = this.getSelectorType(def.selector);
            // Track what data we need
            if (["entity", "target"].includes(selectorType)) {
                needsEntities = true;
            }
            if (["area", "target"].includes(selectorType)) {
                needsAreas = true;
            }

            fields.push({
                key,
                name: def.name || key,
                description: def.description || "",
                default: def.default,
                selector: def.selector || {},
                required: !("default" in def),
                value: this.state.inputValues[key],
            });
        }

        // Trigger lazy loading if needed (non-blocking)
        if (needsEntities && !this.state.entitiesLoaded && !this.state.loadingEntities) {
            this._loadEntities();
        }
        if (needsAreas && !this.state.areasLoaded && !this.state.loadingAreas) {
            this._loadAreas();
        }

        return fields;
    }

    /**
     * Determine the input type based on selector
     */
    getSelectorType(selector) {
        if (!selector || Object.keys(selector).length === 0) {
            return "text";
        }

        const type = Object.keys(selector)[0];
        return type;
    }

    /**
     * Check if selector type is supported with UI
     */
    isSupportedType(selector) {
        const type = this.getSelectorType(selector);
        const supportedTypes = [
            "entity", "target", "number", "boolean", "select",
            "time", "text", "duration", "date", "datetime",
            "area", "device"
        ];
        return supportedTypes.includes(type);
    }

    /**
     * Get entities filtered by selector config
     */
    getFilteredEntities(selector) {
        if (!selector) {
            return this.state.entities;
        }

        // Handle both entity selector and target.entity selector
        const config = selector.entity || selector.target?.entity || selector;
        let filtered = this.state.entities;

        if (config.domain) {
            const domains = Array.isArray(config.domain) ? config.domain : [config.domain];
            filtered = filtered.filter(e => domains.includes(e.domain));
        }

        if (config.device_class) {
            const classes = Array.isArray(config.device_class) ? config.device_class : [config.device_class];
            filtered = filtered.filter(e => classes.includes(e.device_class));
        }

        // Sort by name
        filtered.sort((a, b) => (a.name || a.entity_id).localeCompare(b.name || b.entity_id));

        return filtered;
    }

    /**
     * Get number selector config
     */
    getNumberConfig(selector) {
        if (!selector || !selector.number) {
            return { min: 0, max: 100, step: 1, unit: "", mode: "slider" };
        }
        const config = selector.number;
        return {
            min: config.min ?? 0,
            max: config.max ?? 100,
            step: config.step ?? 1,
            unit: config.unit_of_measurement || "",
            mode: config.mode || "slider",
        };
    }

    /**
     * Get select options from selector
     */
    getSelectOptions(selector) {
        if (!selector || !selector.select) {
            return [];
        }
        const options = selector.select.options || [];
        return options.map(opt => {
            if (typeof opt === "string") {
                return { value: opt, label: opt };
            }
            return { value: opt.value, label: opt.label || opt.value };
        });
    }

    /**
     * Get text selector config
     */
    getTextConfig(selector) {
        if (!selector || !selector.text) {
            return { multiline: false, type: "text" };
        }
        const config = selector.text;
        return {
            multiline: config.multiline || false,
            type: config.type || "text",
            suffix: config.suffix || "",
            prefix: config.prefix || "",
        };
    }

    // ===== Event Handlers =====

    /**
     * Update input value and sync to record
     */
    onInputChange(key, value) {
        this.state.inputValues[key] = value;
        this._syncToRecord();
    }

    onEntitySelect(key, ev) {
        const entityId = ev.target.value;
        this.onInputChange(key, entityId || null);
    }

    onMultiEntitySelect(key, ev) {
        // For multi-select entity
        const options = ev.target.selectedOptions;
        const values = Array.from(options).map(opt => opt.value);
        this.onInputChange(key, values.length > 0 ? values : null);
    }

    onNumberInput(key, ev) {
        const value = parseFloat(ev.target.value);
        this.onInputChange(key, isNaN(value) ? null : value);
    }

    onBooleanChange(key, ev) {
        this.onInputChange(key, ev.target.checked);
    }

    onTextInput(key, ev) {
        this.onInputChange(key, ev.target.value || null);
    }

    onSelectChange(key, ev) {
        this.onInputChange(key, ev.target.value || null);
    }

    onTimeInput(key, ev) {
        this.onInputChange(key, ev.target.value || null);
    }

    onDateInput(key, ev) {
        this.onInputChange(key, ev.target.value || null);
    }

    onDatetimeInput(key, ev) {
        this.onInputChange(key, ev.target.value || null);
    }

    onAreaSelect(key, ev) {
        const areaId = ev.target.value;
        this.onInputChange(key, areaId || null);
    }

    /**
     * Handle target selector (entity/area/device)
     */
    onTargetEntitySelect(key, ev) {
        const entityId = ev.target.value;
        if (entityId) {
            this.onInputChange(key, { entity_id: entityId });
        } else {
            this.onInputChange(key, null);
        }
    }

    onTargetAreaSelect(key, ev) {
        const areaId = ev.target.value;
        if (areaId) {
            this.onInputChange(key, { area_id: areaId });
        } else {
            this.onInputChange(key, null);
        }
    }

    /**
     * Handle duration selector
     */
    onDurationChange(key, unit, ev) {
        const currentValue = this.state.inputValues[key] || {};
        const newValue = {
            ...currentValue,
            [unit]: parseInt(ev.target.value) || 0,
        };
        this.onInputChange(key, newValue);
    }

    /**
     * Handle JSON input for advanced types (action, condition, etc.)
     */
    onJsonInput(key, ev) {
        try {
            const value = JSON.parse(ev.target.value);
            this.onInputChange(key, value);
        } catch (e) {
            // Keep the raw text if invalid JSON
            console.warn("Invalid JSON input:", e);
        }
    }

    _syncToRecord() {
        const json = JSON.stringify(this.state.inputValues, null, 2);
        this.props.record.update({ [this.props.name]: json });
    }

    /**
     * Format JSON value for display in textarea
     */
    formatJsonValue(value) {
        if (value === null || value === undefined) {
            return "";
        }
        try {
            return JSON.stringify(value, null, 2);
        } catch (e) {
            return String(value);
        }
    }
}

BlueprintInputs.extractProps = ({ attrs }) => {
    return {
        schema_field: attrs.options?.schema_field || "blueprint_schema_json",
    };
};

registry.category("fields").add("blueprint_inputs", {
    component: BlueprintInputs,
    extractProps: BlueprintInputs.extractProps,
    supportedTypes: ["text"],
});
