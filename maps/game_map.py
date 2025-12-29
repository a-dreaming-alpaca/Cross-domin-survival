"""
游戏地图模块
"""

import pygame
import random
from config.settings import (
    WIDTH, HEIGHT, RESOURCE_COUNT_PER_MAP,
    COLOR_BACKGROUND, COLOR_RESOURCE, COLOR_PORTAL, COLOR_EXIT,
    ENEMY_SPAWN_WEIGHTS
)
from entities.factory import EnemyFactory


class GameMap:
    """
    游戏地图类：管理敌人、资源、传送门和撤离点
    """
    
    def __init__(self, idx, is_final=False, images=None):
        """
        初始化地图
        
        Args:
            idx: 地图索引
            is_final: 是否为最终地图
        """
        self.idx = idx
        self.is_final = is_final
        self.images = images
        self.enemies = []
        self.portal = None
        self.exit_rect = None
        self.resource_img = None
        self.portal_img = None
        self.exit_img = None
        self.enemy_factory = EnemyFactory(images=self.images)
        if images:
            self.resource_img = images.get('map/resource', scale=(16, 16), fallback_size=(16, 16), fallback_color=COLOR_RESOURCE)
            self.portal_img = images.get('map/portal', scale=(52, 52), fallback_size=(52, 52), fallback_color=COLOR_PORTAL)
            self.exit_img = images.get('map/exit', scale=(80, 80), fallback_size=(80, 80), fallback_color=COLOR_EXIT)
        self.make_content()

    def make_content(self):
        """
        生成地图内容：敌人、资源、传送门/撤离点
        """
        # 通用：按 settings 中的权重决定每张地图的敌人类型
        spawn_weights = ENEMY_SPAWN_WEIGHTS[min(self.idx, len(ENEMY_SPAWN_WEIGHTS) - 1)]

        # 如果是最终地图且权重配置只包含 boss，则只生成一个 Boss
        if self.is_final and set(spawn_weights.keys()) == {'boss'}:
            bx = WIDTH // 2
            by = HEIGHT // 2
            self.enemies.append(self.enemy_factory.create('boss', bx, by, patrol_radius=0))
            # 不事先创建撤离点或传送门，玩家需击败 boss 后触发传送门
            self.exit_rect = None
            self.portal = None
            return

        # 否则按原逻辑生成若干小怪（或根据权重生成可能的 boss）
        enemy_count = 3 + self.idx
        for i in range(enemy_count):
            x = random.randint(60, WIDTH - 60)
            y = random.randint(60, HEIGHT - 60)
            patrol = random.choice([0, 40, 80])
            archetype = self._pick_archetype(spawn_weights)
            self.enemies.append(self.enemy_factory.create(archetype, x, y, patrol_radius=patrol))

    def spawn_portal(self):
        """在随机的有效位置生成一个传送门（在非最终地图和敌人被清除后的最终地图中均会使用）。"""
        if self.portal is not None:
            return
        px = random.randint(80, WIDTH - 120)
        py = random.randint(80, HEIGHT - 120)
        self.portal = pygame.Rect(px, py, 52, 52)

    def _pick_archetype(self, weights):
        """基于提供的字典进行加权选择；返回原型名称。"""
        total = sum(weights.values())
        r = random.random() * total
        acc = 0.0
        for name, w in weights.items():
            acc += w
            if r <= acc:
                return name
        # 备选
        return next(iter(weights.keys()))

    def draw(self, surf):
        """
        绘制地图背景及元素
        
        Args:
            surf: pygame表面对象
        """
        # 背景
        surf.fill(COLOR_BACKGROUND)
        
        # 绘制传送门
        if self.portal:
            if self.portal_img:
                surf.blit(self.portal_img, self.portal.topleft)
            else:
                pygame.draw.ellipse(surf, COLOR_PORTAL, self.portal)
            # 可以在此处添加文字标签
        
        # 绘制撤离点
        if self.exit_rect:
            if self.exit_img:
                surf.blit(self.exit_img, self.exit_rect.topleft)
            else:
                pygame.draw.rect(surf, COLOR_EXIT, self.exit_rect)
