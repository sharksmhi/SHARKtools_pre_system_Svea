from importlib.metadata import entry_points


platform_info = None
platform_info_exceptions = None

for discovered_plugin in entry_points(group='sharktools.platform_info'):
    platform_info = discovered_plugin.load()
    platform_info.exceptions = platform_info.exceptions
