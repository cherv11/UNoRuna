from ability import *


class AbilityDevilsEye(Ability):
    def __init__(self, caster):
        super().__init__(caster)
        self.summons = []
        self.projectiles = []
        self.name = "Devil's Eye"
        self.type = 'targetpoint'
        self.proj_speed = 30 * self.castspeed / FPS
        self.unit_duration = 10 * self.aduration

    def onAbilityStart(self):
        pos = mouse_active(self.level, self.caster)
        ppos = Vector((pos[0] - self.level.mp[0]) / self.level.tile_size, (pos[1] - self.level.mp[1]) / self.level.tile_size)
        spawn_point = self.caster.cordcenter()
        dv = ppos - spawn_point
        ang = dv.angle()
        self.caster.flip = True if dv.x < 0 else False
        ang = accuracy(self.caster.accuracy, ang)
        for i in range(int(self.super)):
            ang2 = ang
            if i > 0:
                ang2 += (random.randint(0, 60)-30)/100*math.pi
            nvector = Vector(math.cos(ang2) * self.proj_speed, -1 * math.sin(ang2) * self.proj_speed)
            projectile = Projectile(self.caster, self, spawn_point, nvector, search_unit_folder('DevilsEye')+"\\proj.png", **{'size': Vector(0.5, 0.5), "destroybyMapCollisions": 1, 'accel': Vector(0, -0.5*GRAVITY), 'duration': 0.5})
            self.projectiles.append(projectile)
            self.summons.append(None)
            self.level.projectiles.append(projectile)

    def onProjectileDestroy(self, projectile):
        unit = self.caster.summon('DevilsEye', duration=self.unit_duration, cords=projectile.pos)
        unit.strength = self.strength
        unit.radius = self.radius
        unit.aduration = self.aduration
        unit.manacost = self.manacost
        unit.castspeed = self.castspeed
        unit.reduction = self.reduction
        unit.super = self.super
        self.summons[self.projectiles.index(projectile)] = unit


class ModifierDevilAura(Modifier):
    def __init__(self, unit, ability, duration):
        super().__init__(unit, ability, duration)
        self.name = 'ModifierDevilAura'
        self.provides = Provides((PROVIDE_SIGHT, -10*self.strength))
        self.hidden = False
        self.debuff = True
        self.purgable = True
        self.removeOnDeath = True
        self.stackable = 1


class AbilityDevilAura(Ability):
    def __init__(self, caster):
        super().__init__(caster)
        self.castersummoner = self.caster.summoner
        self.aura_units = []
        self.name = "Devil's Eye Blind Aura"
        self.type = 'passive'
        self.aura_radius = 10 * self.radius

    def onAbilityStart(self):
        self.intervalThink = 15

    def onIntervalThink(self):
        if self.breaked:
            return
        new = findUnits(self.units, self.caster, self.caster.cordcenter(), self.aura_radius)
        for i in self.aura_units:
            if i not in new:
                i.removeModifier('ModifierDevilAura', self.caster)
                self.aura_units.remove(i)
        if not self.castersummoner:
            for i in new:
                if not findModifier(i, 'ModifierDevilAura', self.caster):
                    self.aura_units.append(i)
                    i.addModifier('ModifierDevilAura', self, 0)
        else:
            for i in new:
                if not findModifier(i, 'ModifierDevilAura', castersummoner=self.castersummoner):
                    self.aura_units.append(i)
                    i.addModifier('ModifierDevilAura', self, 0)

    def onOwnerDied(self):
        self.destroy()

    def destroy(self):
        for i in self.aura_units:
            i.removeModifier('ModifierDevilAura', self.caster)
        self.caster.abilities.remove(self)

    def ability_off(self):
        self.breaked = True
        for i in self.aura_units:
            i.removeModifier('ModifierDevilAura', self.caster)
        self.aura_units = []

