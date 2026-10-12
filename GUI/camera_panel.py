from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QSpinBox,
                             QLabel, QPushButton, QDoubleSpinBox, QFileDialog)
from PyQt5.QtCore import pyqtSignal, QTimer
import os
import time
class CameraPanel(QWidget):
    start_preview = pyqtSignal()
    stop_preview = pyqtSignal()
    camera_params_exposure = pyqtSignal(float)
    camera_params_binning = pyqtSignal(int)
    camera_params_gain = pyqtSignal(float)
    camera_initialized = pyqtSignal(bool, str)

    def __init__(self, camera_controller):
        super().__init__()
        self.camera_controller = camera_controller
        self.snapshot_folder = os.getcwd() + "/snapshots"
        self.is_previewing = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Init group
        init_group = QGroupBox("Camera Control")
        init_layout = QVBoxLayout(init_group)

        # Init/close button
        init_btn_layout = QHBoxLayout()
        self.init_btn = QPushButton("Initialize Camera")
        init_btn_layout.addWidget(self.init_btn)

        # Camera status display
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("color: gray; font-weight: bold;")

        init_layout.addLayout(init_btn_layout)
        init_layout.addWidget(self.status_label)

        # Parameter settings group
        params_group = QGroupBox("Camera Parameters")
        params_layout = QVBoxLayout(params_group)

        # Exposure time
        exposure_layout = QHBoxLayout()
        exposure_layout.addWidget(QLabel("Exposure Time:"))
        self.exposure_spin = QDoubleSpinBox()
        self.exposure_spin.setRange(0.1, 1000)
        self.exposure_spin.setValue(10.0)
        self.exposure_spin.setSuffix(" ms")
        self.exposure_spin.setEnabled(False)
        self.exposure_spin.setFixedWidth(200)
        exposure_layout.addWidget(self.exposure_spin)
        exposure_layout.addStretch()

        # Binning
        binning_layout = QHBoxLayout()
        binning_layout.addWidget(QLabel("Binning:"))
        self.binning_spin = QSpinBox()
        self.binning_spin.setRange(1, 2)
        self.binning_spin.setValue(2)
        self.binning_spin.setSuffix("x")
        self.binning_spin.setEnabled(False)
        self.binning_spin.setFixedWidth(200)
        binning_layout.addWidget(self.binning_spin)
        binning_layout.addStretch()

        # Gain
        gain_layout = QHBoxLayout()
        gain_layout.addWidget(QLabel("Gain:"))
        self.gain_spin = QDoubleSpinBox()
        self.gain_spin.setRange(0, 20)
        self.gain_spin.setValue(1)
        self.gain_spin.setSuffix(" dB")
        self.gain_spin.setEnabled(False)
        self.binning_spin.setFixedWidth(200)
        gain_layout.addWidget(self.gain_spin)
        gain_layout.addStretch()


        # Frame rate display
        self.frame_rate_label = QLabel("Frame Rate: 0 FPS")

        # Add to layout

        params_layout.addLayout(exposure_layout)
        params_layout.addLayout(binning_layout)
        params_layout.addLayout(gain_layout)
        params_layout.addWidget(self.frame_rate_label)
        for label in [self.exposure_spin, self.binning_spin, self.gain_spin]:
            label.setStyleSheet("font-size: 9pt;")


        # Preview control group
        preview_group = QGroupBox("Preview Control")
        preview_layout = QHBoxLayout(preview_group)

        self.preview_btn = QPushButton("Start Preview")  # Combined preview button
        self.snapshot_btn = QPushButton("Snapshot")

        self.preview_btn.setEnabled(False)
        self.snapshot_btn.setEnabled(False)

        preview_layout.addWidget(self.preview_btn)
        preview_layout.addWidget(self.snapshot_btn)

        # Snapshot settings group
        snapshot_group = QGroupBox("Snapshot Settings")
        snapshot_layout = QVBoxLayout(snapshot_group)

        folder_layout = QHBoxLayout()
        self.folder_label = QLabel(f"Save to: {format_path_display(self.snapshot_folder)}")
        self.folder_label.setStyleSheet("color: gray; font-size: 9pt;")
        self.select_folder_btn = QPushButton("Select Folder")

        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.select_folder_btn)

        snapshot_layout.addLayout(folder_layout)

        layout.addWidget(init_group)
        layout.addWidget(params_group)
        layout.addWidget(preview_group)
        layout.addWidget(snapshot_group)
        layout.addStretch()

        # Connect signals
        self.init_btn.clicked.connect(self.toggle_camera)
        self.preview_btn.clicked.connect(self.toggle_preview)
        self.snapshot_btn.clicked.connect(self.take_snapshot)
        self.exposure_spin.valueChanged.connect(self.change_params_exposure)
        self.binning_spin.valueChanged.connect(self.change_params_binning)
        self.gain_spin.valueChanged.connect(self.change_params_gain)
        self.select_folder_btn.clicked.connect(self.select_snapshot_folder)

    def toggle_camera(self):
        """Toggle camera state: initialize or close"""
        if not self.camera_controller.is_connected:
            self.initialize_camera()
        else:
            self.close_camera()

    def initialize_camera(self):
        """Initialize camera"""
        self.init_btn.setEnabled(False)
        self.status_label.setText("Initializing...")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")

        try:
            # Call camera controller initialization
            success = self.camera_controller.init_camera()
            if success:
                self.status_label.setText("Connected")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                self.init_btn.setText("Close Camera")  # Update button text
                self.exposure_spin.setEnabled(True)
                self.preview_btn.setEnabled(True)  # Enable preview button
                self.snapshot_btn.setEnabled(True)
                self.binning_spin.setEnabled(True)
                self.gain_spin.setEnabled(True)
                message = "Camera initialized successfully"
            else:
                self.status_label.setText("Connection Failed")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                message = "Camera initialization failed"

        except Exception as e:
            success = False
            self.status_label.setText("Initialization Error")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            message = f"Camera initialization error: {str(e)}"

        # Re-enable button
        self.init_btn.setEnabled(True)

        # Send initialization complete signal
        self.camera_initialized.emit(success, message)

    def close_camera(self):
        """Close camera"""
        # If previewing, stop first
        if self.is_previewing:
            self.stop_preview.emit()

        # Close camera
        self.camera_controller.close_camera()

        # Update UI state
        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: gray; font-weight: bold;")
        self.init_btn.setText("Initialize Camera")  # Restore button text

        # Disable related controls
        self.exposure_spin.setEnabled(False)
        self.preview_btn.setEnabled(False)
        self.preview_btn.setText("Start Preview")  # Reset preview button text
        self.snapshot_btn.setEnabled(False)
        self.is_previewing = False

        # Send log
        self.camera_initialized.emit(False, "Camera closed")

    def toggle_preview(self):
        """Toggle preview state: start or stop"""
        if not self.is_previewing:
            self.start_preview.emit()
        else:
            self.stop_preview.emit()

    def set_preview_state(self, is_previewing):
        """Set preview state"""
        self.is_previewing = is_previewing
        if is_previewing:
            self.preview_btn.setText("Stop Preview")
            self.preview_btn.setStyleSheet("background-color: #ff6b6b; color: white;")

        else:
            self.preview_btn.setText("Start Preview")
            self.preview_btn.setStyleSheet("")  # Restore default style


    def change_params_exposure(self):
        """Camera parameter changed"""
        if self.camera_controller.is_connected:
            self.camera_params_exposure.emit(self.exposure_spin.value()*1000)

    def change_params_binning(self):
        """Camera parameter changed"""
        if self.camera_controller.is_connected:
            print(self.binning_spin.value(),isinstance(self.binning_spin.value(), int))

            self.camera_params_binning.emit(self.binning_spin.value())
    def change_params_gain(self):
        """Camera parameter changed"""
        if self.camera_controller.is_connected:
            self.camera_params_gain.emit(self.gain_spin.value())

    def update_frame_rate(self, fps):
        """Update frame rate display"""
        self.frame_rate_label.setText(f"Frame Rate: {fps:.1f} FPS")

    def take_snapshot(self):
        """Take a snapshot"""
        if self.camera_controller.is_connected:
            # Add snapshot logic here
            print(f"Snapshot saved to: {self.snapshot_folder}")
            ret = self.camera_controller.take_snapshot(self.snapshot_folder)
            if ret:
                print("Snapshot taken successfully")
            else:
                print("Snapshot failed")


    def select_snapshot_folder(self):
        """Select snapshot save folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Snapshot Folder", self.snapshot_folder)
        if folder:
            self.snapshot_folder = folder
            # Display shortened path
            display_path = folder
            if len(display_path) > 30:
                display_path = "..." + display_path[-27:]
            self.folder_label.setText(f"Save to: {display_path}")


def format_path_display(path):
    if len(path) > 20:
        return  path[-17:] + "..."
    else:
        return path