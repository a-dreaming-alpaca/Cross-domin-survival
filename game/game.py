"""
主游戏类模块
包含核心游戏逻辑和主循环
"""

import pygame
import sys
import random
from config.settings import (
    WIDTH, HEIGHT, FPS, WINDOW_TITLE, MAP_COUNT,
    PLAYER_MAX_HP, MONEY_PER_RESOURCE, MONEY_PER_ENEMY, BULLET_SPEED
)
from entities.weapons import SHOP_WEAPONS
from config.settings import SHOP_MEDKIT_COST, SHOP_MEDKIT_HEAL
from game.shop_ui import ShopItem
from entities.player import Player
from maps.game_map import GameMap
from game.shop_ui import ShopUI, ShopState
from game.hud import HUDRenderer


class Game:
    """
    主游戏类：管理游戏状态、更新和渲染
    """
    
    def __init__(self, screen, clock, font, bigfont, images=None, music=None, initial_state=None):
        """
        初始化游戏
        
        参数:
            screen: pygame 显示表面
            clock: pygame 时钟对象
            font: pygame 小号字体对象
            bigfont: pygame 大号字体对象
        """
        self.screen = screen
        self.clock = clock
        self.font = font
        self.bigfont = bigfont
        
        self.images = images
        self.music = music
        self.player = Player(60, 60, images=images)
        # 若提供 initial_state（存档），则应用对应属性
        if initial_state:
            try:
                if 'money' in initial_state:
                    self.player.money = int(initial_state.get('money', 0))
                if 'hp' in initial_state and initial_state.get('hp') is not None:
                    self.player.hp = int(initial_state.get('hp', self.player.hp))
                wl = initial_state.get('weapon_levels')
                if isinstance(wl, dict):
                    self.player.weapon_levels = dict(wl)
                inv = initial_state.get('inventory_objs')
                if inv:
                    # 若存档包含重建好的武器对象，直接替换背包
                    try:
                        self.player.inventory = list(inv)
                    except Exception:
                        pass
                    # 将统计数据与存储的升级级别同步
                    for w in self.player.inventory:
                        try:
                            self.player.apply_weapon_upgrade(getattr(w, 'name', None))
                        except Exception:
                            pass
                eq = initial_state.get('equipped_idx')
                if eq is not None:
                    try:
                        self.player.equipped_idx = int(eq)
                    except Exception:
                        pass
                # 确保即使库存未更换，升级也能生效
                for w in getattr(self.player, 'inventory', []):
                    try:
                        self.player.apply_weapon_upgrade(getattr(w, 'name', None))
                    except Exception:
                        pass
            except Exception:
                pass
        self.bullets = []
        self.maps = []
        self.current_map_idx = 0
        self.running = True
        self.last_time = pygame.time.get_ticks()
        self.hud = HUDRenderer(font)
        
        self.spawn_maps()

    def spawn_maps(self):
        """
        生成所有地图
        """
        for i in range(MAP_COUNT):
            is_final = (i == MAP_COUNT - 1)
            gm = GameMap(i, is_final=is_final, images=self.images)
            self.maps.append(gm)

    @property
    def curmap(self):
        """
        获取当前地图
        
        Returns:
            当前游戏地图对象
        """
        return self.maps[self.current_map_idx]

    def update(self, dt):
        """
        更新游戏逻辑
        
        Args:
            dt: 帧时间差(ms)
        """
        now = pygame.time.get_ticks()
        
        # ========== 处理输入 ==========
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_w]:
            dy -= self.player.speed
        if keys[pygame.K_s]:
            dy += self.player.speed
        if keys[pygame.K_a]:
            dx -= self.player.speed
        if keys[pygame.K_d]:
            dx += self.player.speed
        
        # 对角线速度归一化
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        
        self.player.move(dx, dy)
        # 更新玩家视觉计时（后坐力/闪光），dt 为毫秒
        try:
            self.player.update(dt)
        except Exception:
            pass

        # ========== 射击 ==========
        mpressed = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        if mpressed[0]:
            res = self.player.try_shoot(mouse_pos, now)
            if res:
                if isinstance(res, list):
                    self.bullets.extend(res)
                else:
                    self.bullets.append(res)
        # 近战（右键或 E）
        if mpressed[2]:
            melee_res = self.player.try_melee(now, self.curmap.enemies, self.bullets)
            if melee_res:
                hit_enemies, reflected = melee_res
                # 处理击杀奖励的金币
                for e in hit_enemies:
                    if not e.alive:
                        self.player.money += getattr(e, 'money', MONEY_PER_ENEMY)

        # ========== 更新敌人 ==========
        for e in self.curmap.enemies:
            if e.alive:
                e.update(dt)
                b = e.try_shoot(self.player, now)
                if b:
                    if isinstance(b, list):
                        self.bullets.extend(b)
                    else:
                        self.bullets.append(b)

        # 当所有敌人被清除后（包含最终地图的 boss 被清除），生成传送门
        if self.curmap.portal is None:
            if all(not e.alive for e in self.curmap.enemies):
                try:
                    self.curmap.spawn_portal()
                except Exception:
                    pass

        # ========== 更新子弹 ==========
        for b in self.bullets:
            b.update(dt)
        self.bullets = [b for b in self.bullets if b.alive]

        # ========== 子弹碰撞检测 ==========
        for b in self.bullets:
            if b.owner == 'player':
                # 玩家子弹与敌人碰撞
                for e in self.curmap.enemies:
                    if e.alive and b.rect.colliderect(e.rect):
                        e.hp -= b.damage
                        b.alive = False
                        if e.hp <= 0:
                            e.alive = False
                            self.player.money += getattr(e, 'money', MONEY_PER_ENEMY)
                        break
            else:
                # 敌人子弹与玩家碰撞
                if b.rect.colliderect(self.player.rect):
                    self.player.hp -= b.damage
                    b.alive = False

        # ========== 检测传送门碰撞 ==========
        if self.curmap.portal and self.player.rect.colliderect(self.curmap.portal):
            if self.curmap.is_final:
                # 最终地图：传送门表示击败 Boss 后的撤离出口，触发胜利
                self.victory()
            else:
                self.switch_map()

        # ========== 检测撤离点碰撞 ==========
        if self.curmap.is_final and self.curmap.exit_rect and \
           self.player.rect.colliderect(self.curmap.exit_rect):
            self.victory()

        # ========== 玩家死亡检测 ==========
        if self.player.hp <= 0:
            self.game_over()

    def switch_map(self):
        """
        切换到下一个地图
        """
        if self.current_map_idx < len(self.maps) - 1:
            # 为下一张地图显示商店；如果商店操作完成，就切换地图
            self.open_shop()

    def open_shop(self):
        """
        在切换地图时显示武器购买界面（暂停游戏循环）
        玩家可以购买或装备武器，然后点击开始下一张地图
        """
        entries = list(SHOP_WEAPONS) + [ShopItem('Medkit', SHOP_MEDKIT_COST, desc=f'恢复 +{SHOP_MEDKIT_HEAL} HP', heal_amount=SHOP_MEDKIT_HEAL)]
        state = ShopState(self.player, entries)
        ui = ShopUI(self.font, self.bigfont, images=self.images, width=WIDTH, height=HEIGHT)
        ui.rebuild_layout(len(entries))

        running_shop = True
        while running_shop:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

                action = ui.handle_event(event)
                if not action:
                    continue
                if action.kind == 'start':
                    running_shop = False
                elif action.kind == 'buy' and action.idx is not None:
                    state.buy(action.idx)
                elif action.kind == 'upgrade' and action.idx is not None:
                    state.upgrade(action.idx)
                elif action.kind == 'equip' and action.idx is not None:
                    state.equip(action.idx)

            ui.draw(self.screen, state)
            pygame.display.flip()
            self.clock.tick(60)

        # 关闭商店后切换地图并重置玩家状态
        self.current_map_idx += 1
        self.player.rect.center = (80, 80)
        self.player.hp = min(PLAYER_MAX_HP, self.player.hp + 15)

    def victory(self):
        """
        游戏胜利，显示结算画面
        """
        total_money = self.player.money
        # 显示结算画面并提供操作：保存 / 返回菜单 / 重新开始
        title = '通关成功！'
        subtitle = f'总收益：¥{total_money}'
        action = self._end_screen(title, subtitle)
        # action 可能为 'save'/'menu'/'restart'
        # 若请求保存则执行
        if action == 'save':
            try:
                from game.save_manager import save_game
                save_game(self.player)
            except Exception:
                pass
            # 保存后返回菜单
            action = 'menu'
        # 离开到菜单或重开时停止音乐
        try:
            if self.music:
                self.music.stop()
        except Exception:
            pass
        # 标记结束并记录给调用方的结局动作
        self.running = False
        self.end_action = action
        return

    def game_over(self):
        """
        游戏失败，显示失败画面
        """
        title = '你阵亡了'
        subtitle = f'携带金钱：¥{self.player.money}'
        action = self._end_screen(title, subtitle)
        if action == 'save':
            try:
                from game.save_manager import save_game
                save_game(self.player)
            except Exception:
                pass
            action = 'menu'
        try:
            if self.music:
                self.music.stop()
        except Exception:
            pass
        self.running = False
        self.end_action = action
        return

    def _end_screen(self, title, subtitle):
        """渲染结算界面，含保存/回到菜单/重新开始按钮。

        返回值：'save' | 'menu' | 'restart'
        """
        # 构建按钮
        btn_w = 220
        btn_h = 48
        gap = 12
        cx = WIDTH // 2
        cy = HEIGHT // 2

        rect_save = pygame.Rect(cx - btn_w // 2, cy + 20, btn_w, btn_h)
        rect_menu = pygame.Rect(cx - btn_w // 2, cy + 20 + (btn_h + gap), btn_w, btn_h)
        rect_restart = pygame.Rect(cx - btn_w // 2, cy + 20 + 2 * (btn_h + gap), btn_w, btn_h)

        clock = pygame.time.Clock()
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return 'menu'
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        return 'menu'
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mx, my = ev.pos
                    if rect_save.collidepoint(mx, my):
                        return 'save'
                    if rect_menu.collidepoint(mx, my):
                        return 'menu'
                    if rect_restart.collidepoint(mx, my):
                        return 'restart'

            # 绘制覆盖层
            self.screen.fill((8, 8, 10))
            t_surf = self.bigfont.render(title, True, (220, 220, 220))
            sub_surf = self.font.render(subtitle, True, (200, 200, 200))
            self.screen.blit(t_surf, (WIDTH // 2 - t_surf.get_width() // 2, HEIGHT // 2 - 120))
            self.screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2, HEIGHT // 2 - 60))

            mx, my = pygame.mouse.get_pos()
            for rect, label, color in ((rect_save, '保存存档', (80, 140, 80)), (rect_menu, '返回主菜单', (100, 100, 160)), (rect_restart, '重新开始', (160, 80, 80))):
                hover = rect.collidepoint(mx, my)
                col = tuple(min(255, c + (30 if hover else 0)) for c in color)
                pygame.draw.rect(self.screen, col, rect, border_radius=6)
                lab = self.font.render(label, True, (255, 255, 255))
                self.screen.blit(lab, (rect.centerx - lab.get_width() // 2, rect.centery - lab.get_height() // 2))

            pygame.display.flip()
            clock.tick(60)

    def draw_hud(self):
        self.hud.draw(self.screen, self.player, self.current_map_idx, len(self.maps))

    def draw(self):
        """
        绘制整个游戏画面
        """
        # 绘制地图背景
        self.curmap.draw(self.screen)
        
        # 绘制敌人
        for e in self.curmap.enemies:
            if e.alive:
                e.draw(self.screen)
        
        # 绘制子弹
        for b in self.bullets:
            b.draw(self.screen)
        
        # 绘制玩家（在最上层）
        self.player.draw(self.screen)

        # 绘制传送门提示
        if self.curmap.portal:
            pygame.draw.circle(self.screen, (255, 255, 255), 
                             self.curmap.portal.center, 2)

        # 绘制HUD
        self.draw_hud()
        pygame.display.flip()

    def run(self):
        """
        主游戏循环
        """
        while self.running:
            dt = self.clock.tick(FPS)
            
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    try:
                        from game.save_manager import save_game
                        save_game(self.player)
                    except Exception:
                        pass
                        # 停止游戏循环并回到菜单（不退出进程）
                    try:
                        if self.music:
                            self.music.stop()
                    except Exception:
                        pass
                    self.running = False
                    self.end_action = 'menu'
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        try:
                            from game.save_manager import save_game
                            save_game(self.player)
                        except Exception:
                            pass
                        try:
                            if self.music:
                                self.music.stop()
                        except Exception:
                            pass
                        self.running = False
                        self.end_action = 'menu'
                        break
                    if event.key == pygame.K_e:
                        # 按键触发近战
                        now = pygame.time.get_ticks()
                        melee_res = self.player.try_melee(now, self.curmap.enemies, self.bullets)
                        if melee_res:
                            hit_enemies, reflected = melee_res
                            for e in hit_enemies:
                                if not e.alive:
                                    self.player.money += MONEY_PER_ENEMY
                    # 武器快捷选择（数字 1-9）
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        idx = event.key - pygame.K_1
                        self.player.equip_by_index(idx)

            # 更新逻辑
            self.update(dt)

            # 渲染
            self.draw()
        # 循环结束，返回记录的结局动作（如 'menu' 或 'restart'）
        return getattr(self, 'end_action', None)
