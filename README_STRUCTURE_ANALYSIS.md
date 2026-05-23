# LabelPaw 项目结构全面分析

> 本文档是对项目的完整分析，供修改 README 时参考。
> 创建日期：2026-05-20

---

## 一、项目概述

### 1.1 项目定位

**LabelPaw** 是一个基于 **PySide6 (Qt for Python)** 的智能图像标注系统，集成 **SAM2/SAM3/YOLO** 三大视觉模型，提供 AI 辅助的图像标注能力。

### 1.2 核心价值

- 用 AI 辅助替代纯手动标注，效率提升约 10 倍
- 一站式解决方案：标注 + 格式转换 + 数据集切分
- 支持多种标注格式和多种标注模式

---

## 二、目录结构详解

```
LabelPaw/
│
├── main.py                          ★ 程序入口
├── main_dataset_tool.py             ★ 数据集处理工具独立窗口
├── update_templates.py              ★ 骨架模板数据迁移脚本
│
├── requirements.txt                 ★ Python 依赖清单
├── requirements1.txt                ★ (备用依赖清单)
│
├── core/                            ★★★ 核心逻辑层
│   ├── __init__.py
│   ├── canvas.py                    ★★★ 画布场景 (核心交互)
│   ├── shapes.py                    ★★★ 所有标注形状类
│   ├── sam_client.py                ★★★ SAM 模型加载与推理
│   ├── yolo_predictor.py            ★★★ YOLO 推理封装
│   ├── exporter.py                  ★★★ 标注数据导出
│   ├── pose_template.py             ★★★ 骨架模板管理
│   ├── translations.py              ★ 关键点名称翻译
│   ├── geometry.py                  ★ 几何计算工具
│   └── config/                      ★ 骨架模板 JSON
│       ├── person.json              COCO 17点人体
│       ├── hand.json                21点手部
│       ├── face.json                68点面部
│       ├── rectangle.json           4点矩形
│       └── triangle.json            3点三角形
│
├── ui/                              ★★★ UI 层
│   ├── __init__.py
│   ├── main_window.py               ★★★ UI 布局 (QMainWindow)
│   ├── theme.py                     ★★ 亮色/暗黑主题 QSS 样式
│   ├── style.qss                    ★ 额外样式表
│   ├── template_dialog.py           ★★ 骨架模板编辑对话框
│   ├── train_dialog.py              ★★ YOLO 训练对话框
│   ├── model_selector_dialog.py     ★ 模型选择弹窗
│   ├── author_info.py               ★ 作者信息弹窗
│   └── icon/                        ★ 图标资源
│       ├── logo.png                 应用 Logo
│       ├── Loading.gif              加载动画
│       ├── *.svg                    功能图标 (18个)
│       └── ... 
│
├── utils/                           ★ 工具模块
│   ├── __init__.py
│   └── message.py                   ★★ DialogOver 通知组件
│
├── weights/                         ★ 模型权重目录
│   ├── sam_weights/                 SAM 系列 (.pt)
│   ├── yolo26_weights/              YOLO26 系列 (.pt)
│   └── yolov8_weights/              YOLOv8 系列 (.pt)
│
├── assets/                          ★ README 截图
│   ├── logo.png
│   ├── img_1.png ~ img_16.png       (15张截图)
│   └── ...
│
├── 01_json_to_unet.py               ★ 工具: JSON 标注转 U-Net Mask
├── 02_split_yolo_dataset.py         ★ 工具: YOLO 数据集随机切分
├── 03_convert_and_split_yolo.py     ★ 工具: JSON/XML 转 YOLO 并切分
│
├── LICENSE                          GPL-3.0
├── SAM_LICENSE.txt                  SAM 模型额外许可证
├── output_3_masks.png               示例输出
│
├── .gitignore
├── .idea/                           PyCharm 配置
│
├── README.md                        ★ 英文 README
└── README_zh-CN.md                  ★ 中文 README (待修改)
```

---

## 三、核心模块逐文件分析

### 3.1 `main.py` (1467 行) — 主控窗口

**角色**：程序入口，事件中枢，所有功能的调度器。

**关键类**：`MainWindow(QMainWindow, Ui_MainWindow)`

**核心职责**：

| 职责 | 相关方法 | 说明 |
|------|----------|------|
| 模型管理 | `_init_model_selector()`, `on_model_selected()` | SAM/YOLO 模型加载切换 |
| 标注模式 | `_set_mode()` | 矩形/多边形/关键点/OBB 切换 |
| 文件浏览 | `open_dir()`, `on_file_selected()` | 图片目录选择、文件列表切换 |
| 标注管理 | `save_annotation()`, `load_annotations()`, `auto_save_annotation()` | 三种格式的读写 |
| 撤销重做 | `push_state()`, `undo()`, `redo()`, `restore_state()` | 20 步历史栈 |
| 智能辅助 | `on_sam_toggled()`, `trigger_sam_prompt()` | SAM 开关、文本提示 |
| YOLO 预测 | `on_predict_clicked()`, `on_predict_finished()` | YOLO 异步推理 |
| 类别管理 | `add_class_to_list()`, `edit_shape_label()`, `on_list_item_changed()` | 分类列表及批量改名 |
| 主题切换 | `toggle_theme()` | 亮色/暗黑 |
| 快捷键 | `keyPressEvent()` | 全部快捷键分发 |
| 数据集工具 | `open_dataset_tool()` | 启动独立数据集工具窗口 |

**信号流**：
```
用户操作 → keyPressEvent / 按钮点击
  → _set_mode() → canvas.set_mode()
  → on_sam_toggled() → canvas.set_sam_enabled()
  → on_predict_clicked() → YoloPredictorWorker (QThread)
  → push_state() → undo_stack[]
```

**撤销重做机制**：
- 每次 `state_changed` 信号触发时，`Exporter.extract_shapes()` 拍快照
- 快照存入 `undo_stack` (最大 20 步)
- `undo()` 将当前状态移入 `redo_stack`，还原上一步快照
- `restore_state()` 完全重建画布元素

### 3.2 `core/canvas.py` (464 行) — 画布场景

**角色**：图形交互核心，处理所有鼠标事件和绘制逻辑。

**关键类**：`Canvas(QGraphicsScene)`, `CanvasMode`

**标注模式枚举**：

| 模式 | 值 | 描述 |
|------|----|------|
| `EDIT` | 0 | 编辑模式 |
| `RECT` | 1 | 矩形标注 |
| `POLY` | 2 | 多边形标注 |
| `POINT` | 3 | 关键点标注 |
| `RBOX` | 4 | 旋转框标注 |

**画布元素层次**：

```
QGraphicsScene
├── QGraphicsPixmapItem (img_item)     ← 背景图片
├── QGraphicsLineItem (h_line)         ← 水平十字线
├── QGraphicsLineItem (v_line)         ← 垂直十字线
├── QGraphicsRectItem (sam_hover_item) ← SAM 悬停预览 (临时)
├── RectShape / PolyShape / ...        ← 用户标注 (持久)
│   ├── QGraphicsTextItem (label_text) ← 标签文字
│   └── HandleItem[]                   ← 编辑手柄
└── PoseShape (pose_preview_item)     ← 骨架模板预览 (临时)
```

**鼠标事件流**：

```
mouseMoveEvent
  ├── 更新十字线 + 坐标信号
  ├── POINT 模式 → 骨架模板预览跟随鼠标
  ├── SAM 开启 → 调用 sam_client.request_inference() 悬停推理
  └── 绘制中 → 更新 temp_item (拖拽预览)

mousePressEvent
  ├── SAM 开启 → 调用 sam_client.request_inference(is_click=True)
  ├── 点击到已有图形 → 选中/编辑
  ├── 点击空白 → 取消选中
  └── 开始新绘制 → 记录 start_pt / poly_pts

mouseReleaseEvent
  └── 完成绘制 → 发射 shape_drawn 信号

mouseDoubleClickEvent
  ├── 双击已有图形 → 发射 shape_double_clicked 信号
  └── POLY 模式 → 闭合多边形
```

### 3.3 `core/shapes.py` (1248 行) — 标注图形

**角色**：定义所有可标注的图形类型及其交互行为。

**类层次**：

```
BaseShape (Mixin)
  ├── setup_style()      设置画笔/画刷/标志
  ├── setup_label()      标签文字
  ├── update_label_visibility()  悬停/选中时显示
  └── apply_hover_enter/leave()  悬停样式

RectShape(QGraphicsRectItem, BaseShape)        ← 矩形
  ├── lt/rt/lb/rb_handle (HandleItem)          四个角手柄
  └── update_from_handle()                     拖拽手柄更新形状

PolyShape(QGraphicsPolygonItem, BaseShape)      ← 多边形
  ├── handles[] (HandleItem)                    每个顶点有手柄
  ├── ghost_handle                              悬停时边中点预览
  ├── 支持边插入新顶点 (点选边中间 → 拖拽)
  └── remove_handle()                           右键删除顶点

PointShape(QGraphicsEllipseItem, BaseShape)     ← 点

RotatedRectShape(QGraphicsObject, BaseShape)    ← 旋转框 OBB
  ├── top/bottom/left/right/rotate 手柄
  ├── handle_dragged()                         拖拽手柄更新
  └── polygon() → 4 个场景坐标顶点

PoseShape(QGraphicsObject, BaseShape)           ← 关键点骨架
  ├── kps[] (KeypointHandle)                   关键点手柄
  ├── lines[] (line + p1/p2 索引)              骨架连接线
  ├── top/bottom/left/right/tl/tr/bl/br/rotate 9 个手柄
  ├── handle_dragged()                         缩放/旋转
  ├── set_hover_state()                        悬停/选中交互
  └── update_bounding_box()                    自动适配关键点边界

--- 辅助类 ---
HandleItem(QGraphicsEllipseItem)               ← 通用编辑手柄
  ├── 四边形角点拖拽
  └── 单击可删除 (多边形顶点)

KeypointHandle(QGraphicsEllipseItem)           ← 关键点手柄
  ├── 右键菜单设置可见性 (visible=2/occluded=1/hidden=0)
  ├── ToolTip 显示中文名称
  └── 仅编辑模式下可拖拽

OBBHandle(QGraphicsItem)                       ← OBB 控制手柄
  ├── 胶囊形 (top/bottom) / 竖胶囊 (left/right) / 圆形 (rotate)
  └── 自定义 paint() 渲染
```

**YOLO 格式规范**：
- 检测: `class_id cx cy w h` (归一化)
- OBB: `class_id x1 y1 x2 y2 x3 y3 x4 y4` (归一化)
- Pose: `class_id cx cy w h kp1x kp1y kp1v ...`
- Segment: `class_id x1 y1 x2 y2 ...`

### 3.4 `core/sam_client.py` (496 行) — SAM 模型客户端

**角色**：管理 SAM 模型的异步加载和推理。

**多线程架构**：

```
SAMClient (QObject, 主线程)
  │
  ├── Sam3ModelLoadWorker (QThread)     ← SAM3 模型加载
  │     └── loaded → _on_sam3_loaded
  │
  ├── Sam2ModelLoadWorker (QThread)     ← SAM2 模型加载  
  │     └── loaded → _on_sam2_loaded
  │
  ├── Sam3InferenceWorker (QThread)     ← SAM3 推理循环
  │     ├── task_queue (Queue, maxsize=1)
  │     ├── request_inference(x, y, is_click) → point 任务
  │     └── request_text_inference(prompt)     → text 任务
  │
  └── Sam2InferenceWorker (QThread)     ← SAM2 推理循环
        └── request_inference(x, y, is_click)
```

**模型发现机制**：
- 扫描 `weights/sam_weights/` 目录下的 `.pt` 文件
- 按文件名自动识别 SAM3 / SAM2.1 及对应配置
- 显示模型文件大小（MB/GB）

**支持的特性**：

| 模型 | 点击分割 | 文本提示 |
|------|---------|---------|
| SAM2.1 | ✅ | ❌ |
| SAM3 | ✅ | ✅ |

**推理结果处理**：
- 掩膜 → `cv2.findContours` → 多边形近似
- `cv2.boundingRect` → 外接矩形
- `cv2.minAreaRect` → 旋转框 OBB (角度 + 中心 + 宽高)

### 3.5 `core/yolo_predictor.py` (201 行) — YOLO 推理

**角色**：封装 Ultralytics YOLO 模型的推理逻辑。

**类结构**：

```
YoloPredictor
  ├── task: detect | segment | pose | obb
  ├── skeleton: 骨架连接定义 (pose 任务)
  ├── kpt_names: 关键点名称列表 (pose 任务)
  └── predict_sync(image_path)
       └── → shapes[]

YoloPredictorWorker(QThread)            ← 异步 Worker
  ├── finished → on_predict_finished()
  └── error → on_predict_error()
```

**YOLO 任务类型映射**：

| YOLO 任务 | 自动切换的标注模式 |
|-----------|-------------------|
| `detect` | 矩形 (Rect) |
| `segment` | 多边形 (Poly) |
| `pose` | 关键点 (Point) |
| `obb` | 旋转框 (RBOX) |

**去重机制 (IoU)**：
- 新预测结果与已有标注计算 IoU
- IoU > 0.8 判定为重复，跳过
- 有效减少重复标注

### 3.6 `core/exporter.py` (210 行) — 数据导出

**角色**：将画布标注序列化为文件。

**输出格式**：

| 格式 | 方法 | 文件扩展名 | 说明 |
|------|------|-----------|------|
| JSON | `save_json()` | `.json` | labelme 格式兼容 |
| YOLO | `save_yolo()` | `.txt` | 检测/分割/姿态/OBB |
| XML | `save_xml()` | `.xml` | Pascal VOC 格式 |

**导出数据类型**：
- rectangle → JSON/XML/YOLO
- polygon → JSON/YOLO
- pose → JSON/YOLO (归一化关键点坐标)
- obb → JSON/YOLO (4点或中心+宽高+角度)
- point → YOLO (微小框模拟)

**解析/导入逻辑 (`main.py`)**：
- `_load_json()` — labelme JSON → shape 对象
- `_load_yolo()` — 自动识别检测/OBB/姿态/分割格式
- `_load_xml()` — Pascal VOC → 矩形标注

### 3.7 `core/pose_template.py` (744 行) — 骨架模板

**角色**：定义和管理关键点骨架模板。

**内置模板集合**：

| 模板名 | 关键点数 | 应用场景 |
|--------|---------|---------|
| Person (COCO) | 17 | 人体姿态估计 |
| Hand | 21 | 手部关键点 |
| Face (68 pts) | 68 | 面部特征点 |
| Rectangle | 4 | 通用矩形模板 |
| Triangle | 3 | 通用三角形模板 |

**模板生命周期**：
- 初始化时从 `core/config/*.json` 加载
- 无配置文件时使用 `DEFAULT_TEMPLATES` 回退
- 通过 `TemplateManager` 进行 CRUD 操作
- 保存为独立 JSON 文件到 `core/config/`

### 3.8 `main_dataset_tool.py` — 数据集处理

**角色**：独立的批量数据处理工具窗口。

**功能**：
- JSON → YOLO 格式转换
- JSON/XML → YOLO 格式转换
- 按比例随机划分 train/val/test 集
- 自动生成 `data.yaml`

**多线程**：`DatasetWorker(QThread)` 异步处理，通过信号更新 UI 日志

### 3.9 `utils/message.py` (250 行) — 通知组件

**角色**：美观的 Toast 通知组件。

**特性**：
- 四种类型：success / warning / danger / info
- 右上角堆叠显示，最多 7 个同时存在
- 滑入动画 (OutBack)
- 淡出动画 (3s 后自动消失)
- 无边框 + 透明背景 + 阴影

### 3.10 `ui/theme.py` — 主题系统

**角色**：亮色/暗黑主题样式。

**实现方式**：字符串形式的 QSS（Qt Style Sheets）
- `DARK_THEME` — 暗色主题 (深蓝底色 #020617)
- `LIGHT_THEME` — 亮色主题
- 通过 `setStyleSheet()` 动态切换

### 3.11 工具脚本

| 脚本 | 功能 |
|------|------|
| `01_json_to_unet.py` | 读取 JSON 标注，为每个类别生成独立 Mask，按 YOLO 目录结构组织 |
| `02_split_yolo_dataset.py` | 将 YOLO 格式数据集按比例随机切分 train/val/test |
| `03_convert_and_split_yolo.py` | 先转换 JSON/XML 为 YOLO 格式，再随机切分 |
| `update_templates.py` | 将旧版 `pose_templates.json` 迁移为带 `kpt_shape` 的新格式 |

---

## 四、关键架构决策

### 4.1 为什么要用多线程

- SAM/SAM2 推理是 GPU 密集型操作，同步执行会阻塞 UI
- 每个模型有独立的 `ModelLoadWorker` + `InferenceWorker`
- 推理请求通过 `queue.Queue` 传递，保证串行处理

### 4.2 标注格式支持策略

- **内存中**：统一使用 `Exporter.extract_shapes()` 的字典格式
- **文件 I/O**：读写时由 `save_*` / `_load_*` 方法做格式转换
- **切换格式时**：清空画布 → 用新格式的加载器重新加载

### 4.3 撤销/重做实现

- 完整快照模式：保存当前所有标注的状态快照
- 快照内容 = `Exporter.extract_shapes()` 的输出
- `restore_state()` 完全重建所有 shape 对象
- 性能局限：复杂标注（如 68 点面部）较多时快照较大

### 4.4 自动保存机制

- 切换到下一张图片时：`on_file_selected()` 中调用 `auto_save_annotation()`
- 修改标注后：`push_state()` 中自动保存
- 关闭程序时：`closeEvent()` 中自动保存

### 4.5 模型路径发现机制

- 可执行文件模式: `os.path.dirname(sys.executable)` + `/weights/`
- 源码模式: `__file__` 上一级 + `/weights/`
- 硬编码备用: `HARDCODED_DEV_DIR` (需手动修改)
- SAM 模型: 自动扫描 `sam_weights/`
- YOLO 模型: 自动扫描 `yolo*_weights/`

---

## 五、依赖清单分析

### 必须依赖

| 包 | 用途 | 版本要求 |
|----|------|---------|
| PySide6 | Qt GUI 框架 | ~=6.4.2 |
| torch | 深度学习框架 | >=2.5.0 |
| numpy | 数值计算 | >=1.26, <2 |
| opencv-python | 图像处理、轮廓提取 | ~=4.11.0 |
| pillow | 图像加载 | ~=10.4.0 |
| ultralytics | YOLO 模型 | (pip 安装) |

### SAM 依赖

| 包 | 来源 | 用途 |
|----|------|------|
| sam2 | GitHub | SAM2 模型 |
| sam3 | GitHub | SAM3 模型 |

### 辅助依赖

| 包 | 用途 |
|----|------|
| einops | 张量操作 |
| pycocotools | COCO 评估工具 |
| scipy | 科学计算 |
| tqdm | 进度条 |
| matplotlib | 可视化 |
| timm | 模型库 |
| ftfy | 文本修复 |
| psutil | 系统监控 |
| omegaconf | 配置管理 |
| scikit-learn | 机器学习工具 |

---

## 六、README 章节建议

基于以上分析，建议 README_zh-CN.md 包含以下章节：

1. **项目标题 + Logo + 简介**（一句话定位）
2. **核心功能清单**（Feature 列表，配图标）
3. **界面演示截图**（表格形式，功能 vs 截图）
4. **技术架构**（目录树 + 数据流图 + 模块关系）
5. **快速开始**（pip 安装命令，非源码编译指导）
6. **模型下载**（模型链接 + 目录结构示范）
7. **用户操作指南**（基本工作流 + 快捷键表格）
8. **标注格式说明**（三种格式的规范对比）
9. **数据集处理工具**（脚本清单和使用方法）
10. **常见问题 FAQ**（GPU/显存/安装错误等）
11. **开发指南**（如何扩展新模型/新标注形状）
12. **许可证 + 引用**

---

## 七、注意点

- 英文 README (`README.md`) 比中文版简短，建议保持内容一致
- 注意事项：
  - 国内用户安装 GitHub 依赖可能需要代理或镜像
  - 无 GPU 用户建议用 YOLO 而非 SAM
  - 引用部分需保留模型作者的 bibtex
