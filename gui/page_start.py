#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import tkinter as tk
from sharkpylib.tklib import tkinter_widgets as tkw

from . import frames


from pre_system_svea.controller import Controller
from file_explorer.seabird.paths import SBEPaths

from ..events import subscribe


class PageStart(tk.Frame):

    def __init__(self, parent, parent_app, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        # parent is the frame "container" in App. controller is the App class
        self.parent = parent
        self.parent_app = parent_app

        self._station_instruments = ['SBE09', 'SBE19']
        self._transect_instruments = ['MVP200', 'Triaxus']

        self._current_instrument = None

        self.sbe_paths = SBEPaths()
        self.controller = Controller(paths_object=self.sbe_paths)

    def _add_subscribers(self):
        subscribe('select_instrument', self._on_select_instrument)
        subscribe('confirm_sensors', self._on_confirm_sensors, before=True)

    @property
    def user(self):
        return self.parent_app.user

    def startup(self):
        self._create_frame()
        self._add_subscribers()
        try:
            self.controller.ctd_config_root_directory = self._frame_select_instrument.config_root_directory
            self.controller.ctd_data_root_directory = self._frame_select_instrument.data_root_directory_local
        except FileNotFoundError:
            pass

    def close(self):
        self._frame_manage_ctd_casts.save_selection()
        self._frame_select_instrument.save_selection()

    def update_page(self):
        pass

    def _create_frame(self):

        self.notebook = tkw.NotebookWidget(self, frames=['Välj CTD', 'Försystem (Inför station / På station)'], place=(.5, .5))
        self.notebook.set_state('normal', 'Välj CTD', rest='disabled')
        layout = dict(padx=20, pady=20, sticky='nsew')

        self._frame_select_instrument = frames.FrameSelectInstrument(self.notebook.get_frame('Välj CTD'), self.controller)
        self._frame_select_instrument.grid(row=0, column=0, **layout)

        self._update_frame_manage_ctd_casts()

        self.notebook.select_frame('Välj CTD')

    def _update_frame_manage_ctd_casts(self):
        frame = self.notebook.get_frame('Försystem (Inför station / På station)')
        layout = dict(padx=10, pady=10, sticky='nsew')

        try:
            self._frame_manage_ctd_casts.destroy()
        except:
            pass

        if self._current_instrument in self._station_instruments:
            self._frame_manage_ctd_casts = frames.FrameManageCTDcastsStation(frame, self.controller)
            self._frame_manage_ctd_casts.grid(row=0, column=1, **layout)
            self._frame_manage_ctd_casts.instrument = self._current_instrument

        elif self._current_instrument in self._transect_instruments:
            self._frame_manage_ctd_casts = frames.FrameManageCTDcastsTransect(frame, self.controller)
            self._frame_manage_ctd_casts.grid(row=1, column=1, **layout)
            self._frame_manage_ctd_casts.instrument = self._current_instrument

        else:
            self._frame_manage_ctd_casts = frames.FrameManageCTDcastsStation(frame, self.controller)
            self._frame_manage_ctd_casts.grid(row=0, column=1, **layout)

    def _on_select_instrument(self, *args):
        self.notebook.set_state('disabled', 'Försystem (Inför station / På station)')

    def _on_confirm_sensors(self, *args):
        from ..events import nr_subscribers
        print('aa', nr_subscribers('confirm_sensors'))
        instrument = self._frame_select_instrument.instrument
        print('bb', nr_subscribers('confirm_sensors'))
        if not instrument:
            return
        if instrument == self._current_instrument:
            self.notebook.set_state('normal', 'Försystem (Inför station / På station)')
            self.notebook.select_frame('Försystem (Inför station / På station)')
            return
        self._current_instrument = instrument
        print('cc', nr_subscribers('confirm_sensors'))
        self._update_frame_manage_ctd_casts()
        print('dd', nr_subscribers('confirm_sensors'))

        self.notebook.set_state('normal', 'Försystem (Inför station / På station)')
        self.notebook.select_frame('Försystem (Inför station / På station)')
        print('xx', nr_subscribers('confirm_sensors'))

