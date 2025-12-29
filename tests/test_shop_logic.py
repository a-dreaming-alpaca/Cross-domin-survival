import os
import pycache_init  # must import first to set sys.pycache_prefix
import pygame
import pytest

from game.shop_ui import ShopState, ShopItem
from entities.player import Player
from entities.weapons import SHOP_WEAPONS
from config.settings import get_weapon_upgrade_cfg


@pytest.fixture(autouse=True)
def init_pygame():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    yield
    pygame.quit()


def make_state(player):
    # mirror Game.open_shop ordering: weapons + medkit at the end
    items = list(SHOP_WEAPONS) + [ShopItem('Medkit', 120, desc='heal', heal_amount=45)]
    return ShopState(player, items)


def test_buy_requires_money():
    player = Player(0, 0)
    player.money = 0
    state = make_state(player)
    idx = 1  # Shotgun

    assert state.buy(idx) is False
    assert len([w for w in player.inventory if w.name == SHOP_WEAPONS[idx].name]) == 0


def test_buy_equips_first_time_and_blocks_duplicate():
    player = Player(0, 0)
    player.money = 2000
    state = make_state(player)
    idx = 1  # Shotgun

    assert state.buy(idx) is True
    names = [w.name for w in player.inventory]
    assert SHOP_WEAPONS[idx].name in names

    # should auto-equip the newly bought weapon
    assert player.inventory[player.equipped_idx].name == SHOP_WEAPONS[idx].name

    # duplicate buy is blocked
    before_money = player.money
    assert state.buy(idx) is False
    assert player.money == before_money
    assert names.count(SHOP_WEAPONS[idx].name) == 1


def test_upgrade_increments_level_and_costs_money():
    player = Player(0, 0)
    player.money = 5000
    state = make_state(player)
    idx = 1  # Shotgun

    cfg = get_weapon_upgrade_cfg(SHOP_WEAPONS[idx].name)
    if not cfg:
        pytest.skip("No upgrade config for weapon")
    cost_next = cfg['costs'][1]

    assert state.buy(idx) is True
    w = next(w for w in player.inventory if w.name == SHOP_WEAPONS[idx].name)
    base_cd = getattr(w, 'cooldown', None)

    before_money = player.money
    assert state.upgrade(idx) is True
    assert player.weapon_levels[SHOP_WEAPONS[idx].name] == 1
    assert player.money == before_money - cost_next

    w_after = next(w for w in player.inventory if w.name == SHOP_WEAPONS[idx].name)
    if base_cd is not None:
        # upgrade通常降低冷却，若配置无变化则允许相等
        assert w_after.cooldown <= base_cd
