# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsLineItem, QGraphicsRectItem
from PySide6.QtGui import QPixmap, QPolygonF, QPen, QColor, QBrush
from PySide6.QtCore import Qt, QPointF, Signal, QRectF
from core.shapes import RectShape, PolyShape, PointShape, RotatedRectShape, HandleItem, PoseShape


class CanvasMode:
    """画布绘制模式枚举类。

    定义标注工具支持的所有绘制模式：
        EDIT (0): 编辑模式，用于选择和操作已有的标注图形。
        RECT (1): 矩形标注模式，绘制轴对齐的矩形框。
        POLY (2): 多边形标注模式，通过连续点击顶点绘制任意多边形。
        POINT (3): 关键点标注模式，用于放置骨架关键点或单点标注。
        RBOX (4): 旋转矩形（OBB）标注模式，绘制带旋转角度的矩形框。
    """
    EDIT = 0
    RECT = 1
    POLY = 2
    POINT = 3
    RBOX = 4

    @staticmethod
    def get_mode_name(mode):
        names = {1: "矩形", 2: "多边形", 3: "关键点", 4: "旋转框"}
        return names.get(mode, "未知")


class Canvas(QGraphicsScene):
    """标注画布场景，管理所有标注图形和绘制交互。

    作为 QGraphicsScene 的子类，Canvas 负责：
    - 管理图片加载与显示
    - 处理鼠标事件以实现绘制、编辑和选择操作
    - 管理标注图形的增删改查
    - 支持 SAM (Segment Anything Model) 智能辅助标注
    - 支持骨架关键点（Pose）模板的预览与放置
    - 显示十字准星辅助线
    """
    mouse_moved = Signal(int, int)
    shape_drawn = Signal(object)
    shape_double_clicked = Signal(object)
    state_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode = CanvasMode.RECT
        self.img_item = None
        self.sam_client = None
        self.sam_enabled = False
        
        self.current_pose_template = None

        self.drawing = False
        self.start_pt = None
        self.temp_item = None
        self.poly_pts = []

        # 智能悬停提示图层
        self.sam_hover_item = None

        self.h_line = QGraphicsLineItem()
        self.v_line = QGraphicsLineItem()
        crosshair_pen = QPen(QColor(255, 255, 255, 200), 1, Qt.DashLine)
        self.h_line.setPen(crosshair_pen)
        self.v_line.setPen(crosshair_pen)
        self.h_line.setZValue(9999)
        self.v_line.setZValue(9999)
        self.h_line.hide()
        self.v_line.hide()
        self.addItem(self.h_line)
        self.addItem(self.v_line)

    def load_image(self, path):
        """加载图片到画布中。

        清除已有标注图形，加载指定路径的图片，并设置场景矩形为图片大小。
        同时显示十字准星辅助线。

        Args:
            path: 图片文件的路径。
        """
        self.clear_shapes()
        pixmap = QPixmap(path)
        if self.img_item:
            self.removeItem(self.img_item)
        self.img_item = QGraphicsPixmapItem(pixmap)
        self.addItem(self.img_item)
        self.setSceneRect(pixmap.rect())
        self.h_line.show()
        self.v_line.show()

    def clear_shapes(self):
        """清除画布上所有标注图形。

        遍历画布中的所有图形项，移除 RectShape、PolyShape、PointShape、
        RotatedRectShape 和 PoseShape 类型的标注图形，同时清理临时预览项的引用。
        """
        # Clear all shape items from the canvas
        for item in self.items():
            if isinstance(item, (RectShape, PolyShape, PointShape, RotatedRectShape, PoseShape)):
                if getattr(item, 'is_temp', False):
                    if hasattr(self, 'pose_preview_item') and item == getattr(self, 'pose_preview_item', None):
                        self.pose_preview_item = None
                    if hasattr(self, 'sam_hover_item') and item == getattr(self, 'sam_hover_item', None):
                        self.sam_hover_item = None
                self.removeItem(item)

    def set_mode(self, mode):
        """设置画布的绘制模式。

        切换标注模式时自动取消正在进行的绘制操作，
        并清除当前所有选中项的选择状态。

        Args:
            mode: 绘制模式，应为 CanvasMode 枚举值之一。
        """
        self.mode = mode
        self.cancel_drawing()
        for item in self.selectedItems():
            item.setSelected(False)

    def set_sam_enabled(self, enabled):
        """启用或禁用 SAM 智能辅助标注功能。

        当禁用 SAM 时，自动移除当前的 SAM 悬停预览图形。

        Args:
            enabled: True 表示启用 SAM 辅助标注，False 表示禁用。
        """
        self.sam_enabled = enabled
        if not enabled and self.sam_hover_item:
            self.removeItem(self.sam_hover_item)
            self.sam_hover_item = None

    def is_inside_image(self, pt):
        if not self.img_item: return False
        return self.sceneRect().contains(pt)

    def clamp_point(self, pt):
        rect = self.sceneRect()
        x = max(rect.left(), min(pt.x(), rect.right()))
        y = max(rect.top(), min(pt.y(), rect.bottom()))
        return QPointF(x, y)

    def update_crosshair(self, pt):
        """更新十字准星辅助线的位置。

        根据鼠标当前坐标，在画布上绘制水平和垂直两条虚线，
        帮助用户精确定位标注位置。同时发射 mouse_moved 信号。

        Args:
            pt: 鼠标当前场景坐标（QPointF）。
        """
        if self.img_item:
            rect = self.sceneRect()
            x = max(rect.left(), min(pt.x(), rect.right()))
            y = max(rect.top(), min(pt.y(), rect.bottom()))
            self.h_line.setLine(rect.left(), y, rect.right(), y)
            self.v_line.setLine(x, rect.top(), x, rect.bottom())
            self.mouse_moved.emit(int(x), int(y))

    def mouseMoveEvent(self, event):
        """鼠标移动事件处理。

        根据当前绘制模式执行不同操作：
        - 更新十字准星位置
        - 在 POINT 模式下预览骨架模板
        - 在 SAM 启用时请求智能辅助推理
        - 在 RECT/RBOX 模式下实时显示拖拽过程中的临时矩形
        - 在 POLY 模式下更新多边形的临时预览边

        Args:
            event: 鼠标事件对象。
        """
        pt = event.scenePos()
        self.update_crosshair(pt)
        super().mouseMoveEvent(event)
        clamped_pt = self.clamp_point(pt)

        # 预览骨架模板 (跟随鼠标)
        if self.mode == CanvasMode.POINT and self.current_pose_template:
            # 1. State Constraint: Hide preview if ANY item is selected (Edit Mode)
            has_selection = len(self.selectedItems()) > 0
            
            if has_selection:
                if hasattr(self, 'pose_preview_item') and self.pose_preview_item:
                    self.pose_preview_item.hide()
            else:
                # 检查鼠标下方是否有其他标注对象 (排除图片和线条)
                items_under_mouse = self.items(pt)
                hovering_on_shape = False
                for item in items_under_mouse:
                    from core.shapes import BaseShape, HandleItem, KeypointHandle
                    if isinstance(item, (BaseShape, HandleItem, KeypointHandle)) and not getattr(item, 'is_temp', False):
                        hovering_on_shape = True
                        break
                
                if hovering_on_shape:
                    if hasattr(self, 'pose_preview_item') and self.pose_preview_item:
                        self.pose_preview_item.hide()
                else:
                    if not hasattr(self, 'pose_preview_item') or not self.pose_preview_item:
                        from core.shapes import PoseShape
                        # Create a preview shape centered at 0,0 with default size
                        rect = QRectF(-50, -75, 100, 150)
                        self.pose_preview_item = PoseShape(rect, self.current_pose_template, is_temp=True)
                        self.pose_preview_item.setAcceptedMouseButtons(Qt.NoButton)
                        self.addItem(self.pose_preview_item)
                        self.pose_preview_item.setOpacity(0.6)
                    
                    self.pose_preview_item.show()
                    self.pose_preview_item.setPos(clamped_pt)

        # ---------------- SAM 智能辅助悬停 ----------------
        # 将 RBOX 加入 SAM 支持的模式列表
        if self.sam_enabled and self.is_inside_image(pt) and self.mode in [CanvasMode.RECT, CanvasMode.POLY,
                                                                           CanvasMode.RBOX]:
            if self.sam_client:
                self.sam_client.request_inference(clamped_pt.x(), clamped_pt.y(), is_click=False)
            return
        elif self.sam_hover_item:
            self.removeItem(self.sam_hover_item)
            self.sam_hover_item = None

        # ---------------- 常规绘图 ----------------
        if self.drawing and self.start_pt:
            rect = QRectF(min(self.start_pt.x(), clamped_pt.x()), min(self.start_pt.y(), clamped_pt.y()),
                          abs(clamped_pt.x() - self.start_pt.x()), abs(clamped_pt.y() - self.start_pt.y()))
            if self.temp_item: self.removeItem(self.temp_item)

            if self.mode == CanvasMode.RECT:
                self.temp_item = QGraphicsRectItem(rect)
                self.temp_item.is_temp = True
                self.temp_item.setPen(QPen(QColor(28, 126, 214), 2, Qt.DashLine))

            # 手动拉框时，调用全新的 RotatedRectShape 参数格式
            elif self.mode == CanvasMode.RBOX:
                cx, cy = rect.center().x(), rect.center().y()
                w, h = max(1, rect.width()), max(1, rect.height())
                self.temp_item = RotatedRectShape(cx, cy, w, h, 0, is_temp=True)

            self.addItem(self.temp_item)

        elif self.mode == CanvasMode.POLY and not self.sam_enabled and len(self.poly_pts) > 0:
            self.update_temp_poly(mouse_pos=clamped_pt)

    def handle_sam_result(self, poly_pts, rect_xywh, rect_obb, score, is_click):
        """处理 SAM 模型的推理结果并渲染到画布上。

        根据当前绘制模式将 SAM 推理结果渲染为对应类型的图形：
        - RECT 模式：渲染为矩形框
        - POLY 模式：渲染为多边形轮廓
        - RBOX 模式：渲染为旋转矩形（OBB）
        如果是点击确认（is_click=True），则发射 shape_drawn 信号生成最终标注；
        如果是悬停预览（is_click=False），则创建临时预览图形。

        Args:
            poly_pts: 多边形顶点列表。
            rect_xywh: 矩形参数 [x, y, w, h]。
            rect_obb: 旋转矩形参数 [cx, cy, w, h, angle]。
            score: 推理置信度分数。
            is_click: True 表示点击确认生成标注，False 表示悬停预览。
        """
        # 支持 RBOX
        if not self.sam_enabled or self.mode not in [CanvasMode.RECT, CanvasMode.POLY, CanvasMode.RBOX]:
            return

        if self.sam_hover_item:
            self.removeItem(self.sam_hover_item)
            self.sam_hover_item = None

        if not poly_pts or not rect_xywh:
            return

        # ---- 模式判断：矩形智能框 / 多边形点选 / 旋转框 ----
        if self.mode == CanvasMode.RECT:
            x, y, w, h = rect_xywh
            rect = QRectF(x, y, w, h)

            if is_click:
                shape = RectShape(rect)
                self.shape_drawn.emit(shape)
            else:
                self.sam_hover_item = QGraphicsRectItem(rect)
                self.sam_hover_item.setPen(QPen(QColor(0, 255, 0), 2, Qt.DashLine))
                self.sam_hover_item.setBrush(QBrush(QColor(0, 255, 0, 50)))
                self.addItem(self.sam_hover_item)

        elif self.mode == CanvasMode.POLY:
            qpts = [QPointF(p[0], p[1]) for p in poly_pts]
            if is_click:
                shape = PolyShape(QPolygonF(qpts))
                self.shape_drawn.emit(shape)
            else:
                self.sam_hover_item = PolyShape(QPolygonF(qpts), is_temp=True)
                self.sam_hover_item.setPen(QPen(QColor(0, 255, 0), 2, Qt.DashLine))
                self.sam_hover_item.setBrush(QBrush(QColor(0, 255, 0, 50)))
                self.addItem(self.sam_hover_item)

        # SAM 的 OBB 旋转框处理分支
        elif self.mode == CanvasMode.RBOX:
            if not rect_obb or len(rect_obb) < 5: return
            cx, cy, w, h, angle = rect_obb

            if is_click:
                shape = RotatedRectShape(cx, cy, w, h, angle)
                self.shape_drawn.emit(shape)
            else:
                self.sam_hover_item = RotatedRectShape(cx, cy, w, h, angle, is_temp=True)
                self.addItem(self.sam_hover_item)

    def mousePressEvent(self, event):
        """鼠标按下事件处理。

        根据当前模式和点击位置执行不同操作：
        - SAM 启用时：发送点击坐标请求 SAM 推理生成标注
        - 点击已有标注图形：处理选中/编辑逻辑（支持手柄拖拽和骨架编辑）
        - 点击空白处：取消所有选中状态
        - RECT/RBOX 模式：开始绘制新图形，记录起始点
        - POINT 模式：放置骨架模板或单点标注
        - POLY 模式：添加多边形顶点，检测闭合条件

        Args:
            event: 鼠标事件对象。
        """
        pt = event.scenePos()
        clamped_pt = self.clamp_point(pt)

        is_yolo = getattr(self.sam_client, 'current_model_key', '').startswith('yolo')

        # ---------------- SAM 确认生成 ----------------
        # 支持 RBOX, 但仅限 SAM 模型
        if self.sam_enabled and not is_yolo and event.button() == Qt.LeftButton and self.mode in [CanvasMode.RECT, CanvasMode.POLY,
                                                                                  CanvasMode.RBOX]:
            if self.is_inside_image(pt) and self.sam_client:
                self.sam_client.request_inference(clamped_pt.x(), clamped_pt.y(), is_click=True)
            return

        items = self.items(clamped_pt)
        clicked_item = None
        for item in items:
            from core.shapes import HandleItem, OBBHandle, KeypointHandle, BaseShape
            if isinstance(item, (HandleItem, OBBHandle, KeypointHandle)) and item.isVisible():
                if not getattr(item.parentItem(), 'is_temp', False):
                    clicked_item = item
                    break
        if not clicked_item:
            for item in items:
                from core.shapes import BaseShape
                if isinstance(item, BaseShape):
                    if not getattr(item, 'is_temp', False):
                        clicked_item = item
                        break
                elif item.parentItem() and isinstance(item.parentItem(), BaseShape):
                    if not getattr(item.parentItem(), 'is_temp', False):
                        clicked_item = item.parentItem()
                        break

        # 允许在关闭 SAM 或是使用 YOLO 的情况下编辑，或者点击到了手柄也允许编辑
        from core.shapes import HandleItem, OBBHandle, KeypointHandle, PoseShape
        is_handle = isinstance(clicked_item, (HandleItem, OBBHandle, KeypointHandle))
        is_pose = isinstance(clicked_item, PoseShape)
        if clicked_item and (not self.sam_enabled or is_yolo or is_handle or is_pose):
            # First, let the item handle the event (e.g. for dragging)
            # This is crucial so that QGraphicsScene can set it as the mouse grabber
            super().mousePressEvent(event)
            
            # Then handle our custom selection logic
            if event.button() == Qt.LeftButton:
                if not (event.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)):
                    # Deselect all other items
                    for item in self.selectedItems():
                        if item != clicked_item and item != clicked_item.parentItem():
                            item.setSelected(False)
                    
                    # Select the clicked item (or its parent if it's a handle)
                    if isinstance(clicked_item, (HandleItem, OBBHandle, KeypointHandle)):
                        parent = clicked_item.parentItem()
                        if parent:
                            parent.setSelected(True)
                    else:
                        clicked_item.setSelected(True)
            return
            
        # 如果点击了空白处，取消所有选中状态 (退出编辑模式)
        if event.button() == Qt.LeftButton and not clicked_item:
            has_selection = len(self.selectedItems()) > 0
            if has_selection:
                for item in self.selectedItems():
                    item.setSelected(False)
                # 如果是点击空白处退出编辑模式，我们不应该继续向下执行绘制新图形的逻辑
                return

        # ---------------- 常规绘图起点 ----------------
        if not self.is_inside_image(pt) and not self.drawing: return
        if event.button() == Qt.LeftButton:
            if self.mode in [CanvasMode.RECT, CanvasMode.RBOX]:
                self.drawing = True
                self.start_pt = clamped_pt
            elif self.mode == CanvasMode.POINT:
                if self.current_pose_template:
                    # 单击放置骨架模板
                    from core.shapes import PoseShape
                    rect = QRectF(-50, -75, 100, 150) # 默认大小缩小一半
                    shape = PoseShape(rect, self.current_pose_template)
                    shape.setPos(clamped_pt)
                    shape.is_temp = False
                    
                    # 默认创建后不选中（不进入编辑模式）
                    shape.setSelected(False)
                    shape._update_handle_visibility()
                    
                    self.shape_drawn.emit(shape)
                    
                    # 隐藏预览
                    if hasattr(self, 'pose_preview_item') and self.pose_preview_item:
                        self.removeItem(self.pose_preview_item)
                        self.pose_preview_item = None
                else:
                    shape = PointShape(clamped_pt)
                    self.shape_drawn.emit(shape)
            elif self.mode == CanvasMode.POLY:
                if len(self.poly_pts) > 2:
                    dist = ((clamped_pt.x() - self.poly_pts[0].x()) ** 2 + (
                            clamped_pt.y() - self.poly_pts[0].y()) ** 2) ** 0.5
                    if dist < 10:
                        self.finish_poly_shape()
                        return
                self.poly_pts.append(clamped_pt)
                self.update_temp_poly()
            elif self.mode == CanvasMode.POINT:
                pass # Already handled above
        elif event.button() == Qt.RightButton:
            if self.mode == CanvasMode.POLY and len(self.poly_pts) > 2:
                self.finish_poly_shape()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件处理。

        当鼠标释放时，结束当前绘图拖拽操作。
        如果拖拽产生的矩形尺寸大于阈值（5x5），
        则根据当前模式生成 RectShape 或 RotatedRectShape 标注图形。

        Args:
            event: 鼠标事件对象。
        """
        super().mouseReleaseEvent(event)
        if self.sam_enabled: return

        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            if self.temp_item:
                pt = self.clamp_point(event.scenePos())
                rect = QRectF(min(self.start_pt.x(), pt.x()), min(self.start_pt.y(), pt.y()),
                              abs(pt.x() - self.start_pt.x()), abs(pt.y() - self.start_pt.y()))
                self.removeItem(self.temp_item)
                self.temp_item = None

                if rect.width() > 5 and rect.height() > 5:
                    if self.mode == CanvasMode.RECT:
                        self.shape_drawn.emit(RectShape(rect))
                    # 手动松开鼠标完成绘制时，实例化新的 RotatedRectShape
                    elif self.mode == CanvasMode.RBOX:
                        cx, cy = rect.center().x(), rect.center().y()
                        w, h = rect.width(), rect.height()
                        self.shape_drawn.emit(RotatedRectShape(cx, cy, w, h, 0))

        self.state_changed.emit()

    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件处理。

        检测双击位置的标注图形，发射 shape_double_clicked 信号以打开编辑对话框。
        在 POLY 模式下双击可结束多边形绘制。

        Args:
            event: 鼠标事件对象。
        """
        pt = event.scenePos()
        if not self.is_inside_image(pt): return

        for item in self.items(pt):
            from core.shapes import BaseShape, HandleItem
            if getattr(item, 'is_temp', False):
                continue
            if isinstance(item, BaseShape):
                self.shape_double_clicked.emit(item)
                return
            elif isinstance(item, HandleItem):
                parent = item.parentItem()
                if parent and not getattr(parent, 'is_temp', False):
                    self.shape_double_clicked.emit(parent)
                    return
            elif item.parentItem() and isinstance(item.parentItem(), BaseShape):
                parent = item.parentItem()
                if not getattr(parent, 'is_temp', False):
                    self.shape_double_clicked.emit(parent)
                    return

        if event.button() == Qt.LeftButton and self.mode == CanvasMode.POLY and not self.sam_enabled and len(
                self.poly_pts) > 2:
            self.finish_poly_shape()
        else:
            super().mouseDoubleClickEvent(event)

    def update_temp_poly(self, mouse_pos=None):
        """更新多边形绘制的临时预览图形。

        在当前已添加的顶点和鼠标当前位置之间绘制实时的预览线段，
        帮助用户在闭合多边形前看到完整形状。

        Args:
            mouse_pos: 当前鼠标位置（QPointF），为 None 时仅显示已有顶点。
        """
        display_pts = self.poly_pts.copy()
        if mouse_pos is not None: display_pts.append(mouse_pos)
        if len(display_pts) < 2:
            if self.temp_item: self.removeItem(self.temp_item); self.temp_item = None
            return
        if self.temp_item and isinstance(self.temp_item, PolyShape):
            self.temp_item.setPolygon(QPolygonF(display_pts))
        else:
            if self.temp_item: self.removeItem(self.temp_item)
            self.temp_item = PolyShape(QPolygonF(display_pts), is_temp=True)
            self.addItem(self.temp_item)

    def finish_poly_shape(self):
        """完成多边形绘制并生成标注图形。

        将当前收集的多边形顶点列表转换为 PolyShape 对象，
        清除临时预览图形和顶点缓存，发射 shape_drawn 信号。
        """
        shape = PolyShape(QPolygonF(self.poly_pts))
        self.poly_pts.clear()
        if self.temp_item:
            self.removeItem(self.temp_item)
            self.temp_item = None
        self.shape_drawn.emit(shape)

    def cancel_drawing(self):
        """取消当前正在进行的绘制操作。

        重置绘制状态，清除所有临时图形（包括多边形顶点、临时矩形、
        SAM 悬停预览和骨架预览），释放相关资源。
        """
        self.drawing = False
        self.poly_pts.clear()
        if self.temp_item:
            self.removeItem(self.temp_item)
            self.temp_item = None
        if self.sam_hover_item:
            self.removeItem(self.sam_hover_item)
            self.sam_hover_item = None
        if hasattr(self, 'pose_preview_item') and self.pose_preview_item:
            self.removeItem(self.pose_preview_item)
            self.pose_preview_item = None

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key_Backspace or key == Qt.Key_Delete:
            for item in self.selectedItems():
                self.removeItem(item)
            self.state_changed.emit()
        elif key == Qt.Key_Z and modifiers == Qt.ControlModifier:
            if self.mode == CanvasMode.POLY and not self.sam_enabled and len(self.poly_pts) > 0:
                self.poly_pts.pop()
                self.update_temp_poly()
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            if self.mode == CanvasMode.POLY and len(self.poly_pts) > 2:
                self.finish_poly_shape()
        elif key == Qt.Key_Escape:
            self.cancel_drawing()
        elif key in [Qt.Key_Z, Qt.Key_X, Qt.Key_C, Qt.Key_V]:
            items = self.selectedItems()
            if items and isinstance(items[0], RotatedRectShape):
                delta = 0
                if key == Qt.Key_Z:
                    delta = -5
                elif key == Qt.Key_X:
                    delta = -1
                elif key == Qt.Key_C:
                    delta = 1
                elif key == Qt.Key_V:
                    delta = 5
                if delta != 0:
                    item = items[0]
                    item.setRotation(item.rotation() + delta)
                    self.state_changed.emit()

        super().keyPressEvent(event)