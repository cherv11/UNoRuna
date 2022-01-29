from ability import *


class AbilityForbiddenWord(Ability):
    def __init__(self, caster):
        super().__init__(caster)
        self.name = "Forbidden Word"
        self.type = 'passive'
        self.aura_units = []
        self.aura_radius = 7 * self.radius * self.super
        self.silence_duration = 3 * self.aduration

    def onAbilityStart(self):
        self.intervalThink = 30

    def onIntervalThink(self):
        if self.breaked:
            return
        new = findUnits(self.units, self.caster, self.caster.cordcenter(), self.aura_radius)
        for i in self.aura_units:
            if i not in new:
                i.removeModifier('ModifierForbiddenWordAura', self.caster)
                self.aura_units.remove(i)
        for i in new:
            if not findModifier(i, 'ModifierForbiddenWordAura', self.caster):
                self.aura_units.append(i)
                i.addModifier('ModifierForbiddenWordAura', self, 0)

    def onOwnerDied(self):
        self.destroy()

    def destroy(self):
        for i in self.aura_units:
            i.removeModifier('ModifierForbiddenWordAura', self.caster)
        self.caster.abilities.remove(self)

    def ability_off(self):
        self.breaked = True
        for i in self.aura_units:
            i.removeModifier('ModifierForbiddenWordAura', self.caster)
        self.aura_units = []


class ModifierForbiddenWordAura(Modifier):
    def __init__(self, unit, ability, duration):
        super().__init__(unit, ability, duration)
        self.name = 'ModifierForbiddenWordAura'
        self.provides = Provides((PROVIDE_SPELL_STARTING, 1))
        self.hidden = False
        self.debuff = True
        self.purgable = True
        self.removeOnDeath = True
        self.stackable = 1
        self.silence_duration = ability.silence_duration

    def onAbilityStart(self, ability):
        if not findModifier(self.owner, 'ModifierForbiddenWord', self.ability.caster):
            self.owner.addModifier('ModifierForbiddenWord', self.ability, self.silence_duration)


class ModifierForbiddenWord(Modifier):
    def __init__(self, unit, ability, duration):
        super().__init__(unit, ability, duration)
        self.name = 'ModifierForbiddenWord'
        self.provides = Provides((PROVIDE_STATUS, STATUS_SILENCE))
        self.hidden = False
        self.debuff = True
        self.purgable = True
        self.removeOnDeath = True
        self.stackable = 1
