# -*- coding: utf-8 -*-
"""
Home Assistant service-call policy shared by the backend dashboard
(/odoo_ha_addon/call_service) and the portal (/my/ha/.../service).

Goals:
- only well-known domain/service pairs can be called by non-managers;
- only the parameters the UI actually sends (see
  static/src/hooks/entity_control/domain_config.js) are forwarded;
- HA target selectors (area_id, device_id, floor_id, label_id, target)
  are never forwarded, so a call cannot fan out to entities that the
  caller is not authorised for;
- numeric parameters must be finite numbers (no NaN / Infinity).
"""
import math

# Services whitelist using HA call_service naming convention.
CONTROL_SERVICES = {
    'switch': ['toggle', 'turn_on', 'turn_off'],
    'light': ['toggle', 'turn_on', 'turn_off', 'set_brightness', 'set_color_temp'],
    'fan': ['toggle', 'turn_on', 'turn_off', 'set_percentage', 'set_preset_mode', 'set_direction', 'oscillate'],
    'climate': ['set_temperature', 'set_hvac_mode', 'set_fan_mode', 'set_swing_mode', 'set_preset_mode'],
    'cover': ['open_cover', 'close_cover', 'stop_cover', 'set_cover_position',
              'open_cover_tilt', 'close_cover_tilt', 'stop_cover_tilt', 'set_cover_tilt_position'],
    'scene': ['turn_on'],
    'script': ['toggle', 'turn_on', 'turn_off'],
    'automation': ['toggle', 'trigger', 'turn_on', 'turn_off'],
    'sensor': [],
    'input_boolean': ['toggle', 'turn_on', 'turn_off'],
    'siren': ['toggle', 'turn_on', 'turn_off'],
    'button': ['press'],
    'input_button': ['press'],
    'lock': ['lock', 'unlock', 'open'],
    'humidifier': ['toggle', 'turn_on', 'turn_off', 'set_humidity', 'set_mode'],
    'input_number': ['set_value', 'increment', 'decrement'],
    'number': ['set_value'],
    'input_text': ['set_value'],
    'text': ['set_value'],
    'input_select': ['select_option', 'select_next', 'select_previous', 'select_first', 'select_last'],
    'select': ['select_option', 'select_first', 'select_last', 'select_next', 'select_previous'],
    'input_datetime': ['set_datetime'],
    'date': ['set_value'],
    'time': ['set_value'],
    'datetime': ['set_value'],
    'media_player': ['toggle', 'turn_on', 'turn_off', 'media_play', 'media_pause', 'media_stop',
                     'media_next_track', 'media_previous_track', 'volume_set', 'volume_mute', 'select_source',
                     'select_sound_mode', 'shuffle_set', 'repeat_set'],
    'vacuum': ['start', 'stop', 'pause', 'return_to_base', 'locate', 'set_fan_speed'],
    'valve': ['open_valve', 'close_valve', 'stop_valve', 'set_valve_position'],
    'water_heater': ['set_temperature', 'set_operation_mode', 'set_away_mode'],
    'alarm_control_panel': ['alarm_arm_home', 'alarm_arm_away', 'alarm_arm_night',
                            'alarm_arm_vacation', 'alarm_disarm', 'alarm_trigger'],
    'remote': ['toggle', 'turn_on', 'turn_off', 'send_command'],
    'lawn_mower': ['start_mowing', 'pause', 'dock'],
    'binary_sensor': [],
    'weather': [],
    'device_tracker': [],
    'person': [],
    'calendar': [],
    'event': [],
    'todo': ['add_item', 'update_item', 'remove_item'],
    'update': ['install', 'skip'],
    'camera': [],
    'tts': ['speak'],
}

# Domains that an internal HA User (non-manager) may never call from the
# backend dashboard: they run arbitrary HA actions or system operations.
MANAGER_ONLY_DOMAINS = frozenset({
    'homeassistant', 'hassio', 'shell_command', 'script', 'automation',
    'python_script', 'rest_command', 'pyscript', 'recorder', 'logger',
    'system_log', 'persistent_notification', 'notify', 'backup', 'cloud',
    'frontend', 'conversation', 'zone', 'mqtt',
})

# HA target selectors. HA merges these with entity_id, so forwarding them
# would let one authorised entity reach every entity of an area/device/...
TARGET_SELECTOR_KEYS = frozenset({'area_id', 'device_id', 'floor_id', 'label_id', 'target'})

# Parameters that reference another entity and must be authorised too.
ENTITY_REFERENCE_KEYS = frozenset({'media_player_entity_id'})

# Per-domain parameters forwarded to HA (besides entity_id).
DOMAIN_PARAMS = {
    'light': {'brightness', 'brightness_pct', 'brightness_step', 'brightness_step_pct',
              'color_temp', 'color_temp_kelvin', 'kelvin', 'rgb_color', 'rgbw_color',
              'rgbww_color', 'hs_color', 'xy_color', 'color_name', 'white', 'effect',
              'transition', 'flash'},
    'climate': {'temperature', 'target_temp_high', 'target_temp_low', 'hvac_mode',
                'fan_mode', 'swing_mode', 'preset_mode'},
    'automation': {'skip_condition'},
    'scene': {'transition'},
    'cover': {'position', 'tilt_position'},
    'fan': {'percentage', 'direction', 'oscillating', 'preset_mode'},
    'siren': {'tone', 'volume_level', 'duration'},
    'lock': {'code'},
    'humidifier': {'humidity', 'mode'},
    'input_number': {'value'},
    'number': {'value'},
    'input_text': {'value'},
    'text': {'value'},
    'input_select': {'option', 'cycle'},
    'select': {'option', 'cycle'},
    'input_datetime': {'date', 'time', 'datetime', 'timestamp'},
    'date': {'date'},
    'time': {'time'},
    'datetime': {'datetime'},
    'media_player': {'volume_level', 'is_volume_muted', 'source', 'sound_mode',
                     'shuffle', 'repeat'},
    'vacuum': {'fan_speed'},
    'valve': {'position'},
    'water_heater': {'temperature', 'operation_mode', 'away_mode'},
    'alarm_control_panel': {'code'},
    'remote': {'command', 'device', 'num_repeats', 'delay_secs', 'hold_secs', 'activity'},
    'todo': {'item', 'rename', 'status', 'description', 'due_date', 'due_datetime'},
    'update': {'version', 'backup'},
    'tts': {'message', 'language', 'cache', 'options', 'media_player_entity_id'},
}

# Parameters that must be finite numbers (per domain where ambiguous).
NUMERIC_PARAMS = frozenset({
    'brightness', 'brightness_pct', 'brightness_step', 'brightness_step_pct',
    'color_temp', 'color_temp_kelvin', 'kelvin', 'white', 'transition',
    'temperature', 'target_temp_high', 'target_temp_low',
    'position', 'tilt_position', 'percentage', 'humidity', 'volume_level',
    'duration', 'num_repeats', 'delay_secs', 'hold_secs', 'timestamp',
})
NUMERIC_VALUE_DOMAINS = frozenset({'input_number', 'number'})
NUMERIC_LIST_PARAMS = frozenset({'rgb_color', 'rgbw_color', 'rgbww_color', 'hs_color', 'xy_color'})
# Free-form dict parameters (only scalar values inside are accepted).
DICT_PARAMS = frozenset({'options'})

MAX_STRING_LENGTH = 1024
MAX_LIST_LENGTH = 32


class ServicePolicyError(ValueError):
    """Raised when a service call is rejected; ``code`` is a short error code."""

    def __init__(self, message, code='invalid_params'):
        super().__init__(message)
        self.code = code


def is_finite_number(value):
    """True for int/float (not bool) values that are finite."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)


def coerce_finite_number(value, key):
    """Return a finite number from value (number or numeric string) or raise."""
    if isinstance(value, bool):
        raise ServicePolicyError('Parameter %s must be a number' % key)
    if isinstance(value, str):
        try:
            value = float(value.strip())
        except ValueError:
            raise ServicePolicyError('Parameter %s must be a number' % key)
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ServicePolicyError('Parameter %s must be a finite number' % key)
    return value


def _check_scalar(value, key):
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            raise ServicePolicyError('Parameter %s must be a finite number' % key)
        return value
    if isinstance(value, str):
        if len(value) > MAX_STRING_LENGTH:
            raise ServicePolicyError('Parameter %s is too long' % key)
        return value
    raise ServicePolicyError('Parameter %s has an unsupported type' % key)


def _check_value(domain, key, value):
    if key in NUMERIC_PARAMS or (key == 'value' and domain in NUMERIC_VALUE_DOMAINS):
        return coerce_finite_number(value, key)
    if key in NUMERIC_LIST_PARAMS:
        if not isinstance(value, (list, tuple)) or not 1 <= len(value) <= 5:
            raise ServicePolicyError('Parameter %s must be a list of numbers' % key)
        return [coerce_finite_number(v, key) for v in value]
    if key in DICT_PARAMS:
        if not isinstance(value, dict) or len(value) > MAX_LIST_LENGTH:
            raise ServicePolicyError('Parameter %s must be an object' % key)
        return {str(k): _check_scalar(v, key) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        if len(value) > MAX_LIST_LENGTH:
            raise ServicePolicyError('Parameter %s has too many items' % key)
        return [_check_scalar(v, key) for v in value]
    return _check_scalar(value, key)


def normalize_entity_ids(value):
    """Return entity_id(s) as a non-empty list of strings or raise."""
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, (list, tuple)):
        values = list(value)
    else:
        raise ServicePolicyError('entity_id must be a string or a list of strings', 'invalid_entity')
    if not values or len(values) > MAX_LIST_LENGTH:
        raise ServicePolicyError('entity_id is required in service_data', 'invalid_entity')
    result = []
    for item in values:
        if not isinstance(item, str) or not item or item.strip().lower() in ('all', 'none'):
            raise ServicePolicyError('Invalid entity_id', 'invalid_entity')
        result.append(item.strip())
    return result


def check_domain_service(domain, service, allow_any=False):
    """
    Validate a (domain, service) pair.

    ``allow_any`` (HA managers on the backend) skips the whitelist but still
    requires well-formed names.
    """
    if not isinstance(domain, str) or not isinstance(service, str) or not domain or not service:
        raise ServicePolicyError('domain and service are required', 'missing_params')
    if allow_any:
        return
    if domain in MANAGER_ONLY_DOMAINS or domain not in CONTROL_SERVICES:
        raise ServicePolicyError('Domain not allowed: %s' % domain, 'domain_denied')
    if service not in CONTROL_SERVICES[domain]:
        raise ServicePolicyError(
            'Service not allowed for this domain: %s.%s' % (domain, service), 'service_denied')


def sanitize_service_params(domain, service_data, passthrough_unknown_domain=False):
    """
    Return the forwarded parameters of ``service_data`` (without entity_id).

    - target selectors are always dropped;
    - for known domains only DOMAIN_PARAMS keys are kept (unknown keys are
      silently dropped, matching what the UI may send);
    - for unknown domains nothing is kept unless ``passthrough_unknown_domain``
      (HA managers only), in which case non-selector keys are kept but still
      type-checked.
    """
    if service_data is None:
        service_data = {}
    if not isinstance(service_data, dict):
        raise ServicePolicyError('service_data must be an object', 'invalid_params')
    allowed = DOMAIN_PARAMS.get(domain)
    params = {}
    for key, value in service_data.items():
        if not isinstance(key, str) or key == 'entity_id' or key in TARGET_SELECTOR_KEYS:
            continue
        if allowed is not None:
            if key not in allowed:
                continue
        elif not passthrough_unknown_domain:
            continue
        params[key] = _check_value(domain, key, value)
    return params
