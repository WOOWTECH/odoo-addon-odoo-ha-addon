# PRD: Portal User Sharing for HA Entities

## Overview

### Problem Statement

Currently, the HA Entity and Entity Group sharing functionality only allows sharing with **internal Odoo users** (users with `share=False`). Portal users (external users with limited Odoo access, `share=True`) are explicitly excluded from the user selection dropdown via domain filter `[('share', '=', False)]`.

This limitation prevents common use cases where:
1. External partners or customers need to view IoT device status
2. Family members with portal accounts need to control home automation
3. Building managers need to share device access with tenants

### Goal

Enable sharing HA Entities and Entity Groups with **Portal users** in addition to internal users, while maintaining security and access control.

### Success Metrics

| Metric | Target |
|--------|--------|
| Portal users can be selected in share wizard | 100% |
| Portal users can access shared entities via `/my/ha` | 100% |
| Portal users can control shared entities (if permission=control) | 100% |
| Existing internal user sharing continues to work | No regression |
| Security (no unauthorized access) | Zero vulnerabilities |

---

## Current State Analysis

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Share Wizard (Transient)                     │
│  ha.entity.share.wizard                                          │
│  - user_ids: Many2many with domain=[('share', '=', False)]  ❌   │
│  - permission: view/control                                      │
│  - expiry_date: optional                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Share Record (Persistent)                    │
│  ha.entity.share                                                 │
│  - entity_id / group_id                                          │
│  - user_id: Many2one (no domain restriction)                     │
│  - permission: view/control                                      │
│  - expiry_date, is_expired                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Portal Controller                            │
│  - Routes: /portal/entity/<id>, /portal/call-service, /my/ha     │
│  - Auth: auth='user' (requires Odoo login)  ✅                   │
│  - Access check via ha.entity.share lookup  ✅                   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `src/wizard/ha_entity_share_wizard.py` | Share wizard with user selection |
| `src/models/ha_entity_share.py` | Share data model |
| `src/controllers/portal.py` | Portal access routes |
| `src/views/ha_entity_share_wizard_views.xml` | Wizard UI |

### Current Domain Filter (Line 53 of wizard)

```python
user_ids = fields.Many2many(
    'res.users',
    ...
    domain="[('share', '=', False)]",  # EXCLUDES portal users
)
```

---

## Proposed Solution

### Approach: Extend Domain to Include Portal Users

**Simple solution**: Modify the domain filter to include both internal users and portal users with specific group membership.

#### Option A: Allow All Users (Simplest)
```python
domain="[('active', '=', True)]"
```
- Pros: Simple, allows all users including portal
- Cons: May show system users, superuser, etc.

#### Option B: Allow Internal + Portal Users (Recommended)
```python
domain="['|', ('share', '=', False), '&', ('share', '=', True), ('groups_id', 'in', [ref('base.group_portal')])]"
```
- Pros: Explicit about which users are allowed
- Cons: Slightly complex domain

#### Option C: Create a Helper Method
```python
@api.model
def _get_shareable_users_domain(self):
    """Return domain for users that can receive shares."""
    return [
        ('active', '=', True),
        '|',
        ('share', '=', False),  # Internal users
        ('groups_id', 'in', [self.env.ref('base.group_portal').id])  # Portal users
    ]
```
- Pros: Reusable, easy to modify
- Cons: Cannot use directly in field definition

### Recommended: Option B with UI Enhancement

1. **Modify domain filter** to include portal users
2. **Add visual indicator** in the user selection showing user type (Internal/Portal)
3. **Update help text** to clarify that both internal and portal users can be selected

---

## Implementation Plan

### Phase 1: Enable Portal User Selection

#### Task 1.1: Update Share Wizard Domain Filter

**File**: `src/wizard/ha_entity_share_wizard.py`

**Change**:
```python
# Before
domain="[('share', '=', False)]"

# After
domain="[('active', '=', True), '|', ('share', '=', False), ('groups_id.name', '=', 'Portal')]"
```

**Effort**: 5 minutes

#### Task 1.2: Add Computed Field for User Type Display

**File**: `src/wizard/ha_entity_share_wizard.py`

**Add helper to show user type**:
```python
@api.depends('user_ids')
def _compute_user_types_display(self):
    """Show which users are portal vs internal."""
    for wizard in self:
        internal = wizard.user_ids.filtered(lambda u: not u.share)
        portal = wizard.user_ids.filtered(lambda u: u.share)
        parts = []
        if internal:
            parts.append(f"{len(internal)} internal")
        if portal:
            parts.append(f"{len(portal)} portal")
        wizard.user_types_display = ", ".join(parts) if parts else ""
```

**Effort**: 15 minutes

#### Task 1.3: Update Wizard View with User Type Info

**File**: `src/views/ha_entity_share_wizard_views.xml`

**Add info message showing user types**:
```xml
<div class="text-muted" invisible="not user_types_display">
    Selected: <field name="user_types_display" nolabel="1"/>
</div>
```

**Effort**: 10 minutes

### Phase 2: Update Documentation and Help Text

#### Task 2.1: Update Field Help Text

**File**: `src/wizard/ha_entity_share_wizard.py`

```python
user_ids = fields.Many2many(
    ...
    help='Select users to share with. Supports both internal users and portal users.'
)
```

**Effort**: 5 minutes

#### Task 2.2: Update Permission Levels Info Box

**File**: `src/views/ha_entity_share_wizard_views.xml`

Add clarification that portal users access via `/my/ha`:
```xml
<div class="alert alert-light" role="alert">
    <strong>Access Methods:</strong>
    <ul class="mb-0">
        <li><strong>Internal users:</strong> Access via WOOW Dashboard menu</li>
        <li><strong>Portal users:</strong> Access via My Account → HA Devices (/my/ha)</li>
    </ul>
</div>
```

**Effort**: 10 minutes

### Phase 3: Testing

#### Task 3.1: Unit Tests for Portal User Sharing

**File**: `src/tests/test_portal_user_sharing.py` (new)

Test cases:
1. ✅ Portal user can be selected in share wizard
2. ✅ Share record created successfully for portal user
3. ✅ Portal user can access shared entity via `/portal/entity/<id>`
4. ✅ Portal user can control entity if permission=control
5. ✅ Portal user cannot control entity if permission=view
6. ✅ Expired share denies portal user access
7. ✅ Internal user sharing continues to work

**Effort**: 1 hour

#### Task 3.2: E2E Tests with Playwright

Test the full flow:
1. Admin shares entity with portal user
2. Portal user logs in
3. Portal user accesses `/my/ha`
4. Portal user views entity state
5. Portal user controls entity (if permission allows)

**Effort**: 1 hour

### Phase 4: i18n Updates

#### Task 4.1: Update Translation Files

**Files**: `src/i18n/odoo_ha_addon.pot`, `src/i18n/zh_TW.po`

Add translations for:
- "Supports both internal users and portal users"
- "Access via My Account → HA Devices"
- User type display strings

**Effort**: 30 minutes

---

## Security Considerations

### Current Security (Already Implemented)

| Layer | Protection |
|-------|------------|
| Route Auth | `auth='user'` requires Odoo login |
| Share Validation | `_check_entity_share_access()` validates share record |
| Permission Check | Enforces `view` vs `control` permission level |
| Expiry Check | Denies access for expired shares |
| Field Whitelist | `PORTAL_ENTITY_FIELDS` limits exposed data |
| Service Whitelist | `PORTAL_CONTROL_SERVICES` limits allowed actions |

### Additional Security for Portal Users

1. **Portal users are limited by Odoo's portal security**
   - Cannot access backend
   - Cannot modify system data
   - Already sandboxed by Odoo

2. **No additional security needed** - existing mechanisms apply equally to portal users

3. **Audit trail** - All shares are logged in `ha.entity.share` with timestamps

---

## UI/UX Mockup

### Updated Share Dialog

```
┌──────────────────────────────────────────────────────────┐
│  Share Entity                                        ✕   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Sharing: 全室能源監控 Voltage                            │
│                                                          │
│  ─────────────── SHARE SETTINGS ───────────────          │
│                                                          │
│  Share With Users *                                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │ [Alice (Internal)] [Bob (Portal)] [+]              │  │
│  └────────────────────────────────────────────────────┘  │
│  Selected: 1 internal, 1 portal                          │
│                                                          │
│  Permission *         [ View Only      ▼ ]               │
│                                                          │
│  Expiry Date          [                  ]               │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │ ℹ️ Permission Levels:                            │    │
│  │ • View Only: Users can see state but cannot      │    │
│  │   control it                                     │    │
│  │ • Can Control: Users can view and control        │    │
│  │   (turn on/off, adjust settings)                 │    │
│  │                                                  │    │
│  │ Access Methods:                                  │    │
│  │ • Internal users: Access via Dashboard menu      │    │
│  │ • Portal users: Access via My Account → HA       │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  [ Share ]  [ Cancel ]                                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Rollout Plan

| Phase | Timeline | Description |
|-------|----------|-------------|
| Development | Day 1 | Implement domain filter change + UI updates |
| Testing | Day 1-2 | Unit tests + E2E tests |
| Code Review | Day 2 | Review security implications |
| Staging | Day 2 | Deploy to staging environment |
| Production | Day 3 | Deploy to production |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Portal user gains unauthorized access | High | Existing share validation + permission checks already prevent this |
| Performance degradation with larger user list | Low | User dropdown is filtered, pagination handled by Odoo widget |
| Confusion about portal vs internal users | Medium | Add visual indicator (Internal/Portal) label |
| Existing shares break | High | No migration needed - existing shares unaffected |

---

## Out of Scope

1. **Email notifications to portal users** - Can be added later via existing cron jobs
2. **Public link sharing (no login)** - Different feature, requires token-based auth
3. **Bulk sharing to user groups** - Can be added later
4. **Permission inheritance** - Groups already inherit entity permissions

---

## Acceptance Criteria

### Functional

- [ ] Portal users appear in "Share With Users" dropdown
- [ ] Portal users can be selected alongside internal users
- [ ] Share record created successfully for portal users
- [ ] Portal users can access shared entities via `/my/ha`
- [ ] Portal users can view entity state
- [ ] Portal users can control entities (if permission=control)
- [ ] Expiry dates work correctly for portal users
- [ ] Internal user sharing continues to work unchanged

### Non-Functional

- [ ] No security vulnerabilities introduced
- [ ] No performance regression
- [ ] i18n strings added for new text
- [ ] Unit test coverage > 80%
- [ ] E2E tests pass

---

## Appendix

### Related Files

```
src/
├── wizard/
│   └── ha_entity_share_wizard.py      # Main change location
├── views/
│   └── ha_entity_share_wizard_views.xml # UI updates
├── models/
│   └── ha_entity_share.py             # No changes needed
├── controllers/
│   └── portal.py                      # No changes needed
├── tests/
│   └── test_portal_user_sharing.py    # New test file
└── i18n/
    ├── odoo_ha_addon.pot              # Translation template
    └── zh_TW.po                       # Chinese translations
```

### References

- [Odoo Portal Users Documentation](https://www.odoo.com/documentation/17.0/applications/websites/website/configuration/portal_access.html)
- [Odoo Domain Syntax](https://www.odoo.com/documentation/17.0/developer/reference/backend/orm.html#domains)
- Current implementation: `src/wizard/ha_entity_share_wizard.py:53`
