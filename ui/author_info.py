from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Qt
from ui.ui_author_info import Ui_AuthorInfoDialog


class AuthorInfoDialog(QDialog, Ui_AuthorInfoDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint | Qt.WindowCloseButtonHint
        )
