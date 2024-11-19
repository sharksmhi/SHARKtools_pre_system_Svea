import collections
import math
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

        subscribe('select_station', self._on_change_station)
        subscribe('focus_out_wadep', self.set_max_depth_to_autofire)
        subscribe('select_auto_fire_depth', self._validate_autofire_table)
        subscribe('select_auto_fire_bottle', self._validate_autofire_table)
        subscribe('select_auto_fire_bottle', self._validate_autofire_table)

    def _build_frame(self):

        use_auto_fire = tk.Frame(self)
        use_auto_fire.grid(row=0, column=0, sticky='nw')

        self._intvar_use_auto_fire = tk.IntVar()
        self._intvar_use_auto_fire.set(True)
        tk.Checkbutton(use_auto_fire, text='Använd Auto Fire', variable=self._intvar_use_auto_fire, command=self._on_toggle_auto_fire).grid()

        nr_btl_frame = tk.Frame(self)
        nr_btl_frame.grid(row=1, column=0, sticky='nw')

        tkw.grid_configure(self)
        tkw.grid_configure(use_auto_fire)
        tkw.grid_configure(nr_btl_frame)

        self._stringvar_nr_btl = tk.StringVar()

        tk.Radiobutton(nr_btl_frame, text='12 flaskor', variable=self._stringvar_nr_btl, value='12', command=self._on_change_nr_btl).grid(row=0, column=0)
        tk.Radiobutton(nr_btl_frame, text='24 flaskor', variable=self._stringvar_nr_btl, value='24', command=self._on_change_nr_btl).grid(row=0, column=1)

        self._stringvar_nr_btl.set('24')

        self._auto_fire_notebook = tkw.NotebookWidget(self, frames=['Tabell', 'Layout'], row=2, column=0)

        self._set_table_frame_layout(self._auto_fire_notebook.get_frame('Tabell'))
        self._set_canvas_layout(self._auto_fire_notebook.get_frame('Layout'))

    def _on_toggle_auto_fire(self, *args):
        if self._intvar_use_auto_fire.get():
            self._on_change_station()
        else:
            self._disable()

    def _disable(self):
        self._clear_table_frame_layout()
        self._canvas.clear_canvas()


    def _set_canvas_layout(self, frame):
        self._canvas = FrameAutoFireCanvas(frame, self.controller, self, row=0, column=0)

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

        nr_btl = int(self._stringvar_nr_btl.get())

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
        nr_btl = int(self._stringvar_nr_btl.get())
        for i in range(nr_btl):
            row_widgets = self._table_widgets[i]
            row_widgets['depth'].set_state('readonly')
            row_widgets['BottleNumber'].set_state('readonly')
            print(i, row_widgets['depth'].state)

    def _clear_table_frame_layout(self):
        for row_widgets in self._table_widgets:
            row_widgets['depth'].set_state('readonly')
            row_widgets['BottleNumber'].set_state('readonly')
            row_widgets['depth'].value = ''
            row_widgets['BottleNumber'].value = ''
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
        self._canvas.update_layout(self.get_data())

    def _update_table_with_default_data(self, nr_active_bottles: int = None):
        station = self.parent_frame.station
        if not station:
            return
        depth_list = [''] + [str(d) for d in sorted(self.controller.get_pressure_mapping_for_station(station))]
        info = self.controller.get_auto_fire_info_for_station(station, nr_active_bottles=nr_active_bottles)
        # for row_widgets, row_info in zip(self._table_widgets, info):
        for i, row_widgets in enumerate(self._table_widgets):
            if row_widgets['depth'].state == 'disabled':
                break
            row_widgets['depth'].values = depth_list
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
        #self._on_change_nr_btl(
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
            ))
        return data


class FrameAutoFireCanvas(tk.Frame):

    def __init__(self,
                 parent,
                 controller=None,
                 parent_frame=None,
                 circle_size=20,
                 canvas_width=400,
                 canvas_height=400,
                 bottle_radius=180,

                 **kwargs):
        self.grid_frame = {'padx': 5,
                           'pady': 5,
                           'sticky': 'nsew'}
        self.grid_frame.update(kwargs)

        super().__init__(parent)

        self.controller = controller
        self.parent_frame = parent_frame
        self._circle_size = circle_size
        self._canvas_width = canvas_width
        self._canvas_height = canvas_height
        self._bottle_radius = bottle_radius

        self.grid(**self.grid_frame)

        self._build_frame()

    def _build_frame(self):
        self.canvas = tk.Canvas(self, width=self._canvas_width, height=self._canvas_height, borderwidth=0, highlightthickness=0, bg="white", )
        self.canvas.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

    def clear_canvas(self):
        self.canvas.delete("all")

    def _create_circle(self, x, y, r, text='', **kwargs):  # center coordinates, radius
        x0 = x - r
        y0 = y - r
        x1 = x + r
        y1 = y + r
        oval = self.canvas.create_oval(x0, y0, x1, y1, **kwargs)
        if text:
            self.canvas.create_text(x, y, anchor="center")
            self.canvas.create_text(x, y, font=("Purisa", 24), text=text)

    def update_layout(self, table_data: list[dict[str, int]], nr_bottles: int = 24):
        self.clear_canvas()
        print(f'{table_data=}')
        index_mapping = {int(item['BottleNumber']): item for item in table_data}
        colors = get_colors(len(table_data))
        print(colors)
        color_index = 0
        for i, (x, y) in enumerate(get_coordinates(nr_bottles, radius=self._bottle_radius)):
            data = index_mapping.get(i+1)
            if data:
                self._create_circle(x, y, self._circle_size, text=str(i+1), fill=colors[color_index])
                color_index += 1
            else:
                self._create_circle(x, y, self._circle_size, text=str(i+1))
