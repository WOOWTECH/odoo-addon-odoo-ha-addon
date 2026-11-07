# -*- coding: utf-8 -*-
# Part of odoo_ha_addon. See LICENSE file for full copyright and licensing details.
"""
Regression tests for the 2026-11-07 security sweep.

Every class documents the finding fingerprint it covers.  Home Assistant is
never contacted: the WebSocket client and the thread manager are mocked.
"""
import inspect
import json
import re
from datetime import timedelta
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import HttpCase, TransactionCase, tagged

from odoo.addons.odoo_ha_addon import hooks
from odoo.addons.odoo_ha_addon.models.common import (
    hass_rest_api,
    websocket_client,
    websocket_thread_manager,
)

PASSWORD = 'Sweep-20261107-pw'


class _HAFixtureMixin:
    """Shared fixture: two instances, entities, groups, users and shares."""

    @classmethod
    def _make_user(cls, login, groups):
        return cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': login,
            'login': login,
            'password': PASSWORD,
            'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])],
        })

    @classmethod
    def _setup_ha_fixture(cls):
        env = cls.env
        Instance = env['ha.instance'].sudo()
        cls.inst_a = Instance.create({
            'name': 'Sweep Instance A', 'api_url': 'http://sweep-a.invalid:8123',
            'api_token': 'sweep-token-a-0123456789', 'active': True,
        })
        cls.inst_b = Instance.create({
            'name': 'Sweep Instance B', 'api_url': 'http://sweep-b.invalid:8123',
            'api_token': 'sweep-token-b-0123456789', 'active': True,
        })
        cls.device_d = env['ha.device'].sudo().create({
            'ha_instance_id': cls.inst_a.id, 'device_id': 'sweep_dev_d', 'name': 'Sweep Device D',
        })
        Entity = env['ha.entity'].sudo()
        cls.light_a = Entity.create({
            'name': 'Sweep Light A', 'entity_id': 'light.sweep_a', 'domain': 'light',
            'entity_state': 'off', 'ha_instance_id': cls.inst_a.id, 'device_id': cls.device_d.id,
        })
        cls.switch_b = Entity.create({
            'name': 'Sweep Switch B', 'entity_id': 'switch.sweep_b', 'domain': 'switch',
            'entity_state': 'off', 'ha_instance_id': cls.inst_a.id, 'device_id': cls.device_d.id,
        })
        cls.script_c = Entity.create({
            'name': 'Sweep Script C', 'entity_id': 'script.sweep_c', 'domain': 'script',
            'entity_state': 'off', 'ha_instance_id': cls.inst_a.id,
        })
        cls.number_n = Entity.create({
            'name': 'Sweep Number N', 'entity_id': 'input_number.sweep_n', 'domain': 'input_number',
            'entity_state': '1', 'ha_instance_id': cls.inst_a.id,
            'attributes': {'min': 0, 'max': 10},
        })
        cls.lock_other = Entity.create({
            'name': 'Sweep Lock B', 'entity_id': 'lock.sweep_b', 'domain': 'lock',
            'entity_state': 'locked', 'ha_instance_id': cls.inst_b.id,
        })

        cls.manager = cls._make_user('sweep_manager', ['odoo_ha_addon.group_ha_manager'])
        cls.ha_user = cls._make_user('sweep_ha_user', ['base.group_user', 'odoo_ha_addon.group_ha_user'])
        cls.ha_user2 = cls._make_user('sweep_ha_user2', ['base.group_user', 'odoo_ha_addon.group_ha_user'])
        cls.internal = cls._make_user('sweep_internal', ['base.group_user'])
        cls.portal_share = cls._make_user('sweep_portal_share', ['base.group_portal'])
        cls.portal_none = cls._make_user('sweep_portal_none', ['base.group_portal'])
        cls.portal_expired = cls._make_user('sweep_portal_expired', ['base.group_portal'])
        cls.portal_device = cls._make_user('sweep_portal_device', ['base.group_portal'])

        Group = env['ha.entity.group'].sudo()
        cls.group_g = Group.create({
            'name': 'Sweep Group G', 'ha_instance_id': cls.inst_a.id,
            'entity_ids': [(6, 0, [cls.light_a.id, cls.script_c.id, cls.number_n.id])],
            'user_ids': [(6, 0, [cls.ha_user.id])],
        })
        cls.group_other = Group.create({
            'name': 'Sweep Group Other', 'ha_instance_id': cls.inst_b.id,
            'entity_ids': [(6, 0, [cls.lock_other.id])],
            'user_ids': [(6, 0, [cls.ha_user2.id])],
        })

        Share = env['ha.entity.share'].sudo()
        cls.share_portal = Share.create({
            'entity_id': cls.light_a.id, 'user_id': cls.portal_share.id, 'permission': 'control',
        })
        cls.share_expired = Share.create({
            'entity_id': cls.light_a.id, 'user_id': cls.portal_expired.id, 'permission': 'control',
            'expiry_date': fields.Datetime.now() - timedelta(days=3),
        })
        cls.share_device = Share.create({
            'device_id': cls.device_d.id, 'user_id': cls.portal_device.id, 'permission': 'view',
        })
        env.registry.clear_cache()


# ---------------------------------------------------------------------------
# 81c5ad52f34c  ha.ws.request.queue global ACL
# ---------------------------------------------------------------------------
@tagged('post_install', '-at_install', 'ha_sweep')
class TestSweepWsRequestQueueAcl(_HAFixtureMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_ha_fixture()

    def test_no_global_acl_row(self):
        rows = self.env['ir.model.access'].search([
            ('model_id.model', '=', 'ha.ws.request.queue'),
            ('group_id', '=', False),
        ])
        self.assertFalse(rows, "ha.ws.request.queue must not have a group-less ACL row")
        self.assertFalse(self.env.ref('odoo_ha_addon.access_ha_ws_request_queue', raise_if_not_found=False))

    def test_non_system_users_cannot_create_or_read_queue(self):
        Queue = self.env['ha.ws.request.queue']
        for user in (self.portal_share, self.ha_user, self.manager, self.internal):
            with self.subTest(user=user.login):
                with self.assertRaises(AccessError):
                    Queue.with_user(user).create({
                        'request_id': 'sweep-%s' % user.id,
                        'message_type': 'call_service',
                        'payload': '{"domain": "homeassistant", "service": "restart"}',
                        'ha_instance_id': self.inst_a.id,
                    })
                with self.assertRaises(AccessError):
                    Queue.with_user(user).search_read([], ['result'])

    def test_manager_clear_wizard_still_counts_queue(self):
        self.env['ha.ws.request.queue'].sudo().create({
            'request_id': 'sweep-queue-1', 'message_type': 'get_states',
            'payload': '{}', 'ha_instance_id': self.inst_a.id,
        })
        wizard = self.env['ha.instance.clear.wizard'].with_user(self.manager).create({
            'instance_id': self.inst_a.id,
        })
        self.assertEqual(wizard.queue_count, 1)


# ---------------------------------------------------------------------------
# 9c5d22553699  realtime bus broadcast to every user  (+ hardening 3c2a6e5d034d)
# ---------------------------------------------------------------------------
@tagged('post_install', '-at_install', 'ha_sweep')
class TestSweepRealtimeBusRecipients(_HAFixtureMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_ha_fixture()

    def _capture(self, func):
        sent = []

        def fake_sendone(bus_self, target, notification_type, message):
            sent.append((target, notification_type, message))

        with patch.object(type(self.env['bus.bus']), '_sendone', fake_sendone):
            func()
        partners = self.env['res.partner']
        for target, _type, _msg in sent:
            if isinstance(target, tuple):
                target = target[0]
            if getattr(target, '_name', None) == 'res.partner':
                partners |= target
        return partners, sent

    def _notify(self, name, *args, **kwargs):
        model = self.env['ha.realtime.update'].sudo()
        # private after the fix; the public name exists on the vulnerable base
        method = getattr(model, '_' + name, None) or getattr(model, name)
        return method(*args, **kwargs)

    @staticmethod
    def _messages_by_partner(sent):
        result = {}
        for target, notification_type, message in sent:
            if isinstance(target, tuple):
                target = target[0]
            if getattr(target, '_name', None) == 'res.partner':
                result.setdefault(target.id, []).append((notification_type, message))
        return result

    def test_state_change_only_reaches_authorised_users(self):
        attributes = {
            'friendly_name': 'Sweep Light A',
            'access_token': 'cam-secret-token',
            'latitude': 25.03, 'longitude': 121.56,
            'entity_picture': '/api/camera_proxy/light.sweep_a?token=cam-secret-token&w=1',
        }
        partners, sent = self._capture(lambda: self._notify(
            'notify_entity_state_change', 'light.sweep_a',
            {'state': 'off', 'attributes': dict(attributes)},
            {'state': 'on', 'attributes': dict(attributes), 'context': {'user_id': 'ha-admin'}},
            ha_instance_id=self.inst_a.id,
        ))
        self.assertTrue(sent)
        self.assertTrue(all(t == 'ha_state_changed' for _c, t, _m in sent))
        for user in (self.manager, self.ha_user, self.portal_share, self.portal_device):
            self.assertIn(user.partner_id, partners, "%s is authorised" % user.login)
        for user in (self.ha_user2, self.internal, self.portal_none, self.portal_expired):
            self.assertNotIn(user.partner_id, partners, "%s must not receive the state" % user.login)

        by_partner = self._messages_by_partner(sent)
        # internal HA users authorised through groups keep the full HA state
        for user in (self.manager, self.ha_user):
            [(_t, message)] = by_partner[user.partner_id.id]
            self.assertEqual(message['new_state']['attributes']['access_token'], 'cam-secret-token')
            self.assertEqual(message['new_state']['attributes']['latitude'], 25.03)
        # share-only recipients get the portal attribute policy
        for user in (self.portal_share, self.portal_device):
            [(_t, message)] = by_partner[user.partner_id.id]
            self.assertEqual(message['entity_id'], 'light.sweep_a')
            self.assertEqual(message['new_state']['state'], 'on')
            for state_key in ('old_state', 'new_state'):
                attrs = message[state_key]['attributes']
                self.assertEqual(attrs['friendly_name'], 'Sweep Light A')
                for key in ('access_token', 'latitude', 'longitude'):
                    self.assertNotIn(key, attrs, "%s leaked to %s" % (key, user.login))
                self.assertNotIn('cam-secret-token', attrs['entity_picture'])
                self.assertIn('w=1', attrs['entity_picture'])
            self.assertNotIn('context', message['new_state'])

    def test_group_member_without_ha_user_group_gets_nothing(self):
        former = self._make_user('sweep_former_ha_user', ['base.group_user'])
        self.group_g.sudo().write({'user_ids': [(4, former.id)]})
        partners, _sent = self._capture(lambda: self._notify(
            'notify_entity_state_change', 'light.sweep_a', {}, {'state': 'on'},
            ha_instance_id=self.inst_a.id,
        ))
        self.assertIn(self.ha_user.partner_id, partners)
        self.assertNotIn(former.partner_id, partners)
        partners, _sent = self._capture(lambda: self._notify(
            'notify_ha_websocket_status', 'connected', 'ok', ha_instance_id=self.inst_a.id,
        ))
        self.assertNotIn(former.partner_id, partners)

    def test_instance_status_for_share_only_recipients_is_minimal(self):
        _partners, sent = self._capture(lambda: self._notify(
            'notify_ha_websocket_status', 'error', 'cannot reach http://10.0.0.5:8123',
            ha_instance_id=self.inst_a.id, instance_name='Sweep Instance A',
        ))
        by_partner = self._messages_by_partner(sent)
        [(_t, full)] = by_partner[self.manager.partner_id.id]
        self.assertEqual(full['message'], 'cannot reach http://10.0.0.5:8123')
        [(_t, minimal)] = by_partner[self.portal_share.partner_id.id]
        self.assertEqual(minimal['status'], 'error')
        self.assertNotIn('message', minimal)
        self.assertNotIn('instance_name', minimal)

    def test_public_group_reaches_all_ha_users_only(self):
        self.env['ha.entity.group'].sudo().create({
            'name': 'Sweep Public Group', 'ha_instance_id': self.inst_a.id,
            'entity_ids': [(6, 0, [self.switch_b.id])],
        })
        partners, sent = self._capture(lambda: self._notify(
            'notify_entity_state_change', 'switch.sweep_b', {},
            {'state': 'on', 'attributes': {'friendly_name': 'B', 'access_token': 'secret-b'},
             'context': {'user_id': 'ha-admin'}},
            ha_instance_id=self.inst_a.id,
        ))
        for user in (self.manager, self.ha_user, self.ha_user2):
            self.assertIn(user.partner_id, partners)
        for user in (self.internal, self.portal_none, self.portal_share):
            self.assertNotIn(user.partner_id, partners)
        # Round 3: the ha.entity record rules only follow explicit membership,
        # so public-group-only HA Users get the sanitized payload.
        by_partner = self._messages_by_partner(sent)
        [(_t, full)] = by_partner[self.manager.partner_id.id]
        self.assertEqual(full['new_state']['attributes']['access_token'], 'secret-b')
        for user in (self.ha_user, self.ha_user2):
            [(_t, message)] = by_partner[user.partner_id.id]
            self.assertEqual(message['new_state']['state'], 'on')
            self.assertEqual(message['new_state']['attributes']['friendly_name'], 'B')
            self.assertNotIn('access_token', message['new_state']['attributes'])
            self.assertNotIn('context', message['new_state'])

    def test_public_group_instance_status_is_minimal(self):
        self.env['ha.entity.group'].sudo().create({
            'name': 'Sweep Public Group B', 'ha_instance_id': self.inst_b.id,
            'entity_ids': [(6, 0, [self.lock_other.id])],
        })
        _partners, sent = self._capture(lambda: self._notify(
            'notify_ha_websocket_status', 'error', 'cannot reach http://10.0.0.6:8123',
            ha_instance_id=self.inst_b.id, instance_name='Sweep Instance B',
        ))
        by_partner = self._messages_by_partner(sent)
        [(_t, member)] = by_partner[self.ha_user2.partner_id.id]
        self.assertEqual(member['message'], 'cannot reach http://10.0.0.6:8123')
        [(_t, public)] = by_partner[self.ha_user.partner_id.id]
        self.assertEqual(public['status'], 'error')
        self.assertNotIn('message', public)
        self.assertNotIn(self.internal.partner_id.id, by_partner)

    def test_unknown_entity_only_reaches_managers(self):
        partners, _sent = self._capture(lambda: self._notify(
            'notify_entity_state_change', 'light.not_synced', {}, {'state': 'on'},
            ha_instance_id=self.inst_a.id,
        ))
        self.assertIn(self.manager.partner_id, partners)
        for user in (self.ha_user, self.internal, self.portal_share, self.portal_none):
            self.assertNotIn(user.partner_id, partners)

    def test_instance_status_scoped_to_instance(self):
        partners, _sent = self._capture(lambda: self._notify(
            'notify_ha_websocket_status', 'connected', 'ok', ha_instance_id=self.inst_b.id,
        ))
        self.assertIn(self.manager.partner_id, partners)
        self.assertIn(self.ha_user2.partner_id, partners)
        for user in (self.ha_user, self.internal, self.portal_share, self.portal_none):
            self.assertNotIn(user.partner_id, partners)

    def test_registry_updates_scoped_to_instance(self):
        for name, arg in (('notify_device_registry_update', 'dev'), ('notify_area_registry_update', 'area')):
            with self.subTest(name=name):
                partners, _sent = self._capture(lambda: self._notify(
                    name, 'update', arg, ha_instance_id=self.inst_a.id))
                self.assertIn(self.ha_user.partner_id, partners)
                self.assertIn(self.portal_share.partner_id, partners)
                for user in (self.ha_user2, self.internal, self.portal_none):
                    self.assertNotIn(user.partner_id, partners)

    def test_instance_switched_only_to_switching_user(self):
        partners, _sent = self._capture(lambda: self._notify(
            'notify_instance_switched', self.inst_a.id, self.inst_a.name, user_id=self.ha_user.id))
        self.assertEqual(partners, self.ha_user.partner_id)

    def test_notify_helpers_are_private(self):
        model = self.env['ha.realtime.update']
        for name in ('notify_entity_state_change', 'notify_ha_websocket_status',
                     'notify_instance_invalidated', 'notify_instance_fallback',
                     'notify_instance_switched', 'notify_device_registry_update',
                     'notify_area_registry_update', '_broadcast_to_users'):
            self.assertFalse(hasattr(model, name), "%s must not be a public RPC method" % name)
            if not name.startswith('_'):
                self.assertTrue(hasattr(model, '_' + name))


# ---------------------------------------------------------------------------
# 7cc62a202824  HA User self-authorisation through ha.entity.group CRUD
# ---------------------------------------------------------------------------
@tagged('post_install', '-at_install', 'ha_sweep')
class TestSweepEntityGroupAcl(_HAFixtureMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_ha_fixture()
        cls.public_group = cls.env['ha.entity.group'].sudo().create({
            'name': 'Sweep Public B', 'ha_instance_id': cls.inst_b.id,
            'entity_ids': [(6, 0, [cls.lock_other.id])],
        })

    def test_ha_user_cannot_create_group(self):
        with self.assertRaises(AccessError):
            self.env['ha.entity.group'].with_user(self.ha_user).create({
                'name': 'Sweep Self Grant', 'ha_instance_id': self.inst_b.id,
                'user_ids': [(4, self.ha_user.id)],
            })

    def test_ha_user_cannot_join_public_group(self):
        with self.assertRaises(AccessError):
            self.public_group.with_user(self.ha_user).write({'user_ids': [(4, self.ha_user.id)]})

    def test_ha_user_cannot_modify_or_delete_own_group(self):
        group = self.group_g.with_user(self.ha_user)
        with self.assertRaises(AccessError):
            group.write({'entity_ids': [(4, self.switch_b.id)]})
        with self.assertRaises(AccessError):
            group.unlink()

    def test_ha_user_cannot_manage_group_tags(self):
        with self.assertRaises(AccessError):
            self.env['ha.entity.group.tag'].with_user(self.ha_user).create({
                'name': 'Sweep Tag', 'ha_instance_id': self.inst_a.id,
            })

    def test_ha_user_still_reads_own_group_and_entities(self):
        groups = self.env['ha.entity.group'].with_user(self.ha_user).search([('id', '=', self.group_g.id)])
        self.assertEqual(groups, self.group_g)
        visible = self.env['ha.entity'].with_user(self.ha_user).search([('ha_instance_id', '=', self.inst_a.id)])
        self.assertIn(self.light_a, visible)
        self.assertNotIn(self.switch_b, visible)

    def test_manager_grant_and_revoke_take_effect_immediately(self):
        Entity = self.env['ha.entity'].with_user(self.ha_user2)
        # warm the per-uid ir.rule cache
        self.assertNotIn(self.light_a, Entity.search([('ha_instance_id', '=', self.inst_a.id)]))
        self.group_g.with_user(self.manager).write({'user_ids': [(4, self.ha_user2.id)]})
        self.assertIn(self.light_a, Entity.search([('ha_instance_id', '=', self.inst_a.id)]))
        self.group_g.with_user(self.manager).write({'user_ids': [(3, self.ha_user2.id)]})
        self.assertNotIn(self.light_a, Entity.search([('ha_instance_id', '=', self.inst_a.id)]))


# ---------------------------------------------------------------------------
# 9b54a6ece4bd  ha.entity.share readable by every portal / HA user
# ---------------------------------------------------------------------------
@tagged('post_install', '-at_install', 'ha_sweep')
class TestSweepEntityShareRules(_HAFixtureMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_ha_fixture()
        cls.share_ha_user = cls.env['ha.entity.share'].sudo().create({
            'entity_id': cls.switch_b.id, 'user_id': cls.ha_user.id, 'permission': 'view',
        })

    def test_portal_reads_only_own_shares(self):
        rows = self.env['ha.entity.share'].with_user(self.portal_share).search_read([], ['user_id'])
        self.assertTrue(rows)
        self.assertEqual({r['user_id'][0] for r in rows}, {self.portal_share.id})
        self.assertEqual(self.env['ha.entity.share'].with_user(self.portal_none).search_count([]), 0)

    def test_ha_user_reads_only_own_shares(self):
        shares = self.env['ha.entity.share'].with_user(self.ha_user).search([])
        self.assertEqual(shares, self.share_ha_user)

    def test_manager_reads_all_shares(self):
        shares = self.env['ha.entity.share'].with_user(self.manager).search([])
        for share in (self.share_portal, self.share_expired, self.share_device, self.share_ha_user):
            self.assertIn(share, shares)


# ---------------------------------------------------------------------------
# Hardening: model-level manager checks, runtime pip, token logs, portal token
# (4f22a544827d, b876fbe88121, 33c0905ad0b5, 655a39e9d150)
# ---------------------------------------------------------------------------
@tagged('post_install', '-at_install', 'ha_sweep')
class TestSweepModelHardening(_HAFixtureMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_ha_fixture()

    def test_websocket_start_stop_require_manager(self):
        with patch.object(websocket_thread_manager, 'start_websocket_service') as start, \
                patch.object(websocket_thread_manager, 'stop_websocket_service') as stop:
            Entity = self.env['ha.entity']
            with self.assertRaises(AccessError):
                Entity.with_user(self.ha_user).start_websocket_service_manual()
            with self.assertRaises(AccessError):
                Entity.with_user(self.ha_user).stop_websocket_service()
            start.assert_not_called()
            stop.assert_not_called()

            Entity.with_user(self.manager).stop_websocket_service()
            stop.assert_called_once_with(self.env.cr.dbname)

    def test_instance_actions_require_manager(self):
        instance = self.inst_a.with_user(self.ha_user)
        with patch.object(websocket_thread_manager, 'restart_websocket_service') as restart, \
                patch.object(websocket_client, 'get_websocket_client'):
            for action in ('action_restart_websocket', 'action_sync_entities',
                           'action_sync_registry', 'action_clear_data'):
                with self.subTest(action=action):
                    with self.assertRaises(AccessError):
                        getattr(instance, action)()
            restart.assert_not_called()

    def test_sync_entry_points_require_manager(self):
        calls = [
            lambda: self.env['ha.entity'].with_user(self.ha_user).sync_entity_states_from_ha(self.inst_a.id),
            lambda: self.env['ha.area'].with_user(self.ha_user).sync_areas_from_ha(self.inst_a.id),
            lambda: self.env['ha.device'].with_user(self.ha_user).sync_devices_from_ha(self.inst_a.id),
            lambda: self.env['ha.label'].with_user(self.ha_user).sync_labels_from_ha(self.inst_a.id),
            lambda: self.script_c.with_user(self.ha_user).action_run_script(),
        ]
        with patch.object(websocket_client, 'get_websocket_client') as client:
            for call in calls:
                with self.assertRaises(AccessError):
                    call()
            client.assert_not_called()

    def test_scene_activation_matches_call_service_policy(self):
        """Round 3: HA Users may activate scenes they can read (like call_service scene.turn_on)."""
        Entity = self.env['ha.entity'].sudo()
        scene = Entity.create({
            'name': 'Sweep Scene S', 'entity_id': 'scene.sweep_s', 'domain': 'scene',
            'entity_state': 'scening', 'ha_instance_id': self.inst_a.id,
        })
        hidden_scene = Entity.create({
            'name': 'Sweep Scene H', 'entity_id': 'scene.sweep_h', 'domain': 'scene',
            'entity_state': 'scening', 'ha_instance_id': self.inst_a.id,
        })
        self.group_g.sudo().write({'entity_ids': [(4, scene.id)]})
        self.env.registry.clear_cache()
        client = MagicMock()
        with patch.object(websocket_client, 'get_websocket_client', return_value=client):
            result = scene.with_user(self.ha_user).action_activate_scene()
            self.assertEqual(result['params']['type'], 'success', result)
            client.call_websocket_api_sync.assert_called_once_with('call_service', {
                'domain': 'scene', 'service': 'turn_on', 'target': {'entity_id': 'scene.sweep_s'},
            })
            client.reset_mock()
            for user, record in ((self.ha_user, hidden_scene), (self.ha_user2, scene),
                                 (self.internal, scene), (self.portal_share, scene)):
                with self.subTest(user=user.login, record=record.entity_id):
                    with self.assertRaises(AccessError):
                        record.with_user(user).action_activate_scene()
            # scripts stay manager-only for HA Users, managers keep both
            with self.assertRaises(AccessError):
                self.script_c.with_user(self.ha_user).action_run_script()
            client.call_websocket_api_sync.assert_not_called()
            scene.with_user(self.manager).action_activate_scene()
            client.call_websocket_api_sync.assert_called_once()

    def test_no_runtime_pip_install(self):
        source = inspect.getsource(hooks)
        self.assertNotIn('subprocess', source)
        self.assertNotIn("'-m', 'pip'", source)
        from odoo.modules.module import get_manifest
        manifest = get_manifest('odoo_ha_addon')
        self.assertIn('websockets', manifest.get('external_dependencies', {}).get('python', []))

    def test_token_prefix_not_logged(self):
        for module in (hass_rest_api, websocket_thread_manager):
            source = inspect.getsource(module)
            self.assertNotIn("token[:10]", source)
            self.assertNotIn("ha_token[:10]", source)

    def test_revoking_share_resets_portal_token(self):
        self.light_a._portal_ensure_token()
        self.assertTrue(self.light_a.access_token)
        self.share_portal.unlink()
        self.assertFalse(self.light_a.access_token)

    def test_expiry_cron_resets_portal_token(self):
        self.light_a._portal_ensure_token()
        self.share_expired.write({'expiry_date': fields.Datetime.now() - timedelta(hours=1)})
        self.env['ha.entity.share']._cron_check_expiring_shares()
        self.assertFalse(self.light_a.access_token)


# ---------------------------------------------------------------------------
# HTTP controllers: eefe41281f6e (restart/areas), eae835a11941 (call_service,
# glances, hardware/network), 940a44f359bd (portal call-service), 99fb8b890178
# ---------------------------------------------------------------------------
class _ControllerCase(_HAFixtureMixin, HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_ha_fixture()

    def setUp(self):
        super().setUp()
        self.ws_calls = []
        self.registry_entities = [
            {'entity_id': 'light.sweep_a', 'device_id': 'sweep_dev_d'},
            {'entity_id': 'switch.sweep_b', 'device_id': 'sweep_dev_d'},
        ]
        self.devices = [
            {'id': 'sweep_dev_d', 'name': 'Glances D', 'identifiers': [['glances', 'd']]},
            {'id': 'sweep_dev_x', 'name': 'Glances X', 'identifiers': [['glances', 'x']]},
        ]

        def call_websocket_api(message_type, payload=None, timeout=15):
            self.ws_calls.append((message_type, payload))
            if message_type == 'config/entity_registry/list':
                return {'success': True, 'data': self.registry_entities}
            if message_type == 'config/device_registry/list':
                return {'success': True, 'data': self.devices}
            if message_type == 'get_states':
                return {'success': True, 'data': [
                    {'entity_id': 'light.sweep_a', 'state': 'on', 'attributes': {}},
                    {'entity_id': 'switch.sweep_b', 'state': 'on', 'attributes': {'secret': 'x'}},
                ]}
            if message_type == 'search/related':
                return {'success': True, 'data': self.related_data}
            if message_type == 'network/url':
                return {'success': True, 'data': {
                    'internal': 'http://192.168.77.10:8123',
                    'external': 'https://sweep-external.invalid',
                    'cloud': 'https://sweepcloud.ui.nabu.casa',
                }}
            return {'success': True, 'data': {'context': {}}}

        def call_websocket_api_sync(message_type, payload=None, timeout=15):
            self.ws_calls.append((message_type, payload))
            if message_type == 'config/area_registry/list':
                return [{'area_id': 'rv_area', 'name': 'Forged area'}]
            return []

        self.related_data = {}
        client = MagicMock()
        client.call_websocket_api.side_effect = call_websocket_api
        client.call_websocket_api_sync.side_effect = call_websocket_api_sync
        patch.object(websocket_client, 'get_websocket_client', return_value=client).start()

        self.restart = patch.object(
            websocket_thread_manager, 'restart_websocket_service',
            return_value={'success': True, 'message': 'restarted'}).start()
        self.addCleanup(patch.stopall)

    def _rpc(self, route, **params):
        return self.make_jsonrpc_request(route, params)

    def _service_calls(self):
        return [p for t, p in self.ws_calls if t == 'call_service']


@tagged('post_install', '-at_install', 'ha_sweep')
class TestSweepRestartAndAreas(_ControllerCase):

    def _patch_sync(self):
        area_sync = patch.object(type(self.env['ha.area']), 'sync_areas_from_ha').start()
        entity_sync = patch.object(type(self.env['ha.entity']), 'sync_entity_states_from_ha').start()
        rel_sync = patch.object(type(self.env['ha.entity']), '_sync_entity_registry_relations').start()
        return area_sync, entity_sync, rel_sync

    def test_restart_denied_for_portal_and_ha_user(self):
        for login in ('sweep_portal_share', 'sweep_ha_user'):
            self.authenticate(login, PASSWORD)
            for instance_id in (0, False, self.inst_a.id, self.inst_b.id):
                with self.subTest(login=login, instance_id=instance_id):
                    result = self._rpc('/odoo_ha_addon/websocket_restart',
                                       ha_instance_id=instance_id, force=True)
                    self.assertFalse(result['success'])
        self.restart.assert_not_called()

    def test_restart_manager_never_restarts_all(self):
        self.authenticate('sweep_manager', PASSWORD)
        for instance_id in (0, False, -3, 'abc'):
            result = self._rpc('/odoo_ha_addon/websocket_restart', ha_instance_id=instance_id)
            self.assertFalse(result['success'])
        self.restart.assert_not_called()
        result = self._rpc('/odoo_ha_addon/websocket_restart', ha_instance_id=self.inst_a.id)
        self.assertTrue(result['success'])
        self.restart.assert_called_once()
        self.assertEqual(self.restart.call_args.kwargs['instance_id'], self.inst_a.id)

    def test_areas_no_sync_for_unauthorised_or_non_manager(self):
        area_sync, entity_sync, rel_sync = self._patch_sync()
        self.authenticate('sweep_portal_share', PASSWORD)
        result = self._rpc('/odoo_ha_addon/areas', ha_instance_id=self.inst_a.id)
        self.assertFalse(result['success'])

        self.authenticate('sweep_ha_user', PASSWORD)
        result = self._rpc('/odoo_ha_addon/areas', ha_instance_id=self.inst_b.id)
        self.assertFalse(result['success'], "instance B is not visible to this HA User")
        result = self._rpc('/odoo_ha_addon/areas', ha_instance_id=self.inst_a.id)
        self.assertTrue(result['success'], "authorised HA User still reads areas")
        area_sync.assert_not_called()
        entity_sync.assert_not_called()
        rel_sync.assert_not_called()

    def test_areas_manager_triggers_sync(self):
        area_sync, entity_sync, rel_sync = self._patch_sync()
        self.authenticate('sweep_manager', PASSWORD)
        result = self._rpc('/odoo_ha_addon/areas', ha_instance_id=self.inst_a.id)
        self.assertTrue(result['success'])
        area_sync.assert_called_once()
        entity_sync.assert_called_once()


@tagged('post_install', '-at_install', 'ha_sweep')
class TestSweepCallService(_ControllerCase):

    def _as_ha_user_with_preference(self):
        # current instance preference (the path that bypassed the api_token
        # field check on the vulnerable base through the sudo prefetch)
        self.ha_user.sudo().write({'current_ha_instance_id': self.inst_a.id})
        self.authenticate('sweep_ha_user', PASSWORD)

    def test_ha_user_controls_authorised_entity(self):
        self._as_ha_user_with_preference()
        result = self._rpc('/odoo_ha_addon/call_service', domain='light', service='turn_on',
                           service_data={'entity_id': 'light.sweep_a', 'brightness': 100,
                                         'area_id': 'kitchen', 'device_id': 'x',
                                         'target': {'area_id': 'kitchen'}, 'foo': 'bar'},
                           ha_instance_id=self.inst_a.id)
        self.assertTrue(result['success'], result)
        self.assertEqual(self._service_calls(), [{
            'domain': 'light', 'service': 'turn_on',
            'service_data': {'entity_id': 'light.sweep_a', 'brightness': 100},
        }])

    def test_ha_user_without_explicit_instance_uses_current(self):
        self._as_ha_user_with_preference()
        result = self._rpc('/odoo_ha_addon/call_service', domain='light', service='toggle',
                           service_data={'entity_id': 'light.sweep_a'})
        self.assertTrue(result['success'], result)
        self.assertEqual(len(self._service_calls()), 1)

    def test_ha_user_denied_calls(self):
        self._as_ha_user_with_preference()
        denied = [
            ('switch', 'turn_off', {'entity_id': 'switch.sweep_b'}),          # not in group
            ('homeassistant', 'restart', {'entity_id': 'light.sweep_a'}),     # system domain
            ('shell_command', 'run', {'entity_id': 'light.sweep_a'}),
            ('script', 'turn_on', {'entity_id': 'script.sweep_c'}),           # manager-only domain
            ('lock', 'unlock', {'entity_id': 'light.sweep_a'}),               # domain mismatch
            ('lock', 'unlock', {'entity_id': 'lock.sweep_b'}),                # other instance
            ('light', 'turn_on', {'entity_id': ['light.sweep_a', 'switch.sweep_b']}),
            ('light', 'turn_on', {'entity_id': 'all'}),
            ('input_number', 'set_value', {'entity_id': 'input_number.sweep_n', 'value': 'nan'}),
            ('light', 'turn_on', {'entity_id': 'light.sweep_a', 'brightness': 'inf'}),
        ]
        for domain, service, data in denied:
            with self.subTest(domain=domain, service=service, data=data):
                result = self._rpc('/odoo_ha_addon/call_service', domain=domain,
                                   service=service, service_data=data)
                self.assertFalse(result['success'], result)
        self.assertEqual(self._service_calls(), [])

    def test_manager_only_domain_message_is_clear(self):
        """Round 3: dashboard users see why a script/automation card cannot run."""
        self._as_ha_user_with_preference()
        result = self._rpc('/odoo_ha_addon/call_service', domain='script', service='turn_on',
                           service_data={'entity_id': 'script.sweep_c'}, ha_instance_id=self.inst_a.id)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'domain_denied')
        self.assertIn('Only Home Assistant Managers', result['error'])
        self.assertEqual(self._service_calls(), [])

    def test_number_value_clamped_with_finite_check(self):
        self._as_ha_user_with_preference()
        result = self._rpc('/odoo_ha_addon/call_service', domain='input_number', service='set_value',
                           service_data={'entity_id': 'input_number.sweep_n', 'value': 42},
                           ha_instance_id=self.inst_a.id)
        self.assertTrue(result['success'], result)
        self.assertEqual(self._service_calls()[0]['service_data']['value'], 10)

    def test_portal_and_internal_without_groups_denied(self):
        for login in ('sweep_portal_share', 'sweep_internal'):
            self.authenticate(login, PASSWORD)
            result = self._rpc('/odoo_ha_addon/call_service', domain='light', service='turn_on',
                               service_data={'entity_id': 'light.sweep_a'},
                               ha_instance_id=self.inst_a.id)
            self.assertFalse(result['success'])
        self.assertEqual(self._service_calls(), [])

    def test_manager_call_service_drops_target_selectors(self):
        self.authenticate('sweep_manager', PASSWORD)
        result = self._rpc('/odoo_ha_addon/call_service', domain='script', service='turn_on',
                           service_data={'entity_id': 'script.sweep_c', 'area_id': 'all'},
                           ha_instance_id=self.inst_a.id)
        self.assertTrue(result['success'], result)
        self.assertEqual(self._service_calls()[0]['service_data'], {'entity_id': 'script.sweep_c'})
        result = self._rpc('/odoo_ha_addon/call_service', domain='homeassistant', service='restart',
                           service_data={'entity_id': 'light.sweep_a'},
                           ha_instance_id=self.inst_a.id)
        self.assertFalse(result['success'], "domain must match the entity domain")

    def test_glances_only_visible_entities(self):
        self._as_ha_user_with_preference()
        result = self._rpc('/odoo_ha_addon/glances_device_entities', device_id='sweep_dev_d',
                           ha_instance_id=self.inst_a.id)
        self.assertTrue(result['success'], result)
        self.assertEqual([e['entity_id'] for e in result['data']['entities']], ['light.sweep_a'])

        result = self._rpc('/odoo_ha_addon/glances_devices', ha_instance_id=self.inst_a.id)
        self.assertTrue(result['success'], result)
        self.assertEqual([d['id'] for d in result['data']['devices']], ['sweep_dev_d'])

    def test_entity_related_only_visible_entities(self):
        self._as_ha_user_with_preference()
        result = self._rpc('/odoo_ha_addon/entity_related', entity_id='switch.sweep_b',
                           ha_instance_id=self.inst_a.id)
        self.assertFalse(result['success'])
        self.assertFalse([t for t, _p in self.ws_calls if t == 'search/related'])
        result = self._rpc('/odoo_ha_addon/entity_related', entity_id='light.sweep_a',
                           ha_instance_id=self.inst_a.id)
        self.assertTrue(result['success'], result)

    def test_hardware_and_network_info_manager_only(self):
        self._as_ha_user_with_preference()
        for route in ('/odoo_ha_addon/hardware_info', '/odoo_ha_addon/network_info'):
            result = self._rpc(route, ha_instance_id=self.inst_a.id)
            self.assertFalse(result['success'])
        self.assertFalse([t for t, _p in self.ws_calls if t == 'supervisor/api'])
        self.authenticate('sweep_manager', PASSWORD)
        result = self._rpc('/odoo_ha_addon/hardware_info', ha_instance_id=self.inst_a.id)
        self.assertTrue(result['success'], result)
        self.assertTrue([t for t, _p in self.ws_calls if t == 'supervisor/api'])


@tagged('post_install', '-at_install', 'ha_sweep')
class TestSweepPortalCallService(_ControllerCase):

    def _portal_call(self, domain, service, service_data, instance=None, entity=None):
        instance = instance or self.inst_a
        entity = entity or self.light_a
        return self._rpc('/my/ha/%s/entity/%s/service' % (instance.id, entity.id),
                         domain=domain, service=service, service_data=service_data)

    def test_portal_control_happy_path_strips_selectors(self):
        self.authenticate('sweep_portal_share', PASSWORD)
        result = self._portal_call('light', 'turn_on', {
            'brightness': 50, 'area_id': 'kitchen', 'device_id': 'dev', 'floor_id': 'f1',
            'label_id': 'l1', 'target': {'area_id': 'kitchen'}, 'entity_id': 'lock.front', 'x': 1,
        })
        self.assertTrue(result['success'], result)
        self.assertEqual(self._service_calls(), [{
            'domain': 'light', 'service': 'turn_on',
            'service_data': {'entity_id': 'light.sweep_a', 'brightness': 50},
        }])

    def test_portal_domain_must_match_entity(self):
        self.authenticate('sweep_portal_share', PASSWORD)
        for domain, service in (('lock', 'unlock'), ('cover', 'open_cover'),
                                ('alarm_control_panel', 'alarm_disarm'), ('homeassistant', 'restart')):
            with self.subTest(domain=domain):
                result = self._portal_call(domain, service, {'area_id': 'kitchen'})
                self.assertFalse(result['success'])
        self.assertEqual(self._service_calls(), [])

    def test_portal_rejects_non_finite_and_wrong_instance(self):
        self.authenticate('sweep_portal_share', PASSWORD)
        result = self._portal_call('light', 'turn_on', {'brightness': 'nan'})
        self.assertFalse(result['success'])
        result = self._portal_call('light', 'turn_on', {}, instance=self.inst_b)
        self.assertFalse(result['success'])
        self.assertEqual(self._service_calls(), [])

    def test_portal_without_control_share_denied(self):
        for login in ('sweep_portal_none', 'sweep_portal_expired', 'sweep_portal_device'):
            self.authenticate(login, PASSWORD)
            result = self._portal_call('light', 'turn_on', {})
            self.assertFalse(result['success'])
        self.assertEqual(self._service_calls(), [])


    def _shared_entity(self, entity_id, domain, user, permission='control'):
        entity = self.env['ha.entity'].sudo().create({
            'name': 'Sweep %s' % entity_id, 'entity_id': entity_id, 'domain': domain,
            'entity_state': 'off', 'ha_instance_id': self.inst_a.id,
        })
        self.env['ha.entity.share'].sudo().create({
            'entity_id': entity.id, 'user_id': user.id, 'permission': permission,
        })
        return entity

    def test_portal_control_share_on_script_and_automation(self):
        """Round 3: a control share on script/automation keeps the portal buttons working."""
        automation = self._shared_entity('automation.sweep_auto', 'automation', self.portal_share)
        self.env['ha.entity.share'].sudo().create({
            'entity_id': self.script_c.id, 'user_id': self.portal_share.id, 'permission': 'control',
        })
        self.authenticate('sweep_portal_share', PASSWORD)
        cases = [
            # (entity, domain, service, data sent by domain_config.js, expected HA service_data)
            (self.script_c, 'script', 'turn_on', {'area_id': 'all'}, {'entity_id': 'script.sweep_c'}),
            (self.script_c, 'script', 'toggle', {}, {'entity_id': 'script.sweep_c'}),
            (automation, 'automation', 'trigger', {'skip_condition': True, 'target': {'area_id': 'x'}},
             {'entity_id': 'automation.sweep_auto', 'skip_condition': True}),
            (automation, 'automation', 'toggle', {}, {'entity_id': 'automation.sweep_auto'}),
        ]
        for entity, domain, service, data, expected in cases:
            with self.subTest(domain=domain, service=service):
                self.ws_calls.clear()
                result = self._portal_call(domain, service, data, entity=entity)
                self.assertTrue(result['success'], result)
                self.assertEqual(self._service_calls(), [{
                    'domain': domain, 'service': service, 'service_data': expected,
                }])
        # still restricted to the entity's own domain and the whitelist
        self.ws_calls.clear()
        for domain, service in (('script', 'reload'), ('automation', 'reload'),
                                ('homeassistant', 'turn_on')):
            with self.subTest(denied='%s.%s' % (domain, service)):
                entity = self.script_c if domain != 'automation' else automation
                result = self._portal_call(domain, service, {}, entity=entity)
                self.assertFalse(result['success'], result)
        self.assertEqual(self._service_calls(), [])

    def test_portal_view_share_on_script_denied(self):
        self.env['ha.entity.share'].sudo().create({
            'entity_id': self.script_c.id, 'user_id': self.portal_none.id, 'permission': 'view',
        })
        automation = self._shared_entity(
            'automation.sweep_view', 'automation', self.portal_none, permission='view')
        self.authenticate('sweep_portal_none', PASSWORD)
        self.assertFalse(self._portal_call('script', 'turn_on', {}, entity=self.script_c)['success'])
        self.assertFalse(self._portal_call('automation', 'trigger', {}, entity=automation)['success'])
        self.assertEqual(self._service_calls(), [])

    def test_portal_control_share_on_update_entity(self):
        """Portal keeps the base behaviour for explicitly shared update entities."""
        update = self._shared_entity('update.sweep_fw', 'update', self.portal_share)
        self.authenticate('sweep_portal_share', PASSWORD)
        result = self._portal_call('update', 'install', {'backup': True, 'device_id': 'x'}, entity=update)
        self.assertTrue(result['success'], result)
        self.assertEqual(self._service_calls(), [{
            'domain': 'update', 'service': 'install',
            'service_data': {'entity_id': 'update.sweep_fw', 'backup': True},
        }])

    def test_portal_legacy_route_rejects_non_int_entity(self):
        self.authenticate('sweep_portal_share', PASSWORD)
        for value in ('light.sweep_a', [self.light_a.id], True, -1):
            with self.subTest(value=value):
                result = self._rpc('/portal/call-service', domain='light', service='turn_on',
                                   service_data={'entity_id': value})
                self.assertFalse(result['success'], result)
        result = self._rpc('/portal/call-service', domain='light', service='turn_on',
                           service_data={'entity_id': self.light_a.id, 'area_id': 'all'})
        self.assertTrue(result['success'], result)
        self.assertEqual(self._service_calls(), [{
            'domain': 'light', 'service': 'turn_on',
            'service_data': {'entity_id': 'light.sweep_a'},
        }])


    def test_ha_user_cannot_install_updates(self):
        update = self.env['ha.entity'].sudo().create({
            'name': 'Sweep Update U', 'entity_id': 'update.sweep_u', 'domain': 'update',
            'entity_state': 'on', 'ha_instance_id': self.inst_a.id,
        })
        self.group_g.sudo().write({'entity_ids': [(4, update.id)]})
        self.env.registry.clear_cache()
        self.ha_user.sudo().write({'current_ha_instance_id': self.inst_a.id})
        self.authenticate('sweep_ha_user', PASSWORD)
        for service in ('install', 'skip'):
            result = self._rpc('/odoo_ha_addon/call_service', domain='update', service=service,
                               service_data={'entity_id': 'update.sweep_u'},
                               ha_instance_id=self.inst_a.id)
            self.assertFalse(result['success'], result)
        self.assertEqual(self._service_calls(), [])
        self.authenticate('sweep_manager', PASSWORD)
        result = self._rpc('/odoo_ha_addon/call_service', domain='update', service='install',
                           service_data={'entity_id': 'update.sweep_u'},
                           ha_instance_id=self.inst_a.id)
        self.assertTrue(result['success'], result)
        self.assertEqual(len(self._service_calls()), 1)


# ---------------------------------------------------------------------------
# eefe41281f6e / hardening 4f22a544827d: HA registry sync helpers and other
# model methods must not be reachable through /web/dataset/call_kw
# ---------------------------------------------------------------------------
@tagged('post_install', '-at_install', 'ha_sweep')
class TestSweepRegistryHelpersNotRpc(_ControllerCase):

    def _call_kw(self, model, method, args, kwargs=None):
        response = self.url_open(
            '/web/dataset/call_kw/%s/%s' % (model, method),
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': 1, 'params': {
                'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {},
            }}),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def _registry_calls(self):
        inst = self.inst_a.id
        return [
            ('ha.device', 'sync_device_from_ha_data',
             [{'id': 'rv_dev', 'name': 'Forged device', 'area_id': 'rv_area',
               'configuration_url': 'https://evil.example'}, inst]),
            ('ha.device', 'sync_device_from_ha_data',
             [{'id': 'sweep_dev_d', 'name': 'Overwritten', 'configuration_url': 'https://evil.example'}, inst]),
            ('ha.area', 'sync_area_from_ha_data', [{'area_id': 'rv_area', 'name': 'Forged area'}, inst]),
            ('ha.area', 'sync_area_from_ha_event', ['create', 'rv_area', inst]),
            ('ha.label', 'sync_label_from_ha_data', [{'label_id': 'rv_label', 'name': 'Forged label'}, inst]),
            ('ha.label', 'get_or_create_labels', [['rv_label'], inst]),
        ]

    def _assert_nothing_forged(self):
        self.assertFalse(self.env['ha.device'].sudo().search([('device_id', '=', 'rv_dev')]))
        self.assertFalse(self.env['ha.area'].sudo().search([('area_id', '=', 'rv_area')]))
        self.assertFalse(self.env['ha.label'].sudo().search([('label_id', '=', 'rv_label')]))
        self.device_d.invalidate_recordset()
        self.assertEqual(self.device_d.name, 'Sweep Device D')
        self.assertFalse(self.device_d.configuration_url)
        self.assertFalse([t for t, _p in self.ws_calls if t == 'config/area_registry/list'])

    def test_registry_sync_helpers_not_callable(self):
        for login in ('sweep_portal_none', 'sweep_ha_user', 'sweep_internal', 'sweep_manager'):
            self.authenticate(login, PASSWORD)
            for model, method, args in self._registry_calls():
                with self.subTest(login=login, method=method):
                    response = self._call_kw(model, method, args)
                    self.assertIn('error', response, response)
                    self.assertNotIn('result', response)
        self._assert_nothing_forged()

    def test_internal_registry_sync_still_works(self):
        # the WebSocket service / manual sync path uses the private helpers
        action, device = self.env['ha.device'].sudo()._sync_device_from_ha_data(
            {'id': 'sweep_dev_new', 'name': 'New Device', 'area_id': 'sweep_area_new'}, self.inst_a.id)
        self.assertEqual(action, 'created')
        self.assertEqual(device.area_id.area_id, 'sweep_area_new')
        action, _area = self.env['ha.area'].sudo()._sync_area_from_ha_data(
            {'area_id': 'sweep_area_new', 'name': 'Kitchen'}, self.inst_a.id)
        self.assertEqual(action, 'updated')
        self.assertEqual(device.area_id.name, 'Kitchen')
        action, label = self.env['ha.label'].sudo()._sync_label_from_ha_data(
            {'label_id': 'sweep_label', 'name': 'Sweep'}, self.inst_a.id)
        self.assertEqual(action, 'created')
        self.assertEqual(self.env['ha.label']._get_or_create_labels(['sweep_label'], self.inst_a.id), label)

    def test_accessible_instances_of_other_user(self):
        self.authenticate('sweep_ha_user', PASSWORD)
        response = self._call_kw('ha.instance', 'get_accessible_instances', [],
                                 {'user_id': self.manager.id})
        self.assertIn('error', response, response)
        self.assertNotIn('result', response)
        for login in ('sweep_ha_user', 'sweep_manager'):
            self.authenticate(login, PASSWORD)
            response = self._call_kw('ha.instance', 'get_accessible_instances', [],
                                     {'user_id': self.ha_user.id})
            self.assertNotIn('error', response, response)
            # the method returns a recordset, serialised as "ha.instance(1, 2)"
            ids = [int(i) for i in re.findall(r'\d+', str(response['result']))]
            self.assertIn(self.inst_a.id, ids, response)
            self.assertNotIn(self.inst_b.id, ids, response)

    def test_entity_related_filters_hidden_records(self):
        hidden = self.env['ha.entity'].sudo().create({
            'name': 'Sweep Hidden Automation', 'entity_id': 'automation.sweep_hidden',
            'domain': 'automation', 'ha_instance_id': self.inst_a.id,
        })
        self.related_data = {
            'automation': ['automation.sweep_hidden'],
            'script': ['script.sweep_c'],
        }
        self.ha_user.sudo().write({'current_ha_instance_id': self.inst_a.id})
        self.authenticate('sweep_ha_user', PASSWORD)
        result = self._rpc('/odoo_ha_addon/entity_related', entity_id='light.sweep_a',
                           ha_instance_id=self.inst_a.id)
        self.assertTrue(result['success'], result)
        self.assertEqual(result['data']['automations'], [])
        self.assertEqual([s['entity_id'] for s in result['data']['scripts']], ['script.sweep_c'])
        self.authenticate('sweep_manager', PASSWORD)
        result = self._rpc('/odoo_ha_addon/entity_related', entity_id='light.sweep_a',
                           ha_instance_id=self.inst_a.id)
        self.assertEqual([a['id'] for a in result['data']['automations']], [hidden.id])


@tagged('post_install', '-at_install', 'ha_sweep')
class TestSweepEntitySideMembershipCache(_HAFixtureMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_ha_fixture()

    def test_entity_side_revoke_applies_immediately(self):
        Entity = self.env['ha.entity'].with_user(self.ha_user)
        self.assertIn(self.light_a, Entity.search([('ha_instance_id', '=', self.inst_a.id)]))
        self.light_a.sudo().write({'group_ids': [(3, self.group_g.id)]})
        self.assertNotIn(self.light_a, Entity.search([('ha_instance_id', '=', self.inst_a.id)]))
        self.switch_b.sudo().write({'group_ids': [(4, self.group_g.id)]})
        self.assertIn(self.switch_b, Entity.search([('ha_instance_id', '=', self.inst_a.id)]))


# ---------------------------------------------------------------------------
# Round-1 open item: /odoo_ha_addon/ha_urls and /websocket_status exposed the
# HA host URLs (LAN, external, Nabu Casa cloud) to every user who can read
# the instance.
# ---------------------------------------------------------------------------
@tagged('post_install', '-at_install', 'ha_sweep')
class TestSweepHaUrlsAndStatus(_ControllerCase):

    URL_MARKERS = ('192.168.77.10', 'sweep-external.invalid', 'nabu.casa', 'sweep-a.invalid')

    def setUp(self):
        super().setUp()
        patch.object(websocket_thread_manager, 'is_websocket_service_running',
                     return_value=True).start()
        patch.object(websocket_thread_manager, 'is_config_changed',
                     return_value=False).start()

    def _assert_no_urls(self, result):
        dumped = json.dumps(result)
        for marker in self.URL_MARKERS:
            self.assertNotIn(marker, dumped)

    def test_ha_urls_manager_only(self):
        for login in ('sweep_ha_user', 'sweep_portal_share', 'sweep_internal'):
            with self.subTest(login=login):
                self.ws_calls.clear()
                self.authenticate(login, PASSWORD)
                result = self._rpc('/odoo_ha_addon/ha_urls', ha_instance_id=self.inst_a.id)
                self.assertFalse(result['success'])
                self._assert_no_urls(result)
                self.assertFalse(
                    [t for t, _p in self.ws_calls if t == 'network/url'],
                    "HA must not be queried for non-managers")

        self.authenticate('sweep_manager', PASSWORD)
        result = self._rpc('/odoo_ha_addon/ha_urls', ha_instance_id=self.inst_a.id)
        self.assertTrue(result['success'])
        self.assertEqual(result['data'], {
            'internal': 'http://192.168.77.10:8123',
            'external': 'https://sweep-external.invalid',
            'cloud': 'https://sweepcloud.ui.nabu.casa',
        })

    def test_websocket_status_hides_url_for_non_managers(self):
        self.authenticate('sweep_ha_user', PASSWORD)
        result = self._rpc('/odoo_ha_addon/websocket_status', ha_instance_id=self.inst_a.id)
        self.assertTrue(result['success'])
        data = result['data']
        # What the dashboard needs is still there.
        self.assertIs(data['is_running'], True)
        self.assertIs(data['config_synced'], True)
        self.assertEqual(data['instance_id'], self.inst_a.id)
        self.assertEqual(data['instance_name'], 'Sweep Instance A')
        self.assertTrue(data['status_text'])
        self.assertIs(data.get('url_hidden'), True)
        self.assertNotIn('current_url', data)
        self.assertNotIn('has_token', data)
        self._assert_no_urls(result)

        # Instance B is not visible to this HA User at all.
        result = self._rpc('/odoo_ha_addon/websocket_status', ha_instance_id=self.inst_b.id)
        self.assertFalse(result['success'])
        self.assertNotIn('sweep-b.invalid', json.dumps(result))

    def test_websocket_status_portal_denied(self):
        self.authenticate('sweep_portal_share', PASSWORD)
        result = self._rpc('/odoo_ha_addon/websocket_status', ha_instance_id=self.inst_a.id)
        self.assertFalse(result.get('success'))
        self._assert_no_urls(result)

    def test_websocket_status_manager_keeps_url(self):
        self.authenticate('sweep_manager', PASSWORD)
        result = self._rpc('/odoo_ha_addon/websocket_status', ha_instance_id=self.inst_a.id)
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['current_url'], 'http://sweep-a.invalid:8123')
        self.assertIs(result['data']['has_token'], True)
        self.assertNotIn('url_hidden', result['data'])
