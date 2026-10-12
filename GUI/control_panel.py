from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QDoubleSpinBox, QComboBox,
                             QTextEdit)
from PyQt5.QtCore import pyqtSignal

class ControlPanel(QWidget):
    start_preview = pyqtSignal()
    stop_preview = pyqtSignal()
    camera_params_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Camera control group
        camera_group = QGroupBox("Camera Control")
        camera_layout = QVBoxLayout(camera_group)

        # Preview control buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Preview")
        self.stop_btn = QPushButton("Stop Preview")
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)

        # Camera parameter settings
        params_layout = QHBoxLayout()
        params_layout.addWidget(QLabel("Exposure Time (ms):"))
        self.exposure_spin = QDoubleSpinBox()
        self.exposure_spin.setRange(1, 1000)
        self.exposure_spin.setValue(10.0)
        self.exposure_spin.setSingleStep(1.0)

        params_layout.addWidget(self.exposure_spin)
        params_layout.addStretch()

        camera_layout.addLayout(btn_layout)
        camera_layout.addLayout(params_layout)

        # Resolution settings
        binning_layout = QHBoxLayout()
        binning_layout.addWidget(QLabel("Binning:"))
        self.binning_combo = QComboBox()
        self.binning_combo.addItems(["1x1", "2x2", "4x4"])
        binning_layout.addWidget(self.binning_combo)
        camera_layout.addLayout(binning_layout)


        # Status info
        self.status_display = QTextEdit()
        self.status_display.setMaximumHeight(100)
        self.status_display.setReadOnly(True)

        layout.addWidget(camera_group)
        layout.addWidget(self.status_display)
        layout.addStretch()

        # Connect signals
        self.start_btn.clicked.connect(self.start_preview.emit)
        self.stop_btn.clicked.connect(self.stop_preview.emit)
        self.exposure_spin.valueChanged.connect(self.on_exposure_changed)
        self.binning_combo.valueChanged.connect(self.on_binning_changed)

        self.update_camera_info("Waiting to start...")

    def on_exposure_changed(self):
        """Camera parameter changed"""
        params = {
            'exposure': self.exposure_spin.value()
        }
        self.camera_params_changed.emit(params)
    def on_binning_changed(self):
        """Camera parameter changed"""
        params = {
            'binning': self.binning_combo.currentText()
        }
        self.camera_params_changed.emit(params)

    def update_camera_info(self, message):
        """Update status info"""
        self.status_display.append(f"> {message}")