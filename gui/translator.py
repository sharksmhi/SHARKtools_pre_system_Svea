

class Translator:
    names = {'_depth': 'Plotdjup',
             '_bin_size': 'Bin-storlek',
             '_cruise': 'Cruise',
             '_vessel': 'Fartyg',
             '_series': 'Serie',
             '_station': 'Station',
             '_distance': 'Avstånd station (m)',
             '_operator': 'Operator',
             '_position': 'Position',
             '_event_id': 'EventID      ',
             '_parent_event_id': 'ParentEventID',

             'mprog':   'Övervakningsprogram',
             'proj':    'Projekt',
             'orderer': 'Beställare',
             'slabo':   'Provtagande laboratorium',
             'alabo':   'Analyserande laboratorium',

             'wadep': 'Vattendjup vid station [m]',
             'windir': 'Vindriktning',
             'windsp': 'Vindhastighet [m/s]',
             'airtemp': 'Vindtemperatur [grader C]',
             'airpres': 'Lufttryck [hPa]',
             'weather': 'Väder [kod]',
             'cloud': 'Moln [kod]',
             'waves': 'Vågor [kod]',
             'ice': 'Is [kod]',
             'comment': 'CTD kommentar'}

    def get(self, item):
        return self.names.get(item, item)