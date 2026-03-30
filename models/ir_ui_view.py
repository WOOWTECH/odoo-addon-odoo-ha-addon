# -*- coding: utf-8 -*-
from odoo import fields, models


class View(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[('hahistory', "HA History")])
    def _get_view_info(self):
            return {'hahistory': {'icon': 'fa fa-line-chart'}} | super()._get_view_info()