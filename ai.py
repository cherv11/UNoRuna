from config import *


class AI:
    def __init__(self, unit):
        self.unit = unit

    @classmethod
    def choosepos(cls):
        pass


def mouse_active(level, unit):
    if level.selected_unit is unit:
        return pygame.mouse.get_pos()
    if unit.mousepos:
        return unit.mousepos[0]+level.mp[0], unit.mousepos[1]+level.mp[1]
    return  # TODO: AI instead of this