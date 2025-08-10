from __future__ import annotations
from typing import Sequence
import numpy as np 

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# -----------------------------
# Axis control popup (Qt)
# -----------------------------
class AxisControlDialog(QDialog):
    def __init__(self, ax, canvas: FigureCanvas, title: str = "Set Axis Scale", parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.ax = ax
        self.canvas = canvas

        self.orig_xlim = ax.get_xlim()
        self.orig_ylim = ax.get_ylim()

        self.xmin = QLineEdit(f"{self.orig_xlim[0]:.3f}")
        self.xmax = QLineEdit(f"{self.orig_xlim[1]:.3f}")
        self.ymin = QLineEdit(f"{self.orig_ylim[0]:.3f}")
        self.ymax = QLineEdit(f"{self.orig_ylim[1]:.3f}")
        self.lock_aspect = QCheckBox("Lock Aspect Ratio")

        form = QFormLayout()
        form.addRow("X Axis Min:", self.xmin)
        form.addRow("X Axis Max:", self.xmax)
        form.addRow("Y Axis Min:", self.ymin)
        form.addRow("Y Axis Max:", self.ymax)
        form.addRow(self.lock_aspect)

        btns = QDialogButtonBox()
        btn_apply = btns.addButton("Apply", QDialogButtonBox.ButtonRole.AcceptRole)
        btn_reset = btns.addButton("Reset", QDialogButtonBox.ButtonRole.ResetRole)
        btn_close = btns.addButton("Close", QDialogButtonBox.ButtonRole.RejectRole)

        btn_apply.clicked.connect(self.apply_scale)
        btn_reset.clicked.connect(self.reset_scale)
        btn_close.clicked.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(btns)

    def _parse_float(self, le: QLineEdit) -> float | None:
        try:
            return float(le.text())
        except ValueError:
            return None

    def apply_scale(self):
        x_min = self._parse_float(self.xmin)
        x_max = self._parse_float(self.xmax)
        y_min = self._parse_float(self.ymin)
        y_max = self._parse_float(self.ymax)
        if None in (x_min, x_max, y_min, y_max):
            QMessageBox.critical(self, "Invalid Input", "Please enter valid numeric values.")
            return
        if x_min >= x_max or y_min >= y_max:
            QMessageBox.critical(self, "Invalid Range", "Min must be less than Max for both axes.")
            return
        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)
        self.ax.set_aspect('equal' if self.lock_aspect.isChecked() else 'auto')
        self.canvas.draw_idle()
        self.accept()

    def reset_scale(self):
        self.xmin.setText(f"{self.orig_xlim[0]:.3f}")
        self.xmax.setText(f"{self.orig_xlim[1]:.3f}")
        self.ymin.setText(f"{self.orig_ylim[0]:.3f}")
        self.ymax.setText(f"{self.orig_ylim[1]:.3f}")
        self.ax.set_xlim(self.orig_xlim)
        self.ax.set_ylim(self.orig_ylim)
        self.ax.set_aspect('auto')
        self.canvas.draw_idle()


# -----------------------------
# Comparison Plot dialog
# -----------------------------
class ComparisonPlotDialog(QDialog):
    """
    Dual-panel Matplotlib dialog (Ads/Des on left, PSD on right) for PySide6.

    Expected model API:
        model.get_adsorption_data(sample_name) -> list[(x, y)] for ads, list[(x, y)] for des
        model.get_dft_data(sample_name) -> list[dict|tuple] where keys may include
            "Pore Diameter(nm)", "PSD(total)" or tuple/list (x, y)
    """
    def __init__(self, model, sample_names: Sequence[str], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Comparison Plot")
        self.resize(1100, 560)
        self.model = model
        self.sample_names = sample_names

        # Root layout: two columns
        root = QGridLayout(self)

        # Left: Ads/Des figure
        self.fig1 = Figure(figsize=(5, 4))
        self.ax1 = self.fig1.add_subplot(111)
        self._x_is_log_left = False

        self.ax1.set_xlabel("Pressure (P/P₀)")
        self.ax1.set_ylabel("Volume (cc/g)")
        self.canvas1 = FigureCanvas(self.fig1)
        left_box = QVBoxLayout()
        left_box.addWidget(self.canvas1, 1)
        left_btns = self._build_left_buttons()
        left_box.addLayout(left_btns)
        left_host = QWidget()
        left_host.setLayout(left_box)

        # Right: PSD figure
        self.fig2 = Figure(figsize=(5, 4))
        self.ax2 = self.fig2.add_subplot(111)
        self.ax2.set_xlabel("Pore Diameter (nm)")
        self.ax2.set_ylabel("PSD (total)")
        self.canvas2 = FigureCanvas(self.fig2)
        right_box = QVBoxLayout()
        right_box.addWidget(self.canvas2, 1)
        right_btns = self._build_right_buttons()
        right_box.addLayout(right_btns)
        right_host = QWidget()
        right_host.setLayout(right_box)

        root.addWidget(left_host, 0, 0)
        root.addWidget(right_host, 0, 1)
        root.setColumnStretch(0, 1)
        root.setColumnStretch(1, 1)
        root.setRowStretch(0, 1)

        # Data/lines holders
        self.ads_des_lines = []
        self.psd_lines = []
        self.legend1 = None
        self.legend2 = None

        self._populate()

    # ---------- UI builders ----------
    def _build_left_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()
        btn_toggle = QPushButton("Hide/Show Legend")
        self.btn_xscale_left = QPushButton("X: Lin→Log")  # ← was local var
        btn_axis = QPushButton("Set Axis")
        btn_save = QPushButton("Save Plot")
        btn_save_leg = QPushButton("Save Legend")
        
        # make it an instance attribute

        btn_toggle.clicked.connect(self._toggle_legend_1)
        btn_save.clicked.connect(self._save_plot_1)
        btn_save_leg.clicked.connect(self._save_legend_1)
        btn_axis.clicked.connect(lambda: self._open_axis_dialog(self.ax1, self.canvas1, "Set Ads/Des Axis"))
        self.btn_xscale_left.clicked.connect(self._toggle_xscale_left)

        # include the new button in the layout
        for b in (btn_toggle, btn_axis, self.btn_xscale_left, btn_save, btn_save_leg):
            row.addWidget(b)
        row.addStretch(1)
        return row

    def _build_right_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()
        btn_toggle = QPushButton("Hide/Show Legend")
        btn_axis = QPushButton("Set Axis")
        btn_save = QPushButton("Save Plot")
        btn_save_leg = QPushButton("Save Legend")
       
        btn_toggle.clicked.connect(self._toggle_legend_2)
        btn_save.clicked.connect(self._save_plot_2)
        btn_save_leg.clicked.connect(self._save_legend_2)
        btn_axis.clicked.connect(lambda: self._open_axis_dialog(self.ax2, self.canvas2, "Set PSD Axis"))

        for b in (btn_toggle, btn_axis, btn_save, btn_save_leg):
            row.addWidget(b)
        row.addStretch(1)
        return row

    # ---------- Data & plotting ----------
    def _populate(self):
        plot_data = []
        for name in self.sample_names:
            ads, des = self.model.get_adsorption_data(name)
            dft_list = self.model.get_dft_data(name)
            if (ads and len(ads) > 0) or (des and len(des) > 0) or (dft_list and len(dft_list) > 0):
                plot_data.append({"name": name, "ads": ads, "des": des, "dft": dft_list})

        if not plot_data:
            QMessageBox.information(self, "Send to Plot", "Selected sample(s) have no data.")
            self.reject()
            return

        # Left: Ads/Des
        for rec in plot_data:
            name = rec["name"]
            ads = rec.get("ads") or []
            des = rec.get("des") or []
            if ads:
                try:
                    x_ads, y_ads = zip(*ads)
                    line_a, = self.ax1.plot(x_ads, y_ads, marker="o", linestyle="-", label=f"{name} (ads)")
                    self.ads_des_lines.append(line_a)
                except Exception:
                    pass
            if des:
                try:
                    x_des, y_des = zip(*des)
                    line_d, = self.ax1.plot(x_des, y_des, marker="s", linestyle="--", label=f"{name} (des)")
                    self.ads_des_lines.append(line_d)
                except Exception:
                    pass
        self.legend1 = self.ax1.legend(fontsize=8, loc="upper right")
        self.canvas1.draw()

        # Right: PSD
        for rec in plot_data:
            name = rec["name"]
            dft_list = rec.get("dft") or []
            xs, ys = [], []
            for entry in dft_list:
                x = y = None
                if isinstance(entry, dict):
                    x = entry.get("Pore Diameter(nm)")
                    y = entry.get("PSD(total)")
                    if x is None:
                        x = entry.get("Pore Diameter (nm)")  # tolerate minor key variant
                    if y is None:
                        y = entry.get("dV/dlogD")  # tolerate alternative PSD key
                elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                    x, y = entry[0], entry[1]
                if x is not None and y is not None:
                    xs.append(x)
                    ys.append(y)
            if xs:
                line_p, = self.ax2.plot(xs, ys, linestyle="-", label=name)
                self.psd_lines.append(line_p)
        self.legend2 = self.ax2.legend(fontsize=8, loc="upper right")
        self.canvas2.draw()

    # ---------- Legend & save helpers ----------
    def _toggle_xscale_left(self):
        """Toggle left plot X-axis between linear and log.
        Safely masks nonpositive x values when switching to log.
        """
        self._x_is_log_left = not self._x_is_log_left
        use_log = self._x_is_log_left

        # Mask/clean any nonpositive x-data for log scale to avoid warnings
        min_pos = np.inf
        if use_log:
            for line in self.ads_des_lines:
                xd = np.asarray(line.get_xdata(), dtype=float)
                yd = np.asarray(line.get_ydata(), dtype=float)
                if xd.size == 0:
                    continue
                # keep only positive x for log scale
                mask = xd > 0
                if not np.all(mask):
                    line.set_data(xd[mask], yd[mask])
                # track smallest positive for reasonable xlim
                if np.any(mask):
                    min_pos = min(min_pos, np.min(xd[mask]))

        # Switch scale
        if use_log:
            self.ax1.set_xscale('log', nonpositive='clip')
            # Ensure left limit is positive
            if not np.isfinite(min_pos):
                min_pos = 1e-6
            left, right = self.ax1.get_xlim()
            # Keep right as-is, nudge left to a small positive value if needed
            left = max(min_pos * 0.8, 1e-6)
            if right <= left:
                right = left * 10.0
            self.ax1.set_xlim(left, right)
            self.btn_xscale_left.setText("X: Log→Lin")
             # --- NEW: vertical-only log grid (both major & minor) ---
            self.ax1.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5)
            self.ax1.tick_params(which='both', direction='in')
        else:
            self.ax1.set_xscale('linear')
            self.btn_xscale_left.setText("X: Lin→Log")
            self.ax1.set_xlim(0.0, 1.05)
            self.ax1.grid(False, axis='x')

        self.canvas1.draw_idle()
    def _toggle_legend_1(self):
        if self.legend1 is None:
            return
        self.legend1.set_visible(not self.legend1.get_visible())
        self.canvas1.draw_idle()

    def _toggle_legend_2(self):
        if self.legend2 is None:
            return
        self.legend2.set_visible(not self.legend2.get_visible())
        self.canvas2.draw_idle()

    def _save_plot_1(self):
        if self.legend1 is None:
            return
        fn, _ = QFileDialog.getSaveFileName(self, "Save Plot", "", "PNG (*.png);;SVG (*.svg);;PDF (*.pdf)")
        if fn:
            vis = self.legend1.get_visible()
            self.legend1.set_visible(False)
            self.fig1.savefig(fn, bbox_inches="tight")
            self.legend1.set_visible(vis)
            self.canvas1.draw_idle()

    def _save_plot_2(self):
        if self.legend2 is None:
            return
        fn, _ = QFileDialog.getSaveFileName(self, "Save Plot", "", "PNG (*.png);;SVG (*.svg);;PDF (*.pdf)")
        if fn:
            vis = self.legend2.get_visible()
            self.legend2.set_visible(False)
            self.fig2.savefig(fn, bbox_inches="tight")
            self.legend2.set_visible(vis)
            self.canvas2.draw_idle()

    def _save_legend_1(self):
        if self.legend1 is None:
            return
        fn, _ = QFileDialog.getSaveFileName(self, "Save Legend", "", "PNG (*.png);;SVG (*.svg);;PDF (*.pdf)")
        if fn:
            fig_leg = Figure(figsize=(4, 2))
            ax_leg = fig_leg.add_subplot(111)
            ax_leg.axis("off")
            handles = self.legend1.legendHandles
            labels = [t.get_text() for t in self.legend1.get_texts()]
            ax_leg.legend(handles, labels, loc="center left")
            fig_leg.savefig(fn, bbox_inches="tight")

    def _save_legend_2(self):
        if self.legend2 is None:
            return
        fn, _ = QFileDialog.getSaveFileName(self, "Save Legend", "", "PNG (*.png);;SVG (*.svg);;PDF (*.pdf)")
        if fn:
            fig_leg = Figure(figsize=(4, 2))
            ax_leg = fig_leg.add_subplot(111)
            ax_leg.axis("off")
            handles = self.legend2.legendHandles
            labels = [t.get_text() for t in self.legend2.get_texts()]
            ax_leg.legend(handles, labels, loc="center left")
            fig_leg.savefig(fn, bbox_inches="tight")

    def _open_axis_dialog(self, ax, canvas, title: str):
        dlg = AxisControlDialog(ax, canvas, title, self)
        dlg.exec()


# -----------------------------
# Controller integration helper
# -----------------------------
class PlotControllerMixin:
    """Mixin you can add to your MainController to provide send_to_plot().

    Requirements:
      - self.view.get_selected_sample_names() -> list[str]
      - self.model has get_adsorption_data(name) & get_dft_data(name)
      - self.main_window (QWidget) available as parent for dialogs
    """
    def send_to_plot(self):
        selected = []
        if hasattr(self.view, "get_selected_sample_names"):
            selected = self.view.get_selected_sample_names()
        if not selected:
            QMessageBox.information(self.main_window, "Send to Plot", "No samples selected.")
            return
        dlg = ComparisonPlotDialog(self.model, selected, parent=self.main_window)
        dlg.exec()


# -----------------------------
# Example view stub (replace with your actual view implementation)
# -----------------------------
class ViewStub:
    def __init__(self, sample_names: Sequence[str]):
        self._samples = list(sample_names)
    def get_selected_sample_names(self) -> list[str]:
        return self._samples


# -----------------------------
# Minimal example wiring (for testing)
# -----------------------------
if __name__ == "__main__":
    # Minimal test harness: run `python this_file.py` to validate UI opens
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow
    import math

    class DummyModel:
        def get_adsorption_data(self, name):
            # fake isotherm
            xs = [i/20 for i in range(1, 20)]
            ys = [math.log1p((i+1)/20.0) * (1 + hash(name) % 5 * 0.1) for i in range(1, 20)]
            ads = list(zip(xs, ys))
            des = list(zip(xs[::-1], [y*0.9 for y in ys][::-1]))
            return ads, des
        def get_dft_data(self, name):
            xs = [0.35 + 0.05*i for i in range(1, 30)]
            ys = [math.exp(-((x-1.2)**2)/(2*0.15**2)) * (1 + (hash(name) % 7)*0.05) for x in xs]
            return [{"Pore Diameter(nm)": x, "PSD(total)": y} for x, y in zip(xs, ys)]

    class MainApp(QMainWindow, PlotControllerMixin):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("MainApp Demo")
            self.resize(960, 640)
            self.model = DummyModel()
            self.view = ViewStub(["Sample A", "Sample B"])  # pretend these are selected
            self.main_window = self

            btn = QPushButton("Send to Plot")
            btn.clicked.connect(self.send_to_plot)
            host = QWidget()
            lay = QVBoxLayout(host)
            lay.addWidget(QLabel("Demo: click to open Comparison Plot"))
            lay.addWidget(btn)
            self.setCentralWidget(host)

    app = QApplication(sys.argv)
    w = MainApp()
    w.show()
    sys.exit(app.exec())
