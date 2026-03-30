/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { EntityController } from "../entity_controller/entity_controller";
import { RelatedEntityDialog } from "../related_entity_dialog/related_entity_dialog";

/**
 * StandaloneEntityCard - A card component for entities without a device or moved from another device
 *
 * Features:
 * - Displays entity info with EntityController
 * - Shows source_device badge for entities moved from another device's area
 * - Card-based layout for grid display
 *
 * Usage:
 *   <StandaloneEntityCard entity="entityData"/>
 *
 * Where entityData is:
 * {
 *   id: int,
 *   entity_id: str,
 *   name: str,
 *   entity_state: str,
 *   domain: str,
 *   attributes: dict,
 *   source_device: null | {
 *     device_id: int,
 *     device_name: str,
 *     device_area_name: str
 *   }
 * }
 */
export class StandaloneEntityCard extends Component {
    static template = "odoo_ha_addon.StandaloneEntityCard";
    static components = { EntityController };
    static props = {
        entity: { type: Object },
    };

    setup() {
        // Dialog service for showing related entity dialog
        this.dialogService = useService("dialog");
    }

    get displayName() {
        return this.props.entity.name || this.props.entity.entity_id;
    }

    get hasSourceDevice() {
        return !!this.props.entity.source_device;
    }

    get sourceDeviceInfo() {
        const source = this.props.entity.source_device;
        if (!source) return null;
        return `${source.device_name} (${source.device_area_name})`;
    }

    /**
     * Show related entity dialog
     */
    onShowRelated() {
        this.dialogService.add(RelatedEntityDialog, {
            entityId: this.props.entity.entity_id,
            entityName: this.props.entity.name || this.props.entity.friendly_name,
        });
    }
}
