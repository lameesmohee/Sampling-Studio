import math
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
import pandas as pd
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from qtawesome import icon
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


MainUI, _ = loadUiType(path.join(path.dirname(__file__), 'sampler.ui'))


class MainApp(QMainWindow, MainUI):
    def __init__(self, parent=None):
        super(MainApp, self).__init__(parent)
        QMainWindow.__init__(self)
        self.toolbar1 = None
        self.data_signal = None
        self.ISsignal = False
        self.sample = False
        self.add_noise = False
        self.signal_name = None
        self.ax = None
        self.figure = None
        self.combined_signal_noise = 0
        self.setupUi(self)
        self.figure_sampling = Figure(figsize=(12, 3.5), dpi=80)
        self.ax1 = self.figure_sampling.add_subplot(111)
        self.figure_interpolation = Figure(figsize=(12, 3.5), dpi=80)
        self.ax2 = self.figure_interpolation.add_subplot(111)
        self.figure_Error = Figure(figsize=(12, 3.5), dpi=80)
        self.ax3 = self.figure_Error.add_subplot(111)
        self.signal_waveforms = []
        self.signals_sampling = []
        self.error_data = None
        self.original_data = None
        self.existed_signals = {}  # {signal_name:[freq, amp]}
        self.Noise = 0
        self.styles()
        self.freq_input.setText("1")
        self.amp_input.setText("1")
        self.handle_buttons()
        self.name_counter = 1
        self.default_name = f"signal_{self.name_counter}"
        self.signal_name_input.setText(self.default_name)
        self.freq_options.removeItem(1)
        self.SNR_Slider.setValue(self.SNR_Slider.maximum())
        self.SNR_Slider.valueChanged.connect(self.update_SNRslider_value)
        self.sampling_frequency_slider.valueChanged.connect(self.update_freqslider_value)

    def handle_buttons(self):
        self.freq_up.clicked.connect(lambda: self.freq_handling(self.freq_up))
        self.freq_down.clicked.connect(lambda: self.freq_handling(self.freq_down))
        self.amp_up.clicked.connect(lambda: self.amp_handling(self.amp_up))
        self.amp_down.clicked.connect(lambda: self.amp_handling(self.amp_down))
        self.add_signal_button.clicked.connect(self.signal_name_handling)
        self.actionopen.triggered.connect(self.browse_file)
        self.add_signal_button.clicked.connect(self.plot)
        self.signals_names.currentIndexChanged.connect(self.on_combobox_change)
        self.delete_signal_button.clicked.connect(self.delete_signal)
        self.sampling.toggled.connect(self.plot)
        self.sampling_frequency_slider.valueChanged.connect(self.plot)
        self.freq_options.currentTextChanged.connect(self.plot)
        self.SNR_Slider.valueChanged.connect(self.Gaussian_noise)
        self.interpolation.stateChanged.connect(self.Interpolation)

    def styles(self):
        self.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView_interpolation.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView_interpolation.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView_error.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView_error.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        plus_icon = icon("fa.plus", color='black')
        minus_icon = icon("fa.minus", color='black')
        self.freq_up.setIcon(plus_icon)
        self.freq_down.setIcon(minus_icon)
        self.amp_up.setIcon(plus_icon)
        self.amp_down.setIcon(minus_icon)
        self.sampling_frequency_slider.setMinimum(1)
        self.sampling_frequency_slider.setMaximum(100)
        self.sampling_frequency_slider.setTickPosition(QSlider.TicksBothSides)
        self.SNR_Slider.setMinimum(1)
        self.SNR_Slider.setMaximum(100)
        self.SNR_Slider.setTickPosition(QSlider.TicksBothSides)

    def update_SNRslider_value(self, value):
        self.snr_value.setText(f"{value}")

    def update_freqslider_value(self, value):
        self.freq_value.setText(f"{value}")

    def on_combobox_change(self, index):
        # The 'index' parameter contains the index of the selected item
        self.current_combox_index = index
        text = self.signals_names.currentText()
        self.current_combox_text = text

    def delete_signal(self):
        # Checking if it's a File or a user made signal
        if self.ISsignal:
            self.signal_waveforms.pop(self.current_combox_index)
            self.freq_options.removeItem(self.current_combox_index + 1)
            self.signals_names.removeItem(self.current_combox_index)
            self.plot()
        else:
            self.signal_waveforms.pop(self.current_combox_index)
            self.freq_options.removeItem(self.current_combox_index + 1)
            del self.existed_signals[self.current_combox_text]
            self.signals_names.removeItem(self.current_combox_index)
            self.plot()

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
        self.name_counter += 1
        self.default_name = f"signal_{self.name_counter}"
        self.signal_name_input.setText(self.default_name)
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
            if len(self.signal_name) != 0:
                self.existed_signals[self.signal_name] = [f, amp]
        self.check_largest_freq(self.existed_signals)
        # Time values (from 0 to 2 second)
        # 1000 data points
        t = np.linspace(0, 2, 1000)
        # Calculate the cosine waveform for the current signal
        signal_waveform = self.cos_creation(f, amp, t)
        self.signal_waveforms.append(signal_waveform)

    def plot(self):
        scene = QGraphicsScene()
        self.graphicsView.setScene(scene)
        canvas = FigureCanvas(self.figure_sampling)
        scene.addWidget(canvas)
        print('signal_count: ', self.signals_names.count())
        if self.signals_names.count() == 0:
            self.ax1.cla()
            self.ax2.cla()
            self.ax3.cla()

        if self.signal_waveforms:
            # Combine all signal waveforms
            self.ax1.cla()
            if not self.add_noise:  # check if noise is added or not
                self.combined_signal = np.sum(self.signal_waveforms, axis=0)
                self.original_data, = self.ax1.plot(np.linspace(0, 2, 1000), self.combined_signal)
            else:
                self.original_data, = self.ax1.plot(np.linspace(0, 2, 1000), self.combined_signal_noise)
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
                if self.interpolation.isChecked():
                    self.Interpolation()

    def Sampling(self):
        if self.sampling.isChecked():
            self.sample = True
            state_sampling = self.freq_options.currentText()
            if state_sampling == "Hz":
                self.sampling_rate = self.sampling_frequency_slider.value()
            else:
                if self.ISsignal:
                    signal_max_freq = self.get_largest_freq_signal()
                    max_freq = signal_max_freq
                    if len(self.existed_signals) >= 1:
                        max_freq = max(signal_max_freq, self.max_freq)
                    Nyquist_freq = 2 * max_freq
                else:
                    Nyquist_freq = 2 * self.max_freq
                self.sampling_rate = self.sampling_frequency_slider.value() * Nyquist_freq

        print(f"sam:{self.sampling_rate}")
        self.Time = 1 / self.sampling_rate
        self.Num_of_sampling_points = np.arange(0, ceil(2 / self.Time))
        self.time = self.Time * self.Num_of_sampling_points
        duration = np.linspace(0, 2, 1000)
        print(f"time:{self.time}")
        indices_to_mark = []
        if self.ISsignal:
            for idx in self.time:
                for index in range(len(duration)):
                    if idx <= duration[index]:
                        print(index)
                        print("lll")
                        indices_to_mark.append(index)
                        break
            if not self.add_noise:
                sum_of_sampling_points = np.sum(self.signal_waveforms, axis=0)
                self.ax1.plot(np.linspace(0, 2, 1000), sum_of_sampling_points, 'ro', color='r',
                              markevery=indices_to_mark)
            else:
                self.ax1.plot(np.linspace(0, 2, 1000), self.combined_signal_noise, 'ro', color='r',
                              markevery=indices_to_mark)
        else:
            self.signals_sampling.clear()
            for signal, attributes in self.existed_signals.items():
                print(f"exist:{len(self.existed_signals)}")
                print(attributes[0], attributes[1])
                sampler_signal = self.cos_creation(attributes[0], attributes[1], self.time)
                self.signals_sampling.append(sampler_signal)
            if not self.add_noise:
                sum_of_sampling_points = np.sum(self.signals_sampling, axis=0)
                self.ax1.plot(self.time, sum_of_sampling_points, 'ro', color='r')
            else:
                for idx in self.time:
                    for index in range(len(duration)):
                        if idx <= duration[index]:
                            print(index)
                            print("lll")
                            indices_to_mark.append(index)
                            break
                self.ax1.plot(np.linspace(0, 2, 1000), self.combined_signal_noise, 'ro', color='r',
                              markevery=indices_to_mark)
        self.figure_sampling.canvas.draw()
        if self.interpolation.isChecked():
            self.Interpolation()

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
        if self.ISsignal:
            max_freq_signal = self.get_largest_freq_signal()
            if max_freq_signal < self.max_freq:
                self.freq_options.addItem("Nyquist–Shannon" + ' ' + str((2 * self.max_freq)) + ' ' + "Hz")
                index1 = self.freq_options.findText("Nyquist–Shannon" + ' ' + str((2 * max_freq_signal)) + ' ' + "Hz")
                self.freq_options.removeItem(index1)
            else:
                self.freq_options.addItem("Nyquist–Shannon" + ' ' + str((2 * max_freq_signal)) + ' ' + "Hz")
        else:
            self.freq_options.addItem("Nyquist–Shannon" + ' ' + str((2 * self.max_freq)) + ' ' + "Hz")

    def Gaussian_noise(self):
        if len(self.existed_signals) >= 1 or self.ISsignal:
            SNR = self.SNR_Slider.value()  # SNR = Average power of signal / Average power of noise
            print(SNR)
            self.add_noise = True
            Average_power_signal = np.mean(self.combined_signal ** 2)
            Average_power_noise = Average_power_signal / (math.pow(10, SNR/10))
            mean_noise = 0
            self.Noise = np.random.normal(mean_noise, np.sqrt(Average_power_noise), len(self.combined_signal))
            self.combined_signal_noise = self.Noise + self.combined_signal
            self.plot()

    def Interpolation(self):
        if self.interpolation.isChecked() and (len(self.existed_signals) >= 1 or self.ISsignal):
            scene2 = QGraphicsScene()
            self.graphicsView_interpolation.setScene(scene2)
            canvas = FigureCanvas(self.figure_interpolation)
            scene2.addWidget(canvas)
            state_sampling = self.freq_options.currentText()
            if state_sampling == "Hz":
                self.sampling_rate = self.sampling_frequency_slider.value()
            else:
                if self.ISsignal:
                    signal_max_freq = self.get_largest_freq_signal()
                    max_freq = signal_max_freq
                    if len(self.existed_signals) >= 1:
                        max_freq = max(signal_max_freq, self.max_freq)
                    Nyquist_freq = 2 * max_freq
                else:
                    Nyquist_freq = 2 * self.max_freq
                self.sampling_rate = self.sampling_frequency_slider.value() * Nyquist_freq

            print(f"sam:{self.sampling_rate}")
            self.Time = 1 / self.sampling_rate
            self.Num_of_sampling_points = np.arange(0, ceil(2 / self.Time))
            self.time = self.Time * self.Num_of_sampling_points
            duration = np.linspace(0, 2, 1000)
            indices_to_mark = []
            self.ax2.cla()

            if self.ISsignal:
                self.signals_sampling.clear()
                if self.add_noise:
                    sum_of_sampling_points = []
                    for idx in self.time:
                        for index in range(len(duration)):
                            if idx <= duration[index]:
                                print(index)
                                print("lll")
                                indices_to_mark.append(index)
                                break
                    for time in indices_to_mark:
                        sum_of_sampling_points.append(self.combined_signal_noise[time])
                else:
                    for idx in self.time:
                        for index in range(len(duration)):
                            if idx <= duration[index]:
                                print(index)
                                print("lll")
                                indices_to_mark.append(index)
                                break
                    sampling_data_signal = []
                    for item in indices_to_mark:  # for interpolation
                        sampling_data_signal.append(self.data_signal[item])
                    self.signals_sampling.append(sampling_data_signal)
                    print(indices_to_mark)
                    if len(self.existed_signals) >= 1:
                        for signal, attributes in self.existed_signals.items():
                            sampler_signal = self.cos_creation(attributes[0], attributes[1], self.time)
                            self.signals_sampling.append(sampler_signal)
                    sum_of_sampling_points = np.sum(self.signals_sampling, axis=0)

                y_reconstruction = np.zeros(len(duration))
                for i in range(0, len(duration)):
                    for n in self.Num_of_sampling_points:
                        y_reconstruction[i] += sum_of_sampling_points[n] * np.sinc(
                            (duration[i] - self.time[n]) / self.Time)
                self.reconstruction_data, = self.ax2.plot(duration, y_reconstruction)
            else:
                if self.add_noise:
                    sum_of_sampling_points = []
                    for idx in self.time:
                        for index in range(len(duration)):
                            if idx <= duration[index]:
                                print(index)
                                print("lll")
                                indices_to_mark.append(index)
                                break
                    for time in indices_to_mark:
                        sum_of_sampling_points.append(self.combined_signal_noise[time])

                else:
                    self.signals_sampling.clear()
                    for signal, attributes in self.existed_signals.items():
                        print(attributes[0], attributes[1])
                        sampler_signal = self.cos_creation(attributes[0], attributes[1], self.time)
                        self.signals_sampling.append(sampler_signal)
                    sum_of_sampling_points = np.sum(self.signals_sampling, axis=0)

                y_reconstruction = np.zeros(len(duration))
                for i in range(0, len(duration)):
                    for n in self.Num_of_sampling_points:
                        y_reconstruction[i] += sum_of_sampling_points[n] * np.sinc(
                            (duration[i] - self.time[n])/self.Time)
                self.reconstruction_data, = self.ax2.plot(duration, y_reconstruction)
            left_margin = 0.1
            self.ax2.set_position([left_margin, 0.12, 0.78, 0.8])
            self.ax2.grid(True, color='gray', linestyle='--', alpha=0.5)
            self.ax2.set_title('Reconstruction Signal')
            self.ax2.set_xlabel('Time (s)')
            self.ax2.set_ylabel('Amplitude')
            canvas.draw()
            self.error()
        else:
            if (len(self.existed_signals) >= 1 or self.ISsignal) and not self.interpolation.isChecked():
                print("ksd.")
                self.figure_interpolation.clear()
                self.figure_interpolation.canvas.draw()
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setInformativeText("Please complete the signal requirements!")
                msg.show()
                msg.exec_()

    def browse_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "",
                                                   "CSV Files (*.csv)",
                                                   options=options)
        print(file_name)
        file_name_actual = file_name.split('/')[-1].split('.')[0]
        self.signals_names.addItem(file_name_actual)
        # self.existed_signals[file_name_actual] = []
        self.data_signal = pd.read_csv(file_name)
        self.data_signal = self.data_signal[:1000]
        self.data_signal = self.data_signal.iloc[:, 0].tolist()
        self.ISsignal = True
        self.signal_waveforms.append(self.data_signal)
        max_freq = self.get_largest_freq_signal()
        self.freq_options.addItem("Nyquist–Shannon" + ' ' + str((2 * max_freq)) + ' ' + "Hz")
        self.plot()

    def get_largest_freq_signal(self):
        fft_result = np.fft.fft(self.data_signal)
        print(fft_result)
        n = len(fft_result)
        frequencies = np.fft.fftfreq(n)
        max_freq = max(frequencies)
        print('lama: ', max_freq)
        return max_freq

    def error(self):
        scene2 = QGraphicsScene()
        self.graphicsView_error.setScene(scene2)
        canvas = FigureCanvas(self.figure_Error)
        scene2.addWidget(canvas)
        self.ax3.cla()
        y_original_data = self.original_data.get_ydata()
        y_reconstruction_data = self.reconstruction_data.get_ydata()
        error_y = np.subtract(y_original_data, y_reconstruction_data)
        error_abs = np.abs(error_y)
        time = np.linspace(0, 2, 1000)
        self.ax3.plot(time, error_abs)
        left_margin = 0.1
        self.ax3.set_position([left_margin, 0.12, 0.78, 0.8])
        self.ax3.grid(True, color='gray', linestyle='--', alpha=0.5)
        self.ax3.set_title('Error Signal')
        self.ax3.set_xlabel('Time (s)')
        self.ax3.set_ylabel('Amplitude')
        canvas.draw()


def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
