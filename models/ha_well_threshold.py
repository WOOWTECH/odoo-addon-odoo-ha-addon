# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class HaWellThreshold(models.Model):
    _name = 'ha.well.threshold'
    _description = 'WELL IEQ Compliance Threshold'
    _order = 'well_feature, name'

    name = fields.Char(string='Parameter Name', required=True)
    well_feature = fields.Selection([
        ('A01', 'A01 - Air Quality'),
        ('A05', 'A05 - Enhanced Air Quality'),
        ('T01', 'T01 - Thermal Performance'),
        ('L01', 'L01 - Light Exposure'),
        ('S01', 'S01 - Sound Mapping'),
    ], string='WELL Feature', required=True)
    parameter_type = fields.Selection([
        ('co2', 'CO\u2082 (ppm)'),
        ('pm25', 'PM2.5 (\u03bcg/m\u00b3)'),
        ('voc', 'VOC (\u03bcg/m\u00b3)'),
        ('temperature', 'Temperature (\u00b0C)'),
        ('humidity', 'Humidity (%)'),
        ('illuminance', 'Illuminance (lux)'),
        ('noise', 'Noise (dB)'),
    ], string='Parameter Type', required=True)
    min_value = fields.Float(string='Minimum Value')
    max_value = fields.Float(string='Maximum Value')
    unit = fields.Char(string='Unit')
    entity_id = fields.Many2one('ha.entity', string='Linked HA Entity')
    instance_id = fields.Many2one('ha.instance', string='HA Instance')
    active = fields.Boolean(default=True)
    compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('warning', 'Warning'),
        ('non_compliant', 'Non-Compliant'),
        ('no_data', 'No Data'),
    ], string='Status', compute='_compute_compliance', store=False)
    last_value = fields.Float(
        string='Last Reading', compute='_compute_compliance', store=False)

    @api.depends('entity_id')
    def _compute_compliance(self):
        for rec in self:
            if not rec.entity_id or not rec.entity_id.entity_state:
                rec.compliance_status = 'no_data'
                rec.last_value = 0.0
                continue
            try:
                val = float(rec.entity_id.entity_state)
                rec.last_value = val
                if rec.min_value and val < rec.min_value:
                    rec.compliance_status = 'non_compliant'
                elif rec.max_value and val > rec.max_value:
                    rec.compliance_status = 'non_compliant'
                else:
                    rec.compliance_status = 'compliant'
            except (ValueError, TypeError):
                rec.compliance_status = 'no_data'
                rec.last_value = 0.0
