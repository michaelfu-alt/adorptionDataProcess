# controller/main_controller.py
from PySide6.QtWidgets import QMessageBox
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
        self.left_panel = view.left_panel
        self.right_panel = view.right_panel

        # 具体功能分模块
        self.sample_manager = SampleManager(self.model)
        self.db_manager = DBManager(self.model, self.view)
        self.import_export_manager = ImportExportManager(model, view)
    
    
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
    
    def on_sample_selected(self,sample_name):
        details = self.sample_manager.get_all_sample_details(sample_name)
        # print(f"{sample_name} is passed to maintroller")
        # print("[Controller] Send to right_panel info:", details["info"])
        # print("[Controller] Send to right_panel results:", details["results"])
        # 关键：更新 right_panel！
        self.view.right_panel.update_sample_details(details["info"], details["results"])
        self.view.right_panel.update_adsorption_data(details["ads"], details["des"])
        self.view.right_panel.update_psd_data(details["psd"])
    
    # Edit Sample info
    def edit_sample_info(self, sample_name):
        print(f"{sample_name} is passed to edit sample info in maincontroller")
        info = self.sample_manager.get_edit_sample_info(sample_name)
        print(f"info for editing: {info}")
        if not info:
            QMessageBox.warning(self.view, "No Data", f"No info for sample '{sample_name}'")
            return
        # 只在这里弹窗
        self.sample_manager.open_edit_dialog(sample_name, info, self.on_edit_save)

    def on_edit_save(self, sample_name, updated_info):
        # 保存
        self.sample_manager.save_sample_info(sample_name, updated_info)

        # 刷新LeftPanel表格（或主界面）
        self.view.left_panel.refresh_table()
        print("Maincontroller has updated leftpanel")

        # 刷新右侧panel
        details = self.sample_manager.get_all_sample_details(sample_name)
        self.view.right_panel.update_sample_details(details["info"], details["results"])
        self.view.right_panel.update_adsorption_data(details["ads"], details["des"])
        self.view.right_panel.update_psd_data(details["psd"])