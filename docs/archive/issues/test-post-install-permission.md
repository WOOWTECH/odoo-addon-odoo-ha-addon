# Testing Guide: Post-Install Permission Fix

This guide provides step-by-step instructions to verify the post-install permission fix works correctly.

---

## Prerequisites

- Docker Compose environment running Odoo 18
- Access to `docker compose` command
- Fresh Odoo database or ability to create one

---

## Test Scenario 1: Fresh Installation (Primary Test)

This test verifies that admin gets HA Manager permissions automatically on fresh installation.

### Step 1: Prepare Clean Environment

```bash
# Navigate to project root
cd /Users/eugene/Documents/woow/AREA-odoo/odoo-server

# Stop Odoo if running
docker compose -f docker-compose-18.yml down

# Start Odoo
docker compose -f docker-compose-18.yml up -d
```

### Step 2: Access Odoo Web Interface

1. Open browser: http://localhost:8069
2. Create a new database (or use existing `odoo`)
   - Database Name: `test_ha_permissions`
   - Email: `admin@example.com`
   - Password: `admin`
   - Language: English
   - Country: Taiwan

### Step 3: Install the Addon

1. Go to **Apps** menu
2. Remove the "Apps" filter to show all modules
3. Search for: `WOOW Dashboard` or `odoo_ha_addon`
4. Click **Install**

### Step 4: Monitor Installation Logs

**In a separate terminal:**

```bash
# Monitor Odoo logs in real-time
docker compose -f docker-compose-18.yml logs -f web
```

**Expected Log Output:**

```
============================================================
Initializing Home Assistant addon...
============================================================
✓ Added user 'admin' to Home Assistant Manager group
  User can now access HA settings and configure instances
✓ Home Assistant WebSocket integration module installed successfully
============================================================
```

### Step 5: Verify Access to Settings

1. In Odoo web interface, go to:
   - **WOOW Dashboard > Configuration > WOOW HA**

2. **Expected Result:**
   - ✅ Settings page loads successfully
   - ✅ No "Access Error" message
   - ✅ You see the HA instance selector and configuration options
   - ✅ "No Home Assistant Instance selected" message appears (normal for fresh install)

3. **Failure Indicators:**
   - ❌ Access Error appears
   - ❌ Page doesn't load
   - ❌ Redirect to another page

### Step 6: Verify Permission Grant

1. Go to **Settings > Users & Companies > Users**
2. Click on **Administrator** user
3. Go to **Administration** tab
4. Check **Access Rights** section

**Expected Result:**
- ✅ **Home Assistant Manager** checkbox is checked
- ✅ **Home Assistant User** checkbox is checked (implied by Manager)

### Step 7: Create HA Instance

1. Return to **WOOW Dashboard > Configuration > WOOW HA**
2. Click **+ New Instance** button
3. Fill in test configuration:
   - Instance Name: `Test HA`
   - API URL: `http://homeassistant.local:8123`
   - Access Token: `test_token_12345`
4. Click **Save**

**Expected Result:**
- ✅ Instance is created successfully
- ✅ No permission errors

---

## Test Scenario 2: Reinstallation

This test verifies that reinstalling doesn't create duplicate permissions.

### Step 1: Uninstall Addon

1. Go to **Apps**
2. Search for `WOOW Dashboard`
3. Click **Uninstall**
4. Confirm uninstallation

### Step 2: Reinstall Addon

1. Search for `WOOW Dashboard` again
2. Click **Install**

### Step 3: Check Logs

**Expected Log Output:**

```
============================================================
Initializing Home Assistant addon...
============================================================
✓ User 'admin' already has Home Assistant Manager permissions
✓ Home Assistant WebSocket integration module installed successfully
============================================================
```

**Key Point:** Should say "already has permissions", not "Added user"

### Step 4: Verify No Duplicate Permissions

1. Go to **Settings > Users & Companies > Users**
2. Click **Administrator**
3. Go to **Administration** tab

**Expected Result:**
- ✅ **Home Assistant Manager** is checked (only once, not duplicated)
- ✅ No errors in Odoo logs

---

## Test Scenario 3: Multi-User Environment

This test verifies that only admin gets auto-granted permissions.

### Step 1: Create New User

1. Go to **Settings > Users & Companies > Users**
2. Click **Create**
3. Fill in details:
   - Name: `Test User`
   - Email: `testuser@example.com`
   - Access Rights: Select **Internal User**
4. Click **Save**

### Step 2: Login as New User

1. Logout from admin
2. Login as `testuser@example.com`

### Step 3: Try Accessing HA Settings

1. Navigate to **WOOW Dashboard > Configuration > WOOW HA**

**Expected Result:**
- ❌ Access Error appears (this is correct!)
- ❌ Cannot access settings without permissions

**Error Message Should Be:**
```
Access Error
You are not allowed to access 'Home Assistant Instance' (ha.instance) records.
This operation is allowed for the following groups:
- Administration/Home Assistant Manager
- Administration/Home Assistant User
```

### Step 4: Grant Permissions (As Admin)

1. Logout and login as admin
2. Go to **Settings > Users & Companies > Users**
3. Select **Test User**
4. Go to **Administration** tab
5. Check **Home Assistant User** or **Home Assistant Manager**
6. Click **Save**

### Step 5: Verify New User Access

1. Logout and login as `testuser@example.com`
2. Navigate to **WOOW Dashboard > Configuration > WOOW HA**

**Expected Result:**
- ✅ Settings page loads successfully (if granted Manager)
- ✅ Can view HA instances (if granted User)

---

## Test Scenario 4: Odoo Shell Verification

For advanced users who want to verify permissions programmatically.

### Step 1: Access Odoo Shell

```bash
docker compose -f docker-compose-18.yml exec web odoo shell -d odoo
```

### Step 2: Check Admin Permissions

```python
# Get admin user
admin = env.ref('base.user_admin')

# Get HA Manager group
ha_manager = env.ref('odoo_ha_addon.group_ha_manager')

# Check if admin has HA Manager permission
has_permission = ha_manager in admin.groups_id

print(f"Admin user: {admin.login}")
print(f"Has HA Manager permission: {has_permission}")
print(f"All groups: {admin.groups_id.mapped('name')}")
```

**Expected Output:**

```python
Admin user: admin
Has HA Manager permission: True
All groups: ['Administration / Access Rights', 'Administration / Settings', 'Home Assistant Manager', ...]
```

### Step 3: List All HA Groups

```python
# Get all HA-related groups
ha_groups = env['res.groups'].search([('name', 'like', 'Home Assistant')])

for group in ha_groups:
    print(f"\nGroup: {group.name}")
    print(f"Category: {group.category_id.name}")
    print(f"Users: {group.users.mapped('login')}")
    print(f"Implied Groups: {group.implied_ids.mapped('name')}")
```

**Expected Output:**

```
Group: Home Assistant User
Category: Administration
Users: ['admin']
Implied Groups: []

Group: Home Assistant Manager
Category: Administration
Users: ['admin']
Implied Groups: ['Internal User', 'Home Assistant User']
```

---

## Test Scenario 5: Manual Permission Revocation

This test verifies that permission enforcement still works after auto-grant.

### Step 1: Revoke Admin Permissions

1. Go to **Settings > Users & Companies > Users**
2. Click **Administrator**
3. Go to **Administration** tab
4. **Uncheck** both:
   - ❌ Home Assistant Manager
   - ❌ Home Assistant User
5. Click **Save**

### Step 2: Try Accessing Settings

1. Navigate to **WOOW Dashboard > Configuration > WOOW HA**

**Expected Result:**
- ❌ Access Error appears (proving permissions are properly enforced)

### Step 3: Re-grant Permissions

1. Follow the manual permission grant process to restore access

---

## Troubleshooting

### Issue: Access Error Still Appears After Installation

**Possible Causes:**

1. **Installation Failed Silently**
   - Check logs: `docker compose -f docker-compose-18.yml logs web | grep "post_init_hook"`
   - Look for errors or warnings

2. **Cache Issue**
   - Restart Odoo: `docker compose -f docker-compose-18.yml restart web`
   - Clear browser cache and re-login

3. **Database Already Had Addon**
   - The addon may have been installed before the fix
   - **Solution:** Manually grant permissions (see Manual Fix below)

### Manual Fix for Existing Installations

**Via Web Interface:**

1. Go to **Settings > Users & Companies > Users**
2. Click **Administrator**
3. Go to **Administration** tab
4. Check **Home Assistant Manager**
5. Click **Save**

**Via Odoo Shell:**

```bash
# Access shell
docker compose -f docker-compose-18.yml exec web odoo shell -d odoo

# Grant permission
env['res.users'].browse(2).write({
    'groups_id': [(4, env.ref('odoo_ha_addon.group_ha_manager').id)]
})
```

### Issue: Warning in Logs

**Warning Message:**

```
⚠ Failed to auto-grant HA Manager permissions to admin: [error details]
  Please manually grant 'Home Assistant Manager' permissions via:
  Settings > Users & Companies > Users > [Select User] > Administration tab
```

**Solution:**

This is expected if there's an issue finding the admin user or group. Follow the manual fix instructions above.

---

## Success Criteria Summary

| Test | Success Indicator |
|------|------------------|
| **Fresh Install** | Admin can access HA settings immediately, no Access Error |
| **Reinstall** | Log shows "already has permissions", no duplicate grants |
| **Multi-User** | New users get Access Error until manually granted |
| **Permission Check** | Admin has "Home Assistant Manager" in user settings |
| **Manual Revoke** | Access Error appears when permissions removed (proves enforcement works) |

---

## Automated Test Script

For CI/CD pipelines or automated testing:

```bash
#!/bin/bash
# File: test_ha_permissions.sh

echo "=== Testing HA Permission Auto-Grant ==="

# Start Odoo
docker compose -f docker-compose-18.yml up -d web

# Wait for Odoo to start
sleep 10

# Install addon and check permissions via shell
docker compose -f docker-compose-18.yml exec -T web odoo shell -d odoo <<EOF
# Check if admin has HA Manager permission
admin = env.ref('base.user_admin')
ha_manager = env.ref('odoo_ha_addon.group_ha_manager')
has_permission = ha_manager in admin.groups_id

if has_permission:
    print("✅ TEST PASSED: Admin has HA Manager permissions")
    exit(0)
else:
    print("❌ TEST FAILED: Admin does not have HA Manager permissions")
    exit(1)
EOF

TEST_RESULT=$?

if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ All tests passed"
    exit 0
else
    echo "❌ Tests failed"
    exit 1
fi
```

**Usage:**

```bash
chmod +x test_ha_permissions.sh
./test_ha_permissions.sh
```

---

## Conclusion

This testing guide ensures the post-install permission fix works correctly across various scenarios. The key success indicator is that admin users can access HA settings immediately after installation without manual permission configuration.

If any test fails, review the logs and check the implementation in `/hooks.py`.
