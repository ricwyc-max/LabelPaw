import math
from PySide6.QtCore import QPointF


def point_to_segment_dist(pt, p1, p2):
    """计算点到线段的最短距离和垂足投影点。

    使用参数化直线方程计算点到线段的投影位置，
    并将投影点约束在线段范围内（参数 t 限制在 [0, 1] 区间）。
    若线段退化为点（p1 == p2），则直接返回点到 p1 的距离。

    Args:
        pt: 目标点（QPointF）。
        p1: 线段起点（QPointF）。
        p2: 线段终点（QPointF）。

    Returns:
        tuple: (最短距离, 投影点 QPointF)。
    """
    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    if dx == 0 and dy == 0:
        return ((pt.x() - p1.x()) ** 2 + (pt.y() - p1.y()) ** 2) ** 0.5, p1
    
    t = ((pt.x() - p1.x()) * dx + (pt.y() - p1.y()) * dy) / (dx ** 2 + dy ** 2)
    t = max(0, min(1, t))
    proj_x = p1.x() + t * dx
    proj_y = p1.y() + t * dy
    proj = QPointF(proj_x, proj_y)
    dist = ((pt.x() - proj_x) ** 2 + (pt.y() - proj_y) ** 2) ** 0.5
    return dist, proj


def point_in_polygon(pt, polygon):
    """判断点是否在多边形内部（射线法 / Ray Casting Algorithm）。

    从目标点向右发射水平射线，统计与多边形边的交点数。
    若交点为奇数，则点在多边形内部；偶数为外部。
    适用于凸多边形和凹多边形。

    Args:
        pt: 目标点（QPointF）。
        polygon: 多边形顶点列表（list of QPointF）。

    Returns:
        bool: 点在多边形内返回 True，否则返回 False。
    """
    x, y = pt.x(), pt.y()
    inside = False
    n = len(polygon)
    
    for i in range(n):
        j = (i + 1) % n
        xi, yi = polygon[i].x(), polygon[i].y()
        xj, yj = polygon[j].x(), polygon[j].y()
        
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
    
    return inside


def find_closest_edge(pt, polygon):
    """找到多边形上距离点最近的边
    
    Args:
        pt: 点
        polygon: 多边形顶点列表
        
    Returns:
        (最小距离, 最近边的索引, 投影点)
    """
    min_dist = float('inf')
    closest_edge = -1
    closest_proj = None
    
    n = len(polygon)
    for i in range(n):
        j = (i + 1) % n
        dist, proj = point_to_segment_dist(pt, polygon[i], polygon[j])
        if dist < min_dist:
            min_dist = dist
            closest_edge = i
            closest_proj = proj
    
    return min_dist, closest_edge, closest_proj


def snap_to_edge(pt, polygon, threshold=8):
    """边缘吸附：如果点靠近多边形边缘，则吸附到边缘
    
    Args:
        pt: 点
        polygon: 多边形顶点列表
        threshold: 吸附阈值（像素）
        
    Returns:
        (是否吸附, 吸附后的点)
    """
    min_dist, edge_idx, proj = find_closest_edge(pt, polygon)
    if min_dist < threshold:
        return True, proj
    return False, pt


def polygon_area(polygon):
    """计算多边形面积
    
    Args:
        polygon: 多边形顶点列表
        
    Returns:
        面积
    """
    area = 0.0
    n = len(polygon)
    
    for i in range(n):
        j = (i + 1) % n
        area += polygon[i].x() * polygon[j].y() - polygon[j].x() * polygon[i].y()
    
    return abs(area) / 2.0


def polygon_centroid(polygon):
    """计算多边形重心
    
    Args:
        polygon: 多边形顶点列表
        
    Returns:
        重心点
    """
    area = polygon_area(polygon)
    if area == 0:
        return QPointF(0, 0)
    
    cx, cy = 0.0, 0.0
    n = len(polygon)
    
    for i in range(n):
        j = (i + 1) % n
        factor = polygon[i].x() * polygon[j].y() - polygon[j].x() * polygon[i].y()
        cx += (polygon[i].x() + polygon[j].x()) * factor
        cy += (polygon[i].y() + polygon[j].y()) * factor
    
    cx /= 6.0 * area
    cy /= 6.0 * area
    return QPointF(cx, cy)
