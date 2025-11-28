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
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTimeEdit
from PyQt6.QtCore import Qt, QTime
from database import Database
import datetime

class EditAttendanceDialog(QDialog):
    def __init__(self, record_data, parent=None):
        super().__init__(parent)
        self.record_data = record_data
        self.db = Database()
        self.setWindowTitle("ویرایش رکورد حضور و غیاب")
        self.setFixedSize(400, 350)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Info labels
        self.name_label = QLabel()
        self.date_label = QLabel()
        layout.addWidget(self.name_label)
        layout.addWidget(self.date_label)

        # Entry time
        layout.addWidget(QLabel("ساعت ورود:"))
        self.entry_time_edit = QTimeEdit()
        self.entry_time_edit.setDisplayFormat("HH:mm:ss")
        layout.addWidget(self.entry_time_edit)

        # Exit time
        layout.addWidget(QLabel("ساعت خروج:"))
        self.exit_time_edit = QTimeEdit()
        self.exit_time_edit.setDisplayFormat("HH:mm:ss")
        layout.addWidget(self.exit_time_edit)

        # Buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        save_button = QPushButton("ذخیره تغییرات")
        save_button.clicked.connect(self.save)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("انصراف")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

    def load_data(self):
        self.name_label.setText(f"<b>کارمند:</b> {self.record_data['full_name']}")
        self.date_label.setText(f"<b>تاریخ:</b> {self.record_data['jalali_date']}")

        if 'entry_time' in self.record_data.keys() and self.record_data['entry_time']:
            entry_dt = datetime.datetime.fromisoformat(self.record_data['entry_time'])
            self.entry_time_edit.setTime(QTime(entry_dt.hour, entry_dt.minute, entry_dt.second))
        
        if 'exit_time' in self.record_data.keys() and self.record_data['exit_time']:
            exit_dt = datetime.datetime.fromisoformat(self.record_data['exit_time'])
            self.exit_time_edit.setTime(QTime(exit_dt.hour, exit_dt.minute, exit_dt.second))

    def save(self):
        attendance_id = self.record_data['id']
        
        # Update entry time
        entry_time = self.entry_time_edit.time().toString("HH:mm:ss")
        entry_datetime_str = f"{self.record_data['date']}T{entry_time}"
        self.db.update_attendance_time(attendance_id, 'entry_time', entry_datetime_str)

        # Update exit time
        exit_time = self.exit_time_edit.time().toString("HH:mm:ss")
        exit_datetime_str = f"{self.record_data['date']}T{exit_time}"
        self.db.update_attendance_time(attendance_id, 'exit_time', exit_datetime_str)
        
        QMessageBox.information(self, "موفق", "تغییرات با موفقیت ذخیره شد.")
        self.accept()