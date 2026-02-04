from datetime import datetime, timedelta, timezone
import logging
import requests
from .utils import to_iso_datetime_time_string
from typing import TypedDict, Optional

_logger = logging.getLogger(__name__)


class HAInfo(TypedDict):
    ha_url: str
    ha_token: str


class HassRestApi:
    """
    Ref url https://developers.home-assistant.io/docs/api/rest/

    多實例模式 REST API 客戶端：
    - instance_id 為必需參數（Fail-fast 原則）
    - 從 ha.instance 讀取該實例的 API 配置
    - 如果實例不存在，直接拋出異常
    """

    ha_token = None
    ha_url = None
    instance_id = None

    def __init__(self, env, instance_id):
        """
        初始化 Home Assistant REST API 客戶端

        Args:
            env: Odoo environment
            instance_id: HA 實例 ID（必需）

        Raises:
            ValueError: 如果 instance_id 未提供或實例不存在
        """
        if not instance_id:
            raise ValueError("instance_id is required for HassRestApi. Multi-instance mode is mandatory.")

        self.env = env
        self.instance_id = instance_id
        self.__refetch_ha_info()

    def __refetch_ha_info(self) -> HAInfo:
        """
        從 ha.instance 獲取 API 配置資訊

        Raises:
            ValueError: 如果實例不存在
        """
        instance = self.env['ha.instance'].sudo().browse(self.instance_id)
        if not instance.exists():
            raise ValueError(f"HA instance with ID {self.instance_id} not found")

        ha_url = instance.api_url
        ha_token = instance.api_token

        self.ha_url = ha_url if ha_url is not None else ""
        self.ha_token = ha_token if ha_token is not None else ""

        _logger.debug(f"Using HA instance '{instance.name}' (ID: {instance.id})")
        return {"ha_url": ha_url, "ha_token": ha_token}

    def get_ha_state(self):
        """
        return
        ```
        [
            {
                "attributes": {},
                "entity_id": "sun.sun",
                "last_changed": "2016-05-30T21:43:32.418320+00:00",
                "state": "below_horizon"
            },
            {
                "attributes": {},
                "entity_id": "process.Dropbox",
                "last_changed": "22016-05-30T21:43:32.418320+00:00",
                "state": "on"
            }
        ]
        ```
        """
        ha_info = self.__refetch_ha_info()
        ha_url = ha_info["ha_url"]
        ha_token = ha_info["ha_token"]

        api_endpoint = "/api/states"

        _logger.debug("ha_url: %s", ha_url)
        # 安全起見，只顯示 token 前綴
        token_prefix = (ha_token[:10] + '...') if (ha_token and isinstance(ha_token, str) and len(ha_token) > 10) else 'None'
        _logger.debug("ha_token: %s", token_prefix)

        url = f"{ha_url}{api_endpoint}"
        _logger.info("URL: %s", url)

        # 發送 GET 請求
        headers = {
            "Authorization": f"Bearer {ha_token}",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers)

        # 檢查回應狀態碼
        if response.status_code == 200:
            # 成功取得資料
            data = response.json()
            _logger.info(f'ha states response data: {data}')
            return data
        else:
            # 處理錯誤
            _logger.error(
                f"HA API request failed: status={response.status_code}, "
                f"url={url}, response={response.text[:500] if response.text else 'empty'}"
            )
            if response.status_code == 401:
                raise ConnectionError(f"HA API authentication failed (401): Invalid or expired access token")
            elif response.status_code == 403:
                raise PermissionError(f"HA API access denied (403): Insufficient permissions")
            elif response.status_code == 404:
                raise ValueError(f"HA API endpoint not found (404): {url}")
            else:
                raise ConnectionError(f"HA API request failed: HTTP {response.status_code}")

    def get_ha_history(self, entity_id: str, timestamp: Optional[datetime] = None, end_timestamp: Optional[datetime] = None):
        """
        若不提供 timestamp 和 end_timestamp, 預設就是抓一天的時間。
        """
        ha_info = self.__refetch_ha_info()
        ha_url = ha_info["ha_url"]
        ha_token = ha_info["ha_token"]

        api_endpoint = "/api/history/period/" if timestamp else "/api/history/period"

        _logger.debug("ha_url: %s", ha_url)
        # 安全起見，只顯示 token 前綴
        token_prefix = (ha_token[:10] + '...') if (ha_token and isinstance(ha_token, str) and len(ha_token) > 10) else 'None'
        _logger.debug("ha_token: %s", token_prefix)

        # 完整的 API URL
        # url = f"{ha_url}{api_endpoint}2024-12-15T16:00:00?filter_entity_id={entity_id}"
        start_time = to_iso_datetime_time_string(timestamp) if timestamp else ''
        url = f"{ha_url}{api_endpoint}{start_time}?filter_entity_id={entity_id}"
        if end_timestamp is not None:
            url += f"&end_time={to_iso_datetime_time_string(end_timestamp)}"
        _logger.info("URL: %s", url)

        # 發送 GET 請求
        headers = {
            "Authorization": f"Bearer {ha_token}",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers)

        # 檢查回應狀態碼
        if response.status_code == 200:
            # 成功取得資料
            data = response.json()
            _logger.info(f'ha history response data: {data}')
            return data
        else:
            # 處理錯誤
            _logger.error(
                f"HA API history request failed: status={response.status_code}, "
                f"url={url}, response={response.text[:500] if response.text else 'empty'}"
            )
            if response.status_code == 401:
                raise ConnectionError(f"HA API authentication failed (401): Invalid or expired access token")
            elif response.status_code == 403:
                raise PermissionError(f"HA API access denied (403): Insufficient permissions")
            elif response.status_code == 404:
                raise ValueError(f"HA API endpoint not found (404): {url}")
            else:
                raise ConnectionError(f"HA API history request failed: HTTP {response.status_code}")