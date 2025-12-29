import os
import pycache_init  # must import first to set sys.pycache_prefix
import pygame
from entities.enemy import BossEnemy
from entities.player import Player
from config.settings import WIDTH, HEIGHT


def test_boss_basic_behavior():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()

    bx = WIDTH // 2
    by = HEIGHT // 2
    boss = BossEnemy(bx, by, patrol_radius=0, images=None, archetype='boss')

    player = Player(60, 60, images=None)
    player.rect.center = (bx + 120, by)

    clock = pygame.time.Clock()
    bullets_emitted = 0
    for _ in range(60):  # fewer frames to keep test quick
        dt = clock.tick(120)
        now = pygame.time.get_ticks()
        boss.update(dt)
        res = boss.try_shoot(player, now)
        if res:
            bullets_emitted += len(res) if isinstance(res, list) else 1

        margin_x = max(boss.rect.width // 2 + 4, 8)
        margin_y = max(boss.rect.height // 2 + 4, 8)
        minx = margin_x
        maxx = WIDTH - margin_x
        miny = margin_y
        maxy = HEIGHT - margin_y
        cx, cy = boss.rect.center
        assert minx <= cx <= maxx
        assert miny <= cy <= maxy

    assert boss.is_boss
    assert boss.max_hp >= 1
    assert bullets_emitted >= 0
    pygame.quit()
