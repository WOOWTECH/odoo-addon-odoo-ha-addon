from odoo import models, fields, api, _
from odoo.exceptions import AccessError
import logging
import json

_logger = logging.getLogger(__name__)


class HADevice(models.Model):
    """Home Assistant Device Model with Bidirectional Sync

    Note: Devices are managed by HA integrations and CANNOT be created or deleted from Odoo.
    Only certain fields can be updated: area_id, name_by_user, disabled_by, labels
    """
    _name = 'ha.device'
    _description = 'Home Assistant Device'

    # SQL Constraints
    _sql_constraints = [
        ('device_instance_unique',
         'unique(device_id, ha_instance_id)',
         'Device ID must be unique per HA instance')
    ]

    ha_instance_id = fields.Many2one(
        'ha.instance',
        string='HA Instance',
        required=True,
        index=True,
        ondelete='cascade',
        help='The Home Assistant instance this device belongs to'
    )
    device_id = fields.Char(
        string='Device ID',
        required=True,
        index=True,
        readonly=True,
        help='Home Assistant device ID'
    )

    # Device identification fields
    name = fields.Char(
        string='Name',
        readonly=True,
        help='Device name (read-only, managed by HA integration)'
    )
    name_by_user = fields.Char(
        string='Custom Name',
        help='User-defined device name (can be updated)'
    )
    manufacturer = fields.Char(
        string='Manufacturer',
        readonly=True
    )
    model = fields.Char(
        string='Model',
        readonly=True
    )
    model_id = fields.Char(
        string='Model ID',
        readonly=True
    )

    # Hardware/Software information (read-only)
    hw_version = fields.Char(
        string='Hardware Version',
        readonly=True
    )
    sw_version = fields.Char(
        string='Software Version',
        readonly=True
    )
    serial_number = fields.Char(
        string='Serial Number',
        readonly=True
    )

    # Configuration
    configuration_url = fields.Char(
        string='Configuration URL',
        readonly=True
    )
    config_entries = fields.Json(
        string='Config Entries',
        readonly=True,
        help='List of config entry IDs'
    )

    # Connections and identifiers (read-only)
    connections = fields.Json(
        string='Connections',
        readonly=True,
        help='Device connections (e.g., MAC addresses)'
    )
    identifiers = fields.Json(
        string='Identifiers',
        readonly=True,
        help='Device identifiers used by integrations'
    )

    # Device status and categorization
    entry_type = fields.Char(
        string='Entry Type',
        readonly=True,
        help='Device entry type (e.g., "service")'
    )
    disabled_by = fields.Char(
        string='Disabled By',
        help='Who/what disabled this device (user, integration, etc.)'
    )
    label_ids = fields.Many2many(
        'ha.label',
        'ha_device_label_rel',
        'device_id',
        'label_id',
        string='Labels',
        domain="[('ha_instance_id', '=', ha_instance_id)]",
        help='Device labels for categorization (synced with HA)'
    )

    # Timestamps (read-only)
    created_at = fields.Float(
        string='Created At',
        readonly=True,
        help='Unix timestamp when device was created in HA'
    )
    modified_at = fields.Float(
        string='Modified At',
        readonly=True,
        help='Unix timestamp when device was last modified in HA'
    )

    # Relationships
    area_id = fields.Many2one(
        'ha.area',
        string='Area',
        domain="[('ha_instance_id', '=', ha_instance_id)]",
        help='The area this device belongs to (can be updated)'
    )
    entity_ids = fields.One2many(
        'ha.entity',
        'device_id',
        string='Entities',
        help='Entities belonging to this device'
    )

    # Computed fields for related automation/script/scene entities
    automation_ids = fields.Many2many(
        'ha.entity',
        string='Related Automations',
        compute='_compute_related_automations',
        help='Automation entities from the same HA instance'
    )
    script_ids = fields.Many2many(
        'ha.entity',
        string='Related Scripts',
        compute='_compute_related_scripts',
        help='Script entities from the same HA instance'
    )
    scene_ids = fields.Many2many(
        'ha.entity',
        string='Related Scenes',
        compute='_compute_related_scenes',
        help='Scene entities from the same HA instance'
    )

    # Count fields for display in list view
    entity_count = fields.Integer(
        string='Entity Count',
        compute='_compute_entity_count'
    )
    automation_count = fields.Integer(
        string='Automation Count',
        compute='_compute_related_automations'
    )
    script_count = fields.Integer(
        string='Script Count',
        compute='_compute_related_scripts'
    )
    scene_count = fields.Integer(
        string='Scene Count',
        compute='_compute_related_scenes'
    )

    via_device_id = fields.Char(
        string='Via Device ID',
        readonly=True,
        help='Device ID this device is connected through'
    )
    primary_config_entry = fields.Char(
        string='Primary Config Entry',
        readonly=True
    )

    # 允許用戶修改的欄位（其他欄位只能由系統 sudo() 修改）
    # - area_id: Device 所屬區域（雙向同步到 HA）
    # - name_by_user: 使用者自訂名稱（雙向同步到 HA Device Registry）
    # - label_ids: Device 標籤（雙向同步到 HA Device Registry）
    _USER_EDITABLE_FIELDS = {'area_id', 'name_by_user', 'label_ids'}

    # ========== Computed Fields ==========

    @api.depends('entity_ids')
    def _compute_entity_count(self):
        for device in self:
            device.entity_count = len(device.entity_ids)

    @api.depends('entity_ids')
    def _compute_related_automations(self):
        """Compute automation entities that belong to this device"""
        for device in self:
            # Only show automations that are direct children of this device
            automations = device.entity_ids.filtered(lambda e: e.domain == 'automation')
            device.automation_ids = automations
            device.automation_count = len(automations)

    @api.depends('entity_ids')
    def _compute_related_scripts(self):
        """Compute script entities that belong to this device"""
        for device in self:
            # Only show scripts that are direct children of this device
            scripts = device.entity_ids.filtered(lambda e: e.domain == 'script')
            device.script_ids = scripts
            device.script_count = len(scripts)

    @api.depends('entity_ids')
    def _compute_related_scenes(self):
        """Compute scene entities that belong to this device"""
        for device in self:
            # Only show scenes that are direct children of this device
            scenes = device.entity_ids.filtered(lambda e: e.domain == 'scene')
            device.scene_ids = scenes
            device.scene_count = len(scenes)

    # ========== Bidirectional Sync: Odoo → HA ==========

    def write(self, vals):
        """
        覆寫 write 方法，限制一般用戶只能修改特定欄位。
        系統同步（使用 sudo()）不受此限制。

        當 area_id, name_by_user, labels 變更時，同步更新到 Home Assistant。
        使用 context['from_ha_sync'] = True 來防止循環同步。
        """
        # 權限檢查：非 sudo 操作只能修改 _USER_EDITABLE_FIELDS 中的欄位
        if not self.env.su:
            disallowed_fields = set(vals.keys()) - self._USER_EDITABLE_FIELDS
            if disallowed_fields:
                raise AccessError(
                    _('You do not have permission to modify the following fields: %s') %
                    ', '.join(sorted(disallowed_fields))
                )

        result = super().write(vals)

        # Check if any syncable fields were updated (same as _USER_EDITABLE_FIELDS)
        if not self.env.context.get('from_ha_sync') and any(field in vals for field in self._USER_EDITABLE_FIELDS):
            for record in self:
                try:
                    record._update_device_in_ha()
                except Exception as e:
                    _logger.error(f"Failed to sync device update {record.name} to HA: {e}")

        return result

    def _update_device_in_ha(self):
        """
        Update device in HA using WebSocket API

        API: config/device_registry/update
        Only updates fields that can be modified from Odoo
        """
        self.ensure_one()

        if not self.ha_instance_id or not self.device_id:
            _logger.warning(f"Cannot sync device update {self.name}: missing HA instance or device_id")
            return

        try:
            from odoo.addons.odoo_ha_addon.models.common.websocket_client import get_websocket_client
            client = get_websocket_client(self.env, instance_id=self.ha_instance_id.id)

            # Prepare payload with only updatable fields
            payload = {
                'device_id': self.device_id,
            }

            # Add area_id (convert Odoo area to HA area_id)
            if self.area_id:
                payload['area_id'] = self.area_id.area_id
            else:
                payload['area_id'] = None

            # Add other updatable fields
            if self.name_by_user:
                payload['name_by_user'] = self.name_by_user
            else:
                payload['name_by_user'] = None

            if self.disabled_by:
                payload['disabled_by'] = self.disabled_by
            else:
                payload['disabled_by'] = None

            # Convert Odoo label_ids (Many2many) to HA labels (label_id array)
            # HA stores labels as label_id references, not names
            payload['labels'] = self.label_ids.mapped('label_id') if self.label_ids else []

            _logger.info(f"Updating device in HA: {self.name} (device_id={self.device_id})")
            client.call_websocket_api_sync('config/device_registry/update', payload)

            _logger.info(f"Device {self.name} updated in HA successfully")

        except Exception as e:
            _logger.error(f"Failed to update device {self.name} in HA: {e}", exc_info=True)
            raise

    # ========== Bidirectional Sync: HA → Odoo ==========

    @api.model
    def sync_device_from_ha_data(self, device_data, instance_id):
        """
        Unified method: Sync single device from HA data to Odoo

        This is the single entry point for HA → Odoo sync, called by:
        - WebSocket event handlers
        - Initial sync (batch)
        - Manual sync

        Args:
            device_data: HA device registry data dict
            instance_id: HA instance ID

        Returns:
            tuple: (action, device_record) - action is 'created', 'updated', or None
        """
        device_id = device_data.get('id')
        if not device_id:
            return None, None

        # Resolve area_id to Odoo area record
        area_odoo_id = None
        ha_area_id = device_data.get('area_id')
        if ha_area_id:
            area_record = self.env['ha.area'].sudo().search([
                ('area_id', '=', ha_area_id),
                ('ha_instance_id', '=', instance_id)
            ], limit=1)
            if area_record:
                area_odoo_id = area_record.id
            else:
                _logger.warning(f"Area {ha_area_id} not found in Odoo for device {device_id}")

        # Convert HA labels (string array) to Odoo label_ids (Many2many)
        ha_labels = device_data.get('labels', [])
        label_records = self.env['ha.label'].get_or_create_labels(ha_labels, instance_id)

        values = {
            'device_id': device_id,
            'ha_instance_id': instance_id,
            'name': device_data.get('name', ''),
            'name_by_user': device_data.get('name_by_user'),
            'manufacturer': device_data.get('manufacturer'),
            'model': device_data.get('model'),
            'model_id': device_data.get('model_id'),
            'hw_version': device_data.get('hw_version'),
            'sw_version': device_data.get('sw_version'),
            'serial_number': device_data.get('serial_number'),
            'configuration_url': device_data.get('configuration_url'),
            'config_entries': device_data.get('config_entries', []),
            'connections': device_data.get('connections', []),
            'identifiers': device_data.get('identifiers', []),
            'entry_type': device_data.get('entry_type'),
            'disabled_by': device_data.get('disabled_by'),
            'label_ids': [(6, 0, label_records.ids)],  # Replace all labels
            'created_at': device_data.get('created_at', 0),
            'modified_at': device_data.get('modified_at', 0),
            'area_id': area_odoo_id,
            'via_device_id': device_data.get('via_device_id'),
            'primary_config_entry': device_data.get('primary_config_entry'),
        }

        existing_device = self.sudo().search([
            ('device_id', '=', device_id),
            ('ha_instance_id', '=', instance_id)
        ], limit=1)

        # Use from_ha_sync to prevent reverse sync loop
        if existing_device:
            existing_device.with_context(from_ha_sync=True).write(values)
            return 'updated', existing_device
        else:
            new_device = self.sudo().with_context(from_ha_sync=True).create(values)
            return 'created', new_device

    @api.model
    def sync_devices_from_ha(self, instance_id=None):
        """
        Sync all devices from Home Assistant

        Uses WebSocket API: config/device_registry/list

        Args:
            instance_id: HA instance ID, if None uses HAInstanceHelper

        Returns:
            dict: {'created': int, 'updated': int}
        """
        _logger.info(f"=== Starting sync_devices_from_ha (instance_id={instance_id}) ===")

        try:
            if instance_id is None:
                from odoo.addons.odoo_ha_addon.models.common.instance_helper import HAInstanceHelper
                instance_id = HAInstanceHelper.get_current_instance(self.env, logger=_logger)
                if not instance_id:
                    _logger.error("No HA instance available")
                    return {'created': 0, 'updated': 0}

            from odoo.addons.odoo_ha_addon.models.common.websocket_client import get_websocket_client
            client = get_websocket_client(self.env, instance_id=instance_id)

            result = client.call_websocket_api_sync('config/device_registry/list', {})

            if not result or not isinstance(result, list):
                _logger.warning("No devices received from Home Assistant or invalid format")
                return {'created': 0, 'updated': 0}

            _logger.info(f"Received {len(result)} devices from Home Assistant (instance {instance_id})")

            created_count = 0
            updated_count = 0

            for device_data in result:
                try:
                    action, _ = self.sync_device_from_ha_data(device_data, instance_id)
                    if action == 'created':
                        created_count += 1
                    elif action == 'updated':
                        updated_count += 1
                except Exception as e:
                    _logger.error(f"Error processing device {device_data.get('id')}: {e}")

            _logger.info(f"Device sync (instance {instance_id}): {created_count} created, {updated_count} updated")
            _logger.info("=== sync_devices_from_ha completed ===")

            return {'created': created_count, 'updated': updated_count}

        except Exception as e:
            _logger.error(f"Failed to sync devices: {e}", exc_info=True)
            return {'created': 0, 'updated': 0}
