# Post-Install Permission Issue Fix

## Issue Summary

**Problem:** After fresh installation, users cannot access the HA settings page to configure Home Assistant instances.

**Error Message:**
```
Access Error
You are not allowed to access 'Home Assistant Instance' (ha.instance) records.

This operation is allowed for the following groups:
- Administration/Home Assistant Manager
- Administration/Home Assistant User
```

**Root Cause:** The addon does not automatically grant permissions to any user after installation, creating a chicken-and-egg problem where users need permissions to configure HA instances but cannot get those permissions without manual intervention.

---

## Technical Analysis

### Permission Architecture

The addon uses a two-tier permission model (similar to Point of Sale):

1. **`group_ha_user`** (Home Assistant User)
   - Read-only access to authorized HA data via entity groups
   - Can view entities within assigned groups
   - Cannot manage instances or configurations

2. **`group_ha_manager`** (Home Assistant Manager)
   - Full administrative access to all HA instances
   - Can create, modify, and delete instances
   - Includes all `group_ha_user` permissions (via `implied_ids`)

### Access Control Rules

#### Model Access (ir.model.access.csv)

```csv
# HA Instance model access
access_ha_instance_manager  → group_ha_manager (CRUD: 1,1,1,1)
access_ha_instance_user     → group_ha_user    (CRUD: 1,0,0,0)
```

#### Record Rules (security/security.xml)

**HA User Restrictions:**
```python
# Rule 1: Users can only see instances linked to their authorized entity groups
domain_force = [('id', 'in', user.ha_entity_group_ids.mapped('ha_instance_id').ids)]
```

**HA Manager Full Access:**
```python
# Rule 2: Managers can see all instances
domain_force = [(1, '=', 1)]
```

### Why the Error Occurs

1. **No Default Permissions**
   - After installation, even the admin user has no HA permissions
   - Not in `group_ha_manager` nor `group_ha_user`

2. **Settings Page Requires Permissions**
   - The settings page inherits `res.config.settings`
   - Contains a `ha_instance_id` Many2one field
   - Accessing this field triggers a search on `ha.instance` model
   - Without permissions, the search fails with an Access Error

3. **Chicken-and-Egg Problem**
   - Users need HA Manager permissions to access settings
   - But cannot grant permissions without accessing user management
   - Most users don't know to manually add themselves to the HA Manager group

---

## Solution Implementation

### Approach: Auto-Grant Admin Permissions

Following Odoo best practices (as seen in POS, Sales, Inventory modules), we automatically grant the admin user HA Manager permissions during installation.

### Code Changes

**File:** `/hooks.py`

**Modified Function:** `post_init_hook(env)`

```python
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
```

### How It Works

1. **On Installation:** `post_init_hook` is triggered after all data files are loaded
2. **Get References:** Uses `env.ref()` to get the admin user and HA Manager group
3. **Check Membership:** Verifies if admin already has the permission (for reinstallation cases)
4. **Grant Permission:** Uses `write()` with ORM command `(4, group_id)` to add the user to the group
5. **Graceful Fallback:** If anything fails, logs a warning with manual instructions

### Odoo ORM Command Used

```python
user.write({'groups_id': [(4, ha_manager_group.id)]})
```

**Command `(4, id)`:** Link existing record (add to many2many relation without unlinking others)

---

## Benefits of This Solution

### ✅ Advantages

1. **Immediate Usability**
   - Users can access HA settings immediately after installation
   - No manual permission configuration required

2. **Follows Odoo Standards**
   - Matches the approach used by official Odoo modules (POS, Sales, Inventory)
   - Familiar pattern for Odoo developers

3. **Safe and Flexible**
   - Only affects the admin user
   - Admin can revoke the permission if not needed
   - Graceful error handling with clear fallback instructions

4. **No Breaking Changes**
   - Existing permissions are preserved (uses `(4, id)` instead of `(6, 0, [ids])`)
   - Works correctly on reinstallation (checks existing membership)

5. **Multi-Database Compatible**
   - Works correctly in multi-database Odoo instances
   - Uses environment-specific user references

### 🔒 Security Considerations

- **Only Admin is Auto-Granted:** Other users must be explicitly added by the admin
- **Audit Trail:** All permission changes are logged in Odoo's audit log
- **Revocable:** Admin can remove HA Manager permissions at any time
- **Group-Based:** Uses Odoo's standard security group mechanism (not hardcoded user IDs)

---

## Testing Recommendations

### Test Case 1: Fresh Installation

**Steps:**
1. Uninstall `odoo_ha_addon` if previously installed
2. Install `odoo_ha_addon` via Apps menu
3. Immediately access the HA settings page

**Expected Result:**
- No access error
- Settings page loads successfully
- Admin user can create HA instances

**Verification:**
```bash
# Check Odoo logs for confirmation message
docker compose -f docker-compose-18.yml logs -f web | grep "Added user"
```

Expected log:
```
✓ Added user 'admin' to Home Assistant Manager group
  User can now access HA settings and configure instances
```

### Test Case 2: Reinstallation

**Steps:**
1. Install addon (admin gets permissions)
2. Uninstall addon
3. Reinstall addon

**Expected Result:**
- No duplicate permission grants
- Log shows: "User 'admin' already has Home Assistant Manager permissions"

### Test Case 3: Manual Permission Revocation

**Steps:**
1. Install addon (admin gets permissions)
2. Manually revoke HA Manager from admin user
3. Verify admin cannot access HA settings

**Expected Result:**
- Access error appears again (proves permissions are properly enforced)

### Test Case 4: Multi-User Environment

**Steps:**
1. Install addon
2. Create a new user
3. Try accessing HA settings with new user

**Expected Result:**
- New user gets access error (only admin auto-granted)
- Admin must manually grant permissions to other users

---

## Alternative Solutions Considered

### ❌ Option 1: Make ha.instance Publicly Readable

**Approach:** Remove permission requirements for initial setup

**Rejected Because:**
- Security risk: all users could see HA instance configurations
- Breaks the intended permission model
- API tokens would be visible to unauthorized users

### ❌ Option 2: Setup Wizard

**Approach:** Create a wizard that auto-grants permissions during first-run setup

**Rejected Because:**
- Adds complexity for minimal benefit
- Not friendly for automated deployments
- Doesn't follow Odoo standard patterns
- Users might skip the wizard

### ✅ Option 3: Auto-Grant Admin (Selected)

**Why Chosen:**
- Simple, clear, and follows Odoo best practices
- Works seamlessly in all deployment scenarios
- Minimal code changes required
- Familiar pattern for Odoo developers

---

## Migration Notes

### For Existing Installations

If the addon was already installed before this fix:

**Manual Fix:**
1. Go to **Settings > Users & Companies > Users**
2. Select the **admin** user
3. Go to the **Administration** tab
4. Check **Home Assistant Manager** under Access Rights
5. Click **Save**

**Or Use Odoo Shell:**
```python
# Connect to Odoo shell
docker compose -f docker-compose-18.yml exec web odoo shell -d odoo

# Run in shell
env['res.users'].browse(2).write({'groups_id': [(4, env.ref('odoo_ha_addon.group_ha_manager').id)]})
```

### For Fresh Installations

No action required - permissions are automatically granted during installation.

---

## Related Documentation

- **Security Model:** `/docs/tech/security.md` - Two-tier permission system
- **Development Guide:** `/docs/development-guide.md` - General addon guidelines
- **Architecture:** `/docs/architecture.md` - Complete system architecture

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2025-11-26 | 18.0.4.0 | Implemented auto-grant admin permissions in `post_init_hook` |

---

## Summary

This fix ensures a smooth out-of-box experience by automatically granting the admin user HA Manager permissions during installation. This follows Odoo best practices and eliminates the frustrating "chicken-and-egg" permission problem that prevented initial setup.

**Key Takeaway:** Users can now configure Home Assistant instances immediately after installation, without manual permission configuration.
