import pygame
import scripts.creatures as sc
import scripts.battle as sb
import scripts.player as pl

def main():
    player1_creatures = player2_creatures = \
        (sc.CreatureOccurrence(sc.all_creatures["FRAGONIRE"]), sc.CreatureOccurrence(sc.all_creatures["SCHONIPS"]))

    player1 = pl.Player(pl.random_name(), player1_creatures, 0)
    player2 = pl.Player(pl.random_name(), player2_creatures, 0)

    sb.Battle(player1, player2)

if __name__ == "__main__":
    main()
