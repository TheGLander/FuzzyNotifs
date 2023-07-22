from typing import Any, List
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QTableView,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)
from scheduler import Todo, TodoBias


class BiasDelegate(QStyledItemDelegate):
    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        combo_box = QComboBox(parent)
        for bias in TodoBias:
            combo_box.addItem(str(bias), bias)
        return combo_box

    def setEditorData(self, editor: QComboBox, index: QModelIndex) -> None:
        model: TodoModel = index.model()  # type: ignore
        editor.setCurrentText(str(model.todos[index.row()].bias))

    def setModelData(
        self, editor: QComboBox, model: QAbstractTableModel, index: QModelIndex
    ) -> None:
        model.setData(index, editor.currentData(), Qt.ItemDataRole.EditRole)


class TodoModel(QAbstractTableModel):
    todos: List[Todo]

    def __init__(self, *args, todos, **kwargs):
        super(TodoModel, self).__init__(*args, **kwargs)
        self.todos = todos

    def data(self, index: QModelIndex, role: Qt.ItemDataRole):
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            todo = self.todos[index.row()]
            attribute = getattr(todo, todo.column_order[index.column()])
            if type(attribute) is int:
                return attribute
            return str(attribute)

    def rowCount(self, _index):
        return len(self.todos)

    def columnCount(self, _index):
        return len(Todo.column_names)

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
        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsEditable
            | Qt.ItemFlag.ItemIsSelectable
        )

    def new_todo(self):
        self.beginInsertRows(QModelIndex(), len(self.todos), len(self.todos))
        self.todos.append(Todo(title="Take a nap", times_per_day=5, bias=TodoBias.NONE))
        self.endInsertRows()

    def remove_todo(self, rows: List[int]):
        rows.sort(reverse=True)
        for row_n in rows:
            self.beginRemoveRows(QModelIndex(), row_n, row_n)
            self.todos.pop(row_n)
            self.endRemoveRows()

    @staticmethod
    def setup_table(table: QTableView):
        table.setItemDelegateForColumn(Todo.column_order.index("bias"), BiasDelegate())


mock_todos = [Todo(title="Work more", bias=TodoBias.MORNING_ONLY, times_per_day=3)]


class EditTab(QWidget):
    table: QTableView
    model: TodoModel

    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.model = TodoModel(todos=mock_todos)
        self.table = QTableView(self)
        self.model.setup_table(self.table)
        self.table.setModel(self.model)
        layout.addWidget(self.table)

        misc_options = QWidget(self)
        misc_layout = QHBoxLayout(misc_options)
        misc_options.setLayout(misc_layout)
        layout.addWidget(misc_options)

        todo_cooldown_input = QTimeEdit(misc_options)
        todo_cooldown_input.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum
        )
        tc_label = QLabel("Todo cooldown (h:m)", misc_options)
        tc_label.setBuddy(todo_cooldown_input)
        misc_layout.addWidget(todo_cooldown_input)
        misc_layout.addWidget(tc_label)

        remove_todo = QPushButton("-", misc_options)
        remove_todo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        remove_todo.pressed.connect(self.remove_todo)
        misc_layout.addWidget(remove_todo)

        add_todo = QPushButton("+", misc_options)
        add_todo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        add_todo.pressed.connect(self.model.new_todo)
        misc_layout.addWidget(add_todo)

    def remove_todo(self):
        self.model.remove_todo([index.row() for index in self.table.selectedIndexes()])
