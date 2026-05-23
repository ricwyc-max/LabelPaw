from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Qt
from ui.ui_author_info import Ui_AuthorInfoDialog


class AuthorInfoDialog(QDialog, Ui_AuthorInfoDialog):
    """作者信息弹窗，显示软件作者、版本和联系方式等信息。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
