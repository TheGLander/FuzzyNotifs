from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QTabWidget
from scheduler import SchedulerConfig
from ViewTab import ViewTab
from EditTab import EditTab


class MainWindow(QMainWindow):
    config: SchedulerConfig
    config_changed = Signal()

    def __init__(self, app_icon: QIcon, config: SchedulerConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Fuzzy notifications!")
        self.setWindowIcon(app_icon)
        self.make_tabs()

    def make_tabs(self):
        tab_widget = QTabWidget(self)
        view_tab = ViewTab(self)
        tab_widget.addTab(view_tab, "View")
        edit_tab = EditTab(self.config, self)
        edit_tab.config_changed.connect(self.config_changed)
        tab_widget.addTab(edit_tab, "Edit")
        self.setCentralWidget(tab_widget)
