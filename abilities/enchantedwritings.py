from ability import *


class AbilityEnchantedWritings(Ability):
    def __init__(self, caster):
        super().__init__(caster)
        self.projectile = None
        self.name = "Enchanted Writings"
        self.type = 'targetpoint'
        self.proj_speed = 20 * self.castspeed / FPS
        self.bushes_duration = 10 * self.aduration
        self.bushes = []
        self.halfcount = int(2 * self.super * self.radius)

    def onAbilityStart(self):
        pos = mouse_active(self.level, self.caster)
        spawn_point = self.caster.cordcenter()
        ppos = Vector((pos[0] - self.level.mp[0]) / self.level.tile_size, (pos[1] - self.level.mp[1]) / self.level.tile_size)
        dv = ppos - spawn_point
        ang = dv.angle()
        self.caster.flip = True if dv.x < 0 else False
        ang = accuracy(self.caster.accuracy, ang)
        nvector = Vector(math.cos(ang) * self.proj_speed, -1 * math.sin(ang) * self.proj_speed)
        self.projectile = Projectile(self.caster, self, spawn_point, nvector, search_unit_folder('Zalgo')+"\\writings.png", **{'size': Vector(1, 0.5), "destroybyMapCollisions": 1})
        self.level.projectiles.append(self.projectile)

    def onProjectileHit(self, projectile, unit):
        if not projectile == self.projectile:
            if unit.team == self.caster.team or unit.dead:
                return False
            if not findModifier(unit, 'ModifierEnchantedWritings', self.caster):
                unit.addModifier('ModifierEnchantedWritings', self, 0.25)
        return True

    def onProjectileDestroy(self, projectile):
        if projectile == self.projectile:
            for i in range(self.halfcount*2+1):
                i -= self.halfcount
                projectile2 = Projectile(self.caster, self, Vector(projectile.pos.x+i, projectile.pos.y), Vector(), search_unit_folder('Zalgo')+"\\writings.png", **{'size': Vector(1, 0.5), "accel": Vector(), "duration": self.bushes_duration, 'collision_cd': FPS//4})
                self.bushes.append(projectile2)
                self.level.projectiles.append(projectile2)


class ModifierEnchantedWritings(Modifier):
    def __init__(self, unit, ability, duration):
        super().__init__(unit, ability, duration)
        self.name = 'ModifierEnchantedWritings'
        self.provides = Provides((PROVIDE_SPEED_PERCENT, -30*self.strength))
        self.hidden = False
        self.debuff = True
        self.purgable = True
        self.removeOnDeath = True
        self.stackable = 1
        self.dmg = DamageTable(d=6.25)  # it is on 0.25s interval so /4
        unit.applyDamage(self.ability.caster, self.dmg)

