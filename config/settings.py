"""
游戏配置常量模块
存放所有游戏的全局常量配置
"""

# ========== 窗口配置 ==========
WIDTH = 960
HEIGHT = 640
FPS = 60
WINDOW_TITLE = "Cross-Domain-Survival"

# ========== 玩家配置 ==========
PLAYER_SPEED = 4.0
PLAYER_SIZE = 36
PLAYER_MAX_HP = 100
PLAYER_FIRE_COOLDOWN = 250  # ms
PLAYER_MELEE_COOLDOWN = 400  # ms

# ========== 子弹配置 ==========
BULLET_SPEED = 9
BULLET_SIZE = 6
DEFAULT_BULLET_DAMAGE = 20
DEFAULT_BULLET_RANGE = 800  # px

# ========== 敌人配置 ==========
ENEMY_SIZE = 36
ENEMY_HP = 30
ENEMY_FIRE_COOLDOWN = 1200  # ms
ENEMY_DETECT_RANGE = 360
ENEMY_BULLET_DAMAGE = 12
ENEMY_ARCHETYPES = {
	# 基础小兵：手枪，常规射速/射程
	'grunt': {
		'hp': 30,
		'detect_range': 360,
		'fire_cooldown': 1200,
		'bullet_damage': 12,
		'weapon': 'basic pistol',
		'money': 150,
	},
	# 近距离压制：霰弹枪，稍快冷却
	'shotgunner': {
		'hp': 36,
		'detect_range': 340,
		'fire_cooldown': 900,
		'bullet_damage': 10,
		'weapon': 'shotgun',
		'money': 170,
	},
	# 精准火力：狙击，慢冷却高伤害
	'sniper': {
		'hp': 42,
		'detect_range': 460,
		'fire_cooldown': 1400,
		'bullet_damage': 32,
		'weapon': 'sniper rifle',
		'money': 200,
	},
	# Boss 示例配置：最终关卡专用
	'boss': {
		'hp': 600,
		'detect_range': 520,
		'fire_cooldown': 1400,
		'bullet_damage': 18,
		'weapon': 'heavy cannon',
		'money': 1500,
	},
}

# 每张地图的敌人类型权重（按索引取，超出则用最后一组）
ENEMY_SPAWN_WEIGHTS = [
	{'grunt': 1.0},
	{'grunt': 0.6, 'shotgunner': 0.4},
	{'grunt': 0.4, 'shotgunner': 0.35, 'sniper': 0.25},
	{'boss': 1.0},
]

# ========== 地图配置 ==========
MAP_COUNT = 4
RESOURCE_COUNT_PER_MAP = 0  # 地面资源已禁用

# Boss 大小（像素），可在此处调整 boss 体积
BOSS_SIZE = 96

# ========== 经济系统配置 ==========
MONEY_PER_RESOURCE = (10, 40)  # 保留数值以备启用
MONEY_PER_ENEMY = 150
SHOP_MEDKIT_COST = 120
SHOP_MEDKIT_HEAL = 45

# ========== 武器升级配置 ==========
# costs/damage_mult/cooldown_mult/range_add 均按等级索引（0 为基础等级）
# 升级仅对远程枪械生效
WEAPON_UPGRADE_CONFIG = {
	'Basic Pistol': {
		'max_level': 3,
		'costs': [0, 120, 220, 340],
		'damage_mult': [1.0, 1.15, 1.30, 1.50],
		'cooldown_mult': [1.0, 0.93, 0.90, 0.86],
		'range_add': [0, 40, 80, 120],
	},
	'Shotgun': {
		'max_level': 3,
		'costs': [0, 180, 260, 360],
		'damage_mult': [1.0, 1.10, 1.22, 1.35],
		'cooldown_mult': [1.0, 0.96, 0.93, 0.90],
		'range_add': [0, 20, 40, 70],
	},
	'Sniper Rifle': {
		'max_level': 3,
		'costs': [0, 240, 320, 420],
		'damage_mult': [1.0, 1.12, 1.25, 1.42],
		'cooldown_mult': [1.0, 0.97, 0.94, 0.90],
		'range_add': [0, 80, 140, 220],
	},
}


def get_weapon_upgrade_cfg(name):
	"""如果已定义，则返回武器名称对应的升级配置字典。"""
	return WEAPON_UPGRADE_CONFIG.get(name)

# ========== 颜色常量 ==========
COLOR_BACKGROUND = (28, 28, 36)
COLOR_PLAYER = (50, 140, 255)
COLOR_ENEMY = (220, 50, 50)
COLOR_PLAYER_BULLET = (255, 220, 50)
COLOR_ENEMY_BULLET = (255, 90, 90)
COLOR_RESOURCE = (255, 215, 110)
COLOR_PORTAL = (160, 80, 255)
COLOR_EXIT = (60, 200, 120)
COLOR_HP_BAR_BG = (200, 60, 60)
COLOR_HP_BAR_FG = (60, 200, 100)
COLOR_TEXT = (255, 255, 255)

# ========== UI 配置 ==========
# 全局 UI 颜色、间距、字体等
UI_FONT_NAMES = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS', 'NotoSansCJK', None]
UI_COLOR_TEXT = (255, 255, 255)
UI_COLOR_TEXT_SECONDARY = (200, 200, 200)
UI_COLOR_MONEY = (255, 235, 120)
UI_HUD_PADDING = 10

# ========== 近战武器贴图默认 ==========
MELEE_SPRITE_SIZE = (32, 12)
MELEE_SPRITE_FALLBACK_COLOR = (180, 120, 80)
