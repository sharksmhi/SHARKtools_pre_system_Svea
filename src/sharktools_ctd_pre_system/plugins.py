from importlib.metadata import entry_points
import uuid


platform_info = None
platform_info_exceptions = None

for discovered_plugin in entry_points(group='sharktools.platform_info'):
    platform_info = discovered_plugin.load()
    platform_info.exceptions = platform_info.exceptions


def get_platform_info(**kwargs) -> dict:
    data = dict(platform_name='platform')
    if platform_info:
        data.update(platform_info.get_platform_info(**kwargs))
    return data


def get_current_platform_data(**kwargs) -> dict:
    data = dict(
        event_id=str(uuid.uuid4()),
        parent_event_id=str(uuid.uuid4()),
    )
    if platform_info:
        data.update(platform_info.get_current_data(**kwargs))
    return data
