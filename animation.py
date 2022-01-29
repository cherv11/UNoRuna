import pygame
from PIL import Image, ImageSequence
import random

from config import *


class Particles:
    """
        speed=1.0,
        frame_rate=60,
        count=0,
        spawn=0,
        lifetime=1.0
        start=0,
        scale=(256, 256),
        changexy = lambda(obj, x, y, i),
        rotate = 0.0,
        folder='textures\\particles'
        single=False
        pos='mouse_attach' or (0, 0)
        random_offset=(-1, 1, -1, 1)
        random_speed=(0.5, 2)
        random_scale=(0.5, 2)
        random_rotate=(0, 180)
    """
    def __init__(self, name, **kwargs):
        self.speed = kwargs['speed'] if 'speed' in kwargs else 1.0
        if 'frame_rate' in kwargs:
            self.speed *= kwargs['frame_rate'] / FPS
        self.count = kwargs['count'] if 'count' in kwargs else 0
        self.spawn_count = kwargs['spawn'] if 'spawn' in kwargs else 1.0
        kwargs['lifetime'] = FPS if 'lifetime' not in kwargs else int(kwargs['lifetime'] * FPS)
        self.lifetime = kwargs['lifetime']

        if 'folder' not in kwargs:
            kwargs['folder'] = f'textures\\particles\\{name.split(".")[0]}'

        self.changexy = kwargs['changexy'] if 'changexy' in kwargs else None
        if isinstance(self.changexy, str):
            self.changexy = eval(self.changexy)
        self.rotate = kwargs['rotate'] if 'rotate' in kwargs else None
        self.kwargs = kwargs
        self.particles = []

    def spawn(self, *args, **kwargs):
        spawn = int(self.spawn_count // 1)
        spawn = spawn + 1 if self.spawn_count % 1 and chance((self.spawn_count % 1) * 100) else spawn
        for i in range(spawn):
            pos = args[0]
            if 'pos' in self.kwargs:
                if self.kwargs['pos'] == 'mouse_attach':
                    pos = kwargs['pos']
                else:
                    pos = self.kwargs['pos']
            if 'random_offset' in self.kwargs:
                offset = self.kwargs['random_offset']
                pos = (pos[0]+random.randint(offset[0]*100, offset[1]*100)/100, pos[1]+random.randint(offset[2]*100, offset[3]*100)/100)

            speed = random.randint(self.kwargs['random_speed'][0] * 1000, self.kwargs['random_speed'][1] * 1000) * self.speed / 1000 if 'random_speed' in self.kwargs else self.speed
            folder = self.kwargs['folder'] if 'single' in self.kwargs else self.kwargs['folder'] + '\\' + random.choice(os.listdir(self.kwargs["folder"]))
            cycle = os.listdir(folder)
            frames = [pygame.image.load(f'{folder}\\{frame}').convert_alpha() for frame in cycle]
            frames = longsplit(frames, self.kwargs['lifetime'])

            if 'start' in self.kwargs:
                frames = frames[self.kwargs['start']:] + frames[:self.kwargs['start']]

            if 'scale' in self.kwargs:
                if self.kwargs['scale'][0] == 0:
                    frames = [pygame.transform.scale(i, (int(i.get_width() / i.get_height() * self.kwargs['scale'][1]), self.kwargs['scale'][1])) for i in frames]
                elif self.kwargs['scale'][1] == 0:
                    frames = [pygame.transform.scale(i, (self.kwargs['scale'][0], int(i.get_height() / i.get_width() * self.kwargs['scale'][0]))) for i in frames]
                else:
                    frames = [pygame.transform.scale(i, self.kwargs['scale']) for i in frames]

            scale = 1
            if 'random_scale' in self.kwargs:
                scale = random.randint(self.kwargs['random_scale'][0] * 100, self.kwargs['random_scale'][1] * 100) / 100
            if 'level_scale' in kwargs:
                scale *= kwargs['level_scale']
            if scale != 1:
                frames = [pygame.transform.scale(i, (int(i.get_width() * scale), int(i.get_height() * scale))) for i in frames]

            rotate = 0
            if 'random_rotate' in self.kwargs:
                rotate = random.randint(self.kwargs['random_rotate'][0] * 100, self.kwargs['random_rotate'][1] * 100) / 100
                frames = [pygame.transform.rotate(i, rotate) for i in frames]
            frame_idx = 0
            pos_idx = 0
            speed_repeats = 0
            particle = (frames, pos, scale, rotate, speed, frame_idx, pos_idx, speed_repeats)
            self.particles.append(particle)

    def act(self, *args, **kwargs):
        pos = args[0]
        trash = []
        res = []

        for i,p in enumerate(self.particles):
            frames, pos, scale, rotate, speed, frame_idx, pos_idx, speed_repeats = p
            if pos_idx >= self.lifetime:
                trash.append(p)
                continue
            if frame_idx >= len(frames):
                while frame_idx >= len(frames):
                    frame_idx -= len(frames)

            frame = kwargs['img'] if 'img' in kwargs else frames[frame_idx]

            x, y = pos
            if self.changexy:
                pos = self.changexy(frame, x, y, pos_idx)

            res.append([frame, pos])

            if speed == 1.0:
                frame_idx += 1
            elif speed > 1.0:
                frame_idx += int(speed)
                mod = speed % 1
                if mod and chance(mod*100):
                    frame_idx += 1
            else:
                subspeed = 1 / speed
                subspeedmod = subspeed % 1
                speed_repeats += 1
                if speed_repeats >= subspeed:
                    speed_repeats = 0
                    frame_idx += 1
                elif speed_repeats == int(subspeed) and chance(subspeedmod*100):
                    speed_repeats = 0
                    frame_idx += 1
            pos_idx += 1
            self.particles[i] = [frames, pos, scale, rotate, speed, frame_idx, pos_idx, speed_repeats]

        for i in trash:
            del self.particles[self.particles.index(i)]
        return res


class Button:
    def __init__(self, anim, **kwargs):
        self.name = anim.asset
        self.prs_name = kwargs['prs_name'] if 'prs_name' in kwargs else anim.asset
        self.folder = kwargs['folder'] if 'folder' in kwargs else f'textures\\animated_assets'
        filename = f'{self.folder}\\{self.prs_name}'
        self.img = pygame.image.load(filename).convert_alpha()
        pil_img = Image.open(filename).convert('RGBA')
        self.pixels = pil_img.load()
        self.size = pil_img.size
        self.trigger = kwargs['trigger'] if 'trigger' in kwargs else 'mb1'
        self.particles = kwargs['particles'] if 'particles' in kwargs else []
        self.kwargs = kwargs

    def act(self, *args, **kwargs):
        frame, pos, pos_idx = args
        mpos = kwargs['pos']
        actions = {}
        if 0 < mpos[0] - pos[0] < self.size[0] and 0 < mpos[1] - pos[1] < self.size[1]:
            if not self.pixels[mpos[0] - pos[0], mpos[1] - pos[1]] == (0, 0, 0, 0):
                frame = self.img
                self.press(actions, **kwargs)
                if self.particles:
                    for p in self.particles:
                        p.spawn(*[pos], **kwargs)
        if self.particles:
            actions['blit'] = []
            for p in self.particles:
                actions['blit'] += p.act(*[pos], **kwargs)
        return frame, actions

    def press(self, res, **kw2):
        if self.trigger == 'mb1' and kw2['pressed'][0]:
            if 'change_mode' in self.kwargs:
                option = self.kwargs['changelevel'] if 'changelevel' in self.kwargs else 0
                res['change_mode'] = {'mode': self.kwargs['change_mode'], 'changelevel': option}


class Animation:
    """
    duration=0,
    speed=1.0, аnimation speed
    frame_rate=60, animation speed via framerate
    start=0,
    scale=(256, 256),
    changexy = lambda(obj, x, y, i),
    rotate = 0.0,
    folder='textures\\animated_assets'
    """
    def __init__(self, asset, pos, **kwargs):
        self.speed = kwargs['speed'] if 'speed' in kwargs else 1.0
        if 'frame_rate' in kwargs:
            self.speed *= kwargs['frame_rate'] / FPS
        self.mod = self.speed % 1
        self.subspeed = 1/self.speed
        self.subspeedmod = self.subspeed % 1
        self.speed_repeats = 0
        self.asset = asset

        if 'folder' not in kwargs:
            kwargs['folder'] = f'textures\\animated_assets\\{asset.split(".")[0]}'
        self.cycle = os.listdir(f'{kwargs["folder"]}') if not 'single' in kwargs else [asset]

        frames = int(FPS*kwargs['duration']) if 'duration' in kwargs else len(self.cycle)

        self.frames = [pygame.image.load(f'{kwargs["folder"]}\\{frame}').convert_alpha() for frame in self.cycle]
        if frames < 0:
            self.inf = True
        else:
            self.inf = False
            self.frames = longsplit(self.frames, frames)

        if 'start' in kwargs:
            self.frames = self.frames[kwargs['start']:] + self.frames[:kwargs['start']]

        if 'scale' in kwargs:
            if kwargs['scale'][0] == 0:
                self.frames = [pygame.transform.scale(i, (int(i.get_width() / i.get_height() * kwargs['scale'][1]), kwargs['scale'][1])) for i in self.frames]
            elif kwargs['scale'][1] == 0:
                self.frames = [pygame.transform.scale(i, (kwargs['scale'][0], int(i.get_height() / i.get_width() * kwargs['scale'][0]))) for i in self.frames]
            else:
                self.frames = [pygame.transform.scale(i, kwargs['scale']) for i in self.frames]

        self.frame_idx = 0
        self.pos_idx = 0
        self.pos = pos
        self.changexy = kwargs['changexy'] if 'changexy' in kwargs else None
        self.rotate = kwargs['rotate'] if 'rotate' in kwargs else None
        self.particles = kwargs['particles'] if 'particles' in kwargs else []
        self.button = Button(self, **kwargs['button']) if 'button' in kwargs else None

    def animate(self, sc, **kwargs):
        if self.frame_idx >= len(self.frames):
            if self.inf:
                while self.frame_idx >= len(self.frames):
                    self.frame_idx -= len(self.frames)
            else:
                return False

        frame = kwargs['img'] if 'img' in kwargs else self.frames[self.frame_idx]
        frame = pygame.transform.rotate(frame, -1 * self.rotate * self.pos_idx) if self.rotate else frame

        if self.changexy:
            x, y = self.pos
            self.pos = self.changexy(frame, x, y, self.pos_idx)
        actions = {}
        if self.button:
            frame, actions = self.button.act(*[frame, self.pos, self.pos_idx], **kwargs)

        sc.blit(frame, self.pos)

        if self.particles:
            for p in self.particles:
                p.spawn(*[self.pos], **kwargs)
            if 'blit' not in actions:
                actions['blit'] = []
            for p in self.particles:
                actions['blit'] += p.act(*[self.pos], **kwargs)

        if 'blit' in actions:
            for x, p in actions['blit']:
                sc.blit(x, p)

        # speed calculation
        if self.speed == 1.0:
            self.frame_idx += 1
        elif self.speed > 1.0:
            self.frame_idx += int(self.speed)
            if self.mod and chance(self.mod*100):
                self.frame_idx += 1
        else:
            self.speed_repeats += 1
            if self.speed_repeats >= self.subspeed:
                self.speed_repeats = 0
                self.frame_idx += 1
            elif self.speed_repeats == int(self.subspeed) and chance(self.subspeedmod*100):
                self.speed_repeats = 0
                self.frame_idx += 1
        self.pos_idx += 1

        return actions

