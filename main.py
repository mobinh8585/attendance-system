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