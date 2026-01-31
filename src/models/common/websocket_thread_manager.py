"""
WebSocket Thread Manager
管理在背景執行緒中運行的 WebSocket 服務
"""
import threading
import asyncio
import logging
from odoo import api, _

_logger = logging.getLogger(__name__)

# 全域變數：儲存多資料庫、多實例的執行緒和停止事件
# Phase 2 重構：雙層結構 {db_name: {instance_id: {'thread': ..., 'stop_event': ..., 'config': ...}}}
_websocket_connections = {}
_connections_lock = threading.Lock()  # 保護 _websocket_connections 的執行緒安全

# 重啟冷卻時間（秒）：防止短時間內重複重啟
_RESTART_COOLDOWN = 5


def _run_websocket_in_thread(db_name, instance_id, ha_url, ha_token, stop_event):
    """
    在執行緒中運行 WebSocket 服務
    這個函數會被 threading.Thread 調用

    Phase 2 重構：新增 instance_id 參數

    Args:
        db_name: 資料庫名稱
        instance_id: HA Instance ID (Phase 2 新增)
        ha_url: Home Assistant URL
        ha_token: Home Assistant Token
        stop_event: 該實例專用的停止事件
    """
    _logger.info(f"WebSocket thread started for database: {db_name}, instance: {instance_id}")

    try:
        # 延遲導入，避免循環依賴
        from .hass_websocket_service import HassWebSocketService

        # 建立新的 event loop（因為執行緒沒有 event loop）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # 建立服務實例（Phase 2: 傳入 instance_id）
        service = HassWebSocketService(
            env=None,
            db_name=db_name,
            ha_url=ha_url,
            ha_token=ha_token,
            instance_id=instance_id  # Phase 2: 新增 instance_id
        )

        # 運行服務直到停止事件被設置
        async def run_until_stopped():
            try:
                # 啟動 WebSocket 服務
                connect_task = asyncio.create_task(service.connect_and_listen())

                # 同時監聽該資料庫專用的停止事件
                while not stop_event.is_set():
                    await asyncio.sleep(1)

                # 收到停止信號，停止服務
                _logger.info(f"Stop signal received for {db_name} instance {instance_id}, shutting down WebSocket service...")
                service.stop()

                # 等待連線任務完成
                try:
                    await asyncio.wait_for(connect_task, timeout=5)
                except asyncio.TimeoutError:
                    _logger.warning(f"WebSocket service shutdown timed out for {db_name} instance {instance_id}")

            except Exception as e:
                _logger.error(f"Error in WebSocket service for {db_name} instance {instance_id}: {e}")

        # 運行 async 函數
        loop.run_until_complete(run_until_stopped())

    except Exception as e:
        _logger.error(f"Fatal error in WebSocket thread for {db_name} instance {instance_id}: {e}", exc_info=True)
    finally:
        _logger.info(f"WebSocket thread stopped for database: {db_name}, instance: {instance_id}")
        try:
            loop.close()
        except:
            pass

        # Phase 2: 清理雙層結構的連線記錄
        with _connections_lock:
            if db_name in _websocket_connections:
                if instance_id in _websocket_connections[db_name]:
                    del _websocket_connections[db_name][instance_id]
                    _logger.info(f"Cleaned up connection record for {db_name} instance {instance_id}")

                # 如果該資料庫沒有任何實例連接，移除整個資料庫條目
                if not _websocket_connections[db_name]:
                    del _websocket_connections[db_name]
                    _logger.info(f"Removed empty database entry for {db_name}")


def start_websocket_service(env, instance_id=None):
    """
    啟動 WebSocket 服務在背景執行緒中
    Phase 2 重構：支援多實例

    Args:
        env: Odoo environment
        instance_id: 特定實例 ID (可選)
            - 如果提供，只啟動該實例
            - 如果為 None，啟動所有活躍實例
    """
    db_name = env.cr.dbname

    # Phase 2: 取得要啟動的實例列表
    if instance_id:
        # 啟動特定實例
        instances = env['ha.instance'].sudo().browse(instance_id)
        if not instances.exists():
            _logger.warning(f"HA instance {instance_id} not found")
            return
    else:
        # 啟動所有活躍實例
        instances = env['ha.instance'].sudo().search([('active', '=', True)])

    if not instances:
        _logger.warning(f"No active HA instances found for database {db_name}")
        return

    # Phase 2: 為每個實例啟動 WebSocket 服務
    with _connections_lock:
        # 確保資料庫層級的字典存在
        if db_name not in _websocket_connections:
            _websocket_connections[db_name] = {}

        for instance in instances:
            # 檢查該實例是否已經有運行的連線
            if instance.id in _websocket_connections[db_name]:
                conn = _websocket_connections[db_name][instance.id]
                if conn['thread'].is_alive():
                    _logger.info(f"WebSocket service already running for {db_name} instance {instance.id} ({instance.name})")
                    continue

            # 取得實例配置
            ha_url = instance.api_url
            ha_token = instance.api_token

            if not ha_url or not ha_token:
                _logger.warning(
                    f"HA instance {instance.id} ({instance.name}) configuration incomplete, "
                    f"cannot start WebSocket service"
                )
                continue

            # 建立該實例專用的停止事件
            stop_event = threading.Event()

            # 建立並啟動執行緒
            thread = threading.Thread(
                target=_run_websocket_in_thread,
                args=(db_name, instance.id, ha_url, ha_token, stop_event),
                daemon=True,  # daemon thread 會在主程序結束時自動結束
                name=f"HomeAssistantWebSocket-{db_name}-Instance-{instance.id}"
            )

            # Phase 2: 儲存到雙層結構
            _websocket_connections[db_name][instance.id] = {
                'thread': thread,
                'stop_event': stop_event,
                'config': {
                    'ha_url': ha_url,
                    'ha_token': ha_token
                },
                'instance_name': instance.name  # 額外儲存名稱方便 debug
            }

            thread.start()
            _logger.info(
                f"WebSocket service thread started for {db_name} "
                f"instance {instance.id} ({instance.name}) with config: {ha_url}"
            )


def stop_websocket_service(db_name=None, instance_id=None):
    """
    停止 WebSocket 服務
    Phase 2 重構：支援多實例

    Args:
        db_name: 資料庫名稱（None 表示停止所有資料庫）
        instance_id: 實例 ID（None 表示停止該資料庫的所有實例）
    """
    with _connections_lock:
        if db_name is None:
            # 停止所有資料庫的所有連線
            if not _websocket_connections:
                _logger.info("No WebSocket connections to stop")
                return

            total_instances = sum(len(instances) for instances in _websocket_connections.values())
            _logger.info(
                f"Stopping all WebSocket connections "
                f"({len(_websocket_connections)} databases, {total_instances} instances)..."
            )

            # Phase 2: 遍歷所有資料庫和實例
            for db, instances_dict in list(_websocket_connections.items()):
                for inst_id, conn in list(instances_dict.items()):
                    _stop_single_connection(db, inst_id, conn)

        elif instance_id is None:
            # 停止特定資料庫的所有實例
            if db_name not in _websocket_connections:
                _logger.info(f"WebSocket service not running for database: {db_name}")
                return

            instances_dict = _websocket_connections[db_name]
            _logger.info(f"Stopping all WebSocket services for database: {db_name} ({len(instances_dict)} instances)...")

            for inst_id, conn in list(instances_dict.items()):
                _stop_single_connection(db_name, inst_id, conn)

        else:
            # 停止特定資料庫的特定實例
            if db_name not in _websocket_connections:
                _logger.info(f"WebSocket service not running for database: {db_name}")
                return

            if instance_id not in _websocket_connections[db_name]:
                _logger.info(f"WebSocket service not running for {db_name} instance {instance_id}")
                return

            _logger.info(f"Stopping WebSocket service for {db_name} instance {instance_id}...")
            conn = _websocket_connections[db_name][instance_id]
            _stop_single_connection(db_name, instance_id, conn)


def _stop_single_connection(db_name, instance_id, conn):
    """
    停止單一實例的 WebSocket 連線
    Phase 2 重構：支援實例參數

    Args:
        db_name: 資料庫名稱
        instance_id: 實例 ID
        conn: 連線資訊字典 {'thread': Thread, 'stop_event': Event, 'config': dict}
    """
    stop_event = conn['stop_event']
    thread = conn['thread']
    instance_name = conn.get('instance_name', f'Instance-{instance_id}')

    stop_event.set()

    # 等待執行緒結束（最多 10 秒）
    thread.join(timeout=10)

    if thread.is_alive():
        _logger.warning(f"WebSocket thread for {db_name} instance {instance_id} ({instance_name}) did not stop gracefully")
    else:
        _logger.info(f"WebSocket service stopped successfully for {db_name} instance {instance_id} ({instance_name})")

    # Phase 2: 清理雙層結構的連線記錄
    if db_name in _websocket_connections:
        if instance_id in _websocket_connections[db_name]:
            del _websocket_connections[db_name][instance_id]

        # 如果該資料庫沒有任何實例，移除整個資料庫條目
        if not _websocket_connections[db_name]:
            del _websocket_connections[db_name]


def is_websocket_service_running(env=None, instance_id=None):
    """
    檢查 WebSocket 服務是否在運行
    Phase 2 重構：支援多實例檢查

    Args:
        env: Odoo environment (optional, for cross-process check)
        instance_id: 特定實例 ID (可選)
            - 如果提供，檢查特定實例是否在運行
            - 如果為 None，檢查是否有任何實例在運行

    Returns:
        bool: True if running, False otherwise
    """
    import os

    # 如果沒有 env，只能檢查本 process 的連線
    if env is None:
        with _connections_lock:
            if instance_id:
                # 檢查特定實例
                for db_instances in _websocket_connections.values():
                    if instance_id in db_instances:
                        return db_instances[instance_id]['thread'].is_alive()
                return False
            else:
                # 檢查是否有任何實例
                total = sum(len(instances) for instances in _websocket_connections.values())
                _logger.debug(f"[PID {os.getpid()}] No env provided, checking local connections: {total} instances")
                return total > 0

    db_name = env.cr.dbname

    # Phase 2: 如果在主 process，直接檢查執行緒狀態
    with _connections_lock:
        if db_name in _websocket_connections:
            instances_dict = _websocket_connections[db_name]

            if instance_id:
                # 檢查特定實例
                if instance_id in instances_dict:
                    is_alive = instances_dict[instance_id]['thread'].is_alive()
                    _logger.debug(
                        f"[PID {os.getpid()}] Found instance {instance_id} for {db_name}, "
                        f"thread is_alive={is_alive}"
                    )
                    return is_alive
                else:
                    _logger.debug(f"[PID {os.getpid()}] Instance {instance_id} not found in {db_name}")
                    return False
            else:
                # 檢查是否有任何實例在運行
                running_count = sum(1 for conn in instances_dict.values() if conn['thread'].is_alive())
                _logger.debug(
                    f"[PID {os.getpid()}] Found {running_count}/{len(instances_dict)} "
                    f"running instances for {db_name}"
                )
                return running_count > 0
        else:
            _logger.debug(
                f"[PID {os.getpid()}] No local connection for {db_name}, "
                f"falling back to heartbeat check (cross-process)"
            )

    # Phase 2: 跨 process 檢查 - 使用心跳機制
    from datetime import datetime, timedelta, timezone
    from odoo.sql_db import db_connect

    try:
        if instance_id:
            # 檢查特定實例的心跳
            heartbeat_key = f'odoo_ha_addon.ws_heartbeat_{db_name}_instance_{instance_id}'

            with db_connect(db_name).cursor() as cr:
                cr.execute(
                    "SELECT value FROM ir_config_parameter WHERE key = %s",
                    (heartbeat_key,)
                )
                result = cr.fetchone()
                last_heartbeat = result[0] if result else None

                _logger.debug(
                    f"[PID {os.getpid()}] Heartbeat check for {db_name} instance {instance_id}: "
                    f"key={heartbeat_key}, value={last_heartbeat}"
                )

                if not last_heartbeat:
                    _logger.debug(f"[PID {os.getpid()}] No heartbeat for instance {instance_id}")
                    return False

                # 解析和檢查心跳時間
                last_heartbeat_dt = datetime.strptime(last_heartbeat, '%Y-%m-%d %H:%M:%S')
                last_heartbeat_dt = last_heartbeat_dt.replace(tzinfo=timezone.utc)
                now_utc = datetime.now(timezone.utc)
                time_diff = (now_utc - last_heartbeat_dt).total_seconds()

                # 心跳檢查閾值：heartbeat_interval * 1.5 = 10 * 1.5 = 15 秒
                # 給 heartbeat 更新一些緩衝時間，但不要太寬鬆
                is_running = time_diff < 15
                _logger.info(
                    f"[PID {os.getpid()}] ⏱️  Heartbeat Check - Instance {instance_id}: "
                    f"time_diff={time_diff:.2f}s, threshold=15s, is_running={is_running}"
                )
                return is_running

        else:
            # Phase 2: 檢查是否有任何實例在運行（查找所有心跳）
            heartbeat_pattern = f'odoo_ha_addon.ws_heartbeat_{db_name}_instance_%'

            with db_connect(db_name).cursor() as cr:
                cr.execute(
                    "SELECT key, value FROM ir_config_parameter WHERE key LIKE %s",
                    (heartbeat_pattern,)
                )
                heartbeats = cr.fetchall()

                if not heartbeats:
                    _logger.debug(f"[PID {os.getpid()}] No heartbeats found for {db_name}")
                    return False

                # 檢查是否有任何心跳在 25 秒內
                now_utc = datetime.now(timezone.utc)
                running_count = 0

                for key, value in heartbeats:
                    try:
                        last_heartbeat_dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                        last_heartbeat_dt = last_heartbeat_dt.replace(tzinfo=timezone.utc)
                        time_diff = (now_utc - last_heartbeat_dt).total_seconds()

                        if time_diff < 25:
                            running_count += 1

                    except Exception as e:
                        _logger.warning(f"Failed to parse heartbeat {key}: {e}")

                _logger.debug(
                    f"[PID {os.getpid()}] Found {running_count}/{len(heartbeats)} "
                    f"running instances for {db_name}"
                )
                return running_count > 0

    except Exception as e:
        _logger.error(
            f"[PID {os.getpid()}] Error checking WebSocket service status: {e}",
            exc_info=True
        )
        return False


def is_config_changed(env, instance_id, return_details=False):
    """
    檢查組態是否已變更
    Phase 2 重構：檢查特定實例的配置變更

    Args:
        env: Odoo environment
        instance_id: HA Instance ID (必需)
        return_details: 若為 True，返回變更詳情字典；若為 False，只返回 bool

    Returns:
        bool 或 dict: 配置是否變更或詳細資訊
    """
    import os
    db_name = env.cr.dbname

    with _connections_lock:
        if db_name not in _websocket_connections:
            if return_details:
                return {
                    'changed': False,
                    'url_changed': False,
                    'token_changed': False,
                    'reason': 'no_connection'
                }
            return False

        # Phase 2: 檢查特定實例
        if instance_id not in _websocket_connections[db_name]:
            if return_details:
                return {
                    'changed': False,
                    'url_changed': False,
                    'token_changed': False,
                    'reason': 'instance_not_connected'
                }
            return False

        stored_config = _websocket_connections[db_name][instance_id]['config']

    # Phase 2: 從 ha.instance 模型讀取當前配置
    try:
        instance = env['ha.instance'].sudo().browse(instance_id)
        if not instance.exists():
            _logger.warning(f"HA instance {instance_id} not found")
            return False

        current_ha_url = instance.api_url
        current_ha_token = instance.api_token
    except Exception as e:
        _logger.error(f"Failed to read instance {instance_id} config: {e}")
        return False

    old_url = stored_config.get('ha_url')
    old_token = stored_config.get('ha_token')

    url_changed = old_url != current_ha_url
    token_changed = old_token != current_ha_token
    any_changed = url_changed or token_changed

    # 詳細日誌（只在有變更時記錄）
    if any_changed:
        _logger.info(
            f"[PID {os.getpid()}] Config change detected for {db_name} instance {instance_id}: "
            f"url_changed={url_changed}, token_changed={token_changed}"
        )
        if url_changed:
            _logger.info(f"  URL: {old_url} -> {current_ha_url}")
        if token_changed:
            # 安全起見，只顯示 token 前綴
            old_prefix = (old_token[:10] + '...') if (old_token and isinstance(old_token, str) and len(old_token) > 10) else 'None'
            new_prefix = (current_ha_token[:10] + '...') if (current_ha_token and isinstance(current_ha_token, str) and len(current_ha_token) > 10) else 'None'
            _logger.info(f"  Token: {old_prefix} -> {new_prefix}")

    if not return_details:
        return any_changed

    # 返回詳細資訊
    old_token_prefix = None
    if old_token and isinstance(old_token, str) and len(old_token) > 10:
        old_token_prefix = old_token[:10] + '...'

    new_token_prefix = None
    if current_ha_token and isinstance(current_ha_token, str) and len(current_ha_token) > 10:
        new_token_prefix = current_ha_token[:10] + '...'

    return {
        'changed': any_changed,
        'url_changed': url_changed,
        'token_changed': token_changed,
        'old_url': old_url,
        'new_url': current_ha_url,
        'old_token_prefix': old_token_prefix,
        'new_token_prefix': new_token_prefix
    }


def restart_websocket_service(env, instance_id=None, force=False):
    """
    重啟 WebSocket 服務
    Phase 2 重構：支援多實例

    Args:
        env: Odoo environment
        instance_id: HA Instance ID (可選)
            - 如果提供，只重啟該實例
            - 如果為 None，重啟所有實例
        force: 若為 True，忽略冷卻時間強制重啟

    Returns:
        dict: {'success': bool, 'message': str, 'skipped': bool, 'restarted_count': int}
    """
    import time
    import os
    db_name = env.cr.dbname

    # Phase 2: 如果指定實例，只重啟該實例
    if instance_id:
        with _connections_lock:
            # 檢查是否在冷卻時間內
            if not force and db_name in _websocket_connections:
                if instance_id in _websocket_connections[db_name]:
                    last_restart = _websocket_connections[db_name][instance_id].get('last_restart', 0)
                    time_since_restart = time.time() - last_restart

                    if time_since_restart < _RESTART_COOLDOWN:
                        remaining = _RESTART_COOLDOWN - time_since_restart
                        _logger.warning(
                            f"[PID {os.getpid()}] Skipping restart for {db_name} instance {instance_id}: "
                            f"last restart was {time_since_restart:.1f}s ago "
                            f"(cooldown: {_RESTART_COOLDOWN}s, remaining: {remaining:.1f}s)"
                        )
                        return {
                            'success': False,
                            'message': _('Restart too frequent, please wait %d seconds') % int(remaining),
                            'skipped': True,
                            'restarted_count': 0
                        }

            # 記錄當前時間作為重啟時間
            current_time = time.time()

        _logger.info(
            f"[PID {os.getpid()}] Restarting WebSocket service for {db_name} instance {instance_id}"
            f"{' (forced)' if force else ''}..."
        )

        try:
            # 停止服務
            stop_websocket_service(db_name, instance_id)
            time.sleep(1)  # 等待執行緒完全停止

            # 啟動服務
            start_websocket_service(env, instance_id)

            # 更新最後重啟時間
            with _connections_lock:
                if db_name in _websocket_connections and instance_id in _websocket_connections[db_name]:
                    _websocket_connections[db_name][instance_id]['last_restart'] = current_time

            _logger.info(f"[PID {os.getpid()}] WebSocket service restarted successfully for {db_name} instance {instance_id}")

            return {
                'success': True,
                'message': _('WebSocket service restarted (instance %d)') % instance_id,
                'skipped': False,
                'restarted_count': 1
            }

        except Exception as e:
            _logger.error(f"[PID {os.getpid()}] Failed to restart WebSocket service for {db_name} instance {instance_id}: {e}")
            return {
                'success': False,
                'message': _('Restart failed: %s') % str(e),
                'skipped': False,
                'restarted_count': 0
            }

    else:
        # Phase 2: 重啟所有活躍實例
        _logger.info(
            f"[PID {os.getpid()}] Restarting all WebSocket services for {db_name}"
            f"{' (forced)' if force else ''}..."
        )

        try:
            # 停止所有實例
            stop_websocket_service(db_name)
            time.sleep(1)  # 等待執行緒完全停止

            # 啟動所有活躍實例
            start_websocket_service(env)

            # 計算重啟的實例數量
            restarted_count = 0
            with _connections_lock:
                if db_name in _websocket_connections:
                    restarted_count = len(_websocket_connections[db_name])

            _logger.info(
                f"[PID {os.getpid()}] WebSocket services restarted successfully for {db_name} "
                f"({restarted_count} instances)"
            )

            return {
                'success': True,
                'message': _('All WebSocket services restarted (%d instances)') % restarted_count,
                'skipped': False,
                'restarted_count': restarted_count
            }

        except Exception as e:
            _logger.error(f"[PID {os.getpid()}] Failed to restart WebSocket services for {db_name}: {e}")
            return {
                'success': False,
                'message': _('Restart failed: %s') % str(e),
                'skipped': False,
                'restarted_count': 0
            }
