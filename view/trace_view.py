import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QListWidget, QCheckBox, QScrollArea, QGridLayout
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.font_manager import FontProperties

class TraceView(QWidget):
    def __init__(self, controller, model):
        super().__init__()
        self.controller = controller
        self.model = model
        self.setWindowTitle("Trace Samples")
        self.resize(1000, 700)

        # 中文字体
        ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        font_path = os.path.join(ROOT_DIR, "asset", "fonts", "NotoSansSC-Regular.ttf")
        if os.path.exists(font_path):
            self.chinese_font = FontProperties(fname=font_path)
        else:
            self.chinese_font = FontProperties()

        layout = QVBoxLayout(self)

        # ===== Filter area =====
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter Field:"))
        self.field_cb = QComboBox()
        self.field_cb.addItems(self.model.get_fields())
        filter_layout.addWidget(self.field_cb)

        self.op_cb = QComboBox()
        self.op_cb.addItems([">", ">=", "<", "<=", "==", "!="])
        filter_layout.addWidget(self.op_cb)

        self.val_edit = QLineEdit()
        filter_layout.addWidget(self.val_edit)

        self.filter_btn = QPushButton("Filter")
        filter_layout.addWidget(self.filter_btn)

        self.reset_btn = QPushButton("Reset Filter")
        filter_layout.addWidget(self.reset_btn)

        layout.addLayout(filter_layout)

        # ===== Sample list =====
        self.sample_list = QListWidget()
        self.sample_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.sample_list)

        # ===== Field selection (scrollable, grid) =====
        layout.addWidget(QLabel("Select Fields to Plot/Export:"))
        self.field_scroll = QScrollArea()
        self.field_scroll.setWidgetResizable(True)
        self.field_scroll_content = QWidget()
        self.field_scroll.setWidget(self.field_scroll_content)

        self.field_scroll_layout = QGridLayout(self.field_scroll_content)
        self.field_checkboxes = []
        self._rebuild_field_checkboxes(self.model.get_fields())
        layout.addWidget(self.field_scroll)

        # ===== Matplotlib plot =====
        self.fig = Figure(figsize=(8, 5))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
        self.ax = self.fig.add_subplot(111)

        self.ax.set_title("样品追踪", fontproperties=self.chinese_font)
        self.ax.set_xlabel("字段", fontproperties=self.chinese_font)
        labels = self.get_selected_fields()
        self.ax.set_xticks(range(len(labels)))
        self.ax.set_xticklabels(labels, fontproperties=self.chinese_font, rotation=45, ha='right')
        self.ax.set_ylabel("数值 / 分类", fontproperties=self.chinese_font)

        # ===== Buttons =====
        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.clear_btn = QPushButton("Clear Selection")
        self.plot_btn = QPushButton("Plot")
        self.save_btn = QPushButton("Save Graph")
        self.export_btn = QPushButton("Export Excel")
        for btn in (self.select_all_btn, self.clear_btn, self.plot_btn, self.save_btn, self.export_btn):
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

        # ===== Signals =====
        self.filter_btn.clicked.connect(self.on_filter_clicked)
        self.reset_btn.clicked.connect(self.on_reset_clicked)
        self.select_all_btn.clicked.connect(self.select_all_samples)
        self.clear_btn.clicked.connect(self.clear_selection)
        self.plot_btn.clicked.connect(self.controller.on_plot)
        self.save_btn.clicked.connect(self.controller.on_save_graph)
        self.export_btn.clicked.connect(self.controller.on_export)

    # ---------- UI rebuild helpers ----------
    def _rebuild_field_checkboxes(self, fields: list[str], columns: int = 3):
        """(Re)create the field checkbox grid, skipping 'Sample Name'."""
        # Clear old widgets from layout
        while self.field_scroll_layout.count():
            item = self.field_scroll_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self.field_checkboxes = []

        # Create new checkboxes
        filtered_fields = [f for f in fields if f != "Sample Name"]
        for idx, f in enumerate(filtered_fields):
            cb = QCheckBox(f)
            cb.setChecked(True)
            row = idx // columns
            col = idx % columns
            self.field_scroll_layout.addWidget(cb, row, col)
            self.field_checkboxes.append(cb)

        # Also refresh the filter combobox to match current fields
        self._rebuild_filter_fields(fields)

    def _rebuild_filter_fields(self, fields: list[str]):
        """Repopulate the filter field combobox."""
        current = self.field_cb.currentText()
        self.field_cb.blockSignals(True)
        self.field_cb.clear()
        self.field_cb.addItems(fields)
        # try to preserve previous selection if still present
        idx = self.field_cb.findText(current)
        if idx >= 0:
            self.field_cb.setCurrentIndex(idx)
        self.field_cb.blockSignals(False)

    # Exposed for controller
    def update_field_list(self, fields: list[str]):
        self._rebuild_field_checkboxes(fields)

    # alias if controller uses set_fields
    def set_fields(self, fields: list[str]):
        self.update_field_list(fields)

    # ---------- Events to controller ----------
    def on_filter_clicked(self):
        self.controller.on_filter(self.field_cb.currentText(), self.op_cb.currentText(), self.val_edit.text())

    def on_reset_clicked(self):
        self.controller.on_reset_filter()

    # ---------- Sample list ops ----------
    def update_sample_list(self, sample_names: list[str]):
        self.sample_list.clear()
        self.sample_list.addItems(sample_names)

    def get_selected_samples(self) -> list[str]:
        return [item.text() for item in self.sample_list.selectedItems()]

    def get_selected_fields(self) -> list[str]:
        return [cb.text() for cb in self.field_checkboxes if cb.isChecked()]

    def select_all_samples(self):
        self.sample_list.selectAll()

    def clear_selection(self):
        self.sample_list.clearSelection()






# import os
# from PySide6.QtWidgets import (
#     QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
#     QPushButton, QListWidget, QCheckBox, QScrollArea, QWidget, QGridLayout
# )
# from matplotlib.figure import Figure
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.font_manager import FontProperties

# class TraceView(QWidget):
#     def __init__(self, controller, model):
#         super().__init__()
#         self.controller = controller
#         self.model = model
#         self.setWindowTitle("Trace Samples")
#         self.resize(1000, 700)

#         # 加载中文字体，只尝试一次
#         ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
#         font_path = os.path.join(ROOT_DIR, "asset", "fonts", "NotoSansSC-Regular.ttf")
#         print(font_path)
#         if os.path.exists(font_path):
#             print(font_path)
#             self.chinese_font = FontProperties(fname=font_path)
#         else:
#             self.chinese_font = FontProperties()  # 默认字体

#         layout = QVBoxLayout(self)

#         # Filter area
#         filter_layout = QHBoxLayout()
#         filter_layout.addWidget(QLabel("Filter Field:"))
#         self.field_cb = QComboBox()
#         self.field_cb.addItems(self.model.get_fields())
#         filter_layout.addWidget(self.field_cb)

#         self.op_cb = QComboBox()
#         self.op_cb.addItems([">", ">=", "<", "<=", "==", "!="])
#         filter_layout.addWidget(self.op_cb)

#         self.val_edit = QLineEdit()
#         filter_layout.addWidget(self.val_edit)

#         self.filter_btn = QPushButton("Filter")
#         filter_layout.addWidget(self.filter_btn)

#         self.reset_btn = QPushButton("Reset Filter")
#         filter_layout.addWidget(self.reset_btn)

#         layout.addLayout(filter_layout)

#         # Sample list
#         self.sample_list = QListWidget()
#         self.sample_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
#         layout.addWidget(self.sample_list)

#         # Field selection area (改为多列布局)
#         layout.addWidget(QLabel("Select Fields to Plot/Export:"))
#         self.field_scroll = QScrollArea()
#         self.field_scroll.setWidgetResizable(True)
#         self.field_scroll_content = QWidget()
#         self.field_scroll.setWidget(self.field_scroll_content)

#         self.field_scroll_layout = QGridLayout(self.field_scroll_content)
#         self.field_checkboxes = []
#         columns = 3
#         fields = [f for f in self.model.get_fields() if f != "Sample Name"]
#         for idx, f in enumerate(fields):
#             cb = QCheckBox(f)
#             cb.setChecked(True)
#             row = idx // columns
#             col = idx % columns
#             self.field_scroll_layout.addWidget(cb, row, col)
#             self.field_checkboxes.append(cb)
#         layout.addWidget(self.field_scroll)

#         # Matplotlib plot
#         self.fig = Figure(figsize=(8, 5))
#         self.canvas = FigureCanvas(self.fig)
#         layout.addWidget(self.canvas)
#         self.ax = self.fig.add_subplot(111)

#         self.ax.set_title("样品追踪", fontproperties=self.chinese_font)
#         self.ax.set_xlabel("字段", fontproperties=self.chinese_font)

#         labels = self.get_selected_fields()  # 你的选中字段列表
#         self.ax.set_xticks(range(len(labels)))  # 设置刻度位置
#         self.ax.set_xticklabels(labels, fontproperties=self.chinese_font, rotation=45, ha='right')
#         self.ax.set_ylabel("数值 / 分类", fontproperties=self.chinese_font)

#         # Buttons
#         btn_layout = QHBoxLayout()
#         self.select_all_btn = QPushButton("Select All")
#         self.clear_btn = QPushButton("Clear Selection")
#         self.plot_btn = QPushButton("Plot")
#         self.save_btn = QPushButton("Save Graph")
#         self.export_btn = QPushButton("Export Excel")

#         for btn in [self.select_all_btn, self.clear_btn, self.plot_btn, self.save_btn, self.export_btn]:
#             btn_layout.addWidget(btn)
#         layout.addLayout(btn_layout)

#         # Connect signals
#         self.filter_btn.clicked.connect(self.on_filter_clicked)
#         self.reset_btn.clicked.connect(self.on_reset_clicked)
#         self.select_all_btn.clicked.connect(self.select_all_samples)
#         self.clear_btn.clicked.connect(self.clear_selection)
#         self.plot_btn.clicked.connect(self.controller.on_plot)
#         self.save_btn.clicked.connect(self.controller.on_save_graph)
#         self.export_btn.clicked.connect(self.controller.on_export)

#     # 事件转发给 controller
#     def on_filter_clicked(self):
#         self.controller.on_filter(self.field_cb.currentText(), self.op_cb.currentText(), self.val_edit.text())

#     def on_reset_clicked(self):
#         self.controller.on_reset_filter()

#     # 更新样品列表（调用时传入字符串列表）
#     def update_sample_list(self, sample_names):
#         self.sample_list.clear()
#         self.sample_list.addItems(sample_names)

#     # 获取选中的样品名称列表
#     def get_selected_samples(self):
#         return [item.text() for item in self.sample_list.selectedItems()]

#     # 获取选中的字段列表
#     def get_selected_fields(self):
#         return [cb.text() for cb in self.field_checkboxes if cb.isChecked()]

#     def select_all_samples(self):
#         self.sample_list.selectAll()

#     def clear_selection(self):
#         self.sample_list.clearSelection()