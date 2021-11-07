"""
This module is an example of a barebones QWidget plugin for napari

It implements the ``napari_experimental_provide_dock_widget`` hook specification.
see: https://napari.org/docs/dev/plugins/hook_specifications.html

Replace code below according to your needs.
"""
from napari_plugin_engine import napari_hook_implementation
from qtpy.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFileDialog
from napari.utils.events import EventedModel
from napari.utils.events.custom_types import Array
from dask import delayed
import dask.array as da

from pydantic import Field
import typing
import mrcfile
import numpy as np

import sqlite3
import pandas as pd


def read_and_resize_mrc(filename, x, y):
    with mrcfile.open(filename,"r") as mrc:
        data = mrc.data
    if len(data.shape) == 3:
        data = data[0]
    if data.shape[0] != y or data.shape[1] != x:
        data = np.pad(data, pad_with = [y-data.shape[0],x-data.shape[1]])
    return(data)


class CistemProjectModel(EventedModel):
    dbfile: str = None
    image_asset_data: Array = None
    class Config:
        arbitrary_types_allowed = True




class CistemProjectManager():
    def __init__(self,model,viewer):
        self.model = model
        self.viewer = viewer
        model.events.dbfile.connect(self._on_dbfile)
        model.events.image_asset_data.connect(self._on_image_assets)
    
    def _on_dbfile(self, event):
        con = sqlite3.connect(event.value)
        
        data = pd.read_sql_query("SELECT * FROM IMAGE_ASSETS",con)
        self.model.image_asset_data = data.to_records()
        con.close

    def _on_image_assets(self, event):
        df = event.value
        x_size = df["X_SIZE"].max()
        y_size = df["Y_SIZE"].max()
        dtype=float
        lazy_imread = delayed(read_and_resize_mrc)  # lazy reader
        lazy_arrays = [lazy_imread(fn,x_size,y_size) for fn in df["FILENAME"]]
        dask_arrays = [
            da.from_delayed(delayed_reader, shape=(y_size,x_size), dtype=dtype)
            for delayed_reader in lazy_arrays
        ]
        # Stack into one large dask.array
        stack = da.stack(dask_arrays, axis=0)
        self.viewer.add_image(stack)




class CistemWidget(QWidget):
    # your QWidget.__init__ can optionally request the napari viewer instance
    # in one of two ways:
    # 1. use a parameter called `napari_viewer`, as done here
    # 2. use a type annotation of 'napari.viewer.Viewer' for any parameter
    cistem_project : CistemProjectModel = None
    cistem_project_manager: CistemProjectManager = None

    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        cistem_open_btn = QPushButton("Open cisTEM project")
        cistem_open_btn.clicked.connect(self._on_cistem_open_click)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(cistem_open_btn)
        self.cistem_project = CistemProjectModel()
        self.cistem_project_manager = CistemProjectManager(model=self.cistem_project, viewer = napari_viewer)

    def _on_cistem_open_click(self):
        db_filename = str(QFileDialog.getOpenFileName(self, 'Open file', None,"cisTEM database (*.db)")[0])
        self.cistem_project.dbfile = db_filename


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    widget_options = {
        "name": "cisTEM",
        "add_vertical_stretch": False,
        "area": 'left',
    }
    return CistemWidget, widget_options
