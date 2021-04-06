#!/usr/bin/env python3
# coding=utf-8
#
# Copyright (c) 2021 Antonio González

from datetime import datetime
from itertools import count
import os
import sys
import time

import numpy as np
from PyQt5 import (QtCore, QtGui, QtWidgets)
import pyqtgraph as pg
from serial import Serial, SerialException
from serial.tools import list_ports

from ui.ui_main import Ui_MainWindow
from ui.ui_settings_dlg import Ui_Dialog

# GUI parameters
GUI_REFRESH_RATE = 100  # In milliseconds
WIN_WIDTH_SAMPLES = 500

# Serial parameters
BAUD_DEFAULT = 115200
BAUD_RATES = (460800, 115200, 57600, 38400, 19200, 14400, 9600)


class SettingsDialog(QtWidgets.QDialog, Ui_Dialog):
    """
    Settings dialog
    """
    def __init__(self, settings, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.settings = settings

        # Baud
        for (index, baud) in zip(count(), BAUD_RATES):
            self.baudComboBox.addItem(str(baud))
            if baud == settings.baud:
                self.baudComboBox.setCurrentIndex(index)

        # Port
        for (index, port) in zip(count(), settings.available_ports):
            port_str = f'{port.device} -- {port.manufacturer}'
            self.portComboBox.addItem(port_str)
            if port.device == self.settings.port:
                self.portComboBox.setCurrentIndex(index)

        # Path
        self.savePathLabel.setText(settings.save_path)

        # Window width
        self.widthSpinBox.setValue(settings.width)

    @QtCore.pyqtSlot()
    def on_portRefreshButton_clicked(self):
        self.portComboBox.clear()
        self.settings.scan_ports()
        for port in self.settings.available_ports:
            port_str = f'{port.device} -- {port.manufacturer}'
            self.portComboBox.addItem(port_str)

    @QtCore.pyqtSlot()
    def on_savePathButton_clicked(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, caption='Select default data directory')
        if path:
            self.savePathLabel.setText(path)


class Settings:
    def __init__(self):
        self.baud = BAUD_DEFAULT
        self.width = WIN_WIDTH_SAMPLES
        self.save_path = os.path.expanduser("~")
        self.port = ''
        self.scan_ports()
        # Set as default the first port in the list (ifa any)
        if len(self.available_ports) > 0:
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

        # Create a timer to update plot at regular intervals
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)

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
        ok = dialog.exec_()
        if ok:
            self.settings.baud = int(dialog.baudComboBox.currentText())
            port_index = dialog.portComboBox.currentIndex()
            port = self.settings.available_ports[port_index]
            self.settings.port = port.device
            self.settings.save_path = dialog.savePathLabel.text()
            self.settings.width = dialog.widthSpinBox.value()

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
            self.data.append(deque([], maxlen=self.settings.width))

        # Set up plots
        self.setup_plot(nsignals)

        # Start the timer
        self.timer.start(self._gui_refresh_rate)

        # Update gui
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
        path = os.path.join(self.settings.save_path, filename)
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
                # sys.exit()

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
            plot.setXRange(0, self.settings.width)

        # Link x-axis from all plots to that of the last one.
        for plot in self.plots[:-1]:
            plot.setXLink(self.plots[-1])

        #  Show the x-axis and the x-label in the last plot.
        # last_plot = self.plots[-1]
        # xaxis = last_plot.axes['bottom']['item']
        # xaxis.setStyle(showValues=True)
        # xaxis.setTickFont(yfont)
        # last_plot.setLabel('bottom', 'Time', units='s', size=10)

        # Add labels to y axis
        # self.update_y_labels()

        # Update plot at regular intervals.
        #self.timer = QtCore.QTimer()
        #self.timer.timeout.connect(self.update)
        #self.timer.start(self._gui_refresh_rate)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    self = MainWindow()
    self.show()
    sys.exit(app.exec_())
