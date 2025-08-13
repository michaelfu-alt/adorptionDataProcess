# filter_dialog.py

# filter_dialog.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QScrollArea, QWidget, QDialogButtonBox, QCheckBox, QMessageBox, QFrame, QSpacerItem, QSizePolicy
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
        self._all_fields = list(fields)

        main = QVBoxLayout(self)

        # ── Top: logic & options ────────────────────────────────────────────────
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

        # ── Scrollable conditions area (now aligned-to-top) ─────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.host = QWidget()
        self.grid = QGridLayout(self.host)
        self.grid.setContentsMargins(8, 8, 8, 8)
        self.grid.setHorizontalSpacing(8)

        # Header row
        hdr_font = self.font()
        hdr_font.setBold(True)
        def _hdr(label: str):
            w = QLabel(label)
            w.setFont(hdr_font)
            return w

        self.grid.addWidget(_hdr("Field"),   0, 0)
        self.grid.addWidget(_hdr("Operator"),0, 1)
        self.grid.addWidget(_hdr("Value"),   0, 2)
        self.grid.addWidget(_hdr("Value 2"), 0, 3)
        self.grid.addWidget(QLabel(""),      0, 4)

        # a stretch spacer at the BOTTOM keeps everything packed to the top
        # (so the first condition sits right under the header/Combine row)
        self._bottom_spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.grid.addItem(self._bottom_spacer, 1, 0, 1, 5)
        self._next_row = 1  # next grid row to place a condition (spacer will be moved down)

        self.scroll.setWidget(self.host)
        main.addWidget(self.scroll, 1)

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

        self._rows: List[Dict[str, Any]] = []  # logical rows we manage

        # Start with one row
        self.add_condition_row()

    # ────────────────────────────────────────────────────────────────────────────
    def _make_separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setObjectName("row-sep")
        return line

    def add_condition_row(self, preset: FilterRule | None = None):
        # move spacer down to make room
        self.grid.removeItem(self._bottom_spacer)

        r = self._next_row  # put widgets at this row; a separator will occupy r+1
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
        rm.clicked.connect(lambda: self._remove_row(field_cb))  # key by a widget ref

        # place widgets
        self.grid.addWidget(field_cb, r, 0)
        self.grid.addWidget(op_cb,    r, 1)
        self.grid.addWidget(v1,       r, 2)
        self.grid.addWidget(v2,       r, 3)
        self.grid.addWidget(rm,       r, 4)

        # add separator line under this row (visual divider)
        sep = self._make_separator()
        self.grid.addWidget(sep, r + 1, 0, 1, 5)

        row = {"field": field_cb, "op": op_cb, "v1": v1, "v2": v2, "rm": rm, "sep": sep}
        self._rows.append(row)

        # apply preset if provided
        if preset:
            field_cb.setCurrentText(preset.field)
            op_cb.setCurrentText(preset.op)
            v1.setText(preset.v1 or "")
            if preset.op == "between":
                v2.setEnabled(True); v2.setVisible(True); v2.setText(preset.v2 or "")

        # advance counter by 2 (widgets + separator)
        self._next_row += 2

        # put the spacer back at the very bottom so content stays top-aligned
        self.grid.addItem(self._bottom_spacer, self._next_row, 0, 1, 5)

    def _remove_row(self, key_widget):
        # find by one of the widgets we stored (field cb)
        for i, d in enumerate(self._rows):
            if d["field"] is key_widget:
                # delete widgets + separator
                for k in ("field", "op", "v1", "v2", "rm", "sep"):
                    w = d[k]
                    if isinstance(w, QFrame):
                        w.setParent(None); w.deleteLater()
                    else:
                        w.setParent(None); w.deleteLater()
                self._rows.pop(i)
                break
        # rebuild grid positions tightly packed (so there are no gaps)
        self._rebuild_rows()

    def _rebuild_rows(self):
        # remove everything except the header
        # (header is on row 0; we’ll clear rows >=1)
        # simplest: destroy the host layout and recreate it
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                if isinstance(w, QLabel) and w.text() in ("Field","Operator","Value","Value 2",""):
                    # keep header widgets by re-adding them later
                    w.setParent(None)
                else:
                    w.setParent(None)
        # rebuild header
        self.grid.addWidget(QLabel("Field"),   0, 0)
        self.grid.addWidget(QLabel("Operator"),0, 1)
        self.grid.addWidget(QLabel("Value"),   0, 2)
        self.grid.addWidget(QLabel("Value 2"), 0, 3)
        self.grid.addWidget(QLabel(""),        0, 4)

        # reset placing state
        self._next_row = 1
        # re-add all logical rows
        rows_copy = list(self._rows)
        self._rows.clear()
        for d in rows_copy:
            # we can reuse the widgets already created in d
            self.grid.addWidget(d["field"], self._next_row, 0)
            self.grid.addWidget(d["op"],    self._next_row, 1)
            self.grid.addWidget(d["v1"],    self._next_row, 2)
            self.grid.addWidget(d["v2"],    self._next_row, 3)
            self.grid.addWidget(d["rm"],    self._next_row, 4)
            sep = self._make_separator()
            self.grid.addWidget(sep, self._next_row + 1, 0, 1, 5)
            d["sep"] = sep
            self._rows.append(d)
            self._next_row += 2

        # bottom spacer back
        self.grid.addItem(self._bottom_spacer, self._next_row, 0, 1, 5)

    def clear_all_rows(self):
        for d in list(self._rows):
            for k in ("field","op","v1","v2","rm","sep"):
                d[k].setParent(None)
                d[k].deleteLater()
        self._rows.clear()
        self._rebuild_rows()
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
        return {"rules": getattr(self, "_rules", []),
                "logic": getattr(self, "_logic", "AND"),
                "case":  getattr(self, "_case", False)}


# from __future__ import annotations
# from dataclasses import dataclass
# from typing import List, Dict, Any
# from PySide6.QtCore import Qt
# from PySide6.QtWidgets import (
#     QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit,
#     QPushButton, QScrollArea, QWidget, QDialogButtonBox, QCheckBox, QMessageBox
# )

# @dataclass
# class FilterRule:
#     field: str
#     op: str               # >, >=, <, <=, ==, !=, contains, startswith, endswith, between
#     v1: str
#     v2: str = ""          # only used for 'between'

# class FilterDialog(QDialog):
#     def __init__(self, fields: List[str], parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Advanced Filter")
#         self.resize(720, 480)
#         self._all_fields = list(fields)  # as-is (already merged in your TraceModel)

#         main = QVBoxLayout(self)

#         # Top: logic & options
#         top = QHBoxLayout()
#         top.addWidget(QLabel("Combine with:"))
#         self.logic_combo = QComboBox()
#         self.logic_combo.addItems(["AND", "OR"])
#         top.addWidget(self.logic_combo)

#         self.case_chk = QCheckBox("Case sensitive (string ops)")
#         self.case_chk.setChecked(False)
#         top.addWidget(self.case_chk)
#         top.addStretch(1)
#         main.addLayout(top)

#         # Scrollable conditions area
#         self.scroll = QScrollArea()
#         self.scroll.setWidgetResizable(True)
#         self.host = QWidget()
#         self.grid = QGridLayout(self.host)
#         self.grid.setContentsMargins(8, 8, 8, 8)
#         self.grid.setHorizontalSpacing(8)
#         self.scroll.setWidget(self.host)
#         main.addWidget(self.scroll, 1)

#         # Header row
#         self.grid.addWidget(QLabel("Field"),   0, 0)
#         self.grid.addWidget(QLabel("Operator"),0, 1)
#         self.grid.addWidget(QLabel("Value"),   0, 2)
#         self.grid.addWidget(QLabel("Value 2"), 0, 3)
#         self.grid.addWidget(QLabel(""),        0, 4)

#         self._rows: List[Dict[str, Any]] = []  # each row: dict of widgets

#         # Buttons row
#         row_btns = QHBoxLayout()
#         self.add_btn = QPushButton("Add Condition")
#         self.clear_btn = QPushButton("Clear All")
#         row_btns.addWidget(self.add_btn)
#         row_btns.addWidget(self.clear_btn)
#         row_btns.addStretch(1)
#         main.addLayout(row_btns)

#         # Dialog buttons
#         buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
#         main.addWidget(buttons)

#         # Signals
#         self.add_btn.clicked.connect(self.add_condition_row)
#         self.clear_btn.clicked.connect(self.clear_all_rows)
#         buttons.accepted.connect(self._on_accept)
#         buttons.rejected.connect(self.reject)

#         # Start with one row
#         self.add_condition_row()

#     def add_condition_row(self, preset: FilterRule | None = None):
#         r = len(self._rows) + 1  # grid row index (1-based, 0 is header)
#         field_cb = QComboBox(); field_cb.addItems(self._all_fields)
#         op_cb = QComboBox()
#         op_cb.addItems([">", ">=", "<", "<=", "==", "!=", "contains", "startswith", "endswith", "between"])
#         v1 = QLineEdit(); v1.setPlaceholderText("Value or min")
#         v2 = QLineEdit(); v2.setPlaceholderText("max (for between)")
#         v2.setEnabled(False); v2.setVisible(False)
#         rm = QPushButton("✕")

#         def on_op_change():
#             is_between = (op_cb.currentText() == "between")
#             v2.setEnabled(is_between)
#             v2.setVisible(is_between)

#         op_cb.currentIndexChanged.connect(on_op_change)
#         rm.clicked.connect(lambda: self._remove_row_widgets(r))

#         self.grid.addWidget(field_cb, r, 0)
#         self.grid.addWidget(op_cb,    r, 1)
#         self.grid.addWidget(v1,       r, 2)
#         self.grid.addWidget(v2,       r, 3)
#         self.grid.addWidget(rm,       r, 4)

#         row = {"row": r, "field": field_cb, "op": op_cb, "v1": v1, "v2": v2, "rm": rm}
#         self._rows.append(row)

#         # apply preset if provided
#         if preset:
#             field_cb.setCurrentText(preset.field)
#             op_cb.setCurrentText(preset.op)
#             v1.setText(preset.v1 or "")
#             if preset.op == "between":
#                 v2.setEnabled(True); v2.setVisible(True); v2.setText(preset.v2 or "")

#     def _remove_row_widgets(self, row_idx: int):
#         # find row dict
#         to_remove = None
#         for d in self._rows:
#             if d["row"] == row_idx:
#                 to_remove = d
#                 break
#         if not to_remove:
#             return
#         for key in ("field", "op", "v1", "v2", "rm"):
#             w = to_remove[key]
#             w.setParent(None)
#             w.deleteLater()
#         self._rows.remove(to_remove)

#     def clear_all_rows(self):
#         for d in list(self._rows):
#             self._remove_row_widgets(d["row"])
#         # leave one blank row
#         self.add_condition_row()

#     def _collect_rules(self) -> List[FilterRule]:
#         rules: List[FilterRule] = []
#         for d in self._rows:
#             field = d["field"].currentText().strip()
#             op    = d["op"].currentText().strip()
#             v1    = d["v1"].text().strip()
#             v2    = d["v2"].text().strip() if op == "between" else ""
#             if not field or not op:
#                 continue
#             # allow empty v1 only for is-empty/!=? (not implemented here) — so require v1
#             if op != "between" and v1 == "":
#                 continue
#             if op == "between" and (v1 == "" or v2 == ""):
#                 continue
#             rules.append(FilterRule(field, op, v1, v2))
#         return rules

#     def _on_accept(self):
#         rules = self._collect_rules()
#         if not rules:
#             QMessageBox.information(self, "Filter", "请至少添加一个有效条件")
#             return
#         self._rules = rules
#         self._logic = self.logic_combo.currentText()
#         self._case  = bool(self.case_chk.isChecked())
#         self.accept()

#     def result(self) -> Dict[str, Any]:
#         """Call after exec() returns Accepted."""
#         return {"rules": getattr(self, "_rules", []),
#                 "logic": getattr(self, "_logic", "AND"),
#                 "case":  getattr(self, "_case", False)}
