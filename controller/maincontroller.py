# controller/main_controller.py
from PySide6.QtWidgets import QMessageBox, QDialog, QApplication
from controller.sample_manager import SampleManager
from controller.db_manager import DBManager
from controller.import_export import ImportExportManager
from view.duplicate_sample_dialog import DuplicateFieldDialog, DuplicateDeleteDialog
import os
import sqlite3
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

        # Copy/Paste function
        self._copied_samples = []
        self._copied_db_path = None

        # 具体功能分模块
        self.sample_manager = SampleManager(self.model)
        self.db_manager = DBManager(self.model, self.view)
        # self.import_export_manager = ImportExportManager(model, view)
        self.import_manager = ImportExportManager(model)
        self.import_manager.import_error.connect(self.on_import_error)
        self.import_manager.import_finished.connect(self.on_import_finished)
    
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
        self.left_panel.set_status(f"{sample_name}")
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
        self.left_panel.set_status(f"{sample_name} is edited")

    # Delete sample info
    def delete_sample_info(self, sample_names):
        self.sample_manager.delete_samples(sample_names)
        self.left_panel.refresh_table()
        self.right_panel.clear()
        self.left_panel.set_status("已删除选中样品")

    #Find and delete Duplciate
    def find_duplicates(self):
        dup_groups = self.sample_manager.find_exact_duplicates_by_file_and_sample()
        if not dup_groups:
            QMessageBox.information(self.view, "No Duplicates", "No duplicates found with same File Name and Sample Name.")
            return

        # 计算默认删除项：每组保留 internal_name 最长的，其它选中删除
        to_delete = []
        for key, internal_names in dup_groups.items():
            # 保留最长 internal_name
            keep = max(internal_names, key=len)
            for n in internal_names:
                if n != keep:
                    to_delete.append(n)

        # 调用弹窗，弹窗支持预选 to_delete
        dlg = DuplicateDeleteDialog(dup_groups, preselect=to_delete, parent=self.view)
        dlg.deleteConfirmed.connect(self._on_delete_duplicates)
        dlg.exec()
    
    def _on_delete_duplicates(self, to_delete: list[str]):
        if not to_delete:
            return

        reply = QMessageBox.question(
            self.view, "Confirm Delete",
            f"Delete {len(to_delete)} duplicate sample(s)?\n\n"
            + "\n".join(to_delete[:10])
            + ("" if len(to_delete) <= 10 else "\n…"),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        errors = []
        for internal_name in to_delete:
            try:
                self.sample_manager.model.delete_sample(internal_name)
            except Exception as e:
                errors.append(f"Could not delete '{internal_name}': {str(e)}")

        self._load_sample_list()  # 你已有的刷新样品列表函数

        if errors:
            QMessageBox.critical(self.view, "Delete Errors", "\n".join(errors))
        else:
            QMessageBox.information(self.view, "Duplicates Removed", f"Deleted {len(to_delete)} duplicate sample(s).")
    
    # Context Menu from Right click
    def copy_samples(self):
        self._copied_samples = []
        selected_names = self.view.get_selected_sample_names()
        for name in selected_names:
            data = self.sample_manager.copy_sample_data(name)
            self._copied_samples.append(data)
        self.view.left_panel.set_status(f"Copied {len(self._copied_samples)} samples.")

    def paste_samples(self):
        if not self._copied_samples:
            self.view.show_message("No samples to paste.")
            return
        pasted = []
        for sample_data in self._copied_samples:
            new_name = self.sample_manager.paste_sample_data(sample_data)
            pasted.append(new_name)
        self._load_sample_list()
        self.view.show_message(f"Pasted {len(pasted)} samples:\n" + "\n".join(pasted))
        self.view.set_status(f"Pasted {len(pasted)} samples.")


    def _clone_sample_from_external_db(self, external_db_path, old_name):
        ext_conn = sqlite3.connect(external_db_path)
        ext_cur = ext_conn.cursor()
        cur_conn = self.model.conn
        cur_cur = cur_conn.cursor()

        ext_cur.execute("SELECT id, name FROM samples WHERE name = ?", (old_name,))
        row = ext_cur.fetchone()
        if row is None:
            ext_conn.close()
            raise KeyError(f"No such sample '{old_name}' in external DB.")
        old_id, sample_name = row

        # 生成新样品名
        base_name = sample_name
        new_name = base_name
        counter = 1
        while True:
            cur_cur.execute("SELECT 1 FROM samples WHERE name = ?", (new_name,))
            if cur_cur.fetchone():
                new_name = f"{base_name}_copy{counter}"
                counter += 1
            else:
                break

        cur_cur.execute("INSERT INTO samples (name) VALUES (?)", (new_name,))
        new_id = cur_cur.lastrowid

        # 复制关联表，示例复制 sample_info
        ext_cur.execute("SELECT field_name, field_value FROM sample_info WHERE sample_id = ?", (old_id,))
        for field_name, field_value in ext_cur.fetchall():
            cur_cur.execute(
                "INSERT INTO sample_info (sample_id, field_name, field_value) VALUES (?, ?, ?)",
                (new_id, field_name, field_value)
            )
        # 其他关联表同理复制 ...

        cur_conn.commit()
        ext_conn.close()
        return new_name

    def cut_samples(self):
        # 这里可以先调用 copy_samples，然后删除选中样品，示例：
        self.copy_samples()
        self.delete_samples()  # 你已有删除逻辑

    # Import Excel Files
    def start_import_files(self):
        self.import_manager.start_import(self.view.left_panel)

    def on_import_error(self):
        # Show message box or log
        pass

    def on_import_finished(self, loaded_files):
        self.view.left_panel.set_status(f"Import complete: {len(loaded_files)} files.")
        self.view.left_panel.refresh_sample_table()