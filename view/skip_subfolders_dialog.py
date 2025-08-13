# view/skip_subfolders_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QDialogButtonBox
)
from PySide6.QtCore import Qt

class SkipSubfoldersDialog(QDialog):
    def __init__(self, root_path: str, subfolders: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Skip Subfolders")
        self.resize(520, 420)

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(f"Root: {root_path}"))

        self.listw = QListWidget()
        self.listw.setSelectionMode(QListWidget.NoSelection)
        for name in subfolders:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)   # Unchecked = keep; Checked = skip
            self.listw.addItem(item)
        lay.addWidget(self.listw, 1)

        # quick helpers
        btns_row = QHBoxLayout()
        btn_all = QPushButton("Check All")
        btn_none = QPushButton("Uncheck All")
        btn_all.clicked.connect(lambda: self._check_all(Qt.Checked))
        btn_none.clicked.connect(lambda: self._check_all(Qt.Unchecked))
        btns_row.addWidget(btn_all)
        btns_row.addWidget(btn_none)
        btns_row.addStretch(1)
        lay.addLayout(btns_row)

        db = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        db.accepted.connect(self.accept)
        db.rejected.connect(self.reject)
        lay.addWidget(db)

    def _check_all(self, state: Qt.CheckState):
        for i in range(self.listw.count()):
            self.listw.item(i).setCheckState(state)

    def skipped(self) -> list[str]:
        out = []
        for i in range(self.listw.count()):
            it = self.listw.item(i)
            if it.checkState() == Qt.Checked:
                out.append(it.text())
        return out
