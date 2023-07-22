from os import path, makedirs
import sys
from PySide6.QtCore import QStandardPaths, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QSystemTrayIcon,
    QTabWidget,
)
from camel import Camel
from EditTab import EditTab, SchedulerConfig
from ViewTab import ViewTab
from scheduler import Schedule, todo_types
from pathlib import Path

if __name__ != "__main__":
    sys.exit(1)


app = QApplication(sys.argv)
QApplication.setApplicationName("FuzzyNotifs")
app.setQuitOnLastWindowClosed(False)
app_icon = QIcon("icon.png")


def make_tray_icon():
    tray_icon = QSystemTrayIcon(app)
    tray_icon.setIcon(app_icon)
    tray_icon.show()
    tray_menu = QMenu()
    quit_action = QAction("Quit", tray_menu)
    quit_action.triggered.connect(lambda: sys.exit(0))
    tray_menu.addAction(quit_action)
    tray_icon.setContextMenu(tray_menu)


def load_config():
    file_path = QStandardPaths.locate(
        QStandardPaths.StandardLocation.AppDataLocation,
        "scheduler_config.yaml",
    )
    if file_path == "":
        return SchedulerConfig.make_default_config()
    with open(file_path, "r") as file:
        return Camel([todo_types]).load(file.read())


def save_config(config: SchedulerConfig):
    writable_path = Path(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    )
    makedirs(writable_path, exist_ok=True)
    file_path = writable_path / "scheduler_config.yaml"
    with open(file_path, "w") as file:
        file.write(Camel([todo_types]).dump(config))


make_tray_icon()

config = load_config()
config.update_morning()
save_config(config)


class MainWindow(QMainWindow):
    tray_icon: QSystemTrayIcon
    app_icon: QIcon
    config: SchedulerConfig
    config_changed = Signal()

    def __init__(self, config: SchedulerConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Fuzzy notifications!")
        self.setWindowIcon(app_icon)
        self.make_tabs()
        self.config_changed.connect(lambda: save_config(self.config))

    def make_tabs(self):
        tab_widget = QTabWidget(self)
        view_tab = ViewTab(self)
        tab_widget.addTab(view_tab, "View")
        edit_tab = EditTab(self.config, self)
        edit_tab.config_changed.connect(self.config_changed)
        tab_widget.addTab(edit_tab, "Edit")
        self.setCentralWidget(tab_widget)


if "--silent" not in app.arguments():
    window = MainWindow(config)
    window.show()
app.exec()
