import logging

_logger = logging.getLogger(__name__)

def _check_python_dependencies():
    """
    檢查必要的 Python 依賴是否已安裝
    如果缺少依賴，將自動安裝
    """
    import subprocess
    import sys

    _logger.info("Checking Python dependencies for Home Assistant WebSocket integration")

    required_packages = {
        'websockets': 'websockets>=10.0',
    }

    missing_packages = []

    for package, pip_spec in required_packages.items():
        try:
            __import__(package)
            _logger.info(f"✓ {package} is installed")
        except ImportError:
            _logger.warning(f"✗ Missing required package: {package}")
            missing_packages.append(pip_spec)

    if missing_packages:
        _logger.info("=" * 60)
        _logger.info("Auto-installing missing Python packages...")
        _logger.info("=" * 60)

        for pip_spec in missing_packages:
            try:
                _logger.info(f"Installing {pip_spec}...")
                # Use --break-system-packages for Debian/Ubuntu externally-managed Python
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install',
                    '--break-system-packages', pip_spec
                ])
                _logger.info(f"✓ Successfully installed {pip_spec}")
            except subprocess.CalledProcessError as e:
                _logger.error(f"✗ Failed to install {pip_spec}: {e}")
                # Fallback: try without --break-system-packages
                try:
                    subprocess.check_call([
                        sys.executable, '-m', 'pip', 'install', pip_spec
                    ])
                    _logger.info(f"✓ Successfully installed {pip_spec} (fallback)")
                except subprocess.CalledProcessError as e2:
                    raise ImportError(
                        f"Failed to install {pip_spec}. "
                        f"Please install manually: pip install --break-system-packages {pip_spec}"
                    )

        # 重新檢查安裝是否成功
        for package in required_packages.keys():
            try:
                __import__(package)
                _logger.info(f"✓ {package} is now available")
            except ImportError:
                raise ImportError(
                    f"Package {package} was installed but cannot be imported. "
                    "Please restart Odoo."
                )

def pre_init_hook(cr):
    """
    在模組安裝前執行，檢查必要的 Python 依賴
    如果依賴缺失，將拋出錯誤並提供安裝指引
    """
    _check_python_dependencies()

def post_init_hook(env):
    """
    在模組安裝後執行的 Hook
    自動將 admin 用戶加入 HA Manager 群組，確保初次安裝後可以立即使用
    """
    _logger.info("=" * 60)
    _logger.info("Initializing Home Assistant addon...")
    _logger.info("=" * 60)

    try:
        # 取得 HA Manager 群組
        ha_manager_group = env.ref('odoo_ha_addon.group_ha_manager')

        # 取得 admin 用戶 (通常 login='admin' 且 id=2)
        admin_user = env.ref('base.user_admin')

        # 將 admin 加入 HA Manager 群組
        if admin_user and ha_manager_group:
            if ha_manager_group not in admin_user.groups_id:
                admin_user.write({'groups_id': [(4, ha_manager_group.id)]})
                _logger.info(f"✓ Added user '{admin_user.login}' to Home Assistant Manager group")
                _logger.info(f"  User can now access HA settings and configure instances")
            else:
                _logger.info(f"✓ User '{admin_user.login}' already has Home Assistant Manager permissions")
        else:
            _logger.warning("⚠ Could not find admin user or HA Manager group")
            _logger.warning("  Please manually grant 'Home Assistant Manager' permissions to users")

    except Exception as e:
        _logger.warning(f"⚠ Failed to auto-grant HA Manager permissions to admin: {e}")
        _logger.warning("  Please manually grant 'Home Assistant Manager' permissions via:")
        _logger.warning("  Settings > Users & Companies > Users > [Select User] > Administration tab")

    _logger.info("✓ Home Assistant WebSocket integration module installed successfully")
    _logger.info("=" * 60)

    # 自動把 admin 用戶加入 HA Manager 群組
    try:
        admin_user = env.ref('base.user_admin', raise_if_not_found=False)
        ha_manager_group = env.ref('odoo_ha_addon.group_ha_manager', raise_if_not_found=False)

        if admin_user and ha_manager_group:
            if ha_manager_group not in admin_user.groups_id:
                admin_user.write({'groups_id': [(4, ha_manager_group.id)]})
                _logger.info(f"✓ Added admin user to HA Manager group")
            else:
                _logger.info("Admin user already in HA Manager group")
        else:
            _logger.warning("Could not find admin user or HA Manager group")
    except Exception as e:
        _logger.warning(f"Failed to add admin to HA Manager group: {e}")

def uninstall_hook(env):
    """
    在模組卸載時執行的 Hook
    完整清理所有模組資料和配置
    """
    _logger.info("=" * 60)
    _logger.info("開始卸載 Home Assistant WebSocket integration")
    _logger.info("=" * 60)

    # 1. 停止 WebSocket 服務
    try:
        _logger.info("步驟 1/9: 停止所有 WebSocket 服務...")
        from odoo.addons.odoo_ha_addon.models.common.websocket_thread_manager import stop_websocket_service
        # Phase 2: 不傳參數會停止所有資料庫的所有 HA 實例
        stop_websocket_service()
        _logger.info("✓ 所有 WebSocket 服務已停止")
    except Exception as e:
        _logger.error(f"✗ 停止 WebSocket 服務失敗: {e}")

    # 2. 清理 WebSocket 請求佇列
    try:
        _logger.info("步驟 2/9: 清理 WebSocket 請求佇列...")
        queue_records = env['ha.ws.request.queue'].search([])
        queue_count = len(queue_records)
        queue_records.unlink()
        _logger.info(f"✓ 已刪除 {queue_count} 筆 WebSocket 請求佇列記錄")
    except Exception as e:
        _logger.warning(f"✗ 清理請求佇列失敗: {e}")

    # 3. 清理歷史資料
    try:
        _logger.info("步驟 3/9: 清理 Home Assistant 歷史資料...")
        history_records = env['ha.entity.history'].search([])
        history_count = len(history_records)
        history_records.unlink()
        _logger.info(f"✓ 已刪除 {history_count} 筆歷史記錄")
    except Exception as e:
        _logger.warning(f"✗ 清理歷史資料失敗: {e}")

    # 4. 清理實體群組標籤 (需在群組之前刪除)
    try:
        _logger.info("步驟 4/13: 清理 Home Assistant 實體群組標籤...")
        tag_records = env['ha.entity.group.tag'].search([])
        tag_count = len(tag_records)
        tag_records.unlink()
        _logger.info(f"✓ 已刪除 {tag_count} 筆實體群組標籤記錄")
    except Exception as e:
        _logger.warning(f"✗ 清理實體群組標籤失敗: {e}")

    # 5. 清理實體標籤 (需在實體之前刪除)
    try:
        _logger.info("步驟 5/13: 清理 Home Assistant 實體標籤...")
        entity_tag_records = env['ha.entity.tag'].search([])
        entity_tag_count = len(entity_tag_records)
        entity_tag_records.unlink()
        _logger.info(f"✓ 已刪除 {entity_tag_count} 筆實體標籤記錄")
    except Exception as e:
        _logger.warning(f"✗ 清理實體標籤失敗: {e}")

    # 6. 清理實體群組 (需在實體之前刪除)
    try:
        _logger.info("步驟 6/13: 清理 Home Assistant 實體群組...")
        group_records = env['ha.entity.group'].search([])
        group_count = len(group_records)
        group_records.unlink()
        _logger.info(f"✓ 已刪除 {group_count} 筆實體群組記錄")
    except Exception as e:
        _logger.warning(f"✗ 清理實體群組失敗: {e}")

    # 7. 清理實體資料
    try:
        _logger.info("步驟 7/13: 清理 Home Assistant 實體資料...")
        entity_records = env['ha.entity'].search([])
        entity_count = len(entity_records)
        entity_records.unlink()
        _logger.info(f"✓ 已刪除 {entity_count} 筆實體記錄")
    except Exception as e:
        _logger.warning(f"✗ 清理實體資料失敗: {e}")

    # 8. 清理設備資料 (需在區域之前刪除，因為設備參照區域)
    try:
        _logger.info("步驟 8/13: 清理 Home Assistant 設備資料...")
        device_records = env['ha.device'].search([])
        device_count = len(device_records)
        device_records.unlink()
        _logger.info(f"✓ 已刪除 {device_count} 筆設備記錄")
    except Exception as e:
        _logger.warning(f"✗ 清理設備資料失敗: {e}")

    # 9. 清理區域資料
    try:
        _logger.info("步驟 9/13: 清理 Home Assistant 區域資料...")
        area_records = env['ha.area'].search([])
        area_count = len(area_records)
        # 使用 from_ha_sync=True 防止同步刪除 HA 端資料
        area_records.with_context(from_ha_sync=True).unlink()
        _logger.info(f"✓ 已刪除 {area_count} 筆區域記錄")
    except Exception as e:
        _logger.warning(f"✗ 清理區域資料失敗: {e}")

    # 10. 清理標籤資料 (在設備和區域之後刪除)
    try:
        _logger.info("步驟 10/13: 清理 Home Assistant 標籤資料...")
        label_records = env['ha.label'].search([])
        label_count = len(label_records)
        # 使用 from_ha_sync=True 防止同步刪除 HA 端資料
        label_records.with_context(from_ha_sync=True).unlink()
        _logger.info(f"✓ 已刪除 {label_count} 筆標籤記錄")
    except Exception as e:
        _logger.warning(f"✗ 清理標籤資料失敗: {e}")

    # 11. 清理即時更新記錄
    try:
        _logger.info("步驟 11/13: 清理 Home Assistant 即時更新記錄...")
        realtime_records = env['ha.realtime.update'].search([])
        realtime_count = len(realtime_records)
        realtime_records.unlink()
        _logger.info(f"✓ 已刪除 {realtime_count} 筆即時更新記錄")
    except Exception as e:
        _logger.warning(f"✗ 清理即時更新記錄失敗: {e}")

    # 12. 清理 HA 實例 (最後刪除，因為其他表都依賴它)
    try:
        _logger.info("步驟 12/13: 清理 Home Assistant 實例...")
        instance_records = env['ha.instance'].search([])
        instance_count = len(instance_records)
        if instance_count > 0:
            for instance in instance_records:
                _logger.info(f"  - 刪除實例: {instance.name} (ID: {instance.id})")
            instance_records.unlink()
            _logger.info(f"✓ 已刪除 {instance_count} 個 HA 實例")
        else:
            _logger.info("✓ 沒有需要清理的 HA 實例")
    except Exception as e:
        _logger.warning(f"✗ 清理 HA 實例失敗: {e}")

    # 13. 清理配置參數（清理所有 odoo_ha_addon. 開頭的參數）
    try:
        _logger.info("步驟 13/13: 清理配置參數...")
        params = env['ir.config_parameter'].search([('key', '=like', 'odoo_ha_addon.%')])
        param_count = len(params)
        if param_count > 0:
            for param in params:
                _logger.info(f"  - 刪除配置參數: {param.key}")
            params.unlink()
            _logger.info(f"✓ 已刪除 {param_count} 個配置參數")
        else:
            _logger.info("✓ 沒有需要清理的配置參數")
    except Exception as e:
        _logger.warning(f"✗ 清理配置參數失敗: {e}")

    _logger.info("=" * 60)
    _logger.info("✓ Home Assistant WebSocket integration 卸載完成")
    _logger.info("=" * 60)


def post_load_hook():
    """
    在 Odoo 模組載入後執行的 Hook
    這個 hook 會在每次 Odoo 重啟時執行
    用於檢查 Python 依賴並啟動 WebSocket 背景執行緒

    Phase 2: 支援多 HA 實例
    - 自動為每個資料庫啟動所有活躍的 HA 實例 WebSocket 服務
    - start_websocket_service(env) 會查找所有 active=True 的 ha.instance 並啟動
    """
    _logger.info("=" * 60)
    _logger.info("Post-load hook: Initializing Home Assistant WebSocket integration")
    _logger.info("=" * 60)

    # 每次重啟都檢查 Python 依賴（如果缺失會拋出錯誤）
    _check_python_dependencies()

    _logger.info("Starting WebSocket services for all active HA instances...")

    try:
        from odoo import api, SUPERUSER_ID
        from odoo.addons.odoo_ha_addon.models.common.websocket_thread_manager import start_websocket_service

        # 取得資料庫列表（通常只有一個）
        import odoo
        db_names = odoo.service.db.list_dbs(True)

        if not db_names:
            _logger.warning("No databases found, skipping WebSocket service start")
            return

        # 為每個資料庫啟動 WebSocket 服務
        for db_name in db_names:
            try:
                # Odoo 18: Environment.manage() 已被移除，直接使用 registry
                registry = odoo.registry(db_name)
                with registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})

                    # 檢查 addon 是否已安裝
                    if 'ha.entity' not in env:
                        _logger.info(f"odoo_ha_addon not installed in database {db_name}, skipping")
                        continue

                    # Phase 2: 啟動所有活躍實例的 WebSocket 服務
                    # 不傳 instance_id 參數，start_websocket_service 會自動啟動所有 active=True 的實例
                    # sudo: 系統啟動時無用戶上下文，需要存取所有實例
                    active_instances = env['ha.instance'].sudo().search([('active', '=', True)])
                    instance_count = len(active_instances)

                    if instance_count == 0:
                        _logger.info(f"No active HA instances found in database {db_name}, skipping")
                        continue

                    _logger.info(f"Found {instance_count} active HA instance(s) in database {db_name}")
                    start_websocket_service(env)
                    _logger.info(f"✓ WebSocket services started for {instance_count} instance(s)")

            except Exception as e:
                _logger.error(f"Failed to start WebSocket service for database {db_name}: {e}")

    except Exception as e:
        _logger.error(f"Error in post_load_hook: {e}", exc_info=True)