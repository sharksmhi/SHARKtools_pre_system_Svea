import tkinter as tk
from tkinter import messagebox

from . import components

from sharkpylib.tklib import tkinter_widgets as tkw

from ..saves import SaveSelection

from pre_system_svea.operator import Operators
from pre_system_svea.station import Stations

TEXT_LJUST = 10


class ColoredFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, highlightbackground=None, highlightcolor=None, highlightthickness=1)

    def set_frame_color(self, color):
        self.config(highlightbackground=color, highlightcolor=color)

    def set_frame_thickness(self, thickness):
        self.config(highlightthickness=thickness)

    def set_fill_color(self, color):
        self.config(bg=color)


class CommonFrameMethods:
    operators = Operators()
    stations = Stations()

    def get_operator_list(self):
        """
        :return: list of strings
        """
        return self.operators.get_operator_list()

    def get_station_list(self):
        """
        :return: list of strings
        """
        return self.stations.get_station_list()


class StationPreSystemFrame(ColoredFrame, SaveSelection, CommonFrameMethods):

    def __init__(self,
                 parent,
                 **kwargs):
        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        super().__init__(parent)

        self.grid(**self.grid_frame)

        self._saves_id_key = 'StationPreSystemFrame'
        self._selections_to_store = []

        self._build_frame()

        self._initiate_frame()

        self.load_selection()

    def _build_frame(self):
        frame = tk.Frame(self)
        frame.grid(row=0, column=0, sticky='nw')
        tkw.grid_configure(self)

        layout = dict(padx=5, pady=5, sticky='nw')

        self._cruise = components.CruiseLabelDoubleEntry(frame, title='Cruise'.ljust(TEXT_LJUST), row=0, column=0, **layout)
        self._series = components.SeriesEntryPicker(frame, title='Series'.ljust(TEXT_LJUST), row=1, column=0, **layout)
        self._station = components.LabelDropdownList(frame, title='Station'.ljust(TEXT_LJUST), width=25, autocomplete=True, row=2, column=0, **layout)
        self._distance = components.LabelEntry(frame, title='Distance to station'.ljust(TEXT_LJUST), state='disabled', data_type=int, row=3, column=0, **layout)
        self._depth = components.LabelEntry(frame, title='Depth'.ljust(TEXT_LJUST), data_type=float, row=4, column=0, **layout)
        self._operator = components.LabelDropdownList(frame, title='Operator'.ljust(TEXT_LJUST), row=5, column=0, **layout)

        self._vessel = components.VesselLabelDoubleEntry(frame, title='Vessel'.ljust(TEXT_LJUST), row=0, column=1, **layout)
        self._new_station = components.LabelCheckbox(frame, title='New station'.ljust(TEXT_LJUST), row=1, column=1, **layout)
        self._nr_of_ticks = components.LabelDropdownList(frame, title='Number of ticks'.ljust(TEXT_LJUST), row=2, column=1,
                                                     **layout)
        self._svepa = components.CallbackButton(frame, title='Load SVEPA', row=3, column=1, **layout)
        self._position = components.PositionEntries(frame, row=4, column=1, **layout)
        self._validate = components.CallbackButton(frame, title='Validate', row=5, column=1, **layout)

        tkw.grid_configure(frame, nr_rows=6, nr_columns=2)

        # Adding callbacks
        self._station.add_callback_select(self._on_select_station)
        self._depth.add_callback(self._on_select_depth)
        self._svepa.add_callback(self._load_svepa)
        self._position.add_callback(self._on_select_lat_lon)
        self._validate.add_callback(self._validate_all)

        # Store selection
        self._selections_to_store = ['_cruise', '_series', '_station', '_depth', '_operator',
                                     '_vessel', '_new_station', '_nr_of_ticks', '_position']

    def _initiate_frame(self):
        self._station.values = self.get_station_list()
        self._depth.values = get_depth_list()
        self._operator.values = self.get_operator_list()
        self._nr_of_ticks.values = get_nr_of_ticks_list()

    def _on_select_station(self, *args):
        station_name = self._station.value
        station_info = self.stations.get_station_info(station_name)
        if not station_info:
            return
        self._depth.value = str(station_info.get('depth'))
        self.save_selection()

    def _on_select_lat_lon(self, *args):
        lat, lon = self._position.get()
        if not lat and lon:
            return
        # Check position against station list
        station_info = self.stations.get_closest_station(lat, lon)
        if not station_info:
            self._station.value = ''
            self._distance.value = ''
            return

        self._station.value = station_info.get('station', '')
        self._depth.value = station_info.get('depth', '')
        self._distance.value = station_info.get('distance', '')

    def _on_select_depth(self, *args):
        pass

    def _validate_all(self):
        """
        Validates if station and depth has matching information.
        :return:
        """
        pass

    def _is_validate_station_name(self):
        """
        Check if the station name is valid
        :return:
        """
        station_name = self._station.value
        station_info = self.stations.get_station_info(station_name)
        if not station_info:
            return False


    def _load_svepa(self):
        print('Loading SVEPA information')


class TransectPreSystemFrame(ColoredFrame, SaveSelection, CommonFrameMethods):

    def __init__(self,
                 parent,
                 **kwargs):
        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        super().__init__(parent)

        self.grid(**self.grid_frame)

        self._saves_id_key = 'TransectPreSystemFrame'
        self._selections_to_store = []

        self._build_frame()

        self._initiate_frame()

        self.load_selection()

    def _build_frame(self):
        frame = tk.Frame(self)
        frame.grid(row=0, column=0, sticky='nw')
        tkw.grid_configure(self)

        layout = dict(padx=5, pady=5, sticky='nw')

        self._cruise = components.CruiseLabelDoubleEntry(frame, title='Cruise'.ljust(TEXT_LJUST), row=0, column=0, **layout)
        self._series = components.SeriesEntryPicker(frame, title='Series'.ljust(TEXT_LJUST), row=1, column=0, **layout)
        self._transect = components.LabelDropdownList(frame, title='Transect'.ljust(TEXT_LJUST), width=15, row=2, column=0, **layout)
        self._operator = components.LabelDropdownList(frame, title='Operator'.ljust(TEXT_LJUST), row=4, column=0, **layout)

        self._vessel = components.VessleLabelDoubleEntry(frame, title='Vessel'.ljust(TEXT_LJUST), row=0, column=1, **layout)
        self._new_transect = components.LabelCheckbox(frame, title='New transect'.ljust(TEXT_LJUST), row=1, column=1, **layout)

        tkw.grid_configure(frame, nr_rows=5, nr_columns=2)

        # Adding callbacks
        self._transect.add_callback_select(self._on_select_transect)

        # Store selection
        self._selections_to_store = ['_cruise', '_series', '_transect', '_operator',
                                     '_vessel', '_new_transect']

    def _initiate_frame(self):
        self._transect.values = get_transect_list()
        self._operator.values = self.get_operator_list()

    def _on_select_transect(self, *args):
        print(args)


class ProcessingFrame(ColoredFrame, SaveSelection):

    def __init__(self,
                 parent,
                 **kwargs):
        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        super().__init__(parent)

        self.grid(**self.grid_frame)

        self._saves_id_key = 'StationPreSystemFrame'
        self._selections_to_store = []

        self._build_frame()

        self.load_selection()

    def _build_frame(self):
        frame = tk.Frame(self)
        frame.grid(row=0, column=0, sticky='nw')
        tkw.grid_configure(self)

        layout = dict(padx=5, pady=5, sticky='nw')

        # Store selection
        self._selections_to_store = []


class FrameProcessing(ColoredFrame):

    def __init__(self, parent):
        super().__init__(parent)

        self.__instrument = ''

        self._build_frame()

    def _build_frame(self):

        frame = tk.Frame(self)
        frame.grid(row=0, column=0, sticky='nw')
        tkw.grid_configure(self)

        layout = dict(padx=5, pady=5, sticky='nwse')

        self.instrument_text_frame = components.SelectedInstrumentTextFrame(frame, row=0, column=0, **layout)

        self.content_frame = ProcessingFrame(frame, row=1, column=0, **layout)

        tkw.grid_configure(frame, nr_rows=2)

    def _update_frame(self):
        self.instrument_text_frame.instrument = self.__instrument

    def save_selection(self):
        self.content_frame.save_selection()

    @property
    def instrument(self):
        return self.__instrument

    @instrument.setter
    def instrument(self, name):
        self.__instrument = name
        self._update_frame()


class FrameSelectInstrument(ColoredFrame):

    def __init__(self, parent):
        super().__init__(parent)

        self.buttons = {}

        self._selected = None

        self.button_unselected_color = None
        self.button_selected_color = '#6bd688'

        self._instrument_type = {}

        self._cb_instrument_select = set()

        self._build_frame()

    def _build_frame(self):

        frame = tk.Frame(self)
        frame.grid(row=0, column=0, sticky='nw')
        tkw.grid_configure(self)

        layout = dict(padx=5, pady=5, sticky='nw')

        tk.Label(frame, text='Välj CTD:').grid(row=0, column=0, **layout)

        width = 10

        self.buttons['SBE09'] = tk.Button(frame, text='SBE09', width=width,
                                          command=lambda name='SBE09': self._on_select_instrument(name))
        self.buttons['SBE09'].grid(row=0, column=1, **layout)

        self.buttons['SBE19'] = tk.Button(frame, text='SBE19', width=width,
                                          command=lambda name='SBE19': self._on_select_instrument(name))
        self.buttons['SBE19'].grid(row=0, column=2, **layout)

        tk.Label(frame, text='(Stationära CTD-kast)').grid(row=0, column=3, **layout)

        self.buttons['MVP200'] = tk.Button(frame, text='MVP200', width=width,
                                           command=lambda name='MVP200': self._on_select_instrument(name))
        self.buttons['MVP200'].grid(row=1, column=1, **layout)

        self.buttons['Triaxus'] = tk.Button(frame, text='Triaxus', width=width,
                                            command=lambda name='Triaxus': self._on_select_instrument(name))
        self.buttons['Triaxus'].grid(row=1, column=2, **layout)
        self.buttons['Triaxus'].config(state='disabled')

        self.button_unselected_color = self.buttons['SBE09'].cget('bg')

        tk.Label(frame, text='(CTD-transekt)').grid(row=1, column=3, **layout)

        tkw.grid_configure(frame, nr_rows=2, nr_columns=4)

    def _deselect(self):
        for name, wid in self.buttons.items():
            wid.configure(bg=self.button_unselected_color)
        self._selected = None

    def _select(self, name, callback=True):
        if not self.buttons.get(name):
            return
        self.buttons[name].configure(bg=self.button_selected_color)
        self._selected = name

        if callback:
            for func in self._cb_instrument_select:
                func(self._selected)

    def _on_select_instrument(self, button_name):
        self._deselect()
        self._select(button_name)

    @property
    def instrument(self):
        return self._selected

    @instrument.setter
    def instrument(self, name):
        if not self.buttons.get(name):
            return
        self._deselect()
        self._select(name, callback=False)

    def add_callback_instrument_select(self, func):
        self._cb_instrument_select.add(func)


class FrameStartUp(ColoredFrame, SaveSelection):

        def __init__(self, parent):
            super().__init__(parent)

            self.__instrument = ''

            self._build_frame()

        def _build_frame(self):
            frame = tk.Frame(self)
            frame.grid(row=0, column=0, sticky='nw')
            tkw.grid_configure(self)

            layout = dict(padx=5, pady=5, sticky='nwse')

            self._sensor_table = components.SensorTable(self, row=0, column=0, **layout)
            self._sensor_table.set_frame_color('blue')

            self._selections_to_store = ['_sensor_table']

            tkw.grid_configure(frame, nr_rows=2)

        def _update_frame(self):
            pass

        def update_sbe_instrument_info(self, instrument_info):
            self._sensor_table.update_data(instrument_info)
            self.load_selection()

        @property
        def instrument(self):
            return self.__instrument

        @instrument.setter
        def instrument(self, name):
            self.__instrument = name
            self._sensor_table.instrument = self.__instrument


class FrameManageCTDcastsStation(ColoredFrame):

    def __init__(self, parent):
        super().__init__(parent)

        self.__instrument = ''

        self._build_frame()

    def _build_frame(self):

        frame = tk.Frame(self)
        frame.grid(row=0, column=0, sticky='nw')
        tkw.grid_configure(self)

        layout = dict(padx=5, pady=5, sticky='nwse')

        self.instrument_text_frame = components.SelectedInstrumentTextFrame(frame, row=0, column=0, **layout)

        self.content_frame = StationPreSystemFrame(frame, row=1, column=0, **layout)

        tkw.grid_configure(frame, nr_rows=2)

    def _update_frame(self):
        self.instrument_text_frame.instrument = self.__instrument

    def save_selection(self):
        self.content_frame.save_selection()

    @property
    def instrument(self):
        return self.__instrument

    @instrument.setter
    def instrument(self, name):
        self.__instrument = name
        self._update_frame()


class FrameManageCTDcastsTransect(ColoredFrame):

    def __init__(self, parent):
        super().__init__(parent)

        self.__instrument = ''

        self._build_frame()

    def _build_frame(self):

        frame = tk.Frame(self)
        frame.grid(row=0, column=0, sticky='nw')
        tkw.grid_configure(self)

        layout = dict(padx=5, pady=5, sticky='nwse')

        self.instrument_text_frame = components.SelectedInstrumentTextFrame(frame, row=0, column=0, **layout)

        self.content_frame = TransectPreSystemFrame(frame, row=1, column=0, **layout)

        tkw.grid_configure(frame, nr_rows=2)

    def _update_frame(self):
        self.instrument_text_frame.instrument = self.__instrument

    def save_selection(self):
        self.content_frame.save_selection()

    @property
    def instrument(self):
        return self.__instrument

    @instrument.setter
    def instrument(self, name):
        self.__instrument = name
        self._update_frame()


def get_transect_list():
    """
    :return: list of strings
    """
    return ['BY15 <-> BY32',
            'BY32 <-> BY39']


def get_depth_list():
    """
    :param station_name: string
    :return: list of strings
    """
    return ['0', '5', '10', '15', '20']


def get_nr_of_ticks_list():
    """
    :return: list of strings
    """
    return [str(nr) for nr in range(20)]




