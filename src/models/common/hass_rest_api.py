from datetime import datetime, timedelta, timezone
import logging
import requests
from .utils import to_iso_datetime_time_string
from typing import TypedDict, Optional

_logger = logging.getLogger(__name__)

# Default timeout for HTTP requests (in seconds)
# Prevents blocking if HA server is unreachable or slow
DEFAULT_TIMEOUT = 10


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
        response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)

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

    def call_service(self, domain: str, service: str, service_data: dict = None, target: dict = None):
        """
        Call a Home Assistant service via REST API.

        REST API endpoint: POST /api/services/<domain>/<service>

        Args:
            domain: Service domain (e.g., 'scene', 'light', 'switch')
            service: Service name (e.g., 'create', 'turn_on', 'turn_off')
            service_data: Optional service data dictionary
            target: Optional target dict (e.g., {'entity_id': 'light.bedroom'})

        Returns:
            list: Array of state objects that changed as a result

        Raises:
            ConnectionError: If API request fails
        """
        ha_info = self.__refetch_ha_info()
        ha_url = ha_info["ha_url"]
        ha_token = ha_info["ha_token"]

        api_endpoint = f"/api/services/{domain}/{service}"
        url = f"{ha_url}{api_endpoint}"

        _logger.info(f"Calling HA service: {domain}.{service}")
        _logger.debug(f"URL: {url}")

        headers = {
            "Authorization": f"Bearer {ha_token}",
            "Content-Type": "application/json",
        }

        # Build payload
        payload = {}
        if service_data:
            payload.update(service_data)
        if target:
            payload.update(target)

        _logger.debug(f"Service payload: {payload}")

        response = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)

        if response.status_code == 200:
            data = response.json()
            _logger.info(f"Service {domain}.{service} called successfully")
            return data
        else:
            _logger.error(
                f"HA service call failed: status={response.status_code}, "
                f"url={url}, response={response.text[:500] if response.text else 'empty'}"
            )
            if response.status_code == 401:
                raise ConnectionError(f"HA API authentication failed (401): Invalid or expired access token")
            elif response.status_code == 403:
                raise PermissionError(f"HA API access denied (403): Insufficient permissions")
            elif response.status_code == 404:
                raise ValueError(f"HA service not found (404): {domain}.{service}")
            else:
                raise ConnectionError(f"HA service call failed: HTTP {response.status_code}")

    def create_scene_config(self, ha_scene_id: str, name: str, entities: dict, icon: str = None):
        """
        Create or update a scene in Home Assistant's scenes.yaml via config API.

        This creates a scene that is editable in the HA GUI, unlike scene.create service
        which creates dynamic/runtime scenes.

        REST API endpoint: POST /api/config/scene/config/{ha_scene_id}

        IMPORTANT: The ha_scene_id must be a numeric timestamp string (e.g., '1578926818642')
        to match how HA frontend creates scenes. This ensures scenes are editable in HA GUI.

        Args:
            ha_scene_id: Numeric timestamp ID for HA config (e.g., '1709123456789')
                         This is NOT the entity_id, but a unique numeric identifier.
            name: Display name for the scene
            entities: Dict of entity_id -> state/attributes to set
                      e.g., {'light.bedroom': {'state': 'on', 'brightness': 128}}
            icon: Optional icon (e.g., 'mdi:lightbulb')

        Returns:
            dict: Response from HA API containing the result

        Raises:
            ConnectionError: If API request fails
        """
        ha_info = self.__refetch_ha_info()
        ha_url = ha_info["ha_url"]
        ha_token = ha_info["ha_token"]

        api_endpoint = f"/api/config/scene/config/{ha_scene_id}"
        url = f"{ha_url}{api_endpoint}"

        _logger.info(f"Creating scene config: ha_scene_id={ha_scene_id}, name={name}")
        _logger.debug(f"URL: {url}")

        headers = {
            "Authorization": f"Bearer {ha_token}",
            "Content-Type": "application/json",
        }

        # Build metadata to mark all entities as entity_only
        # This ensures entities are displayed in the "Entities" section of HA scene editor
        # instead of being grouped by device in the "Devices" section
        metadata = {}
        for entity_id in entities.keys():
            metadata[entity_id] = {"entity_only": True}

        # Build scene config payload matching HA frontend format
        # NOTE: Do NOT include 'id' in payload body - HA frontend doesn't send it
        # The id is only in the URL path, not in the request body
        # Including 'id' in body causes HA to strip the metadata field
        payload = {
            "name": name,
            "entities": entities,
            "metadata": metadata
        }
        if icon:
            payload["icon"] = icon

        _logger.debug(f"Scene config payload: {payload}")

        response = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)

        if response.status_code == 200:
            data = response.json()
            _logger.info(f"Scene config {ha_scene_id} ({name}) created/updated successfully")
            return data
        else:
            _logger.error(
                f"HA scene config failed: status={response.status_code}, "
                f"url={url}, response={response.text[:500] if response.text else 'empty'}"
            )
            if response.status_code == 401:
                raise ConnectionError(f"HA API authentication failed (401): Invalid or expired access token")
            elif response.status_code == 403:
                raise PermissionError(f"HA API access denied (403): Insufficient permissions")
            elif response.status_code == 404:
                raise ValueError(f"HA config API not found (404): {api_endpoint}")
            else:
                raise ConnectionError(f"HA scene config failed: HTTP {response.status_code}")

    def delete_scene_config(self, ha_scene_id: str):
        """
        Delete a scene from Home Assistant's scenes.yaml via config API.

        REST API endpoint: DELETE /api/config/scene/config/{ha_scene_id}

        Args:
            ha_scene_id: Numeric timestamp ID of the scene to delete
                         (same ID used when creating the scene)

        Returns:
            dict: Response from HA API

        Raises:
            ConnectionError: If API request fails
        """
        ha_info = self.__refetch_ha_info()
        ha_url = ha_info["ha_url"]
        ha_token = ha_info["ha_token"]

        api_endpoint = f"/api/config/scene/config/{ha_scene_id}"
        url = f"{ha_url}{api_endpoint}"

        _logger.info(f"Deleting scene config: ha_scene_id={ha_scene_id}")

        headers = {
            "Authorization": f"Bearer {ha_token}",
            "Content-Type": "application/json",
        }

        response = requests.delete(url, headers=headers, timeout=DEFAULT_TIMEOUT)

        if response.status_code == 200:
            _logger.info(f"Scene config {ha_scene_id} deleted successfully")
            return response.json() if response.text else {}
        else:
            _logger.error(
                f"HA scene config delete failed: status={response.status_code}, "
                f"url={url}, response={response.text[:500] if response.text else 'empty'}"
            )
            raise ConnectionError(f"HA scene config delete failed: HTTP {response.status_code}")

    def get_scene_entity_id_by_config_id(self, ha_scene_id: str) -> str:
        """
        Get the entity_id of a scene by its config ID (ha_scene_id).

        HA generates entity_id based on the scene name when creating via config API.
        This method queries all states and finds the scene with matching 'id' attribute.

        Args:
            ha_scene_id: Numeric timestamp ID used when creating the scene

        Returns:
            str: The entity_id (e.g., 'scene.living_room') or None if not found
        """
        ha_info = self.__refetch_ha_info()
        ha_url = ha_info["ha_url"]
        ha_token = ha_info["ha_token"]

        url = f"{ha_url}/api/states"
        headers = {
            "Authorization": f"Bearer {ha_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            if response.status_code == 200:
                states = response.json()
                # Find scene with matching 'id' attribute
                for state in states:
                    if state.get('entity_id', '').startswith('scene.'):
                        attrs = state.get('attributes', {})
                        if str(attrs.get('id')) == str(ha_scene_id):
                            entity_id = state.get('entity_id')
                            _logger.debug(f"Found scene entity_id '{entity_id}' for config_id '{ha_scene_id}'")
                            return entity_id
                _logger.warning(f"No scene found with config_id '{ha_scene_id}'")
                return None
            else:
                _logger.error(f"Failed to fetch states: HTTP {response.status_code}")
                return None
        except Exception as e:
            _logger.error(f"Error fetching scene entity_id: {e}")
            return None

    def get_entity_states(self, entity_ids: list):
        """
        Get current states of multiple entities using a single API call.

        Optimized to fetch all states at once and filter locally,
        instead of making individual HTTP requests for each entity.

        Args:
            entity_ids: List of entity IDs to fetch

        Returns:
            dict: entity_id -> state dict mapping
        """
        if not entity_ids:
            return {}

        # Fetch all states with a single API call
        try:
            all_states = self.get_ha_state()
        except Exception as e:
            _logger.error(f"Failed to fetch all states from HA: {e}")
            # Return defaults for all requested entities
            return {eid: {"state": "on"} for eid in entity_ids}

        # Build a lookup map from the fetched states
        states_map = {state['entity_id']: state for state in all_states}

        # Extract requested entity states
        result = {}
        for entity_id in entity_ids:
            if entity_id in states_map:
                data = states_map[entity_id]
                # Build entity state dict for scene
                state_dict = {"state": data.get("state", "on")}
                attrs = data.get("attributes", {})
                # Include relevant attributes based on domain
                domain = entity_id.split(".")[0]
                if domain == "light":
                    for key in ["brightness", "color_temp", "rgb_color", "hs_color", "xy_color"]:
                        if key in attrs:
                            state_dict[key] = attrs[key]
                elif domain == "cover":
                    if "current_position" in attrs:
                        state_dict["position"] = attrs["current_position"]
                elif domain == "climate":
                    for key in ["temperature", "target_temp_high", "target_temp_low", "hvac_mode"]:
                        if key in attrs:
                            state_dict[key] = attrs[key]
                elif domain == "fan":
                    for key in ["percentage", "preset_mode", "oscillating"]:
                        if key in attrs:
                            state_dict[key] = attrs[key]
                result[entity_id] = state_dict
            else:
                _logger.warning(f"Entity {entity_id} not found in HA states, using default")
                result[entity_id] = {"state": "on"}  # Default fallback

        return result

    def get_scene_config_id(self, entity_id: str) -> Optional[str]:
        """
        Get the config ID (ha_scene_id) for a scene from HA.

        This queries the scene's state to get the 'id' attribute which is
        the numeric timestamp ID used by HA for scene configuration.

        Note: The scene state contains an 'id' field in attributes only for
        scenes created via the UI editor (stored in scenes.yaml).

        Args:
            entity_id: Scene entity ID (e.g., 'scene.movie_mode')

        Returns:
            str: The scene's config ID if found, None otherwise
        """
        ha_info = self.__refetch_ha_info()
        ha_url = ha_info["ha_url"]
        ha_token = ha_info["ha_token"]

        # First, get the scene's state to check if it has an 'id' in attributes
        url = f"{ha_url}/api/states/{entity_id}"
        headers = {
            "Authorization": f"Bearer {ha_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                attributes = data.get('attributes', {})
                # The 'id' field is only present for scenes created via UI editor
                scene_id = attributes.get('id')
                if scene_id:
                    _logger.debug(f"Found scene config id for {entity_id}: {scene_id}")
                    return str(scene_id)
                else:
                    _logger.debug(f"Scene {entity_id} has no 'id' attribute (may be YAML-only scene)")
                    return None
            else:
                _logger.warning(f"Failed to get scene state for {entity_id}: HTTP {response.status_code}")
                return None
        except Exception as e:
            _logger.warning(f"Error getting scene config id for {entity_id}: {e}")
            return None

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
        response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)

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