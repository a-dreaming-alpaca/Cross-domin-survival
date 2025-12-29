"""
Cross-Domin-Survival

操作说明：WASD 移动，鼠标指向方向并左键射击，触碰传送门自动切换地图，抵达最终地图的绿色撤离点即可结算。

项目结构：
  - config/settings.py: 游戏配置常量
  - utils.py: 工具函数
  - entities/: 实体模块（玩家、敌人、子弹）
  - maps/: 地图模块
  - game/: 主游戏逻辑
  - main.py: 启动入口
"""

import os
import pycache_init  # must import first to set sys.pycache_prefix
import pygame
import random
from config.settings import WIDTH, HEIGHT, FPS, WINDOW_TITLE, UI_FONT_NAMES
from game.game import Game
from game.start_menu import StartMenu
from game.audio import MusicPlayer
from game.image_manager import ImageManager


def select_font(name_list, size):
  """选择第一个可用且能渲染中文的字体，失败则回退到默认字体。"""
  for name in name_list:
    try:
      font_obj = pygame.font.SysFont(name, size)
      try:
        test_surface = font_obj.render('测试', True, (255, 255, 255))
        if test_surface.get_width() > 0:
          return font_obj
      except Exception:
        # 即便渲染失败也返回构造出的字体，保持既有行为
        return font_obj
    except Exception:
      continue
  return pygame.font.SysFont(None, size)


def play_menu_music(music):
  try:
    music.play('menu_bg')
  except Exception:
    pass


def play_game_music(music):
  try:
    music.play('game_bg')
  except Exception:
    pass


def run_game_loop(screen, clock, font, bigfont, images, music, initial_state=None):
  game = Game(screen, clock, font, bigfont, images=images, music=music, initial_state=initial_state)
  return game.run()


def main():
    """
    游戏启动入口
    """
    # 初始化pygame
    pygame.init()
    
    # 创建游戏窗口和工具
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()
    # 选一个尽量支持中文的字体
    font = select_font(UI_FONT_NAMES, 24)
    bigfont = select_font(UI_FONT_NAMES, 48)
    
    # 创建游戏实例并运行（先显示开始界面）
    random.seed()
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets', 'images')
    images = ImageManager(assets_dir)

    # 显示开始菜单；如果用户选择开始则进入游戏
    music_dir = os.path.join(os.path.dirname(__file__), 'assets', 'music')
    music = MusicPlayer(music_dir)
    # 尝试播放名为 menu_bg 的菜单音乐（可在 assets/music/ 添加 menu_bg.mp3）
    play_menu_music(music)

    # 主循环：显示菜单 -> 跑游戏 -> 可能返回菜单或重开
    while True:
      menu = StartMenu(screen, font, bigfont, images=images, width=WIDTH, height=HEIGHT, music=music)
      action = menu.run(clock)
      # action 形如 ('new'|'load'|'quit', state) 或 None
      if not action:
        break
      kind, state = action
      if kind == 'quit':
        break

      # 进入游戏前停止菜单音乐
      try:
        music.stop()
      except Exception:
        pass

      # 跑一局游戏（载入或新开）
      play_game_music(music)
      end_action = run_game_loop(screen, clock, font, bigfont, images, music, initial_state=state if kind == 'load' else None)

      # 处理游戏结束后的分支
      if end_action == 'restart':
        play_game_music(music)
        end_action = run_game_loop(screen, clock, font, bigfont, images, music)

      # 其他情况回到菜单（menu/None）
      play_menu_music(music)


if __name__ == '__main__':
    main()
