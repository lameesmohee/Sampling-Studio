from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
from PyQt5.QtGui import QPixmap
import sys
from os import path
import numpy as np
from math import ceil
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from qtawesome import icon
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib as plt

MainUI, _ = loadUiType(path.join(path.dirname(__file__), 'sampler.ui'))


class MainApp(QMainWindow, MainUI):
    def __init__(self, parent=None):
        super(MainApp, self).__init__(parent)
        QMainWindow.__init__(self)
        self.sample = False
        self.add_noise = False
        self.signal_name = None
        self.ax = None

        self.figure = None
        self.combined_signal_noise = 0
        self.setupUi(self)
        self.figure_sampling = Figure(figsize=(9.5, 3.5), dpi=80)
        self.ax1 = self.figure_sampling.add_subplot(111)
        self.figure_interpolation= Figure(figsize=(9.5, 3.5), dpi=80)
        self.ax2 = self.figure_interpolation.add_subplot(111)
        self.signal_waveforms = []
        self.signals_sampling = []
        self.existed_signals = {}  # {signal_name:[freq, amp]}
        self.Noise = 0
        self.styles()

        self.freq_input.setText("1")
        self.amp_input.setText("1")
        self.handle_buttons()



    def handle_buttons(self):
        self.freq_up.clicked.connect(lambda: self.freq_handling(self.freq_up))
        self.freq_down.clicked.connect(lambda: self.freq_handling(self.freq_down))
        self.amp_up.clicked.connect(lambda: self.amp_handling(self.amp_up))
        self.amp_down.clicked.connect(lambda: self.amp_handling(self.amp_down))
        self.add_signal_button.clicked.connect(self.signal_name_handling)
        self.add_signal_button.clicked.connect(self.plot)
        self.sampling.toggled.connect(self.plot)
        self.sampling_frequency_slider.valueChanged.connect(self.plot)
        self.freq_options.currentTextChanged.connect(self.plot)
        self.SNR_Slider.valueChanged.connect(self.Gaussian_noise)
        self.interpolation.toggled.connect(self.Interpolation)

    def styles(self):
        self.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        plus_icon = icon("fa.plus", color='green')
        minus_icon = icon("fa.minus", color='red')
        self.freq_up.setIcon(plus_icon)
        self.freq_down.setIcon(minus_icon)
        self.amp_up.setIcon(plus_icon)
        self.amp_down.setIcon(minus_icon)
        self.sampling_frequency_slider.setMinimum(1)
        self.sampling_frequency_slider.setMaximum(100)
        # self.sampling_frequency_slider.setValue(20)
        self.sampling_frequency_slider.setTickPosition(QSlider.TicksBothSides)
        self.SNR_Slider.setMinimum(1)
        self.SNR_Slider.setMaximum(1000)

        self.SNR_Slider.setTickPosition(QSlider.TicksBothSides)

    def freq_handling(self, button):
        # Getting the text form the frequency input
        input_freq_str = self.freq_input.text()
        input_freq_int = int(input_freq_str)
        # Increasing it by one on every click
        if button == self.freq_up:
            input_freq_int += 1
            updated_freq_str = str(input_freq_int)
            self.freq_input.setText(updated_freq_str)
        else:
            # Decreasing it by one on every click
            if input_freq_int == 1:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setInformativeText("Frequency cannot be zero!")
                msg.show()
                msg.exec_()
            else:
                input_freq_int -= 1
                updated_freq_str = str(input_freq_int)
                self.freq_input.setText(updated_freq_str)

    def amp_handling(self, button):
        # Getting the text form the amplitude input
        input_amp_str = self.amp_input.text()
        input_amp_int = int(input_amp_str)
        # Increasing it by one on every click
        if button == self.amp_up:
            input_amp_int += 1
            updated_amp_str = str(input_amp_int)
            self.amp_input.setText(updated_amp_str)
        else:
            # Decreasing it by one on every click
            if input_amp_int == 1:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setInformativeText("Amplitude cannot be zero!")
                msg.show()
                msg.exec_()
            else:
                input_amp_int -= 1
                updated_amp_str = str(input_amp_int)
                self.amp_input.setText(updated_amp_str)

    def signal_name_handling(self):
        # Adding the signal name into the QComboBox of the signals names
        self.signal_name = self.signal_name_input.text()
        if self.signal_name == "" or self.freq_input.text() == "" or self.amp_input.text == "":
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setInformativeText("Please complete the signal requirements!")
            msg.show()
            msg.exec_()
        else:
            self.signals_names.addItem(self.signal_name)
            self.update_signal_waveforms()

    def cos_creation(self, f, amp, t=0):
        cos_wave = amp * np.cos(2 * np.pi * f * t)
        return cos_wave

    def update_signal_waveforms(self):
        # Get the current frequency and amplitude
        input_freq_str = self.freq_input.text()
        f = int(input_freq_str)
        input_amp_str = self.amp_input.text()
        amp = int(input_amp_str)
        # Check if the user added the signal with the same name and changed its freq and amp
        if self.signal_name in self.existed_signals:
            # Update the existing signal's frequency and amplitude
            self.existed_signals[self.signal_name][0] = f
            self.existed_signals[self.signal_name][1] = amp
        else:
            # Add a new entry for the signal
            self.existed_signals[self.signal_name] = [f, amp]

        self.check_largest_freq(self.existed_signals)
        # Time values (from 0 to 2 second)
        # 1000 data points
        t = np.linspace(0, 2, 1000)
        # Calculate the cosine waveform for the current signal
        signal_waveform = self.cos_creation(f, amp, t)

        # Adding each signal to a list, so it can be summed
        self.signal_waveforms.append(signal_waveform)
        # print(f"signal:{self.signal_waveforms}")
        print(self.existed_signals)

    def plot(self):
        scene = QGraphicsScene()
        self.graphicsView.setScene(scene)
        canvas = FigureCanvas(self.figure_sampling)
        scene.addWidget(canvas)

        if self.signal_waveforms:
            # Combine all signal waveforms
            self.ax1.cla()
            if not self.add_noise: # check if noise is added or not
                self.combined_signal = np.sum(self.signal_waveforms, axis=0)
                self.ax1.plot(np.linspace(0, 2, 1000), self.combined_signal)
            else:
                self.ax1.plot(np.linspace(0, 2, 1000), self.combined_signal_noise)
            left_margin = 0.1
            self.ax1.set_position([left_margin, 0.12, 0.78, 0.8])
            self.ax1.grid(True, color='gray', linestyle='--', alpha=0.5)
            self.ax1.set_title('Original Signal and Sampling Points')
            self.ax1.set_xlabel('Time (s)')
            self.ax1.set_ylabel('Amplitude')
            canvas.draw()
            if self.sampling.isChecked():
                self.Sampling()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setInformativeText("Please complete the signal requirements!")
            msg.show()
            msg.exec_()


    def Sampling(self):
        if self.sampling.isChecked():
            self.sample =True
            state_sampling = self.freq_options.currentText()
            if state_sampling == "Hz":
                self.sampling_rate = self.sampling_frequency_slider.value()
                print(f"sam:{self.sampling_rate}")
                self.Time = 1 / self.sampling_rate
                self.Num_of_sampling_points = np.arange(0, ceil(2 / self.Time))
                self.time = self.Time * self.Num_of_sampling_points
                self.signals_sampling.clear()
                for signal, attributes in self.existed_signals.items():
                    print(attributes[0], attributes[1])
                    sampler_signal = self.cos_creation(attributes[0], attributes[1], self.time)
                    self.signals_sampling.append(sampler_signal)

                sum_of_sampling_points = np.sum(self.signals_sampling, axis=0)
                self.ax1.plot(self.time, sum_of_sampling_points, 'ro', color='r')

                self.figure_sampling.canvas.draw()


            else:
                Nyquist_freq = 2 * self.max_freq
                print(self.sampling_frequency_slider.value())

                self.sampling_rate = self.sampling_frequency_slider.value() * Nyquist_freq

                print(f"sam:{self.sampling_rate}")
                self.Time = 1 / self.sampling_rate
                self.Num_of_sampling_points = np.arange(0, ceil(2 / self.Time))
                self.time = self.Time * self.Num_of_sampling_points
                self.signals_sampling.clear()
                for signal, attributes in self.existed_signals.items():
                    print(attributes[0], attributes[1])
                    sampler_signal = self.cos_creation(attributes[0], attributes[1], self.time)
                    self.signals_sampling.append(sampler_signal)

                sum_of_sampling_points = np.sum(self.signals_sampling, axis=0)
                print(sum_of_sampling_points)

                self.ax1.plot(self.time, sum_of_sampling_points, 'ro', color='r')
                self.figure_sampling.canvas.draw()




    def check_largest_freq(self, data_signals):
        if len(data_signals) > 1:
            self.prev_freq = self.max_freq

        else:
            self.prev_freq = 0
            self.max_freq = 0


        for data, value in data_signals.items():
            if value[0] > self.max_freq:
                self.max_freq = value[0]




        index = self.freq_options.findText(' ')
        self.freq_options.removeItem(index)
        index1 = self.freq_options.findText("Nyquist–Shannon" + ' ' + str((2 * self.prev_freq)) + ' ' + "Hz")
        self.freq_options.removeItem(index1)

        print(index1)
        self.freq_options.addItem("Nyquist–Shannon" + ' ' + str((2 * self.max_freq)) + ' ' + "Hz")

    def Gaussian_noise(self):
        if len(self.existed_signals) >= 1:
            SNR = self.SNR_Slider.value()  # SNR = Average power of signal / Average power of noise
            print(SNR)
            self.add_noise = True
            Average_power_signal = np.mean(self.combined_signal ** 2)
            Average_power_noise = Average_power_signal / SNR
            mean_noise = 0
            self.Noise = np.random.normal(mean_noise, np.sqrt(Average_power_noise), len(self.combined_signal))
            # np.delete(self.combined_signal_noise)
            self.combined_signal_noise = self.Noise + self.combined_signal
            self.plot()

        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setInformativeText("Please complete the signal requirements!")
            msg.show()
            msg.exec_()

    def Interpolation(self):
        pass








def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
