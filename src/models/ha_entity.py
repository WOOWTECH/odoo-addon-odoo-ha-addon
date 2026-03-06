from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError
import logging
import json
import re
import threading
import unicodedata
from .common.utils import parse_iso_datetime, parse_domain_from_entitiy_id
from .common.hass_rest_api import HassRestApi

_logger = logging.getLogger(__name__)

def _name_to_entity_id(name, domain='scene'):
    """
    Convert a display name to a valid Home Assistant entity_id.

    Uses pinyin conversion for Chinese characters (if pypinyin available),
    otherwise falls back to unicode normalization.

    Args:
        name: Display name (e.g., "測試場景", "My Scene")
        domain: Entity domain (default: 'scene')

    Returns:
        Valid entity_id (e.g., "scene.ce_shi_chang_jing", "scene.my_scene")
    """
    if not name:
        return None

    # Try to use pypinyin for Chinese character conversion
    try:
        from pypinyin import lazy_pinyin, Style
        # Convert to pinyin (without tones)
        pinyin_parts = lazy_pinyin(name, style=Style.NORMAL)
        slug = '_'.join(pinyin_parts)
    except ImportError:
        # Fallback: Use unicode normalization and keep only ASCII
        # This handles Latin characters well but Chinese will be removed
        slug = unicodedata.normalize('NFKD', name)
        slug = slug.encode('ascii', 'ignore').decode('ascii')
        if not slug:
            # If nothing left after normalization, use a hash-based ID
            import hashlib
            slug = 'scene_' + hashlib.md5(name.encode('utf-8')).hexdigest()[:8]

    # Clean up the slug
    slug = slug.lower()
    slug = re.sub(r'[^a-z0-9]+', '_', slug)  # Replace non-alphanumeric with underscore
    slug = re.sub(r'_+', '_', slug)  # Collapse multiple underscores
    slug = slug.strip('_')  # Remove leading/trailing underscores

    if not slug:
        slug = 'unnamed'

    return f"{domain}.{slug}"


class HAEntity(models.Model):
    _name = 'ha.entity'
    _inherit = ['ha.current.instance.filter.mixin', 'mail.thread', 'mail.activity.mixin', 'portal.mixin']
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
        store=True,  # Store for grouping in kanban/list views
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

    # Scene-specific fields (only applicable when domain='scene')
    scene_entity_ids = fields.Many2many(
        'ha.entity',
        'ha_scene_entity_rel',
        'scene_id',
        'entity_id',
        string='Scene Entities',
        domain="[('domain', '!=', 'scene')]",
        help='Entities included in this scene (only for domain=scene)'
    )
    scene_entity_count = fields.Integer(
        string='Scene Entity Count',
        compute='_compute_scene_entity_count',
        help='Number of entities in this scene'
    )
    ha_scene_id = fields.Char(
        string='HA Scene ID',
        copy=False,
        help='Numeric ID used by Home Assistant for scene config (timestamp format). '
             'Required for scenes to be editable in HA GUI.'
    )
    scene_source = fields.Selection(
        [
            ('odoo', 'Created in Odoo'),
            ('device', 'Device Scene'),
        ],
        string='Scene Source',
        compute='_compute_scene_source',
        store=False,
        help='Indicates where the scene was created. '
             'Device scenes (e.g., Hue Bridge) have limited sync capabilities.'
    )

    @api.depends('domain', 'ha_scene_id', 'device_id')
    def _compute_scene_source(self):
        """Compute the source of the scene for display purposes."""
        for record in self:
            if record.domain != 'scene':
                record.scene_source = False
            elif record.ha_scene_id:
                # Has ha_scene_id means it was created via Odoo or is an editable HA scene
                record.scene_source = 'odoo'
            else:
                # No ha_scene_id means it's a device-created scene (Hue, etc.)
                record.scene_source = 'device'

    # Blueprint-specific fields (only applicable when domain='automation' or 'script')
    blueprint_path = fields.Char(
        string='Blueprint Path',
        help='Path to the blueprint (e.g., homeassistant/motion_light.yaml). '
             'Only applicable for automation/script entities based on blueprints.'
    )
    blueprint_inputs = fields.Text(
        string='Blueprint Inputs (JSON)',
        help='User-provided input values for the blueprint in JSON format.'
    )
    blueprint_metadata = fields.Text(
        string='Blueprint Metadata (JSON)',
        help='Cached blueprint schema including inputs definition, name, and description.'
    )
    is_blueprint_based = fields.Boolean(
        string='Is Blueprint Based',
        compute='_compute_is_blueprint_based',
        store=True,
        help='Whether this automation/script is based on a blueprint'
    )
    ha_automation_id = fields.Char(
        string='HA Automation/Script ID',
        copy=False,
        help='The ID used by Home Assistant for automation/script config. '
             'Usually matches the entity_id without domain prefix.'
    )

    @api.depends('blueprint_path')
    def _compute_is_blueprint_based(self):
        """Compute whether this entity is based on a blueprint."""
        for record in self:
            record.is_blueprint_based = bool(record.blueprint_path)

    @api.depends('tag_ids')
    def _compute_tag_count(self):
        for entity in self:
            entity.tag_count = len(entity.tag_ids)

    @api.depends('scene_entity_ids')
    def _compute_scene_entity_count(self):
        """Compute the number of entities in this scene"""
        for entity in self:
            if entity.domain == 'scene':
                entity.scene_entity_count = len(entity.scene_entity_ids)
            else:
                entity.scene_entity_count = 0

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
    # - scene_entity_ids: Scene 包含的實體（雙向同步到 HA，僅適用於 domain='scene'）
    # - blueprint_inputs: Blueprint 參數（雙向同步到 HA，僅適用於 domain='automation'/'script'）
    _USER_EDITABLE_FIELDS = {'enable_record', 'area_id', 'follows_device_area', 'name', 'label_ids', 'tag_ids', 'note', 'properties', 'scene_entity_ids', 'blueprint_inputs'}

    @api.model
    def default_get(self, fields_list):
        """
        Override default_get to auto-select HA instance when creating new entities.

        If there's only one HA instance, automatically select it.
        This improves UX for single-instance setups.
        """
        defaults = super().default_get(fields_list)

        # Auto-select HA instance if creating a new entity
        if 'ha_instance_id' in fields_list and not defaults.get('ha_instance_id'):
            # Check context for default instance
            if self.env.context.get('default_ha_instance_id'):
                defaults['ha_instance_id'] = self.env.context['default_ha_instance_id']
            else:
                # Get all accessible instances
                instances = self.env['ha.instance'].search([], limit=2)
                if len(instances) == 1:
                    # Only one instance - auto-select it
                    defaults['ha_instance_id'] = instances.id

        return defaults

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        """
        Override _search to handle scene entity search with instance filtering.

        When searching for entities to add to a scene, the domain may contain
        ha_instance_id = False in create mode. We use the context to get the
        correct instance_id.

        Context keys:
        - scene_entity_search_instance_id: The instance ID for filtering scene entities
        """
        # Check if this is a scene entity search with a False instance_id
        scene_instance_id = self.env.context.get('scene_entity_search_instance_id')
        if scene_instance_id:
            # Build a new domain with the correct instance_id
            new_domain = []
            for clause in domain:
                if isinstance(clause, (list, tuple)) and len(clause) >= 3:
                    field, op, value = clause[0], clause[1], clause[2]
                    # Replace ha_instance_id = False with the correct instance_id
                    if field == 'ha_instance_id' and op == '=' and not value:
                        new_domain.append(('ha_instance_id', '=', scene_instance_id))
                        continue
                new_domain.append(clause)
            domain = new_domain

        return super()._search(domain, offset=offset, limit=limit, order=order)

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to process entity_id for new scenes.

        For entities with domain='scene':
        - Process user-provided entity_id: add scene. prefix, convert Chinese to pinyin
        - If entity_id is not provided, generate it from the name
        - Auto-select ha_instance_id if only one instance exists
        - Sync new scene to Home Assistant after creation
        """
        for vals in vals_list:
            # Handle scene-specific logic
            if vals.get('domain') == 'scene':
                # Get instance_id for uniqueness check
                instance_id = vals.get('ha_instance_id')
                if not instance_id:
                    instance_id = self.env.context.get('default_ha_instance_id')
                    if not instance_id:
                        instances = self.env['ha.instance'].search([], limit=1)
                        if instances:
                            instance_id = instances.id
                            vals['ha_instance_id'] = instance_id

                # Process entity_id
                if vals.get('entity_id'):
                    # User provided entity_id - process it
                    user_input = vals['entity_id'].strip()

                    # Remove scene. prefix if user included it (we'll add it back)
                    if user_input.startswith('scene.'):
                        user_input = user_input[6:]

                    # Convert to valid entity_id format (handles Chinese -> pinyin)
                    base_entity_id = _name_to_entity_id(user_input, 'scene')
                    vals['entity_id'] = base_entity_id

                elif vals.get('name'):
                    # No entity_id provided - generate from name
                    base_entity_id = _name_to_entity_id(vals['name'], 'scene')
                    vals['entity_id'] = base_entity_id

                # Ensure entity_id is unique within the instance
                if instance_id and vals.get('entity_id'):
                    base_entity_id = vals['entity_id']
                    entity_id = base_entity_id
                    counter = 1
                    while self.search([
                        ('entity_id', '=', entity_id),
                        ('ha_instance_id', '=', instance_id)
                    ], limit=1):
                        entity_id = f"{base_entity_id}_{counter}"
                        counter += 1
                    vals['entity_id'] = entity_id

                # Set initial state
                if not vals.get('entity_state'):
                    vals['entity_state'] = 'unknown'

        records = super().create(vals_list)

        # Schedule HA sync for new scenes after transaction commits
        # This ensures Many2many relations (scene_entity_ids) are fully persisted
        scene_ids_to_sync = []
        for record in records:
            if record.domain == 'scene':
                scene_ids_to_sync.append(record.id)

        if scene_ids_to_sync:
            # Capture required data before postcommit
            db_name = self.env.cr.dbname
            uid = self.env.uid

            def sync_scenes_in_background():
                """
                Background thread for HA scene sync.

                This runs in a completely separate thread with its own database connection,
                avoiding all transaction conflicts with the main Odoo process.

                Key design decisions:
                1. Use db_connect() instead of registry.cursor() - cleaner connection handling
                2. Use READ COMMITTED isolation (default) - avoids serialization conflicts
                3. Commit immediately after each scene - partial success is better than total failure
                4. Use REST API for scene creation (no WebSocket queue complexity)
                5. Use direct WebSocket call only for entity_registry updates
                """
                import time as time_module
                from odoo.sql_db import db_connect

                # Wait for original transaction to fully complete
                time_module.sleep(0.3)

                _logger.debug(f"[BG_THREAD] Starting sync for scene_ids: {scene_ids_to_sync}")
                _logger.info(f"[BG_THREAD] Starting background sync for {len(scene_ids_to_sync)} scenes")

                for scene_id in scene_ids_to_sync:
                    try:
                        # Create fresh database connection for each scene
                        # This ensures clean transaction state
                        with db_connect(db_name).cursor() as cr:
                            env = api.Environment(cr, uid, {})
                            scene = env['ha.entity'].browse(scene_id)

                            if not scene.exists():
                                _logger.warning(f"[BG_THREAD] Scene {scene_id} no longer exists, skipping")
                                continue

                            if not scene.scene_entity_ids:
                                _logger.warning(f"[BG_THREAD] Scene {scene_id} has no entities, skipping")
                                continue

                            _logger.info(f"[BG_THREAD] Processing scene {scene_id}: "
                                        f"entity_id={scene.entity_id}, "
                                        f"area_id={scene.area_id.area_id if scene.area_id else None}")
                            _logger.debug(f"[BG_THREAD] Processing scene {scene_id}")

                            try:
                                # Use _sync_scene_to_ha_internal which handles both
                                # scene creation and area/label sync
                                scene._sync_scene_to_ha_internal()
                                cr.commit()
                                _logger.info(f"[BG_THREAD] Scene {scene_id} synced successfully")
                                _logger.debug(f"[BG_THREAD] Scene {scene_id} sync SUCCESS")
                            except Exception as sync_error:
                                _logger.error(f"[BG_THREAD] Scene {scene_id} sync failed: {sync_error}", exc_info=True)
                                _logger.debug(f"[BG_THREAD] Scene {scene_id} sync FAILED: {sync_error}")
                                cr.rollback()

                    except Exception as e:
                        _logger.error(f"[BG_THREAD] Error processing scene {scene_id}: {e}", exc_info=True)
                        _logger.debug(f"[BG_THREAD] Scene {scene_id} outer error: {e}")

            def start_sync_thread():
                """Postcommit callback to start the background sync thread."""
                thread = threading.Thread(
                    target=sync_scenes_in_background,
                    name=f"ha_scene_sync_{scene_ids_to_sync[0]}",
                    daemon=True
                )
                thread.start()
                _logger.info(f"[POSTCOMMIT] Started background sync thread for scenes: {scene_ids_to_sync}")

            self.env.cr.postcommit.add(start_sync_thread)

        return records

    def unlink(self):
        """
        Override unlink to delete scenes from Home Assistant when deleted in Odoo.

        HA deletion is scheduled via postcommit + background thread to:
        1. Not block the Odoo delete operation if HA is slow/unreachable
        2. Only execute after the Odoo transaction successfully commits
        3. Not block Odoo's HTTP worker threads (prevents bus/longpolling interruption)

        Handles both cases:
        - Scenes with ha_scene_id: Delete directly using the stored ID
        - Scenes without ha_scene_id: Query HA to get the config ID first

        If called with context 'from_ha_sync=True', skips HA deletion to prevent
        sync loops when entity is removed from HA first.
        """
        # Skip HA deletion if this unlink is triggered by HA sync
        # (entity was already deleted in HA, no need to delete again)
        from_ha_sync = self.env.context.get('from_ha_sync', False)

        # Collect scene info before deletion
        scenes_to_delete = []
        scenes_to_lookup = []  # Scenes that need ID lookup from HA

        if not from_ha_sync:
            for record in self:
                if record.domain == 'scene' and record.ha_instance_id:
                    if record.ha_scene_id:
                        # Scene has stored ha_scene_id, can delete directly
                        scenes_to_delete.append({
                            'entity_id': record.entity_id,
                            'ha_scene_id': record.ha_scene_id,
                            'ha_instance_id': record.ha_instance_id.id,
                        })
                    else:
                        # Scene needs ID lookup from HA before deletion
                        scenes_to_lookup.append({
                            'entity_id': record.entity_id,
                            'ha_instance_id': record.ha_instance_id.id,
                        })

        # Perform the actual deletion in Odoo
        result = super().unlink()

        # Schedule HA scene deletion via postcommit + background thread (truly non-blocking)
        # This runs after the transaction commits successfully, in a separate thread
        # to avoid blocking Odoo's HTTP workers (which would cause bus/longpolling interruption)
        if scenes_to_delete or scenes_to_lookup:
            # Capture necessary info for the background thread
            db_name = self.env.cr.dbname
            uid = self.env.uid

            def delete_scenes_from_ha_thread():
                """Background thread function to delete scenes from HA."""
                try:
                    from odoo import registry
                    from odoo.sql_db import db_connect

                    with db_connect(db_name).cursor() as new_cr:
                        new_env = api.Environment(new_cr, uid, {})

                        # First, lookup IDs for scenes that need it
                        for scene_info in scenes_to_lookup:
                            try:
                                rest_api = HassRestApi(new_env, scene_info['ha_instance_id'])
                                ha_scene_id = rest_api.get_scene_config_id(scene_info['entity_id'])
                                if ha_scene_id:
                                    scenes_to_delete.append({
                                        'entity_id': scene_info['entity_id'],
                                        'ha_scene_id': ha_scene_id,
                                        'ha_instance_id': scene_info['ha_instance_id'],
                                    })
                                    _logger.info(
                                        f"Found ha_scene_id for {scene_info['entity_id']}: {ha_scene_id}"
                                    )
                                else:
                                    _logger.info(
                                        f"Scene {scene_info['entity_id']} has no config ID in HA "
                                        f"(may be a device-created scene like Hue), skipping HA deletion"
                                    )
                            except Exception as e:
                                _logger.warning(
                                    f"Failed to lookup scene config ID for {scene_info['entity_id']}: {e}"
                                )

                        # Now delete all scenes with known IDs
                        for scene_info in scenes_to_delete:
                            try:
                                rest_api = HassRestApi(new_env, scene_info['ha_instance_id'])
                                rest_api.delete_scene_config(scene_info['ha_scene_id'])
                                _logger.info(
                                    f"Deleted scene {scene_info['entity_id']} "
                                    f"(ha_scene_id={scene_info['ha_scene_id']}) from HA"
                                )
                            except Exception as e:
                                # Log error but don't fail - Odoo deletion was already successful
                                _logger.error(
                                    f"Failed to delete scene {scene_info['entity_id']} from HA: {e}"
                                )
                except Exception as e:
                    _logger.error(f"Error in background scene deletion thread: {e}")

            def start_delete_thread():
                """Postcommit callback to start the background thread."""
                thread = threading.Thread(
                    target=delete_scenes_from_ha_thread,
                    name=f"ha_scene_delete_{scenes_to_delete[0]['entity_id'] if scenes_to_delete else 'lookup'}",
                    daemon=True
                )
                thread.start()
                _logger.debug(f"Started background thread for HA scene deletion")

            self.env.cr.postcommit.add(start_delete_thread)

        return result

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
        scene_entity_ids_changed = 'scene_entity_ids' in vals
        blueprint_inputs_changed = 'blueprint_inputs' in vals

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

                # 當 scene_entity_ids 變更時，更新 Scene 到 HA
                if scene_entity_ids_changed and record.domain == 'scene':
                    _logger.info(f"Scene entity_ids changed for {record.entity_id}, triggering sync to HA")
                    _logger.debug(f"Scene {record.entity_id} has {len(record.scene_entity_ids)} entities: {record.scene_entity_ids.mapped('entity_id')}")
                    if record.scene_entity_ids:
                        try:
                            record._create_scene_in_ha()
                            _logger.info(f"Scene {record.entity_id} synced to HA successfully")
                        except Exception as e:
                            _logger.error(f"Failed to sync scene {record.entity_id} to HA: {e}", exc_info=True)
                    else:
                        _logger.info(f"Scene {record.entity_id} has no entities, skipping sync to HA")

                # 當 blueprint_inputs 變更時，更新 Automation/Script 到 HA
                if blueprint_inputs_changed and record.domain in ['automation', 'script']:
                    if record.is_blueprint_based:
                        _logger.info(f"Blueprint inputs changed for {record.entity_id}, triggering sync to HA")
                        try:
                            record._sync_blueprint_inputs_to_ha()
                            _logger.info(f"Blueprint inputs synced for {record.entity_id}")
                        except Exception as e:
                            _logger.error(f"Failed to sync blueprint inputs for {record.entity_id}: {e}", exc_info=True)
                    else:
                        _logger.warning(f"Blueprint inputs changed for non-blueprint entity {record.entity_id}, skipping sync")

        return result

    def _update_entity_area_in_ha(self, override_entity_id=None):
        """
        在 HA 中更新 Entity 的 area_id

        使用 WebSocket API: config/entity_registry/update
        參考: docs/homeassistant-api/websocket-message-logs/config_entity_registry_update.md

        當 follows_device_area = True 時，發送 area_id = null 給 HA，
        這會讓 HA 中的實體設定為「跟隨裝置分區」。

        IMPORTANT: This method uses direct WebSocket connection (via HassRestApi)
        instead of the queue-based WebSocketClient to avoid PostgreSQL serialization
        conflicts when called from background threads. The direct WebSocket approach
        creates a short-lived connection that doesn't involve database commits.

        Args:
            override_entity_id: Optional entity_id to use instead of self.entity_id.
                               This is needed for scenes where HA generates a different
                               entity_id than what Odoo has stored.
        """
        self.ensure_one()
        # Use override_entity_id if provided (for scenes with HA-generated entity_id)
        effective_entity_id = override_entity_id or self.entity_id
        _logger.debug(f"[AREA_SYNC_EXEC] Starting _update_entity_area_in_ha for {effective_entity_id}")
        _logger.info(f"[AREA_SYNC_EXEC] Starting _update_entity_area_in_ha for {effective_entity_id}")
        _logger.info(f"[AREA_SYNC_EXEC] Self record: id={self.id}, entity_id={self.entity_id}, effective_entity_id={effective_entity_id}, area_id={self.area_id}, follows_device_area={self.follows_device_area}")
        _logger.debug(f"[AREA_SYNC_EXEC] Self record: id={self.id}, entity_id={self.entity_id}, effective_entity_id={effective_entity_id}, area_id={self.area_id}, follows_device_area={self.follows_device_area}")

        if not self.ha_instance_id:
            _logger.warning(f"[AREA_SYNC_EXEC] Cannot sync entity area {self.entity_id}: no HA instance")
            _logger.debug(f"[AREA_SYNC_EXEC] Cannot sync entity area {self.entity_id}: no HA instance")
            return

        try:
            # 當 follows_device_area = True 時，發送 null 給 HA（跟隨裝置分區）
            # 否則發送實體的 area_id
            if self.follows_device_area:
                ha_area_id = None
            else:
                ha_area_id = self.area_id.area_id if self.area_id else None

            _logger.info(f"[AREA_SYNC_EXEC] Using direct WebSocket for entity_registry/update")
            _logger.debug(f"[AREA_SYNC_EXEC] Using direct WebSocket for entity_registry/update")

            # Use direct WebSocket via HassRestApi to avoid database queue conflicts
            rest_api = HassRestApi(self.env, self.ha_instance_id.id)

            _logger.info(f"[AREA_SYNC_EXEC] Sending direct WebSocket update: entity_id={effective_entity_id}, area_id={ha_area_id}")
            _logger.debug(f"[AREA_SYNC_EXEC] Sending direct WebSocket update: entity_id={effective_entity_id}, area_id={ha_area_id}")

            result = rest_api.update_entity_registry(
                entity_id=effective_entity_id,
                area_id=ha_area_id
            )

            _logger.info(f"[AREA_SYNC_EXEC] Direct WebSocket result: {result}")
            _logger.debug(f"[AREA_SYNC_EXEC] Direct WebSocket result: {result}")

            if result and isinstance(result, dict):
                # Verify HA accepted the area change by checking the response
                returned_area = result.get('area_id')
                if returned_area == ha_area_id:
                    _logger.info(f"Entity {effective_entity_id} area updated in HA successfully: area_id={returned_area}")
                else:
                    # HA may reject area changes for device-owned entities
                    _logger.warning(
                        f"Entity {effective_entity_id} area update mismatch: "
                        f"sent area_id={ha_area_id}, HA returned area_id={returned_area}. "
                        f"This may occur for device-owned entities (e.g., Hue scenes)."
                    )
            else:
                _logger.warning(f"Unexpected result from HA for {effective_entity_id}: {result}")

        except Exception as e:
            _logger.error(f"Failed to update entity area {effective_entity_id} in HA: {e}", exc_info=True)
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

    def _update_entity_labels_in_ha(self, override_entity_id=None):
        """
        在 HA 中更新 Entity 的 labels

        使用 WebSocket API: config/entity_registry/update
        HA Entity Registry 的 labels 欄位是 label_id 陣列

        IMPORTANT: This method uses direct WebSocket connection (via HassRestApi)
        instead of the queue-based WebSocketClient to avoid PostgreSQL serialization
        conflicts when called from background threads.

        Args:
            override_entity_id: Optional entity_id to use instead of self.entity_id.
                               This is needed for scenes where HA generates a different
                               entity_id than what Odoo has stored.
        """
        self.ensure_one()
        # Use override_entity_id if provided (for scenes with HA-generated entity_id)
        effective_entity_id = override_entity_id or self.entity_id

        if not self.ha_instance_id:
            _logger.warning(f"Cannot sync entity labels {effective_entity_id}: no HA instance")
            return

        try:
            # Convert Odoo label_ids (Many2many) to HA labels (label_id array)
            ha_labels = self.label_ids.mapped('label_id') if self.label_ids else []

            _logger.info(f"Updating entity labels in HA: {effective_entity_id} -> labels={ha_labels}")

            # Use direct WebSocket via HassRestApi to avoid database queue conflicts
            rest_api = HassRestApi(self.env, self.ha_instance_id.id)
            result = rest_api.update_entity_registry(
                entity_id=effective_entity_id,
                labels=ha_labels
            )

            if result and isinstance(result, dict):
                _logger.info(f"Entity {effective_entity_id} labels updated in HA successfully")
            else:
                _logger.warning(f"Unexpected result from HA: {result}")

        except Exception as e:
            _logger.error(f"Failed to update entity labels {effective_entity_id} in HA: {e}", exc_info=True)
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

                # 同步 Scene 的實體清單（從 Scene attributes.entity_id 取得）
                self._sync_scene_entity_relations(instance_id)

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

    def _sync_scene_entity_relations(self, instance_id):
        """
        同步 Scene 的實體清單關聯
        從 Scene 的 attributes.entity_id 取得包含的實體清單並更新 scene_entity_ids
        同時也同步 ha_scene_id（HA 場景的數字 ID）

        Home Assistant Scene 的 attributes 中包含 entity_id 欄位，
        這是一個包含 Scene 所控制的所有實體 ID 的列表。
        attributes 中的 'id' 欄位是場景的配置 ID（用於 GUI 編輯）。

        Args:
            instance_id: HA 實例 ID
        """
        _logger.info(f"=== Starting sync scene entity relations (instance {instance_id}) ===")

        try:
            # 查找所有 Scene 實體
            scenes = self.env['ha.entity'].sudo().search([
                ('domain', '=', 'scene'),
                ('ha_instance_id', '=', instance_id)
            ])

            if not scenes:
                _logger.debug("No scene entities found to sync")
                return

            _logger.info(f"Found {len(scenes)} scene entities to sync")

            # 建立 entity_id -> ha.entity record ID 的映射（只包含此實例的 entities）
            all_entities = self.env['ha.entity'].sudo().search([
                ('ha_instance_id', '=', instance_id),
                ('domain', '!=', 'scene')  # Scene 不能包含其他 Scene
            ])
            entity_map = {entity.entity_id: entity.id for entity in all_entities}
            _logger.debug(f"Entity map size: {len(entity_map)} entities")

            updated_count = 0
            ha_scene_id_updated_count = 0
            for scene in scenes:
                try:
                    # 從 Scene 的 attributes 中取得資訊
                    attributes = scene.attributes or {}
                    ha_entity_ids = attributes.get('entity_id', [])
                    # HA scene 的 'id' 欄位（數字時間戳，用於 GUI 編輯）
                    ha_scene_id_from_attr = attributes.get('id')

                    if not isinstance(ha_entity_ids, list):
                        # 有時可能是單一字串
                        ha_entity_ids = [ha_entity_ids] if ha_entity_ids else []

                    # 將 HA entity_id 轉換為 Odoo record IDs
                    odoo_entity_ids = []
                    for ha_entity_id in ha_entity_ids:
                        if ha_entity_id in entity_map:
                            odoo_entity_ids.append(entity_map[ha_entity_id])
                        else:
                            _logger.debug(f"Scene {scene.entity_id}: entity {ha_entity_id} not found in map")

                    # 準備更新資料
                    update_vals = {}

                    # 比較並更新 scene_entity_ids
                    current_ids = set(scene.scene_entity_ids.ids)
                    new_ids = set(odoo_entity_ids)

                    if current_ids != new_ids:
                        update_vals['scene_entity_ids'] = [(6, 0, odoo_entity_ids)]
                        updated_count += 1
                        _logger.debug(
                            f"Updated scene {scene.entity_id}: "
                            f"{len(current_ids)} -> {len(new_ids)} entities"
                        )

                    # 同步 ha_scene_id（如果 HA 有提供且 Odoo 尚未有）
                    if ha_scene_id_from_attr and not scene.ha_scene_id:
                        update_vals['ha_scene_id'] = str(ha_scene_id_from_attr)
                        ha_scene_id_updated_count += 1
                        _logger.debug(
                            f"Synced ha_scene_id for {scene.entity_id}: {ha_scene_id_from_attr}"
                        )

                    if update_vals:
                        scene.with_context(from_ha_sync=True).write(update_vals)

                except Exception as e:
                    _logger.error(f"Error syncing scene {scene.entity_id} entities: {e}")

            _logger.info(
                f"Scene entity relations sync completed (instance {instance_id}): "
                f"{updated_count} scene entity lists updated, {ha_scene_id_updated_count} ha_scene_ids synced"
            )

        except Exception as e:
            _logger.error(f"Failed to sync scene entity relations: {e}", exc_info=True)

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

    # ========== Scene-specific Methods ==========

    def action_activate_scene(self):
        """
        Activate a scene in Home Assistant.

        Calls HA service: scene.turn_on
        Only applicable for entities with domain='scene'.
        """
        self.ensure_one()

        if self.domain != 'scene':
            raise ValidationError(_('This action is only available for scene entities.'))

        if not self.ha_instance_id:
            raise ValidationError(_('No HA instance configured for this entity.'))

        try:
            from odoo.addons.odoo_ha_addon.models.common.websocket_client import get_websocket_client
            client = get_websocket_client(self.env, instance_id=self.ha_instance_id.id)

            payload = {
                'domain': 'scene',
                'service': 'turn_on',
                'target': {
                    'entity_id': self.entity_id
                }
            }

            _logger.info(f"Activating scene: {self.entity_id}")
            client.call_websocket_api_sync('call_service', payload)
            _logger.info(f"Scene {self.entity_id} activated successfully")

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Scene Activated'),
                    'message': _('Scene "%s" has been activated.') % (self.name or self.entity_id),
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            _logger.error(f"Failed to activate scene {self.entity_id}: {e}", exc_info=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Activation Failed'),
                    'message': _('Failed to activate scene: %s') % str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def action_sync_scene_to_ha(self):
        """
        Public action to sync scene to Home Assistant.
        This creates/updates the scene in HA with current entity states.

        Can be called from UI button or programmatically.
        """
        self.ensure_one()

        if self.domain != 'scene':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('This action is only available for scenes.'),
                    'type': 'warning',
                }
            }

        if not self.scene_entity_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Entities'),
                    'message': _('Please add entities to the scene before syncing.'),
                    'type': 'warning',
                }
            }

        try:
            self._create_scene_in_ha()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Scene Synced'),
                    'message': _('Scene "%s" has been synced to Home Assistant.') % (self.name or self.entity_id),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sync Failed'),
                    'message': _('Failed to sync scene: %s') % str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def action_batch_sync_scenes_to_ha(self):
        """
        Batch action to sync multiple scenes to Home Assistant.

        This is useful for re-syncing existing scenes to ensure they have
        the correct metadata (entity_only: true) for proper display in HA.

        Can be called from:
        - Tree view action menu (multi-select)
        - Server action
        - Programmatically
        """
        scenes = self.filtered(lambda r: r.domain == 'scene')

        if not scenes:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Scenes Selected'),
                    'message': _('Please select scene entities to sync.'),
                    'type': 'warning',
                }
            }

        success_count = 0
        failed_scenes = []
        skipped_scenes = []

        for scene in scenes:
            if not scene.scene_entity_ids:
                skipped_scenes.append(scene.name or scene.entity_id)
                continue

            try:
                scene._create_scene_in_ha()
                success_count += 1
            except Exception as e:
                _logger.error(f"Failed to sync scene {scene.entity_id}: {e}")
                failed_scenes.append(f"{scene.name or scene.entity_id}: {str(e)}")

        # Build result message
        messages = []
        if success_count:
            messages.append(_('%d scene(s) synced successfully.') % success_count)
        if skipped_scenes:
            messages.append(_('Skipped (no entities): %s') % ', '.join(skipped_scenes))
        if failed_scenes:
            messages.append(_('Failed: %s') % ', '.join(failed_scenes))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Batch Scene Sync Complete'),
                'message': ' '.join(messages),
                'type': 'success' if not failed_scenes else 'warning',
                'sticky': bool(failed_scenes),
            }
        }

    def _create_scene_in_ha(self):
        """
        Create or update a scene in Home Assistant via config API.

        Uses the /api/config/scene/config/{id} endpoint to create scenes
        that are editable in the HA GUI (stored in scenes.yaml).

        IMPORTANT: HA requires a numeric timestamp ID (e.g., '1709123456789') for scenes
        to be editable in the GUI. This is how the HA frontend creates scenes.

        This method:
        1. Generates or reuses a numeric ha_scene_id (timestamp format)
        2. Gets current states of all scene entities
        3. Creates/updates scene config via HA config API
        4. Scene will be editable in HA Settings > Automations & Scenes

        Uses REST API to avoid WebSocket connection issues in async contexts.
        Only applicable for entities with domain='scene'.
        """
        self.ensure_one()

        if self.domain != 'scene':
            return

        if not self.ha_instance_id or not self.scene_entity_ids:
            _logger.warning(f"Cannot create scene {self.entity_id}: missing instance or entities")
            return

        try:
            import time

            rest_api = HassRestApi(self.env, self.ha_instance_id.id)

            # Generate or reuse numeric HA scene ID (timestamp in milliseconds)
            # This format matches how HA frontend creates scenes
            if not self.ha_scene_id:
                # Generate new timestamp ID
                ha_scene_id = str(int(time.time() * 1000))
                # Save it for future updates
                self.sudo().write({'ha_scene_id': ha_scene_id})
                _logger.info(f"Generated new ha_scene_id for {self.entity_id}: {ha_scene_id}")
            else:
                ha_scene_id = self.ha_scene_id
                _logger.info(f"Reusing existing ha_scene_id for {self.entity_id}: {ha_scene_id}")

            # Get entity_ids for the scene
            entity_ids = self.scene_entity_ids.mapped('entity_id')

            # Get current states of all entities
            _logger.info(f"Getting current states for scene entities: {entity_ids}")
            entity_states = rest_api.get_entity_states(entity_ids)
            _logger.debug(f"Entity states for scene {self.entity_id}: {entity_states}")

            if not entity_states:
                _logger.warning(f"No entity states retrieved for scene {self.entity_id}, skipping sync")
                return

            # Create scene config via HA config API (editable in GUI)
            scene_name = self.name or self.entity_id.replace('scene.', '')
            _logger.info(f"Creating scene config in HA: ha_scene_id={ha_scene_id}, name={scene_name}, entities={len(entity_states)}")
            result = rest_api.create_scene_config(
                ha_scene_id=ha_scene_id,
                name=scene_name,
                entities=entity_states
            )
            _logger.info(f"Scene {self.entity_id} (ha_scene_id={ha_scene_id}) created in HA successfully. Result: {result}")

            # HA generates entity_id based on scene name, which may differ from Odoo's entity_id
            # We need to fetch the actual entity_id from HA and update Odoo
            # Wait briefly for HA to register the scene, then query for it
            import time as time_module
            time_module.sleep(0.5)  # Brief delay for HA to process

            ha_entity_id = rest_api.get_scene_entity_id_by_config_id(ha_scene_id)
            if ha_entity_id and ha_entity_id != self.entity_id:
                old_entity_id = self.entity_id
                # Update entity_id to match HA's generated ID
                self.sudo().with_context(from_ha_sync=True).write({'entity_id': ha_entity_id})
                # Note: Do NOT call self.env.cr.commit() here - let the caller handle transaction
                # This method is called from postcommit callback which manages its own transaction
                # Invalidate cache to refresh entity_id for subsequent operations
                self.invalidate_recordset(['entity_id'])
                _logger.info(f"Updated entity_id from '{old_entity_id}' to '{ha_entity_id}' to match HA")
            elif ha_entity_id:
                _logger.info(f"Scene entity_id '{ha_entity_id}' matches Odoo, no update needed")
            else:
                _logger.warning(f"Could not determine HA entity_id for scene {ha_scene_id}, keeping '{self.entity_id}'")

            # Sync area_id to HA via entity_registry/update
            # Scene area is managed at entity registry level, not in scene config
            # Refresh the record to ensure we have latest data after the ha_scene_id write
            self.invalidate_recordset()
            _logger.debug(f"[AREA_SYNC_CREATE] Starting area sync for scene")

            # CRITICAL: Use the HA-confirmed entity_id for Area/Label sync
            # After scene creation, HA may generate a different entity_id than what Odoo has
            # We must use the actual HA entity_id for entity_registry/update calls
            current_area = self.area_id
            # Use ha_entity_id if available, otherwise fall back to self.entity_id
            current_entity_id = ha_entity_id if ha_entity_id else self.entity_id
            _logger.info(f"[AREA_SYNC_CREATE] Scene {current_entity_id} - area_id record: {current_area}, "
                        f"ha_area_id: {current_area.area_id if current_area else None}, "
                        f"ha_instance_id: {self.ha_instance_id.id if self.ha_instance_id else None}")
            _logger.debug(f"[AREA_SYNC_CREATE] Scene {current_entity_id} - area_id record: {current_area}, "
                        f"ha_area_id: {current_area.area_id if current_area else None}")

            if current_area:
                try:
                    _logger.info(f"[AREA_SYNC_CREATE] Calling _update_entity_area_in_ha for {current_entity_id} with area {current_area.area_id}")
                    _logger.debug(f"[AREA_SYNC_CREATE] Calling _update_entity_area_in_ha for {current_entity_id} with area {current_area.area_id}")
                    # Pass the HA-confirmed entity_id to ensure correct API call
                    self._update_entity_area_in_ha(override_entity_id=current_entity_id)
                    _logger.info(f"[AREA_SYNC_CREATE] Scene {current_entity_id} area synced to HA successfully: {current_area.area_id}")
                    _logger.debug(f"[AREA_SYNC_CREATE] Scene {current_entity_id} area synced to HA successfully: {current_area.area_id}")
                except Exception as area_error:
                    # Log warning but don't fail the entire scene creation
                    _logger.warning(f"[AREA_SYNC_CREATE] Scene {current_entity_id} created but area sync failed: {area_error}", exc_info=True)
                    _logger.debug(f"[AREA_SYNC_CREATE] Scene {current_entity_id} area sync FAILED: {area_error}")
            else:
                _logger.info(f"[AREA_SYNC_CREATE] Scene {current_entity_id} has no area_id, skipping area sync")
                _logger.debug(f"[AREA_SYNC_CREATE] Scene {current_entity_id} has no area_id, skipping area sync")

            # Sync labels to HA if any
            if self.label_ids:
                try:
                    # Pass the HA-confirmed entity_id to ensure correct API call
                    self._update_entity_labels_in_ha(override_entity_id=current_entity_id)
                    _logger.info(f"Scene {current_entity_id} labels synced to HA")
                except Exception as label_error:
                    _logger.warning(f"Scene {current_entity_id} created but label sync failed: {label_error}")

        except Exception as e:
            _logger.error(f"Failed to create scene {self.entity_id} in HA: {e}", exc_info=True)
            raise

    def _delete_scene_in_ha(self):
        """
        Delete a scene from Home Assistant via config API.

        Uses the DELETE /api/config/scene/config/{ha_scene_id} endpoint.
        Only applicable for entities with domain='scene' that have ha_scene_id set.
        """
        self.ensure_one()

        if self.domain != 'scene':
            return

        if not self.ha_instance_id:
            _logger.warning(f"Cannot delete scene {self.entity_id}: missing instance")
            return

        if not self.ha_scene_id:
            _logger.warning(f"Cannot delete scene {self.entity_id}: no ha_scene_id (scene may not exist in HA)")
            return

        try:
            rest_api = HassRestApi(self.env, self.ha_instance_id.id)

            _logger.info(f"Deleting scene config from HA: {self.entity_id} (ha_scene_id={self.ha_scene_id})")
            rest_api.delete_scene_config(self.ha_scene_id)
            _logger.info(f"Scene {self.entity_id} (ha_scene_id={self.ha_scene_id}) deleted from HA successfully")

            # Clear ha_scene_id after successful deletion
            self.sudo().write({'ha_scene_id': False})

        except Exception as e:
            _logger.error(f"Failed to delete scene {self.entity_id} from HA: {e}", exc_info=True)

    def _sync_scene_to_ha_internal(self):
        """
        Internal method for syncing a scene to Home Assistant.

        This method is called from a background thread with its own database connection,
        ensuring complete isolation from the main Odoo transaction.

        The method handles:
        1. Scene creation/update via REST API (config/scene/config endpoint)
        2. Area synchronization via WebSocket API (config/entity_registry/update)
        3. Label synchronization via WebSocket API (config/entity_registry/update)

        Design rationale:
        - Called from background thread started via postcommit callback
        - Uses fresh db_connect() cursor, completely isolated from main transaction
        - WebSocketClient's internal commits won't conflict with Odoo's transaction
        - REST API for scene creation is reliable and doesn't involve transaction issues

        Note: This method is specifically designed to be called from the background
        sync thread in create(). Direct calls from other contexts should use
        _create_scene_in_ha() directly.
        """
        self.ensure_one()

        if self.domain != 'scene':
            _logger.warning(f"_sync_scene_to_ha_internal called on non-scene entity: {self.entity_id}")
            return

        _logger.info(f"[SYNC_INTERNAL] Starting scene sync for {self.entity_id}")
        _logger.debug(f"[SYNC_INTERNAL] Starting scene sync for {self.entity_id}")

        # Delegate to the existing method which handles:
        # 1. Scene creation via REST API
        # 2. Entity ID synchronization (HA may generate different ID)
        # 3. Area sync via WebSocket
        # 4. Label sync via WebSocket
        self._create_scene_in_ha()

        _logger.info(f"[SYNC_INTERNAL] Scene sync completed for {self.entity_id}")
        _logger.debug(f"[SYNC_INTERNAL] Scene sync completed for {self.entity_id}")

    # ========== Blueprint Sync Methods ==========

    def action_sync_blueprint_from_ha(self):
        """
        Sync blueprint configuration from Home Assistant.

        Fetches the automation/script config and blueprint metadata from HA
        and updates the local blueprint_* fields.

        Only applicable for blueprint-based automation/script entities.
        """
        self.ensure_one()

        if self.domain not in ['automation', 'script']:
            raise ValidationError(_('This action is only available for automation/script entities.'))

        if not self.ha_instance_id:
            raise ValidationError(_('No HA instance configured for this entity.'))

        try:
            self._sync_blueprint_config_from_ha()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Blueprint Refreshed'),
                    'message': _('Blueprint configuration for "%s" has been refreshed from Home Assistant.') % (self.name or self.entity_id),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            _logger.error(f"Failed to sync blueprint for {self.entity_id}: {e}", exc_info=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sync Failed'),
                    'message': _('Failed to refresh blueprint: %s') % str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def _sync_blueprint_config_from_ha(self):
        """
        Internal method to sync blueprint configuration from Home Assistant.

        Fetches:
        1. Automation/script config to get use_blueprint.path and use_blueprint.input
        2. Blueprint metadata from blueprint/list WebSocket command

        Updates: blueprint_path, blueprint_inputs, blueprint_metadata, ha_automation_id
        """
        self.ensure_one()

        if self.domain not in ['automation', 'script']:
            return

        if not self.ha_instance_id:
            _logger.warning(f"Cannot sync blueprint for {self.entity_id}: no HA instance")
            return

        rest_api = HassRestApi(self.env, self.ha_instance_id.id)

        # Get config_id from attributes - HA stores the actual config ID in the 'id' attribute
        config_id = None
        _logger.info(f"[Blueprint Sync] Processing {self.entity_id}, attributes type: {type(self.attributes)}")

        # For fields.Json, Odoo automatically deserializes JSONB to Python dict
        if self.attributes:
            attrs = self.attributes
            _logger.info(f"[Blueprint Sync] Attributes for {self.entity_id}: {attrs}")
            if isinstance(attrs, dict):
                config_id = attrs.get('id')
                _logger.info(f"[Blueprint Sync] Got config_id from attributes: {config_id}")

        # Fallback: Extract from entity_id if attributes don't have id
        if not config_id:
            entity_id_parts = self.entity_id.split('.', 1)
            if len(entity_id_parts) == 2:
                config_id = entity_id_parts[1]
                _logger.info(f"[Blueprint Sync] Using fallback config_id from entity_id: {config_id}")

        if not config_id:
            _logger.warning(f"Cannot determine config_id for {self.entity_id}")
            return

        vals = {'ha_automation_id': str(config_id)}
        _logger.info(f"[Blueprint Sync] Fetching config for {self.entity_id} with config_id: {config_id}")

        # Fetch automation/script config
        if self.domain == 'automation':
            config = rest_api.get_automation_config(config_id)
        else:
            config = rest_api.get_script_config(config_id)

        if not config:
            _logger.warning(f"[Blueprint Sync] Could not fetch config for {self.entity_id} (config_id={config_id})")
            # Clear blueprint fields if config not found
            vals.update({
                'blueprint_path': False,
                'blueprint_inputs': False,
                'blueprint_metadata': False,
            })
            self.sudo().write(vals)
            return

        _logger.info(f"[Blueprint Sync] Config fetched for {self.entity_id}: {config}")

        # Check if it's blueprint-based
        if 'use_blueprint' in config:
            blueprint_info = config['use_blueprint']
            blueprint_path = blueprint_info.get('path', '')
            blueprint_inputs = blueprint_info.get('input', {})

            vals['blueprint_path'] = blueprint_path
            vals['blueprint_inputs'] = json.dumps(blueprint_inputs, ensure_ascii=False, indent=2)

            # Fetch blueprint metadata
            try:
                blueprints = rest_api.get_blueprint_list(self.domain)
                if blueprint_path in blueprints:
                    blueprint_data = blueprints[blueprint_path]
                    # The blueprint list returns metadata under 'metadata' key
                    metadata = blueprint_data.get('metadata', blueprint_data)
                    vals['blueprint_metadata'] = json.dumps(metadata, ensure_ascii=False, indent=2)
                else:
                    _logger.warning(f"Blueprint {blueprint_path} not found in blueprint list")
                    vals['blueprint_metadata'] = False
            except Exception as e:
                _logger.warning(f"Failed to fetch blueprint metadata: {e}")
                vals['blueprint_metadata'] = False
        else:
            # Not blueprint-based
            _logger.info(f"[Blueprint Sync] {self.entity_id} is NOT blueprint-based (no use_blueprint in config)")
            vals.update({
                'blueprint_path': False,
                'blueprint_inputs': False,
                'blueprint_metadata': False,
            })

        self.sudo().write(vals)
        _logger.info(f"[Blueprint Sync] Wrote vals to {self.entity_id}: blueprint_path={vals.get('blueprint_path', 'N/A')}")

    def _sync_blueprint_inputs_to_ha(self):
        """
        Sync modified blueprint inputs back to Home Assistant.

        This method:
        1. Reads current automation/script config from HA
        2. Updates the use_blueprint.input with new values
        3. Posts the updated config back to HA

        Only applicable for blueprint-based automation/script entities.
        """
        self.ensure_one()

        if self.domain not in ['automation', 'script']:
            return

        if not self.ha_instance_id:
            _logger.warning(f"Cannot sync blueprint inputs for {self.entity_id}: no HA instance")
            return

        if not self.blueprint_path:
            _logger.warning(f"Cannot sync blueprint inputs for {self.entity_id}: not blueprint-based")
            return

        # Get or extract the HA config ID
        config_id = self.ha_automation_id
        if not config_id:
            # Try to extract from entity_id
            entity_id_parts = self.entity_id.split('.', 1)
            if len(entity_id_parts) == 2:
                config_id = entity_id_parts[1]
                self.sudo().write({'ha_automation_id': config_id})
            else:
                _logger.warning(f"Cannot determine automation/script ID for {self.entity_id}")
                return

        rest_api = HassRestApi(self.env, self.ha_instance_id.id)

        # Parse the blueprint inputs
        try:
            inputs = json.loads(self.blueprint_inputs) if self.blueprint_inputs else {}
        except json.JSONDecodeError as e:
            _logger.error(f"Invalid blueprint_inputs JSON for {self.entity_id}: {e}")
            raise ValidationError(_('Invalid blueprint inputs JSON format.'))

        # Fetch current config to preserve other fields
        if self.domain == 'automation':
            current_config = rest_api.get_automation_config(config_id)
        else:
            current_config = rest_api.get_script_config(config_id)

        if not current_config:
            _logger.warning(f"Could not fetch current config for {self.entity_id}")
            raise ValidationError(_('Could not fetch current configuration from Home Assistant.'))

        # Update the use_blueprint.input
        if 'use_blueprint' not in current_config:
            current_config['use_blueprint'] = {}

        current_config['use_blueprint']['path'] = self.blueprint_path
        current_config['use_blueprint']['input'] = inputs

        # Post updated config
        try:
            if self.domain == 'automation':
                rest_api.update_automation_config(config_id, current_config)
            else:
                rest_api.update_script_config(config_id, current_config)

            _logger.info(f"Blueprint inputs synced to HA for {self.entity_id}")
        except Exception as e:
            _logger.error(f"Failed to sync blueprint inputs to HA for {self.entity_id}: {e}")
            raise

    def _sync_automation_blueprint_configs(self, instance_id):
        """
        同步所有 Automation/Script 的 Blueprint 配置
        從 HA 取得 automation/script config，檢測 use_blueprint 並更新本地欄位

        Args:
            instance_id: HA 實例 ID
        """
        _logger.debug(f"[BLUEPRINT DEBUG] _sync_automation_blueprint_configs CALLED for instance {instance_id}")
        _logger.info(f"=== Starting sync automation/script blueprint configs (instance {instance_id}) ===")

        try:
            # 查找所有 automation/script entities for this instance
            entities = self.env['ha.entity'].sudo().search([
                ('ha_instance_id', '=', instance_id),
                ('domain', 'in', ['automation', 'script']),
            ])

            if not entities:
                _logger.info("No automation/script entities found, skipping blueprint sync")
                return

            _logger.info(f"Found {len(entities)} automation/script entities to check for blueprints")

            updated_count = 0
            for entity in entities:
                try:
                    # 使用現有的 _sync_blueprint_config_from_ha 方法
                    entity._sync_blueprint_config_from_ha()

                    # 檢查是否有 blueprint_path 被設定
                    if entity.blueprint_path:
                        updated_count += 1
                        _logger.debug(f"Blueprint detected for {entity.entity_id}: {entity.blueprint_path}")

                except Exception as e:
                    _logger.warning(f"Failed to sync blueprint for {entity.entity_id}: {e}")
                    continue

            _logger.info(
                f"Blueprint config sync completed (instance {instance_id}): "
                f"{updated_count}/{len(entities)} entities have blueprint configurations"
            )

        except Exception as e:
            _logger.error(f"Failed to sync automation blueprint configs: {e}", exc_info=True)


