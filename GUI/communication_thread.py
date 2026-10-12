from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QSpinBox,
                             QLabel, QPushButton, QDoubleSpinBox, QFileDialog,
                             QComboBox, QSlider, QMessageBox, QFrame, QTextEdit,
                             QSplitter, QTextBrowser, QCheckBox)
from PyQt5.QtCore import pyqtSignal, QTimer, QThread, pyqtSignal as Signal
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QTextCursor, QColor, QFont
import os
import time
import serial
import queue
import socket
import threading

# ============ Base class: Communication Thread ============
class CommunicationThread(QThread):
    """Base class for communication threads"""
    esp2main_command = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.main2esp_queue = queue.Queue()
        self.connect_flag = False
        self.running = True

    def main2esp(self, data):
        """Send data (subclass must implement)"""
        raise NotImplementedError

    def esp2main(self, data):
        """Receive data (subclass must implement)"""
        raise NotImplementedError

    def disconnect_esp32(self):
        """Disconnect (subclass must implement)"""
        raise NotImplementedError
    def connect_esp32(self):
        """Connect"""
        raise NotImplementedError

# ============ Serial Communication Thread ============
class SerialCommunicationThread(CommunicationThread):
    """Serial communication thread"""

    def __init__(self, port, baudrate=115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial = None
    def main2esp(self, data):
        self.serial.write(data.encode())
    def esp2main(self, data):
        self.esp2main_command.emit(data)

    def run(self):
        while self.running:
            if not self.connect_flag:
                self.connect_esp32()
            else:
                    data_esp32 = self.serial.readline().decode().strip()
                    if data_esp32:
                        self.esp2main(data_esp32)
                        print(f"Received: {data_esp32}")
                    if self.main2esp_queue.qsize() > 0:

                        data_main = self.main2esp_queue.get_nowait()
                        print(f"Sending: {data_main}")
                        self.serial.write(data_main.encode())

    def connect_esp32(self):
        try:
            print('start')
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.1  # Set timeout to avoid readline blocking
            )
            time.sleep(2)  # Wait for serial initialization
            self.connect_flag = True
            print('connect esp32 success')

            # Send connection test
            # self.serial.write("connect\n".encode())
            # response = self.serial.readline().decode().strip()
            # print(f"Received: {response}")

            # if response == "connect":
            #     self.connect_flag = True
            #     print("Serial connection successful")
            # else:
            #     self.connect_flag = False
            #     print(f"Connection failed, received: {response}")

        except Exception as e:
            print(f"Serial connection failed: {e}")
            time.sleep(1)
            self.connect_flag = False
    def disconnect_esp32(self):
        self.serial.close()
        self.connect_flag = False
        self.main2esp_queue.put("disconnect")