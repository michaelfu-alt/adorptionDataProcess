# view/dialogs.py
import os, re
import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton, QScrollArea, QWidget, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt, QStandardPaths
from controller.import_export import SampleExporter
class FieldSelectDialog(QDialog):
    CONFIG_FILE = os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation), "field_select_config.json")

    def __init__(self, all_fields, default_fields=None, all_stats=None, default_stats=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Fields and Statistics")

        self.all_fields = all_fields
        self.default_fields = default_fields or []
        self.all_stats = all_stats or ["Mean", "Max", "Min", "StdDev"]
        self.default_stats = default_stats or ["Mean", "Max"]

        self.selected_fields = []
        self.selected_stats = []

        self._load_config()

        layout = QVBoxLayout(self)        
        layout.addWidget(QLabel("Select Fields:"))

        field_scroll = QScrollArea()
        field_widget = QWidget()
        field_layout = QVBoxLayout(field_widget)
        self.field_checkboxes = []
        for f in self.all_fields:
            cb = QCheckBox(f)
            cb.setChecked(f in self.selected_fields)
            field_layout.addWidget(cb)
            self.field_checkboxes.append(cb)
        field_scroll.setWidget(field_widget)
        field_scroll.setWidgetResizable(True)
        field_scroll.setFixedHeight(200)
        layout.addWidget(field_scroll)

        # 添加设置按钮
        self.settings_btn = QPushButton("字段单元格映射设置")
        layout.addWidget(self.settings_btn)
        self.settings_btn.clicked.connect(self.open_cell_mapping_dialog)

        # layout.addWidget(QLabel("Select Statistics:"))
        # stats_layout = QHBoxLayout()
        # self.stat_checkboxes = []
        # for s in self.all_stats:
        #     cb = QCheckBox(s)
        #     cb.setChecked(s in self.selected_stats)
        #     stats_layout.addWidget(cb)
        #     self.stat_checkboxes.append(cb)
        # layout.addLayout(stats_layout)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

         # 初始化单元格映射，默认用从配置文件或默认字段映射
        self.field_cell_map = self._load_field_cell_map()

    def accept(self):
        self.selected_fields = [cb.text() for cb in self.field_checkboxes if cb.isChecked()]
        # self.selected_stats = [cb.text() for cb in self.stat_checkboxes if cb.isChecked()]
        self._save_config()
        super().accept()

    def _load_config(self):
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.selected_fields = data.get("fields", self.default_fields)
                    self.selected_stats = data.get("stats", self.default_stats)
            else:
                self.selected_fields = self.default_fields
                self.selected_stats = self.default_stats
        except Exception:
            self.selected_fields = self.default_fields
            self.selected_stats = self.default_stats

    def _save_config(self):
        try:
            os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "fields": self.selected_fields,
                    "stats": self.selected_stats
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def _load_field_cell_map(self):
        config_path = os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation), "field_cell_map.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # 默认映射
        EXCEL_CELL_MAP = SampleExporter.EXCEL_CELL_MAP
        return {k: EXCEL_CELL_MAP.get(k, "") for k in self.all_fields}

    def _save_field_cell_map(self, mapping):
        config_path = os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation), "field_cell_map.json")
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存字段单元格映射失败: {e}")

    def open_cell_mapping_dialog(self):
        dlg = FieldCellMappingDialog(self.field_cell_map, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.field_cell_map = dlg.get_mapping()
            self._save_field_cell_map(self.field_cell_map)


class FieldCellMappingDialog(QDialog):
    CELL_PATTERN = re.compile(r"^[A-Z]{1,3}[1-9][0-9]{0,4}$")  # 简单单元格格式校验

    def __init__(self, field_cell_map, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置字段对应Excel单元格")
        self.resize(400, 500)
        self.field_cell_map = field_cell_map.copy()
        self.line_edits = {}

        main_layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        for field, cell in self.field_cell_map.items():
            row_layout = QHBoxLayout()
            label = QLabel(field)
            label.setFixedWidth(150)
            edit = QLineEdit(cell)
            edit.setPlaceholderText("单元格地址，如 B32")
            row_layout.addWidget(label)
            row_layout.addWidget(edit)
            scroll_layout.addLayout(row_layout)
            self.line_edits[field] = edit

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("确定")
        btn_cancel = QPushButton("取消")
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        main_layout.addLayout(btn_layout)

        btn_ok.clicked.connect(self.on_ok)
        btn_cancel.clicked.connect(self.reject)

    def on_ok(self):
        for field, edit in self.line_edits.items():
            text = edit.text().strip().upper()
            if not text:
                QMessageBox.warning(self, "输入错误", f"字段 '{field}' 的单元格地址不能为空")
                return
            if not self.CELL_PATTERN.match(text):
                QMessageBox.warning(self, "输入错误", f"字段 '{field}' 的单元格地址格式错误: {text}")
                return
        for field, edit in self.line_edits.items():
            self.field_cell_map[field] = edit.text().strip().upper()
        self.accept()

    def get_mapping(self):
        return self.field_cell_map