#!/usr/bin/env python3
"""
Manually test the follows_device_area feature by:
1. Finding an entity with a device
2. Setting follows_device_area = True
3. Verifying display_area_id shows device's area
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
    print("Manual Test: follows_device_area Feature")
    print("="*60 + "\n")

    # Connect and authenticate
    common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    if not uid:
        print("❌ Authentication failed")
        sys.exit(1)
    print(f"✅ Connected as user ID: {uid}")

    models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

    # Find an entity with a device that has an area
    print("\n1. Finding entity with device that has an area...")

    # First, get devices with areas
    devices_with_area = models.execute_kw(
        DB, uid, PASSWORD,
        'ha.device', 'search_read',
        [[['area_id', '!=', False]]],
        {'fields': ['id', 'name', 'area_id'], 'limit': 5}
    )

    if not devices_with_area:
        print("   ⚠ No devices with areas found")
        print("   → Need to set up device areas first")

        # Try to find any device
        any_device = models.execute_kw(
            DB, uid, PASSWORD,
            'ha.device', 'search_read',
            [[]],
            {'fields': ['id', 'name', 'area_id'], 'limit': 1}
        )
        if any_device:
            print(f"\n   Found device without area: {any_device[0]['name']}")
            print("   Setting up test area...")

            # Create a test area
            areas = models.execute_kw(
                DB, uid, PASSWORD,
                'ha.area', 'search_read',
                [[]],
                {'fields': ['id', 'name'], 'limit': 1}
            )

            if areas:
                area_id = areas[0]['id']
                area_name = areas[0]['name']
                print(f"   Using existing area: {area_name}")

                # Update device with area
                models.execute_kw(
                    DB, uid, PASSWORD,
                    'ha.device', 'write',
                    [[any_device[0]['id']], {'area_id': area_id}]
                )
                print(f"   ✅ Set device '{any_device[0]['name']}' to area '{area_name}'")
                devices_with_area = [{'id': any_device[0]['id'], 'name': any_device[0]['name'], 'area_id': [area_id, area_name]}]
            else:
                print("   ❌ No areas found in system")
                sys.exit(1)
        else:
            print("   ❌ No devices found")
            sys.exit(1)

    device = devices_with_area[0]
    print(f"   Found device: {device['name']} (area: {device['area_id'][1]})")

    # Find entity with this device
    print("\n2. Finding entity belonging to this device...")
    entities = models.execute_kw(
        DB, uid, PASSWORD,
        'ha.entity', 'search_read',
        [[['device_id', '=', device['id']]]],
        {'fields': ['id', 'entity_id', 'name', 'area_id', 'follows_device_area', 'display_area_id'], 'limit': 1}
    )

    if not entities:
        print("   ❌ No entities found for this device")
        sys.exit(1)

    entity = entities[0]
    print(f"   Found entity: {entity['entity_id']}")
    print(f"   Current state:")
    print(f"     - area_id: {entity['area_id'][1] if entity['area_id'] else 'None'}")
    print(f"     - follows_device_area: {entity['follows_device_area']}")
    print(f"     - display_area_id: {entity['display_area_id'][1] if entity['display_area_id'] else 'None'}")

    # Test 1: Set follows_device_area = True
    print("\n3. Setting follows_device_area = True...")
    try:
        models.execute_kw(
            DB, uid, PASSWORD,
            'ha.entity', 'write',
            [[entity['id']], {'follows_device_area': True, 'area_id': False}]
        )
        print("   ✅ Updated successfully!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        sys.exit(1)

    # Re-read entity
    print("\n4. Verifying changes...")
    entity = models.execute_kw(
        DB, uid, PASSWORD,
        'ha.entity', 'search_read',
        [[['id', '=', entity['id']]]],
        {'fields': ['id', 'entity_id', 'area_id', 'follows_device_area', 'display_area_id']}
    )[0]

    print(f"   Entity: {entity['entity_id']}")
    print(f"   - area_id: {entity['area_id'][1] if entity['area_id'] else 'None'}")
    print(f"   - follows_device_area: {entity['follows_device_area']}")
    print(f"   - display_area_id: {entity['display_area_id'][1] if entity['display_area_id'] else 'None'}")

    # Verify
    if entity['follows_device_area'] and entity['display_area_id']:
        if entity['display_area_id'][0] == device['area_id'][0]:
            print(f"\n   ✅ SUCCESS! display_area_id correctly shows device's area: {device['area_id'][1]}")
        else:
            print(f"\n   ⚠ display_area_id doesn't match device's area")
            print(f"      Expected: {device['area_id'][1]}")
            print(f"      Got: {entity['display_area_id'][1] if entity['display_area_id'] else 'None'}")
    elif entity['follows_device_area'] and not entity['display_area_id']:
        print(f"\n   ⚠ follows_device_area is True but display_area_id is empty")
        print(f"      This might indicate the compute field is not working correctly")
    else:
        print(f"\n   ❌ follows_device_area was not set correctly")

    # Test 2: Reset
    print("\n5. Resetting entity (follows_device_area = False)...")
    try:
        models.execute_kw(
            DB, uid, PASSWORD,
            'ha.entity', 'write',
            [[entity['id']], {'follows_device_area': False}]
        )
        print("   ✅ Reset successfully!")
    except Exception as e:
        print(f"   ⚠ Reset warning: {e}")

    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
