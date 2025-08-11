from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QListWidgetItem,
    QDialogButtonBox, QLabel
)
import os

class FolderFilterDialog(QDialog):
    def __init__(self, parent, root_dir):
        super().__init__(parent)
        self.setWindowTitle("排除子文件夹")
        self.setMinimumWidth(400)

        self.layout = QVBoxLayout(self)

        self.layout.addWidget(QLabel(f"根目录: {root_dir}"))
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)

        # 添加子文件夹
        for name in os.listdir(root_dir):
            full_path = os.path.join(root_dir, name)
            if os.path.isdir(full_path):
                item = QListWidgetItem(name)
                item.setSelected(False)
                self.list_widget.addItem(item)

        self.layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

    def get_excluded_folders(self):
        return [item.text() for item in self.list_widget.selectedItems()]
