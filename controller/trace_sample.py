from PySide6.QtWidgets import QMessageBox, QFileDialog, QDialog
from view.trace_view import TraceView
from controller.import_export import SampleExporter  # 你已有的导出类
from matplotlib.font_manager import FontProperties
import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.cm as cm

from view.filter_dialog import FilterDialog, FilterRule
import math

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
    """
    Builds trace rows from:
      - global_model.get_sample_info(name)      -> dict
      - global_model.get_sample_results(name)   -> dict
      - global_model.get_dft_data(name)         -> list[dict|tuple] to compute pore stats

    Each row merges info + results + pore stats:
      {
        "Sample Name": ...,
        ...info fields...,
        ...result fields...,
        "Pore Min (nm)": float|None,
        "Pore Max (nm)": float|None,
        "Pore Peak (nm)": float|None,
        "Pore Range (nm)": "min - max" | "-"
      }
    """
    def __init__(self, global_model, trace_rows):
        self.global_model = global_model  # 主程序Model
        rows = self._build_rows_from_model(trace_rows)

        self.model = TraceModel(rows)  # 本地Trace数据Model
        self.filtered_rows = rows
        self.view = TraceView(self, self.model)

        # 加载中文字体，只尝试一次
        ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        font_path = os.path.join(ROOT_DIR, "asset", "fonts", "NotoSansSC-Regular.ttf")
        print(font_path)
        if os.path.exists(font_path):
            self.chinese_font = FontProperties(fname=font_path)
        else:
            self.chinese_font = FontProperties()  # 默认字体
    
        if hasattr(self.view, "update_field_list"):
            self.view.update_field_list(self.model.get_fields())
        elif hasattr(self.view, "set_fields"):
            self.view.set_fields(self.model.get_fields())

        self.update_sample_list()
    # ----------------- data assembly helpers -----------------
    def _enumerate_samples(self):
        """
        Try to list sample names from global_model.
        Adjust this to your actual API if needed.
        """
        # preferred: an explicit API
        if hasattr(self.global_model, "list_samples"):
            try:
                return list(self.global_model.list_samples())
            except Exception:
                pass

        # fallback: if your model stores a dict/map
        if hasattr(self.global_model, "samples"):
            try:
                return list(self.global_model.samples.keys())
            except Exception:
                pass

        # last resort: empty
        return []
    
    def _build_rows_from_model(self, sample_names=None):
        """Merge info + results + pore stats per sample into a list of dicts."""
        # 1) Normalize to a list of names
        names = []
        if not sample_names:
            names = self._enumerate_samples()
        else:
            for item in sample_names:
                if isinstance(item, str):
                    names.append(item)
                elif isinstance(item, dict):
                    nm = item.get("Sample Name") or item.get("样品名称")
                    if nm:
                        names.append(nm)
                else:
                    # last resort: stringy form
                    try:
                        names.append(str(item))
                    except Exception:
                        pass

        rows = []
        for name in names:
            info = {}
            results = {}
            try:
                if hasattr(self.global_model, "get_sample_info"):
                    info = self.global_model.get_sample_info(name) or {}
            except Exception:
                pass
            try:
                if hasattr(self.global_model, "get_sample_results"):
                    results = self.global_model.get_sample_results(name) or {}
            except Exception:
                pass

            pore_stats = self._compute_pore_stats(name)

            # canonical display name
            if "样品名称" in info and info.get("样品名称"):
                canonical_name = info.get("样品名称")
            elif "Sample Name" in info and info.get("Sample Name"):
                canonical_name = info.get("Sample Name")
            else:
                canonical_name = name

            row = {
                "Sample Name": canonical_name,
                **info,
                **results,
                "Pore Min (nm)":  pore_stats.get("pore_min_nm"),
                "Pore Max (nm)":  pore_stats.get("pore_max_nm"),
                "Pore Peak (nm)": pore_stats.get("pore_peak_nm"),
                "Pore Range (nm)": pore_stats.get("pore_range_str"),
            }
            rows.append(row)

        return rows
    
    def _compute_pore_stats(self, sample_name):
        """
        Compute min/max/peak pore diameter from DFT data.
        Accepts rows of dicts with keys:
          "Pore Diameter(nm)" or "Pore Diameter (nm)"
          and either "PSD(total)" or "dV/dlogD"
        Or tuples/lists (x, y).
        """
        xs, ys = [], []
        try:
            if hasattr(self.global_model, "get_dft_data"):
                dft_list = self.global_model.get_dft_data(sample_name) or []
            else:
                dft_list = []
        except Exception:
            dft_list = []

        for entry in dft_list:
            x = y = None
            if isinstance(entry, dict):
                x = entry.get("Pore Diameter(nm)")
                if x is None:
                    x = entry.get("Pore Diameter (nm)")
                y = entry.get("PSD(total)")
                if y is None:
                    y = entry.get("dV/dlogD")
            elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                x, y = entry[0], entry[1]
            if x is None or y is None:
                continue
            try:
                xf = float(x)
                yf = float(y)
                xs.append(xf)
                ys.append(yf)
            except Exception:
                continue

        if not xs:
            return {
                "pore_min_nm": None,
                "pore_max_nm": None,
                "pore_peak_nm": None,
                "pore_range_str": "-",
            }

        xs_arr = np.asarray(xs, dtype=float)
        ys_arr = np.asarray(ys, dtype=float)
        pore_min = float(np.nanmin(xs_arr))
        pore_max = float(np.nanmax(xs_arr))

        # peak by max PSD if available
        try:
            peak_idx = int(np.nanargmax(ys_arr))
            pore_peak = float(xs_arr[peak_idx])
        except Exception:
            pore_peak = None

        # friendly range string
        range_str = f"{pore_min:.3f} - {pore_max:.3f}"

        return {
            "pore_min_nm": pore_min,
            "pore_max_nm": pore_max,
            "pore_peak_nm": pore_peak,
            "pore_range_str": range_str,
        }

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

    # ----------------- plotting / export (unchanged except fields now richer) -----------------
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

        # Prepare mapping
        categorical_maps = {}
        norm_minmax = {}
        for f in fields:
            vals = [r.get(f) for r in self.filtered_rows if r.get(f) is not None]
            if not vals:
                continue
            if f in self.model._categorical_fields or any(isinstance(v, str) for v in vals):
                cats = sorted(set(vals))
                categorical_maps[f] = {v: i for i, v in enumerate(cats)}
                norm_minmax[f] = (0, len(cats) - 1)
            else:
                nums = []
                for v in vals:
                    try:
                        nums.append(float(v))
                    except:
                        pass
                if nums:
                    minv, maxv = min(nums), max(nums)
                    if minv == maxv:
                        maxv = minv + 1
                    norm_minmax[f] = (minv, maxv)
                else:
                    norm_minmax[f] = (0, 1)

        # Plot setup
        x_positions = list(range(len(fields)))
        colors = plt.cm.get_cmap('tab10', len(samples))

        for i, sample_name in enumerate(samples):
            row = next((r for r in self.filtered_rows
                        if r.get("Sample Name") == sample_name or r.get("样品名称") == sample_name), None)
            if not row:
                continue

            y_values = []
            for f in fields:
                val = row.get(f)
                if f in categorical_maps:
                    idx = categorical_maps[f].get(val, 0)
                    y_values.append(idx)
                else:
                    try:
                        y_values.append(float(val))
                    except:
                        y_values.append(None)

            # Normalize all to [0,1]
            y_norm = []
            for yi, f in zip(y_values, fields):
                if yi is None:
                    y_norm.append(None)
                    continue
                minv, maxv = norm_minmax[f]
                y_norm.append((yi - minv) / (maxv - minv) if maxv > minv else 0.5)

            ax.plot(x_positions, y_norm, color=colors(i), label=sample_name, alpha=0.8)

        # Vertical axes
        for idx, f in enumerate(fields):
            ax.axvline(x=idx, color='gray', lw=0.5)
            if f in categorical_maps:
                cats = list(categorical_maps[f].keys())
                ax.set_yticks([i / (len(cats) - 1) if len(cats) > 1 else 0.5 for i in range(len(cats))])
                ax.set_yticklabels(cats, fontproperties=self.chinese_font)
            else:
                minv, maxv = norm_minmax[f]
                ax.text(idx, -0.05, f"{minv:.2f}", ha='center', va='top', fontsize=8)
                ax.text(idx, 1.05, f"{maxv:.2f}", ha='center', va='bottom', fontsize=8)

        ax.set_xticks(x_positions)
        ax.set_xticklabels(fields, fontproperties=self.chinese_font, rotation=45, ha='right')
        ax.set_ylim(-0.1, 1.1)
        ax.set_xlim(-0.5, len(fields) - 0.5)
        ax.legend(loc='upper right', fontsize=8)
        ax.set_title("平行坐标图", fontproperties=self.chinese_font)

        self.view.canvas.draw()
    
    def open_advanced_filter(self):
        fields = self.model.get_fields()
        dlg = FilterDialog(fields, parent=self.view)
        if dlg.exec() != QDialog.Accepted:
            return
        res = dlg.result()
        rules: list[FilterRule] = res["rules"]
        logic: str = res["logic"]  # "AND" / "OR"
        case: bool = res["case"]

        rows = self.model.get_rows()
        filtered = self._apply_advanced_filters(rows, rules, logic, case)
        if not filtered:
            QMessageBox.information(self.view, "提示", "无符合条件的样品")
            self.filtered_rows = rows
        else:
            self.filtered_rows = filtered
        self.update_sample_list()

    def _apply_advanced_filters(self, rows, rules: list, logic: str, case: bool):
        def matches(rule: FilterRule, row: dict) -> bool:
            v = row.get(rule.field, None)
            op = rule.op

            # numeric try
            def f(x):
                try:
                    return float(x)
                except Exception:
                    return None

            if op in (">", ">=", "<", "<=", "==", "!="):
                a = f(v); b = f(rule.v1)
                if a is not None and b is not None:
                    if op == ">":  return a >  b
                    if op == ">=": return a >= b
                    if op == "<":  return a <  b
                    if op == "<=": return a <= b
                    if op == "==": return a == b
                    if op == "!=": return a != b
                # fallback to string compare for ==/!= only
                if op in ("==","!="):
                    s1 = "" if v is None else str(v)
                    s2 = str(rule.v1)
                    if not case:
                        s1, s2 = s1.lower(), s2.lower()
                    return (s1 == s2) if op == "==" else (s1 != s2)
                return False

            if op == "between":
                a = f(v); lo = f(rule.v1); hi = f(rule.v2)
                if a is None or lo is None or hi is None:
                    return False
                if lo > hi: lo, hi = hi, lo
                return lo <= a <= hi

            # string ops
            s = "" if v is None else str(v)
            t = str(rule.v1)
            if not case:
                s, t = s.lower(), t.lower()

            if op == "contains":    return t in s
            if op == "startswith":  return s.startswith(t)
            if op == "endswith":    return s.endswith(t)
            return False

        out = []
        use_and = (logic.upper() == "AND")
        for r in rows:
            results = [matches(rule, r) for rule in rules]
            keep = all(results) if use_and else any(results)
            if keep:
                out.append(r)
        return out
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

    #     # 1. 找出分类字段和数值字段，计算归一化和类别映射
    #     categorical_maps = {}
    #     norm_minmax = {}

    #     for f in fields:
    #         # 取当前过滤行对应的字段值列表（非空）
    #         vals = [r.get(f) for r in self.filtered_rows if r.get(f) is not None]
    #         # 判断是否分类字段（字符串）
    #         if f in self.model._categorical_fields:
    #             cats = sorted(set(vals))
    #             categorical_maps[f] = {v: i for i, v in enumerate(cats)}
    #         else:
    #             # 数值字段，尝试转float
    #             nums = []
    #             for v in vals:
    #                 try:
    #                     nums.append(float(v))
    #                 except:
    #                     pass
    #             if nums:
    #                 minv, maxv = min(nums), max(nums)
    #                 if minv == maxv:
    #                     maxv = minv + 1  # 防止除0
    #                 norm_minmax[f] = (minv, maxv)
    #             else:
    #                 norm_minmax[f] = (0, 1)

    #     # 2. 准备颜色和线型映射
    #     colors = cm.get_cmap('tab10').colors  # 10种颜色
    #     line_styles = ['-', '--', '-.', ':']
    #     n_colors = len(colors)
    #     n_styles = len(line_styles)

    #     sample_color_style = {}
    #     for i, s in enumerate(samples):
    #         sample_color_style[s] = (colors[i % n_colors], line_styles[(i // n_colors) % n_styles])

    #     x = np.arange(len(fields))

    #     # 3. 画每个样品的曲线，计算y值归一化或分类映射
    #     for sample_name in samples:
    #         row = next((r for r in self.filtered_rows if (r.get("Sample Name") == sample_name or r.get("样品名称") == sample_name)), None)
    #         if not row:
    #             continue

    #         ys = []
    #         for f in fields:
    #             v = row.get(f)
    #             if f in categorical_maps:
    #                 # 分类映射成0~1区间
    #                 cats = categorical_maps[f]
    #                 idx = cats.get(v, 0)
    #                 n_cat = len(cats)
    #                 y_val = 0.1 + 0.8 * idx / max(1, n_cat - 1)
    #             else:
    #                 try:
    #                     num = float(v)
    #                     minv, maxv = norm_minmax.get(f, (0, 1))
    #                     y_val = 0.1 + 0.8 * (num - minv) / (maxv - minv)
    #                 except:
    #                     y_val = 0.1
    #             ys.append(y_val)

    #         c, ls = sample_color_style[sample_name]
    #         ln, = ax.plot(x, ys, color=c, linestyle=ls, marker='o', label=sample_name)

    #         # 4. 标记每个点的实际值（显示原始数值或分类名）
    #         for xi, yv, f in zip(x, ys, fields):
    #             val = row.get(f)
    #             if f in categorical_maps:
    #                 # 显示类别文本
    #                 text = str(val)
    #             else:
    #                 # 显示数值，保留3位小数
    #                 try:
    #                     text = f"{float(val):.3f}"
    #                 except:
    #                     text = str(val)
    #             ax.text(xi, yv, text, fontsize=8, ha='center', va='bottom')

    #     ax.set_xticks(x)
    #     ax.set_xticklabels(fields, fontproperties=self.chinese_font, rotation=45, ha='right')
    #     ax.set_ylim(0, 1.1)
    #     ax.set_ylabel("数值 / 分类", fontproperties=self.chinese_font)
    #     ax.set_title("样品追踪", fontproperties=self.chinese_font)
    #     ax.legend(loc='upper left', fontsize=8)

    #     self.view.fig.tight_layout()
    #     self.view.canvas.draw()



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