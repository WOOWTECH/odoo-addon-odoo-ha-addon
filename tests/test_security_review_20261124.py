# -*- coding: utf-8 -*-
# Part of odoo_ha_addon. See LICENSE file for full copyright and licensing details.
"""Regression tests for the 2026-11-24 security review."""
import json
from unittest.mock import MagicMock, patch

from odoo.exceptions import AccessError
from odoo.tests import HttpCase, TransactionCase, tagged

from odoo.addons.odoo_ha_addon.models.common import hass_rest_api

from .test_security_sweep_20261107 import PASSWORD, _HAFixtureMixin


class _ReviewFixtureMixin(_HAFixtureMixin):

    @classmethod
    def _setup_review_fixture(cls):
        cls._setup_ha_fixture()
        env = cls.env
        cls.device_other = env['ha.device'].sudo().create({
            'ha_instance_id': cls.inst_b.id, 'device_id': 'review_dev_b', 'name': 'Review Device B',
            'serial_number': 'review-serial-b',
        })
        cls.lock_other.sudo().write({'device_id': cls.device_other.id})
        cls.tag_a, cls.tag_b = env['ha.device.tag'].sudo().create([
            {'name': 'Review Tag A', 'ha_instance_id': cls.inst_a.id},
            {'name': 'Review Tag B', 'ha_instance_id': cls.inst_b.id},
        ])
        cls.label_a, cls.label_b = env['ha.label'].sudo().with_context(from_ha_sync=True).create([
            {'name': 'Review Label A', 'label_id': 'review_label_a', 'ha_instance_id': cls.inst_a.id},
            {'name': 'Review Label B', 'label_id': 'review_label_b', 'ha_instance_id': cls.inst_b.id},
        ])
        cls.ha_user_none = cls._make_user(
            'review_ha_user_none', ['base.group_user', 'odoo_ha_addon.group_ha_user'])
        env.registry.clear_cache()


@tagged('post_install', '-at_install', 'ha_review')
class TestReviewRecordRules(_ReviewFixtureMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_review_fixture()

    def _visible(self, model, user):
        return self.env[model].with_user(user).search([])

    def test_devices_follow_visible_entities(self):
        self.assertIn(self.device_d, self._visible('ha.device', self.ha_user))
        self.assertNotIn(self.device_other, self._visible('ha.device', self.ha_user))
        self.assertEqual(self._visible('ha.device', self.ha_user2) & (self.device_d | self.device_other),
                         self.device_other)
        self.assertFalse(self._visible('ha.device', self.ha_user_none))
        with self.assertRaises(AccessError):
            self.device_other.with_user(self.ha_user).read(['serial_number'])

    def test_labels_and_device_tags_follow_instances(self):
        for model, rec_a, rec_b in (('ha.label', self.label_a, self.label_b),
                                    ('ha.device.tag', self.tag_a, self.tag_b)):
            with self.subTest(model=model):
                self.assertEqual(self._visible(model, self.ha_user) & (rec_a | rec_b), rec_a)
                self.assertEqual(self._visible(model, self.ha_user2) & (rec_a | rec_b), rec_b)
                self.assertFalse(self._visible(model, self.ha_user_none) & (rec_a | rec_b))

    def test_device_tags_of_another_instance_cannot_be_changed(self):
        with self.assertRaises(AccessError):
            self.tag_b.with_user(self.ha_user).write({'name': 'changed'})
        with self.assertRaises(AccessError):
            self.tag_b.with_user(self.ha_user).unlink()
        self.tag_a.with_user(self.ha_user).write({'name': 'Review Tag A renamed'})

    def test_manager_sees_everything(self):
        for model, records in (('ha.device', self.device_d | self.device_other),
                               ('ha.label', self.label_a | self.label_b),
                               ('ha.device.tag', self.tag_a | self.tag_b)):
            with self.subTest(model=model):
                self.assertEqual(self._visible(model, self.manager) & records, records)

    def test_revoking_the_group_hides_the_device_at_once(self):
        self.assertIn(self.device_d, self._visible('ha.device', self.ha_user))
        self.group_g.sudo().write({'user_ids': [(3, self.ha_user.id)]})
        self.assertNotIn(self.device_d, self._visible('ha.device', self.ha_user))

    def test_archived_member_keeps_the_group_private(self):
        Realtime = self.env['ha.realtime.update'].sudo()
        full, restricted = Realtime._get_entity_recipient_sets('lock.sweep_b', self.inst_b.id)
        self.assertIn(self.ha_user2, full)
        self.assertNotIn(self.ha_user, full | restricted)
        self.ha_user2.sudo().write({'active': False})
        full, restricted = Realtime._get_entity_recipient_sets('lock.sweep_b', self.inst_b.id)
        self.assertNotIn(self.ha_user, full | restricted)
        self.assertNotIn(self.ha_user_none, full | restricted)

    def test_archived_instance_or_group_stops_realtime_for_shares(self):
        Realtime = self.env['ha.realtime.update'].sudo()
        self.assertIn(self.portal_share, Realtime._get_entity_recipients('light.sweep_a', self.inst_a.id))
        self.inst_a.sudo().write({'active': False})
        self.assertNotIn(self.portal_share, Realtime._get_entity_recipients('light.sweep_a', self.inst_a.id))


@tagged('post_install', '-at_install', 'ha_review')
class TestReviewOnchangeAccess(_ReviewFixtureMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_review_fixture()

    def test_onchange_does_not_leak_to_portal_or_plain_users(self):
        calls = [
            ('res.config.settings', {'ha_instance_id': self.inst_b.id}, ['ha_instance_id'],
             {'ha_instance_id': {}, 'ha_api_url': {}, 'ha_name': {}}),
            ('ha.entity.history', {'entity_id': self.lock_other.id}, ['entity_id'],
             {'entity_id': {}, 'entity_name': {}, 'ha_instance_id': {}}),
            ('ha.entity.share', {'entity_id': self.lock_other.id}, ['entity_id'],
             {'entity_id': {}, 'display_name': {}, 'ha_instance_id': {}}),
        ]
        for user in (self.portal_none, self.internal):
            for model, values, changed, spec in calls:
                with self.subTest(user=user.login, model=model):
                    with self.assertRaises(AccessError):
                        self.env[model].with_user(user).onchange(values, changed, spec)

    def test_onchange_still_works_for_authorised_users(self):
        admin = self.env.ref('base.user_admin')
        result = self.env['res.config.settings'].with_user(admin).onchange(
            {'ha_instance_id': self.inst_b.id}, ['ha_instance_id'],
            {'ha_instance_id': {}, 'ha_api_url': {}})
        self.assertEqual(result['value'].get('ha_api_url'), 'http://sweep-b.invalid:8123')
        result = self.env['ha.entity.share'].with_user(self.manager).onchange(
            {'entity_id': self.lock_other.id}, ['entity_id'],
            {'entity_id': {}, 'ha_instance_id': {}})
        self.assertEqual(result['value'].get('ha_instance_id'), self.inst_b.id)


@tagged('post_install', '-at_install', 'ha_review')
class TestReviewNoStatesInLog(TransactionCase):

    SENTINEL = 'review-camera-token-sentinel'

    def _api(self):
        instance = self.env['ha.instance'].sudo().create({
            'name': 'Review Log Instance', 'api_url': 'http://review-log.invalid:8123',
            'api_token': 'review-token-0123456789', 'active': True,
        })
        return hass_rest_api.HassRestApi(self.env, instance_id=instance.id)

    def test_states_and_history_content_not_logged(self):
        state = {'entity_id': 'camera.front', 'state': 'idle',
                 'attributes': {'access_token': self.SENTINEL, 'latitude': 25.033}}
        for method, args, body in (('get_ha_state', (), [state]),
                                   ('get_ha_history', ('camera.front',), [[state]])):
            with self.subTest(method=method):
                response = MagicMock(status_code=200)
                response.json.return_value = body
                with patch.object(hass_rest_api.requests, 'get', return_value=response), \
                        self.assertLogs(hass_rest_api._logger, level='DEBUG') as logs:
                    getattr(self._api(), method)(*args)
                self.assertNotIn(self.SENTINEL, '\n'.join(logs.output))


@tagged('post_install', '-at_install', 'ha_review')
class TestReviewRoutes(_ReviewFixtureMixin, HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_review_fixture()

    def _rpc(self, url, **params):
        response = self.url_open(url, data=json.dumps({'jsonrpc': '2.0', 'params': params}),
                                 headers={'Content-Type': 'application/json'})
        return response.json()

    def test_area_dashboard_of_another_instance_denied(self):
        self.authenticate('sweep_ha_user', PASSWORD)
        result = self._rpc('/odoo_ha_addon/area_dashboard_data',
                           area_id=0, ha_instance_id=self.inst_b.id)['result']
        self.assertFalse(result['success'])
        self.assertNotIn('Review Device B', json.dumps(result))
        result = self._rpc('/odoo_ha_addon/area_dashboard_data',
                           area_id=0, ha_instance_id=self.inst_a.id)['result']
        self.assertTrue(result['success'])
        self.assertIn('Sweep Device D', json.dumps(result))

    def test_portal_share_needs_an_active_instance(self):
        url = f'/my/ha/{self.inst_a.id}/entity/{self.light_a.id}/service'
        params = {'domain': 'light', 'service': 'turn_on', 'service_data': {}}
        self.authenticate('sweep_portal_share', PASSWORD)
        with patch('odoo.addons.odoo_ha_addon.models.common.websocket_client.get_websocket_client') as client:
            client.return_value.call_websocket_api.return_value = {'success': True}
            self.assertTrue(self._rpc(url, **params)['result']['success'])
            client.reset_mock()
            self.inst_a.sudo().write({'active': False})
            result = self._rpc(url, **params)['result']
            self.assertFalse(result['success'])
            self.assertEqual(result['error_code'], 'access_denied')
            client.assert_not_called()

    def test_portal_share_of_an_archived_group_denied(self):
        share = self.env['ha.entity.share'].sudo().create({
            'group_id': self.group_g.id, 'user_id': self.portal_none.id, 'permission': 'view',
        })
        self.authenticate('sweep_portal_none', PASSWORD)
        url = f'/my/ha/{self.inst_a.id}/group/{self.group_g.id}/state'
        self.assertTrue(self._rpc(url)['result']['success'])
        self.group_g.sudo().write({'active': False})
        self.assertFalse(self._rpc(url)['result']['success'])
        self.assertTrue(share.exists())
