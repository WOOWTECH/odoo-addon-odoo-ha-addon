import odoo
from odoo import models, fields, api
from datetime import datetime, timedelta, timezone
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from .common.utils import parse_domain_from_entitiy_id
from .common.hass_rest_api import HassRestApi
from .common.utils import parse_iso_datetime
from .common.instance_helper import HAInstanceHelper

_logger = logging.getLogger(__name__)


class HAEntityHistory(models.Model):
    _name = 'ha.entity.history'
    _inherit = ['ha.current.instance.filter.mixin']
    _description = 'Home Assistant Entity History'

    domain = fields.Char(string='Domain', required=True)
    entity_state = fields.Char(string='Entity State')
    last_changed = fields.Datetime(string='Last Changed', copy=False)
    last_updated = fields.Datetime(string='Last Updated', copy=False)
    attributes = fields.Json(string='Attributes')

    # 定義計算字段
    num_state = fields.Float(string='Numeric State', compute='_compute_num_state', store=True)

    # Relational
    # 注意，這是 record 的外鍵，不是 HA 的 entity id string
    ha_instance_id = fields.Many2one(
        'ha.instance',
        string='HA Instance',
        related='entity_id.ha_instance_id',
        store=True,
        index=True,
        help='The Home Assistant instance (inherited from entity)'
    )
    entity_id = fields.Many2one('ha.entity', string='Entity', required=True, ondelete='cascade')
    entity_id_string = fields.Char(string='Entity ID', related='entity_id.entity_id', readonly=True)
    entity_name = fields.Char(string='Entity Name', related='entity_id.name', readonly=True)

    @api.depends('entity_state')
    def _compute_num_state(self):
        for record in self:
            try:
                # 將 entity_state 轉換為浮點數，如果 entity_state 是可轉換的
                record.num_state = float(record.entity_state)
            except (ValueError, TypeError):
                # 如果 entity_state 不是數字，則設置為 0 或其他默認值
                record.num_state = -1

    def create_history_records(self, history_data):
        """
        Create history records for a given entity.
        :param history_data: List of history data dictionaries.
        """
        for record in history_data:
            _logger.info(f"Creating history record: {record}")
            self.create({
                'domain': parse_domain_from_entitiy_id(record['entity_id']),
                'entity_id': record['entity_id'],
                'entity_state': record['state'],
                'last_changed': record['last_changed'],
                'last_updated': record['last_updated'],
                'attributes': record['attributes'],
            })

    def _find_entity(self, entity_id: str):
        """
        Find an entity by its ID.
        :param entity_id: The ID of the entity to find.
        :return: The found entity record or None if not found.
        """
        return self.env['ha.entity'].search([('entity_id', '=', entity_id)])

    def _get_current_instance(self):
        """
        取得當前 HA 實例 ID

        使用 HAInstanceHelper 統一實現 (重構後)，支持：
        - Session validation (失效自動清除 + Bus notification)
        - User preference support (res.users.current_ha_instance_id)
        - Bus notifications (失效 + fallback 通知)
        - Comprehensive logging (DEBUG/INFO/WARNING/ERROR)
        - Ordered search (sequence, id)

        3-level fallback 優先順序：
        1. Session 中的 current_ha_instance_id（驗證存在且活躍）
        2. 使用者偏好設定 (res.users.current_ha_instance_id)
        3. 第一個可存取的活躍實例（ordered by sequence, id, filtered by user permissions）

        實現位置：models/common/instance_helper.py::HAInstanceHelper
        重構文檔：docs/tech/instance-helper-refactoring.md

        Returns:
            int: 實例 ID，如果找不到則返回 None
        """
        return HAInstanceHelper.get_current_instance(self.env, logger=_logger)

    def sync_entity_history_from_ha(self, instance_id=None):
        """
        從 Home Assistant 同步實體歷史資料
        優先使用 WebSocket API，失敗時退回 REST API

        Args:
            instance_id: HA 實例 ID（可選，預設使用當前實例）
        """
        _logger.info("=== Starting sync_entity_history_from_ha ===")

        # 取得當前實例
        if not instance_id:
            instance_id = self._get_current_instance()

        if not instance_id:
            _logger.error("No HA instance available")
            return

        instance = self.env['ha.instance'].browse(instance_id)
        _logger.info(f"Syncing history for instance: {instance.name} (ID: {instance_id})")

        # 查詢該實例啟用歷史記錄的實體
        entities = self.env['ha.entity'].search([
            ('enable_record', '=', True),
            ('ha_instance_id', '=', instance_id)
        ])

        if not entities:
            _logger.info(f"No entities with history recording enabled for instance {instance.name}")
            return

        _logger.info(f"Found {len(entities)} entities with history recording enabled for instance {instance.name}")

        # 預先建立 entity_id -> record_id 的映射，避免重複查詢
        entity_map = {entity.entity_id: entity.id for entity in entities}

        # 並行處理所有實體的歷史資料
        total_created = 0
        total_skipped = 0
        total_errors = 0

        # 使用 ThreadPoolExecutor 並行處理（從系統參數讀取 workers 數量，預設 5）
        config_max_workers = int(
            self.env['ir.config_parameter'].sudo().get_param(
                'odoo_ha_addon.ha_history_sync_max_workers', '5'
            )
        )
        max_workers = min(len(entities), config_max_workers)
        _logger.info(f"Processing {len(entities)} entities with {max_workers} parallel workers (config: {config_max_workers})")

        # 預先取得線程安全需要的參數
        db_name = self.env.cr.dbname
        uid = self.env.uid
        context = dict(self.env.context)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任務
            futures = {
                executor.submit(
                    self._fetch_entity_history_threaded,
                    entity.entity_id,
                    entity.id,
                    entity_map,
                    instance_id,
                    db_name,
                    uid,
                    context
                ): entity.entity_id
                for entity in entities
            }

            try:
                # 等待結果，整體 timeout 90 秒（在 WorkerCron 120 秒限制內）
                for future in as_completed(futures, timeout=90):
                    entity_id_str, created, skipped, error = future.result()
                    if error:
                        total_errors += 1
                        _logger.error(f"Failed to fetch history for {entity_id_str}: {error}")
                    else:
                        total_created += created
                        total_skipped += skipped
                        _logger.info(f"Completed {entity_id_str}: {created} created, {skipped} skipped")

            except FuturesTimeoutError:
                _logger.error("Overall timeout (90s) reached, handling remaining tasks")
                # 處理尚未完成的任務
                cancelled_count = 0
                running_count = 0
                for future, entity_id_str in futures.items():
                    if not future.done():
                        # future.cancel() 只能取消尚未開始的任務
                        # 已開始執行的 thread 會繼續運行直到完成（但結果不會被處理）
                        was_cancelled = future.cancel()
                        total_errors += 1
                        if was_cancelled:
                            cancelled_count += 1
                            _logger.warning(f"Cancelled pending task for {entity_id_str}")
                        else:
                            running_count += 1
                            _logger.warning(f"Task for {entity_id_str} still running (will complete in background)")

                if running_count > 0:
                    _logger.warning(
                        f"Note: {running_count} tasks still running in background. "
                        f"Their DB cursors will be released when they complete."
                    )

        _logger.info(f"=== sync_entity_history_from_ha completed ===")
        _logger.info(f"Summary: {total_created} created, {total_skipped} skipped, {total_errors} errors")
        _logger.info(f"Instance: {instance.name} (ID: {instance_id})")

    def fetch_and_store_history(self, instance_id=None):
        """
        從 Home Assistant 取得並儲存歷史資料

        已棄用: 此方法保留以維持向後兼容，請使用 sync_entity_history_from_ha()

        Args:
            instance_id: HA 實例 ID（可選，預設使用當前實例）
        """
        _logger.info("=== fetch_and_store_history called (delegating to sync_entity_history_from_ha) ===")

        # 委派給新的標準方法
        # sudo: 系統層級同步，需要寫入所有用戶可見的歷史記錄
        self.env['ha.entity.history'].sudo().sync_entity_history_from_ha(instance_id=instance_id)

    def _fetch_entity_history(self, entity, entity_map, instance_id):
        """
        取得單一實體的歷史資料

        Args:
            entity: ha.entity record
            entity_map: entity_id -> record_id 映射字典
            instance_id: HA 實例 ID

        Returns:
            tuple: (created_count, skipped_count)
        """
        _logger.info(f"Fetching history for entity: {entity.entity_id} (instance: {instance_id})")

        # 優先嘗試 WebSocket API
        history_data = self._fetch_history_via_websocket(entity.entity_id, instance_id)

        # 若 WebSocket 失敗，退回 REST API
        if history_data is None:
            _logger.info(f"WebSocket failed for {entity.entity_id}, falling back to REST API")
            history_data = self._fetch_history_via_rest(entity.entity_id, instance_id)

        if not history_data:
            _logger.info(f"{entity.entity_id} has no history data")
            return 0, 0

        # 處理歷史資料並儲存
        return self._process_and_store_history(history_data, entity_map)

    def _fetch_entity_history_threaded(self, entity_id_str, entity_record_id, entity_map, instance_id, db_name, uid, context):
        """
        Thread-safe 版本的 _fetch_entity_history
        使用 odoo.registry() 在獨立的 cursor 中執行，確保線程安全

        Args:
            entity_id_str: 實體 ID 字串 (如 "sensor.temperature")
            entity_record_id: ha.entity record ID
            entity_map: entity_id -> record_id 映射字典
            instance_id: HA 實例 ID
            db_name: 資料庫名稱（線程安全需要傳入）
            uid: 使用者 ID
            context: 環境 context

        Returns:
            tuple: (entity_id_str, created_count, skipped_count, error_message)
        """
        try:
            # 使用 odoo.registry() 取得獨立的 registry 和 cursor
            registry = odoo.registry(db_name)
            with registry.cursor() as new_cr:
                new_env = api.Environment(new_cr, uid, context)
                history_model = new_env['ha.entity.history']
                entity = new_env['ha.entity'].browse(entity_record_id)

                created, skipped = history_model._fetch_entity_history(entity, entity_map, instance_id)
                new_cr.commit()
                return (entity_id_str, created, skipped, None)
        except Exception as e:
            _logger.error(f"Thread error for {entity_id_str}: {e}", exc_info=True)
            return (entity_id_str, 0, 0, str(e))

    def _fetch_history_via_websocket(self, entity_id, instance_id):
        """
        使用 WebSocket API 取得歷史資料
        使用 history/stream 訂閱機制

        Args:
            entity_id: 實體 ID
            instance_id: HA 實例 ID

        Returns:
            list or None: 歷史資料，失敗時返回 None
        """
        try:
            from odoo.addons.odoo_ha_addon.models.common.websocket_client import get_websocket_client

            client = get_websocket_client(self.env, instance_id=instance_id)

            # 使用 history/stream 訂閱API
            today = datetime.now()
            yesterday = today - timedelta(days=1)

            _logger.info(f"Subscribing to history/stream for {entity_id}")

            # 使用訂閱方法（會自動收集事件並取消訂閱）
            result = client.subscribe_history_stream(
                entity_ids=[entity_id],
                start_time=yesterday.isoformat(),
                end_time=today.isoformat(),
                timeout=60  # 60 秒 timeout
            )

            if result['success']:
                events = result['data']

                # 處理空事件列表
                if not events:
                    _logger.info(f"WebSocket history stream successful for {entity_id}, but received 0 events")
                    return None

                _logger.info(f"WebSocket history stream successful for {entity_id}, received {len(events)} events")

                # 轉換事件格式為歷史資料格式
                return self._convert_stream_events_to_history(events, entity_id)
            else:
                _logger.warning(f"WebSocket history stream failed for {entity_id}: {result.get('error')}")
                return None

        except Exception as e:
            _logger.warning(f"WebSocket history query failed for {entity_id}: {e}")
            return None

    def _normalize_state_format(self, state_item, entity_id):
        """
        標準化狀態項目格式（處理 HA WebSocket API 的縮寫格式）

        HA WebSocket API 可能返回縮寫格式：
        {'s': 'on', 'a': {...}, 'lu': 1761002858.785457, 'lc': 1761002858.785457}

        需要轉換為完整格式：
        {'state': 'on', 'attributes': {...}, 'last_updated': '2025-10-21T...', 'last_changed': '...'}

        Args:
            state_item: 狀態項目（可能是縮寫或完整格式）
            entity_id: 實體 ID（用於日誌）

        Returns:
            dict or None: 標準化後的狀態項目，失敗時返回 None
        """
        if not isinstance(state_item, dict):
            return None

        # 檢測是否為縮寫格式（'s' 欄位存在）
        if 's' in state_item:
            # 縮寫格式轉換
            try:
                normalized = {
                    'state': state_item.get('s'),
                    'attributes': state_item.get('a', {}),
                    'entity_id': entity_id,
                }

                # 轉換 Unix timestamp 為 ISO 格式
                if 'lu' in state_item:
                    normalized['last_updated'] = datetime.fromtimestamp(
                        state_item['lu'], tz=timezone.utc
                    ).isoformat()

                if 'lc' in state_item:
                    normalized['last_changed'] = datetime.fromtimestamp(
                        state_item['lc'], tz=timezone.utc
                    ).isoformat()
                else:
                    # 如果沒有 last_changed，使用 last_updated
                    normalized['last_changed'] = normalized.get('last_updated')

                _logger.debug(f"Converted abbreviated format for {entity_id}: {state_item['s']}")
                return normalized

            except Exception as e:
                _logger.error(f"Failed to convert abbreviated format for {entity_id}: {e}")
                return None

        # 完整格式（REST API 或已標準化格式）
        elif 'state' in state_item:
            # 確保包含 entity_id
            if 'entity_id' not in state_item:
                state_item['entity_id'] = entity_id
            return state_item

        else:
            # 無法識別的格式
            return None

    def _convert_stream_events_to_history(self, events, entity_id):
        """
        將 history/stream 事件轉換為歷史資料格式

        根據文件，每個事件格式：
        {
          "states": {
            "entity_id": [
              {"state": "...", "last_changed": "...", ...}
            ]
          },
          "start_time": 1760957597.057,  // Unix timestamp (秒)
          "end_time": 1761043997.057
        }

        實際上 HA WebSocket API 返回的是縮寫格式：
        {"states": {"entity_id": [{"s": "on", "a": {...}, "lu": 123.456, "lc": 123.456}]}}

        Args:
            events: history/stream 返回的事件列表
            entity_id: 實體 ID

        Returns:
            list: 轉換後的歷史資料（與 REST API 格式相同）[[...]]
        """
        if not events:
            _logger.debug(f"No events received for {entity_id}")
            return None

        history_records = []

        for event in events:
            states = event.get('states', {})

            # 檢查 states 是否為空（該時段內無狀態變化）
            if not states:
                _logger.debug(f"Empty states in event for {entity_id}")
                continue

            # states 是一個字典，key 是 entity_id
            if entity_id in states:
                state_list = states[entity_id]

                # state_list 是該實體的狀態列表
                if isinstance(state_list, list):
                    for state_item in state_list:
                        # 確保 state_item 包含必要欄位
                        if isinstance(state_item, dict):
                            # 處理縮寫格式（HA WebSocket API 返回）或完整格式（REST API）
                            normalized_item = self._normalize_state_format(state_item, entity_id)
                            if normalized_item:
                                history_records.append(normalized_item)
                            else:
                                _logger.warning(f"Invalid state item format: {state_item}")
                else:
                    _logger.warning(f"state_list is not a list: {type(state_list)}")
            else:
                # entity_id 不在 states 中，記錄警告
                available_entities = list(states.keys())
                _logger.debug(
                    f"Entity {entity_id} not found in states. "
                    f"Available entities: {available_entities}"
                )

        if not history_records:
            _logger.warning(
                f"No valid history records extracted from {len(events)} events for {entity_id}"
            )
            return None

        _logger.info(f"Converted {len(history_records)} history records for {entity_id}")

        # 返回與 REST API 相同的格式：[[...]]
        return [history_records]

    def _fetch_history_via_rest(self, entity_id, instance_id):
        """
        使用 REST API 取得歷史資料

        Args:
            entity_id: 實體 ID
            instance_id: HA 實例 ID

        Returns:
            list: 歷史資料
        """
        try:
            api = HassRestApi(self.env, instance_id=instance_id)
            # 預設取得近一天的歷史資料
            history_data = api.get_ha_history(entity_id)

            if history_data:
                _logger.info(f"REST API history query successful for {entity_id}")

            return history_data

        except Exception as e:
            _logger.error(f"REST API history query failed for {entity_id}: {e}")
            raise

    def _process_and_store_history(self, history_data, entity_map):
        """
        處理並儲存歷史資料

        Args:
            history_data: 從 API 取得的歷史資料
            entity_map: entity_id -> record_id 映射字典

        Returns:
            tuple: (created_count, skipped_count)
        """
        if not history_data or not isinstance(history_data, list) or len(history_data) == 0:
            return 0, 0

        # 歷史資料的第一層是實體陣列
        first_entity_history = history_data[0]

        if not first_entity_history:
            return 0, 0

        # 準備要建立的記錄
        records_to_create = []

        for history_item in first_entity_history:
            entity_id_str = history_item.get('entity_id')

            # 使用預先建立的映射查詢 entity record id
            entity_record_id = entity_map.get(entity_id_str)

            if not entity_record_id:
                _logger.warning(f"Entity {entity_id_str} not found in entity map, skipping")
                continue

            # 解析時間戳
            try:
                last_changed = parse_iso_datetime(history_item.get('last_changed'))
                last_updated = parse_iso_datetime(history_item.get('last_updated'))
            except Exception as e:
                _logger.error(f"Failed to parse timestamp for {entity_id_str}: {e}")
                continue

            record_data = {
                'domain': parse_domain_from_entitiy_id(entity_id_str),
                'entity_id': entity_record_id,
                'entity_state': history_item.get('state'),
                'last_changed': last_changed,
                'last_updated': last_updated,
                'attributes': history_item.get('attributes', {}),
            }

            records_to_create.append(record_data)

        # 批次去重並建立記錄
        return self._batch_create_deduplicated(records_to_create)

    def _batch_create_deduplicated(self, records):
        """
        批次建立記錄，自動去除重複項

        Args:
            records: 要建立的記錄列表

        Returns:
            tuple: (created_count, skipped_count)
        """
        if not records:
            return 0, 0

        created_count = 0
        skipped_count = 0

        # 收集所有需要檢查的 (entity_id, last_updated) 組合
        check_pairs = [(r['entity_id'], r['last_updated']) for r in records]

        # 批次查詢已存在的記錄（提升效能）
        existing_records = set()
        for entity_id, last_updated in check_pairs:
            exists = self.env[self._name].search([
                ('entity_id', '=', entity_id),
                ('last_updated', '=', last_updated)
            ], limit=1)

            if exists:
                existing_records.add((entity_id, last_updated))

        # 批次建立不存在的記錄
        for record in records:
            pair = (record['entity_id'], record['last_updated'])

            if pair in existing_records:
                skipped_count += 1
                _logger.debug(f"Record already exists, skipping: entity={record['entity_id']}, updated={record['last_updated']}")
            else:
                try:
                    self.env[self._name].create(record)
                    created_count += 1
                    _logger.debug(f"Record created: entity={record['entity_id']}, updated={record['last_updated']}")
                except Exception as e:
                    _logger.error(f"Failed to create record: {e}")
                    skipped_count += 1

        _logger.info(f"Batch create completed: {created_count} created, {skipped_count} skipped")
        return created_count, skipped_count
