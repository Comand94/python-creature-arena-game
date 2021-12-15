import random

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
#   for now I will settle with a multiplier of 0.75
for i in range(0, n_o_c):
    cr_mo_op_multiplier[3][4][i] = 0.75


# score status deadliness against opponent
# faster = 0.5 means proc might or might not be before opponent's turn
# opponent_attacking = True means opponent is attacking this turn
def score_se(se: cr.StatusEffect, faster: float = 0.5,
             target_self: bool = False, opponent_attacking: bool = False,
             damage_sm: float = 1, thorn_sm: float = 1,
             round_cap: int = 16) -> float:
    score: float = 0

    # normalize score for status on self
    if target_self:
        m = -1
    else:
        m = 1

    # cap duration
    status_duration = se.status_duration
    if status_duration > round_cap:
        status_duration = round_cap
    stun_duration = se.stun_duration
    if stun_duration > round_cap:
        stun_duration = round_cap

    # damage over time average
    score += m * (se.damage_low + se.damage_high) * damage_sm * status_duration / 2 * 8

    # damage penalty
    if se.damage_mod_type is None or target_self is True:  # relevant for sure
        score -= m * se.damage_mod * damage_sm * status_duration * 4
    else:  # affects some attacks (I wouldn't bother to check with creature type)
        score -= m * se.damage_mod * damage_sm * status_duration

    # penalty duration and severity
    score -= m * (se.aim_mod + se.defense_mod) * status_duration

    # penalty for opponent during casting turn
    if opponent_attacking and target_self:
        score -= m * faster * se.defense_mod * 2
    if opponent_attacking and not target_self:
        score -= m * faster * se.aim_mod * 2

    # stun duration
    if stun_duration >= 0 and not target_self:
        score += 120 * faster  # extra turn from stun means way more incentive to use it
    if stun_duration > 0:
        score += m * 80 * stun_duration

    # thorn damage - average damage and assuming 50% hit chance
    if target_self and opponent_attacking:  # 100% hit chance for turn 0 if faster
        score -= m * faster * (se.thorn_damage_low + se.thorn_damage_high) * thorn_sm * 5
    score -= m * (se.thorn_damage_low + se.thorn_damage_high) * thorn_sm * status_duration * 2.5

    return score


def score_move(creatures: list[cr.CreatureOccurrence, cr.CreatureOccurrence],
               move_indices: list[int, int]) -> (float, float):
    scores: list[float, float] = [0, 0]

    for index in range(2):
        opponent = creatures[(index + 1) % 2]
        move_op = opponent.c.moves[move_indices[(index + 1) % 2]]
        ai = creatures[index]
        move_ai = ai.c.moves[move_indices[index]]
        is_not_stunned = not ai.isStunned

        # rough estimate of how many rounds are left to play before one of the creatures dies
        # this is to lower status effect's impact on score when it is clear it won't dish out full benefits
        round_cap = opponent.health
        if round_cap > ai.health:
            round_cap = ai.health
        round_cap /= 5

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

        if move_ai.target_self and is_not_stunned:

            # normalized damage score
            damage = -(move_ai.damage_low + move_ai.damage_high) * move_ai.hit_attempts
            heal_limit = ai.c.health - ai.health  # max health that can be healed rn
            if damage > heal_limit:
                damage = heal_limit
            damage_score = 5 * damage

            if move_ai.status_effect is not None:
                thorn_mp = opponent.__checkTypeRelationship__(move_ai.status_effect.type)

                # normalized status score (inside the score_se function)
                status_score = \
                    score_se(move_ai.status_effect, faster, True, opponent_attacking, 1, thorn_mp, round_cap) * \
                    (move_ai.status_chance / 100) * move_ai.hit_attempts
            else:
                status_score = 0
            scores[index] = \
                (damage_score + status_score) * \
                cr_mo_op_multiplier[ai.c.id][move_indices[index]][opponent.c.id]

            # if the move makes AI kill itself, reset score!
            if ai.health - damage <= 0:
                scores[index] = 0

        elif is_not_stunned:
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
            if hit_chance > 100:
                hit_chance = 100
            damage_mp = opponent.__checkTypeRelationship__(move_ai.type)

            # calculate damage
            damage = ((((move_ai.damage_low + move_ai.damage_high) / 2)
                       + damage_mod) * damage_mp)
            if damage < 0:
                damage = 0

            # if damage will likely instantly kill opponent, add extra score - this is likely no time to heal yourself
            damage_score = \
                damage * (hit_chance / 100) * move_ai.hit_attempts
            if damage_score > opponent.health:
                damage_score += 5

            # normalized damage score
            damage_score *= 10

            # calculate and normalize retaliation/leech
            thorn_damage = 10 * (thorn_mod_low + thorn_mod_high) / 2
            heal_limit = ai.c.health - ai.health  # max health that can be leeched rn
            if thorn_damage < -heal_limit:
                thorn_damage = -heal_limit

            if move_ai.status_effect is not None:
                status_mp = opponent.__checkTypeRelationship__(move_ai.status_effect.type)
                # normalized status score (inside the score_se function)
                status_score = \
                    score_se(move_ai.status_effect, faster, False, opponent_attacking, status_mp, 1, round_cap) * \
                    (move_ai.status_chance / 100) * status_mp * \
                    (hit_chance / 100) * move_ai.hit_attempts
            else:
                status_score = 0
            scores[index] = \
                (damage_score - thorn_damage + status_score) * \
                cr_mo_op_multiplier[ai.c.id][move_indices[index]][opponent.c.id]
            #print(f"score_move final for {move_ai.name} {scores[index]} with cr_mo_op mp "
            #      f"{cr_mo_op_multiplier[ai.c.id][move_indices[index]][opponent.c.id]}")
        else:
            scores[index] = 0

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
        if self.ai > 5:
            self.ai = 5
        # how much ai appreciates own score against enemy move score
        # 0.5 means equally, 1 means it only cares about enemy move, 0 means it only cares about own move
        self.risk_aversion_factor = random.uniform(0.1, 0.9)
        # max cap for random score factor (AI can make mistakes in calculations that add randomness)
        self.random_score_factor_cap = 0.25 - float(self.ai / 20)

    # was guess correct?
    def risk_evaluation(self, op_assumed: int, op_roll: int):
        if op_assumed == op_roll: # it was correct, risk aversion subsides
            self.risk_aversion_factor -= 0.1
            if self.risk_aversion_factor < 0.1:
                self.risk_aversion_factor = 0.1
        elif op_assumed != -1: # it was incorrect, risk aversion increases doubly
            self.risk_aversion_factor += 0.2
            if self.risk_aversion_factor > 0.9:
                self.risk_aversion_factor = 0.9

    # returns move index and assumed opponent move if risking, else -1
    def __calculateMove__(self, opponent: cr.CreatureOccurrence) -> (int, int):
        if self.ai <= 0:  # dumb ai makes random moves
            move_roll = random.randrange(0, 5)
            while self.ac.cooldowns[move_roll] >= 1:
                move_roll = random.randrange(0, 5)

        if self.ai > 0:  # ai calculates rewards of each move in every possible scenario

            move_ai_score_sum = [0, 0, 0, 0, 0]
            opponent_score_sum = [0, 0, 0, 0, 0]
            rewards_ai = [0, 0, 0, 0, 0]
            best_avg_moves_ai = [-1, -1]
            best_avg_rewards_ai = [-100000, -100000]

            move_opponent_score_sum = [0, 0, 0, 0, 0]
            ai_score_sum = [0, 0, 0, 0, 0]
            n_opponent = [0, 0, 0, 0, 0]
            rewards_opponent = [0, 0, 0, 0, 0]
            best_avg_move_opponent = -1
            best_avg_move_opponent_reward = -100000

            move_opponent_best_ai_counter_move = [0, 0, 0, 0, 0]
            move_opponent_best_ai_counter_move_score = [-100000, -100000, -100000, -100000, -100000]

            ami = 0
            while ami < 5:
                n = 0
                if self.ac.cooldowns[ami] <= 0:  # ai move to take into account
                    omi = 0
                    while omi < 5:
                        if opponent.cooldowns[omi] <= 0:  # opponent move to take into account

                            # calculate move score for moves in pairs
                            a, b = score_move([self.ac, opponent], [ami, omi])

                            # mistake in calculations by novice ai
                            random_factor = random.uniform(0, self.random_score_factor_cap)
                            a *= 1 - random_factor
                            b *= 1 - random_factor

                            # increment divisors
                            n += 1
                            n_opponent[omi] += 1

                            # figure out own average (safe) move
                            move_ai_score_sum[ami] += a
                            opponent_score_sum[ami] += b
                            rewards_ai[ami] += move_ai_score_sum[ami] - opponent_score_sum[ami]

                            # figure out opponent's best average (safe) move
                            move_opponent_score_sum[omi] += b
                            ai_score_sum[omi] += a
                            rewards_opponent[omi] += move_opponent_score_sum[omi] - ai_score_sum[omi]

                            # track best counter-moves to each opponent move
                            if a - b > move_opponent_best_ai_counter_move_score[omi]:
                                move_opponent_best_ai_counter_move_score[omi] = a - b
                                move_opponent_best_ai_counter_move[omi] = ami

                        omi += 1
                    if n > 0: # figure out own average reward of average (safe) move
                        rewards_ai[ami] /= n
                        print(f"{self.ac.c.name} rewards[{ami}] = {rewards_ai[ami]}")
                        if rewards_ai[ami] > best_avg_rewards_ai[0]:
                            best_avg_moves_ai[1] = best_avg_moves_ai[0]
                            best_avg_rewards_ai[1] = best_avg_rewards_ai[0]
                            best_avg_moves_ai[0] = ami
                            best_avg_rewards_ai[0] = rewards_ai[ami]
                        elif rewards_ai[ami] > best_avg_rewards_ai[1]:
                            best_avg_moves_ai[1] = ami
                            best_avg_rewards_ai[1] = rewards_ai[ami]
                ami += 1

            # figure out opponent average reward of average (safe) move
            for ind in range(0, 5):
                if n_opponent[ind] != 0:
                    rewards_opponent[ind] /= n_opponent[ind]
                    if rewards_opponent[ind] > best_avg_move_opponent_reward:
                        best_avg_move_opponent = ind
                        best_avg_move_opponent_reward = rewards_opponent[ind]

            risk_roll = random.uniform(0, 1)
            if not opponent.isStunned and \
                    risk_roll > self.risk_aversion_factor and best_avg_move_opponent != -1:
                # take a risk - assume enemy will make the best average move
                # counter it with the best move in that situation
                print(f"{self.ac.c.name} risque "
                      f"{move_opponent_best_ai_counter_move[best_avg_move_opponent]}")
                return move_opponent_best_ai_counter_move[best_avg_move_opponent], best_avg_move_opponent

            # function finished if took risk, else take an average move
            # when taking an average move, risk aversion subsides a little
            self.risk_aversion_factor -= 0.02
            if self.risk_aversion_factor < 0.1:
                self.risk_aversion_factor = 0.1

            # pick between two best moves
            if best_avg_moves_ai[1] != -1:
                #print(f"best_moves_rewards {best_moves_rewards[0]} {best_moves_rewards[1]}")
                score0 = best_avg_rewards_ai[0]
                score1 = best_avg_rewards_ai[1]
                #print(f"best_moves_rewards 2 {best_moves_rewards[0]} {best_moves_rewards[1]}")
                abs_score1 = abs(score1) + 1
                score0 += abs_score1
                score1 += abs_score1
                #print(f"score0, score1 {score0}, {score1}")
                #print(f"moves {best_moves[0]} {best_moves[1]}")
                randomized = random.choices([0, 1], weights = [score0, score1])
                if randomized == [1]:
                    move_roll = best_avg_moves_ai[1]
                else:
                    #print(f"randomized {randomized}")
                    move_roll = best_avg_moves_ai[0]

            else:
                move_roll = best_avg_moves_ai[0]
            #print(f"move_roll {move_roll}")
            return move_roll, -1

