import tkinter as tk
from tkinter import ttk

from operator import itemgetter

import sharkpylib.tklib.tkinter_widgets as tkw


class MonospaceLabel(tk.Label):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        # self.config(font=("Courier", 10))
        self.config(font='TkFixedFont')


class ColoredFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        kw = dict(highlightthickness=1)
        kw.update(kwargs)
        super().__init__(parent, **kw)

    def set_frame_color(self, color):
        self.config(highlightbackground=color, highlightcolor=color)

    def set_frame_thickness(self, thickness):
        self.config(highlightthickness=thickness)

    def set_fill_color(self, color):
        self.config(bg=color)


class LoadSvepaButton(ColoredFrame):

    def __init__(self,
                 parent,
                 title='double entry',
                 width=8,
                 **kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        self.title = title

        if type(width) == int:
            self.width = [width, width]
        else:
            self.width = width[:2]

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._cb = set()

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=5,
                      sticky='nsew')

        self.button = tk.Button(self, text='Load SVEPA', command=self._callback)
        self.button.grid(**layout)

        tkw.grid_configure(self)

    def _callback(self, *args):
        for func in self._cb:
            func()

    def add_callback(self, func):
        self._cb.add(func)


class LabelDropdownList(ColoredFrame):

    def __init__(self,
                 parent,
                 title='dropdown list',
                 width=10,
                 **kwargs):

        self.grid_frame = {'padx': 5,
                            'pady': 5,
                            'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        self.title = title
        self.width = width

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._cb_select = set()

        self._create_frame()

    def _create_frame(self):
        # layout = dict(padx=5,
        #               pady=5,
        #               sticky='nsew')
        # tk.Label(self, text=self.title).grid(column=0, padx=5, pady=5, sticky='w')
        MonospaceLabel(self, text=self.title).grid(column=0, padx=5, pady=5, sticky='w')

        self.stringvar = tk.StringVar()
        self.combobox = ttk.Combobox(self, width=self.width, textvariable=self.stringvar, state="readonly")
        self.combobox.bind("<<ComboboxSelected>>", self._on_select)
        self.combobox.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        tkw.grid_configure(self, nr_columns=2)

    def _on_select(self, *args):
        for func in self._cb_select:
            func()

    def add_callback_select(self, func):
        self._cb_select.add(func)

    @property
    def values(self):
        return self.combobox['values']

    @values.setter
    def values(self, items):
        current_value = self.stringvar.get()
        self.combobox['values'] = items
        if current_value not in items:
            self.stringvar.set(items[0])

    @property
    def value(self):
        return self.stringvar.get()

    @value.setter
    def value(self, item):
        if item in self.combobox['values']:
            self.stringvar.set(item)

    def get(self):
        return self.value

    def set(self, item):
        self.value = item


class LabelDoubleEntry(ColoredFrame):

    def __init__(self,
                 parent,
                 title='double entry',
                 width=8,
                 **kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        self.title = title

        if type(width) == int:
            self.width = [width, width]
        else:
            self.width = width[:2]

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._cb = set()

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=5,
                      sticky='nsew')
        MonospaceLabel(self, text=self.title).grid(column=0, **layout)

        self.stringvar_first = tk.StringVar()
        self.stringvar_second = tk.StringVar()

        self.entry_first = tk.Entry(self, textvariable=self.stringvar_first, width=self.width[0])
        self.entry_first.grid(row=0, column=1, **layout)

        self.entry_second = tk.Entry(self, textvariable=self.stringvar_second, width=self.width[1])
        self.entry_second.grid(row=0, column=2, **layout)

        tkw.grid_configure(self, nr_columns=3)

    @property
    def first_value(self):
        return self.stringvar_first.get()

    @first_value.setter
    def first_value(self, value):
        self.stringvar_first.set(str(value))

    @property
    def second_value(self):
        return self.stringvar_second.get()

    @second_value.setter
    def second_value(self, value):
        self.stringvar_second.set(str(value))

    def get(self):
        return self.first_value, self.second_value

    def set(self, item):
        self.first_value = item[0]
        self.second_value = item[1]


class CruiseLabelDoubleEntry(LabelDoubleEntry):

    def __init__(self, *args, **kwargs):
        if not kwargs.get('title'):
            kwargs['title'] = 'Cruise'
        super().__init__(*args, **kwargs)
        self._modify()

    def _modify(self):
        self.stringvar_first.trace("w", lambda name, index, mode, sv=self.stringvar_first: self._on_change_entry(sv))
        self.stringvar_second.trace("w", lambda name, index, mode, sv=self.stringvar_second: self._on_change_entry(sv))
        self.entry_first.bind('<FocusIn>', self._on_focus_in_first)
        self.entry_second.bind('<FocusIn>', self._on_focus_in_second)

        self.entry_first.config(width=5)

    def _on_change_entry(self, stringvar=None):
        string = self.stringvar_first.get()
        new_string = ''.join([s for s in string if s.isdigit()])
        self.stringvar_first.set(new_string[:2])

        string = self.stringvar_second.get()
        new_string = ''.join([s for s in string if s.isdigit()])
        self.stringvar_second.set(new_string[:4])

    def _on_focus_in_first(self, event=None):
        self.entry_first.selection_range(0, 'end')

    def _on_focus_in_second(self, event=None):
        self.entry_second.selection_range(0, 'end')

    @property
    def nr(self):
        return self.first_value

    @nr.setter
    def nr(self, nr):
        self.first_value = nr

    @property
    def year(self):
        return self.second_value

    @year.setter
    def year(self, year):
        self.second_value = year


class VessleLabelDoubleEntry(LabelDoubleEntry):

    def __init__(self, *args, **kwargs):
        if not kwargs.get('title'):
            kwargs['title'] = 'Vessel'
        super().__init__(*args, **kwargs)
        self._modify()

    def _modify(self):
        self.stringvar_first.set('Svea')
        self.stringvar_second.set('77SE')

        self.entry_first.config(state='disabled', width=5)
        self.entry_second.config(state='disabled', width=5)

    @property
    def name(self):
        return self.first_value

    @name.setter
    def name(self, nr):
        self.first_value = nr

    @property
    def code(self):
        return self.second_value

    @code.setter
    def code(self, year):
        self.second_value = year


class SelectedInstrumentTextFrame(ColoredFrame):

    def __init__(self,
                 parent,
                 **kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._instrument_type = 'CTD'
        self.__instrument_name = ''

        self.stringvar = tk.StringVar()

        MonospaceLabel(self, textvariable=self.stringvar).grid(row=0, column=0, padx=5, pady=5, sticky='w')

    @property
    def instrument(self):
        return self.__instrument_name

    @instrument.setter
    def instrument(self, name):
        self.__instrument_name = name
        self._set_text()

    def _set_text(self):
        string = f'Vald {self._instrument_type}: {self.__instrument_name}'
        self.stringvar.set(string)

    def get(self):
        return self.instrument

    def set(self, item):
        self.instrument = item


class SeriesEntryPicker(ColoredFrame):

    def __init__(self,
                 parent,
                 width=10,
                 include_arrows=True,
                 title='Series',
                 **kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        self.title = title

        if type(width) == int:
            self.width = [width, width]
        else:
            self.width = width[:2]

        self.include_arrows = include_arrows

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._cb = set()

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=5,
                      sticky='nsew')
        MonospaceLabel(self, text=self.title).grid(column=0, **layout)

        self.stringvar = tk.StringVar()
        self.stringvar.trace("w", lambda name, index, mode, sv=self.stringvar: self._on_change_entry(sv))

        self.entry = tk.Entry(self, textvariable=self.stringvar, width=self.width[0])
        self.entry.grid(row=0, column=1, ipady=2, **layout)
        self.entry.bind('<FocusOut>', self._on_focus_out)
        self.entry.bind('<Return>', self._on_focus_out)
        self.entry.bind('<FocusIn>', self._on_focus_in)

        if not self.include_arrows:
            tkw.grid_configure(self, nr_columns=2)
            return

        frame_buttons = tk.Frame(self)
        frame_buttons.grid(row=0, column=2, **layout)

        self.button_down = tk.Button(frame_buttons, text=u'\u25BC', command=self._on_button_down)
        self.button_down.grid(row=0, column=0, **layout)
        self.button_down.config(font=('Courier', 8))

        self.button_up = tk.Button(frame_buttons, text=u'\u25B2', command=self._on_button_up)
        self.button_up.grid(row=0, column=1, **layout)
        self.button_up.config(font=('Courier', 8))

        tkw.grid_configure(self, nr_columns=3)

    def _on_change_entry(self, event=None):
        string = self.stringvar.get()
        new_string = ''.join([s for s in string if s.isdigit()])
        self.stringvar.set(new_string[:4])

    def _on_focus_in(self, event=None):
        self.entry.selection_range(0, 'end')

    def _on_focus_out(self, event=None):
        string = self.stringvar.get()
        num = int(''.join([s for s in string if s.isdigit()]))
        if num < 1:
            num = 1
        elif num > 9999:
            num = 9999
        new_string = str(num).zfill(4)
        self.stringvar.set(new_string)
        for func in self._cb:
            func(new_string)

    def _on_button_down(self, event=None):
        string = self.value
        if not string:
            self.value = 9999
        else:
            self.value = int(string) - 1

    def _on_button_up(self, event=None):
        string = self.value
        if not string:
            self.value = 1
        else:
            num = int(string) + 1
            if num > 9999:
                num = 9999
            self.value = num

    @property
    def value(self):
        return self.stringvar.get().strip()

    @value.setter
    def value(self, value):
        self.stringvar.set(str(value).strip())
        self._on_focus_out()

    def add_callback(self, func):
        self._cb.add(func)

    def get(self):
        return self.value

    def set(self, item):
        self.value = item


class SurfaceSoakSelector(ColoredFrame):

    def __init__(self,
                parent,
                ** kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self.buttons = {}

        self._selected = None

        self._cb = set()

        self.button_unselected_color = None
        self.button_selected_color = '#6bd688'

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=5,
                      sticky='nsew')
        MonospaceLabel(self, text='Soak').grid(column=0, **layout)
        self.buttons['normal'] = tk.Button(self, text='Normal', command=lambda x='normal': self._on_select_button(x))
        self.buttons['normal'].grid(row=0, column=1, **layout)
        self.buttons['deep'] = tk.Button(self, text='Deep', command=lambda x='deep': self._on_select_button(x))
        self.buttons['deep'].grid(row=0, column=2, **layout)
        self.buttons['shallow'] = tk.Button(self, text='Shallow', command=lambda x='shallow': self._on_select_button(x))
        self.buttons['shallow'].grid(row=0, column=3, **layout)

        self.button_unselected_color = self.buttons['normal'].cget('bg')

        tkw.grid_configure(self, nr_columns=4)

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
            for func in self._cb:
                func()

    def _on_select_button(self, button_name):
        self._deselect()
        self._select(button_name)

    @property
    def surfacesoak(self):
        return self._selected

    @surfacesoak.setter
    def surfacesoak(self, name):
        if not self.buttons.get(name):
            return
        self._deselect()
        self._select(name, callback=False)

    def add_callback(self, func):
        self._cb.add(func)

    def get(self):
        return self.surfacesoak

    def set(self, item):
        self.surfacesoak = item


class SensorTable(ColoredFrame):

    def __init__(self,
                parent,
                ** kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._data = {}
        self._instrument_list = []
        self._current_instrument = None
        self._current_instrument_data = {}
        self._current_sort_par = None

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=2,
                      sticky='nsew')

        self.stringvar_instrument = tk.StringVar()
        self.combobox_instrument = ttk.Combobox(self, textvariable=self.stringvar_instrument, state="readonly")
        self.combobox_instrument.grid(row=0, column=0, padx=5, pady=5, sticky='nw')
        self.combobox_instrument.bind("<<ComboboxSelected>>", self._on_select_instrument)

        list_frame = tk.Frame(self)
        list_frame.grid(row=0, column=1, **layout)

        tkw.grid_configure(self)

        canvas = tk.Canvas(list_frame)
        canvas.grid(row=0, column=0, sticky='nsew')
        # canvas.pack(side=tk.LEFT)

        yscrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=canvas.yview)
        yscrollbar.grid(row=0, column=1, sticky='ns')
        # yscrollbar.pack(side=tk.RIGHT, fill='y')

        canvas.configure(yscrollcommand=yscrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor='nw')

        tkw.grid_configure(list_frame, nr_columns=2, c0=10)
        tkw.grid_configure(canvas)

        column_width = [10, 10, 5]

        tk.Button(frame, text='Parameter', width=column_width[0], command=lambda x='parameter': self._sort_by(x)).grid(row=0, column=0, **layout)
        tk.Button(frame, text='Sensor ID', width=column_width[1], command=lambda x='sensor_id': self._sort_by(x)).grid(row=0, column=1, **layout)
        tk.Button(frame, text='Status', width=column_width[2], command=lambda x='status': self._sort_by(x)).grid(row=0, column=2, **layout)

        self.stringvar_par = []
        self.stringvar_sensor_id = []
        self.stringvar_status = []
        self.combobox_status = []

        for i in range(80):
            par = tk.StringVar()
            sensor_id = tk.StringVar()
            status = tk.StringVar()

            tk.Entry(frame, textvariable=par, width=column_width[0], state='disabled').grid(row=i+1, column=0, **layout)
            tk.Entry(frame, textvariable=sensor_id, width=column_width[1], state='disabled').grid(row=i+1, column=1, **layout)
            cb = ttk.Combobox(frame, textvariable=status, width=column_width[2], state="readonly")
            cb.grid(row=i + 1, column=2, **layout)
            cb.bind("<<ComboboxSelected>>", lambda event, index=i: self._on_change_status(event, index))
            # cb.bind("<<ComboboxSelected>>", self._on_change_status)
            cb['values'] = ['OK', 'BAD']
            status.set('OK')


            # cb = ttk.Checkbutton(frame, variable=status, command=lambda index=i: self._on_change_status(index))
            # cb.grid(row=i+1, column=2, **layout)

            self.stringvar_par.append(par)
            self.stringvar_sensor_id.append(sensor_id)
            self.stringvar_status.append(status)
            self.combobox_status.append(cb)

        tkw.grid_configure(frame, nr_rows=i+2)

    def get(self):
        """
        :return: {'bad_sensors: [],
                  'current_instrument: str,
                  'current_sort_par: str}
        """
        if not self._data:
            return
        return_info = {'current_instrument': self._current_instrument,
                       'current_sort_par': self._current_sort_par}
        bad_sensors = []
        for sensor_id, info in self._data.items():
            if info.get('status') == 'BAD':
                bad_sensors.append(sensor_id)
        return_info['bad_sensors'] = bad_sensors
        return return_info

    def set(self, info):
        """
        Expects: {'bad_sensors: [],
                  'current_instrument: str,
                  'current_sort: str}
        :return:
        """
        if not self._data:
            return
        for sensor_id in info['bad_sensors']:
            if sensor_id not in self._data:
                continue
            self._data[sensor_id]['status'] = 'BAD'
        self._current_sort_par = info['current_sort_par']
        self.instrument = info['current_instrument']

    @property
    def instrument(self):
        return self._current_instrument

    @instrument.setter
    def instrument(self, instrument):
        if instrument == self._current_instrument:
            pass
        elif instrument in self._instrument_list:
            self.stringvar_instrument.set(instrument)
            self._on_select_instrument()

    def _on_select_instrument(self, event=None):
        if not self._data:
            return
        self._current_instrument = self.stringvar_instrument.get()
        if self._current_instrument == 'All':
            self._current_instrument_data = self._data
        else:
            self._current_instrument_data = {}
            for key, value in self._data.items():
                if value.get('model') == self._current_instrument:
                    self._current_instrument_data[key] = value
        self._sort_by(self._current_sort_par)

    def _on_change_status(self, event, index):
        status = self.stringvar_status[index].get()
        sensor_id = self.stringvar_sensor_id[index].get()
        self._data[sensor_id]['status'] = status

    def _get_sorted_list_by(self, key=None):
        self._current_sort_par = key
        if not key or key == 'sensor_id':
            return sorted(self._current_instrument_data)
        id_list = list(self._current_instrument_data)
        value_list = [self._current_instrument_data[_id].get(key, '') for _id in self._current_instrument_data.keys()]
        sorted_id_list, sorted_value_list = list(zip(*sorted(zip(id_list, value_list), key=itemgetter(1))))
        return sorted_id_list

    def _sort_by(self, key=None):
        self._clear_widget()
        self._sort_by_id_list(self._get_sorted_list_by(key))

    def _sort_by_id_list(self, id_list):
        for i, _id in enumerate(id_list):
            self.combobox_status[i].configure(state='normal')
            self.stringvar_par[i].set(self._data[_id]['parameter'])
            self.stringvar_sensor_id[i].set(self._data[_id]['sensor_id'])
            status = self._data[_id].get('status')
            if status == 'BAD':
                print('BAD')
            self.stringvar_status[i].set(status)

    def update_data(self, data):
        """
        :param data:
        :return:
        """
        self._data = data.copy()

        print(len(data))
        for _id in self._data:
            self._data[_id]['status'] = 'OK'
        self._instrument_list = ['All'] + sorted(set([self._data[_id].get('model', '') for _id in self._data]))
        self.combobox_instrument['values'] = self._instrument_list
        if self._current_instrument not in self._instrument_list:
            self._current_instrument = self._instrument_list[0]
        self.stringvar_instrument.set(self._current_instrument)
        self._on_select_instrument()

    def _clear_widget(self):
        for i in range(len(self.stringvar_par)):
            self.stringvar_par[i].set('')
            self.stringvar_sensor_id[i].set('')
            self.stringvar_status[i].set('OK')
            self.combobox_status[i].configure(state='disabled')


class LabelCheckbox(ColoredFrame):

    def __init__(self,
                 parent,
                 title='New station', 
                 **kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._cb = set()
        
        self.title = title

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=5,
                      sticky='nsew')


        self.intvar = tk.BooleanVar()
        self.checkbutton = tk.Checkbutton(self, variable=self.intvar, command=self._on_toggle)
        self.checkbutton.grid(row=0, column=0, **layout)

        MonospaceLabel(self, text=self.title).grid(row=0, column=1, **layout)

    def _on_toggle(self, *args):
        print(self.intvar.get())
        for func in self._cb:
            func(self.intvar.get())

    def get(self):
        return self.intvar.get()

    def set(self, state):
        self.intvar.set(state)

    def add_callback(self, func):
        self._cb.add(func)


class PositionEntries(ColoredFrame):

    def __init__(self,
                 parent,
                 width=8,
                 **kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        if type(width) == int:
            self.width = [width, width]
        else:
            self.width = width[:2]

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._cb = set()

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=5,
                      sticky='nsew')
        MonospaceLabel(self, text='Lat').grid(row=0, column=0, **layout)
        MonospaceLabel(self, text='Lon').grid(row=0, column=1, **layout)

        self.stringvar_lat = tk.StringVar()
        self.stringvar_lon = tk.StringVar()
        self.stringvar_lat.trace("w", lambda name, index, mode, sv=self.stringvar_lat: self._on_change_entry_lat(sv))
        self.stringvar_lon.trace("w", lambda name, index, mode, sv=self.stringvar_lon: self._on_change_entry_lon(sv))

        self.entry_lat = tk.Entry(self, textvariable=self.stringvar_lat, width=self.width[0])
        self.entry_lat.grid(row=1, column=0, **layout)

        self.entry_lon = tk.Entry(self, textvariable=self.stringvar_lon, width=self.width[1])
        self.entry_lon.grid(row=1, column=1, **layout)

        self.entry_lat.bind('<FocusOut>', self._on_focus_out_lat)
        self.entry_lat.bind('<Return>', self._on_focus_out_lat)
        self.entry_lat.bind('<FocusIn>', self._on_focus_in_lat)

        self.entry_lon.bind('<FocusOut>', self._on_focus_out_lon)
        self.entry_lon.bind('<Return>', self._on_focus_out_lon)
        self.entry_lon.bind('<FocusIn>', self._on_focus_in_lon)
        
        tkw.grid_configure(self, nr_columns=2, nr_rows=2)

    def _on_change_entry_lat(self, *args):
        self._on_change_entry(self.stringvar_lat, self.entry_lat)

    def _on_change_entry_lon(self, *args):
        self._on_change_entry(self.stringvar_lon, self.entry_lon)

    def _on_change_entry(self, stringvar, entry):
        string = stringvar.get()
        new_string = ''.join([s for s in string if s.isdigit()][:6])
        stringvar.set(new_string)

        # current_index = entry.index(tk.INSERT)
        # chars = '1234567890.'
        # new_string = ''
        # count = 0
        # for s in string:
        #     if s not in chars:
        #         current_index -= 1
        #         continue
        #     if s == '.':
        #         if count < 4:
        #             current_index -= 1
        #             continue
        #         if '.' in new_string:
        #             current_index -= 1
        #             continue
        #     new_string += s
        #     count += 1
        #     if '.' not in new_string:
        #         if count == 4:
        #             new_string += '.'
        #             count += 1
        #             current_index += 2
        #
        # new_string = new_string[:7]
        # stringvar.set(new_string)
        #
        # print('a:', current_index, len(new_string))
        # if current_index < len(new_string):
        #     entry.icursor(current_index - 1)
        # else:
        #     entry.icursor(current_index)


    def _on_focus_in_lat(self, event=None):
        self.entry_lat.selection_range(0, 'end')

    def _on_focus_in_lon(self, event=None):
        self.entry_lon.selection_range(0, 'end')

    def _on_focus_out_lat(self, event=None):
        string = self.stringvar_lat.get()
        string_list = list(string)
        string_list.insert(4, '.')
        new_string = ''.join(string_list)
        self.stringvar_lat.set(new_string)

    def _on_focus_out_lon(self, event=None):
        string = self.stringvar_lon.get()
        string_list = list(string)
        string_list.insert(4, '.')
        new_string = ''.join(string_list)
        self.stringvar_lon.set(new_string)
            
    def get(self):
        return self.stringvar_lat.get(), self.stringvar_lon.get()

    def set(self, items):
        self.stringvar_lat.set(items[0])
        self.stringvar_lon.set(items[1])

    def add_callback(self, func):
        self._cb.add(func)


