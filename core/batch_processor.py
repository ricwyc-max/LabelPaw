import os
import time
import threading
from PIL import Image
from PySide6.QtCore import QThread, Signal, QPointF, QRectF
from PySide6.QtGui import QPolygonF
from PySide6.QtWidgets import QGraphicsScene

from core.shapes import RectShape, PolyShape
from core.exporter import Exporter

# 支持的图片扩展名
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}


def scan_image_files(folder_path):
    """扫描文件夹中的所有图片文件"""
    image_files = []
    if not os.path.isdir(folder_path):
        return image_files

    for filename in sorted(os.listdir(folder_path)):
        ext = os.path.splitext(filename)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            image_files.append(os.path.join(folder_path, filename))

    return image_files


class BatchProcessorWorker(QThread):
    """批量处理工作线程，支持 SAM3 文本提示词和 YOLO 模型自动标注"""

    # 信号定义
    progress_updated = Signal(int, int, str)  # 当前索引, 总数, 当前文件名
    processing_finished = Signal(int, int)    # 成功数, 失败数
    log_message = Signal(str)                 # 日志信息

    def __init__(self, mode="sam3", sam_client=None, yolo_model_path=None,
                 input_folder=None, output_folder=None, output_format="json",
                 confidence_threshold=0.25, annotation_mode="poly",
                 classes_list=None, prompt_text=None):
        """
        Args:
            mode: 处理模式 ("sam3" 或 "yolo")
            sam_client: SAMClient 实例（SAM3 模式需要）
            yolo_model_path: YOLO 模型路径（YOLO 模式需要）
            input_folder: 输入文件夹路径
            output_folder: 输出文件夹路径
            output_format: 输出格式 ("json", "yolo", "xml")
            confidence_threshold: 置信度阈值
            annotation_mode: 标注模式 ("rect" 或 "poly")
            classes_list: 类别列表（YOLO 格式需要）
            prompt_text: SAM3 文本提示词（SAM3 模式需要）
        """
        super().__init__()
        self.mode = mode
        self.sam_client = sam_client
        self.yolo_model_path = yolo_model_path
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.output_format = output_format
        self.confidence_threshold = confidence_threshold
        self.annotation_mode = annotation_mode
        self.classes_list = classes_list or []
        self.prompt_text = prompt_text

        # 控制标志
        self._is_paused = False
        self._is_cancelled = False

        # SAM3 结果同步
        self._result_event = threading.Event()
        self._current_results = None

        # YOLO 预测器
        self._yolo_predictor = None

    def _init_sam3(self):
        """初始化 SAM3 模式"""
        if not self.sam_client:
            self.log_message.emit("❌ SAM 客户端未初始化")
            return False

        if not self.sam_client.supports_text_prompt():
            self.log_message.emit("❌ 当前模型不支持文本提示词，请加载 SAM3 模型")
            return False

        # 连接信号接收推理结果
        self.sam_client.text_result_ready.connect(self._on_sam3_text_result)
        return True

    def _init_yolo(self):
        """初始化 YOLO 模式"""
        try:
            from core.yolo_predictor import YoloPredictor
            self.log_message.emit(f"正在加载 YOLO 模型: {self.yolo_model_path}")
            self._yolo_predictor = YoloPredictor(self.yolo_model_path)
            self.log_message.emit(f"✅ YOLO 模型加载成功，任务类型: {self._yolo_predictor.task}")
            return True
        except Exception as e:
            self.log_message.emit(f"❌ YOLO 模型加载失败: {str(e)}")
            return False

    def _on_sam3_text_result(self, results, prompt_text):
        """接收 SAM3 文本推理结果"""
        if prompt_text == self.prompt_text:
            self._current_results = results
            self._result_event.set()

    def pause(self):
        """暂停处理"""
        self._is_paused = True

    def resume(self):
        """恢复处理"""
        self._is_paused = False

    def cancel(self):
        """取消处理"""
        self._is_cancelled = True
        self._is_paused = False

    def _check_pause_cancel(self):
        """检查暂停/取消状态，返回 True 表示已取消"""
        while self._is_paused and not self._is_cancelled:
            time.sleep(0.1)
        return self._is_cancelled

    def _get_output_path(self, image_path):
        """根据输入图片路径和输出格式生成输出文件路径"""
        basename = os.path.splitext(os.path.basename(image_path))[0]

        if self.output_format == "json":
            ext = ".json"
        elif self.output_format == "yolo":
            ext = ".txt"
        elif self.output_format == "xml":
            ext = ".xml"
        else:
            ext = ".json"

        return os.path.join(self.output_folder, basename + ext)

    def _get_image_size(self, image_path):
        """获取图片尺寸"""
        try:
            with Image.open(image_path) as img:
                return img.size  # (width, height)
        except Exception:
            return None

    def _process_sam3_image(self, image_path):
        """使用 SAM3 处理单张图片"""
        # 重置结果同步
        self._current_results = None
        self._result_event.clear()

        # 设置图片并请求推理
        self.sam_client.set_image(image_path)
        self.sam_client.request_text_inference(self.prompt_text)

        # 等待结果（最多等待 30 秒）
        if not self._result_event.wait(timeout=30):
            return None

        return self._current_results

    def _process_yolo_image(self, image_path):
        """使用 YOLO 处理单张图片"""
        if not self._yolo_predictor:
            return None

        try:
            shapes = self._yolo_predictor.predict_sync(image_path)
            return shapes
        except Exception as e:
            self.log_message.emit(f"  ⚠ YOLO 推理失败: {str(e)}")
            return None

    def _create_shapes_from_sam3_results(self, results):
        """将 SAM3 推理结果转换为标注形状列表"""
        shapes = []

        for res in results:
            # 过滤低置信度结果
            score = res.get("score", 1.0)
            if score < self.confidence_threshold:
                continue

            if self.annotation_mode == "rect":
                x, y, w, h = res["rect"]
                shape = RectShape(QRectF(x, y, w, h), self.prompt_text)
            else:
                poly_pts = res.get("poly_pts", [])
                if not poly_pts:
                    x, y, w, h = res["rect"]
                    shape = RectShape(QRectF(x, y, w, h), self.prompt_text)
                else:
                    qpts = [QPointF(p[0], p[1]) for p in poly_pts]
                    shape = PolyShape(QPolygonF(qpts), self.prompt_text)

            shapes.append(shape)

        return shapes

    def _create_shapes_from_yolo_results(self, yolo_shapes):
        """将 YOLO 推理结果转换为标注形状列表"""
        shapes = []

        for s in yolo_shapes:
            # 过滤低置信度结果
            score = s.get("score", 1.0)
            if score < self.confidence_threshold:
                continue

            shape_type = s["type"]
            label = s["label"]
            data = s["data"]

            if shape_type == "rect":
                shape = RectShape(data, label)
            elif shape_type == "poly":
                shape = PolyShape(data, label)
            elif shape_type == "rbox":
                # OBB 转换为多边形
                shape = PolyShape(data, label)
            elif shape_type == "pose":
                # 关键点检测，使用矩形框
                rect = data["rect"]
                shape = RectShape(rect, label)
            else:
                continue

            shapes.append(shape)

        return shapes

    def _save_annotation(self, image_path, shapes):
        """保存标注文件"""
        output_path = self._get_output_path(image_path)
        image_size = self._get_image_size(image_path)

        if not image_size:
            self.log_message.emit(f"  ⚠ 无法读取图片尺寸: {os.path.basename(image_path)}")
            return False

        img_width, img_height = image_size

        # 创建临时场景用于导出
        scene = QGraphicsScene()
        for shape in shapes:
            scene.addItem(shape)

        # 提取标注数据
        shapes_data = Exporter.extract_shapes(scene)

        try:
            if self.output_format == "json":
                Exporter.save_json(output_path, image_path, img_width, img_height, shapes_data)
            elif self.output_format == "yolo":
                Exporter.save_yolo(output_path, img_width, img_height, shapes_data, self.classes_list)
            elif self.output_format == "xml":
                Exporter.save_xml(output_path, image_path, img_width, img_height, shapes_data)

            # 清理场景
            for shape in shapes:
                scene.removeItem(shape)
            scene.deleteLater()

            return True
        except Exception as e:
            self.log_message.emit(f"  ⚠ 保存失败: {str(e)}")
            for shape in shapes:
                scene.removeItem(shape)
            scene.deleteLater()
            return False

    def run(self):
        """主处理循环"""
        # 初始化模型
        if self.mode == "sam3":
            if not self._init_sam3():
                self.processing_finished.emit(0, 0)
                return
            self.log_message.emit(f"📝 模式: SAM3 文本提示词")
            self.log_message.emit(f"   提示词: {self.prompt_text}")
        else:
            if not self._init_yolo():
                self.processing_finished.emit(0, 0)
                return
            self.log_message.emit(f"📝 模式: YOLO 模型自动标注")

        # 扫描图片文件
        image_files = scan_image_files(self.input_folder)
        total = len(image_files)

        if total == 0:
            self.log_message.emit("❌ 未找到任何图片文件")
            self.processing_finished.emit(0, 0)
            return

        # 创建输出文件夹
        os.makedirs(self.output_folder, exist_ok=True)

        self.log_message.emit(f"🚀 开始批量处理")
        self.log_message.emit(f"   输入文件夹: {self.input_folder}")
        self.log_message.emit(f"   输出文件夹: {self.output_folder}")
        self.log_message.emit(f"   输出格式: {self.output_format}")
        self.log_message.emit(f"   置信度阈值: {self.confidence_threshold}")
        self.log_message.emit(f"   共找到 {total} 张图片")
        self.log_message.emit("-" * 50)

        success_count = 0
        fail_count = 0

        for i, image_path in enumerate(image_files):
            # 检查取消/暂停
            if self._check_pause_cancel():
                self.log_message.emit("⚠ 处理已取消")
                break

            filename = os.path.basename(image_path)
            self.progress_updated.emit(i + 1, total, filename)

            try:
                # 根据模式处理图片
                if self.mode == "sam3":
                    raw_results = self._process_sam3_image(image_path)
                    if raw_results is None:
                        self.log_message.emit(f"✗ [{i+1}/{total}] {filename}: 推理超时")
                        fail_count += 1
                        continue
                    if not raw_results:
                        self.log_message.emit(f"✗ [{i+1}/{total}] {filename}: 未检测到目标")
                        fail_count += 1
                        continue
                    shapes = self._create_shapes_from_sam3_results(raw_results)
                else:
                    raw_results = self._process_yolo_image(image_path)
                    if raw_results is None:
                        self.log_message.emit(f"✗ [{i+1}/{total}] {filename}: YOLO 推理失败")
                        fail_count += 1
                        continue
                    if not raw_results:
                        self.log_message.emit(f"✗ [{i+1}/{total}] {filename}: 未检测到目标")
                        fail_count += 1
                        continue
                    shapes = self._create_shapes_from_yolo_results(raw_results)

                if not shapes:
                    self.log_message.emit(f"✗ [{i+1}/{total}] {filename}: 无符合阈值的结果")
                    fail_count += 1
                    continue

                # 保存标注
                if self._save_annotation(image_path, shapes):
                    self.log_message.emit(f"✓ [{i+1}/{total}] {filename}: 检测到 {len(shapes)} 个目标")
                    success_count += 1
                else:
                    fail_count += 1

                # 清理形状对象
                for shape in shapes:
                    del shape

            except Exception as e:
                self.log_message.emit(f"✗ [{i+1}/{total}] {filename}: 处理失败 - {str(e)}")
                fail_count += 1

        # 断开信号连接
        if self.mode == "sam3" and self.sam_client:
            try:
                self.sam_client.text_result_ready.disconnect(self._on_sam3_text_result)
            except:
                pass

        self.log_message.emit("-" * 50)
        self.log_message.emit(f"✅ 批量处理完成: 成功 {success_count}, 失败 {fail_count}")

        self.processing_finished.emit(success_count, fail_count)
