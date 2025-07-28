# controller/main_controller.py
from controller.sample_manager import SampleManager
from controller.db_manager import DBManager
from controller.import_export import ImportExportManager
# from controller.batch_tools import 
# from controller.analysis_tools import AnalysisTools
# from controller.plot_tools import PlotTools
# from controller.play_tools import PlayTools

class MainController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

        # 具体功能分模块
        self.sample_manager = SampleManager(self)
        self.db_manager = DBManager(self.model, self.view)
        self.import_export_manager = ImportExportManager(model, view)
        # self.batch_tools = BatchTools(self)
        # self.analysis_tools = AnalysisTools(self)
        # self.plot_tools = PlotTools(self)
        # self.play_tools = PlayTools(self)
        # # self.dft_tools = DFTTools(self)

        # 可选: 初始化
        # self._init_ui_events()

    # def _init_ui_events(self):
    #     # 这里可以连接 view 的信号和 controller 的槽函数
    #     # 例如:
    #     self.view.on_sample_select = self.sample_manager.on_sample_select
    #     self.view.on_db_switch = self.db_manager.switch_database
    #     # ... 其它绑定

    # 也可以提供一些统一入口给主程序用
    # def load_samples(self):
    #     self.sample_manager.load_samples()

    # def export_samples(self):
    #     self.import_export.export_samples()
    
    def load_files(self):
        print("MainController.load_files called")
        self.import_export_manager.load_files()
    
    def select_database(self, db_path=None):
        print(f"MainController.select_database called, db_path={db_path}")
        self.db_manager.select_database(db_path)

    def create_database(self):
        print("MainController.create_database called")
        self.db_manager.create_database()

    def backup_database(self):
        print("MainController.backup_database called")
        self.db_manager.backup_database()
    
    def delete_database(self):
        print("MainController.delete_database called")
        self.db_manager.delete_database()