import random
import pygame

import scripts.player as pl
import scripts.creatures as sc
import scripts.gui as g


class Battle:
    def __init__(self, battle_scene: g.BattleScene, p1: pl.Player, p2: pl.Player, speed: float = 1):
        self.p1 = p1
        self.p2 = p2
        self.speed = speed
        self.bs = battle_scene
        self.__startBattle__()

    def __startBattle__(self):

        print("\nPlayer 1: choose your creature")
        i = 1
        c: sc.CreatureOccurrence
        for c in self.p1.creatures:
            print(f"{i}. {c.c.name}")
        self.p1.ac = self.p1.creatures.__getitem__(0)
        print(f"\nPlayer 1 chose {self.p1.ac.c.name}!")

        self.p1.ac.__joinBattleScene__(self.bs)

        print("\nPlayer 2: choose your creature")
        i = 1
        c: sc.CreatureOccurrence
        for c in self.p2.creatures:
            print(f"{i}. {c.c.name}")
        self.p2.ac = self.p2.creatures.__getitem__(1)
        print(f"\nPlayer 2 chose {self.p2.ac.c.name}!")

        self.p2.ac.__joinBattleScene__(self.bs)

        print("\nFIGHT!")

        self.bs.__changeHUD__()

        p1_move_count = [0, 0, 0, 0, 0, 0]
        p2_move_count = [0, 0, 0, 0, 0, 0]

        while self.p1.ac.health > 0 and self.p2.ac.health > 0:

            self.bs.gui.display.fill(self.bs.gui.colors.GRAY)
            self.bs.__blitHealth__()
            self.bs.__blitHUD__()
            self.bs.gui.__blitScreen__()

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

            g.__delay__(1000 / self.speed)

            # roll the moves for testing
            if not self.p1.ac.isStunned:
                p1_move_roll, p2_assumed, p2_assumed_mode = self.p1.__calculateMove__(self.p2.ac)
            else:
                p1_move_roll, p2_assumed, p2_assumed_mode = -1, -1, ""
            if not self.p2.ac.isStunned:
                p2_move_roll, p1_assumed, p1_assumed_mode = self.p2.__calculateMove__(self.p1.ac)
            else:
                p2_move_roll, p1_assumed, p1_assumed_mode = -1, -1, ""
            print(f"{self.p1.ac.c.name} rolled {p1_move_roll}, cooldown: {self.p1.ac.cooldowns[p1_move_roll]}")
            print(f"{self.p2.ac.c.name} rolled {p2_move_roll}, cooldown: {self.p2.ac.cooldowns[p2_move_roll]}")

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
                roll = random.randrange(0, 100)
                if roll <= 49:
                    moves_first = 1
                    moves_second = 2
                else:
                    moves_first = 2
                    moves_second = 1

            if not self.p1.ac.isStunned and not self.p2.ac.isStunned:
                self.bs.__animateMovePriority__(p1_move_speed, p2_move_speed, moves_first)

            if self.p1.ac.isStunned:
                g.__delay__(1000 / self.speed)

                self.bs.gui.display.fill(self.bs.gui.colors.GRAY)
                self.bs.__blitHealth__()
                self.bs.__blitHUD__()
                self.bs.gui.__blitScreen__()

                self.bs.__animateTextbox__(True)
                self.bs.__blitBattleText__(f"{self.p1.ac.c.name} IS STUNNED AND SKIPS THE TURN!")
                self.bs.__animateTextbox__(False)

                print("Player 1 is stunned and skips the turn!")

            if self.p2.ac.isStunned:
                g.__delay__(1000 / self.speed)

                self.bs.gui.display.fill(self.bs.gui.colors.GRAY)
                self.bs.__blitHealth__()
                self.bs.__blitHUD__()
                self.bs.gui.__blitScreen__()

                self.bs.__animateTextbox__(True)
                self.bs.__blitBattleText__(f"{self.p2.ac.c.name} IS STUNNED AND SKIPS THE TURN!")
                self.bs.__animateTextbox__(False)

                print("Player 2 is stunned and skips the turn!")

            # moves
            if moves_first == 2:
                g.__delay__(1000 / self.speed)

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

                g.__delay__(1000 / self.speed)

                # mark beginning of turn
                self.bs.active_player = 1

                self.p1.ac.__checkIfStunned__()
                if self.p1.ac.isStunned:  # could be stunned if moves second
                    print("Player 1 is stunned out of his move and skips the turn!")

                    self.bs.__animateTextbox__(True)
                    self.bs.__blitBattleText__(f"{self.p1.ac.c.name} IS STUNNED AND SKIPS THE TURN!")
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

                g.__delay__(1000 / self.speed)

                # mark beginning of turn
                self.bs.active_player = 2

                self.p2.ac.__checkIfStunned__()
                if self.p2.ac.isStunned:  # could be stunned if moves second
                    print("Player 2 is stunned out of his move and skips the turn!")

                    self.bs.__animateTextbox__(True)
                    self.bs.__blitBattleText__(f"{self.p2.ac.c.name} IS STUNNED AND SKIPS THE TURN!")
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

            g.__delay__(1000 / self.speed)

            print(f"(EOT) Player 1 health: {self.p1.ac.health}\n      Player 2 health: {self.p2.ac.health}")

            self.bs.gui.display.fill(self.bs.gui.colors.GRAY)
            self.bs.__blitHealth__()
            self.bs.__blitHUD__()
            self.bs.gui.__blitScreen__()

            g.__delay__(1000 / self.speed)

        if self.p1.ac.health <= 0 and self.p2.ac.health > 0:
            print("\nPLAYER 2 WINS!")

            self.bs.gui.display.fill(self.bs.gui.colors.GRAY)
            self.bs.__blitHealth__()
            self.bs.__blitHUD__()
            self.bs.gui.__blitScreen__()

            self.bs.__animateTextbox__(True)
            self.bs.__blitBattleText__(f"{self.p2.ac.c.name} WINS!")

        elif self.p1.ac.health > 0 and self.p2.ac.health <= 0:
            print("\nPLAYER 1 WINS!")

            self.bs.gui.display.fill(self.bs.gui.colors.GRAY)
            self.bs.__blitHealth__()
            self.bs.__blitHUD__()
            self.bs.gui.__blitScreen__()

            self.bs.__animateTextbox__(True)
            self.bs.__blitBattleText__(f"{self.p1.ac.c.name} WINS!")

        else:
            print("\nDRAW! NO ONE WINS!")

            self.bs.gui.display.fill(self.bs.gui.colors.GRAY)
            self.bs.__blitHealth__()
            self.bs.__blitHUD__()
            self.bs.gui.__blitScreen__()

            self.bs.__animateTextbox__(True)
            self.bs.__blitBattleText__(f"DRAW! NO ONE WINS!")

        print(f"Player 1 health: {self.p1.ac.health}\nPlayer 2 health: {self.p2.ac.health}")
        print(f"Player 1 move count & health healed: {p1_move_count} & {self.p1.ac.total_damage_healed}")
        print(f"Player 2 move count & health healed: {p2_move_count} & {self.p2.ac.total_damage_healed}")
