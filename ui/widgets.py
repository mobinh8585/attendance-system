from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSpinBox, QLabel, QPushButton, QCalendarWidget, QVBoxLayout, QDialog
from PyQt6.QtCore import pyqtSignal, QDate
from persiantools.jdatetime import JalaliDate
from utils.persian_utils import to_persian_number, to_english_number

class JalaliDatePicker(QWidget):
    dateChanged = pyqtSignal(JalaliDate)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.set_date(JalaliDate.today())
        
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        # Year spinbox
        self.year_spin = QSpinBox()
        self.year_spin.setRange(1300, 1500)
        self.year_spin.valueChanged.connect(self._on_date_changed)
        layout.addWidget(self.year_spin)
        
        layout.addWidget(QLabel("/"))
        
        # Month spinbox
        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        self.month_spin.valueChanged.connect(self._on_date_changed)
        layout.addWidget(self.month_spin)
        
        layout.addWidget(QLabel("/"))
        
        # Day spinbox
        self.day_spin = QSpinBox()
        self.day_spin.setRange(1, 31)
        self.day_spin.valueChanged.connect(self._on_date_changed)
        layout.addWidget(self.day_spin)
        
    def set_date(self, jalali_date):
        self.year_spin.setValue(jalali_date.year)
        self.month_spin.setValue(jalali_date.month)
        self.day_spin.setValue(jalali_date.day)
        
    def get_date(self):
        try:
            return JalaliDate(self.year_spin.value(), self.month_spin.value(), self.day_spin.value())
        except:
            return JalaliDate.today()
            
    def _on_date_changed(self):
        try:
            date = self.get_date()
            self.dateChanged.emit(date)
        except:
            pass