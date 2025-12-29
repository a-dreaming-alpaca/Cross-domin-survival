"""敌人工厂：集中创建 Enemy / Boss 变体。"""

from entities.enemy import Enemy, BossEnemy


class EnemyFactory:
    def __init__(self, images=None):
        self.images = images
        # 注册表：将 archetype 名称映射到创建函数
        self.registry = {
            'boss': self._create_boss,
        }

    def create(self, archetype, x, y, patrol_radius=0):
        name = archetype or 'grunt'
        # 若在注册表中则使用对应的创建器
        if name in self.registry:
            return self.registry[name](x, y, patrol_radius)
        #备用方案：默认敌人
        return Enemy(x, y, patrol_radius=patrol_radius, images=self.images, archetype=name)

    def _create_boss(self, x, y, patrol_radius=0):
        return BossEnemy(x, y, patrol_radius=patrol_radius, images=self.images, archetype='boss')
