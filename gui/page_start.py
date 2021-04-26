#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import tkinter as tk
from tkinter import ttk
from sharkpylib.tklib import tkinter_widgets as tkw

from . import frames

from pathlib import Path

from . import components

from ctd_processing.sensor_info import InstrumentFile


class PageStart(tk.Frame):

    def __init__(self, parent, parent_app, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        # parent is the frame "container" in App. controller is the App class
        self.parent = parent
        self.parent_app = parent_app

        self._station_instruments = ['SBE09', 'SBE19']
        self._transect_instruments = ['MVP200', 'Triaxus']

        self._current_instrument = None

    @property
    def user(self):
        return self.parent_app.user

    def startup(self):
        self._create_frame()

    def close(self):
        self._frame_manage_ctd_casts.save_selection()
        self._frame_start_up.save_selection()

    def update_page(self):
        file_path = Path(Path(__file__).parent.parent, 'temp_files','Instruments.xlsx')
        instrument = InstrumentFile(file_path)
        self._frame_start_up.update_sbe_instrument_info(instrument.sbe_instrument_info)

    def _create_frame(self):

        self.notebook = tkw.NotebookWidget(self, frames=['Välj CTD', 'Uppstart ombord', 'Försystem (Inför station / På station)'], place=(.5, .5))
        layout = dict(padx=20, pady=20, sticky='nsew')

        self._frame_select_instrument = frames.FrameSelectInstrument(self.notebook.get_frame('Välj CTD'))
        self._frame_select_instrument.grid(row=0, column=0, **layout)
        self._frame_select_instrument.add_callback_instrument_select(self._on_instrument_select)
        self._frame_select_instrument.set_frame_color('green')

        self._frame_start_up = frames.FrameStartUp(self.notebook.get_frame('Uppstart ombord'))
        self._frame_start_up.grid(row=0, column=0, **layout)

        self._update_frame_manage_ctd_casts()

        self._on_instrument_select('SBE09')

    def _update_frame_manage_ctd_casts(self):
        frame = self.notebook.get_frame('Försystem (Inför station / På station)')
        layout = dict(padx=10, pady=10, sticky='nsew')

        try:
            self._frame_manage_ctd_casts.destroy()
        except:
            pass

        if self._current_instrument in self._station_instruments:
            self._frame_manage_ctd_casts = frames.FrameManageCTDcastsStation(frame)
            self._frame_manage_ctd_casts.grid(row=0, column=1, **layout)
            self._frame_manage_ctd_casts.instrument = 'SBE09'

        elif self._current_instrument in self._transect_instruments:
            self._frame_manage_ctd_casts = frames.FrameManageCTDcastsTransect(frame)
            self._frame_manage_ctd_casts.grid(row=1, column=1, **layout)
            self._frame_manage_ctd_casts.instrument = 'MVP200'
            # self._frame_manage_ctd_casts.set_frame_color('green')

    def _on_instrument_select(self, instrument):
        if instrument == self._current_instrument:
            return
        self._current_instrument = instrument

        self._update_frame_manage_ctd_casts()

        self._frame_select_instrument.instrument = instrument
        self._frame_manage_ctd_casts.instrument = instrument
        self._frame_start_up.instrument = instrument

