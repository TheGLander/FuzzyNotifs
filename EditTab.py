from typing import Any, List
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)
from scheduler import Todo


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


mock_todos = [Todo("Work more", 5), Todo("Work less", 5)]


class EditTab(QWidget):
    table: QTableView
    model: TodoModel

    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.model = TodoModel(todos=mock_todos)
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
