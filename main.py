import pygame
import scripts.creatures as sc
import scripts.battle as sb

def main():
    player1_creatures = player2_creatures = \
        (sc.CreatureOccurrence(sc.all_creatures["FRAGONIRE"]), sc.CreatureOccurrence(sc.all_creatures["SCHONIPS"]))

    sb.Battle(player1_creatures, player2_creatures, False)

if __name__ == "__main__":
    main()