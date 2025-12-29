import os
import pycache_init  # must import first to set sys.pycache_prefix
from copy import copy
from game import save_manager
from entities.player import Player
from entities.weapons import SHOP_WEAPONS


def test_save_and_load_weapon_levels(tmp_path):
    player = Player(0, 0)
    player.money = 1484  # after buying shotgun (250) remains 1234
    player.hp = 77
    # add shotgun and set upgrade level
    player.buy_weapon(SHOP_WEAPONS[1])
    player.set_weapon_upgrade_level(SHOP_WEAPONS[1].name, 2)

    save_file = tmp_path / "savegame.json"
    ok = save_manager.save_game(player, filename=str(save_file))
    assert ok is True

    loaded = save_manager.load_game(filename=str(save_file))
    assert loaded is not None
    assert loaded.get('money') == 1234
    assert loaded.get('hp') == 77
    assert loaded.get('weapon_levels', {}).get(SHOP_WEAPONS[1].name) == 2

    inv_objs = loaded.get('inventory_objs', [])
    names = [getattr(w, 'name', '') for w in inv_objs]
    assert SHOP_WEAPONS[1].name in names
