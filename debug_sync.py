#!/usr/bin/env python3
"""
Debug sync: Manually trigger entity sync and check follows_device_area.
"""

import xmlrpc.client
import sys

URL = 'http://localhost:8069'
DB = 'woowtech'
USERNAME = 'woowtech@designsmart.com.tw'
PASSWORD = 'test123'

def main():
    print("\n" + "="*60)
    print("Debug: Entity Sync for follows_device_area")
    print("="*60 + "\n")

    common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

    print("1. Finding specific entity (light.jie_dai_qu_ci_xi_gui_2)...")
    entity = models.execute_kw(
        DB, uid, PASSWORD,
        'ha.entity', 'search_read',
        [[['entity_id', '=', 'light.jie_dai_qu_ci_xi_gui_2']]],
        {'fields': ['id', 'entity_id', 'area_id', 'device_id', 'follows_device_area', 'display_area_id']}
    )

    if entity:
        e = entity[0]
        print(f"   Entity ID: {e['id']}")
        print(f"   entity_id: {e['entity_id']}")
        print(f"   area_id: {e['area_id']}")
        print(f"   device_id: {e['device_id']}")
        print(f"   follows_device_area: {e['follows_device_area']}")
        print(f"   display_area_id: {e['display_area_id']}")
    else:
        print("   Entity not found!")
        return

    # Check if device has area
    if entity[0]['device_id']:
        device_id = entity[0]['device_id'][0]
        print(f"\n2. Checking device (ID: {device_id})...")
        device = models.execute_kw(
            DB, uid, PASSWORD,
            'ha.device', 'search_read',
            [[['id', '=', device_id]]],
            {'fields': ['id', 'name', 'device_id', 'area_id']}
        )
        if device:
            d = device[0]
            print(f"   Device name: {d['name']}")
            print(f"   Device device_id (HA): {d['device_id']}")
            print(f"   Device area_id: {d['area_id']}")

    print("\n3. Stats before sync...")
    following_count = models.execute_kw(DB, uid, PASSWORD, 'ha.entity', 'search_count', [[['follows_device_area', '=', True]]])
    print(f"   Entities with follows_device_area=True: {following_count}")

    print("\n4. Triggering full entity sync...")
    try:
        # Get instance ID first
        instances = models.execute_kw(
            DB, uid, PASSWORD,
            'ha.instance', 'search_read',
            [[['active', '=', True]]],
            {'fields': ['id', 'name'], 'limit': 1}
        )
        if instances:
            instance_id = instances[0]['id']
            print(f"   Using instance: {instances[0]['name']} (ID: {instance_id})")

            # Trigger sync
            result = models.execute_kw(
                DB, uid, PASSWORD,
                'ha.entity', 'sync_entity_states_from_ha',
                [],
                {'instance_id': instance_id, 'sync_area_relations': True}
            )
            print(f"   Sync triggered!")
        else:
            print("   No active HA instance found!")
            return
    except Exception as e:
        print(f"   Sync error (may be normal): {str(e)[:100]}")

    print("\n5. Stats after sync...")
    following_count = models.execute_kw(DB, uid, PASSWORD, 'ha.entity', 'search_count', [[['follows_device_area', '=', True]]])
    print(f"   Entities with follows_device_area=True: {following_count}")

    print("\n6. Re-checking entity...")
    entity = models.execute_kw(
        DB, uid, PASSWORD,
        'ha.entity', 'search_read',
        [[['entity_id', '=', 'light.jie_dai_qu_ci_xi_gui_2']]],
        {'fields': ['id', 'entity_id', 'area_id', 'device_id', 'follows_device_area', 'display_area_id']}
    )
    if entity:
        e = entity[0]
        print(f"   area_id: {e['area_id']}")
        print(f"   device_id: {e['device_id']}")
        print(f"   follows_device_area: {e['follows_device_area']}")
        print(f"   display_area_id: {e['display_area_id']}")

        if e['follows_device_area']:
            print("\n   ✅ SUCCESS! follows_device_area is now True!")
        else:
            print("\n   ❌ FAILED! follows_device_area is still False")
            print("   → Need to check Odoo logs for errors")

if __name__ == '__main__':
    main()
