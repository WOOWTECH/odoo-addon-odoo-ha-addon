# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging


class HADeviceTag(models.Model):
    _logger = logging.getLogger(__name__)
    _name = 'ha.device.tag'
    _inherit = ['ha.current.instance.filter.mixin']
    _description = 'Home Assistant Device Tag'
    _order = 'sequence, name'

    ha_instance_id = fields.Many2one(
        'ha.instance',
        string='HA Instance',
        required=True,
        index=True,
        ondelete='cascade',
        help='The Home Assistant instance this tag belongs to'
    )
    name = fields.Char(string='Tag Name', required=True, index=True)
    color = fields.Integer(string='Color', default=0)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    # Many2many relationship with ha.device
    device_ids = fields.Many2many(
        'ha.device',
        'ha_device_tag_rel',  # Relation table name
        'tag_id',             # This model's ID field
        'device_id',          # ha.device's ID field
        string='Devices',
        help='Devices with this tag'
    )

    # Computed field: device count
    device_count = fields.Integer(
        string='Device Count',
        compute='_compute_device_count',
        store=True
    )

    @api.depends('device_ids')
    def _compute_device_count(self):
        """Calculate the number of devices associated with this tag"""
        for tag in self:
            tag.device_count = len(tag.device_ids)

    @api.constrains('name', 'ha_instance_id')
    def _check_name_unique(self):
        """Ensure tag name is unique within the same HA instance"""
        for tag in self:
            if self.search_count([
                ('name', '=', tag.name),
                ('ha_instance_id', '=', tag.ha_instance_id.id),
                ('id', '!=', tag.id)
            ]) > 0:
                raise ValidationError(
                    _('Tag name "%s" already exists in this instance, please use a different name') % tag.name
                )

    @api.constrains('ha_instance_id', 'device_ids')
    def _check_instance_consistency(self):
        """
        Ensure all devices associated with this tag belong to the same HA instance
        This is a critical data integrity constraint
        """
        for tag in self:
            if tag.device_ids:
                mismatched_devices = tag.device_ids.filtered(
                    lambda d: d.ha_instance_id.id != tag.ha_instance_id.id
                )
                if mismatched_devices:
                    device_names = ', '.join(mismatched_devices.mapped('name')[:3])
                    if len(mismatched_devices) > 3:
                        device_names += _(' (and %d more)') % (len(mismatched_devices) - 3)
                    raise ValidationError(
                        _('Tag "%s" belongs to instance "%s",\n'
                          'but the following devices belong to different instances: %s\n'
                          'A tag can only be associated with devices from the same instance.') % (
                              tag.name,
                              tag.ha_instance_id.name,
                              device_names
                          )
                    )

    def action_view_devices(self):
        """Open the list of devices associated with this tag"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'odoo_ha_addon.ha_device_tag_view_devices_action'
        )
        action['name'] = f'{self.name} - Devices'
        action['domain'] = [('id', 'in', self.device_ids.ids)]
        action['context'] = {'default_tag_ids': [(4, self.id)]}
        return action
