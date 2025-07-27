# view/left_panel.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel, QGroupBox,
    QTableWidget, QTableWidgetItem, QMenu, QAbstractItemView, QFrame
)
from PySide6.QtCore import Qt, Signal

class LeftPanel(QWidget):
    # 可定义自定义信号，例如
    # sampleSelected = Signal(str)

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6,6,6,6)
        layout.setSpacing(8)

        # Database 操作区
        db_group = QGroupBox("Database")
        db_layout = QHBoxLayout()
        self.db_combo = QComboBox()
        self.db_combo.setEditable(True)
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
        # self.btn_select_db.clicked.connect(self.controller.select_database)
        # self.btn_new_db.clicked.connect(self.controller.create_database)
        # self.btn_backup_db.clicked.connect(self.controller.backup_database)
        # self.btn_delete_db.clicked.connect(self.controller.delete_database)
        # self.db_combo.currentIndexChanged.connect(self.on_db_combo_changed)
        self.btn_select_db.clicked.connect(self._on_select_db_clicked)
        self.btn_new_db.clicked.connect(self._on_new_db_clicked)
        self.btn_backup_db.clicked.connect(self._on_backup_db_clicked)
        self.btn_delete_db.clicked.connect(self._on_delete_db_clicked)

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
        self.btn_load_files.clicked.connect(self.on_load_files_btn_clicked)
      
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


    def update_db_combo(self, new_path):
        exist = [self.db_combo.itemText(i) for i in range(self.db_combo.count())]
        if new_path not in exist:
            self.db_combo.addItem(new_path)
        self.db_combo.setCurrentText(new_path)

    def clear_db_combo(self):
        self.db_combo.clear()

    def set_status(self, msg):
        self.status_label.setText(msg)

    def on_db_combo_changed(self, index):
        path = self.db_combo.currentText()
        if path:
            self.controller.model.open_database(path)
            self.set_status(f"Database loaded: {path}")
    

    def _on_select_db_clicked(self):
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