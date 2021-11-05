"""
This module is an example of a barebones QWidget plugin for napari

It implements the ``napari_experimental_provide_dock_widget`` hook specification.
see: https://napari.org/docs/dev/plugins/hook_specifications.html

Replace code below according to your needs.
"""
from napari_plugin_engine import napari_hook_implementation
from qtpy.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFileDialog
from magicgui import magic_factory

import sqlite3
import pandas as pd

class CistemProject():

    def __init__(self, dbfile):
        print(dbfile)
        con = sqlite3.connect(dbfile)
        self.image_asset_data = pd.read_sql_query("SELECT * FROM IMAGE_ASSETS",con)
        con.close

class ExampleQWidget(QWidget):
    # your QWidget.__init__ can optionally request the napari viewer instance
    # in one of two ways:
    # 1. use a parameter called `napari_viewer`, as done here
    # 2. use a type annotation of 'napari.viewer.Viewer' for any parameter
    cistem_project : CistemProject = None

    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        cistem_open_btn = QPushButton("Open cisTEM project")
        cistem_open_btn.clicked.connect(self._on_cistem_open_click)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(cistem_open_btn)

    def _on_cistem_open_click(self):
        db_filename = str(QFileDialog.getOpenFileName(self, 'Open file', None,"cisTEM database (*.db)"))
        self.cistem_project = CistemProject(db_filename)
        print(self.cistem_project.image_asset_data)


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    return [ExampleQWidget]
