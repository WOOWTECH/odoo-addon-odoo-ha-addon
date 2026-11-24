# -*- coding: utf-8 -*-
# Part of odoo_ha_addon. See LICENSE file for full copyright and licensing details.
"""
Home Assistant without Supervisor (Container / Core installs, e.g. Docker or
Kubernetes) answers `supervisor/api` with `unknown_command`.

- The hardware / network routes must turn that into a clear
  `supervisor_unavailable` answer instead of a red error.
- A failed WebSocket request must never carry the Python traceback back to
  the browser; Home Assistant's error code is kept.

Home Assistant is never contacted: the WebSocket client is mocked.
"""
import asyncio
import json
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.odoo_ha_addon.models.common import websocket_client
from odoo.addons.odoo_ha_addon.models.common.hass_websocket_service import (
    HassCommandError,
    HassWebSocketService,
)

from .test_security_sweep_20261107 import PASSWORD, _ControllerCase, _HAFixtureMixin

SERVICE_LOGGER = 'odoo.addons.odoo_ha_addon.models.common.hass_websocket_service'


@tagged('post_install', '-at_install', 'ha_supervisor')
class TestSupervisorUnavailableRoutes(_ControllerCase):

    def setUp(self):
        super().setUp()
        self.supervisor_reply = {
            'success': False, 'error': 'Unknown command.', 'error_code': 'unknown_command',
        }
        client = websocket_client.get_websocket_client.return_value
        base = client.call_websocket_api.side_effect

        def call_websocket_api(message_type, payload=None, timeout=15):
            if message_type == 'supervisor/api':
                self.ws_calls.append((message_type, payload))
                return dict(self.supervisor_reply)
            return base(message_type, payload, timeout)

        client.call_websocket_api.side_effect = call_websocket_api

    def test_hardware_and_network_info_without_supervisor(self):
        self.authenticate('sweep_manager', PASSWORD)
        for route in ('/odoo_ha_addon/hardware_info', '/odoo_ha_addon/network_info'):
            result = self._rpc(route, ha_instance_id=self.inst_a.id)
            self.assertFalse(result['success'])
            self.assertEqual(result['error_type'], 'supervisor_unavailable')
            self.assertIn('Supervisor', result['error'])
            self.assertNotIn('Unknown command', result['error'])
        self.assertEqual(
            [p['endpoint'] for t, p in self.ws_calls if t == 'supervisor/api'],
            ['/hardware/info', '/network/info'])

    def test_other_supervisor_errors_stay_errors(self):
        self.supervisor_reply = {'success': False, 'error': 'Unauthorized', 'error_code': 'unauthorized'}
        self.authenticate('sweep_manager', PASSWORD)
        result = self._rpc('/odoo_ha_addon/hardware_info', ha_instance_id=self.inst_a.id)
        self.assertEqual(result, {'success': False, 'error': 'Unauthorized'})

    def test_supervisor_reply_still_returned(self):
        self.supervisor_reply = {'success': True, 'data': {'devices': [], 'drives': []}}
        self.authenticate('sweep_manager', PASSWORD)
        result = self._rpc('/odoo_ha_addon/network_info', ha_instance_id=self.inst_a.id)
        self.assertEqual(result, {'success': True, 'data': {'devices': [], 'drives': []}})


@tagged('post_install', '-at_install', 'ha_supervisor')
class TestRequestErrorsCarryNoTraceback(_HAFixtureMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_ha_fixture()

    def _service(self):
        return HassWebSocketService(
            db_name=self.env.cr.dbname, ha_url='http://sweep-a.invalid:8123',
            ha_token='sweep-token-a-0123456789', instance_id=self.inst_a.id)

    def _run_queue_once(self, error):
        """Run one pass of the request queue with send_request raising `error`."""
        service = self._service()
        service._running = True
        failed = []

        async def run_sync(func, *args):
            return func(*args)

        def pending():
            service._running = False  # a single pass
            return [{
                'id': 1, 'request_id': 'sup-1', 'message_type': 'supervisor/api',
                'payload': json.dumps({'endpoint': '/hardware/info', 'method': 'get'}),
                'is_subscription': False,
            }]

        with patch.object(service, '_run_sync', side_effect=run_sync), \
                patch.object(service, '_get_pending_requests', side_effect=pending), \
                patch.object(service, '_mark_request_processing'), \
                patch.object(service, '_cleanup_stale_subscriptions'), \
                patch.object(service, 'send_request', side_effect=error), \
                patch.object(service, '_mark_request_failed',
                             side_effect=lambda *args: failed.append(args)):
            asyncio.run(service._process_request_queue())
        return failed

    def test_ha_error_reply_keeps_code(self):
        service = self._service()

        async def scenario():
            future = asyncio.get_running_loop().create_future()
            service._pending_requests[7] = future
            await service._handle_message({
                'id': 7, 'type': 'result', 'success': False,
                'error': {'code': 'unknown_command', 'message': 'Unknown command.'},
            })
            return future

        with self.assertLogs(SERVICE_LOGGER, level='ERROR'):
            future = asyncio.run(scenario())
        error = future.exception()
        self.assertIsInstance(error, HassCommandError)
        self.assertEqual(error.code, 'unknown_command')
        self.assertEqual(str(error), 'Unknown command.')

    def test_ha_rejection_stored_with_code(self):
        with self.assertLogs(SERVICE_LOGGER, level='WARNING') as logs:
            failed = self._run_queue_once(HassCommandError('Unknown command.', 'unknown_command'))
        self.assertEqual(failed, [(1, 'Unknown command.', 'unknown_command')])
        self.assertNotIn('Traceback', '\n'.join(logs.output))

    def test_crash_stored_without_traceback(self):
        with self.assertLogs(SERVICE_LOGGER, level='ERROR') as logs:
            failed = self._run_queue_once(RuntimeError('boom'))
        self.assertEqual(failed, [(1, 'boom')])
        # the traceback is still in the server log
        self.assertIn('Traceback', '\n'.join(logs.output))

    def test_client_returns_error_code(self):
        Queue = self.env['ha.ws.request.queue'].sudo()
        client = websocket_client.WebSocketClient(self.env, instance_id=self.inst_a.id)
        for values, expected in (
            ({'error': 'Unknown command.', 'error_code': 'unknown_command'},
             {'success': False, 'error': 'Unknown command.', 'error_code': 'unknown_command'}),
            ({'error': 'boom'}, {'success': False, 'error': 'boom'}),
        ):
            request = Queue.create(dict(values, request_id='sup-2', message_type='supervisor/api',
                                        state='failed', ha_instance_id=self.inst_a.id))
            with patch.object(self.env.cr, 'commit'), \
                    self.assertLogs('odoo.addons.odoo_ha_addon.models.common.websocket_client', level='ERROR'):
                result = client._wait_for_result(request, 'sup-2', timeout=2)
            self.assertEqual(result, expected)
            self.assertFalse(request.exists())
