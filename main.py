"""
build with:
1) python -m nuitka --follow-imports --windows-console-mode=disable main.py
2) pyinstaller --noconsole --onefile main.spec
"""

import sys
from SamGui.MVVM.view import AppView
from SamGui.MVVM.model import DataModel
from SamGui.MVVM.viewmodel import SamViewModel
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication
from SamGui.Utils import get_screen_center


if __name__ == '__main__':
    app = QApplication()
    model = DataModel()
    view_model = SamViewModel(model)
    app_view = AppView(view_model)
    screen_data = get_screen_center(app)
    app_view.resize(screen_data.start_width, screen_data.start_height)
    app_view.move(QPoint(screen_data.start_x, screen_data.start_y))

    sys.exit(app.exec())