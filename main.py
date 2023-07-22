import asyncio
from os import makedirs
import sys
from PySide6.QtCore import QResource, QStandardPaths, QTime, QUrl, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QSystemTrayIcon,
)
from PySide6.QtMultimedia import QMediaDevices, QSoundEffect
from camel import Camel
from scheduler import Schedule, SchedulerConfig, Todo, todo_types
from pathlib import Path
from MainWindow import MainWindow

if __name__ != "__main__":
    sys.exit(1)


QApplication.setApplicationName("FuzzyNotifs")


class FuzzyApplication(QApplication):
    app_icon: QIcon
    tray_icon: QSystemTrayIcon
    config_changed = Signal()
    scheduler_changed = Signal(Schedule)
    config: SchedulerConfig
    window: MainWindow
    schedule: Schedule

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_icon = QIcon("icon.png")
        self.setQuitOnLastWindowClosed(False)
        self.make_tray_icon()

        self.load_config()
        self.config.update_morning()
        self.update_config()
        if "--silent" not in self.arguments():
            self.make_main_window()

    def make_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.app_icon)
        self.tray_icon.show()
        tray_menu = QMenu()
        quit_action = QAction("Quit", tray_menu)
        quit_action.triggered.connect(lambda: sys.exit(0))
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)

    def make_main_window(self):
        self.window = MainWindow(self.app_icon, self.config, self.schedule)
        self.window.config_changed.connect(self.update_config)
        self.scheduler_changed.connect(self.window.schedule_changed)
        self.window.show()

    def load_config(self):
        file_path = QStandardPaths.locate(
            QStandardPaths.StandardLocation.AppDataLocation,
            "scheduler_config.yaml",
        )
        if file_path == "":
            return SchedulerConfig.make_default_config()
        with open(file_path, "r") as file:
            self.config = Camel([todo_types]).load(file.read())

    def save_config(self):
        writable_path = Path(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.AppDataLocation
            )
        )
        makedirs(writable_path, exist_ok=True)
        file_path = writable_path / "scheduler_config.yaml"
        with open(file_path, "w") as file:
            file.write(Camel([todo_types]).dump(self.config))

    def update_config(self):
        self.save_config()
        if hasattr(self, "schedule"):
            self.schedule.cancel_queued()
        self.schedule = Schedule(self.config)
        self.scheduler_changed.emit(self.schedule)

        self.schedule.queue_todo(self.todo_sched_cycle)

    def todo_sched_cycle(self, todo: Todo, time: QTime):
        self.tray_icon.showMessage(
            todo.title,
            f"New fuzzy notif just dropped ({time.toString()})",
            self.app_icon,
        )
        sfx = QSoundEffect(self)
        # Why does this need to be set??
        sfx.setAudioDevice(QMediaDevices.defaultAudioOutput())
        sfx.setSource(QUrl.fromLocalFile("new todo.wav"))
        sfx.setVolume(0.25)
        sfx.play()

        self.schedule.queue_todo(self.todo_sched_cycle)


app = FuzzyApplication(sys.argv)
app.exec()
