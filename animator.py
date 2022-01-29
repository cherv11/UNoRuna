import pygame
import os
import sqlite3
import ast

from config import *
from maps import *

name = 'idle'
object = 'Zalgo'
folder = 'units\\heroes\\Zalgo'

pygame.init()
sc = pygame.display.set_mode(WINDOW, pygame.FULLSCREEN)
clock = pygame.time.Clock()

font = pygame.font.SysFont('calibri', 30)
font2 = pygame.font.SysFont('calibri', 36)
font3 = pygame.font.SysFont('calibri', 22)
font4 = pygame.font.SysFont('calibri', 12)
text_parts = font2.render(f'In Folder', True, (0, 0, 0))
text_curparts = font2.render(f'Parts', True, (0, 0, 0))
text_poses = font2.render(f'Poses', True, (0, 0, 0))
text_bones = font.render('Bones [F]', True, (0, 0, 0))
text_tbones = font.render('Toggle bones [G]', True, (0, 0, 0))
text_save = font.render('Saved', True, (0, 0, 0))
text_point_move_bind = font.render('Point Move Binding [H]', True, (0, 0, 0))
text_save_frames = 0
TILE_SCALE = 7
TILE_SIZE_SCALED = TILE_SIZE * TILE_SCALE
X_OFFSET, Y_OFFSET = 400, 250
AMAP_SIZE_X, AMAP_SIZE_Y = 3, 2
SCALING_POINT = (X_OFFSET + TILE_SIZE_SCALED * AMAP_SIZE_X // 2, Y_OFFSET + TILE_SIZE_SCALED * AMAP_SIZE_Y)
X_OFFSET_MINI, Y_OFFSET_MINI = 1590, 800
SCALING_POINT_MINI = (X_OFFSET_MINI + TILE_SIZE * AMAP_SIZE_X // 2, Y_OFFSET_MINI + TILE_SIZE * AMAP_SIZE_Y)

parts = [i for i in os.listdir(folder) if i.endswith('.png')]
cur_ic = pygame.image.load(f'textures\\GUI\\firesm.png').convert_alpha()
sec_ic = pygame.image.load(f'textures\\GUI\\watersm.png').convert_alpha()
plus_ic = pygame.image.load(f'textures\\GUI\\plus.png').convert_alpha()
play_ic = pygame.image.load(f'textures\\GUI\\aplay.png').convert_alpha()
playon_ic = pygame.image.load(f'textures\\GUI\\aplayon.png').convert_alpha()
bonetool = False
bonesmode = True
boneline = None
point_move_bind = False
cur_idx = -1
sec_idx = -1
curparts = []
bones = []
points = {}
obj_lock = None
point_lock = None
list_lock = None
pose_lock = None
frame_lock = None
cur_pose = -1
log = []
frames = {}
poses = []
temp_pose = {}
cur_frame = -1
play = -1


class Bone:
    def __init__(self, pp, pd, ang=0):
        self.pp = pp
        self.pd = pd
        self.length = math.sqrt((points[pp].pos[0] - points[pd].pos[0]) ** 2 + (points[pp].pos[1] - points[pd].pos[1]) ** 2)
        self.ang = ang


class Point:
    def __init__(self, pos, id, obj, parent=None, daughters=None):
        self.id = id
        self.obj = obj
        self.parent = parent
        self.daughters = daughters if daughters else []
        self.pos = pos
        self.lastpos = pos

    def move(self, daughterid=0, checkparent=True, ps=False, pi=False):
        if self.parent and checkparent:
            if points[self.parent].parent or ps or pi:
                self.push(self.parent, ps)
                points[self.parent].move(daughterid=self.id, ps=ps)
            else:
                self.pull(self.parent, ps)
                points[self.parent].move(checkparent=False, ps=ps)
        for i in self.daughters:
            if not i == daughterid:
                self.push(i, ps)
                points[i].move(checkparent=False, ps=ps)
        self.lastpos = self.pos

    def push(self, p, ps):
        l = 0
        for i in bones:
            if i.pp == self.id and i.pd == p or i.pp == p and i.pd == self.id:
                l = i.length
        if l == 0:
            return
        newlen = math.sqrt((self.pos[0] - points[p].pos[0]) ** 2 + (self.pos[1] - points[p].pos[1]) ** 2)
        diff = newlen - l
        newv = ((self.lastpos[0] - points[p].pos[0]) / newlen, (self.lastpos[1] - points[p].pos[1]) / newlen)
        lp = points[p].pos
        points[p].pos = (points[p].pos[0] + diff * newv[0], points[p].pos[1] + diff * newv[1])
        if ps:
            return
        ang, ang2 = 0, 0
        for i in range(len(curparts)):
            if curparts[i][6] == points[p].obj:
                for b in bones:
                    if b.pp == p and b.pd == self.id:
                        w, h = points[b.pd].pos[0] - points[b.pp].pos[0], points[b.pp].pos[1] - points[b.pd].pos[1]
                        ang = math.asin(h / math.sqrt(h ** 2 + w ** 2))
                        ang = math.pi - ang if w < 0 else ang

                        ang2 = curparts[i][4]
                        curparts[i][4] = ang / math.pi * 180 - b.ang
                        ang2 = curparts[i][4] - ang2

                        for pp in curparts[i][7]:
                            curparts[i][7][pp][1] += ang2 * math.pi / 180
                        rad, ang3 = curparts[i][7][p]
                        curparts[i][2] = (int(points[p].pos[0] + rad * math.cos(ang3)), int(points[p].pos[1] - rad * math.sin(ang3)))
                    elif b.pp == self.id and b.pd == p:
                        rad, ang3 = curparts[i][7][p]
                        curparts[i][2] = (int(points[p].pos[0] + rad * math.cos(ang3)), int(points[p].pos[1] - rad * math.sin(ang3)))
        for i in range(len(curparts)):
            if curparts[i][6] == self.obj:
                rad, ang3 = curparts[i][7][self.id]
                curparts[i][2] = (int(self.pos[0] + rad * math.cos(ang3 + ang2 - ang)), int(self.pos[1] - rad * math.sin(ang3 + ang2 - ang)))

    def pull(self, p, ps):
        self.pos = self.lastpos
        l = 0
        for i in bones:
            if i.pp == self.id and i.pd == p or i.pp == p and i.pd == self.id:
                l = i.length
        if l == 0:
            return
        newlen = math.sqrt((self.pos[0] - points[p].pos[0]) ** 2 + (self.pos[1] - points[p].pos[1]) ** 2)
        diff = newlen - l
        newv = ((points[p].pos[0] - self.lastpos[0]) / newlen, (points[p].pos[1] - self.lastpos[1]) / newlen)
        lp = self.pos
        self.pos = (self.pos[0] + diff * newv[0], self.pos[1] + diff * newv[1])
        if ps:
            return
        ang, ang2 = 0, 0
        for i in range(len(curparts)):
            if curparts[i][6] == self.obj:
                for b in bones:
                    if b.pp == self.id and b.pd == p:
                        w, h = points[b.pd].pos[0] - points[b.pp].pos[0], points[b.pp].pos[1] - points[b.pd].pos[1]
                        ang = math.asin(h / math.sqrt(h ** 2 + w ** 2))
                        ang = math.pi - ang if w < 0 else ang

                        ang2 = curparts[i][4]
                        curparts[i][4] = ang / math.pi * 180 - b.ang
                        ang2 = curparts[i][4] - ang2

                        for pp in curparts[i][7]:
                            curparts[i][7][pp][1] += ang2 * math.pi / 180
                        rad, ang3 = curparts[i][7][self.id]
                        curparts[i][2] = (int(self.pos[0] + rad * math.cos(ang3)), int(self.pos[1] - rad * math.sin(ang3)))
                    elif b.pp == p and b.pd == self.id:
                        rad, ang3 = curparts[i][7][self.id]
                        curparts[i][2] = (int(self.pos[0] + rad * math.cos(ang3)), int(self.pos[1] - rad * math.sin(ang3)))


def magnetify(pos):
    for j in points:
        i = points[j].pos
        if abs(i[0]-pos[0]) <= 10 and abs(i[1]-pos[1]) <= 10:
            return (i[0], i[1])
    return False


def unscale(p, forshow=False):
    w, h = p[0] - SCALING_POINT[0], SCALING_POINT[1] - p[1]
    rad = math.sqrt(w ** 2 + h ** 2)
    ang = math.asin(h / rad)
    ang = math.pi - ang if w < 0 else ang
    rad /= TILE_SCALE
    spos = (int(SCALING_POINT_MINI[0] + rad * math.cos(ang)), int(SCALING_POINT_MINI[1] - rad * math.sin(ang)))
    if forshow:
        return spos
    else:
        return (spos[0] - SCALING_POINT_MINI[0], spos[1] - SCALING_POINT_MINI[1])


def save(sc):
    global text_save
    global text_save_frames
    try:
        save = {'frames': frames, 'poses': []}
        if cur_pose > -1:
            poses[cur_pose] = {'name': poses[cur_pose]['name'], 'parts': mkcopy(curparts), 'points': mkcopy(points), 'bones': mkcopy(bones)}
        for pose in poses:
            s_points = {p:(pose['points'][p].pos, pose['points'][p].id, pose['points'][p].obj, pose['points'][p].parent, pose['points'][p].daughters) for p in pose['points']}
            s_bones = [(b.pp, b.pd, b.ang) for b in pose['bones']]
            s_parts = [(p[0], p[2], p[3], p[4], p[6], p[7]) for p in pose['parts']]
            save['poses'].append({'name': pose['name'], 'parts': s_parts, 'points': s_points, 'bones': s_bones})
        fone, ftwo = 0, 0
        for i in range(240):
            if i in frames:
                fone = i
                break
        for i in range(240):
            if i in frames and not i == fone:
                ftwo = i
        num = ftwo-fone+1 if ftwo else 0
        save['len'] = num

        file = open(folder + '\\' + name + '.txt', 'w', encoding='utf-8')
        file.write(str(save))
        text_save = font.render(f'Saved {len(save["poses"])} poses and {save["len"]} frames', True, (0, 0, 0))
        text_save_frames = 180
    except Exception as e:
        text_save = font.render(str(e), True, (0, 0, 0))
        text_save_frames = 180
        print(e)


def mkcopy(iter):
    if type(iter) == list:
        return [mkcopy(i) for i in iter]
    if type(iter) == dict:
        return {i:mkcopy(iter[i]) for i in iter}
    if type(iter) == tuple:
        return tuple([mkcopy(i) for i in iter])
    if type(iter) == Point:
        return Point(iter.pos, iter.id, iter.obj, iter.parent, iter.daughters)
    if type(iter) == Bone:
        return Bone(iter.pp, iter.pd, iter.ang)
    return iter


def load(inter=None):
    global frames
    global curparts
    global bones
    global points
    global poses
    if inter:
        data, parts = inter
        poses = []
        frames = data['frames']
        for pi,i in enumerate(data['poses']):
            curparts = []
            bones = []
            points = {}
            for p in i['points']:
                points[p] = Point(i['points'][p][0], i['points'][p][1], i['points'][p][2], i['points'][p][3], i['points'][p][4])
            for b in i['bones']:
                bones.append(Bone(b[0], b[1], b[2]))
            for p in i['parts']:
                curparts.append([p[0], parts[p[0]], p[1], p[2], p[3], None, p[4], p[5]])
            pose = {'name': i['name'], 'parts': curparts, 'points': points, 'bones': bones}
            data['poses'][pi] = pose
            poses.append(pose)
    elif os.path.exists(folder + '\\' + name + '.txt'):
        data = ast.literal_eval(open(folder + '\\' + name + '.txt', 'r', encoding='utf-8').read())
        frames = data['frames']
        for i in data['poses']:
            curparts = []
            bones = []
            points = {}
            for p in i['points']:
                points[p] = Point(i['points'][p][0], i['points'][p][1], i['points'][p][2], i['points'][p][3], i['points'][p][4])
            for b in i['bones']:
                bones.append(Bone(b[0], b[1], b[2]))
            for p in i['parts']:
                curparts.append([p[0], pygame.image.load(f'{folder}\\{p[0]}').convert_alpha(), p[1], p[2], p[3], Image.open(f'{folder}\\{p[0]}').convert('RGBA').load(), p[4], p[5]])
            poses.append({'name': i['name'], 'parts': curparts, 'points': points, 'bones': bones})


def posesplit(one, two, kef):
    for i, p in enumerate(curparts):
        for pp in poses[frames[two]]['parts']:
            if pp[6] == p[6]:
                if not pp[3] == p[3]:
                    diff = (pp[3] - p[3]) * kef
                    old = p[3]
                    curparts[i][3] = p[3] + diff
                    for po in curparts[i][7]:
                        curparts[i][7][po][0] = curparts[i][7][po][0] / old * curparts[i][3]

    for p in points:
        if p in poses[frames[two]]['points'] and not points[p].pos == poses[frames[two]]['points'][p].pos:
            pos1 = points[p].pos
            pos2 = poses[frames[two]]['points'][p].pos
            diff = ((pos2[0] - pos1[0]) * kef, (pos2[1] - pos1[1]) * kef)
            points[p].pos = (points[p].pos[0] + diff[0], points[p].pos[1] + diff[1])

    for p in points:
        points[p].move(ps=True)

    for i, p in enumerate(curparts):
        for pp in poses[frames[two]]['parts']:
            if not pp[7]:
                continue
            if pp[6] == p[6]:
                pFlag = False
                for pt in p[7]:
                    for b in bones:
                        if b.pp == pt and b.pd in poses[frames[one]]['points']:
                            w, h = poses[frames[one]]['points'][b.pd].pos[0] - poses[frames[one]]['points'][b.pp].pos[0], poses[frames[one]]['points'][b.pp].pos[1] - poses[frames[one]]['points'][b.pd].pos[1]
                            ang = math.asin(h / math.sqrt(w ** 2 + h ** 2))
                            ang = math.pi - ang if w < 0 else ang

                            w, h = points[b.pd].pos[0] - points[b.pp].pos[0], points[b.pp].pos[1] - points[b.pd].pos[1]
                            ang2 = math.asin(h / math.sqrt(w ** 2 + h ** 2))
                            ang2 = math.pi - ang2 if w < 0 else ang2

                            curparts[i][7][pt][1] += ang2 - ang
                            pFlag = True
                            break
                    if pFlag:
                        break
                if not pFlag:
                    if pt in pp[7]:
                        if not p[7][pt][1] == pp[7][pt][1]:
                            ang = pp[7][pt][1] - p[7][pt][1]
                            while ang > 2 * math.pi:
                                ang -= 2 * math.pi
                            while ang < -2 * math.pi:
                                ang += 2 * math.pi
                            ang = ang
                            diff = ang * kef
                            curparts[i][7][pt][1] = p[7][pt][1] + diff

    for i, p in enumerate(curparts):
        for pt in p[7]:
            pFlag = False
            for b in bones:
                if b.pp == pt:
                    w, h = points[b.pd].pos[0] - points[b.pp].pos[0], points[b.pp].pos[1] - points[b.pd].pos[1]
                    ang = math.asin(h / math.sqrt(h ** 2 + w ** 2))
                    ang = math.pi - ang if w < 0 else ang
                    ang = ang / math.pi * 180 - b.ang
                    curparts[i][4] = ang
                    pFlag = True
            if pFlag is False:
                for pp in poses[frames[two]]['parts']:
                    if pp[6] == p[6]:
                        ang = pp[4] - p[4]
                        while ang > 360:
                            ang -= 360
                        while ang < -360:
                            ang += 360
                        ang = ang
                        diff = ang * kef
                        curparts[i][4] = p[4] + diff

    for i, p in enumerate(curparts):
        for pp in poses[frames[two]]['parts']:
            if pp[6] == p[6]:
                pFlag = False
                for po in curparts[i][7]:
                    for b in bones:
                        if b.pd == po:
                            rad, ang = curparts[i][7][po]
                            curparts[i][2] = (int(points[po].pos[0] + rad * math.cos(ang)), int(points[po].pos[1] - rad * math.sin(ang)))
                            pFlag = po
                if pFlag is False:
                    if not curparts[i][7]:
                        diff = ((pp[2][0] - p[2][0]) * kef, (pp[2][1] - p[2][1]) * kef)
                        curparts[i][2] = (p[2][0] + diff[0], p[2][1] + diff[0])
                    else:
                        for po in curparts[i][7]:
                            rad, ang = curparts[i][7][po]
                            curparts[i][2] = (int(points[po].pos[0] + rad * math.cos(ang)), int(points[po].pos[1] - rad * math.sin(ang)))
                            break
    return curparts, points, bones


def create_frames():
    global curparts
    global bones
    global points
    res = {}
    fone, ftwo = 0, 0
    for i in range(240):
        if i in frames:
            fone = i
            break
    for i in range(240):
        if i in frames and not i == fone:
            ftwo = i
    if not ftwo:
        return res
    for play in range(fone, ftwo + 1):
        if play in frames:
            curparts = mkcopy(poses[frames[play]]['parts'])
            points = mkcopy(poses[frames[play]]['points'])
            bones = mkcopy(poses[frames[play]]['bones'])
        else:
            one, two = None, None
            for i in range(240):
                if i < play:
                    if i in frames:
                        one = i
            for i in range(240):
                if i > play:
                    if i in frames:
                        two = i
                        break
            if two is None:
                for i in range(240):
                    if i in frames:
                        one = i
                        break
                curparts = mkcopy(poses[frames[one]]['parts'])
                points = mkcopy(poses[frames[one]]['points'])
                bones = mkcopy(poses[frames[one]]['bones'])
            else:
                curparts = mkcopy(poses[frames[one]]['parts'])
                points = mkcopy(poses[frames[one]]['points'])
                bones = mkcopy(poses[frames[one]]['bones'])
                kef = (play - one) / (two - one)

                posesplit(one, two, kef)
        res[play] = [(p[0], p[2], p[3], p[4]) for p in curparts]
    return res


if __name__ == "__main__":
    load()
    while True:
        sc.fill(pygame.Color('white'))
        pos = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()
        magnet = magnetify(pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    bonetool = False if bonetool else True
                if event.key == pygame.K_g:
                    bonesmode = False if bonesmode else True
                if event.key == pygame.K_u:
                    parts = [i for i in os.listdir(folder) if i.endswith('.png')]
                if event.key == pygame.K_s:
                    save(sc)
                if event.key == pygame.K_h:
                    point_move_bind = False if point_move_bind else True

                if event.key == pygame.K_z:
                    dl = log[-1]
                    if dl[0] == 'newpart':
                        for i, p in enumerate(curparts):
                            if curparts[i][6] == dl[1]:
                                delbones = []
                                delp = []
                                del curparts[i]
                                for j in points:
                                    if points[j].obj == dl[1]:
                                        for bdx, b in enumerate(bones):
                                            if b.pp == j or b.pd == j:
                                                delbones.append(bdx)
                                        delp.append(j)
                                for j in delp:
                                    for pp in points:
                                        if j in pp.daughters:
                                            del pp.daughters[pp.daughters.index(j)]
                                        if j == pp.parent:
                                            pp.parent = None
                                    del points[j]
                                for j in delbones:
                                    del bones[j]
                                if i == cur_idx:
                                    cur_idx = -1
                                if i == sec_idx:
                                    sec_idx = -1
                                break
                    elif dl[0] == 'partdrag':
                        new_cur_idx, new_sec_idx = cur_idx, sec_idx
                        llpart = curparts[dl[2]]
                        if dl[2] == cur_idx:
                            new_cur_idx = dl[1]
                        if dl[2] == sec_idx:
                            new_sec_idx = dl[1]
                        if dl[1] < dl[2]:
                            for j in range(dl[1], dl[2])[::-1]:
                                curparts[j + 1] = curparts[j]
                                if j == cur_idx:
                                    new_cur_idx = j + 1
                                if j == sec_idx:
                                    new_sec_idx = j + 1
                        else:
                            for j in range(dl[2], dl[1]):
                                curparts[j] = curparts[j + 1]
                                if j + 1 == cur_idx:
                                    new_cur_idx = j
                                if j + 1 == sec_idx:
                                    new_sec_idx = j
                        curparts[dl[1]] = llpart
                        cur_idx, sec_idx = new_cur_idx, new_sec_idx
                    elif dl[0] == 'bonecr':
                        for bdx, b in enumerate(bones):
                            if b.pp == dl[1][0] and b.pd == dl[1][1]:
                                del bones[bdx]
                                break
                        for p in dl[1]:
                            delp = False
                            for b in bones:
                                if b.pp == p or b.pd == p:
                                    delp = True
                                    break
                            if not delp:
                                for i in range(len(curparts)):
                                    if curparts[i][6] == points[p].obj:
                                        del curparts[i][7][p]
                                        break
                                del points[p]
                    elif dl[0] == 'motion':
                        for pr in dl[1]['parts']:
                            dld = dl[1]['parts'][pr]
                            for p in range(len(curparts)):
                                if curparts[p][6] == pr:
                                    curparts[p][4] = dld[4]
                                    curparts[p][2] = dld[2]
                                    curparts[p][3] = dld[3]
                                    curparts[p][7] = dld[7]
                        for p in dl[1]['points']:
                            points[p].pos = dl[1]['points'][p]
                            points[p].move()
                    elif dl[0] == 'newpos':
                        for i in poses:
                            if i['name'] == dl[1]:
                                for j in range(240):
                                    if j in frames:
                                        if frames[j] == dl[1]:
                                            del frames[j]
                                del poses[poses.index(i)]
                                break
                    elif dl[0] == 'setpos':
                        if dl[2] == None:
                            del frames[dl[1]]
                        else:
                            frames[dl[1]] = dl[2]
                    del log[-1]
                if event.key == pygame.K_ESCAPE:
                    exit()
            if event.type == pygame.MOUSEMOTION:
                if not point_lock == None:
                    points[point_lock].pos = (points[point_lock].pos[0] + event.rel[0], points[point_lock].pos[1] + event.rel[1])
                    for b in bones:
                        if b.pd == point_lock:
                            b.length = math.sqrt((points[b.pp].pos[0] - points[b.pd].pos[0]) ** 2 + (points[b.pp].pos[1] - points[b.pd].pos[1]) ** 2)
                    for i,p in enumerate(curparts):
                        if p[6] == points[point_lock].obj:
                            for pp in p[7]:
                                if pp == point_lock:
                                    w, h = curparts[i][2][0] - points[point_lock].pos[0], points[point_lock].pos[1] - curparts[i][2][1]
                                    rad = math.sqrt(h ** 2 + w ** 2)
                                    ang = math.asin(h / rad)
                                    ang = math.pi - ang if w < 0 else ang
                                    curparts[i][7][point_lock] = [rad, ang]
                            break
                    if point_move_bind:
                        points[point_lock].move()
                    else:
                        points[point_lock].move(pi=True)
                elif not obj_lock == None:
                    if event.buttons[0]:
                        opos = curparts[obj_lock][2]
                        pFlag = False
                        logdict = {'parts': {}, 'points': {}}
                        logdict['parts'][curparts[obj_lock][6]] = {4: curparts[obj_lock][4], 2: curparts[obj_lock][2], 7: curparts[obj_lock][7], 3: curparts[obj_lock][3]}
                        for p in curparts[obj_lock][7]:
                            for b in bones:
                                if b.pd == p:
                                    rad, ang = curparts[obj_lock][7][p]

                                    w, h = pos[0] - points[p].pos[0], points[p].pos[1] - pos[1]
                                    rad2 = math.sqrt(w ** 2 + h ** 2)
                                    ang2 = math.asin(h / rad2)
                                    ang2 = math.pi - ang2 if w < 0 else ang2

                                    curparts[obj_lock][4] += (ang2 - ang)*180/math.pi
                                    curparts[obj_lock][7][p][1] = ang2
                                    pos1 = (int(points[p].pos[0] + rad * math.cos(ang2)), int(points[p].pos[1] - rad * math.sin(ang2)))
                                    if rad*2 < rad2:
                                        curparts[obj_lock][2] = pos1
                                    else:
                                        pos2 = (int(points[p].pos[0] + rad2 * math.cos(ang2)), int(points[p].pos[1] - rad2 * math.sin(ang2)))
                                        offset = (pos2[0] - pos1[0], pos2[1] - pos1[1])
                                        curparts[obj_lock][2] = pos1
                                        logdict['points'][p] = points[p].pos
                                        points[p].pos = (points[p].pos[0] + offset[0], points[p].pos[1] + offset[1])
                                        points[p].move()
                                    pFlag = p
                                    break
                            if pFlag:
                                break
                        if pFlag:
                            for p in curparts[obj_lock][7]:
                                rad, ang3 = curparts[obj_lock][7][p]
                                ang3 += math.pi
                                logdict['points'][p] = points[p].pos
                                points[p].pos = (int(curparts[obj_lock][2][0] + rad * math.cos(ang3)), int(curparts[obj_lock][2][1] - rad * math.sin(ang3)))
                                points[p].move()
                                for b in bones:
                                    if b.pp == p:
                                        ang = (curparts[obj_lock][4] + b.ang) * math.pi / 180
                                        points[b.pd].pos = (int(points[b.pp].pos[0] + b.length * math.cos(ang)), int(points[b.pp].pos[1] - b.length * math.sin(ang)))
                                        points[b.pd].move()
                        elif not curparts[obj_lock][7]:
                            p = curparts[obj_lock]
                            part = p[1]
                            if not p[3] == 1:
                                part = pygame.transform.scale(part, (int(part.get_width() * p[3]), int(part.get_height() * p[3])))
                            if p[4]:
                                part = pygame.transform.rotate(part, p[4])
                            rad = (part.get_width() + part.get_height()) / 8
                            w, h = pos[0] - curparts[obj_lock][2][0], curparts[obj_lock][2][1] - pos[1]
                            rad2 = math.sqrt(w ** 2 + h ** 2)
                            if rad2 > rad:
                                ang2 = math.asin(h / rad2)
                                ang2 = math.pi - ang2 if w < 0 else ang2
                                ang2 += math.pi/2
                                curparts[obj_lock][4] = ang2/math.pi*180
                            else:
                                curparts[obj_lock][2] = (opos[0] + event.rel[0], opos[1] + event.rel[1])
                        else:
                            curparts[obj_lock][2] = (opos[0] + event.rel[0], opos[1] + event.rel[1])
                            for i in curparts[obj_lock][7]:
                                logdict['points'][i] = points[i].pos
                                points[i].pos = (points[i].pos[0] + event.rel[0], points[i].pos[1] + event.rel[1])
                                points[i].move()
                                for b in bones:
                                    if b.pp == i:
                                        points[b.pd].pos = (points[b.pd].pos[0] + event.rel[0], points[b.pd].pos[1] + event.rel[1])
                                        points[b.pd].move(pi=True)
                        laFlag = True
                        if log and log[-1][0] == 'motion':
                            laFlag = False
                            for pr in logdict['parts']:
                                if pr not in log[-1][1]['parts']:
                                    laFlag = True
                            for p in logdict['points']:
                                if p not in log[-1][1]['points']:
                                    laFlag = True
                        if laFlag:
                            log.append(('motion', logdict))
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button < 4:
                    if bonetool and pos[0] < 1535 and pos[1] < 950 and cur_idx > -1 and sec_idx > -1:
                        p = curparts[cur_idx]
                        part = p[1]
                        if not p[3] == 1:
                            part = pygame.transform.scale(part, (int(part.get_width() * p[3]), int(part.get_height() * p[3])))
                        if p[4]:
                            part = pygame.transform.rotate(part, p[4])
                        if p[2][0] - part.get_width() // 2 < pos[0] < p[2][0] + part.get_width() // 2 and p[2][1] - part.get_height() // 2 < pos[1] < p[2][1] + part.get_height() // 2:
                            mpos = magnet if magnet else pos
                            boneline = mpos
                    if not bonetool and pos[0] < 1535 and pos[1] < 950:
                        if event.button == 1 or event.button == 3:
                            for i in range(len(curparts))[::-1]:
                                p = curparts[i]
                                part = p[1]
                                if not p[3] == 1:
                                    part = pygame.transform.scale(part, (int(part.get_width() * p[3]), int(part.get_height() * p[3])))
                                if p[4]:
                                    part = pygame.transform.rotate(part, p[4])
                                if p[2][0] - part.get_width()//2 < pos[0] < p[2][0] + part.get_width()//2 and p[2][1] - part.get_height()//2 < pos[1] < p[2][1] + part.get_height()//2:
                                    obj_lock = i
                                    break
                        elif event.button == 2:
                            if magnet:
                                for j in points:
                                    if magnet == points[j].pos:
                                        point_lock = j
                    for i, p in enumerate(curparts):
                        if 1535 < pos[0] < 1750 and 50 + 25 * i < pos[1] < 75 + 25 * i:
                            if event.button == 2:
                                id = curparts[i][6]
                                delbones = []
                                delp = []
                                del curparts[i]
                                for j in points:
                                    if points[j].obj == id:
                                        for bdx, b in enumerate(bones):
                                            if b.pp == j or b.pd == j:
                                                delbones.append(bdx)
                                        delp.append(j)
                                for j in delp:
                                    for pp in points:
                                        if j in pp.daughters:
                                            del pp.daughters[pp.daughters.index(j)]
                                        if j == pp.parent:
                                            pp.parent = None
                                    del points[j]
                                for j in delbones:
                                    del bones[j]
                                if i == cur_idx:
                                    cur_idx = -1
                                if i == sec_idx:
                                    sec_idx = -1
                                # сделать отмену удаления
                                break
                            list_lock = i
                    posesplus = 25 if temp_pose else 0
                    for i, p in enumerate(poses):
                        if 50 < pos[0] < 125 and 50 + posesplus + 25 * i < pos[1] < 75 + posesplus + 25 * i:
                            pose_lock = i
                            obj_lock = None
                if pos[1] > 970:
                    for i in range(240):
                        if i in frames:
                            fyoffset = 0 if i < 120 else 55
                            if 16 + i%120 * 15 < pos[0] < 28 + i%120 * 15 and 970 + fyoffset < pos[1] < 994 + fyoffset:
                                frame_lock = frames[i]
                                break
                elif not obj_lock == None:
                    if event.button == 4 or event.button == 5:
                        logdict = {'parts': {}, 'points': {}}
                        logdict['parts'][curparts[obj_lock][6]] = {4: curparts[obj_lock][4], 2: curparts[obj_lock][2], 7: curparts[obj_lock][7], 3: curparts[obj_lock][3]}
                        if event.button == 5:
                            curparts[obj_lock][3] *= 0.9
                        else:
                            curparts[obj_lock][3] /= 0.9
                        for p in curparts[obj_lock][7]:
                            curparts[obj_lock][7][p][0] = curparts[obj_lock][7][p][0]/logdict['parts'][curparts[obj_lock][6]][3]*curparts[obj_lock][3]
                        for p in curparts[obj_lock][7]:
                            for b in bones:
                                if b.pd == p:
                                    rad, ang = curparts[obj_lock][7][p]
                                    curparts[obj_lock][2] = (int(points[p].pos[0] + rad * math.cos(ang)), int(points[p].pos[1] - rad * math.sin(ang)))
                        for p in curparts[obj_lock][7]:
                            for b in bones:
                                if not b.pd == p:
                                    rad, ang = curparts[obj_lock][7][p]
                                    ang += math.pi
                                    points[p].pos = (int(curparts[obj_lock][2][0] + rad * math.cos(ang)), int(curparts[obj_lock][2][1] - rad * math.sin(ang)))
                                    points[p].move()
                        log.append(('motion', logdict))
            if event.type == pygame.MOUSEBUTTONUP:
                if boneline:
                    if cur_idx > -1 and sec_idx > -1:
                        p = curparts[sec_idx]
                        part = p[1]
                        if not p[3] == 1:
                            part = pygame.transform.scale(part, (int(part.get_width() * p[3]), int(part.get_height() * p[3])))
                        if p[4]:
                            part = pygame.transform.rotate(part, p[4])
                        if p[2][0] - part.get_width() // 2 < pos[0] < p[2][0] + part.get_width() // 2 and p[2][1] - part.get_height() // 2 < pos[1] < p[2][1] + part.get_height() // 2:
                            p1, p2 = None, None
                            mpos = magnet if magnet else pos
                            for i in points:
                                if points[i].pos == boneline:
                                    p1 = i
                                if points[i].pos == mpos:
                                    p2 = i
                            if p1 is None:
                                p1 = curparts[cur_idx][6]
                                while p1 in points:
                                    p1 += 100
                                points[p1] = Point(boneline, p1, curparts[cur_idx][6])
                                w, h = curparts[cur_idx][2][0] - boneline[0], boneline[1] - curparts[cur_idx][2][1]
                                rad = math.sqrt(h ** 2 + w ** 2)
                                ang = math.asin(h / rad)
                                ang = math.pi - ang if w < 0 else ang
                                curparts[cur_idx][7][p1] = [rad, ang]
                            if p2 is None:
                                p2 = curparts[sec_idx][6]
                                while p2 in points:
                                    p2 += 100
                                points[p2] = Point(mpos, p2, curparts[sec_idx][6])
                                w, h = curparts[sec_idx][2][0] - mpos[0], mpos[1] - curparts[sec_idx][2][1]
                                rad = math.sqrt(h ** 2 + w ** 2)
                                ang = math.asin(h / rad)
                                ang = math.pi - ang if w < 0 else ang
                                curparts[sec_idx][7][p2] = [rad, ang]

                            w, h = mpos[0] - boneline[0], boneline[1] - mpos[1]
                            ang = math.asin(h / math.sqrt(h ** 2 + w ** 2))
                            ang = math.pi - ang if w < 0 else ang
                            ang = ang/math.pi*180 - curparts[cur_idx][4]
                            points[p1].daughters.append(p2)
                            points[p2].parent = p1
                            bones.append(Bone(p1, p2, ang))
                            cur_idx = sec_idx
                            sec_idx = -1
                            log.append(('bonecr', (p1, p2)))
                    boneline = None
                elif 110 < pos[0] < 145 and 15 < pos[1] < 50:
                    pose = {'name': len(poses)+1, 'parts': mkcopy(curparts), 'points': mkcopy(points), 'bones': mkcopy(bones)}
                    poses.append(pose)
                    log.append(('newpos', pose['name']))
                elif 1830 < pos[0] < 1880 and 970 < pos[1] < 1020:
                    if play < 0:
                        if len(frames) > 1:
                            if cur_pose > -1:
                                poses[cur_pose] = {'name': poses[cur_pose]['name'], 'parts': mkcopy(curparts), 'points': mkcopy(points), 'bones': mkcopy(bones)}
                            for i in range(240):
                                if i in frames:
                                    play = i
                                    break
                    else:
                        play = -1
                        if cur_pose > -1:
                            curparts = mkcopy(poses[cur_pose]['parts'])
                            points = mkcopy(poses[cur_pose]['points'])
                            bones = mkcopy(poses[cur_pose]['bones'])
                elif pos[1] >= 970:
                    for i in range(240):
                        fyoffset = 0 if i < 120 else 55
                        if 16 + i%120 * 15 < pos[0] < 28 + i%120 * 15 and 970 + fyoffset < pos[1] < 994 + fyoffset:
                            if event.button == 3:
                                if i in frames:
                                    f = frames[i]
                                    log.append(('setpos', i, f))
                                    del frames[i]
                            elif not frame_lock == None:
                                if i in frames:
                                    f = frames[i]
                                else:
                                    f = None
                                log.append(('setpos', i, f))
                                frames[i] = frame_lock
                            elif not pose_lock == None:
                                if i in frames:
                                    f = frames[i]
                                else:
                                    f = None
                                log.append(('setpos', i, f))
                                frames[i] = pose_lock
                            elif i in frames:
                                if cur_pose > -1:
                                    poses[cur_pose] = {'name': poses[cur_pose]['name'], 'parts': mkcopy(curparts), 'points': mkcopy(points), 'bones': mkcopy(bones)}
                                elif curparts:
                                    temp_pose = {'name': 'temp', 'parts': mkcopy(curparts), 'points': mkcopy(points), 'bones': mkcopy(bones)}
                                cur_pose = frames[i]
                                curparts = mkcopy(poses[cur_pose]['parts'])
                                points = mkcopy(poses[cur_pose]['points'])
                                bones = mkcopy(poses[cur_pose]['bones'])
                elif temp_pose:
                    if 50 < pos[0] < 125 and 50 < pos[1] < 75:
                        if cur_pose > -1:
                            poses[cur_pose] = {'name': poses[cur_pose]['name'], 'parts': mkcopy(curparts), 'points': mkcopy(points), 'bones': mkcopy(bones)}
                            cur_pose = -1
                        curparts = mkcopy(temp_pose['parts'])
                        points = mkcopy(temp_pose['points'])
                        bones = mkcopy(temp_pose['bones'])
                        temp_pose = {}
                    elif not pose_lock == None:
                        for i, p in enumerate(poses):
                            if 50 < pos[0] < 125 and 75 + 25 * i < pos[1] < 100 + 25 * i:
                                if event.button == 1 or event.button == 3:
                                    if cur_pose > -1:
                                        poses[cur_pose] = {'name': poses[cur_pose]['name'], 'parts': mkcopy(curparts),
                                                           'points': mkcopy(points), 'bones': mkcopy(bones)}
                                    cur_pose = i
                                    curparts = mkcopy(poses[cur_pose]['parts'])
                                    points = mkcopy(poses[cur_pose]['points'])
                                    bones = mkcopy(poses[cur_pose]['bones'])
                                elif event.button == 2:
                                    for f in range(240):
                                        if f in frames:
                                            if frames[f] == i:
                                                del frames[f]
                                            elif frames[f] > i:
                                                frames[f] -= 1
                                    del poses[i]
                                    for pi in range(i, len(poses)):
                                        poses[pi]['name'] -= 1
                elif not pose_lock == None:
                    for i, p in enumerate(poses):
                        if 50 < pos[0] < 125 and 50 + 25 * i < pos[1] < 75 + 25 * i:
                            if event.button == 1 or event.button == 3:
                                if cur_pose > -1:
                                    poses[cur_pose] = {'name': poses[cur_pose]['name'], 'parts': mkcopy(curparts), 'points': mkcopy(points), 'bones': mkcopy(bones)}
                                elif curparts:
                                    temp_pose = {'name': 'temp', 'parts': mkcopy(curparts), 'points': mkcopy(points), 'bones': mkcopy(bones)}
                                cur_pose = i
                                curparts = mkcopy(poses[cur_pose]['parts'])
                                points = mkcopy(poses[cur_pose]['points'])
                                bones = mkcopy(poses[cur_pose]['bones'])
                            elif event.button == 2:
                                for f in range(240):
                                    if f in frames:
                                        if frames[f] == i:
                                            del frames[f]
                                        elif frames[f] > i:
                                            frames[f] -= 1
                                del poses[i]
                                for pi in range(i, len(poses)):
                                    poses[pi]['name'] -= 1
                elif obj_lock == None and pose_lock == None:
                    for i, p in enumerate(curparts):
                        if 1535 < pos[0] < 1750 and 50 + 25 * i < pos[1] < 75 + 25 * i:
                            if not list_lock == None and not i == list_lock:
                                log.append(('partdrag', list_lock, i))
                                new_cur_idx, new_sec_idx = cur_idx, sec_idx
                                llpart = curparts[list_lock]
                                if list_lock == cur_idx:
                                    new_cur_idx = i
                                if list_lock == sec_idx:
                                    new_sec_idx = i
                                if i < list_lock:
                                    for j in range(i, list_lock)[::-1]:
                                        curparts[j+1] = curparts[j]
                                        if j == cur_idx:
                                            new_cur_idx = j+1
                                        if j == sec_idx:
                                            new_sec_idx = j+1
                                else:
                                    for j in range(list_lock, i):
                                        curparts[j] = curparts[j+1]
                                        if j+1 == cur_idx:
                                            new_cur_idx = j
                                        if j+1 == sec_idx:
                                            new_sec_idx = j
                                curparts[i] = llpart
                                cur_idx, sec_idx = new_cur_idx, new_sec_idx
                            else:
                                if event.button == 1:
                                    if cur_idx == i:
                                        cur_idx = -1
                                    else:
                                        cur_idx = i
                                    if sec_idx == i:
                                        sec_idx = -1
                                if event.button == 3:
                                    if sec_idx == i:
                                        sec_idx = -1
                                    else:
                                        sec_idx = i
                                    if cur_idx == i:
                                        cur_idx = -1
                            break
                    for i, p in enumerate(parts):
                        if 1750 < pos[0] < 1950 and 50 + 25 * i < pos[1] < 75 + 25 * i:
                            max = 0
                            for i in curparts:
                                if i[6] > max:
                                    max = i[6]
                            curparts.append([p, pygame.image.load(f'{folder}\\{p}').convert_alpha(), (1000, 500), 1, 0, Image.open(f'{folder}\\{p}').convert('RGBA').load(), max+1, {}])
                            log.append(('newpart', max+1))
                if not event.button == 4 and not event.button == 5:
                    obj_lock = None
                    point_lock = None
                list_lock = None
                pose_lock = None
                frame_lock = None

        for i in range(AMAP_SIZE_X-1):
            pygame.draw.aaline(sc, YELLANGE, (i * TILE_SIZE_SCALED + TILE_SIZE_SCALED + X_OFFSET, Y_OFFSET), (i * TILE_SIZE_SCALED + TILE_SIZE_SCALED + X_OFFSET, Y_OFFSET + TILE_SIZE_SCALED * AMAP_SIZE_Y))
        for i in range(AMAP_SIZE_Y):
            pygame.draw.aaline(sc, YELLANGE, (X_OFFSET, i * TILE_SIZE_SCALED + TILE_SIZE_SCALED + Y_OFFSET), (X_OFFSET + TILE_SIZE_SCALED * AMAP_SIZE_X, i * TILE_SIZE_SCALED + TILE_SIZE_SCALED + Y_OFFSET))
            pygame.draw.aaline(sc, YELLOW, (X_OFFSET, (i - 0.25) * TILE_SIZE_SCALED + TILE_SIZE_SCALED + Y_OFFSET), (X_OFFSET + TILE_SIZE_SCALED * AMAP_SIZE_X, (i - 0.25) * TILE_SIZE_SCALED + TILE_SIZE_SCALED + Y_OFFSET))
        pygame.draw.circle(sc, DARK_RED, SCALING_POINT, 1)
        sc.blit(font.render(str((pos[0]-SCALING_POINT[0], pos[1]-SCALING_POINT[1])), True, (0, 0, 0)), (200, 15))

        for i in range(AMAP_SIZE_X - 1):
            pygame.draw.aaline(sc, YELLANGE, (i * TILE_SIZE + TILE_SIZE + X_OFFSET_MINI, Y_OFFSET_MINI), (i * TILE_SIZE + TILE_SIZE + X_OFFSET_MINI, Y_OFFSET_MINI + TILE_SIZE * AMAP_SIZE_Y))
        for i in range(AMAP_SIZE_Y):
            pygame.draw.aaline(sc, YELLANGE, (X_OFFSET_MINI, i * TILE_SIZE + TILE_SIZE + Y_OFFSET_MINI), (X_OFFSET_MINI + TILE_SIZE * AMAP_SIZE_X, i * TILE_SIZE + TILE_SIZE + Y_OFFSET_MINI))
            pygame.draw.aaline(sc, YELLOW, (X_OFFSET_MINI, (i - 0.25) * TILE_SIZE + TILE_SIZE + Y_OFFSET_MINI), (X_OFFSET_MINI + TILE_SIZE * AMAP_SIZE_X, (i - 0.25) * TILE_SIZE + TILE_SIZE + Y_OFFSET_MINI))

        pygame.draw.circle(sc, DARK_RED, SCALING_POINT_MINI, 1)
        for i,p in enumerate(curparts):
            if i == cur_idx:
                sc.blit(cur_ic, (1535, 50 + 25 * i))
                pygame.draw.rect(sc, BLUE, (1550, 50 + 25 * i, 180, 25))
            if i == sec_idx:
                sc.blit(sec_ic, (1535, 55 + 25 * i))
                pygame.draw.rect(sc, DARK_RED, (1550, 50 + 25 * i, 180, 25))
            sc.blit(font.render(p[0].split('.png')[0], True, (0, 0, 0)), (1550, 50+25*i))
            part = p[1]
            if not p[3] == 1:
                part = pygame.transform.scale(part, (int(part.get_width()*p[3]), int(part.get_height()*p[3])))
            if p[4]:
                part = pygame.transform.rotate(part, p[4])
            if i == cur_idx:
                pygame.draw.rect(sc, BLUE, (p[2][0]-part.get_width()//2, p[2][1]-part.get_height()//2, part.get_width(), part.get_height()), 1)
            if i == sec_idx:
                pygame.draw.rect(sc, DARK_RED, (p[2][0]-part.get_width()//2, p[2][1]-part.get_height()//2, part.get_width(), part.get_height()), 1)
            sc.blit(part, (p[2][0]-part.get_width()//2, p[2][1]-part.get_height()//2))
            pygame.draw.circle(sc, BLUE, p[2], 5)
            minipart = pygame.transform.scale(p[1], (int(p[1].get_width() * p[3] / TILE_SCALE), int(p[1].get_height() * p[3] / TILE_SCALE)))
            if p[4]:
                minipart = pygame.transform.rotate(minipart, p[4])
            minipos = unscale(p[2], True)
            sc.blit(minipart, (minipos[0] - minipart.get_width() // 2, minipos[1] - minipart.get_height() // 2))
        if not obj_lock == None:
            pFlag = False
            for p in curparts[obj_lock][7]:
                for b in bones:
                    if b.pd == p:
                        rad = curparts[obj_lock][7][p][0]*2
                        pygame.draw.circle(sc, GREY, curparts[obj_lock][2], rad, 1)
                        pFlag = True
            if not pFlag and not curparts[obj_lock][7]:
                p = curparts[obj_lock]
                part = p[1]
                if not p[3] == 1:
                    part = pygame.transform.scale(part, (int(part.get_width() * p[3]), int(part.get_height() * p[3])))
                if p[4]:
                    part = pygame.transform.rotate(part, p[4])
                rad = (part.get_width() + part.get_height()) / 8
                pygame.draw.circle(sc, GREY, curparts[obj_lock][2], rad, 1)
        if bonesmode:
            for i in bones:
                pygame.draw.aaline(sc, YELLOW, points[i.pp].pos, points[i.pd].pos)
                pygame.draw.circle(sc, LIGHT_GREEN, points[i.pp].pos, 8, 2)
                pygame.draw.circle(sc, LIGHT_BLUE, points[i.pd].pos, 5)

        if play > -1:
            if play in frames:
                curparts = mkcopy(poses[frames[play]]['parts'])
                points = mkcopy(poses[frames[play]]['points'])
                bones = mkcopy(poses[frames[play]]['bones'])
            else:
                one, two = None, None
                for i in range(240):
                    if i < play:
                        if i in frames:
                            one = i
                for i in range(240):
                    if i > play:
                        if i in frames:
                            two = i
                            break
                if two is None:
                    for i in range(240):
                        if i in frames:
                            one = i
                            break
                    curparts = mkcopy(poses[frames[one]]['parts'])
                    points = mkcopy(poses[frames[one]]['points'])
                    bones = mkcopy(poses[frames[one]]['bones'])
                    play = one
                else:
                    curparts = mkcopy(poses[frames[one]]['parts'])
                    points = mkcopy(poses[frames[one]]['points'])
                    bones = mkcopy(poses[frames[one]]['bones'])
                    kef = (play - one) / (two - one)

                    posesplit(one, two, kef)
            play += 1
        sc.blit(text_parts, (1750, 15))
        for i, p in enumerate(parts):
            sc.blit(font.render(p.split('.png')[0], True, (0, 0, 0)), (1750, 50 + 25 * i))
        sc.blit(text_curparts, (1550, 15))
        sc.blit(text_poses, (15, 15))
        if text_save_frames:
            text_save_frames -= 1
            sc.blit(text_save, (600, 15))
        sc.blit(plus_ic, (110, 15))
        posesplus = 0
        if temp_pose:
            sc.blit(font.render(str(temp_pose['name']), True, (0, 0, 0)), (50, 50))
            posesplus = 25
        for i, p in enumerate(poses):
            if i == cur_pose:
                pygame.draw.rect(sc, YELLOW, (40, 50 + posesplus + 25 * i, 40, 25))
            sc.blit(font.render(str(p['name']), True, (0, 0, 0)), (50, 50 + posesplus + 25 * i))
        sc.blit(text_bones, (1250, 20))
        sc.blit(text_tbones, (1250, 50))
        color = GREEN if bonetool else RED
        sc.blit(font.render(str(bonetool), True, color), (1370, 20))
        sc.blit(text_point_move_bind, (880, 50))
        color = GREEN if point_move_bind else RED
        sc.blit(font.render(str(point_move_bind), True, color), (1170, 50))
        pygame.draw.aaline(sc, DARK_RED, (1535, 0), (1535, 950))
        pygame.draw.aaline(sc, DARK_RED, (0, 950), (2000, 950))
        for i in range(240):
            fyoffset = 0 if i < 120 else 55
            if i == play-1:
                pygame.draw.rect(sc, DARK_RED, (16 + i%120 * 15, 970+fyoffset, 12, 24))
            else:
                pygame.draw.rect(sc, DARK_RED, (16+i%120*15, 970+fyoffset, 12, 24), 1)
            if i in frames:
                pygame.draw.circle(sc, BLACK, (22 + i%120 * 15, 988+fyoffset), 4)
                sc.blit(font3.render(str(poses[frames[i]]['name']), True, (0, 0, 0)), (17 + i%120 * 15, 995+fyoffset))
            if i % 5 == 4:
                sc.blit(font4.render(str(i+1), True, (0, 0, 0)), (17 + i % 120 * 15, 958 + fyoffset))
        if play > -1:
            sc.blit(playon_ic, (1830, 970))
        else:
            sc.blit(play_ic, (1830, 970))
        if boneline:
            mpos = magnet if magnet else pos
            pygame.draw.aaline(sc, YELLOW, boneline, mpos)
            pygame.draw.circle(sc, LIGHT_GREEN, boneline, 8, 2)
            pygame.draw.circle(sc, LIGHT_BLUE, mpos, 5)
        pygame.display.flip()
        clock.tick(FPS)
