#!/usr/bin/env python3
# coding=utf-8
#
# Copyright (c) 2021 Antonio González

from PyQt5 import (QtCore, QtGui, QtWidgets)
from datetime import datetime
from itertools import count
from serial import Serial, SerialException
from serial.tools import list_ports
import numpy as np
import os
import pyqtgraph as pg
import sys
import time

from ui.ui_main import Ui_MainWindow
from ui.ui_settings_dlg import Ui_Dialog

# GUI parameters
GUI_REFRESH_RATE = 100 #  In milliseconds
WIN_WIDTH_SAMPLES = 500

# Serial parameters
BAUD_DEFAULT = 115200
#PORT_DEFAULT = "/dev/ttyACM0"
BAUD_RATES = (460800, 115200, 57600, 38400, 19200, 14400, 9600)


MAIN_NROWS = 3
(BAUD, PORT, SAVE_PATH) = range(MAIN_NROWS)


class SettingsDialog(QtWidgets.QDialog, Ui_Dialog):
    """
    Data acquisition main window
    """
    def __init__(self, settings, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.settings = settings
        #self._gui_refresh_rate = GUI_REFRESH_RATE

        # Baud
        baud_rates = [str(baud) for baud in BAUD_RATES]
        baud_model = QtCore.QStringListModel(baud_rates, self)
        self.baudComboBox.setModel(baud_model)

        # Ports
        ports_str = [port.device for port in self.settings.available_ports]
        ports_model = QtCore.QStringListModel(ports_str, self)
        self.portComboBox.setModel(ports_model)

        # Default save path
        self.savePathLabel.setText(self.settings.save_path)

        # Setup model
        main_settings_model = MainSettingsModel(self.settings)
        mapper = QtWidgets.QDataWidgetMapper(self)
        mapper.setOrientation(QtCore.Qt.Vertical)
        mapper.setModel(main_settings_model)
        mapper.addMapping(self.baudComboBox, BAUD)
        mapper.addMapping(self.portComboBox, PORT)
        mapper.addMapping(self.savePathLabel, SAVE_PATH)
        mapper.toFirst()

    @QtCore.pyqtSlot()
    def on_savePathButton_clicked(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, caption='Select default data directory')
        if path:
            self.settings.save_path = path
            self.savePathLabel.setText(path)
    
    @QtCore.pyqtSlot()
    def on_portRefreshButton_clicked(self):
        self.settings.scan_ports()
        ports_str = [port.device for port in self.settings.available_ports]
        ports_model = QtCore.QStringListModel(ports_str, self)
        self.portComboBox.setModel(ports_model)


class MainSettingsModel(QtCore.QAbstractListModel):
    def __init__(self, settings, parent=None):
        super(MainSettingsModel, self).__init__(parent)
        self.settings = settings

    def rowCount(self, index=QtCore.QModelIndex()):
        return MAIN_NROWS

    def data(self, index, role=QtCore.Qt.DisplayRole):
        row = index.row()

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            if row == BAUD:
                return QtCore.QVariant(self.settings.baud)
            elif row == PORT:                
                return QtCore.QVariant(self.settings.port)
            elif row == SAVE_PATH:
                return QtCore.QVariant(self.settings.save_path)
        else:
            return QtCore.QVariant()

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if index.isValid():
            row = index.row()
            if row == BAUD:
                self.settings.baud = int(value)
            elif row == PORT:
                self.settings.port = value
            elif row == SAVE_PATH:
                self.settings.save_path = value
            self.dataChanged.emit(index, index, [])
            return True
        else:
            return False

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled
        else:
            return QtCore.Qt.ItemFlags(
                QtCore.QAbstractListModel.flags(self, index) |
                QtCore.Qt.ItemIsEditable)


class Settings:
    def __init__(self):
        self.baud = BAUD_DEFAULT
        self.save_path = os.path.expanduser("~")
        self.scan_ports()
        self.port = self.available_ports[0].device

    def scan_ports(self):
        self.available_ports = list_ports.comports()
        for port in self.available_ports:
            if port.manufacturer is None:
                self.available_ports.remove(port)
        self.available_ports.sort()


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    """
    Data acquisition main window
    """
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setupUi(self)
        self._gui_refresh_rate = GUI_REFRESH_RATE
        self.playButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.settings = Settings()

    @QtCore.pyqtSlot()
    def on_quitButton_clicked(self):
        self.stop()
        self.close()

    @QtCore.pyqtSlot()
    def on_playButton_clicked(self):
        self.start()
    
    @QtCore.pyqtSlot()
    def on_stopButton_clicked(self):
        self.stop()

    @QtCore.pyqtSlot(bool)
    def on_recButton_toggled(self, toggled):
        if toggled:
            self.start_recording()
        else:
            self.stop_recording()
    
    @QtCore.pyqtSlot()
    def on_settingsButton_clicked(self):
        dialog = SettingsDialog(self.settings, parent=self)
        self.W = dialog
        dialog.exec_()

    def start(self, retry=3):
        """
        Start reading serial data
        """
        # Connect to the microcontroller and wait for data
        self.statusbar.showMessage('Connecting to µC...')
        try:
            self.serial = Serial(port=self.settings.port,
                                 baudrate=self.settings.baud,
                                 timeout=None)
        except SerialException as exc:
            self.statusbar.showMessage("Serial error")
            QtWidgets.QMessageBox.critical(self, "Serial error", exc.strerror)
            return
        
        time.sleep(0.1)
        self.serial.reset_input_buffer()

        retries = 0
        self.statusbar.showMessage("Waiting for data...")
        while self.serial.in_waiting == 0:
            if retries == retry:
                msg = "No serial data received."
                self.stop()
                self.statusbar.clearMessage()
                QtWidgets.QMessageBox.information(self, "Notice", msg)
                return
            retries += 1
            time.sleep(1)

        # Find out how many values per line there are in the serial
        # datafrom reading the first line
        line = self.serial.readline()
        line = line.decode().split()
        nsignals = len(line)
        
        # Initialise data container
        self.data = []
        from collections import deque
        for _ in range(nsignals):
            self.data.append(deque([], maxlen=WIN_WIDTH_SAMPLES))

        # Set up plots
        self.setup_plot(nsignals)

        #self.x = deque(np.arange(data_len), maxlen=data_len)
        self.statusbar.clearMessage()
        self.playButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.recButton.setEnabled(True)
        self.settingsButton.setEnabled(False)
    
    def stop(self):
        """
        Stop reading serial data.
        """
        # Stop data acquisition.
        if hasattr(self, 'timer'):
            self.timer.stop()
        
        # Close serial connection
        if hasattr(self, 'serial'):
            self.serial.close()

        if self.recButton.isChecked():
            self.recButton.toggle()

        # Reset buttons
        self.playButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.recButton.setEnabled(False)
        self.settingsButton.setEnabled(True)

    def start_recording(self):
        now = datetime.today()
        filename = '{:%Y-%m-%d_%H_%M_%S}.tab'.format(now)
        path = os.path.join(self.settings.save_path,filename)
        self._outfile = open(path, 'w')
        self.statusbar.showMessage(f"Recording to {path}")

    def stop_recording(self):
        self._outfile.close()
        self.statusbar.clearMessage()

    def update(self):
        """
        Update the plots with incoming data

        This function runs repeatedly under a QTimer. It reads the data
        form the serial port and plots it.
        """
        if self.serial.in_waiting > 10:
            try:
                this_data = self.serial.readlines(self.serial.in_waiting)             

                for (index, line) in zip(count(), this_data):
                    line = line.decode()
                    if self.recButton.isChecked():
                        self._outfile.writelines(line)
                        self._outfile.flush()
                    this_data[index] = line.split()
                this_data = np.array(this_data).astype('float')
                for (index, samples) in zip(count(), this_data.T):
                    self.data[index].extend(samples)
                    self.curves[index].setData(self.data[index])

            except ValueError as error:
                print(error)
                #sys.exit()
        
    def setup_plot(self, nsignals):
        # title_fontsize = 10
        x_tick_fontsize = 10
        y_tick_fontsize = 10
        # marker_fontsize = 8
        y_tick_margin = 60
        curve_colour = "#acfa58"

        xfont = pg.QtGui.QFont()
        yfont = pg.QtGui.QFont()
        yfont.setPointSize(y_tick_fontsize)
        xfont.setPointSize(x_tick_fontsize)

        # Format with bounding box...
        # self.layout = pg.GraphicsLayout(border=(100, 100, 100))
        # ...or no box.
        self.layout = pg.GraphicsLayout()

        self.graphicsView.setCentralItem(self.layout)
        self.plots = []
        self.curves = []

        # Create a plot for each signal and initialise a curve for
        # each plot. These curves are the ones that will be updated
        # with serial data.
        for nrow in range(nsignals):
            plot = self.layout.addPlot(row=nrow, col=0)

            # Format y-axis.
            # Add a fixed margin to the left so that the plots are
            # aligned regardless of the width of the y-ticklabels.
            yaxis = plot.axes['left']['item']
            yaxis.setWidth(y_tick_margin)
            yaxis.setTickFont(yfont)

            # Format x-axis. Do not show x-ticklabels but do retain
            # the x-axis line and the vertical grid lines.
            xaxis = plot.axes['bottom']['item']
            xaxis.setStyle(showValues=False)
            plot.showGrid(x=True, y=True)

            # Create curves.
            curve = plot.plot(pen=curve_colour)
            self.plots.append(plot)
            self.curves.append(curve)
            plot.setXRange(0, WIN_WIDTH_SAMPLES)

        ## Link x-axis from all plots to that of the last one.
        for plot in self.plots[:-1]:
            plot.setXLink(self.plots[-1])

        ## Show the x-axis and the x-label in the last plot.
        #last_plot = self.plots[-1]
        #xaxis = last_plot.axes['bottom']['item']
        #xaxis.setStyle(showValues=True)
        #xaxis.setTickFont(yfont)
        #last_plot.setLabel('bottom', 'Time', units='s', size=10)

        ## Add labels to y axis
        #self.update_y_labels()

        ## Update plot at regular intervals.
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self._gui_refresh_rate)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    self = MainWindow()
    self.show()
    sys.exit(app.exec_())
