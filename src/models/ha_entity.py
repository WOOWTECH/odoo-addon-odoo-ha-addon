from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError
import logging
import json
from .common.utils import parse_iso_datetime, parse_domain_from_entitiy_id
from .common.hass_rest_api import HassRestApi

_logger = logging.getLogger(__name__)


class HAEntity(models.Model):
    _name = 'ha.entity'
    _inherit = ['ha.current.instance.filter.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Home Assistant Entity'

    # SQL Constraints
    _sql_constraints = [
        ('entity_instance_unique',
         'unique(entity_id, ha_instance_id)',
         'Entity ID must be unique per HA instance')
    ]

    entity_id = fields.Char(string='Entity ID', required=True, index=True, copy=False)
    domain = fields.Char(string='Domain', required=True)
    name = fields.Char(string='Name')
    entity_state = fields.Char(string='Entity State')
    last_changed = fields.Datetime(string='Last Changed', copy=False)
    attributes = fields.Json(string='Attributes')
    attributes_str = fields.Text(
        string='Attributes (JSON)',
        compute='_compute_attributes_str',
        inverse='_inverse_attributes_str',
        store=False
    )
    enable_record = fields.Boolean(
        string='Enable Record',
        default=False,
        tracking=True
    )

    # Relational
    ha_instance_id = fields.Many2one(
        'ha.instance',
        string='HA Instance',
        required=True,
        index=True,
        ondelete='cascade',
        help='The Home Assistant instance this entity belongs to'
    )
    area_id = fields.Many2one('ha.area', string='Area', index=True, ondelete='set null')
    follows_device_area = fields.Boolean(
        string='Follows Device Area',
        default=False,
        help='If checked, entity area follows its device area (synced from HA)'
    )
    display_area_id = fields.Many2one(
        'ha.area',
        string='Display Area',
        compute='_compute_display_area_id',
        store=False,
        help='Actual area shown: own area or device area if follows_device_area is True'
    )
    device_id = fields.Many2one(
        'ha.device',
        string='Device',
        index=True,
        ondelete='cascade',
        domain="[('ha_instance_id', '=', ha_instance_id)]",
        help='The device this entity belongs to (synced from HA, read-only)'
    )
    history_ids = fields.One2many('ha.entity.history', 'entity_id', string='History Records')

    # One2many relationship with ha.entity.share
    share_ids = fields.One2many(
        'ha.entity.share',
        'entity_id',
        string='Shares',
        help='Share records for this entity',
        groups='odoo_ha_addon.group_ha_manager'
    )

    # Many2many relationship with ha.entity.group
    group_ids = fields.Many2many(
        'ha.entity.group',
        'ha_entity_group_entity_rel',  # 關聯表名稱（必須與 ha_entity_group 相同）
        'entity_id',                    # 此 model 的 ID 欄位
        'group_id',                     # ha.entity.group 的 ID 欄位
        string='Groups',
        help='Entity groups this entity belongs to',
        tracking=True
    )

    # Many2many relationship with ha.label
    label_ids = fields.Many2many(
        'ha.label',
        'ha_entity_label_rel',
        'entity_id',
        'label_id',
        string='Labels',
        domain="[('ha_instance_id', '=', ha_instance_id)]",
        help='Entity labels for categorization (synced with HA)'
    )

    # Many2many relationship with ha.entity.tag
    tag_ids = fields.Many2many(
        'ha.entity.tag',
        'ha_entity_tag_rel',  # 關聯表名稱（必須與 ha_entity_tag 相同）
        'entity_id',          # 此 model 的 ID 欄位
        'tag_id',             # ha.entity.tag 的 ID 欄位
        string='Tags',
        help='Tags for this entity',
        tracking=True
    )
    tag_count = fields.Integer(
        string='Tag Count',
        compute='_compute_tag_count',
        help='Number of tags'
    )

    @api.depends('tag_ids')
    def _compute_tag_count(self):
        for entity in self:
            entity.tag_count = len(entity.tag_ids)

    @api.depends('area_id', 'follows_device_area', 'device_id.area_id')
    def _compute_display_area_id(self):
        """
        Compute the actual area to display.
        If follows_device_area is True and entity has a device, use device's area.
        Otherwise, use entity's own area_id.
        """
        for entity in self:
            if entity.follows_device_area and entity.device_id:
                entity.display_area_id = entity.device_id.area_id
            else:
                entity.display_area_id = entity.area_id

    # Text field for user notes
    note = fields.Text(
        string='Note',
        groups='odoo_ha_addon.group_ha_user',
        help='Internal notes for this entity'
    )

    # Custom properties - definition is stored in ha.instance
    properties = fields.Properties(
        'Properties',
        definition='ha_instance_id.entity_properties_definition',
        copy=True,
        help='Custom properties for this entity (defined at instance level)'
    )

    # 允許用戶修改的欄位（其他欄位只能由系統 sudo() 修改）
    # - enable_record: 啟用歷史記錄
    # - area_id: Entity 所屬區域（雙向同步到 HA）
    # - name: Entity 顯示名稱（雙向同步到 HA Entity Registry）
    #   注意：此 name 會同步到 HA Entity Registry 的 name 欄位，
    #   HA 會根據此值計算出 state attributes 中的 friendly_name
    # - label_ids: Entity 標籤（雙向同步到 HA Entity Registry）
    # - tag_ids: Entity 標籤（Odoo 內部分類，不同步到 HA）
    # - note: 使用者備註
    _USER_EDITABLE_FIELDS = {'enable_record', 'area_id', 'follows_device_area', 'name', 'label_ids', 'tag_ids', 'note', 'properties'}

    @api.constrains('ha_instance_id', 'group_ids', 'tag_ids')
    def _check_instance_consistency(self):
        """
        確保實體關聯的所有群組和標籤都屬於同一個 HA 實例
        這是資料完整性的關鍵約束
        """
        for entity in self:
            # 檢查所有群組是否屬於同一實例
            if entity.group_ids:
                mismatched_groups = entity.group_ids.filtered(
                    lambda g: g.ha_instance_id.id != entity.ha_instance_id.id
                )
                if mismatched_groups:
                    group_names = ', '.join(mismatched_groups.mapped('name')[:3])
                    if len(mismatched_groups) > 3:
                        group_names += _(' (and %d more)') % (len(mismatched_groups) - 3)
                    raise ValidationError(
                        _('Entity "%s" belongs to instance "%s",\n'
                          'but the following groups belong to different instances: %s\n'
                          'An entity can only join groups from the same instance.') % (
                              entity.name or entity.entity_id,
                              entity.ha_instance_id.name,
                              group_names
                          )
                    )

            # 檢查所有標籤是否屬於同一實例
            if entity.tag_ids:
                mismatched_tags = entity.tag_ids.filtered(
                    lambda t: t.ha_instance_id.id != entity.ha_instance_id.id
                )
                if mismatched_tags:
                    tag_names = ', '.join(mismatched_tags.mapped('name')[:3])
                    if len(mismatched_tags) > 3:
                        tag_names += _(' (and %d more)') % (len(mismatched_tags) - 3)
                    raise ValidationError(
                        _('Entity "%s" belongs to instance "%s",\n'
                          'but the following tags belong to different instances: %s\n'
                          'An entity can only use tags from the same instance.') % (
                              entity.name or entity.entity_id,
                              entity.ha_instance_id.name,
                              tag_names
                          )
                    )

    def write(self, vals):
        """
        覆寫 write 方法，限制一般用戶只能修改特定欄位。
        系統同步（使用 sudo()）不受此限制。

        當 area_id, name 或 label_ids 變更時，同步更新到 Home Assistant。
        使用 context['from_ha_sync'] = True 來防止循環同步。
        """
        if not self.env.su:
            disallowed_fields = set(vals.keys()) - self._USER_EDITABLE_FIELDS
            if disallowed_fields:
                raise AccessError(
                    _('You do not have permission to modify the following fields: %s') %
                    ', '.join(sorted(disallowed_fields))
                )

        # 檢查是否有需要同步到 HA 的欄位變更
        area_id_changed = 'area_id' in vals
        follows_device_area_changed = 'follows_device_area' in vals
        name_changed = 'name' in vals
        label_ids_changed = 'label_ids' in vals

        result = super().write(vals)

        # 若是從 HA 同步過來的，不再回傳給 HA（防止循環）
        if not self.env.context.get('from_ha_sync'):
            for record in self:
                # 當 follows_device_area 變更時，需要同步 area_id 到 HA
                # 勾選時發送 null，取消勾選時發送當前 area_id
                if follows_device_area_changed:
                    try:
                        record._update_entity_area_in_ha()
                    except Exception as e:
                        _logger.error(f"Failed to sync entity area {record.entity_id} to HA: {e}")
                elif area_id_changed:
                    try:
                        record._update_entity_area_in_ha()
                    except Exception as e:
                        _logger.error(f"Failed to sync entity area {record.entity_id} to HA: {e}")

                if name_changed:
                    try:
                        record._update_entity_name_in_ha()
                    except Exception as e:
                        _logger.error(f"Failed to sync entity name {record.entity_id} to HA: {e}")

                if label_ids_changed:
                    try:
                        record._update_entity_labels_in_ha()
                    except Exception as e:
                        _logger.error(f"Failed to sync entity labels {record.entity_id} to HA: {e}")

        return result

    def _update_entity_area_in_ha(self):
        """
        在 HA 中更新 Entity 的 area_id

        使用 WebSocket API: config/entity_registry/update
        參考: docs/homeassistant-api/websocket-message-logs/config_entity_registry_update.md

        當 follows_device_area = True 時，發送 area_id = null 給 HA，
        這會讓 HA 中的實體設定為「跟隨裝置分區」。
        """
        self.ensure_one()

        if not self.ha_instance_id:
            _logger.warning(f"Cannot sync entity area {self.entity_id}: no HA instance")
            return

        try:
            from odoo.addons.odoo_ha_addon.models.common.websocket_client import get_websocket_client
            client = get_websocket_client(self.env, instance_id=self.ha_instance_id.id)

            # 當 follows_device_area = True 時，發送 null 給 HA（跟隨裝置分區）
            # 否則發送實體的 area_id
            if self.follows_device_area:
                ha_area_id = None
            else:
                ha_area_id = self.area_id.area_id if self.area_id else None

            payload = {
                'entity_id': self.entity_id,
                'area_id': ha_area_id,
            }

            _logger.info(f"Updating entity area in HA: {self.entity_id} -> area_id={ha_area_id} (follows_device_area={self.follows_device_area})")
            result = client.call_websocket_api_sync('config/entity_registry/update', payload)

            if result and isinstance(result, dict):
                _logger.info(f"Entity {self.entity_id} area updated in HA successfully")
            else:
                _logger.warning(f"Unexpected result from HA: {result}")

        except Exception as e:
            _logger.error(f"Failed to update entity area {self.entity_id} in HA: {e}", exc_info=True)
            raise

    def _update_entity_name_in_ha(self):
        """
        在 HA 中更新 Entity 的 name（顯示名稱）

        使用 WebSocket API: config/entity_registry/update
        參考: docs/homeassistant-api/websocket-message-logs/config_entity_registry_update.md

        關於 HA Entity Registry 的 name 欄位：
        - 這是「使用者自訂的覆蓋名稱」，儲存在 Entity Registry 中
        - 預設值為 null，表示使用 original_name（整合提供的原始名稱）
        - 當 name 有值時，HA 會根據此值計算 state attributes 中的 friendly_name
        - friendly_name 計算規則：
          * 若 Entity 不屬於 Device: friendly_name = entity.name ?? original_name
          * 若 Entity 屬於 Device 且 name 有值: friendly_name = "{device.name} {entity.name}"
          * 若 Entity 屬於 Device 但 name 為 null: friendly_name = "{device.name}"

        注意：Odoo 中的 name 欄位儲存的是 friendly_name（計算後的顯示名稱），
        但我們同步到 HA 的是 Entity Registry 的 name 欄位。
        當使用者在 Odoo 清空 name 時，我們傳送 null 給 HA，表示恢復使用 original_name。
        """
        self.ensure_one()

        if not self.ha_instance_id:
            _logger.warning(f"Cannot sync entity name {self.entity_id}: no HA instance")
            return

        try:
            from odoo.addons.odoo_ha_addon.models.common.websocket_client import get_websocket_client
            client = get_websocket_client(self.env, instance_id=self.ha_instance_id.id)

            # HA Entity Registry 的 name 欄位：
            # - 有值時覆蓋 original_name
            # - 為 null 時使用 original_name
            # Odoo 的 name 欄位為空字串或 False 時，傳送 None（在 JSON 中會變成 null）
            ha_name = self.name if self.name else None

            payload = {
                'entity_id': self.entity_id,
                'name': ha_name,
            }

            _logger.info(f"Updating entity name in HA: {self.entity_id} -> name={ha_name!r}")
            result = client.call_websocket_api_sync('config/entity_registry/update', payload)

            if result and isinstance(result, dict):
                _logger.info(f"Entity {self.entity_id} name updated in HA successfully")
            else:
                _logger.warning(f"Unexpected result from HA: {result}")

        except Exception as e:
            _logger.error(f"Failed to update entity name {self.entity_id} in HA: {e}", exc_info=True)
            raise

    def _update_entity_labels_in_ha(self):
        """
        在 HA 中更新 Entity 的 labels

        使用 WebSocket API: config/entity_registry/update
        HA Entity Registry 的 labels 欄位是 label_id 陣列
        """
        self.ensure_one()

        if not self.ha_instance_id:
            _logger.warning(f"Cannot sync entity labels {self.entity_id}: no HA instance")
            return

        try:
            from odoo.addons.odoo_ha_addon.models.common.websocket_client import get_websocket_client
            client = get_websocket_client(self.env, instance_id=self.ha_instance_id.id)

            # Convert Odoo label_ids (Many2many) to HA labels (label_id array)
            ha_labels = self.label_ids.mapped('label_id') if self.label_ids else []

            payload = {
                'entity_id': self.entity_id,
                'labels': ha_labels,
            }

            _logger.info(f"Updating entity labels in HA: {self.entity_id} -> labels={ha_labels}")
            result = client.call_websocket_api_sync('config/entity_registry/update', payload)

            if result and isinstance(result, dict):
                _logger.info(f"Entity {self.entity_id} labels updated in HA successfully")
            else:
                _logger.warning(f"Unexpected result from HA: {result}")

        except Exception as e:
            _logger.error(f"Failed to update entity labels {self.entity_id} in HA: {e}", exc_info=True)
            raise

    @api.depends('attributes')
    def _compute_attributes_str(self):
        """將 JSON 物件轉換為格式化的字串供 ACE editor 顯示"""
        for record in self:
            if record.attributes:
                try:
                    # 將 JSON 格式化為有縮排的字串
                    record.attributes_str = json.dumps(
                        record.attributes,
                        indent=2,
                        ensure_ascii=False,
                        sort_keys=True
                    )
                except (TypeError, ValueError) as e:
                    _logger.warning(f"Failed to format attributes for {record.entity_id}: {e}")
                    record.attributes_str = str(record.attributes)
            else:
                record.attributes_str = '{}'

    def _inverse_attributes_str(self):
        """將編輯後的字串轉換回 JSON 物件"""
        for record in self:
            if record.attributes_str:
                try:
                    # 解析 JSON 字串並存回 attributes 欄位
                    record.attributes = json.loads(record.attributes_str)
                except (TypeError, ValueError) as e:
                    _logger.error(f"Failed to parse JSON for {record.entity_id}: {e}")
                    # 保持原值不變
                    pass

    @api.model
    def sync_entity_states_from_ha(self, instance_id=None, sync_area_relations=True):
        """
        從 Home Assistant 同步所有實體狀態
        使用 WebSocket API 的 get_states 指令
        參考: PDF 文檔 page 4-5 "取回 HA 裝置清狀態清單"

        Args:
            instance_id: HA 實例 ID (Phase 3 & 3.1)，如果為 None 則使用 HAInstanceHelper
            sync_area_relations: 是否同步 entity 與 area 的關聯關係（預設 True）
        """
        _logger.info(f"=== Starting sync_entity_states_from_ha (instance_id={instance_id}) ===")

        try:
            # Phase 3.1: 使用 HAInstanceHelper 統一獲取實例 ID（重構後）
            if instance_id is None:
                from odoo.addons.odoo_ha_addon.models.common.instance_helper import HAInstanceHelper
                instance_id = HAInstanceHelper.get_current_instance(self.env, logger=_logger)
                if not instance_id:
                    _logger.error("No HA instance available")
                    return

            # 創建 WebSocket client（傳入明確的 instance_id）
            from odoo.addons.odoo_ha_addon.models.common.websocket_client import get_websocket_client
            client = get_websocket_client(self.env, instance_id=instance_id)

            # 根據 PDF 文檔，WebSocket message: {"type": "get_states"}
            _logger.debug("Sending get_states request via WebSocket...")
            entity_states = client.call_websocket_api_sync('get_states', {})

            if not entity_states or not isinstance(entity_states, list):
                _logger.warning("No entity states received from Home Assistant or invalid format")
                _logger.debug(f"Received result: {entity_states}")
                return

            _logger.info(f"Received {len(entity_states)} entities from Home Assistant (instance {instance_id})")
            _logger.debug(f"First few entities: {entity_states[:3] if len(entity_states) > 3 else entity_states}")

            # Phase 3: 處理實體狀態並更新資料庫，傳入 instance_id
            self._process_entity_states(entity_states, instance_id)

            # 同步完成後，更新 entity 與 area, labels 和 device 的關聯
            if sync_area_relations:
                # 確保 devices 已同步（device_id 依賴 device 記錄存在）
                # Check if devices exist, if not sync them first
                device_count = self.env['ha.device'].sudo().search_count([
                    ('ha_instance_id', '=', instance_id)
                ])
                if device_count == 0:
                    _logger.info("No devices found, syncing devices first...")
                    self.env['ha.device'].sudo().sync_devices_from_ha(instance_id=instance_id)

                self._sync_entity_registry_relations(instance_id)

            # 更新實例的 last_sync_date（批量同步完成時間）
            try:
                instance = self.env['ha.instance'].sudo().browse(instance_id)
                if instance.exists():
                    instance.write({'last_sync_date': fields.Datetime.now()})
                    _logger.info(f"Updated last_sync_date for instance {instance.name}")
            except Exception as e:
                _logger.warning(f"Failed to update last_sync_date: {e}")

            _logger.info("=== sync_entity_states_from_ha completed successfully ===")

        except Exception as e:
            _logger.error(f"Failed to sync entity states: {e}", exc_info=True)
            # Fallback 到 REST API
            _logger.info("Attempting fallback to REST API...")
            self._fallback_to_rest_api(instance_id)

    def _sync_entity_registry_relations(self, instance_id):
        """
        同步 entity 與 area, labels 和 device 的關聯關係
        從 entity_registry 取得 area_id, labels 和 device_id 並更新到 ha.entity

        Args:
            instance_id: HA 實例 ID (Phase 3)
        """
        _logger.info(f"=== Starting sync entity-area-label-device relations (instance {instance_id}) ===")

        try:
            from odoo.addons.odoo_ha_addon.models.common.websocket_client import get_websocket_client

            # Phase 3: 傳入 instance_id
            client = get_websocket_client(self.env, instance_id=instance_id)

            # Fetch registry data BEFORE opening new cursor to avoid holding connections
            _logger.debug("Fetching entity_registry list...")
            registry_data = client.call_websocket_api_sync('config/entity_registry/list', {})

            if not registry_data or not isinstance(registry_data, list):
                _logger.warning("No entity registry data received")
                return

            _logger.info(f"Received {len(registry_data)} entity registry entries")

            # Use a NEW cursor to isolate sync from concurrent WebSocket updates
            # This prevents "current transaction is aborted" errors from affecting the sync
            with self.pool.cursor() as new_cr:
                # Set isolation level to READ COMMITTED to avoid serialization conflicts
                # with real-time WebSocket state updates running in the main server
                new_cr.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
                new_env = self.env(cr=new_cr)
                self._do_sync_entity_registry_relations(new_env, instance_id, registry_data)
                new_cr.commit()
                _logger.info(f"Entity relations sync transaction committed successfully")

        except Exception as e:
            _logger.error(f"Failed to sync entity-area-label-device relations: {e}", exc_info=True)

    def _do_sync_entity_registry_relations(self, env, instance_id, registry_data):
        """
        Internal method to perform the actual sync using the provided environment.
        This is called with a fresh cursor to isolate from concurrent updates.

        Args:
            env: The environment with a fresh cursor
            instance_id: HA instance ID
            registry_data: List of entity registry entries from HA
        """
        # Phase 3: 建立 area_id -> ha.area record ID 的映射（只包含此實例的 areas）
        areas = env['ha.area'].sudo().search([
            ('ha_instance_id', '=', instance_id)
        ])
        area_map = {area.area_id: area.id for area in areas}

        # 建立 device_id -> ha.device record ID 的映射（只包含此實例的 devices）
        devices = env['ha.device'].sudo().search([
            ('ha_instance_id', '=', instance_id)
        ])
        device_map = {device.device_id: device.id for device in devices}
        _logger.info(f"Device map size: {len(device_map)} devices for instance {instance_id}")
        if device_map:
            _logger.debug(f"Sample device_ids in map: {list(device_map.keys())[:3]}")

        area_updated_count = 0
        label_updated_count = 0
        device_updated_count = 0
        device_set_count = 0  # Entities where device_id was SET
        device_clear_count = 0  # Entities where device_id was CLEARED
        device_not_in_map_count = 0  # Entities with device_id not in our map
        for entry in registry_data:
            try:
                entity_id = entry.get('entity_id')
                ha_area_id = entry.get('area_id')  # HA 的 area_id (string)
                ha_labels = entry.get('labels', [])  # HA 的 labels (label_id array)
                ha_device_id = entry.get('device_id')  # HA 的 device_id (string)

                if not entity_id:
                    continue

                # Phase 3: 查找對應的 entity（加上 instance_id 過濾）
                entity = env['ha.entity'].sudo().search([
                    ('entity_id', '=', entity_id),
                    ('ha_instance_id', '=', instance_id)
                ], limit=1)

                if not entity:
                    continue

                update_vals = {}

                # 更新 area_id 和 follows_device_area
                # 當 HA 的 area_id 為 null 且有 device_id 時，表示實體跟隨裝置分區
                if ha_area_id:
                    # 實體有自己的分區
                    if ha_area_id in area_map:
                        odoo_area_id = area_map[ha_area_id]
                    else:
                        # Auto-create area if it doesn't exist
                        _logger.info(f"Auto-creating area {ha_area_id} for entity {entity_id}")
                        area_record = env['ha.area'].sudo().create({
                            'area_id': ha_area_id,
                            'name': ha_area_id,  # Temporary name, will be updated by area sync
                            'ha_instance_id': instance_id,
                        })
                        odoo_area_id = area_record.id
                        area_map[ha_area_id] = odoo_area_id  # Update map for future entities

                    if entity.area_id.id != odoo_area_id:
                        update_vals['area_id'] = odoo_area_id
                        area_updated_count += 1
                        _logger.debug(f"Updated entity {entity_id} -> area {ha_area_id}")
                    # 有自己的 area_id，不跟隨裝置
                    if entity.follows_device_area:
                        update_vals['follows_device_area'] = False
                elif not ha_area_id and ha_device_id:
                    # HA 中沒有 area 但有 device，表示跟隨裝置分區
                    if entity.area_id:
                        update_vals['area_id'] = False
                        area_updated_count += 1
                    if not entity.follows_device_area:
                        update_vals['follows_device_area'] = True
                        _logger.debug(f"Entity {entity_id} follows device area")
                elif not ha_area_id and not ha_device_id:
                    # HA 中沒有 area 也沒有 device
                    if entity.area_id:
                        update_vals['area_id'] = False
                        area_updated_count += 1
                    if entity.follows_device_area:
                        update_vals['follows_device_area'] = False

                # 更新 label_ids
                if ha_labels:
                    label_records = env['ha.label'].get_or_create_labels(ha_labels, instance_id)
                    current_label_ids = set(entity.label_ids.ids)
                    new_label_ids = set(label_records.ids)
                    if current_label_ids != new_label_ids:
                        update_vals['label_ids'] = [(6, 0, label_records.ids)]
                        label_updated_count += 1
                        _logger.debug(f"Updated entity {entity_id} labels: {ha_labels}")
                elif entity.label_ids:
                    # 清空 labels
                    update_vals['label_ids'] = [(5, 0, 0)]
                    label_updated_count += 1

                # 更新 device_id
                if ha_device_id and ha_device_id in device_map:
                    odoo_device_id = device_map[ha_device_id]
                    if entity.device_id.id != odoo_device_id:
                        update_vals['device_id'] = odoo_device_id
                        device_updated_count += 1
                        device_set_count += 1
                        _logger.debug(f"SET device_id: entity {entity_id} -> device {ha_device_id} (odoo_id={odoo_device_id})")
                elif ha_device_id and ha_device_id not in device_map:
                    # Log when device_id is in registry but not in our device_map
                    device_not_in_map_count += 1
                    if device_not_in_map_count <= 5:  # Only log first few
                        _logger.warning(f"Entity {entity_id} has device_id={ha_device_id} but not in device_map")
                elif not ha_device_id and entity.device_id:
                    # HA 中沒有 device，清空 Odoo 的 device_id
                    update_vals['device_id'] = False
                    device_updated_count += 1
                    device_clear_count += 1

                if update_vals:
                    _logger.debug(f"Writing update_vals for {entity_id}: {update_vals}")
                    try:
                        # Must use sudo() to bypass _USER_EDITABLE_FIELDS restriction for device_id
                        entity.sudo().with_context(from_ha_sync=True).write(update_vals)
                    except Exception as write_error:
                        _logger.error(f"Write failed for {entity_id}: {write_error}")

            except Exception as e:
                _logger.error(f"Error syncing relations for entity: {e}")

        _logger.info(
            f"Entity relations sync completed (instance {instance_id}): "
            f"{area_updated_count} areas updated, {label_updated_count} labels updated, "
            f"{device_updated_count} device relations updated "
            f"(SET: {device_set_count}, CLEARED: {device_clear_count}, NOT_IN_MAP: {device_not_in_map_count})"
        )

    def fetch_states(self):
        """
        使用 WebSocket API 獲取所有實體狀態
        參考: https://developers.home-assistant.io/docs/api/websocket#fetching-states

        已棄用: 此方法保留以維持向後兼容，請使用 sync_entity_states_from_ha()
        未來需要排程成刪除不存在的 entity。
        """
        _logger.info("=== fetch_states called (delegating to sync_entity_states_from_ha) ===")
        _logger.debug(f"Current model: {self._name}")
        _logger.debug(f"Environment context: {self.env.context}")

        # 委派給新的標準方法（不同步 area 關聯以保持原有行為）
        # Phase 3: instance_id=None 會使用預設實例
        self.env['ha.entity'].sudo().sync_entity_states_from_ha(instance_id=None, sync_area_relations=False)

    def _process_entity_states(self, entity_states, instance_id):
        """
        處理從 WebSocket 獲取的實體狀態

        Args:
            entity_states: HA 回傳的實體狀態列表
            instance_id: HA 實例 ID (Phase 3)
        """
        _logger.debug(f"=== Processing {len(entity_states)} entity states (instance {instance_id}) ===")
        records = []
        processed_count = 0
        error_count = 0

        for i, state in enumerate(entity_states):
            try:
                entity_id = state.get('entity_id', 'unknown')
                _logger.debug(f"Processing entity {i+1}/{len(entity_states)}: {entity_id}")

                record = {
                    "domain": parse_domain_from_entitiy_id(state['entity_id']),
                    "entity_id": state['entity_id'],
                    "name": state.get('attributes', {}).get('friendly_name'),
                    "entity_state": state['state'],
                    "last_changed": parse_iso_datetime(state['last_changed']),
                    "attributes": state['attributes'],
                    "ha_instance_id": instance_id  # Phase 3: 指定實例 ID
                }

                _logger.debug(f"Entity {entity_id}: domain={record['domain']}, entity_state={record['entity_state']}")
                records.append(record)
                processed_count += 1

            except Exception as e:
                error_count += 1
                entity_id = state.get('entity_id', 'unknown') if isinstance(state, dict) else 'invalid_state'
                _logger.error(f"Error processing entity {entity_id}: {e}")
                _logger.debug(f"Problematic state data: {state}")

        _logger.info(f"Entity processing summary: {processed_count} processed, {error_count} errors")
        _logger.debug(f"Records ready for batch update: {len(records)}")

        # Phase 3: 批次處理記錄（提升性能），傳入 instance_id
        self._batch_update_entities(records, instance_id)

    def _batch_update_entities(self, records, instance_id):
        """
        批次更新實體記錄（提升性能）
        使用 savepoint 隔離每個實體的更新，避免序列化衝突

        Args:
            records: 實體記錄列表
            instance_id: HA 實例 ID (Phase 3)
        """
        _logger.debug(f"=== Starting batch update for {len(records)} records (instance {instance_id}) ===")

        created_count = 0
        updated_count = 0
        error_count = 0

        for i, record in enumerate(records):
            # 使用 savepoint 隔離每個實體的更新
            # 如果與 WebSocket state_changed 並發，只影響此實體
            with self.env.cr.savepoint():
                try:
                    entity_id = record['entity_id']
                    _logger.debug(f"Batch update {i+1}/{len(records)}: {entity_id}")

                    # Phase 3: 檢查是否已存在（加上 instance_id 過濾）
                    existing_record = self.env[self._name].search([
                        ('entity_id', '=', entity_id),
                        ('ha_instance_id', '=', instance_id)
                    ], limit=1)

                    if existing_record:
                        # 檢查是否需要更新
                        needs_update = (
                            existing_record.entity_state != record['entity_state'] or
                            existing_record.name != record['name'] or
                            existing_record.last_changed != record['last_changed'] or
                            existing_record.attributes != record['attributes']
                        )

                        if needs_update:
                            # 更新現有記錄（使用 from_ha_sync 防止循環同步）
                            existing_record.with_context(from_ha_sync=True).write({
                                'name': record['name'],
                                'entity_state': record['entity_state'],
                                'last_changed': record['last_changed'],
                                'attributes': record['attributes']
                            })
                            updated_count += 1
                            _logger.debug(f"Updated entity: {entity_id} (entity_state: {record['entity_state']})")
                        else:
                            _logger.debug(f"Entity {entity_id} unchanged, skipping update")
                    else:
                        # 建立新記錄（record 中已包含 ha_instance_id）
                        self.env[self._name].create(record)
                        created_count += 1
                        _logger.info(f"Created entity: {entity_id} (domain: {record['domain']})")

                except Exception as e:
                    # savepoint 會自動 rollback 此次迭代
                    error_count += 1
                    entity_id = record.get('entity_id', 'unknown')
                    _logger.error(f"Error updating entity {entity_id}: {e}")
                    _logger.debug(f"Problematic record: {record}")

        _logger.info(f"Batch update summary (instance {instance_id}): {created_count} created, {updated_count} updated, {error_count} errors")
        _logger.debug("=== Batch update completed ===")

    def _fallback_to_rest_api(self, instance_id):
        """
        WebSocket 失敗時的 REST API fallback

        Args:
            instance_id: HA 實例 ID
        """
        _logger.info(f"=== Starting REST API fallback (instance {instance_id}) ===")
        _logger.debug("Creating HassRestApi client...")

        try:
            # 使用 multi-instance REST API
            api = HassRestApi(self.env, instance_id=instance_id)
            _logger.debug("Calling REST API get_ha_state()...")

            entity_states = api.get_ha_state()

            if entity_states:
                _logger.info(f"REST API returned {len(entity_states)} entities")
                _logger.debug("Processing entities from REST API...")
                self._process_entity_states(entity_states, instance_id)

                # 更新實例的 last_sync_date（REST API fallback 同步完成時間）
                try:
                    instance = self.env['ha.instance'].sudo().browse(instance_id)
                    if instance.exists():
                        instance.write({'last_sync_date': fields.Datetime.now()})
                        _logger.info(f"Updated last_sync_date for instance {instance.name} (REST API fallback)")
                except Exception as e:
                    _logger.warning(f"Failed to update last_sync_date: {e}")

                _logger.info("=== REST API fallback completed successfully ===")
            else:
                _logger.warning("REST API returned no entities")

        except Exception as e:
            _logger.error(f"REST API fallback also failed: {e}")
            _logger.debug(f"REST API exception details: {str(e)}", exc_info=True)
            _logger.error("=== Both WebSocket and REST API failed ===")


    @api.model
    def start_websocket_service_manual(self):
        """
        手動啟動 WebSocket 服務 (用於測試或手動控制)
        """
        from .common.websocket_thread_manager import start_websocket_service

        try:
            start_websocket_service(self.env)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('WebSocket Service'),
                    'message': _('WebSocket service started'),
                    'type': 'success'
                }
            }
        except Exception as e:
            _logger.error(f"Failed to start WebSocket service: {e}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('WebSocket Service'),
                    'message': _('Start failed: %s') % str(e),
                    'type': 'danger'
                }
            }

    @api.model
    def stop_websocket_service(self):
        """
        停止 WebSocket 服務
        """
        from .common.websocket_thread_manager import stop_websocket_service as stop_ws

        try:
            stop_ws()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('WebSocket Service'),
                    'message': _('WebSocket service stopped'),
                    'type': 'success'
                }
            }
        except Exception as e:
            _logger.error(f"Failed to stop WebSocket service: {e}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('WebSocket Service'),
                    'message': _('Stop failed: %s') % str(e),
                    'type': 'danger'
                }
            }

    @api.model
    def get_websocket_service_status(self):
        """
        取得 WebSocket 服務狀態
        """
        from .common.websocket_thread_manager import is_websocket_service_running

        is_running = is_websocket_service_running(self.env)
        return {
            'is_running': is_running,
            'status': '已連線' if is_running else '未連線'
        }

    @api.model
    def _cron_ensure_websocket_service(self):
        """
        Cron Job: 確保 WebSocket 服務運行（Threading 版本 - Multi-Instance Support）
        每分鐘執行一次，檢查並啟動 WebSocket 服務
        如果組態變更，自動重啟服務

        Phase 2 更新：支援多實例架構
        - 遍歷所有活躍的 HA 實例
        - 為每個配置完整的實例啟動/維護 WebSocket 服務
        - 檢測並處理配置變更
        """
        from .common.websocket_thread_manager import (
            start_websocket_service,
            is_websocket_service_running,
            is_config_changed,
            restart_websocket_service
        )

        _logger.info("Checking WebSocket service status (multi-instance)")

        # Phase 2: 取得所有活躍的 HA 實例
        instances = self.env['ha.instance'].sudo().search([('active', '=', True)])

        if not instances:
            _logger.warning("No active HA instances found, skipping WebSocket service check")
            return

        _logger.info(f"Found {len(instances)} active HA instance(s) to monitor")

        # Phase 2: 為每個實例檢查和維護 WebSocket 服務
        for instance in instances:
            instance_id = instance.id
            instance_name = instance.name

            # 檢查該實例的配置是否完整
            if not instance.api_url or not instance.api_token:
                _logger.debug(
                    f"Instance '{instance_name}' (ID: {instance_id}) configuration incomplete, "
                    f"skipping WebSocket service"
                )
                continue

            # 檢查該實例的 WebSocket 服務是否已在運行
            if is_websocket_service_running(self.env, instance_id=instance_id):
                # 檢查該實例的組態是否變更
                if is_config_changed(self.env, instance_id=instance_id):
                    _logger.info(
                        f"Instance '{instance_name}' (ID: {instance_id}) configuration changed, "
                        f"restarting WebSocket service..."
                    )
                    result = restart_websocket_service(self.env, instance_id=instance_id)
                    if result['success']:
                        _logger.info(
                            f"WebSocket service restarted successfully for instance '{instance_name}'"
                        )
                    elif result.get('skipped'):
                        _logger.warning(
                            f"Restart skipped for instance '{instance_name}': {result['message']}"
                        )
                    else:
                        _logger.error(
                            f"Failed to restart WebSocket service for instance '{instance_name}': "
                            f"{result['message']}"
                        )
                else:
                    _logger.debug(
                        f"Instance '{instance_name}' (ID: {instance_id}) WebSocket service "
                        f"already running with current configuration"
                    )
            else:
                # 該實例的 WebSocket 服務未運行，啟動它
                _logger.info(
                    f"Starting WebSocket service for instance '{instance_name}' (ID: {instance_id})"
                )
                try:
                    start_websocket_service(self.env, instance_id=instance_id)
                    _logger.info(
                        f"WebSocket service started successfully for instance '{instance_name}'"
                    )
                except Exception as e:
                    _logger.error(
                        f"Failed to start WebSocket service for instance '{instance_name}': {e}"
                    )

    def _compute_access_url(self):
        """Compute the portal access URL for each entity."""
        for record in self:
            record.access_url = f'/portal/entity/{record.id}'

    def action_view_tags(self):
        """開啟此實體的標籤列表"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'odoo_ha_addon.ha_entity_view_tags_action'
        )
        action['name'] = f'{self.name or self.entity_id} - Tags'
        action['domain'] = [('id', 'in', self.tag_ids.ids)]
        action['context'] = {'default_entity_ids': [(4, self.id)]}
        return action

    def action_share(self):
        """
        Open the entity share wizard to share this entity with specific users.

        This opens a wizard that allows selecting users and setting permissions
        for user-based sharing (not portal token-based).
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Share Entity'),
            'res_model': 'ha.entity.share.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_entity_id': self.id,
            },
        }


