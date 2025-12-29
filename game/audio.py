"""简单的音乐播放器工具。

将音乐文件放在 `assets/music/` 目录下（例如 `assets/music/menu_bg.mp3`）。
调用 `MusicPlayer(base_dir).play('menu_bg')` 可播放 `menu_bg.mp3` 或 `menu_bg.ogg`。
"""

import os
import pygame


class MusicPlayer:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.current = None
        # 尝试初始化混音器（如果尚未初始化）
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception:
            pass

    def _full_path(self, name):
        if os.path.splitext(name)[1]:
            fname = name
        else:
            # 尝试常见的扩展名；调用者可以选择一个存在的扩展名
            for ext in ('.mp3', '.ogg', '.wav'):
                candidate = f"{name}{ext}"
                if os.path.exists(os.path.join(self.base_dir, candidate)):
                    return os.path.join(self.base_dir, candidate)
            # 备用：mp3路径
            fname = f"{name}.mp3"
        return os.path.join(self.base_dir, fname)

    def play(self, name, loops=-1, volume=0.6, fade_ms=400):
        path = self._full_path(name)
        if not os.path.exists(path):
            return False
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
            self.current = name
            return True
        except Exception:
            return False

    def stop(self, fade_ms=300):
        try:
            pygame.mixer.music.fadeout(fade_ms)
        except Exception:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        self.current = None

    def is_playing(self):
        try:
            return pygame.mixer.music.get_busy()
        except Exception:
            return False

    def set_volume(self, volume: float):
        """设置全局音乐音量（0.0 - 1.0）。"""
        try:
            # 确保混音器在调整音量之前初始化
            if not pygame.mixer.get_init():
                try:
                    pygame.mixer.init()
                except Exception:
                    pass
            pygame.mixer.music.set_volume(max(0.0, min(1.0, float(volume))))
            return True
        except Exception:
            return False

    def get_volume(self):
        try:
            return pygame.mixer.music.get_volume()
        except Exception:
            return 1.0
