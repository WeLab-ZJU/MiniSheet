from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPushButton,
                             QHBoxLayout)
from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QTextCursor

class LogPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Log display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)

        # Control buttons
        control_layout = QHBoxLayout()
        self.clear_btn = QPushButton("Clear Log")
        self.save_btn = QPushButton("Save Log")

        control_layout.addWidget(self.clear_btn)
        control_layout.addWidget(self.save_btn)
        control_layout.addStretch()

        layout.addWidget(self.log_text)
        layout.addLayout(control_layout)

        # Connect signals
        self.clear_btn.clicked.connect(self.clear_log)
        self.save_btn.clicked.connect(self.save_log)

    def add_log(self, message, level="info"):
        """Add log message"""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")

        # Set color based on level
        if level == "error":
            color = "red"
            prefix = "[error]"
        elif level == "warning":
            color = "orange"
            prefix = "[warning]"
        else:
            color = "white"
            prefix = "[message]"

        log_entry = f'<span style="color: gray;">[{timestamp}]</span> <span style="color: {color};">{prefix} {message}</span><br>'

        # Add to log display
        self.log_text.append(log_entry)

        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

    def clear_log(self):
        """Clear log"""
        self.log_text.clear()

    def save_log(self):
        """Save log to file"""
        # Add save functionality here
        pass