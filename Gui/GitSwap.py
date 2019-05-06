#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import signal
import sys
from collections import OrderedDict
from typing import List

from PyQt5.QtCore import QItemSelectionModel, QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QAbstractItemView, QStyledItemDelegate, \
    QInputDialog, QErrorMessage, QMessageBox

from Core.GitCommands import Git
from Core.MergeDiff import CommitMerge
from Gui.MergeWindow import Merger
from Gui.helpers import ItemDelegate, append
from Gui.main_window import Ui_MainWindow
from Core.DiffParser import parse_git_diff, GitDiff


class FileDelegate(QStyledItemDelegate):
    def __init__(self, window, parent_list):
        super().__init__(parent_list)
        self.window = window

    def displayText(self, value, locale):
        if isinstance(value, str):
            return self.window.commit_merge.files[value][0]
        return value


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.mainwidget = Ui_MainWindow(self)
        self.mainwidget.setupUi(self)
        self.show()
        self.mainwidget.pathButton.clicked.connect(self.on_path_clicked)
        self.mainwidget.pathLabel.setText(os.getcwd())
        self.history: List[GitDiff] = []
        self.hash_to_diff = OrderedDict
        self.current_git_diff = None
        self.current_git_diff_index = None
        self.current_conflict_row = None
        self.merge_window = None
        self.current_modif_index = None
        self.root_commit = None

        signal.signal(signal.SIGINT, self.sigint_handler)
        self.load_cwd()
        self.configure_widgets()

    def on_commit_dropped(self, row):
        current_diff = self.current_git_diff
        conflict = False

        if row > self.current_git_diff_index:
            for i in range(self.current_git_diff_index, row):
                previous_diff: GitDiff = self.history[i + 1]
                previous_files = set(previous_diff.file_diffs.keys())
                current_files = set(current_diff.file_diffs.keys())

                if len(previous_files.intersection(current_files)) == 0:
                    continue

                merge_diff = CommitMerge(previous_diff, current_diff)

                if merge_diff.conflicts:
                    conflict = True
                    break
                else:
                    merge_diff.swap_all()
                    new_left, new_right = merge_diff.dump()
                    current_diff = parse_git_diff(new_left.split(b"\n"), current_diff.hash, current_diff.message)
                    swapped_diff = parse_git_diff(new_right.split(b"\n"), previous_diff.hash, previous_diff.message)
                    self.history.pop(i + 1)
                    self.history.insert(i + 1, swapped_diff)

        if row < self.current_git_diff_index:
            for i in range(self.current_git_diff_index, row, -1):
                next_diff: GitDiff = self.history[i - 1]
                next_files = set(next_diff.file_diffs.keys())
                current_files = set(current_diff.file_diffs.keys())

                if len(next_files.intersection(current_files)) == 0:
                    continue

                merge_diff = CommitMerge(current_diff, next_diff)

                if merge_diff.conflicts:
                    conflict = True
                    break
                else:
                    merge_diff.swap_all()
                    new_left, new_right = merge_diff.dump()
                    current_diff = parse_git_diff(new_right.split("\n"), current_diff.hash, current_diff.message)
                    swapped_diff = parse_git_diff(new_left.split("\n"), next_diff.hash, next_diff.message)
                    self.history.pop(i - 1)
                    self.history.insert(i - 1, swapped_diff)

        if conflict:
            if row < self.current_git_diff_index:
                self.merge_window = Merger(self, main_commit_on_left=True)
                self.merge_window.load(current_diff, self.history[row])
                self.merge_window.show()
                self.current_conflict_row = row
                row += 1
            else:
                self.merge_window = Merger(self, main_commit_on_left=False)
                self.merge_window.load(self.history[row], current_diff)
                self.merge_window.show()
                self.current_conflict_row = row - 1
                row -= 1
        else:
            self.current_conflict_row = None

        self.history.pop(self.current_git_diff_index)
        self.history.insert(row, current_diff)
        self.current_git_diff_index = row
        self.current_git_diff = current_diff

        self.refresh(row)

    def configure_widgets(self):
        commit_list = self.mainwidget.commitList
        commit_list.setDragDropMode(QAbstractItemView.InternalMove)
        commit_list.setSelectionMode(QAbstractItemView.ContiguousSelection)

        self.mainwidget.commitList.dropped.connect(self.on_commit_dropped)
        self.mainwidget.splitButton.pressed.connect(self.on_split_button_pressed)
        self.mainwidget.mergeButton.pressed.connect(self.on_merge_button_pressed)
        self.mainwidget.commitButton.pressed.connect(self.on_commit_button_pressed)

    def on_commit_button_pressed(self):

        if self.current_modif_index is None:
            return
        if self.current_modif_index + 1 < len(self.history):
            commit = self.history[self.current_modif_index + 1].hash
        else:
            commit = self.root_commit

        # tag = "GitSwap_backup_0"
        # i = 0
        # while not Git.tag(tag):
        #     i += 1
        #     tag = "GitSwap_backup_" + str(i)
        #     if i > 2:
        #         msg = QMessageBox(self)
        #         msg.setWindowTitle("GitSwap - Commit")
        #         msg.setIcon(QMessageBox.Critical)
        #         msg.setText("Impossible to place a backup tag:\nCommit canceled")
        #         msg.show()
        #         return

        Git.stash()
        Git.reset_to(commit)
        for i in range(self.current_modif_index, -1, -1):
            error = False
            for file_name in self.history[i].file_diffs:
                diff = self.history[i].file_diffs[file_name].to_bytes()
                if not Git.apply_and_stage(diff):
                    print(
                        "Error with file '{}' while applying '{}'".format(file_name, self.history[i].message))
                    error = True

            if error:
                return

            if not Git.commit(self.history[i].message):
                print("Error while committing {}".format(self.history[i].message))
                return

        Git.stash_pop()
        Git.clean_patch()
        self.current_modif_index = None

    def on_merge_button_pressed(self):
        selection_model: QItemSelectionModel = self.mainwidget.commitList.selectionModel()
        indexes = [int(row.data()) for row in selection_model.selectedRows()]
        indexes.sort()
        indexes_count = len(indexes)
        right = indexes.pop(0)
        res = self.history[right]
        while len(indexes) > 0:
            left = indexes.pop(0)
            merge = CommitMerge(self.history[left], res)
            merge.move_left()
            res = parse_git_diff(merge.dump()[0].split(b"\n"), None, merge.right_git_diff.message)

        start = len(self.history) - indexes_count + 1
        self.mainwidget.commitList.model().removeRows(start, indexes_count - 1)

        for i in range(0, indexes_count - 1):
            self.history.pop(right)
        self.history[right] = res

        self.refresh(right)

    def on_split_button_pressed(self):
        if self.current_git_diff is not None:
            item = QStandardItem()
            item.setText(str(len(self.history)))
            item.setDropEnabled(False)
            self.mainwidget.commitList.model().appendRow(item)
            self.history.insert(self.current_git_diff_index, GitDiff([], None, "Splitting ..."))
            empty_commit = GitDiff([], None, self.current_git_diff.message)
            self.merge_window = Merger(self, main_commit_on_left=True)
            self.merge_window.load(self.current_git_diff, empty_commit)
            self.current_conflict_row = self.current_git_diff_index
            self.merge_window.show()

    def on_merger_closed(self, commitMerge: CommitMerge = None, main_commit_on_left=None):
        if commitMerge is not None:
            new_left, new_right = commitMerge.dump()
            has_left = new_left != b""
            has_right = new_right != b""
            if has_left:
                new_left_commit = parse_git_diff(new_left.split(b"\n"), None, commitMerge.left_git_diff.message)
            if has_right:
                new_right_commit = parse_git_diff(new_right.split(b"\n"), None, commitMerge.right_git_diff.message)
            self.history.pop(self.current_conflict_row)
            self.history.pop(self.current_conflict_row)

            if has_left:
                self.history.insert(self.current_conflict_row, new_left_commit)
            else:
                model = self.mainwidget.commitList.model()
                model.removeRow(model.rowCount() - 1)
            if has_right:
                self.history.insert(self.current_conflict_row, new_right_commit)
            else:
                model: QStandardItemModel = self.mainwidget.commitList.model()
                model.removeRow(model.rowCount() - 1)

            if main_commit_on_left:
                self.refresh(self.current_conflict_row + 1, self.current_conflict_row)
            else:
                self.refresh(self.current_conflict_row + 1, self.current_conflict_row + 1)

    def display_file_diff(self, data):
        test = self.current_git_diff.file_diffs[data.encode("utf8")]
        diff_view = self.mainwidget.diffView
        diff_model = QStandardItemModel(diff_view)

        for hunk in test.hunks:
            item = QStandardItem()
            item.setEditable(False)
            item.setText(str(hunk.stats))
            diff_model.appendRow(item)
            for line in hunk.lines:
                append(diff_model, str(line))

        diff_view.setModel(diff_model)
        diff_view.show()

    def on_file_selection_changed(self, selected, deselected):
        selection_model: QItemSelectionModel = self.mainwidget.fileView.selectionModel()
        rows = selection_model.selectedRows()
        if len(rows) == 1:
            model_index: QModelIndex = rows[0]
            self.display_file_diff(model_index.data())
        else:
            self.mainwidget.fileView.setModel(QStandardItemModel(self.mainwidget.fileView))
            self.mainwidget.diffView.setModel(QStandardItemModel(self.mainwidget.diffView))

    def display_git_diff(self):
        file_view = self.mainwidget.fileView
        file_model = QStandardItemModel(file_view)

        for file_diff in self.current_git_diff.file_diffs:
            item = QStandardItem()
            item.setEditable(False)
            item.setText(file_diff.decode("utf8"))
            file_model.appendRow(item)

        file_view.setModel(file_model)
        file_model = file_view.selectionModel()  # Weird Bug in PyQt ?
        file_model.selectionChanged.connect(self.on_file_selection_changed)
        # file_view.show()

    def reset_conflict_indexes(self):
        self.mainwidget.commitList.top_conflict = None
        self.mainwidget.commitList.bottom_conflict = None
        self.mainwidget.commitList.current_index = None

    def on_commit_selection_changed(self, selected, deselected):
        # selected: QItemSelection = selected
        # deselected: QItemSelection = deselected
        selection_model: QItemSelectionModel = self.mainwidget.commitList.selectionModel()
        rows = selection_model.selectedRows()

        """ Only one commit for now
        # Ensuring we keep the hash in reverse chronological order
        hashs = [row.data() for row in rows]
        ref = list(self.history.keys())
        hashs.sort(key=lambda x: ref.index(x))
        """

        if len(rows) == 1:
            self.current_git_diff_index = int(rows[0].data())
            self.current_git_diff: GitDiff = self.history[self.current_git_diff_index]
            row: QModelIndex = rows[0]
            self.display_git_diff()
            self.compute_conflicts(row.row())
        else:
            self.current_git_diff_index = None
            self.current_git_diff = None
            self.mainwidget.fileView.setModel(QStandardItemModel(self.mainwidget.fileView))
            self.reset_conflict_indexes()
        self.mainwidget.diffView.setModel(QStandardItemModel(self.mainwidget.diffView))

        model: QStandardItemModel = self.mainwidget.commitList.model()

        for i in range(0, len(self.history)):
            item: QStandardItem = model.item(i, 0)
            if (
                    self.mainwidget.commitList.top_conflict is not None and i <= self.mainwidget.commitList.top_conflict) or (
                    self.mainwidget.commitList.bottom_conflict is not None and i >= self.mainwidget.commitList.bottom_conflict):
                if i == self.mainwidget.commitList.top_conflict or i == self.mainwidget.commitList.bottom_conflict:
                    item.setBackground(QColor(255, 255, 0, 127))
                else:
                    item.setBackground(QColor(159, 159, 159, 127))
            else:
                item.setBackground(QColor(255, 255, 255))

    def compute_conflicts(self, row):
        current_diff = self.history[row]
        top_conflict = None
        bottom_conflict = None
        for i in range(row - 1, -1, -1):
            next_diff: GitDiff = self.history[i]
            next_files = set(next_diff.file_diffs.keys())
            current_files = set(current_diff.file_diffs.keys())

            if len(next_files.intersection(current_files)) == 0:
                continue

            merge_diff = CommitMerge(current_diff, next_diff)

            if merge_diff.conflicts:
                top_conflict = i
                break
            else:
                merge_diff.swap_all()
                current_diff = parse_git_diff(merge_diff.dump()[1].split(b"\n"), current_diff.hash, current_diff.message)

        for i in range(row + 1, len(self.history)):
            previous_diff: GitDiff = self.history[i]
            previous_files = set(previous_diff.file_diffs.keys())
            current_files = set(current_diff.file_diffs.keys())

            if len(previous_files.intersection(current_files)) == 0:
                continue

            merge_diff = CommitMerge(previous_diff, current_diff)

            if merge_diff.conflicts:
                bottom_conflict = i
                break
            else:
                merge_diff.swap_all()
                current_diff = parse_git_diff(merge_diff.dump()[0].split(b"\n"), current_diff.hash, current_diff.message)
        self.mainwidget.commitList.top_conflict = top_conflict
        self.mainwidget.commitList.bottom_conflict = bottom_conflict
        self.mainwidget.commitList.current_index = row

    def on_path_clicked(self):
        Git.path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.load_cwd()

    def load_commit(self, commit):
        raw_diff = Git.raw_diff(commit)
        gitDiff = parse_git_diff(raw_diff, commit, Git.message(commit))
        self.history.append(gitDiff)

    def refresh(self, modif_index, selection_index=None):
        if selection_index is None:
            selection_index = modif_index
        self.update_hash_to_commit()

        if self.current_modif_index is None:
            self.current_modif_index = modif_index
        else:
            self.current_modif_index = max(modif_index, self.current_modif_index)

        self.mainwidget.commitList.setCurrentIndex(self.mainwidget.commitList.model().index(selection_index, 0))

    def update_hash_to_commit(self):
        self.hash_to_diff = OrderedDict()
        for elt in self.history:
            self.hash_to_diff[elt.hash] = elt

    def load_history(self):
        self.history = []
        if Git.valid_repository():
            current_commit = Git.current_hash()
            parents = Git.parents(current_commit)
            while len(parents) <= 1 and \
                    current_commit != "1b9e9cf66fe61bd4ebee912d8ea48aa55e167bae":
                self.load_commit(current_commit)
                if len(parents) == 0:
                    break
                current_commit = parents[0]
                parents = Git.parents(current_commit)
            self.root_commit = current_commit

        self.update_hash_to_commit()

        commit_list = self.mainwidget.commitList
        commit_model = QStandardItemModel(commit_list)

        for i in range(0, len(self.history)):
            item = QStandardItem()
            item.setText(str(i))
            item.setDropEnabled(False)
            commit_model.appendRow(item)

        commit_list.setItemDelegate(ItemDelegate(self, commit_list))
        commit_list.setModel(commit_model)
        commit_model = commit_list.selectionModel()  # Weird Bug in PyQt ?
        commit_model.selectionChanged.connect(self.on_commit_selection_changed)
        commit_list.mouseDoubleClickEvent = self.commit_double_click
        self.reset_conflict_indexes()
        commit_list.show()
        self.current_modif_index = None

    def commit_double_click(self, event):
        message, accepted = QInputDialog.getMultiLineText(self, "Renaming commit message", "",
                                                          self.history[self.current_git_diff_index].message)
        if accepted:
            self.history[self.current_git_diff_index].message = message
        self.refresh(self.current_git_diff_index)

    def load_cwd(self):
        if Git.valid_repository():
            self.mainwidget.pathLabel.setText(Git.path)
        else:
            self.mainwidget.pathLabel.setText("(invalid git repository) " + Git.path)
        self.load_history()

    def sigint_handler(self, *_):  # Quitting from leftclick on menubar
        QApplication.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    ex = Main()
    sys.exit(app.exec_())
