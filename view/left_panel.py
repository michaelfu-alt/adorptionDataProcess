# view/left_panel.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel, QGroupBox,
    QTableWidget, QTableWidgetItem, QMenu, QAbstractItemView, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal
import os

class LeftPanel(QWidget):
    # 可定义自定义信号，例如
    # sampleSelected = Signal(str)

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6,6,6,6)
        layout.setSpacing(8)

        # db_data = load_db_history()
        # last_db = db_data.get("last", "")
        # if last_db:
        #     self.controller.select_database(last_db)


        # Database 操作区
        db_group = QGroupBox("Database")
        db_layout = QHBoxLayout()
        self.db_combo = QComboBox()
        self.db_combo.setEditable(False)
        self.db_combo.setEnabled(False) 
        db_layout.addWidget(self.db_combo, 4)
        self.btn_select_db = QPushButton("Select DB")
        self.btn_new_db = QPushButton("New DB")
        self.btn_backup_db = QPushButton("Backup DB")
        self.btn_delete_db = QPushButton("Delete DB")
        db_layout.addWidget(self.btn_select_db, 2)
        db_layout.addWidget(self.btn_new_db, 2)
        db_layout.addWidget(self.btn_backup_db, 2)
        db_layout.addWidget(self.btn_delete_db, 2)
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)


        # 控制按钮区
        ctrl_layout = QHBoxLayout()
        self.btn_merge_dft = QPushButton("Merge-DFT Files")
        self.btn_load_folder = QPushButton("Load File Folder")
        self.btn_load_files = QPushButton("Load Files")


        self.btn_dft_analysis = QPushButton("DFT Analysis")
        self.btn_save_db = QPushButton("Save DB")
        ctrl_layout.addWidget(self.btn_merge_dft)
        ctrl_layout.addWidget(self.btn_load_folder)
        ctrl_layout.addWidget(self.btn_load_files)
        ctrl_layout.addWidget(self.btn_dft_analysis)
        ctrl_layout.addWidget(self.btn_save_db)
        layout.addLayout(ctrl_layout)
        
        
        # 信号连接
      
        # 样品数据表（Table）
        self.sample_table = QTableWidget(0, 14)
        self.sample_table.setHorizontalHeaderLabels([
            "File Name", "Sample Name", "Probe Molecule", "BET Surface", "Volume",
            "Pore 0-0.5 nm", "Pore 0.5-0.7 nm", "Pore 0.7-1 nm",
            "Pore 1-2 nm", "Pore 2-5 nm", "Pore 5-10 nm", "Pore 10-Inf nm",
            "Analysis Date", "Date Logged"
        ])
        self.sample_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sample_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sample_table.setSortingEnabled(True)
        self.sample_table.sortItems(14, Qt.AscendingOrder)  # 按第1列升序排序
        self.sample_table.setContextMenuPolicy(Qt.CustomContextMenu)
        layout.addWidget(self.sample_table, 10)

        # 操作区
        crud_layout = QHBoxLayout()
        self.btn_edit = QPushButton("Edit")
        self.btn_delete = QPushButton("Delete")
        self.btn_find_duplicates = QPushButton("Find Duplicates")
        self.btn_export = QPushButton("Export")
        self.btn_compare_sets = QPushButton("Compare Sets")
        self.btn_trace_samples = QPushButton("Trace Samples")
        crud_layout.addWidget(self.btn_edit)
        crud_layout.addWidget(self.btn_delete)
        crud_layout.addWidget(self.btn_find_duplicates)
        crud_layout.addWidget(self.btn_export)
        crud_layout.addWidget(self.btn_compare_sets)
        crud_layout.addWidget(self.btn_trace_samples)
        layout.addLayout(crud_layout)

        # 样品数状态
        self.count_label = QLabel("Samples: 0")
        layout.addWidget(self.count_label)

        # 状态栏
        self.status_label = QLabel("Ready")
        self.status_label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        layout.addWidget(self.status_label)

        # 右键菜单（后续可绑定到sample_table）
        self.sample_menu = QMenu(self)
        self.sample_menu.addAction("Copy")
        self.sample_menu.addAction("Paste")
        self.sample_menu.addAction("Plot")
        self.sample_menu.addAction("Make a Set")
        self.sample_menu.addAction("Statistics")
        self.sample_menu.addAction("Play")

        self.setLayout(layout)
        self.connect_signals()

    def connect_signals(self):
        # controller赋值后，单独调用此函数进行信号绑定
        # self.db_combo.currentIndexChanged.connect(self.on_db_combo_changed)
        print("Connecting signals!")
        self.btn_select_db.clicked.connect(self.on_select_db_clicked)
        self.btn_new_db.clicked.connect(self._on_new_db_clicked)
        self.btn_backup_db.clicked.connect(self._on_backup_db_clicked)
        self.btn_delete_db.clicked.connect(self._on_delete_db_clicked)
        self.sample_table.itemSelectionChanged.connect(self._on_sample_selected)

        # Sample Edit Delete Find Duplicate
        self.btn_edit.clicked.connect(self._on_edit_clicked)
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        self.btn_find_duplicates.clicked.connect(self._on_find_duplicates_clicked)
        self.sample_table.customContextMenuRequested.connect(self.show_context_menu)

        #Load files
        self.btn_load_files.clicked.connect(self.on_load_files_btn_clicked)

    def bind_controller(self, controller, last_db=None):
        self.controller = controller
        if last_db:
            print(f"Auto-select last_db: {last_db}")
            self.controller.select_database(last_db)

    def update_db_combo(self, full_path):
        """在 combo 中显示文件名，但存储全路径"""
        filename = os.path.basename(full_path)
        # 检查是否已存在（避免重复）
        filename = os.path.basename(full_path)
        self.db_combo.clear()
        self.db_combo.addItem(filename, userData=full_path)
        self.db_combo.setCurrentIndex(0)
    
   

    def clear_db_combo(self):
        self.db_combo.clear()

    def set_status(self, msg):
        self.status_label.setText(msg)

    def on_select_db_clicked(self):
            print("Select DB Clicked")
            print("self =", self)
            print("self.controller =", getattr(self, "controller", None))
            if self.controller: 
                print("controller is", self.controller)
                self.controller.select_database()

    def _on_new_db_clicked(self):
        print("New DB Clicked")
        if self.controller: self.controller.create_database()

    def _on_backup_db_clicked(self):
        print("Backup DB Clicked")
        if self.controller: self.controller.backup_database()

    def _on_delete_db_clicked(self):
        print("Delete DB Clicked")
        if self.controller: self.controller.delete_database()

    def on_load_files_btn_clicked(self):
        print("Load Files Clicked")
        if self.controller:
            print("controller is", self.controller)
            self.controller.load_files()
    
    def set_status(self, msg):
        print("[STATUS]", msg)
    
    #Refresh Sample tables
    def refresh_sample_table(self):
        """
        清空并重新填充样品数据表。
        """
        # 1. 清空表
        self.sample_table.setRowCount(0)

        # 2. 获取所有样品数据（建议调用 model.get_sample_overview()）
        if not self.controller:
            return
        try:
            sample_list = self.controller.model.get_sample_overview()
        except Exception as e:
            self.set_status(f"载入样品列表失败: {e}")
            return

        # 3. 填充表格
        for row_idx, row_data in enumerate(sample_list):
            self.sample_table.insertRow(row_idx)
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value) if value is not None else "")
                self.sample_table.setItem(row_idx, col_idx, item)
        self.count_label.setText(f"Samples: {len(sample_list)}")
    
    def _on_sample_selected(self):
        items = self.sample_table.selectedItems()
        if not items:
            return
        # 第一列通常为 sample_name
        row = items[0].row()
        sample_name = self.sample_table.item(row, 0).text()  # 假设第一列为样品名
        print(f"Left panel sample_name {sample_name}")
        if self.controller:
            self.controller.on_sample_selected(sample_name)

    def on_sample_selection_changed(self, sample_name, deselected):
        indexes = self.sample_table.selectedIndexes()
        if not indexes:
            return
        row = indexes[0].row()
        sample_name = self.sample_table.item(row, 1).text()
        if self.controller:
            self.controller.on_sample_selected(sample_name)
    
    def _on_edit_clicked(self):
        items = self.sample_table.selectedItems()
        if not items:
            return
        # 第一列通常为 sample_name
        row = items[0].row()
        sample_name = self.sample_table.item(row, 0).text()  # 假设第一列为样品名
        print(f"Left panel sample_name {sample_name}")
        if self.controller:
            self.controller.edit_sample_info(sample_name)

    def refresh_table(self):
        """
        刷新左侧样品数据表，从数据库拉取最新数据并填充表格。
        """
        print("[DEBUG] 正在刷新样品数据表 ...")
        # 1. 清空所有数据行
        self.sample_table.setRowCount(0)
        if not self.controller:
            return
        # 2. 获取数据库最新样品数据
        if not self.controller:
            print("[ERROR] Controller 未初始化，无法刷新表格！")
            return
        try:
            sample_list = self.controller.model.get_sample_overview()  # [(col1, col2, ...), ...]
        except Exception as e:
            self.set_status(f"载入样品列表失败: {e}")
            print("[ERROR] 载入样品失败:", e)
            return

        # 3. 填充表格
        for row_idx, row_data in enumerate(sample_list):
            self.sample_table.insertRow(row_idx)
            for col_idx, value in enumerate(row_data):
                # 支持 None/空值
                item = QTableWidgetItem(str(value) if value is not None else "")
                self.sample_table.setItem(row_idx, col_idx, item)

        # 4. 更新底部样品数显示
        self.count_label.setText(f"Samples: {len(sample_list)}")

        # 5. 可选：自适应列宽
        self.sample_table.resizeColumnsToContents()
        print("[DEBUG] 样品表刷新完成。")
    

    # Delete Sample

    def _on_delete_clicked(self):
        items = self.sample_table.selectedItems()
        if not items:
            print("没有选中样品，无法删除")
            return

        # 第一列通常为 sample_name
        rows = set()
        for item in items:
            rows.add(item.row())

        sample_names = []
        for row in rows:
        # 第一列为样品名（文件名）
            name = self.sample_table.item(row, 0).text()
            sample_names.append(name)

        print("准备删除样品（文件名）：", sample_names)
        for name in sample_names:
            self.controller.delete_sample_info(name)
    
        self.refresh_sample_table()

    # Find duplicate and delete
    def _on_find_duplicates_clicked(self):
        print("[View] Find Duplicates 按钮被点击，转给 Controller")
        self.controller.find_duplicates()
    
    # Right click of context menu
    def show_context_menu(self, pos):
        indexes = self.sample_table.selectionModel().selectedRows()
        if not indexes:
            return  # no selection, do not show menu

        menu = QMenu(self.sample_table)

        copy_action = menu.addAction("Copy")
        cut_action = menu.addAction("Cut")
        paste_action = menu.addAction("Paste")
        menu.addSeparator()
        plot_action = menu.addAction("Plot")

        action = menu.exec(self.sample_table.viewport().mapToGlobal(pos))
        if action == copy_action:
            self.controller.copy_samples()
        elif action == cut_action:
            self.controller.cut_samples()
        elif action == paste_action:
            self.controller.paste_samples()
        elif action == plot_action:
            self.controller.plot_samples()
    
    def get_selected_sample_names(self) -> list[str]:
        selected_rows = self.sample_table.selectionModel().selectedRows()
        names = []
        for idx in selected_rows:
            item = self.sample_table.item(idx.row(), 1)
            if item:
                names.append(item.text())
        return names

    def set_status(self, message: str):
        if hasattr(self, "statusBar"):
            self.statusBar().showMessage(message, 5000)
        elif hasattr(self, "status_label"):
            self.status_label.setText(message)
    # Load files
    def on_load_files_btn_clicked(self):
        if self.controller:
            self.controller.start_import_files()

    def show_error(self):
        print("Show error in View")