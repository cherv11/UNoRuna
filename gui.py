from config import *


class GUI:
    texd = {i.split('.png')[0]: pygame.image.load(f'textures\\GUI\\{i}') for i in os.listdir('textures\\GUI') if i.endswith('.png')}

    def __init__(self):
        for i in GUI.texd.values():
            i.convert_alpha()
        self.level = None
        self.panel = GUI.texd['game1']

        self.hpbar = GUI.texd['hpbar']
        self.hpbar_mask = GUI.texd['hpbar_mask']
        self.hpbarsize = self.hpbar.get_width(), self.hpbar.get_height()
        self.hpbaroffset = 0, 0
        self.manabar = GUI.texd['manabar']
        self.manabar_mask = GUI.texd['manabar_mask']
        self.manabarsize = self.manabar.get_width(), self.manabar.get_height()
        self.manabaroffset = 0, self.hpbarsize[1]+7

        self.color = (0, 0, 0)
        self.color_panel()

        self.selected_unit = None
        self.selected_unit_menu = ''
        self.selected_unit_menu_pos = (0,0)
        self.bigmenu = None

    def load(self, level):
        self.level = level

    def blit(self, sc):
        pass
        sc.blit(self.panel, (0, 100))
        if self.selected_unit:
            sc.blit(self.panel, self.selected_unit_menu_pos)

    def make_unit_bar(self, unit):
        bar = pygame.Surface(UNIT_BAR_SIZE, pygame.SRCALPHA, 32)

        hpvalue = pygame.Surface((int(self.hpbarsize[0]*unit.hp/unit.maxhp), self.hpbarsize[1]), pygame.SRCALPHA, 32)
        hpvalue.set_colorkey(GREEN_MASK)
        hpvalue.fill(RED)
        hpvalue.blit(self.hpbar_mask, (0, 0))
        manavalue = pygame.Surface((int(self.manabarsize[0] * unit.mana / unit.maxmana), self.manabarsize[1]), pygame.SRCALPHA, 32)
        manavalue.set_colorkey(GREEN_MASK)
        manavalue.fill(BLUE)
        manavalue.blit(self.manabar_mask, (0, 0))

        bar.blit(hpvalue, self.hpbaroffset)
        bar.blit(manavalue, self.manabaroffset)
        bar.blit(self.hpbar, self.hpbaroffset)
        bar.blit(self.manabar, self.manabaroffset)
        return bar

    def make_fresh_from_bar(self, unit, bar, kef):
        if kef < 0:
            return bar
        freshvalue = pygame.Surface((int(self.hpbarsize[0] * (unit.lasthp[1]-unit.hp) / unit.maxhp * kef), self.hpbarsize[1]), pygame.SRCALPHA, 32)
        freshvalue.set_colorkey(GREEN_MASK)
        freshvalue.fill(YELLANGE)
        xoffset = int(self.hpbarsize[0]*unit.hp/unit.maxhp)
        freshvalue.blit(self.hpbar_mask, (-xoffset, 0))

        bar.blit(freshvalue, (self.hpbaroffset[0]+xoffset, self.hpbaroffset[1]))
        bar.blit(self.hpbar, self.hpbaroffset)
        return bar

    def recolor(self):
        if self.level.sp.sum() == 0:
            self.color = (0, 0, 0)
        else:
            count = 0
            color = [0, 0, 0]
            for k, v in self.level.sp:
                if v > 0:
                    count += 1
                    color[0] += DMGCOLORS[k][0]
                    color[1] += DMGCOLORS[k][1]
                    color[2] += DMGCOLORS[k][2]
            color[0] //= count
            color[1] //= count
            color[2] //= count
            self.color = tuple(color)
        self.color_panel()

    def color_panel(self):
        w, h = self.panel.get_size()
        # r, g, b = self.color
        # for x in range(w):
        #     for y in range(h):
        #         a = self.panel.get_at((x, y))[3]
        #         self.panel.set_at((x, y), (r, g, b, a))

    # TODO: интерфейс на позиции мыши (юниты, предметы, способности)
    #  ПКМ по юниту делает его selected_unit
    #  Общй инвентарь блоков
    #

    def fetch_click(self, button, mpos):
            pos = (mpos[0]-self.level.mp[0])/self.level.tile_size, (mpos[1]-self.level.mp[1])/self.level.tile_size
            menuActivateFlag = False
            for u in self.level.units:
                if u.cords.x + u.size.x / 2 > pos[0] > u.cords.x - u.size.x / 2 and u.cords.y > pos[1] > u.cords.y - u.size.y:
                    if button == 3:
                        if u.canbecontrolled and not u.dead:
                            self.level.selected_unit.mousepos = (pos[0] - self.level.mp[0], pos[1] - self.level.mp[1])
                            self.level.selected_unit = u
                            self.level.camera_bind = u
                            self.level.camera_bind_offset = (0, 0)
                            self.level.selected_skill = None
                            self.level.selected_item = None
                    elif button == 2:
                        menuActivateFlag = True
                        self.selected_unit = u
                        self.selected_unit_menu = 'main'
                        self.selected_unit_menu_pos = mpos
            if not menuActivateFlag:
                self.selected_unit = None
                self.selected_unit_menu = ''
                self.selected_unit_menu_pos = (0,0)



class Dialogs:
    def __init__(self):
        self.level = None

    def load(self, level):
        self.level = level

    # TODO: интерфейс для диалогов, сохранение и загрузка, интеракции
