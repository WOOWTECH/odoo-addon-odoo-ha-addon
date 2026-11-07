from datetime import datetime, timedelta, timezone
import pytz

def parse_iso_datetime(iso_str):
    # 分離日期時間和時區部分
    date_time_str, tz_str = iso_str.split('T')
    time_str, tz_offset_str = tz_str[:8], tz_str[8:]

    # 解析日期和時間部分
    naive_datetime = datetime.strptime(f"{date_time_str}T{time_str}", "%Y-%m-%dT%H:%M:%S")

    return naive_datetime

    # 處理時區部分
    if tz_offset_str == 'Z':
        # UTC 時間
        return naive_datetime.replace(tzinfo=timezone.utc)
    else:
        # 解析時區偏移
        sign = 1 if tz_offset_str[0] == '+' else -1
        offset_hours = int(tz_offset_str[1:3])
        offset_minutes = int(tz_offset_str[4:6])
        offset = timedelta(hours=offset_hours, minutes=offset_minutes) * sign

        # 確保 offset 在正確的範圍內
        if not timedelta(hours=-24) < offset < timedelta(hours=24):
            raise ValueError(f"Invalid timezone offset: {offset}")

        return naive_datetime.replace(tzinfo=timezone(offset))

def parse_domain_from_entitiy_id(entity_id):
    """
    input:
        entity_id: sensor.weather_temperature
    output:
        'sensor'
    """
    parts = entity_id.split('.')
    if len(parts) != 2:
        raise ValueError(f"Invalid domain format for entity ID {entity_id}")
    return parts[0]

def to_iso_datetime_time_string(dt):
    # 設定時區為 +8 時區
    tz = pytz.timezone('Asia/Taipei')
    dt = dt.astimezone(tz)

    # 格式化為指定格式的字串
    formatted_date = dt.strftime('%Y-%m-%dT%H:%M:%S%z')

    # 在 %z 格式中，時區偏移量是以 "+0800" 的形式顯示的
    # 如果你需要 "+08:00" 的形式，可以手動調整
    formatted_date = formatted_date[:-2] + ':' + formatted_date[-2:]

    # print(formatted_date)
    return formatted_date

def ensure_ha_manager(env):
    """
    Raise AccessError unless the environment is superuser (system code,
    cron, WebSocket worker, explicit sudo()) or the user is an HA Manager.

    Used on public model methods that trigger Home Assistant calls or full
    synchronisations and are therefore reachable through /web/dataset/call_kw.
    """
    if env.su or env.user.has_group('odoo_ha_addon.group_ha_manager'):
        return
    from odoo import _
    from odoo.exceptions import AccessError
    raise AccessError(_('Only Home Assistant Managers can perform this operation.'))


def ensure_ha_entity_control(records):
    """
    Raise AccessError unless the current user may control ``records`` the
    same way /odoo_ha_addon/call_service allows it:

    - superuser and HA Managers: always;
    - HA Users: only for entities they can read through the ORM (ir.rule)
      and whose domain is not in MANAGER_ONLY_DOMAINS (script, automation,
      update, ...).
    """
    env = records.env
    if env.su or env.user.has_group('odoo_ha_addon.group_ha_manager'):
        return
    from odoo import _
    from odoo.exceptions import AccessError
    from .service_policy import CONTROL_SERVICES, MANAGER_ONLY_DOMAINS
    if not env.user.has_group('odoo_ha_addon.group_ha_user'):
        raise AccessError(_('Only Home Assistant Users can control entities.'))
    records.check_access('read')
    for record in records:
        if record.domain in MANAGER_ONLY_DOMAINS or record.domain not in CONTROL_SERVICES:
            raise AccessError(_('Only Home Assistant Managers can perform this operation.'))
