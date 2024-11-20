import collections
import math
import re
import tkinter as tk
from tkinter import ttk

from shark_tkinter_lib import tkinter_widgets as tkw

from . import components
from ..events import subscribe

COLORS = [
    '#1D9A6C',
    '#249E73',
    '#2BA27A',
    '#32A681',
    '#39A988',
    '#41AD8F',
    '#48B195',
    '#4FB49B',
    '#56B8A2',
    '#5EBCA8',
    '#65BFAE',
    '#6CC3B3',
    '#74C6B9',
    '#7BCABE',
    '#83CDC4',
    '#8AD0C9',
    '#92D4CE',
    '#99D7D3',
    '#A1DAD7',
    '#A9DEDC',
    '#B0E1E0',
    '#B8E4E4',
    '#C0E7E7',
    '#C8E9EA',
    '#CFECED',
]


def get_colors(nr_bottles: int):
    tot_nr_colors = len(COLORS)
    if not nr_bottles:
        nr_bottles = 1
    steps = tot_nr_colors // nr_bottles
    return_colors = []
    index = []
    for i, c in enumerate(COLORS):
        #if i == 0:
        #    continue
        if i % steps:
            continue
        return_colors.append(c)
        index.append(i)
    return return_colors


def get_coordinates(nr_bottles: int, radius: int = 180, offset: int = 20) -> list[tuple[int, int]]:
    coords = []
    section_size = 2 * math.pi / nr_bottles
    for n in range(nr_bottles):
        co = int(math.cos(section_size*n) * radius + (radius + offset))
        si = int(math.sin(section_size*n) * radius + (radius + offset))
        coords.append((co, si))
    return coords


class FrameAutoFire(tk.Frame):

    def __init__(self,
                 parent,
                 controller=None,
                 parent_frame= None,
                 **kwargs):
        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        super().__init__(parent)

        self.controller = controller
        self.parent_frame = parent_frame
        self.instrument = None
        self._max_depth = None

        self.grid(**self.grid_frame)

        self._build_frame()

        subscribe('confirm_sensors', self._on_confirm_sensors)
        subscribe('select_station', self._on_change_station)
        subscribe('focus_out_wadep', self.set_max_depth_to_autofire)
        subscribe('select_auto_fire_depth', self._validate_autofire_table)
        subscribe('select_auto_fire_bottle', self._validate_autofire_table)
        subscribe('select_auto_fire_bottle', self._validate_autofire_table)

    def _build_frame(self):

        use_auto_fire = tk.Frame(self)
        use_auto_fire.grid(row=0, column=0, sticky='nw')

        nr_btl_frame = tk.Frame(self)
        nr_btl_frame.grid(row=1, column=0, sticky='nw')

        option_frame = tk.Frame(self)
        option_frame.grid(row=2, column=0, sticky='nw')

        option_label_frame = tk.Frame(option_frame)
        option_label_frame.grid(row=0, column=0, sticky='w')

        option_entry_frame = tk.Frame(option_frame)
        option_entry_frame.grid(row=0, column=1, sticky='w')

        self._auto_fire_notebook = tkw.NotebookWidget(self, frames=['Tabell', 'Layout'], row=4, column=0)

        self._intvar_use_auto_fire = tk.IntVar()
        self._intvar_use_auto_fire.set(True)
        tk.Checkbutton(use_auto_fire, text='Använd Auto Fire', variable=self._intvar_use_auto_fire, command=self._on_toggle_auto_fire).grid()

        self._stringvar_nr_btl = tk.StringVar()

        tk.Radiobutton(nr_btl_frame, text='12 flaskor', variable=self._stringvar_nr_btl, value='12', command=self._on_change_nr_btl).grid(row=0, column=0)
        tk.Radiobutton(nr_btl_frame, text='24 flaskor', variable=self._stringvar_nr_btl, value='24', command=self._on_change_nr_btl).grid(row=0, column=1)
        self._stringvar_nr_btl.set('24')

        tk.Label(option_label_frame, text='Offset (db):').grid(row=0, column=0, sticky='w')
        tk.Label(option_label_frame, text='Minimum tryck för auto fire:').grid(row=1, column=0, sticky='w')

        self._offset = tkw.EntryWidget(option_entry_frame, callback_on_change_value=self._on_change_offset, prop_entry=dict(width=10), row=0, column=0)
        self._offset.set_value(0)

        self._min_pres = tkw.EntryWidget(option_entry_frame, callback_on_change_value=self._on_change_min_pres,
                                       prop_entry=dict(width=10), row=1, column=0)

        self._set_table_frame_layout(self._auto_fire_notebook.get_frame('Tabell'))
        self._set_canvas_layout(self._auto_fire_notebook.get_frame('Layout'))

        tkw.grid_configure(self)
        tkw.grid_configure(use_auto_fire)
        tkw.grid_configure(nr_btl_frame)

    @property
    def nr_bottles(self) -> int:
        return int(self._stringvar_nr_btl.get())

    @property
    def offset(self) -> float:
        value = self._offset.get_value().strip()
        if not value:
            return 0
        return float(value)

    def _on_confirm_sensors(self, *args):
        self._min_pres.set_value(self.controller.auto_fire_min_pressure_or_depth)

    def _on_change_offset(self, *args):
        value = self._offset.get_value().strip().replace(',', '.')
        new_value_list = []
        for d in list(value):
            if d.isdigit():
                new_value_list.append(d)
            elif d == '.' and '.' not in new_value_list:
                new_value_list.append(d)
        self._offset.set_value(''.join(new_value_list))

    def _on_change_min_pres(self, *args):
        value = self._min_pres.get_value().strip().replace(',', '.')
        new_value_list = []
        for d in list(value):
            if d.isdigit():
                new_value_list.append(d)
            elif d == '.' and '.' not in new_value_list:
                new_value_list.append(d)
        self._min_pres.set_value(''.join(new_value_list))

    def _on_toggle_auto_fire(self, *args):
        if not self.parent_frame.station:
            return
        if self._intvar_use_auto_fire.get():
            self._on_change_station()
            self.set_max_depth_to_autofire()
        else:
            self._disable()

    def _disable(self):
        self._clear_table_frame_layout()
        self._canvas.clear_canvas()

    def _set_canvas_layout(self, frame):
        # self._canvas = FrameAutoFireCanvas(frame, self.controller, self, row=0, column=0)
        self._canvas = FrameAutoFireCanvas(frame, row=0, column=0)

    def _set_table_frame_layout(self, frame):

        self._table_frame = tk.Frame(frame)
        self._table_frame.grid(row=0, column=0, sticky='nw')
        tkw.grid_configure(self._table_frame)

        label_row = tk.Frame(self._table_frame)
        label_row.grid(row=0, column=0)
        self.DEFAULT_FRAME_COLOR = label_row.cget('bg')
        tk.Label(label_row, text='Djup / Flasknummer').grid(row=0, column=0)

        layout = dict(padx=3, pady=0, sticky='nwse')

        self._table_widgets = []

        nr_btl = self.nr_bottles

        c = 0
        r = 0
        for i in range(24):
            state = 'readonly'
            row_frame = tk.Frame(self._table_frame)
            row_frame.grid(row=r+1, column=c)
            depth = components.DropdownList(row_frame, 'auto_fire_depth', state=state, row=0, column=0, **layout)
            bottle = components.DropdownList(row_frame, 'auto_fire_bottle', state=state, row=0, column=1, **layout)
            bottle.values = [''] + [str(i) for i in range(1, nr_btl+1)]

            row_widgets = dict(
                depth=depth,
                BottleNumber=bottle,
                row=row_frame
            )
            self._table_widgets.append(row_widgets)
            r += 1
            if i == 11:
                ttk.Separator(self._table_frame, orient='vertical').grid(row=0, column=2, sticky='ns', rowspan=13)
                c = 1
                r = 0
                label_row = tk.Frame(self._table_frame)
                label_row.grid(row=0, column=c)
                tk.Label(label_row, text='Djup / flasknummer').grid(row=0, column=0, sticky='w')
                tkw.grid_configure(label_row)

    def _update_table_frame_layout(self):
        self._clear_table_frame_layout()
        nr_btl = self.nr_bottles
        for i in range(nr_btl):
            row_widgets = self._table_widgets[i]
            row_widgets['depth'].set_state('readonly')
            row_widgets['BottleNumber'].set_state('readonly')

    def _clear_table_frame_layout(self):
        bottle_list = [''] + [str(i) for i in range(1, self.nr_bottles+1)]
        depth_list = ['']
        if self.parent_frame.station:
            depth_list = depth_list + [str(d) for d in sorted(self.controller.get_pressure_mapping_for_station(self.parent_frame.station))]

        for row_widgets in self._table_widgets:
            row_widgets['depth'].set_state('readonly')
            row_widgets['BottleNumber'].set_state('readonly')

            row_widgets['depth'].value = ''
            row_widgets['BottleNumber'].value = ''

            row_widgets['depth'].values = depth_list[:]
            row_widgets['BottleNumber'].values = bottle_list[:]

            row_widgets['depth'].set_state('disabled')
            row_widgets['BottleNumber'].set_state('disabled')

    def _on_change_station(self, *args):
        self._on_change_nr_btl()

    def _on_change_nr_btl(self, *args):
        self._set_default_table_data()
        self._update_canvas_layout()

    def _set_default_table_data(self, *args):
        self._update_table_frame_layout()
        self._update_table_with_default_data()

    def _update_canvas_layout(self):
        self._canvas.update_layout(self.get_data(), nr_bottles=self.nr_bottles)

    def _update_table_with_default_data(self, nr_active_bottles: int = None):
        station = self.parent_frame.station
        if not station:
            return
        info = self.controller.get_auto_fire_info_for_station(station, nr_active_bottles=nr_active_bottles, nr_bottles=self.nr_bottles)
        for i, row_widgets in enumerate(self._table_widgets):
            if row_widgets['depth'].state == 'disabled':
                break
            try:
                row_info = info[i]
                row_widgets['depth'].value = row_info['depth']
                row_widgets['BottleNumber'].value = row_info['BottleNumber']
            except IndexError:
                pass

    def _validate_autofire_table(self, *args):
        if not self._intvar_use_auto_fire.get():
            return
        all_bottles = [item['BottleNumber'] for item in self.get_data()]
        # all_bottles = [row_widgets['BottleNumber'].value for row_widgets in self._table_widgets if (row_widgets['BottleNumber'].value and row_widgets['depth'].value)]
        dublicates = [k for k, v in collections.Counter(all_bottles).items() if v > 1]
        for row_widgets in self._table_widgets:
            color = self.DEFAULT_FRAME_COLOR
            if row_widgets['BottleNumber'].value in dublicates:
                color = 'red'
            row_widgets['row'].config(bg=color)
        self._canvas.clear_canvas()
        if not dublicates:
            self._update_canvas_layout()

    def set_max_depth_to_autofire(self, depth: str | int = None) -> None:
        if depth is None:
            depth = self._max_depth
        if not depth:
            return
        self._set_default_table_data()
        max_depth = int(depth)
        nr_active_bottles = 0
        for item in self._table_widgets:
            if not item['depth'].value:
                continue
            if int(item['depth'].value) >= max_depth:
                continue
            nr_active_bottles += 1
        self._update_table_with_default_data(nr_active_bottles=nr_active_bottles)
        for row_widgets in self._table_widgets:
            if not row_widgets['depth'].value:
                continue
            if int(row_widgets['depth'].value) >= max_depth:
                row_widgets['depth'].value = ''
                row_widgets['BottleNumber'].value = ''
                row_widgets['row'].config(bg=None)
        self._max_depth = max_depth
        self._update_canvas_layout()

    def get_data(self) -> list[dict[str, int]]:
        data = []
        for row_widgets in self._table_widgets:
            depth = row_widgets['depth'].value
            bottle = row_widgets['BottleNumber'].value
            if not (depth and bottle):
                continue
            data.append(dict(
                depth=depth,
                BottleNumber=bottle,
                offset=self.offset
            ))
        return data

    def clear_frame(self):
        self._clear_table_frame_layout()
        self._canvas.clear_canvas()

    @property
    def enable_auto_fire(self) -> bool:
        return bool(self._intvar_use_auto_fire.get())

    @property
    def auto_fire_min_pressure_or_depth(self) -> str:
        return self._min_pres.get_value()


class FrameAutoFireCanvas(tk.Frame):

    def __init__(self,
                 parent,
                 # controller=None,
                 # parent_frame=None,
                 circle_size: int = 20,
                 canvas_width: int = 381,
                 # canvas_width: int = 400,
                 canvas_height: int = 381,
                 # canvas_height: int = 400,
                 bottle_radius: int = 180,
                 scale: int | float = 1,
                 include_option_large: bool = True,
                 **kwargs):
        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        super().__init__(parent)

        # self.controller = controller
        # self.parent_frame = parent_frame
        # self._circle_size = circle_size
        # self._canvas_width = canvas_width
        # self._canvas_height = canvas_height
        # self._bottle_radius = bottle_radius

        self._circle_size = int(circle_size * scale)
        self._canvas_width = int(canvas_width * scale) + self._circle_size
        self._canvas_height = int(canvas_height * scale) + self._circle_size
        self._bottle_radius = int(bottle_radius * scale)

        self._include_option_large = include_option_large

        self.grid(**self.grid_frame)

        self._current_table_data: list[dict[str, int]] = []
        self._current_nr_bottles: int | None = None
        self._toplevel: tk.Toplevel | None = None

        self._build_frame()

    def _build_frame(self):
        self.canvas = tk.Canvas(self, width=self._canvas_width, height=self._canvas_height, borderwidth=0, highlightthickness=0, bg="white", )
        # self.canvas.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.canvas.grid(column=0, row=0, sticky='nsew')
        if self._include_option_large:
            option_frame = tk.Frame(self)
            option_frame.grid(column=0, row=1, sticky='nsew')
            tk.Label(option_frame, text='Skala upp:').grid(column=0, row=0)
            self._scale = tk.Scale(option_frame,
                                   # label='Skala upp...',
                                   from_=1, to=3.5, orient=tk.HORIZONTAL,
                                   # length=100,
                                   tickinterval=2, resolution=0.1)
            self._scale.grid(column=1, row=0, sticky='nsew')
            self._scale.set(2.4)
            tk.Button(option_frame, text='Öppna uppskalad vy', command=self._open_large_canvas).grid(column=2, row=0)

    def clear_canvas(self):
        self.canvas.delete("all")
        self._current_table_data = []
        self._current_nr_bottles = None
        if self._toplevel:
            self._toplevel.destroy()
            self._toplevel = None

    def _add_circle(self, x, y, r, text='', **kwargs):  # center coordinates, radius
        x0 = x - r
        y0 = y - r
        x1 = x + r
        y1 = y + r
        oval = self.canvas.create_oval(x0, y0, x1, y1, **kwargs)
        if text:
            self.canvas.create_text(x, y, anchor="center")
            self.canvas.create_text(x, y, font=("Purisa", 24), text=text)

    def _add_text(self, x, y, text='', text_size=12):  # center coordinates, radius
        self.canvas.create_text(x, y, anchor="center")
        self.canvas.create_text(x, y, font=("Purisa", text_size), text=text)

    def update_layout(self, table_data: list[dict[str, int]], nr_bottles: int = 24):
        self.clear_canvas()

        self._current_table_data = table_data
        self._current_nr_bottles = nr_bottles

        unique_depths = sorted([int(item['depth']) for item in table_data], reverse=True)
        colors = get_colors(len(unique_depths))
        depth_color_mapping = dict(zip(unique_depths, colors))

        index_mapping = {int(item['BottleNumber']): item for item in table_data}
        color_index = 0
        # text_coordinates = get_coordinates(nr_bottles, radius=self._bottle_radius - 40, offset=60)
        text_coordinates = get_coordinates(nr_bottles, radius=int(self._bottle_radius * 0.79), offset=int(self._circle_size * 3))
        for i, (x, y) in enumerate(get_coordinates(nr_bottles, radius=self._bottle_radius, offset=self._circle_size)):
            data = index_mapping.get(i+1)
            if data:
                self._add_circle(x, y, self._circle_size, text=str(i+1), fill=depth_color_mapping[int(data['depth'])])
                tx, ty = text_coordinates[i]
                self._add_text(tx, ty, text=str(data['depth']))
                # self._add_circle(x, y, self._circle_size, text=str(i+1), fill=colors[color_index])
                color_index += 1
            else:
                self._add_circle(x, y, self._circle_size, text=str(i+1))

    def _open_large_canvas(self):
        if not self._current_table_data:
            return
        if self._toplevel:
            return
        self._toplevel = tk.Toplevel()
        self._toplevel.resizable(False, False)
        canvas_frame = FrameAutoFireCanvas(
            self._toplevel,
            # scale=2.4,
            scale=float(self._scale.get()),
            include_option_large=False
        )
        canvas_frame.update_layout(self._current_table_data, nr_bottles=self._current_nr_bottles)

