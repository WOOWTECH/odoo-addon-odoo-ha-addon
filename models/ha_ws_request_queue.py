from odoo import models, fields, api
import logging
import json

_logger = logging.getLogger(__name__)


class HAWebSocketRequestQueue(models.Model):
    """
    Home Assistant WebSocket 請求隊列
    用於跨 process 通訊：Controller -> Queue Job Worker
    支持一般請求和訂閱請求
    """
    _name = 'ha.ws.request.queue'
    _description = 'Home Assistant WebSocket Request Queue'
    _order = 'create_date asc'

    ha_instance_id = fields.Many2one(
        'ha.instance',
        string='HA Instance',
        index=True,
        ondelete='cascade',
        help='The Home Assistant instance this request is for (optional for now, required in future)'
    )
    request_id = fields.Char(string='Request ID', required=True, index=True, copy=False)
    message_type = fields.Char(string='Message Type', required=True)
    payload = fields.Text(string='Payload')  # JSON string

    # 訂閱相關欄位
    is_subscription = fields.Boolean(string='Is Subscription', default=False)
    subscription_id = fields.Integer(string='Subscription ID', copy=False, help='Home Assistant 返回的訂閱 ID')
    events = fields.Text(string='Events', help='收集的事件（JSON 陣列）')
    event_count = fields.Integer(string='Event Count', default=0)

    state = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('subscribed', 'Subscribed'),  # 新增：訂閱中
        ('collecting', 'Collecting'),  # 新增：收集事件中
        ('done', 'Done'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout')
    ], string='State', default='pending', required=True, index=True)

    result = fields.Text(string='Result')  # JSON string
    error = fields.Text(string='Error Message')

    create_date = fields.Datetime(string='Created At', readonly=True)
    write_date = fields.Datetime(string='Updated At', readonly=True)

    def add_event(self, event_data):
        """
        添加事件到訂閱請求

        Args:
            event_data: 事件數據（dict）
        """
        self.ensure_one()

        if not self.is_subscription:
            _logger.warning(f"Request {self.request_id} is not a subscription, cannot add event")
            return

        # 解析現有事件
        events = json.loads(self.events) if self.events else []

        # 添加新事件
        events.append(event_data)

        # 更新記錄
        self.write({
            'events': json.dumps(events),
            'event_count': len(events),
            'state': 'collecting'
        })

        _logger.debug(f"Added event to subscription {self.request_id}, total events: {len(events)}")

    def complete_subscription(self):
        """
        完成訂閱，將收集的事件作為結果
        """
        self.ensure_one()

        if not self.is_subscription:
            _logger.warning(f"Request {self.request_id} is not a subscription")
            return

        # 將收集的事件設為結果
        events = json.loads(self.events) if self.events else []

        self.write({
            'result': json.dumps(events),
            'state': 'done'
        })

        _logger.info(f"Subscription {self.request_id} completed with {len(events)} events")

    @api.model
    def cleanup_old_requests(self):
        """
        清理超過 1 小時的舊請求
        """
        from datetime import datetime, timedelta

        one_hour_ago = datetime.now() - timedelta(hours=1)
        old_requests = self.search([
            ('create_date', '<', one_hour_ago)
        ])

        if old_requests:
            count = len(old_requests)
            old_requests.unlink()
            _logger.info(f"Cleaned up {count} old WebSocket requests")
