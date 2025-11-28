I'll create a complete Persian user management app for you. This will be a comprehensive application with multiple files for better organization.

## Project Structure

```
persian_attendance_app/
│
├── main.py
├── database.py
├── models.py
├── ui/
│   ├── __init__.py
│   ├── styles.py
│   ├── login_window.py
│   ├── worker_window.py
│   ├── admin_window.py
│   └── dialogs.py
├── utils/
│   ├── __init__.py
│   ├── persian_utils.py
│   └── export_utils.py
└── requirements.txt
```

Let me create each file:

## requirements.txt

```txt
PyQt6==6.6.1
persiantools==4.1.0
jdatetime==4.1.1
pandas==2.1.4
openpyxl==3.1.2
reportlab==4.0.8
sqlite3
```

## main.py

```python
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QLocale
from PyQt6.QtGui import QFont
from database import Database
from ui.login_window import LoginWindow

def main():
    # Create application
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("سیستم مدیریت حضور و غیاب")
    app.setOrganizationName("شرکت شما")
    
    # Set default font for Persian support
    font = QFont("B Nazanin", 12)
    app.setFont(font)
    
    # Set layout direction to RTL
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    
    # Set locale to Persian
    locale = QLocale(QLocale.Language.Persian, QLocale.Country.Iran)
    QLocale.setDefault(locale)
    
    # Initialize database
    db = Database()
    db.init_db()
    
    # Create and show login window
    login_window = LoginWindow()
    login_window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

## database.py

```python
import sqlite3
import os
from datetime import datetime
import hashlib
from persiantools.jdatetime import JalaliDateTime

class Database:
    def __init__(self):
        self.db_path = "attendance.db"
        self.conn = None
        
    def connect(self):
        """Create database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Create workers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personal_number TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create attendance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER NOT NULL,
                entry_time TIMESTAMP,
                exit_time TIMESTAMP,
                date TEXT NOT NULL,
                jalali_date TEXT NOT NULL,
                total_hours REAL DEFAULT 0,
                FOREIGN KEY (worker_id) REFERENCES workers (id)
            )
        ''')
        
        # Create admin table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        
        # Create default admin if not exists
        cursor.execute("SELECT COUNT(*) FROM admin")
        if cursor.fetchone()[0] == 0:
            self.create_admin("admin", "admin123")
        
        conn.commit()
        conn.close()
    
    def create_admin(self, username, password):
        """Create admin user"""
        conn = self.connect()
        cursor = conn.cursor()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("INSERT INTO admin (username, password_hash) VALUES (?, ?)",
                      (username, password_hash))
        conn.commit()
        conn.close()
    
    def verify_admin(self, username, password):
        """Verify admin credentials"""
        conn = self.connect()
        cursor = conn.cursor()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("SELECT * FROM admin WHERE username = ? AND password_hash = ?",
                      (username, password_hash))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def add_worker(self, personal_number, full_name, phone=""):
        """Add new worker"""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO workers (personal_number, full_name, phone) VALUES (?, ?, ?)",
                          (personal_number, full_name, phone))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_worker_by_personal_number(self, personal_number):
        """Get worker by personal number"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workers WHERE personal_number = ?", (personal_number,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_all_workers(self):
        """Get all workers"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workers ORDER BY full_name")
        results = cursor.fetchall()
        conn.close()
        return results
    
    def record_entry(self, worker_id):
        """Record worker entry time"""
        conn = self.connect()
        cursor = conn.cursor()
        now = datetime.now()
        jalali_now = JalaliDateTime.now()
        date_str = now.strftime('%Y-%m-%d')
        jalali_date_str = jalali_now.strftime('%Y/%m/%d')
        
        # Check if already has entry today
        cursor.execute("SELECT * FROM attendance WHERE worker_id = ? AND date = ? AND exit_time IS NULL",
                      (worker_id, date_str))
        if cursor.fetchone():
            conn.close()
            return False, "شما قبلاً ورود خود را ثبت کرده‌اید"
        
        cursor.execute("INSERT INTO attendance (worker_id, entry_time, date, jalali_date) VALUES (?, ?, ?, ?)",
                      (worker_id, now, date_str, jalali_date_str))
        conn.commit()
        conn.close()
        return True, "ورود با موفقیت ثبت شد"
    
    def record_exit(self, worker_id):
        """Record worker exit time"""
        conn = self.connect()
        cursor = conn.cursor()
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        
        # Find today's entry without exit
        cursor.execute("SELECT * FROM attendance WHERE worker_id = ? AND date = ? AND exit_time IS NULL",
                      (worker_id, date_str))
        record = cursor.fetchone()
        
        if not record:
            conn.close()
            return False, "ابتدا باید ورود خود را ثبت کنید"
        
        # Calculate total hours
        entry_time = datetime.fromisoformat(record['entry_time'])
        total_hours = (now - entry_time).total_seconds() / 3600
        
        cursor.execute("UPDATE attendance SET exit_time = ?, total_hours = ? WHERE id = ?",
                      (now, total_hours, record['id']))
        conn.commit()
        conn.close()
        return True, f"خروج با موفقیت ثبت شد. مدت حضور: {total_hours:.2f} ساعت"
    
    def get_worker_attendance(self, worker_id, start_date=None, end_date=None):
        """Get worker attendance records"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE worker_id = ? AND date BETWEEN ? AND ?
                ORDER BY date DESC
            """, (worker_id, start_date, end_date))
        else:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE worker_id = ?
                ORDER BY date DESC
            """, (worker_id,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_all_attendance(self, start_date=None, end_date=None):
        """Get all attendance records with worker info"""
        conn = self.connect()
        cursor = conn.cursor()
        
        query = """
            SELECT a.*, w.full_name, w.personal_number 
            FROM attendance a
            JOIN workers w ON a.worker_id = w.id
        """
        
        if start_date and end_date:
            query += " WHERE a.date BETWEEN ? AND ?"
            cursor.execute(query + " ORDER BY a.date DESC, w.full_name", (start_date, end_date))
        else:
            cursor.execute(query + " ORDER BY a.date DESC, w.full_name")
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def delete_worker(self, worker_id):
        """Delete worker and their attendance records"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attendance WHERE worker_id = ?", (worker_id,))
        cursor.execute("DELETE FROM workers WHERE id = ?", (worker_id,))
        conn.commit()
        conn.close()
    
    def get_monthly_report(self, worker_id, year, month):
        """Get monthly report for a worker"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Create date range
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
        
        cursor.execute("""
            SELECT COUNT(*) as days_worked, SUM(total_hours) as total_hours
            FROM attendance
            WHERE worker_id = ? AND date >= ? AND date < ?
        """, (worker_id, start_date, end_date))
        
        result = cursor.fetchone()
        conn.close()
        return result
```

## ui/styles.py

```python
# Modern and sleek stylesheet for the application
MAIN_STYLE = """
QWidget {
    background-color: #f5f5f5;
    font-family: 'B Nazanin', 'Tahoma';
    font-size: 14px;
}

QMainWindow {
    background-color: #ffffff;
}

QPushButton {
    background-color: #2196F3;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    font-weight: bold;
    min-width: 100px;
}

QPushButton:hover {
    background-color: #1976D2;
}

QPushButton:pressed {
    background-color: #0D47A1;
}

QPushButton#dangerButton {
    background-color: #f44336;
}

QPushButton#dangerButton:hover {
    background-color: #d32f2f;
}

QPushButton#successButton {
    background-color: #4CAF50;
}

QPushButton#successButton:hover {
    background-color: #388E3C;
}

QLineEdit {
    padding: 10px;
    border: 2px solid #e0e0e0;
    border-radius: 5px;
    background-color: white;
}

QLineEdit:focus {
    border-color: #2196F3;
}

QLabel {
    color: #333333;
}

QLabel#titleLabel {
    font-size: 24px;
    font-weight: bold;
    color: #1976D2;
    padding: 10px;
}

QLabel#infoLabel {
    font-size: 16px;
    color: #555555;
    padding: 5px;
}

QTableWidget {
    background-color: white;
    alternate-background-color: #f9f9f9;
    border: 1px solid #e0e0e0;
    border-radius: 5px;
    gridline-color: #e0e0e0;
}

QTableWidget::item {
    padding: 5px;
}

QTableWidget::item:selected {
    background-color: #E3F2FD;
    color: #1976D2;
}

QHeaderView::section {
    background-color: #2196F3;
    color: white;
    padding: 10px;
    border: none;
    font-weight: bold;
}

QComboBox {
    padding: 8px;
    border: 2px solid #e0e0e0;
    border-radius: 5px;
    background-color: white;
}

QComboBox:focus {
    border-color: #2196F3;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #666;
}

QGroupBox {
    border: 2px solid #e0e0e0;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 10px;
    color: #1976D2;
    font-weight: bold;
}

QMessageBox {
    background-color: white;
}

QTabWidget::pane {
    border: 1px solid #e0e0e0;
    background-color: white;
}

QTabWidget::tab-bar {
    alignment: right;
}

QTabBar::tab {
    background-color: #e0e0e0;
    padding: 10px 20px;
    margin-left: 2px;
}

QTabBar::tab:selected {
    background-color: white;
    border-bottom: 3px solid #2196F3;
}

QTabBar::tab:hover {
    background-color: #f5f5f5;
}

QDateEdit {
    padding: 8px;
    border: 2px solid #e0e0e0;
    border-radius: 5px;
    background-color: white;
}

QDateEdit:focus {
    border-color: #2196F3;
}

QScrollBar:vertical {
    border: none;
    background-color: #f0f0f0;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #c0c0c0;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a0a0a0;
}
"""
```

## ui/login_window.py

```python
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLineEdit, QLabel, QMessageBox,
                            QGroupBox, QRadioButton)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPalette, QBrush
from database import Database
from .styles import MAIN_STYLE
from .worker_window import WorkerWindow
from .admin_window import AdminWindow

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("سیستم مدیریت حضور و غیاب")
        self.setFixedSize(500, 600)
        self.setStyleSheet(MAIN_STYLE)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_widget.setLayout(layout)
        
        # Title
        title_label = QLabel("سیستم مدیریت حضور و غیاب")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Login type selection
        type_group = QGroupBox("نوع ورود را انتخاب کنید")
        type_layout = QHBoxLayout()
        type_group.setLayout(type_layout)
        
        self.worker_radio = QRadioButton("کارمند")
        self.admin_radio = QRadioButton("مدیر")
        self.worker_radio.setChecked(True)
        
        type_layout.addWidget(self.worker_radio)
        type_layout.addWidget(self.admin_radio)
        layout.addWidget(type_group)
        
        # Login form
        form_group = QGroupBox("اطلاعات ورود")
        form_layout = QVBoxLayout()
        form_group.setLayout(form_layout)
        
        # Username/Personal number input
        self.username_label = QLabel("شماره پرسنلی:")
        form_layout.addWidget(self.username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("شماره پرسنلی خود را وارد کنید")
        form_layout.addWidget(self.username_input)
        
        # Password input (hidden by default)
        self.password_label = QLabel("رمز عبور:")
        self.password_label.hide()
        form_layout.addWidget(self.password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("رمز عبور")
        self.password_input.hide()
        form_layout.addWidget(self.password_input)
        
        layout.addWidget(form_group)
        
        # Login button
        self.login_button = QPushButton("ورود")
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)
        
        # Info label
        info_label = QLabel("توجه: رمز عبور پیش‌فرض مدیر: admin / admin123")
        info_label.setObjectName("infoLabel")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        # Connect radio buttons
        self.worker_radio.toggled.connect(self.on_type_changed)
        self.admin_radio.toggled.connect(self.on_type_changed)
        
        # Connect Enter key
        self.username_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)
        
    def on_type_changed(self):
        if self.admin_radio.isChecked():
            self.username_label.setText("نام کاربری:")
            self.username_input.setPlaceholderText("نام کاربری مدیر")
            self.password_label.show()
            self.password_input.show()
        else:
            self.username_label.setText("شماره پرسنلی:")
            self.username_input.setPlaceholderText("شماره پرسنلی خود را وارد کنید")
            self.password_label.hide()
            self.password_input.hide()
    
    def handle_login(self):
        if self.admin_radio.isChecked():
            # Admin login
            username = self.username_input.text().strip()
            password = self.password_input.text()
            
            if not username or not password:
                QMessageBox.warning(self, "خطا", "لطفاً نام کاربری و رمز عبور را وارد کنید")
                return
            
            if self.db.verify_admin(username, password):
                self.admin_window = AdminWindow()
                self.admin_window.show()
                self.close()
            else:
                QMessageBox.critical(self, "خطا", "نام کاربری یا رمز عبور اشتباه است")
        else:
            # Worker login
            personal_number = self.username_input.text().strip()
            
            if not personal_number:
                QMessageBox.warning(self, "خطا", "لطفاً شماره پرسنلی خود را وارد کنید")
                return
            
            worker = self.db.get_worker_by_personal_number(personal_number)
            if worker:
                self.worker_window = WorkerWindow(worker)
                self.worker_window.show()
                self.close()
            else:
                QMessageBox.critical(self, "خطا", "شماره پرسنلی یافت نشد")
```

## ui/worker_window.py

```python
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
```

## ui/admin_window.py

```python
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QMessageBox, QTableWidget,
                            QTableWidgetItem, QHeaderView, QTabWidget,
                            QComboBox, QDateEdit, QLineEdit, QGroupBox,
                            QFileDialog)
from PyQt6.QtCore import Qt, QDate
from database import Database
from .styles import MAIN_STYLE
from .dialogs import AddWorkerDialog, EditWorkerDialog
from utils.persian_utils import to_persian_number, gregorian_to_jalali
from utils.export_utils import ExportManager
from persiantools.jdatetime import JalaliDate
import datetime

class AdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.export_manager = ExportManager()
        self.init_ui()
        self.load_workers()
        self.load_all_attendance()
        
    def init_ui(self):
        self.setWindowTitle("پنل مدیریت")
        self.setMinimumSize(1000, 700)
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
        
        title_label = QLabel("پنل مدیریت سیستم")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        logout_button = QPushButton("خروج")
        logout_button.clicked.connect(self.logout)
        header_layout.addWidget(logout_button)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Workers tab
        self.workers_tab = QWidget()
        self.init_workers_tab()
        self.tabs.addTab(self.workers_tab, "مدیریت کارمندان")
        
        # Attendance tab
        self.attendance_tab = QWidget()
        self.init_attendance_tab()
        self.tabs.addTab(self.attendance_tab, "گزارش حضور و غیاب")
        
        # Reports tab
        self.reports_tab = QWidget()
        self.init_reports_tab()
        self.tabs.addTab(self.reports_tab, "گزارشات پیشرفته")
        
    def init_workers_tab(self):
        layout = QVBoxLayout()
        self.workers_tab.setLayout(layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        add_button = QPushButton("افزودن کارمند جدید")
        add_button.setObjectName("successButton")
        add_button.clicked.connect(self.add_worker)
        button_layout.addWidget(add_button)
        
        edit_button = QPushButton("ویرایش کارمند")
        edit_button.clicked.connect(self.edit_worker)
        button_layout.addWidget(edit_button)
        
        delete_button = QPushButton("حذف کارمند")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self.delete_worker)
        button_layout.addWidget(delete_button)
        
        button_layout.addStretch()
        
        # Workers table
        self.workers_table = QTableWidget()
        self.workers_table.setColumnCount(4)
        self.workers_table.setHorizontalHeaderLabels([
            "شماره پرسنلی", "نام و نام خانوادگی", "شماره تماس", "تاریخ ثبت"
        ])
        
        header = self.workers_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.workers_table)
        
    def init_attendance_tab(self):
        layout = QVBoxLayout()
        self.attendance_tab.setLayout(layout)
        
        # Filter group
        filter_group = QGroupBox("فیلترها")
        filter_layout = QHBoxLayout()
        filter_group.setLayout(filter_layout)
        
        # Worker filter
        filter_layout.addWidget(QLabel("کارمند:"))
        self.worker_filter = QComboBox()
        self.worker_filter.addItem("همه کارمندان", None)
        self.worker_filter.currentIndexChanged.connect(self.filter_attendance)
        filter_layout.addWidget(self.worker_filter)
        
        # Date filter
        filter_layout.addWidget(QLabel("از تاریخ:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.dateChanged.connect(self.filter_attendance)
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel("تا تاریخ:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.dateChanged.connect(self.filter_attendance)
        filter_layout.addWidget(self.end_date)
        
        filter_layout.addStretch()
        
        layout.addWidget(filter_group)
        
        # Export buttons
        export_layout = QHBoxLayout()
        layout.addLayout(export_layout)
        
        excel_button = QPushButton("خروجی Excel")
        excel_button.clicked.connect(lambda: self.export_attendance('excel'))
        export_layout.addWidget(excel_button)
        
        pdf_button = QPushButton("خروجی PDF")
        pdf_button.clicked.connect(lambda: self.export_attendance('pdf'))
        export_layout.addWidget(pdf_button)
        
        csv_button = QPushButton("خروجی CSV")
        csv_button.clicked.connect(lambda: self.export_attendance('csv'))
        export_layout.addWidget(csv_button)
        
        print_button = QPushButton("چاپ")
        print_button.clicked.connect(self.print_attendance)
        export_layout.addWidget(print_button)
        
        export_layout.addStretch()
        
        # Attendance table
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(7)
        self.attendance_table.setHorizontalHeaderLabels([
            "تاریخ", "کارمند", "شماره پرسنلی", "ساعت ورود", 
            "ساعت خروج", "مدت حضور", "وضعیت"
        ])
        
        header = self.attendance_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.attendance_table)
        
    def init_reports_tab(self):
        layout = QVBoxLayout()
        self.reports_tab.setLayout(layout)
        
        # Monthly report section
        monthly_group = QGroupBox("گزارش ماهانه")
        monthly_layout = QHBoxLayout()
        monthly_group.setLayout(monthly_layout)
        
        monthly_layout.addWidget(QLabel("کارمند:"))
        self.monthly_worker_combo = QComboBox()
        monthly_layout.addWidget(self.monthly_worker_combo)
        
        monthly_layout.addWidget(QLabel("سال:"))
        self.year_combo = QComboBox()
        current_jalali = JalaliDate.today()
        for year in range(current_jalali.year - 2, current_jalali.year + 2):
            self.year_combo.addItem(to_persian_number(str(year)), year)
        self.year_combo.setCurrentIndex(2)
        monthly_layout.addWidget(self.year_combo)
        
        monthly_layout.addWidget(QLabel("ماه:"))
        self.month_combo = QComboBox()
        months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                 "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        for i, month in enumerate(months, 1):
            self.month_combo.addItem(month, i)
        self.month_combo.setCurrentIndex(current_jalali.month - 1)
        monthly_layout.addWidget(self.month_combo)
        
        generate_button = QPushButton("تولید گزارش")
        generate_button.clicked.connect(self.generate_monthly_report)
        monthly_layout.addWidget(generate_button)
        
        monthly_layout.addStretch()
        
        layout.addWidget(monthly_group)
        
        # Report display
        self.report_display = QLabel()
        self.report_display.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 20px;
                font-size: 16px;
            }
        """)
        self.report_display.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.report_display)
        
    def load_workers(self):
        workers = self.db.get_all_workers()
        self.workers_table.setRowCount(len(workers))
        
        # Update combo boxes
        self.worker_filter.clear()
        self.worker_filter.addItem("همه کارمندان", None)
        self.monthly_worker_combo.clear()
        
        for row, worker in enumerate(workers):
            self.workers_table.setItem(row, 0, QTableWidgetItem(worker['personal_number']))
            self.workers_table.setItem(row, 1, QTableWidgetItem(worker['full_name']))
            self.workers_table.setItem(row, 2, QTableWidgetItem(worker['phone'] or '-'))
            
            # Convert created_at to Jalali
            created_date = datetime.datetime.fromisoformat(worker['created_at'])
            jalali_date = gregorian_to_jalali(created_date)
            self.workers_table.setItem(row, 3, QTableWidgetItem(
                to_persian_number(jalali_date.strftime('%Y/%m/%d'))
            ))
            
            # Add to combo boxes
            self.worker_filter.addItem(worker['full_name'], worker['id'])
            self.monthly_worker_combo.addItem(worker['full_name'], worker['id'])
        
        # Store worker data for later use
        self.workers_table.workers_data = workers
    
    def load_all_attendance(self):
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        
        records = self.db.get_all_attendance(str(start_date), str(end_date))
        self.display_attendance_records(records)
        
    def display_attendance_records(self, records):
        self.attendance_table.setRowCount(len(records))
        
        for row, record in enumerate(records):
            # Date
            self.attendance_table.setItem(row, 0, QTableWidgetItem(
                to_persian_number(record['jalali_date'])
            ))
            
            # Worker name
            self.attendance_table.setItem(row, 1, QTableWidgetItem(record['full_name']))
            
            # Personal number
            self.attendance_table.setItem(row, 2, QTableWidgetItem(record['personal_number']))
            
            # Entry time
            if record['entry_time']:
                entry_dt = datetime.datetime.fromisoformat(record['entry_time'])
                self.attendance_table.setItem(row, 3, QTableWidgetItem(
                    to_persian_number(entry_dt.strftime('%H:%M:%S'))
                ))
            
            # Exit time
            if record['exit_time']:
                exit_dt = datetime.datetime.fromisoformat(record['exit_time'])
                self.attendance_table.setItem(row, 4, QTableWidgetItem(
                    to_persian_number(exit_dt.strftime('%H:%M:%S'))
                ))
            else:
                self.attendance_table.setItem(row, 4, QTableWidgetItem("-"))
            
            # Total hours
            if record['total_hours'] > 0:
                self.attendance_table.setItem(row, 5, QTableWidgetItem(
                    to_persian_number(f"{record['total_hours']:.2f} ساعت")
                ))
            else:
                self.attendance_table.setItem(row, 5, QTableWidgetItem("-"))
            
            # Status
            if record['exit_time']:
                status = "تکمیل شده"
            else:
                status = "در حال کار"
            self.attendance_table.setItem(row, 6, QTableWidgetItem(status))
    
    def filter_attendance(self):
        worker_id = self.worker_filter.currentData()
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        
        if worker_id:
            records = self.db.get_worker_attendance(worker_id, str(start_date), str(end_date))
            # Add worker info to records
            worker_name = self.worker_filter.currentText()
            for record in records:
                record['full_name'] = worker_name
                worker_info = self.db.get_worker_by_personal_number(
                    next(w['personal_number'] for w in self.workers_table.workers_data 
                         if w['id'] == worker_id)
                )
                record['personal_number'] = worker_info['personal_number']
        else:
            records = self.db.get_all_attendance(str(start_date), str(end_date))
        
        self.display_attendance_records(records)
    
    def add_worker(self):
        dialog = AddWorkerDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if self.db.add_worker(data['personal_number'], data['full_name'], data['phone']):
                QMessageBox.information(self, "موفق", "کارمند جدید با موفقیت اضافه شد")
                self.load_workers()
            else:
                QMessageBox.critical(self, "خطا", "این شماره پرسنلی قبلاً ثبت شده است")
    
    def edit_worker(self):
        current_row = self.workers_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "خطا", "لطفاً یک کارمند را انتخاب کنید")
            return
        
        worker_data = self.workers_table.workers_data[current_row]
        dialog = EditWorkerDialog(worker_data, self)
        if dialog.exec():
            # Reload workers
            self.load_workers()
    
    def delete_worker(self):
        current_row = self.workers_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "خطا", "لطفاً یک کارمند را انتخاب کنید")
            return
        
        worker_data = self.workers_table.workers_data[current_row]
        reply = QMessageBox.question(
            self, "تأیید حذف",
            f"آیا از حذف {worker_data['full_name']} و تمام سوابق مربوطه اطمینان دارید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_worker(worker_data['id'])
            QMessageBox.information(self, "موفق", "کارمند با موفقیت حذف شد")
            self.load_workers()
            self.load_all_attendance()
    
    def generate_monthly_report(self):
        worker_id = self.monthly_worker_combo.currentData()
        if not worker_id:
            QMessageBox.warning(self, "خطا", "لطفاً یک کارمند را انتخاب کنید")
            return
        
        year = self.year_combo.currentData()
        month = self.month_combo.currentData()
        
        # Convert Jalali to Gregorian for database query
        jalali_start = JalaliDate(year, month, 1)
        if month == 12:
            jalali_end = JalaliDate(year + 1, 1, 1)
        else:
            jalali_end = JalaliDate(year, month + 1, 1)
        
        gregorian_start = jalali_start.to_gregorian()
        gregorian_end = jalali_end.to_gregorian()
        
        # Get attendance records
        records = self.db.get_worker_attendance(
            worker_id, 
            str(gregorian_start), 
            str(gregorian_end)
        )
        
        # Calculate statistics
        total_days = len(records)
        total_hours = sum(r['total_hours'] for r in records if r['total_hours'])
        
        # Generate report text
        worker_name = self.monthly_worker_combo.currentText()
        month_name = self.month_combo.currentText()
        
        report_text = f"""
        <h2>گزارش ماهانه</h2>
        <p><b>کارمند:</b> {worker_name}</p>
        <p><b>سال:</b> {to_persian_number(str(year))}</p>
        <p><b>ماه:</b> {month_name}</p>
        <hr>
        <p><b>تعداد روزهای حضور:</b> {to_persian_number(str(total_days))} روز</p>
        <p><b>مجموع ساعات کاری:</b> {to_persian_number(f"{total_hours:.2f}")} ساعت</p>
        <p><b>میانگین ساعات کاری روزانه:</b> {to_persian_number(f"{total_hours/total_days:.2f}" if total_days > 0 else "0")} ساعت</p>
        """
        
        self.report_display.setText(report_text)
    
    def export_attendance(self, format_type):
        # Get current attendance data
        data = []
        for row in range(self.attendance_table.rowCount()):
            row_data = []
            for col in range(self.attendance_table.columnCount()):
                item = self.attendance_table.item(row, col)
                row_data.append(item.text() if item else '')
            data.append(row_data)
        
        if not data:
            QMessageBox.warning(self, "خطا", "داده‌ای برای خروجی وجود ندارد")
            return
        
        # Get file path
        default_name = f"گزارش_حضور_غیاب_{JalaliDate.today().strftime('%Y_%m_%d')}"
        
        if format_type == 'excel':
            file_path, _ = QFileDialog.getSaveFileName(
                self, "ذخیره فایل Excel", default_name, "Excel Files (*.xlsx)"
            )
            if file_path:
                columns = ["تاریخ", "کارمند", "شماره پرسنلی", "ساعت ورود", 
                          "ساعت خروج", "مدت حضور", "وضعیت"]
                if self.export_manager.export_to_excel(data, columns, file_path):
                    QMessageBox.information(self, "موفق", "فایل Excel با موفقیت ذخیره شد")
        
        elif format_type == 'pdf':
            file_path, _ = QFileDialog.getSaveFileName(
                self, "ذخیره فایل PDF", default_name, "PDF Files (*.pdf)"
            )
            if file_path:
                columns = ["تاریخ", "کارمند", "شماره پرسنلی", "ساعت ورود", 
                          "ساعت خروج", "مدت حضور", "وضعیت"]
                if self.export_manager.export_to_pdf(data, columns, file_path, "گزارش حضور و غیاب"):
                    QMessageBox.information(self, "موفق", "فایل PDF با موفقیت ذخیره شد")
        
        elif format_type == 'csv':
            file_path, _ = QFileDialog.getSaveFileName(
                self, "ذخیره فایل CSV", default_name, "CSV Files (*.csv)"
            )
            if file_path:
                columns = ["تاریخ", "کارمند", "شماره پرسنلی", "ساعت ورود", 
                          "ساعت خروج", "مدت حضور", "وضعیت"]
                if self.export_manager.export_to_csv(data, columns, file_path):
                    QMessageBox.information(self, "موفق", "فایل CSV با موفقیت ذخیره شد")
    
    def print_attendance(self):
        # Get current attendance data
        data = []
        for row in range(self.attendance_table.rowCount()):
            row_data = []
            for col in range(self.attendance_table.columnCount()):
                item = self.attendance_table.item(row, col)
                row_data.append(item.text() if item else '')
            data.append(row_data)
        
        if not data:
            QMessageBox.warning(self, "خطا", "داده‌ای برای چاپ وجود ندارد")
            return
        
        columns = ["تاریخ", "کارمند", "شماره پرسنلی", "ساعت ورود", 
                  "ساعت خروج", "مدت حضور", "وضعیت"]
        
        if self.export_manager.print_data(data, columns, "گزارش حضور و غیاب", self):
            QMessageBox.information(self, "موفق", "چاپ با موفقیت انجام شد")
    
    def logout(self):
        from .login_window import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()
```

## ui/dialogs.py

```python
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from database import Database

class AddWorkerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("افزودن کارمند جدید")
        self.setFixedSize(400, 300)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Personal number
        layout.addWidget(QLabel("شماره پرسنلی:"))
        self.personal_number_input = QLineEdit()
        self.personal_number_input.setPlaceholderText("مثال: 1234")
        layout.addWidget(self.personal_number_input)
        
        # Full name
        layout.addWidget(QLabel("نام و نام خانوادگی:"))
        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("مثال: علی احمدی")
        layout.addWidget(self.full_name_input)
        
        # Phone
        layout.addWidget(QLabel("شماره تماس (اختیاری):"))
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("مثال: 09123456789")
        layout.addWidget(self.phone_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        save_button = QPushButton("ذخیره")
        save_button.clicked.connect(self.save)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("انصراف")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
    def save(self):
        personal_number = self.personal_number_input.text().strip()
        full_name = self.full_name_input.text().strip()
        
        if not personal_number or not full_name:
            QMessageBox.warning(self, "خطا", "شماره پرسنلی و نام الزامی است")
            return
        
        self.accept()
    
    def get_data(self):
        return {
            'personal_number': self.personal_number_input.text().strip(),
            'full_name': self.full_name_input.text().strip(),
            'phone': self.phone_input.text().strip()
        }

class EditWorkerDialog(QDialog):
    def __init__(self, worker_data, parent=None):
        super().__init__(parent)
        self.worker_data = worker_data
        self.db = Database()
        self.setWindowTitle("ویرایش کارمند")
        self.setFixedSize(400, 300)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Personal number (read-only)
        layout.addWidget(QLabel("شماره پرسنلی:"))
        self.personal_number_input = QLineEdit()
        self.personal_number_input.setText(self.worker_data['personal_number'])
        self.personal_number_input.setReadOnly(True)
        layout.addWidget(self.personal_number_input)
        
        # Full name
        layout.addWidget(QLabel("نام و نام خانوادگی:"))
        self.full_name_input = QLineEdit()
        self.full_name_input.setText(self.worker_data['full_name'])
        layout.addWidget(self.full_name_input)
        
        # Phone
        layout.addWidget(QLabel("شماره تماس:"))
        self.phone_input = QLineEdit()
        self.phone_input.setText(self.worker_data['phone'] or '')
        layout.addWidget(self.phone_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        save_button = QPushButton("ذخیره تغییرات")
        save_button.clicked.connect(self.save)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("انصراف")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
    def save(self):
        full_name = self.full_name_input.text().strip()
        
        if not full_name:
            QMessageBox.warning(self, "خطا", "نام الزامی است")
            return
        
        # Update worker in database
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE workers 
            SET full_name = ?, phone = ?
            WHERE id = ?
        """, (full_name, self.phone_input.text().strip(), self.worker_data['id']))
        conn.commit()
        conn.close()
        
        self.accept()
```

## utils/persian_utils.py

```python
from persiantools import digits
from persiantools.jdatetime import JalaliDateTime, JalaliDate
import datetime

def to_persian_number(text):
    """Convert English numbers to Persian numbers"""
    return digits.en_to_fa(str(text))

def to_english_number(text):
    """Convert Persian numbers to English numbers"""
    return digits.fa_to_en(str(text))

def gregorian_to_jalali(gregorian_date):
    """Convert Gregorian date to Jalali date"""
    if isinstance(gregorian_date, datetime.datetime):
        return JalaliDateTime.from_datetime(gregorian_date)
    elif isinstance(gregorian_date, datetime.date):
        return JalaliDate.from_date(gregorian_date)
    else:
        return None

def jalali_to_gregorian(jalali_date):
    """Convert Jalali date to Gregorian date"""
    if isinstance(jalali_date, JalaliDateTime):
        return jalali_date.to_datetime()
    elif isinstance(jalali_date, JalaliDate):
        return jalali_date.to_date()
    else:
        return None

def format_jalali_datetime(datetime_str):
    """Format datetime string to Jalali datetime"""
    dt = datetime.datetime.fromisoformat(datetime_str)
    return JalaliDateTime.from_datetime(dt)

def get_persian_month_name(month_number):
    """Get Persian month name from number"""
    months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
              "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
    return months[month_number - 1] if 1 <= month_number <= 12 else ""

def get_persian_weekday_name(weekday_number):
    """Get Persian weekday name from number"""
    weekdays = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
    return weekdays[weekday_number] if 0 <= weekday_number <= 6 else ""
```

## utils/export_utils.py

```python
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
import csv
import os
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QTextDocument
from utils.persian_utils import to_persian_number
from persiantools.jdatetime import JalaliDateTime

class ExportManager:
    def __init__(self):
        # Register Persian font for PDF if available
        try:
            # You need to have a Persian font file (like BNazanin.ttf) in your system
            # This is a placeholder - adjust path as needed
            if os.path.exists("fonts/BNazanin.ttf"):
                pdfmetrics.registerFont(TTFont('BNazanin', 'fonts/BNazanin.ttf'))
                self.persian_font = 'BNazanin'
            else:
                self.persian_font = 'Helvetica'
        except:
            self.persian_font = 'Helvetica'
    
    def export_to_excel(self, data, columns, file_path):
        """Export data to Excel file"""
        try:
            df = pd.DataFrame(data, columns=columns)
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='گزارش', index=False)
                
                # Get the workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['گزارش']
                
                # Set RTL direction
                worksheet.sheet_view.rightToLeft = True
                
                # Adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            return True
        except Exception as e:
            print(f"Export to Excel error: {e}")
            return False
    
    def export_to_pdf(self, data, columns, file_path, title="گزارش"):
        """Export data to PDF file"""
        try:
            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
            elements = []
            
            # Create styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=self.persian_font,
                fontSize=24,
                textColor=colors.HexColor('#1976D2'),
                spaceAfter=30,
                alignment=1  # Center alignment
            )
            
            # Add title
            elements.append(Paragraph(title, title_style))
            
            # Add timestamp
            now = JalaliDateTime.now()
            timestamp = f"تاریخ گزارش: {to_persian_number(now.strftime('%Y/%m/%d - %H:%M'))}"
            elements.append(Paragraph(timestamp, styles['Normal']))
            elements.append(Paragraph("<br/><br/>", styles['Normal']))
            
            # Create table data with headers
            table_data = [columns] + data
            
            # Create table
            table = Table(table_data)
            
            # Apply table style
            table_style = TableStyle([
                # Header style
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), self.persian_font),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Data style
                ('FONTNAME', (0, 1), (-1, -1), self.persian_font),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ])
            
            table.setStyle(table_style)
            elements.append(table)
            
            # Build PDF
            doc.build(elements)
            return True
        except Exception as e:
            print(f"Export to PDF error: {e}")
            return False
    
    def export_to_csv(self, data, columns, file_path):
        """Export data to CSV file"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(columns)
                writer.writerows(data)
            return True
        except Exception as e:
            print(f"Export to CSV error: {e}")
            return False
    
    def print_data(self, data, columns, title, parent_widget):
        """Print data using system print dialog"""
        try:
            # Create HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl">
            <head>
                <meta charset="utf-8">
                <style>
                    body {{
                        font-family: 'B Nazanin', Tahoma, Arial;
                        direction: rtl;
                        text-align: right;
                    }}
                    h1 {{
                        color: #1976D2;
                        text-align: center;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 20px;
                    }}
                    th {{
                        background-color: #2196F3;
                        color: white;
                        padding: 10px;
                        text-align: center;
                        border: 1px solid #ddd;
                    }}
                    td {{
                        padding: 8px;
                        text-align: center;
                        border: 1px solid #ddd;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f5f5f5;
                    }}
                    .timestamp {{
                        text-align: center;
                        color: #666;
                        margin-top: 10px;
                    }}
                </style>
            </head>
            <body>
                <h1>{title}</h1>
                <p class="timestamp">تاریخ: {to_persian_number(JalaliDateTime.now().strftime('%Y/%m/%d - %H:%M'))}</p>
                <table>
                    <thead>
                        <tr>
            """
            
            # Add headers
            for col in columns:
                html_content += f"<th>{col}</th>"
            
            html_content += """
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # Add data rows
            for row in data:
                html_content += "<tr>"
                for cell in row:
                    html_content += f"<td>{cell}</td>"
                html_content += "</tr>"
            
            html_content += """
                    </tbody>
                </table>
            </body>
            </html>
            """
            
            # Create printer and document
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            dialog = QPrintDialog(printer, parent_widget)
            
            if dialog.exec():
                document = QTextDocument()
                document.setHtml(html_content)
                document.print(printer)
                return True
            
            return False
        except Exception as e:
            print(f"Print error: {e}")
            return False
```

## ui/__init__.py

```python
# UI package initialization file
```

## utils/__init__.py

```python
# Utils package initialization file
```

## Installation and Running Instructions

1. **Install Python 3.8 or higher**

2. **Install required packages:**
```bash
pip install PyQt6 persiantools jdatetime pandas openpyxl reportlab
```

3. **Download Persian fonts (optional but recommended):**
   - Download "B Nazanin" font and place it in a `fonts` directory in your project root
   - This will improve Persian text rendering in PDFs

4. **Run the application:**
```bash
python main.py
```

## Features Summary

### Worker Features:
- Login with personal number
- Clock in/out with single button click
- View personal attendance history
- Real-time Persian date/time display

### Admin Features:
- Secure login (default: admin/admin123)
- Complete worker management (add, edit, delete)
- View all attendance records with filtering
- Generate monthly reports
- Export to Excel, PDF, and CSV
- Print functionality
- Custom date range reports
- RTL support throughout

### Technical Features:
- SQLite database for offline storage
- Persian (Jalali) calendar support
- Modern, sleek Material Design-inspired UI
- Fully RTL interface
- Persian number display
- Comprehensive error handling
- Modular architecture for easy maintenance

## Usage Notes

1. **First Run:** The application will create a SQLite database file (`attendance.db`) in the application directory

2. **Admin Access:** Default admin credentials are:
   - Username: `admin`
   - Password: `admin123`

3. **Adding Workers:** Admin must add workers before they can use the system

4. **Date Format:** All dates are displayed in Persian (Jalali) calendar format

5. **Export Formats:**
   - Excel: Full formatting with RTL support
   - PDF: Formatted report with Persian font support
   - CSV: Simple comma-separated format

6. **Backup:** The `attendance.db` file contains all data - backup this file regularly

This complete application provides a professional attendance management system with full Persian language support, modern UI, and comprehensive reporting features.