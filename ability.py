import pygame
from PIL import Image, ImageSequence
import random
import os
import re
from collections import defaultdict
import ast

from config import *
from proto import *
from ai import *


def findUnits(units, caster, center, radius, team='enemies', type='all'):
    return [i for i in units if (team == 'enemies' and i.team != caster.team or i.team == team) and circleColl(center.cort(), radius, i.hitbox())]


def findModifier(unit, name, caster=None, ability=None, castersummoner=None):
    for i in unit.modifiers:
        if i.name == name and (not caster or i.ability.caster == caster) and (not ability or i.ability == ability) and (not castersummoner or i.ability.caster.summoner == castersummoner):
            return i
    return False


class AttackAbility:
    def __init__(self, caster):
        self.caster = caster
        self.data = self.caster.data['attack']
        self.dmg = caster.dmg()
        self.type = 'attack'
        self.orbEffects = tuple((i for i in self.caster.abilities if i.type == 'orb')) if not get_bit(self.caster.status, 4) else ()
        self.level = caster.level
        self.units = caster.units
        self.ticks = 0
        self.maxhits = int(self.caster.multishot * self.caster.super)
        self.targets = defaultdict(int)  # for melee
        self.angles = meleeaccuracy(self.caster.accuracy, self.data["top_angle"], self.data['bottom_angle'])  # for melee
        self.projectiles = []  # for ranged
        self.done = False  # for ranged

    def onProjectileHit(self, projectile, unit):
        res = False
        for i in self.orbEffects:
            unitcoll = i.onProjectileHit(projectile, unit)
            if unitcoll:
                res = unitcoll
        if not self.caster.team == unit.team and not unit.dead:
            self.level.runa.stats.hit(self.caster, unit)
            unit.applyDamage(self.caster, self.dmg)
            res = True
        return res

    def onProjectileCollide(self, projectile, blockpos):
        for i in self.orbEffects:
            i.onProjectileCollide(projectile, blockpos)

    def onProjectileDestroy(self, projectile):
        for i in self.orbEffects:
            i.onProjectileDestroy(projectile)
        self.projectiles.remove(projectile)
        if not self.projectiles:
            self.destroy()

    def onOwnerDied(self):
        pass
            
    def tick(self):
        self.ticks += 1

    def destroy(self):
        self.caster.abilities.remove(self)

    def meleeAttack(self, curframe, aframes, anim_speed):
        self.level.runa.stats.shoot(self.caster)
        dvx = (mouse_active(self.level, self.caster)[0] - self.level.mp[0]) / self.level.tile_size - self.caster.cords.x + self.data["spawn_offset"][0]
        self.caster.flip = True if dvx < 0 else False
        ang = self.angles[0] - (self.angles[0] - self.angles[1]) * curframe / aframes
        if 'fromBottom' in self.data and self.data['fromBottom']:
            ang = self.angles[1] - ang
        ang = ang * math.pi / 180
        if self.caster.flip:
            ang = math.pi - ang
        spos = self.caster.cords
        epos = self.caster.cords + Vector(math.cos(ang) * self.data['radius'], -1 * math.sin(ang) * self.data['radius'])
        minx, maxx = (spos.x, epos.x) if spos.x < epos.x else (epos.x, spos.x)
        miny, maxy = (spos.y, epos.y) if spos.y < epos.y else (epos.y, spos.y)
        box = (minx, maxx, miny, maxy)
        # left right top bottom
        for unit in self.units:
            if self.targets[unit] < self.maxhits and unit.boxcollide(box):
                unitcoll = self.onProjectileHit(None, unit)
                if unitcoll:
                    self.targets[unit] += 1

    def rangedAttack(self, curframe, aframes, anim_speed):
        if self.done or curframe/anim_speed < self.data["attack_frame"]:
            return
        self.level.runa.stats.shoot(self.caster)
        spawn_point = Vector(self.caster.cords.x + self.data["spawn_offset"][0], self.caster.cords.y + self.data["spawn_offset"][1])
        pos = mouse_active(self.level, self.caster)
        ppos = Vector((pos[0] - self.level.mp[0]) / self.level.tile_size, (pos[1] - self.level.mp[1]) / self.level.tile_size)
        dv = ppos - spawn_point
        ang = dv.angle()
        self.caster.flip = True if dv.x < 0 else False
        if self.caster.flip:
            if ang < math.pi - self.data["top_angle"] * math.pi / 180:
                ang = math.pi - self.data["top_angle"] * math.pi / 180
            if ang > math.pi - self.data["bottom_angle"] * math.pi / 180:
                ang = math.pi - self.data["bottom_angle"] * math.pi / 180
        else:
            if ang > self.data["top_angle"] * math.pi / 180:
                ang = self.data["top_angle"] * math.pi / 180
            if ang < self.data["bottom_angle"] * math.pi / 180:
                ang = self.data["bottom_angle"] * math.pi / 180
        ang = accuracy(self.caster.accuracy, ang)
        for shot in range(self.maxhits):
            ang2 = ang
            if shot > 0:
                ang2 += (random.randint(0, 60) - 30) / 100 * math.pi
            nvector = Vector(math.cos(ang2) * self.data["speed"] / FPS, -1 * math.sin(ang2) * self.data["speed"] / FPS)
            p = Projectile(self.caster, self, spawn_point, nvector, self.caster.texture_folder + "\\" + self.data["projectile"], **self.data)
            self.level.projectiles.append(p)
            self.projectiles.append(p)
        self.done = True


class Ability:
    def __init__(self, caster):
        self.caster = caster
        self.type = 'None'
        self.name = 'None'
        self.level = caster.level
        self.units = caster.units
        self.ticks = 0
        self.intervalThink = 0
        self.ultimate = False
        self.breaked = False  # for passives

        self.strength = self.caster.strength
        self.radius = self.caster.radius
        self.aduration = self.caster.aduration
        self.manacost = self.caster.manacost
        self.castspeed = self.caster.castspeed
        self.reduction = self.caster.reduction
        self.super = self.caster.super

    def onIntervalThink(self):
        pass

    def onAbilityCastStart(self):
        pass

    def onAbilityCastInterrupted(self):
        pass

    def onAbilityStart(self):
        pass

    def onProjectileHit(self, projectile, unit):
        return False

    def onProjectileCollide(self, projectile, blockpos):
        pass

    def onProjectileDestroy(self, projectile):
        pass

    def onOwnerDied(self):
        pass

    def tick(self):
        if self.intervalThink and self.ticks % self.intervalThink == 0:
            self.onIntervalThink()
        self.ticks += 1

    def destroy(self):
        self.caster.abilities.remove(self)

    def ability_off(self):
        self.breaked = True

    def ability_on(self):
        self.breaked = False


class Modifier:
    def __init__(self, unit, ability, duration):
        self.owner = unit
        self.ability = ability
        self.duration = duration
        self.baseduration = self.duration
        self.ticks = 0
        self.name = 'None'
        self.provides = None

        self.hidden = False
        self.debuff = False
        self.purgable = True
        self.removeOnDeath = True
        self.stackable = 1 # 0 for non-stackable, 1 for fully stackable

        self.strength = self.ability.strength
        self.radius = self.ability.radius
        self.aduration = self.ability.aduration
        self.manacost = self.ability.manacost
        self.castspeed = self.ability.castspeed
        self.reduction = self.ability.reduction
        self.super = self.ability.super

    def tick(self):
        self.ticks += 1
        if self.duration and self.ticks >= self.duration*FPS:
            self.destroy()

    def destroy(self, r=True):
        self.owner.modifiers.remove(self)
        if r:
            self.owner.recount(self.provides)

    def onAbilityCastStart(self, ability):
        pass

    def onAbilityStart(self, ability):
        pass

    def addStack(self, c=1):
        pass

    def removeStack(self, c=1):
        pass


class Item:
    data = {i.split('.txt')[0]: ast.literal_eval(open(f'items\\{i}', 'r', encoding='utf-8').read()) for i in os.listdir('items') if i.endswith('.txt')}
    icons = {i.split('.png')[0]: pygame.image.load(f'items\\{i}') for i in os.listdir('items') if i.endswith('.png')}

    def __init__(self, name, level, count=1):
        self.name = name
        self.data = Item.data[name]
        self.provides = None
        self.count = count
        self.level = level
        self.icon = pygame.transform.scale(Item.icons[name], (int(level.tile_size*0.7), int(level.tile_size*0.7)))

    @classmethod
    def init(cls):
        for i in cls.icons.values():
            i.convert_alpha()
