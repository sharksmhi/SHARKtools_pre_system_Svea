import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

import datetime

import math
from pathlib import Path
from operator import itemgetter

from ..events import post_event
from ..events import subscribe
from .. import saves

import sharkpylib.tklib.tkinter_widgets as tkw


class AutocompleteCombobox(ttk.Combobox):
    """
    https://gist.github.com/victordomingos/3a2a143c573e49308aad392acff25b47

    Subclass of ttk.Combobox that features autocompletion.
    To cycle through hits use down and up arrow keys.
    """

    def set_values(self, values):
        self['values'] = values
        self._completion_list = values
        self._hits = []
        self._hit_index = 0
        self.position = 0
        self.bind('<KeyRelease>', self.handle_keyrelease)

    def autocomplete(self, delta=0):
        """autocomplete the Entry, delta may be 0/1/-1 to cycle through possible hits"""
        if delta:  # need to delete selection otherwise we would fix the current position
            self.delete(self.position, tk.END)
        else:  # set position to end so selection starts where textentry ended
            self.position = len(self.get())
        # collect hits
        _hits = []
        for element in self._completion_list:
            if element.lower().startswith(self.get().lower()):
                _hits.append(element)

        # if we have a new hit list, keep this in mind
        if _hits != self._hits:
            self._hit_index = 0
            self._hits = _hits
        # only allow cycling if we are in a known hit list
        if _hits == self._hits and self._hits:
            self._hit_index = (self._hit_index + delta) % len(self._hits)
        # now finally perform the auto completion
        if self._hits:
            self.delete(0, tk.END)
            self.insert(0, self._hits[self._hit_index])
            self.select_range(self.position, tk.END)

    def handle_keyrelease(self, event):
        """event handler for the keyrelease event on this widget"""
        if event.keysym == "BackSpace":
            if self.position < self.index(tk.END):  # delete the selection
                self.delete(self.position, tk.END)
            else:
                self.position = self.index(tk.END)
        if event.keysym == "Left":
            if self.position < self.index(tk.END):  # delete the selection
                self.delete(self.position, tk.END)
        if event.keysym == "Right":
            self.position = self.index(tk.END)  # go to end (no selection)
        if event.keysym == "Down":
            self.autocomplete(1)  # cycle to next hit
        if event.keysym == "Up":
            self.autocomplete(-1)  # cycle to previous hit
        # perform normal autocomplete if event is a single key or an umlaut
        if len(event.keysym) == 1:
            self.autocomplete()
            
            
class MonospaceLabel(tk.Label):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        # self.config(font=("Courier", 10))
        self.config(font='TkFixedFont')
        
    def set_color(self, color='black'):
        self.configure(fg=color)


class Common:
    def set_color(self, color='black'):
        print('TRYING to set color')
        if hasattr(self, 'monospace_label'):
            print('Setting color:', color)
            self.monospace_label.set_color(color)


class ColoredFrame(tk.Frame, Common):
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


class AddSampInfo(tk.Frame, Common):

    def __init__(self,
                 parent,
                 id,
                 title='Add sampl:',
                 width=8,
                 state='normal',
                 data_type=None,
                 **kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        self._id = id
        self.title = title
        self.width = width
        self.data_type = data_type
        self.state = state

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._right_widgets = []
        self._nr_right_rows = 4

        self._create_frame()

        subscribe('load_svepa', self._update)

    def _create_frame(self):
        layout = dict(padx=2,
                      pady=5,
                      sticky='nw')
        self.monospace_label = MonospaceLabel(self, text=self.title)
        self.monospace_label.grid(column=0, **layout)

        self.right_frame = tk.Frame(self)
        self.right_frame.grid(row=0, column=1, **layout)

    def _remove_right_widgets(self):
        for wid in self._right_widgets:
            wid.destroy()
        self._right_widgets = []

    def _update(self, data):
        add_samp_list = data.get('running_event_types', [])
        self._update_rigth_widgets(add_samp_list)

    def _update_rigth_widgets(self, add_samp_list):
        layout = dict(padx=5,
                      pady=1,
                      sticky='nw')
        self._remove_right_widgets()
        len_add_samp_list = len(add_samp_list)
        self._nr_right_rows = max(self._nr_right_rows, len_add_samp_list)
        for r in range(self._nr_right_rows):
            text = ''
            if r < len_add_samp_list:
                text = add_samp_list[r]
            wid = tk.Label(self.right_frame, text=text)
            wid.grid(row=r, **layout)
            self._right_widgets.append(wid)

    @property
    def value(self):
        return sorted([item.cget('text') for item in self._right_widgets if item.cget('text').strip()])

    @value.setter
    def value(self, items):
        if not items:
            items = []
        self._update_rigth_widgets(items)


class LabelDropdownList(tk.Frame, Common):

    def __init__(self,
                 parent,
                 id,
                 title='dropdown list',
                 width=10,
                 state='readonly',
                 autocomplete=False,
                 **kwargs):

        self.grid_frame = {'padx': 5,
                            'pady': 5,
                            'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        self._id = id
        self.title = title
        self.width = width
        self.state = state
        self.autocomplete = autocomplete
        if self.autocomplete:
            self.state = 'normal'

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._old_value = None

        self._create_frame()

    def _create_frame(self):
        # layout = dict(padx=5,
        #               pady=5,
        #               sticky='nsew')
        # tk.Label(self, text=self.title).grid(column=0, padx=5, pady=5, sticky='w')
        self.monospace_label = MonospaceLabel(self, text=self.title)
        self.monospace_label.grid(column=0, padx=5, pady=5, sticky='w')

        self._stringvar = tk.StringVar()
        if self.autocomplete:
            self.combobox = AutocompleteCombobox(self, width=self.width, textvariable=self._stringvar)
        else:
            self.combobox = ttk.Combobox(self, width=self.width, textvariable=self._stringvar, state=self.state)
        self.combobox.bind("<<ComboboxSelected>>", self._on_select)
        self.combobox.bind("<<FocusIn>>", self._on_focus_in)
        self.combobox.bind("<<FocusOut>>", self._on_focus_out)
        self.combobox.grid(row=0, column=1, padx=5, pady=5, sticky='e')

        tkw.grid_configure(self, nr_columns=2)

    def _has_new_value(self):
        current_value = self._stringvar.get()
        if current_value == self._old_value:
            return False
        self._old_value = current_value
        return True

    def _on_focus_in(self, *args):
        self._old_value = self._stringvar.get()

    def _on_focus_out(self, *args):
        if not self._has_new_value():
            return
        post_event(f'focus_out_{self._id}', self.value)

    def _on_select(self, *args):
        if not self._has_new_value():
            return
        post_event(f'select_{self._id}', self.value)

        # value_is_in_list = self.value in self.values
        # for func in self._cb_select:
        #     func(value_is_in_list=value_is_in_list)
    #
    # def add_callback_select(self, func):
    #     self._cb_select.add(func)

    @property
    def values(self):
        return self.combobox['values']

    @values.setter
    def values(self, items):
        current_value = self._stringvar.get()
        if self.autocomplete:
            self.combobox.set_values(items)
        else:
            self.combobox['values'] = items
        if current_value not in items:
            self._stringvar.set('')
            # self._stringvar.set(items[0])

    @property
    def value(self):
        return self._stringvar.get()

    @value.setter
    def value(self, item):
        self._stringvar.set(item)
        # if item in self.combobox['values']:
        #     self._stringvar.set(item)

    def get(self):
        return self.value

    def set(self, item):
        self.value = item


class LabelEntry(tk.Frame, Common):

    def __init__(self,
                 parent,
                 id,
                 title='entry',
                 width=8,
                 state='normal',
                 data_type=None,
                 **kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        self._id = id
        self.title = title
        self.width = width
        self.data_type = data_type
        self.state = state

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=5,
                      sticky='nsew')
        self.monospace_label = MonospaceLabel(self, text=self.title)
        self.monospace_label.grid(column=0, **layout)

        self._stringvar = tk.StringVar()
        # self._stringvar.trace("w", lambda name, index, mode, sv=self._stringvar: self._on_change_entry(sv))
        self._stringvar.trace("w", self._on_change_entry)

        self.entry = tk.Entry(self, textvariable=self._stringvar, width=self.width)
        self.entry.bind('<FocusOut>', self._on_focus_out)
        self.entry.bind('<Return>', self._on_focus_out)
        self.entry.grid(row=0, column=1, **layout)
        self.entry.configure(state=self.state)

        tkw.grid_configure(self, nr_columns=3)

    def _on_focus_out(self, *args):
        post_event(f'focus_out_{self._id}', self.value)
        # for func in self._cb:
        #     func(self.value)

    def _on_change_entry(self, *args):
        string = self._stringvar.get()
        if self.data_type == int:
            string = ''.join([s for s in string if s.isdigit()])
            self._stringvar.set(string)
        elif self.data_type == float:
            return_list = []
            for s in string:
                if s.isdigit():
                    return_list.append(s)
                elif s == '.' and '.' not in return_list:
                    return_list.append(s)

            return_string = ''.join(return_list)
            self._stringvar.set(return_string)

    @property
    def value(self):
        return self._stringvar.get()

    @value.setter
    def value(self, value):
        self._stringvar.set(str(value))
        self._on_change_entry()

    def get(self):
        return self.value

    def set(self, item):
        self.value = item


class LabelDoubleEntry(tk.Frame, Common):

    def __init__(self,
                 parent,
                 id,
                 title='double entry',
                 width=8,
                 **kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        self._id = id
        self.title = title

        if type(width) == int:
            self.width = [width, width]
        else:
            self.width = width[:2]

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=5,
                      sticky='nsew')
        self.monospace_label = MonospaceLabel(self, text=self.title)
        self.monospace_label.grid(column=0, **layout)

        self._stringvar_first = tk.StringVar()
        self._stringvar_second = tk.StringVar()

        self.entry_first = tk.Entry(self, textvariable=self._stringvar_first, width=self.width[0])
        self.entry_first.grid(row=0, column=1, **layout)

        self.entry_second = tk.Entry(self, textvariable=self._stringvar_second, width=self.width[1])
        self.entry_second.grid(row=0, column=2, **layout)

        tkw.grid_configure(self, nr_columns=3)

    @property
    def first_value(self):
        return self._stringvar_first.get()

    @first_value.setter
    def first_value(self, value):
        self._stringvar_first.set(str(value))

    @property
    def second_value(self):
        return self._stringvar_second.get()

    @second_value.setter
    def second_value(self, value):
        self._stringvar_second.set(str(value))

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
        self._stringvar_first.trace("w", lambda name, index, mode, sv=self._stringvar_first: self._on_change_entry(sv))
        self.entry_first.bind('<FocusIn>', self._on_focus_in_first)
        self.entry_first.bind('<FocusOut>', self._on_focus_out_first)
        self.entry_first.bind('<Return>', self._on_focus_out_first)

        self._stringvar_second.set(str(datetime.datetime.now().year))
        self.entry_second.configure(state='disabled')

        self.entry_first.config(width=5)

    def _on_change_entry(self, stringvar=None):
        string = self._stringvar_first.get()
        new_string = ''.join([s for s in string if s.isdigit()])
        value = new_string[:2]
        if value == '00':
            value = '01'
        self._stringvar_first.set(value)

        string = self._stringvar_second.get()
        new_string = ''.join([s for s in string if s.isdigit()])
        self._stringvar_second.set(new_string[:4].zfill(4))

    def _on_focus_in_first(self, event=None):
        self.entry_first.selection_range(0, 'end')

    def _on_focus_in_second(self, event=None):
        self.entry_second.selection_range(0, 'end')

    def _on_focus_out_first(self, event=None):
        string = self._stringvar_first.get()[:2].zfill(2)
        self._stringvar_first.set(string)
        post_event('focus_out_cruise', string)

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

    def set(self, item):
        self.first_value = item[0]


class CallbackButton(tk.Frame, Common):

    def __init__(self,
                 parent,
                 id,
                 title='CallbackButton',
                 **kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        self._id = id
        self.title = title

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=5,
                      sticky='nsew')

        self.button = tk.Button(self, text=self.title, command=self._callback)
        self.button.grid(**layout)

        tkw.grid_configure(self)

    def _callback(self, *args):
        post_event(f'button_{self._id}', None)

    def set_state(self, state):
        self.button.configure(state=state)


class DepthEntry(tk.Frame, Common):

    def __init__(self,
                 parent,
                 id,
                 width=8,
                 title='Plot depth',
                 state='normal',
                 data_type=None,
                 **kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        self._id = id
        self.title = title
        self.width = width
        self.data_type = data_type
        self.state = state

        self._bottom_depth_string_base = 'Bottom depth: '
        self._bottom_depth = None
        self.step = None

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=5,
                      sticky='nsew')
        self.monospace_label = MonospaceLabel(self, text=self.title)
        self.monospace_label.grid(column=0, **layout)

        self._stringvar = tk.StringVar()
        # self._stringvar.trace("w", lambda name, index, mode, sv=self._stringvar: self._on_change_entry(sv))
        self._stringvar.trace("w", self._on_change_entry)

        self.entry = tk.Entry(self, textvariable=self._stringvar, width=self.width)
        self.entry.bind('<FocusOut>', self._on_focus_out)
        self.entry.bind('<Return>', self._on_focus_out)
        self.entry.grid(row=0, column=1, pady=(5, 0), padx=5, sticky='w')
        self.entry.configure(state=self.state)

        self._stringvar_bottom_depth = tk.StringVar()
        tk.Label(self, textvariable=self._stringvar_bottom_depth).grid(row=1, column=1, pady=0, padx=5, sticky='nw')

        tkw.grid_configure(self, nr_columns=2)

    def _on_focus_out(self, *args):
        post_event(f'focus_out_{self._id}', self.value)

    def _on_change_entry(self, *args):
        string = self._stringvar.get()
        if self.data_type == int:
            string = ''.join([s for s in string if s.isdigit()])
            if string and int(string) > 1000:
                string = '1000'
            self._stringvar.set(string)
        elif self.data_type == float:
            return_list = []
            for s in string:
                if s.isdigit():
                    return_list.append(s)
                elif s == '.' and '.' not in return_list:
                    return_list.append(s)
            return_string = ''.join(return_list)
            if return_string and int(return_string) > 1000:
                return_string = '1000'
            self._stringvar.set(return_string)

    @property
    def water_depth(self):
        return self._bottom_depth

    @water_depth.setter
    def water_depth(self, depth):
        if depth in ['', None, True, False]:
            self.value = None
            self._stringvar_bottom_depth.set(self._bottom_depth_string_base)
            return
        self._bottom_depth = depth
        string = self._bottom_depth_string_base + str(depth)
        self._stringvar_bottom_depth.set(string)
        plot_depth = self._get_plot_depth(float(depth))
        self.value = plot_depth

    @property
    def value(self):
        return self._stringvar.get()

    @value.setter
    def value(self, value):
        if not value and value is not 0:
            self._stringvar.set('')
            return
        self._stringvar.set(str(value))
        self._on_change_entry()

    def get(self):
        return self.value

    def set(self, item):
        self.value = item

    def _get_plot_depth(self, water_depth):
        depth = water_depth + 5
        if water_depth < 50:
            self.step = 5
        elif water_depth < 150:
            self.step = 10
        else:
            self.step = 25

        return (math.ceil(depth / self.step)) * self.step


class IntEntry(tk.Frame, Common):

    def __init__(self,
                 parent,
                 id,
                 width=8,
                 title='IntEntry',
                 state='normal',
                 min_value=None,
                 max_value=None,
                 **kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        self._id = id
        self.title = title
        self.width = width
        self.state = state
        self.min_value = min_value
        self.max_value = max_value

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=5,
                      sticky='nsew')
        self.monospace_label = MonospaceLabel(self, text=self.title)
        self.monospace_label.grid(column=0, **layout)

        self._stringvar = tk.StringVar()
        # self._stringvar.trace("w", lambda name, index, mode, sv=self._stringvar: self._on_change_entry(sv))
        self._stringvar.trace("w", self._on_change_entry)

        self.entry = tk.Entry(self, textvariable=self._stringvar, width=self.width)
        self.entry.bind('<FocusOut>', self._on_focus_out)
        self.entry.bind('<Return>', self._on_focus_out)
        self.entry.grid(row=0, column=1, pady=(5, 0), padx=5, sticky='e')
        self.entry.configure(state=self.state)

        tkw.grid_configure(self, nr_columns=2)

    def _on_focus_out(self, *args):
        string = self._stringvar.get()
        if string:
            if self.min_value is not None and int(string) < self.min_value:
                string = str(self.min_value)
            if self.max_value is not None and int(string) > self.max_value:
                string = str(self.max_value)
            self._stringvar.set(string)
        post_event(f'focus_out_{self._id}', self.value)

    def _on_change_entry(self, *args):
        string = self._stringvar.get()
        string = ''.join([s for s in string if s.isdigit()])
        self._stringvar.set(string)

    @property
    def value(self):
        return self._stringvar.get()

    @value.setter
    def value(self, value):
        if not value and value is not 0:
            self._stringvar.set('')
            return
        self._stringvar.set(str(value))
        self._on_change_entry()

    def get(self):
        return self.value

    def set(self, item):
        self.value = item


class VesselLabelDoubleEntry(LabelDoubleEntry):

    def __init__(self, *args, **kwargs):
        if not kwargs.get('title'):
            kwargs['title'] = 'Vessel'
        super().__init__(*args, **kwargs)
        self._modify()

    def _modify(self):
        self._stringvar_first.set('Svea')
        self._stringvar_second.set('77SE')
        # self._stringvar_second.set('7710')

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


class SelectDirectory(tk.Frame, Common):

    def __init__(self,
                 parent,
                 id,
                 title='Directory',
                 width=40,
                 state='disabled',
                 **kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        self._id = id
        self.title = title
        self.width = width
        self.state = state

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=5,
                      sticky='nsew')
#        self.monospace_label = MonospaceLabel(self, text=self.title).grid(column=0, **layout)

        tk.Label(self, text=self.title).grid(row=0, column=0, padx=0, pady=5, sticky='w')
        self._stringvar = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self._stringvar, width=self.width)
        self.entry.grid(row=1, column=0, **layout)
        self.entry.configure(state=self.state)
        self.button = tk.Button(self, text='GET', command=self._on_button_pres)
        self.button.grid(row=1, column=1, **layout)

        tkw.grid_configure(self, nr_rows=2, nr_columns=2)

    def _on_button_pres(self):
        directory = filedialog.askdirectory()
        if not directory:
            return
        self._stringvar.set(directory)
        post_event(f'select_{self._id}')

    @property
    def directory(self):
        return self._stringvar.get()

    def get(self):
        return self.directory

    def set(self, path):
        path = Path(path)
        if not path.exists():
            return
        if path.is_file():
            path = path.parent
        self._stringvar.set(str(path))


class SelectedInstrumentTextFrame(tk.Frame, Common):

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

        self.controller = controller

        self._instrument_type = 'CTD'
        self.__instrument_name = ''

        self._stringvar = tk.StringVar()

        self.monospace_label = MonospaceLabel(self, textvariable=self._stringvar)
        self.monospace_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')

        subscribe('confirm_sensors', self.set)

    @property
    def instrument(self):
        return self.__instrument_name

    @instrument.setter
    def instrument(self, name):
        self.__instrument_name = name
        self._set_text()

    def _set_text(self):
        string = f'Vald {self._instrument_type}: {self.instrument} ({self.controller.get_instrument_serial_number(self.instrument)})'
        self._stringvar.set(string)

    def get(self):
        return self.instrument

    def set(self, item, **kwargs):
        self.instrument = item


class SelectedDefaultUserTextFrame(tk.Frame, Common):

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

        self.controller = controller

        self.user_selection_widget = None

        self._default_users = saves.get_default_users()

        self._stringvar = tk.StringVar()

        MonospaceLabel(self, text='Användare').grid(column=0, padx=5, pady=5, sticky='w')

        self.user_selection_widget = tkw.ComboboxWidget(self, items=self._default_users, row=0, column=1,
                                                        padx=5, pady=5, sticky='w')
        self.user_selection_widget.add_target(self._on_select_user)

    def _on_select_user(self, *args):
        user = self.user_selection_widget.get()
        post_event(f'select_default_user', user)

    def get(self):
        return self._stringvar.get()

    def set(self, item, **kwargs):
        if item not in self._default_users:
            return
        self._stringvar.set(item)


class SeriesEntryPicker(tk.Frame, Common):

    def __init__(self,
                 parent,
                 id,
                 width=10,
                 include_arrows=True,
                 title='Series',
                 **kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        self._id = id
        self.title = title

        if type(width) == int:
            self.width = [width, width]
        else:
            self.width = width[:2]

        self.include_arrows = include_arrows

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=5,
                      sticky='nsew')
        self.monospace_label = MonospaceLabel(self, text=self.title)
        self.monospace_label.grid(column=0, **layout)

        self._stringvar = tk.StringVar()
        self._stringvar.trace("w", lambda name, index, mode, sv=self._stringvar: self._on_change_entry(sv))

        self.entry = tk.Entry(self, textvariable=self._stringvar, width=self.width[0])
        self.entry.grid(row=0, column=1, ipady=2, **layout)
        self.entry.bind('<FocusOut>', self._on_focus_out)
        self.entry.bind('<Return>', self._on_return)
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
        string = self._stringvar.get()
        new_string = ''.join([s for s in string if s.isdigit()])
        self._stringvar.set(new_string[:4])

    def _on_focus_in(self, event=None):
        self.entry.selection_range(0, 'end')

    def _format_value(self):
        string = self._stringvar.get()
        print('_format_value', string)
        if not string:
            return
        num = int(''.join([s for s in string if s.isdigit()]))
        if num < 1:
            num = 1
        elif num > 9999:
            num = 9999
        new_string = str(num).zfill(4)
        self._stringvar.set(new_string)
        self.entry.update_idletasks()

    def _on_return(self, event=None):
        self._format_value()

    def _on_focus_out(self, event=None):
        self._format_value()
        post_event(f'focus_out_{self._id}', self._stringvar.get())

    def _on_button_down(self, event=None):
        string = self.value
        if not string:
            self.value = 9999
        else:
            self.value = int(string) - 1
        post_event('series_step', self.value)

    def _on_button_up(self, event=None):
        string = self.value
        if not string:
            self.value = 1
        else:
            num = int(string) + 1
            if num > 9999:
                num = 9999
            self.value = num
        post_event('series_step', self.value)

    @property
    def value(self):
        return self._stringvar.get().strip()

    @value.setter
    def value(self, value):
        print('value', value)
        self._stringvar.set(str(value).strip())
        self._format_value()

    def get(self):
        return self.value

    def set(self, item):
        self.value = item


class SurfaceSoakSelector(tk.Frame, Common):

    def __init__(self,
                parent,
                id,
                ** kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._id = id
        self.buttons = {}

        self._selected = None

        self.button_unselected_color = None
        self.button_selected_color = '#6bd688'

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=5,
                      sticky='nsew')
        self.monospace_label = MonospaceLabel(self, text='Soak')
        self.monospace_label.grid(column=0, **layout)
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
            post_event(f'select_{self._id}')

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

    def get(self):
        return self.surfacesoak

    def set(self, item):
        self.surfacesoak = item


class SensorTableOld(tk.Frame, Common):

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

        self._stringvar_instrument = tk.StringVar()
        self.combobox_instrument = ttk.Combobox(self, textvariable=self._stringvar_instrument, state="readonly")
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

        self._stringvar_par = []
        self._stringvar_sensor_id = []
        self._stringvar_status = []
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

            self._stringvar_par.append(par)
            self._stringvar_sensor_id.append(sensor_id)
            self._stringvar_status.append(status)
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
            self._stringvar_instrument.set(instrument)
            self._on_select_instrument()

    def _on_select_instrument(self, event=None):
        if not self._data:
            return
        self._current_instrument = self._stringvar_instrument.get()
        if self._current_instrument == 'All':
            self._current_instrument_data = self._data
        else:
            self._current_instrument_data = {}
            for key, value in self._data.items():
                if value.get('model') == self._current_instrument:
                    self._current_instrument_data[key] = value
        self._sort_by(self._current_sort_par)

    def _on_change_status(self, event, index):
        status = self._stringvar_status[index].get()
        sensor_id = self._stringvar_sensor_id[index].get()
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
            self._stringvar_par[i].set(self._data[_id]['parameter'])
            self._stringvar_sensor_id[i].set(self._data[_id]['sensor_id'])
            status = self._data[_id].get('status')
            if status == 'BAD':
                print('BAD')
            self._stringvar_status[i].set(status)

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
        self._stringvar_instrument.set(self._current_instrument)
        self._on_select_instrument()

    def _clear_widget(self):
        for i in range(len(self._stringvar_par)):
            self._stringvar_par[i].set('')
            self._stringvar_sensor_id[i].set('')
            self._stringvar_status[i].set('OK')
            self.combobox_status[i].configure(state='disabled')


class SensorTable(tk.Frame, Common):

    def __init__(self,
                parent,
                controller,
                ** kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self.controller = controller

        self._data = {}
        self._current_sort_par = None

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=2,
                      sticky='nsew')

        column_width = [30, 15]

        tk.Button(self, text='Parameter', width=column_width[0], command=lambda x='parameter': self._sort_by(x)).grid(row=0, column=0, **layout)
        tk.Button(self, text='Serial Number', width=column_width[1], command=lambda x='serial_number': self._sort_by(x)).grid(row=0, column=1, **layout)

        self._stringvar_par = []
        self._stringvar_serial_number = []

        for i in range(15):
            par = tk.StringVar()
            sensor_id = tk.StringVar()

            tk.Entry(self, textvariable=par, width=column_width[0], state='disabled').grid(row=i+1, column=0, **layout)
            tk.Entry(self, textvariable=sensor_id, width=column_width[1], state='disabled').grid(row=i+1, column=1, **layout)

            self._stringvar_par.append(par)
            self._stringvar_serial_number.append(sensor_id)

    def get(self):
        """
        :return: {'instrument: str,
                  'sort_par: str}
        """
        if not self._data:
            return {}
        return_info = {'sort_par': self._current_sort_par}
        return return_info

    def set(self, info):
        """
        Expects: {'instrument: str,
                  'sort: str}
        :return:
        """
        if not self._data:
            return
        self._current_sort_par = info.get('sort_par', 'serial_number')

    def _sort_by(self, key):
        self.update_data(sort_by=key)

    def update_data(self, data=None, sort_by=None):
        """
        :param data:
        :return:
        """
        if data:
            self._data = data[:]
        self._clear_widget()

        if not self._data:
            return

        if sort_by:
            self._current_sort_par = sort_by

        if self._current_sort_par:
            self._data = sorted(self._data, key=lambda x: x[self._current_sort_par])

        for i, info in enumerate(self._data):
            self._stringvar_par[i].set(info.get('parameter', ''))
            self._stringvar_serial_number[i].set(info.get('serial_number', ''))

    def reset_data(self):
        self._clear_widget()
        self._data = {}

    def _clear_widget(self):
        for i in range(len(self._stringvar_par)):
            self._stringvar_par[i].set('')
            self._stringvar_serial_number[i].set('')


class LabelCheckbox(tk.Frame, Common):

    def __init__(self,
                 parent,
                 id,
                 title='New station', 
                 **kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._id = id
        self.title = title

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=5,
                      sticky='nsew')

        self.intvar = tk.BooleanVar()
        self.checkbutton = tk.Checkbutton(self, variable=self.intvar, command=self._on_toggle)
        self.checkbutton.grid(row=0, column=0, **layout)

        self.monospace_label = MonospaceLabel(self, text=self.title)
        self.monospace_label.grid(column=1, **layout)

    def _on_toggle(self, *args):
        print(self.intvar.get())
        post_event(f'toggle_{self._id}', self.intvar.get())

    def get(self):
        return self.intvar.get()

    def set(self, state):
        self.intvar.set(state)


class PositionEntries(tk.Frame, Common):

    def __init__(self,
                 parent,
                 id,
                 width=8,
                 **kwargs):

        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        self._id = id

        if type(width) == int:
            self.width = [width, width]
        else:
            self.width = width[:2]

        super().__init__(parent)
        self.grid(**self.grid_frame)

        self._create_frame()

    def _create_frame(self):
        layout = dict(padx=5,
                      pady=5,
                      sticky='nsew')
        MonospaceLabel(self, text='Lat').grid(row=0, column=0, **layout)
        MonospaceLabel(self, text='Lon').grid(row=0, column=1, **layout)

        self._stringvar_lat = tk.StringVar()
        self._stringvar_lon = tk.StringVar()
        self._stringvar_lat.trace("w", lambda name, index, mode, sv=self._stringvar_lat: self._on_change_entry_lat(sv))
        self._stringvar_lon.trace("w", lambda name, index, mode, sv=self._stringvar_lon: self._on_change_entry_lon(sv))

        self.entry_lat = tk.Entry(self, textvariable=self._stringvar_lat, width=self.width[0])
        self.entry_lat.grid(row=1, column=0, **layout)
        self.entry_lat.config(state='disabled')

        self.entry_lon = tk.Entry(self, textvariable=self._stringvar_lon, width=self.width[1])
        self.entry_lon.grid(row=1, column=1, **layout)
        self.entry_lon.config(state='disabled')

        self.entry_lat.bind('<FocusOut>', self._on_focus_out_lat)
        self.entry_lat.bind('<Return>', self._on_return_lat)
        self.entry_lat.bind('<FocusIn>', self._on_focus_in_lat)

        self.entry_lon.bind('<FocusOut>', self._on_focus_out_lon)
        self.entry_lon.bind('<Return>', self._on_return_lon)
        self.entry_lon.bind('<FocusIn>', self._on_focus_in_lon)
        
        source_frame = tk.Frame(self)
        source_frame.grid(row=2, column=0, columnspan=2, sticky='w')
        tk.Label(source_frame, text='Position is:').grid(row=0, column=0, sticky='w')
        self._stringvar_source = tk.StringVar()
        tk.Label(source_frame, textvariable=self._stringvar_source).grid(row=0, column=1, sticky='w')
        
        tkw.grid_configure(self, nr_columns=2, nr_rows=2)

    def _on_change_entry_lat(self, *args):
        self._on_change_entry(self._stringvar_lat, self.entry_lat)

    def _on_change_entry_lon(self, *args):
        self._on_change_entry(self._stringvar_lon, self.entry_lon)

    def _on_change_entry(self, stringvar, entry):
        string = stringvar.get()
        new_string = ''.join([s for s in string if s.isdigit()][:6])
        stringvar.set(new_string)

    def _on_return_lat(self, event=None):
        # _on_focus out should be called here when switching focus
        self.entry_lon.focus_set()

    def _on_return_lon(self, event=None):
        self._on_focus_out_lon()
        post_event(f'return_{self._id}', [self.lat, self.lon])

    def _on_focus_in_lat(self, event=None):
        self.entry_lat.selection_range(0, 'end')

    def _on_focus_in_lon(self, event=None):
        self.entry_lon.selection_range(0, 'end')

    def _on_focus_out_lat(self, event=None):
        string = self._stringvar_lat.get()
        string_list = list(string)
        string_list.insert(2, '.')
        new_string = ''.join(string_list)
        self._stringvar_lat.set(new_string)

    def _on_focus_out_lon(self, event=None):
        string = self._stringvar_lon.get()
        string_list = list(string)
        string_list.insert(2, '.')
        new_string = ''.join(string_list)
        self._stringvar_lon.set(new_string)

    @property
    def lat(self):
        string = self._stringvar_lat.get()
        string_list = list(string)
        string_list.insert(4, '.')
        new_string = ''.join(string_list).strip('.')
        return new_string

    @lat.setter
    def lat(self, latitude):
        lat = str(latitude)
        if '.' in lat and lat[4] != '.':
            return
        self._stringvar_lat.set(lat)

    @property
    def lon(self):
        string = self._stringvar_lon.get()
        string_list = list(string)
        string_list.insert(4, '.')
        new_string = ''.join(string_list).strip('.')
        return new_string

    @lon.setter
    def lon(self, longitude):
        lon = str(longitude)
        if '.' in lon and lon[4] != '.':
            return
        self._stringvar_lon.set(lon)

    @property
    def source(self):
        return self._stringvar_source.get()

    @source.setter
    def source(self, source):
        self._stringvar_source.set(source)
            
    def get(self):
        return self.lat, self.lon

    def set(self, items):
        self.lat = items[0]
        self.lon = items[1]



