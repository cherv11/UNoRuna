from ability import *


class AbilitySummonSorcery(Ability):
    def __init__(self, caster):
        super().__init__(caster)
        self.summon = None
        self.name = "Summon Sorcery"
        self.type = 'notarget'
        self.unit_duration = 30 * self.aduration
        self.ultimate = True

    def onAbilityStart(self):
        spawn_point = self.caster.cordcenter()
        spawn_offset = (Vector(mouse_active(self.level, self.caster)) - Vector(self.level.mp)) / self.level.tile_size - spawn_point
        if spawn_offset.getlen() > 3:
            spawn_offset.setlen(3)
        spawn_point += spawn_offset
        unit = self.caster.summon('Azel', duration=self.unit_duration, cords=spawn_point)
        unit.strength = self.strength
        unit.radius = self.radius
        unit.aduration = self.aduration
        unit.manacost = self.manacost
        unit.castspeed = self.castspeed
        unit.reduction = self.reduction
        unit.super = self.super
        self.summon = unit


class ModifierAzelCurse(Modifier):
    def __init__(self, unit, ability, duration):
        super().__init__(unit, ability, duration)
        self.name = 'ModifierAzelCurse'
        self.def_provides = Provides((PROVIDE_SIGHT, -10*self.strength))
        self.stacks = 1
        self.provides = self.def_provides()
        self.hidden = False
        self.debuff = True
        self.purgable = True
        self.removeOnDeath = True
        self.stackable = 1

    def addStack(self, c=1):
        self.stacks += c
        self.provides = self.def_provides * self.stacks
        self.owner.recount(self.provides)
        self.duration = self.ticks/FPS + self.baseduration

    def removeStack(self, c=1):
        self.stacks -= c
        self.provides = self.def_provides * self.stacks
        self.owner.recount(self.provides)


class AbilityAzelCurse(Ability):
    def __init__(self, caster):
        super().__init__(caster)
        self.castersummoner = self.caster.summoner
        self.debuff_duration = 10
        self.stackdmg = DamageTable(n=10*self.super, d=15*self.super)
        self.name = "Azel Curse"
        self.type = 'orb'

    def onProjectileHit(self, projectile, unit):
        if self.caster.team == unit.team or unit.dead:
            return False
        if not self.castersummoner:
            mod = findModifier(unit, 'ModifierAzelCurse', self.caster)
        else:
            mod = findModifier(unit, 'ModifierAzelCurse', castersummoner=self.castersummoner)
        if mod:
            sdmg = self.stackdmg * mod.stacks
            unit.applyDamage(self.caster, sdmg)
            mod.addStack()
        else:
            unit.addModifier('ModifierAzelCurse', self, self.debuff_duration)
            unit.applyDamage(self.caster, self.stackdmg)
        return True
