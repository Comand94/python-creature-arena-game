import math
import random
import sys

import pygame
import os  # os.path.join

import scripts.creatures as cr
# import scripts.battle as sb #imported through BattleScene constructor
import scripts.player as pl
import scripts.spritesheet as ss

# some color presets
class Color:
    def __init__(self):
        self.WHITE = (255, 255, 255)
        self.NEARLY_WHITE = (200, 200, 200)
        self.BLEEDING_WHITE = (255, 200, 200)
        self.GREENING_WHITE = (200, 255, 200)
        self.BLUEISH_WHITE = (200, 200, 255)
        self.CYANISH_WHITE = (190, 230, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (68, 68, 68)
        self.BLUEISH_GRAY = (68, 68, 102)
        self.LIGHT_GRAY = (136, 136, 136)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)
        self.CYAN = (0, 200, 255)
        self.PINK = (255, 0, 255)


# pressed keys and key definitions
class Keys:
    def __init__(self):
        # pygame keycodes of all pressed down keys
        keys_down: list[int, ...]
        self.keys_down = []

        # changeable key definitions for menu traversal and playing, for both players
        self.Q, self.W, self.E, self.A, self.S, self.D = [pygame.K_q, pygame.K_KP4], [pygame.K_w, pygame.K_KP5], [
            pygame.K_e, pygame.K_KP6], \
                                                         [pygame.K_a, pygame.K_KP1], [pygame.K_s, pygame.K_KP2], [
                                                             pygame.K_d, pygame.K_KP3]

        self.CONFIRM, self.BACK, self.INFO = [pygame.K_SPACE, pygame.K_KP_ENTER], [pygame.K_ESCAPE,
                                                                                   pygame.K_BACKSPACE], [pygame.K_TAB,
                                                                                                         pygame.K_KP_PLUS]

        # universal keys
        self.UP, self.LEFT, self.DOWN, self.RIGHT = pygame.K_UP, pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT
        self.ENTER = pygame.K_RETURN

    def __clearKeys__(self):
        self.keys_down.clear()


# the base for user interface
class GUI:
    def __init__(self):
        pygame.init()
        self.running = True
        self.paused = False
        self.return_to_menu = False
        self.skip_animations = False

        pygame.display.set_caption('PYTHON CREATURE ARENA - Dawid Leszczynski WCY19IJ1S1')
        self.DISPLAY_W, self.DISPLAY_H = 1920, 1080
        self.display = pygame.Surface((self.DISPLAY_W, self.DISPLAY_H)) # standard game display
        self.display_paused = pygame.Surface((self.DISPLAY_W, self.DISPLAY_H)) # semi-transparent display
        self.display_paused_text = pygame.Surface((self.DISPLAY_W, self.DISPLAY_H)) # to be displayed on top of display_paused
        self.window = pygame.display.set_mode((self.DISPLAY_W, self.DISPLAY_H), pygame.RESIZABLE)

        dirname = os.path.dirname(__file__)
        self.font_path = os.path.join(dirname, '../assets/art/fonts/GOODTIME.ttf')
        self.colors = Color()
        self.keys = Keys()
        self.allowed_speed = [0.5, 1, 1.5, 2, 3, 4, 6, 50]
        self.current_speed_index = 2
        self.speed = self.allowed_speed[self.current_speed_index]
        self.delay_clock = pygame.time.Clock()

        self.main_menu = self.current_scene = MainMenuScene(self)

    # delay a certain amount of milliseconds
    def __delay__(self, time: int):
        time = time / self.speed
        before = now = self.delay_clock.tick()
        while now <= before + time:
            now += self.delay_clock.tick()

            if self.paused: # pause the delay
                dt = 0
                while self.paused: # if paused, keep "pausing" the clock
                    dt += self.delay_clock.tick()
                    now += dt
                    before += dt
                    self.__blitScreen__() # to be able to unpause at all during delay and display pause menu - event handling and all those good things
                time = time / self.speed # update time, as speed could have been altered
                self.__blitScreen__()
            if self.return_to_menu:
                return

    # draw text centered around x and y coordinates
    def __blitText__(self, text: str, size: int, x: float, y: float, color: tuple[int, int, int], display: pygame.Surface = None):

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
        if display is None:
            self.display.blit(text_surface, text_rect)
        else:
            display.blit(text_surface, text_rect)

    # update game based on events
    def __checkEvents__(self):

        # check all pending events
        for event in pygame.event.get():
            # quit game
            if event.type == pygame.QUIT:
                self.running, self.current_scene.run_display = False, False
                pygame.display.quit()
                pygame.quit()
                sys.exit()

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
                self.display_paused = pygame.Surface((self.DISPLAY_W, self.DISPLAY_H))
                self.display_paused_text = pygame.Surface((self.DISPLAY_W, self.DISPLAY_H))
                self.window = pygame.display.set_mode((self.DISPLAY_W, self.DISPLAY_H), pygame.RESIZABLE)

                # rescale images
                print(f"current_scene {self.current_scene.__class__.__name__}")
                self.current_scene.__rescaleEvent__()

            # check keys
            if event.type == pygame.KEYDOWN:  # any key was pressed down
                if event.key == self.keys.BACK[0] or event.key == self.keys.BACK[1]:
                    self.paused = not self.paused
                elif self.paused:
                    if event.key == self.keys.ENTER or event.key == self.keys.CONFIRM[0] or event.key == self.keys.CONFIRM[1]:
                        self.return_to_menu = True
                        self.current_scene.run_display = False
                        self.main_menu.run_display = True
                        self.current_scene = self.main_menu
                        self.paused = False
                    if event.key == self.keys.LEFT or event.key == self.keys.A[0] or event.key == self.keys.A[1]:
                        self.current_speed_index = self.current_speed_index - 1
                        if self.current_speed_index < 0:
                            self.current_speed_index = 0
                        self.speed = self.allowed_speed[self.current_speed_index]
                    if event.key == self.keys.RIGHT or event.key == self.keys.D[0] or event.key == self.keys.D[1]:
                        self.current_speed_index = self.current_speed_index + 1
                        if self.current_speed_index >= len(self.allowed_speed):
                            self.current_speed_index = len(self.allowed_speed) - 1
                        self.speed = self.allowed_speed[self.current_speed_index]
                    if event.key == self.keys.INFO[0] or event.key == self.keys.INFO[1]:
                        self.skip_animations = not self.skip_animations
                else:
                    self.keys.keys_down.append(event.key)

    # blit screen, clear keys and check events
    def __blitScreen__(self):
        self.window.blit(self.display, (0, 0))

        if self.paused:
            self.__blitPaused__()

        pygame.display.update()
        self.keys.__clearKeys__()
        self.__checkEvents__()

    def __blitPaused__(self):
        self.display_paused.fill((68, 68, 68))
        self.display_paused.set_alpha(200)
        self.window.blit(self.display_paused, (0, 0))
        y_mod = 80
        self.display_paused_text.fill(self.colors.BLACK) # remove old things from this display when coupled with colorkey line below
        self.__blitText__("PAUSED", 120, 960, 300 + y_mod, self.colors.RED, self.display_paused_text)
        self.__blitText__("THE GAME WAS PAUSED", 60, 960, 420 + y_mod, self.colors.WHITE, self.display_paused_text)
        self.__blitText__("ESC/BACKSPACE - UNPAUSE", 60, 960, 480 + y_mod, self.colors.WHITE, self.display_paused_text)
        self.__blitText__("ENTER/SPACE - LOAD TO MENU", 60, 960, 540 + y_mod, self.colors.WHITE,
                          self.display_paused_text)
        self.__blitText__(f"A/D - ANIMATION SPEED: {self.speed}", 60, 960, 600 + y_mod, self.colors.WHITE,
                          self.display_paused_text)
        self.__blitText__(f"TAB - SKIP ANIMATIONS: {self.skip_animations}", 60, 960, 660 + y_mod, self.colors.WHITE,
                          self.display_paused_text)
        self.display_paused_text.set_colorkey((0, 0, 0))
        self.window.blit(self.display_paused_text, (0, 0))

class Scene:
    def __init__(self, gui: GUI):
        self.gui = gui
        self.run_display = True
        self.color_text = self.gui.colors.WHITE
        self.color_text_secondary = self.gui.colors.BLACK
        self.color_text_grayed_out = self.gui.colors.GRAY
        self.color_text_selected = self.gui.colors.GREEN

    def __cyclePrimarySprites__(self):
        pass

    def __blitPrimarySprites__(self):
        pass

    def __displayScene__(self):
        pass

    def __rescaleEvent__(self):
        pass

class MatchSettingsScene(Scene):
    def __init__(self, gui):
        Scene.__init__(self, gui)
        self.text = ['START MATCH', 'PLAYER', 'CREATURE 1', 'CREATURE 2', 'CREATURE 3']
        self.text_offset_mp = [-150, 100, 200, 300, 400]
        self.selected_x = 0
        self.selected_y = 0
        self.max_x = 1
        self.max_y = 5
        self.player_ai = [-1, -1]
        self.player_creatures = [[-1, -2, -2], [-1, -2, -2]]

    def __updateSelected__(self):
        for k in self.gui.keys.keys_down:
            if k == self.gui.keys.ENTER or k == self.gui.keys.CONFIRM[0] or k == self.gui.keys.CONFIRM[1]:
                if self.selected_y == 0: # start game with current settings
                    player1_creatures = []
                    player2_creatures = []

                    for x in (0, 1, 2):
                        if self.player_creatures[0][x] != -2:
                            if self.player_creatures[0][x] == -1:
                                p1_creature_index = random.randrange(0, len(cr.all_creatures))
                            else:
                                p1_creature_index = self.player_creatures[0][x]
                            player1_creatures.append(cr.CreatureOccurrence(cr.all_creatures[p1_creature_index]))

                        if self.player_creatures[1][x] != -2:
                            if self.player_creatures[1][x] == -1:
                                p2_creature_index = random.randrange(0, len(cr.all_creatures))
                            else:
                                p2_creature_index = self.player_creatures[1][x]
                            player2_creatures.append(cr.CreatureOccurrence(cr.all_creatures[p2_creature_index]))

                    if len(player1_creatures) <= 0 or len(player2_creatures) <= 0:
                        return

                    player1 = pl.Player(1, player1_creatures, self.player_ai[0])
                    player2 = pl.Player(2, player2_creatures, self.player_ai[1])

                    self.run_display = False
                    self.gui.current_scene = BattleScene(self.gui, player1, player2, False)

            if k == self.gui.keys.DOWN or k == self.gui.keys.S[0] or k == self.gui.keys.S[1]: # one down
                self.selected_y = (self.selected_y + 1) % self.max_y

            if k == self.gui.keys.UP or k == self.gui.keys.W[0] or k == self.gui.keys.W[1]: # one up
                self.selected_y = (self.selected_y - 1) % self.max_y

            if k == self.gui.keys.LEFT or k == self.gui.keys.A[0] or k == self.gui.keys.A[1]: # change left side
                if self.selected_y == 1: # ai
                    self.player_ai[0] += 1
                    if self.player_ai[0] > 10:
                        self.player_ai[0] = -1
                elif self.selected_y >= 2: # creature
                    self.player_creatures[0][self.selected_y - 2] += 1
                    if self.player_creatures[0][self.selected_y - 2] >= len(cr.all_creatures):
                        self.player_creatures[0][self.selected_y - 2] = -2

            if k == self.gui.keys.RIGHT or k == self.gui.keys.D[0] or k == self.gui.keys.D[1]: # change right side
                if self.selected_y == 1: # ai
                    self.player_ai[1] += 1
                    if self.player_ai[1] > 10:
                        self.player_ai[1] = -1
                elif self.selected_y >= 2: # creature
                    self.player_creatures[1][self.selected_y - 2] += 1
                    if self.player_creatures[1][self.selected_y - 2] >= len(cr.all_creatures):
                        self.player_creatures[1][self.selected_y - 2] = -2

    def __displayScene__(self):
        while self.run_display:
            self.gui.return_to_menu = False
            self.gui.display.fill(self.gui.colors.GRAY)
            self.__updateSelected__()
            for i in range(0, 5):
                if i == self.selected_y:
                    color = self.color_text_selected
                else:
                    color = self.color_text
                text_size = 60
                text_size_2 = 30
                text_size_3 = 90
                text_x = 960
                text_y = 300

                if i == 0:
                    size = text_size_3
                else:
                    size = text_size

                self.gui.__blitText__(self.text[i], size, text_x, text_y + self.text_offset_mp[i], color)

                if i == 0:
                    self.gui.__blitText__("PLAYER 1", text_size_2, text_x - 400,
                                          text_y + self.text_offset_mp[i + 1] - 100, self.gui.colors.CYAN)
                    self.gui.__blitText__("PLAYER 2", text_size_2, text_x + 400,
                                          text_y + self.text_offset_mp[i + 1] - 100, self.gui.colors.RED)
                elif i == 1:
                    if self.player_ai[0] == -1:
                        player_text = "HUMAN"
                    else:
                        player_text = f"AI LVL: {self.player_ai[0]}"
                    self.gui.__blitText__(player_text, text_size_2, text_x - 400,
                                            text_y + self.text_offset_mp[i], self.gui.colors.CYANISH_WHITE)

                    if self.player_ai[1] == -1:
                        player_text = "HUMAN"
                    else:
                        player_text = f"AI LVL: {self.player_ai[1]}"
                    self.gui.__blitText__(player_text, text_size_2, text_x + 400,
                                            text_y + self.text_offset_mp[i], self.gui.colors.BLEEDING_WHITE)

                elif i >= 2:
                    if self.player_creatures[0][i - 2] == -2:
                        p1_creature_name = "NONE"
                        p1_creature_description = "NO CREATURE IN THE FIRST SLOT"
                    elif self.player_creatures[0][i - 2] == -1:
                        p1_creature_name = "? ? ?"
                        p1_creature_description = "UNKNOWN CHALLENGER"
                    else:
                        p1_creature_name = cr.all_creatures[self.player_creatures[0][i - 2]].name
                        p1_creature_description = cr.all_creatures[self.player_creatures[0][i - 2]].desc

                    if self.player_creatures[1][i - 2] == -2:
                        p2_creature_name = "NONE"
                        p2_creature_description = "NO CREATURE IN THE FIRST SLOT"
                    elif self.player_creatures[1][i - 2] == -1:
                        p2_creature_name = "? ? ?"
                        p2_creature_description = "UNKNOWN CHALLENGER"
                    else:
                        p2_creature_name = cr.all_creatures[self.player_creatures[1][i - 2]].name
                        p2_creature_description = cr.all_creatures[self.player_creatures[1][i - 2]].desc

                    self.gui.__blitText__(p1_creature_name, text_size_2, text_x - 400,
                                          text_y + self.text_offset_mp[i], self.gui.colors.CYANISH_WHITE)
                    self.gui.__blitText__(p2_creature_name, text_size_2, text_x + 400,
                                          text_y + self.text_offset_mp[i], self.gui.colors.BLEEDING_WHITE)

                    if i == 2:
                        self.gui.__blitText__(p1_creature_description, text_size_2, text_x,
                                              text_y + self.text_offset_mp[i] + 350, self.gui.colors.CYANISH_WHITE)
                        self.gui.__blitText__("--- VS ---", text_size, text_x,
                                              text_y + self.text_offset_mp[i] + 410, self.gui.colors.WHITE)
                        self.gui.__blitText__(p2_creature_description, text_size_2, text_x,
                                              text_y + self.text_offset_mp[i] + 470, self.gui.colors.BLEEDING_WHITE)


            self.gui.__blitScreen__()


# main menu of the game
class MainMenuScene(Scene):
    def __init__(self, gui):
        Scene.__init__(self, gui)
        self.text = ['NEW MATCH', 'CREATURE INDEX', 'QUIT GAME']
        self.text_offset_mp = [-100, 0, 100]
        self.selected_x = 0
        self.selected_y = 0
        self.max_x = 1
        self.max_y = 3

    def __updateSelected__(self):
        for k in self.gui.keys.keys_down:
            if k == self.gui.keys.DOWN:
                self.selected_y = (self.selected_y + 1) % self.max_y
            if k == self.gui.keys.UP:
                self.selected_y = (self.selected_y - 1) % self.max_y
            if k == self.gui.keys.LEFT:
                self.selected_x = (self.selected_x - 1) % self.max_x
            if k == self.gui.keys.RIGHT:
                self.selected_x = (self.selected_x + 1) % self.max_x

            for i in (0, 1):
                if k == self.gui.keys.S[i]:
                    self.selected_y = (self.selected_y + 1) % self.max_y
                if k == self.gui.keys.W[i]:
                    self.selected_y = (self.selected_y - 1) % self.max_y
                if k == self.gui.keys.A[i]:
                    self.selected_x = (self.selected_x - 1) % self.max_x
                if k == self.gui.keys.D[i]:
                    self.selected_x = (self.selected_x + 1) % self.max_x

    def __changeMenuState__(self):
        for k in self.gui.keys.keys_down:
            if k == self.gui.keys.ENTER or k == self.gui.keys.CONFIRM[0] or k == self.gui.keys.CONFIRM[1]:
                if self.selected_y == 0:  # open new match settings
                    self.run_display = False
                    self.gui.current_scene = MatchSettingsScene(self.gui)

                if self.selected_y == 1: # start index
                    player1_creatures = player2_creatures = []

                    random_creature_index = random.randrange(0, len(cr.all_creatures))
                    player1_creatures.append(cr.CreatureOccurrence(cr.all_creatures[random_creature_index]))
                    random_creature_index = random.randrange(0, len(cr.all_creatures))
                    player2_creatures.append(cr.CreatureOccurrence(cr.all_creatures[random_creature_index]))

                    player1 = pl.Player(1, player1_creatures, -1)
                    player2 = pl.Player(2, player2_creatures, -1)

                    self.run_display = False
                    self.gui.current_scene = BattleScene(self.gui, player1, player2, True)

                if self.selected_y == 2:  # gracefully exit the game
                    pygame.display.quit()
                    pygame.quit()
                    sys.exit()

    # blit menu
    def __displayScene__(self):
        while self.run_display:
            self.gui.return_to_menu = False
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
    def __init__(self, gui: GUI, p1: pl.Player, p2: pl.Player, testing: bool = False):
        Scene.__init__(self, gui)
        self.health_color = gui.colors.RED
        self.background_color = self.gui.colors.GRAY
        self.p1 = p1
        self.p2 = p2
        self.player_button_tips = [["Q", "W", "E", "A", "S", "D", "TAB", "SPACE"], ["4", "5", "6", "1", "2", "3", "PLUS", "ENTER"]]

        # selected creature indices in case there are battles of more than 1 creature later
        self.player_selected_creature = [0, 0]

        # battletext textbox
        self.textbox_up = False

        # decides creature name color
        self.active_player = -1

        # battle text persistence between some methods
        self.last_battle_text = ["", None]

        # calculated player bonuses
        self.player_aim_mods = [0, 0]
        self.player_def_mods = [0, 0]
        self.player_thorn_lows = [0, 0]
        self.player_thorn_highs = [0, 0]

        # for which players are infoboxes (of any type) up
        self.player_infobox_up = [False, False]

        # infobox selected options
        self.player_max_x = [len(cr.all_types), 6, 1]
        self.player_max_y = [1, 9, 1]
        self.player_max_z = 3
        self.player_selected_x = [[0, 0, 0], [0, 0, 0]]
        self.player_selected_y = [[0, 0, 0], [0, 0, 0]]
        self.player_selected_z = [1, 1]

        self.testing = testing # whether to load battle or creature index
        self.hud_clock = pygame.time.Clock() # for hud hotfix

        # creature animations are on separate clocks so they are not synchronized
        self.animation_clock = [pygame.time.Clock(), pygame.time.Clock()]
        self.animation_now = [0, 0]
        self.animation_before = [0, 0]

        # get directory
        self.dirname = os.path.dirname(__file__)

        # hud images
        self.textbox_images = []
        self.player_hud_images = []
        self.player_infobox_images = []
        self.player_typebox_images = []
        self.player_creaturebox_images = []
        self.selected_images = []

        # controls for animations
        self.creature_idle_images_index = [0, 0]
        self.creature_idle_images_reverse = [False, False]

        # creatures, abilities and active statuses (images)
        self.creature_idle_images = [[], []]
        self.creature_abilities_images = [[], []]
        self.creature_abilities_mini_images = [[], []]
        self.creature_active_statuses_images = [[], []]

        # open images
        self.__rescaleEvent__()

        if not self.testing:
            self.gui.current_scene = self
            for p_id in (0, 1):
                self.animation_now[p_id] = self.animation_before[p_id] = self.animation_clock[p_id].tick()
            import scripts.battle as sb
            sb.Battle(self, p1, p2)

    def __cyclePrimarySprites__(self):
        # for each player
        for p_id in (0, 1):
            self.animation_now[p_id] += self.animation_clock[p_id].tick() # clock goes tick-tock

            # should you cycle? with minimal random time to spice things up
            random_time = random.randrange(100, 200)
            if self.animation_now[p_id] > self.animation_before[p_id] + random_time:

                # constraints
                if not self.creature_idle_images_reverse[p_id] and self.creature_idle_images_index[p_id] + 1 >= len(self.creature_idle_images[0]):
                    self.creature_idle_images_reverse[p_id] = True
                elif self.creature_idle_images_reverse[p_id] and self.creature_idle_images_index[p_id] -1 <= -1:
                    self.creature_idle_images_reverse[p_id] = False

                # change index
                if not self.creature_idle_images_reverse[p_id]:
                    self.creature_idle_images_index[p_id] += 1
                else:
                    self.creature_idle_images_index[p_id] -= 1

                # new time
                self.animation_now[p_id] = self.animation_before[p_id] = self.animation_clock[p_id].tick()

    # blits creatures and shows textbox over them if needed
    def __blitPrimarySprites__(self):
        # resolution scaling multiplier
        res_mp = self.gui.DISPLAY_W / 1920

        for p_id in (0, 1):
            image = self.creature_idle_images[p_id][self.creature_idle_images_index[p_id]]
            rect = image.get_rect()
            rect = rect.move((180 + 960 * p_id) * res_mp, 240 * res_mp)
            self.gui.display.blit(image, rect)

        # textbox comes second
        self.__keepTextboxText__()

    def __rescaleEvent__(self):
        print(f"rescale {self.gui.DISPLAY_W}x{self.gui.DISPLAY_H}")
        self.__updateHUDImages__()
        self.__updateCreatureImages__()
        self.__updateStatusImages__()


    def __updateSelected__(self, player_curr_moves: [int, int]) -> (int, int):

        player_chosen_moves = [-1, -1]

        # starting point for player moves
        for p in (self.p1, self.p2):
            i = p.id - 1
            if p.ai >= 0 or player_curr_moves[i] >= 0:
                player_chosen_moves[i] = player_curr_moves[i]
            elif p.ac.isStunned:
                player_chosen_moves[i] = -2
            else:
                player_chosen_moves[i] = -1

            for k in self.gui.keys.keys_down:
                if self.testing and not self.player_infobox_up[i]: # creature index controls with infobox down
                    if k == self.gui.keys.A[i]:
                        self.player_selected_creature[i] = (self.player_selected_creature[i] - 1) % len(p.creatures)
                        p.ac = p.creatures[self.player_selected_creature[i]]
                        self.__updateCreatureImages__()
                    if k == self.gui.keys.D[i]:
                        self.player_selected_creature[i] = (self.player_selected_creature[i] + 1) % len(p.creatures)
                        p.ac = p.creatures[self.player_selected_creature[i]]
                        self.__updateCreatureImages__()
                    if k == self.gui.keys.INFO[i]:
                        self.player_infobox_up[i] = True
                elif player_chosen_moves[i] == -1 and p.ai < 0 and not self.player_infobox_up[i] and not self.testing: # move choice
                    if k == self.gui.keys.INFO[i]:
                        self.player_infobox_up[i] = True
                    if k == self.gui.keys.Q[i] and p.ac.cooldowns[0] <= 0:
                        player_chosen_moves[i] = 0
                    if k == self.gui.keys.W[i] and p.ac.cooldowns[1] <= 0:
                        player_chosen_moves[i] = 1
                    if k == self.gui.keys.E[i] and p.ac.cooldowns[2] <= 0:
                        player_chosen_moves[i] = 2
                    if k == self.gui.keys.A[i] and p.ac.cooldowns[3] <= 0:
                        player_chosen_moves[i] = 3
                    if k == self.gui.keys.S[i] and p.ac.cooldowns[4] <= 0:
                        player_chosen_moves[i] = 4
                    if k == self.gui.keys.D[i] and p.ac.cooldowns[5] <= 0:
                        player_chosen_moves[i] = 5
                    if k == self.gui.keys.CONFIRM[i] and p.ac.rage >= p.ac.c.moves[6].rage_cost:
                        player_chosen_moves[i] = 6
                elif player_chosen_moves[i] == -1 and p.ai < 0 and self.player_infobox_up[i] and self.player_selected_z[i] == 1: #infobox
                    z = 1
                    if k == self.gui.keys.INFO[i]:
                        self.player_infobox_up[i] = False
                    if k == self.gui.keys.Q[i]:
                        self.player_selected_z[i] = (self.player_selected_z[i] - 1) % self.player_max_z
                    if k == self.gui.keys.W[i]:
                        self.player_selected_y[i][z] = (self.player_selected_y[i][z] - 1) % self.player_max_y[z]
                        if self.player_selected_y[i][z] == 2:
                            self.player_selected_x[i][z] *= 2
                        if self.player_selected_x[i][z] <= 2 and self.player_selected_y[i][z] == 3: # own rage
                            self.player_selected_x[i][z] = 0
                        if self.player_selected_x[i][z] > 2 and self.player_selected_y[i][z] == 3: # opponent rage
                            self.player_selected_x[i][z] = 1
                        if self.player_selected_x[i][z] >= 2 and self.player_selected_y[i][z] == 8:
                            self.player_selected_x[i][z] += 1
                        # safety checks
                        if self.player_selected_x[i][z] >= 4 and self.player_selected_y[i][z] <= 2:
                            self.player_selected_x[i][z] = 3
                        if self.player_selected_x[i][z] >= 2 and self.player_selected_y[i][z] == 3:
                            self.player_selected_x[i][z] = 1
                    if k == self.gui.keys.E[i]:
                        self.player_selected_z[i] = (self.player_selected_z[i] + 1) % self.player_max_z
                    if k == self.gui.keys.A[i]:
                        self.player_selected_x[i][z] = (self.player_selected_x[i][z] - 1) % self.player_max_x[z]
                        if self.player_selected_x[i][z] >= 4 and self.player_selected_y[i][z] <= 2:
                            self.player_selected_x[i][z] = 3
                        if self.player_selected_x[i][z] >= 2 and self.player_selected_y[i][z] == 3:
                            self.player_selected_x[i][z] = 1
                    if k == self.gui.keys.S[i]:
                        self.player_selected_y[i][z] = (self.player_selected_y[i][z] + 1) % self.player_max_y[z]
                        if self.player_selected_x[i][z] >= 2 and self.player_selected_y[i][z] == 0:
                            self.player_selected_x[i][z] -= 1
                        if self.player_selected_x[i][z] >= 4 and self.player_selected_y[i][z] == 0:
                            self.player_selected_x[i][z] -= 1
                        if self.player_selected_x[i][z] < 2 and self.player_selected_y[i][z] == 3:
                            self.player_selected_x[i][z] = 0
                        if self.player_selected_x[i][z] >= 2 and self.player_selected_y[i][z] == 3:
                            self.player_selected_x[i][z] = 1
                        if self.player_selected_y[i][z] == 4:
                            self.player_selected_x[i][z] *= 3
                        # safety checks
                        if self.player_selected_x[i][z] >= 4 and self.player_selected_y[i][z] <= 2:
                            self.player_selected_x[i][z] = 3
                        if self.player_selected_x[i][z] >= 2 and self.player_selected_y[i][z] == 3:
                            self.player_selected_x[i][z] = 1
                    if k == self.gui.keys.D[i]:
                        self.player_selected_x[i][z] = (self.player_selected_x[i][z] + 1) % self.player_max_x[z]
                        if self.player_selected_x[i][z] >= 4 and self.player_selected_y[i][z] <= 2:
                            self.player_selected_x[i][z] = 0
                        if self.player_selected_x[i][z] >= 2 and self.player_selected_y[i][z] == 3:
                            self.player_selected_x[i][z] = 0
                elif player_chosen_moves[i] == -1 and p.ai < 0 and self.player_infobox_up[i] and self.player_selected_z[i] == 0: # typebox
                    z = 0
                    if k == self.gui.keys.INFO[i]:
                        self.player_infobox_up[i] = False
                    if k == self.gui.keys.Q[i]:
                        self.player_selected_z[i] = (self.player_selected_z[i] - 1) % self.player_max_z
                    if k == self.gui.keys.E[i]:
                        self.player_selected_z[i] = (self.player_selected_z[i] + 1) % self.player_max_z
                    if k == self.gui.keys.A[i]:
                        self.player_selected_x[i][z] = (self.player_selected_x[i][z] - 1) % self.player_max_x[z]
                    if k == self.gui.keys.D[i]:
                        self.player_selected_x[i][z] = (self.player_selected_x[i][z] + 1) % self.player_max_x[z]
                elif player_chosen_moves[i] == -1 and p.ai < 0 and self.player_infobox_up[i] and self.player_selected_z[i] == 2: # creaturebox
                    if k == self.gui.keys.INFO[i]:
                        self.player_infobox_up[i] = False
                    if k == self.gui.keys.Q[i]:
                        self.player_selected_z[i] = (self.player_selected_z[i] - 1) % self.player_max_z
                    if k == self.gui.keys.E[i]:
                        self.player_selected_z[i] = (self.player_selected_z[i] + 1) % self.player_max_z

        return player_chosen_moves


    def __displayScene__(self):
        # while running, battle.py will do the work, battle scene will be waiting at this point
        # while testing, run hud and check for inputs
        if self.testing:
            self.background_color = self.gui.colors.BLUEISH_GRAY
            self.p1.ai = self.p2.ai = -1
            self.p1.creatures.clear()
            self.p2.creatures.clear()
            creatures = []

            c: cr.Creature
            for c in cr.all_creatures:
                co = cr.CreatureOccurrence(c)
                creatures.append(co)

            self.p1.creatures = self.p2.creatures = creatures
            self.p1.ac = self.p1.creatures[0]
            self.p2.ac = self.p2.creatures[0]

            self.p1.ac.__joinBattleScene__(self)
            self.p2.ac.__joinBattleScene__(self)

            self.__updateCreatureImages__()

            while self.testing:
                self.__updateSelected__((-1, -1))
                self.gui.display.fill(self.background_color)
                self.__blitHealth__()
                self.__blitModifiers__()
                self.__cyclePrimarySprites__()
                self.__blitHUD__()
                self.gui.__blitScreen__()
                if self.gui.return_to_menu:
                    self.testing = False

        # after it's done, go back to main menu
        self.run_display = False
        self.gui.main_menu.run_display = True
        self.gui.current_scene = self.gui.main_menu

    def __updateHUDImages__(self):
        res_mp = self.gui.DISPLAY_W / 1920

        # clears
        self.textbox_images.clear()
        self.player_hud_images.clear()
        self.player_infobox_images.clear()
        self.player_typebox_images.clear()
        self.player_creaturebox_images.clear()
        self.selected_images.clear()

        # get animated textbox
        textbox_sprite_path = os.path.join(self.dirname, f'../assets/art/interface/textbox_battle_sprite.png')
        textbox_sprite_sheet = ss.SpriteSheet(textbox_sprite_path)
        textbox_sprite_name = 'textbox_battle'
        for i in range(1, 11):
            image = textbox_sprite_sheet.parse_sprite(f'{textbox_sprite_name}{i}')
            image = pygame.transform.scale(image, (1460 * res_mp, 140 * res_mp))
            self.textbox_images.append(image)

        # get hud
        hud_path = os.path.join(self.dirname, f'../assets/art/interface/hud.png')
        image = pygame.image.load(hud_path)
        image = pygame.transform.scale(image, (self.gui.DISPLAY_W, self.gui.DISPLAY_H))
        self.player_hud_images.append(image)

        for p_id in (1, 2):
            # get infoboxes
            infobox_path = os.path.join(self.dirname, f'../assets/art/interface/p{p_id}_infobox.png')
            image = pygame.image.load(infobox_path)
            image = pygame.transform.scale(image, (self.gui.DISPLAY_W, self.gui.DISPLAY_H))
            self.player_infobox_images.append(image)

            # get typeboxes
            typebox_path = os.path.join(self.dirname, f'../assets/art/interface/p{p_id}_typebox.png')
            image = pygame.image.load(typebox_path)
            image = pygame.transform.scale(image, (self.gui.DISPLAY_W, self.gui.DISPLAY_H))
            self.player_typebox_images.append(image)

            # get creatureboxes
            creaturebox_path = os.path.join(self.dirname, f'../assets/art/interface/p{p_id}_creaturebox.png')
            image = pygame.image.load(creaturebox_path)
            image = pygame.transform.scale(image, (self.gui.DISPLAY_W, self.gui.DISPLAY_H))
            self.player_creaturebox_images.append(image)

        # get infobox selected ability and status
        selected_path = os.path.join(self.dirname, f'../assets/art/interface/selected_ability.png')
        image = pygame.image.load(selected_path)
        image = pygame.transform.scale(image, (85 * res_mp, 46 * res_mp))
        self.selected_images.append(image)
        selected_path = os.path.join(self.dirname, f'../assets/art/interface/selected_status.png')
        image = pygame.image.load(selected_path)
        image = pygame.transform.scale(image, (65 * res_mp, 26 * res_mp))
        self.selected_images.append(image)

    def __updateStatusImages__(self):
        res_mp = self.gui.DISPLAY_W / 1920

        for p in (self.p1, self.p2):
            i = p.id - 1
            self.creature_active_statuses_images[i].clear()

            for so in p.ac.active_statuses:
                path = os.path.join(self.dirname, f'../assets/art/interface/statuses/{so.se.name}.png')
                image = pygame.image.load(path)
                image = pygame.transform.scale(image, (54 * res_mp, 15 * res_mp))
                self.creature_active_statuses_images[i].append(image)

    def __updateCreatureImages__(self):
        res_mp = self.gui.DISPLAY_W / 1920

        # creature specific - do one player after another
        for p in (self.p1, self.p2):
            i = p.id - 1
            self.creature_idle_images[i].clear()
            self.creature_abilities_images[i].clear()
            self.creature_abilities_mini_images[i].clear()

            # creatures
            creature_idle_path = os.path.join(self.dirname, f'../assets/art/creatures/{p.ac.c.name}/{p.ac.c.name}_idle_sprite.png')
            creature_idle_sprite_sheet = ss.SpriteSheet(creature_idle_path)
            sprite_name = 'idle_'
            for j in range(0, 5):
                image = creature_idle_sprite_sheet.parse_sprite(f'{sprite_name}{j + 1}')
                image = pygame.transform.scale(image, (600 * res_mp, 600 * res_mp))
                if i == 0: # flip the image for player 1
                    image = pygame.transform.flip(image, True, False)
                self.creature_idle_images[i].append(image)

            for j in range(0, 5):
                path = os.path.join(self.dirname, f'../assets/art/interface/abilities/{p.ac.c.name}/{j}.png')
                image = pygame.image.load(path)
                image = pygame.transform.scale(image, (138 * res_mp, 64 * res_mp))
                self.creature_abilities_images[i].append(image)
                image = pygame.transform.scale(image, (69 * res_mp, 32 * res_mp))
                self.creature_abilities_mini_images[i].append(image)

        # universal - don't open the same images twice!
        # info
        path = os.path.join(self.dirname, f'../assets/art/interface/abilities/universal/5.png')
        image = pygame.image.load(path)
        image = pygame.transform.scale(image, (138 * res_mp, 64 * res_mp))
        self.creature_abilities_images[0].append(image)
        self.creature_abilities_images[1].append(image)
        image = pygame.transform.scale(image, (69 * res_mp, 32 * res_mp))
        self.creature_abilities_mini_images[i].append(image)
        self.creature_abilities_mini_images[0].append(image)
        self.creature_abilities_mini_images[1].append(image)

        # ?
        path = os.path.join(self.dirname, f'../assets/art/interface/abilities/universal/6.png')
        image = pygame.image.load(path)
        image = pygame.transform.scale(image, (71 * res_mp, 64 * res_mp))
        self.creature_abilities_images[0].append(image)
        self.creature_abilities_images[1].append(image)

    def __blitInfoboxImages__(self, player: pl.Player):
        res_mp = self.gui.DISPLAY_W / 1920

        p_id = player.id - 1
        o_id = player.id % 2

        if p_id == 0:
            opponent = self.p2
        else:
            opponent = self.p1

        if self.player_infobox_up[p_id]:
            for ability in range(0, 6):
                # player moves
                x = ability % 2
                y = math.floor(ability / 2)
                move = self.creature_abilities_mini_images[p_id][ability]
                rect = move.get_rect()
                rect = rect.move(((57 + 103 * x + 1408 * p_id) * res_mp, (342 + 50 * y) * res_mp))
                self.gui.display.blit(move, rect)

                # opponent moves
                x = (ability % 2) + 2
                move = self.creature_abilities_mini_images[o_id][ability]
                rect = move.get_rect()
                rect = rect.move(((79 + 103 * x + 1408 * p_id) * res_mp, (342 + 50 * y) * res_mp))
                self.gui.display.blit(move, rect)

            # statuses
            for p in (player, opponent):
                i = 0
                player_index = p.id - 1
                if p == player:
                    base_x = 46
                else:
                    base_x = 274

                for status_image in self.creature_active_statuses_images[player_index]:
                    x = i % 3
                    y = math.floor(i / 3)
                    status = status_image
                    rect = status.get_rect()
                    rect = rect.move(((base_x + 71 * x + 1408 * p_id) * res_mp, (555 + 28 * y) * res_mp))
                    self.gui.display.blit(status, rect)
                    i += 1
                    if i >= 15: # if someone's somehow got more than 15 active effects, don't draw them
                        break

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
            if self.gui.return_to_menu or self.gui.skip_animations:
                return

            self.gui.display.fill(self.background_color)
            self.__blitHealth__()
            self.__blitHUD__()
            self.gui.__delay__(10)

            textbox = self.textbox_images[i]
            rect = self.textbox_images[i].get_rect()
            rect = rect.move((230 * res_mp, 679 * res_mp))
            self.gui.display.blit(textbox, rect)
            self.gui.__blitScreen__()
            i = y(i)

        if not zoom_in:
            self.gui.__delay__(10)
            self.gui.display.fill(self.background_color)
            self.__blitHealth__()
            self.__blitHUD__()
            self.gui.__blitScreen__()
        else:
            self.textbox_up = True

        self.gui.__delay__(100)

    def __blitTextbox__(self):
        res_mp = self.gui.DISPLAY_W / 1920
        textbox = self.textbox_images[9]
        rect = self.textbox_images[9].get_rect()
        rect = rect.move((230 * res_mp, 679 * res_mp))
        self.gui.display.blit(textbox, rect)

    def __animateBattleText__(self, line1: str, line2: str = None):
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
            if self.gui.return_to_menu or self.gui.skip_animations:
                return
            message += c
            self.gui.display.fill(self.background_color)
            self.__blitHealth__()
            self.__blitTextbox__()
            self.__blitHUD__()
            self.gui.__blitText__(message, font_size, 960, y, self.gui.colors.BLACK)
            self.gui.__blitScreen__()
            if c == '!' or c == '?':
                self.gui.__delay__(500)  # 500ms delay with ! or ?
            elif c == '.':
                self.gui.__delay__(200)  # 200ms delay with .
            else:
               self.gui.__delay__(15)  # 15ms delay with letter
        self.last_battle_text[0] = message

        if line2 is not None:
            self.last_battle_text[1] = ""
            message = ""
            for c in line2:
                if self.gui.return_to_menu or self.gui.skip_animations:
                    return
                message += c
                self.gui.display.fill(self.background_color)
                self.__blitHealth__()
                self.__blitTextbox__()
                self.__blitHUD__()
                #self.__keepTextboxText__()
                self.gui.__blitText__(message, font_size, 960, y + 60, self.gui.colors.BLACK)
                self.gui.__blitScreen__()
                if c == '!' or c == '?':
                    self.gui.__delay__(500)  # 500ms delay with ! or ?
                elif c == '.':
                    self.gui.__delay__(200)  # 200ms delay with .
                else:
                    self.gui.__delay__(15)  # 15 delay with letter
            self.last_battle_text[1] = message

        # 500ms delay at the end of the message
        self.gui.__delay__(500)

    def __blitHealth__(self):
        # resolution scaling multiplier
        res_mp = self.gui.DISPLAY_W / 1920

        # health
        health_bar_width = 906 * self.p1.ac.health / self.p1.ac.c.health
        if health_bar_width < 0:
            health_bar_width = 0
        health_rect = pygame.Rect((res_mp * 28, res_mp * 138, res_mp * health_bar_width, res_mp * 28))
        self.gui.display.fill(self.health_color, health_rect)

        health_text = f"-- {self.p1.ac.health}/{self.p1.ac.c.health} --"
        self.gui.__blitText__(health_text, 45, 481, 210, self.gui.colors.WHITE)

        health_bar_width = 906 * self.p2.ac.health / self.p2.ac.c.health
        if health_bar_width < 0:
            health_bar_width = 0
        health_rect = pygame.Rect((res_mp * 987, res_mp * 138, res_mp * health_bar_width, res_mp * 28))
        self.gui.display.fill(self.health_color, health_rect)

        health_text = f"-- {self.p2.ac.health}/{self.p2.ac.c.health} --"
        self.gui.__blitText__(health_text, 45, 1440, 210, self.gui.colors.WHITE)

    def __animateHealth__(self, ac: cr.CreatureOccurrence, prev_health: int):
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
            if self.gui.return_to_menu or self.gui.skip_animations:
                return

            # update health by 1 point
            prev_health = update_health(prev_health)

            # redraw background
            self.gui.display.fill(self.background_color)

            # update health on gui by 1 point
            health_bar_width = 906 * prev_health / ac.c.health
            if health_bar_width < 0:
                health_bar_width = 0
            health_rect = pygame.Rect((res_mp * hbar_x, res_mp * 138, res_mp * health_bar_width, res_mp * 28))
            self.gui.display.fill(self.health_color, health_rect)
            health_text = f"-- {prev_health}/{ac.c.health} --"
            self.gui.__blitText__(health_text, 45, htext_x, 210, self.gui.colors.WHITE)

            # draw health of opponent
            health_bar_width = 906 * op.health / op.c.health
            if health_bar_width < 0:
                health_bar_width = 0
            health_rect = pygame.Rect((res_mp * hbar2_x, res_mp * 138, res_mp * health_bar_width, res_mp * 28))
            self.gui.display.fill(self.health_color, health_rect)
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
                color = self.gui.colors.GREENING_WHITE
            else:
                color = self.gui.colors.BLEEDING_WHITE

            self.gui.__blitText__(f"{ac.c.name}", 80, name_x, 65, color)

            # blit screen
            self.gui.__blitScreen__()
            self.gui.__delay__(15)

        self.gui.__delay__(500)

    def __keepTextboxText__(self):
        # textbox
        if self.textbox_up is True:
            self.__blitTextbox__()
            if self.last_battle_text[1] is None and self.last_battle_text[0] is not None:
                self.gui.__blitText__(self.last_battle_text[0], 50, 960, 750, self.gui.colors.BLACK)
            elif self.last_battle_text[1] is not None and self.last_battle_text[0] is not None:
                self.gui.__blitText__(self.last_battle_text[0], 45, 960, 720, self.gui.colors.BLACK)
                self.gui.__blitText__(self.last_battle_text[1], 45, 960, 780, self.gui.colors.BLACK)

    def __blitMove__(self, p: pl.Player, opponent: pl.Player):
        # resolution scaling multiplier
        res_mp = self.gui.DISPLAY_W / 1920

        i = p.id - 1
        z = self.player_selected_z[i]
        y = self.player_selected_y[i][z]
        x = self.player_selected_x[i][z]

        x_mod2 = 493 * i

        self.gui.__blitText__("SELECTED MOVE:", 20, 713 + x_mod2, 300, self.gui.colors.RED)

        if y == 3 and x == 0: # own rage
            move_index = 6
            move = p.ac.c.moves[move_index]
            base_x = 49
        elif y == 3 and x == 1: # enemy rage
            move_index = 6
            move = opponent.ac.c.moves[move_index]
            base_x = 71
        elif x <= 1:  # own ability
            move_index = y * 2 + x
            move = p.ac.c.moves[move_index]
            base_x = 49
        else:
            move_index = y * 2 + x - 2
            move = opponent.ac.c.moves[move_index]
            base_x = 71

        if y != 3:
            selected = self.selected_images[0]
            rect = selected.get_rect()
            rect = rect.move(((base_x + 103 * x + 1408 * i) * res_mp, (335 + 50 * y) * res_mp))
            self.gui.display.blit(selected, rect)

        # blit move
        self.gui.__blitText__(f"{move.name}", 20, 713 + x_mod2, 320, self.gui.colors.RED)
        self.gui.__blitText__(f"SPEED: {move.speed}", 20, 713 + x_mod2, 360, self.gui.colors.BLACK)
        if move.target_self:
            target_self_text = "YES"
        else:
            target_self_text = "NO"
        self.gui.__blitText__(f"TARGET SELF: {target_self_text}", 20, 713 + x_mod2, 380,
                              self.gui.colors.BLACK)
        self.gui.__blitText__(f"DAMAGE: {move.damage_low} TO {move.damage_high}", 20, 713 + x_mod2, 400,
                              self.gui.colors.BLACK)
        self.gui.__blitText__(f"HIT CHANCE: {move.aim}", 20, 713 + x_mod2, 420, self.gui.colors.BLACK)
        self.gui.__blitText__(f"HIT ATTEMPTS: {move.hit_attempts}", 20, 713 + x_mod2, 440,
                              self.gui.colors.BLACK)
        self.gui.__blitText__(f"STATUS CHANCE: {move.status_chance}", 20, 713 + x_mod2, 460,
                              self.gui.colors.BLACK)
        if move.rage_cost == 0:
            self.gui.__blitText__(f"COOLDOWN: {move.cooldown}", 20, 713 + x_mod2, 480, self.gui.colors.BLACK)
            self.gui.__blitText__(f"TYPE: {move.type.name}", 20, 713 + x_mod2, 540, self.gui.colors.BLACK)
        else:
            self.gui.__blitText__(f"RAGE COST: {move.rage_cost}", 20, 713 + x_mod2, 480, self.gui.colors.BLACK)
            self.gui.__blitText__(f"CURRENT RAGE: ({p.ac.rage}/{p.ac.c.rage})", 20, 713 + x_mod2, 500, self.gui.colors.BLACK)
            self.gui.__blitText__(f"TYPE: {move.type.name}", 20, 713 + x_mod2, 530, self.gui.colors.BLACK)

        if move.status_effect is not None:  # blit status if there is one
            se = move.status_effect
            self.gui.__blitText__("SELECTED MOVE'S STATUS EFFECT:", 20, 713 + x_mod2, 583,
                                  self.gui.colors.RED)
            self.gui.__blitText__(f"{move.status_effect.name}", 20, 713 + x_mod2, 603,
                                  self.gui.colors.RED)
            self.gui.__blitText__(f"DAMAGE PER TURN: {se.damage_low} TO {se.damage_high}", 20, 713 + x_mod2,
                                  643, self.gui.colors.BLACK)
            self.gui.__blitText__(f"THORN DAMAGE: {se.thorn_damage_low} TO {se.thorn_damage_high}", 20,
                                  713 + x_mod2, 663, self.gui.colors.BLACK)
            self.gui.__blitText__(f"AIM MODIFIER: {se.aim_mod}", 20, 713 + x_mod2, 683,
                                  self.gui.colors.BLACK)
            self.gui.__blitText__(f"DEFENSE MODIFIER: {se.defense_mod}", 20, 713 + x_mod2, 703,
                                  self.gui.colors.BLACK)
            self.gui.__blitText__(f"DAMAGE MODIFIER: {se.damage_mod}", 20, 713 + x_mod2, 723,
                                  self.gui.colors.BLACK)
            if se.damage_mod_type is not None:
                self.gui.__blitText__(f"DAMAGE MOD TYPE: {se.damage_mod_type.name}", 20, 713 + x_mod2, 743,
                                      self.gui.colors.BLACK)
            elif se.damage_mod != 0:
                self.gui.__blitText__(f"DAMAGE MOD TYPE: ALL TYPES", 20, 713 + x_mod2, 743,
                                      self.gui.colors.BLACK)
            else:
                self.gui.__blitText__(f"DAMAGE MOD TYPE: NONE", 20, 713 + x_mod2, 743,
                                      self.gui.colors.BLACK)
            self.gui.__blitText__(f"STATUS DURATION: {se.status_duration} TURN(S)", 20, 713 + x_mod2, 763,
                                  self.gui.colors.BLACK)
            if se.stun_duration <= -1:
                self.gui.__blitText__(f"STUN DURATION: NO STUN", 20, 713 + x_mod2, 783,
                                      self.gui.colors.BLACK)
            elif se.stun_duration == 0:
                self.gui.__blitText__(f"STUN DURATION: CASTING TURN", 20, 713 + x_mod2, 783,
                                      self.gui.colors.BLACK)
            else:
                self.gui.__blitText__(f"STUN DURATION: {se.stun_duration} TURN(S)", 20, 713 + x_mod2, 783,
                                      self.gui.colors.BLACK)
            self.gui.__blitText__(f"TYPE: {se.type.name}", 20, 713 + x_mod2, 823, self.gui.colors.BLACK)
        else:  # blit empty status
            self.gui.__blitText__("--------", 20, 713 + x_mod2, 583, self.gui.colors.RED)

    def __blitHUD__(self):
        # make sure the hud doesn't blit too fast in lower resolutions
        now = before = self.hud_clock.tick()

        # resolution scaling multiplier
        res_mp = self.gui.DISPLAY_W / 1920

        # creatures come first, then textbox with it
        self.__blitPrimarySprites__()

        # abilities black background
        if not self.testing:
            for i in (0, 1):
                p_ability_background = pygame.Rect((res_mp * (34 + 948 * i), res_mp * 860, res_mp * 904, res_mp * 180))
                self.gui.display.fill(self.gui.colors.BLACK, p_ability_background)

        # abilities
        for p_id in (0, 1):  # for players
            if not self.testing:
                for i in range(0, 6):  # for abilities

                    # get coordinate modifiers
                    if i > 2:
                        j = 1
                        k = i - 3
                    else:
                        j = 0
                        k = i

                    # get base x coordinate
                    if p_id == 0:
                        base_x = 147
                    else:
                        base_x = 1155

                    # get image
                    ability = self.creature_abilities_images[p_id][i]

                    # blit ability
                    rect = ability.get_rect()
                    rect = rect.move(((base_x + 242 * k) * res_mp, (875 + 90 * j) * res_mp))
                    self.gui.display.blit(ability, rect)
            ability = self.creature_abilities_images[p_id][6]
            rect = ability.get_rect()
            rect = rect.move(((813 + 227 * p_id) * res_mp, 965 * res_mp))
            self.gui.display.blit(ability, rect)

        # hud
        for hud_image in self.player_hud_images:
            hud = hud_image
            rect = hud.get_rect()
            rect = rect.move((0, 0))
            self.gui.display.blit(hud, rect)

        # if testing, blit a white box over abilities' spots
        if self.testing:
            for i in (0, 1):
                p_ability_background = pygame.Rect((res_mp * (34 + 1092 * i), res_mp * 864, res_mp * 750, res_mp * 172))
                self.gui.display.fill(self.gui.colors.WHITE, p_ability_background)

            # new tooltips
            for p_id in (0, 1):  # for players
                if p_id == 0:
                    p = self.p1
                else:
                    p = self.p2
                self.gui.__blitText__(f"CHANGE CREATURE", 50, 456 + 1008 * p_id, 950, self.gui.colors.BLACK)
                if not self.player_infobox_up[p_id]:
                    self.gui.__blitText__(
                        f"{p.creatures[(self.player_selected_creature[p_id] - 1) % len(p.creatures)].c.name} << {self.player_button_tips[p_id][3]}       "
                        f"{self.player_button_tips[p_id][5]} >> {p.creatures[(self.player_selected_creature[p_id] + 1) % len(p.creatures)].c.name}",
                        30,
                        456 + 1008 * p_id, 1000, self.gui.colors.BLACK)

        # infobox black background, infobox images, infobox itself, \
        # infobox text, infobox selected text and infobox selected ability/status window
        for p in (self.p1, self.p2):

            i = p.id - 1
            if i == 0:
                opponent = self.p2
            else:
                opponent = self.p1

            z = self.player_selected_z[i]
            x = self.player_selected_x[i][z]
            y = self.player_selected_y[i][z]

            if self.player_infobox_up[i] and z == 1:

                # blit infobox black background
                p_infobox_background = pygame.Rect((res_mp * (33 + 949 * i), res_mp * 282, res_mp * 905, res_mp * 568))
                self.gui.display.fill(self.gui.colors.BLACK, p_infobox_background)

                # blit images of abilities and statuses
                self.__blitInfoboxImages__(p)

                # blit infobox
                infobox = self.player_infobox_images[i]
                rect = infobox.get_rect()
                rect = rect.move((0, 0))
                self.gui.display.blit(infobox, rect)

                # non-changeable text
                x_mod = 1407 * i
                x_mod2 = 493 * i
                self.gui.__blitText__("PLAYER", 20, 142 + x_mod, 300, self.gui.colors.RED)
                self.gui.__blitText__("MOVES", 20, 142 + x_mod, 320, self.gui.colors.RED)
                self.gui.__blitText__("OPPONENT", 20, 370 + x_mod, 300, self.gui.colors.RED)
                self.gui.__blitText__("MOVES", 20, 370 + x_mod, 320, self.gui.colors.RED)

                if x == 0 and y == 3:
                    self.gui.__blitText__("RAGE ABILITY", 18, 142 + x_mod, 503, self.gui.colors.CYAN)
                else:
                    self.gui.__blitText__("RAGE ABILITY", 16, 142 + x_mod, 504, self.gui.colors.GRAY)

                if x == 1 and y == 3:
                    self.gui.__blitText__("RAGE ABILITY", 18, 370 + x_mod, 503, self.gui.colors.CYAN)
                else:
                    self.gui.__blitText__("RAGE ABILITY", 16, 370 + x_mod, 504, self.gui.colors.GRAY)


                self.gui.__blitText__("ACTIVE EFFECTS", 20, 142 + x_mod, 535, self.gui.colors.RED)
                self.gui.__blitText__("ACTIVE EFFECTS", 20, 370 + x_mod, 535, self.gui.colors.RED)

                if y <= 3:  # selected ability
                    self.__blitMove__(p, opponent)

                elif y >= 4:  # selected status or empty

                    if x <= 2:  # own status
                        status_index = (y - 4) * 3 + x
                        base_x = 40
                        if status_index < len(p.ac.active_statuses):
                            so = p.ac.active_statuses[status_index]
                        else:
                            so = None
                    else:
                        status_index = (y - 4) * 3 + x - 3
                        base_x = 55
                        if status_index < len(opponent.ac.active_statuses):
                            so = opponent.ac.active_statuses[status_index]
                        else:
                            so = None

                    selected = self.selected_images[1]
                    rect = selected.get_rect()
                    rect = rect.move(((base_x + 71 * x + 1408 * i) * res_mp, (437 + 28 * y) * res_mp))
                    self.gui.display.blit(selected, rect)

                    if so is None:
                        self.gui.__blitText__("--------", 20, 713 + x_mod2, 583, self.gui.colors.RED)
                    else:
                        self.gui.__blitText__("SELECTED STATUS OCCURRENCE:", 20, 713 + x_mod2, 583,
                                              self.gui.colors.RED)
                        self.gui.__blitText__(f"{so.se.name}", 20, 713 + x_mod2, 603, self.gui.colors.RED)
                        self.gui.__blitText__(f"DAMAGE PER TURN: {so.se.damage_low} TO {so.se.damage_high}", 20,
                                              713 + x_mod2,
                                              643, self.gui.colors.BLACK)
                        self.gui.__blitText__(f"THORN DAMAGE: {so.se.thorn_damage_low} TO {so.se.thorn_damage_high}",
                                              20,
                                              713 + x_mod2, 663, self.gui.colors.BLACK)
                        self.gui.__blitText__(f"AIM MODIFIER: {so.se.aim_mod}", 20, 713 + x_mod2, 683,
                                              self.gui.colors.BLACK)
                        self.gui.__blitText__(f"DEFENSE MODIFIER: {so.se.defense_mod}", 20, 713 + x_mod2, 703,
                                              self.gui.colors.BLACK)
                        self.gui.__blitText__(f"DAMAGE MODIFIER: {so.se.damage_mod}", 20, 713 + x_mod2, 723,
                                              self.gui.colors.BLACK)
                        if so.se.damage_mod_type is not None:
                            self.gui.__blitText__(f"DAMAGE MOD TYPE: {so.se.damage_mod_type.name}", 20, 713 + x_mod2,
                                                  743,
                                                  self.gui.colors.BLACK)
                        elif so.se.damage_mod != 0:
                            self.gui.__blitText__(f"DAMAGE MOD TYPE: ALL TYPES", 20, 713 + x_mod2, 743,
                                                  self.gui.colors.BLACK)
                        else:
                            self.gui.__blitText__(f"DAMAGE MOD TYPE: NONE", 20, 713 + x_mod2, 743,
                                                  self.gui.colors.BLACK)
                        if so.status_d == 0:
                            self.gui.__blitText__(f"STATUS DURATION: CURRENT TURN", 20, 713 + x_mod2, 763,
                                                  self.gui.colors.BLACK)
                        else:
                            self.gui.__blitText__(f"STATUS DURATION: {so.status_d} TURN(S)", 20, 713 + x_mod2, 763,
                                                  self.gui.colors.BLACK)
                        if so.stun_d <= -1:
                            self.gui.__blitText__(f"STUN DURATION: NO STUN", 20, 713 + x_mod2, 783,
                                                  self.gui.colors.BLACK)
                        elif so.stun_d == 0:
                            self.gui.__blitText__(f"STUN DURATION: CURRENT TURN", 20, 713 + x_mod2, 783,
                                                  self.gui.colors.BLACK)
                        else:
                            self.gui.__blitText__(f"STUN DURATION: {so.stun_d} TURN(S)", 20, 713 + x_mod2, 783,
                                                  self.gui.colors.BLACK)
                        self.gui.__blitText__(f"TYPE: {so.se.type.name}", 20, 713 + x_mod2, 823, self.gui.colors.BLACK)

            elif self.player_infobox_up[i] and z == 0: # typebox
                # blit typebox
                typebox = self.player_typebox_images[i]
                rect = typebox.get_rect()
                rect = rect.move((0, 0))
                self.gui.display.blit(typebox, rect)

                # non-changeable text
                x_mod = 1407 * i
                self.gui.__blitText__("PLAYER", 20, 142 + x_mod, 300, self.gui.colors.RED)
                self.gui.__blitText__("TYPES", 20, 142 + x_mod, 320, self.gui.colors.RED)
                y_coordinate = 350
                y_inc = 20
                for t in p.ac.c.types:
                    self.gui.__blitText__(f"{t.name}", 20, 142 + x_mod, y_coordinate, self.gui.colors.BLACK)
                    y_coordinate += y_inc

                self.gui.__blitText__("OPPONENT", 20, 370 + x_mod, 300, self.gui.colors.RED)
                self.gui.__blitText__("TYPES", 20, 370 + x_mod, 320, self.gui.colors.RED)
                y_coordinate = 350
                y_inc = 20
                for t in opponent.ac.c.types:
                    self.gui.__blitText__(f"{t.name}", 20, 370 + x_mod, y_coordinate, self.gui.colors.BLACK)
                    y_coordinate += y_inc

                self.gui.__blitText__("WEAK TO:", 20, 256 + x_mod, 536, self.gui.colors.PINK)
                self.gui.__blitText__("1.2X DAMAGE AND STATUS FROM THIS TYPE", 16, 256 + x_mod, 556, self.gui.colors.BLACK)
                self.gui.__blitText__("STRONG AGAINST:", 20, 256 + x_mod, 596, self.gui.colors.PINK)
                self.gui.__blitText__("0.8X DAMAGE AND STATUS FROM THIS TYPE", 16, 256 + x_mod, 616,
                                      self.gui.colors.BLACK)
                self.gui.__blitText__("IMMUNE AGAINST:", 20, 256 + x_mod, 656, self.gui.colors.PINK)
                self.gui.__blitText__("0.0X DAMAGE AND STATUS FROM THIS TYPE", 16, 256 + x_mod, 676,
                                      self.gui.colors.BLACK)

                # type text
                type = cr.types[self.player_selected_x[i][z]]
                x_mod2 = 493 * i

                self.gui.__blitText__(f"SELECTED TYPE: {type.name}", 20, 713 + x_mod2, 300, self.gui.colors.RED)
                self.gui.__blitText__("TYPE RELATIONSHIPS:", 20, 713 + x_mod2, 320, self.gui.colors.RED)

                x_mod2 = 493 * i
                self.gui.__blitText__(f"< {type.name} >", 40, 713 + x_mod2, 820, type.color)

                # weaknesses, resistances and immunities
                r_index = 0
                relationship_text = ["WEAK TO:", "STRONG AGAINST:", "IMMUNE AGAINST:"]
                y_coordinate = 370
                y_inc = 20
                y_inc_2 = 30
                ind = 0
                text = ""

                for relationship in (type.weaknesses, type.resistances, type.immunities):
                    if len(relationship) > 0:
                        self.gui.__blitText__(relationship_text[r_index], 20, 713 + x_mod2, y_coordinate, self.gui.colors.PINK)
                        y_coordinate += y_inc_2

                        for t in relationship:
                            text += t.name + "; "
                            ind += 1

                            if ind >= 3:
                                self.gui.__blitText__(f"{text}", 20, 713 + x_mod2, y_coordinate, self.gui.colors.BLACK)
                                y_coordinate += y_inc
                                ind = 0
                                text = ""

                        if text != "":
                            self.gui.__blitText__(f"{text}", 20, 713 + x_mod2, y_coordinate, self.gui.colors.BLACK)
                            y_coordinate += y_inc
                        ind = 0
                        text = ""
                        y_coordinate += y_inc_2 * 2
                    r_index += 1

                # is this type an extinguisher?
                self.gui.__blitText__("CAN EXTINGUISH EFFECTS?", 20, 713 + x_mod2, y_coordinate, self.gui.colors.PINK)
                y_coordinate += y_inc_2
                if type.isAnExtinguisher:
                    self.gui.__blitText__("YES, MOVES OF THIS TYPE WILL", 20, 713 + x_mod2, y_coordinate,
                                          self.gui.colors.BLACK)
                    y_coordinate += y_inc
                    self.gui.__blitText__("REMOVE SOME EFFECTS", 20, 713 + x_mod2, y_coordinate,
                                          self.gui.colors.BLACK)
                else:
                    self.gui.__blitText__("NO, MOVES OF THIS TYPE WON'T", 20, 713 + x_mod2, y_coordinate,
                                          self.gui.colors.BLACK)
                    y_coordinate += y_inc
                    self.gui.__blitText__("REMOVE ANY EFFECTS", 20, 713 + x_mod2, y_coordinate,
                                          self.gui.colors.BLACK)

            elif self.player_infobox_up[i] and z == 2: # creaturebox
                # blit creaturebox
                creaturebox = self.player_creaturebox_images[i]
                rect = creaturebox.get_rect()
                rect = rect.move((0, 0))
                self.gui.display.blit(creaturebox, rect)

                # non-changeable text
                x_mod = 1407 * i
                self.gui.__blitText__("PLAYER", 20, 142 + x_mod, 300, self.gui.colors.RED)
                self.gui.__blitText__("CREATURES", 20, 142 + x_mod, 320, self.gui.colors.RED)
                y_coordinate = 370
                y_inc = 20
                for co in p.creatures:
                    self.gui.__blitText__(f"{co.c.name}", 20, 142 + x_mod, y_coordinate, self.gui.colors.BLACK)
                    y_coordinate += y_inc
                    self.gui.__blitText__(f"({co.health}/{co.c.health})", 20, 142 + x_mod, y_coordinate, self.gui.colors.BLACK)
                    y_coordinate += 2 * y_inc

                self.gui.__blitText__("OPPONENT", 20, 370 + x_mod, 300, self.gui.colors.RED)
                self.gui.__blitText__("CREATURES", 20, 370 + x_mod, 320, self.gui.colors.RED)
                y_coordinate = 370
                y_inc = 20
                for co in opponent.creatures:
                    self.gui.__blitText__(f"{co.c.name}", 20, 370 + x_mod, y_coordinate, self.gui.colors.BLACK)
                    y_coordinate += y_inc
                    self.gui.__blitText__(f"({co.health}/{co.c.health})", 20, 370 + x_mod, y_coordinate,
                                          self.gui.colors.BLACK)
                    y_coordinate += 2 * y_inc

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
            if p.id == 1:
                x = 107
            else:
                x = 1330

            # cycle through all abilities with cooldowns
            if not self.testing:
                for i in range(0, 6):
                    if p.ac.cooldowns[i] == 0 and p.ai < 0 and not self.player_infobox_up[p.id - 1]:
                        text = self.player_button_tips[p.id - 1][i]
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

            if p.ai < 0 and not self.player_infobox_up[p.id - 1]:
                self.gui.__blitText__(self.player_button_tips[p.id - 1][6], 27, 847 + 227 * (p.id - 1), 890, self.gui.colors.BLACK)
                self.gui.__blitText__("(INFO)", 27, 847 + 227 * (p.id - 1), 921, self.gui.colors.BLACK)

            elif self.player_infobox_up[p.id - 1]:
                # w
                self.gui.__blitText__(self.player_button_tips[p.id - 1][1], 20, 323 + 1278 * (p.id - 1), 736, self.gui.colors.BLACK)
                # asd
                text_asd = self.player_button_tips[p.id - 1][3] + self.player_button_tips[p.id - 1][4] + self.player_button_tips[p.id - 1][5]
                self.gui.__blitText__(text_asd, 20, 323 + 1278 * (p.id - 1), 759, self.gui.colors.BLACK)
                # tab
                self.gui.__blitText__(self.player_button_tips[p.id - 1][6], 20, 145 + 1630 * (p.id - 1), 747, self.gui.colors.BLACK)
                # qe
                self.gui.__blitText__(self.player_button_tips[p.id - 1][0], 30, 133 + 1408 * (p.id - 1), 813,
                                      self.gui.colors.BLACK)
                self.gui.__blitText__(self.player_button_tips[p.id - 1][2], 30, 382 + 1408 * (p.id - 1), 813,
                                      self.gui.colors.BLACK)

        # again, make sure it isn't so fast you can't see stuff when game is faster due to lower res
        now += self.hud_clock.tick()
        while now < before + 40 / self.gui.speed:
            now += self.hud_clock.tick()

    def __animateRoll__(self, roll: int, chance: int, for_status: bool = False):
        # only animate when chances are uncertain
        if 0 < chance < 100:

            # text 3 is just number = delay multiplier and x = terminate
            text = ["", "", "000000000000000000000000000011226699x", ""]
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
                self.gui.__delay__(200)  # 200ms delay between lines
                for c in text[i]:
                    if self.gui.return_to_menu or self.gui.skip_animations:
                        return

                    message += c
                    self.gui.display.fill(self.background_color)
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
                            self.gui.__delay__(30 * 9)
                        else:  # random number for SUSPENSE!
                            number = "-- " + str(random.randrange(0, 100)) + " --"
                            self.gui.__delay__(30 * int(c))
                        self.gui.__blitText__(number, 30, 960, 280, self.gui.colors.WHITE)

                    else:  # 5th line - draw out success message
                        self.gui.__blitText__(message, 30, 960, 340, self.gui.colors.WHITE)

                    self.gui.__blitScreen__()
                    if c == '!' or c == '?':
                        self.gui.__delay__(500)  # 500ms delay with ! or ?
                    elif c == '.':
                        self.gui.__delay__(200)  # 200ms delay with .
                    else:
                        self.gui.__delay__(15)  # 15ms delay with letter

            self.gui.__delay__(500)  # 500ms delay

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
            self.gui.__delay__(200)  # 200ms delay between lines
            for c in text[i]:
                if self.gui.return_to_menu or self.gui.skip_animations:
                    return

                message += c
                self.gui.display.fill(self.background_color)
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
                    self.gui.__delay__(500)  # 500ms delay with ! or ?
                elif c == '.':
                    self.gui.__delay__(200)  # 200ms delay with .
                else:
                    self.gui.__delay__(15)  # 15ms delay with letter

        self.gui.__delay__(500)  # 500ms delay

    def __blitReadiness__(self, p1_move_roll: int, p2_move_roll: int):
        # resolution scaling multiplier
        res_mp = self.gui.DISPLAY_W / 1920

        if not self.player_infobox_up[0]:
            p1_ready_rect = pygame.Rect((res_mp * 21, res_mp * 848, res_mp * 933, res_mp * 206))
        else:  # infobox is circled too
            p1_ready_rect = pygame.Rect((res_mp * 21, res_mp * 270, res_mp * 933, res_mp * 787))

        if not self.player_infobox_up[1]:
            p2_ready_rect = pygame.Rect((res_mp * 969, res_mp * 848, res_mp * 933, res_mp * 206))
        else:  # infobox is circled too
            p2_ready_rect = pygame.Rect((res_mp * 969, res_mp * 270, res_mp * 933, res_mp * 787))

        if 0 <= p1_move_roll <= 6:  # p1 ready
            self.gui.display.fill(self.gui.colors.GREEN, p1_ready_rect)
        elif p1_move_roll == -2:
            self.gui.display.fill(self.gui.colors.BLUE, p1_ready_rect)
        else:
            self.gui.display.fill(self.gui.colors.RED, p1_ready_rect)

        if 0 <= p2_move_roll <= 6:  # p1 ready
            self.gui.display.fill(self.gui.colors.GREEN, p2_ready_rect)
        elif p2_move_roll == -2:
            self.gui.display.fill(self.gui.colors.BLUE, p2_ready_rect)
        else:
            self.gui.display.fill(self.gui.colors.RED, p2_ready_rect)

    def __calculateModifiers__(self):  # called by tickStatuses

        # reset
        self.player_aim_mods = [0, 0]
        self.player_def_mods = [0, 0]
        self.player_thorn_lows = [0, 0]
        self.player_thorn_highs = [0, 0]

        # re-calculate
        for p in (self.p1, self.p2):
            so: cr.StatusOccurrence
            for so in p.ac.active_statuses:
                self.player_aim_mods[p.id - 1] += so.se.aim_mod
                self.player_def_mods[p.id - 1] += so.se.defense_mod
                self.player_thorn_lows[p.id - 1] += so.se.thorn_damage_low
                self.player_thorn_highs[p.id - 1] += so.se.thorn_damage_high

    def __blitModifiers__(self):
        # blit 'em!
        for p in (self.p1, self.p2):
            i = p.id - 1
            x_mod = 959
            x2_mod = 965
            self.gui.__blitText__(f"AIM BOOST: {self.player_aim_mods[i]}", 20, 191 + x_mod * i, 195,
                                  self.gui.colors.WHITE)
            self.gui.__blitText__(f"DEF BOOST: {self.player_def_mods[i]}", 20, 191 + x_mod * i, 225,
                                  self.gui.colors.WHITE)
            self.gui.__blitText__(f"THORN LOW: {self.player_thorn_lows[i]}", 20, 771 + x_mod * i, 195,
                                  self.gui.colors.WHITE)
            self.gui.__blitText__(f"THORN HIGH: {self.player_thorn_highs[i]}", 20, 771 + x_mod * i, 225,
                                  self.gui.colors.WHITE)
            self.gui.__blitText__(f"BASE DEFENSE OF {p.ac.c.defense}", 20, 477 + x2_mod * i, 250, self.gui.colors.WHITE)


    def __blitTurnCounter__(self, turn: int):
        self.gui.__blitText__(f"TURN {turn}", 25, 960, 210,
                              self.gui.colors.WHITE)

    def __blitRage__(self):
        for p in (self.p1, self.p2):
            i = p.id - 1

            if not self.player_infobox_up[i]:  # rage counter
                color = self.gui.colors.BLEEDING_WHITE # standard color for non-ready

                if p.ai < 0 and p.ac.rage >= p.ac.c.moves[6].rage_cost: # player and can use
                    color = self.gui.colors.WHITE
                    rage_info = f'PRESS "{self.player_button_tips[i][7]}" TO USE "{p.ac.c.moves[6].name}" FOR {p.ac.c.moves[6].rage_cost} RP ({p.ac.rage}/{p.ac.c.rage})'
                elif p.ac.rage >= p.ac.c.moves[6].rage_cost: # not player and can use
                    color = self.gui.colors.WHITE
                    rage_info = f'MOVE "{p.ac.c.moves[6].name}" IS READY FOR {p.ac.c.moves[6].rage_cost} RP ({p.ac.rage}/{p.ac.c.rage})'
                else: # can't use
                    rage_info = f'MOVE "{p.ac.c.moves[6].name}" REQUIRES {p.ac.c.moves[6].rage_cost} RAGE POINTS ({p.ac.rage}/{p.ac.c.rage})'

                self.gui.__blitText__(rage_info, 23, 480 + 960 * i, 819,
                                    color)