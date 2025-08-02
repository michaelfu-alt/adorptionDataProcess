from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QCheckBox, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal


class DuplicateFieldDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Fields for Duplicate Detection")
        layout = QVBoxLayout(self)

        self.check_sample_name = QCheckBox("Sample Name")
        self.check_sample_name.setChecked(True)
        self.check_analysis_date = QCheckBox("Analysis Date")
        self.check_analysis_date.setChecked(True)

        layout.addWidget(self.check_sample_name)
        layout.addWidget(self.check_analysis_date)

        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)

    def get_selected_fields(self):
        fields = []
        if self.check_sample_name.isChecked():
            fields.append("Sample Name")
        if self.check_analysis_date.isChecked():
            fields.append("Analysis Date")
        return fields


class DuplicateDeleteDialog(QDialog):
    deleteConfirmed = Signal(list)  # Emits list of internal_names to delete

    def __init__(self, dup_map, preselect=None, parent=None):
        """
        dup_map: dict, keys either str label or tuple (file_name, sample_name),
                 values: list of internal_name strings
        preselect: list or set of internal_name strings to be pre-selected
        """
        super().__init__(parent)
        self.setWindowTitle("Delete Duplicate Samples")
        self.resize(500, 400)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Select samples to delete:"))
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.list_widget)

        self.preselect = set(preselect or [])

        for label, internal_names in dup_map.items():
            # 支持传入 label 为 str 或 tuple
            if isinstance(label, tuple):
                display_label = " // ".join(label)
            else:
                display_label = label

            header_item = QListWidgetItem(display_label)
            header_item.setFlags(Qt.NoItemFlags)
            header_item.setBackground(Qt.lightGray)
            self.list_widget.addItem(header_item)

            for internal_name in internal_names:
                item = QListWidgetItem("    " + internal_name)
                item.setData(Qt.UserRole, internal_name)
                self.list_widget.addItem(item)
                if internal_name in self.preselect:
                    item.setSelected(True)

        btn_delete = QPushButton("Delete Selected")
        btn_delete.clicked.connect(self.on_delete_clicked)
        layout.addWidget(btn_delete)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)

    def on_delete_clicked(self):
        selected_items = self.list_widget.selectedItems()
        to_delete = []
        for item in selected_items:
            internal_name = item.data(Qt.UserRole)
            if internal_name:
                to_delete.append(internal_name)

        if not to_delete:
            QMessageBox.warning(self, "No selection", "Please select samples to delete.")
            return

        self.deleteConfirmed.emit(to_delete)
        self.accept()