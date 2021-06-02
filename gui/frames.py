import threading
import time
import tkinter as tk
import traceback
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

from sharkpylib.tklib import tkinter_widgets as tkw

from . import components
from ..saves import SaveSelection

# from pre_system_svea.operator import Operators
# from pre_system_svea.station import Stations

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

    def get_operator_list(self):
        """
        :return: list of strings
        """
        return self.controller.get_operator_list()

    def get_station_list(self):
        """
        :return: list of strings
        """
        return self.controller.get_station_list()


class StationPreSystemFrame(tk.Frame, SaveSelection, CommonFrameMethods):

    def __init__(self,
                 parent,
                 controller=None,
                 **kwargs):
        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        super().__init__(parent)

        self.controller = controller
        self.instrument = None

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

        frame_left = tk.Frame(frame)
        frame_left.grid(row=0, column=0)

        ttk.Separator(frame, orient='vertical').grid(row=0, column=1, sticky='ns')

        frame_right = tk.Frame(frame)
        frame_right.grid(row=0, column=2)

        ttk.Separator(frame, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky='ew')

        frame_bottom = tk.Frame(frame)
        frame_bottom.grid(row=2, column=0, columnspan=3)

        tkw.grid_configure(frame, nr_columns=3, nr_rows=2)

        self._cruise = components.CruiseLabelDoubleEntry(frame_left, title='Cruise'.ljust(TEXT_LJUST), row=0, column=0, **layout)
        self._series = components.SeriesEntryPicker(frame_left, title='Series'.ljust(TEXT_LJUST), row=1, column=0, **layout)
        self._station = components.LabelDropdownList(frame_left, title='Station'.ljust(TEXT_LJUST), width=25, autocomplete=True, row=2, column=0, **layout)
        self._distance = components.LabelEntry(frame_left, title='Distance to station (m)'.ljust(TEXT_LJUST), state='disabled', data_type=int, row=3, column=0, **layout)
        self._depth = components.DepthEntry(frame_left, title='Plot depth'.ljust(TEXT_LJUST), data_type=float, row=4, column=0, **layout)
        self._bin_size = components.LabelEntry(frame_left, title='Plot bin size'.ljust(TEXT_LJUST), data_type=int, row=5, column=0, **layout)

        self._vessel = components.VesselLabelDoubleEntry(frame_right, title='Vessel'.ljust(TEXT_LJUST), row=0, column=0, **layout)
        self._operator = components.LabelDropdownList(frame_right, title='Operator'.ljust(TEXT_LJUST), row=1, column=0, **layout)
        self._position = components.PositionEntries(frame_right, row=2, column=0, **layout)

        self._svepa = components.CallbackButton(frame_bottom, title='Load SVEPA', row=0, column=0, **layout)
        self._validate = components.CallbackButton(frame_bottom, title='Validate', row=0, column=1, **layout)
        self._validate.button.config(state='disabled')
        self._seasave = components.CallbackButton(frame_bottom, title='Run Seasave', row=0, column=2, **layout)
        self._seasave.button.config(bg='#6691bd')

        tkw.grid_configure(frame_left, nr_rows=6)
        tkw.grid_configure(frame_right, nr_rows=4)
        tkw.grid_configure(frame_bottom, nr_columns=3)

        # Adding callbacks
        self._series.add_callback(self._on_select_series)
        self._station.add_callback_select(self._on_select_station)
        self._depth.add_callback(self._on_select_depth)
        self._bin_size.add_callback(self._on_select_bin_size)
        self._svepa.add_callback(self._load_svepa)
        self._position.add_callback(self._on_select_lat_lon)
        self._validate.add_callback(self._validate_all)
        self._seasave.add_callback(self._run_seasave)

        # Store selection
        self._selections_to_store = ['_cruise', '_series', '_operator',
                                     '_vessel', '_bin_size']

    def _initiate_frame(self):
        self._station.values = self.get_station_list()
        self._operator.values = self.get_operator_list()

    def _on_select_series(self, *arg):
        pass

    def _on_select_station(self, *args, **kwargs):
        station_name = self._station.value
        station_info = self.controller.get_station_info(station_name)
        if not station_info:
            self._depth.water_depth = ''
            self._distance.value = ''
            return
        self._station.value = station_info.get('station')
        self._depth.water_depth = str(station_info.get('depth'))
        self._position.lat = station_info.get('lat', '')
        self._position.lon = station_info.get('lon', '')
        self._on_select_depth()
        self._position.source = 'Nominal'
        self.save_selection()

    def _on_select_lat_lon(self, *args):
        lat, lon = self._position.get()
        print('lon:', lon)
        print('lat:', lat)
        if not all([lat, lon]):
            return
        # Check position against station list
        station_info = self.controller.get_closest_station(float(lat), float(lon))
        print('station_info:', station_info)
        if not station_info:
            self._station.value = ''
            self._distance.value = ''
            return
        if station_info['acceptable']:
            self._station.value = station_info.get('station', '')
            self._depth.water_depth = station_info.get('depth', '')
            self._distance.value = station_info.get('distance', '')
        else:
            self._station.value = ''
            self._depth.water_depth = ''
            self._distance.value = station_info.get('distance', '')

        self._position.source = 'Manual'

    def _on_select_depth(self, *args):
        # Set bin size
        plot_depth = self._depth.value
        if not plot_depth:
            return
        plot_depth = int(plot_depth)
        if not plot_depth % 25:
            self._bin_size.value = 25
        elif not plot_depth % 10:
            self._bin_size.value = 10
        else:
            self._bin_size.value = 5

    def _on_select_bin_size(self, *args):
        print('_on_select_bin_size')
        nr_bins = self.get_nr_bins()
        print(nr_bins)
        if nr_bins == int(nr_bins):
            return

        water_depth = float(self._depth.value)
        step = self._depth.step

        sum_depth = 0
        while sum_depth < water_depth:
            print(sum_depth)
            sum_depth += step
        self._depth.value = sum_depth

    def get_nr_bins(self):
        bin_size = self._bin_size.value
        plot_depth = self._depth.value
        if not all([bin_size, plot_depth]):
            return None
        return float(plot_depth) / int(bin_size)

    def _validate_all(self):
        """
        Validates if station and depth has matching information.
        :return:
        """
        pass

    def _modify_seasave_file(self):
        depth = self._depth.value
        bin_size = self._bin_size.value
        cruise_nr = self._cruise.nr
        ship_code = self._vessel.code
        serno = self._series.value
        station = self._station.value
        operator = self._operator.value
        lat = self._position.lat
        lon = self._position.lon
        pos_source = self._position.source

        if not all([depth, bin_size, cruise_nr, ship_code, serno, lat, lon, station, operator]):
            raise ValueError('Missing information')

        nr_bins = int(float(depth) / float(bin_size))

        # Update
        self.controller.update_main_psa_file(instrument=self.instrument,
                                             depth=depth,
                                             nr_bins=nr_bins,
                                             cruise_nr=cruise_nr,
                                             ship_code=ship_code,
                                             serno=serno,
                                             station=station,
                                             operator=operator,
                                             position=[lat, lon, pos_source])

    def _run_seasave(self):
        try:
            self._modify_seasave_file()
            self.controller.run_seasave()
            self._time_disabled_widget(self._seasave.button, 20)
            # self._seasave.set_state('disabled')
        except ValueError:
            messagebox.showerror('Run seasave', f'Kan inte köra Seasave.\nInformation saknas')
        except ChildProcessError:
            messagebox.showerror('Run seasave', 'Det körs redan en instans av Seasave!')
        except:
            messagebox.showerror('Run seasave', f'Något gick fel!\n{traceback.format_exc()}')

    def _time_disabled_widget(self, widget, seconds):
        def sub_func():
            widget.config(state='disabled')
            time.sleep(seconds)
            widget.config(state='normal')

        t = threading.Thread(target=sub_func)
        t.daemon = True  # close pipe if GUI process exits
        t.start()

    def _is_validate_station_name(self):
        """
        Check if the station name is valid
        :return:
        """
        station_name = self._station.value
        station_info = self.controller.get_station_info(station_name)
        if not station_info:
            return False

    def _load_svepa(self):
        print('Loading SVEPA information')
        # self._position.source = 'Svepa'


class TransectPreSystemFrame(tk.Frame, SaveSelection, CommonFrameMethods):

    def __init__(self,
                 parent,
                 controller,
                 **kwargs):
        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        super().__init__(parent)

        self.grid(**self.grid_frame)

        self._saves_id_key = 'TransectPreSystemFrame'
        self._selections_to_store = []

        self.controller = controller
        self.instrument = None

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

        self._vessel = components.VesselLabelDoubleEntry(frame, title='Vessel'.ljust(TEXT_LJUST), row=0, column=1, **layout)
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


class ProcessingFrame(tk.Frame, SaveSelection):

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
        self._selections_to_store = ['_sensor_table']


class FrameSelectInstrument(tk.Frame):

    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller

        self._cb = set()

        self._build_frame()

    def _build_frame(self):
        layout = dict(padx=5, pady=5, sticky='nsew')

        self._frame_instrument_buttons = FrameInstrumentButtons(self, self.controller)
        self._frame_instrument_buttons.grid(row=0, column=0, **layout)
        self._frame_instrument_buttons.add_callback(self._on_select_instrument)

        self._sensor_table = components.SensorTable(self, self.controller, row=0, column=1, **layout)

        ttk.Separator(self, orient='horizontal').grid(row=1, column=0, columnspan=2, sticky='ew')

        self._frame_info = SelectionInfoFrame(self, self.controller)
        self._frame_info.grid(row=2, column=0, columnspan=2, sticky='nsew')
        self._frame_info.add_callback_config(self._on_change_config_path)
        self._frame_info.add_callback_data(self._on_change_data_path)

        tk.Button(self, text='Jag har kontrollerat sensoruppsättningen!', bg='#6691bd',
                  command=self._on_confirm).grid(row=3, column=0, columnspan=2, sticky='e')

        tkw.grid_configure(self, nr_rows=4, nr_columns=3)

    def _on_confirm(self):
        for func in self._cb:
            func()

    def _on_change_config_path(self, ok):
        if not ok:
            self._frame_instrument_buttons.deselect()
            return

    def _on_change_data_path(self, ok):
        if not ok:
            self._frame_instrument_buttons.deselect()
            return

    def _on_select_instrument(self):

        if not self.instrument:
            self._frame_info.reset_info()
            self._sensor_table.reset_data()
            return

        if not all([self._frame_info.config_root_path, self._frame_info.data_root_path]):
            self._frame_info.reset_info()
            self._sensor_table.reset_data()
            self._frame_instrument_buttons.deselect()
            messagebox.showwarning('Rotkatalog saknas!', 'Du måste ange rotkatalog för config och data')
            return

        self._frame_info.update_info(self.instrument)
        instrument_info = self.controller.get_sensor_info_in_xmlcon(self.instrument)
        self._sensor_table.update_data(instrument_info)

    @property
    def config_root_directory(self):
        return self._frame_info.config_root_path

    @property
    def data_root_directory(self):
        return self._frame_info.data_root_path

    def add_callback(self, func):
        self._cb.add(func)

    @property
    def instrument(self):
        return self._frame_instrument_buttons.instrument

    @instrument.setter
    def instrument(self, name):
        self._frame_instrument_buttons.instrument = name


class SelectionInfoFrame(tk.Frame, SaveSelection):

    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller

        self.latest_instrument = None

        self._selections_to_store = ['_stringvar_config_root_path', '_stringvar_data_root_path']

        self._cb_config = set()
        self._cb_data = set()

        self._build_frame()

        self.load_selection()

    def _build_frame(self):
        layout = dict(padx=3,
                      pady=3)

        self._stringvar_config_root_path = tk.StringVar()
        self._stringvar_data_root_path = tk.StringVar()
        self._stringvar_ctd = tk.StringVar()
        self._stringvar_xmlcon = tk.StringVar()
        self._stringvar_seasave_psa = tk.StringVar()

        root_config = tk.Label(self, text='Rotkatalog för configfiler:')
        root_config.grid(row=0, column=0, sticky='w', **layout)
        root_config.bind('<Control-Button-3>', self._on_click_root_config)
        tk.Label(self, textvariable=self._stringvar_config_root_path).grid(row=0, column=1, sticky='w', **layout)

        root_data = tk.Label(self, text='Rotkatalog för data:')
        root_data.grid(row=1, column=0, sticky='w', **layout)
        root_data.bind('<Control-Button-3>', self._on_click_root_data)
        tk.Label(self, textvariable=self._stringvar_data_root_path).grid(row=1, column=1, sticky='w', **layout)

        ttk.Separator(self, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky='ew')

        tk.Label(self, text='Vald CTD:').grid(row=3, column=0, sticky='w', **layout)
        tk.Label(self, textvariable=self._stringvar_ctd).grid(row=3, column=1, sticky='w', **layout)

        ttk.Separator(self, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky='ew')

        tk.Label(self, text='Sökväg XMLCON:').grid(row=5, column=0, sticky='w', **layout)
        tk.Label(self, textvariable=self._stringvar_xmlcon).grid(row=5, column=1, sticky='w', **layout)

        tk.Label(self, text='Sökväg seasave.psa:').grid(row=6, column=0, sticky='w', **layout)
        tk.Label(self, textvariable=self._stringvar_seasave_psa).grid(row=6, column=1, sticky='w', **layout)

        ttk.Separator(self, orient='horizontal').grid(row=8, column=0, columnspan=2, sticky='ew')

        tkw.grid_configure(self, nr_columns=2, nr_rows=8)

    def add_callback_config(self, func):
        self._cb_config.add(func)

    def add_callback_data(self, func):
        self._cb_data.add(func)

    def _on_click_root_config(self, event=None):
        directory = filedialog.askdirectory()
        if not directory:
            return
        ok = self._check_config_root_directory()
        if ok:
            self._stringvar_config_root_path.set(directory)
            self.controller.ctd_config_root_directory = directory
            self.save_selection()
            self.update_info()
        else:
            self.reset_info()
        for func in self._cb_config:
            func(ok)

    def _on_click_root_data(self, event=None):
        directory = filedialog.askdirectory()
        if not directory:
            return
        ok = self._check_data_root_directory()
        if ok:
            self._stringvar_data_root_path.set(directory)
            self.controller.ctd_data_root_directory = directory
            self.save_selection()
            self.update_info()
        else:
            self.reset_info()

        for func in self._cb_data:
            func(ok)

    def reset_info(self):
        self._stringvar_ctd.set('')
        self._stringvar_xmlcon.set('')
        self._stringvar_seasave_psa.set('')

    def update_info(self, instrument=None):
        if instrument:
            self.latest_instrument = instrument
        self.reset_info()
        if not self.latest_instrument:
            return
        nr = self.controller.get_instrument_serial_number(self.latest_instrument)
        ctd_str = f'{self.latest_instrument} ({nr})'

        self._stringvar_ctd.set(ctd_str)
        self._stringvar_xmlcon.set(self.controller.get_xmlcon_path(self.latest_instrument))
        self._stringvar_seasave_psa.set(self.controller.get_seasave_psa_path())

    def _check_config_root_directory(self):
        try:
            self.controller.ctd_config_root_directory = self.config_root_path
        except:
            messagebox.showerror('Val av instrument',
                                 f'Rotkatalogens struktur för configfiler verkar inte stämma: '
                                 f'\n{traceback.format_exc()}')
            return False
        return True

    def _check_data_root_directory(self):
        try:
            self.controller.ctd_data_root_directory = self.data_root_path
        except:
            messagebox.showerror('Val av instrument',
                                 f'Något gick fel när rotkatalogen för data skulle sättas: '
                                 f'\n{traceback.format_exc()}')
            return False
        return True

    @property
    def config_root_path(self):
        return self._stringvar_config_root_path.get()

    @config_root_path.setter
    def config_root_path(self, path):
        self._stringvar_config_root_path.set(str(path))

    @property
    def data_root_path(self):
        return self._stringvar_data_root_path.get()

    @data_root_path.setter
    def data_root_path(self, path):
        self._stringvar_data_root_path.set(str(path))


class FrameInstrumentButtons(tk.Frame, SaveSelection):

    def __init__(self, parent, controller):
        super().__init__(parent)

        self.buttons = {}

        self._selected = None

        self.controller = controller

        self.button_unselected_color = None
        self.button_selected_color = '#6bd688'

        self._instrument_type = {}

        self._selections_to_store = ['directory_config', 'directory_data']

        self._cb = set()

        self._build_frame()

        self.load_selection()

    def _build_frame(self):

        frame = tk.Frame(self)
        frame.grid(row=0, column=0, sticky='nw')
        tkw.grid_configure(self)

        layout = dict(padx=5, pady=5, sticky='nw')

        tk.Label(frame, text='Välj CTD:').grid(row=0, column=0, **layout)

        width = 10

        self.buttons['SBE09'] = tk.Button(frame, text='SBE09', width=width,
                                          command=lambda name='SBE09': self._on_select_instrument(name))
        self.buttons['SBE09'].grid(row=1, column=0, **layout)

        self.buttons['SBE19'] = tk.Button(frame, text='SBE19', width=width,
                                          command=lambda name='SBE19': self._on_select_instrument(name))
        self.buttons['SBE19'].grid(row=2, column=0, **layout)

        # tk.Label(frame, text='(Stationära CTD-kast)').grid(row=0, column=3, **layout)

        self.buttons['MVP200'] = tk.Button(frame, text='MVP200', width=width,
                                           command=lambda name='MVP200': self._on_select_instrument(name))
        self.buttons['MVP200'].grid(row=3, column=0, **layout)
        self.buttons['MVP200'].config(state='disabled')

        self.buttons['Triaxus'] = tk.Button(frame, text='Triaxus', width=width,
                                            command=lambda name='Triaxus': self._on_select_instrument(name))
        self.buttons['Triaxus'].grid(row=4, column=0, **layout)
        self.buttons['Triaxus'].config(state='disabled')

        self.button_unselected_color = self.buttons['SBE09'].cget('bg')

        # tk.Label(frame, text='(CTD-transekt)').grid(row=1, column=3, **layout)

        tkw.grid_configure(frame, nr_rows=5, nr_columns=1)

    def deselect(self):
        for name, wid in self.buttons.items():
            wid.configure(bg=self.button_unselected_color)
        self._selected = None

    def _select(self, name):
        if not self.buttons.get(name):
            return
        self.buttons[name].configure(bg=self.button_selected_color)
        self._selected = name

    def _on_select_instrument(self, button_name):
        self.deselect()
        self._select(button_name)
        for func in self._cb:
            func()

    @property
    def instrument(self):
        return self._selected

    @instrument.setter
    def instrument(self, name):
        if not self.buttons.get(name):
            return
        self.deselect()
        self._select(name)

    def add_callback(self, func):
        self._cb.add(func)


class FrameStartUp(tk.Frame, SaveSelection):

        def __init__(self, parent, controller):
            super().__init__(parent)

            self.controller = controller

            self.__instrument = ''

            self._build_frame()

        def _build_frame(self):
            frame = tk.Frame(self)
            frame.grid(row=0, column=0, sticky='nw')
            tkw.grid_configure(self)

            layout = dict(padx=5, pady=5, sticky='nwse')

            self._sensor_table = components.SensorTableOld(self, row=0, column=0, **layout)
            # self._sensor_table.set_frame_color('blue')

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


class FrameManageCTDcastsStation(tk.Frame):

    def __init__(self, parent, controller):
        super().__init__(parent)

        self.__instrument = ''

        self.controller = controller

        self._build_frame()

    def _build_frame(self):

        frame = tk.Frame(self)
        frame.grid(row=0, column=0, sticky='nw')
        tkw.grid_configure(self)

        layout = dict(padx=5, pady=5, sticky='nwse')

        self.instrument_text_frame = components.SelectedInstrumentTextFrame(frame, self.controller, row=0, column=0, **layout)

        ttk.Separator(frame, orient='horizontal').grid(row=1, column=0, sticky='ew')

        self.content_frame = StationPreSystemFrame(frame, controller=self.controller, row=2, column=0, **layout)

        tkw.grid_configure(frame, nr_rows=3)

    def _update_frame(self):
        self.instrument_text_frame.instrument = self.__instrument
        self.content_frame.instrument = self.__instrument

    def save_selection(self):
        self.content_frame.save_selection()

    @property
    def instrument(self):
        return self.__instrument

    @instrument.setter
    def instrument(self, name):
        self.__instrument = name
        self._update_frame()


class FrameManageCTDcastsTransect(tk.Frame):

    def __init__(self, parent, controller):
        super().__init__(parent)

        self.__instrument = ''

        self.controller = controller

        self._build_frame()

    def _build_frame(self):

        frame = tk.Frame(self)
        frame.grid(row=0, column=0, sticky='nw')
        tkw.grid_configure(self)

        layout = dict(padx=5, pady=5, sticky='nwse')

        self.instrument_text_frame = components.SelectedInstrumentTextFrame(frame, self.controller, row=0, column=0, **layout)

        self.content_frame = TransectPreSystemFrame(frame, controller=self.controller, row=1, column=0, **layout)

        tkw.grid_configure(frame, nr_rows=2)

    def _update_frame(self):
        self.instrument_text_frame.instrument = self.__instrument
        self.content_frame.instrument = self.__instrument

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





