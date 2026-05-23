import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QToolBar, QListWidget, QGraphicsView,
                               QLabel, QLineEdit, QPushButton, QStatusBar, QMenu, QComboBox, QSizePolicy, QAbstractItemView)
from PySide6.QtCore import Qt, Signal, QRect, QSize
from PySide6.QtGui import QAction, QActionGroup, QPainter, QColor, QFont, QIcon, QPixmap


class FormatSelectorWidget(QWidget):
    """标注格式选择器组件，提供 JSON / YOLO / XML 三种标注格式的下拉切换。

    通过 QPushButton + QMenu 实现简洁的格式切换交互，
    切换后通过 format_changed 信号通知外部当前选中的格式。
    """
    format_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 5, 5, 5)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.btn = QPushButton()
        self.btn.setIcon(QIcon(":/icon/格式.svg"))
        self.btn.setIconSize(QSize(20, 20))  # 放大图标
        self.btn.setText("　JSON 格式 ▾")
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setToolTip("选择标注格式")
        self.btn.setObjectName("formatBtn")

        # 下拉菜单
        self.menu = QMenu(self)
        self.menu.setWindowFlag(Qt.FramelessWindowHint)
        self.menu.setAttribute(Qt.WA_TranslucentBackground)
        self.menu.setObjectName("formatMenu")

        self.act_json = QAction("JSON 格式", self)
        self.act_yolo = QAction("YOLO 格式", self)
        self.act_xml = QAction("XML 格式", self)

        self.menu.addAction(self.act_json)
        self.menu.addAction(self.act_yolo)
        self.menu.addAction(self.act_xml)

        self.btn.setMenu(self.menu)

        layout.addWidget(self.btn)

        self.act_json.triggered.connect(lambda: self._on_format_selected("json", "　JSON 格式 ▾"))
        self.act_yolo.triggered.connect(lambda: self._on_format_selected("yolo", "　YOLO 格式 ▾"))
        self.act_xml.triggered.connect(lambda: self._on_format_selected("xml", "　XML 格式 ▾"))

    def _on_format_selected(self, fmt, text):
        """内部处理格式选择事件，更新按钮文字并发射信号。"""
        self.btn.setText(text)
        self.format_changed.emit(fmt)

    def set_yolo_enabled(self, enabled):
        """启用或禁用 YOLO 格式选项。在骨架标注模式下可强制禁用。"""
        self.act_yolo.setEnabled(enabled)
        if not enabled and self.btn.text().strip() == "YOLO 格式 ▾":
            self._on_format_selected("json", "　JSON 格式 ▾")

    def set_format(self, fmt):
        """外部设置当前格式并更新按钮显示文字。"""
        if fmt == "json":
            self.btn.setText("　JSON 格式 ▾")
        elif fmt == "yolo":
            self.btn.setText("　YOLO 格式 ▾")
        elif fmt == "xml":
            self.btn.setText("　XML 格式 ▾")
            
    def set_icon_only(self, icon_only):
        """切换为纯图标模式（侧边栏折叠时使用），隐藏文字并固定按钮大小。"""
        if icon_only:
            # 记住当前文字以便恢复
            self._cached_text = self.btn.text()
            self.btn.setText("")
            self.btn.setFixedSize(34, 34)
            self.btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 1px solid transparent;
                    color: #F8FAFC;
                    font-size: 13px;
                    font-weight: bold;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #1E293B;
                    color: #22C55E;
                }
                QPushButton::menu-indicator {
                    image: none; /* 强制隐藏默认箭头 */
                }
            """)
        else:
            if hasattr(self, '_cached_text'):
                self.btn.setText(self._cached_text)
            self.btn.setMaximumWidth(16777215)  # 释放宽度限制
            self.btn.setFixedHeight(34)
            self.btn.setStyleSheet("")


class TemplateSelectorWidget(QWidget):
    """骨架模板选择器组件，提供动态下拉菜单以选择和编辑骨架模板。

    支持固定模板（Person (COCO)、Hand、Face 等）和用户自定义模板的切换。
    内置编辑和删除按钮，用于管理自定义模板。
    """
    template_changed = Signal(str)

    edit_template = Signal(str)
    delete_template = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        self.btn = QPushButton("Person (COCO) ▾")
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setObjectName("templateBtn")

        # 下拉菜单
        self.menu = QMenu(self)
        self.menu.setWindowFlag(Qt.FramelessWindowHint)
        self.menu.setAttribute(Qt.WA_TranslucentBackground)
        self.menu.setObjectName("templateMenu")
        self.btn.setMenu(self.menu)

        layout.addWidget(self.btn)

    def update_templates(self, templates, main_window=None):
        """刷新模板下拉菜单列表。固定模板显示为简单菜单项，自定义模板附带编辑和删除按钮。"""
        self.menu.clear()
        
        fixed_templates = ["Person (COCO)", "Hand", "Face (68 pts)", "Rectangle", "Triangle"]

        for t_name in templates:
            if t_name in fixed_templates:
                act = QAction(t_name, self)
                act.triggered.connect(lambda checked=False, name=t_name: self._on_template_selected(name, f"{name} ▾"))
                self.menu.addAction(act)
            else:
                from PySide6.QtWidgets import QWidgetAction, QWidget, QHBoxLayout, QPushButton, QToolButton
                from PySide6.QtGui import QIcon, QColor
                from PySide6.QtCore import Qt

                action = QWidgetAction(self)
                widget = QWidget()
                widget.setStyleSheet("QWidget { background: transparent; }")
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(10, 4, 10, 4)
                layout.setSpacing(5)

                btn_select = QPushButton(t_name)
                btn_select.setStyleSheet("text-align: left; background: transparent; border: none; padding: 2px;")
                btn_select.setCursor(Qt.PointingHandCursor)
                btn_select.clicked.connect(lambda checked=False, name=t_name: self._on_template_selected(name, f"{name} ▾"))
                btn_select.clicked.connect(self.menu.close)

                btn_edit = QToolButton()
                btn_delete = QToolButton()
                
                if main_window:
                    try:
                        btn_edit.setIcon(main_window.set_icon_color(QIcon(":/icon/编辑.svg"), main_window.current_icon_color))
                        btn_delete.setIcon(main_window.set_icon_color(QIcon(":/icon/trash.svg"), QColor("#EF4444")))
                    except:
                        pass

                btn_edit.setStyleSheet("QToolButton { background: transparent; border: none; } QToolButton:hover { background-color: rgba(128,128,128,0.2); border-radius: 4px; }")
                btn_delete.setStyleSheet("QToolButton { background: transparent; border: none; } QToolButton:hover { background-color: rgba(128,128,128,0.2); border-radius: 4px; }")
                btn_edit.setCursor(Qt.PointingHandCursor)
                btn_delete.setCursor(Qt.PointingHandCursor)

                btn_edit.clicked.connect(lambda checked=False, name=t_name: self.edit_template.emit(name))
                btn_edit.clicked.connect(self.menu.close)

                btn_delete.clicked.connect(lambda checked=False, name=t_name: self.delete_template.emit(name))
                btn_delete.clicked.connect(self.menu.close)

                layout.addWidget(btn_select, 1)
                layout.addWidget(btn_edit)
                layout.addWidget(btn_delete)
                action.setDefaultWidget(widget)
                self.menu.addAction(action)
            
        self.menu.addSeparator()
        
        act_new = QAction("+ New Template...", self)
        act_new.triggered.connect(lambda: self._on_template_selected("+ New Template...", self.btn.text()))
        self.menu.addAction(act_new)

    def _on_template_selected(self, template_name, btn_text):
        """内部处理模板选择事件，更新按钮文字并发射信号。"""
        if template_name != "+ New Template...":
            self.btn.setText(btn_text)
        self.template_changed.emit(template_name)
        
    def set_current_template_text(self, text):
        """外部设置当前选中的模板名称。"""
        self.btn.setText(f"{text} ▾")


class SwitchControl(QWidget):
    """自定义绘制的开关控件，模拟 iOS 风格的开/关切换。

    支持横向和竖向两种模式，通过 QPainter 绘制圆角矩形背景和圆形滑块。
    状态改变时发射 toggled 信号。
    """
    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 26)
        self.setCursor(Qt.PointingHandCursor)
        self._checked = False
        self._vertical = False  # 竖向模式

    def isChecked(self):
        """返回当前开关是否处于打开状态。"""
        return self._checked

    def setChecked(self, checked):
        """设置开关状态，若状态发生变化则发射 toggled 信号并重绘。"""
        if self._checked != checked:
            self._checked = checked
            self.toggled.emit(checked)
            self.update()

    def mouseReleaseEvent(self, event):
        """点击开关时切换状态。"""
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        """重写绘制事件，用 QPainter 自定义渲染开关外观。"""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRect(0, 0, self.width(), self.height())

        if self._checked:
            p.setBrush(QColor("#22C55E"))
        else:
            p.setBrush(QColor("#334155"))

        p.setPen(Qt.NoPen)
        radius = min(self.width(), self.height()) // 2
        p.drawRoundedRect(rect, radius, radius)

        p.setBrush(QColor("#FFFFFF"))
        if self._vertical:
            # 竖向模式：圆球上下滑动
            circle_size = self.width() - 4
            if self._checked:
                p.drawEllipse(2, self.height() - circle_size - 2, circle_size, circle_size)
            else:
                p.drawEllipse(2, 2, circle_size, circle_size)
        else:
            # 横向模式：圆球左右滑动
            if self._checked:
                p.drawEllipse(self.width() - 24, 2, 22, 22)
            else:
                p.drawEllipse(2, 2, 22, 22)


class CanvasView(QGraphicsView):
    """自定义画布视图，支持缩放和平移操作。

    - Ctrl + 滚轮：缩放到鼠标所在位置
    - 中键拖拽：平移画布
    - 普通滚轮：在放大状态下滚动浏览画布
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignCenter)
        self.setDragMode(QGraphicsView.NoDrag)
        self.viewport().setCursor(Qt.CrossCursor)

        self._is_panning = False
        self._pan_start_pos = None

    def wheelEvent(self, event):
        """处理滚轮事件：按住 Ctrl 时缩放画布，否者进行滚动浏览。"""
        if event.modifiers() & Qt.ControlModifier:
            # Ctrl + 滚轮：缩放
            zoom_in_factor = 1.15
            zoom_out_factor = 1.0 / zoom_in_factor
            if event.angleDelta().y() > 0:
                self.scale(zoom_in_factor, zoom_in_factor)
            else:
                self.scale(zoom_out_factor, zoom_out_factor)
        else:
            # 普通滚轮：滚动画布（仅放大后才生效，未放大时滚动条范围为 0 自动无效）
            # 垂直滚动
            if event.angleDelta().y() != 0:
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() - event.angleDelta().y()
                )
            # 水平滚动（支持鼠标左右滚轮）
            if event.angleDelta().x() != 0:
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - event.angleDelta().x()
                )

    def mousePressEvent(self, event):
        """鼠标中键按下时进入平移模式。"""
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._pan_start_pos = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动事件：平移模式下根据鼠标位移滚动画布。"""
        if self._is_panning:
            delta = event.position().toPoint() - self._pan_start_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self._pan_start_pos = event.position().toPoint()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标中键释放时退出平移模式。"""
        if event.button() == Qt.MiddleButton:
            self._is_panning = False
            self.viewport().setCursor(Qt.CrossCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)


