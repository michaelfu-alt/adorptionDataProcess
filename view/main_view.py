# view/main_view.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from .left_panel import LeftPanel
from .right_panel import RightPanel

class MainView(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Adsorption Data Wizard")
        self.resize(1000, 600)
        # 布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 1, 0, 1)
        self.left_panel = LeftPanel(controller, self)
        self.right_panel = RightPanel(controller, self)
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        layout.addWidget(self.left_panel, 1)   # 左侧
        layout.addWidget(self.right_panel, 3)  # 右侧
        
        self.setLayout(layout)
    
    def set_status(self, msg):
        self.status_label.setText(msg)