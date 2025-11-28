from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QMessageBox, QTableWidget,
                            QTableWidgetItem, QHeaderView, QTabWidget,
                            QComboBox, QDateEdit, QLineEdit, QGroupBox,
                            QFileDialog)
from PyQt6.QtCore import Qt, QDate
from database import Database
from .styles import MAIN_STYLE
from .dialogs import AddWorkerDialog, EditWorkerDialog, EditAttendanceDialog
from utils.persian_utils import to_persian_number, to_english_number, gregorian_to_jalali, jalali_to_gregorian
from utils.export_utils import ExportManager
from persiantools.jdatetime import JalaliDate
from .widgets import JalaliDatePicker
import datetime

class AdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.export_manager = ExportManager()
        self._is_loading = False
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
        self.workers_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
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
        self.start_date = JalaliDatePicker()
        # Set to 30 days ago
        today_gregorian = datetime.date.today()
        start_gregorian = today_gregorian - datetime.timedelta(days=30)
        start_jalali = gregorian_to_jalali(start_gregorian)
        self.start_date.set_date(start_jalali)
        self.start_date.dateChanged.connect(lambda: self.filter_attendance())
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel("تا تاریخ:"))
        self.end_date = JalaliDatePicker()
        self.end_date.set_date(JalaliDate.today())
        self.end_date.dateChanged.connect(lambda: self.filter_attendance())
        filter_layout.addWidget(self.end_date)
        
        filter_layout.addStretch()
        
        layout.addWidget(filter_group)
        
        # Export buttons
        export_layout = QHBoxLayout()
        layout.addLayout(export_layout)
        
        # Edit button
        edit_attendance_button = QPushButton("ویرایش رکورد")
        edit_attendance_button.clicked.connect(self.edit_attendance_record)
        export_layout.addWidget(edit_attendance_button)
        
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
        self.attendance_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
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
            # Handle the created_at string properly
            created_date = datetime.datetime.strptime(worker['created_at'].split('.')[0], '%Y-%m-%d %H:%M:%S')
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
        start_jalali = self.start_date.get_date()
        end_jalali = self.end_date.get_date()
        start_date = jalali_to_gregorian(start_jalali)
        end_date = jalali_to_gregorian(end_jalali)
        
        self.current_attendance_records = self.db.get_all_attendance(str(start_date), str(end_date))
        self.display_attendance_records(self.current_attendance_records)
        
    def display_attendance_records(self, records):
        self._is_loading = True
        self.attendance_table.setRowCount(len(records))
        
        for row, record in enumerate(records):
            # Store record ID
            self.attendance_table.setVerticalHeaderItem(row, QTableWidgetItem(str(record['id'])))

            # Date
            date_item = QTableWidgetItem(to_persian_number(record['jalali_date']))
            date_item.setFlags(date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.attendance_table.setItem(row, 0, date_item)
            
            # Worker name
            name_item = QTableWidgetItem(record['full_name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.attendance_table.setItem(row, 1, name_item)
            
            # Personal number
            personal_num_item = QTableWidgetItem(record['personal_number'])
            personal_num_item.setFlags(personal_num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.attendance_table.setItem(row, 2, personal_num_item)
            
            # Entry time
            entry_time_str = ""
            if record['entry_time']:
                entry_dt = datetime.datetime.fromisoformat(record['entry_time'])
                entry_time_str = entry_dt.strftime('%H:%M:%S')
            self.attendance_table.setItem(row, 3, QTableWidgetItem(to_persian_number(entry_time_str)))
            
            # Exit time
            exit_time_str = ""
            if record['exit_time']:
                exit_dt = datetime.datetime.fromisoformat(record['exit_time'])
                exit_time_str = exit_dt.strftime('%H:%M:%S')
            self.attendance_table.setItem(row, 4, QTableWidgetItem(to_persian_number(exit_time_str)))

            # Total hours
            total_hours_str = "-"
            if record['total_hours'] and record['total_hours'] > 0:
                total_hours_str = f"{record['total_hours']:.2f} ساعت"
            total_hours_item = QTableWidgetItem(to_persian_number(total_hours_str))
            total_hours_item.setFlags(total_hours_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.attendance_table.setItem(row, 5, total_hours_item)
            
            # Status
            status_str = "در حال کار"
            if record['exit_time']:
                status_str = "تکمیل شده"
            status_item = QTableWidgetItem(status_str)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.attendance_table.setItem(row, 6, status_item)
        self._is_loading = False
    
    def filter_attendance(self):
        worker_id = self.worker_filter.currentData()
        start_jalali = self.start_date.get_date()
        end_jalali = self.end_date.get_date()
        start_date = jalali_to_gregorian(start_jalali)
        end_date = jalali_to_gregorian(end_jalali)
        
        if worker_id:
            db_records = self.db.get_worker_attendance(worker_id, str(start_date), str(end_date))
            worker_info = next((w for w in self.workers_table.workers_data if w['id'] == worker_id), None)
            
            records = []
            if worker_info:
                for record in db_records:
                    mutable_record = dict(record)
                    mutable_record['full_name'] = worker_info['full_name']
                    mutable_record['personal_number'] = worker_info['personal_number']
                    records.append(mutable_record)
        else:
            self.current_attendance_records = self.db.get_all_attendance(str(start_date), str(end_date))
            records = self.current_attendance_records
        
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

    def edit_attendance_record(self):
        current_row = self.attendance_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "خطا", "لطفاً یک رکورد را برای ویرایش انتخاب کنید.")
            return

        record_id = int(self.attendance_table.verticalHeaderItem(current_row).text())
        
        # Find the full record data
        record_data = next((r for r in self.current_attendance_records if r['id'] == record_id), None)

        if not record_data:
            QMessageBox.critical(self, "خطا", "رکورد مورد نظر یافت نشد.")
            return

        dialog = EditAttendanceDialog(record_data, self)
        if dialog.exec():
            self.filter_attendance()