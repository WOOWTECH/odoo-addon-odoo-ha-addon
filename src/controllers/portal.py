# -*- coding: utf-8 -*-
"""
Portal Controller for Entity and Entity Group user-based access.

This controller provides user-authenticated endpoints for viewing shared entities
and entity groups via ha.entity.share records, replacing the old token-based
authentication system.

Security:
- Routes use auth='user' requiring Odoo login
- Access checked via ha.entity.share records
- Field whitelists prevent exposure of sensitive data
- sudo() is used only for reading, never for writing
- Expired shares are treated as no access (403)
"""
from odoo import http, _
from odoo.http import request
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
    'switch': ['toggle', 'turn_on', 'turn_off'],
    'light': ['toggle', 'turn_on', 'turn_off', 'set_brightness', 'set_color_temp'],
    'fan': ['toggle', 'turn_on', 'turn_off', 'set_percentage', 'set_preset_mode', 'set_direction', 'oscillate'],
    'climate': ['set_temperature', 'set_hvac_mode', 'set_fan_mode'],
    'cover': ['open_cover', 'close_cover', 'stop_cover', 'set_cover_position'],
    'scene': ['turn_on'],
    'script': ['toggle', 'turn_on', 'turn_off'],
    'automation': ['toggle', 'trigger', 'turn_on', 'turn_off'],
    'sensor': [],  # Read-only, no control actions
}


class HAPortalController(http.Controller):
    """
    Controller for portal access to entities and entity groups.

    All routes use auth='user' requiring Odoo login.
    Access is controlled via ha.entity.share records.
    """

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

    def _get_safe_entity_data(self, entity):
        """
        Extract whitelisted fields from an entity record.

        Args:
            entity: ha.entity record

        Returns:
            dict: Dictionary containing only whitelisted fields
        """
        data = entity.read(PORTAL_ENTITY_FIELDS)[0]
        # Convert area_id from (id, name) tuple to dict for JSON serialization
        if data.get('area_id') and isinstance(data['area_id'], tuple):
            data['area_id'] = {
                'id': data['area_id'][0],
                'name': data['area_id'][1],
            }
        # Handle last_changed datetime serialization
        if data.get('last_changed'):
            data['last_changed'] = data['last_changed'].isoformat()
        return data

    def _get_safe_group_data(self, group):
        """
        Extract whitelisted fields from an entity group record.

        Args:
            group: ha.entity.group record

        Returns:
            dict: Dictionary containing only whitelisted fields
        """
        data = group.read(PORTAL_GROUP_FIELDS)[0]
        # Convert entity_ids from list of IDs to list of basic info
        if data.get('entity_ids'):
            entities = request.env['ha.entity'].sudo().browse(data['entity_ids'])
            data['entities'] = [{
                'id': e.id,
                'name': e.name,
                'entity_id': e.entity_id,
                'entity_state': e.entity_state,
                'domain': e.domain,
            } for e in entities]
            del data['entity_ids']  # Remove raw IDs, use entities list instead
        return data

    # ========================================
    # Entity Portal Routes
    # ========================================

    @http.route(
        '/portal/entity/<int:entity_id>',
        type='http',
        auth='user',
        website=True,
        sitemap=False
    )
    def portal_entity(self, entity_id, **kw):
        """
        Render the portal view for a shared entity.

        This route displays a page showing entity information
        for users with a valid share record.

        Args:
            entity_id: The Odoo record ID of the entity

        Returns:
            Rendered template or 403/404 error page
        """
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

        # Only show controllable domains if user has control permission
        controllable_domains = []
        if share.permission == 'control':
            controllable_domains = list(PORTAL_CONTROL_SERVICES.keys())

        return request.render('odoo_ha_addon.portal_entity', {
            'entity': entity,
            'instance': entity.ha_instance_id,
            'permission': share.permission,
            'page_name': 'portal_entity',
            'controllable_domains': controllable_domains,
        })

    @http.route(
        '/portal/entity/<int:entity_id>/state',
        type='json',
        auth='user',
        cors='*'
    )
    def portal_entity_state(self, entity_id, **kw):
        """
        JSON polling endpoint for entity state updates.

        This endpoint returns the current entity state and can be
        polled by the frontend to show real-time updates.

        Args:
            entity_id: The Odoo record ID of the entity

        Returns:
            dict: Entity state data or error message
        """
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
        '/portal/call-service',
        type='json',
        auth='user',
        cors='*',
        csrf=False
    )
    def portal_call_service(self, domain=None, service=None, service_data=None, **kw):
        """
        Unified Portal control endpoint using HA call_service style API.

        This endpoint provides a single entry point for all entity controls,
        similar to Home Assistant's call_service API. Requires 'control'
        permission in the share record.

        Args:
            domain: Entity domain (e.g., 'light', 'switch', 'climate')
            service: Service to call (e.g., 'turn_on', 'set_temperature')
            service_data: Service parameters including entity_id

        Returns:
            dict: Success status with updated entity state or error message
        """
        user = request.env.user

        # 1. Validate required parameters
        # Note: service_data can be an empty dict {}, so we check if it's None explicitly
        if not domain or not service or service_data is None:
            return {
                'success': False,
                'error': _('Missing required parameters (domain, service, service_data)'),
                'error_code': 'missing_params'
            }

        # entity_id here is Odoo record ID (integer), not HA entity_id string
        record_id = service_data.get('entity_id')
        if not record_id:
            return {
                'success': False,
                'error': _('entity_id is required in service_data'),
                'error_code': 'missing_entity_id'
            }

        # 2. Check entity exists
        entity = request.env['ha.entity'].sudo().browse(record_id)
        if not entity.exists():
            _logger.warning(f"Portal call-service for non-existent entity: {record_id}")
            return {
                'success': False,
                'error': _('Entity not found'),
                'error_code': 'not_found'
            }

        # 3. Check user has 'control' permission via share record (direct or via group)
        share = self._check_entity_share_access(record_id, user.id, required_permission='control')
        if not share:
            _logger.warning(f"Portal call-service denied for entity {record_id}: user {user.id} lacks control permission")
            return {
                'success': False,
                'error': _('Control permission required'),
                'error_code': 'access_denied'
            }

        # 4. Validate domain and service against whitelist
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

        # 5. Call WebSocket API
        try:
            from odoo.addons.odoo_ha_addon.models.common.websocket_client import get_websocket_client

            instance_id = entity.ha_instance_id.id if entity.ha_instance_id else None
            if not instance_id:
                return {
                    'success': False,
                    'error': _('Entity has no associated HA instance'),
                    'error_code': 'no_instance'
                }

            # Build service data for HA - use entity_id string, not Odoo ID
            ha_service_data = {'entity_id': entity.entity_id}
            # Add additional service parameters (brightness, temperature, etc.)
            for key, value in service_data.items():
                if key != 'entity_id':  # Don't override entity_id
                    ha_service_data[key] = value

            client = get_websocket_client(request.env, instance_id=instance_id)
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
            _logger.exception(f"Portal call-service error for entity {record_id}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'system_error'
            }

    # ========================================
    # Entity Group Portal Routes
    # ========================================

    @http.route(
        '/portal/entity_group/<int:group_id>',
        type='http',
        auth='user',
        website=True,
        sitemap=False
    )
    def portal_entity_group(self, group_id, **kw):
        """
        Render the portal view for a shared entity group.

        This route displays a page showing the entity group
        and its member entities for users with a valid share record.

        Args:
            group_id: The Odoo record ID of the entity group

        Returns:
            Rendered template or 403/404 error page
        """
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

        # Only show controllable domains if user has control permission
        controllable_domains = []
        if share.permission == 'control':
            controllable_domains = list(PORTAL_CONTROL_SERVICES.keys())

        return request.render('odoo_ha_addon.portal_entity_group', {
            'group': group,
            'instance': group.ha_instance_id,
            'permission': share.permission,
            'page_name': 'portal_entity_group',
            'controllable_domains': controllable_domains,
        })

    @http.route(
        '/portal/entity_group/<int:group_id>/state',
        type='json',
        auth='user',
        cors='*'
    )
    def portal_entity_group_state(self, group_id, **kw):
        """
        JSON polling endpoint for entity group state updates.

        This endpoint returns the current state of all entities
        in the group and can be polled by the frontend.

        Args:
            group_id: The Odoo record ID of the entity group

        Returns:
            dict: Group data with entity states or error message
        """
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

        # Get group data with all entity states
        group_data = self._get_safe_group_data(group)

        # Also get detailed state for each entity
        entities_with_state = []
        for entity in group.entity_ids:
            entities_with_state.append(self._get_safe_entity_data(entity))
        group_data['entities'] = entities_with_state

        return {
            'success': True,
            'data': group_data,
        }

    # ========================================
    # Portal /my Integration Routes
    # ========================================

    def _get_user_shares(self, user_id):
        """
        Get all valid (non-expired) shares for a user.

        Args:
            user_id: res.users record ID

        Returns:
            ha.entity.share recordset
        """
        return request.env['ha.entity.share'].sudo().search([
            ('user_id', '=', user_id),
            ('is_expired', '=', False),
        ])

    def _get_user_share_count(self, user_id):
        """
        Get the count of valid shares for a user.

        Args:
            user_id: res.users record ID

        Returns:
            int: Number of valid shares
        """
        return request.env['ha.entity.share'].sudo().search_count([
            ('user_id', '=', user_id),
            ('is_expired', '=', False),
        ])

    def _get_user_instances_with_shares(self, user_id):
        """
        Get all HA instances that have shares for the user.

        Args:
            user_id: res.users record ID

        Returns:
            dict: {instance: {'entity_shares': [...], 'group_shares': [...], 'total_count': int}}
        """
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
                    'total_count': 0,
                }

            if share.entity_id:
                instance_data[instance.id]['entity_shares'].append(share)
            elif share.group_id:
                instance_data[instance.id]['group_shares'].append(share)
            instance_data[instance.id]['total_count'] += 1

        return instance_data

    @http.route(
        '/my/ha',
        type='http',
        auth='user',
        website=True,
        sitemap=False
    )
    def portal_my_ha(self, **kw):
        """
        Portal page showing all HA instances with shares for the current user.

        Returns:
            Rendered template with list of HA instances
        """
        user = request.env.user
        instance_data = self._get_user_instances_with_shares(user.id)

        # Convert to list for template iteration
        instances_with_counts = []
        for data in instance_data.values():
            instances_with_counts.append({
                'instance': data['instance'],
                'entity_count': len(data['entity_shares']),
                'group_count': len(data['group_shares']),
                'total_count': data['total_count'],
            })

        # Sort by instance name
        instances_with_counts.sort(key=lambda x: x['instance'].name)

        return request.render('odoo_ha_addon.portal_my_ha', {
            'instances': instances_with_counts,
            'page_name': 'portal_my_ha',
        })

    @http.route(
        '/my/ha/<int:instance_id>',
        type='http',
        auth='user',
        website=True,
        sitemap=False
    )
    def portal_my_ha_instance(self, instance_id, tab='entities', **kw):
        """
        Portal page showing entities and groups shared from a specific HA instance.

        Args:
            instance_id: ha.instance record ID
            tab: Active tab ('entities' or 'groups')

        Returns:
            Rendered template with Entity/Group tabs or 403 if no access
        """
        user = request.env.user

        # Check if instance exists
        instance = request.env['ha.instance'].sudo().browse(instance_id)
        if not instance.exists():
            _logger.warning(f"Portal /my/ha access for non-existent instance: {instance_id}")
            return request.render('odoo_ha_addon.portal_error_404', status=404)

        # Get entity shares for this instance
        entity_shares = request.env['ha.entity.share'].sudo().search([
            ('user_id', '=', user.id),
            ('entity_id', '!=', False),
            ('entity_id.ha_instance_id', '=', instance_id),
            ('is_expired', '=', False),
        ])

        # Get group shares for this instance
        group_shares = request.env['ha.entity.share'].sudo().search([
            ('user_id', '=', user.id),
            ('group_id', '!=', False),
            ('group_id.ha_instance_id', '=', instance_id),
            ('is_expired', '=', False),
        ])

        # If user has no shares for this instance, return 403
        if not entity_shares and not group_shares:
            _logger.warning(f"Portal /my/ha/{instance_id} access denied: user {user.id} has no shares")
            return request.render('odoo_ha_addon.portal_error_403', status=403)

        _logger.info(
            f"Portal /my/ha/{instance_id} access granted for user {user.login}: "
            f"{len(entity_shares)} entities, {len(group_shares)} groups"
        )

        return request.render('odoo_ha_addon.portal_my_ha_instance', {
            'instance': instance,
            'entity_shares': entity_shares,
            'group_shares': group_shares,
            'active_tab': tab,
            'page_name': 'portal_my_ha_instance',
        })
