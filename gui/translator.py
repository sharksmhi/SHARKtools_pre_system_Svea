

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

             '_mprog':   'Övervakningsprogram',
             '_proj':    'Projekt',
             '_orderer': 'Beställare',
             '_slabo':   'Provtagande laboratorium',
             '_alabo':   'Analyserande laboratorium',

             '_wadep': 'Vattendjup vid sation [m]',
             '_windir': 'Vindriktning',
             '_windsp': 'Vindhastighet [m/s]',
             '_airtemp': 'Vindtemperatur [grader C]',
             '_airpres': 'Lufttryck [hPa]',
             '_weather': 'Väder [kod]',
             '_cloud': 'Moln [kod]',
             '_waves': 'Vågor [kod]',
             '_ice': 'Is [kod]',
             '_comment': 'CTD kommentar'}

    def get(self, item):
        return self.names.get(item, item)