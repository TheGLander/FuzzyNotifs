from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ViewTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(QLabel("Poop appointment in 5 minutes", self))
