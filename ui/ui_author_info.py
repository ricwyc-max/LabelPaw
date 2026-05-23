# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'author_info.ui'
##
## Created by: Qt User Interface Compiler version 6.4.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)
import resources_rc

class Ui_AuthorInfoDialog(object):
    def setupUi(self, AuthorInfoDialog):
        if not AuthorInfoDialog.objectName():
            AuthorInfoDialog.setObjectName(u"AuthorInfoDialog")
        AuthorInfoDialog.resize(400, 280)
        self.verticalLayout = QVBoxLayout(AuthorInfoDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.labelTitle = QLabel(AuthorInfoDialog)
        self.labelTitle.setObjectName(u"labelTitle")
        self.labelTitle.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.labelTitle)

        self.labelAuthor = QLabel(AuthorInfoDialog)
        self.labelAuthor.setObjectName(u"labelAuthor")
        self.labelAuthor.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.labelAuthor)

        self.labelEmail = QLabel(AuthorInfoDialog)
        self.labelEmail.setObjectName(u"labelEmail")
        self.labelEmail.setOpenExternalLinks(True)
        self.labelEmail.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.labelEmail)

        self.labelGithub = QLabel(AuthorInfoDialog)
        self.labelGithub.setObjectName(u"labelGithub")
        self.labelGithub.setOpenExternalLinks(True)
        self.labelGithub.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.labelGithub)

        self.labelCoding = QLabel(AuthorInfoDialog)
        self.labelCoding.setObjectName(u"labelCoding")
        self.labelCoding.setOpenExternalLinks(True)
        self.labelCoding.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.labelCoding)

        self.labelMotto = QLabel(AuthorInfoDialog)
        self.labelMotto.setObjectName(u"labelMotto")
        self.labelMotto.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.labelMotto)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.btnClose = QPushButton(AuthorInfoDialog)
        self.btnClose.setObjectName(u"btnClose")

        self.verticalLayout.addWidget(self.btnClose)


        self.retranslateUi(AuthorInfoDialog)
        self.btnClose.clicked.connect(AuthorInfoDialog.accept)

        QMetaObject.connectSlotsByName(AuthorInfoDialog)
    # setupUi

    def retranslateUi(self, AuthorInfoDialog):
        AuthorInfoDialog.setWindowTitle(QCoreApplication.translate("AuthorInfoDialog", u"\u5173\u4e8e\u4f5c\u8005", None))
        self.labelTitle.setText(QCoreApplication.translate("AuthorInfoDialog", u"<h2>LabelPaw - \u667a\u80fd\u56fe\u50cf\u6807\u6ce8\u7cfb\u7edf</h2>", None))
        self.labelAuthor.setText(QCoreApplication.translate("AuthorInfoDialog", u"<b>\u4f5c\u8005\uff1a</b>\u843d\u82b1\u4e0d\u5199\u7801", None))
        self.labelEmail.setText(QCoreApplication.translate("AuthorInfoDialog", u"<a href=\"mailto:179958974@qq.com\">\ud83d\udce7 179958974@qq.com</a>", None))
        self.labelGithub.setText(QCoreApplication.translate("AuthorInfoDialog", u"<a href=\"https://github.com/luohuabuxiema/LabelPaw\">\ud83c\udf10 GitHub \u9879\u76ee\u5730\u5740</a>", None))
        self.labelCoding.setText(QCoreApplication.translate("AuthorInfoDialog", u"<a href=\"https://blog.csdn.net/qq_42910179\">\ud83d\udcdd CSDN \u535a\u5ba2</a>", None))
        self.labelMotto.setText(QCoreApplication.translate("AuthorInfoDialog", u"\u5b66\u4e60\u65b0\u601d\u60f3\uff0c\u4e89\u505a\u65b0\u9752\u5e74", None))
        self.btnClose.setText(QCoreApplication.translate("AuthorInfoDialog", u"\u5173\u95ed", None))
    # retranslateUi

