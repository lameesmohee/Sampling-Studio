from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
from PyQt5.QtGui import QPixmap
import sys
from os import path


MainUI, _ = loadUiType(path.join(path.dirname(__file__), 'sampler.ui'))


class MainApp(QMainWindow, MainUI):
    def __init__(self, parent=None):
        super(MainApp, self).__init__(parent)
        QMainWindow.__init__(self)
        self.setupUi(self)

def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()