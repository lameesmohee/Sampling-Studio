from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
from PyQt5.QtGui import QPixmap
import sys
from os import path
import numpy as np
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
        self.signal_name = None
        self.ax = None
        self.figure = None
        self.setupUi(self)
        self.freq_input.setText("1")
        self.amp_input.setText("1")
        self.handle_buttons()
        self.styles()
        self.signal_waveforms = []
        self.existed_signals = {}  # {signal_name:[freq, amp]}

    def handle_buttons(self):
        self.freq_up.clicked.connect(lambda: self.freq_handling(self.freq_up))
        self.freq_down.clicked.connect(lambda: self.freq_handling(self.freq_down))
        self.amp_up.clicked.connect(lambda: self.amp_handling(self.amp_up))
        self.amp_down.clicked.connect(lambda: self.amp_handling(self.amp_down))
        self.add_signal_button.clicked.connect(self.signal_name_handling)
        self.add_signal_button.clicked.connect(self.plot)

    def styles(self):
        self.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        plus_icon = icon("fa.plus", color='green')
        minus_icon = icon("fa.minus", color='red')
        self.freq_up.setIcon(plus_icon)
        self.freq_down.setIcon(minus_icon)
        self.amp_up.setIcon(plus_icon)
        self.amp_down.setIcon(minus_icon)

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


    def cos_creation(self, f, amp):
        # Time values (from 0 to 2 second)
        t = np.linspace(0, 2, 1000)  # 1000 data points
        cos_wave = amp * np.cos(2 * np.pi * f * t)
        return cos_wave

    def update_signal_waveforms(self):
        # Get the current frequency and amplitude
        input_freq_str = self.freq_input.text()
        f = int(input_freq_str)
        input_amp_str = self.amp_input.text()
        amp = int(input_amp_str)
        # Check if the user added the signal with the same name and changed it's freq and amp
        if self.signal_name in self.existed_signals:
            # Update the existing signal's frequency and amplitude
            self.existed_signals[self.signal_name][0] = f
            self.existed_signals[self.signal_name][1] = amp
        else:
            # Add a new entry for the signal
            self.existed_signals[self.signal_name] = [f, amp]
        # Calculate the cosine waveform for the current signal
        signal_waveform = self.cos_creation(f, amp)
        # Adding each signal to a list, so it can be summed
        self.signal_waveforms.append(signal_waveform)
        print(self.existed_signals)

    def plot(self):
        scene = QGraphicsScene()
        self.graphicsView.setScene(scene)
        self.figure = Figure(figsize=(9.5, 3.5), dpi=80)
        canvas = FigureCanvas(self.figure)
        scene.addWidget(canvas)

        if self.signal_waveforms:
            # Combine all signal waveforms
            combined_signal = np.sum(self.signal_waveforms, axis=0)
            ax = self.figure.add_subplot(111)
            ax.plot(np.linspace(0, 2, 1000), combined_signal)
            left_margin = 0.1
            ax.set_position([left_margin, 0.12, 0.78, 0.8])
            ax.grid(True, color='gray', linestyle='--', alpha=0.5)
            ax.set_title('Original Signal and Sampling Points')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Amplitude')
            canvas.draw()


def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()