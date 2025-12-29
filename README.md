# Cross-domain Survival

一个用 pygame 编写的俯视角射击游戏，支持多地图切换、商店购装与近战/远程武器。

## 快速开始
- 需求：Python 3.8+，`pygame`
- 安装：
	```powershell
	pip install pygame
	```
- 运行：
	```powershell
	python main.py
	```

## 操作
- 移动：W / A / S / D
- 射击：鼠标指向 + 左键（按冷却自动连发）
- 近战：右键或 E（带挥舞动画，可反弹的武器会弹回敌弹）
- 快速切枪：数字键 1-9
- 退出：Esc 或 关闭窗口
- 商店：用鼠标点击购买/装备/跳过

## 主要特性
- 多地图循环：传送门切关，最终绿色撤离点结算
- 商店：关间使用金钱购买武器并立即装备
- 武器系统：
	- 远程：支持散弹、后坐力、枪口火花、抖动、冷却变灰
	- 近战：半径判定、可选反弹子弹，带挥舞动画（前伸+角度扫动）
- 图像管理：`ImageManager` 提供按需加载与缺省占位色块
- UI 字体：启动时自动从候选字体中挑选支持 CJK 的字体

## 设计说明（OOP / 封装 / 模式）
- 模块划分：
	- config：全局常量与平衡参数（窗口、颜色、经济、敌人/武器原型）。
	- entities：Player/Enemy/Bullet/Weapon 等面向对象实体，职责单一、接口清晰。
	- game：流程与 UI（Game 主循环、HUD、Shop UI/State、音频、保存）。
	- maps：GameMap 负责敌人生成、传送门/撤离点等场景元素。
- 核心类接口：
	- Game：驱动输入、更新、碰撞、胜利/失败、商店切换。
	- Player：移动/射击/近战、背包与金钱、升级等级，`try_shoot`/`try_melee`/`buy_weapon`/`set_weapon_upgrade_level`。
	- Weapon 体系：`RangedWeapon`/`MeleeWeapon` 继承 `Weapon`，封装冷却、伤害、范围、散射、渲染与特效；`apply_upgrade_stats` 依据配置调整属性。
	- ShopState/ShopUI：逻辑与渲染分离；事件映射为 `ShopAction(kind, idx)`，逻辑侧判断拥有/装备/升级/扣费。
	- save_manager：`save_game`/`load_game` 负责 JSON 序列化，重建武器实例并同步升级。
- 数据结构：
	- `ENEMY_ARCHETYPES`/`ENEMY_SPAWN_WEIGHTS` 字典+列表描述敌人原型与权重。
	- `SHOP_WEAPONS` 原型列表 + `copy` 生成实例，避免共享状态。
	- `weapon_levels` 字典（name -> level）集中管理升级等级，调用 `apply_weapon_upgrade` 批量同步。
	- Shop 使用 `ShopItem`/`ShopAction` dataclass 提供语义化数据传递。
- 设计模式：
	- 原型：`SHOP_WEAPONS` 作为原型池，购买时浅拷贝。
	- 策略/状态分离：ShopState（逻辑）与 ShopUI（渲染）；输入事件转语义动作类似轻量命令。
	- 工厂思路：敌人原型 + 权重生成敌人；地图生成传送门/撤离点。
- 异常与健壮性：
	- save_manager 读写包裹 try/except，缺失文件返回 None，保存前确保目录存在。
	- 渲染缺资源时回退占位 Surface；射击零向量、索引越界等做防御性检查。
	- 商店逻辑在资金不足、未拥有、满级等场景返回 False 防止状态污染。


## 目录结构
```
cross-domain-survival/
├── assets/
│   ├── images/              # 贴图资源（player/enemy/weapons 等）
│   └── music/               # 音乐与音效资源
├── config/
│   └── settings.py          # 全局常量：窗口、颜色、数值、字体列表
├── entities/
│   ├── bullet.py            # 子弹：运动、碰撞、绘制
│   ├── player.py            # 玩家：移动、射击、近战、金钱、绘制
│   ├── enemy.py             # 敌人：巡逻、索敌、射击、绘制
│   ├── weapons.py           # 武器基类；远程/近战实现与挂载渲染
│   └── factory.py           # 敌人与武器构建辅助
├── game/
│   ├── game.py              # 核心循环：输入、状态更新、碰撞、HUD、商店
│   ├── image_manager.py     # 贴图加载与缩放，占位回退
│   ├── audio.py             # 音频播放与管理
│   ├── hud.py               # HUD 绘制
│   ├── shop_ui.py           # 商店 UI 与交互
│   ├── save_manager.py      # 存档/读档
│   └── start_menu.py        # 开始菜单
├── maps/
│   └── game_map.py          # 地图生成与绘制，包含传送门/撤离点/资源
├── utils.py                 # 工具函数：向量、方向、角度辅助
├── main.py                  # 启动入口：初始化 pygame/字体/图像并运行 Game
├── tests/
│   ├── test_buy_equip.py            # 商店购买与装备
│   ├── test_open_shop.py            # 打开商店流程
│   ├── test_open_shop_click.py      # 商店点击购买
│   ├── test_shop_logic.py           # ShopState 逻辑单测（买/装/升）
│   ├── test_player_weapons.py       # 玩家射击/近战行为
│   ├── test_save_load.py            # 存档/读档升级与武器重建
│   ├── test_combat_integration.py   # 击杀奖励与受击扣血
│   └── test_boss.py                 # Boss 基础行为
└── README.md                # 本文件
```


