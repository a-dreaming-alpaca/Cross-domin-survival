"""
工具函数模块
包含向量计算等通用工具函数
"""

import math
import os
import sys
import shutil


def setup_pycache_path():
    """
    将 Python 的字节码缓存目录统一到项目根的 `.cache` 文件夹。

    该函数会创建 `.cache`（如果不存在）并设置 `sys.pycache_prefix`。
    在需要避免在不同文件夹产生多个 `__pycache__` 时调用。
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    pycache_dir = os.path.join(project_root, ".cache")
    if not os.path.exists(pycache_dir):
        os.makedirs(pycache_dir, exist_ok=True)
    sys.pycache_prefix = pycache_dir
    
    # 注意：此函数不会在模块导入时自动调用。为了保证 pycache 在 import 之前被设置，
    # 请在程序最先的入口处 import `pycache_init`（推荐），或显式调用本函数。
    return


def vec_from_points(a, b):
    """
    计算从点a到点b的单位方向向量和距离
    
    Args:
        a: (x, y) 起点坐标
        b: (x, y) 终点坐标
    
    Returns:
        (dx, dy, distance): 方向向量(x, y)及距离
                           当距离为0时返回 (0, 0, 0)
    """
    ax, ay = a
    bx, by = b
    dx = bx - ax
    dy = by - ay
    dist = math.hypot(dx, dy)
    if dist == 0:
        return 0, 0, 0
    return dx / dist, dy / dist, dist


def clamp(value, min_val, max_val):
    """
    限制值在指定范围内
    
    Args:
        value: 待限制的值
        min_val: 最小值
        max_val: 最大值
    
    Returns:
        限制后的值
    """
    return max(min_val, min(value, max_val))


def distance(p1, p2):
    """
    计算两点间的欧几里得距离
    
    Args:
        p1: (x, y) 点1
        p2: (x, y) 点2
    
    Returns:
        距离值
    """
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def aim_info(src, tgt, fallback_dir=(1, 0)):
    """
    计算从 src 指向 tgt 的单位方向、用于贴图的渲染角度和水平翻转标志。
    当 src==tgt 时使用 fallback_dir。

    Returns:
        (dx, dy, angle_deg, flip):
            dx, dy: 单位方向向量
            angle_deg: 贴图旋转角（已适配 y 轴向下的屏幕坐标系）
            flip: 是否需要水平翻转贴图
    """
    dx, dy, dist = vec_from_points(src, tgt)
    if dist == 0:
        dx, dy = fallback_dir
        # 保证 fallback_dir 已归一化
        mag = math.hypot(dx, dy)
        if mag != 0:
            dx, dy = dx / mag, dy / mag

    # y 轴向下，渲染时采用 atan2(-dy, dx) 以获得与贴图翻转一致的角度
    angle = math.degrees(math.atan2(-dy, dx))
    flip = False
    if angle < -90:
        angle += 180
        flip = True
    elif angle > 90:
        angle -= 180
        flip = True

    return dx, dy, angle, flip
