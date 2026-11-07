# -*- coding: utf-8 -*-
"""
18.0.7.1 security migration (idempotent).

- Drop the former global ir.model.access ``access_ha_ws_request_queue``
  (no group_id => every logged-in user, portal included, could create
  arbitrary Home Assistant WebSocket requests).  Odoo already removes
  records whose xmlid disappeared from the data files on -u; this is a
  safety net for databases where that cleanup was skipped.
- Clear the ormcache so the new ir.rule / ACL definitions apply at once.
"""
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    acl = env.ref('odoo_ha_addon.access_ha_ws_request_queue', raise_if_not_found=False)
    if acl:
        _logger.info("Removing global ACL odoo_ha_addon.access_ha_ws_request_queue (id %s)", acl.id)
        acl.unlink()

    leftovers = env['ir.model.access'].search([
        ('model_id.model', '=', 'ha.ws.request.queue'),
        ('group_id', '=', False),
    ])
    if leftovers:
        _logger.warning(
            "Removing %s global ACL row(s) on ha.ws.request.queue: %s",
            len(leftovers), leftovers.mapped('name'),
        )
        leftovers.unlink()
    env.registry.clear_cache()
