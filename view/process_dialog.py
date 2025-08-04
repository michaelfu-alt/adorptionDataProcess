from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QPushButton, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Signal, Qt

class ProcessDialog(QDialog):
    pause_clicked = Signal()
    continue_clicked = Signal()
    end_clicked = Signal()

    def __init__(self, total_files, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importing Files…")
        self.setModal(True)
        self.setFixedSize(400, 150)

        self.label = QLabel("Starting…")
        self.progress = QProgressBar()
        self.progress.setMaximum(total_files)
        self.progress.setValue(0)

        self.btn_pause = QPushButton("Pause")
        self.btn_continue = QPushButton("Continue")
        self.btn_end = QPushButton("End")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_continue)
        btn_layout.addWidget(self.btn_pause)
        btn_layout.addWidget(self.btn_end)

        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel("Importing files:"))
        main_layout.addWidget(self.label)
        main_layout.addWidget(self.progress)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

        self.btn_pause.clicked.connect(self.pause_clicked.emit)
        self.btn_continue.clicked.connect(self.continue_clicked.emit)
        self.btn_end.clicked.connect(self.end_clicked.emit)

    def update_status(self, current_index, total, filename):
        self.label.setText(f"{current_index}/{total}: {filename}")
        self.progress.setValue(current_index)
        self.repaint()