/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { usePortalEntityControl } from "./hooks/usePortalEntityControl";

/**
 * PortalEntityController - Entity control component for Portal pages
 *
 * This component provides entity control functionality for Portal (public) pages.
 * It uses the Portal-specific hook which calls the user-authenticated API
 * (session cookie) instead of the old token-based API.
 *
 * Only users with 'control' permission can see and use this component.
 *
 * Usage:
 *   <PortalEntityController entity="entityData" permission="control"/>
 */
export class PortalEntityController extends Component {
    static template = "odoo_ha_addon.PortalEntityController";
    static props = {
        entity: { type: Object },
        permission: { type: String, optional: true },
    };

    setup() {
        // Use Portal-specific hook for control logic
        // API matches useEntityControl: { state, actions, entityId, domain, refresh }
        const { state, actions, entityId, domain, refresh } = usePortalEntityControl(
            this.props.entity
        );

        this.controlState = state;
        this.actions = actions;
        this.refresh = refresh;
        this.entityId = entityId;
        this.domainValue = domain;

        // Temporary slider values for immediate visual feedback
        this.sliderValues = useState({
            fanPercentage: null,
            brightness: null,
            coverPosition: null,
        });
    }

    // Computed properties
    get entity() {
        // Return props entity for static data, state for reactive updates
        return this.props.entity;
    }

    get domain() {
        return this.domainValue;
    }

    get permission() {
        return this.props.permission || 'control';
    }

    get entityState() {
        return this.controlState.entityState;
    }

    get isOn() {
        return this.controlState.entityState === "on";
    }

    get isOff() {
        return this.controlState.entityState === "off";
    }

    get isLoading() {
        return this.controlState.isLoading;
    }

    get error() {
        return this.controlState.error;
    }

    get attributes() {
        return this.controlState.attributes || {};
    }

    // Get current display value for sliders
    get currentFanPercentage() {
        return this.sliderValues.fanPercentage !== null
            ? this.sliderValues.fanPercentage
            : this.attributes.percentage || 0;
    }

    get currentBrightness() {
        return this.sliderValues.brightness !== null
            ? this.sliderValues.brightness
            : this.attributes.brightness || 0;
    }

    get currentCoverPosition() {
        return this.sliderValues.coverPosition !== null
            ? this.sliderValues.coverPosition
            : this.attributes.current_position || 0;
    }

    // Action handlers for templates
    async onToggle() {
        await this.actions.toggle();
    }

    async onTurnOn() {
        await this.actions.turnOn();
    }

    async onTurnOff() {
        await this.actions.turnOff();
    }

    // Brightness controls
    onBrightnessInput(brightness) {
        this.sliderValues.brightness = parseInt(brightness);
    }

    async onSetBrightness(brightness) {
        const finalValue = parseInt(brightness);
        this.sliderValues.brightness = finalValue;

        try {
            await this.actions.setBrightness(finalValue);
            setTimeout(() => {
                this.sliderValues.brightness = null;
            }, 1000);
        } catch (e) {
            this.sliderValues.brightness = null;
        }
    }

    // Fan controls
    onPercentageInput(percentage) {
        this.sliderValues.fanPercentage = parseInt(percentage);
    }

    async onSetPercentage(percentage) {
        const finalValue = parseInt(percentage);
        this.sliderValues.fanPercentage = finalValue;

        try {
            await this.actions.setPercentage(finalValue);
            setTimeout(() => {
                this.sliderValues.fanPercentage = null;
            }, 1000);
        } catch (e) {
            this.sliderValues.fanPercentage = null;
        }
    }

    // Cover controls
    async onOpenCover() {
        await this.actions.openCover();
    }

    async onCloseCover() {
        await this.actions.closeCover();
    }

    async onStopCover() {
        await this.actions.stopCover();
    }

    onCoverPositionInput(position) {
        this.sliderValues.coverPosition = parseInt(position);
    }

    async onSetCoverPosition(position) {
        const finalValue = parseInt(position);
        this.sliderValues.coverPosition = finalValue;

        try {
            await this.actions.setCoverPosition(finalValue);
            setTimeout(() => {
                this.sliderValues.coverPosition = null;
            }, 1000);
        } catch (e) {
            this.sliderValues.coverPosition = null;
        }
    }

    // Climate controls
    async onSetTemperature(temperature) {
        await this.actions.setTemperature(parseFloat(temperature));
    }

    async onSetHvacMode(mode) {
        await this.actions.setHvacMode(mode);
    }

    async onSetFanMode(fanMode) {
        await this.actions.setFanMode(fanMode);
    }

    // Fan extended controls
    async onSetDirection(direction) {
        await this.actions.setDirection(direction);
    }

    async onOscillate(oscillating) {
        await this.actions.oscillate(oscillating);
    }

    async onSetPresetMode(presetMode) {
        await this.actions.setPresetMode(presetMode);
    }

    // Automation controls
    async onTrigger() {
        await this.actions.trigger();
    }

    // Script controls
    async onRun() {
        await this.actions.run();
    }

    // Scene controls
    async onActivate() {
        await this.actions.activate();
    }

    // Refresh state
    async onRefresh() {
        await this.refresh();
    }
}

// Register component for <owl-component> tag usage in portal pages
registry.category("public_components").add(
    "odoo_ha_addon.PortalEntityController",
    PortalEntityController
);
