from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QLabel
from PySide6.QtCore import Signal

class DuplicateDeleteDialog(QDialog):
    deleteConfirmed = Signal(list)

    def __init__(self, dup_map: dict, preselect: list = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Duplicate Samples Found")

        self.dup_map = dup_map
        self.preselect = set(preselect or [])

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select samples to delete:"))

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.list_widget)

        # 展开显示样品
        for (file_name, sample_name), internal_names in dup_map.items():
            label = file_name  # 显示文件名即可
            for internal_name in internal_names:
                item = QListWidgetItem(f"{label} // {internal_name}")
                item.setData(256, internal_name)
                self.list_widget.addItem(item)
                if internal_name in self.preselect:
                    item.setSelected(True)

        btn_delete = QPushButton("Delete Selected")
        btn_cancel = QPushButton("Cancel")
        layout.addWidget(btn_delete)
        layout.addWidget(btn_cancel)

        btn_delete.clicked.connect(self._on_delete_clicked)
        btn_cancel.clicked.connect(self.reject)

    def _on_delete_clicked(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
        to_delete = [item.data(256) for item in selected_items]
        self.deleteConfirmed.emit(to_delete)
        self.accept()