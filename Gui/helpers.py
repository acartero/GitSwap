import platform
from PyQt5.QtGui import QStandardItem, QFont, QColor
from PyQt5.QtWidgets import QStyledItemDelegate

if platform.system() == 'Windows':
    FONT_DIFF = 0
else:
    FONT_DIFF = 2


class ItemDelegate(QStyledItemDelegate):
    def __init__(self, window, parent_list):
        super().__init__(parent_list)
        self.window = window

    def displayText(self, value, locale):
        if isinstance(value, str):
            index = int(value)
            top_index = self.window.mainwidget.commitList.top_conflict
            bottom_index = self.window.mainwidget.commitList.bottom_conflict
            if (top_index is None or index > top_index) and (bottom_index is None or index < bottom_index):
                return self.window.history[index].message
            elif (top_index is not None and index == top_index) or (bottom_index is not None and index == bottom_index):
                return "/!\\ " + self.window.history[index].message
            else:
                return "? " + self.window.history[index].message
        return value


def append_middle(model, text):
    item = QStandardItem()
    text = str(text) if text is not None else ""
    item.setText(text)
    item.setDropEnabled(False)
    item.setEditable(False)
    font: QFont = item.font()
    font.setFamily("Courier New")
    font.setPointSize(font.pointSize() - FONT_DIFF)
    item.setFont(font)
    if text.endswith("!") or text.endswith("!>"):
        item.setBackground(QColor(255, 255, 0, 127))
    if text == "":
        item.setBackground(QColor(0, 0, 0, 47))

    model.appendRow(item)


def append(model, text):
    item = QStandardItem()
    text = str(text) if text is not None else ""
    item.setText(text)
    item.setDropEnabled(False)
    item.setEditable(False)
    font: QFont = item.font()
    font.setFamily("Courier New")
    font.setPointSize(font.pointSize() - FONT_DIFF)
    item.setFont(font)
    if text.startswith("+"):
        item.setBackground(QColor(0, 255, 0, 127))
    if text.startswith("-"):
        item.setBackground(QColor(255, 0, 0, 127))
    if text == "":
        item.setBackground(QColor(0, 0, 0, 47))

    model.appendRow(item)
