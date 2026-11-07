# -*- coding: utf-8 -*-
"""
Home Assistant attribute policy for share-only viewers.

Users who only see an entity through an ha.entity.share (portal users, or
internal users without HA group membership on that entity) must never get
the HA attributes that carry credentials or location data.  The same policy
is applied by the portal controllers (controllers/portal.py) and by the
realtime bus (models/ha_realtime_update.py), so both channels expose exactly
the same data.
"""
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Attribute keys stripped for share-only viewers.  These may contain
# network/auth information or GPS coordinates from Home Assistant.
SENSITIVE_ATTRIBUTE_KEYS = frozenset({
    'access_token', 'token', 'api_key', 'password', 'secret',
    'ip_address', 'mac_address', 'network_key', 'host',
    'latitude', 'longitude', 'gps_accuracy',
})

# Attributes that may embed a credential in a URL query string
# (e.g. camera entity_picture "/api/camera_proxy/camera.x?token=...").
URL_ATTRIBUTE_KEYS = frozenset({'entity_picture'})
SENSITIVE_QUERY_KEYS = frozenset({'token', 'access_token', 'authsig', 'api_key'})

# Top-level state-object keys that are not needed by share-only viewers
# (HA context carries the HA user id that triggered the change).
SENSITIVE_STATE_KEYS = frozenset({'context'})


def _strip_url_credentials(value):
    if not isinstance(value, str) or '?' not in value:
        return value
    parts = urlsplit(value)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if k.lower() not in SENSITIVE_QUERY_KEYS]
    return urlunsplit(parts._replace(query=urlencode(query)))


def sanitize_attributes(attributes):
    """Return a copy of HA ``attributes`` without sensitive keys/credentials."""
    if not attributes or not isinstance(attributes, dict):
        return attributes or {}
    result = {}
    for key, value in attributes.items():
        if not isinstance(key, str) or key.lower() in SENSITIVE_ATTRIBUTE_KEYS:
            continue
        if key.lower() in URL_ATTRIBUTE_KEYS:
            value = _strip_url_credentials(value)
        result[key] = value
    return result


def sanitize_state(state):
    """Return a copy of an HA state object with sanitized attributes."""
    if not isinstance(state, dict):
        return state
    result = {k: v for k, v in state.items() if k not in SENSITIVE_STATE_KEYS}
    if 'attributes' in result:
        result['attributes'] = sanitize_attributes(result.get('attributes'))
    return result
