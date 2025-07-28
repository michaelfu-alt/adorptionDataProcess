# view/left_panel.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel, QGroupBox,
    QTableWidget, QTableWidgetItem, QMenu, QAbstractItemView, QFrame
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

        self.db_combo = QComboBox()
        self.db_combo.setEditable(True)

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

        # 信号连接
       
        # self.db_combo.currentIndexChanged.connect(self.on_db_combo_changed)
        # self.btn_select_db.clicked.connect(self._on_select_db_clicked)
        # self.btn_new_db.clicked.connect(self._on_new_db_clicked)
        # self.btn_backup_db.clicked.connect(self._on_backup_db_clicked)
        # self.btn_delete_db.clicked.connect(self._on_delete_db_clicked)

        # 控制按钮区
        ctrl_layout = QHBoxLayout()
        self.btn_merge_dft = QPushButton("Merge-DFT Files")
        self.btn_load_folder = QPushButton("Load File Folder")
        self.btn_load_files = QPushButton("Load Files")
        self.btn_load_files.clicked.connect(self.on_load_files_btn_clicked)


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

    def connect_signals(self):
        # controller赋值后，单独调用此函数进行信号绑定
        # self.db_combo.currentIndexChanged.connect(self.on_db_combo_changed)
        self.btn_select_db.clicked.connect(self.on_select_db_clicked)
        self.btn_new_db.clicked.connect(self.controller.create_database)
        self.btn_backup_db.clicked.connect(self.controller.backup_database)
        self.btn_delete_db.clicked.connect(self.controller.delete_database)


    def bind_controller(self, controller, last_db=None):
        self.controller = controller
        self.connect_signals()   # 一起做信号绑定
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
    
    def on_db_combo_changed(self, index):
        if index < 0:
            return

        db_path = self.db_combo.itemData(index)
        if not db_path or not os.path.exists(db_path):
            print("[WARN] Invalid DB path selected:", db_path)
            return  # 不调用 controller
        print(f"[INFO] ComboBox changed to: {db_path}")
        if self.controller:
            self.controller.select_database(db_path)
            self.set_status(f"Database loaded: {os.path.basename(db_path)}")

    def clear_db_combo(self):
        self.db_combo.clear()

    def set_status(self, msg):
        self.status_label.setText(msg)

    def on_db_combo_changed(self, index):
        db_path = self.db_combo.currentText()
        if self.controller:
            # 这里做防御式处理，保证 "" 不传下去
            self.controller.select_database(index or None)
            self.set_status(f"Database loaded: {db_path}")
    

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

    # Select Database
    
    
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
