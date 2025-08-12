# # controller/external_process_manager.py

# # 文件: controller/external_process_manager.py

# # automation/external_process_manager.py
# from PySide6.QtCore import QProcess, QObject, Signal
# import os
# import sys

# class ExternalProcessManager(QObject):
#     log_updated = Signal(str)
#     finished = Signal(str)

#     def __init__(self, name: str, script_path: str, args: list):
#         super().__init__()
#         self.name = name
#         self.script_path = script_path
#         self.args = args
#         self.process = QProcess()
#         self._connect_signals()

#     def _connect_signals(self):
#         self.process.readyReadStandardOutput.connect(self._on_stdout)
#         self.process.readyReadStandardError.connect(self._on_stderr)
#         self.process.finished.connect(self._on_finished)

#     def start(self):
#         python_exec = sys.executable
#         self.process.setProgram(python_exec)
#         self.process.setArguments([self.script_path] + self.args)
#         self.process.setWorkingDirectory(os.path.dirname(self.script_path))
#         self.process.start()
#         self.log_updated.emit(f"[{self.name}] 启动: {python_exec} {self.script_path} {' '.join(self.args)}")

#     def _on_stdout(self):
#         text = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
#         self.log_updated.emit(f"[{self.name}] {text.strip()}")

#     def _on_stderr(self):
#         err = self.process.readAllStandardError().data().decode("utf-8", errors="replace")
#         self.log_updated.emit(f"[{self.name}][STDERR] {err.strip()}")

#     def _on_finished(self):
#         self.log_updated.emit(f"[{self.name}] 执行完成")

# external/external_process_manager.py
# from PySide6.QtCore import QObject, Signal, QProcess
# import os
# import sys

# class ExternalProcessManager(QObject):
#     log_updated = Signal(str)
#     finished = Signal()

#     def __init__(self, script_name="automation/main_stencil_runner.py", parent=None):
#         super().__init__(parent)
#         self.script_path = os.path.abspath(script_name)
#         self.python_exec = sys.executable
#         self.process = None

#     def start_process(self):
#         if not os.path.exists(self.script_path):
#             self.log_updated.emit(f"[ERROR] 脚本不存在: {self.script_path}")
#             return

#         self.process = QProcess(self)
#         self.process.setProgram(self.python_exec)
#         self.process.setArguments([self.script_path])
#         self.process.setWorkingDirectory(os.path.dirname(self.script_path))

#         self.process.readyReadStandardOutput.connect(self.handle_stdout)
#         self.process.readyReadStandardError.connect(self.handle_stderr)
#         self.process.finished.connect(self.handle_finished)

#         self.log_updated.emit(f"[启动] {self.python_exec} {self.script_path}")
#         self.process.start()

#     def handle_stdout(self):
#         output = self.process.readAllStandardOutput().data().decode()
#         self.log_updated.emit(output)

#     def handle_stderr(self):
#         error = self.process.readAllStandardError().data().decode()
#         self.log_updated.emit(f"[STDERR] {error}")

#     def handle_finished(self):
#         self.log_updated.emit("[完成] 外部程序运行完毕")
#         self.finished.emit()

# external/external_process_manager.py
from PySide6.QtCore import QObject, Signal, QProcess
import os
import sys

class ExternalProcessManager(QObject):
    log_updated = Signal(str)
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.python_exec = sys.executable
        self.process = None

    def start_process(self, program_name: str, settings_path: str, script: str):
        script_path = os.path.abspath(os.path.join(script))
        program_path = os.path.abspath(program_name)
        settings_path = os.path.abspath(settings_path)

        if not os.path.exists(program_path):
            self.log_updated.emit(f"[ERROR] 数据文件不存在: {program_path}")
            return
        if not os.path.exists(settings_path):
            self.log_updated.emit(f"[ERROR] 设置文件不存在: {settings_path}")
            return

        self.process = QProcess(self)
        self.process.setProgram(self.python_exec)
        self.process.setArguments([script_path, program_path, settings_path])
        self.process.setWorkingDirectory(os.path.dirname(script_path))

        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.handle_finished)

        self.log_updated.emit(f"[启动] {self.python_exec} {script_path} {program_path} {settings_path}")
        self.process.start()

    def handle_stdout(self):
        output = self.process.readAllStandardOutput().data().decode("gbk", errors="replace")
        self.log_updated.emit(output)

    def handle_stderr(self):
        error = self.process.readAllStandardError().data().decode("gbk", errors="replace")
        self.log_updated.emit(f"[STDERR] {error}")

    def handle_finished(self):
        self.log_updated.emit("[完成] 外部程序运行完毕")
        self.finished.emit()
