import os
import pycache_init  # must import first to set sys.pycache_prefix
import pygame
from game.game import Game
from config.settings import WIDTH, HEIGHT


def test_open_shop_quick_exit():
	os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
	pygame.init()
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	font = pygame.font.SysFont(None, 24)
	bigfont = pygame.font.SysFont(None, 48)
	clock = pygame.time.Clock()

	g = Game(screen, clock, font, bigfont)
	g.player.money = 1000

	# post a return keydown to end shop immediately
	pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RETURN}))

	g.open_shop()

	assert g.current_map_idx == 1  # shop increments map after close
	pygame.quit()
