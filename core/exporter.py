import json
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from core.shapes import RectShape, PolyShape, PointShape, RotatedRectShape, PoseShape


class Exporter:
    """标注数据导出器，支持多种格式的标注结果输出。

    提供将画布中的标注图形提取为结构化数据，并导出为
    JSON（LabelMe 格式）、YOLO（文本格式）和 Pascal VOC XML 格式的功能。
    支持矩形、多边形、关键点、旋转框（OBB）和骨架（Pose）等标注类型。
    """
    @staticmethod
    def extract_shapes(scene):
        """从画布场景中提取所有非临时标注图形数据。

        遍历场景中的所有图形项，根据类型（矩形、多边形、关键点、
        旋转框、骨架）提取坐标、标签、角度等标注信息，
        并以统一的字典列表格式返回。临时图形（is_temp=True）会被跳过。

        Args:
            scene: QGraphicsScene 画布场景对象。

        Returns:
            标注数据字典列表，每个字典包含 type、label、points 等字段。
        """
        shapes_data = []
        for item in scene.items():
            if isinstance(item, RectShape) and not getattr(item, 'is_temp', False):
                rect = item.rect()
                p1 = item.mapToScene(rect.topLeft())
                p2 = item.mapToScene(rect.bottomRight())
                shapes_data.append({
                    "label": item.label,
                    "type": "rectangle",
                    "points": [[p1.x(), p1.y()], [p2.x(), p2.y()]]
                })
            elif isinstance(item, PoseShape) and not getattr(item, 'is_temp', False):
                # Export pose
                keypoints = []
                for kp in item.kps:
                    pos = kp.scenePos()
                    keypoints.append([pos.x(), pos.y(), kp.visible_state])
                shapes_data.append({
                    "label": item.label,
                    "type": "pose",
                    "points": [],
                    "rect": [item.pos().x(), item.pos().y(), item.box_w, item.box_h],
                    "angle": item.rotation(),
                    "keypoints": keypoints,
                    "kpt_shape": item.template.get("kpt_shape", [len(item.kps), 3]),
                    "template_name": item.template.get("name", "Unknown")
                })
            elif isinstance(item, PolyShape) and not getattr(item, 'is_temp', False):
                poly = item.polygon()
                mapped_poly = item.mapToScene(poly)
                points = [[pt.x(), pt.y()] for pt in mapped_poly]
                shapes_data.append({
                    "label": item.label,
                    "type": "polygon",
                    "points": points
                })
            elif isinstance(item, PointShape) and not getattr(item, 'is_temp', False):
                rect = item.rect()
                shapes_data.append({
                    "label": item.label,
                    "type": "point",
                    "points": [[rect.center().x(), rect.center().y()]]
                })
            elif isinstance(item, RotatedRectShape) and not getattr(item, 'is_temp', False):
                poly = item.polygon()
                points = [[poly[i].x(), poly[i].y()] for i in range(4)]

                cx = item.pos().x()
                cy = item.pos().y()
                w = item.box_w
                h = item.box_h
                angle = item.rotation()

                shapes_data.append({
                    "label": item.label,
                    "type": "obb",
                    "points": points,
                    "rect": [cx, cy, w, h],  # JSON 中保存: [中心X, 中心Y, 宽, 高]
                    "angle": angle
                })
        shapes_data.reverse()
        return shapes_data

    @staticmethod
    def save_json(filepath, image_path, image_width, image_height, shapes):
        """导出标注数据为 JSON 格式（LabelMe 标准格式）。

        生成符合 LabelMe 标注规范（版本 5.2.1）的 JSON 文件，
        支持矩形、多边形、关键点、旋转框（含 angle/rect 字段）
        和骨架（含 keypoints/kpt_shape/template_name 字段）的完整输出。

        Args:
            filepath: 输出文件路径。
            image_path: 原图路径，用于记录文件名。
            image_width: 图片宽度（像素）。
            image_height: 图片高度（像素）。
            shapes: 标注数据字典列表，由 extract_shapes() 生成。
        """
        data = {
            "version": "5.2.1",
            "flags": {},
            "shapes": [],
            "imagePath": os.path.basename(image_path),
            "imageHeight": int(image_height),
            "imageWidth": int(image_width)
        }
        for s in shapes:
            shape_type = s["type"]
            shape_dict = {
                "label": s["label"],
                "points": s["points"],
                "group_id": None,
                "shape_type": shape_type,
                "flags": {}
            }
            if shape_type == "obb":
                shape_dict["angle"] = s.get("angle", 0)
                shape_dict["rect"] = s.get("rect", [0, 0, 0, 0])
            elif shape_type == "pose":
                shape_dict["rect"] = s.get("rect", [0, 0, 0, 0])
                shape_dict["kpt_shape"] = s.get("kpt_shape", [])
                shape_dict["keypoints"] = s.get("keypoints", [])
                shape_dict["template_name"] = s.get("template_name", "")

            data["shapes"].append(shape_dict)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def save_yolo(filepath, image_width, image_height, shapes, classes_list):
        """导出标注数据为 YOLO 格式（纯文本标注文件）。

        将标注数据转换为 YOLO 训练格式，坐标归一化到 [0, 1] 范围。
        支持以下标注类型：
        - rectangle: 输出 class_id cx cy w h
        - pose: 输出 class_id cx cy w h kp1_x kp1_y kp1_vis ...
        - obb: 输出 class_id x1 y1 x2 y2 x3 y3 x4 y4
        - polygon: 输出 class_id x1 y1 x2 y2 ...
        - point: 输出 class_id cx cy w h（微小固定框）

        Args:
            filepath: 输出文件路径。
            image_width: 图片宽度（像素）。
            image_height: 图片高度（像素）。
            shapes: 标注数据字典列表。
            classes_list: 类别名称列表，索引值即为 class_id。
        """
        lines = []
        for s in shapes:
            if s["label"] not in classes_list:
                continue
            class_id = classes_list.index(s["label"])

            if s["type"] == "rectangle":
                x1, y1 = s["points"][0]
                x2, y2 = s["points"][1]
                cx = ((x1 + x2) / 2.0) / image_width
                cy = ((y1 + y2) / 2.0) / image_height
                w = abs(x2 - x1) / image_width
                h = abs(y2 - y1) / image_height
                lines.append(f"{class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

            elif s["type"] == "pose":
                rect = s.get("rect", [0, 0, 0, 0])
                cx = rect[0] / image_width
                cy = rect[1] / image_height
                w = rect[2] / image_width
                h = rect[3] / image_height
                
                # Ensure coordinates are properly normalized and within bounds [0, 1]
                cx = max(0.0, min(1.0, cx))
                cy = max(0.0, min(1.0, cy))
                w = max(0.0, min(1.0, w))
                h = max(0.0, min(1.0, h))
                
                parts = [f"{class_id}", f"{cx:.6f}", f"{cy:.6f}", f"{w:.6f}", f"{h:.6f}"]
                for kp in s.get("keypoints", []):
                    kx = kp[0] / image_width
                    ky = kp[1] / image_height
                    kx = max(0.0, min(1.0, kx))
                    ky = max(0.0, min(1.0, ky))
                    vis = kp[2]
                    parts.extend([f"{kx:.6f}", f"{ky:.6f}", f"{vis}"])
                lines.append(" ".join(parts))

            elif s["type"] == "obb":
                flat_pts = []
                for pt in s["points"][:4]:
                    flat_pts.append(f"{pt[0] / image_width:.6f} {pt[1] / image_height:.6f}")
                lines.append(f"{class_id} " + " ".join(flat_pts))

            elif s["type"] == "polygon":
                flat_pts = []
                for pt in s["points"]:
                    flat_pts.append(f"{pt[0] / image_width:.6f} {pt[1] / image_height:.6f}")
                lines.append(f"{class_id} " + " ".join(flat_pts))

            elif s["type"] == "point":
                cx = s["points"][0][0] / image_width
                cy = s["points"][0][1] / image_height
                pw, ph = 0.02, 0.02  # 微小框宽高
                cx = max(pw / 2, min(1.0 - pw / 2, cx))
                cy = max(ph / 2, min(1.0 - ph / 2, cy))
                lines.append(f"{class_id} {cx:.6f} {cy:.6f} {pw:.6f} {ph:.6f}")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    @staticmethod
    def save_xml(filepath, image_path, image_width, image_height, shapes):
        """导出标注数据为 Pascal VOC XML 格式。

        生成符合 Pascal VOC 标注规范的 XML 文件，
        包含文件夹、文件名、图片尺寸和所有目标对象（object）的
        边界框（bndbox: xmin, ymin, xmax, ymax）信息。
        对旋转框和骨架使用 rect 中心坐标计算边界框。

        Args:
            filepath: 输出文件路径。
            image_path: 原图路径。
            image_width: 图片宽度（像素）。
            image_height: 图片高度（像素）。
            shapes: 标注数据字典列表。
        """
        root = ET.Element("annotation")
        ET.SubElement(root, "folder").text = "images"
        ET.SubElement(root, "filename").text = os.path.basename(image_path)
        size = ET.SubElement(root, "size")
        ET.SubElement(size, "width").text = str(int(image_width))
        ET.SubElement(size, "height").text = str(int(image_height))
        ET.SubElement(size, "depth").text = "3"

        for s in shapes:
            if s["type"] == "pose" or s["type"] == "obb":
                rect = s.get("rect", [0, 0, 0, 0])
                cx, cy, w, h = rect
                min_x = cx - w / 2
                max_x = cx + w / 2
                min_y = cy - h / 2
                max_y = cy + h / 2
            elif s["points"]:
                min_x = min(p[0] for p in s["points"])
                max_x = max(p[0] for p in s["points"])
                min_y = min(p[1] for p in s["points"])
                max_y = max(p[1] for p in s["points"])
            else:
                continue

            obj = ET.SubElement(root, "object")
            ET.SubElement(obj, "name").text = s["label"]
            ET.SubElement(obj, "pose").text = "Unspecified"
            ET.SubElement(obj, "truncated").text = "0"
            ET.SubElement(obj, "difficult").text = "0"

            bndbox = ET.SubElement(obj, "bndbox")
            ET.SubElement(bndbox, "xmin").text = str(int(min_x))
            ET.SubElement(bndbox, "ymin").text = str(int(min_y))
            ET.SubElement(bndbox, "xmax").text = str(int(max_x))
            ET.SubElement(bndbox, "ymax").text = str(int(max_y))

        xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xmlstr)