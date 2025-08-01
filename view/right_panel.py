# # view/right_panel.py
# from PySide6.QtWidgets import (
#     QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox, QLabel, QTextEdit,
#     QTableWidget, QTableWidgetItem, QSplitter
# )
# from matplotlib.figure import Figure
# from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

# class RightPanel(QWidget):
#     def __init__(self, controller, parent=None):
#         super().__init__(parent)
#         layout = QVBoxLayout(self)

#         self.controller = controller
#         self.info_label = QLabel()
#         self.results_label = QLabel()
#         layout.setContentsMargins(6,6,6,6)
#         layout.setSpacing(8)

#         # 顶部 Sample Info
#         info_group = QGroupBox("Sample Information")
#         info_layout = QHBoxLayout()
#         self.info_texts = [QTextEdit() for _ in range(3)]
#         for t in self.info_texts:
#             t.setReadOnly(True)
#             info_layout.addWidget(t)
#         info_group.setLayout(info_layout)
#         layout.addWidget(info_group, 2)

#         # 中部 Result Summary
#         result_group = QGroupBox("Result Summary")
#         result_layout = QHBoxLayout()
#         self.result_texts = [QTextEdit() for _ in range(3)]
#         for t in self.result_texts:
#             t.setReadOnly(True)
#             result_layout.addWidget(t)
#         result_group.setLayout(result_layout)
#         layout.addWidget(result_group, 2)

#         # 下部 Tab（显示数据表、图）
#         tabs = QTabWidget()
#         # —— Adsorption Tab ——
#         tab_ads = QWidget()
#         ads_layout = QHBoxLayout(tab_ads)
#         # Ads Table
#         self.ads_table = QTableWidget(0, 4)
#         self.ads_table.setHorizontalHeaderLabels([
#             "P/P₀ (ads)", "V (ads)", "P/P₀ (des)", "V (des)"
#         ])
#         ads_layout.addWidget(self.ads_table, 1)
#         # Ads Plot
#         fig_ads = Figure(figsize=(4,3))
#         self.ax_ads = fig_ads.add_subplot(111)
#         self.ax_ads.set_xlabel("Pressure(P/P₀)")
#         self.ax_ads.set_ylabel("Volume(cc/g)")
#         self.ads_canvas = FigureCanvas(fig_ads)
#         ads_layout.addWidget(self.ads_canvas, 2)
#         tabs.addTab(tab_ads, "Adsorption")

#         # —— PSD Tab ——
#         tab_psd = QWidget()
#         psd_layout = QHBoxLayout(tab_psd)
#         # PSD Table
#         self.psd_table = QTableWidget(0, 4)
#         self.psd_table.setHorizontalHeaderLabels([
#             "Diameter (nm)", "PSD(total)", "Pore Range(nm)", "Percentage(%)"
#         ])
#         psd_layout.addWidget(self.psd_table, 1)
#         # PSD Plot
#         fig_psd = Figure(figsize=(4,3))
#         self.ax_psd = fig_psd.add_subplot(111)
#         self.ax_psd.set_xlabel("Diameter (nm)")
#         self.ax_psd.set_ylabel("PSD (total)")
#         self.psd_canvas = FigureCanvas(fig_psd)
#         psd_layout.addWidget(self.psd_canvas, 2)
#         tabs.addTab(tab_psd, "Pore Size Dist.")

#         layout.addWidget(tabs, 8)
#         self.setLayout(layout)
    
#     def update_sample_details(self, info, results):
#         # 这里可以自定义格式
#         info_text = "\n".join([f"{k}: {v}" for k, v in info.items()])
#         result_text = "\n".join([f"{k}: {v}" for k, v in results.items()])
#         self.info_label.setText(f"样品信息:\n{info_text}")
#         self.results_label.setText(f"分析结果:\n{result_text}")

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTextEdit, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

class RightPanel(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.controller = controller
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # —— 顶部 Sample Info ——
        info_group = QGroupBox("Sample Information")
        info_layout = QHBoxLayout()
        self.info_texts = [QTextEdit() for _ in range(3)]
        for t in self.info_texts:
            t.setReadOnly(True)
            info_layout.addWidget(t)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group, 2)

        # —— 中部 Result Summary ——
        result_group = QGroupBox("Result Summary")
        result_layout = QHBoxLayout()
        self.result_texts = [QTextEdit() for _ in range(3)]
        for t in self.result_texts:
            t.setReadOnly(True)
            result_layout.addWidget(t)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group, 2)

        # —— 下部 Tabs (数据/图表) ——
        tabs = QTabWidget()
        # — Adsorption Tab —
        tab_ads = QWidget()
        ads_layout = QHBoxLayout(tab_ads)
        self.ads_table = QTableWidget(0, 4)
        self.ads_table.setHorizontalHeaderLabels([
            "P/P₀ (ads)", "V (ads)", "P/P₀ (des)", "V (des)"
        ])
        ads_layout.addWidget(self.ads_table, 1)
        fig_ads = Figure(figsize=(4,3))
        self.ax_ads = fig_ads.add_subplot(111)
        self.ax_ads.set_xlabel("Pressure(P/P₀)")
        self.ax_ads.set_ylabel("Volume(cc/g)")
        self.ads_canvas = FigureCanvas(fig_ads)
        ads_layout.addWidget(self.ads_canvas, 2)
        tabs.addTab(tab_ads, "Adsorption")

        # — PSD Tab —
        tab_psd = QWidget()
        psd_layout = QHBoxLayout(tab_psd)
        self.psd_table = QTableWidget(0, 4)
        self.psd_table.setHorizontalHeaderLabels([
            "Diameter (nm)", "PSD(total)", "Pore Range(nm)", "Percentage(%)"
        ])
        psd_layout.addWidget(self.psd_table, 1)
        fig_psd = Figure(figsize=(4,3))
        self.ax_psd = fig_psd.add_subplot(111)
        self.ax_psd.set_xlabel("Diameter (nm)")
        self.ax_psd.set_ylabel("PSD (total)")
        self.psd_canvas = FigureCanvas(fig_psd)
        psd_layout.addWidget(self.psd_canvas, 2)
        tabs.addTab(tab_psd, "Pore Size Dist.")

        layout.addWidget(tabs, 8)
        self.setLayout(layout)

    def update_sample_details(self, info, results):
        """
        info, results: dict
        """
        print("update_sample_details in right panel called!")

        def split_lines(lines, ncols):
            avg = (len(lines) + ncols - 1) // ncols
            return [lines[i*avg:(i+1)*avg] for i in range(ncols)]

        info_lines = [f"{k}: {v}" for k, v in info.items()]
        result_lines = [f"{k}: {v}" for k, v in results.items()]

        info_cols = split_lines(info_lines, len(self.info_texts))
        result_cols = split_lines(result_lines, len(self.result_texts))

        for textedit, lines in zip(self.info_texts, info_cols):
            textedit.setText("\n".join(lines))
        for textedit, lines in zip(self.result_texts, result_cols):
            textedit.setText("\n".join(lines))

    def update_adsorption_data(self, ads_list, des_list):
        """
        ads_list, des_list: [(p, v), ...]
        """
        n = max(len(ads_list), len(des_list))
        self.ads_table.setRowCount(n)
        for i in range(n):
            p_ads, v_ads = ads_list[i] if i < len(ads_list) else ("", "")
            p_des, v_des = des_list[i] if i < len(des_list) else ("", "")
            self.ads_table.setItem(i, 0, QTableWidgetItem(str(p_ads)))
            self.ads_table.setItem(i, 1, QTableWidgetItem(str(v_ads)))
            self.ads_table.setItem(i, 2, QTableWidgetItem(str(p_des)))
            self.ads_table.setItem(i, 3, QTableWidgetItem(str(v_des)))

        # 更新吸附等温线曲线
        self.ax_ads.clear()
        if ads_list:
            ps, vs = zip(*ads_list)
            self.ax_ads.plot(ps, vs, label="Adsorption")
        if des_list:
            ps, vs = zip(*des_list)
            self.ax_ads.plot(ps, vs, label="Desorption")
        self.ax_ads.set_xlabel("P/P₀")
        self.ax_ads.set_ylabel("V (cc/g)")
        self.ax_ads.legend()
        self.ads_canvas.draw()

    def update_psd_data(self, psd_rows):
        """
        psd_rows: [{"Pore Diameter(nm)": d, "PSD(total)": psd, "pore_range": r, "percentage": pct}, ...]
        """
        self.psd_table.setRowCount(len(psd_rows))
        for i, row in enumerate(psd_rows):
            self.psd_table.setItem(i, 0, QTableWidgetItem(str(row.get("Pore Diameter(nm)", ""))))
            self.psd_table.setItem(i, 1, QTableWidgetItem(str(row.get("PSD(total)", ""))))
            self.psd_table.setItem(i, 2, QTableWidgetItem(str(row.get("pore_range", ""))))
            self.psd_table.setItem(i, 3, QTableWidgetItem(str(row.get("percentage", ""))))

        # PSD 曲线
        self.ax_psd.clear()
        ds = [row.get("Pore Diameter(nm)") for row in psd_rows if row.get("Pore Diameter(nm)") is not None]
        psds = [row.get("PSD(total)") for row in psd_rows if row.get("PSD(total)") is not None]
        if ds and psds:
            self.ax_psd.plot(ds, psds, marker="o", linestyle="-")
        self.ax_psd.set_xlabel("Diameter (nm)")
        self.ax_psd.set_ylabel("PSD (total)")
        self.psd_canvas.draw()
    
    # Delete Sample
    def clear(self):
        """清空所有显示内容"""
        self.update_sample_details({}, {})  # 传空字典，详情区也就空了
        self.update_adsorption_data([], []) # 传空
        self.update_psd_data([])           # 传空