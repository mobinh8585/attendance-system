# Modern and sleek stylesheet for the application
MAIN_STYLE = """
QWidget {
    background-color: #f5f5f5;
    font-family: 'B Nazanin', 'Tahoma';
    font-size: 14px;
    color: #333333;
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
    color: #0D47A1;
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
    color: #333;
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