# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HACurrentInstanceFilterMixin(models.AbstractModel):
    """
    Mixin for filtering records by the current user's selected HA instance.

    This mixin provides:
    - `is_current_user_instance` computed field for Search View filtering
    - `_compute_is_current_user_instance()` compute method
    - `_search_is_current_user_instance()` search method

    Requirements:
    - The model using this mixin MUST have a `ha_instance_id` field
      (either direct Many2one or related field)

    Usage:
        class MyModel(models.Model, HACurrentInstanceFilterMixin):
            _name = 'my.model'
            _inherit = ['ha.current.instance.filter.mixin']

            ha_instance_id = fields.Many2one('ha.instance', ...)
    """
    _name = 'ha.current.instance.filter.mixin'
    _description = 'HA Current Instance Filter Mixin'

    is_current_user_instance = fields.Boolean(
        string='Is Current User Instance',
        compute='_compute_is_current_user_instance',
        search='_search_is_current_user_instance',
        help="Whether this record belongs to the current user's selected HA instance"
    )

    def _compute_is_current_user_instance(self):
        """
        Compute whether the record belongs to the current user's selected HA instance.
        Used for Search View "Current Instance" filter.
        """
        current_instance_id = (
            self.env.user.current_ha_instance_id.id
            if self.env.user.current_ha_instance_id
            else False
        )
        for record in self:
            if current_instance_id:
                record.is_current_user_instance = (
                    record.ha_instance_id.id == current_instance_id
                )
            else:
                record.is_current_user_instance = False

    def _search_is_current_user_instance(self, operator, value):
        """
        Implement search for is_current_user_instance field.
        Used for Search View filter.
        """
        current_instance_id = (
            self.env.user.current_ha_instance_id.id
            if self.env.user.current_ha_instance_id
            else False
        )

        if operator == '=' and value:
            # Find records belonging to current user's instance
            if current_instance_id:
                return [('ha_instance_id', '=', current_instance_id)]
            else:
                return [('id', '=', False)]  # No results if no instance selected
        elif operator == '=' and not value:
            # Find records NOT belonging to current user's instance
            if current_instance_id:
                return [('ha_instance_id', '!=', current_instance_id)]
            else:
                return []  # All records if no instance selected
        else:
            return []
