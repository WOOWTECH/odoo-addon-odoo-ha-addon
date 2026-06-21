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
      colorTemp: null,
      coverPosition: null,
      coverTiltPosition: null,
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

  get currentColorTemp() {
    return this.sliderValues.colorTemp !== null
      ? this.sliderValues.colorTemp
      : (this.state.attributes?.color_temp_kelvin || this.state.attributes?.min_color_temp_kelvin || 2700);
  }

  get currentCoverPosition() {
    return this.sliderValues.coverPosition !== null
      ? this.sliderValues.coverPosition
      : (this.state.attributes?.current_position || 0);
  }

  get currentCoverTiltPosition() {
    return this.sliderValues.coverTiltPosition !== null
      ? this.sliderValues.coverTiltPosition
      : (this.state.attributes?.current_tilt_position || 0);
  }

  // Check if light supports RGB-compatible color modes
  get supportsRgbColor() {
    const modes = this.state.attributes?.supported_color_modes || [];
    return modes.some((m) => ['rgb', 'rgbw', 'rgbww', 'hs', 'xy'].includes(m));
  }

  // Convert current rgb_color attribute to hex string for <input type="color">
  get currentRgbHex() {
    const rgb = this.state.attributes?.rgb_color;
    if (rgb && rgb.length >= 3) {
      const toHex = (v) => Math.max(0, Math.min(255, v)).toString(16).padStart(2, '0');
      return `#${toHex(rgb[0])}${toHex(rgb[1])}${toHex(rgb[2])}`;
    }
    return '#ffffff';
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

  onColorTempInput(colorTemp) {
    this.sliderValues.colorTemp = parseInt(colorTemp);
  }

  async onSetColorTemp(colorTemp) {
    const finalValue = parseInt(colorTemp);
    this.sliderValues.colorTemp = finalValue;

    try {
      await this.actions.setColorTemp(finalValue);
      setTimeout(() => {
        this.sliderValues.colorTemp = null;
      }, 1000);
    } catch (error) {
      this.sliderValues.colorTemp = null;
    }
  }

  // RGB color control - converts hex color to [r, g, b] array
  async onSetRgbColor(hexColor) {
    const r = parseInt(hexColor.slice(1, 3), 16);
    const g = parseInt(hexColor.slice(3, 5), 16);
    const b = parseInt(hexColor.slice(5, 7), 16);
    await this.actions.setRgbColor({ rgb_color: [r, g, b] });
  }

  // Effect control
  async onSetEffect(effect) {
    await this.actions.setEffect({ effect });
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

  // Cover tilt actions
  async onOpenCoverTilt() {
    await this.actions.openCoverTilt();
  }

  async onCloseCoverTilt() {
    await this.actions.closeCoverTilt();
  }

  async onStopCoverTilt() {
    await this.actions.stopCoverTilt();
  }

  onCoverTiltPositionInput(position) {
    this.sliderValues.coverTiltPosition = parseInt(position);
  }

  async onSetCoverTiltPosition(position) {
    const finalValue = parseInt(position);
    this.sliderValues.coverTiltPosition = finalValue;

    try {
      await this.actions.setCoverTiltPosition(finalValue);
      setTimeout(() => {
        this.sliderValues.coverTiltPosition = null;
      }, 1000);
    } catch (error) {
      this.sliderValues.coverTiltPosition = null;
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
  async onSetHvacMode(mode) {
    await this.actions.setHvacMode(mode);
  }

  async onSetFanMode(fanMode) {
    await this.actions.setFanMode(fanMode);
  }

  async onSetSwingMode(swingMode) {
    await this.actions.setSwingMode(swingMode);
  }

  // Climate preset mode is handled by onSetPresetMode (shared with fan domain)

  // Phase 1: Button / Lock / Humidifier actions
  async onPress() {
    await this.actions.press();
  }

  async onLock() {
    await this.actions.lock();
  }

  async onUnlock() {
    await this.actions.unlock();
  }

  async onOpen() {
    await this.actions.open();
  }

  async onSetHumidity(humidity) {
    await this.actions.setHumidity(parseInt(humidity));
  }

  async onSetMode(mode) {
    await this.actions.setMode(mode);
  }

  // Number increment/decrement helpers (parseFloat not available in OWL templates)
  async onDecrementValue() {
    const current = parseFloat(this.state.entityState) || 0;
    const step = this.state.attributes?.step || 1;
    const min = this.state.attributes?.min;
    const newVal = current - step;
    await this.actions.setValue(min != null ? Math.max(min, newVal) : newVal);
  }

  async onIncrementValue() {
    const current = parseFloat(this.state.entityState) || 0;
    const step = this.state.attributes?.step || 1;
    const max = this.state.attributes?.max;
    const newVal = current + step;
    await this.actions.setValue(max != null ? Math.min(max, newVal) : newVal);
  }

  // Phase 2: Number / Text / Select / Datetime actions
  async onSetValue(value) {
    // Clamp to min/max for number-like domains
    if (this.domain === 'input_number' || this.domain === 'number') {
      let numVal = parseFloat(value);
      const min = this.state.attributes?.min;
      const max = this.state.attributes?.max;
      if (min != null) numVal = Math.max(min, numVal);
      if (max != null) numVal = Math.min(max, numVal);
      await this.actions.setValue(numVal);
      return;
    }
    await this.actions.setValue(value);
  }

  async onSelectOption(option) {
    await this.actions.selectOption(option);
  }

  async onSetDatetime(datetime) {
    await this.actions.setDatetime(datetime);
  }

  // Phase 3: Media Player actions
  async onMediaPlay() {
    await this.actions.mediaPlay();
  }

  async onMediaPause() {
    await this.actions.mediaPause();
  }

  async onMediaStop() {
    await this.actions.mediaStop();
  }

  async onMediaNextTrack() {
    await this.actions.mediaNextTrack();
  }

  async onMediaPreviousTrack() {
    await this.actions.mediaPreviousTrack();
  }

  async onSetVolume(volume) {
    await this.actions.setVolume(parseFloat(volume));
  }

  async onVolumeMute(mute) {
    await this.actions.volumeMute(mute);
  }

  async onSelectSource(source) {
    await this.actions.selectSource(source);
  }

  async onSelectSoundMode(soundMode) {
    await this.actions.selectSoundMode(soundMode);
  }

  async onShuffleSet(shuffle) {
    await this.actions.shuffleSet(shuffle);
  }

  async onRepeatSet(repeat) {
    await this.actions.repeatSet(repeat);
  }

  // Cycle repeat mode: off -> all -> one -> off
  async onRepeatCycle() {
    const current = this.state.attributes?.repeat || 'off';
    const next = current === 'off' ? 'all' : current === 'all' ? 'one' : 'off';
    await this.actions.repeatSet(next);
  }

  // Vacuum actions
  async onStart() {
    await this.actions.start();
  }

  async onStop() {
    await this.actions.stop();
  }

  async onPause() {
    await this.actions.pause();
  }

  async onReturnToBase() {
    await this.actions.returnToBase();
  }

  async onSetFanSpeed(speed) {
    await this.actions.setFanSpeed(speed);
  }

  // Valve actions
  async onOpenValve() {
    await this.actions.openValve();
  }

  async onCloseValve() {
    await this.actions.closeValve();
  }

  async onStopValve() {
    await this.actions.stopValve();
  }

  async onSetValvePosition(position) {
    await this.actions.setValvePosition(parseInt(position));
  }

  // Water Heater actions
  async onSetOperationMode(mode) {
    await this.actions.setOperationMode(mode);
  }

  // Alarm Control Panel actions
  async onArmHome(code) {
    await this.actions.armHome(code);
  }

  async onArmAway(code) {
    await this.actions.armAway(code);
  }

  async onArmNight(code) {
    await this.actions.armNight(code);
  }

  async onDisarm(code) {
    await this.actions.disarm(code);
  }

  // Remote actions
  async onSendCommand(command) {
    await this.actions.sendCommand(command);
  }

  // Lawn Mower actions
  async onStartMowing() {
    await this.actions.startMowing();
  }

  async onDock() {
    await this.actions.dock();
  }

  // Phase 5: Todo actions
  async onAddItem(item) {
    await this.actions.addItem(item);
  }

  // Update actions
  async onInstall() {
    await this.actions.install();
  }

  async onSkip() {
    await this.actions.skip();
  }

  // TTS actions
  async onSpeak(message) {
    await this.actions.speak({ message, entity_id: this.entityId });
  }
}
