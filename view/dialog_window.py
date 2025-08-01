from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QLabel
import traceback

class EditSampleDialog(QDialog):
    def __init__(self, sample_name, info: dict, parent=None):
        super().__init__(parent)
        
        print("EditSampleDialog收到info:", info)
        print("[DEBUG] _on_edit_clicked", sample_name)
        traceback.print_stack()

        self.setWindowTitle(f"Edit Sample: {sample_name}")
        self.entries = {}

        layout = QVBoxLayout(self)
        form = QFormLayout()
        for key, val in info.items():
            ent = QLineEdit(str(val))
            self.entries[key] = ent
            form.addRow(QLabel(key), ent)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("保存")
        btn_cancel = QPushButton("取消")
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        btn_save.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        self.setLayout(layout)  # 别忘了这句！

    def get_data(self):
        return {k: ent.text() for k, ent in self.entries.items()}
    
    def on_edit_save(self, sample_name, updated_info):
        # 1. 保存到数据库
        self.sample_manager.save_sample_info(sample_name, updated_info)

        # 2. 刷新左侧表格（可只刷新一行，也可全刷新）
        self.view.left_panel.refresh_table()  # 推荐全刷新，最简单

        # 3. 刷新右侧详情
        # 如果你的右侧详情和左表联动，可以直接重新加载
        details = self.sample_manager.get_all_sample_details(sample_name)
        self.view.right_panel.update_sample_details(details["info"], details["results"])
        self.view.right_panel.update_adsorption_data(details["ads"], details["des"])
        self.view.right_panel.update_psd_data(details["psd"])