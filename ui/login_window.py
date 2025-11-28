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