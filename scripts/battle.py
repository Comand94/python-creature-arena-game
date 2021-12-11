import random
import time
import pygame
import scripts.creatures as cr
from scripts.creatures import CreatureOccurrence


class Battle:
    def __init__(self, player1_creatures: tuple[cr.CreatureOccurrence, ...], player2_creatures: tuple[cr.CreatureOccurrence, ...],
                 isAgainstAI: bool = True):

        print("\nPlayer 1: choose your creature")
        i = 1
        c: CreatureOccurrence
        for c in player1_creatures:
            print(f"{i}. {c.c.name}")
        p1_ac = player1_creatures.__getitem__(0)
        print(f"\nPlayer 1 chose {p1_ac.c.name}!")

        print("\nPlayer 2: choose your creature")
        i = 1
        c: CreatureOccurrence
        for c in player2_creatures:
            print(f"{i}. {c.c.name}")
        p2_ac = player2_creatures.__getitem__(1)
        print(f"\nPlayer 2 chose {p2_ac.c.name}!")

        print("\nFIGHT!")

        p1_move_count = [0, 0, 0, 0, 0]
        p2_move_count = [0, 0, 0, 0, 0]

        while p1_ac.health > 0 and p2_ac.health > 0:

            p1_ac.__checkIfStunned__()
            p2_ac.__checkIfStunned__()
            p1_ac.__tickStatus__()
            p2_ac.__tickStatus__()
            # time.sleep(1)
            print()
            p1_ac.__tickCooldowns__()
            p2_ac.__tickCooldowns__()
            # time.sleep(1)

            # roll the moves for testing
            p1_move_roll = random.randrange(0, 5)
            p2_move_roll = random.randrange(0, 5)
            print(f"{p1_ac.c.name} rolled {p1_move_roll}, cooldown: {p1_ac.cooldowns[p1_move_roll]}")
            print(f"{p2_ac.c.name} rolled {p2_move_roll}, cooldown: {p2_ac.cooldowns[p2_move_roll]}")

            # re-roll if necessary
            while p1_ac.cooldowns[p1_move_roll] >= 1:
                p1_move_roll = random.randrange(0, 5)
                print(f"{p1_ac.c.name} rolled {p1_move_roll}, cooldown: {p1_ac.cooldowns[p1_move_roll]}")
                # time.sleep(0.2)
            while p2_ac.cooldowns[p2_move_roll] >= 1:
                p2_move_roll = random.randrange(0, 5)
                print(f"{p2_ac.c.name} rolled {p2_move_roll}, cooldown: {p2_ac.cooldowns[p2_move_roll]}")
                # time.sleep(0.2)

            print(f"\n(SOT) Player 1 health: {p1_ac.health}\n      Player 2 health: {p2_ac.health}")

            if p1_ac.isStunned:
                print("Player 1 is stunned and skips the turn!")
            if p2_ac.isStunned:
                print("Player 2 is stunned and skips the turn!")

            # move order
            if p2_ac.isStunned and not p1_ac.isStunned:
                moves_first = 1
                moves_second = 0
            elif not p2_ac.isStunned and p1_ac.isStunned:
                moves_first = 2
                moves_second = 0
            elif p2_ac.isStunned and p1_ac.isStunned:
                moves_first = 0
                moves_second = 0
            elif p2_ac.c.moves[p2_move_roll].speed > p1_ac.c.moves[p1_move_roll].speed:
                moves_first = 2
                moves_second = 1
            elif p2_ac.c.moves[p2_move_roll].speed < p1_ac.c.moves[p1_move_roll].speed:
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

            # moves
            if moves_first == 2:
                #time.sleep(1)
                p2_ac.__makeMove__(p1_ac, p2_ac.c.moves[p2_move_roll])
                p2_ac.cooldowns[p2_move_roll] = p2_ac.c.moves[p2_move_roll].cooldown + 1
                p2_move_count[p2_move_roll] += 1

            if moves_first == 1 or moves_second == 1:
                # time.sleep(1)
                p1_ac.__makeMove__(p2_ac, p1_ac.c.moves[p1_move_roll])
                p1_ac.cooldowns[p1_move_roll] = p1_ac.c.moves[p1_move_roll].cooldown + 1
                p1_move_count[p1_move_roll] += 1

            if moves_second == 2:
                # time.sleep(1)
                p2_ac.__makeMove__(p1_ac, p2_ac.c.moves[p2_move_roll])
                p2_ac.cooldowns[p2_move_roll] = p2_ac.c.moves[p2_move_roll].cooldown + 1
                p2_move_count[p2_move_roll] += 1

            #time.sleep(1)
            print(f"(EOT) Player 1 health: {p1_ac.health}\n      Player 2 health: {p2_ac.health}")

            # time.sleep(1)

        if p1_ac.health <= 0 and p2_ac.health > 0:
            print("\nPLAYER 2 WINS!")
        elif p1_ac.health > 0 and p2_ac.health <= 0:
            print("\nPLAYER 1 WINS!")
        else:
            print("\nDRAW! NO ONE WINS!")

        print(f"Player 1 health: {p1_ac.health}\nPlayer 2 health: {p2_ac.health}")
        print(f"Player 1 move count: {p1_move_count}")
        print(f"Player 2 move count: {p2_move_count}")

