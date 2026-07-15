"""YOLO 模型转 ONNX 导出对话框"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QPushButton, QComboBox, QSpinBox,
    QLabel, QTextEdit, QProgressBar, QMessageBox, QFileDialog,
    QCheckBox, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QTextCursor


def find_project_root():
    """从当前文件位置向上查找项目根目录。"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def scan_pt_weights():
    """扫描 weights/ 目录下的所有 .pt 模型文件。"""
    root = find_project_root()
    weights_dir = os.path.join(root, "weights")
    models = []
    if os.path.exists(weights_dir):
        # 扫描 yolo*_weights/ 目录
        for folder in sorted(os.listdir(weights_dir)):
            folder_path = os.path.join(weights_dir, folder)
            if os.path.isdir(folder_path) and folder.startswith("yolo"):
                for f in sorted(os.listdir(folder_path)):
                    if f.endswith(".pt"):
                        models.append((os.path.join(folder_path, f), f"{folder}/{f}"))
        # 扫描训练输出
        train_dir = os.path.join(weights_dir, "train")
        if os.path.exists(train_dir):
            for exp in sorted(os.listdir(train_dir)):
                best = os.path.join(train_dir, exp, "weights", "best.pt")
                if os.path.exists(best):
                    models.append((best, f"[已训练] {exp}"))
    return models


class ExportWorker(QThread):
    """ONNX 导出工作线程。"""

    log_signal = Signal(str)
    progress_signal = Signal(int)
    finished_signal = Signal(bool, str)

    def __init__(self, model_path, opset=17, dynamic=True, simplify=True, half=False):
        super().__init__()
        self.model_path = model_path
        self.opset = opset
        self.dynamic = dynamic
        self.simplify = simplify
        self.half = half

    def run(self):
        try:
            from ultralytics import YOLO

            self.log_signal.emit(f"正在加载模型: {self.model_path}\n")
            model = YOLO(self.model_path)
            self.progress_signal.emit(30)
            self.log_signal.emit("模型加载完成，开始导出 ONNX...\n")

            result = model.export(
                format="onnx",
                opset=self.opset,
                dynamic=self.dynamic,
                simplify=self.simplify,
                half=self.half,
            )
            self.progress_signal.emit(90)

            output_path = str(result) if result else ""
            self.log_signal.emit(f"导出成功: {output_path}\n")
            self.progress_signal.emit(100)
            self.finished_signal.emit(True, output_path)

        except ImportError as e:
            self.log_signal.emit(f"缺少依赖: {str(e)}\n")
            self.finished_signal.emit(False, f"缺少依赖: {str(e)}")
        except Exception as e:
            self.log_signal.emit(f"导出失败: {str(e)}\n")
            self.finished_signal.emit(False, str(e))


class ExportOnnxDialog(QDialog):
    """YOLO 模型转 ONNX 对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("YOLO 模型转 ONNX")
        self.resize(600, 600)
        self.worker = None
        self._is_exporting = False
        self._last_output_dir = ""

        self._setup_ui()
        self._load_models()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ── 源模型选择 ──
        model_group = QGroupBox("源模型选择")
        model_layout = QVBoxLayout(model_group)

        model_row = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        btn_browse = QPushButton("浏览本地模型")
        btn_browse.clicked.connect(self._browse_model)
        model_row.addWidget(self.model_combo, 1)
        model_row.addWidget(btn_browse)

        self.model_path_label = QLabel("")
        self.model_path_label.setWordWrap(True)
        self.model_path_label.setStyleSheet("color: #666; font-size: 11px;")

        model_layout.addLayout(model_row)
        model_layout.addWidget(self.model_path_label)
        layout.addWidget(model_group)

        # ── 导出参数 ──
        param_group = QGroupBox("导出参数")
        param_layout = QFormLayout(param_group)

        self.spin_opset = QSpinBox()
        self.spin_opset.setRange(9, 21)
        self.spin_opset.setValue(17)
        self.spin_opset.setToolTip("ONNX opset 版本，推荐 17")
        param_layout.addRow("Opset 版本:", self.spin_opset)

        self.chk_dynamic = QCheckBox("动态输入尺寸 (Dynamic Axes)")
        self.chk_dynamic.setChecked(True)
        self.chk_dynamic.setToolTip("允许推理时使用不同的输入尺寸")
        param_layout.addRow("", self.chk_dynamic)

        self.chk_simplify = QCheckBox("简化模型 (Simplify)")
        self.chk_simplify.setChecked(True)
        self.chk_simplify.setToolTip("使用 onnxsim 简化模型结构，提升推理性能")
        param_layout.addRow("", self.chk_simplify)

        self.chk_half = QCheckBox("FP16 半精度 (Half)")
        self.chk_half.setChecked(False)
        self.chk_half.setToolTip("导出 FP16 模型，体积减半但需要 GPU 支持")
        param_layout.addRow("", self.chk_half)

        layout.addWidget(param_group)

        # ── 输出设置 ──
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout(output_group)

        output_row = QHBoxLayout()
        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("默认与源模型同目录")
        btn_output_browse = QPushButton("浏览")
        btn_output_browse.clicked.connect(self._browse_output_dir)
        output_row.addWidget(self.output_dir, 1)
        output_row.addWidget(btn_output_browse)
        output_layout.addLayout(output_row)

        self.output_hint = QLabel("留空则 ONNX 文件保存在源模型所在目录")
        self.output_hint.setStyleSheet("color: #999; font-size: 11px;")
        output_layout.addWidget(self.output_hint)

        layout.addWidget(output_group)

        # ── 操作按钮 ──
        btn_row = QHBoxLayout()
        self.btn_export = QPushButton("开始导出")
        self.btn_export.clicked.connect(self._toggle_export)
        self.btn_open_dir = QPushButton("打开输出目录")
        self.btn_open_dir.setEnabled(False)
        self.btn_open_dir.clicked.connect(self._open_output_dir)
        btn_row.addWidget(self.btn_export)
        btn_row.addWidget(self.btn_open_dir)
        layout.addLayout(btn_row)

        # ── 日志 ──
        layout.addWidget(QLabel("导出日志:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(120)
        layout.addWidget(self.log_output, 1)

        # ── 进度条 ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

    def _load_models(self):
        """加载本地 .pt 模型到下拉框。"""
        models = scan_pt_weights()
        if models:
            for path, desc in models:
                self.model_combo.addItem(f"{desc}", path)
        else:
            self.model_combo.addItem("未找到 .pt 模型文件", "")
            self.btn_export.setEnabled(False)

    def _on_model_changed(self, index):
        """模型选择变化时更新路径显示。"""
        path = self.model_combo.currentData()
        if path and os.path.exists(path):
            self.model_path_label.setText(f"路径: {path}")
        else:
            self.model_path_label.setText("")

    def _browse_model(self):
        """浏览选择本地 .pt 模型文件。"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择模型文件", "", "PyTorch 模型 (*.pt *.pth);;所有文件 (*)"
        )
        if path:
            name = os.path.basename(path)
            self.model_combo.insertItem(0, f"[本地] {name}", path)
            self.model_combo.setCurrentIndex(0)

    def _browse_output_dir(self):
        """选择输出目录。"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir.setText(dir_path)

    def _toggle_export(self):
        """开始/停止导出。"""
        if self._is_exporting:
            self._stop_export()
        else:
            self._start_export()

    def _start_export(self):
        """验证参数并启动导出线程。"""
        model_path = self.model_combo.currentData()
        if not model_path or not os.path.exists(model_path):
            QMessageBox.warning(self, "提示", "请选择有效的模型文件")
            return

        self._is_exporting = True
        self.btn_export.setText("停止导出")
        self.model_combo.setEnabled(False)
        self.btn_open_dir.setEnabled(False)
        self.log_output.clear()
        self.progress_bar.setValue(0)

        self.worker = ExportWorker(
            model_path=model_path,
            opset=self.spin_opset.value(),
            dynamic=self.chk_dynamic.isChecked(),
            simplify=self.chk_simplify.isChecked(),
            half=self.chk_half.isChecked(),
        )
        self.worker.log_signal.connect(self._on_log)
        self.worker.progress_signal.connect(self._on_progress)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _stop_export(self):
        """停止导出。"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(3000)
            self._on_log("\n导出已手动停止\n")
            self._reset_ui()

    def _on_log(self, msg):
        """追加日志。"""
        self.log_output.moveCursor(QTextCursor.End)
        self.log_output.insertPlainText(msg)
        self.log_output.moveCursor(QTextCursor.End)

    def _on_progress(self, value):
        """更新进度条。"""
        self.progress_bar.setValue(value)

    def _on_finished(self, success, msg):
        """导出完成回调。"""
        if success:
            self._last_output_dir = os.path.dirname(msg) if msg else ""
            self.btn_open_dir.setEnabled(bool(self._last_output_dir))
            QMessageBox.information(self, "导出成功", f"ONNX 模型已保存到:\n{msg}")
        else:
            QMessageBox.warning(self, "导出失败", msg)
        self._reset_ui()

    def _reset_ui(self):
        """重置 UI 状态。"""
        self._is_exporting = False
        self.btn_export.setText("开始导出")
        self.model_combo.setEnabled(True)

    def _open_output_dir(self):
        """打开输出目录。"""
        import subprocess
        output_dir = self._last_output_dir or self.output_dir.text().strip()
        if output_dir and os.path.isdir(output_dir):
            subprocess.Popen(["explorer", os.path.normpath(output_dir)])
        else:
            QMessageBox.information(self, "提示", "暂无输出目录")
