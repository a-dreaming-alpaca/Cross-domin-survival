"""开始界面（Start Menu）组件。

重构目标：
- 明确状态（menu/settings/message），减少嵌套循环。
- 复用预计算背景/布局，避免重复创建 Surface。
- 统一输入处理：键盘、鼠标都映射到选项 id。
"""

import pygame
from config import settings


class StartMenu:
    def __init__(self, screen, font, bigfont, images=None, width=800, height=600, music=None):
        self.screen = screen
        self.font = font
        self.bigfont = bigfont
        self.images = images
        self.music = music
        self.width = width
        self.height = height

        self.bg_color = getattr(settings, 'UI_COLOR_BG', (12, 12, 16))
        self.title_color = getattr(settings, 'UI_COLOR_TITLE', (200, 240, 200))
        self.btn_color = getattr(settings, 'UI_COLOR_BTN', (40, 40, 48))
        self.btn_hover = getattr(settings, 'UI_COLOR_BTN_HOVER', (70, 70, 90))
        self.text_color = getattr(settings, 'UI_COLOR_TEXT', (255, 255, 255))

        self.title = getattr(settings, 'WINDOW_TITLE', 'Game')
        # (id, label)
        self.options = [
            ('new', '新游戏'),
            ('load', '载入存档'),
            ('settings', '设置'),
            ('quit', '退出'),
        ]
        self.selected = 0

        self.btn_width = min(420, int(self.width * 0.64))
        self.btn_height = 54
        self.btn_gap = 14

        self.fade_alpha = 0
        self.state = 'menu'  # menu | settings | message
        self.message_until = 0
        self.message_text = None

        self._bg_surf = self._build_background()
        self.particles = []
        self._spawn_particles(42)

    # ----------------- 布局辅助工具 -----------------
    def _panel_rect(self):
        panel_w = int(self.width * 0.66)
        panel_h = int(self.height * 0.5)
        px = self.width // 2 - panel_w // 2
        py = self.height // 2 - panel_h // 2 + 20
        return pygame.Rect(px, py, panel_w, panel_h)

    def _button_rect(self, idx):
        panel = self._panel_rect()
        total_h = len(self.options) * self.btn_height + (len(self.options) - 1) * self.btn_gap
        start_y = panel.top + 40 + (panel.height // 2 - total_h // 2)
        x = panel.left + panel.width // 2 - self.btn_width // 2
        y = start_y + idx * (self.btn_height + self.btn_gap)
        return pygame.Rect(x, y, self.btn_width, self.btn_height)

    # ----------------- 视觉工具 -----------------
    def _build_background(self):
        # 如果有则选择图片
        if self.images:
            try:
                surf = self.images.get('menu_bg', scale=(self.width, self.height))
                if surf:
                    return surf
            except Exception:
                pass
        # 备用渐变
        top = (18, 24, 36)
        bottom = (6, 12, 22)
        surf = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            r = int(top[0] * (1 - t) + bottom[0] * t)
            g = int(top[1] * (1 - t) + bottom[1] * t)
            b = int(top[2] * (1 - t) + bottom[2] * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.width, y))
        return surf

    def _spawn_particles(self, count=32):
        import random
        for _ in range(count):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            vy = random.uniform(-0.05, -0.4)
            size = random.randint(1, 3)
            self.particles.append({'x': x, 'y': y, 'vy': vy, 'size': size, 'alpha': random.randint(30, 120)})

    def _update_particles(self, dt):
        for p in self.particles:
            p['y'] += p['vy'] * dt
            if p['y'] < -12:
                p['y'] = self.height + 12

    def _draw_particles(self):
        for p in self.particles:
            col = (255, 255, 255, p['alpha'])
            s = pygame.Surface((p['size'] * 2, p['size'] * 2), flags=pygame.SRCALPHA)
            pygame.draw.circle(s, col, (p['size'], p['size']), p['size'])
            self.screen.blit(s, (int(p['x']), int(p['y'])))

    # ----------------- input -----------------
    def _option_id(self, idx):
        return self.options[idx][0]

    def _handle_menu_event(self, event):
        if event.type == pygame.QUIT:
            return 'quit'
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'quit'
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self._option_id(self.selected)
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            if event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            for i in range(len(self.options)):
                if self._button_rect(i).collidepoint(mx, my):
                    self.selected = i
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for i in range(len(self.options)):
                if self._button_rect(i).collidepoint(mx, my):
                    return self._option_id(i)
        return None

    # ----------------- 渲染 -----------------
    def draw(self, dt=16):
        self.fade_alpha = min(255, self.fade_alpha + int(dt * 0.5))
        self._update_particles(dt)

        bg = self._bg_surf.copy()
        tint = pygame.Surface((self.width, self.height), flags=pygame.SRCALPHA)
        tint.fill((10, 8, 12, 60))
        bg.blit(tint, (0, 0))
        self.screen.blit(bg, (0, 0))
        self._draw_particles()

        panel_rect = self._panel_rect()
        panel = pygame.Surface((panel_rect.width, panel_rect.height), flags=pygame.SRCALPHA)
        panel.fill((8, 8, 12, 150))
        self.screen.blit(panel, panel_rect.topleft)

        title_surf = self.bigfont.render(self.title, True, self.title_color)
        title_surf.set_alpha(self.fade_alpha)
        self.screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, panel_rect.top + 16))

        hint = 'WASD 移动，鼠标瞄准并左键射击'
        hint_surf = self.font.render(hint, True, self.text_color)
        hint_surf.set_alpha(self.fade_alpha)
        self.screen.blit(hint_surf, (self.width // 2 - hint_surf.get_width() // 2, panel_rect.top + 16 + title_surf.get_height() + 6))

        mx, my = pygame.mouse.get_pos()
        for i, (_, label) in enumerate(self.options):
            rect = self._button_rect(i)
            hover = rect.collidepoint(mx, my) or (i == self.selected)
            color = self.btn_hover if hover else self.btn_color
            btn_surf = pygame.Surface((rect.w, rect.h), flags=pygame.SRCALPHA)
            btn_surf.fill(color + (220,))
            btn_surf.set_alpha(self.fade_alpha)
            pygame.draw.rect(btn_surf, color, btn_surf.get_rect(), border_radius=6)
            self.screen.blit(btn_surf, rect.topleft)
            text_surf = self.font.render(label, True, self.text_color)
            text_surf.set_alpha(self.fade_alpha)
            self.screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2, rect.centery - text_surf.get_height() // 2))

        # 信息覆盖 (e.g., load failed)
        if self.state == 'message' and self.message_text:
            overlay = pygame.Surface((self.width, self.height), flags=pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 90))
            self.screen.blit(overlay, (0, 0))
            msg = self.font.render(self.message_text, True, (255, 200, 100))
            self.screen.blit(msg, (self.width // 2 - msg.get_width() // 2, self.height // 2 + 80))

        pygame.display.flip()

    # ----------------- 时间流更新 -----------------
    def run(self, clock, fps=60):
        running = True
        while running:
            dt = clock.tick(fps)
            now = pygame.time.get_ticks()
            if self.state == 'message' and now >= self.message_until:
                self.state = 'menu'
                self.message_text = None

            for event in pygame.event.get():
                if self.state == 'menu':
                    res = self._handle_menu_event(event)
                    if res == 'new':
                        return ('new', None)
                    if res == 'load':
                        payload = self._try_load_save()
                        if payload is not None:
                            return ('load', payload)
                    if res == 'settings':
                        self._settings_loop(clock, fps)
                    if res == 'quit':
                        return ('quit', None)
                elif self.state == 'settings':
                    # 设置在其自身的循环中运行；退出时会将状态重置为菜单
                    pass
            self.draw(dt)

    def _try_load_save(self):
        try:
            from game.save_manager import load_game
            state = load_game()
            if state:
                return state
            self._show_temp_message('未找到存档', 1200)
        except Exception:
            self._show_temp_message('载入失败', 1200)
        return None

    def _show_temp_message(self, text, ms=1200):
        self.state = 'message'
        self.message_text = text
        self.message_until = pygame.time.get_ticks() + ms

    def _settings_loop(self, clock, fps=60):
        self.state = 'settings'
        if not hasattr(self, 'settings_volume'):
            try:
                self.settings_volume = self.music.get_volume() if self.music else 0.6
            except Exception:
                self.settings_volume = 0.6
        try:
            if self.music:
                self.music.set_volume(self.settings_volume)
        except Exception:
            pass

        dragging = False
        slider_rect = pygame.Rect(self.width // 2 - 160, self.height // 2 + 20, 320, 10)
        while True:
            dt = clock.tick(fps)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.state = 'menu'
                    return
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        self.state = 'menu'
                        return
                    if ev.key == pygame.K_LEFT:
                        self.settings_volume = max(0.0, self.settings_volume - 0.05)
                        if self.music:
                            self.music.set_volume(self.settings_volume)
                    if ev.key == pygame.K_RIGHT:
                        self.settings_volume = min(1.0, self.settings_volume + 0.05)
                        if self.music:
                            self.music.set_volume(self.settings_volume)
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if slider_rect.collidepoint(ev.pos):
                        dragging = True
                if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                    dragging = False
                if ev.type == pygame.MOUSEMOTION and dragging:
                    mx = ev.pos[0]
                    t = (mx - slider_rect.left) / max(1, slider_rect.width)
                    self.settings_volume = max(0.0, min(1.0, t))
                    if self.music:
                        self.music.set_volume(self.settings_volume)

            # 绘制基础菜单和叠加滑块
            self.draw(dt)
            pygame.draw.rect(self.screen, (120, 120, 120), slider_rect)
            fill_w = int(slider_rect.width * self.settings_volume)
            pygame.draw.rect(self.screen, (200, 200, 60), (slider_rect.left, slider_rect.top, fill_w, slider_rect.height))
            vol_text = self.font.render(f'音量: {int(self.settings_volume*100)}%', True, (240, 240, 240))
            self.screen.blit(vol_text, (self.width // 2 - vol_text.get_width() // 2, slider_rect.top - 28))
            hint = self.font.render('按 ← → 调整，回车或Esc返回', True, (180, 180, 180))
            self.screen.blit(hint, (self.width // 2 - hint.get_width() // 2, slider_rect.bottom + 8))
            pygame.display.flip()
