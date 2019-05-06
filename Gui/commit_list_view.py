from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QDropEvent
from PyQt5.QtWidgets import QListView, QAbstractItemView


class CommitListView(QListView):
    dropped = pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self.top_conflict = None
        self.bottom_conflict = None
        self.current_index = None

    def get_row(self, event):
        if self.current_index is None:
            return None
        row = self.indexAt(event.pos()).row()
        indicator_position = self.dropIndicatorPosition()
        if indicator_position == QAbstractItemView.AboveItem:
            pass
        elif indicator_position == QAbstractItemView.BelowItem:
            row += 1
        elif indicator_position == QAbstractItemView.OnViewport:
            return -1
        else:
            return self.current_index
        if row > self.current_index:
            row -= 1
        return row

    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)
        drop_row = self.get_row(event)

        if drop_row is None:
            event.ignore()
            return

        if drop_row >= 0 and (self.top_conflict is None or drop_row >= self.top_conflict) and (
                self.bottom_conflict is None or drop_row <= self.bottom_conflict):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        # https://stackoverflow.com/a/38239804/6130671
        drop_row = self.get_row(event)
        self.dropped.emit(drop_row)
