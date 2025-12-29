"""
用于缓存加载占位符的轻量级图像管理器。当文件缺失时，会退回到纯色表面。
"""
import os
import pygame


class ImageManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self._cache = {}

    def _full_path(self, name):
        # 允许同时使用'foo/bar'和'foo/bar.png'
        if name.lower().endswith('.png'):
            rel = name
        else:
            rel = f"{name}.png"
        return os.path.join(self.base_dir, rel)

    def get(self, name, scale=None, colorkey=None, fallback_size=(32, 32), fallback_color=(255, 0, 255)):
        """Load and cache an image. Missing files return a colored placeholder surface."""
        key = (name, scale, colorkey)
        if key in self._cache:
            return self._cache[key]

        full_path = self._full_path(name)
        surf = None
        if os.path.exists(full_path):
            try:
                surf = pygame.image.load(full_path)
                surf = surf.convert_alpha()
            except Exception:
                surf = None
        if surf is None:
            size = fallback_size
            if isinstance(scale, tuple):
                size = scale
            elif isinstance(scale, (int, float)):
                size = (int(fallback_size[0] * scale), int(fallback_size[1] * scale))
            surf = pygame.Surface(size, flags=pygame.SRCALPHA)
            surf.fill(fallback_color)

        if colorkey is not None:
            surf.set_colorkey(colorkey)

        if scale is not None and not isinstance(scale, tuple):
            # 数值尺度在上面已经处理过了；只剩下元组缩放了
            pass
        elif scale is not None and isinstance(scale, tuple):
            surf = pygame.transform.smoothscale(surf, scale)

        self._cache[key] = surf
        return surf
