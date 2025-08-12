# settings_dialog.py
from __future__ import annotations

import json
import os
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

# ---- Master model list (fallback / default) ----
MODEL_OPTIONS: List[str] = [
    "Mixing Model ...",  # index 0 -> triggers mixing dialog
    "N2 in Carbon Slit pore at 77K",
    "N2 in Carbon Cylindrical pore at 77K",
    "N2 in Carbon Spherical pore at 77K",
    "Ar in Zeolite Slit pore at 87K",
    "Ar in Zeolite Cylindrical pore at 87K",
    "Ar in Zeolite Spherical pore at 87K",
    "CO2 in Carbon Slit pore at 273K",
    "CO2 in Carbon Cylindric pore at 273K",
    "CO2 in Carbon Spherical pore at 273K",
    "N2 in Zeolite Slit pore at 77K",
    "N2 in Zeolite Cylindrical pore at 77K",
    "N2 in Zeolite Spherical pore at 77K",
    "N2 in MOF (site Zn) at 77K",
    "N2 in MOF (linker C) at 77K",
    "N2 in MOF (site Al) at 77K",
    "N2 in MOF (linker N) at 77K",
    "N2 in Carbon Slit pore at 77K (2D-NLDFT)",
    "N2 in Carbon Cylindrical pore at 77K (2D-NLDFT)",
    "N2 in Carbon Spherical pore at 77K (2D-NLDFT)",
    "Ar in Carbon Slit pore at 87K (zeolite-like)",
    "Ar in Carbon Cylindrical pore at 87K (zeolite-like)",
    "Ar in Carbon Spherical pore at 87K (zeolite-like)",
    "N2 in Zeolite Slit pore at 77K (2D-NLDFT)",
    "N2 in Zeolite Cylindrical pore at 77K (2D-NLDFT)",
    "N2 in Zeolite Spherical pore at 77K (2D-NLDFT)",
    "O2 in Carbon Slit pore at 87K",
    "O2 in Carbon Cylindrical pore at 87K",
    "O2 in Carbon Spherical pore at 87K",
    "H2 in Carbon Slit pore at 77K",
    "H2 in Carbon Cylindrical pore at 77K",
    "H2 in Carbon Spherical pore at 77K",
    "N2 in Carbon Slit pore at 77K (HS-2D-NLDFT)",
    "N2 in Carbon Cylindrical pore at 77K (HS-2D-NLDFT)",
    "N2 in Carbon Spherical pore at 77K (HS-2D-NLDFT)",
    "N2 in Zeolite Slit pore at 77K (HS-2D-NLDFT)",
    "N2 in Zeolite Cylindrical pore at 77K (HS-2D-NLDFT)",
    "N2 in Zeolite Spherical pore at 77K (HS-2D-NLDFT)",
    "H2 in Zeolite Slit pore at 77K",
    "H2 in Zeolite Cylindrical pore at 77K",
    "H2 in Zeolite Spherical pore at 77K",
    "Ar in MFI Slit pore at 87K",
    "Ar in MFI Cylindrical pore at 87K",
    "Ar in MFI Spherical pore at 87K",
    "O2 in MFI Slit pore at 77K",
    "O2 in MFI Cylindrical pore at 77K",
    "O2 in MFI Spherical pore at 77K",
]

# ---- Defaults (overlayed on load) ----
DEFAULTS = {
    "stencil_exe": "",
    "soran_exe": "",
    "model": "N2 in Carbon Slit pore at 77K",
    "model_index": 0,                 # 0-based index
    "model_options": MODEL_OPTIONS,   # full list as default
    "desorption": False,
    "pp0": "p0",
    "unit": "cm3(STP)/g",
    "min_pressure": "0.05",
    "max_pressure": "0.95",
    "smooth_factor": "4",
    # New keys for Mixing Model
    "mixing_model_indices": [],       # indices into MODEL_OPTIONS (excluding index 0)
    "mixing_model_names": [],         # the saved names
}

# ---------- Mixing Model Dialog ----------
class MixingModelDialog(QDialog):
    """
    Lets the user select multiple base models to mix (checkbox list).
    We hide the first header option ('Mixing Model ...') and show the rest.
    """
    def __init__(self, parent: QWidget | None, all_models: List[str], prechecked_names: List[str] | None = None):
        super().__init__(parent)
        self.setWindowTitle("选择混合模型 (Mixed Model)")
        self.resize(540, 520)
        self._models = all_models[1:]  # skip header
        pre = set(prechecked_names or [])

        self.listw = QListWidget()
        self.listw.setSelectionMode(QListWidget.NoSelection)

        for name in self._models:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if name in pre else Qt.Unchecked)
            self.listw.addItem(item)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("勾选需要混合的模型："))
        lay.addWidget(self.listw, 1)
        lay.addWidget(btns)

    def selected_names(self) -> List[str]:
        names: List[str] = []
        for i in range(self.listw.count()):
            it = self.listw.item(i)
            if it.checkState() == Qt.Checked:
                names.append(it.text())
        return names


class SettingsDialog(QDialog):
    """
    Settings UI matching the JSON schema:
      stencil_exe, soran_exe,
      model, model_index (0-based), model_options (list of strings),
      desorption (bool), pp0, unit, min_pressure, max_pressure, smooth_factor,
      mixing_model_indices, mixing_model_names (for index 0)
    """

    def __init__(self, parent: QWidget | None = None, settings_path: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(860, 680)
        self.settings_path = os.path.abspath(settings_path or "settings.json")

        # Read (with defaults merged for UI)
        self.data = self._load_json(self.settings_path)
        # Original existing JSON (so we can merge on save without dropping keys)
        self._data = self._load_existing(self.settings_path)

        # ===== Top row: settings.json path =====
        top_row = QHBoxLayout()
        self.settings_file_edit = QLineEdit(self.settings_path)
        btn_browse_settings = QPushButton("保存为…")
        btn_browse_settings.clicked.connect(self._choose_settings_path)
        top_row.addWidget(QLabel("设置文件:"))
        top_row.addWidget(self.settings_file_edit, 1)
        top_row.addWidget(btn_browse_settings)

        # ===== Executables =====
        exe_group = QGroupBox("执行程序路径")
        exe_form = QFormLayout()

        self.stencil_exe_edit = QLineEdit(self.data.get("stencil_exe", ""))
        btn_browse_stencil = QPushButton("选择…")
        btn_browse_stencil.clicked.connect(self._choose_stencil_exe)
        r1 = QHBoxLayout()
        r1.addWidget(self.stencil_exe_edit, 1)
        r1.addWidget(btn_browse_stencil)
        exe_form.addRow(QLabel("StencilWizard:"), self._wrap(r1))

        self.soran_exe_edit = QLineEdit(self.data.get("soran_exe", ""))
        btn_browse_soran = QPushButton("选择…")
        btn_browse_soran.clicked.connect(self._choose_soran_exe)
        r2 = QHBoxLayout()
        r2.addWidget(self.soran_exe_edit, 1)
        r2.addWidget(btn_browse_soran)
        exe_form.addRow(QLabel("Soran:"), self._wrap(r2))

        exe_group.setLayout(exe_form)

        # ===== DFT params =====
        dft_group = QGroupBox("DFT 参数")
        dft_form = QFormLayout()

        # Model options editor (multiline) + refresh button
        self.model_options_edit = QPlainTextEdit()
        self.model_options_edit.setPlaceholderText("每行一个模型选项…")
        self.model_options_edit.setPlainText("\n".join(self.data.get("model_options", [])))

        # Row: model combo + refresh + configure mixing
        self.model_combo = QComboBox()
        self._reload_model_combo_from_text()  # pure UI rebuild, no data mutation

        # Restore selection from settings.json (block signals to avoid clobber)
        saved_idx = int(self.data.get("model_index", 0))
        saved_txt = self.data.get("model", "")

        self.model_combo.blockSignals(True)
        if 0 <= saved_idx < self.model_combo.count():
            self.model_combo.setCurrentIndex(saved_idx)
        elif saved_txt:
            i = self.model_combo.findText(saved_txt, Qt.MatchExactly)
            self.model_combo.setCurrentIndex(i if i >= 0 else 0)
        else:
            self.model_combo.setCurrentIndex(0)
        self.model_combo.blockSignals(False)

        self.model_combo.currentIndexChanged.connect(self._on_model_changed)

        btn_reload_model = QPushButton("从文本刷新选项")
        btn_reload_model.clicked.connect(self._on_reload_click)

        self.btn_config_mix = QPushButton("配置混合…")
        self.btn_config_mix.clicked.connect(self._open_mixing_dialog)
        self._update_mixing_button_state()

        row_model = QHBoxLayout()
        row_model.addWidget(self.model_combo, 1)
        row_model.addWidget(btn_reload_model)
        row_model.addWidget(self.btn_config_mix)

        # Other fields
        self.desorption_chk = QCheckBox("Desorption")
        self.desorption_chk.setChecked(bool(self.data.get("desorption", False)))

        self.pp0_edit = QLineEdit(self.data.get("pp0", "p0"))
        self.unit_edit = QLineEdit(self.data.get("unit", "cm3(STP)/g"))

        self.min_spin = QDoubleSpinBox()
        self.min_spin.setDecimals(4)
        self.min_spin.setRange(0.0, 1.0)
        self.min_spin.setSingleStep(0.01)
        self.min_spin.setValue(self._to_float(self.data.get("min_pressure", "0.05"), 0.05))

        self.max_spin = QDoubleSpinBox()
        self.max_spin.setDecimals(4)
        self.max_spin.setRange(0.0, 1.0)
        self.max_spin.setSingleStep(0.01)
        self.max_spin.setValue(self._to_float(self.data.get("max_pressure", "0.95"), 0.95))

        self.smooth_spin = QSpinBox()
        self.smooth_spin.setRange(0, 999)
        self.smooth_spin.setValue(self._to_int(self.data.get("smooth_factor", "4"), 4))

        # Layout rows
        dft_form.addRow(QLabel("模型选项(每行一个):"), self.model_options_edit)
        dft_form.addRow(QLabel("模型选择:"), self._wrap(row_model))
        dft_form.addRow(QLabel("p/p0:"), self.pp0_edit)
        dft_form.addRow(QLabel("单位:"), self.unit_edit)
        dft_form.addRow(QLabel("最小压力:"), self.min_spin)
        dft_form.addRow(QLabel("最大压力:"), self.max_spin)
        dft_form.addRow(QLabel("平滑因子:"), self.smooth_spin)
        dft_form.addRow(self.desorption_chk)
        dft_group.setLayout(dft_form)

        # ===== Buttons =====
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)

        # ===== Main layout =====
        main = QVBoxLayout(self)
        main.addLayout(top_row)
        main.addWidget(exe_group)
        main.addWidget(dft_group, 1)
        main.addWidget(buttons)

    # ---------- helpers ----------
    def _wrap(self, layout: QHBoxLayout) -> QWidget:
        w = QWidget()
        w.setLayout(layout)
        return w

    def _load_existing(self, path: str) -> dict:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _load_json(self, path: str) -> dict:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                merged = DEFAULTS | data
                # Ensure list types
                if not isinstance(merged.get("model_options"), list):
                    merged["model_options"] = list(DEFAULTS["model_options"])
                if not isinstance(merged.get("mixing_model_indices"), list):
                    merged["mixing_model_indices"] = []
                if not isinstance(merged.get("mixing_model_names"), list):
                    merged["mixing_model_names"] = []
                return merged
            except Exception as e:
                QMessageBox.warning(self, "设置", f"读取设置失败：\n{e}\n使用默认值。")
        return DEFAULTS.copy()

    def _choose_settings_path(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存设置为…", self.settings_path, "JSON Files (*.json);;All Files (*)"
        )
        if path:
            self.settings_path = path
            self.settings_file_edit.setText(path)

    def _choose_stencil_exe(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 StencilWizard 程序", "", "Executables (*.exe);;All Files (*)"
        )
        if path:
            self.stencil_exe_edit.setText(path)

    def _choose_soran_exe(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 Soran 程序", "", "Executables (*.exe);;All Files (*)"
        )
        if path:
            self.soran_exe_edit.setText(path)

    def _reload_model_combo_from_text(self):
        """Rebuild the combo from the multiline text, preserving selection if possible.
        Does NOT mutate self.data (pure UI op).
        """
        options = [ln.strip() for ln in self.model_options_edit.toPlainText().splitlines() if ln.strip()]
        if not options:
            options = MODEL_OPTIONS[:]  # fallback

        current_txt = self.model_combo.currentText() if self.model_combo.count() > 0 else ""
        current_idx = self.model_combo.currentIndex() if self.model_combo.count() > 0 else 0

        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        self.model_combo.addItems(options)

        # Try keep same text → same index → 0
        if current_txt:
            i = self.model_combo.findText(current_txt, Qt.MatchExactly)
            if i >= 0:
                self.model_combo.setCurrentIndex(i)
            elif 0 <= current_idx < self.model_combo.count():
                self.model_combo.setCurrentIndex(current_idx)
            else:
                self.model_combo.setCurrentIndex(0)
        else:
            self.model_combo.setCurrentIndex(0)
        self.model_combo.blockSignals(False)

    def _on_reload_click(self):
        """User clicked '从文本刷新选项': rebuild options, then re-apply saved selection, then mirror to data."""
        saved_idx = int(self.data.get("model_index", 0))
        saved_txt = self.data.get("model", "")

        self._reload_model_combo_from_text()

        # Re-apply saved selection after rebuild (no signals while restoring)
        self.model_combo.blockSignals(True)
        if 0 <= saved_idx < self.model_combo.count():
            self.model_combo.setCurrentIndex(saved_idx)
        elif saved_txt:
            i = self.model_combo.findText(saved_txt, Qt.MatchExactly)
            self.model_combo.setCurrentIndex(i if i >= 0 else 0)
        else:
            self.model_combo.setCurrentIndex(0)
        self.model_combo.blockSignals(False)

        # Mirror final selection & options to data once
        self.data["model_options"] = [self.model_combo.itemText(i) for i in range(self.model_combo.count())]
        self.data["model_index"] = self.model_combo.currentIndex()
        self.data["model"] = self.model_combo.currentText()
        self._update_mixing_button_state()

    def _on_model_changed(self, idx: int):
        """Keep 0-based model_index and model text in sync when user changes selection."""
        if idx < 0 or idx >= self.model_combo.count():
            return
        self.data["model_index"] = int(idx)  # 0-based
        self.data["model"] = self.model_combo.currentText()
        self._update_mixing_button_state()
        # If user picked Mixing Model, prompt configuration immediately (optional UX)
        if idx == 0:
            self._open_mixing_dialog()

    def _update_mixing_button_state(self):
        self.btn_config_mix.setEnabled(self.model_combo.currentIndex() == 0)

    def _open_mixing_dialog(self):
        """Open the MixingModelDialog, prechecked with saved names, and persist selection."""
        # Ensure options list reflects current combo/editor
        all_models = [self.model_combo.itemText(i) for i in range(self.model_combo.count())]
        # Saved names
        pre = self.data.get("mixing_model_names", [])
        dlg = MixingModelDialog(self, all_models, prechecked_names=pre)
        if dlg.exec() == QDialog.Accepted:
            chosen_names = dlg.selected_names()  # names excluding header
            # Map names back to global MODEL_OPTIONS indices (skip header at 0)
            name_to_global_index = {name: MODEL_OPTIONS.index(name) for name in MODEL_OPTIONS[1:] if name in MODEL_OPTIONS}
            indices_global = [name_to_global_index.get(n) for n in chosen_names if n in name_to_global_index]
            # Persist
            self.data["mixing_model_names"] = chosen_names
            self.data["mixing_model_indices"] = indices_global

    def _to_float(self, v, default=0.0) -> float:
        try:
            return float(v)
        except Exception:
            return default

    def _to_int(self, v, default=0) -> int:
        try:
            return int(v)
        except Exception:
            try:
                return int(float(v))
            except Exception:
                return default

    def _on_save(self):
        # Target settings.json path (allow "Save As")
        settings_path = self.settings_file_edit.text().strip() or self.settings_path
        settings_path = os.path.abspath(settings_path)

        existing = self._load_existing(settings_path)

        # Gather UI fields
        stencil_path = self.stencil_exe_edit.text().strip()
        soran_path = self.soran_exe_edit.text().strip()

        # Basic validation (remove if you prefer lax saving)
        if not stencil_path or not os.path.isfile(stencil_path):
            QMessageBox.critical(self, "设置", "请正确选择 StencilWizard 程序。")
            return
        if not soran_path or not os.path.isfile(soran_path):
            QMessageBox.critical(self, "设置", "请正确选择 Soran 程序。")
            return

        # Model-related
        model_options = [ln.strip() for ln in self.model_options_edit.toPlainText().splitlines() if ln.strip()]
        if not model_options:
            model_options = MODEL_OPTIONS[:]
        current_index = max(0, self.model_combo.currentIndex())
        current_model = self.model_combo.currentText()

        # Other params
        desorption = bool(self.desorption_chk.isChecked())
        pp0 = self.pp0_edit.text().strip() or "p0"
        unit = self.unit_edit.text().strip() or "cm3(STP)/g"

        # Save min/max as strings (to match your schema)
        min_val = self.min_spin.value()
        max_val = self.max_spin.value()
        min_p = f"{min_val:.2f}".rstrip('0').rstrip('.') if min_val % 1 else f"{int(min_val)}"
        max_p = f"{max_val:.2f}".rstrip('0').rstrip('.') if max_val % 1 else f"{int(max_val)}"
        smooth = str(self.smooth_spin.value())

        merged = dict(existing)
        merged.update({
            "stencil_exe": os.path.normpath(stencil_path),
            "soran_exe": os.path.normpath(soran_path),
            "model_options": model_options,
            "model_index": current_index,  # 0-based index (0..len-1)
            "model": current_model,
            "desorption": desorption,
            "pp0": pp0,
            "unit": unit,
            "min_pressure": min_p,
            "max_pressure": max_p,
            "smooth_factor": smooth,
            # mixing selections (already updated when user closed the mixing dialog)
            "mixing_model_indices": self.data.get("mixing_model_indices", []),
            "mixing_model_names": self.data.get("mixing_model_names", []),
        })

        # Ensure directory exists
        try:
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        except Exception:
            pass

        # Write file
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "设置", f"保存失败：\n{e}")
            return

        self.settings_path = settings_path
        self.data = merged
        self._data = merged
        QMessageBox.information(self, "设置", f"已保存到：\n{settings_path}")
        self.accept()


# ---- Optional: quick manual test ----
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dlg = SettingsDialog(settings_path="settings.json")
    dlg.show()
    sys.exit(app.exec())



# # settings_dialog.py
# from __future__ import annotations

# import json
# import os
# from typing import List

# from PySide6.QtCore import Qt
# from PySide6.QtWidgets import (
#     QCheckBox,
#     QComboBox,
#     QDialog,
#     QDialogButtonBox,
#     QDoubleSpinBox,
#     QFileDialog,
#     QFormLayout,
#     QGroupBox,
#     QHBoxLayout,
#     QLabel,
#     QLineEdit,
#     QMessageBox,
#     QPushButton,
#     QPlainTextEdit,
#     QSpinBox,
#     QVBoxLayout,
#     QWidget,
# )

# # ---- Master model list (fallback / default) ----
# MODEL_OPTIONS: List[str] = [
#     "Mixing Model ...",
#     "N2 in Carbon Slit pore at 77K",
#     "N2 in Carbon Cylindrical pore at 77K",
#     "N2 in Carbon Spherical pore at 77K",
#     "Ar in Zeolite Slit pore at 87K",
#     "Ar in Zeolite Cylindrical pore at 87K",
#     "Ar in Zeolite Spherical pore at 87K",
#     "CO2 in Carbon Slit pore at 273K",
#     "CO2 in Carbon Cylindric pore at 273K",
#     "CO2 in Carbon Spherical pore at 273K",
#     "N2 in Zeolite Slit pore at 77K",
#     "N2 in Zeolite Cylindrical pore at 77K",
#     "N2 in Zeolite Spherical pore at 77K",
#     "N2 in MOF (site Zn) at 77K",
#     "N2 in MOF (linker C) at 77K",
#     "N2 in MOF (site Al) at 77K",
#     "N2 in MOF (linker N) at 77K",
#     "N2 in Carbon Slit pore at 77K (2D-NLDFT)",
#     "N2 in Carbon Cylindrical pore at 77K (2D-NLDFT)",
#     "N2 in Carbon Spherical pore at 77K (2D-NLDFT)",
#     "Ar in Carbon Slit pore at 87K (zeolite-like)",
#     "Ar in Carbon Cylindrical pore at 87K (zeolite-like)",
#     "Ar in Carbon Spherical pore at 87K (zeolite-like)",
#     "N2 in Zeolite Slit pore at 77K (2D-NLDFT)",
#     "N2 in Zeolite Cylindrical pore at 77K (2D-NLDFT)",
#     "N2 in Zeolite Spherical pore at 77K (2D-NLDFT)",
#     "O2 in Carbon Slit pore at 87K",
#     "O2 in Carbon Cylindrical pore at 87K",
#     "O2 in Carbon Spherical pore at 87K",
#     "H2 in Carbon Slit pore at 77K",
#     "H2 in Carbon Cylindrical pore at 77K",
#     "H2 in Carbon Spherical pore at 77K",
#     "N2 in Carbon Slit pore at 77K (HS-2D-NLDFT)",
#     "N2 in Carbon Cylindrical pore at 77K (HS-2D-NLDFT)",
#     "N2 in Carbon Spherical pore at 77K (HS-2D-NLDFT)",
#     "N2 in Zeolite Slit pore at 77K (HS-2D-NLDFT)",
#     "N2 in Zeolite Cylindrical pore at 77K (HS-2D-NLDFT)",
#     "N2 in Zeolite Spherical pore at 77K (HS-2D-NLDFT)",
#     "H2 in Zeolite Slit pore at 77K",
#     "H2 in Zeolite Cylindrical pore at 77K",
#     "H2 in Zeolite Spherical pore at 77K",
#     "Ar in MFI Slit pore at 87K",
#     "Ar in MFI Cylindrical pore at 87K",
#     "Ar in MFI Spherical pore at 87K",
#     "O2 in MFI Slit pore at 77K",
#     "O2 in MFI Cylindrical pore at 77K",
#     "O2 in MFI Spherical pore at 77K",
# ]

# # ---- Defaults (overlayed on load) ----
# DEFAULTS = {
#     "stencil_exe": "",
#     "soran_exe": "",
#     "model": "N2 in Carbon Slit pore at 77K",
#     "model_index": 0,                 # 0-based index
#     "model_options": MODEL_OPTIONS,   # full list as default
#     "desorption": False,
#     "pp0": "p0",
#     "unit": "cm3(STP)/g",
#     "min_pressure": "0.05",
#     "max_pressure": "0.95",
#     "smooth_factor": "4",
# }


# class SettingsDialog(QDialog):
#     """
#     Settings UI matching the JSON schema:
#       stencil_exe, soran_exe,
#       model, model_index (0-based), model_options (list of strings),
#       desorption (bool), pp0, unit, min_pressure, max_pressure, smooth_factor
#     """

#     def __init__(self, parent: QWidget | None = None, settings_path: str | None = None):
#         super().__init__(parent)
#         self.setWindowTitle("设置")
#         self.resize(820, 640)
#         self.settings_path = os.path.abspath(settings_path or "settings.json")

#         # Read (with defaults merged for UI)
#         self.data = self._load_json(self.settings_path)
#         # Original existing JSON (so we can merge on save without dropping keys)
#         self._data = self._load_existing(self.settings_path)

#         # ===== Top row: settings.json path =====
#         top_row = QHBoxLayout()
#         self.settings_file_edit = QLineEdit(self.settings_path)
#         btn_browse_settings = QPushButton("保存为…")
#         btn_browse_settings.clicked.connect(self._choose_settings_path)
#         top_row.addWidget(QLabel("设置文件:"))
#         top_row.addWidget(self.settings_file_edit, 1)
#         top_row.addWidget(btn_browse_settings)

#         # ===== Executables =====
#         exe_group = QGroupBox("执行程序路径")
#         exe_form = QFormLayout()

#         self.stencil_exe_edit = QLineEdit(self.data.get("stencil_exe", ""))
#         btn_browse_stencil = QPushButton("选择…")
#         btn_browse_stencil.clicked.connect(self._choose_stencil_exe)
#         r1 = QHBoxLayout()
#         r1.addWidget(self.stencil_exe_edit, 1)
#         r1.addWidget(btn_browse_stencil)
#         exe_form.addRow(QLabel("StencilWizard:"), self._wrap(r1))

#         self.soran_exe_edit = QLineEdit(self.data.get("soran_exe", ""))
#         btn_browse_soran = QPushButton("选择…")
#         btn_browse_soran.clicked.connect(self._choose_soran_exe)
#         r2 = QHBoxLayout()
#         r2.addWidget(self.soran_exe_edit, 1)
#         r2.addWidget(btn_browse_soran)
#         exe_form.addRow(QLabel("Soran:"), self._wrap(r2))

#         exe_group.setLayout(exe_form)

#         # ===== DFT params =====
#         dft_group = QGroupBox("DFT 参数")
#         dft_form = QFormLayout()

#         # Model options editor (multiline) + refresh button
#         self.model_options_edit = QPlainTextEdit()
#         self.model_options_edit.setPlaceholderText("每行一个模型选项…")
#         self.model_options_edit.setPlainText("\n".join(self.data.get("model_options", [])))

#         self.model_combo = QComboBox()
#         self._reload_model_combo_from_text()  # pure UI rebuild, no data mutation

#         # Restore selection from settings.json (block signals to avoid clobber)
#         saved_idx = int(self.data.get("model_index", 0))
#         saved_txt = self.data.get("model", "")

#         self.model_combo.blockSignals(True)
#         if 0 <= saved_idx < self.model_combo.count():
#             self.model_combo.setCurrentIndex(saved_idx)
#         elif saved_txt:
#             i = self.model_combo.findText(saved_txt, Qt.MatchExactly)
#             self.model_combo.setCurrentIndex(i if i >= 0 else 0)
#         else:
#             self.model_combo.setCurrentIndex(0)
#         self.model_combo.blockSignals(False)

#         # Connect after restoration
#         self.model_combo.currentIndexChanged.connect(self._on_model_changed)

#         btn_reload_model = QPushButton("从文本刷新选项")
#         btn_reload_model.clicked.connect(self._on_reload_click)  # uses saved selection

#         row_model = QHBoxLayout()
#         row_model.addWidget(self.model_combo, 1)
#         row_model.addWidget(btn_reload_model)

#         self.desorption_chk = QCheckBox("Desorption")
#         self.desorption_chk.setChecked(bool(self.data.get("desorption", False)))

#         self.pp0_edit = QLineEdit(self.data.get("pp0", "p0"))
#         self.unit_edit = QLineEdit(self.data.get("unit", "cm3(STP)/g"))

#         self.min_spin = QDoubleSpinBox()
#         self.min_spin.setDecimals(4)
#         self.min_spin.setRange(0.0, 1.0)
#         self.min_spin.setSingleStep(0.01)
#         self.min_spin.setValue(self._to_float(self.data.get("min_pressure", "0.05"), 0.05))

#         self.max_spin = QDoubleSpinBox()
#         self.max_spin.setDecimals(4)
#         self.max_spin.setRange(0.0, 1.0)
#         self.max_spin.setSingleStep(0.01)
#         self.max_spin.setValue(self._to_float(self.data.get("max_pressure", "0.95"), 0.95))

#         self.smooth_spin = QSpinBox()
#         self.smooth_spin.setRange(0, 999)
#         self.smooth_spin.setValue(self._to_int(self.data.get("smooth_factor", "4"), 4))

#         # Layout rows
#         dft_form.addRow(QLabel("模型选项(每行一个):"), self.model_options_edit)
#         dft_form.addRow(QLabel("模型选择:"), self._wrap(row_model))
#         dft_form.addRow(QLabel("p/p0:"), self.pp0_edit)
#         dft_form.addRow(QLabel("单位:"), self.unit_edit)
#         dft_form.addRow(QLabel("最小压力:"), self.min_spin)
#         dft_form.addRow(QLabel("最大压力:"), self.max_spin)
#         dft_form.addRow(QLabel("平滑因子:"), self.smooth_spin)
#         dft_form.addRow(self.desorption_chk)
#         dft_group.setLayout(dft_form)

#         # ===== Buttons =====
#         buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
#         buttons.accepted.connect(self._on_save)
#         buttons.rejected.connect(self.reject)

#         # ===== Main layout =====
#         main = QVBoxLayout(self)
#         main.addLayout(top_row)
#         main.addWidget(exe_group)
#         main.addWidget(dft_group, 1)
#         main.addWidget(buttons)

#     # ---------- helpers ----------
#     def _wrap(self, layout: QHBoxLayout) -> QWidget:
#         w = QWidget()
#         w.setLayout(layout)
#         return w

#     def _load_existing(self, path: str) -> dict:
#         if os.path.exists(path):
#             try:
#                 with open(path, "r", encoding="utf-8") as f:
#                     return json.load(f)
#             except Exception:
#                 return {}
#         return {}

#     def _load_json(self, path: str) -> dict:
#         if os.path.exists(path):
#             try:
#                 with open(path, "r", encoding="utf-8") as f:
#                     data = json.load(f)
#                 # Overlay defaults so all keys exist
#                 merged = DEFAULTS | data
#                 if "model_options" not in merged or not isinstance(merged["model_options"], list):
#                     merged["model_options"] = list(DEFAULTS["model_options"])
#                 return merged
#             except Exception as e:
#                 QMessageBox.warning(self, "设置", f"读取设置失败：\n{e}\n使用默认值。")
#         return DEFAULTS.copy()

#     def _choose_settings_path(self):
#         path, _ = QFileDialog.getSaveFileName(
#             self, "保存设置为…", self.settings_path, "JSON Files (*.json);;All Files (*)"
#         )
#         if path:
#             self.settings_path = path
#             self.settings_file_edit.setText(path)

#     def _choose_stencil_exe(self):
#         path, _ = QFileDialog.getOpenFileName(
#             self, "选择 StencilWizard 程序", "", "Executables (*.exe);;All Files (*)"
#         )
#         if path:
#             self.stencil_exe_edit.setText(path)

#     def _choose_soran_exe(self):
#         path, _ = QFileDialog.getOpenFileName(
#             self, "选择 Soran 程序", "", "Executables (*.exe);;All Files (*)"
#         )
#         if path:
#             self.soran_exe_edit.setText(path)

#     def _reload_model_combo_from_text(self):
#         """Rebuild the combo from the multiline text, preserving selection if possible.
#         Does NOT mutate self.data (pure UI op).
#         """
#         options = [ln.strip() for ln in self.model_options_edit.toPlainText().splitlines() if ln.strip()]
#         if not options:
#             options = MODEL_OPTIONS[:]  # fallback

#         current_txt = self.model_combo.currentText() if self.model_combo.count() > 0 else ""
#         current_idx = self.model_combo.currentIndex() if self.model_combo.count() > 0 else 0

#         self.model_combo.blockSignals(True)
#         self.model_combo.clear()
#         self.model_combo.addItems(options)

#         # Try keep same text → same index → 0
#         if current_txt:
#             i = self.model_combo.findText(current_txt, Qt.MatchExactly)
#             if i >= 0:
#                 self.model_combo.setCurrentIndex(i)
#             elif 0 <= current_idx < self.model_combo.count():
#                 self.model_combo.setCurrentIndex(current_idx)
#             else:
#                 self.model_combo.setCurrentIndex(0)
#         else:
#             self.model_combo.setCurrentIndex(0)
#         self.model_combo.blockSignals(False)

#     def _on_reload_click(self):
#         """User clicked '从文本刷新选项': rebuild options, then re-apply saved selection, then mirror to data."""
#         saved_idx = int(self.data.get("model_index", 0))
#         saved_txt = self.data.get("model", "")

#         self._reload_model_combo_from_text()

#         # Re-apply saved selection after rebuild (no signals while restoring)
#         self.model_combo.blockSignals(True)
#         if 0 <= saved_idx < self.model_combo.count():
#             self.model_combo.setCurrentIndex(saved_idx)
#         elif saved_txt:
#             i = self.model_combo.findText(saved_txt, Qt.MatchExactly)
#             self.model_combo.setCurrentIndex(i if i >= 0 else 0)
#         else:
#             self.model_combo.setCurrentIndex(0)
#         self.model_combo.blockSignals(False)

#         # Mirror final selection & options to data once
#         self.data["model_options"] = [self.model_combo.itemText(i) for i in range(self.model_combo.count())]
#         self.data["model_index"] = self.model_combo.currentIndex()
#         self.data["model"] = self.model_combo.currentText()

#     def _to_float(self, v, default=0.0) -> float:
#         try:
#             return float(v)
#         except Exception:
#             return default

#     def _to_int(self, v, default=0) -> int:
#         try:
#             return int(v)
#         except Exception:
#             try:
#                 return int(float(v))
#             except Exception:
#                 return default

#     def _on_model_changed(self, idx: int):
#         """Keep 0-based model_index and model text in sync when user changes selection."""
#         if idx < 0 or idx >= self.model_combo.count():
#             return
#         self.data["model_index"] = int(idx)  # 0-based
#         self.data["model"] = self.model_combo.currentText()

#     def _on_save(self):
#         # Target settings.json path (allow "Save As")
#         settings_path = self.settings_file_edit.text().strip() or self.settings_path
#         settings_path = os.path.abspath(settings_path)

#         existing = self._load_existing(settings_path)

#         # Gather UI fields
#         stencil_path = self.stencil_exe_edit.text().strip()
#         soran_path = self.soran_exe_edit.text().strip()

#         # Basic validation (remove if you prefer lax saving)
#         if not stencil_path or not os.path.isfile(stencil_path):
#             QMessageBox.critical(self, "设置", "请正确选择 StencilWizard 程序。")
#             return
#         if not soran_path or not os.path.isfile(soran_path):
#             QMessageBox.critical(self, "设置", "请正确选择 Soran 程序。")
#             return

#         # Model-related
#         model_options = [ln.strip() for ln in self.model_options_edit.toPlainText().splitlines() if ln.strip()]
#         if not model_options:
#             model_options = MODEL_OPTIONS[:]
#         current_index = max(0, self.model_combo.currentIndex())
#         current_model = self.model_combo.currentText()

#         # Other params
#         desorption = bool(self.desorption_chk.isChecked())
#         pp0 = self.pp0_edit.text().strip() or "p0"
#         unit = self.unit_edit.text().strip() or "cm3(STP)/g"

#         # Save min/max as strings (to match your schema)
#         min_val = self.min_spin.value()
#         max_val = self.max_spin.value()
#         min_p = f"{min_val:.2f}".rstrip('0').rstrip('.') if min_val % 1 else f"{int(min_val)}"
#         max_p = f"{max_val:.2f}".rstrip('0').rstrip('.') if max_val % 1 else f"{int(max_val)}"
#         smooth = str(self.smooth_spin.value())

#         merged = dict(existing)
#         merged.update({
#             "stencil_exe": os.path.normpath(stencil_path),
#             "soran_exe": os.path.normpath(soran_path),
#             "model_options": model_options,
#             "model_index": current_index,  # 0-based index (0..len-1)
#             "model": current_model,
#             "desorption": desorption,
#             "pp0": pp0,
#             "unit": unit,
#             "min_pressure": min_p,
#             "max_pressure": max_p,
#             "smooth_factor": smooth,
#         })

#         # Ensure directory exists
#         try:
#             os.makedirs(os.path.dirname(settings_path), exist_ok=True)
#         except Exception:
#             pass

#         # Write file
#         try:
#             with open(settings_path, "w", encoding="utf-8") as f:
#                 json.dump(merged, f, ensure_ascii=False, indent=2)
#         except Exception as e:
#             QMessageBox.critical(self, "设置", f"保存失败：\n{e}")
#             return

#         self.settings_path = settings_path
#         self.data = merged
#         self._data = merged
#         QMessageBox.information(self, "设置", f"已保存到：\n{settings_path}")
#         self.accept()


# # ---- Optional: quick manual test ----
# if __name__ == "__main__":
#     import sys
#     from PySide6.QtWidgets import QApplication

#     app = QApplication(sys.argv)
#     dlg = SettingsDialog(settings_path="settings.json")
#     dlg.show()
#     sys.exit(app.exec())
# # # settings_dialog.py
# # from __future__ import annotations

# # import json
# # import os
# # from typing import List

# # from PySide6.QtCore import Qt
# # from PySide6.QtWidgets import (
# #     QCheckBox,
# #     QComboBox,
# #     QDialog,
# #     QDialogButtonBox,
# #     QDoubleSpinBox,
# #     QFileDialog,
# #     QFormLayout,
# #     QGroupBox,
# #     QHBoxLayout,
# #     QLabel,
# #     QLineEdit,
# #     QMessageBox,
# #     QPushButton,
# #     QPlainTextEdit,
# #     QSpinBox,
# #     QVBoxLayout,
# #     QWidget,
# # )

# # # ---- Master model list (for fallback / default) ----
# # MODEL_OPTIONS: List[str] = [
# #     "Mixing Model ...",
# #     "N2 in Carbon Slit pore at 77K",
# #     "N2 in Carbon Cylindrical pore at 77K",
# #     "N2 in Carbon Spherical pore at 77K",
# #     "Ar in Zeolite Slit pore at 87K",
# #     "Ar in Zeolite Cylindrical pore at 87K",
# #     "Ar in Zeolite Spherical pore at 87K",
# #     "CO2 in Carbon Slit pore at 273K",
# #     "CO2 in Carbon Cylindric pore at 273K",
# #     "CO2 in Carbon Spherical pore at 273K",
# #     "N2 in Zeolite Slit pore at 77K",
# #     "N2 in Zeolite Cylindrical pore at 77K",
# #     "N2 in Zeolite Spherical pore at 77K",
# #     "N2 in MOF (site Zn) at 77K",
# #     "N2 in MOF (linker C) at 77K",
# #     "N2 in MOF (site Al) at 77K",
# #     "N2 in MOF (linker N) at 77K",
# #     "N2 in Carbon Slit pore at 77K (2D-NLDFT)",
# #     "N2 in Carbon Cylindrical pore at 77K (2D-NLDFT)",
# #     "N2 in Carbon Spherical pore at 77K (2D-NLDFT)",
# #     "Ar in Carbon Slit pore at 87K (zeolite-like)",
# #     "Ar in Carbon Cylindrical pore at 87K (zeolite-like)",
# #     "Ar in Carbon Spherical pore at 87K (zeolite-like)",
# #     "N2 in Zeolite Slit pore at 77K (2D-NLDFT)",
# #     "N2 in Zeolite Cylindrical pore at 77K (2D-NLDFT)",
# #     "N2 in Zeolite Spherical pore at 77K (2D-NLDFT)",
# #     "O2 in Carbon Slit pore at 87K",
# #     "O2 in Carbon Cylindrical pore at 87K",
# #     "O2 in Carbon Spherical pore at 87K",
# #     "H2 in Carbon Slit pore at 77K",
# #     "H2 in Carbon Cylindrical pore at 77K",
# #     "H2 in Carbon Spherical pore at 77K",
# #     "N2 in Carbon Slit pore at 77K (HS-2D-NLDFT)",
# #     "N2 in Carbon Cylindrical pore at 77K (HS-2D-NLDFT)",
# #     "N2 in Carbon Spherical pore at 77K (HS-2D-NLDFT)",
# #     "N2 in Zeolite Slit pore at 77K (HS-2D-NLDFT)",
# #     "N2 in Zeolite Cylindrical pore at 77K (HS-2D-NLDFT)",
# #     "N2 in Zeolite Spherical pore at 77K (HS-2D-NLDFT)",
# #     "H2 in Zeolite Slit pore at 77K",
# #     "H2 in Zeolite Cylindrical pore at 77K",
# #     "H2 in Zeolite Spherical pore at 77K",
# #     "Ar in MFI Slit pore at 87K",
# #     "Ar in MFI Cylindrical pore at 87K",
# #     "Ar in MFI Spherical pore at 87K",
# #     "O2 in MFI Slit pore at 77K",
# #     "O2 in MFI Cylindrical pore at 77K",
# #     "O2 in MFI Spherical pore at 77K",
# # ]

# # # ---- Defaults (overlayed on load) ----
# # DEFAULTS = {
# #     "stencil_exe": "",
# #     "soran_exe": "",
# #     "model": "N2 in Carbon Slit pore at 77K",
# #     "model_index": 0,                 # 0-based index
# #     "model_options": MODEL_OPTIONS,   # full list as default
# #     "desorption": False,
# #     "pp0": "p0",
# #     "unit": "cm3(STP)/g",
# #     "min_pressure": "0.05",
# #     "max_pressure": "0.95",
# #     "smooth_factor": "4",
# # }


# # class SettingsDialog(QDialog):
# #     """
# #     Settings UI matching the JSON schema:
# #       stencil_exe, soran_exe,
# #       model, model_index (0-based), model_options (list of strings),
# #       desorption (bool), pp0, unit, min_pressure, max_pressure, smooth_factor
# #     """

# #     def __init__(self, parent: QWidget | None = None, settings_path: str | None = None):
# #         super().__init__(parent)
# #         self.setWindowTitle("设置")
# #         self.resize(820, 640)
# #         self.settings_path = os.path.abspath(settings_path or "settings.json")

# #         # Read (with defaults merged for UI)
# #         self.data = self._load_json(self.settings_path)
# #         # Original existing JSON (so we can merge on save without dropping keys)
# #         self._data = self._load_existing(self.settings_path)

# #         # ===== Top row: settings.json path =====
# #         top_row = QHBoxLayout()
# #         self.settings_file_edit = QLineEdit(self.settings_path)
# #         btn_browse_settings = QPushButton("保存为…")
# #         btn_browse_settings.clicked.connect(self._choose_settings_path)
# #         top_row.addWidget(QLabel("设置文件:"))
# #         top_row.addWidget(self.settings_file_edit, 1)
# #         top_row.addWidget(btn_browse_settings)

# #         # ===== Executables =====
# #         exe_group = QGroupBox("执行程序路径")
# #         exe_form = QFormLayout()

# #         self.stencil_exe_edit = QLineEdit(self.data.get("stencil_exe", ""))
# #         btn_browse_stencil = QPushButton("选择…")
# #         btn_browse_stencil.clicked.connect(self._choose_stencil_exe)
# #         r1 = QHBoxLayout()
# #         r1.addWidget(self.stencil_exe_edit, 1)
# #         r1.addWidget(btn_browse_stencil)
# #         exe_form.addRow(QLabel("StencilWizard:"), self._wrap(r1))

# #         self.soran_exe_edit = QLineEdit(self.data.get("soran_exe", ""))
# #         btn_browse_soran = QPushButton("选择…")
# #         btn_browse_soran.clicked.connect(self._choose_soran_exe)
# #         r2 = QHBoxLayout()
# #         r2.addWidget(self.soran_exe_edit, 1)
# #         r2.addWidget(btn_browse_soran)
# #         exe_form.addRow(QLabel("Soran:"), self._wrap(r2))

# #         exe_group.setLayout(exe_form)

# #         # ===== DFT params =====
# #         dft_group = QGroupBox("DFT 参数")
# #         dft_form = QFormLayout()

# #         # Model options editor (multiline) + refresh button
# #         self.model_options_edit = QPlainTextEdit()
# #         self.model_options_edit.setPlaceholderText("每行一个模型选项…")
# #         self.model_options_edit.setPlainText("\n".join(self.data.get("model_options", [])))

# #         self.model_combo = QComboBox()
# #         self._reload_model_combo_from_text()  # populate from editor text

# #         # Set current index from saved data; else by text; else 0
# #         saved_idx = int(self.data.get("model_index", 0))
# #         saved_txt = self.data.get("model", "")
# #         if 0 <= saved_idx < self.model_combo.count():
# #             self.model_combo.setCurrentIndex(saved_idx)
# #         elif saved_txt:
# #             i = self.model_combo.findText(saved_txt, Qt.MatchExactly)
# #             self.model_combo.setCurrentIndex(i if i >= 0 else 0)
# #         else:
# #             self.model_combo.setCurrentIndex(0)

# #         self.model_combo.blockSignals(False)

# #         # Connect after restoration so we don't clobber data during init
# #         self.model_combo.currentIndexChanged.connect(self._on_model_changed)

# #         btn_reload_model = QPushButton("从文本刷新选项")
# #         btn_reload_model.clicked.connect(self._reload_model_combo_from_text)

# #         row_model = QHBoxLayout()
# #         row_model.addWidget(self.model_combo, 1)
# #         row_model.addWidget(btn_reload_model)

# #         self.desorption_chk = QCheckBox("Desorption")
# #         self.desorption_chk.setChecked(bool(self.data.get("desorption", False)))

# #         self.pp0_edit = QLineEdit(self.data.get("pp0", "p0"))
# #         self.unit_edit = QLineEdit(self.data.get("unit", "cm3(STP)/g"))

# #         self.min_spin = QDoubleSpinBox()
# #         self.min_spin.setDecimals(4)
# #         self.min_spin.setRange(0.0, 1.0)
# #         self.min_spin.setSingleStep(0.01)
# #         self.min_spin.setValue(self._to_float(self.data.get("min_pressure", "0.05"), 0.05))

# #         self.max_spin = QDoubleSpinBox()
# #         self.max_spin.setDecimals(4)
# #         self.max_spin.setRange(0.0, 1.0)
# #         self.max_spin.setSingleStep(0.01)
# #         self.max_spin.setValue(self._to_float(self.data.get("max_pressure", "0.95"), 0.95))

# #         self.smooth_spin = QSpinBox()
# #         self.smooth_spin.setRange(0, 999)
# #         self.smooth_spin.setValue(self._to_int(self.data.get("smooth_factor", "4"), 4))

# #         # Layout rows
# #         dft_form.addRow(QLabel("模型选项(每行一个):"), self.model_options_edit)
# #         dft_form.addRow(QLabel("模型选择:"), self._wrap(row_model))
# #         dft_form.addRow(QLabel("p/p0:"), self.pp0_edit)
# #         dft_form.addRow(QLabel("单位:"), self.unit_edit)
# #         dft_form.addRow(QLabel("最小压力:"), self.min_spin)
# #         dft_form.addRow(QLabel("最大压力:"), self.max_spin)
# #         dft_form.addRow(QLabel("平滑因子:"), self.smooth_spin)
# #         dft_form.addRow(self.desorption_chk)
# #         dft_group.setLayout(dft_form)

# #         # ===== Buttons =====
# #         buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
# #         buttons.accepted.connect(self._on_save)
# #         buttons.rejected.connect(self.reject)

# #         # ===== Main layout =====
# #         main = QVBoxLayout(self)
# #         main.addLayout(top_row)
# #         main.addWidget(exe_group)
# #         main.addWidget(dft_group, 1)
# #         main.addWidget(buttons)

# #     # ---------- helpers ----------
# #     def _wrap(self, layout: QHBoxLayout) -> QWidget:
# #         w = QWidget()
# #         w.setLayout(layout)
# #         return w

# #     def _load_existing(self, path: str) -> dict:
# #         if os.path.exists(path):
# #             try:
# #                 with open(path, "r", encoding="utf-8") as f:
# #                     return json.load(f)
# #             except Exception:
# #                 return {}
# #         return {}

# #     def _load_json(self, path: str) -> dict:
# #         if os.path.exists(path):
# #             try:
# #                 with open(path, "r", encoding="utf-8") as f:
# #                     data = json.load(f)
# #                 # Overlay defaults so all keys exist
# #                 merged = DEFAULTS | data
# #                 if "model_options" not in merged or not isinstance(merged["model_options"], list):
# #                     merged["model_options"] = list(DEFAULTS["model_options"])
# #                 return merged
# #             except Exception as e:
# #                 QMessageBox.warning(self, "设置", f"读取设置失败：\n{e}\n使用默认值。")
# #         return DEFAULTS.copy()

# #     def _choose_settings_path(self):
# #         path, _ = QFileDialog.getSaveFileName(
# #             self, "保存设置为…", self.settings_path, "JSON Files (*.json);;All Files (*)"
# #         )
# #         if path:
# #             self.settings_path = path
# #             self.settings_file_edit.setText(path)

# #     def _choose_stencil_exe(self):
# #         path, _ = QFileDialog.getOpenFileName(
# #             self, "选择 StencilWizard 程序", "", "Executables (*.exe);;All Files (*)"
# #         )
# #         if path:
# #             self.stencil_exe_edit.setText(path)

# #     def _choose_soran_exe(self):
# #         path, _ = QFileDialog.getOpenFileName(
# #             self, "选择 Soran 程序", "", "Executables (*.exe);;All Files (*)"
# #         )
# #         if path:
# #             self.soran_exe_edit.setText(path)

# #     def _reload_model_combo_from_text(self):
# #         """Rebuild the combo from the multiline text, preserving selection if possible."""
# #         options = [ln.strip() for ln in self.model_options_edit.toPlainText().splitlines() if ln.strip()]
# #         if not options:
# #             options = MODEL_OPTIONS[:]  # fallback if user cleared everything

# #         current_txt = self.model_combo.currentText() if self.model_combo.count() > 0 else ""
# #         current_idx = self.model_combo.currentIndex() if self.model_combo.count() > 0 else 0
        
# #         self.model_combo.blockSignals(True)
# #         # current_txt = self.model_combo.currentText()
# #         self.model_combo.clear()
# #         self.model_combo.addItems(options)

# #         # Prefer to keep same text; else same index; else 0
# #         if current_txt:
# #             i = self.model_combo.findText(current_txt, Qt.MatchExactly)
# #             if i >= 0:
# #                 self.model_combo.setCurrentIndex(i)
# #             elif 0 <= current_idx < self.model_combo.count():
# #                 self.model_combo.setCurrentIndex(current_idx)
# #             else:
# #                 self.model_combo.setCurrentIndex(0)
# #         else:
# #             self.model_combo.setCurrentIndex(0)
# #         self.model_combo.blockSignals(False)

# #         # Mirror to data
# #         self.data["model_options"] = options
# #         self.data["model_index"] = self.model_combo.currentIndex()
# #         self.data["model"] = self.model_combo.currentText()

# #     def _to_float(self, v, default=0.0) -> float:
# #         try:
# #             return float(v)
# #         except Exception:
# #             return default

# #     def _to_int(self, v, default=0) -> int:
# #         try:
# #             return int(v)
# #         except Exception:
# #             try:
# #                 return int(float(v))
# #             except Exception:
# #                 return default

# #     def _on_model_changed(self, idx: int):
# #         """Keep 0-based model_index and model text in sync when user changes selection."""
# #         if idx < 0 or idx >= self.model_combo.count():
# #             # idx = max(0, min(idx, self.model_combo.count() - 1))
# #             # self.model_combo.blockSignals(True)
# #             # self.model_combo.setCurrentIndex(idx)
# #             # self.model_combo.blockSignals(False)
# #             return
# #         self.data["model_index"] = int(idx)  # 0-based
# #         self.data["model"] = self.model_combo.currentText()

# #     def _on_save(self):
# #         # Target settings.json path (allow "Save As")
# #         settings_path = self.settings_file_edit.text().strip() or self.settings_path
# #         settings_path = os.path.abspath(settings_path)

# #         existing = self._load_existing(settings_path)

# #         # Gather UI fields
# #         stencil_path = self.stencil_exe_edit.text().strip()
# #         soran_path = self.soran_exe_edit.text().strip()

# #         # Basic validation
# #         if not stencil_path or not os.path.isfile(stencil_path):
# #             QMessageBox.critical(self, "设置", "请正确选择 StencilWizard 程序。")
# #             return
# #         if not soran_path or not os.path.isfile(soran_path):
# #             QMessageBox.critical(self, "设置", "请正确选择 Soran 程序。")
# #             return

# #         # Model-related
# #         model_options = [ln.strip() for ln in self.model_options_edit.toPlainText().splitlines() if ln.strip()]
# #         if not model_options:
# #             model_options = MODEL_OPTIONS[:]
# #         current_index = max(0, self.model_combo.currentIndex())
# #         current_model = self.model_combo.currentText()

# #         # Other params
# #         desorption = bool(self.desorption_chk.isChecked())
# #         pp0 = self.pp0_edit.text().strip() or "p0"
# #         unit = self.unit_edit.text().strip() or "cm3(STP)/g"

# #         # Save min/max as strings (to match your schema)
# #         min_val = self.min_spin.value()
# #         max_val = self.max_spin.value()
# #         min_p = f"{min_val:.2f}".rstrip('0').rstrip('.') if min_val % 1 else f"{int(min_val)}"
# #         max_p = f"{max_val:.2f}".rstrip('0').rstrip('.') if max_val % 1 else f"{int(max_val)}"
# #         smooth = str(self.smooth_spin.value())

# #         merged = dict(existing)
# #         merged.update({
# #             "stencil_exe": os.path.normpath(stencil_path),
# #             "soran_exe": os.path.normpath(soran_path),
# #             "model_options": model_options,
# #             "model_index": current_index,  # 0-based index (0..len-1)
# #             "model": current_model,
# #             "desorption": desorption,
# #             "pp0": pp0,
# #             "unit": unit,
# #             "min_pressure": min_p,
# #             "max_pressure": max_p,
# #             "smooth_factor": smooth,
# #         })

# #         # Ensure directory exists
# #         try:
# #             os.makedirs(os.path.dirname(settings_path), exist_ok=True)
# #         except Exception:
# #             pass

# #         # Write file
# #         try:
# #             with open(settings_path, "w", encoding="utf-8") as f:
# #                 json.dump(merged, f, ensure_ascii=False, indent=2)
# #         except Exception as e:
# #             QMessageBox.critical(self, "设置", f"保存失败：\n{e}")
# #             return

# #         self.settings_path = settings_path
# #         self.data = merged
# #         self._data = merged
# #         QMessageBox.information(self, "设置", f"已保存到：\n{settings_path}")
# #         self.accept()

# #     def _on_reload_click(self):
# #         """User clicked '从文本刷新选项'."""
# #         saved_idx = int(self.data.get("model_index", 0))
# #         saved_txt = self.data.get("model", "")

# #         self._reload_model_combo_from_text()

# #         # Re-apply saved selection after rebuild
# #         self.model_combo.blockSignals(True)
# #         if 0 <= saved_idx < self.model_combo.count():
# #             self.model_combo.setCurrentIndex(saved_idx)
# #         elif saved_txt:
# #             i = self.model_combo.findText(saved_txt, Qt.MatchExactly)
# #             self.model_combo.setCurrentIndex(i if i >= 0 else 0)
# #         else:
# #             self.model_combo.setCurrentIndex(0)
# #         self.model_combo.blockSignals(False)

# #         # Mirror final selection to data once
# #         self.data["model_options"] = [self.model_combo.itemText(i) for i in range(self.model_combo.count())]
# #         self.data["model_index"] = self.model_combo.currentIndex()
# #         self.data["model"] = self.model_combo.currentText()

# # # ---- Optional: quick manual test ----
# # if __name__ == "__main__":
# #     import sys
# #     from PySide6.QtWidgets import QApplication

# #     app = QApplication(sys.argv)
# #     dlg = SettingsDialog(settings_path="settings.json")
# #     dlg.show()
# #     sys.exit(app.exec())


