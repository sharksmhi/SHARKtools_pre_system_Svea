

class Translator:
    names = {'_depth': 'Plot Depth',
             '_bin_size': 'Bin size',
             '_cruise': 'Cruise',
             '_vessel': 'Vessel',
             '_series': 'Series',
             '_station': 'Station',
             '_distance': 'Distance to station (m)',
             '_operator': 'Operator',
             '_position': 'Position',
             '_event_id': 'EventID      ',
             '_parent_event_id': 'ParentEventID'}

    def get(self, item):
        return self.names.get(item, item)