/** @odoo-module **/

import { whenReady } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { mount } from "@odoo/owl";
import { templates } from "@web/core/assets";

/**
 * Portal OWL Component Mount Script
 *
 * Scans the DOM for portal mount point divs (.o_portal_entity_controller,
 * .o_portal_entity_info, .o_portal_group_info) and mounts the corresponding
 * OWL components with props extracted from data-* attributes.
 *
 * This replaces the <owl-component> tag approach, allowing server-rendered
 * mount points with data-* attributes that define the component's props.
 */

/**
 * Parse data-* attributes from an element into a props object
 * Converts kebab-case attribute names to camelCase prop names
 */
function parseDataAttributes(el) {
    const data = {};
    for (const attr of el.attributes) {
        if (attr.name.startsWith("data-")) {
            const key = attr.name
                .slice(5) // remove "data-"
                .replace(/-([a-z])/g, (_, c) => c.toUpperCase()); // kebab to camelCase
            data[key] = attr.value;
        }
    }
    return data;
}

/**
 * Mount PortalEntityController components
 * Reads entity data from data-* attributes and passes as props
 */
function mountEntityControllers(ComponentClass) {
    const elements = document.querySelectorAll(".o_portal_entity_controller");
    for (const el of elements) {
        const data = parseDataAttributes(el);

        // Build entity object from data attributes
        const entity = {
            id: parseInt(data.entityId),
            entity_id: data.entityHaId || "",
            domain: data.entityDomain || "",
            entity_state: data.entityState || "unknown",
            name: data.entityName || "",
            attributes: data.attributes ? JSON.parse(data.attributes) : {},
        };

        const props = {
            entity,
            permission: data.permission || "control",
            stateUrl: data.stateUrl,
            serviceUrl: data.serviceUrl,
        };

        mount(ComponentClass, el, { templates, props });
    }
}

/**
 * Mount PortalEntityInfo components
 * Reads entity data from data-* attributes and passes as props
 */
function mountEntityInfos(ComponentClass) {
    const elements = document.querySelectorAll(".o_portal_entity_info");
    for (const el of elements) {
        const data = parseDataAttributes(el);

        // Build minimal entity object for info display
        const entity = {
            id: parseInt(data.entityId),
            entity_id: data.entityHaId || "",
            entity_state: data.entityState || "unknown",
            name: data.entityName || "",
            domain: data.entityDomain || "",
            attributes: {},
        };

        const props = {
            entity,
            stateUrl: data.stateUrl,
        };

        mount(ComponentClass, el, { templates, props });
    }
}

/**
 * Mount PortalGroupInfo components
 * Reads group data from data-* attributes and passes as props
 */
function mountGroupInfos(ComponentClass) {
    const elements = document.querySelectorAll(".o_portal_group_info");
    for (const el of elements) {
        const data = parseDataAttributes(el);

        // Build group object (entities will be fetched via polling)
        const group = {
            id: parseInt(data.groupId),
            name: data.groupName || "",
            entities: [], // Will be populated by polling
        };

        const controllableDomains = data.controllableDomains
            ? data.controllableDomains.split(",").filter(Boolean)
            : [];

        const props = {
            group,
            permission: data.permission || "view",
            controllableDomains,
            stateUrl: data.stateUrl,
            serviceUrl: data.serviceUrl,
        };

        mount(ComponentClass, el, { templates, props });
    }
}

/**
 * Initialize all portal OWL components after DOM is ready
 */
whenReady(() => {
    const publicComponents = registry.category("public_components");

    // Mount PortalEntityController instances
    const EntityController = publicComponents.get("odoo_ha_addon.PortalEntityController", null);
    if (EntityController && document.querySelector(".o_portal_entity_controller")) {
        mountEntityControllers(EntityController);
    }

    // Mount PortalEntityInfo instances
    const EntityInfo = publicComponents.get("odoo_ha_addon.PortalEntityInfo", null);
    if (EntityInfo && document.querySelector(".o_portal_entity_info")) {
        mountEntityInfos(EntityInfo);
    }

    // Mount PortalGroupInfo instances
    const GroupInfo = publicComponents.get("odoo_ha_addon.PortalGroupInfo", null);
    if (GroupInfo && document.querySelector(".o_portal_group_info")) {
        mountGroupInfos(GroupInfo);
    }
});
