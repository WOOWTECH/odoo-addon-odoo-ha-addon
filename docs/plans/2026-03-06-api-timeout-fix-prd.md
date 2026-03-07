---
name: api-timeout-fix-prd
description: Fix API timeout issues in get_instances endpoint and WebSocket status checks
status: complete
created: 2026-03-06T09:00:00Z
updated: 2026-03-07T06:50:24Z
---

# PRD: API Timeout Fix for WOOW Dashboard

## Problem Statement

The WOOW Dashboard's `/odoo_ha_addon/get_instances` API endpoint was hanging indefinitely under certain conditions, causing:
- Dashboard content failing to load
- Page stuck on "載入中..." (Loading...) indefinitely
- Users unable to access dashboard after login
- Container requiring restart to recover

## Root Cause Analysis

### Issue Location
The issue was traced through the following call chain:

```
get_instances (controllers.py)
  → inst.websocket_status (computed field)
    → _compute_websocket_status (ha_instance.py)
      → is_websocket_service_running() (websocket_thread_manager.py)
        → db_connect().cursor() (blocking indefinitely)
```

### Technical Details

1. **`_compute_websocket_status`** in `ha_instance.py`:
   - Called `is_websocket_service_running()` without any timeout
   - This is a computed field, so it runs every time `websocket_status` is accessed

2. **`is_websocket_service_running`** in `websocket_thread_manager.py`:
   - Used `db_connect()` to create a new database connection
   - This could block indefinitely when:
     - Database connection pool exhausted
     - Network issues
     - Transaction deadlocks

3. **`get_instances`** in `controllers.py`:
   - Returned raw exception messages via `str(e)`
   - Exposed internal error details to users

## Solution Implemented

### Fix 1: Threading Timeout for WebSocket Status Check

**File:** `src/models/ha_instance.py` (lines 172-206)

```python
def _compute_websocket_status(self):
    """
    計算 WebSocket 連接狀態
    Phase 3: 加入 timeout 防止 API 阻塞
    - 使用 threading 實現 timeout
    - 預設 3 秒 timeout，避免阻塞整個 get_instances API
    """
    import threading

    WS_STATUS_CHECK_TIMEOUT = 3  # seconds

    for record in self:
        try:
            result = {'status': 'disconnected'}

            def check_status():
                try:
                    is_running = is_websocket_service_running(
                        env=self.env,
                        instance_id=record.id
                    )
                    result['status'] = 'connected' if is_running else 'disconnected'
                except Exception as e:
                    _logger.warning(f"WebSocket status check failed: {e}")
                    result['status'] = 'disconnected'

            check_thread = threading.Thread(target=check_status)
            check_thread.start()
            check_thread.join(timeout=WS_STATUS_CHECK_TIMEOUT)

            if check_thread.is_alive():
                _logger.warning(f"WebSocket status check timed out for instance {record.id}")
                record.websocket_status = 'disconnected'
            else:
                record.websocket_status = result['status']

        except Exception as e:
            _logger.error(f"Failed to compute WebSocket status: {e}")
            record.websocket_status = 'error'
```

**Benefits:**
- Prevents indefinite blocking
- Returns 'disconnected' on timeout (graceful degradation)
- Logs timeout events for debugging

### Fix 2: PostgreSQL Statement Timeout

**File:** `src/models/common/websocket_thread_manager.py`

```python
DB_QUERY_TIMEOUT_MS = 2000  # 2 seconds

with db_connect(db_name).cursor() as cr:
    # Set statement timeout to prevent long-running queries
    cr.execute(f"SET LOCAL statement_timeout = {DB_QUERY_TIMEOUT_MS}")
    cr.execute(
        "SELECT value FROM ir_config_parameter WHERE key = %s",
        (heartbeat_key,)
    )
```

**Benefits:**
- Database queries cannot block longer than 2 seconds
- `SET LOCAL` ensures timeout only affects current transaction
- Prevents connection pool exhaustion

### Fix 3: Error Message Sanitization

**File:** `src/controllers/controllers.py` (get_instances endpoint)

```python
except Exception as e:
    _logger.error(f"Failed to get HA instances: {e}", exc_info=True)
    # Return generic error message to avoid exposing internal details
    return self._standardize_response({
        'success': False,
        'error': _('Failed to load HA instances. Please try again.')
    })
```

**Benefits:**
- Hides internal error details from users
- Provides user-friendly error message
- Full error logged for debugging

## Testing Results

### Before Fix
- API hangs indefinitely (no response)
- Dashboard stuck on loading state
- Container becomes unresponsive

### After Fix
- API responds within 1-2 seconds
- Dashboard loads successfully
- 629 entities, 89 scenes displayed correctly
- All Model and Configuration menus functional

### E2E Test Results

| Feature | Status |
|---------|--------|
| Dashboard Main Page | ✅ Pass |
| Model > Area (8 areas) | ✅ Pass |
| Model > Entity (629 entities) | ✅ Pass |
| Model > History (charts) | ✅ Pass |
| Configuration > Scene (89 scenes) | ✅ Pass |
| All Configuration Menus | ✅ Pass |

## Files Modified

| File | Changes |
|------|---------|
| `src/models/ha_instance.py` | Added threading timeout to `_compute_websocket_status` |
| `src/models/common/websocket_thread_manager.py` | Added PostgreSQL statement_timeout |
| `src/controllers/controllers.py` | Sanitized error messages in `get_instances` |

## Performance Impact

- **API Response Time:** Improved from ∞ (timeout) to 1-2 seconds
- **Worst Case:** 3 seconds (thread timeout) + 2 seconds (DB timeout) = 5 seconds max
- **Memory:** Minimal impact (threading overhead negligible)

## Deployment Notes

1. No database migration required
2. No configuration changes needed
3. Changes take effect immediately after container restart
4. Backwards compatible with existing data

## Related Documents

- [E2E Testing Report](./2026-03-06-e2e-testing-report.md)
- [Frontend Edge Case Audit](./2026-03-06-frontend-edge-case-audit.md)

## Conclusion

This fix resolves the critical API timeout issue that was blocking production deployment. The WOOW Dashboard module is now **production ready** with all core functionality verified and working correctly.
