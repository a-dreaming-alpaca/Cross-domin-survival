"""
玩家实体模块
"""

import pygame
import math
import random
from copy import copy
from config.settings import (
    PLAYER_SIZE, PLAYER_MAX_HP, PLAYER_SPEED, PLAYER_FIRE_COOLDOWN,
    WIDTH, HEIGHT, BULLET_SPEED, COLOR_PLAYER, COLOR_HP_BAR_BG, COLOR_HP_BAR_FG, PLAYER_MELEE_COOLDOWN,
    get_weapon_upgrade_cfg
)
from utils import vec_from_points, aim_info
from entities.bullet import Bullet
from entities.weapons import RangedWeapon, MeleeWeapon


class Player:
    """
    玩家类：可移动、射击、收集资源
    """
    
    def __init__(self, x, y, images=None):
        """
        初始化玩家
        
        参数:
            x: 初始 x 坐标
            y: 初始 y 坐标
        """
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.hp = PLAYER_MAX_HP
        self.speed = PLAYER_SPEED
        # 当前实体朝向的单位向量
        self.dir = (1, 0)
        # 角度（度数），0 表示向右。用于绘制时旋转贴图。
        self.angle = 0.0
        self.last_shot = 0
        self.last_melee = 0
        self.money = 0
        # weapon name -> upgrade level
        self.weapon_levels = {}
        # 武器库存：默认 Basic Pistol
        self.inventory = []
        self.equipped_idx = 0
        self.images = images
        self.image = None
        if images:
            self.image = images.get('player/placeholder', scale=(PLAYER_SIZE, PLAYER_SIZE), fallback_size=(PLAYER_SIZE, PLAYER_SIZE), fallback_color=COLOR_PLAYER)

        # 视觉效果状态由每把武器持有（按武器区分）

        # 若未通过商店加载，填充默认的基础手枪
        try:
            from entities.weapons import SHOP_WEAPONS
            # 添加一把基础手枪的副本
            base_pistol = copy(SHOP_WEAPONS[0])
            self.inventory.append(base_pistol)
            self.apply_weapon_upgrade(base_pistol.name)
        except Exception:
            # 备用方案：简单远程武器类别
            pistol = RangedWeapon('Basic Pistol', cost=0, cooldown=PLAYER_FIRE_COOLDOWN, damage=18, speed=BULLET_SPEED, range_px=800)
            self.inventory.append(pistol)
            self.apply_weapon_upgrade(pistol.name)

    def move(self, dx, dy):
        """
        移动玩家并受屏幕边界限制
        
        参数:
            dx: x 方向移动距离
            dy: y 方向移动距离
        """
        # 支持浮点移动，通过直接修改 rect 的坐标
        self.rect.x += dx
        self.rect.y += dy
        # 限制在屏幕范围内
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    def try_shoot(self, target_pos, now):
        """
        尝试射击子弹
        
        参数:
            target_pos: (x, y) 目标位置
            now: 当前时间戳(ms)
        
        返回:
            Bullet 对象或 None
        """
        weapon = self.inventory[self.equipped_idx]
        if isinstance(weapon, RangedWeapon):
            if now - self.last_shot < weapon.cooldown:
                return None
            self.last_shot = now
            # 触发特定武器的视觉效果
            try:
                weapon.trigger_fire_visual()
            except Exception:
                pass
            # 炮塔开火返回子弹列表
            try:
                gun_pos, direction = self.get_gun_mount(target_pos)
                return weapon.fire((int(gun_pos.x), int(gun_pos.y)), target_pos)
            except Exception:
                return weapon.fire(self.rect.center, target_pos)
        else:
            # 未装备远程武器
            return None

    def get_gun_mount(self, aim_pos):
        """
        计算枪口安装位置与瞄准方向向量（基于鼠标或目标位置）。
        返回 (gun_pos: Vector2, direction: Vector2)
        """
        center = pygame.math.Vector2(self.rect.center)
        aim = pygame.math.Vector2(aim_pos)
        dirv = aim - center
        if dirv.length_squared() > 0:
            direction = dirv.normalize()
        else:
            direction = pygame.math.Vector2(self.dir)
        hand_offset_dist = max(0, (self.rect.width // 2) - 2)
        hand_offset = direction * hand_offset_dist + pygame.math.Vector2(-direction.y, direction.x) * 10
        gun_pos = center + hand_offset
        return gun_pos, direction

    def update(self, dt):
        """
        更新武器视觉计时器。dt 单位为毫秒。
        """
        # 将视觉更新委托给已装备的武器
        try:
            weapon = self.inventory[self.equipped_idx]
            if isinstance(weapon, (RangedWeapon, MeleeWeapon)):
                weapon.update(dt)
        except Exception:
            pass

    def try_melee(self, now, enemies, bullets):
        weapon = self.inventory[self.equipped_idx]
        if isinstance(weapon, MeleeWeapon):
            if now - self.last_melee < weapon.cooldown:
                return None
            self.last_melee = now
            try:
                weapon.trigger_swing_visual()
            except Exception:
                pass
            hit_enemies, reflected = weapon.attack(self.rect.center, enemies, bullets)
            return hit_enemies, reflected
        return None

    def buy_weapon(self, weapon):
        """购买武器（如果尚未拥有且金钱足够）"""
        if self.has_weapon(getattr(weapon, 'name', None)):
            return False
        if self.money < weapon.cost:
            return False
        self.money -= weapon.cost
        # 添加一个副本，让库存物品就成为独立的对象
        new_w = copy(weapon)
        self.inventory.append(new_w)
        self.apply_weapon_upgrade(new_w.name)
        return True

    def has_weapon(self, weapon_name: str) -> bool:
        """按武器名检查拥有情况，避免升级后对象相等性变化导致的问题。"""
        if not weapon_name:
            return False
        return any(getattr(w, 'name', None) == weapon_name for w in self.inventory)

    def find_weapon_index(self, weapon_name: str):
        """返回武器在库存中的索引，找不到则返回 None。"""
        if not weapon_name:
            return None
        for idx, w in enumerate(self.inventory):
            if getattr(w, 'name', None) == weapon_name:
                return idx
        return None

    def apply_weapon_upgrade(self, weapon_name: str):
        """将保存的升级等级应用到库存中所有匹配的武器上。"""
        level = self.weapon_levels.get(weapon_name, 0)
        cfg = get_weapon_upgrade_cfg(weapon_name)
        for w in self.inventory:
            if getattr(w, 'name', None) == weapon_name and isinstance(w, RangedWeapon):
                try:
                    w.apply_upgrade_stats(level, cfg)
                except Exception:
                    pass

    def set_weapon_upgrade_level(self, weapon_name: str, level: int):
        """保存升级等级并同步武器属性。"""
        self.weapon_levels[weapon_name] = max(0, int(level))
        self.apply_weapon_upgrade(weapon_name)

    def heal(self, amount):
        """回复玩家生命至最大血量，返回实际恢复的量。"""
        before = self.hp
        self.hp = min(PLAYER_MAX_HP, self.hp + amount)
        return self.hp - before

    def equip_by_index(self, idx):
        if 0 <= idx < len(self.inventory):
            self.equipped_idx = idx
            return True
        return False

    def draw(self, surf):
        """
        绘制玩家及其生命条
        
        Args:
            surf: pygame表面对象
        """
        # 绘制玩家身体（会根据最后已知的角度进行旋转）
        if self.image:
            # 旋转贴图，使其朝向当前速度方向
            try:
                rotated = pygame.transform.rotate(self.image, -self.angle)
                rrect = rotated.get_rect(center=self.rect.center)
                surf.blit(rotated, rrect.topleft)
            except Exception:
                surf.blit(self.image, self.rect.topleft)
        else:
            pygame.draw.rect(surf, COLOR_PLAYER, self.rect)
        
        # 绘制生命条
        hp_w = int(self.rect.width * (self.hp / PLAYER_MAX_HP))
        pygame.draw.rect(surf, COLOR_HP_BAR_BG, 
                         (self.rect.x, self.rect.y - 8, self.rect.width, 6))
        pygame.draw.rect(surf, COLOR_HP_BAR_FG, 
                         (self.rect.x, self.rect.y - 8, hp_w, 6))

        # ------------------ 绘制武器（已装配） ------------------
        # 根据鼠标确定瞄准方向
        try:
            mouse_pos = pygame.mouse.get_pos()
        except Exception:
            mouse_pos = self.rect.center
        dx, dy, angle, flip = aim_info(self.rect.center, mouse_pos, fallback_dir=self.dir)
        direction = pygame.math.Vector2(dx, dy)
        # 更新身体旋转的朝向角度
        self.dir = (dx, dy)
        self.angle = math.degrees(math.atan2(dy, dx))

        # 准备武器渲染（远程或近战）
        weapon = None
        try:
            weapon = self.inventory[self.equipped_idx]
        except Exception:
            weapon = None

        if isinstance(weapon, RangedWeapon):
            hand_offset_dist = max(0, (self.rect.width // 2) - 2)
            weapon.render_mounted(
                surf,
                origin=pygame.math.Vector2(self.rect.center),
                direction_vec=direction,
                images=self.images,
                hand_offset_dist=hand_offset_dist,
                last_shot_time=self.last_shot,
                show_gray_cooldown=True,
            )
        elif isinstance(weapon, MeleeWeapon):
            hand_offset_dist = max(0, (self.rect.width // 2) - 2)
            weapon.render_mounted(
                surf,
                origin=pygame.math.Vector2(self.rect.center),
                direction_vec=direction,
                images=self.images,
                hand_offset_dist=hand_offset_dist,
            )
