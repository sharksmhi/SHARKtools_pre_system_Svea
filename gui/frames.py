import datetime
import pathlib
import threading
import time
import tkinter as tk
import traceback
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

import psutil
from ctd_processing.options import get_options
from sharkpylib.tklib import tkinter_widgets as tkw
from svepa import exceptions as svepa_exceptions

from . import components
from .. import lists
from ..events import post_event
from ..events import print_subscribers
from ..events import subscribe
from ..gui.translator import Translator
from ..saves import Defaults
from ..saves import SaveSelection

TEXT_LJUST = 10

translator = Translator()

options = get_options()

SHIP_TO_INTERNAL = {'77SE': '7710'}


class MissingInformationError(Exception):
    def __init__(self, missing_list, message=''):
        self.missing_list = missing_list
        super().__init__(message)


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

        subscribe('confirm_sensors', self._set_instrument)
        subscribe('confirm_sensors', self._set_next_series)
        subscribe('focus_out_cruise', self._set_next_series)
        # subscribe('focus_out_series', self._on_focus_out_series)
        subscribe('select_station', self._on_select_station)
        subscribe('focus_out_station', self._on_select_station)
        subscribe('return_position', self._on_return_position)
        subscribe('focus_out_depth', self._on_focus_out_depth)

        subscribe('button_svepa', self._on_return_load_svepa)
        subscribe('button_seasave', self._on_return_seasave)

        subscribe('missing_input', self._missing_input)
        subscribe('input_ok', self._input_ok)
        subscribe('add_components', self._add_components)

    def save_selection(self):
        self._frame_metadata_admin.save_selection()
        self._frame_metadata_conditions.save_selection()
        super().save_selection()

    def _set_instrument(self, instrument):
        self.instrument = instrument

    def _add_components(self, components):
        print('components', components)
        self._components.update(components)

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

        ttk.Separator(frame, orient='vertical').grid(row=0, column=3, sticky='ns')

        self._frame_metadata_admin = MetadataAdminFrame(frame, self.controller, row=0, column=4, sticky='ns')

        ttk.Separator(frame, orient='vertical').grid(row=0, column=5, sticky='ns')

        self._frame_metadata_conditions = MetadataConditionsFrame(frame, self.controller, row=0, column=6, sticky='ns')

        frame_bottom = tk.Frame(frame)
        frame_bottom.grid(row=1, column=0, columnspan=7)

        tkw.grid_configure(frame, nr_columns=7, nr_rows=2)

        self._components = {}
        self._components['cruise'] = components.CruiseLabelDoubleEntry(frame_left, 'cruise', title=translator.get_readable('cruise').ljust(TEXT_LJUST), row=0, column=0, **layout)
        self._components['series'] = components.SeriesEntryPicker(frame_left, 'series', title=translator.get_readable('series'), row=1, column=0, **layout)
        self._components['tail'] = components.LabelCheckbox(frame_left, 'tail', title=translator.get_readable('tail'), row=2, column=0, **layout)
        self._components['station'] = components.LabelDropdownList(frame_left, 'station', title=translator.get_readable('station'), width=30, autocomplete=True, row=3, column=0, **layout)
        self._components['distance'] = components.LabelEntry(frame_left, 'distance',  title=translator.get_readable('distance').ljust(TEXT_LJUST), state='disabled', data_type=int, row=4, column=0, **layout)
        self._components['depth'] = components.DepthEntry(frame_left, 'depth', title=translator.get_readable('depth').ljust(TEXT_LJUST), data_type=int, row=5, column=0, **layout)
        self._components['bin_size'] = components.LabelEntry(frame_left, 'bin_size', title=translator.get_readable('bin_size').ljust(TEXT_LJUST), data_type=int, row=6, column=0, **layout)

        self._components['vessel'] = components.VesselLabelDoubleEntry(frame_right, 'vessel', title=translator.get_readable('vessel').ljust(TEXT_LJUST), row=0, column=0, **layout)
        self._components['operator'] = components.LabelDropdownList(frame_right, 'operator', title=translator.get_readable('operator').ljust(TEXT_LJUST), row=1, column=0, **layout)
        self._components['position'] = components.PositionEntries(frame_right, 'position', row=2, column=0, **layout)
        self._components['add_samp'] = components.AddSampInfo(frame_right, 'add_samp', row=3, column=0, **layout)
        self._components['event_id'] = components.LabelEntry(frame_right, 'event_id',  title=translator.get_readable('event_id').ljust(TEXT_LJUST), width=37, state='disabled', data_type=str, row=4, column=0, **layout)
        self._components['parent_event_id'] = components.LabelEntry(frame_right, 'parent_event_id',  title=translator.get_readable('parent_event_id').ljust(TEXT_LJUST), width=37, state='disabled', data_type=str, row=5, column=0, **layout)

        self._components['svepa'] = components.CallbackButton(frame_bottom, 'svepa', title='Ladda information från SVEPA', row=0, column=0, **layout)
        self._components['svepa'].button.config(state='disabled')
        self._components['validate'] = components.CallbackButton(frame_bottom, 'validate', title='Validera', row=0, column=1, **layout)
        self._components['validate'].button.config(state='disabled')
        self._components['seasave'] = components.CallbackButton(frame_bottom, 'seasave', title='Starta Seasave', row=0, column=2, **layout)
        self._components['seasave'].button.config(bg='#6691bd')

        tkw.grid_configure(frame_left, nr_rows=6)
        tkw.grid_configure(frame_right, nr_rows=4)
        tkw.grid_configure(frame_bottom, nr_columns=3)

        # Store selection
        to_store = ['cruise', 'operator', 'vessel', 'bin_size']
        self._selections_to_store = {key: comp for key, comp in self._components.items() if key in to_store}

    def _temp(self, dummy):
        print_subscribers()

    def _missing_input(self, missing):
        for key in missing:
            if key.lower() not in self._components:
                continue
            self._components[key.lower()].set_color('red')

    def _input_ok(self, *args):
        if not hasattr(self, '_components'):
            return
        for comp in self._components.values():
            comp.set_color()

    def _initiate_frame(self):
        self._components['station'].values = self.get_station_list()
        self._components['operator'].values = self.get_operator_list()

    def get_latest_file(self, server=False):
        kwargs = {'server': server,
                  'year': self._components['cruise'].year,
                  'ship': self._components['vessel'].code,
                  'cruise': self._components['cruise'].nr}
        print('frames.get_latest_file kwargs', kwargs)
        latest_series_path = self.controller.get_latest_series_path(**kwargs)
        return latest_series_path

    def get_current_file(self):
        tail = None
        if self._components['tail'].value:
            tail = 'test'
        kwargs = {'instrument': self.instrument,
                  'ship': self._components['vessel'].code,
                  'cruise': self._components['cruise'].nr,
                  'serno': self._components['series'].value,
                  'tail': tail}
        current_file_path = self.controller.get_data_file_path(**kwargs)
        return current_file_path

    def _set_next_series(self, *args):
        """
        Search for the last known series and sets the next one.
        :return:
        """
        cruise, year = self._components['cruise'].get()
        ship_name, ship_code = self._components['vessel'].get()
        next_serno = self.controller.get_next_serno(server=True,
                                                    cruise=cruise,
                                                    year=year,
                                                    ship=ship_code)
        self._components['series'].set(next_serno)
        post_event('set_next_series', next_serno)

    def _on_focus_out_series(self, serno):
        cruise, year = self._components['cruise'].get()
        ship_name, ship_code = self._components['vessel'].get()
        series = self.controller.series_exists(server=True,
                                                cruise=cruise,
                                                year=year,
                                                ship=ship_code,
                                                serno=serno,
                                                return_file_name=True)

        if series:
            messagebox.showwarning(f'Series already exists', f'{series}')

    def _on_select_station(self, station_name, *args, **kwargs):
        # station_name = self._components['station'].value
        station_info = self.controller.get_station_info(station_name)
        if not station_info:
            self._components['depth'].water_depth = ''
            self._components['distance'].value = ''
            return
        self._components['station'].value = station_info.get('station') # Could have been a synonym
        self._components['position'].lat = station_info.get('lat', '')
        self._components['position'].lon = station_info.get('lon', '')
        self._components['depth'].water_depth = str(station_info.get('depth'))
        self._components['position'].source = 'Nominal'
        self._components['distance'].value = 0
        self._components['event_id'].value = ''
        self._components['parent_event_id'].value = ''
        self._components['add_samp'].value = None
        self._on_focus_out_depth()
        self.save_selection()

    def _on_return_position(self, position, *args):
        lat, lon = position
        if not all([lat, lon]):
            return False
        # Check position against station list
        station_info = self.controller.get_closest_station(float(lat), float(lon))
        if not station_info:
            self._components['station'].value = ''
            self._components['distance'].value = ''
            return False
        if station_info['acceptable']:
            ok = messagebox.askyesno('Station hittad', f'Positionen ({lat}, {lon}) matchar station: {station_info.get("station", "<No name>")}\n'
                                                       f'Avståndet till stationen är: {station_info.get("distance", "Oklart")} meter.')
            self._components['station'].value = station_info.get('station', '')
            self._components['depth'].water_depth = station_info.get('depth', '')
            self._components['distance'].value = station_info.get('distance', '')
        else:
            ok = messagebox.askyesno(f'Ingen station matchar positionen',
                                     f'Position: ({lat}, {lon})\n'
                                     f'Närmaste station är {station_info.get("station", "<No name>")}\n'
                                     f'Avståndet till stationen är: {station_info.get("distance", "Oklart")} meter.\n'
                                     f'Är detta en ny station?')
            if ok:
                self._components['station'].value = ''
                self._components['depth'].water_depth = ''
                self._components['distance'].value = station_info.get('distance', '')
            else:
                self._components['station'].value = ''
                self._components['depth'].water_depth = ''
                self._components['distance'].value = ''

        self._components['position'].source = 'Manual'
        return True

    def _on_focus_out_depth(self, *args):
        # Set bin size
        plot_depth = self._components['depth'].value
        if not plot_depth:
            return
        plot_depth = int(plot_depth)
        if plot_depth > 100 and not plot_depth % 25:
            self._components['bin_size'].value = 25
        elif plot_depth != 10 and not plot_depth % 10:
            self._components['bin_size'].value = 10
        else:
            self._components['bin_size'].value = 5

    def _on_select_bin_size(self, *args):
        nr_bins = self.get_nr_bins()
        if nr_bins == int(nr_bins):
            return

        water_depth = float(self._components['depth'].value)
        step = self._components['depth'].step

        sum_depth = 0
        while sum_depth < water_depth:
            sum_depth += step
        self._components['depth'].value = sum_depth

    def get_nr_bins(self):
        bin_size = self._components['bin_size'].value
        plot_depth = self._components['depth'].value
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
        data = {}
        for key, comp in self._components.items():
            if key == 'cruise':
                data['cruise_nr'] = self._components[key].nr
                data['year'] = self._components[key].year
                data['cruise'] = self._components[key].nr
            elif key == 'vessel':
                data['ship_code'] = self._components[key].code
                data['vessel'] = self._components[key].code
            elif key == 'series':
                data['serno'] = self._components[key].value
                data['series'] = self._components[key].value
            elif key == 'position':
                data['lat'] = self._components[key].lat
                data['lon'] = self._components[key].lon
                data['pos_source'] = self._components[key].source
                data['position'] = data['lat'] and data['lon']
            elif key == 'add_samp':
                data['add_samp'] = ', '.join(self._components[key].value)
            elif hasattr(self._components[key], 'value'):
                data[key] = self._components[key].value

        data['pumps'] = dict(PrimaryPump=self._components['pump1'].value,
                             SecondaryPump=self._components['pump2'].value)

        data['event_ids'] = dict(EventID=self._components['event_id'].value,
                                 ParentEventID=self._components['parent_event_id'].value)

        metadata_admin = self._frame_metadata_admin.get_data()
        metadata_conditions = self._frame_metadata_conditions.get_data()

        missing = []
        for key in ['depth', 'bin_size', 'cruise', 'vessel', 'series', 'station', 'operator']:
            if not data.get(key):
                missing.append(key)

        missing.extend([key for key, value in metadata_admin.items() if not value])
        missing.extend([key for key, value in metadata_conditions.items() if not value and key not in ['comment', 'comnt_visit']])

        post_event('input_ok', missing)
        if missing:
            post_event('missing_input', missing)
            raise MissingInformationError(missing_list=[translator.get_readable(item) for item in missing])

        data['nr_bins'] = int(float(data['depth']) / float(data['bin_size']))
        data['instrument'] = self.instrument
        data['position'] = ['', '', '']  # We dont set position

        internal_ship_code = SHIP_TO_INTERNAL.get(data['ship_code'], data['ship_code'])
        data['lims_job'] = f"{data['year']}{internal_ship_code}-{data['serno']}"

        if data.get('tail'):
            data['tail'] = 'test'

        # Update
        meta_admin = {key.upper(): value for key, value in metadata_admin.items()}
        meta_cond = {key.upper(): value for key, value in metadata_conditions.items()}
        self.controller.update_main_psa_file(**data, metadata_admin=meta_admin, metadata_conditions=meta_cond)

    def _on_return_seasave(self, *args):
        if self._components['tail'].value:
            ans = messagebox.askyesno('Skapar testfil', 'Vill du skapa en testfil?')
            if not ans:
                return
        self._run_seasave()

    def _run_seasave(self):
        try:
            self._modify_seasave_file()
            self.controller.run_seasave()
            self._time_disabled_widget(self._components['seasave'].button,
                                       program_running='Seasave.exe',
                                       )
        except MissingInformationError as e:
            missing_string = '\n'.join(e.missing_list)
            messagebox.showerror('Run seasave', f'Kan inte köra Seasave!\nFöljande information saknas:\n\n{missing_string}')
            return
        except ChildProcessError:
            messagebox.showerror('Run seasave', 'Det körs redan en instans av Seasave!')
        except Exception as e:
            messagebox.showerror('Run seasave', f'Något gick fel!\n{e}\n\n{traceback.format_exc()}')
            raise

    def _program_is_running(self, program):
        for p in psutil.process_iter():
            if p.name() == program:
                return True
        return False

    def _time_disabled_widget(self, widget, seconds=None, program_running='', then_run=None):
        def sub_func():
            widget.config(state='disabled')
            if seconds:
                time.sleep(seconds)
                widget.config(state='normal')
            elif program_running:
                time.sleep(2)
                running = self._program_is_running(program_running)
                while running:
                    time.sleep(1)
                    running = self._program_is_running(program_running)
                if then_run:
                    then_run()
                widget.config(state='normal')

        t = threading.Thread(target=sub_func)
        t.daemon = True  # close pipe if GUI process exits
        t.start()

    def _is_validate_station_name(self):
        """
        Check if the station name is valid
        :return:
        """
        station_name = self._components['station'].value
        station_info = self.controller.get_station_info(station_name)
        if not station_info:
            return False

    def _on_return_load_svepa(self, *args):
        print('Loading SVEPA information')
        try:
            data = self.controller.get_svepa_info()
            if not data.get('ctd_station_started'):
                messagebox.showwarning('Loading information from Svepa', 'No CTD event is running on Svepa!')

            self._components['series'].value = data.get('serno')
            self._components['station'].value = data.get('station', '')
            self._components['cruise'].nr = data.get('cruise')

            lat = str(data.get('lat'))
            lon = str(data.get('lon'))
            ok = self._on_return_position([lat, lon])
            if ok:
                self._components['position'].lat = lat
                self._components['position'].lon = lon
                self._components['position'].source = 'Svepa'

            self._set_event_id(data)
            self._set_parent_event_id(data)

            post_event('load_svepa', data)

        except svepa_exceptions.SvepaConnectionError as e:
            messagebox.showerror('Load information from Svepa', 'Could not connect to Svepa database!')
        except svepa_exceptions.SvepaEventTypeNotRunningError as e:
            messagebox.showerror('Load information from Svepa', f'Event type {e.event_type} not running!')
        except svepa_exceptions.SvepaException as e:
            messagebox.showerror('Load information from Svepa', traceback.format_exc())

    def _set_event_id(self, data):
        self._components['event_id'].value = data.get('event_id', 'Ingen information från Svepa')

    def _set_parent_event_id(self, data):
        self._components['parent_event_id'].value = data.get('parent_event_id', 'Ingen information från Svepa')


class MetadataAdminFrame(tk.Frame, SaveSelection, CommonFrameMethods):

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

        self._saves_id_key = 'MetadataAdminFrame'
        self._selections_to_store = []

        subscribe('missing_input', self._missing_input)
        subscribe('input_ok', self._input_ok)
        subscribe('select_default_user', self._on_change_default_user)

        self._build_frame()

        self._initiate_frame()

        self.load_selection()

    def _build_frame(self):
        frame = tk.Frame(self)
        frame.grid(row=0, column=0, sticky='nw')
        tkw.grid_configure(self)

        layout = dict(padx=5, pady=2, sticky='nw')

        text_ljust = 30
        width = 15

        self._components = {}
        self._components['mprog'] = components.LabelDropdownList(frame, 'mprog', title=translator.get_readable('mprog').ljust(text_ljust), width=width, row=0, column=0, **layout)
        self._components['proj'] = components.LabelDropdownList(frame, 'proj', title=translator.get_readable('proj').ljust(text_ljust), width=width, row=1, column=0, **layout)
        self._components['orderer'] = components.LabelDropdownList(frame, 'orderer', title=translator.get_readable('orderer').ljust(text_ljust), width=width, row=2, column=0, **layout)
        self._components['slabo'] = components.LabelDropdownList(frame, 'slabo', title=translator.get_readable('slabo').ljust(text_ljust), width=width, row=3, column=0, **layout)
        self._components['alabo'] = components.LabelDropdownList(frame, 'alabo', title=translator.get_readable('alabo').ljust(text_ljust), width=width, row=4, column=0, **layout)
        self._components['refsk'] = components.LabelEntry(frame, 'refsk', title=translator.get_readable('refsk').ljust(text_ljust), state='disabled', width=24, row=5, column=0, **layout)

        tkw.grid_configure(frame, nr_rows=5)

        # Store selection
        to_store = ['mprog', 'proj', 'orderer', 'slabo', 'alabo', 'refsk']
        self._selections_to_store = {key: comp for key, comp in self._components.items() if key in to_store}

    def _initiate_frame(self):
        for key, comp in self._components.items():
            comp.values = options.get(key)

    def get_data(self):
        data = {key: comp.value for key, comp in self._components.items()}
        return data

    def _missing_input(self, missing):
        for key in missing:
            if key.lower() not in self._components:
                continue
            self._components[key.lower()].set_color('red')

    def _input_ok(self, *args):
        if not hasattr(self, '_components'):
            return
        for comp in self._components.values():
            comp.set_color()

    def _on_change_default_user(self, user):
        self.load_selection(default_user=user)


class MetadataConditionsFrame(tk.Frame, SaveSelection, CommonFrameMethods):

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

        self._saves_id_key = 'MetadataConditionsFrame'
        self._selections_to_store = []

        subscribe('missing_input', self._missing_input)
        subscribe('input_ok', self._input_ok)
        subscribe('select_default_user', self._on_change_default_user)

        self._build_frame()

        self._initiate_frame()

        self.load_selection()

    def _build_frame(self):
        frame = tk.Frame(self)
        frame.grid(row=0, column=0, sticky='nw')
        tkw.grid_configure(self)

        layout = dict(padx=5, pady=2, sticky='nw')

        text_ljust = 25

        self._components = {}
        self._components['wadep'] = components.IntEntry(frame, 'wadep', title=translator.get_readable('wadep').ljust(text_ljust), min_value=options.get('wadep').get('min'), max_value=options.get('wadep').get('max'), row=0, column=0, **layout)
        self._components['windir'] = components.LabelDropdownList(frame, 'windir', title=translator.get_readable('windir').ljust(text_ljust), row=1, column=0, **layout)
        self._components['winsp'] = components.FloatEntry(frame, 'winsp', title=translator.get_readable('winsp').ljust(text_ljust), min_value=options.get('winsp').get('min'), max_value=options.get('winsp').get('max'), row=2, column=0, **layout)
        self._components['airtemp'] = components.FloatEntry(frame, 'airtemp', title=translator.get_readable('airtemp').ljust(text_ljust), min_value=options.get('airtemp').get('min'), max_value=options.get('airtemp').get('max'), row=3, column=0, **layout)
        self._components['airpres'] = components.FloatEntry(frame, 'airpres', title=translator.get_readable('airpres').ljust(text_ljust), min_value=options.get('airpres').get('min'), max_value=options.get('airpres').get('max'), row=4, column=0, **layout)
        self._components['weath'] = components.LabelDropdownList(frame, 'weath', title=translator.get_readable('weath').ljust(text_ljust), row=5, column=0, **layout)
        self._components['cloud'] = components.LabelDropdownList(frame, 'cloud', title=translator.get_readable('cloud').ljust(text_ljust), row=6, column=0, **layout)
        self._components['waves'] = components.LabelDropdownList(frame, 'waves', title=translator.get_readable('waves').ljust(text_ljust), row=7, column=0, **layout)
        self._components['iceob'] = components.LabelDropdownList(frame, 'iceob', title=translator.get_readable('iceob').ljust(text_ljust), row=8, column=0, **layout)
        self._components['comnt_visit'] = components.LabelEntry(frame, 'comment', title=translator.get_readable('comment').ljust(5), width=30, row=9, column=0, **layout)

        self._components['winsp'].focus_next_widget = self._components['airtemp']
        self._components['airtemp'].focus_next_widget = self._components['airpres']

        tkw.grid_configure(frame, nr_rows=10)

        # Store selection
        to_store = ['windir', 'winsp', 'airtemp', 'airpres', 'weath', 'cloud', 'waves', 'iceob']
        self._selections_to_store = {key: comp for key, comp in self._components.items() if key in to_store}

    def _initiate_frame(self):
        self._components['windir'].values = [str(i).zfill(2) for i in range(37)] + ['99']

        for key in ['weath', 'cloud', 'waves', 'iceob']:
            self._components[key].values = options.get(key)

    def get_data(self):
        data = {key: comp.value for key, comp in self._components.items()}
        return data

    def _missing_input(self, missing):
        for key in missing:
            low_key = key.lower()
            if low_key not in self._components:
                continue
            if key == 'comment':
                continue
            self._components[low_key].set_color('red')

    def _input_ok(self, *args):
        for comp in self._components.values():
            comp.set_color()

    def _on_change_default_user(self, user):
        self.load_selection(default_user=user)


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

        self._components['cruise'] = components.CruiseLabelDoubleEntry(frame, title='Cruise'.ljust(TEXT_LJUST), row=0, column=0, **layout)
        self._components['series'] = components.SeriesEntryPicker(frame, title='Series'.ljust(TEXT_LJUST), row=1, column=0, **layout)
        self._transect = components.LabelDropdownList(frame, 'transect',  title='Transect'.ljust(TEXT_LJUST), width=15, row=2, column=0, **layout)
        self._components['operator'] = components.LabelDropdownList(frame, 'operator', title='Operator'.ljust(TEXT_LJUST), row=4, column=0, **layout)

        self._components['vessel'] = components.VesselLabelDoubleEntry(frame, title='Vessel'.ljust(TEXT_LJUST), row=0, column=1, **layout)
        self._new_transect = components.LabelCheckbox(frame, title='New transect'.ljust(TEXT_LJUST), row=1, column=1, **layout)

        tkw.grid_configure(frame, nr_rows=5, nr_columns=2)

        # Adding callbacks
        # self._transect.add_callback_select(self._on_select_transect)

        # Store selection
        self._selections_to_store = ['_cruise', '_series', '_transect', '_operator',
                                     '_vessel', '_new_transect']

    def _initiate_frame(self):
        self._transect.values = get_transect_list()
        self._components['operator'].values = self.get_operator_list()

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


class FrameSelectInstrument(tk.Frame, SaveSelection):

    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller

        self._saves_id_key = 'FrameSelectInstrument'

        self._build_frame()
        self._add_subscribers()
        self.load_selection()

    def _add_subscribers(self):
        subscribe('select_instrument', self._on_select_instrument)
        subscribe('change_config_path', self._on_change_config_path)
        subscribe('change_data_path_local', self._on_change_data_path)
        subscribe('change_data_path_server', self._on_change_data_path)

    def _build_frame(self):
        layout = dict(padx=5, pady=5, sticky='nsew')

        self._frame_instrument_buttons = FrameInstrumentButtons(self, self.controller)
        self._frame_instrument_buttons.grid(row=0, column=0, **layout)

        self._sensor_table = components.SensorTable(self, self.controller, row=0, column=1, **layout)

        pump_frame = tk.Frame(self)
        pump_frame.grid(row=0, column=2, sticky='nw')
        self._pump_1 = components.LabelDropdownList(pump_frame, 'pump1',  title='Primär pump SBE5'.ljust(20), row=0, column=0, **layout)
        self._pump_2 = components.LabelDropdownList(pump_frame, 'pump2',  title='Sekundär pump SBE5'.ljust(20), row=1, column=0, **layout)
        self._pump_1.values = lists.get_pump_list()
        self._pump_2.values = lists.get_pump_list()
        tkw.grid_configure(pump_frame, nr_rows=2)

        ttk.Separator(self, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky='ew')

        self._frame_info = SelectionInfoFrame(self, self.controller)
        self._frame_info.grid(row=2, column=0, columnspan=3, sticky='nsew')

        option_frame = tk.Frame(self)
        option_frame.grid(row=3, column=0, columnspan=2, sticky='e')
        self.confirm_button = tk.Button(option_frame, text='Jag har kontrollerat sensoruppsättningen!', bg='#6691bd',
                                        command=self._on_confirm_sensors)
        self.confirm_button.grid(row=0, column=0, sticky='e')
        self.confirm_button.configure(state='disabled')

        # self.save_instruments_button = tk.Button(option_frame, text='Spara', command=self._save_instrument_set)
        # self.save_instruments_button.grid(row=0, column=1, sticky='e')
        #
        # self.save_instruments_button = tk.Button(option_frame, text='Spara och skriv ut', command=self._save_and_print_instrument_set)
        # self.save_instruments_button.grid(row=0, column=2, sticky='e')

        tkw.grid_configure(self, nr_rows=4, nr_columns=3)

        self._selections_to_store = ['_pump_1', '_pump_2']

    def _get_save_instrument_set_path(self):
        from pathlib import Path
        directory = Path(Path(__file__).parent.parent.parent.parent, 'export')
        directory.mkdir(parents=True, exist_ok=True)
        return Path(directory, 'instrument_set.txt')

    def _save_instrument_set(self):
        path = self._get_save_instrument_set_path()

    def _save_and_print_instrument_set(self):
        pass

    def _on_confirm_sensors(self, *args):
        # Check that pumps are not the same. Then post event.
        if not (self._pump_1.value and self._pump_2.value):
            messagebox.showerror('Kontrollera pump-id', 'Information om pump/pumpar saknas')
            return
        if self._pump_1.value == self._pump_2.value:
            messagebox.showerror('Kontrollera pump-id', 'Primär och sekundär pump kan inte vara samma')
            return
        post_event('confirm_sensors', self.instrument)
        post_event('add_components', dict(pump1=self._pump_1,
                                          pump2=self._pump_2))

    def _on_change_config_path(self, ok):
        if not ok:
            self._frame_instrument_buttons.deselect()
            return

    def _on_change_data_path(self, ok):
        if not ok:
            self._frame_instrument_buttons.deselect()
            return

    def _on_select_instrument(self, *args):
        if not self.instrument:
            self._frame_info.reset_info()
            self._sensor_table.reset_data()
            return

        if not all([self._frame_info.config_root_path, self._frame_info.data_root_path_local, self._frame_info.data_root_path_server]):
            self._frame_info.reset_info()
            self._sensor_table.reset_data()
            self._frame_instrument_buttons.deselect()
            messagebox.showwarning('Rotkatalog saknas!', 'Du måste ange rotkatalog för config och data')
            return
        try:
            self._frame_info.update_info(self.instrument)
            instrument_info = self.controller.get_sensor_info_in_xmlcon(self.instrument)
            self._sensor_table.update_data(instrument_info)
            self.confirm_button.configure(state='normal')
        except:
            messagebox.showerror('Något gick fel!', str(traceback.format_exc()))

    @property
    def config_root_directory(self):
        return self._frame_info.config_root_path

    @property
    def data_root_directory_local(self):
        return self._frame_info.data_root_path_local

    @property
    def data_root_directory_server(self):
        return self._frame_info.data_root_path_server

    @property
    def instrument(self):
        return self._frame_instrument_buttons.instrument

    @instrument.setter
    def instrument(self, name):
        self._frame_instrument_buttons.instrument = name

    def save_selection(self):
        self._frame_info.save_selection()
        super().save_selection()


class DataFileInfoFrame(tk.Frame):
    """
    Frame to show information about existing and built data file.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller

        self._build_frame()

    def _build_frame(self):
        layout = dict(padx=3,
                      pady=3)

        self._stringvar_latest_file = tk.StringVar()
        self._stringvar_current_file = tk.StringVar()

        r = 0
        tk.Label(self, text='Senast fil på server:').grid(row=r, column=0, sticky='w', **layout)
        tk.Label(self, textvariable=self._stringvar_latest_file).grid(row=r, column=1, sticky='w', **layout)

        tk.Button(self, text='Uppdatera', command=lambda: post_event('update_server_info', None)).grid(row=r, column=2, sticky='w', **layout)

        r += 1
        tk.Label(self, text='Fil som kommer skapas:').grid(row=r, column=0, sticky='w', **layout)
        tk.Label(self, textvariable=self._stringvar_current_file).grid(row=r, column=1, sticky='w', **layout)

    def set_latest_file(self, path):
        if path:
            self._stringvar_latest_file.set(path)
        else:
            self._stringvar_latest_file.set('För lite information')

    def set_current_file(self, path):
        if path:
            self._stringvar_current_file.set(path)
        else:
            self._stringvar_current_file.set('För lite information')


class SelectionInfoFrame(tk.Frame, SaveSelection):

    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller

        self._saves_id_key = 'SelectionInfoFrame'

        self.latest_instrument = None

        self._selections_to_store = ['_stringvar_config_root_path',
                                     '_stringvar_data_path_local',
                                     '_stringvar_data_root_path_server']

        self._build_frame()

        self.load_selection()

        self._set_paths_in_controller()

    def _set_paths_in_controller(self):
        self._set_config_root_directory()
        self._set_data_directory_local()
        self._set_data_root_directory_server()

    def _build_frame(self):
        layout = dict(padx=3,
                      pady=3)

        self._stringvar_config_root_path = tk.StringVar()
        self._stringvar_data_path_local = tk.StringVar()
        self._stringvar_data_root_path_server = tk.StringVar()
        self._stringvar_ctd = tk.StringVar()
        self._stringvar_xmlcon = tk.StringVar()
        self._stringvar_seasave_psa = tk.StringVar()

        r = 0
        root_config = tk.Label(self, text='Rotkatalog för configfiler:')
        root_config.grid(row=r, column=0, sticky='w', **layout)
        root_config.bind('<Control-Button-1>', self._on_click_root_config)
        tk.Label(self, textvariable=self._stringvar_config_root_path).grid(row=r, column=1, sticky='w', **layout)

        r += 1
        data_local = tk.Label(self, text='Sparar filer till mapp:')
        data_local.grid(row=r, column=0, sticky='w', **layout)
        data_local.bind('<Control-Button-1>', self._on_click_data_local)
        tk.Label(self, textvariable=self._stringvar_data_path_local).grid(row=r, column=1, sticky='w', **layout)

        r += 1
        root_data_server = tk.Label(self, text='Rotkatalog för data på server:')
        root_data_server.grid(row=r, column=0, sticky='w', **layout)
        root_data_server.bind('<Control-Button-1>', self._on_click_root_data_server)
        tk.Label(self, textvariable=self._stringvar_data_root_path_server).grid(row=r, column=1, sticky='w', **layout)

        r += 1
        ttk.Separator(self, orient='horizontal').grid(row=r, column=0, columnspan=2, sticky='ew')

        r += 1
        tk.Label(self, text='Vald CTD:').grid(row=r, column=0, sticky='w', **layout)
        tk.Label(self, textvariable=self._stringvar_ctd).grid(row=r, column=1, sticky='w', **layout)

        r += 1
        ttk.Separator(self, orient='horizontal').grid(row=r, column=0, columnspan=2, sticky='ew')

        r += 1
        tk.Label(self, text='Sökväg XMLCON:').grid(row=r, column=0, sticky='w', **layout)
        tk.Label(self, textvariable=self._stringvar_xmlcon).grid(row=r, column=1, sticky='w', **layout)

        r += 1
        tk.Label(self, text='Sökväg seasave.psa:').grid(row=r, column=0, sticky='w', **layout)
        tk.Label(self, textvariable=self._stringvar_seasave_psa).grid(row=r, column=1, sticky='w', **layout)

        r += 1
        ttk.Separator(self, orient='horizontal').grid(row=r, column=0, columnspan=2, sticky='ew')

        tkw.grid_configure(self, nr_columns=2, nr_rows=r+1)

    def _on_click_root_config(self, event=None):
        directory = filedialog.askdirectory()
        if not directory:
            return
        ok = self._set_config_root_directory(directory)
        if ok:
            self.save_selection()
            self.update_info()
        else:
            self.reset_info()
        post_event('change_config_path', ok)

    def _on_click_data_local(self, event=None):
        directory = filedialog.askdirectory()
        if not directory:
            return
        # Add year folder if not present
        directory = pathlib.Path(directory)
        year = directory.name
        if not (len(year) == 4 and year.isdigit()):
            directory = pathlib.Path(directory, str(datetime.datetime.now().year))
            directory.mkdir(parents=True, exist_ok=True)
        ok = self._set_data_directory_local(directory)
        if ok:
            self.save_selection()
            self.update_info()
        else:
            self.reset_info()
        post_event('change_data_path_local', ok)

    def _on_click_root_data_server(self, event=None):
        print(1)
        directory = filedialog.askdirectory()
        if not directory:
            return
        print(2)
        ok = self._set_data_root_directory_server(directory)
        if ok:
            print(3)
            self.save_selection()
            self.update_info()
        else:
            print(4)
            self.reset_info()
        post_event('change_data_path_server', ok)

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

    def _set_config_root_directory(self, directory=None):
        print('directory', directory)
        if not directory:
            directory = self._stringvar_config_root_path.get()
        try:
            self.controller.ctd_config_root_directory = directory
            self._stringvar_config_root_path.set(directory or '')
        except FileNotFoundError:
            messagebox.showerror('Fel i sökväg',
                                 f'Kan inte hitta rätt sökväg: '
                                 f'\n{traceback.format_exc()}')
            return False
        except:
            messagebox.showerror('Val av instrument',
                                 f'Rotkatalogens struktur för configfiler verkar inte stämma: '
                                 f'\n{traceback.format_exc()}')
            return False
        return True

    def _set_data_directory_local(self, directory=None):
        directory = directory or self._stringvar_data_path_local.get()
        # if not directory:
        #     messagebox.showerror('Sätt lokal data',
        #                          f'Ingen mapp för lokal data vald!')
        #     return False
        try:
            self.controller.ctd_data_directory = directory
            self._stringvar_data_path_local.set(self.controller.ctd_data_directory or '')
        except:
            messagebox.showerror('Sätt lokal data',
                                 f'Något gick fel när rotkatalogen för lokal data skulle sättas: '
                                 f'\n{traceback.format_exc()}')
            return False
        return True

    def _set_data_root_directory_server(self, directory=None):
        if not directory:
            directory = self._stringvar_data_root_path_server.get()
        try:
            self.controller.ctd_data_root_directory_server = directory
            self._stringvar_data_root_path_server.set(self.controller.ctd_data_root_directory_server or '')
        except:
            messagebox.showerror('Val av instrument',
                                 f'Något gick fel när rotkatalogen för data på servern skulle sättas: '
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
    def data_root_path_local(self):
        return self._stringvar_data_path_local.get()

    @data_root_path_local.setter
    def data_root_path_local(self, path):
        self._stringvar_data_path_local.set(str(path))

    @property
    def data_root_path_server(self):
        return self._stringvar_data_root_path_server.get()

    @data_root_path_server.setter
    def data_root_path_server(self, path):
        self._stringvar_data_root_path_server.set(str(path))


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

    def deselect(self, *args, **kwargs):
        for name, wid in self.buttons.items():
            wid.configure(bg=self.button_unselected_color)
        self._selected = None

    def _select(self, name):
        print('Name', name)
        if not self.buttons.get(name):
            return

        self.buttons[name].configure(bg=self.button_selected_color)
        self._selected = name

    def _on_select_instrument(self, button_name):
        self.deselect()
        self._select(button_name)
        post_event('select_instrument', button_name)

    @property
    def instrument(self):
        return self._selected

    @instrument.setter
    def instrument(self, name):
        if not self.buttons.get(name):
            return
        self.deselect()
        self._select(name)


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


class FrameManageCTDcastsStation(tk.Frame, SaveSelection):

    def __init__(self, parent, controller):
        super().__init__(parent)

        self.__instrument = ''

        self.controller = controller

        self._build_frame()

        self._saves_id_key = 'FrameManageCTDcastsStation'
        self._selections_to_store = [self.default_user_frame]

        self._set_default_user()

        subscribe('focus_out_series', self._update_data_file_info)
        subscribe('toggle_tail', self._update_data_file_info)
        subscribe('series_step', self._update_data_file_info)
        subscribe('set_next_series', self._update_data_file_info)
        subscribe('focus_out_cruise', self._update_data_file_info)
        subscribe('load_svepa', self._update_data_file_info)
        subscribe('update_server_info', self._update_data_file_info)

    def _build_frame(self):

        frame = tk.Frame(self)
        frame.grid(row=0, column=0, sticky='nw')
        tkw.grid_configure(self)

        layout = dict(padx=5, pady=5, sticky='nwse')

        top_frame = tk.Frame(frame)
        top_frame.grid(row=0, column=0, sticky='ew')
        self.instrument_text_frame = components.SelectedInstrumentTextFrame(top_frame, self.controller, row=0, column=0, **layout)
        self.default_user_frame = components.SelectedDefaultUserTextFrame(top_frame, self.controller, row=0, column=1, **layout)

        ttk.Separator(frame, orient='horizontal').grid(row=1, column=0, sticky='ew')

        self.content_frame = StationPreSystemFrame(frame, controller=self.controller, row=2, column=0, **layout)

        ttk.Separator(frame, orient='horizontal').grid(row=3, column=0, sticky='ew')

        self.data_file_info_frame = DataFileInfoFrame(frame, controller=self.controller)
        self.data_file_info_frame.grid(row=4, column=0, **layout)

        ttk.Separator(frame, orient='horizontal').grid(row=5, column=0, sticky='ew')

        tkw.grid_configure(frame, nr_rows=6)

    def _set_default_user(self):
        default_user = Defaults().user
        print('default_user', '::::::::::::::::', default_user)
        self.default_user_frame.set(default_user)
        post_event('select_default_user', default_user)

    def _update_data_file_info(self, data):
        self.data_file_info_frame.set_latest_file(self.content_frame.get_latest_file(server=True))
        try:
            self.data_file_info_frame.set_current_file(self.content_frame.get_current_file())
        except ValueError as e:
            if 'Missing information' in str(e):
                return
            raise

    def _update_frame(self):
        # self.instrument_text_frame.instrument = self.__instrument
        self.content_frame.instrument = self.__instrument

    def save_selection(self):
        self.content_frame.save_selection()
        super().save_selection()

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
        # self.instrument_text_frame.instrument = self.__instrument
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





