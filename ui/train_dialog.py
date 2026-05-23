"""YOLO 模型训练对话框"""

import os
import re
import sys

# 在主线程中预导入 ultralytics，避免 QThread 栈空间不足导致 0xC00000FD
try:
    from ultralytics import YOLO
    _ULTRA_AVAILABLE = True
except ImportError:
    _ULTRA_AVAILABLE = False

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QLabel, QTextEdit, QProgressBar, QMessageBox, QFileDialog,
    QCheckBox, QWidget
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon


# ── 预置 YOLO 模型列表 ──
PRESET_MODELS = [
    ("yolov8n.pt", "YOLOv8n (轻量)"),
    ("yolov8s.pt", "YOLOv8s (小)"),
    ("yolov8m.pt", "YOLOv8m (中等)"),
    ("yolov8l.pt", "YOLOv8l (大)"),
    ("yolov8x.pt", "YOLOv8x (超大)"),
    ("yolo11n.pt", "YOLO11n (轻量)"),
    ("yolo11s.pt", "YOLO11s (小)"),
    ("yolo11m.pt", "YOLO11m (中等)"),
    ("yolo11l.pt", "YOLO11l (大)"),
    ("yolo11x.pt", "YOLO11x (超大)"),
]


def find_project_root():
    """从当前文件位置向上查找项目根目录。"""
    # ui/train_dialog.py → 项目根
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def scan_custom_weights():
    """扫描 weights/ 下所有 YOLO 权重文件。"""
    root = find_project_root()
    weights_dir = os.path.join(root, "weights")
    custom = []
    if os.path.exists(weights_dir):
        for folder in sorted(os.listdir(weights_dir)):
            folder_path = os.path.join(weights_dir, folder)
            if os.path.isdir(folder_path) and folder.startswith("yolo"):
                for f in os.listdir(folder_path):
                    if f.endswith(".pt"):
                        custom.append((os.path.join(folder_path, f), f"{folder}/{f}"))
    return custom


def parse_data_yaml(yaml_path):
    """解析 data.yaml 文件，返回摘要信息字典。"""
    info = {"nc": 0, "names": [], "train": 0, "val": 0, "test": 0}
    if not os.path.exists(yaml_path):
        return info

    nc = 0
    names = []
    with open(yaml_path, "r", encoding="utf-8") as f:
        content = f.read()

    # nc 行
    m = re.search(r"nc:\s*(\d+)", content)
    if m:
        info["nc"] = int(m.group(1))

    # names 行 (支持多种格式)
    m = re.search(r"names:\s*(?:\[([^\]]*)\]|([\s\S]*?)(?=\n\w+:))", content)
    if m:
        raw = m.group(1) or m.group(2) or ""
        if raw.strip():
            names = [n.strip().strip("'\"") for n in raw.split(",") if n.strip()]

    # train/val/test 路径
    for key in ("train", "val", "test"):
        m = re.search(rf"{key}:\s*(.+?)(?:\s*#.*)?$", content, re.MULTILINE)
        if m:
            path = m.group(1).strip().strip("'\"")
            info[key] = path

    info["names"] = names
    return info


def count_images_in_path(path):
    """递归统计目录下的图片文件数。"""
    exts = (".jpg", ".jpeg", ".png", ".bmp")
    count = 0
    if os.path.isfile(path):
        return 1
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for f in files:
                if f.lower().endswith(exts):
                    count += 1
    return count


class TrainWorker(QThread):
    """YOLO 训练后台线程，通过重定向 stdout 捕获实时日志。"""
    log_signal = Signal(str)
    progress_signal = Signal(int)
    finished_signal = Signal(bool, str)

    def __init__(self, pretrained_path, data_yaml_path, params):
        super().__init__()
        self.pretrained_path = pretrained_path
        self.data_yaml_path = data_yaml_path
        self.params = params
        self._running = True

    def stop(self):
        self._running = False

    def write(self, text):
        """重定向 stdout.write() 到此方法，捕获 YOLO 日志。"""
        self.log_signal.emit(text)
        # 从日志中提取轮次信息更新进度
        m = re.search(r"Epoch\s+(\d+)/(\d+)", text)
        if m:
            current = int(m.group(1))
            total = int(m.group(2))
            progress = int(current / total * 100)
            self.progress_signal.emit(progress)

    def flush(self):
        pass

    def run(self):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self

        try:
            if not _ULTRA_AVAILABLE:
                self.log_signal.emit("错误: ultralytics 未安装，请执行 pip install ultralytics\n")
                self.finished_signal.emit(False, "ultralytics 未安装")
                return

            self.log_signal.emit(f"加载预训练模型: {self.pretrained_path}\n")
            model = YOLO(self.pretrained_path)

            self.log_signal.emit("开始训练...\n")
            model.train(
                data=self.data_yaml_path,
                epochs=self.params["epochs"],
                batch=self.params["batch"],
                imgsz=self.params["imgsz"],
                device=self.params["device"],
                workers=self.params["workers"],
                lr0=self.params["lr0"],
                patience=self.params["patience"],
                verbose=True,
            )

            self.log_signal.emit("\n训练完成！正在验证...\n")
            metrics = model.val()
            self.log_signal.emit(f"验证完成: mAP50={metrics.box.map50:.4f}, mAP50-95={metrics.box.map:.4f}\n")

            # 找到最佳权重路径
            save_dir = model.trainer.save_dir if hasattr(model, 'trainer') else None
            best_path = os.path.join(save_dir, "weights", "best.pt") if save_dir else ""

            self.progress_signal.emit(100)
            if best_path and os.path.exists(best_path):
                self.log_signal.emit(f"最佳模型已保存: {best_path}\n")
                self.finished_signal.emit(True, best_path)
            else:
                self.finished_signal.emit(True, "训练完成")

        except Exception as e:
            import traceback
            self.log_signal.emit(f"\n训练失败: {e}\n{traceback.format_exc()}\n")
            self.finished_signal.emit(False, str(e))

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


class TrainDialog(QDialog):
    """YOLO 模型训练配置对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("YOLO 模型训练")
        self.resize(640, 720)
        self.worker = None
        self._is_training = False

        self._setup_ui()
        self._load_preset_models()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ── 数据集选择 ──
        ds_group = QGroupBox("数据集")
        ds_layout = QVBoxLayout(ds_group)

        path_row = QHBoxLayout()
        self.ds_path = QLineEdit()
        self.ds_path.setPlaceholderText("选择包含 data.yaml 的数据集目录...")
        btn_browse = QPushButton("浏览")
        btn_browse.clicked.connect(self._browse_dataset)
        path_row.addWidget(self.ds_path, 1)
        path_row.addWidget(btn_browse)

        self.ds_info = QLabel("请选择数据集目录")
        self.ds_info.setWordWrap(True)

        ds_layout.addLayout(path_row)
        ds_layout.addWidget(self.ds_info)
        layout.addWidget(ds_group)

        # ── 基础模型 ──
        model_group = QGroupBox("基础模型")
        model_layout = QFormLayout(model_group)

        self.model_combo = QComboBox()
        model_layout.addRow("预训练模型:", self.model_combo)

        layout.addWidget(model_group)

        # ── 训练参数 ──
        param_group = QGroupBox("训练参数")
        param_layout = QFormLayout(param_group)

        self.spin_epochs = QSpinBox()
        self.spin_epochs.setRange(1, 1000)
        self.spin_epochs.setValue(100)

        self.spin_batch = QSpinBox()
        self.spin_batch.setRange(1, 256)
        self.spin_batch.setValue(16)

        self.spin_imgsz = QSpinBox()
        self.spin_imgsz.setRange(32, 4096)
        self.spin_imgsz.setValue(640)
        self.spin_imgsz.setSingleStep(32)

        self.spin_workers = QSpinBox()
        self.spin_workers.setRange(0, 64)
        self.spin_workers.setValue(8)

        self.spin_lr0 = QDoubleSpinBox()
        self.spin_lr0.setRange(0.0001, 1.0)
        self.spin_lr0.setValue(0.01)
        self.spin_lr0.setSingleStep(0.001)
        self.spin_lr0.setDecimals(4)

        self.spin_patience = QSpinBox()
        self.spin_patience.setRange(0, 500)
        self.spin_patience.setValue(50)
        self.spin_patience.setSpecialValueText("关闭")

        self.combo_device = QComboBox()
        self.combo_device.addItems(["cuda0", "cuda", "cpu", "0", "1"])
        self.combo_device.setCurrentText("cuda0")

        param_layout.addRow("训练轮数:", self.spin_epochs)
        param_layout.addRow("批量大小:", self.spin_batch)
        param_layout.addRow("图片尺寸:", self.spin_imgsz)
        param_layout.addRow("设备:", self.combo_device)
        param_layout.addRow("工作线程:", self.spin_workers)
        param_layout.addRow("学习率:", self.spin_lr0)
        param_layout.addRow("早停耐心:", self.spin_patience)

        layout.addWidget(param_group)

        # ── 操作按钮 ──
        btn_row = QHBoxLayout()
        self.btn_train = QPushButton("开始训练")
        self.btn_train.clicked.connect(self._toggle_training)

        self.btn_open_dir = QPushButton("打开训练目录")
        self.btn_open_dir.clicked.connect(self._open_train_dir)

        btn_row.addWidget(self.btn_train)
        btn_row.addWidget(self.btn_open_dir)
        layout.addLayout(btn_row)

        # ── 日志 ──
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(200)
        layout.addWidget(QLabel("训练日志:"))
        layout.addWidget(self.log_output, 1)

        # ── 进度条 ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

    def _load_preset_models(self):
        """加载预置模型和自定义权重到下拉框。"""
        for filename, label in PRESET_MODELS:
            self.model_combo.addItem(f"{label} ({filename})", filename)
        # 扫描自定义权重
        custom = scan_custom_weights()
        if custom:
            self.model_combo.insertSeparator(self.model_combo.count())
            for path, label in custom:
                self.model_combo.addItem(f"[自定义] {label}", path)

    def _browse_dataset(self):
        """选择数据集目录。"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择数据集目录")
        if dir_path:
            self.ds_path.setText(dir_path)
            self._update_dataset_info(dir_path)

    def _update_dataset_info(self, dir_path):
        """解析并显示数据集摘要信息。"""
        yaml_path = os.path.join(dir_path, "data.yaml")
        if not os.path.exists(yaml_path):
            self.ds_info.setText("⚠️ 目录中未找到 data.yaml 文件")
            return

        info = parse_data_yaml(yaml_path)
        info["train"] = count_images_in_path(
            os.path.join(dir_path, info["train"]) if info["train"] else ""
        ) if info["train"] else 0
        info["val"] = count_images_in_path(
            os.path.join(dir_path, info["val"]) if info["val"] else ""
        ) if info["val"] else 0

        names_str = ", ".join(info["names"][:10])
        if len(info["names"]) > 10:
            names_str += f"... (共 {len(info['names'])} 类)"
        self.ds_info.setText(
            f"✅ 类别数: {info['nc']} ({names_str})\n"
            f"   训练集: {info['train']} 张 | 验证集: {info['val']} 张"
        )

    def _toggle_training(self):
        """开始/停止训练。"""
        if self._is_training:
            self._stop_training()
        else:
            self._start_training()

    def _start_training(self):
        """验证参数并启动训练线程。"""
        ds_dir = self.ds_path.text().strip()
        if not ds_dir:
            QMessageBox.warning(self, "提示", "请先选择数据集目录")
            return
        yaml_path = os.path.join(ds_dir, "data.yaml")
        if not os.path.exists(yaml_path):
            QMessageBox.warning(self, "提示", "数据集目录中未找到 data.yaml")
            return

        pretrained = self.model_combo.currentData()
        if not pretrained or not os.path.exists(pretrained):
            # 预置模型名（如 yolov8n.pt）会被 YOLO 自动下载
            pass

        params = {
            "epochs": self.spin_epochs.value(),
            "batch": self.spin_batch.value(),
            "imgsz": self.spin_imgsz.value(),
            "device": self.combo_device.currentText(),
            "workers": self.spin_workers.value(),
            "lr0": self.spin_lr0.value(),
            "patience": self.spin_patience.value(),
        }

        self.log_output.clear()
        self.progress_bar.setValue(0)
        self._is_training = True
        self.btn_train.setText("停止训练")
        self._set_params_enabled(False)

        self.worker = TrainWorker(pretrained, yaml_path, params)
        self.worker.log_signal.connect(self._on_log)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _stop_training(self):
        """停止训练。"""
        if self.worker:
            self.worker.stop()
            self._on_log("\n⚠️ 用户手动停止训练\n")
            self._on_finished(False, "已停止")

    def _on_log(self, text):
        self.log_output.insertPlainText(text)
        self.log_output.moveCursor(self.log_output.textCursor().End)

    def _on_finished(self, success, msg):
        self._is_training = False
        self.btn_train.setText("开始训练")
        self._set_params_enabled(True)

        if success:
            self.progress_bar.setValue(100)
            if msg:
                self.log_output.insertPlainText(f"\n✅ 训练成功！模型保存至: {msg}\n")
        else:
            self.log_output.insertPlainText(f"\n❌ {msg}\n")

    def _set_params_enabled(self, enabled):
        for w in [
            self.ds_path, self.model_combo,
            self.spin_epochs, self.spin_batch, self.spin_imgsz,
            self.combo_device, self.spin_workers, self.spin_lr0, self.spin_patience,
        ]:
            w.setEnabled(enabled)

    def _open_train_dir(self):
        """打开 YOLO 训练输出目录。"""
        root = find_project_root()
        train_dir = os.path.join(root, "runs", "train")
        if os.path.exists(train_dir):
            os.startfile(train_dir)
        else:
            QMessageBox.information(self, "提示", "尚未进行训练，训练目录不存在")
