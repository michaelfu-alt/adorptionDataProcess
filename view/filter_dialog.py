# filter_dialog.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QScrollArea, QWidget, QDialogButtonBox, QCheckBox, QMessageBox
)

@dataclass
class FilterRule:
    field: str
    op: str               # >, >=, <, <=, ==, !=, contains, startswith, endswith, between
    v1: str
    v2: str = ""          # only used for 'between'

class FilterDialog(QDialog):
    def __init__(self, fields: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Filter")
        self.resize(720, 480)
        self._all_fields = list(fields)  # as-is (already merged in your TraceModel)

        main = QVBoxLayout(self)

        # Top: logic & options
        top = QHBoxLayout()
        top.addWidget(QLabel("Combine with:"))
        self.logic_combo = QComboBox()
        self.logic_combo.addItems(["AND", "OR"])
        top.addWidget(self.logic_combo)

        self.case_chk = QCheckBox("Case sensitive (string ops)")
        self.case_chk.setChecked(False)
        top.addWidget(self.case_chk)
        top.addStretch(1)
        main.addLayout(top)

        # Scrollable conditions area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.host = QWidget()
        self.grid = QGridLayout(self.host)
        self.grid.setContentsMargins(8, 8, 8, 8)
        self.grid.setHorizontalSpacing(8)
        self.scroll.setWidget(self.host)
        main.addWidget(self.scroll, 1)

        # Header row
        self.grid.addWidget(QLabel("Field"),   0, 0)
        self.grid.addWidget(QLabel("Operator"),0, 1)
        self.grid.addWidget(QLabel("Value"),   0, 2)
        self.grid.addWidget(QLabel("Value 2"), 0, 3)
        self.grid.addWidget(QLabel(""),        0, 4)

        self._rows: List[Dict[str, Any]] = []  # each row: dict of widgets

        # Buttons row
        row_btns = QHBoxLayout()
        self.add_btn = QPushButton("Add Condition")
        self.clear_btn = QPushButton("Clear All")
        row_btns.addWidget(self.add_btn)
        row_btns.addWidget(self.clear_btn)
        row_btns.addStretch(1)
        main.addLayout(row_btns)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        main.addWidget(buttons)

        # Signals
        self.add_btn.clicked.connect(self.add_condition_row)
        self.clear_btn.clicked.connect(self.clear_all_rows)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        # Start with one row
        self.add_condition_row()

    def add_condition_row(self, preset: FilterRule | None = None):
        r = len(self._rows) + 1  # grid row index (1-based, 0 is header)
        field_cb = QComboBox(); field_cb.addItems(self._all_fields)
        op_cb = QComboBox()
        op_cb.addItems([">", ">=", "<", "<=", "==", "!=", "contains", "startswith", "endswith", "between"])
        v1 = QLineEdit(); v1.setPlaceholderText("Value or min")
        v2 = QLineEdit(); v2.setPlaceholderText("max (for between)")
        v2.setEnabled(False); v2.setVisible(False)
        rm = QPushButton("✕")

        def on_op_change():
            is_between = (op_cb.currentText() == "between")
            v2.setEnabled(is_between)
            v2.setVisible(is_between)

        op_cb.currentIndexChanged.connect(on_op_change)
        rm.clicked.connect(lambda: self._remove_row_widgets(r))

        self.grid.addWidget(field_cb, r, 0)
        self.grid.addWidget(op_cb,    r, 1)
        self.grid.addWidget(v1,       r, 2)
        self.grid.addWidget(v2,       r, 3)
        self.grid.addWidget(rm,       r, 4)

        row = {"row": r, "field": field_cb, "op": op_cb, "v1": v1, "v2": v2, "rm": rm}
        self._rows.append(row)

        # apply preset if provided
        if preset:
            field_cb.setCurrentText(preset.field)
            op_cb.setCurrentText(preset.op)
            v1.setText(preset.v1 or "")
            if preset.op == "between":
                v2.setEnabled(True); v2.setVisible(True); v2.setText(preset.v2 or "")

    def _remove_row_widgets(self, row_idx: int):
        # find row dict
        to_remove = None
        for d in self._rows:
            if d["row"] == row_idx:
                to_remove = d
                break
        if not to_remove:
            return
        for key in ("field", "op", "v1", "v2", "rm"):
            w = to_remove[key]
            w.setParent(None)
            w.deleteLater()
        self._rows.remove(to_remove)

    def clear_all_rows(self):
        for d in list(self._rows):
            self._remove_row_widgets(d["row"])
        # leave one blank row
        self.add_condition_row()

    def _collect_rules(self) -> List[FilterRule]:
        rules: List[FilterRule] = []
        for d in self._rows:
            field = d["field"].currentText().strip()
            op    = d["op"].currentText().strip()
            v1    = d["v1"].text().strip()
            v2    = d["v2"].text().strip() if op == "between" else ""
            if not field or not op:
                continue
            if op != "between" and v1 == "":
                continue
            if op == "between" and (v1 == "" or v2 == ""):
                continue
            rules.append(FilterRule(field, op, v1, v2))
        return rules

    def _on_accept(self):
        rules = self._collect_rules()
        if not rules:
            QMessageBox.information(self, "Filter", "请至少添加一个有效条件")
            return
        self._rules = rules
        self._logic = self.logic_combo.currentText()
        self._case  = bool(self.case_chk.isChecked())
        self.accept()

    def result(self) -> Dict[str, Any]:
        """Call after exec() returns Accepted."""
        return {"rules": getattr(self, "_rules", []),
                "logic": getattr(self, "_logic", "AND"),
                "case":  getattr(self, "_case", False)}
