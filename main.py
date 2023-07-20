import sys
from typing import Any, List
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QSpinBox,
    QSystemTrayIcon,
    QTabWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)


class ViewTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(QLabel("Poop appointment in 5 minutes", self))


class Todo:
    title: str
    times_per_day: int
    column_order = ["title", "times_per_day"]
    column_names = ["Title", "# per day"]

    def __init__(self, title: str, times_per_day: int) -> None:
        self.title = title
        self.times_per_day = times_per_day


class TodoModel(QAbstractTableModel):
    todos: List[Todo]

    def __init__(self, *args, todos, **kwargs):
        super(TodoModel, self).__init__(*args, **kwargs)
        self.todos = todos

    def data(self, index: QModelIndex, role: Qt.ItemDataRole):
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            todo = self.todos[index.row()]
            return getattr(todo, todo.column_order[index.column()])

    def rowCount(self, _index):
        return len(self.todos)

    def columnCount(self, _index):
        return 2

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ):
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return Todo.column_names[section]

    def setData(self, index: QModelIndex, value: Any, role: Qt.ItemDataRole) -> bool:
        if role != Qt.ItemDataRole.EditRole:
            return False
        todo = self.todos[index.row()]
        setattr(todo, todo.column_order[index.column()], value)
        return True

    def flags(self, _index: QModelIndex) -> Qt.ItemFlag:
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable


todos = [Todo("Work more", 5), Todo("Work less", 5)]


class EditTab(QWidget):
    table: QTableView
    model: TodoModel

    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.model = TodoModel(todos=todos)
        self.table = QTableView(self)
        self.table.setModel(self.model)
        layout.addWidget(self.table)

        misc_options = QWidget(self)
        misc_layout = QHBoxLayout(misc_options)
        misc_options.setLayout(misc_layout)
        layout.addWidget(misc_options)

        task_period_input = QSpinBox(misc_options)
        task_period_input.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum
        )
        tp_label = QLabel("Minimum task interval (m)", misc_options)
        tp_label.setBuddy(task_period_input)
        misc_layout.addWidget(task_period_input)
        misc_layout.addWidget(tp_label)


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
