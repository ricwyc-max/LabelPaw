"""YOLO 模型训练对话框"""

import os
import re
import sys
from datetime import datetime

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
from PySide6.QtCore import Qt, QObject, QProcess, Signal
from PySide6.QtGui import QIcon, QTextCursor


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


class TrainWorker(QObject):
    """YOLO 训练进程管理器，使用 QProcess 在独立进程中运行训练。"""
    log_signal = Signal(str)
    progress_signal = Signal(int)
    finished_signal = Signal(bool, str)

    def __init__(self, pretrained_path, data_yaml_path, params):
        super().__init__()
        self.pretrained_path = pretrained_path
        self.data_yaml_path = data_yaml_path
        self.params = params
        self.process = None
        self._output_buffer = ""

    def start(self):
        """启动训练子进程。"""
        # 创建临时训练脚本（放在项目根目录）
        script = self._make_train_script()
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_train_script.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)

        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.finished.connect(lambda: self._on_finished(script_path))
        # 设置工作目录为项目根目录，使 YOLO 模型下载/保存路径一致
        self.process.setWorkingDirectory(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        python = sys.executable
        self.process.start(python, [script_path])

    def _make_train_script(self):
        """生成训练用的 Python 脚本内容。"""
        return f'''import sys, os, re, shutil, zipfile, time
sys.stdout = sys.stderr  # 合并输出流便于捕获
from ultralytics import YOLO

# 模型下载到指定目录
model_name = os.path.basename({self.pretrained_path!r})
weights_dir = {self.params["save_path"]!r}
os.makedirs(weights_dir, exist_ok=True)
model_path = os.path.join(weights_dir, model_name)

# 如果模型文件损坏（下载中断），自动删除重新下载
if os.path.exists(model_path):
    try:
        with zipfile.ZipFile(model_path) as _zf:
            pass
    except zipfile.BadZipFile:
        for _ in range(5):
            try:
                os.remove(model_path)
                print("检测到损坏的模型文件，自动删除重新下载...")
                break
            except PermissionError:
                time.sleep(1)

# 也检查工作目录中可能存在的损坏文件
if os.path.exists(model_name):
    try:
        with zipfile.ZipFile(model_name) as _zf:
            pass
    except zipfile.BadZipFile:
        # 多试几次删除（可能被杀软或前一进程锁定）
        for _ in range(5):
            try:
                os.remove(model_name)
                print("检测到损坏的模型文件，已删除")
                break
            except PermissionError:
                time.sleep(1)

if not os.path.exists(model_path):
    model = YOLO({self.pretrained_path!r})
    if os.path.exists(model_name):
        shutil.move(model_name, model_path)
else:
    model = YOLO(model_path)

results = model.train(
    data={self.data_yaml_path!r},
    project=os.path.join({self.params["save_path"]!r}, "train"),
    name={self.params["exp_name"]!r},
    epochs={self.params["epochs"]},
    batch={self.params["batch"]},
    imgsz={self.params["imgsz"]},
    device={self.params["device"]!r},
    workers={self.params["workers"]},
    lr0={self.params["lr0"]},
    patience={self.params["patience"]},
    verbose=True,
)
print("__TRAIN_DONE__")
metrics = model.val()
print(f"__METRICS__ mAP50={{metrics.box.map50:.4f}} mAP50-95={{metrics.box.map:.4f}}")
save_dir = getattr(model.trainer, 'save_dir', '') if hasattr(model, 'trainer') else ''
if save_dir:
    best = os.path.join(save_dir, "weights", "best.pt")
    if os.path.exists(best):
        print(f"__BEST__{{best}}")
print("__ALL_DONE__")
'''

    def _on_stdout(self):
        """处理子进程的标准输出，合并 \r 进度更新到进度条。"""
        raw = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        self._output_buffer += raw

        # 按 \n 分割，处理每一行（下载进度用 \r 同行刷新）
        while "\n" in self._output_buffer:
            idx = self._output_buffer.index("\n")
            line = self._output_buffer[:idx].strip()
            self._output_buffer = self._output_buffer[idx + 1:]

            if not line:
                continue

            # 训练/下载进度 → 更新进度条
            m_pct = re.search(r"(\d+)%", line)
            if m_pct and ("Downloading" in line or "Epoch" in line):
                self.progress_signal.emit(int(m_pct.group(1)))
            m_epoch = re.search(r"Epoch\s+(\d+)/(\d+)", line)
            if m_epoch:
                self.progress_signal.emit(int(int(m_epoch.group(1)) / int(m_epoch.group(2)) * 100))

            # 过滤特殊标记
            for tag in ("__TRAIN_DONE__", "__ALL_DONE__", "__METRICS__", "__BEST__"):
                line = line.replace(tag, "")

            if line.strip():
                self.log_signal.emit(line + "\n")

    def _on_finished(self, script_path):
        """子进程结束回调。"""
        # 清理临时脚本
        try:
            os.remove(script_path)
        except OSError:
            pass

        exit_code = self.process.exitCode() if self.process else -1
        if exit_code == 0:
            self.progress_signal.emit(100)
            self.finished_signal.emit(True, "训练完成")
        else:
            self.finished_signal.emit(False, f"进程退出, code={exit_code}")

    def stop(self):
        """停止训练进程。"""
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.kill()
            self.process.waitForFinished(3000)
            self.log_signal.emit("\n⚠️ 训练已手动停止\n")
            self.finished_signal.emit(False, "已停止")


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

        # ── 模型保存位置 ──
        save_group = QGroupBox("模型保存位置")
        save_layout = QVBoxLayout(save_group)
        save_row = QHBoxLayout()
        default_weights = os.path.join(find_project_root(), "weights")
        self.save_path = QLineEdit(default_weights)
        self.save_path.setPlaceholderText("模型文件下载和训练输出目录...")
        btn_save_browse = QPushButton("浏览")
        btn_save_browse.clicked.connect(self._browse_save_path)
        save_row.addWidget(self.save_path, 1)
        save_row.addWidget(btn_save_browse)
        save_layout.addLayout(save_row)
        layout.addWidget(save_group)

        # ── 基础模型 ──
        model_group = QGroupBox("基础模型")
        model_layout = QFormLayout(model_group)

        self.model_combo = QComboBox()
        model_layout.addRow("预训练模型:", self.model_combo)

        layout.addWidget(model_group)

        # ── 实验命名 ──
        name_group = QGroupBox("实验命名")
        name_layout = QFormLayout(name_group)
        self.exp_name = QLineEdit()
        self.exp_name.setPlaceholderText("留空自动使用时间戳")
        name_layout.addRow("实验名称:", self.exp_name)
        layout.addWidget(name_group)

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

    def _browse_save_path(self):
        """选择模型保存目录。"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择模型保存目录")
        if dir_path:
            self.save_path.setText(dir_path)

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

        exp_name = self.exp_name.text().strip() or datetime.now().strftime("%m%d_%H%M")
        save_path = self.save_path.text().strip()
        if not save_path:
            save_path = os.path.join(find_project_root(), "weights")
        params = {
            "exp_name": exp_name,
            "save_path": save_path,
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
        self.log_output.insertPlainText("正在启动训练进程...\n")

    def _stop_training(self):
        """停止训练。"""
        if self.worker:
            self.worker.stop()
            self._on_log("\n⚠️ 用户手动停止训练\n")
            self._on_finished(False, "已停止")

    def _on_log(self, text):
        self.log_output.insertPlainText(text)
        self.log_output.moveCursor(QTextCursor.End)

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
        save_path = self.save_path.text().strip()
        if not save_path:
            save_path = os.path.join(find_project_root(), "weights")
        train_dir = os.path.join(save_path, "train")
        if os.path.exists(train_dir):
            os.startfile(train_dir)
        else:
            QMessageBox.information(self, "提示", "尚未进行训练，训练目录不存在")
