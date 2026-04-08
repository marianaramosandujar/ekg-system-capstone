#!/usr/bin/env python3
"""
Lightweight launcher for EKG System
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui_main import EKGApp

if __name__ == "__main__":
    # Disable high DPI scaling for better performance on some systems
    QApplication.setAttribute(Qt.AA_DisableHighDpiScaling, True)
    
    app = QApplication(sys.argv)
    
    # Use Fusion style for better cross-platform performance
    app.setStyle('Fusion')
    
    window = EKGApp()
    window.show()
    
    sys.exit(app.exec())