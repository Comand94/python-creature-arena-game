import math
import random

import scripts.player as pl
import scripts.creatures as cr
import scripts.gui as g

class Battle:
    def __init__(self, battle_scene: g.BattleScene, p1: pl.Player, p2: pl.Player):
        self.p1 = p1
        self.p2 = p2
        self.bs = battle_scene
        self.turn_counter = 1
        self.__startBattle__()

    def __applyAIModifier__(self, p: pl.Player):
        range_top = 5 - p.ai
        health_penalty_mult = range_top - 1
        if health_penalty_mult < 0:
            health_penalty_mult = 0
        for co in p.creatures:
            co.health -= math.ceil(0.04 * p.ac.c.health * health_penalty_mult)

        # modify ai damage for different difficulties
        if range_top > 3:
            ai_damage_mod = -1
        elif range_top > -3:
            ai_damage_mod = 0
        else:
            ai_damage_mod = 1

        # modify ai stats for different difficulties
        ai_stat_mod = 0
        if range_top > 0:
            for i in range(0, range_top):
                ai_stat_mod -= 3
        elif range_top < 0:
            for i in range(range_top, 0):
                ai_stat_mod += 3
        else:
            ai_stat_mod = 0

        # hardcore ai regen
        if range_top < -3:
            if range_top < -4:
                ai_hp_regen = 2
            else:
                ai_hp_regen = 1
        else:
            ai_hp_regen = 0

        if p.id == 1:
            cr.all_status_effects["AI MODIFIER 1"].defense_mod = cr.all_status_effects["AI MODIFIER 1"].aim_mod = ai_stat_mod
            cr.all_status_effects["AI MODIFIER 1"].damage_mod = ai_damage_mod
            cr.all_status_effects["AI MODIFIER 1"].damage_low = -ai_hp_regen
            for co in p.creatures:
                co.active_statuses.append(cr.StatusOccurrence(cr.all_status_effects["AI MODIFIER 1"]))
        else:
            cr.all_status_effects["AI MODIFIER 2"].defense_mod = cr.all_status_effects[
                "AI MODIFIER 2"].aim_mod = ai_stat_mod
            cr.all_status_effects["AI MODIFIER 2"].damage_mod = ai_damage_mod
            cr.all_status_effects["AI MODIFIER 2"].damage_low = -ai_hp_regen
            for co in p.creatures:
                co.active_statuses.append(cr.StatusOccurrence(cr.all_status_effects["AI MODIFIER 2"]))

    def __startBattle__(self):

        print("\nPlayer 1: choose your creature")
        i = 1
        c: cr.CreatureOccurrence
        for c in self.p1.creatures:
            print(f"{i}. {c.c.name}")
        self.p1.ac = self.p1.creatures[0]
        print(f"\nPlayer 1 chose {self.p1.ac.c.name}!")

        self.p1.ac.__joinBattleScene__(self.bs)

        print("\nPlayer 2: choose your creature")
        i = 1
        c: cr.CreatureOccurrence
        for c in self.p2.creatures:
            print(f"{i}. {c.c.name}")
        self.p2.ac = self.p2.creatures[0]
        print(f"\nPlayer 2 chose {self.p2.ac.c.name}!")

        self.p2.ac.__joinBattleScene__(self.bs)

        print("\nFIGHT!")

        self.bs.__updateCreatureImages__()

        self.bs.__animateTextbox__(True)
        self.bs.__animateBattleText__(f"{self.p1.ac.c.name} JOINS THE BATTLE!")
        self.bs.__animateBattleText__(f"{self.p2.ac.c.name} JOINS THE BATTLE!")
        self.bs.__animateTextbox__(False)

        p1_move_count = [0, 0, 0, 0, 0, 0, 0]
        p2_move_count = [0, 0, 0, 0, 0, 0, 0]

        # different ai stats
        for p in (self.p1, self.p2):
            if p.ai >= 0:
                self.__applyAIModifier__(p)

        while self.p1.ac.health > 0 and self.p2.ac.health > 0:

            # clear moves
            p1_move_roll, p2_assumed, p2_assumed_mode = -1, -1, ""
            p2_move_roll, p1_assumed, p1_assumed_mode = -1, -1, ""

            self.bs.gui.display.fill(self.bs.gui.colors.GRAY)
            self.bs.__blitHealth__()
            self.bs.__blitHUD__()
            self.bs.gui.__blitScreen__()
            if self.bs.gui.return_to_menu:
                return

            print()
            self.bs.active_player = 1
            self.p1.ac.__tickStatus__()
            self.bs.active_player = 2
            self.p2.ac.__tickStatus__()
            self.bs.active_player = -1
            self.p1.ac.__checkIfStunned__()
            self.p2.ac.__checkIfStunned__()
            # time.sleep(1)
            print()
            self.p1.ac.__tickCooldowns__()
            self.p2.ac.__tickCooldowns__()

            # update status images for infobox
            self.bs.__updateStatusImages__()

            self.bs.gui.__delay__(1000)

            # special colors and behaviour for stunned
            if self.p1.ac.isStunned:
                p1_move_roll = -2
            if self.p2.ac.isStunned:
                p2_move_roll = -2

            # reset creature sprite timers
            for p_id in (0, 1):
                self.bs.animation_now[p_id] = self.bs.animation_before[p_id] = self.bs.animation_clock[p_id].tick()

            delay_iterator = 0

            # pre-turn phase: get moves
            while delay_iterator < 60 or p1_move_roll == -1 or p2_move_roll == -1:
                # special delay for ai games and for after the moves are chosen in general (removed delay further down in code)
                if p1_move_roll != -1 and p2_move_roll != -1:
                    delay_iterator += 1
                    self.bs.gui.__delay__(50)

                self.bs.gui.display.fill(self.bs.gui.colors.GRAY)
                self.bs.__blitHealth__()
                self.bs.__blitModifiers__()
                self.bs.__blitTurnCounter__(self.turn_counter)
                self.bs.__blitRage__()
                self.bs.__blitReadiness__(p1_move_roll, p2_move_roll)
                self.bs.__cyclePrimarySprites__()
                self.bs.__blitHUD__()
                self.bs.gui.__blitScreen__()
                if self.bs.gui.return_to_menu:
                    return

                if p1_move_roll == -1 and self.p1.ai >= 0:
                    p1_move_roll, p2_assumed, p2_assumed_mode = self.p1.__calculateMove__(self.p2.ac)
                    print(f"{self.p1.ac.c.name} rolled {p1_move_roll}, cooldown: {self.p1.ac.cooldowns[p1_move_roll]}")

                if p2_move_roll == -1 and self.p2.ai >= 0:
                    p2_move_roll, p1_assumed, p1_assumed_mode = self.p2.__calculateMove__(self.p1.ac)
                    print(f"{self.p2.ac.c.name} rolled {p2_move_roll}, cooldown: {self.p2.ac.cooldowns[p2_move_roll]}")

                p1_move_roll, p2_move_roll = self.bs.__updateSelected__([p1_move_roll, p2_move_roll])

            print(f"\n(SOT) Player 1 health: {self.p1.ac.health}\n      Player 2 health: {self.p2.ac.health}")

            p1_move_speed = self.p1.ac.c.moves[p1_move_roll].speed
            p2_move_speed = self.p2.ac.c.moves[p2_move_roll].speed

            # move order
            if self.p2.ac.isStunned and not self.p1.ac.isStunned:
                moves_first = 1
                moves_second = 0
            elif not self.p2.ac.isStunned and self.p1.ac.isStunned:
                moves_first = 2
                moves_second = 0
            elif self.p2.ac.isStunned and self.p1.ac.isStunned:
                moves_first = 0
                moves_second = 0
            elif p2_move_speed > p1_move_speed:
                moves_first = 2
                moves_second = 1
            elif p2_move_speed < p1_move_speed:
                moves_first = 1
                moves_second = 2
            else:
                roll = random.randrange(0, 101)
                if roll <= 49:
                    moves_first = 1
                    moves_second = 2
                else:
                    moves_first = 2
                    moves_second = 1

            if not self.p1.ac.isStunned and not self.p2.ac.isStunned:
                self.bs.__animateMovePriority__(p1_move_speed, p2_move_speed, moves_first)

            if self.p1.ac.isStunned:
                self.bs.gui.__delay__(500)

                self.bs.gui.display.fill(self.bs.gui.colors.GRAY)
                self.bs.__blitHealth__()
                self.bs.__blitHUD__()
                self.bs.gui.__blitScreen__()
                if self.bs.gui.return_to_menu:
                    return

                self.bs.active_player = 1
                self.bs.__animateTextbox__(True)
                self.bs.__animateBattleText__(f"{self.p1.ac.c.name} IS STUNNED AND SKIPS THE TURN!")
                self.bs.__animateTextbox__(False)
                self.bs.active_player = -1

                print("Player 1 is stunned and skips the turn!")

            if self.p2.ac.isStunned:
                self.bs.gui.__delay__(500)

                self.bs.gui.display.fill(self.bs.gui.colors.GRAY)
                self.bs.__blitHealth__()
                self.bs.__blitHUD__()
                self.bs.gui.__blitScreen__()
                if self.bs.gui.return_to_menu:
                    return

                self.bs.active_player = 2
                self.bs.__animateTextbox__(True)
                self.bs.__animateBattleText__(f"{self.p2.ac.c.name} IS STUNNED AND SKIPS THE TURN!")
                self.bs.__animateTextbox__(False)
                self.bs.active_player = -1

                print("Player 2 is stunned and skips the turn!")

            # moves
            if moves_first == 2:
                self.bs.gui.__delay__(500)

                # mark beginning of turn
                self.bs.active_player = 2

                self.p2.ac.__makeMove__(self.p1.ac, self.p2.ac.c.moves[p2_move_roll])
                self.p2.ac.cooldowns[p2_move_roll] = self.p2.ac.c.moves[p2_move_roll].cooldown + 1
                p2_move_count[p2_move_roll] += 1

                # mark ending of turn
                self.bs.active_player = -1

                if self.p1.ai >= 0:
                    self.p1.risk_evaluation(p2_assumed, self.p2.ac.c.moves[p2_assumed].name, p2_move_roll, p2_assumed_mode)

            if moves_first == 1 or moves_second == 1:

                self.bs.gui.__delay__(500)

                # mark beginning of turn
                self.bs.active_player = 1

                self.p1.ac.__checkIfStunned__()
                if self.p1.ac.isStunned and moves_second == 1:  # could be stunned if moves second
                    print("Player 1 is stunned out of his move and skips the turn!")

                    self.bs.__animateTextbox__(True)
                    self.bs.__animateBattleText__(f"{self.p1.ac.c.name} IS STUNNED AND SKIPS THE TURN!")
                    self.bs.__animateTextbox__(False)

                    # mark ending of turn
                    self.bs.active_player = -1

                else:
                    self.p1.ac.__makeMove__(self.p2.ac, self.p1.ac.c.moves[p1_move_roll])
                    self.p1.ac.cooldowns[p1_move_roll] = self.p1.ac.c.moves[p1_move_roll].cooldown + 1
                    p1_move_count[p1_move_roll] += 1

                    # mark ending of turn
                    self.bs.active_player = -1

                    if self.p2.ai >= 0:
                        self.p2.risk_evaluation(p1_assumed, self.p1.ac.c.moves[p1_assumed].name, p1_move_roll, p1_assumed_mode)

            if moves_second == 2:

                self.bs.gui.__delay__(500)

                # mark beginning of turn
                self.bs.active_player = 2

                self.p2.ac.__checkIfStunned__()
                if self.p2.ac.isStunned:  # could be stunned if moves second
                    print("Player 2 is stunned out of his move and skips the turn!")

                    self.bs.__animateTextbox__(True)
                    self.bs.__animateBattleText__(f"{self.p2.ac.c.name} IS STUNNED AND SKIPS THE TURN!")
                    self.bs.__animateTextbox__(False)

                    # mark ending of turn
                    self.bs.active_player = -1

                else:
                    self.p2.ac.__makeMove__(self.p1.ac, self.p2.ac.c.moves[p2_move_roll])
                    self.p2.ac.cooldowns[p2_move_roll] = self.p2.ac.c.moves[p2_move_roll].cooldown + 1
                    p2_move_count[p2_move_roll] += 1

                    # mark ending of turn
                    self.bs.active_player = -1

                    if self.p1.ai >= 0:
                        self.p1.risk_evaluation(p2_assumed, self.p2.ac.c.moves[p2_assumed].name, p2_move_roll, p2_assumed_mode)

            self.bs.gui.__delay__(500)

            print(f"(EOT) Player 1 health: {self.p1.ac.health}\n      Player 2 health: {self.p2.ac.health}")

            self.bs.gui.display.fill(self.bs.gui.colors.GRAY)
            self.bs.__blitHealth__()
            self.bs.__blitHUD__()
            self.bs.gui.__blitScreen__()
            if self.bs.gui.return_to_menu:
                return

            self.bs.gui.__delay__(500)

            if self.p1.ac.health <= 0:
                self.bs.__animateTextbox__(True)
                self.bs.__animateBattleText__(f"{self.p1.ac.c.name} FAINTED!")
                if  len(self.p1.creatures) > (self.p1.ac_index + 1) is not None:
                    self.p1.ac_index += 1
                    self.p1.ac = self.p1.creatures[self.p1.ac_index]
                    self.p1.ac.__joinBattleScene__(self.bs)
                    self.bs.__updateCreatureImages__()
                    self.bs.__animateBattleText__(f"{self.p1.ac.c.name} JOINS THE BATTLE!")
                    print("switch p1")
                self.bs.__animateTextbox__(False)

            if self.p2.ac.health <= 0:
                self.bs.__animateTextbox__(True)
                self.bs.__animateBattleText__(f"{self.p2.ac.c.name} FAINTED!")
                if len(self.p2.creatures) > (self.p2.ac_index + 1) is not None:
                    self.p2.ac_index += 1
                    self.p2.ac = self.p2.creatures[self.p2.ac_index]
                    self.p2.ac.__joinBattleScene__(self.bs)
                    self.bs.__updateCreatureImages__()
                    self.bs.__animateBattleText__(f"{self.p2.ac.c.name} JOINS THE BATTLE!")
                    print("switch p2")
                self.bs.__animateTextbox__(False)

            self.turn_counter += 1

        if self.p1.ac.health <= 0 and self.p2.ac.health > 0:
            print("\nPLAYER 2 WINS!")

            self.bs.gui.display.fill(self.bs.gui.colors.GRAY)
            self.bs.__blitHealth__()
            self.bs.__blitHUD__()
            self.bs.gui.__blitScreen__()
            if self.bs.gui.return_to_menu:
                return

            self.bs.__animateTextbox__(True)
            self.bs.__animateBattleText__(f"PLAYER 2 WINS!")

        elif self.p1.ac.health > 0 and self.p2.ac.health <= 0:
            print("\nPLAYER 1 WINS!")

            self.bs.gui.display.fill(self.bs.gui.colors.GRAY)
            self.bs.__blitHealth__()
            self.bs.__blitHUD__()
            self.bs.gui.__blitScreen__()
            if self.bs.gui.return_to_menu:
                return

            self.bs.__animateTextbox__(True)
            self.bs.__animateBattleText__(f"PLAYER 1 WINS!")

        else:
            print("\nDRAW! NO ONE WINS!")

            self.bs.gui.display.fill(self.bs.gui.colors.GRAY)
            self.bs.__blitHealth__()
            self.bs.__blitHUD__()
            self.bs.gui.__blitScreen__()
            if self.bs.gui.return_to_menu:
                return

            self.bs.__animateTextbox__(True)
            self.bs.__animateBattleText__(f"DRAW! NO ONE WINS!")

        print(f"Player 1 health: {self.p1.ac.health}\nPlayer 2 health: {self.p2.ac.health}")
        print(f"Player 1 move count & health healed: {p1_move_count} & {self.p1.ac.total_damage_healed}")
        print(f"Player 2 move count & health healed: {p2_move_count} & {self.p2.ac.total_damage_healed}")

        self.bs.gui.__delay__(5000)
