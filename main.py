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
    history = db_history.get("history", [])
    last_db = db_history.get("last")
    print(db_history)
    history = db_history.get("history", [])
    
    # 1. 把历史数据库加到 combobox
    for db_path in reversed(history):
        main_view.left_panel.update_db_combo(db_path)
    # 2. 绑定 controller，自动连接 last_db
    main_view.left_panel.bind_controller(main_controller, last_db=last_db)
    main_view.left_panel.connect_signals()

    
    main_view.show()
    sys.exit(app.exec())
