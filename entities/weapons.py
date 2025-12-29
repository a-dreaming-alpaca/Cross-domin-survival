"""
武器系统模块
定义武器接口、近战武器和远程武器，同时提供商店中的武器列表
"""

from dataclasses import dataclass
import math
import random
from typing import List, Tuple
import pygame
from entities.bullet import Bullet
from config.settings import COLOR_PLAYER_BULLET, MELEE_SPRITE_SIZE, MELEE_SPRITE_FALLBACK_COLOR
from utils import aim_info


@dataclass
class Weapon:
    name: str
    type: str  # 'melee'近战或者'ranged'远程
    cost: int
    cooldown: int
    desc: str = ''


class RangedWeapon(Weapon):
    def __init__(self, name, cost, cooldown, damage, speed, range_px, pellets=1, spread=0.0, desc=''):
        super().__init__(name, 'ranged', cost, cooldown, desc)
        self.damage = damage
        self.speed = speed
        self.range_px = range_px
        self.base_damage = damage
        self.base_speed = speed
        self.base_range = range_px
        self.base_cooldown = cooldown
        self.pellets = pellets
        self.spread = spread 
        # 枪支图片设置：默认安装的枪支尺寸（宽、高），单位为像素
        self.gun_size = (14, 5)
        # images下的可选枪支图片名（例如'weapons/basic_pistol'）
        self.sprite_key = None
        # 发射后冷却的灰色枪支图片（例如“weapons/basic_pistol_gray”）
        self.sprite_key_gray = None
        # 视觉/后坐力/闪光/抖动属性
        self.recoil = 0.0
        self.recoil_strength = 8.0
        self.recoil_return_speed = 60.0  # pixels per second
        self.flash_timer = 0.0
        self.flash_duration = 50.0  # ms
        self.shake_timer = 0.0
        self.shake_duration = 80.0  # ms
        self.shake_strength = 3
        # 从枪口原点向瞄准方向的枪口偏移量（像素）
        self.muzzle_offset = 24
        # 升级状态
        self.upgrade_level = 0

    def apply_upgrade_stats(self, level: int, cfg: dict | None):
        """将升级倍率应用到此武器实例。"""
        self.upgrade_level = max(0, int(level or 0))
        if not cfg:
            return
        lvl = min(self.upgrade_level, cfg.get('max_level', 0))
        dmg_mult = cfg.get('damage_mult', [])
        cd_mult = cfg.get('cooldown_mult', [])
        rng_add = cfg.get('range_add', [])

        if dmg_mult:
            idx = min(lvl, len(dmg_mult) - 1)
            self.damage = int(round(self.base_damage * dmg_mult[idx]))
        if cd_mult:
            idx = min(lvl, len(cd_mult) - 1)
            self.cooldown = int(round(self.base_cooldown * cd_mult[idx]))
        if rng_add:
            idx = min(lvl, len(rng_add) - 1)
            self.range_px = int(round(self.base_range + rng_add[idx]))

    def fire(self, owner_pos: Tuple[int,int], aim_pos: Tuple[int,int], owner='player'):
        """
        发射子弹并返回子弹列表
        """
        ox, oy = owner_pos
        dx = aim_pos[0] - ox
        dy = aim_pos[1] - oy
        base_dist = math.hypot(dx, dy)
        if base_dist == 0:
            ax, ay = 1, 0
        else:
            ax, ay = dx / base_dist, dy / base_dist

        bullets = []
        # 散弹多发
        if self.pellets == 1:
            b = Bullet((ox, oy), (ax, ay), self.speed, owner, damage=self.damage, max_range=self.range_px)
            bullets.append(b)
        else:
            # 围绕瞄准方向生成扩散角度
            base_angle = math.atan2(ay, ax)
            for i in range(self.pellets):
                if self.pellets == 1:
                    ang = base_angle
                else:
                    t = (i - (self.pellets-1)/2) / (self.pellets-1) if self.pellets>1 else 0
                    ang = base_angle + t * self.spread
                adx = math.cos(ang)
                ady = math.sin(ang)
                b = Bullet((ox, oy), (adx, ady), self.speed, owner, damage=self.damage, max_range=self.range_px)
                bullets.append(b)
        return bullets

    def get_gun_image(self, images=None, fallback_color=(200,200,200), gray=False):
        """
        返回表示挂载枪械的 pygame.Surface。
        若提供了 `ImageManager`，将尝试加载 `weapons/<weapon_name>` 下的贴图，找不到则回退为填色矩形。
        """
        size = self.gun_size
        surf = None
        is_placeholder = False
        if images is not None:
            base_key = self.sprite_key or f"weapons/{self.name.lower().replace(' ', '_')}"
            key = base_key
            if gray:
                key = self.sprite_key_gray or f"{base_key}_gray"
            try:
                surf = images.get(key, scale=size, fallback_size=size)
            except Exception:
                surf = None
            # 如果 gray 未被找到, 使用base key
            if gray and surf is None:
                try:
                    surf = images.get(base_key, scale=size, fallback_size=size)
                except Exception:
                    surf = None
        if surf is None:
            surf = pygame.Surface(size, flags=pygame.SRCALPHA)
            surf.fill(fallback_color)
            is_placeholder = True
        return surf, is_placeholder
    
    def trigger_fire_visual(self):
        """武器开火时调用以触发后坐力/闪光/抖动等视觉效果。"""
        self.recoil = self.recoil_strength
        self.flash_timer = self.flash_duration
        self.shake_timer = self.shake_duration

    def update(self, dt):
        """更新武器的视觉计时器。dt 单位为毫秒。"""
        if self.recoil > 0:
            decay = self.recoil_return_speed * (dt / 1000.0)
            self.recoil -= decay
            if self.recoil < 0:
                self.recoil = 0.0
        if self.flash_timer > 0:
            self.flash_timer -= dt
            if self.flash_timer < 0:
                self.flash_timer = 0.0
        if self.shake_timer > 0:
            self.shake_timer -= dt
            if self.shake_timer < 0:
                self.shake_timer = 0.0

    def render_mounted(self, surf, origin, direction_vec, images=None, *, hand_offset_dist=0, lateral_offset=10,
                       last_shot_time=None, now=None, show_gray_cooldown=False, placeholder_color=(200, 200, 200),
                       placeholder_cooldown_color=(100, 100, 100), flash_color=(255, 240, 180)):
        """
        在给定原点沿 `direction_vec` 绘制挂载武器。

        参数:
            origin: pygame.Vector2，用于锚定手或枪的位置。
            direction_vec: pygame.Vector2 表示方向（若需要会被归一化）。
            images: 可选的 ImageManager 用于加载贴图。
            hand_offset_dist: 从原点沿射击方向的前移偏移。
            lateral_offset: 手部的侧向偏移。
            last_shot_time/now/show_gray_cooldown: 控制玩家端冷却态的灰度贴图显示。
        """
        if now is None:
            now = pygame.time.get_ticks()
        direction = pygame.math.Vector2(direction_vec)
        if direction.length_squared() == 0:
            direction = pygame.math.Vector2(1, 0)
        else:
            direction = direction.normalize()

        dx, dy, angle, flip = aim_info((origin.x, origin.y), (origin.x + direction.x, origin.y + direction.y), fallback_dir=(direction.x, direction.y))
        direction = pygame.math.Vector2(dx, dy)

        gray = False
        if show_gray_cooldown and last_shot_time is not None:
            try:
                if now - last_shot_time < self.cooldown:
                    gray = True
            except Exception:
                gray = False

        gun_img, is_placeholder = self.get_gun_image(images, gray=gray)
        if gun_img is None:
            gun_img = pygame.Surface((14, 5), flags=pygame.SRCALPHA)
            is_placeholder = True
        if is_placeholder:
            color = placeholder_color
            if gray:
                color = placeholder_cooldown_color
            gun_img.fill(color)

        if flip:
            gun_img = pygame.transform.flip(gun_img, True, False)
        rotated = pygame.transform.rotate(gun_img, angle)

        recoil_amount = getattr(self, 'recoil', 0.0)
        muzzle_offset = getattr(self, 'muzzle_offset', 24)
        shake_strength = getattr(self, 'shake_strength', 3)
        shake_timer = getattr(self, 'shake_timer', 0.0)
        flash_timer = getattr(self, 'flash_timer', 0.0)

        recoil_offset = -pygame.math.Vector2(direction) * recoil_amount

        shake_offset = pygame.math.Vector2(0, 0)
        if shake_timer > 0:
            shake_offset.x = random.randint(-shake_strength, shake_strength)
            shake_offset.y = random.randint(-shake_strength, shake_strength)

        hand_offset = pygame.math.Vector2(direction) * hand_offset_dist + pygame.math.Vector2(-direction.y, direction.x) * lateral_offset
        gun_pos = pygame.math.Vector2(origin) + hand_offset + recoil_offset + shake_offset

        rrect = rotated.get_rect(center=gun_pos)
        surf.blit(rotated, rrect.topleft)

        if flash_timer > 0:
            flash_pos = gun_pos + pygame.math.Vector2(direction) * muzzle_offset
            pygame.draw.circle(surf, flash_color, (int(flash_pos.x), int(flash_pos.y)), 6)


class MeleeWeapon(Weapon):
    def __init__(self, name, cost, cooldown, damage, radius, reflect=False, desc='', sprite_key=None, sprite_size=None):
        super().__init__(name, 'melee', cost, cooldown, desc)
        self.damage = damage
        self.radius = radius
        self.reflect = reflect
        # 图片设置
        self.sprite_key = sprite_key
        self.sprite_size = sprite_size or MELEE_SPRITE_SIZE
        # 摆动设置
        self.swing_timer = 0.0
        self.swing_duration = 220.0  # ms
        self.swing_arc = 140.0  # 摆动总角度
        self.swing_dir = 1 

    def attack(self, owner_pos: Tuple[int,int], enemies: List, bullets: List[Bullet]):
        """
        执行近战攻击：对 `enemies` 造成伤害并可反弹 `bullets`。
        返回受影响的敌人与被反弹的子弹列表。
        """
        ox, oy = owner_pos
        hit_enemies = []
        reflected_bullets = []
        # 伤害敌人
        for e in enemies:
            if not getattr(e, 'alive', True):
                continue
            ex, ey = e.rect.center
            dist = math.hypot(ex - ox, ey - oy)
            if dist <= self.radius:
                e.hp -= self.damage
                hit_enemies.append(e)
                if e.hp <= 0:
                    e.alive = False

        # 反弹子弹
        if self.reflect:
            for b in bullets:
                if not b.alive or b.owner == 'player':
                    continue
                bx, by = b.x, b.y
                distb = math.hypot(bx - ox, by - oy)
                if distb <= self.radius:
                    # 反射：反向并更改所有者
                    b.dx = -b.dx
                    b.dy = -b.dy
                    b.owner = 'player'
                    # 更改伤害值/颜色
                    b.damage = int(b.damage * 0.9) 
                    reflected_bullets.append(b)
        return hit_enemies, reflected_bullets

    def get_melee_image(self, images=None, fallback_color=None):
        """加载近战武器贴图（缺失时返回占位图）。"""
        fallback_color = fallback_color or MELEE_SPRITE_FALLBACK_COLOR
        surf = None
        is_placeholder = False
        if images is not None:
            key = self.sprite_key or f"weapons/{self.name.lower().replace(' ', '_')}"
            try:
                surf = images.get(key, scale=self.sprite_size, fallback_size=self.sprite_size)
            except Exception:
                surf = None
        if surf is None:
            surf = pygame.Surface(self.sprite_size, flags=pygame.SRCALPHA)
            surf.fill(fallback_color)
            is_placeholder = True
        return surf, is_placeholder

    def trigger_swing_visual(self):
        """启动挥砍动画（仅视觉效果）。"""
        self.swing_timer = self.swing_duration
        # 每次触发时交替摆动方向，以避免视觉上的突然跳动
        self.swing_dir *= -1

    def update(self, dt):
        """更新挥砍计时器。dt 单位为毫秒。"""
        if self.swing_timer > 0:
            self.swing_timer -= dt
            if self.swing_timer < 0:
                self.swing_timer = 0

    def render_mounted(self, surf, origin, direction_vec, images=None, hand_offset_dist=0, lateral_offset=10):
        """在手部位置绘制近战贴图，行为上与远程武器的挂载方式一致。"""
        dx, dy, angle, flip = aim_info((origin.x, origin.y), (origin.x + direction_vec.x, origin.y + direction_vec.y), fallback_dir=(direction_vec.x, direction_vec.y))
        direction = pygame.math.Vector2(dx, dy)
        if direction.length_squared() == 0:
            direction = pygame.math.Vector2(1, 0)
        # 增加向前的偏移量，这样摆动就能稍微向外延伸一些
        swing_forward = 0.0
        swing_angle_offset = 0.0
        if self.swing_duration > 0 and self.swing_timer > 0:
            progress = 1.0 - (self.swing_timer / self.swing_duration)  # 0 -> 1
            swing_forward = 6.0 * math.sin(progress * math.pi)
            swing_angle_offset = (progress * 2 - 1) * (self.swing_arc * 0.5) * self.swing_dir
        hand_offset = pygame.math.Vector2(direction) * (hand_offset_dist + swing_forward) + pygame.math.Vector2(-direction.y, direction.x) * lateral_offset
        sprite, is_placeholder = self.get_melee_image(images)
        if is_placeholder:
            sprite.fill(MELEE_SPRITE_FALLBACK_COLOR)
        if flip:
            sprite = pygame.transform.flip(sprite, True, False)
        rotated = pygame.transform.rotate(sprite, angle + swing_angle_offset)
        rrect = rotated.get_rect(center=origin + hand_offset)
        surf.blit(rotated, rrect.topleft)


# ----------------------------------------------------------------------------------
# 默认商店武器 (示例)
# 建造商店武器并为每种武器分配视觉默认值
bp = RangedWeapon('Basic Pistol', cost=0, cooldown=250, damage=18, speed=12, range_px=800, pellets=1, spread=0.0, desc='简易手枪，稳定的远程武器')
bp.gun_size = (14, 5)
bp.recoil_strength = 6.0
bp.recoil_return_speed = 90.0
bp.flash_duration = 40.0
bp.shake_duration = 60.0
bp.shake_strength = 2
bp.muzzle_offset = 12
bp.sprite_key = 'weapons/basic_pistol'
bp.sprite_key_gray = 'weapons/basic_pistol_gray'

sg = RangedWeapon('Shotgun', cost=250, cooldown=700, damage=10, speed=10, range_px=320, pellets=5, spread=0.9, desc='近距离高伤害的散弹枪')
sg.gun_size = (18, 6)
sg.recoil_strength = 14.0
sg.recoil_return_speed = 140.0
sg.flash_duration = 70.0
sg.shake_duration = 140.0
sg.shake_strength = 6
sg.muzzle_offset = 18
sg.sprite_key = 'weapons/shotgun'
sg.sprite_key_gray = 'weapons/shotgun_gray'

sr = RangedWeapon('Sniper Rifle', cost=400, cooldown=900, damage=80, speed=18, range_px=1200, pellets=1, spread=0.0, desc='远距离高伤害的狙击步枪')
sr.gun_size = (28, 6)
sr.recoil_strength = 18.0
sr.recoil_return_speed = 200.0
sr.flash_duration = 90.0
sr.shake_duration = 100.0
sr.shake_strength = 4
sr.muzzle_offset = 28
sr.sprite_key = 'weapons/sniper_rifle'
sr.sprite_key_gray = 'weapons/sniper_rifle_gray'

cl = MeleeWeapon('Cleaver', cost=150, cooldown=500, damage=40, radius=48, reflect=False, desc='近战大刀，劈砍群体敌人', sprite_key='weapons/cleaver')
rs = MeleeWeapon('Reflector Sword', cost=300, cooldown=800, damage=20, radius=64, reflect=True, desc='近战剑：伤敌并反弹子弹', sprite_key='weapons/reflector_sword')

SHOP_WEAPONS = [bp, sg, sr, cl, rs]
