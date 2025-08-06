from PySide6.QtWidgets import QMessageBox, QFileDialog
from view.trace_view import TraceView
from controller.import_export import SampleExporter  # 你已有的导出类
from matplotlib.font_manager import FontProperties
import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.cm as cm

class TraceModel:
    def __init__(self, rows):
        self.rows = rows
        self._categorical_fields = ["样品名称", "吸附质", "检测员", "Probe molecule"]

    def get_rows(self):
        return self.rows

    def get_fields(self):
        return list(self.rows[0].keys()) if self.rows else []

    def filter_rows(self, field, op, val):
        def compare(v):
            try:
                return eval(f"{float(v)}{op}{float(val)}")
            except:
                if op == "==" and str(v) == val:
                    return True
                if op == "!=" and str(v) != val:
                    return True
                return False
        return [r for r in self.rows if compare(r.get(field))]

class TraceController:
    def __init__(self, global_model, trace_rows):
        self.global_model = global_model  # 主程序Model
        self.model = TraceModel(trace_rows)  # 本地Trace数据Model
        self.view = TraceView(self, self.model)

        # 加载中文字体，只尝试一次
        ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        font_path = os.path.join(ROOT_DIR, "asset", "fonts", "NotoSansSC-Regular.ttf")
        print(font_path)
        if os.path.exists(font_path):
            print(font_path)
            self.chinese_font = FontProperties(fname=font_path)
        else:
            self.chinese_font = FontProperties()  # 默认字体
        self.filtered_rows = trace_rows
        self.update_sample_list()

    def show(self):
        self.view.show()

    def update_sample_list(self):
        sample_names = [r.get("Sample Name") or r.get("样品名称") for r in self.filtered_rows]
        self.view.update_sample_list(sample_names)

    def on_filter(self, field, op, val):
        filtered = self.model.filter_rows(field, op, val)
        if filtered:
            self.filtered_rows = filtered
            self.update_sample_list()
        else:
            QMessageBox.information(self.view, "提示", "无符合条件的样品")
            self.filtered_rows = self.model.get_rows()
            self.update_sample_list()

    def on_reset_filter(self):
        self.filtered_rows = self.model.get_rows()
        self.update_sample_list()

    # def on_plot(self):
    #     fields = self.view.get_selected_fields()
    #     samples = self.view.get_selected_samples()
    #     if not fields:
    #         QMessageBox.warning(self.view, "提示", "请选择要绘制的字段")
    #         return
    #     if not samples:
    #         QMessageBox.warning(self.view, "提示", "请选择样品")
    #         return

    #     ax = self.view.ax
    #     ax.clear()

    #     x = range(len(fields))
    #     categorical_maps = {}
    #     for f in fields:
    #         if f in self.model._categorical_fields:
    #             cats = sorted(set(r.get(f) for r in self.filtered_rows if r.get(f) is not None))
    #             categorical_maps[f] = {v:i for i,v in enumerate(cats)}

    #     for sample_name in samples:
    #         row = next((r for r in self.filtered_rows if (r.get("Sample Name") == sample_name or r.get("样品名称") == sample_name)), None)
    #         if not row:
    #             continue
    #         ys = []
    #         for f in fields:
    #             v = row.get(f)
    #             if f in categorical_maps:
    #                 v = categorical_maps[f].get(v, 0)
    #             else:
    #                 try:
    #                     v = float(v)
    #                 except:
    #                     v = 0
    #             ys.append(v)
    #         ax.plot(x, ys, alpha=0.5)
        
    #     ax.set_xticks(x)
    #    # 关键：给xticklabels设置中文字体
    #     ax.set_xticklabels(fields, fontproperties=self.chinese_font, rotation=45, ha='right')

    #     # y轴标签加字体
    #     ax.set_ylabel("数值 / 分类", fontproperties=self.chinese_font)

    #     # 设置标题（可以按需加）
    #     ax.set_title("样品追踪", fontproperties=self.chinese_font)

    #     self.view.fig.tight_layout()
    #     self.view.canvas.draw()

    def on_plot(self):
        fields = self.view.get_selected_fields()
        samples = self.view.get_selected_samples()
        if not fields:
            QMessageBox.warning(self.view, "提示", "请选择要绘制的字段")
            return
        if not samples:
            QMessageBox.warning(self.view, "提示", "请选择样品")
            return

        ax = self.view.ax
        ax.clear()

        # 1. 找出分类字段和数值字段，计算归一化和类别映射
        categorical_maps = {}
        norm_minmax = {}

        for f in fields:
            # 取当前过滤行对应的字段值列表（非空）
            vals = [r.get(f) for r in self.filtered_rows if r.get(f) is not None]
            # 判断是否分类字段（字符串）
            if f in self.model._categorical_fields:
                cats = sorted(set(vals))
                categorical_maps[f] = {v: i for i, v in enumerate(cats)}
            else:
                # 数值字段，尝试转float
                nums = []
                for v in vals:
                    try:
                        nums.append(float(v))
                    except:
                        pass
                if nums:
                    minv, maxv = min(nums), max(nums)
                    if minv == maxv:
                        maxv = minv + 1  # 防止除0
                    norm_minmax[f] = (minv, maxv)
                else:
                    norm_minmax[f] = (0, 1)

        # 2. 准备颜色和线型映射
        colors = cm.get_cmap('tab10').colors  # 10种颜色
        line_styles = ['-', '--', '-.', ':']
        n_colors = len(colors)
        n_styles = len(line_styles)

        sample_color_style = {}
        for i, s in enumerate(samples):
            sample_color_style[s] = (colors[i % n_colors], line_styles[(i // n_colors) % n_styles])

        x = np.arange(len(fields))

        # 3. 画每个样品的曲线，计算y值归一化或分类映射
        for sample_name in samples:
            row = next((r for r in self.filtered_rows if (r.get("Sample Name") == sample_name or r.get("样品名称") == sample_name)), None)
            if not row:
                continue

            ys = []
            for f in fields:
                v = row.get(f)
                if f in categorical_maps:
                    # 分类映射成0~1区间
                    cats = categorical_maps[f]
                    idx = cats.get(v, 0)
                    n_cat = len(cats)
                    y_val = 0.1 + 0.8 * idx / max(1, n_cat - 1)
                else:
                    try:
                        num = float(v)
                        minv, maxv = norm_minmax.get(f, (0, 1))
                        y_val = 0.1 + 0.8 * (num - minv) / (maxv - minv)
                    except:
                        y_val = 0.1
                ys.append(y_val)

            c, ls = sample_color_style[sample_name]
            ln, = ax.plot(x, ys, color=c, linestyle=ls, marker='o', label=sample_name)

            # 4. 标记每个点的实际值（显示原始数值或分类名）
            for xi, yv, f in zip(x, ys, fields):
                val = row.get(f)
                if f in categorical_maps:
                    # 显示类别文本
                    text = str(val)
                else:
                    # 显示数值，保留3位小数
                    try:
                        text = f"{float(val):.3f}"
                    except:
                        text = str(val)
                ax.text(xi, yv, text, fontsize=8, ha='center', va='bottom')

        ax.set_xticks(x)
        ax.set_xticklabels(fields, fontproperties=self.chinese_font, rotation=45, ha='right')
        ax.set_ylim(0, 1.1)
        ax.set_ylabel("数值 / 分类", fontproperties=self.chinese_font)
        ax.set_title("样品追踪", fontproperties=self.chinese_font)
        ax.legend(loc='upper left', fontsize=8)

        self.view.fig.tight_layout()
        self.view.canvas.draw()



    def on_save_graph(self):
        path, _ = QFileDialog.getSaveFileName(self.view, "保存图像", filter="PNG Files (*.png)")
        if path:
            self.view.fig.savefig(path)

    def on_export(self):
        path, _ = QFileDialog.getSaveFileName(self.view, "导出Excel", filter="Excel Files (*.xlsx)")
        if not path:
            return

        samples = self.view.get_selected_samples()
        fields = self.view.get_selected_fields()

        if not samples:
            QMessageBox.warning(self.view, "提示", "请选择要导出的样品")
            return
        if not fields:
            QMessageBox.warning(self.view, "提示", "请选择要导出的字段")
            return

        try:
            exporter = SampleExporter(self.global_model, parent_widget=self.view)
            exporter.export(path, samples, summary_fields=fields)
            QMessageBox.information(self.view, "导出成功", f"成功导出 {len(samples)} 个样品到：\n{path}")
        except Exception as e:
            QMessageBox.critical(self.view, "导出失败", f"导出失败:\n{str(e)}")