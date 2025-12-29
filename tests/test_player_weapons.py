import os
from copy import copy
import pycache_init  # must import first to set sys.pycache_prefix
import pygame
import pytest

from entities.player import Player
from entities.weapons import SHOP_WEAPONS
from entities.bullet import Bullet


@pytest.fixture(autouse=True)
def init_pygame():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    yield
    pygame.quit()


def test_shoot_cooldown_and_pellets():
    player = Player(0, 0)
    shotgun = copy(SHOP_WEAPONS[1])  # pellets=5
    player.inventory = [shotgun]
    player.equipped_idx = 0
    player.last_shot = -9999

    now = 0
    shots = player.try_shoot((100, 100), now)
    assert isinstance(shots, list)
    assert len(shots) == shotgun.pellets

    # within cooldown should not fire
    blocked = player.try_shoot((100, 100), now + 10)
    assert blocked is None

    # after cooldown it should fire again
    resumed = player.try_shoot((100, 100), now + shotgun.cooldown + 1)
    assert resumed is not None


def test_melee_reflects_enemy_bullet():
    player = Player(0, 0)
    reflector = copy(SHOP_WEAPONS[4])  # Reflector Sword
    player.inventory = [reflector]
    player.equipped_idx = 0
    player.last_melee = -9999

    enemy_bullet = Bullet(player.rect.center, (1, 0), 5, owner='enemy', damage=10, max_range=50)
    res = player.try_melee(0, enemies=[], bullets=[enemy_bullet])
    assert res is not None
    hit_enemies, reflected = res
    assert len(reflected) == 1
    assert reflected[0].owner == 'player'
