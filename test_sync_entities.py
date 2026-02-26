#!/usr/bin/env python3
"""
Trigger entity sync and verify follows_device_area is set correctly.
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
    print("Testing Entity Sync with follows_device_area")
    print("="*60 + "\n")

    # Connect and authenticate
    print("1. Connecting to Odoo...")
    common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    if not uid:
        print("   ❌ Authentication failed")
        sys.exit(1)
    print(f"   ✅ Connected as user ID: {uid}")

    models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

    # Get current stats before sync
    print("\n2. Current entity stats (before sync)...")
    try:
        total = models.execute_kw(DB, uid, PASSWORD, 'ha.entity', 'search_count', [[]])
        with_device = models.execute_kw(DB, uid, PASSWORD, 'ha.entity', 'search_count', [[['device_id', '!=', False]]])
        following = models.execute_kw(DB, uid, PASSWORD, 'ha.entity', 'search_count', [[['follows_device_area', '=', True]]])
        print(f"   Total entities: {total}")
        print(f"   With device: {with_device}")
        print(f"   Following device area: {following}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Trigger sync
    print("\n3. Triggering entity sync...")
    try:
        # Call sync method
        result = models.execute_kw(
            DB, uid, PASSWORD,
            'ha.entity', 'sync_entity_states_from_ha',
            [],
            {'instance_id': None, 'sync_area_relations': True}
        )
        print("   ✅ Sync triggered successfully!")
        time.sleep(3)  # Wait for sync to complete
    except Exception as e:
        print(f"   ⚠ Sync may have completed with warning: {str(e)[:100]}")

    # Get stats after sync
    print("\n4. Entity stats (after sync)...")
    try:
        total = models.execute_kw(DB, uid, PASSWORD, 'ha.entity', 'search_count', [[]])
        with_device = models.execute_kw(DB, uid, PASSWORD, 'ha.entity', 'search_count', [[['device_id', '!=', False]]])
        following = models.execute_kw(DB, uid, PASSWORD, 'ha.entity', 'search_count', [[['follows_device_area', '=', True]]])
        print(f"   Total entities: {total}")
        print(f"   With device: {with_device}")
        print(f"   Following device area: {following}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Show sample entities that follow device area
    print("\n5. Entities following device area...")
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
                device_name = e['device_id'][1][:25] if e['device_id'] else 'None'
                display_area = e['display_area_id'][1] if e['display_area_id'] else 'None'
                print(f"      - {e['entity_id'][:35]:<35} | device: {device_name:<25} | area: {display_area}")
        else:
            print("   ⚠ No entities following device area")
            print("   → Check if any entities in HA are set to 'follow device area'")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Show entities with device but NOT following (should have their own area)
    print("\n6. Entities with device but own area...")
    try:
        own_area_entities = models.execute_kw(
            DB, uid, PASSWORD,
            'ha.entity', 'search_read',
            [[
                ['device_id', '!=', False],
                ['follows_device_area', '=', False],
                ['area_id', '!=', False]
            ]],
            {
                'fields': ['entity_id', 'name', 'area_id', 'device_id'],
                'limit': 5
            }
        )

        if own_area_entities:
            print(f"   Found {len(own_area_entities)} entities with their own area:")
            for e in own_area_entities[:3]:
                area_name = e['area_id'][1] if e['area_id'] else 'None'
                device_name = e['device_id'][1][:25] if e['device_id'] else 'None'
                print(f"      - {e['entity_id'][:35]:<35} | device: {device_name:<25} | own area: {area_name}")
        else:
            print("   No entities with device and own area")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
