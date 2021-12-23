import random
import sys

import pygame
import os  # os.path.join

import scripts.creatures as sc
# import scripts.battle as sb #imported through BattleScene constructor
import scripts.player as pl
import scripts.spritesheet as ss


# delay a certain amount of milliseconds
def __delay__(time: float):
    before = now = pygame.time.get_ticks()
    while now <= before + time:
        now = pygame.time.get_ticks()


# some color presets
class Color:
    def __init__(self):
        self.WHITE = (255, 255, 255)
        self.NEARLY_WHITE = (200, 200, 200)
        self.BLEEDING_WHITE = (255, 200, 200)
        self.BLOOMING_WHITE = (200, 255, 200)
        self.BLACK = (0, 0, 0)
        self.GRAY = (68, 68, 68)
        self.LIGHT_GRAY = (136, 136, 136)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)


# pressed keys and key definitions
class Keys:
    def __init__(self):
        # pygame keycodes of all pressed down keys
        keys_down: list[int, ...]
        self.keys_down = []

        # changeable key definitions for menu traversal and playing
        self.Q, self.W, self.E, self.A, self.S, self.D = pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_a, pygame.K_s, pygame.K_d
        self.NP_4, self.NP_5, self.NP_6, self.NP_1, self.NP_2, self.NP_3 = pygame.K_KP4, pygame.K_KP5, pygame.K_KP6, pygame.K_KP1, pygame.K_KP2, pygame.K_KP3
        self.UP, self.LEFT, self.DOWN, self.RIGHT = pygame.K_UP, pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT
        self.ENTER = pygame.K_RETURN
        self.CONFIRM_1, self.CONFIRM_2, self.BACK_1, self.BACK_2 = pygame.K_SPACE, pygame.K_KP_ENTER, pygame.K_ESCAPE, pygame.K_BACKSPACE

    def __clearKeys__(self):
        self.keys_down.clear()


# the base for user interface
class GUI:
    def __init__(self):
        pygame.init()
        self.running, self.playing = True, False

        pygame.display.set_caption('PYTHON CREATURE ARENA - Dawid Leszczynski WCY19IJ1S1')
        self.DISPLAY_W, self.DISPLAY_H = 1920, 1080
        self.display = pygame.Surface((self.DISPLAY_W, self.DISPLAY_H))
        self.window = pygame.display.set_mode((self.DISPLAY_W, self.DISPLAY_H), pygame.RESIZABLE)

        dirname = os.path.dirname(__file__)
        self.font_path = os.path.join(dirname, '../assets/art/fonts/GOODTIME.ttf')
        self.colors = Color()
        self.keys = Keys()

        self.main_menu = self.current_scene = MainMenu(self)

    # draw text centered around x and y coordinates
    def __blitText__(self, text: str, size: int, x: float, y: float, color: tuple[int, int, int]):

        # resolution scaling multiplier
        res_mp = self.DISPLAY_W / 1920

        # text scaling to resolution
        size = int(size * res_mp)

        # coordinates scaling to resolution
        x *= res_mp
        y *= res_mp

        font = pygame.font.Font(self.font_path, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.center = (x, y)
        self.display.blit(text_surface, text_rect)

    # update game based on events
    def __checkEvents__(self):

        # check all pending events
        for event in pygame.event.get():
            # quit game
            if event.type == pygame.QUIT:
                self.running, self.playing, self.current_scene.run_display = False, False, False
                pygame.quit()
                exit()

            # resize window
            if event.type == pygame.VIDEORESIZE:
                self.display = pygame.display.set_mode((event.w, event.h), flags=pygame.RESIZABLE)

                # keep 16:9 aspect ratio
                if self.DISPLAY_W != event.w:
                    self.DISPLAY_W, self.DISPLAY_H = event.w, event.w * 9 / 16
                elif self.DISPLAY_H != event.h:
                    self.DISPLAY_W, self.DISPLAY_H = event.h * 16 / 9, event.h

                # update window and display size
                self.display = pygame.Surface((self.DISPLAY_W, self.DISPLAY_H))
                self.window = pygame.display.set_mode((self.DISPLAY_W, self.DISPLAY_H), pygame.RESIZABLE)

            # check keys
            if event.type == pygame.KEYDOWN:  # any key was pressed down
                self.keys.keys_down.append(event.key)

    # blit screen, clear keys and check events
    def __blitScreen__(self):
        self.window.blit(self.display, (0, 0))
        pygame.display.update()
        self.keys.__clearKeys__()
        self.__checkEvents__()


class Scene:
    def __init__(self, gui: GUI):
        self.gui = gui
        self.run_display = True
        self.color_text = self.gui.colors.WHITE
        self.color_text_secondary = self.gui.colors.BLACK
        self.color_text_grayed_out = self.gui.colors.GRAY
        self.color_text_selected = self.gui.colors.GREEN
        self.selected_x = 0
        self.selected_y = 0
        self.max_x = 1
        self.max_y = 1

    # move selected state
    def __updateSelected__(self):
        for k in self.gui.keys.keys_down:
            if k == self.gui.keys.DOWN or k == self.gui.keys.S or k == self.gui.keys.NP_2:
                self.selected_y = (self.selected_y + 1) % self.max_y
            if k == self.gui.keys.UP or k == self.gui.keys.W or k == self.gui.keys.NP_5:
                self.selected_y = (self.selected_y - 1) % self.max_y
            if k == self.gui.keys.LEFT or k == self.gui.keys.A or k == self.gui.keys.NP_1:
                self.selected_x = (self.selected_x - 1) % self.max_x
            if k == self.gui.keys.RIGHT or k == self.gui.keys.D or k == self.gui.keys.NP_3:
                self.selected_x = (self.selected_x + 1) % self.max_x

    def __displayScene__(self):
        pass


# main menu of the game
class MainMenu(Scene):
    def __init__(self, gui):
        Scene.__init__(self, gui)
        self.text = ['START GAME', 'OPTIONS', 'QUIT GAME']
        self.text_offset_mp = [-90, 0, 90]
        self.max_x = 1
        self.max_y = 3

    def __changeMenuState__(self):
        for k in self.gui.keys.keys_down:
            if k == self.gui.keys.CONFIRM_1 or k == self.gui.keys.CONFIRM_2 or k == self.gui.keys.ENTER:
                if self.selected_y == 0:  # start a new battle

                    player1_creatures = player2_creatures = \
                        (sc.CreatureOccurrence(sc.all_creatures["PSAWARCA"]),
                         sc.CreatureOccurrence(sc.all_creatures["BAMAT"]))
                    player1 = pl.Player(1, player1_creatures, 3)
                    player2 = pl.Player(2, player2_creatures, 3)

                    self.run_display = False
                    battle_scene = BattleScene(self.gui, player1, player2, 1)
                    battle_scene.run_display = True
                    self.gui.current_scene = battle_scene

                if self.selected_y == 2:  # gracefully exit the game
                    pygame.display.quit()
                    pygame.quit()
                    sys.exit()

    # blit menu
    def __displayScene__(self):
        while self.run_display:
            self.__updateSelected__()
            self.__changeMenuState__()

            self.gui.display.fill(self.gui.colors.GRAY)
            for i in range(0, 3):
                if i == self.selected_y:
                    color = self.color_text_selected
                else:
                    color = self.color_text
                text_size = 96
                text_x = 960
                text_y = 540
                self.gui.__blitText__(self.text[i], text_size, text_x, text_y + self.text_offset_mp[i], color)
            self.gui.__blitScreen__()


class BattleScene(Scene):
    def __init__(self, gui: GUI, p1: pl.Player, p2: pl.Player, speed: float = 1):
        Scene.__init__(self, gui)
        self.color_health = gui.colors.RED
        self.p1 = p1
        self.p2 = p2
        self.speed = speed
        self.textbox_up = False
        self.p1_button_tips = ["Q", "W", "E", "A", "S", "D", "TAB"]
        self.p2_button_tips = ["4", "5", "6", "1", "2", "3", "ENT"]
        self.active_player = -1
        self.last_battle_text = ["", None]

        # get animated textbox
        self.dirname = os.path.dirname(__file__)
        textbox_sprite_path = os.path.join(self.dirname, f'../assets/art/interface/textbox_battle_sprite.png')
        textbox_sprite_sheet = ss.SpriteSheet(textbox_sprite_path)
        textbox_sprite_name = 'textbox_battle'
        self.textbox_image = []
        for i in range(1, 11):
            self.textbox_image.append(textbox_sprite_sheet.parse_sprite(f'{textbox_sprite_name}{i}'))

        import scripts.battle as sb
        self.battle = sb.Battle(self, p1, p2, speed)

    def __displayScene__(self):
        # while running, battle.py will do the work
        while self.run_display:
            pass

        # after it's done, go back to main menu
        self.gui.main_menu.run_display = True
        self.gui.current_scene = self.gui.main_menu

    def __changeHUD__(self):
        hud_path = os.path.join(self.dirname, f'../assets/art/interface/abilities/p1_{self.p1.ac.c.name}.png')
        self.p1_hud = pygame.image.load(hud_path)
        hud_path = os.path.join(self.dirname, f'../assets/art/interface/abilities/p2_{self.p2.ac.c.name}.png')
        self.p2_hud = pygame.image.load(hud_path)

    def __animateTextbox__(self, zoom_in: bool = True):
        res_mp = self.gui.DISPLAY_W / 1920

        # I'll use lambda functions for the loop to be able to "fade" the text bar in and out without writing it all twice
        if zoom_in:
            i = 0
            x = lambda index: True if index <= 9 else False
            y = lambda index: index + 1
        else:
            self.textbox_up = False
            self.last_battle_text[0] = None
            self.last_battle_text[1] = None
            i = 9
            x = lambda index: True if index >= 0 else False
            y = lambda index: index - 1

        while x(i):
            self.gui.display.fill(self.gui.colors.GRAY)
            self.__blitHealth__()
            self.__blitHUD__()
            __delay__(10 / self.speed)

            textbox = pygame.transform.scale(self.textbox_image[i], (1460 * res_mp, 140 * res_mp))
            rect = self.textbox_image[i].get_rect()
            rect = rect.move((230 * res_mp, 679 * res_mp))
            self.gui.display.blit(textbox, rect)
            self.gui.__blitScreen__()
            i = y(i)

        if not zoom_in:
            __delay__(10 / self.speed)
            self.gui.display.fill(self.gui.colors.GRAY)
            self.__blitHealth__()
            self.__blitHUD__()
            self.gui.__blitScreen__()
        else:
            self.textbox_up = True

        __delay__(100 / self.speed)

    def __blitTextbox__(self):
        res_mp = self.gui.DISPLAY_W / 1920
        textbox = pygame.transform.scale(self.textbox_image[9], (1460 * res_mp, 140 * res_mp))
        rect = self.textbox_image[9].get_rect()
        rect = rect.move((230 * res_mp, 679 * res_mp))
        self.gui.display.blit(textbox, rect)

    def __blitBattleText__(self, line1: str, line2: str = None):
        self.last_battle_text[0] = None
        self.last_battle_text[1] = None

        if line2 is None:
            y = 750
            font_size = 50
        else:
            y = 720
            font_size = 45

        message = ''
        for c in line1:
            message += c
            self.gui.display.fill(self.gui.colors.GRAY)
            self.__blitHealth__()
            self.__blitTextbox__()
            self.__blitHUD__()


            self.gui.__blitText__(message, font_size, 960, y, self.gui.colors.BLACK)
            self.gui.__blitScreen__()
            if c == '!' or c == '?':
                __delay__(500 / self.speed)  # 500ms delay with ! or ?
            elif c == '.':
                __delay__(200 / self.speed)  # 500ms delay with .
            else:
                __delay__(15 / self.speed)  # 15ms delay with letter
        self.last_battle_text[0] = message

        if line2 is not None:
            self.last_battle_text[1] = ""
            message = ""
            for c in line2:
                message += c
                self.gui.display.fill(self.gui.colors.GRAY)
                self.__blitHealth__()
                self.__blitTextbox__()
                self.__blitHUD__()
                self.gui.__blitText__(message, font_size, 960, y + 60, self.gui.colors.BLACK)
                self.gui.__blitScreen__()
                if c == '!' or c == '?':
                    __delay__(500 / self.speed)  # 500ms delay with ! or ?
                elif c == '.':
                    __delay__(200 / self.speed)  # 500ms delay with .
                else:
                    __delay__(15 / self.speed)  # 15ms delay with letter
            self.last_battle_text[1] = message

        # 500ms delay at the end of the message
        __delay__(500 / self.speed)

    def __blitHealth__(self):
        # resolution scaling multiplier
        res_mp = self.gui.DISPLAY_W / 1920

        # health
        health_bar_width = 906 * self.p1.ac.health / self.p1.ac.c.health
        health_rect = pygame.Rect((res_mp * 28, res_mp * 138, res_mp * health_bar_width, res_mp * 28))
        self.gui.display.fill(self.color_health, health_rect)

        health_text = f"-- {self.p1.ac.health}/{self.p1.ac.c.health} --"
        self.gui.__blitText__(health_text, 45, 481, 210, self.gui.colors.WHITE)

        health_bar_width = 906 * self.p2.ac.health / self.p2.ac.c.health
        health_rect = pygame.Rect((res_mp * 987, res_mp * 138, res_mp * health_bar_width, res_mp * 28))
        self.gui.display.fill(self.color_health, health_rect)

        health_text = f"-- {self.p2.ac.health}/{self.p2.ac.c.health} --"
        self.gui.__blitText__(health_text, 45, 1440, 210, self.gui.colors.WHITE)

    def __animateHealth__(self, ac: sc.CreatureOccurrence, prev_health: int):

        # resolution scaling multiplier
        res_mp = self.gui.DISPLAY_W / 1920

        # which player's hud should be updated?
        if self.p1.ac == ac:
            hbar_x = 28
            htext_x = 481
            hbar2_x = 987
            htext2_x = 1440
            op = self.p2.ac
            name_x = 480
            if self.active_player == -1 or self.active_player == 1:
                active = True
            else:
                active = False
        else:
            hbar_x = 987
            htext_x = 1440
            hbar2_x = 28
            htext2_x = 481
            op = self.p1.ac
            name_x = 1440
            if self.active_player == -1 or self.active_player == 2:
                active = True
            else:
                active = False

        # add or remove health?
        if prev_health >= ac.health:
            is_healing = False
            update_health = lambda hp: hp - 1
            should_update = lambda hp: True if hp > ac.health else False
        else:
            is_healing = True
            update_health = lambda hp: hp + 1
            should_update = lambda hp: True if hp < ac.health else False

        while should_update(prev_health):
            # update health by 1 point
            prev_health = update_health(prev_health)

            # redraw background
            self.gui.display.fill(self.gui.colors.GRAY)

            # update health on gui by 1 point
            health_bar_width = 906 * prev_health / ac.c.health
            health_rect = pygame.Rect((res_mp * hbar_x, res_mp * 138, res_mp * health_bar_width, res_mp * 28))
            self.gui.display.fill(self.color_health, health_rect)
            health_text = f"-- {prev_health}/{ac.c.health} --"
            self.gui.__blitText__(health_text, 45, htext_x, 210, self.gui.colors.WHITE)

            # draw health of opponent
            health_bar_width = 906 * op.health / op.c.health
            health_rect = pygame.Rect((res_mp * hbar2_x, res_mp * 138, res_mp * health_bar_width, res_mp * 28))
            self.gui.display.fill(self.color_health, health_rect)
            health_text = f"-- {op.health}/{op.c.health} --"
            self.gui.__blitText__(health_text, 45, htext2_x, 210, self.gui.colors.WHITE)

            # finish up hud
            self.__blitHUD__()

            # change text color
            # p1
            if active and is_healing:
                color = self.gui.colors.GREEN
            elif active and not is_healing:
                color = self.gui.colors.RED
            elif not active and is_healing:
                color = self.gui.colors.BLOOMING_WHITE
            else:
                color = self.gui.colors.BLEEDING_WHITE

            self.gui.__blitText__(f"{ac.c.name}", 80, name_x, 65, color)

            # blit screen
            self.gui.__blitScreen__()

            __delay__(15 / self.speed)
        __delay__(500 / self.speed)

    def __blitHUD__(self):
        # resolution scaling multiplier
        res_mp = self.gui.DISPLAY_W / 1920

        # textbox
        if self.textbox_up is True:
            self.__blitTextbox__()
            if self.last_battle_text[1] is None and self.last_battle_text[0] is not None:
                self.gui.__blitText__(self.last_battle_text[0], 50, 960, 750, self.gui.colors.BLACK)
            elif self.last_battle_text[1] is not None and self.last_battle_text[0] is not None:
                self.gui.__blitText__(self.last_battle_text[0], 45, 960, 720, self.gui.colors.BLACK)
                self.gui.__blitText__(self.last_battle_text[1], 45, 960, 780, self.gui.colors.BLACK)

        # hud
        if self.p1_hud is None or self.p2_hud is None:
            self.__changeHUD__()

        ability = pygame.transform.scale(self.p1_hud, (self.gui.DISPLAY_W, self.gui.DISPLAY_H))
        rect = ability.get_rect()
        rect = rect.move((0, 0))
        self.gui.display.blit(ability, rect)

        ability = pygame.transform.scale(self.p2_hud, (self.gui.DISPLAY_W, self.gui.DISPLAY_H))
        rect = ability.get_rect()
        rect = rect.move((0, 0))
        self.gui.display.blit(ability, rect)

        # creature names and whether they are active or not
        # p1
        if self.active_player == -1 or self.active_player == 1:
            color = self.gui.colors.BLACK
        else:
            color = self.gui.colors.NEARLY_WHITE
        self.gui.__blitText__(f"{self.p1.ac.c.name}", 80, 480, 65, color)
        # p2
        if self.active_player == -1 or self.active_player == 2:
            color = self.gui.colors.BLACK
        else:
            color = self.gui.colors.NEARLY_WHITE
        self.gui.__blitText__(f"{self.p2.ac.c.name}", 80, 1440, 65, color)

        # cooldowns
        for p in (self.p1, self.p2):

            # some variables depending on which player is chosen
            if p == self.p1:
                tips = self.p1_button_tips
                x = 107
            else:
                tips = self.p2_button_tips
                x = 1330

            # cycle through all abilities with cooldowns
            for i in range(0, 6):
                if p.ac.cooldowns[i] == 0 and p.ai < 0:
                    text = tips[i]
                    color = self.gui.colors.BLACK
                else:
                    text = str(p.ac.cooldowns[i])
                    color = self.gui.colors.LIGHT_GRAY

                # some variables depending on iteration
                y = 908
                j = i
                if i > 2:
                    y = 999
                    j = i - 3

                # get the text on the board!
                self.gui.__blitText__(text, 45, x + j * 242, y, color)


    def __animateRoll__(self, roll: int, chance: int, for_status: bool = False):
        # only animate when chances are uncertain
        if chance < 100:

            # text 3 is just number = delay multiplier and x = terminate
            text = ["", "", "00000000000000000000000000000011226699x", ""]
            if for_status:
                text[0] = "ROLLING FOR STATUS"
            else:
                text[0] = "ROLLING FOR HIT"

            to_beat = 100 - chance
            text[1] = "ROLL TO BEAT: " + str(to_beat)

            if roll > to_beat:
                text[3] = "SUCCESS!"
            else:
                text[3] = "FAILURE!"

            for i in range(0, 4):
                message = ''
                __delay__(200 / self.speed)  # 200ms delay between lines
                for c in text[i]:
                    message += c
                    self.gui.display.fill(self.gui.colors.GRAY)
                    self.__blitHealth__()
                    self.__blitTextbox__()
                    self.__blitHUD__()


                    # keep text when going to new line
                    if i > 0:
                        self.gui.__blitText__(text[0], 30, 960, 220, self.gui.colors.WHITE)
                        if i > 1:
                            self.gui.__blitText__(text[1], 30, 960, 250, self.gui.colors.WHITE)
                            if i == 3:
                                number = "-- " + str(roll) + " --"
                                self.gui.__blitText__(number, 30, 960, 280, self.gui.colors.WHITE)

                    if i == 0:  # 1st line - what is this roll for?
                        self.gui.__blitText__(message, 30, 960, 220, self.gui.colors.WHITE)

                    elif i == 1:  # 2nd line - roll to beat?
                        self.gui.__blitText__(message, 30, 960, 250, self.gui.colors.WHITE)

                    elif i == 2:  # 3rd line - random number rolling
                        if c == 'x':  # do the correct number, this is the last iteration
                            number = "-- " + str(roll) + " --"
                            __delay__(30 * 9 / self.speed)
                        else:  # random number for SUSPENSE!
                            number = "-- " + str(random.randrange(0, 100)) + " --"
                            __delay__(30 * float(c) / self.speed)
                        self.gui.__blitText__(number, 30, 960, 280, self.gui.colors.WHITE)

                    else:  # 5th line - draw out success message
                        self.gui.__blitText__(message, 30, 960, 340, self.gui.colors.WHITE)

                    self.gui.__blitScreen__()
                    if c == '!' or c == '?':
                        __delay__(500 / self.speed)  # 500ms delay with ! or ?
                    elif c == '.':
                        __delay__(200 / self.speed)  # 500ms delay with .
                    else:
                        __delay__(15 / self.speed)  # 15ms delay with letter

            __delay__(500 / self.speed)  # 500ms delay


    def __animateMovePriority__(self, p1_move_speed: int, p2_move_speed: int, moves_first: int):
        text = ["WHO MOVES FIRST?", f"{p1_move_speed}-SPEED VS {p2_move_speed}-SPEED", "", ""]

        if p1_move_speed == p2_move_speed:
            text[2] = "UNDECIDED!"
        elif moves_first == 1:
            text[2] = "PLAYER 1 IS FASTER!"
        else:
            text[2] = "PLAYER 2 IS FASTER!"

        if moves_first == 1:
            text[3] = "PLAYER 1 MOVES FIRST!"
        else:
            text[3] = "PLAYER 2 MOVES FIRST!"

        for i in range(0, 4):
            message = ''
            __delay__(200 / self.speed)  # 200ms delay between lines
            for c in text[i]:
                message += c
                self.gui.display.fill(self.gui.colors.GRAY)
                self.__blitHealth__()
                self.__blitHUD__()

                # keep text when going to new line
                if i > 0:
                    self.gui.__blitText__(text[0], 30, 960, 220, self.gui.colors.WHITE)
                    if i > 1:
                        self.gui.__blitText__(text[1], 30, 960, 250, self.gui.colors.WHITE)
                        if i > 2:
                            self.gui.__blitText__(text[2], 30, 960, 310, self.gui.colors.WHITE)

                if i == 0:  # 1st line - question
                    self.gui.__blitText__(message, 30, 960, 220, self.gui.colors.WHITE)

                elif i == 1:  # 2nd line - speed comparison
                    self.gui.__blitText__(message, 30, 960, 250, self.gui.colors.WHITE)

                elif i == 2:  # 4th line - IS IT DECIDED WITHOUT CHANCE?
                    self.gui.__blitText__(message, 30, 960, 310, self.gui.colors.WHITE)

                else:  # 5th line - who moves first though?
                    self.gui.__blitText__(message, 30, 960, 340, self.gui.colors.WHITE)

                self.gui.__blitScreen__()
                if c == '!' or c == '?':
                    __delay__(500 / self.speed)  # 500ms delay with ! or ?
                elif c == '.':
                    __delay__(200 / self.speed)  # 500ms delay with .
                else:
                    __delay__(15 / self.speed)  # 15ms delay with letter

        __delay__(500 / self.speed)  # 500ms delay
