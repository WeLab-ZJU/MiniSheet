from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QSpinBox, QTextEdit,
                             QLabel, QPushButton, QDoubleSpinBox, QFileDialog,
                             QComboBox, QSlider, QMessageBox, QFrame)
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtCore import Qt
from communication_thread import SerialCommunicationThread#, BluetoothCommunicationThread
import os
import time
from serial.tools import list_ports
import datetime

class ESP32Panel(QWidget):
    home_signal = pyqtSignal()
    move_signal = pyqtSignal(object)
    laser_signal = pyqtSignal(int, bool)      # Laser ID, state
    speed_signal = pyqtSignal(float)          # Speed value
    direction_signal = pyqtSignal(str)        # Direction: 'forward'/'reverse'/'stop'
    connect_signal = pyqtSignal(str, str)     # Connection type, device address

    def __init__(self):
        super().__init__()
        self.laser_states = [False, False, False]  # Laser 1,2,3 states
        self.is_connected = False  # Connection state
        self.current_speed = 0.0   # Current speed
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # ============ 1. Bluetooth/Serial connection section ============
        conn_group = QGroupBox("Device Connection")
        conn_layout = QVBoxLayout(conn_group)

        # First row: connection type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Connection Type:"))

        self.conn_type_combo = QComboBox()
        self.conn_type_combo.addItems(["Bluetooth", "Serial"])
        self.conn_type_combo.currentIndexChanged.connect(self.on_conn_type_changed)
        self.conn_type_combo.setFixedWidth(150)
        type_layout.addWidget(self.conn_type_combo)

        type_layout.addStretch()
        conn_layout.addLayout(type_layout)

        # Second row: device scan and selection
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Available Devices:"))

        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(200)
        device_layout.addWidget(self.device_combo, 1)

        self.scan_btn = QPushButton("Scan Devices")
        self.scan_btn.setFixedWidth(100)
        self.scan_btn.clicked.connect(self.on_scan_devices)
        device_layout.addWidget(self.scan_btn)

        conn_layout.addLayout(device_layout)

        # Third row: connection control and status
        control_layout = QHBoxLayout()

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setFixedWidth(100)
        self.connect_btn.clicked.connect(self.on_connect)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setFixedWidth(100)
        self.disconnect_btn.clicked.connect(self.on_disconnect)
        self.disconnect_btn.setEnabled(False)

        control_layout.addWidget(self.connect_btn)
        control_layout.addWidget(self.disconnect_btn)
        control_layout.addStretch()

        # Status display
        self.conn_status_label = QLabel("Status: Disconnected")
        self.conn_status_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
        control_layout.addWidget(self.conn_status_label)

        conn_layout.addLayout(control_layout)
        main_layout.addWidget(conn_group)

        # ============ 2. Laser control section ============
        laser_group = QGroupBox("Laser Control")
        laser_layout = QHBoxLayout(laser_group)
        laser_layout.setContentsMargins(20, 10, 20, 10)
        laser_layout.setSpacing(20)

        self.laser_btns = []

        for i in range(3):
            # Create horizontal layout
            laser_item_layout = QHBoxLayout()
            laser_item_layout.setSpacing(10)

            # Laser label
            label = QLabel(f"Laser{i+1}:")
            label.setStyleSheet("font-weight: bold; font-size: 14px;")
            label.setFixedWidth(60)

            # Control button
            btn = QPushButton("OFF")
            btn.setCheckable(True)
            btn.setFixedSize(60, 30)
            btn.setObjectName(f"laser_btn_{i}")

            # Set button style
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #808080;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:checked {
                    background-color: #28a745;
                }
                QPushButton:hover {
                    opacity: 0.9;
                }
            """)

            # Connect signal
            btn.clicked.connect(lambda checked, idx=i: self.on_laser_toggled(idx, checked))

            # Add to layout
            laser_item_layout.addWidget(label)
            laser_item_layout.addWidget(btn)
            laser_item_layout.addStretch()

            # Add to main layout
            laser_layout.addLayout(laser_item_layout)
            self.laser_btns.append(btn)

        # Add right spacer
        laser_layout.addStretch()

        main_layout.addWidget(laser_group)

        # ============ 3. Stage control section ============
        stage_group = QGroupBox("Stage Control")
        stage_layout = QVBoxLayout(stage_group)
        stage_layout.setSpacing(15)

        # Speed control
        speed_group = QGroupBox("Speed Setting")
        speed_layout = QVBoxLayout(speed_group)

        # Speed slider and value
        speed_control_layout = QHBoxLayout()

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(0, 200)  # 0-100.0 mm/s
        self.speed_slider.setValue(0)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)

        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.0, 2.0)
        self.speed_spin.setDecimals(2)
        self.speed_spin.setSingleStep(0.01)
        self.speed_spin.setSuffix(" mm/s")
        self.speed_spin.setValue(0.0)
        self.speed_spin.setFixedWidth(120)
        self.speed_spin.valueChanged.connect(self.on_speed_spin_changed)

        speed_control_layout.addWidget(QLabel("Speed:"))
        speed_control_layout.addWidget(self.speed_slider, 1)
        speed_control_layout.addWidget(self.speed_spin)

        speed_layout.addLayout(speed_control_layout)
        stage_layout.addWidget(speed_group)

        # Direction control
        direction_group = QGroupBox("Direction Control")
        direction_layout = QHBoxLayout(direction_group)
        direction_layout.setSpacing(20)

        self.forward_btn = QPushButton("Forward")
        self.forward_btn.setFixedSize(120, 40)
        self.forward_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)

        self.reverse_btn = QPushButton("Reverse")
        self.reverse_btn.setFixedSize(120, 40)
        self.reverse_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: black;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:pressed {
                background-color: #c69500;
            }
        """)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFixedSize(120, 40)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)

        # Connect signals
        self.forward_btn.clicked.connect(lambda: self.on_direction_control('forward'))
        self.reverse_btn.clicked.connect(lambda: self.on_direction_control('reverse'))
        self.stop_btn.clicked.connect(lambda: self.on_direction_control('stop'))

        direction_layout.addStretch()
        direction_layout.addWidget(self.forward_btn)
        direction_layout.addWidget(self.reverse_btn)
        direction_layout.addWidget(self.stop_btn)
        direction_layout.addStretch()

        stage_layout.addWidget(direction_group)

        # Status display (optional, commented out)
        # status_frame = QFrame()
        # status_layout = QHBoxLayout(status_frame)
        # status_layout.setContentsMargins(10, 10, 10, 10)

        # self.position_label = QLabel("Current Position: 0.00 mm")
        # self.position_label.setStyleSheet("font-size: 14px; padding: 8px; background-color: #f8f9fa; border-radius: 5px;")

        # self.motion_label = QLabel("Motion Status: Stopped")
        # self.motion_label.setStyleSheet("font-size: 14px; padding: 8px; background-color: #e9ecef; border-radius: 5px;")

        # status_layout.addWidget(self.position_label, 1)
        # status_layout.addWidget(self.motion_label, 1)

        #stage_layout.addWidget(status_frame)

        main_layout.addWidget(stage_group)

        #============ 4. Communication log section ============
        self.log_box = ESP32LogBox()
        main_layout.addWidget(self.log_box)

        # Initialize connection type
        self.on_conn_type_changed(0)

    def on_conn_type_changed(self, index):
        """Connection type changed"""
        if index == 0:  # Bluetooth
            self.scan_btn.setText("Scan")
            self.scan_btn.setToolTip("Scan for nearby Bluetooth devices")
        else:  # Serial
            self.scan_btn.setText("Scan")
            self.scan_btn.setToolTip("Scan for available serial ports")
        self.device_combo.clear()

    def on_scan_devices(self):
        """Scan devices"""
        self.device_combo.clear()

        if self.conn_type_combo.currentIndex() == 0:  # Bluetooth
            # Should implement actual Bluetooth scanning
            # For now, simulate some devices
            devices = [
                "ESP32_Laser_Controller (B8:D6:1A:5F:32:11)",
                "ESP32_Stage_Control (00:1A:7D:DA:71:13)",
                "ESP32_Device_001 (A4:CF:12:3E:9B:44)"
            ]
            self.device_combo.addItems(devices)
            if devices:
                self.device_combo.setCurrentIndex(0)
                QMessageBox.information(self, "Scan Complete", f"Found {len(devices)} Bluetooth devices")
        else:  # Serial
            ports = list_ports.comports()
            port_list = []
            for port in ports:
                # Format serial port info
                port_info = f"{port.device} - {port.description}"
                port_list.append(port_info)

            self.device_combo.addItems(port_list)
            if port_list:
                self.device_combo.setCurrentIndex(0)
                QMessageBox.information(self, "Scan Complete", f"Found {len(port_list)} serial ports")

    def on_connect(self):
        """Connect device"""
        device = self.device_combo.currentText()
        if not device:
            QMessageBox.warning(self, "Warning", "Please select a device first")
            return

        conn_type = "bluetooth" if self.conn_type_combo.currentIndex() == 0 else "serial"

        # Update UI state

        self.conn_status_label.setText("Status: Connected")
        self.conn_status_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")

        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.scan_btn.setEnabled(False)
        self.device_combo.setEnabled(False)
        self.conn_type_combo.setEnabled(False)

        # Send connection signal
        if conn_type == "bluetooth":
            pass
        else:
            import re
            match = re.search(r'\((COM\d+)\)', device)
            if match:
                device = match.group(1)
            self.comm_thread = SerialCommunicationThread(device)
            self.comm_thread.esp2main_command.connect(self.log_box.append_log)
            self.comm_thread.start()
            self.is_connected = True


        #QMessageBox.information(self, "Connection Successful", f"Connected to device: {device}")

    def on_disconnect(self):
        """Disconnect"""
        self.is_connected = False

        # Update UI state
        self.conn_status_label.setText("Status: Disconnected")
        self.conn_status_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")

        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.scan_btn.setEnabled(True)
        self.device_combo.setEnabled(True)
        self.conn_type_combo.setEnabled(True)

        # Send disconnect signal
        self.connect_signal.emit("disconnect", "")

    def on_laser_toggled(self, laser_id, state):
        """Laser toggle"""
        self.laser_states[laser_id] = state

        # Update button text
        btn = self.laser_btns[laser_id]
        btn.setText("ON" if state else "OFF")

        # Send laser control signal
        self.laser_signal.emit(laser_id + 1, state)
        while not self.comm_thread.main2esp_queue.empty():
            self.comm_thread.main2esp_queue.get()
        if state:
            self.comm_thread.main2esp_queue.put(f"l{laser_id}1")
        else:
            self.comm_thread.main2esp_queue.put(f"l{laser_id}0")

    def on_speed_changed(self, value):
        """Slider speed changed"""
        speed_value = value / 100.0  # 0-200 mapped to 0.0-2.0
        if abs(self.speed_spin.value() - speed_value) > 0.01:
            self.speed_spin.setValue(speed_value)
        self.current_speed = speed_value
        # Send speed signal in real time
        self.speed_signal.emit(speed_value)
        while not self.comm_thread.main2esp_queue.empty():
            self.comm_thread.main2esp_queue.get()
        self.comm_thread.main2esp_queue.put(f"s{speed_value}")

    def on_speed_spin_changed(self, value):
        """Spin box speed changed"""
        slider_value = int(value * 100)
        if self.speed_slider.value() != slider_value:
            self.speed_slider.setValue(slider_value)
        self.current_speed = value
        # Send speed signal in real time
        self.speed_signal.emit(value)
        while not self.comm_thread.main2esp_queue.empty():
            self.comm_thread.main2esp_queue.get()
        self.comm_thread.main2esp_queue.put(f"s{value}")

    def on_direction_control(self, direction):
        """Direction control"""
        if not self.is_connected:
            QMessageBox.warning(self, "Warning", "Please connect to a device first")
            return

        # # Update motion status display (commented)
        # if direction == 'forward':
        #     self.motion_label.setText("Motion Status: Forward")
        #     self.motion_label.setStyleSheet("font-size: 14px; padding: 8px; background-color: #d1ecf1; border-radius: 5px; color: #0c5460;")
        # elif direction == 'reverse':
        #     self.motion_label.setText("Motion Status: Reverse")
        #     self.motion_label.setStyleSheet("font-size: 14px; padding: 8px; background-color: #fff3cd; border-radius: 5px; color: #856404;")
        # else:  # stop
        #     self.motion_label.setText("Motion Status: Stopped")
        #     self.motion_label.setStyleSheet("font-size: 14px; padding: 8px; background-color: #e9ecef; border-radius: 5px; color: #495057;")

        # Send direction control signal
        self.direction_signal.emit(direction)
        while not self.comm_thread.main2esp_queue.empty():
            self.comm_thread.main2esp_queue.get()
        if direction == 'forward':
            self.comm_thread.main2esp_queue.put("d1")
        elif direction == 'reverse':
            self.comm_thread.main2esp_queue.put("d0")
        else:  # stop
            self.comm_thread.main2esp_queue.put("d9")

    def on_move(self):
        """Move to position (not used now)"""
        pass

    def update_position(self, position):
        """Update position display"""
        self.position_label.setText(f"Current Position: {position:.2f} mm")

    def update_motion_status(self, status):
        """Update motion status"""
        self.motion_label.setText(f"Motion Status: {status}")

    def update_connection_status(self, is_connected, message=""):
        """External update connection status"""
        self.is_connected = is_connected
        if is_connected:
            self.conn_status_label.setText("Status: Connected")
            self.conn_status_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
        else:
            self.conn_status_label.setText("Status: Disconnected")
            self.conn_status_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.scan_btn.setEnabled(True)
            self.device_combo.setEnabled(True)
            self.conn_type_combo.setEnabled(True)


class ESP32LogBox(QWidget):
    """ESP32 data receive log box"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Log box group
        log_group = QGroupBox("Data Receive Log")
        log_layout = QVBoxLayout(log_group)

        # Log display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        #self.log_text.setMaximumHeight(200)

        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)

    def append_log(self, message):
        """Add log message"""
        temp = f">>{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n"
        self.log_text.append(temp)


# Test code
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = ESP32Panel()
    window.setWindowTitle("ESP32 Control System")
    window.resize(900, 700)

    # Example signal connections
    window.home_signal.connect(lambda: print("Home signal emitted"))
    window.move_signal.connect(lambda pos: print(f"Move to: {pos}"))
    window.laser_signal.connect(lambda laser_id, state: print(f"Laser{laser_id}: {'ON' if state else 'OFF'}"))
    window.speed_signal.connect(lambda speed: print(f"Speed set: {speed} mm/s"))
    window.direction_signal.connect(lambda dir: print(f"Direction control: {dir}"))
    window.connect_signal.connect(lambda conn_type, device: print(f"Connection: {conn_type}, Device: {device}"))

    window.show()
    sys.exit(app.exec_())