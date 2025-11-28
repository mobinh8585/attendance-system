from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QMessageBox, QTableWidget,
                            QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QTimer, QDateTime
from PyQt6.QtGui import QIcon
from database import Database
from .styles import MAIN_STYLE
from utils.persian_utils import to_persian_number, format_jalali_datetime
from persiantools.jdatetime import JalaliDateTime

class WorkerWindow(QMainWindow):
    def __init__(self, worker_info):
        super().__init__()
        self.worker_info = worker_info
        self.db = Database()
        self.init_ui()
        self.load_attendance_history()
        
    def init_ui(self):
        self.setWindowTitle(f"پنل کارمند - {self.worker_info['full_name']}")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(MAIN_STYLE)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Header
        header_layout = QHBoxLayout()
        layout.addLayout(header_layout)
        
        # Welcome message
        welcome_label = QLabel(f"خوش آمدید، {self.worker_info['full_name']}")
        welcome_label.setObjectName("titleLabel")
        header_layout.addWidget(welcome_label)
        
        header_layout.addStretch()
        
        # Current date and time
        self.datetime_label = QLabel()
        self.datetime_label.setObjectName("infoLabel")
        header_layout.addWidget(self.datetime_label)
        
        # Update time every second
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)
        self.update_datetime()
        
        # Action buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        self.entry_button = QPushButton("ثبت ورود")
        self.entry_button.setObjectName("successButton")
        self.entry_button.clicked.connect(self.record_entry)
        button_layout.addWidget(self.entry_button)
        
        self.exit_button = QPushButton("ثبت خروج")
        self.exit_button.setObjectName("dangerButton")
        self.exit_button.clicked.connect(self.record_exit)
        button_layout.addWidget(self.exit_button)
        
        button_layout.addStretch()
        
        # Logout button
        logout_button = QPushButton("خروج از سیستم")
        logout_button.clicked.connect(self.logout)
        button_layout.addWidget(logout_button)
        
        # Attendance history table
        history_label = QLabel("سوابق حضور و غیاب")
        history_label.setObjectName("titleLabel")
        layout.addWidget(history_label)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "تاریخ", "ساعت ورود", "ساعت خروج", "مدت حضور (ساعت)", "وضعیت"
        ])
        
        # Set column stretch
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.history_table)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
    def update_datetime(self):
        now = JalaliDateTime.now()
        self.datetime_label.setText(to_persian_number(now.strftime('%Y/%m/%d - %H:%M:%S')))
    
    def record_entry(self):
        success, message = self.db.record_entry(self.worker_info['id'])
        if success:
            QMessageBox.information(self, "موفق", message)
            self.load_attendance_history()
        else:
            QMessageBox.warning(self, "خطا", message)
    
    def record_exit(self):
        success, message = self.db.record_exit(self.worker_info['id'])
        if success:
            QMessageBox.information(self, "موفق", message)
            self.load_attendance_history()
        else:
            QMessageBox.warning(self, "خطا", message)
    
    def load_attendance_history(self):
        records = self.db.get_worker_attendance(self.worker_info['id'])
        self.history_table.setRowCount(len(records))
        
        for row, record in enumerate(records):
            # Date
            self.history_table.setItem(row, 0, QTableWidgetItem(
                to_persian_number(record['jalali_date'])
            ))
            
            # Entry time
            if record['entry_time']:
                entry_time = format_jalali_datetime(record['entry_time'])
                self.history_table.setItem(row, 1, QTableWidgetItem(
                    to_persian_number(entry_time.strftime('%H:%M:%S'))
                ))
            
            # Exit time
            if record['exit_time']:
                exit_time = format_jalali_datetime(record['exit_time'])
                self.history_table.setItem(row, 2, QTableWidgetItem(
                    to_persian_number(exit_time.strftime('%H:%M:%S'))
                ))
            else:
                self.history_table.setItem(row, 2, QTableWidgetItem("-"))
            
            # Total hours
            if record['total_hours'] > 0:
                self.history_table.setItem(row, 3, QTableWidgetItem(
                    to_persian_number(f"{record['total_hours']:.2f}")
                ))
            else:
                self.history_table.setItem(row, 3, QTableWidgetItem("-"))
            
            # Status
            if record['exit_time']:
                status = "تکمیل شده"
            else:
                status = "در حال کار"
            self.history_table.setItem(row, 4, QTableWidgetItem(status))
    
    def logout(self):
        from .login_window import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()