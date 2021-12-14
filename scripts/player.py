import random
from typing import List, Any

import scripts.creatures as cr

# creature move opponent multiplier
# scoring modifier for AI - allows better score interpretation of moves when the score may be misleading
#   for example, using Warmth against Psawarca is a little bit useless due to Wet status effect, but this
#   is not being accounted for during score calculations normally
#   other example would be Void Reset, which has thorn for two turns, but that doesn't mean you will deal
#   twice the damage compared to if it were a one turn move - no one will attack an opponent turn after
#   it was cast in their right mind unless they have due to obviously massive penalty for attacking
#       first I will fill the list with multiplier 1 for each move, then I will change it individually
#       for moves that require different scoring

n_o_c = cr.all_creatures.__len__()
cr_mo_op_multiplier = [[[1.0 for x in range(n_o_c)] for y in range(5)] for z in range(n_o_c)]

# now for individual touch...

#   the first move to change is Warmth against Psawarca - it will rarely see full effect of 4 turns
#   of healing; in fact, Psawarca has two water-based attacks both on 2 turn cooldown, so Warmth,
#   on average, will provide 1/4th of benefit
cr_mo_op_multiplier[0][2][2] = 0.25

#   the second move that needs special scoring is Reset Void - against anyone, really
#   the move is only likely to deal thorn damage in the turn of casting, not afterwards
#   technically any moves that proc status against Shigowi might need special scoring, because
#   Reset Void can remove any status effect, but because RV is on a 6 turn cooldown and because
#   it is a worthwhile move only when timed right before an attack, we can assume that will not
#   happen very often
#   anyhow, thorn's impact should be halved, but extinguishing impact should be recognized
#   for now I will settle with a multiplier of 0.67
for i in range(0, n_o_c):
    cr_mo_op_multiplier[3][4][i] = 0.67


# score status deadliness against opponent
# faster = 0.5 means proc might or might not be before opponent's turn
# opponent_attacking = True means opponent is attacking this turn
def score_se(se: cr.StatusEffect, faster: float = 0.5,
             target_self: bool = False, opponent_attacking: bool = False,
             damage_sm: float = 1, thorn_sm: float = 1) -> float:
    score: float = 0
    print(f"score_se start {score}")

    # normalize score for status on self
    if target_self:
        m = -1
    else:
        m = 1

    # damage over time average
    score += m * (se.damage_low + se.damage_high) * damage_sm * se.status_duration / 2 * 10
    print(f"score_se dot {score}")

    # damage penalty
    if se.damage_mod_type is None or target_self is True:  # relevant for sure
        score -= m * se.damage_mod * damage_sm * se.status_duration * 5
    else:  # affects some attacks (I wouldn't bother to check with creature type)
        score -= m * se.damage_mod * damage_sm * se.status_duration
    print(f"score_se damage_mod {score}")

    # penalty duration and severity
    score -= m * (se.aim_mod + se.defense_mod) * se.status_duration
    print(f"score_se nerf {score}")

    # stun duration
    if se.stun_duration >= 0 and not target_self:
        score += 80 * faster
    if se.stun_duration > 0:
        score += m * 80 * se.stun_duration
    print(f"score_se stun {score}")

    # thorn damage - average damage and assuming 50% hit chance
    if target_self and opponent_attacking:  # 100% hit chance for turn 0 if faster
        score -= m * faster * (se.thorn_damage_low + se.thorn_damage_high) * thorn_sm * 5
    score -= m * (se.thorn_damage_low + se.thorn_damage_high) * thorn_sm * se.status_duration * 2.5

    print(f"score_se thorn {score} {se.name}")

    return score


def score_move(creatures: list[cr.CreatureOccurrence, cr.CreatureOccurrence],
               move_indices: list[int, int]) -> (int, int):

    scores: list[float, float] = [0, 0]
    print(f"score_move 1 {scores}")

    for index in range(2):
        opponent = creatures[(index + 1) % 2]
        move_op = opponent.c.moves[move_indices[(index + 1) % 2]]
        ai = creatures[index]
        move_ai = ai.c.moves[move_indices[index]]

        print(f"score_move name {move_ai.name}")

        if move_op.target_self:
            opponent_attacking = False
        else:
            opponent_attacking = True

        if move_ai.speed > move_op.speed:
            faster = 1.0
        elif move_ai.speed < move_op.speed:
            faster = 0.0
        else:
            faster = 0.5

        if move_ai.target_self:
            print("if")
            # normalized damage score
            damage_score = -5 * (move_ai.damage_low + move_ai.damage_high) * move_ai.hit_attempts
            print(f"score_move damage_score {damage_score}")
            if move_ai.status_effect is not None:
                thorn_mp = opponent.__checkTypeRelationship__(move_ai.status_effect.type)
                # normalized status score (inside the score_se function)
                status_score = \
                    score_se(move_ai.status_effect, faster, True, opponent_attacking, 1, thorn_mp) * \
                    (move_ai.status_chance / 100) * move_ai.hit_attempts
            else:
                status_score = 0
            scores[index] = damage_score + status_score
            print(f"score_move final for {move_ai.name} {scores[index]}")
        else:
            print("else")
            aim_mod = 0
            damage_mod = 0
            defense_mod = 0
            thorn_mod_low = 0
            thorn_mod_high = 0

            so: cr.StatusOccurrence
            for so in ai.active_statuses:
                aim_mod += so.se.aim_mod
                if so.se.damage_mod_type is None:
                    damage_mod += so.se.damage_mod
                elif move_ai.type == so.se.damage_mod_type:
                    damage_mod += so.se.damage_mod
            for so in opponent.active_statuses:
                defense_mod += so.se.defense_mod
                thorn_mod_low += so.se.thorn_damage_low
                thorn_mod_high += so.se.thorn_damage_high

            hit_chance = move_ai.aim + aim_mod - opponent.c.defense - defense_mod
            damage_mp = opponent.__checkTypeRelationship__(move_ai.type)

            damage = ((((move_ai.damage_low + move_ai.damage_high) / 2)
                           + damage_mod) * damage_mp)
            if damage < 0:
                damage = 0

            # normalized damage score
            damage_score = \
                10 * damage * (hit_chance / 100) * move_ai.hit_attempts

            print(f"score_move damage_score {damage_score}")

            if move_ai.status_effect is not None:
                status_mp = opponent.__checkTypeRelationship__(move_ai.status_effect.type)
                # normalized status score (inside the score_se function)
                status_score = \
                    score_se(move_ai.status_effect, faster, False, opponent_attacking, status_mp, 1) * \
                    (move_ai.status_chance / 100) * status_mp * \
                    (hit_chance / 100) * move_ai.hit_attempts
            else:
                status_score = 0
            scores[index] = damage_score + status_score
            print(f"score_move final for {move_ai.name} {scores[index]}")

    print(f"score_move x and y {scores}")
    return scores[0], scores[1]


# random polish names for the AI
# not sure that I'll want to use AI names in the GUI yet, but it might come in handy
def random_name() -> str:
    sex = random.randrange(0, 2)
    name_index = random.randrange(0, 30)
    surname_index = random.randrange(0, 48)

    if sex == 0:
        male_names = ("Dawid", "Łukasz", "Adam", "Janusz", "Mariusz", "Mateusz",
                      "Jakub", "Ksawery", "Adrian", "Lech", "Patryk", "Piotr",
                      "Krystian", "Kamil", "Artur", "Jarosław", "Krzysztof", "Michał",
                      "Dariusz", "Edward", "Ignacy", "Józef", "Maciej", "Radosław",
                      "Kacper", "Szymon", "Filip", "Aleksander", "Oskar", "Fabian")

        male_surnames = ("Leszczyński", "Kowalski", "Abramczyk", "Chlebowski", "Cichowski", "Bachleda",
                         "Białecki", "Błaszczykowski", "Lewandowski", "Borys", "Dziuba", "Dąbrowski",
                         "Dobrzyński", "Frankowski", "Gąsowski", "Górski", "Grabowski", "Gutowski",
                         "Halicki", "Iwanicki", "Jabłczynski", "Mickiewicz", "Zielonka", "Matejko",
                         "Siembieda", "Bonda", "Gombrowicz", "Hejmo", "Kołodziejski", "Łakomy",
                         "Duda", "Kukiz", "Kaczyński", "Łagowski", "Kraszewski", "Łazarczyk",
                         "Jankowski", "Klimek", "Kiszka", "Leniart", "Milski", "Mazurkiewicz",
                         "Karpiński", "Kołodziej", "Kwiatkowski", "Lasocki", "Napiórkowski", "Nowicki")

        name: str = male_names[name_index] + " " + male_surnames[surname_index]

    else:
        female_names = ("Natalia", "Beata", "Anna", "Wioleta", "Maria", "Monika",
                        "Milena", "Wiktoria", "Roksana", "Katarzyna", "Aleksandra", "Marta",
                        "Agnieszka", "Julia", "Zuzanna", "Alicja", "Zofia", "Elżbieta",
                        "Aldona", "Angelika", "Emma", "Oliwia", "Sandra", "Gabriela",
                        "Iga", "Kinga", "Paulina", "Patrycja", "Maja", "Lena")

        female_surnames = ("Leszczyńska", "Kowalska", "Abramczyk", "Chlebowska", "Cichowska", "Bachleda",
                           "Białecka", "Błaszczykowska", "Lewandowska", "Borys", "Dziuba", "Dąbrowska",
                           "Dobrzyńska", "Frankowska", "Gąsowska", "Górska", "Grabowska", "Gutowska",
                           "Halicka", "Iwanicka", "Jabłczynska", "Mickiewicz", "Zielonka", "Matejko",
                           "Siembieda", "Bonda", "Gombrowicz", "Hejmo", "Kołodziejska", "Łakoma",
                           "Duda", "Kukiz", "Kaczyńska", "Łagowska", "Kraszewska", "Łazarczyk",
                           "Jankowska", "Klimek", "Kiszka", "Leniart", "Milska", "Mazurkiewicz",
                           "Karpińska", "Kołodziej", "Kwiatkowska", "Lasocka", "Napiórkowska", "Nowicka")

        name: str = female_names[name_index] + " " + female_surnames[surname_index]

    return name


class Player:
    def __init__(self, name, creatures: tuple[cr.CreatureOccurrence, ...], ai: int = -1):
        if name is None:
            self.name = random_name()
        else:
            self.name = name
        self.creatures = creatures  # player's creatures
        self.ac = creatures[0]  # active creature
        self.ai = ai  # ai difficulty (-1 means Player is controlled by a human)

        # risk aversion of 0.5 means go for the move that has the best average outcome
        # risk aversion of 0 means AI will assume it's opponent is going to make an average move and try to punish it
        # risk aversion of 1 means AI will assume it's opponent is going to make a risky move and try to counteract it/avoid the trap
        self.risk_aversion_multiplier = random.uniform(0, 1)

    # def __calculateMove__(self, opponent: cr.CreatureOccurrence) -> cr.Move:
    #    if self.ai == 0:  # dumb ai makes random moves
    #        move_roll = random.randrange(0, 5)
    #        while self.ac.cooldowns[move_roll] >= 1:
    #            move_roll = random.randrange(0, 5)
    #        return self.ac.c.moves[move_roll]

    #    if self.ai > 0:  # ai calculates rewards of each move in every possible scenario
    #        move_rewards = (0, 0, 0, 0, 0)
    #        ami = 0
    #        while ami < 5:
    #            if self.ac.cooldowns[ami] <= 0:  # ai move to take into account
    #                omi = 0
    #                while omi < 5:
    #                    if opponent.cooldowns[omi] <= 0:  # opponent move to take into account
    #
    #                omi += 1
    #            ami += 1
