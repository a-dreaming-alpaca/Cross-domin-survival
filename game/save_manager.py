"""简单的 JSON 存档加载管理器。

默认保存到项目根目录下的 `save/savegame.json`。
存储字段：money、hp、equipped_idx、inventory（武器名列表）、saved_at（时间戳）。
"""

import os
import json
from datetime import datetime, timezone

from entities.weapons import SHOP_WEAPONS


SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'save')
SAVE_FILE = os.path.join(SAVE_DIR, 'savegame.json')


def ensure_save_dir():
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
    except Exception:
        pass


def save_game(player, filename=SAVE_FILE):
        """将相关玩家状态保存为 JSON。

        说明：此函数保存最小化快照用于载入。默认写入 `save/savegame.json`。
        保存字段：
            - money: 玩家金钱
            - hp: 当前生命值（可为 None 表示不保存）
            - equipped_idx: 装备索引
            - inventory: 武器名列表（加载时将按 `entities.weapons.SHOP_WEAPONS` 名称匹配重建）
            - weapon_levels: 武器升级等级映射（name -> level）
            - saved_at: ISO UTC 时间戳

        加载器会尝试根据保存的武器名从 `SHOP_WEAPONS` 中重建武器对象并浅拷贝到玩家背包，
        以保持存档体积小且可读。
        """
        ensure_save_dir()
        data = {
            'money': getattr(player, 'money', 0),
            'hp': getattr(player, 'hp', None),
            'equipped_idx': getattr(player, 'equipped_idx', 0),
            'inventory': [getattr(w, 'name', str(w)) for w in getattr(player, 'inventory', [])],
            'weapon_levels': getattr(player, 'weapon_levels', {}),
            'saved_at': datetime.now(timezone.utc).isoformat()
        }
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False


def load_game(filename=SAVE_FILE):
    """加载存档并根据武器名从 `SHOP_WEAPONS` 重建最小化的武器对象。

    返回包含保存字段的字典（包括 `inventory_objs` 列表，该列表为重建的武器对象），
    如果存档缺失或无效则返回 `None`。

    调用方应将其视为权威快照并只应用所需字段（如 money/hp/inventory/equipped_idx）到 `Player`。
    """
    if not os.path.exists(filename):
        return None
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return None

    # 从SHOP_WEAPONS重建库存
    names = data.get('inventory', [])
    reconstructed = []
    for n in names:
        found = None
        for w in SHOP_WEAPONS:
            if getattr(w, 'name', '') == n:
                # 制作一个浅拷贝以避免共享状态
                try:
                    from copy import copy
                    found = copy(w)
                except Exception:
                    found = w
                break
        if found is not None:
            reconstructed.append(found)
    data['inventory_objs'] = reconstructed
    # 确保weapon_levels存在
    if 'weapon_levels' not in data or not isinstance(data.get('weapon_levels'), dict):
        data['weapon_levels'] = {}
    return data
