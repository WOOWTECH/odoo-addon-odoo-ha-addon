# -*- coding: utf-8 -*-
"""
Portal Controller for Entity and Entity Group user-based access.

This controller provides user-authenticated endpoints for viewing shared entities
and entity groups via ha.entity.share records. It inherits from CustomerPortal
to use native Odoo 18 portal patterns (sort, filter, pagination, breadcrumbs).

Security:
- Routes use auth='user' requiring Odoo login
- Access checked via ha.entity.share records
- Field whitelists prevent exposure of sensitive data
- sudo() is used only for reading, never for writing
- Expired shares are treated as no access (403)
"""
from collections import OrderedDict

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv.expression import AND
import logging

_logger = logging.getLogger(__name__)

# Field whitelist for portal entity access
# Only these fields will be exposed to public viewers
PORTAL_ENTITY_FIELDS = [
    'id',
    'name',
    'entity_id',
    'entity_state',
    'last_changed',
    'area_id',
    'domain',
    'attributes',
]

# Attribute keys that should be stripped from portal responses
# These may contain sensitive network/auth info from Home Assistant
PORTAL_SENSITIVE_ATTRIBUTE_KEYS = {
    'access_token', 'token', 'api_key', 'password', 'secret',
    'ip_address', 'mac_address', 'network_key', 'host',
    'latitude', 'longitude', 'gps_accuracy',
}


def _sanitize_portal_attributes(attributes):
    """Strip sensitive keys from HA entity attributes for portal display."""
    if not attributes or not isinstance(attributes, dict):
        return attributes or {}
    return {
        k: v for k, v in attributes.items()
        if k.lower() not in PORTAL_SENSITIVE_ATTRIBUTE_KEYS
    }


# Field whitelist for portal entity group access
PORTAL_GROUP_FIELDS = [
    'id',
    'name',
    'description',
    'entity_ids',
    'entity_count',
]

# Services whitelist using HA call_service naming convention
# Includes advanced controls like brightness, temperature, etc.
PORTAL_CONTROL_SERVICES = {
    # Original 9 domains
    'switch': ['toggle', 'turn_on', 'turn_off'],
    'light': ['toggle', 'turn_on', 'turn_off', 'set_brightness', 'set_color_temp'],
    'fan': ['toggle', 'turn_on', 'turn_off', 'set_percentage', 'set_preset_mode', 'set_direction', 'oscillate'],
    'climate': ['set_temperature', 'set_hvac_mode', 'set_fan_mode', 'set_swing_mode', 'set_preset_mode'],
    'cover': ['open_cover', 'close_cover', 'stop_cover', 'set_cover_position',
              'open_cover_tilt', 'close_cover_tilt', 'stop_cover_tilt', 'set_cover_tilt_position'],
    'scene': ['turn_on'],
    'script': ['toggle', 'turn_on', 'turn_off'],
    'automation': ['toggle', 'trigger', 'turn_on', 'turn_off'],
    'sensor': [],  # Read-only, no control actions
    # Phase 1: Toggle / Simple Button Domains
    'input_boolean': ['toggle', 'turn_on', 'turn_off'],
    'siren': ['toggle', 'turn_on', 'turn_off'],
    'button': ['press'],
    'input_button': ['press'],
    'lock': ['lock', 'unlock', 'open'],
    'humidifier': ['toggle', 'turn_on', 'turn_off', 'set_humidity', 'set_mode'],
    # Phase 2: Input Domains
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
    # Phase 3: Complex Control Domains
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
    # Phase 4: Read-only Display Domains (no control services)
    'binary_sensor': [],
    'weather': [],
    'device_tracker': [],
    'person': [],
    'calendar': [],
    'event': [],
    # Phase 5: Special Control Domains
    'todo': ['add_item', 'update_item', 'remove_item'],
    'update': ['install', 'skip'],
    'camera': [],  # Read-only
    'tts': ['speak'],
}


class HAPortalController(CustomerPortal):
    """
    Controller for portal access to entities and entity groups.

    Inherits CustomerPortal to use native Odoo 18 portal patterns
    (sort, filter, pagination, breadcrumbs).
    All routes use auth='user' requiring Odoo login.
    Access is controlled via ha.entity.share records.
    """

    # ========================================
    # CustomerPortal Integration
    # ========================================

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'ha_share_count' in counters:
            values['ha_share_count'] = request.env['ha.entity.share'].sudo().search_count([
                ('user_id', '=', request.env.user.id),
                ('is_expired', '=', False),
            ])
        return values

    # ========================================
    # Access Control Helpers
    # ========================================

    def _check_entity_share_access(self, entity_id, user_id, required_permission='view'):
        """
        Check if user has access to entity via direct share OR via group share.

        This method first checks for a direct entity share, then falls back to
        checking if the entity belongs to any group that the user has access to.

        Args:
            entity_id: ha.entity record ID
            user_id: res.users record ID
            required_permission: 'view' or 'control'

        Returns:
            ha.entity.share record if access granted, False otherwise
        """
        # 1. Check direct entity share
        share = request.env['ha.entity.share'].sudo().search([
            ('entity_id', '=', entity_id),
            ('user_id', '=', user_id),
            ('is_expired', '=', False),
        ], limit=1)

        if share:
            if required_permission == 'control' and share.permission != 'control':
                pass  # Continue to check group share
            else:
                return share

        # 2. Fall back to group share: find groups that contain this entity
        groups = request.env['ha.entity.group'].sudo().search([
            ('entity_ids', 'in', [entity_id])
        ])

        if groups:
            group_share = request.env['ha.entity.share'].sudo().search([
                ('group_id', 'in', groups.ids),
                ('user_id', '=', user_id),
                ('is_expired', '=', False),
            ], limit=1)

            if group_share:
                if required_permission == 'control' and group_share.permission != 'control':
                    _logger.debug(
                        f"Entity {entity_id} control denied via group share "
                        f"(user: {user_id}, group share permission: {group_share.permission})"
                    )
                    return False
                _logger.debug(
                    f"Entity {entity_id} access granted via group share "
                    f"(user: {user_id}, permission: {required_permission})"
                )
                return group_share

        return False

    def _check_group_share_access(self, group_id, user_id, required_permission='view'):
        """
        Check if user has access to entity group via ha.entity.share.

        Args:
            group_id: ha.entity.group record ID
            user_id: res.users record ID
            required_permission: 'view' or 'control'

        Returns:
            ha.entity.share record if access granted, False otherwise
        """
        share = request.env['ha.entity.share'].sudo().search([
            ('group_id', '=', group_id),
            ('user_id', '=', user_id),
            ('is_expired', '=', False),
        ], limit=1)

        if not share:
            return False

        if required_permission == 'control' and share.permission != 'control':
            return False

        return share

    def _check_device_share_access(self, device_id, user_id, required_permission='view'):
        """
        Check if user has access to device via ha.entity.share.

        Args:
            device_id: ha.device record ID
            user_id: res.users record ID
            required_permission: 'view' or 'control'

        Returns:
            ha.entity.share record if access granted, False otherwise
        """
        share = request.env['ha.entity.share'].sudo().search([
            ('device_id', '=', device_id),
            ('user_id', '=', user_id),
            ('is_expired', '=', False),
        ], limit=1)

        if not share:
            return False

        if required_permission == 'control' and share.permission != 'control':
            return False

        return share

    # ========================================
    # Data Extraction Helpers
    # ========================================

    def _get_safe_entity_data(self, entity):
        """Extract whitelisted fields from an entity record."""
        data = entity.read(PORTAL_ENTITY_FIELDS)[0]
        if data.get('area_id') and isinstance(data['area_id'], tuple):
            data['area_id'] = {
                'id': data['area_id'][0],
                'name': data['area_id'][1],
            }
        if data.get('last_changed'):
            data['last_changed'] = data['last_changed'].isoformat()
        data['attributes'] = _sanitize_portal_attributes(data.get('attributes'))
        return data

    def _get_safe_group_data(self, group):
        """Extract whitelisted fields from an entity group record."""
        data = group.read(PORTAL_GROUP_FIELDS)[0]
        if data.get('entity_ids'):
            entities = request.env['ha.entity'].sudo().browse(data['entity_ids'])
            data['entities'] = [{
                'id': e.id,
                'name': e.name,
                'entity_id': e.entity_id,
                'entity_state': e.entity_state,
                'domain': e.domain,
            } for e in entities]
            del data['entity_ids']
        return data

    # ========================================
    # Share Query Helpers
    # ========================================

    def _get_user_shares(self, user_id):
        """Get all valid (non-expired) shares for a user."""
        return request.env['ha.entity.share'].sudo().search([
            ('user_id', '=', user_id),
            ('is_expired', '=', False),
        ])

    def _get_user_share_count(self, user_id):
        """Get the count of valid shares for a user."""
        return request.env['ha.entity.share'].sudo().search_count([
            ('user_id', '=', user_id),
            ('is_expired', '=', False),
        ])

    def _get_user_instances_with_shares(self, user_id):
        """Get all HA instances that have shares for the user."""
        shares = self._get_user_shares(user_id)
        instance_data = {}

        for share in shares:
            instance = share.ha_instance_id
            if not instance:
                continue

            if instance.id not in instance_data:
                instance_data[instance.id] = {
                    'instance': instance,
                    'entity_shares': [],
                    'group_shares': [],
                    'device_shares': [],
                    'total_count': 0,
                }

            if share.entity_id:
                instance_data[instance.id]['entity_shares'].append(share)
            elif share.group_id:
                instance_data[instance.id]['group_shares'].append(share)
            elif share.device_id:
                instance_data[instance.id]['device_shares'].append(share)
            instance_data[instance.id]['total_count'] += 1

        return instance_data

    # ========================================
    # Hub Page: /my/ha
    # ========================================

    @http.route(
        '/my/ha',
        type='http',
        auth='user',
        website=True,
        sitemap=False
    )
    def portal_my_ha(self, **kw):
        """Portal page showing all HA instances with shares for the current user."""
        user = request.env.user
        instance_data = self._get_user_instances_with_shares(user.id)

        instances_with_counts = []
        for data in instance_data.values():
            instances_with_counts.append({
                'instance': data['instance'],
                'entity_count': len(data['entity_shares']),
                'group_count': len(data['group_shares']),
                'device_count': len(data['device_shares']),
                'total_count': data['total_count'],
            })

        instances_with_counts.sort(key=lambda x: x['instance'].name)

        return request.render('odoo_ha_addon.portal_my_ha', {
            'instances': instances_with_counts,
            'page_name': 'portal_my_ha',
        })

    # ========================================
    # Instance Detail Page: /my/ha/<instance_id>
    # ========================================

    def _get_entity_searchbar_sortings(self):
        return OrderedDict([
            ('name_asc', {'label': _('Name (A-Z)'), 'order': 'name asc'}),
            ('name_desc', {'label': _('Name (Z-A)'), 'order': 'name desc'}),
            ('last_changed', {'label': _('Recently Changed'), 'order': 'last_changed desc'}),
            ('domain', {'label': _('Domain'), 'order': 'domain asc, name asc'}),
        ])

    def _get_entity_searchbar_filters(self, entity_shares):
        """Build dynamic filter options based on user's actual entity domains."""
        entities = entity_shares.mapped('entity_id')
        domains = sorted(set(d for d in entities.mapped('domain') if d))
        searchbar_filters = OrderedDict([
            ('all', {'label': _('All'), 'domain': []}),
        ])
        for d in domains:
            searchbar_filters[d] = {
                'label': d.capitalize(),
                'domain': [('domain', '=', d)],
            }
        return searchbar_filters

    def _get_group_searchbar_sortings(self):
        return OrderedDict([
            ('name_asc', {'label': _('Name (A-Z)'), 'order': 'name asc'}),
            ('name_desc', {'label': _('Name (Z-A)'), 'order': 'name desc'}),
            ('entity_count', {'label': _('Entity Count'), 'order': 'entity_count desc'}),
        ])

    def _get_device_searchbar_sortings(self):
        return OrderedDict([
            ('name_asc', {'label': _('Name (A-Z)'), 'order': 'name asc'}),
            ('name_desc', {'label': _('Name (Z-A)'), 'order': 'name desc'}),
            ('manufacturer', {'label': _('Manufacturer'), 'order': 'manufacturer asc, name asc'}),
        ])

    def _get_device_searchbar_filters(self, device_shares):
        """Build dynamic filter options based on user's actual device manufacturers."""
        devices = device_shares.mapped('device_id')
        manufacturers = sorted(set(m for m in devices.mapped('manufacturer') if m))
        searchbar_filters = OrderedDict([
            ('all', {'label': _('All'), 'domain': []}),
        ])
        for m in manufacturers:
            searchbar_filters[m] = {
                'label': m,
                'domain': [('manufacturer', '=', m)],
            }
        return searchbar_filters

    @http.route([
        '/my/ha/<int:instance_id>',
        '/my/ha/<int:instance_id>/page/<int:page>',
    ],
        type='http',
        auth='user',
        website=True,
        sitemap=False
    )
    def portal_my_ha_instance(self, instance_id, tab='entities', page=1,
                              sortby=None, filterby=None, **kw):
        """
        Portal page showing entities, groups and devices shared from a specific
        HA instance with sort/filter/pagination per tab.
        """
        user = request.env.user
        page = int(page)
        step = 20

        # Check if instance exists
        instance = request.env['ha.instance'].sudo().browse(instance_id)
        if not instance.exists():
            _logger.warning(f"Portal /my/ha access for non-existent instance: {instance_id}")
            return request.render('odoo_ha_addon.portal_error_404', status=404)

        # Get shares for this instance
        entity_shares = request.env['ha.entity.share'].sudo().search([
            ('user_id', '=', user.id),
            ('entity_id', '!=', False),
            ('entity_id.ha_instance_id', '=', instance_id),
            ('is_expired', '=', False),
        ])
        group_shares = request.env['ha.entity.share'].sudo().search([
            ('user_id', '=', user.id),
            ('group_id', '!=', False),
            ('group_id.ha_instance_id', '=', instance_id),
            ('is_expired', '=', False),
        ])
        device_shares = request.env['ha.entity.share'].sudo().search([
            ('user_id', '=', user.id),
            ('device_id', '!=', False),
            ('device_id.ha_instance_id', '=', instance_id),
            ('is_expired', '=', False),
        ])

        if not entity_shares and not group_shares and not device_shares:
            _logger.warning(f"Portal /my/ha/{instance_id} access denied: user {user.id} has no shares")
            return request.render('odoo_ha_addon.portal_error_403', status=403)

        # Build searchbar config based on active tab
        url = f'/my/ha/{instance_id}'
        url_args = {'tab': tab}

        if tab == 'entities':
            searchbar_sortings = self._get_entity_searchbar_sortings()
            searchbar_filters = self._get_entity_searchbar_filters(entity_shares)

            if not sortby or sortby not in searchbar_sortings:
                sortby = 'name_asc'
            if not filterby or filterby not in searchbar_filters:
                filterby = 'all'

            order = searchbar_sortings[sortby]['order']
            entity_ids = entity_shares.mapped('entity_id').ids
            base_domain = [('id', 'in', entity_ids)]
            domain = AND([base_domain, searchbar_filters[filterby]['domain']])

            Entity = request.env['ha.entity'].sudo()
            entity_count = Entity.search_count(domain)
            pager = portal_pager(
                url=url,
                url_args={**url_args, 'sortby': sortby, 'filterby': filterby},
                total=entity_count,
                page=page,
                step=step,
            )
            entities = Entity.search(domain, order=order, limit=step, offset=pager['offset'])

            values = {
                'instance': instance,
                'entities': entities,
                'entity_count': entity_count,
                'group_count': len(group_shares),
                'device_count': len(device_shares),
                'pager': pager,
                'searchbar_sortings': searchbar_sortings,
                'sortby': sortby,
                'searchbar_filters': searchbar_filters,
                'filterby': filterby,
                'default_url': url,
                'active_tab': tab,
                'page_name': 'portal_my_ha_instance',
                'sanitize_attrs': _sanitize_portal_attributes,
            }

        elif tab == 'groups':
            searchbar_sortings = self._get_group_searchbar_sortings()
            searchbar_filters = OrderedDict([
                ('all', {'label': _('All'), 'domain': []}),
            ])

            if not sortby or sortby not in searchbar_sortings:
                sortby = 'name_asc'
            filterby = 'all'

            order = searchbar_sortings[sortby]['order']
            group_ids = group_shares.mapped('group_id').ids
            domain = [('id', 'in', group_ids)]

            Group = request.env['ha.entity.group'].sudo()
            group_count = Group.search_count(domain)
            pager = portal_pager(
                url=url,
                url_args={**url_args, 'sortby': sortby},
                total=group_count,
                page=page,
                step=step,
            )
            groups = Group.search(domain, order=order, limit=step, offset=pager['offset'])

            values = {
                'instance': instance,
                'groups': groups,
                'entity_count': len(entity_shares),
                'group_count': group_count,
                'device_count': len(device_shares),
                'pager': pager,
                'searchbar_sortings': searchbar_sortings,
                'sortby': sortby,
                'searchbar_filters': searchbar_filters,
                'filterby': filterby,
                'default_url': url,
                'active_tab': tab,
                'page_name': 'portal_my_ha_instance',
                'sanitize_attrs': _sanitize_portal_attributes,
            }

        elif tab == 'devices':
            searchbar_sortings = self._get_device_searchbar_sortings()
            searchbar_filters = self._get_device_searchbar_filters(device_shares)

            if not sortby or sortby not in searchbar_sortings:
                sortby = 'name_asc'
            if not filterby or filterby not in searchbar_filters:
                filterby = 'all'

            order = searchbar_sortings[sortby]['order']
            device_ids = device_shares.mapped('device_id').ids
            base_domain = [('id', 'in', device_ids)]
            domain = AND([base_domain, searchbar_filters[filterby]['domain']])

            Device = request.env['ha.device'].sudo()
            device_count = Device.search_count(domain)
            pager = portal_pager(
                url=url,
                url_args={**url_args, 'sortby': sortby, 'filterby': filterby},
                total=device_count,
                page=page,
                step=step,
            )
            devices = Device.search(domain, order=order, limit=step, offset=pager['offset'])

            values = {
                'instance': instance,
                'devices': devices,
                'entity_count': len(entity_shares),
                'group_count': len(group_shares),
                'device_count': device_count,
                'pager': pager,
                'searchbar_sortings': searchbar_sortings,
                'sortby': sortby,
                'searchbar_filters': searchbar_filters,
                'filterby': filterby,
                'default_url': url,
                'active_tab': tab,
                'page_name': 'portal_my_ha_instance',
                'sanitize_attrs': _sanitize_portal_attributes,
            }

        else:
            # Invalid tab, default to entities
            return request.redirect(f'/my/ha/{instance_id}?tab=entities')

        _logger.info(
            f"Portal /my/ha/{instance_id} access granted for user {user.login}: "
            f"tab={tab}"
        )

        return request.render('odoo_ha_addon.portal_my_ha_instance', values)

    # ========================================
    # Entity Detail: /my/ha/<instance_id>/entity/<entity_id>
    # ========================================

    @http.route(
        '/my/ha/<int:instance_id>/entity/<int:entity_id>',
        type='http',
        auth='user',
        website=True,
        sitemap=False
    )
    def portal_entity(self, instance_id, entity_id, **kw):
        """Render the portal view for a shared entity."""
        user = request.env.user
        entity = request.env['ha.entity'].sudo().browse(entity_id)

        if not entity.exists():
            _logger.warning(f"Portal access attempt for non-existent entity: {entity_id}")
            return request.render('odoo_ha_addon.portal_error_404', status=404)

        share = self._check_entity_share_access(entity_id, user.id)
        if not share:
            _logger.warning(f"Portal access denied for entity {entity_id}: user {user.id} has no share")
            return request.render('odoo_ha_addon.portal_error_403', status=403)

        _logger.info(f"Portal access granted for entity: {entity.entity_id} (user: {user.login})")

        controllable_domains = []
        if share.permission == 'control':
            controllable_domains = list(PORTAL_CONTROL_SERVICES.keys())

        entity._portal_ensure_token()

        # Prev/Next navigation within this instance's shared entities
        entity_shares = request.env['ha.entity.share'].sudo().search([
            ('user_id', '=', user.id),
            ('entity_id', '!=', False),
            ('entity_id.ha_instance_id', '=', instance_id),
            ('is_expired', '=', False),
        ])
        all_entity_ids = entity_shares.mapped('entity_id').sorted(
            key=lambda e: e.name or ''
        ).ids
        idx = all_entity_ids.index(entity.id) if entity.id in all_entity_ids else -1
        prev_record = (
            f'/my/ha/{instance_id}/entity/{all_entity_ids[idx - 1]}'
            if idx > 0 else None
        )
        next_record = (
            f'/my/ha/{instance_id}/entity/{all_entity_ids[idx + 1]}'
            if 0 <= idx < len(all_entity_ids) - 1 else None
        )

        return request.render('odoo_ha_addon.portal_entity_detail', {
            'entity': entity,
            'instance': entity.ha_instance_id,
            'permission': share.permission,
            'page_name': 'portal_entity',
            'controllable_domains': controllable_domains,
            'token': entity.access_token,
            'sanitize_attrs': _sanitize_portal_attributes,
            'prev_record': prev_record,
            'next_record': next_record,
        })

    @http.route(
        '/my/ha/<int:instance_id>/entity/<int:entity_id>/state',
        type='json',
        auth='user',
    )
    def portal_entity_state(self, instance_id, entity_id, **kw):
        """JSON polling endpoint for entity state updates."""
        user = request.env.user
        share = self._check_entity_share_access(entity_id, user.id)

        if not share:
            _logger.warning(f"Portal state access denied for entity {entity_id}: user {user.id}")
            return {
                'success': False,
                'error': _('Access denied'),
                'error_code': 'access_denied'
            }

        entity = request.env['ha.entity'].sudo().browse(entity_id)
        if not entity.exists():
            return {
                'success': False,
                'error': _('Entity not found'),
                'error_code': 'not_found'
            }

        return {
            'success': True,
            'data': self._get_safe_entity_data(entity),
        }

    # ========================================
    # Unified Portal Control API (call-service style)
    # ========================================

    @http.route(
        '/my/ha/<int:instance_id>/entity/<int:entity_id>/service',
        type='json',
        auth='user',
    )
    def portal_call_service(self, instance_id, entity_id,
                            domain=None, service=None, service_data=None, **kw):
        """
        Unified Portal control endpoint using HA call_service style API.

        This endpoint provides a single entry point for all entity controls,
        similar to Home Assistant's call_service API. Requires 'control'
        permission in the share record.
        """
        user = request.env.user

        if not domain or not service or service_data is None:
            return {
                'success': False,
                'error': _('Missing required parameters (domain, service, service_data)'),
                'error_code': 'missing_params'
            }

        # Use entity_id from URL, ignore service_data.entity_id
        entity = request.env['ha.entity'].sudo().browse(entity_id)
        if not entity.exists():
            _logger.warning(f"Portal call-service for non-existent entity: {entity_id}")
            return {
                'success': False,
                'error': _('Entity not found'),
                'error_code': 'not_found'
            }

        share = self._check_entity_share_access(entity_id, user.id, required_permission='control')
        if not share:
            _logger.warning(f"Portal call-service denied for entity {entity_id}: user {user.id} lacks control permission")
            return {
                'success': False,
                'error': _('Control permission required'),
                'error_code': 'access_denied'
            }

        if domain not in PORTAL_CONTROL_SERVICES:
            _logger.warning(f"Portal call-service denied: domain '{domain}' not allowed")
            return {
                'success': False,
                'error': _('Domain not allowed: %s') % domain,
                'error_code': 'domain_denied'
            }

        if service not in PORTAL_CONTROL_SERVICES[domain]:
            _logger.warning(f"Portal call-service denied: service '{service}' not allowed for domain '{domain}'")
            return {
                'success': False,
                'error': _('Service not allowed for this domain: %s.%s') % (domain, service),
                'error_code': 'service_denied'
            }

        try:
            from odoo.addons.odoo_ha_addon.models.common.websocket_client import get_websocket_client

            ha_instance_id = entity.ha_instance_id.id if entity.ha_instance_id else None
            if not ha_instance_id:
                return {
                    'success': False,
                    'error': _('Entity has no associated HA instance'),
                    'error_code': 'no_instance'
                }

            ha_service_data = {'entity_id': entity.entity_id}
            for key, value in service_data.items():
                if key != 'entity_id':
                    ha_service_data[key] = value

            client = get_websocket_client(request.env, instance_id=ha_instance_id)
            result = client.call_websocket_api(
                message_type='call_service',
                payload={
                    'domain': domain,
                    'service': service,
                    'service_data': ha_service_data
                },
                timeout=10
            )

            if result.get('success'):
                _logger.info(f"Portal call-service success: {domain}.{service} on {entity.entity_id} (user: {user.login})")
                return {
                    'success': True,
                    'state': entity.entity_state,
                    'last_changed': entity.last_changed.isoformat() if entity.last_changed else None,
                    'data': self._get_safe_entity_data(entity)
                }
            else:
                _logger.error(f"Portal call-service failed: {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error', _('Service call failed')),
                    'error_code': 'call_failed'
                }

        except Exception as e:
            _logger.exception(f"Portal call-service error for entity {entity_id}: {e}")
            return {
                'success': False,
                'error': _('An unexpected error occurred. Please try again.'),
                'error_code': 'system_error'
            }

    # ========================================
    # Entity Group Detail: /my/ha/<instance_id>/group/<group_id>
    # ========================================

    @http.route(
        '/my/ha/<int:instance_id>/group/<int:group_id>',
        type='http',
        auth='user',
        website=True,
        sitemap=False
    )
    def portal_entity_group(self, instance_id, group_id, **kw):
        """Render the portal view for a shared entity group."""
        user = request.env.user
        group = request.env['ha.entity.group'].sudo().browse(group_id)

        if not group.exists():
            _logger.warning(f"Portal access attempt for non-existent group: {group_id}")
            return request.render('odoo_ha_addon.portal_error_404', status=404)

        share = self._check_group_share_access(group_id, user.id)
        if not share:
            _logger.warning(f"Portal access denied for group {group_id}: user {user.id} has no share")
            return request.render('odoo_ha_addon.portal_error_403', status=403)

        _logger.info(f"Portal access granted for entity group: {group.name} (user: {user.login})")

        controllable_domains = []
        if share.permission == 'control':
            controllable_domains = list(PORTAL_CONTROL_SERVICES.keys())

        group._portal_ensure_token()

        # Prev/Next navigation within this instance's shared groups
        group_shares = request.env['ha.entity.share'].sudo().search([
            ('user_id', '=', user.id),
            ('group_id', '!=', False),
            ('group_id.ha_instance_id', '=', instance_id),
            ('is_expired', '=', False),
        ])
        all_group_ids = group_shares.mapped('group_id').sorted(
            key=lambda g: g.name or ''
        ).ids
        idx = all_group_ids.index(group.id) if group.id in all_group_ids else -1
        prev_record = (
            f'/my/ha/{instance_id}/group/{all_group_ids[idx - 1]}'
            if idx > 0 else None
        )
        next_record = (
            f'/my/ha/{instance_id}/group/{all_group_ids[idx + 1]}'
            if 0 <= idx < len(all_group_ids) - 1 else None
        )

        return request.render('odoo_ha_addon.portal_group_detail', {
            'group': group,
            'instance': group.ha_instance_id,
            'permission': share.permission,
            'page_name': 'portal_entity_group',
            'controllable_domains': controllable_domains,
            'token': group.access_token,
            'sanitize_attrs': _sanitize_portal_attributes,
            'prev_record': prev_record,
            'next_record': next_record,
        })

    @http.route(
        '/my/ha/<int:instance_id>/group/<int:group_id>/state',
        type='json',
        auth='user',
    )
    def portal_entity_group_state(self, instance_id, group_id, **kw):
        """JSON polling endpoint for entity group state updates."""
        user = request.env.user
        share = self._check_group_share_access(group_id, user.id)

        if not share:
            _logger.warning(f"Portal group state access denied for group {group_id}: user {user.id}")
            return {
                'success': False,
                'error': _('Access denied'),
                'error_code': 'access_denied'
            }

        group = request.env['ha.entity.group'].sudo().browse(group_id)
        if not group.exists():
            return {
                'success': False,
                'error': _('Group not found'),
                'error_code': 'not_found'
            }

        group_data = self._get_safe_group_data(group)

        entities_with_state = []
        if group.entity_ids:
            entities_data = group.entity_ids.read(PORTAL_ENTITY_FIELDS)
            for data in entities_data:
                if data.get('area_id') and isinstance(data['area_id'], tuple):
                    data['area_id'] = {
                        'id': data['area_id'][0],
                        'name': data['area_id'][1]
                    }
                data['attributes'] = _sanitize_portal_attributes(data.get('attributes'))
                entities_with_state.append(data)
        group_data['entities'] = entities_with_state

        return {
            'success': True,
            'data': group_data,
        }

    # ========================================
    # Device Detail: /my/ha/<instance_id>/device/<device_id>
    # ========================================

    @http.route(
        '/my/ha/<int:instance_id>/device/<int:device_id>',
        type='http',
        auth='user',
        website=True,
        sitemap=False
    )
    def portal_device(self, instance_id, device_id, **kw):
        """Render the portal view for a shared device."""
        user = request.env.user
        device = request.env['ha.device'].sudo().browse(device_id)

        if not device.exists():
            _logger.warning(f"Portal access attempt for non-existent device: {device_id}")
            return request.render('odoo_ha_addon.portal_error_404', status=404)

        share = self._check_device_share_access(device_id, user.id)
        if not share:
            _logger.warning(f"Portal access denied for device {device_id}: user {user.id} has no share")
            return request.render('odoo_ha_addon.portal_error_403', status=403)

        _logger.info(f"Portal access granted for device: {device.name} (user: {user.login})")

        controllable_domains = []
        if share.permission == 'control':
            controllable_domains = list(PORTAL_CONTROL_SERVICES.keys())

        entities = device.entity_ids
        device._portal_ensure_token()

        # Prev/Next navigation within this instance's shared devices
        device_shares = request.env['ha.entity.share'].sudo().search([
            ('user_id', '=', user.id),
            ('device_id', '!=', False),
            ('device_id.ha_instance_id', '=', instance_id),
            ('is_expired', '=', False),
        ])
        all_device_ids = device_shares.mapped('device_id').sorted(
            key=lambda d: d.name or ''
        ).ids
        idx = all_device_ids.index(device.id) if device.id in all_device_ids else -1
        prev_record = (
            f'/my/ha/{instance_id}/device/{all_device_ids[idx - 1]}'
            if idx > 0 else None
        )
        next_record = (
            f'/my/ha/{instance_id}/device/{all_device_ids[idx + 1]}'
            if 0 <= idx < len(all_device_ids) - 1 else None
        )

        return request.render('odoo_ha_addon.portal_device_detail', {
            'device': device,
            'instance': device.ha_instance_id,
            'entities': entities,
            'permission': share.permission,
            'page_name': 'portal_device',
            'controllable_domains': controllable_domains,
            'token': device.access_token,
            'sanitize_attrs': _sanitize_portal_attributes,
            'prev_record': prev_record,
            'next_record': next_record,
        })

    @http.route(
        '/my/ha/<int:instance_id>/device/<int:device_id>/state',
        type='json',
        auth='user',
    )
    def portal_device_state(self, instance_id, device_id, **kw):
        """JSON polling endpoint for device state updates."""
        user = request.env.user
        share = self._check_device_share_access(device_id, user.id)

        if not share:
            _logger.warning(f"Portal device state access denied for device {device_id}: user {user.id}")
            return {
                'success': False,
                'error': _('Access denied'),
                'error_code': 'access_denied'
            }

        device = request.env['ha.device'].sudo().browse(device_id)
        if not device.exists():
            return {
                'success': False,
                'error': _('Device not found'),
                'error_code': 'not_found'
            }

        device_data = {
            'id': device.id,
            'name': device.name_by_user or device.name,
            'manufacturer': device.manufacturer,
            'model': device.model,
            'area_id': {
                'id': device.area_id.id,
                'name': device.area_id.name,
            } if device.area_id else None,
        }

        entities_with_state = []
        for entity in device.entity_ids:
            entities_with_state.append(self._get_safe_entity_data(entity))
        device_data['entities'] = entities_with_state

        return {
            'success': True,
            'data': device_data,
        }

    # ========================================
    # Backward Compatibility Redirects (Stage 4)
    # Old routes redirect to new URL structure
    # ========================================

    @http.route(
        '/portal/entity/<int:entity_id>',
        type='http',
        auth='user',
        website=True,
        sitemap=False
    )
    def portal_entity_redirect(self, entity_id, **kw):
        """Redirect old /portal/entity/<id> to new /my/ha/<instance_id>/entity/<id>."""
        user = request.env.user
        share = request.env['ha.entity.share'].sudo().search([
            ('user_id', '=', user.id),
            ('entity_id', '=', entity_id),
            ('is_expired', '=', False),
        ], limit=1)
        if share and share.entity_id.ha_instance_id:
            return request.redirect(
                f'/my/ha/{share.entity_id.ha_instance_id.id}/entity/{entity_id}'
            )
        return request.redirect('/my/ha')

    @http.route(
        '/portal/entity/<int:entity_id>/state',
        type='json',
        auth='user',
    )
    def portal_entity_state_redirect(self, entity_id, **kw):
        """Backward-compatible JSON state endpoint for old URL."""
        user = request.env.user
        share = self._check_entity_share_access(entity_id, user.id)

        if not share:
            return {
                'success': False,
                'error': _('Access denied'),
                'error_code': 'access_denied'
            }

        entity = request.env['ha.entity'].sudo().browse(entity_id)
        if not entity.exists():
            return {
                'success': False,
                'error': _('Entity not found'),
                'error_code': 'not_found'
            }

        return {
            'success': True,
            'data': self._get_safe_entity_data(entity),
        }

    @http.route(
        '/portal/call-service',
        type='json',
        auth='user',
    )
    def portal_call_service_legacy(self, domain=None, service=None, service_data=None, **kw):
        """Backward-compatible call-service endpoint for old URL."""
        user = request.env.user

        if not domain or not service or service_data is None:
            return {
                'success': False,
                'error': _('Missing required parameters (domain, service, service_data)'),
                'error_code': 'missing_params'
            }

        record_id = service_data.get('entity_id')
        if not record_id:
            return {
                'success': False,
                'error': _('entity_id is required in service_data'),
                'error_code': 'missing_entity_id'
            }

        entity = request.env['ha.entity'].sudo().browse(record_id)
        if not entity.exists():
            return {
                'success': False,
                'error': _('Entity not found'),
                'error_code': 'not_found'
            }

        instance_id = entity.ha_instance_id.id if entity.ha_instance_id else 0
        return self.portal_call_service(
            instance_id=instance_id,
            entity_id=record_id,
            domain=domain,
            service=service,
            service_data=service_data,
            **kw
        )

    @http.route(
        '/portal/entity_group/<int:group_id>',
        type='http',
        auth='user',
        website=True,
        sitemap=False
    )
    def portal_entity_group_redirect(self, group_id, **kw):
        """Redirect old /portal/entity_group/<id> to new /my/ha/<instance_id>/group/<id>."""
        user = request.env.user
        share = request.env['ha.entity.share'].sudo().search([
            ('user_id', '=', user.id),
            ('group_id', '=', group_id),
            ('is_expired', '=', False),
        ], limit=1)
        if share and share.group_id.ha_instance_id:
            return request.redirect(
                f'/my/ha/{share.group_id.ha_instance_id.id}/group/{group_id}'
            )
        return request.redirect('/my/ha')

    @http.route(
        '/portal/entity_group/<int:group_id>/state',
        type='json',
        auth='user',
    )
    def portal_entity_group_state_redirect(self, group_id, **kw):
        """Backward-compatible JSON state endpoint for old group URL."""
        user = request.env.user
        share = self._check_group_share_access(group_id, user.id)

        if not share:
            return {
                'success': False,
                'error': _('Access denied'),
                'error_code': 'access_denied'
            }

        group = request.env['ha.entity.group'].sudo().browse(group_id)
        if not group.exists():
            return {
                'success': False,
                'error': _('Group not found'),
                'error_code': 'not_found'
            }

        group_data = self._get_safe_group_data(group)
        entities_with_state = []
        if group.entity_ids:
            entities_data = group.entity_ids.read(PORTAL_ENTITY_FIELDS)
            for data in entities_data:
                if data.get('area_id') and isinstance(data['area_id'], tuple):
                    data['area_id'] = {
                        'id': data['area_id'][0],
                        'name': data['area_id'][1]
                    }
                data['attributes'] = _sanitize_portal_attributes(data.get('attributes'))
                entities_with_state.append(data)
        group_data['entities'] = entities_with_state

        return {
            'success': True,
            'data': group_data,
        }

    @http.route(
        '/portal/device/<int:device_id>',
        type='http',
        auth='user',
        website=True,
        sitemap=False
    )
    def portal_device_redirect(self, device_id, **kw):
        """Redirect old /portal/device/<id> to new /my/ha/<instance_id>/device/<id>."""
        user = request.env.user
        share = request.env['ha.entity.share'].sudo().search([
            ('user_id', '=', user.id),
            ('device_id', '=', device_id),
            ('is_expired', '=', False),
        ], limit=1)
        if share and share.device_id.ha_instance_id:
            return request.redirect(
                f'/my/ha/{share.device_id.ha_instance_id.id}/device/{device_id}'
            )
        return request.redirect('/my/ha')

    @http.route(
        '/portal/device/<int:device_id>/state',
        type='json',
        auth='user',
    )
    def portal_device_state_redirect(self, device_id, **kw):
        """Backward-compatible JSON state endpoint for old device URL."""
        user = request.env.user
        share = self._check_device_share_access(device_id, user.id)

        if not share:
            return {
                'success': False,
                'error': _('Access denied'),
                'error_code': 'access_denied'
            }

        device = request.env['ha.device'].sudo().browse(device_id)
        if not device.exists():
            return {
                'success': False,
                'error': _('Device not found'),
                'error_code': 'not_found'
            }

        device_data = {
            'id': device.id,
            'name': device.name_by_user or device.name,
            'manufacturer': device.manufacturer,
            'model': device.model,
            'area_id': {
                'id': device.area_id.id,
                'name': device.area_id.name,
            } if device.area_id else None,
        }

        entities_with_state = []
        for entity in device.entity_ids:
            entities_with_state.append(self._get_safe_entity_data(entity))
        device_data['entities'] = entities_with_state

        return {
            'success': True,
            'data': device_data,
        }
