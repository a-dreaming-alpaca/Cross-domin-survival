"""
敌人实体模块
"""

import pygame
import random
import math
from copy import copy
from config.settings import (
    ENEMY_SIZE, ENEMY_HP, ENEMY_FIRE_COOLDOWN, ENEMY_DETECT_RANGE,
    BULLET_SPEED, COLOR_ENEMY, ENEMY_BULLET_DAMAGE, ENEMY_ARCHETYPES,
    WIDTH, HEIGHT,
)

# Boss 大小常量（可选覆盖）
from config.settings import BOSS_SIZE
from utils import vec_from_points, aim_info
from entities.bullet import Bullet
from entities.weapons import RangedWeapon, SHOP_WEAPONS, MeleeWeapon


class Enemy:
    """
    敌人类：巡逻、检测、射击
    """

    def __init__(self, x, y, patrol_radius=0, images=None, archetype='grunt'):
        """
        初始化敌人
        
        参数:
            x: 初始 x 坐标
            y: 初始 y 坐标
            patrol_radius: 巡逻半径，0 表示不巡逻
        """
        self.rect = pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)
        # archetype setup
        self.kind = archetype or 'grunt'
        self.archetype = ENEMY_ARCHETYPES.get(self.kind, ENEMY_ARCHETYPES.get('grunt', {}))
        base = self.archetype
        self.max_hp = base.get('hp', ENEMY_HP)
        self.hp = self.max_hp
        self.detect_range = base.get('detect_range', ENEMY_DETECT_RANGE)
        self.fire_cooldown = base.get('fire_cooldown', ENEMY_FIRE_COOLDOWN)
        self.bullet_damage = base.get('bullet_damage', ENEMY_BULLET_DAMAGE)
        self.money = base.get('money', 150)
        self.patrol_center = (x, y)
        self.patrol_radius = patrol_radius
        self.last_shot = 0
        self.alive = True
        # 简单圆形巡逻角度
        self._angle = random.random() * math.pi * 2
        # 朝向（单位向量）及角度（度）用于贴图旋转
        self.dir = (1, 0)
        self.angle = 0.0
        self.images = images
        self.image = None
        if images:
            self.image = images.get('enemy/placeholder', scale=(ENEMY_SIZE, ENEMY_SIZE), fallback_size=(ENEMY_SIZE, ENEMY_SIZE), fallback_color=COLOR_ENEMY)
        # 根据archetype类型添加不同武器
        self.weapon = self._build_weapon_from_archetype(base)
        # 必要时将探测范围扩大到武器可及范围
        try:
            weap_range = getattr(self.weapon, 'range_px', None)
            if weap_range is not None:
                self.detect_range = max(self.detect_range, weap_range)
        except Exception:
            pass

    def _build_weapon_from_archetype(self, base):
        """根据原型名从 `SHOP_WEAPONS` 中选择武器，找不到则回退到基础手枪。"""
        wname = (base or {}).get('weapon', 'basic pistol')
        weapon = None
        try:
            lname = wname.lower()
            for w in SHOP_WEAPONS:
                if w.name.lower() == lname:
                    weapon = copy(w)
                    break
        except Exception:
            weapon = None
        if weapon is None:
            weapon = RangedWeapon('Basic Pistol', cost=0, cooldown=self.fire_cooldown, damage=self.bullet_damage, speed=BULLET_SPEED, range_px=800)
        # 调整伤害和冷却
        try:
            if hasattr(weapon, 'cooldown'):
                weapon.cooldown = base.get('fire_cooldown', weapon.cooldown)
            if hasattr(weapon, 'damage'):
                weapon.damage = base.get('bullet_damage', weapon.damage)
            # 确保敌人等级的伤害与武器伤害保持一致
            self.bullet_damage = getattr(weapon, 'damage', self.bullet_damage)
        except Exception:
            pass
        return weapon

    def update(self, dt):
        """
        更新敌人位置（巡逻）
        
        参数:
            dt: 帧时间差(ms)
        """
        # 如果有巡逻半径，执行圆形巡逻
        if self.patrol_radius > 0:
            self._angle += dt * 0.001
            cx, cy = self.patrol_center
            old_center = self.rect.center
            new_cx = int(cx + math.cos(self._angle) * self.patrol_radius)
            new_cy = int(cy + math.sin(self._angle) * self.patrol_radius)
            self.rect.centerx = new_cx
            self.rect.centery = new_cy
            # 更新朝向为新的移动方向
            ndx, ndy, dist = vec_from_points(old_center, self.rect.center)
            if dist != 0:
                self.dir = (ndx, ndy)
                self.angle = math.degrees(math.atan2(ndy, ndx))
        # 如果存在武器则更新武器的视觉效果
        try:
            if isinstance(self.weapon, RangedWeapon):
                self.weapon.update(dt)
            elif isinstance(self.weapon, MeleeWeapon):
                self.weapon.update(dt)
        except Exception:
            pass

    def try_shoot(self, player, now):
        """
        尝试射击玩家
        
        Args:
            player_pos: (x, y) 玩家位置
            now: 当前时间戳(ms)
        
        Returns:
            Bullet对象或None
        """
        # `player`可以是(x,y)元组或者是一个含`rect`的对象
        if hasattr(player, 'rect'):
            player_pos = player.rect.center
        else:
            player_pos = player
        # 缓存上次已知玩家位置以供Boss行为逻辑使用
        try:
            self.last_player_pos = player_pos
        except Exception:
            pass
        dirx, diry, dist = vec_from_points(self.rect.center, player_pos)
        # 面向玩家
        if dist != 0:
            self.dir = (dirx, diry)
            self.angle = math.degrees(math.atan2(diry, dirx))
        
        # 仅在玩家在检测范围内且冷却时间满足时射击
        if dist <= self.detect_range and now - self.last_shot >= self.fire_cooldown:
            self.last_shot = now
            # 计算与玩家相似的枪口安装位置
            center = pygame.math.Vector2(self.rect.center)
            direction = pygame.math.Vector2(dirx, diry)
            hand_offset_dist = max(0, (self.rect.width // 2) - 2)
            hand_offset = direction * hand_offset_dist + pygame.math.Vector2(-direction.y, direction.x) * 10
            gun_pos = (int(center.x + hand_offset.x), int(center.y + hand_offset.y))
            # 触发武器视觉效果
            try:
                if isinstance(self.weapon, RangedWeapon):
                    self.weapon.trigger_fire_visual()
                    # 武器开火创造子弹对象
                    return self.weapon.fire(gun_pos, player_pos, owner='enemy')
            except Exception:
                pass
            # 回退：创建简单子弹（使用当前武器的伤害以保持一致性）
            b = Bullet(gun_pos, (dirx, diry), BULLET_SPEED * 0.30, 'enemy', damage=getattr(self.weapon, 'damage', self.bullet_damage))
            return b
        
        return None

    def draw(self, surf):
        """
        绘制敌人及其生命条
        
        参数:
            surf: pygame 表面对象
        """
        if self.image:
            try:
                rotated = pygame.transform.rotate(self.image, -self.angle)
                rrect = rotated.get_rect(center=self.rect.center)
                surf.blit(rotated, rrect.topleft)
            except Exception:
                surf.blit(self.image, self.rect.topleft)
        else:
            pygame.draw.rect(surf, COLOR_ENEMY, self.rect)
        # ------------------ 绘制敌人挂载的武器 ------------------
        try:
            if hasattr(self, 'weapon') and isinstance(self.weapon, RangedWeapon):
                hand_offset_dist = max(0, (self.rect.width // 2) - 2)
                direction = pygame.math.Vector2(self.dir)
                self.weapon.render_mounted(
                    surf,
                    origin=pygame.math.Vector2(self.rect.center),
                    direction_vec=direction,
                    images=self.images,
                    hand_offset_dist=hand_offset_dist,
                )
            elif hasattr(self, 'weapon') and isinstance(self.weapon, MeleeWeapon):
                hand_offset_dist = max(0, (self.rect.width // 2) - 2)
                direction = pygame.math.Vector2(self.dir)
                self.weapon.render_mounted(
                    surf,
                    origin=pygame.math.Vector2(self.rect.center),
                    direction_vec=direction,
                    images=self.images,
                    hand_offset_dist=hand_offset_dist,
                )
        except Exception:
            pass
        
        # 绘制生命条
        hp_w = int(self.rect.width * max(0, self.hp) / self.max_hp)
        pygame.draw.rect(surf, (120, 120, 120), 
                         (self.rect.x, self.rect.y - 6, self.rect.width, 5))
        pygame.draw.rect(surf, (200, 200, 60), 
                         (self.rect.x, self.rect.y - 6, hp_w, 5))


class BossEnemy(Enemy):
    """Boss：大体型、高血量，具有弹幕与冲撞的状态机行为。"""

    def __init__(self, x, y, patrol_radius=0, images=None, archetype='boss'):
        super().__init__(x, y, patrol_radius=patrol_radius, images=images, archetype=archetype)
        # 将矩形覆盖为boss尺寸，并保留浮动坐标以实现平滑移动
        self.rect = pygame.Rect(x, y, BOSS_SIZE, BOSS_SIZE)
        self.x = float(self.rect.centerx)
        self.y = float(self.rect.centery)
        self.patrol_center = (x, y)
        self.hp = self.max_hp
        self.is_boss = True

        # 移动 / 轨道参数
        self.prefer_radius = 220
        self.orbit_speed = 0.095  # px/ms
        self.orbit_angle = 0.0
        self.orbit_jitter = 0.35

        # 状态机：ORBIT -> BURST -> DASH_LOCK -> DASH -> RECOVER
        self.state = 'ORBIT'
        self.state_timer = 0
        self.recover_ms = 500

        # 技能1（弹幕环）
        self.skill1_cooldown = 3600
        self.skill1_cooldown_remaining = 0
        self.skill1_duration = 2400
        self.skill1_emit_interval = 140
        self.skill1_active = False
        self.skill1_until = 0
        self.skill1_last_emit = 0

        # 技能2（突进）
        self.skill2_cooldown = 1400
        self.skill2_cooldown_remaining = 0
        self.skill2_active = False
        self.dash_lock_ms = 420
        self.dash_ms = 720
        self.dash_speed_ms = 0.55
        self.dash_vec = pygame.math.Vector2(0, 0)
        self.dash_has_hit = False
        self.dash_damage = getattr(self, 'bullet_damage', 40)

    # ---------------------------- 辅助方法 ----------------------------
    def _player_pos(self):
        if hasattr(self, 'last_player_pos') and self.last_player_pos:
            return pygame.math.Vector2(self.last_player_pos)
        return pygame.math.Vector2(self.patrol_center)

    def _orbit(self, target, dt, slow_factor=1.0):
        self.orbit_angle += 0.009 * (dt / 16.67)
        radius = self.prefer_radius + math.sin(self.orbit_angle * 0.7) * self.orbit_jitter * self.prefer_radius * 0.2
        desired = pygame.math.Vector2(
            target.x + math.cos(self.orbit_angle) * radius,
            target.y + math.sin(self.orbit_angle) * radius,
        )
        to_target = desired - pygame.math.Vector2(self.x, self.y)
        d = to_target.length()
        if d > 0:
            step = min(d, self.orbit_speed * slow_factor * dt)
            move_vec = to_target.normalize() * step
            self.x += move_vec.x
            self.y += move_vec.y

    def _start_skill1(self, now):
        # 启动技能1（进入弹幕态）
        self.skill1_active = True
        self.skill1_until = now + self.skill1_duration
        self.skill1_last_emit = 0
        self.state = 'BURST'
        self.state_timer = 0

    def _end_skill1(self):
        # 结束技能1并进入冷却
        self.skill1_active = False
        self.skill1_cooldown_remaining = self.skill1_cooldown
        self.state = 'ORBIT'
        self.state_timer = 0

    def _start_dash(self, player_pos):
        dx = player_pos.x - self.x
        dy = player_pos.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        self.dash_vec = pygame.math.Vector2(dx / dist * self.dash_speed_ms, dy / dist * self.dash_speed_ms)
        self.skill2_active = True
        self.dash_has_hit = False
        self.state = 'DASH_LOCK'
        self.state_timer = 0

    def _end_dash(self):
        # 结束突进并进入恢复态
        self.skill2_active = False
        self.skill2_cooldown_remaining = self.skill2_cooldown
        self.state = 'RECOVER'
        self.state_timer = 0
        self.dash_has_hit = False

    def _tick_cooldowns(self, dt, now):
        # 推进冷却计时器并自动结束技能
        if self.skill1_active and now >= self.skill1_until:
            self._end_skill1()
        if self.skill1_cooldown_remaining > 0:
            self.skill1_cooldown_remaining = max(0, self.skill1_cooldown_remaining - dt)
        if self.skill2_cooldown_remaining > 0:
            self.skill2_cooldown_remaining = max(0, self.skill2_cooldown_remaining - dt)

    def _sync_rect_and_clamp(self):
        self.x = max(0, min(WIDTH, self.x))
        self.y = max(0, min(HEIGHT, self.y))
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

    def update(self, dt):
        """Boss 行为更新：推进冷却并根据状态机移动。"""
        now = pygame.time.get_ticks()
        self._tick_cooldowns(dt, now)

        self.state_timer += dt
        target = self._player_pos()

        if self.state == 'ORBIT':
            self._orbit(target, dt)
        elif self.state == 'BURST':
            self._orbit(target, dt, slow_factor=0.55)
        elif self.state == 'DASH_LOCK':
            if self.state_timer >= self.dash_lock_ms:
                self.state = 'DASH'
                self.state_timer = 0
        elif self.state == 'DASH':
            move = self.dash_vec * dt
            self.x += move.x
            self.y += move.y
            out_bounds = (self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT)
            if out_bounds or self.state_timer >= self.dash_ms:
                self._end_dash()
        elif self.state == 'RECOVER':
            if self.state_timer >= self.recover_ms:
                self.state = 'ORBIT'
                self.state_timer = 0

        self._sync_rect_and_clamp()

        # 武器视觉效果更新
        try:
            if isinstance(self.weapon, (RangedWeapon, MeleeWeapon)):
                self.weapon.update(dt)
        except Exception:
            pass

    def _emit_skill1(self, dirx, diry):
        bullets = []
        center = pygame.math.Vector2(self.rect.center)
        base_angle = math.degrees(math.atan2(diry, dirx))
        step = 20
        for i, a in enumerate(range(0, 360, step)):
            if (i % 5) in (3, 4):
                continue
            ang = math.radians(a + base_angle)
            vx = math.cos(ang)
            vy = math.sin(ang)
            bpos = (int(center.x + vx * (self.rect.width // 2)), int(center.y + vy * (self.rect.height // 2)))
            b = Bullet(bpos, (vx, vy), BULLET_SPEED * 0.85, 'enemy', damage=self.bullet_damage)
            bullets.append(b)
        return bullets

    def try_shoot(self, player, now):
        """处理 Boss 的技能触发与弹幕生成；此处也处理突进命中逻辑。"""
        player_pos = player.rect.center if hasattr(player, 'rect') else player
        self.last_player_pos = player_pos

        dirx, diry, dist = vec_from_points(self.rect.center, player_pos)
        if dist != 0:
            self.dir = (dirx, diry)
            self.angle = math.degrees(math.atan2(diry, dirx))

        # 突进伤害判定窗口
        if self.skill2_active:
            if hasattr(player, 'rect') and self.rect.colliderect(player.rect) and not self.dash_has_hit:
                try:
                    player.hp -= self.dash_damage
                except Exception:
                    pass
                self.dash_has_hit = True
            return None

        # 弹幕发射阶段
        if self.skill1_active:
            if now - self.skill1_last_emit >= self.skill1_emit_interval:
                self.skill1_last_emit = now
                return self._emit_skill1(dirx, diry)
            return None

        # 如果技能1冷却完且玩家在检测范围内，触发技能1
        if self.skill1_cooldown_remaining <= 0 and dist <= self.detect_range:
            self._start_skill1(now)
            return None

        # 否则若技能2可用且玩家在范围内则触发突进
        if self.skill2_cooldown_remaining <= 0 and not self.skill1_active and dist <= self.detect_range:
            self._start_dash(pygame.math.Vector2(player_pos))
            return None

        # 备用方案：常规拍摄
        return super().try_shoot(player, now)

    def draw(self, surf):
        # 对象图片
        if self.image:
            try:
                rotated = pygame.transform.rotate(self.image, -self.angle)
                rrect = rotated.get_rect(center=self.rect.center)
                surf.blit(rotated, rrect.topleft)
            except Exception:
                surf.blit(self.image, self.rect.topleft)
        else:
            pygame.draw.rect(surf, COLOR_ENEMY, self.rect)

        # 武器图片
        try:
            if hasattr(self, 'weapon') and hasattr(self.weapon, 'render_mounted'):
                hand_offset_dist = max(0, (self.rect.width // 2) - 2)
                direction = pygame.math.Vector2(self.dir)
                self.weapon.render_mounted(
                    surf,
                    origin=pygame.math.Vector2(self.rect.center),
                    direction_vec=direction,
                    images=self.images,
                    hand_offset_dist=hand_offset_dist,
                )
        except Exception:
            pass

        # boss血条
        try:
            ratio = max(0, self.hp) / self.max_hp
            bar_w = max(self.rect.width, 220)
            bar_h = 12
            bx = self.rect.centerx - bar_w // 2
            by = self.rect.y - 24
            pygame.draw.rect(surf, (120, 120, 120), (bx, by, bar_w, bar_h))
            pygame.draw.rect(surf, (200, 60, 60), (bx, by, int(bar_w * ratio), bar_h))
        except Exception:
            pass
