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

class SampleManager:
    def __init__(self, model):
        self.model = model

        # 迁移以下属性（可在主controller.__init__中赋值）
        self.sample_sets = {}
        self._copied_samples = []
        self._copied_db_path = None

    def get_all_sample_details(self, sample_name):
        print("[SampleManager] get_all_sample_details, sample_name:", sample_name)

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
        for name in sample_names:
            self.model.delete_sample(name)
