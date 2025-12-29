"""HUD 绘制组件。"""

import pygame
from config import settings


class HUDRenderer:
    def __init__(self, font):
        self.font = font

    def draw(self, surf, player, current_map_idx, total_maps):
        pad = getattr(settings, 'UI_HUD_PADDING', 10)
        color_text = getattr(settings, 'UI_COLOR_TEXT', (255, 255, 255))
        color_money = getattr(settings, 'UI_COLOR_MONEY', (255, 235, 120))
        color_secondary = getattr(settings, 'UI_COLOR_TEXT_SECONDARY', (200, 200, 200))

        hp_surf = self.font.render(f'HP: {player.hp}', True, color_text)
        money_surf = self.font.render(f'¥{player.money}', True, color_money)
        map_surf = self.font.render(
            f'Map {current_map_idx + 1}/{total_maps}',
            True,
            color_secondary,
        )
        try:
            wname = player.inventory[player.equipped_idx].name
        except Exception:
            wname = 'None'
        weapon_surf = self.font.render(f'Weapon: {wname}', True, color_secondary)

        y = pad
        surf.blit(hp_surf, (pad, y)); y += hp_surf.get_height() + 4
        surf.blit(money_surf, (pad, y)); y += money_surf.get_height() + 4
        surf.blit(map_surf, (pad, y)); y += map_surf.get_height() + 4
        surf.blit(weapon_surf, (pad, y))
