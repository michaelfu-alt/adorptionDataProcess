# view/right_panel.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox, QLabel, QTextEdit,
    QTableWidget, QTableWidgetItem, QSplitter
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

class RightPanel(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6,6,6,6)
        layout.setSpacing(8)

        # 顶部 Sample Info
        info_group = QGroupBox("Sample Information")
        info_layout = QHBoxLayout()
        self.info_texts = [QTextEdit() for _ in range(3)]
        for t in self.info_texts:
            t.setReadOnly(True)
            info_layout.addWidget(t)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group, 2)

        # 中部 Result Summary
        result_group = QGroupBox("Result Summary")
        result_layout = QHBoxLayout()
        self.result_texts = [QTextEdit() for _ in range(3)]
        for t in self.result_texts:
            t.setReadOnly(True)
            result_layout.addWidget(t)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group, 2)

        # 下部 Tab（显示数据表、图）
        tabs = QTabWidget()
        # —— Adsorption Tab ——
        tab_ads = QWidget()
        ads_layout = QHBoxLayout(tab_ads)
        # Ads Table
        self.ads_table = QTableWidget(0, 4)
        self.ads_table.setHorizontalHeaderLabels([
            "P/P₀ (ads)", "V (ads)", "P/P₀ (des)", "V (des)"
        ])
        ads_layout.addWidget(self.ads_table, 1)
        # Ads Plot
        fig_ads = Figure(figsize=(4,3))
        self.ax_ads = fig_ads.add_subplot(111)
        self.ax_ads.set_xlabel("Pressure(P/P₀)")
        self.ax_ads.set_ylabel("Volume(cc/g)")
        self.ads_canvas = FigureCanvas(fig_ads)
        ads_layout.addWidget(self.ads_canvas, 2)
        tabs.addTab(tab_ads, "Adsorption")

        # —— PSD Tab ——
        tab_psd = QWidget()
        psd_layout = QHBoxLayout(tab_psd)
        # PSD Table
        self.psd_table = QTableWidget(0, 4)
        self.psd_table.setHorizontalHeaderLabels([
            "Diameter (nm)", "PSD(total)", "Pore Range(nm)", "Percentage(%)"
        ])
        psd_layout.addWidget(self.psd_table, 1)
        # PSD Plot
        fig_psd = Figure(figsize=(4,3))
        self.ax_psd = fig_psd.add_subplot(111)
        self.ax_psd.set_xlabel("Diameter (nm)")
        self.ax_psd.set_ylabel("PSD (total)")
        self.psd_canvas = FigureCanvas(fig_psd)
        psd_layout.addWidget(self.psd_canvas, 2)
        tabs.addTab(tab_psd, "Pore Size Dist.")

        layout.addWidget(tabs, 8)
        self.setLayout(layout)