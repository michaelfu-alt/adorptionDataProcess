from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTextEdit,
    QLabel, QLineEdit, QFileDialog, QDialog,QHBoxLayout, QApplication, QProgressBar
)
from PySide6.QtCore import Qt
from external_process_manager import ExternalProcessManager
import sys
import os
import tempfile
from folder_filter_dialog import FolderFilterDialog
from file_utils import scan_iprd_files, write_filelist
from PySide6.QtWidgets import QCheckBox
from merge_dft_worker import MergeDftWorker
from settings_dialog import SettingsDialog


class ExternalWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("外部程序控制")
        self.resize(800, 600)
        self.iprd_root_folder = None

        #Properties
        self.auto_merge_checkbox = QCheckBox("处理完成后自动合并结果文件")
        self.auto_merge_checkbox.setChecked(True)  # 默认勾选    

        # Input fields
        # ------- 文件路径设置 -------
        self.filelist_input = QLineEdit()
        self.settings_input = QLineEdit(r"settings.json")

        # 按钮们
        self.select_folder_btn = QPushButton("选择数据目录")
        self.filelist_btn = QPushButton("选择文件列表")
        self.settings_btn = QPushButton("选择设置文件")

        # 信号连接
        self.select_folder_btn.clicked.connect(self.select_and_prepare_filelist)
        self.filelist_btn.clicked.connect(self.select_filelist)
        self.settings_btn.clicked.connect(self.select_settings)

        # Layout 1：选择目录（生成文件列表）
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("数据目录:"))
        folder_layout.addWidget(self.select_folder_btn)

        # Layout 2：文件列表路径
        filelist_layout = QHBoxLayout()
        filelist_layout.addWidget(QLabel("文件列表:"))
        filelist_layout.addWidget(self.filelist_input)
        filelist_layout.addWidget(self.filelist_btn)

        # Layout 3：设置文件路径
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("设置路径:"))
        settings_layout.addWidget(self.settings_input)
        settings_layout.addWidget(self.settings_btn)
        
        # Log box
        self.logbox = QTextEdit()
        self.logbox.setReadOnly(True)

        self.status_label = QLabel("")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        # Buttons
        self.start_stencil_btn = QPushButton("运行 Stencil 控制流程")
        self.start_both_btn = QPushButton("运行 Stencil + Soran 流程")
        self.start_soran_btn = QPushButton("仅运行 Soran 控制流程")  # NEW
        self.settings_main_btn = QPushButton("设置…")

        self.settings_main_btn.clicked.connect(self.open_settings_dialog)
        self.start_stencil_btn.clicked.connect(self.run_stencil_only)
        self.start_both_btn.clicked.connect(self.run_stencil_then_soran)
        self.start_soran_btn.clicked.connect(self.run_soran_only)  # NEW


        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.start_stencil_btn)
        btn_layout.addWidget(self.start_both_btn)
        btn_layout.addWidget(self.start_soran_btn)  # NEW
        btn_layout.addWidget(self.settings_main_btn)

        layout = QVBoxLayout()
        layout.addLayout(folder_layout)
        layout.addLayout(filelist_layout)
        layout.addLayout(settings_layout)
        layout.addWidget(QLabel("运行日志："))
        layout.addWidget(self.logbox)
        layout.addLayout(btn_layout)
        layout.addWidget(self.status_label)
        layout.addWidget(self.auto_merge_checkbox)
        layout.addWidget(self.progress_bar)


        self.setLayout(layout)

        # Managers
        self.stencil_manager = ExternalProcessManager()
        self.soran_manager = ExternalProcessManager()

        self.stencil_manager.log_updated.connect(self.append_log)
        self.soran_manager.log_updated.connect(self.append_log)

        self.stencil_manager.finished.connect(self.on_stencil_finished)
        self.soran_manager.finished.connect(self.on_soran_finished)

        self.pending_soran = False

    def select_and_prepare_filelist(self):
        root_dir = QFileDialog.getExistingDirectory(self, "选择数据主目录")
        if not root_dir:
            return
        self.iprd_root_folder = root_dir

        # 弹出子文件夹排除窗口
        dialog = FolderFilterDialog(self, root_dir)
        if dialog.exec() != QDialog.Accepted:
            return

        excluded = dialog.get_excluded_folders()
        self.append_log(f"排除文件夹: {excluded}")
        self.append_log(f"[Root] 使用根目录：{self.iprd_root_folder}")


        # 扫描 .iPrd 文件
        iprd_files = scan_iprd_files(root_dir, excluded)
        self.append_log("-" * 60)
        for idx, path in enumerate(iprd_files, 1):
            self.append_log(f"{idx:3}. {path}")
        self.append_log("-" * 60)

        self.append_log(f"共找到 {len(iprd_files)} 个 .iPrd 文件")

        # 写入文件列表
        filelist_path = os.path.abspath("processfileiprdlist.txt")
        write_filelist(filelist_path, iprd_files)

        # 自动填入路径
        self.filelist_input.setText(filelist_path)
    
    def select_filelist(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择文件列表", "", "Text Files (*.txt);;All Files (*)")
        if path:
            self.filelist_input.setText(path)

    def select_settings(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择设置文件", "", "JSON Files (*.json);;All Files (*)")
        if path:
            self.settings_input.setText(path)

    def append_log(self, text):
        self.logbox.append(text)

    def run_stencil_only(self):
        self.pending_soran = False
        self._run_stencil()

    def run_stencil_then_soran(self):
        self.pending_soran = True
        # 如果清单已填，尽早推断 root
        fl = self.filelist_input.text().strip()
        if fl and os.path.isfile(fl) and not self.iprd_root_folder:
            try:
                with open(fl, "r", encoding="utf-8") as f:
                    lines = [ln.strip() for ln in f if ln.strip()]
                if lines:
                    root_guess = os.path.dirname(os.path.commonprefix(lines)) or os.path.dirname(lines[0])
                    if os.path.isdir(root_guess):
                        self.iprd_root_folder = root_guess
                        self.append_log(f"[Root] 从清单预设根目录：{self.iprd_root_folder}")
            except Exception as e:
                self.append_log(f"[WARN] 预设根目录失败：{e}")
        self._run_stencil()

    def _run_stencil(self):
        filelist_path = self.filelist_input.text().strip()
        settings_path = self.settings_input.text().strip()
        self.append_log(">>> 开始运行 Stencil 程序 <<<")
        self.stencil_manager.start_process(filelist_path, settings_path, script="stencilwizard_runner.py")

    def on_stencil_finished(self):
        self.append_log(">>> Stencil 任务完成 <<<")
        if self.pending_soran:
            self.append_log(">>> 准备转换文件列表为 Soran 格式（.txt） <<<")
            filelist_path = self.filelist_input.text().strip()
            settings_path = self.settings_input.text().strip()

        # Convert file list
        try:
            soran_filelist_path = self.convert_filelist_iprd_to_txt(filelist_path)
            self.append_log(f">>> 已生成 Soran 文件列表：{soran_filelist_path}")
        except Exception as e:
            self.append_log(f"[ERROR] 生成 Soran 文件列表失败: {e}")
            return
        
        self.append_log(">>> 开始运行 Soran 程序 <<<")
        self.soran_manager.start_process(soran_filelist_path, settings_path, script="soran_runner.py")

    def on_soran_finished(self):
        self.append_log(">>> Soran 任务完成 <<<")
        if self.auto_merge_checkbox.isChecked():
        # Ensure we have a valid root; try to infer from the file list if missing
            if not self.iprd_root_folder or not os.path.isdir(self.iprd_root_folder):
                fl = self.filelist_input.text().strip()
                try:
                    if os.path.isfile(fl):
                        with open(fl, "r", encoding="utf-8") as f:
                            lines = [ln.strip() for ln in f if ln.strip()]
                        if lines:
                            root_guess = os.path.dirname(os.path.commonprefix(lines)) or os.path.dirname(lines[0])
                            if os.path.isdir(root_guess):
                                self.iprd_root_folder = root_guess
                                self.append_log(f"[Root] 从清单推断根目录：{self.iprd_root_folder}")
                except Exception as e:
                    self.append_log(f"[WARN] 推断根目录失败：{e}")

        if not self.iprd_root_folder or not os.path.isdir(self.iprd_root_folder):
            self.append_log("[合并] 根目录无效，跳过自动合并。")
        else:
            self.append_log(f"[合并] 使用根目录（无需确认）：{self.iprd_root_folder}")
            self.run_merge_dft(self.iprd_root_folder)

        self.append_log(">>> 所有任务已完成<<<")
        
    def run_soran_only(self):
        self.pending_soran = False
        filelist_path = self.filelist_input.text().strip()
        settings_path = self.settings_input.text().strip()
        self.append_log(">>> 开始运行 Soran 程序 <<<")
        self.soran_manager.start_process(filelist_path, settings_path, script="soran_runner.py")

    def convert_filelist_iprd_to_txt(self, original_path: str) -> str:
        with open(original_path, "r", encoding="utf-8") as f:
            iprd_lines = [line.strip() for line in f if line.strip()]

        txt_lines = [line.replace(".iPrd", ".txt") for line in iprd_lines]

        # Write to temporary file
        fd, tmp_path = tempfile.mkstemp(suffix=".txt", prefix="converted_soran_list_", text=True)
        os.close(fd)  # Close the OS-level file handle (we'll overwrite it below)

        with open(tmp_path, "w", encoding="utf-8") as out:
            for line in txt_lines:
                out.write(line + "\n")

        return tmp_path

    def run_merge_dft(self, top_folder):
        self.merge_worker = MergeDftWorker(top_folder)
        self.merge_worker.progress_updated.connect(self.on_merge_progress)
        self.merge_worker.status_updated.connect(self.append_log)
        self.merge_worker.log_message.connect(self.append_log)
        self.merge_worker.finished.connect(self.on_merge_finished)
        self.merge_worker.start()

    def on_merge_progress(self, percent, current_index, current_file):
        self.progress_bar.setValue(percent)
        self.status_label.setText(f"处理第 {current_index} 个文件: {current_file}")

    def on_merge_finished(self, success_count, errors):
        self.append_log(f"[合并完成] 成功合并 {len(success_count)} 个文件组")
        if errors:
            self.append_log(">>> 合并中出现错误：")
            for base, msg in errors:
                self.append_log(f"[ERROR] {base}: {msg}")
    
    def open_settings_dialog(self):
    # Prefer current settings path in the edit; fallback to ./settings.json
        current_path = self.settings_input.text().strip() or os.path.abspath("settings.json")
        dlg = SettingsDialog(self, settings_path=current_path)
        if dlg.exec() == QDialog.Accepted:
            # Update settings path (user may have saved to a new path)
            self.settings_input.setText(dlg.settings_path)
            self.append_log(f"[设置] 已保存：{dlg.settings_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ExternalWindow()
    win.show()
    sys.exit(app.exec())
