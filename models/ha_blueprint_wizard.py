# -*- coding: utf-8 -*-
"""
Blueprint Wizard for creating Automation/Script from Blueprint templates.

This wizard provides a two-step process:
1. Select HA Instance and Blueprint template
2. Configure Blueprint inputs via dynamic form
"""

import json
import time
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class HABlueprintWizard(models.TransientModel):
    _name = 'ha.blueprint.wizard'
    _description = 'Create Automation/Script from Blueprint'

    # ===== Step 1: Select Blueprint =====

    domain = fields.Selection([
        ('automation', 'Automation'),
        ('script', 'Script'),
    ], string='Type', required=True, default='automation')

    ha_instance_id = fields.Many2one(
        'ha.instance',
        string='HA Instance',
        required=True,
        default=lambda self: self._default_ha_instance(),
    )

    blueprint_path = fields.Char(
        string='Blueprint Path',
        help='Path to the selected blueprint template',
    )

    blueprint_list_json = fields.Text(
        string='Blueprint List (JSON)',
        help='Cached blueprint list from HA',
    )

    # ===== Step 2: Configure Inputs =====

    name = fields.Char(
        string='Name',
        help='Name for the new Automation/Script',
    )

    description = fields.Text(
        string='Description',
        help='Optional description',
    )

    blueprint_inputs_json = fields.Text(
        string='Blueprint Inputs (JSON)',
        help='User-configured input values',
        default='{}',
    )

    blueprint_schema_json = fields.Text(
        string='Blueprint Schema (JSON)',
        help='Blueprint input schema for dynamic form rendering',
    )

    blueprint_name = fields.Char(
        string='Blueprint Name',
        help='Display name of selected blueprint',
    )

    # ===== Wizard State =====

    state = fields.Selection([
        ('select', 'Select Blueprint'),
        ('configure', 'Configure Inputs'),
    ], string='State', default='select')

    # ===== Default Methods =====

    def _default_ha_instance(self):
        """Get default HA instance from session or first accessible."""
        HAInstance = self.env['ha.instance']
        # Try session instance first
        session_instance_id = self.env.context.get('ha_instance_id')
        if session_instance_id:
            instance = HAInstance.browse(session_instance_id)
            if instance.exists():
                return instance.id
        # Otherwise first accessible
        instances = HAInstance.search([], limit=1)
        return instances[0].id if instances else False

    # ===== Onchange Methods =====

    @api.onchange('ha_instance_id')
    def _onchange_ha_instance_id(self):
        """Load blueprint list when HA instance changes."""
        if self.ha_instance_id:
            self._load_blueprint_list()

    @api.onchange('domain')
    def _onchange_domain(self):
        """Reload blueprint list when domain changes."""
        if self.ha_instance_id and self.domain:
            self._load_blueprint_list()

    # ===== Action Methods =====

    def _load_blueprint_list(self):
        """Load blueprint list from HA."""
        if not self.ha_instance_id or not self.domain:
            self.blueprint_list_json = '{}'
            return

        try:
            rest_api = self.ha_instance_id._get_rest_api()
            blueprint_list = rest_api.get_blueprint_list(self.domain)

            if blueprint_list:
                self.blueprint_list_json = json.dumps(blueprint_list, ensure_ascii=False, indent=2)
                _logger.info(f"Loaded {len(blueprint_list)} blueprints for {self.domain}")
            else:
                self.blueprint_list_json = '{}'
                _logger.warning(f"No blueprints found for {self.domain}")

        except Exception as e:
            _logger.error(f"Failed to load blueprint list: {e}")
            self.blueprint_list_json = '{}'
            raise UserError(_("Failed to load blueprints from Home Assistant: %s") % str(e))

    def action_refresh_blueprints(self):
        """Refresh blueprint list from HA."""
        self.ensure_one()
        self._load_blueprint_list()
        return self._return_wizard()

    def action_select_blueprint(self):
        """
        Select a blueprint and move to configure step.
        Load the blueprint schema for dynamic form rendering.
        """
        self.ensure_one()

        if not self.blueprint_path:
            raise ValidationError(_("Please select a Blueprint template."))

        # Get blueprint metadata/schema
        try:
            rest_api = self.ha_instance_id._get_rest_api()

            # Get blueprint list to extract metadata
            blueprint_list = json.loads(self.blueprint_list_json or '{}')

            if self.blueprint_path not in blueprint_list:
                raise ValidationError(_("Selected blueprint not found. Please refresh the list."))

            blueprint_info = blueprint_list[self.blueprint_path]
            metadata = blueprint_info.get('metadata', {})

            # Store schema and name
            self.blueprint_schema_json = json.dumps(metadata, ensure_ascii=False, indent=2)
            self.blueprint_name = metadata.get('name', self.blueprint_path)

            # Initialize inputs with defaults
            inputs = metadata.get('input', {})
            default_inputs = {}
            for input_key, input_def in inputs.items():
                if 'default' in input_def:
                    default_inputs[input_key] = input_def['default']

            self.blueprint_inputs_json = json.dumps(default_inputs, ensure_ascii=False, indent=2)

            # Move to configure state
            self.state = 'configure'

            _logger.info(f"Selected blueprint: {self.blueprint_path}")

        except ValidationError:
            raise
        except Exception as e:
            _logger.error(f"Failed to load blueprint schema: {e}")
            raise UserError(_("Failed to load blueprint details: %s") % str(e))

        return self._return_wizard()

    def action_back(self):
        """Go back to select step."""
        self.ensure_one()
        self.state = 'select'
        return self._return_wizard()

    def action_create(self):
        """
        Create the Automation/Script in Home Assistant.
        """
        self.ensure_one()

        if not self.name:
            raise ValidationError(_("Please enter a name."))

        if not self.blueprint_path:
            raise ValidationError(_("No blueprint selected."))

        try:
            # Parse inputs
            inputs = json.loads(self.blueprint_inputs_json or '{}')

            # Generate config ID (timestamp format like HA uses)
            config_id = str(int(time.time() * 1000))

            # Build config structure
            config = {
                'id': config_id,
                'alias': self.name,
                'use_blueprint': {
                    'path': self.blueprint_path,
                    'input': inputs,
                }
            }

            if self.description:
                config['description'] = self.description

            _logger.info(f"Creating {self.domain} from blueprint: {self.blueprint_path}")
            _logger.debug(f"Config: {config}")

            # Get REST API
            rest_api = self.ha_instance_id._get_rest_api()

            # Create in HA
            if self.domain == 'automation':
                rest_api.update_automation_config(config_id, config)
                # Reload automations
                self._call_ha_service('automation', 'reload', {})
            else:
                rest_api.update_script_config(config_id, config)
                # Reload scripts
                self._call_ha_service('script', 'reload', {})

            _logger.info(f"Successfully created {self.domain} '{self.name}' with ID {config_id}")

            # Sync entities to get the new entity in Odoo
            # Give HA a moment to process
            import time as time_module
            time_module.sleep(1)

            # Trigger entity sync
            self.ha_instance_id.action_sync_entities()

            # Try to find and open the new entity
            entity_id = f"{self.domain}.{self._generate_entity_id(self.name)}"
            new_entity = self.env['ha.entity'].search([
                ('ha_instance_id', '=', self.ha_instance_id.id),
                ('entity_id', '=', entity_id),
            ], limit=1)

            if not new_entity:
                # Try with config_id based entity_id
                new_entity = self.env['ha.entity'].search([
                    ('ha_instance_id', '=', self.ha_instance_id.id),
                    ('ha_automation_id', '=', config_id),
                ], limit=1)

            # Show success notification and optionally open entity
            if new_entity:
                # Set blueprint fields on the newly created entity
                self._set_blueprint_fields_on_entity(new_entity, inputs)

                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'ha.entity',
                    'res_id': new_entity.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _("Created %s '%s'. Please sync entities to see it in the list.") % (
                            self.domain.capitalize(), self.name
                        ),
                        'type': 'success',
                        'sticky': False,
                    }
                }

        except json.JSONDecodeError as e:
            raise ValidationError(_("Invalid JSON in Blueprint Inputs: %s") % str(e))
        except Exception as e:
            _logger.error(f"Failed to create {self.domain}: {e}", exc_info=True)
            raise UserError(_("Failed to create %s in Home Assistant: %s") % (self.domain, str(e)))

    def _call_ha_service(self, domain, service, service_data=None):
        """Call a Home Assistant service via WebSocket."""
        try:
            from odoo.addons.odoo_ha_addon.models.common.websocket_client import get_websocket_client
            client = get_websocket_client(self.env, instance_id=self.ha_instance_id.id)

            payload = {
                'domain': domain,
                'service': service,
                'service_data': service_data or {}
            }

            _logger.info(f"Calling HA service: {domain}.{service}")
            client.call_websocket_api_sync('call_service', payload)
            _logger.info(f"Service {domain}.{service} called successfully")

        except Exception as e:
            _logger.warning(f"Failed to call HA service {domain}.{service}: {e}")
            # Don't raise - reload failure shouldn't block creation

    def _set_blueprint_fields_on_entity(self, entity, inputs):
        """
        Set blueprint-related fields on the newly created entity.

        Args:
            entity: The ha.entity record
            inputs: The blueprint input values dict
        """
        try:
            entity.write({
                'is_blueprint_based': True,
                'blueprint_path': self.blueprint_path,
                'blueprint_inputs': json.dumps(inputs, ensure_ascii=False, indent=2),
                'blueprint_metadata': self.blueprint_schema_json,
            })
            _logger.info(f"Set blueprint fields on entity {entity.entity_id}")
        except Exception as e:
            _logger.warning(f"Failed to set blueprint fields on entity: {e}")
            # Don't raise - the entity was created successfully

    def _generate_entity_id(self, name):
        """Generate entity_id from name (similar to HA's logic)."""
        import re
        # Convert to lowercase, replace spaces with underscores, remove special chars
        entity_id = name.lower()
        entity_id = re.sub(r'[^a-z0-9_]', '_', entity_id)
        entity_id = re.sub(r'_+', '_', entity_id)
        entity_id = entity_id.strip('_')
        return entity_id

    def _return_wizard(self):
        """Return action to keep wizard open."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # ===== Helper Methods for Frontend =====

    def get_blueprint_list_for_selector(self):
        """
        Return blueprint list formatted for the selector widget.

        Returns:
            list: [{
                'path': 'homeassistant/motion_light.yaml',
                'name': 'Motion-activated Light',
                'description': '...',
                'domain': 'automation',
            }, ...]
        """
        self.ensure_one()
        blueprint_list = json.loads(self.blueprint_list_json or '{}')

        result = []
        for path, info in blueprint_list.items():
            metadata = info.get('metadata', {})
            result.append({
                'path': path,
                'name': metadata.get('name', path),
                'description': metadata.get('description', ''),
                'domain': metadata.get('domain', self.domain),
                'source_url': metadata.get('source_url', ''),
            })

        # Sort by name
        result.sort(key=lambda x: x['name'].lower())
        return result

    def get_blueprint_inputs_schema(self):
        """
        Return the blueprint input schema for dynamic form rendering.

        Returns:
            dict: {
                'input_key': {
                    'name': 'Display Name',
                    'description': 'Help text',
                    'default': 'default value',
                    'selector': {'entity': {'domain': 'light'}},
                },
                ...
            }
        """
        self.ensure_one()
        schema = json.loads(self.blueprint_schema_json or '{}')
        return schema.get('input', {})
