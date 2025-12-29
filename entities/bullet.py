"""
子弹实体模块
"""

import pygame
from config.settings import BULLET_SIZE, WIDTH, HEIGHT, COLOR_PLAYER_BULLET, COLOR_ENEMY_BULLET, DEFAULT_BULLET_RANGE, DEFAULT_BULLET_DAMAGE


class Bullet:
    """
    子弹类：由玩家或敌人发射
    """
    
    def __init__(self, pos, direction, speed, owner, damage=None, max_range=None):
        """
        初始化子弹
        
        参数:
            pos: (x, y) 子弹初始位置
            direction: (dx, dy) 移动方向向量
            speed: 移动速度
            owner: 'player' 或 'enemy' 标识子弹所有者
        """
        self.x, self.y = pos
        self.dx, self.dy = direction
        self.speed = speed
        # 伤害与射程
        self.damage = damage if damage is not None else DEFAULT_BULLET_DAMAGE
        self.max_range = max_range if max_range is not None else DEFAULT_BULLET_RANGE
        self.start_pos = (self.x, self.y)
        self.travelled = 0
        self.owner = owner
        self.rect = pygame.Rect(self.x - BULLET_SIZE // 2, self.y - BULLET_SIZE // 2, 
                                BULLET_SIZE, BULLET_SIZE)
        self.alive = True

    def update(self, dt):
        """
        更新子弹位置
        
        参数:
            dt: 帧时间差(ms)
        """
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.rect.x = int(self.x - BULLET_SIZE // 2)
        self.rect.y = int(self.y - BULLET_SIZE // 2)
        
        # 超出屏幕范围则标记为死亡
        # 更新已飞行的距离
        self.travelled = ((self.x - self.start_pos[0])**2 + (self.y - self.start_pos[1])**2) ** 0.5
        if not (-50 < self.x < WIDTH + 50 and -50 < self.y < HEIGHT + 50) or self.travelled >= self.max_range:
            self.alive = False

    def draw(self, surf):
        """
        绘制子弹
        
        参数:
            surf: pygame 表面对象
        """
        color = COLOR_PLAYER_BULLET if self.owner == 'player' else COLOR_ENEMY_BULLET
        pygame.draw.rect(surf, color, self.rect)
