<div align="center">
  <p>
    <a href="https://github.com/luohuabuxiema/LabelPaw" target="_blank">
      <img alt="LabelPaw" width="200" src="assets/logo.png"></a>
  </p>
  <a href="README.md">English</a> | <a href="README_zh-CN.md">简体中文</a>
</div>

<h1 align="center">🐾 LabelPaw - Intelligent Image Annotation System v2.0.0</h1>

<p align="center">
  <strong>AI-powered annotation — 10x efficiency</strong>
  <br>
  Built on PySide6 · SAM2 · SAM3 · Ultralytics YOLO
</p>

---

## 📖 Other Documentation

| Document | Description |
|----------|-------------|
| [简体中文版 README](README_zh-CN.md) | 中文文档 |
| [Project Architecture Analysis](docs/项目结构分析.md) | Full architecture, data flow, file dependency graph (中文) |
| [Structure Analysis](README_STRUCTURE_ANALYSIS.md) | Code-level directory analysis and chapter suggestions |

---

## 📋 Table of Contents

- [Foreword](#-foreword)
- [System Introduction](#-system-introduction)
- [Core Features](#-core-features)
- [Quick Start](#-quick-start)
- [Model Download](#-model-download)
- [User Operation Guide](#-user-operation-guide)
- [Project Architecture](#-project-architecture)
- [Changelog](#-changelog)
- [FAQ](#-faq)
- [Development](#-development)
- [License & Citation](#-license--citation)

---

## 📌 Foreword

**Defeat AI with AI!** Due to the need for dataset annotation in a project, I previously used tools like labelme and labelimg. Therefore, I decided to integrate excellent vision models like SAM2, SAM3, and YOLO pose estimation to develop a smarter and more efficient annotation tool. After multiple iterations, the system has welcomed the brand-new **version 2.0.0**!

Source Code: [https://github.com/luohuabuxiema/LabelPaw](https://github.com/luohuabuxiema/LabelPaw)

---

## 🎯 System Introduction

The system is built on **PySide6** and integrates **SAM2**, **SAM3**, and **Ultralytics YOLO** vision models, providing comprehensive AI-assisted image annotation:

- **Intelligent Point-and-Click & Prompt Segmentation**: When SAM is enabled, supports rapid object extraction in polygon, rectangle, and OBB modes.
- **Keypoint Skeleton Templates & AI Annotation**: Built-in templates for humans (COCO 17pts), hands (21pts), and faces (68pts). Customizable templates. YOLO pose models support automatic keypoint detection and skeleton connection.

| Feature | Screenshot |
|---------|-----------|
| Polygon Annotation | ![Polygon](assets/img_1.png) |
| OBB Intelligent Annotation | ![OBB](assets/img_2.png) |
| Rectangle Intelligent Annotation | ![Rectangle](assets/img_3.png) |
| Keypoint Annotation | ![Keypoint](assets/img_10.png) |
| YOLO Keypoint Detection | ![YOLO Pose](assets/img_14.png) |
| Built-in Skeleton Templates | ![Templates](assets/img_11.png) |
| Face (68 keypoints) | ![Face](assets/img_13.png) |
| Hand (21 keypoints) | ![Hand](assets/img_16.png) |
| Custom Template Editor | ![Custom Template](assets/img_12.png) |
| Dark Theme | ![Dark Theme](assets/img_15.png) |
| Dataset Processing Tool | ![Dataset Tool](assets/img_6.png) |

---

## ✨ Core Features

- **🤖 AI-Powered (SAM2/SAM3)**: Hover preview, single-point contour extraction, text prompt driven full-image segmentation.
- **🦴 Keypoint Pose (YOLO-driven)**: Intelligent keypoint detection with auto-skeleton connection. Built-in COCO (17pts), Face (68pts), Hand (21pts) templates. Customizable skeleton templates.
- **📐 Versatile Annotation**: Rectangle, Polygon, Point, OBB (rotated box), and Pose (skeleton keypoints).
- **🔄 Ultimate OBB**: Custom drag handles with 360° smooth rotation.
- **💾 Multi-Format Export**: JSON (LabelMe compatible), YOLO (.txt), XML (Pascal VOC). One-click U-Net mask generation.
- **🗄️ Dataset Processing**: Format conversion and train/val/test splitting.
- **🎯 YOLO Model Training**: Built-in training dialog with dataset validation, model download, and GPU/CPU training
- **🔄 Transfer Learning**: Load pretrained models or previous training checkpoints to continue training
- **⚙️ Full Training Controls**: Epochs, batch size, learning rate, optimizer (SGD/Adam/AdamW), augmentation (mosaic, mixup, HSV jitter, geometric transforms)
- **🎨 Dual Theme**: Light and Dark themes.
- **↩️ Undo/Redo**: 20-step history with full state snapshots.

---

## 🚀 Quick Start

### 1. Environment

Recommended **Python 3.10+**. Create a virtual environment:

```bash
conda create -n py311 python==3.11.5
conda activate py311
```

### 2. Install PyTorch

> **Check CUDA version**: Run `nvidia-smi` in terminal, look for **CUDA Version** in the top-right.

**CUDA 11.8** (Alibaba Cloud mirror for China users):
```bash
pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 -f https://mirrors.aliyun.com/pytorch-wheels/cu118
```

**Verify installation**:
```python
import torch
print(torch.__version__)
print(torch.cuda.is_available())  # Must be True
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Key dependencies: `pyside6~=6.4.2`, `torch>=2.5.0`, `opencv-python`, `ultralytics`, `sam2`, `sam3`.

### 4. Install AI Models (pip)

```bash
pip install git+https://github.com/facebookresearch/sam2.git
pip install git+https://github.com/facebookresearch/sam3.git
pip install ultralytics
```

> **Network issues in China?** Download the source code ZIP from each GitHub repo, extract the core folders (`sam2/`, `sam3/`, `ultralytics/`) into the `LabelPaw/` root directory.

### 5. Run

```bash
python main.py
```

> **No GPU?** Use YOLO lightweight models (with "n" suffix). SAM models require significant GPU memory.

---

## 📦 Model Download

Place downloaded `.pt` weight files into the following structure:

```
weights/
  ├── sam_weights/               ← SAM models
  │   ├── sam3.pt                (3.5GB)
  │   ├── sam2.1_hiera_tiny.pt
  │   ├── sam2.1_hiera_small.pt
  │   ├── sam2.1_hiera_base_plus.pt
  │   └── sam2.1_hiera_large.pt
  ├── yolo26_weights/            ← YOLO models (custom)
  │   └── yolo26n-pose.pt
  └── yolov8_weights/
```

**SAM 2.1 Downloads**:
- [Tiny](https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt)
- [Small](https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_small.pt)
- [Base+](https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt)
- [Large](https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt)

**Custom weight path**: Modify `HARDCODED_DEV_DIR` in `main.py`, `core/sam_client.py`, and `ui/model_selector_dialog.py` if your `weights/` directory is in a different location.

---

## 📖 User Operation Guide

### Basic Workflow

1. **Open Directory** — Select the image folder
2. **Select Format** — Left sidebar dropdown: JSON / YOLO / XML
3. **Annotation Mode** — Left toolbar: Rect, Polygon, OBB, Keypoint (or shortcuts)
4. **AI Assistance** — Toggle SAM switch (Shortcut: `Q`). SAM3 supports text prompts (e.g., type "dog" to auto-extract)
5. **YOLO Prediction** — Switch to any YOLO model via the model selector, click the ⚡ button
6. **Keypoint/Skeleton** — Select keypoint mode, choose a built-in template or customize your own
7. **Dataset Processing** — Click "Dataset Processing" for format conversion / splitting / U-Net mask generation
8. **YOLO Model Training** — Click "模型训练" in the left toolbar to open the training dialog. Select your dataset directory (must contain `data.yaml`), choose a pretrained model or local checkpoint, configure hyperparameters, and click "开始训练". Training runs in a separate process with real-time log output and progress bar. The trained model (`best.pt`) is saved to `{save_path}/train/{exp_name}/`.

### ⌨️ Shortcuts

| Key | Action |
|-----|--------|
| `A` / `←` | Previous image |
| `D` / `→` | Next image |
| `Ctrl + S` | Save annotation |
| `Ctrl + Z` | Undo (20 steps) |
| `Ctrl + Y` | Redo |
| `Q` | Toggle SAM |
| `R` | Rectangle mode |
| `P` | Polygon mode |
| `T` | Keypoint mode |
| `O` | OBB (rotated box) mode |
| `M` | YOLO predict |
| `E` | Edit label |
| `Del`| Delete selected |
| `F1` | Help dialog |
| **Polygon** | |
| Left-click | Add vertex |
| `Ctrl + Z` | Undo vertex |
| Double-click | Close polygon |
| **OBB Fine-tune** | |
| `Z` / `V` | Rotate ±5° |
| `X` / `C` | Rotate ±1° |

---

## 🏗️ Project Architecture

```
LabelPaw/
├── main.py                        # Entry point, main controller
├── main_dataset_tool.py           # Dataset processing tool
├── core/                          # Core logic layer
│   ├── canvas.py                  # Annotation canvas (QGraphicsScene)
│   ├── shapes.py                  # All annotation shapes
│   ├── sam_client.py              # SAM2/SAM3 model client
│   ├── yolo_predictor.py          # YOLO inference engine
│   ├── exporter.py                # JSON/YOLO/XML export
│   ├── pose_template.py           # Skeleton template manager
│   ├── translations.py            # Keypoint name translations
│   └── geometry.py                # Geometric utilities
├── ui/                            # UI layer
│   ├── main_window.ui             # Qt Designer layout source
│   ├── ui_main_window.py          # Generated (pyside6-uic)
│   ├── main_window.py             # Custom widgets
│   ├── resources.qrc              # Resource collection
│   ├── resources_rc.py            # Compiled resources
│   ├── theme.py                   # Dark/Light theme QSS
│   ├── template_dialog.py         # Skeleton template editor
│   ├── model_selector_dialog.py   # Model picker dialog
│   ├── train_dialog.py            # YOLO training dialog
│   └── author_info.py             # About dialog
├── utils/
│   └── message.py                 # Toast notification (DialogOver)
└── weights/                       # Model weights directory
```

**Key Design Decisions**:
- **UI in .ui files**: Layouts are designed in Qt Designer, compiled via `pyside6-uic`
- **Qt Resource System**: Icons and styles managed via `.qrc`, compiled via `pyside6-rcc`
- **Multi-threaded inference**: SAM/YOLO run in `QThread` to prevent UI blocking
- **Lazy imports**: `triton` and `sam3` imported inside QThread to avoid DLL conflicts
- **Snapshot undo**: Full state snapshots (20 max) rebuilt from stored data
- **SVG icon tinting**: Icons recolored at runtime via `QPainter` for theme support

> For the full architecture analysis including detailed data flows and class hierarchy, see [docs/项目结构分析.md](docs/项目结构分析.md) (Chinese).

---

## 📜 Changelog

| Date | Changes |
|------|---------|
| 2026-05-23 | Refactored UI to `.ui` + `pyside6-uic` pattern; added `.qrc` resource system |
| 2026-05-23 | Added YOLO model training: dialog, hyperparameter config, GPU/CPU fallback, transfer learning |
| 2026-05-22 | Fixed SAM3 triton DLL compatibility on Windows |
| 2026-05-15 | Added face/hand/person keypoint templates; customizable skeleton connections |
| 2026-05-14 | Integrated SAM2.1; integrated Ultralytics YOLO (detect/segment/pose/OBB) |
| 2026-05-13 | JSON/XML/YOLO inter-conversion; U-Net mask generation; dataset splitting |
| 2026-05-10 | Light/Dark theme support |
| 2026-04-12 | First PySide6-based annotation interface release |
| 2026-04-10 | Integrated SAM3: hover preview, point-click, text prompt segmentation |
| 2026-04-09 | Rectangle, Polygon, Point annotation; OBB rotation handle with 360° control |
| 2026-04-08 | Native JSON, YOLO .txt, XML (Pascal VOC) export |

---

## ❓ FAQ

**Q: SAM3 won't load / `triton` DLL error?**  
A: On Windows, `import triton` must happen before `import PySide6`. This is already handled in `main.py`. If the error persists, try `pip install triton-windows`.

**Q: Training fails with "CUDA unavailable" on a CUDA-capable system?**  
A: QProcess subprocesses inherit the parent environment. Ensure CUDA paths are in your system PATH. The training script automatically falls back to CPU if CUDA is not detected in the subprocess.

**Q: Training crashes with "page file too small"?**  
A: Reduce the `workers` parameter (try 0 or 2). High worker counts cause multiple CUDA DLL loads that can exhaust Windows virtual memory.

**Q: pyside6-uic not found?**  
A: Run `pyside6-uic` via full path: `<venv>/Scripts/pyside6-uic.exe ui/main_window.ui -o ui/ui_main_window.py`

**Q: Can I run without GPU?**  
A: Yes, but only YOLO models will work. Use lightweight YOLO models (nano/small variants). SAM models require a CUDA-compatible GPU.

**Q: How to add a new YOLO model?**  
A: Download the `.pt` file into a `weights/yoloXXX_weights/` folder. The system scans `yolo*_weights/` directories automatically.

**Q: Icons not showing in Qt Designer?**  
A: The `.ui` file references resources via `resources.qrc`. Run `pyside6-rcc ui/resources.qrc -o ui/resources_rc.py` after adding new icons.

---

## 🤝 Development

The system follows a modular design. The UI layer is cleanly separated from the core logic and model inference.

**Adding a new annotation shape**:
1. Create a new shape class in `core/shapes.py` (extend `BaseShape`)
2. Add export/import logic in `core/exporter.py`
3. Register in `core/canvas.py` for mouse event handling

**Adding a new AI model**:
1. Add model loading/inference logic in `core/sam_client.py` (or create a new client)
2. Register the model in the configuration
3. The model selector and signal wiring in `main.py` will handle the rest

**Modifying UI layout**:
```bash
# Edit in Qt Designer
pyside6-designer ui/main_window.ui

# Recompile
pyside6-uic ui/main_window.ui -o ui/ui_main_window.py

# Recompile resources after icon changes
pyside6-rcc ui/resources.qrc -o ui/resources_rc.py
```

Contributions via Fork and PR are welcome!

---

## 📄 License

This project is licensed under the **GPL-3.0 License**. If you use this code in commercial or non-commercial projects, please comply with this license and open-source your derivative modifications.

### Citation

```bibtex
@misc{LabelPaw,
  year = {2026},
  author = {luohuabuxiema},
  publisher = {Github},
  journal = {Github repository},
  title = {LabelPaw: Intelligent image annotation system},
  howpublished = {\url{https://github.com/luohuabuxiema/LabelPaw}}
}
```

### Acknowledgments & Model Citations

```bibtex
@misc{carion2025sam3segmentconcepts,
      title={SAM 3: Segment Anything with Concepts},
      author={Nicolas Carion et al.},
      year={2025},
      eprint={2511.16719},
      archivePrefix={arXiv},
      primaryClass={cs.CV}
}

@article{ravi2024sam2,
  title={SAM 2: Segment Anything in Images and Videos},
  author={Ravi, Nikhila et al.},
  journal={arXiv preprint arXiv:2408.00714},
  year={2024}
}

@software{ultralytics,
  author = {Glenn Jocher and Ayush Chaurasia and Jing Qiu},
  title = {Ultralytics},
  year = {2023},
  url = {https://github.com/ultralytics/ultralytics}
}
```

---

<p align="center">
  ⭐ If this project helps you, please give it a Star! ⭐
</p>
