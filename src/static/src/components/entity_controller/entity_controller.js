/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useEntityControl } from "./hooks/useEntityControl";

/**
 * EntityController - Shared component for rendering domain-specific entity controls
 *
 * This component handles all entity domains (switch, light, sensor, climate, etc.)
 * and renders appropriate controls based on the entity's domain.
 *
 * Usage:
 *   <EntityController entity="entityData"/>
 *
 * Where entityData is a plain object with { entity_id, domain, state, attributes, ... }
 */
export class EntityController extends Component {
  static template = "odoo_ha_addon.EntityController";
  static props = {
    entity: { type: Object },
  };

  setup() {
    // Use shared hook for control logic
    const { state, actions, entityId, domain } = useEntityControl(this.props.entity);

    this.state = state;
    this.actions = actions;
    this.entityId = entityId;
    this.domain = domain;

    // Temporary slider values for immediate visual feedback
    this.sliderValues = useState({
      fanPercentage: null,
      brightness: null,
      coverPosition: null,
    });
  }

  // Helper methods for templates
  get entityData() {
    return this.props.entity;
  }

  get isOn() {
    return this.state.entityState === 'on';
  }

  get isOff() {
    return this.state.entityState === 'off';
  }

  // Get current display value for sliders (temporary value or actual value)
  get currentFanPercentage() {
    return this.sliderValues.fanPercentage !== null
      ? this.sliderValues.fanPercentage
      : (this.state.attributes?.percentage || 0);
  }

  get currentBrightness() {
    return this.sliderValues.brightness !== null
      ? this.sliderValues.brightness
      : (this.state.attributes?.brightness || 0);
  }

  get currentCoverPosition() {
    return this.sliderValues.coverPosition !== null
      ? this.sliderValues.coverPosition
      : (this.state.attributes?.current_position || 0);
  }

  // Domain-specific action wrappers (called from templates)
  async onToggle() {
    await this.actions.toggle();
  }

  onBrightnessInput(brightness) {
    // Update temporary value for immediate visual feedback
    this.sliderValues.brightness = parseInt(brightness);
  }

  async onSetBrightness(brightness) {
    // Optimistic update: keep the slider at final position
    const finalValue = parseInt(brightness);
    this.sliderValues.brightness = finalValue;

    // Call API when user releases the slider
    try {
      await this.actions.setBrightness(finalValue);
      // Clear temporary value after a short delay to allow WebSocket update
      setTimeout(() => {
        this.sliderValues.brightness = null;
      }, 1000);
    } catch (error) {
      // On error, immediately clear temporary value to show actual state
      this.sliderValues.brightness = null;
    }
  }

  async onSetTemperature(temp) {
    await this.actions.setTemperature(temp);
  }

  // Automation domain actions
  async onTurnOn() {
    await this.actions.turnOn();
  }

  async onTurnOff() {
    await this.actions.turnOff();
  }

  async onTrigger() {
    await this.actions.trigger();
  }

  // Scene domain actions
  async onActivate() {
    await this.actions.activate();
  }

  // Script domain actions
  async onRun() {
    await this.actions.run();
  }

  // Cover domain actions
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
    // Update temporary value for immediate visual feedback
    this.sliderValues.coverPosition = parseInt(position);
  }

  async onSetCoverPosition(position) {
    // Optimistic update: keep the slider at final position
    const finalValue = parseInt(position);
    this.sliderValues.coverPosition = finalValue;

    // Call API when user releases the slider
    try {
      await this.actions.setCoverPosition(finalValue);
      // Clear temporary value after a short delay to allow WebSocket update
      setTimeout(() => {
        this.sliderValues.coverPosition = null;
      }, 1000);
    } catch (error) {
      // On error, immediately clear temporary value to show actual state
      this.sliderValues.coverPosition = null;
    }
  }

  // Fan domain actions
  onPercentageInput(percentage) {
    // Update temporary value for immediate visual feedback
    this.sliderValues.fanPercentage = parseInt(percentage);
  }

  async onSetPercentage(percentage) {
    // Optimistic update: keep the slider at final position
    const finalValue = parseInt(percentage);
    this.sliderValues.fanPercentage = finalValue;

    // Call API when user releases the slider
    try {
      await this.actions.setPercentage(finalValue);
      // Clear temporary value after a short delay to allow WebSocket update
      setTimeout(() => {
        this.sliderValues.fanPercentage = null;
      }, 1000);
    } catch (error) {
      // On error, immediately clear temporary value to show actual state
      this.sliderValues.fanPercentage = null;
    }
  }

  async onSetDirection(direction) {
    await this.actions.setDirection(direction);
  }

  async onOscillate(oscillate) {
    await this.actions.oscillate(oscillate);
  }

  async onSetPresetMode(presetMode) {
    await this.actions.setPresetMode(presetMode);
  }

  // Climate domain actions
  async onSetFanMode(fanMode) {
    await this.actions.setFanMode(fanMode);
  }
}
