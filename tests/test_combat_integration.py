import os
import pycache_init  # must import first to set sys.pycache_prefix
import pygame
import pytest

from entities.player import Player
from entities.enemy import Enemy
from entities.bullet import Bullet
from config.settings import MONEY_PER_ENEMY


@pytest.fixture(autouse=True)
def init_pygame():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    yield
    pygame.quit()


def test_player_bullet_kill_awards_money():
    player = Player(0, 0)
    player.money = 0
    enemy = Enemy(50, 50, images=None)
    enemy.hp = 10
    enemy.money = MONEY_PER_ENEMY

    bullet = Bullet(player.rect.center, (1, 0), speed=0, owner='player', damage=20, max_range=10)
    # force overlap
    bullet.rect.center = enemy.rect.center

    # simulate collision as in Game.update
    if enemy.alive and bullet.rect.colliderect(enemy.rect):
        enemy.hp -= bullet.damage
        bullet.alive = False
        if enemy.hp <= 0:
            enemy.alive = False
            player.money += getattr(enemy, 'money', MONEY_PER_ENEMY)

    assert player.money >= MONEY_PER_ENEMY
    assert enemy.alive is False


def test_enemy_bullet_damages_player():
    player = Player(0, 0)
    player.hp = 50
    enemy_bullet = Bullet(player.rect.center, (1, 0), speed=0, owner='enemy', damage=15, max_range=10)
    enemy_bullet.rect.center = player.rect.center

    if enemy_bullet.rect.colliderect(player.rect):
        player.hp -= enemy_bullet.damage
        enemy_bullet.alive = False

    assert player.hp == 35
    assert enemy_bullet.alive is False
