# from PySide6.QtWidgets import (
#     QFileDialog, QDialog, QLabel, QProgressBar, QPushButton, QTextEdit, 
#     QVBoxLayout, QHBoxLayout, QMessageBox
# )

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QFileDialog, QMessageBox
import os
from view.process_dialog import ProcessDialog
import os, time
import pandas as pd   # 用于读取Excel


class ImportWorker(QObject):
    progress = Signal(int, int, str)
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, filepaths, model):
        super().__init__()
        self.filepaths = filepaths
        self.model = model
        self._paused = False
        self._cancelled = False
        self.loaded = []

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        print("Worker started")            
        total = len(self.filepaths)

        # 在线程内新建连接，不修改 self.model.conn
        thread_conn = self.model.get_thread_connection()

        try:
            for idx, fp in enumerate(self.filepaths, start=1):
                print(f"ImportWorker: processing file {idx}/{total}: {fp}")  # DEBUG

                if self._cancelled:
                    break
                while self._paused and not self._cancelled:
                    time.sleep(0.1)
                if self._cancelled:
                    break
                try:
                    filename = os.path.basename(fp)
                    self.progress.emit(idx, total, filename)
                    
                    # 调用 ingest_excel 时传入线程专属连接
                    self.model.ingest_excel(fp, conn=thread_conn)

                    print(f"ImportWorker: successfully loaded {fp}")  # DEBUG
                    self.loaded.append(filename)
                except Exception as e:
                    print(f"ImportWorker: error loading {fp}: {e}")
                    self.error.emit(f"Failed to import '{filename}':\n{e}")
        finally:
            thread_conn.commit()
            thread_conn.close()  # 用完关闭连接

        self.finished.emit(self.loaded)


class ImportExportManager(QObject):
    # import_started = Signal()
    # import_progress = Signal(int, int, str)  # current, total, filename
    import_error = Signal(str)
    import_finished = Signal(list)  # list of loaded files

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.worker = None
        self.thread = None
        self.progress_dialog = None
        self.summary_dialog = None

    def start_import(self, parent_widget):
        filepaths, _ = QFileDialog.getOpenFileNames(
            parent_widget,
            "Select one or more Excel files",
            "",
            "Excel Files (*.xls *.xlsx *.xlsm *.xlsb *.xltx *.xltm);;All Files (*)"
        )
        if not filepaths:
            return

        self.progress_dialog = ProcessDialog(len(filepaths))
        self.progress_dialog.pause_clicked.connect(self.pause_import)
        self.progress_dialog.continue_clicked.connect(self.resume_import)
        self.progress_dialog.end_clicked.connect(self.cancel_import)
        self.progress_dialog.show()

        self.worker = ImportWorker(filepaths, self.model)
        self.worker.progress.connect(self.progress_dialog.update_status)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.on_finished)

        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()
        # self.import_started.emit()

    def pause_import(self):
        if self.worker:
            self.worker.pause()

    def resume_import(self):
        if self.worker:
            self.worker.resume()

    def cancel_import(self):
        if self.worker:
            self.worker.cancel()

    def on_error(self, msg):
        self.import_error.emit(msg)

    def on_finished(self, loaded_files):
        if self.progress_dialog:
            self.progress_dialog.close()

        # 这里用主线程重新建立连接，确保安全
        try:
            if self.model.conn:
                self.model.conn.close()
            self.model.conn = self.model.get_main_thread_connection()
        except Exception as e:
            print("Error resetting main DB connection:", e)

        # 弹窗显示导入完成信息    
        summary_text = "\n".join(loaded_files)
        QMessageBox.information(
            self.progress_dialog.parent() or None,
            "Import Summary",
            f"Successfully imported {len(loaded_files)} files:\n{summary_text}"
        )
        self.import_finished.emit(loaded_files)


    def show_summary(parent, loaded_files):
        msg = QMessageBox(parent)
        msg.setWindowTitle("Import Summary")
        msg.setIcon(QMessageBox.Information)
        msg.setText(f"Successfully imported {len(loaded_files)} files:")
        msg.setDetailedText("\n".join(loaded_files))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
