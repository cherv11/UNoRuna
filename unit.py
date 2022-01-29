import pygame
from PIL import Image, ImageSequence
import random
import os
import sqlite3
import re
import ast
import time

import animator
from animation import *
from config import *
from ability import *
for i in os.listdir('abilities'):
    if i.endswith('.py'):
        exec(f'from abilities.{i[:-3]} import *')

pygame.init()
DMGFONT = pygame.font.SysFont('calibri', 30)


def load_anim(folder, file, parts):
    path = f'{folder}\\{file}'
    data = ast.literal_eval(open(path, 'r', encoding='utf-8').read())
    animator.load([data, parts])
    data['frames_ready'] = {}
    frames = animator.create_frames()
    center = (-1 * animator.X_OFFSET + TILE_SIZE * animator.TILE_SCALE, -1 * animator.Y_OFFSET + 3 * TILE_SIZE * animator.TILE_SCALE)
    for frame in frames:
        sc = pygame.Surface((TILE_SIZE * animator.TILE_SCALE * 5, TILE_SIZE * animator.TILE_SCALE * 5), pygame.SRCALPHA, 32)
        for i in frames[frame]:
            part = pygame.transform.scale(parts[i[0]], (int(parts[i[0]].get_width() * i[2]), int(parts[i[0]].get_height() * i[2])))
            if i[3]:
                part = pygame.transform.rotate(part, i[3])
            sc.blit(part, (center[0] + i[1][0] - part.get_width() // 2, center[1] + i[1][1] - part.get_height() // 2))
        data['frames_ready'][frame] = {False: sc, True: pygame.transform.flip(sc, True, False)}
    return data


class Unit:
    parts = {}
    animations = {}

    def __init__(self, data, level, **kwargs):
        self.game_id = ''
        self.texture_folder = search_unit_folder(data)
        self.data = ast.literal_eval(open(f'{self.texture_folder}\\unit.txt', 'r', encoding='utf-8').read())
        self.id = self.data['id']
        self.name = self.data['name']
        self.element = self.data['element'] if 'element' in self.data else 'normal'
        self.avatar = pygame.image.load(f'{self.texture_folder}\\avatar.png').convert_alpha()
        self.avatar = pygame.transform.scale(self.avatar, GUI_ICON_SIZE)
        if self.name not in Unit.parts:
            Unit.parts[self.name] = {i: pygame.image.load(f'{self.texture_folder}\\{i}').convert_alpha() for i in
                                     os.listdir(self.texture_folder) if i.endswith('.png')}
            Unit.animations[self.name] = {i.split('.txt')[0]: load_anim(self.texture_folder, i, Unit.parts[self.name])
                                          for i in os.listdir(self.texture_folder) if i.endswith('.txt') and not i == 'unit.txt'}
            if 'attack' not in Unit.animations[self.name]:
                Unit.animations[self.name]['attack'] = Unit.animations[self.name]['idle']
            if 'jump' not in Unit.animations[self.name]:
                Unit.animations[self.name]['jump'] = Unit.animations[self.name]['idle']
            if 'fall' not in Unit.animations[self.name]:
                Unit.animations[self.name]['fall'] = Unit.animations[self.name]['idle']
            if 'die' not in Unit.animations[self.name]:
                Unit.animations[self.name]['die'] = Unit.animations[self.name]['idle']
            if 'move' not in Unit.animations[self.name]:
                Unit.animations[self.name]['move'] = Unit.animations[self.name]['idle']
            if 'cast1' not in Unit.animations[self.name]:
                Unit.animations[self.name]['cast1'] = Unit.animations[self.name]['idle']
            if 'cast2' not in Unit.animations[self.name]:
                Unit.animations[self.name]['cast2'] = Unit.animations[self.name]['cast1']
            if 'cast3' not in Unit.animations[self.name]:
                Unit.animations[self.name]['cast3'] = Unit.animations[self.name]['cast1']
            if 'cast4' not in Unit.animations[self.name]:
                Unit.animations[self.name]['cast4'] = Unit.animations[self.name]['cast1']
        self.cur_anim = 'idle'
        self.next_anim = 'idle'
        self.anim_idx = 0
        self.anim_speed = 1
        self.level = level
        self.units = level.units
        self.dialogs = []

        self.hp = self.data['stats']['hp']
        self.mana = self.data['stats']['mana']
        self.dmg = DamageTable(self.data['stats']['dmg'])
        self.armor = DamageTable(self.data['stats']['armor'])
        self.movespeed = self.data['stats']['speed']
        self.attack_speed = self.data['stats']['attack_speed']
        self.sight = self.data['stats']['sight']
        self.accuracy = self.data['stats']['accuracy']
        self.multishot = self.data['stats']['multishot']

        self.melee = self.data['melee']
        self.canattack = self.data['canattack'] if 'canattack' in self.data else True
        if self.canattack:
            if 'attack' in self.data:
                if not self.melee:
                    self.data['attack']['size'] = Vector(self.data['attack']['size'])
            elif self.melee:
                self.data['attack'] = {"projectile": "sword.png", "radius": 1, "spawn_offset": (0, -1),
                                       "top_angle": 90, "bottom_angle": -45}
            else:
                self.data['attack'] = {"projectile": "orb.png", "speed": 40, "size": Vector(30, 30), "spawn_offset": (0, -1),
                                       "attack_frame": 40, "top_angle": 90, "bottom_angle": -45, "destroybyMapCollisions": 1,
                                       "stopbyMapCollisions": 1, "destroybyUnitCollisions": 1, "stopbyUnitCollisions": 1,
                                       "destroyAnimation": "orbDestroy"}
            if 'atability' not in self.data['attack']:
                self.data['attack']['atability'] = 'AttackAbility'

        self.size = Vector(self.data['stats']['size'])
        self.cords = Vector(kwargs['cords']) if 'cords' in kwargs else None
        self.team = 'enemy' if 'e' in kwargs and kwargs['e'] else kwargs['team'] if 'team' in kwargs else 'ally'
        self.flip = True if 'e' in kwargs else False
        self.particles = [Particles(**p) for p in self.data['particles']] if 'particles' in self.data else []
        self.canfly = self.data['canfly'] if 'canfly' in self.data else False
        self.canswim = self.data['canswim'] if 'canswim' in self.data else False
        self.speed = Vector()
        self.accel = Vector(0, GRAVITY) if not self.canfly else Vector()

        self.abilities = []
        self.ability_raws = self.data['abilities'] if 'abilities' in self.data else []
        self.ability_raw_examples = []
        if 'astats' not in self.data:
            self.data['astats'] = {"strength": 1, "radius": 1, "aduration": 1, "manacost": 1, "castspeed": 1, "reduction": 1, "super": 1}
        self.strength = self.data['astats']['strength']  # урон, сила дебаффов или баффов
        self.radius = self.data['astats']['radius']  # радиус способностей и аур
        self.aduration = self.data['astats']['aduration']  # длительность юнитов и пр.
        self.manacost = self.data['astats']['manacost']  # манакост
        self.castspeed = self.data['astats']['castspeed']  # скорость каста
        self.reduction = self.data['astats']['reduction']  # снижение кулдауна
        self.super = self.data['astats']['super']  # ой

        self.exp = 0
        self.perks = []
        self.items = []
        self.modifiers = []
        self.maxhp, self.maxmana = self.hp, self.mana
        self.lasthp = [0, self.hp, None]
        self.tasks = []
        self.dmgvs = []
        self.ticks = 0
        self.status = 0
        self.aiallowed = True
        self.ai = AI(self)

        self.dead = False
        self.summoner = kwargs['summoner'] if 'summoner' in kwargs else None
        self.duration = kwargs['duration'] if 'duration' in kwargs else 0
        self.baseduration = self.duration
        self.canbecontrolled = self.data['canbecontrolled'] if 'canbecontrolled' in self.data else True
        self.baroffset = self.data['baroffset'] if 'baroffset' in self.data else (0, -(self.size.y+0.3))
        self.baroffset = (self.baroffset[0], self.baroffset[1]+(random.randint(0,200)-100)/1000)
        self.mousepos = None
        self.stats = UnitStats()
        self.drop = self.data['drop'] if 'drop' in self.data else {}

    # TODO: новые анимации и текстуры Zalgo, переписать animator

    def change_anim(self, anim, speed=1):
        if not self.cur_anim in ['die', 'fall']:
            self.next_anim = anim
            self.anim_speed = speed

    def tick(self, sc, pos):
        if self.ticks == 0:
            for i in self.ability_raws:
                abl = {'self': self}
                exec(f'ab={i[0]}(self)', globals(), abl)
                ab = abl['ab']
                self.ability_raw_examples.append(ab)
                if i[5] in ('passive', 'orb'):
                    self.abilities.append(ab)
                    ab.onAbilityStart()

        spp = self.speed + self.accel
        dcords = self.cords()
        if not spp.y == 0:
            if spp.y < 0:
                if self.level.find_upper_space(self, spp.y):
                    self.speed.y += self.accel.y
                    self.cords.y += self.speed.y
                    self.next_anim = 'jump'
                else:
                    self.speed.y = 0
            elif self.level.find_under_space(self, spp.y):
                self.speed.y += self.accel.y
                self.cords.y += self.speed.y
                self.next_anim = 'fall'
            else:
                self.speed.y = 0
        if not spp.x == 0:
            if spp.x < 0:
                if self.level.find_left_space(self, spp.x):
                    self.speed.x += self.accel.x
                    self.cords.x += self.speed.x
                else:
                    self.speed.x = 0
            elif self.level.find_right_space(self, spp.x):
                self.speed.x += self.accel.x
                self.cords.x += self.speed.x
            else:
                self.speed.x = 0
        if dcords != self.cords:
            dcords -= self.cords
            self.level.runa.stats.move(self, dcords.getlen())
        # Tasks help
        # die: ['die', cur_frame, last_frame], the animation stops on last_frame when reaches it
        # attack: ['attack', cur_frame, attack time, AttackAbility or its subclass instance]
        # ability: ['cast<num>', cur_frame, cast_time, abilityStart frame, cooldown, Ability subclass instance, num, ifstarted, animation, manacost]
        for i, task in enumerate(self.tasks):
            if task[0] == 'attack':
                aframes = Unit.animations[self.name]['attack']['len'] if Unit.animations[self.name]['attack']['len'] < task[2] else task[2]
                if task[1] < aframes:
                    if Unit.animations[self.name]['attack']['len'] > task[2]:
                        self.anim_speed = Unit.animations[self.name]['attack']['len'] / task[2]
                    if self.melee:
                        task[3].meleeAttack(task[1], aframes, self.anim_speed)
                    else:
                        task[3].rangedAttack(task[1], aframes, self.anim_speed)
                    self.next_anim = 'attack'
                    self.tasks[i][1] += 1
                elif task[1] < task[2]:
                    self.tasks[i][1] += 1
                else:
                    self.tasks.remove(task)
                    if self.melee:
                        task[3].destroy()
                    continue
            if task[0].startswith('cast'):
                if task[1] == 0:
                    task[5].onAbilityCastStart()
                    for mod in self.modifiers:
                        if PROVIDE_SPELL_CASTING in mod.provides:
                            mod.onAbilityCastStart(task[5])
                if task[1] < task[2]:
                    self.next_anim = task[8]
                    self.anim_speed = Unit.animations[self.name][task[8]]['len']/task[2]
                    self.tasks[i][1] += 1
                    if self.mana < self.tasks[i][9] / self.manacost:
                        self.tasks.remove(task)
                        continue
                    elif not task[7] and self.tasks[i][1] >= task[3]:
                        self.abilities.append(task[5])
                        self.tasks[i][7] = True
                        task[5].onAbilityStart()
                        self.level.runa.stats.cast(self, task[5])
                        self.mana -= self.tasks[i][9] / self.manacost
                        for mod in self.modifiers:
                            if PROVIDE_SPELL_STARTING in mod.provides:
                                mod.onAbilityStart(task[5])
                elif task[1] < task[4]:
                    self.tasks[i][1] += 1
                else:
                    self.tasks.remove(task)
                    continue
            if task[0] == 'die':
                self.next_anim = 'die'
                if task[1] < task[2]:
                    self.tasks[i][1] += 1
                else:
                    self.anim_idx = task[2]

        if not self.next_anim == self.cur_anim:
            self.cur_anim = self.next_anim
            self.anim_idx = 0
        if self.anim_idx >= Unit.animations[self.name][self.cur_anim]['len']:
            self.anim_idx = 0

        self.ticks += 1
        for i in self.abilities:
            i.tick()
        for i in self.modifiers:
            i.tick()
        self.change_status()

        if self.duration and self.ticks > self.duration * FPS:
            self.die(self)

    def blit(self, sc):
        mp, cs, ts = self.level.mp, self.level.camera_scale, self.level.tile_size
        if int(self.anim_idx) in Unit.animations[self.name][self.cur_anim]['frames_ready']:
            part = Unit.animations[self.name][self.cur_anim]['frames_ready'][int(self.anim_idx)][self.flip]
            part = pygame.transform.scale(part, (int(part.get_width() / animator.TILE_SCALE * cs), int(part.get_height() / animator.TILE_SCALE * cs)))
            sc.blit(part, (self.cords.x*ts + mp[0] - part.get_width() // 2, self.cords.y*ts + mp[1] - part.get_height()))
            # pygame.draw.rect(sc, RED, (int(self.cords.x-self.size.x//2)*ts + mp[0], int(self.cords.y-self.size.y+0.25)*ts + mp[1], self.size.x*ts, self.size.y*ts), 1)
            # pygame.draw.circle(sc, YELLANGE, (self.cords.x*ts+mp[0], self.cords.y*ts+mp[1]), 3)

        if self.particles:
            pcds = self.cords.x * self.level.tile_size + self.level.mp[0], self.cords.y * self.level.tile_size + self.level.mp[1]
            for p in self.particles:
                p.spawn(pcds, level_scale=self.level.camera_scale)
                for x, p in p.act(pcds):
                    sc.blit(x, p)
        self.anim_idx += self.anim_speed
        self.anim_speed = 1
        self.next_anim = 'idle'

    def blit_dmgvs(self, sc):
        cs = self.level.camera_scale
        mp = self.level.mp
        if self.lasthp[0] >= DAMAGE_BAR_TIME:
            self.lasthp = [0, self.hp, None]
        elif self.hp != self.lasthp[1] or self.lasthp[0] >= DAMAGE_BAR_FRESH_END:
            self.lasthp[0] += 1
            if self.lasthp[2] is None:
                self.lasthp[2] = self.level.gui.make_unit_bar(self)
            bar = self.lasthp[2].copy()
            if self.lasthp[0] >= DAMAGE_BAR_TRANSPARENT_START:
                bar.set_alpha(255*(DAMAGE_BAR_TIME-self.lasthp[0])/DAMAGE_BAR_TRANSPARENT_TIME)
            elif self.lasthp[0] >= DAMAGE_BAR_FRESH_START:
                bar = self.level.gui.make_fresh_from_bar(self, bar, (DAMAGE_BAR_FRESH_END-self.lasthp[0])/DAMAGE_BAR_FRESH_TIME)
            else:
                bar = self.level.gui.make_fresh_from_bar(self, bar, 1)
            bar = pygame.transform.smoothscale(bar, (int(bar.get_width()*self.level.camera_scale//3), int(bar.get_height()*self.level.camera_scale//3)))
            sc.blit(bar, ((self.cords.x+self.baroffset[0])*self.level.tile_size+mp[0]-bar.get_width()//2, (self.cords.y+self.baroffset[1])*self.level.tile_size+mp[1]-bar.get_height()//2))

        for i, v in enumerate(self.dmgvs):
            if v[2] >= DAMAGE_VALUE_TIME:
                self.dmgvs.remove(v)
            else:
                if v[2] >= DAMAGE_VALUE_TRANSPARENT_START:
                    v[0].set_alpha(255*(DAMAGE_VALUE_TIME-self.dmgvs[i][2])/DAMAGE_VALUE_TRANSPARENT_TIME)
                self.dmgvs[i][2] += 1
                sc.blit(v[0], ((self.cords.x*TILE_SIZE+v[1][0])*cs+mp[0]-v[0].get_width()//2, (self.cords.y*TILE_SIZE+v[1][1])*cs+mp[1]-v[0].get_height()//2-self.dmgvs[i][2]*DAMAGE_VALUE_VSPEED*cs))

    def applyDamage(self, caster, dmg):
        if self.dead:
            return
        n = dmg['n'] * 0.5 ** (self.armor['n'] / 25)
        a = dmg['a'] * (100-self.armor['a'])/100
        f = dmg['f'] * (100-self.armor['f'])/100
        w = dmg['w'] * (100-self.armor['w'])/100
        e = dmg['e'] * (100-self.armor['e'])/100
        d = dmg['d'] * (100-self.armor['d'])/100
        l = dmg['l'] * (100-self.armor['l'])/100
        dmgv = DamageTable(*(n, a, w, f, e, d, l))
        dmgs = dmgv.sum()
        if dmgs > 0:
            last = self.hp if self.lasthp[0] >= DAMAGE_BAR_FRESH_END else self.lasthp[1]
            self.lasthp = [0, last, None]
            self.hp -= dmgs
            self.level.runa.stats.dmg(caster, self, dmgs, dmg.sum())
            for i, v in dmgv:
                v = int(v)
                if v > 0:
                    self.dmgvs.append([DMGFONT.render(str(v), True, DMGCOLORS[i]), (random.randint(0, 2*TILE_SIZE)-TILE_SIZE, random.randint(0, 2*TILE_SIZE)-TILE_SIZE-self.size.y*TILE_SIZE), 0])
                elif v < 0:
                    self.dmgvs.append([DMGFONT.render(str(v), True, DMGCOLORS['h']), (random.randint(0, 2*TILE_SIZE)-TILE_SIZE, random.randint(0, 2*TILE_SIZE)-TILE_SIZE-self.size.y*TILE_SIZE), 0])
            if self.hp <= 0:
                self.die(caster)

    def die(self, caster):
        if self.dead:
            return
        self.level.runa.stats.dead(caster, self)
        if caster.team == 'ally' and self.team != 'ally':
            self.level.sp.add(int(caster.super), caster.element)
            self.level.gui.recolor()
        if self != caster:
            self.get_drop()
        self.hp = 0
        self.dead = True
        self.status = STATUS_DEAD
        if self.canfly:
            self.canfly = False
            self.accel.y += GRAVITY
        self.tasks = [['die', 0, Unit.animations[self.name]['die']['len']-1]]
        for i in self.abilities:
            i.onOwnerDied()
        for i in self.modifiers:
            if i.removeOnDeath:
                i.destroy()
        self.recount((), all=True)
        if self.level.selected_unit is self:
            select_next_unit(self.level, pygame.mouse.get_pos())

    def canmove(self):
        if get_bit(self.status, 5):
            return False
        for i in self.tasks:
            if i[0] == 'attack':
                if i[1] < min((Unit.animations[self.name]['attack']['len'], i[2])):
                    return False
            elif i[0].startswith('cast'):
                if i[1] < i[2]:
                    return False
        return True

    def canflip(self):
        if get_bit(self.status, 6):
            return False
        return True

    def attack(self):
        if not self.canattack or self.ticks < 60:
            return
        if get_bit(self.status, 3):
            return
        for i in self.tasks:
            if i[0] == 'attack':
                return
            elif i[0].startswith('cast') and i[1] < i[2]:
                return
        abl = {'self': self}
        exec(f'ab={self.data["attack"]["atability"]}(self)', globals(), abl)
        ab = abl['ab']
        self.tasks.append(['attack', 0, 200 * FPS // self.attack_speed, ab])
        self.abilities.append(ab)

    def cast(self, num):
        if get_bit(self.status, 4):
            return
        if num > len(self.ability_raws):
            return
        if self.mana < self.ability_raws[num-1][6] / self.manacost:
            return
        for i in self.tasks:
            if i[0] == 'attack' and i[1] < min((Unit.animations[self.name]['attack']['len'], i[2])):
                return
            elif i[0] == f'cast{num}':
                return
            elif i[0].startswith('cast') and i[1] < i[2]:
                return
        abl = {'self': self}
        exec(f'ab={self.ability_raws[num-1][0]}(self)', globals(), abl)
        ab = abl['ab']
        if ab.type not in ('passive', 'orb'):
            self.tasks.append([f'cast{num}', 0, self.ability_raws[num-1][2]*FPS//self.castspeed, self.ability_raws[num-1][3]*FPS//self.castspeed, self.ability_raws[num-1][1]*FPS//self.reduction, ab, num, 0, self.ability_raws[num-1][4], self.ability_raws[num-1][6]])

    def jump(self):
        if get_bit(self.status, 6):
            return
        if not self.level.find_under_space(self):
            self.speed.y += JUMP_SPEED
            self.level.runa.stats.jump(self)
            self.change_anim('jump')

    def flyup(self):
        if not self.canfly or not self.canmove():
            return
        msps = -self.movespeed / FPS
        self.speed.y += msps * FLYING_ACCEL_TO_SPEED  # ось y инвертирована
        if self.speed.y < msps:
            self.speed.y = msps
        self.change_anim('jump')

    def flydown(self):
        if not self.canfly or not self.canmove():
            return
        msps = self.movespeed / FPS
        self.speed.y += msps * FLYING_ACCEL_TO_SPEED  # ось y инвертирована
        if self.speed.y > msps:
            self.speed.y = msps
        self.change_anim('fall')

    def moveleft(self):
        if self.canmove():
            msps = self.movespeed / FPS
            if self.canfly:
                self.speed.x -= msps * FLYING_ACCEL_TO_SPEED
                if self.speed.x < -msps:
                    self.speed.x = -msps
            elif self.level.find_left_space(self, -msps):
                self.cords.x -= msps
                self.level.runa.stats.move(self, msps)
            self.change_anim('move', self.movespeed / 6)
        if self.canflip():
            self.flip = True

    def moveright(self):
        if self.canmove():
            msps = self.movespeed / FPS
            if self.canfly:
                self.speed.x += msps * FLYING_ACCEL_TO_SPEED
                if self.speed.x > msps:
                    self.speed.x = msps
            elif self.level.find_right_space(self, msps):
                self.cords.x += msps
                self.level.runa.stats.move(self, msps)
            self.change_anim('move', self.movespeed / 6)
        if self.canflip():
            self.flip = False

    def addModifier(self, mod, ability, duration):
        mdl = {'self': self, 'ability': ability, 'duration': duration}
        exec(f'md={mod}(self, ability, duration)', globals(), mdl)
        md = mdl['md']
        self.modifiers.append(md)
        self.recount(md.provides.provides)

    def removeModifier(self, mod, caster, single=False):
        r = []
        for i in self.modifiers:
            if i.name == mod and i.ability.caster == caster:
                r += list(i.provides.provides)
                i.destroy(r=False)
                if single:
                    break
        self.recount(r)
                    
    def recount(self, prs, all=False):
        if isinstance(prs, Provides):
            prs = prs.provides
        prs = [clear_bit(i, 0) for i in prs]

        if all or PROVIDE_HP in prs:
            s, sp = find_provides(self, PROVIDE_HP, PROVIDE_HP_PERCENT)
            hp = (self.data['stats']['hp'] + sum(s.values())) * (sum(sp.values())/100+1)
            oldmaxhp = self.maxhp
            self.maxhp = hp if hp > MIN_HP else MIN_HP
            self.hp = self.maxhp * self.hp / oldmaxhp

        if all or PROVIDE_MANA in prs:
            s, sp = find_provides(self, PROVIDE_MANA, PROVIDE_MANA_PERCENT)
            mana = (self.data['stats']['mana'] + sum(s.values())) * (sum(sp.values())/100+1)
            oldmaxmana = self.maxmana
            self.maxmana = mana if mana > MIN_MANA else MIN_MANA
            self.mana = self.maxmana * self.mana / oldmaxmana

        if all or PROVIDE_SPEED in prs:
            s, sp = find_provides(self, PROVIDE_SPEED, PROVIDE_SPEED_PERCENT)
            speed = (self.data['stats']['speed'] + sum(s.values())) * (sum(sp.values()) / 100 + 1)
            self.movespeed = speed if speed > MIN_SPEED else MIN_SPEED

        if all or PROVIDE_SIGHT in prs:
            s, sp = find_provides(self, PROVIDE_SIGHT, PROVIDE_SIGHT_PERCENT)
            sight = (self.data['stats']['sight'] + sum(s.values())) * (sum(sp.values()) / 100 + 1)
            self.sight = sight if sight > MIN_SIGHT else MIN_SIGHT

        if all or PROVIDE_ARMOR in prs:
            s, sp = find_provides(self, PROVIDE_ARMOR, PROVIDE_ARMOR_PERCENT)
            armor = DamageTable(self.data['stats']['armor']) + deepsum(list(s.values())) if s else DamageTable(self.data['stats']['armor'])
            self.armor = armor * (deepsum(list(sp.values())) / 100 + 1) if sp else armor

        if all or PROVIDE_SIZE in prs:
            s, sp = find_provides(self, PROVIDE_SIZE, PROVIDE_SIZE_PERCENT)
            size = deepmax(list(s.values())) if s else Vector(self.data['stats']['size'])
            kef = sum(sp.values()) / 100 + 1
            kef = kef if kef > MIN_SIZE_PERCENT else MIN_SIZE_PERCENT
            self.size = size * kef

        if all or PROVIDE_DMG in prs:
            s, sp = find_provides(self, PROVIDE_DMG, PROVIDE_DMG_PERCENT)
            dmg = DamageTable(self.data['stats']['dmg']) + deepsum(list(s.values())) if s else DamageTable(self.data['stats']['dmg'])
            self.dmg = dmg * (deepsum(list(sp.values())) / 100 + 1) if sp else dmg

        if all or PROVIDE_ATTACK_SPEED in prs:
            s, sp = find_provides(self, PROVIDE_ATTACK_SPEED, PROVIDE_ATTACK_SPEED_PERCENT)
            aspeed = (self.data['stats']['attack_speed'] + sum(s.values())) * (sum(sp.values()) / 100 + 1)
            self.attack_speed = aspeed if aspeed > MIN_ATTACK_SPEED else MIN_ATTACK_SPEED

        if all or PROVIDE_ACCURACY in prs:
            s, sp = find_provides(self, PROVIDE_ACCURACY, PROVIDE_ACCURACY)
            accuracy = (self.data['stats']['accuracy'] + sum(s.values())) * (sum(sp.values()) / 100 + 1)
            self.accuracy = accuracy

        if all or PROVIDE_MULTISHOT in prs:
            s, sp = find_provides(self, PROVIDE_MULTISHOT, PROVIDE_MULTISHOT_PERCENT)
            mshot = (self.data['stats']['multishot'] + sum(s.values())) * (sum(sp.values()) / 100 + 1)
            self.multishot = mshot

        if all or PROVIDE_STRENGTH in prs:
            s, sp = find_provides(self, PROVIDE_STRENGTH, PROVIDE_STRENGTH_PERCENT)
            strength = (self.data['astats']['strength'] + sum(s.values())) * (sum(sp.values()) / 100 + 1)
            self.strength = strength

        if all or PROVIDE_RADIUS in prs:
            s, sp = find_provides(self, PROVIDE_RADIUS, PROVIDE_RADIUS_PERCENT)
            radius = (self.data['astats']['radius'] + sum(s.values())) * (sum(sp.values()) / 100 + 1)
            self.radius = radius

        if all or PROVIDE_ADURATION in prs:
            s, sp = find_provides(self, PROVIDE_ADURATION, PROVIDE_ADURATION_PERCENT)
            aduration = (self.data['astats']['aduration'] + sum(s.values())) * (sum(sp.values()) / 100 + 1)
            self.aduration = aduration

        if all or PROVIDE_MANACOST in prs:
            s, sp = find_provides(self, PROVIDE_MANACOST, PROVIDE_MANACOST_PERCENT)
            manacost = (self.data['astats']['manacost'] + sum(s.values())) * (sum(sp.values()) / 100 + 1)
            self.manacost = manacost

        if all or PROVIDE_CASTSPEED in prs:
            s, sp = find_provides(self, PROVIDE_CASTSPEED, PROVIDE_CASTSPEED_PERCENT)
            castspeed = (self.data['astats']['castspeed'] + sum(s.values())) * (sum(sp.values()) / 100 + 1)
            self.castspeed = castspeed

        if all or PROVIDE_REDUCTION in prs:
            s, sp = find_provides(self, PROVIDE_REDUCTION, PROVIDE_REDUCTION_PERCENT)
            reduction = (self.data['astats']['reduction'] + sum(s.values())) * (sum(sp.values()) / 100 + 1)
            self.reduction = reduction

        if all or PROVIDE_SUPER in prs:
            s, sp = find_provides(self, PROVIDE_SUPER, PROVIDE_SUPER_PERCENT)
            spr = (self.data['astats']['super'] + sum(s.values())) * (sum(sp.values()) / 100 + 1)
            self.super = spr
        # TODO: attack, attacktype

    def summon(self, unit_name, duration=0, team=None, cords=None, centercords=True):
        if team is None:
            team = self.team
        if cords is None:
            cords = self.cords
        u = Unit(unit_name, self.level, summoner=self, duration=duration, team=team)
        u.cords = cords()
        if centercords:
            u.cords.y += u.size.y/2
        self.units.append(u)
        return u

    def change_status(self):
        if self.dead:
            return
        status = 0
        for mod in self.modifiers:
            if PROVIDE_STATUS in mod.provides:
                status |= mod.provides[PROVIDE_STATUS]
        diff = self.status ^ status
        if get_bit(diff, 2):
            if get_bit(status, 2):           # 2 - passsives off
                for i in self.abilities:
                    if i.type == 'passive':
                        i.ability_off()
            else:                            # ~2 - раssives on
                for i in self.abilities:
                    if i.type == 'passive':
                        i.ability_on()
        if get_bit(diff, 3):                 # 3 attack
            for i, task in enumerate(self.tasks):
                if task[0] == 'attack':
                    if not task[3]:
                        self.tasks.remove(task)
        if get_bit(diff, 4):                 # 4 abs
            for i, task in enumerate(self.tasks):
                if task[0].startswith('cast'):
                    if not task[7]:
                        if task[1] > 0:
                            task[5].onAbilityCastInterrupted()
                        self.tasks.remove(task)
        if get_bit(diff, 5):                 # 5 move
            if self.canfly:
                self.speed /= 2
        self.status = status

    def boxcollide(self, box):
        if box[0] < self.cords.x + self.size.x / 2 and box[1] > self.cords.x - self.size.x / 2 and box[2] < self.cords.y and box[3] > self.cords.y - self.size.y:
            return True
        return False

    def cordcenter(self):
        return Vector(self.cords.x, self.cords.y - self.size.y / 2)

    def hitbox(self):
        return self.cords.x-self.size.x/2, self.cords.x+self.size.x/2, self.cords.y-self.size.y, self.cords.y

    def save(self):
        return self.name, self.game_id, self.exp, self.perks, self.items, self.stats.save(), self.aiallowed

    def load(self, game_id, exp, perks, items, stats, aiallowed):
        self.game_id = game_id
        self.exp = exp
        self.perks = perks
        self.items = items
        self.stats.load(stats)
        self.aiallowed = aiallowed
        return self

    def get_drop(self):
        if self.team == 'ally':
            return
        else:
            for k, v in self.drop.items():
                count = v if type(v) == int else int(v) if '-' not in v else random.randint(*map(int, v.split('-')))
                if count:
                    self.level.dropped.append([Item(k, self.level, count=count), self.cords])
