import functools
from typing import Tuple
from PySide6.QtCore import QAbstractListModel, QModelIndex, QTime, Signal, Qt
from PySide6.QtWidgets import QLabel, QListView, QVBoxLayout, QWidget, QSizePolicy
from scheduler import Schedule, Todo


def compare_todo_entries(a: Tuple[QTime, Todo], b: Tuple[QTime, Todo]):
    return a[0].msecsSinceStartOfDay() - b[0].msecsSinceStartOfDay()


class ScheduleModel(QAbstractListModel):
    sched: Schedule

    def __init__(self, *args, sched, **kwargs):
        super(ScheduleModel, self).__init__(*args, **kwargs)
        self.sched = sched

    def rowCount(self, parent: QModelIndex) -> int:
        return len(self.sched.todos)

    def data(self, index: QModelIndex, role: Qt.ItemDataRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return
        todo_list = list(self.sched.todos.items())
        todo_list.sort(key=functools.cmp_to_key(compare_todo_entries))
        todo = todo_list[index.row()]
        return f"{todo[0].toString()} - {todo[1].title}"


class ViewTab(QWidget):
    qlist: QListView
    model: ScheduleModel
    schedule_changed = Signal(Schedule)

    def __init__(self, sched: Schedule, parent):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.model = ScheduleModel(sched=sched)

        self.schedule_changed.connect(self.update_view)

        self.qlist = QListView(self)
        self.qlist.setModel(self.model)
        layout.addWidget(self.qlist)

    def update_view(self, new_sched: Schedule):
        self.model.beginResetModel()
        self.model.sched = new_sched
        self.model.endResetModel()
        self.qlist.repaint()
