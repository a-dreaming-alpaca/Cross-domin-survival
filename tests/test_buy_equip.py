import pycache_init  # must import first to set sys.pycache_prefix
from entities.player import Player
from entities.weapons import SHOP_WEAPONS


def test_buy_and_equip_shotgun():
    p = Player(0, 0)
    p.money = 1000

    ok = p.buy_weapon(SHOP_WEAPONS[1])
    assert ok is True

    names = [w.name for w in p.inventory]
    assert SHOP_WEAPONS[1].name in names

    # equip by found index (by name to avoid object identity issues)
    idx = names.index(SHOP_WEAPONS[1].name)
    assert p.equip_by_index(idx) is True
    assert p.inventory[p.equipped_idx].name == SHOP_WEAPONS[1].name
