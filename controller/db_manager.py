from PySide6.QtWidgets import QFileDialog, QMessageBox
import shutil
from utils.db_history import save_db_history
import os

class DBManager:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def select_database(self, db_name=None):
        if db_name is None:
            # 只有按钮调用才弹出文件选择
            file_path, _ = QFileDialog.getOpenFileName(
                self.view, "选择SQLite数据库", "", "SQLite DB (*.db *.sqlite);;所有文件 (*)"
            )
            db_name = file_path
            if not db_name:
                return  # 用户取消选择
        # 此时 db_name 一定是全路径
        print("Connecting to", db_name)
        try:
            self.model.connect_database(db_name)
            self._update_db_history(db_name)
            self.view.left_panel.set_status(f"Database loaded: {os.path.basename(db_name)}")
            self._update_db_history(db_name)   # 数据库路径存储
            print("[DEBUG] DB history saved:", db_name)

            # ... 刷新相关内容
        except Exception as e:
            self.view.left_panel.set_status(f"数据库连接失败: {e}")
        self.view.left_panel.refresh_sample_table()
        


    def _update_db_history(self, db_path):
        # 只显示文件名，存储全路径
        exist_paths = [self.view.left_panel.db_combo.itemData(i) for i in range(self.view.left_panel.db_combo.count())]
        filename = os.path.basename(db_path)
        if db_path not in exist_paths:
            self.view.left_panel.db_combo.addItem(filename, userData=db_path)
        # 设置当前
        idx = exist_paths.index(db_path) if db_path in exist_paths else self.view.left_panel.db_combo.count() - 1
        self.view.left_panel.db_combo.setCurrentIndex(idx)
        # 存储历史
        all_db = [self.view.left_panel.db_combo.itemData(i) for i in range(self.view.left_panel.db_combo.count())]
        save_db_history(all_db, db_path)


    def create_database(self):
        # 弹出文件保存对话框
        db_path, _ = QFileDialog.getSaveFileName(
            self.view, "新建数据库", "", "SQLite DB (*.db *.sqlite)"
        )
        if db_path:
            self.model.create_new_database(db_path)
            self.view.left_panel.update_db_combo(db_path)
            self.view.left_panel.set_status(f"新数据库已创建: {db_path}")
        self._update_db_history(db_path) 

    
    def backup_database(self):
        db_path = getattr(self.model, "db_path", None)
        if not db_path:
            QMessageBox.warning(self.view, "未连接数据库", "请先选择数据库")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self.view, "备份数据库到...", db_path, "SQLite DB (*.db *.sqlite);;所有文件 (*)"
        )
        if file_path:
            try:
                shutil.copyfile(db_path, file_path)
                QMessageBox.information(self.view, "备份完成", f"已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self.view, "备份失败", f"备份出错: {e}")
        self._update_db_history(db_path) 

    def delete_database(self):
        if not self.model.db_path:
            QMessageBox.warning(self.view, "未连接数据库", "请先选择数据库")
            return
        reply = QMessageBox.question(
            self.view, "确认删除",
            f"确定要永久删除当前数据库文件？\n\n{self.model.db_path}",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.model.delete_database()  # 下面会补全
                self.view.left_panel.clear_db_combo()
                self.view.left_panel.set_status("数据库已删除")
                QMessageBox.information(self.view, "删除完成", "数据库已删除。")
            except Exception as e:
                QMessageBox.critical(self.view, "删除失败", f"删除数据库时出错：\n{e}")

    def update_db_history(self, db_path):
        """
        db_path: 新切换/新建/当前操作的数据库全路径
        """
        db_combo = self.view.left_panel.db_combo
        # 全部历史：存储完整路径
        history = [db_combo.itemData(i) for i in range(db_combo.count()) if db_combo.itemData(i)]
        if db_path and db_path not in history:
            history.append(db_path)
        save_db_history(history, db_path)