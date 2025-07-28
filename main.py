# main.py
import sys
from PySide6.QtWidgets import QApplication
from model.database_model import DatabaseModel
from controller.maincontroller import MainController
from view.main_view import MainView
from utils.db_history import load_db_history

if __name__ == "__main__":
    app = QApplication(sys.argv)
    model = DatabaseModel()
    main_view = MainView(controller=None)  # 先传 None
    main_controller = MainController(model, main_view)


    # 加载上次数据库
    db_history = load_db_history()
    last_db = db_history.get("last")
    if last_db:
        main_view.left_panel.bind_controller(main_controller, last_db=last_db)    
    main_view.show()
    sys.exit(app.exec())