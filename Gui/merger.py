# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Gui\merger.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Merger(object):
    def setupUi(self, Merger):
        Merger.setObjectName("Merger")
        Merger.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(Merger)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.swapButton = QtWidgets.QPushButton(self.centralwidget)
        self.swapButton.setObjectName("swapButton")
        self.horizontalLayout.addWidget(self.swapButton)
        self.resetButton = QtWidgets.QPushButton(self.centralwidget)
        self.resetButton.setObjectName("resetButton")
        self.horizontalLayout.addWidget(self.resetButton)
        self.moveLeftButton = QtWidgets.QPushButton(self.centralwidget)
        self.moveLeftButton.setObjectName("moveLeftButton")
        self.horizontalLayout.addWidget(self.moveLeftButton)
        self.moveRightButton = QtWidgets.QPushButton(self.centralwidget)
        self.moveRightButton.setObjectName("moveRightButton")
        self.horizontalLayout.addWidget(self.moveRightButton)
        self.applyButton = QtWidgets.QPushButton(self.centralwidget)
        self.applyButton.setObjectName("applyButton")
        self.horizontalLayout.addWidget(self.applyButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.rightCommitWidget = QtWidgets.QListView(self.centralwidget)
        self.rightCommitWidget.setObjectName("rightCommitWidget")
        self.gridLayout.addWidget(self.rightCommitWidget, 0, 4, 1, 1)
        self.leftIndexes = QtWidgets.QListView(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.leftIndexes.sizePolicy().hasHeightForWidth())
        self.leftIndexes.setSizePolicy(sizePolicy)
        self.leftIndexes.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.leftIndexes.setObjectName("leftIndexes")
        self.gridLayout.addWidget(self.leftIndexes, 0, 0, 1, 1)
        self.leftCommitWidget = QtWidgets.QListView(self.centralwidget)
        self.leftCommitWidget.setObjectName("leftCommitWidget")
        self.gridLayout.addWidget(self.leftCommitWidget, 0, 1, 1, 1)
        self.middleIndexes = QtWidgets.QListView(self.centralwidget)
        self.middleIndexes.setObjectName("middleIndexes")
        self.gridLayout.addWidget(self.middleIndexes, 0, 2, 1, 1)
        self.rightIndexes = QtWidgets.QListView(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.rightIndexes.sizePolicy().hasHeightForWidth())
        self.rightIndexes.setSizePolicy(sizePolicy)
        self.rightIndexes.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.rightIndexes.setObjectName("rightIndexes")
        self.gridLayout.addWidget(self.rightIndexes, 0, 5, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.leftMessage = QtWidgets.QTextEdit(self.centralwidget)
        self.leftMessage.setObjectName("leftMessage")
        self.horizontalLayout_2.addWidget(self.leftMessage)
        self.fileListView = QtWidgets.QListView(self.centralwidget)
        self.fileListView.setObjectName("fileListView")
        self.horizontalLayout_2.addWidget(self.fileListView)
        self.rightMessage = QtWidgets.QTextEdit(self.centralwidget)
        self.rightMessage.setObjectName("rightMessage")
        self.horizontalLayout_2.addWidget(self.rightMessage)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        Merger.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(Merger)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        Merger.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(Merger)
        self.statusbar.setObjectName("statusbar")
        Merger.setStatusBar(self.statusbar)

        self.retranslateUi(Merger)
        QtCore.QMetaObject.connectSlotsByName(Merger)

    def retranslateUi(self, Merger):
        _translate = QtCore.QCoreApplication.translate
        Merger.setWindowTitle(_translate("Merger", "Git Swap - Merger"))
        self.swapButton.setText(_translate("Merger", "Swap"))
        self.resetButton.setText(_translate("Merger", "Reset"))
        self.moveLeftButton.setText(_translate("Merger", "Move left"))
        self.moveRightButton.setText(_translate("Merger", "Move right"))
        self.applyButton.setText(_translate("Merger", "Apply"))
