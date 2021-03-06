import os
import webbrowser

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import resources

from .qgis_utils.utils import create_action
from qProf_QWidget import qprof_QWidget

_plugin_name_ = "qProf"


class qProf_main(object):

    def __init__(self, interface):

        self.plugin_name = _plugin_name_
        self.interface = interface
        self.main_window = self.interface.mainWindow()
        self.canvas = self.interface.mapCanvas()

        self.actions = []

    def initGui(self):

        self.qactOpenMainWin = create_action(
            ":/plugins/{}/icons/qprof.png".format(self.plugin_name),
            self.plugin_name,
            self.open_qprof,
            whats_this="Topographic and geological profiles",
            parent=self.interface.mainWindow())
        self.interface.addPluginToMenu(self.plugin_name,
                                       self.qactOpenMainWin)
        self.actions.append(self.qactOpenMainWin)

        self.qactOpenHelp = create_action(
            ':/plugins/{}/icons/help.ico'.format(self.plugin_name),
            'Help',
            self.open_html_help,
            whats_this="Topographic and geological profiles Help",
            parent=self.interface.mainWindow())
        self.actions.append(self.qactOpenHelp)
        self.interface.addPluginToMenu(self.plugin_name,
                                       self.qactOpenHelp)

    def unload(self):

        self.interface.removePluginMenu(self.plugin_name, self.qactOpenMainWin)
        self.interface.removePluginMenu(self.plugin_name, self.qactOpenHelp)

    def open_qprof(self):

        qprof_DockWidget = QDockWidget(self.plugin_name,
                                       self.interface.mainWindow())
        qprof_DockWidget.setAttribute(Qt.WA_DeleteOnClose)
        qprof_DockWidget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.qProf_QWidget = qprof_QWidget(self.plugin_name,
                                           self.canvas)
        qprof_DockWidget.setWidget(self.qProf_QWidget)
        qprof_DockWidget.destroyed.connect(self.qProf_QWidget.closeEvent)
        self.interface.addDockWidget(Qt.RightDockWidgetArea, qprof_DockWidget)

    def open_html_help(self):

        webbrowser.open('{}/help/help.html'.format(os.path.dirname(__file__)), new=True)
