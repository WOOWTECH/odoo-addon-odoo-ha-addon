---
name: frontend-edge-case-audit
description: Edge case testing and bug fixes for WOOW Dashboard frontend and API components
status: complete
created: 2026-03-06T07:24:28Z
updated: 2026-03-06T07:27:21Z
---

# WOOW Dashboard Edge Case Audit PRD

## Summary

This document captures potential issues identified through static code analysis of the WOOW Dashboard addon, including edge cases, memory leaks, and error handling gaps. Issues have been categorized by severity and component.

## Analysis Approach

Since the WOOW Dashboard module was not installed in available Odoo instances during testing, analysis was performed via:
1. Static code analysis of frontend OWL components
2. API endpoint pattern analysis in controllers
3. WebSocket service reliability review

---

## Issues Found and Fixes Applied

### CRITICAL - Memory Leaks (FIXED)

#### Issue 1: Event Listener Binding Order Bug
**Files Affected:**
- `src/static/src/portal/portal_live_status.js`
- `src/static/src/portal/portal_entity_info.js`
- `src/static/src/portal/portal_group_info.js`

**Problem:**
Event listener binding happened AFTER `onMounted()` hook registered the listener. This causes:
- `addEventListener` uses unbound function reference
- `removeEventListener` in `onWillUnmount` uses bound function reference
- Different references means listener is never actually removed
- Results in memory leak on component unmount/remount cycles

**Before (Buggy):**
```javascript
onMounted(() => {
    document.addEventListener("visibilitychange", this.onVisibilityChange);
});
onWillUnmount(() => {
    document.removeEventListener("visibilitychange", this.onVisibilityChange);
});
// Bind AFTER hooks registered - BUG!
this.onVisibilityChange = this.onVisibilityChange.bind(this);
```

**After (Fixed):**
```javascript
// IMPORTANT: Bind BEFORE registering event listeners
this.onVisibilityChange = this.onVisibilityChange.bind(this);

onMounted(() => {
    document.addEventListener("visibilitychange", this.onVisibilityChange);
});
onWillUnmount(() => {
    document.removeEventListener("visibilitychange", this.onVisibilityChange);
});
```

**Status:** ✅ FIXED in all 3 files

---

### HIGH - Input Validation Gaps (FIXED)

#### Issue 2: Type Coercion Without Validation
**File:** `src/controllers/controllers.py`

**Problem:**
User-provided IDs were converted via `int()` without try-except. Non-numeric strings like `"abc"` or `"1.5"` would raise `ValueError`.

**Fix Applied:**
Added `_safe_int()` helper function and wrapped all ID conversions:
```python
def _safe_int(value, field_name):
    """Safely convert to int with user-friendly error."""
    if value is None:
        raise ValueError(_("%(field)s is required") % {'field': field_name})
    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValueError(_("Invalid %(field)s: must be a numeric ID") % {'field': field_name})
```

**Locations Fixed:**
- Line ~795: `get_entities_by_area()` area_id validation
- Line ~922: `get_area_dashboard_data()` area_id validation
- Line ~1351: `switch_instance()` instance_id validation

**Status:** ✅ FIXED

---

### HIGH - Input Validation Gaps (TO FIX)

#### Issue 2: Type Coercion Without Validation
**File:** `src/controllers/controllers.py`

**Locations:**
- Line 780-782: `int(area_id)` can raise ValueError
- Line 1313: `int(instance_id)` without validation
- Line 884-891: `int(area_id)` after incomplete type check

**Problem:**
User-provided IDs are converted via `int()` without try-except. Non-numeric strings like `"abc"` or `"1.5"` will raise `ValueError` and return unhelpful error messages.

**Recommended Fix:**
```python
def _safe_int(value, field_name):
    """Safely convert to int with user-friendly error."""
    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid {field_name}: must be a numeric ID")
```

**Status:** ⏳ Pending fix

---

### MEDIUM - Error Message Exposure (FIXED)

#### Issue 3: Raw Exception Messages Returned to Users
**File:** `src/controllers/portal.py:428`

**Problem:**
```python
return {
    'success': False,
    'error': str(e),  # Exposes internal exception details
    'error_code': 'system_error'
}
```

Internal exception messages (potentially containing stack traces or sensitive info) were returned directly to users.

**Fix Applied:**
```python
_logger.exception(f"Portal call-service error for entity {record_id}: {e}")
# Return generic error message to avoid exposing internal details
return {
    'success': False,
    'error': _('An unexpected error occurred. Please try again.'),
    'error_code': 'system_error'
}
```

**Status:** ✅ FIXED

---

### MEDIUM - Transaction Management (REVIEW)

#### Issue 4: Manual Commits in HTTP Context
**File:** `src/controllers/controllers.py:652-665`

**Problem:**
Manual `request.env.cr.commit()` calls in HTTP controllers can cause:
- Partial data if subsequent operations fail
- Breaks Odoo's transaction management
- Data inconsistency if browser request interrupted

**Context:**
This is documented as intentional for "reducing lock time" during sync operations. Consider using `savepoint()` for safer partial commits.

**Status:** 📝 Review recommended

---

### LOW - Entity Loop Performance (TO FIX)

#### Issue 5: Unbounded Entity Loop
**File:** `src/controllers/portal.py:860-862`

**Problem:**
```python
for entity in device.entity_ids:
    entities_with_state.append(self._get_safe_entity_data(entity))
```

No pagination for devices with many entities. Could cause memory issues for large devices.

**Recommended Fix:**
Add limit parameter:
```python
MAX_ENTITIES_PER_DEVICE = 100
entities = device.entity_ids[:MAX_ENTITIES_PER_DEVICE]
```

**Status:** ⏳ Pending fix

---

### LOW - Inconsistent Error Response (TO FIX)

#### Issue 6: Non-Standard Response Fields
**File:** `src/controllers/controllers.py:469-473`

**Problem:**
```python
return {
    'success': False,
    'error': result['message'],
    'skipped': result.get('skipped', False)  # Non-standard
}
```

The `skipped` field breaks standard `{success, data, error}` format.

**Recommended Fix:**
```python
return self._standardize_response(False, None, result['message'])
```

**Status:** ⏳ Pending fix

---

## Verified Safe

The following areas were reviewed and found to be properly implemented:

| Area | Status | Notes |
|------|--------|-------|
| Authentication | ✅ Safe | All routes use `auth='user'` |
| Authorization | ✅ Safe | Access via `ir.rule` ORM checks |
| Portal Token Validation | ✅ Safe | Uses `hmac.compare_digest()` |
| CORS | ✅ Safe | Portal removed `cors='*'` |
| CSRF | ✅ Safe | JSON routes use Content-Type checking |
| Field Whitelists | ✅ Safe | `PORTAL_ENTITY_FIELDS` limits exposure |
| Service Whitelist | ✅ Safe | `PORTAL_CONTROL_SERVICES` limits HA calls |

---

## WebSocket Configuration

A centralized configuration file exists at `src/models/common/ws_config.py` with proper timeout constants:

| Constant | Value | Purpose |
|----------|-------|---------|
| `WS_CLOSE_TIMEOUT` | 5s | Connection close timeout |
| `WS_AUTH_TIMEOUT` | 5s | Authentication handshake |
| `WS_DEFAULT_TIMEOUT` | 10s | General API calls |
| `WS_HISTORY_STREAM_TIMEOUT` | 60s | History subscriptions |
| `WS_THREAD_JOIN_TIMEOUT` | 10s | Service shutdown |

**Status:** ✅ Well-structured

---

## Edge Case Test Scenarios (For Future E2E Testing)

### Frontend Edge Cases

| Test | Input | Expected Behavior |
|------|-------|-------------------|
| Tab visibility toggle | Hide/show browser tab rapidly | Polling stops/starts without duplicate timers |
| Component unmount during fetch | Unmount while API call pending | No state update on unmounted component |
| Network timeout | Slow/no network | Graceful error, polling continues |
| Invalid entity state | `entity_state: null` | Display "unknown" fallback |
| Large attribute count | 100+ attributes | Scrollable table, no UI freeze |

### API Edge Cases

| Test | Input | Expected Behavior |
|------|-------|-------------------|
| Non-numeric entity_id | `entity_id="abc"` | 400 with "Invalid entity_id" message |
| Negative entity_id | `entity_id=-1` | 400 with "Invalid entity_id" message |
| Float entity_id | `entity_id=1.5` | 400 with "Invalid entity_id" message |
| Empty area_id | `area_id=""` | Treat as unassigned |
| Deleted entity access | Valid ID, deleted entity | 404 with "Entity not found" |
| Revoked share access | Valid token, revoked share | 403 with "Access revoked" |

### Concurrency Edge Cases

| Test | Input | Expected Behavior |
|------|-------|-------------------|
| Simultaneous state changes | 2 clients toggle same switch | Last write wins, both see final state |
| WebSocket disconnect during call | Restart WS mid-request | Request retries or fails gracefully |
| Database lock contention | Bulk sync during user action | User action completes, sync waits |

---

## Implementation Priority

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| P1 | Memory leaks (3 files) | Low | High - ✅ DONE |
| P2 | Input validation (int coercion) | Low | High |
| P3 | Exception message sanitization | Low | Medium |
| P4 | Entity loop pagination | Low | Medium |
| P5 | Response format consistency | Low | Low |

---

## Commits Made

1. Fixed `portal_live_status.js` - Event listener binding order
2. Fixed `portal_entity_info.js` - Event listener binding order
3. Fixed `portal_group_info.js` - Event listener binding order
4. Added `_safe_int()` helper to `controllers.py` for input validation
5. Fixed 3 locations in `controllers.py` with proper int validation
6. Fixed exception message exposure in `portal.py`

---

## Summary of Changes

| Category | Files Changed | Issues Fixed |
|----------|---------------|--------------|
| Memory Leaks | 3 JS files | 3 CRITICAL |
| Input Validation | controllers.py | 3 HIGH |
| Error Exposure | portal.py | 1 MEDIUM |
| **Total** | **5 files** | **7 issues** |

---

## Remaining Items (Lower Priority)

1. **Entity loop pagination** - Add limit to portal device endpoint
2. **Response format consistency** - Review `skipped` field usage
3. **E2E test environment** - Set up with WOOW module installed
4. **Run edge case scenarios** - Use test matrix defined above
