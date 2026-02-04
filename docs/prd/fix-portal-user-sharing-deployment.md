# PRD: Fix Portal User Sharing Deployment

## Problem Statement

The Portal User Sharing feature code changes are not visible in the running Odoo container because:

1. **Mount Path Mismatch**: The Podman container mounts addons from a different worktree path:
   - Container mount source: `/var/tmp/vibe-kanban/worktrees/fb5a-odoo-dev-contain/woow odoo module/addons`
   - Code changes location: `/var/tmp/vibe-kanban/worktrees/2a1b-/woow-odoo-ha-addon/src/`

2. **Changes Not Synced**: The wizard file in container still has old domain filter:
   ```python
   # In container (OLD)
   domain="[('share', '=', False)]"

   # In worktree (NEW)
   domain="[('active', '=', True), '|', ('share', '=', False), ('groups_id.name', '=', 'Portal')]"
   ```

## Root Cause Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│  Current Worktree (2a1b-)                                       │
│  /var/tmp/vibe-kanban/worktrees/2a1b-/woow-odoo-ha-addon/src/  │
│  ✅ Has updated code                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓ NOT MOUNTED
┌─────────────────────────────────────────────────────────────────┐
│  Podman Container (woowodoomodule-odoo-1)                       │
│  /mnt/extra-addons/odoo_ha_addon/                               │
│  ❌ Has OLD code from different worktree                        │
└─────────────────────────────────────────────────────────────────┘
                              ↑ MOUNTED FROM
┌─────────────────────────────────────────────────────────────────┐
│  Different Worktree (fb5a-)                                     │
│  /var/tmp/.../fb5a-odoo-dev-contain/woow odoo module/addons    │
│  ❌ Does not have our changes                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Solution Options

### Option A: Copy Files to Mounted Directory (Quick Fix)

Copy the modified files to the directory that is actually mounted in the container.

**Pros:**
- Quick, no container restart required (just addon update)
- Minimal disruption

**Cons:**
- Files exist in two places (maintenance burden)
- Changes need to be copied each time

### Option B: Recreate Container with Correct Mount (Proper Fix)

Modify docker-compose or podman run to mount the current worktree.

**Pros:**
- Proper solution
- Changes automatically visible

**Cons:**
- Requires container recreation
- May lose container state

### Option C: Symbolic Link (Hybrid)

Create symbolic link from mounted path to current worktree.

**Pros:**
- One-time setup
- Changes automatically visible

**Cons:**
- May not work with volume mounts
- Could break other worktrees

## Recommended Solution: Option A (Quick Fix)

For immediate testing, copy the changed files to the mounted directory.

## Implementation Steps

### Step 1: Identify Changed Files

```
src/wizard/ha_entity_share_wizard.py
src/views/ha_entity_share_wizard_views.xml
src/i18n/zh_TW.po
src/tests/test_portal_user_sharing.py
```

### Step 2: Copy Files to Mounted Directory

```bash
# Source: Current worktree
SRC="/var/tmp/vibe-kanban/worktrees/2a1b-/woow-odoo-ha-addon/src"

# Destination: Directory mounted in container
DEST="/var/tmp/vibe-kanban/worktrees/fb5a-odoo-dev-contain/woow odoo module/addons/odoo_ha_addon"

# Copy changed files
cp "$SRC/wizard/ha_entity_share_wizard.py" "$DEST/wizard/"
cp "$SRC/views/ha_entity_share_wizard_views.xml" "$DEST/views/"
cp "$SRC/i18n/zh_TW.po" "$DEST/i18n/"
cp "$SRC/tests/test_portal_user_sharing.py" "$DEST/tests/"
```

### Step 3: Update Addon in Odoo

```bash
podman exec woowodoomodule-odoo-1 odoo -d woowtech -u odoo_ha_addon --stop-after-init
podman restart woowodoomodule-odoo-1
```

### Step 4: Verify Changes Applied

```bash
podman exec woowodoomodule-odoo-1 grep "Portal" /mnt/extra-addons/odoo_ha_addon/wizard/ha_entity_share_wizard.py
```

## Success Criteria

- [ ] Portal users appear in "Share With Users" dropdown
- [ ] User type display shows "X internal, Y portal"
- [ ] Access Methods info box is visible
- [ ] Share record can be created for portal users

## Files to Copy

| Source File | Description |
|-------------|-------------|
| `src/wizard/ha_entity_share_wizard.py` | Updated domain filter + user_types_display |
| `src/views/ha_entity_share_wizard_views.xml` | Updated UI with user type info |
| `src/i18n/zh_TW.po` | Chinese translations |
| `src/tests/test_portal_user_sharing.py` | Unit tests |
