#!/usr/bin/env python3
# coding=utf-8
#
# Copyright (c) 2021 Antonio González

from PyQt5 import (QtCore, QtGui, QtWidgets)
from itertools import count
from serial import Serial, SerialException
import numpy as np
import pyqtgraph as pg
import time

from ui.ui_main import Ui_MainWindow

# GUI parameters
GUI_REFRESH_RATE = 100 #  In milliseconds
WIN_WIDTH_SAMPLES = 500

# Serial parameters
BAUD = 115200
PORT = "/dev/ttyACM0"

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

    def start(self, retry=3):
        """
        Start reading serial data
        """
        # Connect to the microcontroller and wait for data
        self.statusbar.showMessage('Connecting to µC...')
        try:
            self.serial = Serial(port=PORT, baudrate=BAUD, timeout=None)
        except SerialException as exc:
            self.statusbar.showMessage("Serial error")
            QtWidgets.QMessageBox.critical(self, "Serial error", exc.strerror)
            return
        
        time.sleep(0.1)
        #self.serial.reset_input_buffer()

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

        # Reset buttons
        self.playButton.setEnabled(True)
        self.stopButton.setEnabled(False)

    def update(self):
        """
        Update the plots with incoming data

        This function runs repeatedly under a QTimer. It reads the data
        form the serial port and plots it.
        """
        if self.serial.in_waiting > 10:
            try:
                this_data = self.serial.readlines(self.serial.in_waiting)
                this_data = [line.decode().split() for line in this_data]
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
    import sys
    app = QtWidgets.QApplication([])
    self = MainWindow()
    self.show()
    sys.exit(app.exec_())
