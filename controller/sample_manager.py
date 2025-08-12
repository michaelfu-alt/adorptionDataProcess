# controller/sample_manager.py
# ① 样品的增删改查
# 	•	_load_sample_list
# 	•	_load_sample_details
# 	•	copy_samples
# 	•	paste_samples
# 	•	_clone_sample_from_external_db
# 	•	delete_sample
# 	•	edit_sample
# 	•	_on_edit_save
# 	•	find_duplicates
# 	•	_on_delete_duplicates
# 	•	define_sample_set
# 	•	compare_sample_sets
# 	•	_show_comparison_plot
# 	•	on_tree_select
# 	•	trace_samples

# ② 其它跟样品操作相关的状态变量
# 	•	self.sample_sets
# 	•	self._copied_samples
# 	•	self._copied_db_path

# •	所有直接涉及样品信息、操作的函数都迁移到 sample_manager.py。
# •	迁移过程中只需要将 self.model, self.view 替换为 self.controller.model/self.controller.view。
# •	若涉及到其它 manager 之间的协作，可在 manager 的 __init__ 里保存 main_controller 的引用。
from model.database_model import DatabaseModel
from view.dialog_window import EditSampleDialog
from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Slot
import json
import datetime

from view.duplicate_sample_dialog import DuplicateDeleteDialog
class SampleManager:
    def __init__(self, model, view):

        self.model = model
        self.view = view
        # 迁移以下属性（可在主controller.__init__中赋值）
        self.sample_sets = {}
        self._copied_samples = []
        self._copied_db_path = None

    def get_all_sample_details(self, sample_name):

        info = self.model.get_sample_info(sample_name)
        results = self.model.get_sample_results(sample_name)
        ads, des = self.model.get_adsorption_data(sample_name)
        psd_rows = self.model.get_dft_data(sample_name)
        # print("[SampleManager] info:", info)

        return {
            "info": info,
            "results": results,
            "ads": ads,
            "des": des,
            "psd": psd_rows
        }
    
    # Edit Sample info
    def get_edit_sample_info(self, sample_name):
        info = self.model.get_edit_sample_info(sample_name)
        return info
        
    def open_edit_dialog(self, sample_name, info, save_callback):
        dlg = EditSampleDialog(sample_name, info)
        if dlg.exec() == QDialog.Accepted:
            new_info = dlg.get_data()
            save_callback(sample_name, new_info)

    def save_sample_info(self, sample_name, updated_info):
        self.model.update_sample_info(sample_name, updated_info)

    #Delete Sample
    def delete_samples(self, sample_names):
        print("传入的 sample_names 类型:", type(sample_names))
        print("传入的 sample_names 内容:", sample_names)

        # 如果传进来是字符串，直接包装成列表
        if isinstance(sample_names, str):
            sample_names = [sample_names]
        for name in sample_names:
            print(f"{name} is called to delete")
            self.model.delete_sample(name)

    # Find Duplicate and Delete
    
    def find_duplicates(self):
        dup_groups = self.find_exact_duplicates_by_file()
        if not dup_groups:
            self.view.left_panel.show_no_duplicates()
            return

        # 计算默认删除项：每组保留 internal_name 最长的，其它选中删除
        to_delete = []
        for file_name, internal_names in dup_groups.items():
            keep = max(internal_names, key=len)
            for n in internal_names:
                if n != keep:
                    to_delete.append(n)

        # 弹窗选择删除（调用自定义的 DuplicateDeleteDialog）
        dlg = DuplicateDeleteDialog(dup_groups, preselect=to_delete, parent=self.view)
        dlg.deleteConfirmed.connect(self._on_delete_duplicates)
        dlg.exec()

    def find_exact_duplicates_by_file(self):
        overview_rows = self.model.get_sample_overview()
        groups = {}
        print(len(overview_rows))
        for row in overview_rows:
            internal_name = row[0]
            file_name   = row[1]
            print("Sample is called in Sample Manager")
            print(internal_name, file_name)
            groups.setdefault(file_name, []).append(internal_name)

        dup_groups = {k: v for k, v in groups.items() if len(v) > 1}
        return dup_groups

    @Slot(list)
    def _on_delete_duplicates(self, to_delete):
        if not to_delete:
            return

        confirm = self.view.left_panel.confirm_delete(to_delete)
        if not confirm:
            return

        errors = []
        for internal_name in to_delete:
            try:
                self.model.delete_sample(internal_name)
            except Exception as e:
                errors.append(f"Could not delete '{internal_name}': {str(e)}")

        # 刷新样品列表（你已有的刷新方法）
        self._load_sample_list()

        if errors:
            self.view.left_panel.show_delete_errors(errors)
        else:
            self.view.left_panel.show_deleted_info(len(to_delete))
    
    def _load_sample_list(self):
        # 调用 View 的刷新方法，或者 Controller 的刷新逻辑
        # 例如：
        try:
            self.view.left_panel.refresh_sample_table()
        except:
            print("Warning: view has no method refresh_sample_table")

    # Copy and paste function
    def copy_sample_data(self, sample_name: str) -> dict:
        """
        读取样品所有相关数据，返回完整字典结构
        """
        conn = self.model.conn
        c = conn.cursor()

        # 1) 找样品id
        c.execute("SELECT id FROM samples WHERE name = ?", (sample_name,))
        row = c.fetchone()
        if not row:
            raise ValueError(f"No such sample '{sample_name}' to copy.")
        sample_id = row[0]

        # 2) 读取 sample_info
        c.execute("SELECT field_name, field_value FROM sample_info WHERE sample_id = ?", (sample_id,))
        sample_info = {field: value for field, value in c.fetchall()}

        # 3) 读取 sample_results
        c.execute("SELECT result_name, result_value FROM sample_results WHERE sample_id = ?", (sample_id,))
        sample_results = {name: value for name, value in c.fetchall()}

        # 4) 读取 adsorption_data
        c.execute("SELECT q, i_ads, i_des FROM adsorption_data WHERE sample_id = ? ORDER BY q", (sample_id,))
        adsorption_data = [{"q": q, "i_ads": i_ads, "i_des": i_des} for q, i_ads, i_des in c.fetchall()]

        # 5) 读取 pore_distribution
        c.execute("SELECT pore_size, distribution FROM pore_distribution WHERE sample_id = ?", (sample_id,))
        pore_distribution = [{"pore_size": ps, "distribution": dist} for ps, dist in c.fetchall()]

        # 6) 读取 dft_data
        c.execute("SELECT row_index, data_json FROM dft_data WHERE sample_id = ? ORDER BY row_index", (sample_id,))
        dft_data = [json.loads(row[1]) for row in c.fetchall()]

        return {
            "name": sample_name,
            "sample_info": sample_info,
            "sample_results": sample_results,
            "adsorption_data": adsorption_data,
            "pore_distribution": pore_distribution,
            "dft_data": dft_data,
        }

    def paste_sample_data(self, sample_data: dict) -> str:
        """
        根据复制的数据插入一条新样品，返回新样品名
        """
        conn = self.model.conn
        c = conn.cursor()

        base_name = sample_data.get("name", "new_sample")
        name = base_name
        idx = 1
        c.execute("SELECT COUNT(*) FROM samples WHERE name = ?", (name,))
        while c.fetchone()[0] > 0:
            name = f"{base_name}_{idx}"
            idx += 1
            c.execute("SELECT COUNT(*) FROM samples WHERE name = ?", (name,))

        # 插入新样品
        c.execute("INSERT INTO samples (name) VALUES (?)", (name,))
        new_sample_id = c.lastrowid

        # 插入 Date Logged 时间戳
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute(
            "INSERT INTO sample_info (sample_id, field_name, field_value) VALUES (?, ?, ?)",
            (new_sample_id, "Date Logged", ts)
        )

        # 插入 sample_info
        for field, value in sample_data.get("sample_info", {}).items():
            c.execute(
                "INSERT INTO sample_info (sample_id, field_name, field_value) VALUES (?, ?, ?)",
                (new_sample_id, field, value)
            )

        # 插入 sample_results
        for result_name, result_value in sample_data.get("sample_results", {}).items():
            c.execute(
                "INSERT INTO sample_results (sample_id, result_name, result_value) VALUES (?, ?, ?)",
                (new_sample_id, result_name, result_value)
            )

        # 插入 adsorption_data
        for entry in sample_data.get("adsorption_data", []):
            c.execute(
                "INSERT INTO adsorption_data (sample_id, q, i_ads, i_des) VALUES (?, ?, ?, ?)",
                (new_sample_id, entry.get("q"), entry.get("i_ads"), entry.get("i_des"))
            )

        # 插入 pore_distribution
        for entry in sample_data.get("pore_distribution", []):
            c.execute(
                "INSERT INTO pore_distribution (sample_id, pore_size, distribution) VALUES (?, ?, ?)",
                (new_sample_id, entry.get("pore_size"), entry.get("distribution"))
            )

        # 插入 dft_data
        for idx, dft_row in enumerate(sample_data.get("dft_data", [])):
            dft_json = json.dumps(dft_row)
            c.execute(
                "INSERT INTO dft_data (sample_id, row_index, data_json) VALUES (?, ?, ?)",
                (new_sample_id, idx, dft_json)
            )

        conn.commit()
        return name
