
subscribers = dict()
subscribers_before = dict()
subscribers_after = dict()


class InvalidEventType(Exception):
    pass


class EventTypes:
    def __init__(self):
        self.event_types = [
                'select_instrument',
                'select_station',
                'return_position',
                'confirm_sensors',
                'change_config_path',
                'change_data_path_local',
                'change_data_path_server',
                'button_svepa',
                'button_seasave',
                'focus_out_series',
                'focus_out_station',
                'focus_out_depth',
                'focus_out_cruise',
                'set_next_series',
                'series_step',
                'load_svepa',
                'missing_input',
                'input_ok',
                'select_default_user',
                'add_components',
                'update_components',
                'toggle_tail',
                'update_server_info',
                'set_water_depth',
                'close_seasave',
                'button_goto_processing_simple',
                'button_goto_processing_advanced'
            ]
        for item in self.event_types:
            setattr(self, item, item)

    def __contains__(self, item):
        if item in self.event_types:
            return True
        return False


def _remove_existing(event_type, func):
    func_part = str(func).split()[2]
    for sub in [subscribers_before, subscribers, subscribers_after]:
        for f in list(sub.get(event_type, [])):
            if func_part == str(f).split()[2]:
                # print('REMOVING:', func_part)
                sub[event_type].remove(f)


def subscribe(event_type, func, before=False, after=False):
    _remove_existing(event_type, func)
    # print('ADDING event:', event_type)
    if event_type not in EventTypes():
        raise InvalidEventType(event_type)
    if before:
        if event_type not in subscribers_before:
            subscribers_before[event_type] = set()
        subscribers_before[event_type].add(func)
    elif after:
        if event_type not in subscribers_after:
            subscribers_after[event_type] = set()
        subscribers_after[event_type].add(func)
    else:
        if event_type not in subscribers:
            subscribers[event_type] = set()
        subscribers[event_type].add(func)


def post_event(event_type, data, **kwargs):
    for sub in [subscribers_before, subscribers, subscribers_after]:
        if event_type not in sub:
            continue
        for func in sub[event_type]:
            func(data, **kwargs)


def nr_subscribers(event_type):
    return len(subscribers[event_type])


def print_even_types():
    print('=' * 50)
    print('Current event_types (before) are:')
    print('-' * 50)
    for event_type in sorted(subscribers_before):
        print(' ' * 4, event_type)
    print('-' * 50)
    print('Current event_types are:')
    print('-' * 50)
    for event_type in sorted(subscribers):
        print(' ' * 4, event_type)
    print('=' * 50)


def print_subscribers():
    print('=' * 50)
    print('Current subscribers_before are:')
    print('-' * 50)
    for event_type in sorted(subscribers_before):
        print(' ' * 4, 'event_type:', event_type)
        for func in subscribers_before[event_type]:
            print(' ' * 8, func)
    print('-' * 50)
    print('Current subscribers are:')
    print('-' * 50)
    for event_type in sorted(subscribers):
        print(' ' * 4, 'event_type:', event_type)
        for func in subscribers[event_type]:
            print(' ' * 8, func)
    print('=' * 50)


def test_subscriber():
    print('I am a test subscriber function!')


if __name__ == '__main__':
    subscribe('select_instrument', test_subscriber)
    et = EventTypes()
