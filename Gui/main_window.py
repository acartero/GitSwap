# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Gui/main_window.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

from Gui.commit_list_view import CommitListView


class Ui_MainWindow(QtWidgets.QWidget):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.pathLabel = QtWidgets.QLabel(self.centralwidget)
        self.pathLabel.setObjectName("pathLabel")
        self.verticalLayout.addWidget(self.pathLabel)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pathButton = QtWidgets.QPushButton(self.centralwidget)
        self.pathButton.setObjectName("pathButton")
        self.horizontalLayout_2.addWidget(self.pathButton)
        self.mergeButton = QtWidgets.QPushButton(self.centralwidget)
        self.mergeButton.setObjectName("mergeButton")
        self.horizontalLayout_2.addWidget(self.mergeButton)
        self.splitButton = QtWidgets.QPushButton(self.centralwidget)
        self.splitButton.setObjectName("splitButton")
        self.horizontalLayout_2.addWidget(self.splitButton)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.commitList = CommitListView(self.centralwidget)
        self.commitList.setObjectName("commitList")
        self.verticalLayout.addWidget(self.commitList)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.fileView = QtWidgets.QListView(self.centralwidget)
        self.fileView.setObjectName("fileView")
        self.horizontalLayout.addWidget(self.fileView)
        self.diffView = QtWidgets.QListView(self.centralwidget)
        self.diffView.setObjectName("diffView")
        self.horizontalLayout.addWidget(self.diffView)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.commitButton = QtWidgets.QPushButton(self.centralwidget)
        self.commitButton.setObjectName("commitButton")
        self.verticalLayout.addWidget(self.commitButton)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "GitSwap"))
        self.pathLabel.setText(_translate("MainWindow", "TextLabel"))
        self.pathButton.setText(_translate("MainWindow", "Select path"))
        self.mergeButton.setText(_translate("MainWindow", "Merge"))
        self.splitButton.setText(_translate("MainWindow", "Split"))
        self.commitButton.setText(_translate("MainWindow", "Commit everything"))

