import os
import pycache_init  # must import first to set sys.pycache_prefix
import pygame
from game.game import Game
from entities.weapons import SHOP_WEAPONS
from config.settings import WIDTH, HEIGHT


def test_shop_click_buys_shotgun():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    font = pygame.font.SysFont('Microsoft YaHei', 24)
    bigfont = pygame.font.SysFont('Microsoft YaHei', 48)
    clock = pygame.time.Clock()

    g = Game(screen, clock, font, bigfont)
    g.player.money = 1000

    # compute coordinates for the Shotgun (index 1) buy button
    weapon_count = len(SHOP_WEAPONS) + 1  # weapons + medkit
    box_w = 780
    item_h = 60
    spacing = 12
    margin_top = 30
    content_h = margin_top + weapon_count * (item_h + spacing) + 100
    box_h = max(420, content_h)
    box_x = (WIDTH - box_w) // 2
    box_y = (HEIGHT - box_h) // 2
    start_y = box_y + margin_top
    idx = 1  # shotgun in SHOP_WEAPONS
    iy = start_y + idx * (item_h + spacing)
    buy_rect = pygame.Rect(box_x + 380, iy + 10, 110, 40)
    center = buy_rect.center

    # click buy and then exit shop
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': center, 'button': 1}))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': center, 'button': 1}))
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RETURN}))

    g.open_shop()

    names = [w.name for w in g.player.inventory]
    assert SHOP_WEAPONS[1].name in names
    pygame.quit()
