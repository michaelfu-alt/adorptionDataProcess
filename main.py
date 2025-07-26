# main.py
import sys
from PySide6.QtWidgets import QApplication
from view.main_view import MainView
# from controller.main_controller import MainController


class DummyController:
    """临时占位controller，后续换成你的MainController。"""
    pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_view = MainView(DummyController())
    main_view.show()
    sys.exit(app.exec())