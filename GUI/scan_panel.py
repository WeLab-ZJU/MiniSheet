from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QDoubleSpinBox,
                             QFileDialog, QMessageBox, QLineEdit)
from PyQt5.QtCore import pyqtSignal, QDir
import os

class ScanPanel(QWidget):
    """Scan panel"""

    # signals
    scan_started = pyqtSignal(dict)
    normal_scan_started = pyqtSignal(dict)
    scan_stopped = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scanning = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ============ 1. Scan distance ============
        distance_group = QGroupBox("Scan Distance")
        distance_layout = QHBoxLayout(distance_group)

        distance_layout.addWidget(QLabel("Distance:"))

        self.distance_spin = QDoubleSpinBox()
        self.distance_spin.setRange(0.0, 1000.0)
        self.distance_spin.setSuffix(" mm")
        self.distance_spin.setValue(100.0)
        self.distance_spin.setDecimals(2)
        self.distance_spin.setSingleStep(1.0)
        self.distance_spin.setMinimumWidth(180)

        distance_layout.addWidget(self.distance_spin)
        distance_layout.addStretch()
        layout.addWidget(distance_group)

        # ============ 2. Save folder ============
        folder_group = QGroupBox("Save Folder")
        folder_layout = QVBoxLayout(folder_group)

        # Show folder path
        self.folder_edit = QLineEdit()
        self.folder_edit.setText(os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_data"))
        self.folder_edit.setPlaceholderText("Select folder to save scan data")
        self.folder_edit.setReadOnly(True)

        # Folder button
        folder_btn_layout = QHBoxLayout()
        self.browse_btn = QPushButton("Select Folder")
        self.browse_btn.clicked.connect(self.browse_folder)
        self.browse_btn.setFixedWidth(150)

        folder_btn_layout.addWidget(self.browse_btn)
        folder_btn_layout.addStretch()

        folder_layout.addWidget(self.folder_edit)
        folder_layout.addLayout(folder_btn_layout)
        layout.addWidget(folder_group)

        # ============ 3. Scan button ============
        self.scan_btn = QPushButton("Start Scan")
        self.scan_btn.clicked.connect(self.toggle_scan)
        self.update_button_style()

        layout.addWidget(self.scan_btn)
        layout.addStretch()

        # ======= 4. Normal scan button ===
        self.normal_scan_btn = QPushButton("Start Normal Scan")
        self.normal_scan_btn.clicked.connect(self.start_normal_scan)
        layout.addWidget(self.normal_scan_btn)
        layout.addStretch()

    def browse_folder(self):
        """Select folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            self.folder_edit.text(),
            QFileDialog.ShowDirsOnly
        )

        if folder:
            self.folder_edit.setText(folder)

    def toggle_scan(self):
        """Toggle scan"""
        if not self.scanning:
            self.start_scan()
        else:
            self.stop_scan()

    def start_scan(self):
        """Start scan"""

        if not self.validate_inputs():
            return

        scan_params = {
            'distance': self.distance_spin.value(),
            'folder': self.folder_edit.text().strip(),
        }

        # Update status and button
        self.scanning = True
        self.update_button_style()

        # Disable input controls (cannot modify during scan)
        self.set_inputs_enabled(False)

        # Emit start signal
        self.scan_started.emit(scan_params)

    def start_normal_scan(self):
        """Start normal scan"""

        if not self.validate_inputs():
            return

        scan_params = {
            'distance': self.distance_spin.value(),
            'folder': self.folder_edit.text().strip(),
        }

        # Update status and button
        self.scanning = True
        self.update_button_style()

        # Disable input controls (cannot modify during scan)
        self.set_inputs_enabled(False)

        # Emit start signal
        self.normal_scan_started.emit(scan_params)

    def stop_scan(self):
        """Stop scan"""
        self.scanning = False
        self.update_button_style()
        self.set_inputs_enabled(True)

        # Emit stop signal
        self.scan_stopped.emit()

    def on_scan_finished(self):
        """Scan finished"""
        self.scanning = False
        self.update_button_style()
        self.set_inputs_enabled(True)

    def update_button_style(self):
        """Update button style"""
        if self.scanning:
            self.scan_btn.setText("Stop Scan")
            self.scan_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    font-weight: bold;
                    padding: 10px;
                    font-size: 14px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
        else:
            self.scan_btn.setText("Start Scan")
            self.scan_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    font-weight: bold;
                    padding: 10px;
                    font-size: 14px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)

    def set_inputs_enabled(self, enabled):
        """Set inputs enabled"""
        self.distance_spin.setEnabled(enabled)
        self.folder_edit.setEnabled(enabled)
        self.browse_btn.setEnabled(enabled)
        self.normal_scan_btn.setEnabled(enabled)

    def validate_inputs(self):

        # Check folder
        folder = self.folder_edit.text().strip()
        if not folder:
            QMessageBox.warning(self, "Error", "Please select a folder")
            return False

        # Check folder exists
        if not os.path.exists(folder):
            QMessageBox.warning(self, "Error", "Folder does not exist")
            return False

        # Check folder writable
        if not os.access(folder, os.W_OK):
            QMessageBox.warning(self, "Error", "Folder is not writable")
            return False

        # Check distance
        distance = self.distance_spin.value()
        if distance <= 0:
            QMessageBox.warning(self, "Error", "Distance must be greater than 0")
            return False

        return True

    def get_scan_params(self):
        """Get scan params"""
        return {
            'distance(mm)': self.distance_spin.value(),
            'folder': self.folder_edit.text().strip()
        }