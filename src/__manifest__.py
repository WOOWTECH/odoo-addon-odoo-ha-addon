{
    'name': 'WOOW Dashboard',
    'version': '18.0.6.2',
    'category': 'WOOW/Extra Tools',
    'summary': 'Dashboard with Home Assistant integration',
    'depends': ['base', 'web', 'mail', 'portal'],
    # Note: Python dependencies (websockets) are auto-installed by pre_init_hook
    # Do not use external_dependencies as it blocks installation before hook runs
    'data': [
        # Security - 權限組必須在 access rules 之前載入
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/ha_ws_request_queue_security.xml',
        'data/dashboard_data.xml',
        'data/websocket_cron.xml',
        'data/cron.xml',  # Entity share expiry notifications
        # 先定義所有 actions（除了 ha_instance）
        'views/ha_instance_dashboard_action.xml',  # ha_instance_dashboard_action (NEW: 入口頁)
        'views/dashboard_views.xml',  # ha_info_dashboard
        'views/area_dashboard_views.xml',  # area_dashboard_action
        'views/ha_entity_views.xml',  # entity_action
        'views/ha_entity_history_views.xml',  # entity_history_action
        'views/ha_entity_group_views.xml',  # ha_entity_group_action
        'views/ha_entity_group_tag_views.xml',  # ha_entity_group_tag_action
        'views/ha_entity_tag_views.xml',  # ha_entity_tag_action
        'views/ha_area_views.xml',  # ha_area_action
        'views/ha_device_views.xml',  # ha_device_action
        'views/ha_device_tag_views.xml',  # ha_device_tag_action
        'views/ha_label_views.xml',  # ha_label_action
        'views/ha_config_action.xml',  # ha_settings_action
        'views/res_config_settings.xml',
        # ha_instance 定義 action_ha_instance（引用 entity_action）
        'views/ha_instance_views.xml',
        # 選單載入（引用上面所有的 actions，包含 action_ha_instance）
        'views/dashboard_menu.xml',
        # Wizard views
        'wizard/ha_instance_clear_wizard_view.xml',
        'views/ha_entity_share_wizard_views.xml',
        # Portal templates (public views for shared entities)
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # 0. 常數定義 - 最先載入
            'odoo_ha_addon/static/src/constants.js',

            # 1. 服務層
            'odoo_ha_addon/static/src/services/chart_service.js',
            'odoo_ha_addon/static/src/services/ha_data_service.js',
            'odoo_ha_addon/static/src/services/ha_bus_bridge.js',
            'odoo_ha_addon/static/src/services/ha_bus_bridge.xml',

            # 2. 共用工具
            'odoo_ha_addon/static/src/util/debug.js',
            'odoo_ha_addon/static/src/util/color.js',

            # 3. 共用 Hooks - Entity Control Core
            'odoo_ha_addon/static/src/hooks/entity_control/domain_config.js',
            'odoo_ha_addon/static/src/hooks/entity_control/core.js',
            'odoo_ha_addon/static/src/hooks/entity_control/index.js',

            # 4. 基礎圖表組件
            'odoo_ha_addon/static/src/components/charts/unified_chart/unified_chart.js',
            'odoo_ha_addon/static/src/components/charts/unified_chart/unified_chart.xml',
            'odoo_ha_addon/static/src/components/charts/chart/ha_chart.js',
            'odoo_ha_addon/static/src/components/charts/chart/ha_chart.xml',
            'odoo_ha_addon/static/src/components/charts/line_chart/line_chart.js',
            'odoo_ha_addon/static/src/components/charts/line_chart/line_chart.xml',

            # 5. 其他可重用組件
            'odoo_ha_addon/static/src/components/dashboard_item/dashboard_item.js',
            'odoo_ha_addon/static/src/components/dashboard_item/dashboard_item.xml',

            # InstanceSelector - Phase 4: Multi-instance support
            'odoo_ha_addon/static/src/components/instance_selector/instance_selector.js',
            'odoo_ha_addon/static/src/components/instance_selector/instance_selector.xml',

            # HaInstanceSystray - REMOVED: No longer used after menu restructure
            # Systray 組件已移除，改用入口頁導航模式
            # 檔案保留在 components/ha_instance_systray/ 以便未來參考
            # 'odoo_ha_addon/static/src/components/ha_instance_systray/ha_instance_systray.js',
            # 'odoo_ha_addon/static/src/components/ha_instance_systray/ha_instance_systray.xml',

            # EntityController - Shared controller for all entity types
            'odoo_ha_addon/static/src/components/entity_controller/hooks/useEntityControl.js',
            'odoo_ha_addon/static/src/components/entity_controller/entity_controller.js',
            'odoo_ha_addon/static/src/components/entity_controller/entity_controller.xml',
            'odoo_ha_addon/static/src/components/entity_controller/controllers/switch_controller.xml',
            'odoo_ha_addon/static/src/components/entity_controller/controllers/light_controller.xml',
            'odoo_ha_addon/static/src/components/entity_controller/controllers/sensor_controller.xml',
            'odoo_ha_addon/static/src/components/entity_controller/controllers/climate_controller.xml',
            'odoo_ha_addon/static/src/components/entity_controller/controllers/cover_controller.xml',
            'odoo_ha_addon/static/src/components/entity_controller/controllers/fan_controller.xml',
            'odoo_ha_addon/static/src/components/entity_controller/controllers/automation_controller.xml',
            'odoo_ha_addon/static/src/components/entity_controller/controllers/scene_controller.xml',
            'odoo_ha_addon/static/src/components/entity_controller/controllers/script_controller.xml',
            'odoo_ha_addon/static/src/components/entity_controller/controllers/generic_controller.xml',

            # RelatedEntityDialog - Entity related information dialog
            'odoo_ha_addon/static/src/components/related_entity_dialog/related_entity_dialog.js',
            'odoo_ha_addon/static/src/components/related_entity_dialog/related_entity_dialog.xml',
            'odoo_ha_addon/static/src/components/related_entity_dialog/related_entity_dialog.scss',

            # Wrappers for EntityController
            'odoo_ha_addon/static/src/components/entity_demo/entity_demo.js',
            'odoo_ha_addon/static/src/components/entity_demo/entity_demo.xml',
            # Area Dashboard Components (Device-first view)
            'odoo_ha_addon/static/src/components/device_card/device_card.js',
            'odoo_ha_addon/static/src/components/device_card/device_card.xml',
            'odoo_ha_addon/static/src/components/standalone_entity_card/standalone_entity_card.js',
            'odoo_ha_addon/static/src/components/standalone_entity_card/standalone_entity_card.xml',

            # Glances Block Component
            'odoo_ha_addon/static/src/components/glances_block/glances_block.js',
            'odoo_ha_addon/static/src/components/glances_block/glances_block.xml',

            # 6. Views - 按依賴順序載入
            # HaHistory 視圖 (Model -> Renderer -> Parser -> Controller -> View)
            'odoo_ha_addon/static/src/views/hahistory/hahistory_model.js',
            'odoo_ha_addon/static/src/views/hahistory/hahistory_renderer.js',
            'odoo_ha_addon/static/src/views/hahistory/hahistory_renderer.xml',
            'odoo_ha_addon/static/src/views/hahistory/hahistory_arch_parser.js',
            'odoo_ha_addon/static/src/views/hahistory/hahistory_controller.js',
            'odoo_ha_addon/static/src/views/hahistory/hahistory_controller.xml',
            'odoo_ha_addon/static/src/views/hahistory/hahistory_view.js',

            # Entity Kanban 視圖
            'odoo_ha_addon/static/src/views/entity_kanban/entity_kanban_controller.js',
            'odoo_ha_addon/static/src/views/entity_kanban/entity_kanban_controller.xml',
            'odoo_ha_addon/static/src/views/entity_kanban/entity_kanban_view.js',

            # 7. Actions - 依賴前面所有組件
            # HA Instance Dashboard (入口頁) - NEW
            'odoo_ha_addon/static/src/actions/ha_instance_dashboard/ha_instance_dashboard.js',
            'odoo_ha_addon/static/src/actions/ha_instance_dashboard/ha_instance_dashboard.xml',
            # Dashboard and Area Dashboard
            'odoo_ha_addon/static/src/actions/dashboard/dashboard.js',
            'odoo_ha_addon/static/src/actions/dashboard/dashboard.xml',
            'odoo_ha_addon/static/src/actions/area_dashboard/area_dashboard.js',
            'odoo_ha_addon/static/src/actions/area_dashboard/area_dashboard.xml',
            # Glances Device Dashboard
            'odoo_ha_addon/static/src/actions/glances_device_dashboard/glances_device_dashboard.js',
            'odoo_ha_addon/static/src/actions/glances_device_dashboard/glances_device_dashboard.xml',

            # 8. 樣式文件 - 最後載入
            'odoo_ha_addon/static/src/scss/dashboard.scss',
            'odoo_ha_addon/static/src/scss/form_view.scss',
        ],

        # Portal frontend assets for public entity control pages
        # These are loaded on portal pages via web.assets_frontend bundle
        'web.assets_frontend': [
            # Utilities (shared with backend)
            'odoo_ha_addon/static/src/util/debug.js',
            'odoo_ha_addon/static/src/util/color.js',

            # Shared Hooks - Entity Control Core (shared with backend)
            'odoo_ha_addon/static/src/hooks/entity_control/domain_config.js',
            'odoo_ha_addon/static/src/hooks/entity_control/core.js',
            'odoo_ha_addon/static/src/hooks/entity_control/index.js',

            # Portal Service Layer - Token-based API
            'odoo_ha_addon/static/src/portal/portal_entity_service.js',
            'odoo_ha_addon/static/src/portal/hooks/usePortalEntityControl.js',

            # Portal Entity Controller (registered to public_components for <owl-component> tag)
            'odoo_ha_addon/static/src/portal/portal_entity_controller.js',
            'odoo_ha_addon/static/src/portal/portal_entity_controller.xml',

            # Portal Entity Info Component (info cards with auto-polling)
            'odoo_ha_addon/static/src/portal/portal_entity_info.js',
            'odoo_ha_addon/static/src/portal/portal_entity_info.xml',

            # Portal Group Info Component (group info with entities table)
            'odoo_ha_addon/static/src/portal/portal_group_info.js',
            'odoo_ha_addon/static/src/portal/portal_group_info.xml',

            # Portal Live Status Component (sidebar live state display)
            'odoo_ha_addon/static/src/portal/portal_live_status.js',
            'odoo_ha_addon/static/src/portal/portal_live_status.xml',

            # Portal Styles
            'odoo_ha_addon/static/src/scss/portal.scss',
        ],
    },
    'installable': True,
    'application': True,
    # 'auto_install': False,
    'license': 'LGPL-3',
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'post_load': 'post_load_hook',
}
