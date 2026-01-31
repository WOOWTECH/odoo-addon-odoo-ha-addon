/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { EntityController } from "../entity_controller/entity_controller";
import { RelatedEntityDialog } from "../related_entity_dialog/related_entity_dialog";

/**
 * DeviceCard - A collapsible card component for displaying a device and its entities
 *
 * Features:
 * - Collapsible card with device info header
 * - Displays device metadata (name, manufacturer, model)
 * - Lists all entities under the device with EntityController
 * - Shows area_override badge for entities moved to other areas
 *
 * Usage:
 *   <DeviceCard device="deviceData"/>
 *
 * Where deviceData is:
 * {
 *   id: int,
 *   device_id: str,
 *   name: str,
 *   name_by_user: str,
 *   manufacturer: str,
 *   model: str,
 *   entity_count: int,
 *   entities: [{
 *     id: int,
 *     entity_id: str,
 *     name: str,
 *     entity_state: str,
 *     domain: str,
 *     attributes: dict,
 *     area_override: null | { area_id: int, area_name: str }
 *   }]
 * }
 */
export class DeviceCard extends Component {
    static template = "odoo_ha_addon.DeviceCard";
    static components = { EntityController };
    static props = {
        device: { type: Object },
    };

    /**
     * Initialize component state
     * Sets default expanded state to true (card starts expanded)
     */
    setup() {
        this.state = useState({
            expanded: true,
        });

        // Dialog service for showing related entity dialog
        this.dialogService = useService("dialog");
    }

    /**
     * Show related entity dialog for a specific entity
     * @param {Object} entity - Entity data
     */
    onShowRelatedFor(entity) {
        this.dialogService.add(RelatedEntityDialog, {
            entityId: entity.entity_id,
            entityName: entity.name || entity.friendly_name,
        });
    }

    /**
     * Toggle the card's expanded/collapsed state
     */
    toggleExpand() {
        this.state.expanded = !this.state.expanded;
    }

    /**
     * Get the display name for the device
     * Priority: name_by_user > name > fallback to "Unknown Device"
     * @returns {string} The device display name
     */
    get displayName() {
        return this.props.device.name_by_user || this.props.device.name || _t("Unknown Device");
    }

    /**
     * Get the total number of entities in this device
     * @returns {number} Entity count
     */
    get entityCount() {
        return this.props.device.entities?.length || 0;
    }

    /**
     * Get entities that belong to this device's area (no area override)
     * These entities are displayed normally in the device card
     * @returns {Array<Object>} Entities without area_override
     */
    get normalEntities() {
        return (this.props.device.entities || []).filter(e => !e.area_override);
    }

    /**
     * Get entities that have been moved to other areas
     * These entities have area_override set, meaning their area differs from device's area
     * @returns {Array<Object>} Entities with area_override containing { area_id, area_name }
     */
    get overriddenEntities() {
        return (this.props.device.entities || []).filter(e => e.area_override);
    }

    /**
     * Check if any entities have been moved to other areas
     * Used to conditionally render the "moved to other areas" section
     * @returns {boolean} True if there are overridden entities
     */
    get hasOverriddenEntities() {
        return this.overriddenEntities.length > 0;
    }

    /**
     * Get tooltip text for overridden entities badge
     * @returns {string} Translated tooltip text
     */
    get overriddenTooltip() {
        return _t("Some entities moved to other areas");
    }

    /**
     * Get label for the "moved to other areas" section header
     * @returns {string} Translated label text
     */
    get movedToOtherAreasLabel() {
        return _t("Moved to other areas:");
    }

    /**
     * Get label for empty device state
     * @returns {string} Translated empty state text
     */
    get noEntitiesLabel() {
        return _t("No entities in this device");
    }

    /**
     * Get formatted manufacturer and model information
     * Combines manufacturer and model with " - " separator
     * @returns {string} Formatted string like "Manufacturer - Model" or just one if other is missing
     */
    get manufacturerInfo() {
        const parts = [];
        if (this.props.device.manufacturer) {
            parts.push(this.props.device.manufacturer);
        }
        if (this.props.device.model) {
            parts.push(this.props.device.model);
        }
        return parts.join(" - ");
    }
}
