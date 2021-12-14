import random
import scripts.player as pl
from scripts.creatures import CreatureOccurrence



class Battle:
    def __init__(self, p1: pl.Player, p2: pl.Player):

        print("\nPlayer 1: choose your creature")
        i = 1
        c: CreatureOccurrence
        for c in p1.creatures:
            print(f"{i}. {c.c.name}")
        p1.ac = p1.creatures.__getitem__(0)
        print(f"\nPlayer 1 chose {p1.ac.c.name}!")

        print("\nPlayer 2: choose your creature")
        i = 1
        c: CreatureOccurrence
        for c in p2.creatures:
            print(f"{i}. {c.c.name}")
        p2.ac = p2.creatures.__getitem__(1)
        print(f"\nPlayer 2 chose {p2.ac.c.name}!")

        print("\nFIGHT!")

        p1_move_count = [0, 0, 0, 0, 0]
        p2_move_count = [0, 0, 0, 0, 0]

        while p1.ac.health > 0 and p2.ac.health > 0:

            print()
            p1.ac.__tickStatus__()
            p2.ac.__tickStatus__()
            p1.ac.__checkIfStunned__()
            p2.ac.__checkIfStunned__()
            # time.sleep(1)
            print()
            p1.ac.__tickCooldowns__()
            p2.ac.__tickCooldowns__()
            # time.sleep(1)

            # roll the moves for testing
            p1_move_roll = random.randrange(0, 5)
            p2_move_roll = random.randrange(0, 5)
            print(f"{p1.ac.c.name} rolled {p1_move_roll}, cooldown: {p1.ac.cooldowns[p1_move_roll]}")
            print(f"{p2.ac.c.name} rolled {p2_move_roll}, cooldown: {p2.ac.cooldowns[p2_move_roll]}")

            # re-roll if necessary
            while p1.ac.cooldowns[p1_move_roll] >= 1:
                p1_move_roll = random.randrange(0, 5)
                print(f"{p1.ac.c.name} rolled {p1_move_roll}, cooldown: {p1.ac.cooldowns[p1_move_roll]}")
                # time.sleep(0.2)
            while p2.ac.cooldowns[p2_move_roll] >= 1:
                p2_move_roll = random.randrange(0, 5)
                print(f"{p2.ac.c.name} rolled {p2_move_roll}, cooldown: {p2.ac.cooldowns[p2_move_roll]}")
                # time.sleep(0.2)

            move_score = pl.score_move([p1.ac, p2.ac], [p1_move_roll, p2_move_roll])
            print(f"move_score p1, p2: {move_score}")

            print(f"\n(SOT) Player 1 health: {p1.ac.health}\n      Player 2 health: {p2.ac.health}")

            # move order
            if p2.ac.isStunned and not p1.ac.isStunned:
                moves_first = 1
                moves_second = 0
            elif not p2.ac.isStunned and p1.ac.isStunned:
                moves_first = 2
                moves_second = 0
            elif p2.ac.isStunned and p1.ac.isStunned:
                moves_first = 0
                moves_second = 0
            elif p2.ac.c.moves[p2_move_roll].speed > p1.ac.c.moves[p1_move_roll].speed:
                moves_first = 2
                moves_second = 1
            elif p2.ac.c.moves[p2_move_roll].speed < p1.ac.c.moves[p1_move_roll].speed:
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

            if p1.ac.isStunned:
                print("Player 1 is stunned and skips the turn!")
            if p2.ac.isStunned:
                print("Player 2 is stunned and skips the turn!")

            # moves
            if moves_first == 2:
                #time.sleep(1)
                print(f"{p2.ac.c.name} uses {p2.ac.c.moves[p2_move_roll].name}!")
                p2.ac.__makeMove__(p1.ac, p2.ac.c.moves[p2_move_roll])
                p2.ac.cooldowns[p2_move_roll] = p2.ac.c.moves[p2_move_roll].cooldown + 1
                p2_move_count[p2_move_roll] += 1

            if moves_first == 1 or moves_second == 1:
                # time.sleep(1)
                p1.ac.__checkIfStunned__()
                if p1.ac.isStunned: # could be stunned if moves second
                    print("Player 1 is stunned out of his move and skips the turn!")
                else:
                    print(f"{p1.ac.c.name} uses {p1.ac.c.moves[p1_move_roll].name}!")
                    p1.ac.__makeMove__(p2.ac, p1.ac.c.moves[p1_move_roll])
                    p1.ac.cooldowns[p1_move_roll] = p1.ac.c.moves[p1_move_roll].cooldown + 1
                    p1_move_count[p1_move_roll] += 1

            if moves_second == 2:
                # time.sleep(1)
                p2.ac.__checkIfStunned__()
                if p2.ac.isStunned: # could be stunned if moves second
                    print("Player 2 is stunned out of his move and skips the turn!")
                else:
                    print(f"{p2.ac.c.name} uses {p2.ac.c.moves[p2_move_roll].name}!")
                    p2.ac.__makeMove__(p1.ac, p2.ac.c.moves[p2_move_roll])
                    p2.ac.cooldowns[p2_move_roll] = p2.ac.c.moves[p2_move_roll].cooldown + 1
                    p2_move_count[p2_move_roll] += 1

            #time.sleep(1)
            print(f"(EOT) Player 1 health: {p1.ac.health}\n      Player 2 health: {p2.ac.health}")

            # time.sleep(1)

        if p1.ac.health <= 0 and p2.ac.health > 0:
            print("\nPLAYER 2 WINS!")
        elif p1.ac.health > 0 and p2.ac.health <= 0:
            print("\nPLAYER 1 WINS!")
        else:
            print("\nDRAW! NO ONE WINS!")

        print(f"Player 1 health: {p1.ac.health}\nPlayer 2 health: {p2.ac.health}")
        print(f"Player 1 move count & health healed: {p1_move_count} & {p1.ac.total_damage_healed}")
        print(f"Player 2 move count & health healed: {p2_move_count} & {p2.ac.total_damage_healed}")

