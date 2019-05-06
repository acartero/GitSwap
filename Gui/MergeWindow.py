from typing import List

from PyQt5 import QtCore
from PyQt5.QtCore import QItemSelectionModel, QModelIndex, QItemSelection, Qt
from PyQt5.QtGui import QCloseEvent, QStandardItemModel, QStandardItem, QColor
from PyQt5.QtWidgets import QMainWindow, QListView, QAbstractItemView

from Core.MergeDiff import CommitMerge, MergeFileDiff, MergeLine
from Core.Diff import GitDiff
from Gui.merger import Ui_Merger
from Gui.helpers import append_middle, append


def keyPressEvent(event):
    if event.key() == QtCore.Qt.Key_S:
        Merger.instance.on_key_swap()


class Merger(QMainWindow):
    instance = None

    def __init__(self, parent, main_commit_on_left):
        Merger.instance = self
        super().__init__(parent)
        self.commit_merge: CommitMerge = None
        self.main_widget = None

        self.main_widget = Ui_Merger()
        self.main_widget.setupUi(self)
        self.configure()
        self.current_file_name: bytes = None
        self.main_commit_on_left = main_commit_on_left
        self.setWindowModality(Qt.WindowModal)

    def configure(self):
        def connect_scrollbars(first_widget, second_widget):
            first_widget.verticalScrollBar().valueChanged.connect(
                second_widget.verticalScrollBar().setValue)
            second_widget.verticalScrollBar().valueChanged.connect(
                first_widget.verticalScrollBar().setValue)

        connect_scrollbars(self.main_widget.leftIndexes, self.main_widget.leftCommitWidget)
        connect_scrollbars(self.main_widget.leftCommitWidget, self.main_widget.middleIndexes)
        connect_scrollbars(self.main_widget.middleIndexes, self.main_widget.rightIndexes)
        connect_scrollbars(self.main_widget.rightIndexes, self.main_widget.rightCommitWidget)

        self.main_widget.leftIndexes.setSelectionMode(QAbstractItemView.NoSelection)
        self.main_widget.middleIndexes.setSelectionMode(QAbstractItemView.NoSelection)
        self.main_widget.rightIndexes.setSelectionMode(QAbstractItemView.NoSelection)

        self.main_widget.leftCommitWidget: QListView
        self.main_widget.rightCommitWidget: QListView
        self.main_widget.leftCommitWidget.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.main_widget.rightCommitWidget.setSelectionMode(QAbstractItemView.ContiguousSelection)

        self.main_widget.leftCommitWidget.horizontalScrollBar().valueChanged.connect(
            self.main_widget.rightCommitWidget.horizontalScrollBar().setValue)
        self.main_widget.rightCommitWidget.horizontalScrollBar().valueChanged.connect(
            self.main_widget.leftCommitWidget.horizontalScrollBar().setValue)

        self.main_widget.swapButton.pressed.connect(self.on_swap_pressed)
        self.main_widget.resetButton.pressed.connect(self.on_reset_pressed)
        self.main_widget.moveLeftButton.pressed.connect(self.on_move_left_pressed)
        self.main_widget.moveRightButton.pressed.connect(self.on_move_right_pressed)
        self.main_widget.applyButton.pressed.connect(self.on_apply_pressed)

        self.main_widget.leftCommitWidget.keyPressEvent = keyPressEvent
        self.main_widget.rightCommitWidget.keyPressEvent = keyPressEvent

    def on_key_swap(self):
        left_selection_model: QItemSelectionModel = self.main_widget.leftCommitWidget.selectionModel()
        selection: List[QModelIndex] = left_selection_model.selectedRows()
        for line in selection:
            self.current_merge().move(line.row())
        self.display_file(self.current_file_name)

    def current_merge(self):
        return self.commit_merge.files[self.current_file_name]

    def on_swap_pressed(self):
        self.commit_merge.swap_all()
        self.display_file(self.current_file_name)

        left_message = self.main_widget.leftMessage.toPlainText()
        right_message = self.main_widget.rightMessage.toPlainText()
        self.main_widget.leftMessage.setText(str(right_message))
        self.main_widget.rightMessage.setText(str(left_message))

    def on_reset_pressed(self):
        self.commit_merge.reset()
        self.display_file(self.current_file_name)

        self.main_widget.leftMessage.setText(str(self.commit_merge.left_git_diff.message))
        self.main_widget.rightMessage.setText(str(self.commit_merge.right_git_diff.message))

    def on_move_left_pressed(self):
        if self.current_file_name is not None:
            self.current_merge().move_left()
        self.display_file(self.current_file_name)

    def on_move_right_pressed(self):
        if self.current_file_name is not None:
            self.commit_merge.files[self.current_file_name].move_right()
        self.display_file(self.current_file_name)

    def on_apply_pressed(self):
        self.commit_merge.left_git_diff.message = self.main_widget.leftMessage.toPlainText()
        self.commit_merge.right_git_diff.message = self.main_widget.rightMessage.toPlainText()
        self.parent().on_merger_closed(self.commit_merge, self.main_commit_on_left)
        self.close()

    def closeEvent(self, event: QCloseEvent):
        self.parent().on_merger_closed()
        event.accept()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(e)

    def load(self, left_commit: GitDiff, right_commit: GitDiff):

        self.commit_merge = CommitMerge(left_commit, right_commit)

        self.main_widget.leftMessage.setText(left_commit.message)
        self.main_widget.rightMessage.setText(right_commit.message)

        self.main_widget: Ui_Merger
        file_list = self.main_widget.fileListView
        file_model = QStandardItemModel(file_list)

        for file_name in self.commit_merge.files:
            item = QStandardItem()
            if self.commit_merge.files[file_name].conflicts:
                item.setText((file_name + b"!").decode("utf8"))
                item.setBackground(QColor(255, 255, 0, 127))
            else:
                item.setText(file_name.decode("utf8"))
            item.setDropEnabled(False)
            file_model.appendRow(item)

        file_list.setModel(file_model)
        file_selection_model: QItemSelectionModel = file_list.selectionModel()  # Weird Bug in PyQt ?
        file_selection_model.selectionChanged.connect(self.on_file_selection_changed)
        file_list.show()
        file_selection_model.select(QModelIndex(file_list.model().index(0, 0)), QItemSelectionModel.ClearAndSelect)

    def on_file_selection_changed(self):
        main_widget: Ui_Merger = self.main_widget
        selection_model: QItemSelectionModel = main_widget.fileListView.selectionModel()
        rows = selection_model.selectedRows()

        if len(rows) == 1:
            model_index: QModelIndex = rows[0]
            self.display_file(model_index.data().strip("!").encode("utf8"))
        else:
            # Reset item model
            main_widget.leftCommitWidget.setModel(QStandardItemModel(main_widget.leftCommitWidget))
            main_widget.rightCommitWidget.setModel(QStandardItemModel(main_widget.rightCommitWidget))
            self.current_file_name = None

    def setup_sync(self):
        left_selection_model: QItemSelectionModel = self.main_widget.leftCommitWidget.selectionModel()
        left_selection_model.selectionChanged.connect(self.on_left_selection)
        right_selection_model: QItemSelectionModel = self.main_widget.rightCommitWidget.selectionModel()
        right_selection_model.selectionChanged.connect(self.on_right_selection)

    def on_left_selection(self):
        self.synchronize_selection(self.main_widget.leftCommitWidget, self.main_widget.rightCommitWidget)

    def on_right_selection(self):
        self.synchronize_selection(self.main_widget.rightCommitWidget, self.main_widget.leftCommitWidget)

    def synchronize_selection(self, from_list: QListView, to_list: QListView):
        source_selection_model: QItemSelectionModel = from_list.selectionModel()
        destination_selection_model: QItemSelectionModel = to_list.selectionModel()
        rows = source_selection_model.selectedRows()
        if len(rows) > 0:
            idx = [r.row() for r in rows]
            min_idx, max_idx = min(idx), max(idx)
            top_index = QModelIndex(to_list.model().index(min_idx, 0))
            bottom_index = QModelIndex(to_list.model().index(max_idx, 0))
            destination_selection_model.select(QItemSelection(top_index, bottom_index),
                                               QItemSelectionModel.ClearAndSelect)

    def display_file(self, file):
        self.current_file_name = file
        merged_file_diff: MergeFileDiff = self.commit_merge.files[file]
        self.main_widget: Ui_Merger = self.main_widget

        left_idx_list = self.main_widget.leftIndexes
        left_idx_model = QStandardItemModel(left_idx_list)
        left_list = self.main_widget.leftCommitWidget
        left_model = QStandardItemModel(left_list)
        middle_list = self.main_widget.middleIndexes
        middle_idx_model = QStandardItemModel(middle_list)
        right_idx_list = self.main_widget.rightIndexes
        right_idx_model = QStandardItemModel(right_idx_list)
        right_list = self.main_widget.rightCommitWidget
        right_model = QStandardItemModel(right_list)

        for line in merged_file_diff.merge_lines:
            append(left_idx_model, line.left_index)
            append(left_model, line.dump_as_left()[2])
            middle_text = str(line.middle_index) if line.middle_index is not None else ""

            if line.conflicts:
                middle_text += "!"
            append_middle(middle_idx_model, middle_text)

            append(right_idx_model, line.right_index)
            append(right_model, line.dump_as_right()[2])

        left_idx_list.setModel(left_idx_model)
        left_list.setModel(left_model)
        middle_list.setModel(middle_idx_model)
        right_idx_list.setModel(right_idx_model)
        right_list.setModel(right_model)

        self.main_widget.leftIndexes.setMinimumWidth(self.main_widget.leftIndexes.sizeHintForColumn(0) + 4)
        self.main_widget.leftIndexes.setMaximumWidth(self.main_widget.leftIndexes.sizeHintForColumn(0) + 4)
        self.main_widget.leftIndexes.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.main_widget.middleIndexes.setMinimumWidth(self.main_widget.middleIndexes.sizeHintForColumn(0) + 4)
        self.main_widget.middleIndexes.setMaximumWidth(self.main_widget.middleIndexes.sizeHintForColumn(0) + 4)
        self.main_widget.middleIndexes.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.main_widget.rightIndexes.setMinimumWidth(self.main_widget.rightIndexes.sizeHintForColumn(0) + 4)
        self.main_widget.rightIndexes.setMaximumWidth(self.main_widget.rightIndexes.sizeHintForColumn(0) + 4)
        self.main_widget.rightIndexes.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setup_sync()
