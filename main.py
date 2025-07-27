# main.py
import sys
from PySide6.QtWidgets import QApplication
from model.database_model import DatabaseModel
from controller.maincontroller import MainController
from view.main_view import MainView

if __name__ == "__main__":
    app = QApplication(sys.argv)
    model = DatabaseModel()
    main_view = MainView(controller=None)  # 先传 None
    main_controller = MainController(model, main_view)
    main_view.left_panel.controller = main_controller
    main_view.show()
    sys.exit(app.exec())