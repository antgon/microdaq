# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'settings_dlg.ui'
#
# Created by: PyQt5 UI code generator 5.15.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(300, 358)
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.baudComboBox = QtWidgets.QComboBox(Dialog)
        self.baudComboBox.setObjectName("baudComboBox")
        self.horizontalLayout.addWidget(self.baudComboBox)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_5.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_2 = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_2.addWidget(self.label_2)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.portComboBox = QtWidgets.QComboBox(Dialog)
        self.portComboBox.setObjectName("portComboBox")
        self.horizontalLayout_2.addWidget(self.portComboBox)
        self.portRefreshButton = QtWidgets.QPushButton(Dialog)
        self.portRefreshButton.setText("")
        icon = QtGui.QIcon.fromTheme("reload")
        self.portRefreshButton.setIcon(icon)
        self.portRefreshButton.setObjectName("portRefreshButton")
        self.horizontalLayout_2.addWidget(self.portRefreshButton)
        self.horizontalLayout_2.setStretch(0, 6)
        self.horizontalLayout_2.setStretch(1, 1)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.verticalLayout_5.addLayout(self.verticalLayout_2)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_3 = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_3.addWidget(self.label_3)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.savePathLabel = QtWidgets.QLabel(Dialog)
        self.savePathLabel.setObjectName("savePathLabel")
        self.horizontalLayout_3.addWidget(self.savePathLabel)
        self.savePathButton = QtWidgets.QToolButton(Dialog)
        self.savePathButton.setObjectName("savePathButton")
        self.horizontalLayout_3.addWidget(self.savePathButton)
        self.horizontalLayout_3.setStretch(1, 1)
        self.verticalLayout_3.addLayout(self.horizontalLayout_3)
        self.verticalLayout_5.addLayout(self.verticalLayout_3)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.label_4 = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.verticalLayout_4.addWidget(self.label_4)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.widthSpinBox = QtWidgets.QSpinBox(Dialog)
        self.widthSpinBox.setMinimum(20)
        self.widthSpinBox.setMaximum(1000)
        self.widthSpinBox.setProperty("value", 500)
        self.widthSpinBox.setObjectName("widthSpinBox")
        self.horizontalLayout_4.addWidget(self.widthSpinBox)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem1)
        self.verticalLayout_4.addLayout(self.horizontalLayout_4)
        self.verticalLayout_5.addLayout(self.verticalLayout_4)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_5.addItem(spacerItem2)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_5.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Settings"))
        self.label.setText(_translate("Dialog", "Baud"))
        self.label_2.setText(_translate("Dialog", "Port"))
        self.portRefreshButton.setToolTip(_translate("Dialog", "Scan serial ports"))
        self.label_3.setText(_translate("Dialog", "Save path"))
        self.savePathLabel.setText(_translate("Dialog", "[path]"))
        self.savePathButton.setToolTip(_translate("Dialog", "Choose a path for saving data"))
        self.savePathButton.setText(_translate("Dialog", "..."))
        self.label_4.setText(_translate("Dialog", "Window width"))
        self.widthSpinBox.setToolTip(_translate("Dialog", "Window width in number of samples"))
