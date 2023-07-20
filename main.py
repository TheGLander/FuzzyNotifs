import sys
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QSystemTrayIcon,
    QTabWidget,
)
from EditTab import EditTab
from ViewTab import ViewTab


class MainWindow(QMainWindow):
    tray_icon: QSystemTrayIcon
    app_icon: QIcon

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fuzzy notifications!")
        self.app_icon = QIcon("icon.png")
        self.setWindowIcon(self.app_icon)
        self.make_tray_icon()
        self.make_tabs()

    def make_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.app_icon)
        self.tray_icon.show()
        tray_menu = QMenu(self)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(lambda: sys.exit(0))
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)

    def make_tabs(self):
        tab_widget = QTabWidget(self)
        tab_widget.addTab(ViewTab(self), "View")
        tab_widget.addTab(EditTab(self), "Edit")
        self.setCentralWidget(tab_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    window.show()
    app.exec()
