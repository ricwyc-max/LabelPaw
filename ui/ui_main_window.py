# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.4.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QGraphicsView, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QPushButton, QSizePolicy, QSpacerItem,
    QSplitter, QStatusBar, QToolBar, QToolButton,
    QVBoxLayout, QWidget)

from ui.main_window import (CanvasView, FormatSelectorWidget, SwitchControl, TemplateSelectorWidget)
import resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1280, 800)
        MainWindow.setStyleSheet(u"QMainWindow, QWidget { background-color: #020617; color: #F8FAFC; font-family: \"Microsoft YaHei\", sans-serif; }\n"
"QToolBar { background-color: #0F172A; border: none; padding: 8px; spacing: 12px; }\n"
"QPushButton { background-color: transparent; border: 1px solid transparent; border-radius: 6px; padding: 6px 12px; color: #F8FAFC; }\n"
"QPushButton:hover { background-color: #1E293B; }\n"
"QToolButton { border: none; background: transparent; border-radius: 6px; }\n"
"QListWidget { background-color: #0F172A; border: 1px solid #1E293B; border-radius: 8px; color: #F8FAFC; }\n"
"QLabel { color: #94A3B8; }\n"
"QLineEdit { background-color: #0F172A; border: 1px solid #1E293B; border-radius: 6px; padding: 6px; color: #F8FAFC; }\n"
"QSplitter::handle { background: transparent; width: 1px; }\n"
"QStatusBar { background-color: #0F172A; border-top: 1px solid #1E293B; color: #94A3B8; }")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionRect = QAction(MainWindow)
        self.actionRect.setObjectName(u"actionRect")
        self.actionRect.setCheckable(True)
        self.actionPoly = QAction(MainWindow)
        self.actionPoly.setObjectName(u"actionPoly")
        self.actionPoly.setCheckable(True)
        self.actionPoint = QAction(MainWindow)
        self.actionPoint.setObjectName(u"actionPoint")
        self.actionPoint.setCheckable(True)
        self.actionRBox = QAction(MainWindow)
        self.actionRBox.setObjectName(u"actionRBox")
        self.actionRBox.setCheckable(True)
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName(u"centralWidget")
        self.mainLayout = QVBoxLayout(self.centralWidget)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.topBar = QWidget(self.centralWidget)
        self.topBar.setObjectName(u"topBar")
        self.topBar.setFixedHeight(50)
        self.topBarLayout = QHBoxLayout(self.topBar)
        self.topBarLayout.setSpacing(8)
        self.topBarLayout.setObjectName(u"topBarLayout")
        self.topBarLayout.setContentsMargins(0, 0, 0, 0)
        self.btnCollapse = QPushButton(self.topBar)
        self.btnCollapse.setObjectName(u"btnCollapse")
        font = QFont()
        font.setFamilies([u"Segoe UI"])
        font.setPointSize(16)
        font.setBold(True)
        self.btnCollapse.setFont(font)
        self.btnCollapse.setProperty("fixedSize", QSize(36, 36))

        self.topBarLayout.addWidget(self.btnCollapse)

        self.topBarSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.topBarLayout.addItem(self.topBarSpacer)

        self.btnAuthorInfo = QPushButton(self.topBar)
        self.btnAuthorInfo.setObjectName(u"btnAuthorInfo")
        self.btnAuthorInfo.setFont(font)
        self.btnAuthorInfo.setProperty("fixedSize", QSize(36, 36))

        self.topBarLayout.addWidget(self.btnAuthorInfo)

        self.btnThemeToggle = QPushButton(self.topBar)
        self.btnThemeToggle.setObjectName(u"btnThemeToggle")
        self.btnThemeToggle.setFont(font)
        self.btnThemeToggle.setProperty("fixedSize", QSize(36, 36))

        self.topBarLayout.addWidget(self.btnThemeToggle)


        self.mainLayout.addWidget(self.topBar)

        self.contentSplitter = QSplitter(self.centralWidget)
        self.contentSplitter.setObjectName(u"contentSplitter")
        self.contentSplitter.setOrientation(Qt.Orientation.Horizontal)
        self.canvasArea = QWidget(self.contentSplitter)
        self.canvasArea.setObjectName(u"canvasArea")
        self.canvasLayout = QVBoxLayout(self.canvasArea)
        self.canvasLayout.setSpacing(0)
        self.canvasLayout.setObjectName(u"canvasLayout")
        self.canvasLayout.setContentsMargins(0, 0, 0, 0)
        self.tb_layout_wrap = QHBoxLayout()
        self.tb_layout_wrap.setSpacing(0)
        self.tb_layout_wrap.setObjectName(u"tb_layout_wrap")
        self.tb_layout_wrap.setContentsMargins(0, 0, 0, 0)
        self.tb_left_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.tb_layout_wrap.addItem(self.tb_left_spacer)

        self.tb_layout = QHBoxLayout()
        self.tb_layout.setSpacing(0)
        self.tb_layout.setObjectName(u"tb_layout")
        self.tb_layout.setContentsMargins(0, 0, 0, 0)
        self.btnDrawMode = QPushButton(self.canvasArea)
        self.btnDrawMode.setObjectName(u"btnDrawMode")
        self.btnDrawMode.setCheckable(True)
        self.btnDrawMode.setChecked(True)

        self.tb_layout.addWidget(self.btnDrawMode)

        self.btnSmartMode = QPushButton(self.canvasArea)
        self.btnSmartMode.setObjectName(u"btnSmartMode")
        self.btnSmartMode.setCheckable(True)

        self.tb_layout.addWidget(self.btnSmartMode)

        self.btnModelSelector = QPushButton(self.canvasArea)
        self.btnModelSelector.setObjectName(u"btnModelSelector")
        self.btnModelSelector.setVisible(False)

        self.tb_layout.addWidget(self.btnModelSelector)

        self.btnPredict = QPushButton(self.canvasArea)
        self.btnPredict.setObjectName(u"btnPredict")
        self.btnPredict.setVisible(False)

        self.tb_layout.addWidget(self.btnPredict)

        self.sep1 = QLabel(self.canvasArea)
        self.sep1.setObjectName(u"sep1")

        self.tb_layout.addWidget(self.sep1)

        self.templateWidget = TemplateSelectorWidget(self.canvasArea)
        self.templateWidget.setObjectName(u"templateWidget")
        self.templateWidget.setVisible(False)

        self.tb_layout.addWidget(self.templateWidget)

        self.sepTemplate = QLabel(self.canvasArea)
        self.sepTemplate.setObjectName(u"sepTemplate")
        self.sepTemplate.setVisible(False)

        self.tb_layout.addWidget(self.sepTemplate)

        self.btnUndo = QToolButton(self.canvasArea)
        self.btnUndo.setObjectName(u"btnUndo")
        self.btnUndo.setProperty("fixedSize", QSize(36, 36))

        self.tb_layout.addWidget(self.btnUndo)

        self.btnRedo = QToolButton(self.canvasArea)
        self.btnRedo.setObjectName(u"btnRedo")
        self.btnRedo.setProperty("fixedSize", QSize(36, 36))

        self.tb_layout.addWidget(self.btnRedo)

        self.btnDelete = QToolButton(self.canvasArea)
        self.btnDelete.setObjectName(u"btnDelete")
        self.btnDelete.setProperty("fixedSize", QSize(36, 36))

        self.tb_layout.addWidget(self.btnDelete)

        self.btnSave = QToolButton(self.canvasArea)
        self.btnSave.setObjectName(u"btnSave")
        self.btnSave.setProperty("fixedSize", QSize(36, 36))

        self.tb_layout.addWidget(self.btnSave)

        self.sep3 = QLabel(self.canvasArea)
        self.sep3.setObjectName(u"sep3")

        self.tb_layout.addWidget(self.sep3)

        self.btnKeyboard = QToolButton(self.canvasArea)
        self.btnKeyboard.setObjectName(u"btnKeyboard")
        self.btnKeyboard.setProperty("fixedSize", QSize(36, 36))

        self.tb_layout.addWidget(self.btnKeyboard)


        self.tb_layout_wrap.addLayout(self.tb_layout)

        self.tb_right_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.tb_layout_wrap.addItem(self.tb_right_spacer)


        self.canvasLayout.addLayout(self.tb_layout_wrap)

        self.view = CanvasView(self.canvasArea)
        self.view.setObjectName(u"view")
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.canvasLayout.addWidget(self.view)

        self.contentSplitter.addWidget(self.canvasArea)
        self.rightPanel = QWidget(self.contentSplitter)
        self.rightPanel.setObjectName(u"rightPanel")
        self.dockLayout = QVBoxLayout(self.rightPanel)
        self.dockLayout.setSpacing(0)
        self.dockLayout.setObjectName(u"dockLayout")
        self.dockLayout.setContentsMargins(0, 0, 0, 0)
        self.rightTitleBar = QHBoxLayout()
        self.rightTitleBar.setObjectName(u"rightTitleBar")
        self.rightPanelTitle = QLabel(self.rightPanel)
        self.rightPanelTitle.setObjectName(u"rightPanelTitle")
        font1 = QFont()
        font1.setFamilies([u"Microsoft YaHei"])
        font1.setPointSize(10)
        font1.setBold(True)
        self.rightPanelTitle.setFont(font1)

        self.rightTitleBar.addWidget(self.rightPanelTitle)

        self.rightTitleSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.rightTitleBar.addItem(self.rightTitleSpacer)


        self.dockLayout.addLayout(self.rightTitleBar)

        self.labelClasses = QLabel(self.rightPanel)
        self.labelClasses.setObjectName(u"labelClasses")

        self.dockLayout.addWidget(self.labelClasses)

        self.listClasses = QListWidget(self.rightPanel)
        self.listClasses.setObjectName(u"listClasses")

        self.dockLayout.addWidget(self.listClasses)

        self.labelFiles = QLabel(self.rightPanel)
        self.labelFiles.setObjectName(u"labelFiles")

        self.dockLayout.addWidget(self.labelFiles)

        self.listFiles = QListWidget(self.rightPanel)
        self.listFiles.setObjectName(u"listFiles")
        self.listFiles.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.listFiles.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.dockLayout.addWidget(self.listFiles)

        self.textLayout = QVBoxLayout()
        self.textLayout.setSpacing(0)
        self.textLayout.setObjectName(u"textLayout")
        self.textLayout.setContentsMargins(0, 0, 0, 0)
        self.samPromptInput = QLineEdit(self.rightPanel)
        self.samPromptInput.setObjectName(u"samPromptInput")

        self.textLayout.addWidget(self.samPromptInput)

        self.samPromptBtn = QPushButton(self.rightPanel)
        self.samPromptBtn.setObjectName(u"samPromptBtn")

        self.textLayout.addWidget(self.samPromptBtn)


        self.dockLayout.addLayout(self.textLayout)

        self.contentSplitter.addWidget(self.rightPanel)

        self.mainLayout.addWidget(self.contentSplitter)

        MainWindow.setCentralWidget(self.centralWidget)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        MainWindow.setStatusBar(self.statusBar)
        self.toolBar = QToolBar(MainWindow)
        self.toolBar.setObjectName(u"toolBar")
        self.toolBar.setMovable(False)
        self.toolBar.setOrientation(Qt.Orientation.Vertical)
        self.toolBar.setIconSize(QSize(24, 24))
        self.toolBar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toolBar.setProperty("fixedWidth", 190)
        self.logoWidget = QWidget(self.toolBar)
        self.logoWidget.setObjectName(u"logoWidget")
        self.logoLayout = QHBoxLayout(self.logoWidget)
        self.logoLayout.setSpacing(5)
        self.logoLayout.setObjectName(u"logoLayout")
        self.logoLayout.setContentsMargins(8, 8, 4, 8)
        self.logoIcon = QLabel(self.logoWidget)
        self.logoIcon.setObjectName(u"logoIcon")
        self.logoIcon.setFixedSize(QSize(28, 28))
        self.logoIcon.setAlignment(Qt.AlignCenter)

        self.logoLayout.addWidget(self.logoIcon)

        self.logoLabel = QLabel(self.logoWidget)
        self.logoLabel.setObjectName(u"logoLabel")
        font2 = QFont()
        font2.setFamilies([u"Microsoft YaHei"])
        font2.setPointSize(11)
        font2.setBold(True)
        self.logoLabel.setFont(font2)

        self.logoLayout.addWidget(self.logoLabel)

        self.toolBar.addWidget(self.logoWidget)
        self.formatWidget = FormatSelectorWidget(self.toolBar)
        self.formatWidget.setObjectName(u"formatWidget")
        self.toolBar.addWidget(self.formatWidget)
        self.samWidget = QWidget(self.toolBar)
        self.samWidget.setObjectName(u"samWidget")
        self.samOuterLayout = QHBoxLayout(self.samWidget)
        self.samOuterLayout.setSpacing(10)
        self.samOuterLayout.setObjectName(u"samOuterLayout")
        self.samOuterLayout.setContentsMargins(8, 5, 4, 5)
        self.samIcon = QLabel(self.samWidget)
        self.samIcon.setObjectName(u"samIcon")
        self.samIcon.setFixedSize(QSize(24, 24))
        self.samIcon.setAlignment(Qt.AlignCenter)

        self.samOuterLayout.addWidget(self.samIcon)

        self.samSwitch = SwitchControl(self.samWidget)
        self.samSwitch.setObjectName(u"samSwitch")

        self.samOuterLayout.addWidget(self.samSwitch)

        self.toolBar.addWidget(self.samWidget)
        self.btnDatasetTool = QPushButton(self.toolBar)
        self.btnDatasetTool.setObjectName(u"btnDatasetTool")
        self.toolBar.addWidget(self.btnDatasetTool)
        self.btnExportONNX = QPushButton(self.toolBar)
        self.btnExportONNX.setObjectName(u"btnExportONNX")
        self.toolBar.addWidget(self.btnExportONNX)
        self.btnTrain = QPushButton(self.toolBar)
        self.btnTrain.setObjectName(u"btnTrain")
        self.toolBar.addWidget(self.btnTrain)
        MainWindow.addToolBar(Qt.LeftToolBarArea, self.toolBar)

        self.toolBar.addAction(self.actionOpen)
        self.toolBar.addSeparator()
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionRect)
        self.toolBar.addAction(self.actionPoly)
        self.toolBar.addAction(self.actionPoint)
        self.toolBar.addAction(self.actionRBox)
        self.toolBar.addSeparator()
        self.toolBar.addSeparator()

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"LabelPaw - \u57fa\u4e8eSAM3\u7684\u667a\u80fd\u6807\u6ce8\u7cfb\u7edf", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"\u6253\u5f00\u76ee\u5f55", None))
        self.actionRect.setText(QCoreApplication.translate("MainWindow", u"\u77e9\u5f62\u6807\u6ce8 (R)", None))
        self.actionPoly.setText(QCoreApplication.translate("MainWindow", u"\u591a\u8fb9\u5f62\u6807\u6ce8 (P)", None))
        self.actionPoint.setText(QCoreApplication.translate("MainWindow", u"\u5173\u952e\u70b9\u6807\u6ce8 (T)", None))
        self.actionRBox.setText(QCoreApplication.translate("MainWindow", u"\u65cb\u8f6c\u6846\u6807\u6ce8 (O)", None))
        self.topBar.setObjectName(QCoreApplication.translate("MainWindow", u"topBar", None))
        self.btnCollapse.setText(QCoreApplication.translate("MainWindow", u"\u2261", None))
        self.btnAuthorInfo.setText(QCoreApplication.translate("MainWindow", u"\u24d8", None))
        self.btnThemeToggle.setText(QCoreApplication.translate("MainWindow", u"\u2600", None))
        self.btnDrawMode.setText(QCoreApplication.translate("MainWindow", u"\u270d \u624b\u52a8\u6807\u6ce8", None))
        self.btnSmartMode.setText(QCoreApplication.translate("MainWindow", u"\u2728 \u667a\u80fd", None))
        self.btnModelSelector.setText(QCoreApplication.translate("MainWindow", u" SAM 3 \u25be", None))
        self.btnPredict.setText(QCoreApplication.translate("MainWindow", u" \u9884\u6d4b", None))
        self.sep1.setText(QCoreApplication.translate("MainWindow", u"|", None))
        self.sepTemplate.setText(QCoreApplication.translate("MainWindow", u"|", None))
        self.sep3.setText(QCoreApplication.translate("MainWindow", u"|", None))
        self.rightPanelTitle.setText(QCoreApplication.translate("MainWindow", u"\u6807\u6ce8\u7ba1\u7406", None))
        self.labelClasses.setText(QCoreApplication.translate("MainWindow", u"\u5386\u53f2\u7c7b\u522b:", None))
        self.labelFiles.setText(QCoreApplication.translate("MainWindow", u"\u6587\u4ef6\u5217\u8868:", None))
        self.samPromptInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u8f93\u5165\u63d0\u793a\u8bcd\u63d0\u53d6 (\u5982: dog)", None))
        self.samPromptBtn.setText(QCoreApplication.translate("MainWindow", u"\u2728 \u63d0\u4ea4", None))
        self.logoLabel.setText(QCoreApplication.translate("MainWindow", u"LabelPaw", None))
#if QT_CONFIG(tooltip)
        self.samIcon.setToolTip(QCoreApplication.translate("MainWindow", u"SAM \u667a\u80fd\u8f85\u52a9", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.samSwitch.setToolTip(QCoreApplication.translate("MainWindow", u"\u5f00\u542f/\u5173\u95ed SAM \u667a\u80fd\u8f85\u52a9", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.btnDatasetTool.setToolTip(QCoreApplication.translate("MainWindow", u"\u6570\u636e\u96c6\u5904\u7406", None))
#endif // QT_CONFIG(tooltip)
        self.btnDatasetTool.setText(QCoreApplication.translate("MainWindow", u" \u6570\u636e\u96c6\u5904\u7406", None))
#if QT_CONFIG(tooltip)
        self.btnExportONNX.setToolTip(QCoreApplication.translate("MainWindow", u"\u6a21\u578b\u8f6c ONNX", None))
#endif // QT_CONFIG(tooltip)
        self.btnExportONNX.setText(QCoreApplication.translate("MainWindow", u" \u6a21\u578b\u8f6cONNX", None))
#if QT_CONFIG(tooltip)
        self.btnTrain.setToolTip(QCoreApplication.translate("MainWindow", u"YOLO \u6a21\u578b\u8bad\u7ec3", None))
#endif // QT_CONFIG(tooltip)
        self.btnTrain.setText(QCoreApplication.translate("MainWindow", u" \u6a21\u578b\u8bad\u7ec3", None))
    # retranslateUi

