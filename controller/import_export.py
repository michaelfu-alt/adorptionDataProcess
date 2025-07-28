from PySide6.QtWidgets import (
    QFileDialog, QDialog, QLabel, QProgressBar, QPushButton, QTextEdit, 
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt, QEventLoop
import os, time
import pandas as pd   # 用于读取Excel

class ImportExportManager:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    # def load_files(self):
    #     # 1. 选择文件
    #     file_dialog = QFileDialog(self.view)
    #     file_dialog.setFileMode(QFileDialog.ExistingFiles)
    #     file_dialog.setNameFilters(["Excel files (*.xls* *.xlsx *.xlsm *.xlsb *.xltx *.xltm)", "All files (*)"])
    #     file_dialog.setWindowTitle("Select one or more Excel files")
    #     if not file_dialog.exec():
    #         return
    #     filepaths = file_dialog.selectedFiles()
    #     if not filepaths:
    #         return

    #     total = len(filepaths)
    #     loaded = []

    #     # 2. 进度窗口
    #     prog_win = QDialog(self.view)
    #     prog_win.setWindowTitle("Importing Files…")
    #     prog_win.setModal(True)
    #     layout = QVBoxLayout(prog_win)

    #     label_info = QLabel("Importing files:")
    #     layout.addWidget(label_info)

    #     label_current = QLabel("Starting…")
    #     layout.addWidget(label_current)

    #     progress = QProgressBar()
    #     progress.setMaximum(total)
    #     layout.addWidget(progress)

    #     btn_layout = QHBoxLayout()
    #     btn_pause = QPushButton("Pause")
    #     btn_continue = QPushButton("Continue")
    #     btn_end = QPushButton("End")
    #     btn_layout.addWidget(btn_continue)
    #     btn_layout.addWidget(btn_pause)
    #     btn_layout.addWidget(btn_end)
    #     layout.addLayout(btn_layout)

    #     paused = False
    #     cancelled = False

    #     def on_pause():
    #         nonlocal paused
    #         paused = True
    #     def on_continue():
    #         nonlocal paused
    #         paused = False
    #     def on_end():
    #         nonlocal cancelled
    #         cancelled = True

    #     btn_pause.clicked.connect(on_pause)
    #     btn_continue.clicked.connect(on_continue)
    #     btn_end.clicked.connect(on_end)

    #     prog_win.show()
    #     def flush():
    #         prog_win.repaint()
    #         QEventLoop().processEvents()

    #     # 3. 文件读取与打印前三列
    #     for idx, filepath in enumerate(filepaths, start=1):
    #         if cancelled:
    #             break

    #         filename = os.path.basename(filepath)
    #         self.view.set_status(f"Importing {idx}/{total}: {filename}")
    #         label_current.setText(f"{idx}/{total}: {filename}")
    #         progress.setValue(idx)
    #         flush()

    #         while paused and not cancelled:
    #             time.sleep(0.1)
    #             flush()
    #         if cancelled:
    #             break

    #         try:
    #             # 读取Excel的第一个sheet前三列
    #             df = pd.read_excel(filepath, sheet_name=0)
    #             print(f"==={filename}===")
    #             print(df.iloc[:, :3].head())  # 打印前三列前五行
    #             loaded.append(filename)
    #         except Exception as e:
    #             QMessageBox.critical(self.view, "Import Error", f"Failed to read '{filename}':\n{e}")

    #         flush()

    #     prog_win.close()
    #     self.view.set_status(f"Import complete: {len(loaded)}/{total} files.")

    #     # 4. 总结
    #     summary = QDialog(self.view)
    #     summary.setWindowTitle("Import Summary")
    #     layout2 = QVBoxLayout(summary)
    #     layout2.addWidget(QLabel("Successfully imported:"))
    #     txt = QTextEdit()
    #     txt.setReadOnly(True)
    #     txt.setLineWrapMode(QTextEdit.NoWrap)
    #     txt.setFixedHeight(min(200, 24 * (len(loaded) + 2)))
    #     for fn in loaded:
    #         txt.append(f"• {fn}")
    #     layout2.addWidget(txt)
    #     btn_ok = QPushButton("OK")
    #     btn_ok.clicked.connect(summary.accept)
    #     layout2.addWidget(btn_ok, alignment=Qt.AlignRight)
    #     summary.exec()

    def load_files(self):
        filepaths, _ = QFileDialog.getOpenFileNames(
            self.view, "选择Excel文件", "", "Excel files (*.xls *.xlsx *.xlsm *.xlsb);;All files (*)"
        )
        if not filepaths:
            return

        # 打印前三列测试
        import pandas as pd
        for fp in filepaths:
            try:
                df = pd.read_excel(fp)
                print(f"{fp}: {df.iloc[:, :3].head()}")
            except Exception as e:
                print(f"Failed to read {fp}: {e}")

        # 后续：展示自定义进度窗口、调用后台处理