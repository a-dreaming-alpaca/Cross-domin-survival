"""商店 UI 模块：负责武器商店的布局、渲染与输入处理。

将 UI 逻辑与 `Game` 解耦，以便于维护与测试。
"""

from dataclasses import dataclass
from typing import Optional, Sequence, Any
import pygame
from config.settings import get_weapon_upgrade_cfg


@dataclass
class ShopAction:
    """商店 UI 发出的语义化操作。"""
    kind: str  # 'start', 'buy', 'equip', 'upgrade'
    idx: Optional[int] = None


@dataclass
class ShopItem:
    """消耗品或非武器的商店条目（例如医疗包）。"""
    name: str
    cost: int
    desc: str = ''
    heal_amount: int = 0
    type: str = 'item'


class ShopState:
    """商店交互的纯逻辑封装（购买/装备/升级）。"""

    def __init__(self, player, items: Sequence[Any]):
        self.player = player
        self.items = list(items)

    def owned(self, idx: int) -> bool:
        entry = self.items[idx]
        # 消耗品不计为拥有
        if getattr(entry, 'type', '') == 'item':
            return False
        return self.player.has_weapon(getattr(entry, 'name', None))

    def equipped(self, idx: int) -> bool:
        try:
            entry = self.items[idx]
            if getattr(entry, 'type', '') == 'item':
                return False
            if not self.owned(idx):
                return False
            inv_idx = self.player.find_weapon_index(getattr(entry, 'name', None))
            return inv_idx is not None and self.player.equipped_idx == inv_idx
        except Exception:
            return False

    def buy(self, idx: int) -> bool:
        entry = self.items[idx]
        cost = getattr(entry, 'cost', 0)
        if self.player.money < cost:
            return False
        # 消耗品：立即生效的恢复道具
        if getattr(entry, 'type', '') == 'item':
            self.player.money -= cost
            try:
                self.player.heal(getattr(entry, 'heal_amount', 0))
            except Exception:
                pass
            return True
        # 武器购买流程
        if self.player.has_weapon(getattr(entry, 'name', None)):
            return False
        ok = self.player.buy_weapon(entry)
        if ok:
            try:
                inv_idx = self.player.find_weapon_index(getattr(entry, 'name', None))
                if inv_idx is not None:
                    self.player.equip_by_index(inv_idx)
            except Exception:
                pass
        return ok

    def equip(self, idx: int) -> bool:
        entry = self.items[idx]
        if getattr(entry, 'type', '') == 'item':
            return False
        if not self.player.has_weapon(getattr(entry, 'name', None)):
            return False
        try:
            inv_idx = self.player.find_weapon_index(getattr(entry, 'name', None))
        except Exception:
            return False
        if inv_idx is None:
            return False
        return self.player.equip_by_index(inv_idx)

    # ---------- 升级辅助方法 ----------
    def upgrade_level(self, idx: int) -> int:
        entry = self.items[idx]
        return self.player.weapon_levels.get(getattr(entry, 'name', ''), 0)

    def upgrade_next_cost(self, idx: int) -> Optional[int]:
        entry = self.items[idx]
        if getattr(entry, 'type', '') == 'item':
            return None
        cfg = get_weapon_upgrade_cfg(getattr(entry, 'name', ''))
        if not cfg:
            return None
        lvl = self.upgrade_level(idx)
        max_lvl = cfg.get('max_level', 0)
        if lvl >= max_lvl:
            return None
        costs = cfg.get('costs', [])
        if len(costs) > lvl + 1:
            return costs[lvl + 1]
        return None

    def upgrade(self, idx: int) -> bool:
        entry = self.items[idx]
        if getattr(entry, 'type', '') == 'item':
            return False
        cfg = get_weapon_upgrade_cfg(getattr(entry, 'name', ''))
        if not cfg:
            return False
        if not self.player.has_weapon(getattr(entry, 'name', None)):
            return False
        lvl = self.upgrade_level(idx)
        max_lvl = cfg.get('max_level', 0)
        if lvl >= max_lvl:
            return False
        costs = cfg.get('costs', [])
        if len(costs) <= lvl + 1:
            return False
        price = costs[lvl + 1]
        if self.player.money < price:
            return False
        self.player.money -= price
        self.player.set_weapon_upgrade_level(entry.name, lvl + 1)
        return True


class ShopUI:
    """负责商店的布局计算、渲染与输入映射。"""

    def __init__(self, font, bigfont, images=None, width: int = 960, height: int = 640):
        self.font = font
        self.bigfont = bigfont
        self.images = images
        self.width = width
        self.height = height

        # 基础布局度量
        self.box_w = 780
        self.item_h = 60
        self.spacing = 12
        self.margin_top = 30
        self.min_box_h = 420

        # 在 `rebuild_layout` 中填充的 Surface 与 Rect
        self.overlay = pygame.Surface((self.width, self.height))
        self.overlay.set_alpha(200)
        self.overlay.fill((10, 10, 10))

        self.box_h = self.min_box_h
        self.box_x = 0
        self.box_y = 0
        self.start_y = 0
        self.shop_bg = None
        self.start_img = None
        self.start_rect = None
        self.buy_rects = []
        self.equip_rects = []
        self.upgrade_rects = []

    def rebuild_layout(self, weapon_count: int):
        """根据武器数量计算布局和相关 Surface。"""
        content_h = self.margin_top + weapon_count * (self.item_h + self.spacing) + 100
        self.box_h = max(self.min_box_h, content_h)
        self.box_x = (self.width - self.box_w) // 2
        self.box_y = (self.height - self.box_h) // 2
        self.start_y = self.box_y + self.margin_top

        # 面板右下的开始按钮
        self.start_rect = pygame.Rect(self.box_x + self.box_w - 170, self.box_y + self.box_h - 60, 140, 40)

        # background and start button sprites
        if self.images:
            self.shop_bg = self.images.get('ui/shop_bg', scale=(self.box_w, self.box_h), fallback_size=(self.box_w, self.box_h), fallback_color=(40, 40, 48))
            self.start_img = self.images.get('ui/button_start', scale=(self.start_rect.width, self.start_rect.height), fallback_size=(self.start_rect.width, self.start_rect.height), fallback_color=(120, 70, 70))
        else:
            self.shop_bg = None
            self.start_img = None

        # 为每个武器行预构建按钮的 Rect
        self.buy_rects = []
        self.equip_rects = []
        self.upgrade_rects = []
        for idx in range(weapon_count):
            iy = self.start_y + idx * (self.item_h + self.spacing)
            buy_rect = pygame.Rect(self.box_x + 380, iy + 10, 110, 40)
            upgrade_rect = pygame.Rect(self.box_x + 500, iy + 10, 110, 40)
            equip_rect = pygame.Rect(self.box_x + 620, iy + 10, 120, 40)
            self.buy_rects.append(buy_rect)
            self.upgrade_rects.append(upgrade_rect)
            self.equip_rects.append(equip_rect)

    def handle_event(self, event) -> Optional[ShopAction]:
        """将 pygame 事件转换为语义化的商店操作。"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return ShopAction('start')
        if event.type == pygame.MOUSEBUTTONDOWN:
            if hasattr(event, 'pos'):
                mx, my = event.pos
            else:
                mx, my = pygame.mouse.get_pos()
            if self.start_rect and self.start_rect.collidepoint(mx, my):
                return ShopAction('start')
            for idx, (brect, erect) in enumerate(zip(self.buy_rects, self.equip_rects)):
                if brect.collidepoint(mx, my):
                    return ShopAction('buy', idx)
                if self.upgrade_rects[idx].collidepoint(mx, my):
                    return ShopAction('upgrade', idx)
                if erect.collidepoint(mx, my):
                    return ShopAction('equip', idx)
        return None

    def draw(self, surface, state: ShopState):
        """根据给定 `state` 渲染商店 UI。"""
        entries = state.items
        surface.blit(self.overlay, (0, 0))

        # 面板背景
        if self.shop_bg:
            surface.blit(self.shop_bg, (self.box_x, self.box_y))
        else:
            pygame.draw.rect(surface, (40, 40, 48), (self.box_x, self.box_y, self.box_w, self.box_h))

        # 商店标题
        title = self.font.render('商店 - 购买装备', True, (240, 240, 240))
        surface.blit(title, (self.box_x + 18, self.box_y))

        # 武器列表
        item_w = self.box_w - 40
        for idx, entry in enumerate(entries):
            iy = self.start_y + idx * (self.item_h + self.spacing)
            pygame.draw.rect(surface, (28, 28, 36), (self.box_x + 20, iy, item_w, self.item_h))
            name_s = self.font.render(f'{entry.name} - ¥{getattr(entry, "cost", 0)}', True, (220, 220, 220))
            surface.blit(name_s, (self.box_x + 28, iy + 8))
            desc_s = self.font.render(getattr(entry, 'desc', ''), True, (180, 180, 180))
            surface.blit(desc_s, (self.box_x + 28, iy + 32))

            # 等级信息
            if getattr(entry, 'type', '') != 'item':
                lvl = state.upgrade_level(idx)
                cfg = get_weapon_upgrade_cfg(getattr(entry, 'name', ''))
                max_lvl = cfg.get('max_level', 0) if cfg else 0
                lvl_text = f'Lv{lvl}/{max_lvl}' if max_lvl else f'Lv{lvl}'
                surface.blit(self.font.render(lvl_text, True, (200, 255, 200)), (self.box_x + 260, iy + 12))

            # 购买和装备按钮
            buy_rect = self.buy_rects[idx]
            equip_rect = self.equip_rects[idx]
            upgrade_rect = self.upgrade_rects[idx]
            pygame.draw.rect(surface, (70, 120, 70), buy_rect)
            pygame.draw.rect(surface, (120, 110, 60), upgrade_rect)
            pygame.draw.rect(surface, (70, 70, 120), equip_rect)

            is_item = getattr(entry, 'type', '') == 'item'
            owned = state.owned(idx)
            equipped = state.equipped(idx)
            buy_label = '购买/使用' if is_item else ('购买' if not owned else '已拥有')
            surface.blit(self.font.render(buy_label, True, (255, 255, 255)), (buy_rect.x + 12, buy_rect.y + 12))
            # 升级按钮
            if is_item:
                pygame.draw.rect(surface, (60, 60, 80), upgrade_rect)
                surface.blit(self.font.render('N/A', True, (180, 180, 180)), (upgrade_rect.x + 28, upgrade_rect.y + 12))
            else:
                next_cost = state.upgrade_next_cost(idx)
                if next_cost is None:
                    pygame.draw.rect(surface, (60, 60, 60), upgrade_rect)
                    surface.blit(self.font.render('满级', True, (200, 200, 200)), (upgrade_rect.x + 26, upgrade_rect.y + 12))
                else:
                    surface.blit(self.font.render(f'升级 ¥{next_cost}', True, (255, 255, 255)), (upgrade_rect.x + 4, upgrade_rect.y + 12))
            if is_item:
                pygame.draw.rect(surface, (60, 60, 80), equip_rect)
                surface.blit(self.font.render('N/A', True, (180, 180, 180)), (equip_rect.x + 36, equip_rect.y + 12))
            else:
                equip_label = '已装备' if equipped else '装备'
                equip_color = (40, 140, 40) if equipped else (255, 255, 255)
                surface.blit(self.font.render(equip_label, True, equip_color), (equip_rect.x + 18, equip_rect.y + 12))

        # 库存和资金
        list_bottom = self.start_y + len(entries) * (self.item_h + self.spacing)
        inv_y = list_bottom + 10
        inv_str = '持有武器: ' + ', '.join([w.name for w in state.player.inventory])
        surface.blit(self.font.render(inv_str, True, (200, 200, 200)), (self.box_x + 28, inv_y))
        money_s = self.font.render(f'金钱: ¥{state.player.money}', True, (255, 235, 120))
        surface.blit(money_s, (self.box_x + self.box_w - 220, inv_y))

        # 开始按钮
        if self.start_img:
            surface.blit(self.start_img, self.start_rect.topleft)
        else:
            pygame.draw.rect(surface, (120, 70, 70), self.start_rect)
        surface.blit(self.font.render('开始下一图', True, (255, 255, 255)), (self.start_rect.x + 18, self.start_rect.y + 10))
