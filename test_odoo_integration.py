#!/usr/bin/env python3
"""
Integration test for follows_device_area feature via Odoo XML-RPC.
"""

import xmlrpc.client
import sys

# Odoo connection settings
URL = 'http://localhost:8069'
DB = 'woowtech'
USERNAME = 'woowtech@designsmart.com.tw'
PASSWORD = 'test123'

def main():
    print("\n" + "="*60)
    print("Testing 'follows_device_area' Feature via Odoo XML-RPC")
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

    # Check if ha.entity model exists and has new fields
    print("\n3. Checking ha.entity model fields...")
    try:
        fields = models.execute_kw(
            DB, uid, PASSWORD,
            'ha.entity', 'fields_get',
            [],
            {'attributes': ['string', 'type', 'help']}
        )

        required_fields = ['follows_device_area', 'display_area_id']
        for field in required_fields:
            if field in fields:
                print(f"   ✅ Field '{field}' exists: {fields[field]['string']} ({fields[field]['type']})")
            else:
                print(f"   ❌ Field '{field}' NOT FOUND - module may need upgrade")

    except Exception as e:
        print(f"   ❌ Error checking fields: {e}")
        print("   → Module may not be installed or needs upgrade")
        sys.exit(1)

    # Get sample entities with devices
    print("\n4. Fetching entities with devices...")
    try:
        entities = models.execute_kw(
            DB, uid, PASSWORD,
            'ha.entity', 'search_read',
            [[['device_id', '!=', False]]],
            {
                'fields': ['entity_id', 'name', 'area_id', 'device_id', 'follows_device_area', 'display_area_id'],
                'limit': 10
            }
        )

        if entities:
            print(f"   ✅ Found {len(entities)} entities with devices:")
            for e in entities[:5]:
                area_name = e['area_id'][1] if e['area_id'] else 'None'
                device_name = e['device_id'][1] if e['device_id'] else 'None'
                display_area = e['display_area_id'][1] if e['display_area_id'] else 'None'
                follows = '✓' if e['follows_device_area'] else '✗'
                print(f"      - {e['entity_id'][:40]:<40} | follows: {follows} | area: {area_name} | display: {display_area}")
        else:
            print("   ⚠ No entities with devices found")

    except Exception as e:
        print(f"   ❌ Error fetching entities: {e}")

    # Test: Find entities that should follow device area (area_id is False but has device)
    print("\n5. Checking entities that follow device area...")
    try:
        following_entities = models.execute_kw(
            DB, uid, PASSWORD,
            'ha.entity', 'search_read',
            [[['follows_device_area', '=', True]]],
            {
                'fields': ['entity_id', 'name', 'area_id', 'device_id', 'display_area_id'],
                'limit': 10
            }
        )

        if following_entities:
            print(f"   ✅ Found {len(following_entities)} entities following device area:")
            for e in following_entities[:5]:
                device_name = e['device_id'][1] if e['device_id'] else 'None'
                display_area = e['display_area_id'][1] if e['display_area_id'] else 'None'
                print(f"      - {e['entity_id'][:40]:<40} | device: {device_name[:20]} | effective area: {display_area}")
        else:
            print("   ⚠ No entities currently following device area")
            print("   → This is normal if you haven't synced entities yet, or all entities have their own area")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print("""
Fields Status:
  - follows_device_area: """ + ("✅ EXISTS" if 'follows_device_area' in fields else "❌ MISSING") + """
  - display_area_id: """ + ("✅ EXISTS" if 'display_area_id' in fields else "❌ MISSING") + """

Next Steps:
  1. Run entity sync from HA Dashboard to populate follows_device_area
  2. Check entities in Form view - should see 'Follows Device' toggle
  3. Test toggling the checkbox and verify sync to HA
""")

if __name__ == '__main__':
    main()
