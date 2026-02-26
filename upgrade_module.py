#!/usr/bin/env python3
"""
Upgrade odoo_ha_addon module via XML-RPC.
"""

import xmlrpc.client
import sys
import time

# Odoo connection settings
URL = 'http://localhost:8069'
DB = 'woowtech'
USERNAME = 'woowtech@designsmart.com.tw'
PASSWORD = 'test123'

def main():
    print("\n" + "="*60)
    print("Upgrading odoo_ha_addon Module")
    print("="*60 + "\n")

    # Connect to Odoo
    print("1. Connecting to Odoo...")
    try:
        common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
        version = common.version()
        print(f"   ✅ Connected to Odoo {version['server_version']}")
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        sys.exit(1)

    # Authenticate
    print("\n2. Authenticating...")
    try:
        uid = common.authenticate(DB, USERNAME, PASSWORD, {})
        if uid:
            print(f"   ✅ Authenticated as user ID: {uid}")
        else:
            print("   ❌ Authentication failed")
            sys.exit(1)
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        sys.exit(1)

    # Create models proxy
    models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

    # Find odoo_ha_addon module
    print("\n3. Finding odoo_ha_addon module...")
    try:
        modules = models.execute_kw(
            DB, uid, PASSWORD,
            'ir.module.module', 'search_read',
            [[['name', '=', 'odoo_ha_addon']]],
            {'fields': ['id', 'name', 'state', 'latest_version']}
        )

        if modules:
            module = modules[0]
            print(f"   ✅ Found module: {module['name']}")
            print(f"      State: {module['state']}")
            print(f"      Version: {module['latest_version']}")
            module_id = module['id']
        else:
            print("   ❌ Module not found")
            sys.exit(1)

    except Exception as e:
        print(f"   ❌ Error: {e}")
        sys.exit(1)

    # Trigger upgrade
    print("\n4. Triggering module upgrade...")
    try:
        # Set module state to 'to upgrade'
        models.execute_kw(
            DB, uid, PASSWORD,
            'ir.module.module', 'button_immediate_upgrade',
            [[module_id]]
        )
        print("   ✅ Module upgrade triggered successfully!")

    except Exception as e:
        error_msg = str(e)
        if "restart" in error_msg.lower() or "upgrade" in error_msg.lower():
            print("   ⚠ Upgrade initiated - server may restart")
        else:
            print(f"   ❌ Error: {e}")
            print("\n   Alternative: Run manually in Odoo shell:")
            print("   $ podman exec -it <container> odoo shell -d woowtech")
            print("   >>> env['ir.module.module'].search([('name','=','odoo_ha_addon')]).button_immediate_upgrade()")
            sys.exit(1)

    # Wait and verify
    print("\n5. Waiting for server to restart (10 seconds)...")
    time.sleep(10)

    print("\n6. Verifying upgrade...")
    try:
        # Reconnect
        common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
        uid = common.authenticate(DB, USERNAME, PASSWORD, {})
        models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

        # Check fields
        fields = models.execute_kw(
            DB, uid, PASSWORD,
            'ha.entity', 'fields_get',
            [],
            {'attributes': ['string', 'type']}
        )

        if 'follows_device_area' in fields:
            print("   ✅ Field 'follows_device_area' now exists!")
        else:
            print("   ❌ Field 'follows_device_area' still missing")

        if 'display_area_id' in fields:
            print("   ✅ Field 'display_area_id' now exists!")
        else:
            print("   ❌ Field 'display_area_id' still missing")

    except Exception as e:
        print(f"   ⚠ Could not verify: {e}")
        print("   → Server may still be restarting")

    print("\n" + "="*60)
    print("Done!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
