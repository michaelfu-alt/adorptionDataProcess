from PySide6.QtWidgets import QFileDialog, QMessageBox

class DBManager:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def select_database(self):
        print("DBManager.select_database called")
        file_path, _ = QFileDialog.getOpenFileName(
            self.view, "选择SQLite数据库", "", "SQLite DB (*.db *.sqlite);;所有文件 (*)"
        )
        if file_path:
            self.model.connect_database(file_path)
            self.view.set_db_path(file_path)
            # 触发左侧表刷新

    def create_database(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self.view, "新建SQLite数据库", "", "SQLite DB (*.db *.sqlite)"
        )
        if file_path:
            self.model.create_new_database(file_path)
            self.view.set_db_path(file_path)
            # 触发左侧表刷新

    def backup_database(self):
        if not self.model.db_path:
            QMessageBox.warning(self.view, "未连接数据库", "请先选择数据库")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self.view, "备份数据库到...", "", "SQLite DB (*.db *.sqlite)"
        )
        if file_path:
            self.model.backup_database(file_path)
            QMessageBox.information(self.view, "备份完成", f"已保存到: {file_path}")

    def delete_database(self):
        if not self.model.db_path:
            QMessageBox.warning(self.view, "未连接数据库", "请先选择数据库")
            return
        reply = QMessageBox.question(self.view, "确认删除", "确定要永久删除当前数据库文件？")
        if reply == QMessageBox.Yes:
            self.model.delete_database()
            self.view.set_db_path("")  # 清空显示
            # 清空表和状态