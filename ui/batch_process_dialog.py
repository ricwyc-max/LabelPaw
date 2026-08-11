import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSlider, QProgressBar, QTextEdit,
    QFileDialog, QGroupBox, QFormLayout, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QFont

from core.batch_processor import BatchProcessorWorker, scan_image_files

# 导入 Toast 通知组件
try:
    from utils.message import DialogOver
except ImportError:
    DialogOver = None


# 支持的 YOLO 模型扩展名
YOLO_EXTENSIONS = {'.pt', '.onnx'}


def scan_yolo_models(folder_path):
    """扫描文件夹中的 YOLO 模型文件"""
    models = []
    if not os.path.isdir(folder_path):
        return models

    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in YOLO_EXTENSIONS:
                models.append(os.path.join(root, filename))

    return sorted(models)


class BatchProcessDialog(QDialog):
    """批量处理对话框，支持 SAM3 文本提示词和 YOLO 模型自动标注"""

    def __init__(self, sam_client, parent=None):
        super().__init__(parent)
        self.sam_client = sam_client
        self.worker = None

        self.setWindowTitle("批量自动标注")
        self.setMinimumSize(700, 650)
        self.resize(750, 750)

        self._setup_ui()
        self._connect_signals()
        self._on_mode_changed(0)  # 初始化 UI 状态

    def _setup_ui(self):
        """设置 UI 布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # ============================================================
        # 标题
        # ============================================================
        title_label = QLabel("批量自动标注")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #409eff;")
        main_layout.addWidget(title_label)

        desc_label = QLabel("使用 AI 模型批量处理文件夹中的图片并自动生成标注文件。")
        desc_label.setStyleSheet("color: #909399; font-size: 12px;")
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)

        # ============================================================
        # 处理模式选择
        # ============================================================
        mode_group = QGroupBox("处理模式")
        mode_layout = QFormLayout(mode_group)
        mode_layout.setSpacing(10)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "SAM3 文本提示词 (语义分割)",
            "YOLO 模型自动标注 (目标检测)"
        ])
        mode_layout.addRow("选择模式:", self.mode_combo)

        main_layout.addWidget(mode_group)

        # ============================================================
        # 输入设置组
        # ============================================================
        input_group = QGroupBox("输入设置")
        input_layout = QFormLayout(input_group)
        input_layout.setSpacing(10)

        # 输入文件夹
        input_folder_layout = QHBoxLayout()
        self.input_folder_edit = QLineEdit()
        self.input_folder_edit.setPlaceholderText("选择包含图片的文件夹...")
        self.input_folder_btn = QPushButton("浏览")
        self.input_folder_btn.setFixedWidth(60)
        input_folder_layout.addWidget(self.input_folder_edit)
        input_folder_layout.addWidget(self.input_folder_btn)
        input_layout.addRow("输入文件夹:", input_folder_layout)

        # 输出文件夹
        output_folder_layout = QHBoxLayout()
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setPlaceholderText("选择标注文件保存位置...")
        self.output_folder_btn = QPushButton("浏览")
        self.output_folder_btn.setFixedWidth(60)
        output_folder_layout.addWidget(self.output_folder_edit)
        output_folder_layout.addWidget(self.output_folder_btn)
        input_layout.addRow("输出文件夹:", output_folder_layout)

        # SAM3 提示词 (SAM3 模式)
        self.prompt_edit = QLineEdit()
        self.prompt_edit.setPlaceholderText("输入提示词，如: dog, cat, car...")
        self.prompt_label = QLabel("文本提示词:")
        input_layout.addRow(self.prompt_label, self.prompt_edit)

        # YOLO 模型选择 (YOLO 模式)
        yolo_model_layout = QHBoxLayout()
        self.yolo_model_edit = QLineEdit()
        self.yolo_model_edit.setPlaceholderText("选择 YOLO 模型文件 (.pt 或 .onnx)...")
        self.yolo_model_btn = QPushButton("浏览")
        self.yolo_model_btn.setFixedWidth(60)
        yolo_model_layout.addWidget(self.yolo_model_edit)
        yolo_model_layout.addWidget(self.yolo_model_btn)
        self.yolo_model_label = QLabel("YOLO 模型:")
        input_layout.addRow(self.yolo_model_label, yolo_model_layout)

        main_layout.addWidget(input_group)

        # ============================================================
        # 输出设置组
        # ============================================================
        output_group = QGroupBox("输出设置")
        output_layout = QFormLayout(output_group)
        output_layout.setSpacing(10)

        # 输出格式
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JSON (LabelMe)", "YOLO TXT", "Pascal VOC XML"])
        output_layout.addRow("输出格式:", self.format_combo)

        # 标注模式
        self.annotation_combo = QComboBox()
        self.annotation_combo.addItems(["多边形 (Polygon)", "矩形 (Rectangle)"])
        output_layout.addRow("标注模式:", self.annotation_combo)

        # 置信度阈值
        threshold_layout = QHBoxLayout()
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setValue(25)
        self.threshold_label = QLabel("0.25")
        self.threshold_label.setFixedWidth(40)
        self.threshold_label.setAlignment(Qt.AlignCenter)
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_label)
        output_layout.addRow("置信度阈值:", threshold_layout)

        main_layout.addWidget(output_group)

        # ============================================================
        # 进度显示
        # ============================================================
        progress_group = QGroupBox("处理进度")
        progress_layout = QVBoxLayout(progress_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #909399;")
        progress_layout.addWidget(self.status_label)

        main_layout.addWidget(progress_group)

        # ============================================================
        # 控制按钮
        # ============================================================
        button_layout = QHBoxLayout()

        self.start_btn = QPushButton("开始处理")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background-color: #66b1ff; }
            QPushButton:pressed { background-color: #3a8ee6; }
            QPushButton:disabled { background-color: #a0cfff; color: #f0f0f0; }
        """)

        self.pause_btn = QPushButton("暂停")
        self.pause_btn.setEnabled(False)
        self.pause_btn.setFixedWidth(80)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setFixedWidth(80)
        self.cancel_btn.setStyleSheet("""
            QPushButton { background-color: #f56c6c; color: white; border: none; border-radius: 6px; padding: 8px; }
            QPushButton:hover { background-color: #f78989; }
            QPushButton:disabled { background-color: #fab6b6; color: #f0f0f0; }
        """)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.pause_btn)
        button_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(button_layout)

        # ============================================================
        # 日志输出
        # ============================================================
        log_label = QLabel("处理日志:")
        log_label.setStyleSheet("color: #909399; font-size: 12px; margin-top: 5px;")
        main_layout.addWidget(log_label)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 9))
        main_layout.addWidget(self.console, 1)

    def _connect_signals(self):
        """连接信号"""
        self.input_folder_btn.clicked.connect(lambda: self._select_folder(self.input_folder_edit))
        self.output_folder_btn.clicked.connect(lambda: self._select_folder(self.output_folder_edit))
        self.yolo_model_btn.clicked.connect(self._select_yolo_model)
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.start_btn.clicked.connect(self._start_processing)
        self.pause_btn.clicked.connect(self._toggle_pause)
        self.cancel_btn.clicked.connect(self._cancel_processing)

    def _select_folder(self, line_edit):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            line_edit.setText(folder)

    def _select_yolo_model(self):
        """选择 YOLO 模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 YOLO 模型文件",
            "",
            "YOLO 模型 (*.pt *.onnx);;所有文件 (*.*)"
        )
        if file_path:
            self.yolo_model_edit.setText(file_path)

    def _on_threshold_changed(self, value):
        """阈值滑块变化"""
        threshold = value / 100.0
        self.threshold_label.setText(f"{threshold:.2f}")

    def _on_mode_changed(self, index):
        """处理模式切换"""
        is_sam3_mode = (index == 0)

        # SAM3 模式显示提示词输入，隐藏 YOLO 模型选择
        self.prompt_label.setVisible(is_sam3_mode)
        self.prompt_edit.setVisible(is_sam3_mode)

        # YOLO 模式显示模型选择，隐藏提示词输入
        self.yolo_model_label.setVisible(not is_sam3_mode)
        self.yolo_model_edit.setVisible(not is_sam3_mode)
        self.yolo_model_btn.setVisible(not is_sam3_mode)

        # SAM3 模式下标注模式可选，YOLO 模式下由模型决定
        self.annotation_combo.setEnabled(is_sam3_mode)

    def _validate_inputs(self):
        """验证输入"""
        input_folder = self.input_folder_edit.text().strip()
        output_folder = self.output_folder_edit.text().strip()
        mode = self.mode_combo.currentIndex()

        if not input_folder:
            QMessageBox.warning(self, "提示", "请选择输入文件夹！")
            return False

        if not os.path.isdir(input_folder):
            QMessageBox.warning(self, "提示", "输入文件夹不存在！")
            return False

        if not output_folder:
            QMessageBox.warning(self, "提示", "请选择输出文件夹！")
            return False

        # 检查是否有图片文件
        image_files = scan_image_files(input_folder)
        if not image_files:
            QMessageBox.warning(self, "提示", "输入文件夹中未找到图片文件！")
            return False

        if mode == 0:  # SAM3 模式
            prompt = self.prompt_edit.text().strip()
            if not prompt:
                QMessageBox.warning(self, "提示", "请输入文本提示词！")
                return False
        else:  # YOLO 模式
            model_path = self.yolo_model_edit.text().strip()
            if not model_path:
                QMessageBox.warning(self, "提示", "请选择 YOLO 模型文件！")
                return False
            if not os.path.exists(model_path):
                QMessageBox.warning(self, "提示", "YOLO 模型文件不存在！")
                return False

        return True

    def _get_output_format(self):
        """获取输出格式"""
        format_map = {0: "json", 1: "yolo", 2: "xml"}
        return format_map.get(self.format_combo.currentIndex(), "json")

    def _get_annotation_mode(self):
        """获取标注模式"""
        return "poly" if self.annotation_combo.currentIndex() == 0 else "rect"

    def _start_processing(self):
        """开始处理"""
        if not self._validate_inputs():
            return

        # 获取参数
        input_folder = self.input_folder_edit.text().strip()
        output_folder = self.output_folder_edit.text().strip()
        output_format = self._get_output_format()
        confidence_threshold = self.threshold_slider.value() / 100.0
        mode = self.mode_combo.currentIndex()

        # 获取类别列表（YOLO 格式需要）
        classes_list = []
        if output_format == "yolo":
            main_window = self.parent()
            if hasattr(main_window, 'class_list'):
                classes_list = main_window.class_list.copy()

        # 清空日志
        self.console.clear()

        # 更新 UI 状态
        self._set_processing_state(True)

        if mode == 0:  # SAM3 模式
            prompt_text = self.prompt_edit.text().strip()
            annotation_mode = self._get_annotation_mode()

            # 确保提示词在类别列表中
            if output_format == "yolo" and prompt_text not in classes_list:
                classes_list.append(prompt_text)

            self.worker = BatchProcessorWorker(
                mode="sam3",
                sam_client=self.sam_client,
                input_folder=input_folder,
                output_folder=output_folder,
                output_format=output_format,
                confidence_threshold=confidence_threshold,
                annotation_mode=annotation_mode,
                classes_list=classes_list,
                prompt_text=prompt_text
            )
        else:  # YOLO 模式
            model_path = self.yolo_model_edit.text().strip()

            self.worker = BatchProcessorWorker(
                mode="yolo",
                yolo_model_path=model_path,
                input_folder=input_folder,
                output_folder=output_folder,
                output_format=output_format,
                confidence_threshold=confidence_threshold,
                classes_list=classes_list
            )

        # 连接信号
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.log_message.connect(self._on_log_message)
        self.worker.processing_finished.connect(self._on_processing_finished)

        # 启动
        self.worker.start()

    def _set_processing_state(self, is_processing):
        """设置处理状态下的 UI"""
        self.start_btn.setEnabled(not is_processing)
        self.pause_btn.setEnabled(is_processing)
        self.cancel_btn.setEnabled(is_processing)
        self.input_folder_btn.setEnabled(not is_processing)
        self.output_folder_btn.setEnabled(not is_processing)
        self.yolo_model_btn.setEnabled(not is_processing)
        self.prompt_edit.setEnabled(not is_processing)
        self.format_combo.setEnabled(not is_processing)
        self.annotation_combo.setEnabled(not is_processing and self.mode_combo.currentIndex() == 0)
        self.threshold_slider.setEnabled(not is_processing)
        self.mode_combo.setEnabled(not is_processing)

        if is_processing:
            self.pause_btn.setText("暂停")

    def _toggle_pause(self):
        """切换暂停/恢复"""
        if not self.worker:
            return

        if self.worker._is_paused:
            self.worker.resume()
            self.pause_btn.setText("暂停")
            self.status_label.setText("处理中...")
            self.status_label.setStyleSheet("color: #409eff;")
        else:
            self.worker.pause()
            self.pause_btn.setText("恢复")
            self.status_label.setText("已暂停")
            self.status_label.setStyleSheet("color: #e6a23c;")

    def _cancel_processing(self):
        """取消处理"""
        if not self.worker:
            return

        reply = QMessageBox.question(
            self, "确认取消",
            "确定要取消批量处理吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.worker.cancel()
            self.status_label.setText("正在取消...")
            self.status_label.setStyleSheet("color: #f56c6c;")

    def _on_progress_updated(self, current, total, filename):
        """更新进度"""
        progress = int(current / total * 100)
        self.progress_bar.setValue(progress)
        self.progress_bar.setFormat(f"{current}/{total} ({progress}%)")
        self.status_label.setText(f"正在处理: {filename}")
        self.status_label.setStyleSheet("color: #409eff;")

    def _on_log_message(self, message):
        """添加日志"""
        self.console.append(message)
        self.console.moveCursor(QTextCursor.End)

    def _on_processing_finished(self, success_count, fail_count):
        """处理完成"""
        self._set_processing_state(False)
        self.progress_bar.setValue(100)

        total = success_count + fail_count
        if fail_count == 0:
            self.status_label.setText(f"处理完成！成功 {success_count} 张")
            self.status_label.setStyleSheet("color: #67c23a;")
        else:
            self.status_label.setText(f"处理完成：成功 {success_count}，失败 {fail_count}")
            self.status_label.setStyleSheet("color: #e6a23c;")

        # 显示通知
        if DialogOver:
            msg = f"成功: {success_count}，失败: {fail_count}，共: {total}"
            DialogOver(self, msg, "批量处理完成", "success" if fail_count == 0 else "warning")

    def closeEvent(self, event):
        """关闭事件"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "确认关闭",
                "批量处理正在进行中，确定要关闭吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.worker.cancel()
                self.worker.wait(3000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
