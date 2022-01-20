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

num_of_creatures = cr.all_creatures.__len__()
cr_mo_op_multiplier = [[[1.0 for x in range(num_of_creatures)] for y in range(7)] for z in range(num_of_creatures)]

# now for individual touch...

#   the first move to change is Warmth against Psawarca - it will rarely see full effect of 4 turns
#   of healing; in fact, Psawarca has two water-based attacks both on 2 turn cooldown, so Warmth,
#   if Psawarca chooses to use them constantly, will provide 1/4th of benefit, but
#   maybe he would prefer a different move because he's afraid of Firewall for example, sooo 0.5 multiplier
cr_mo_op_multiplier[0][2][2] = 0.5

#   the second move that needs special scoring is Reset Void - against anyone, really
#   the move is only likely to deal thorn damage in the turn of casting, not afterwards
#   technically any moves that proc status against Shigowi might need special scoring, because
#   Reset Void can remove any status effect, but because RV is on a 6 turn cooldown and because
#   it is a worthwhile move only when timed right before an attack, we can assume that will not
#   happen very often
for i in range(0, num_of_creatures):
    cr_mo_op_multiplier[3][4][i] = 0.25

# same for escape to void, except actually worse
for i in range(0, num_of_creatures):
    cr_mo_op_multiplier[3][1][i] = 0.15

# health kit / change creature multiplier
for i in range(0, num_of_creatures):
    for j in range(0, num_of_creatures):
        cr_mo_op_multiplier[i][5][j] = 1

# fragonire against psawarca and vice versa
#cr_mo_op_multiplier[0][5][2] = 1.5
#cr_mo_op_multiplier[2][5][0] = 0.5

# psawarca against schonips and vice versa
#cr_mo_op_multiplier[2][5][1] = 1.5
#cr_mo_op_multiplier[1][5][2] = 0.5

# shigowi against psawarca and vice versa
#cr_mo_op_multiplier[2][5][1] = 1.3
#cr_mo_op_multiplier[1][5][2] = 0.7

# bamat might use magical reinforcement too much sometimes...
for i in range(0, num_of_creatures):
    cr_mo_op_multiplier[4][4][i] = 0.85

# bites and claws are underappreciated by AI because of their lack of status
for i in range(0, num_of_creatures):
    cr_mo_op_multiplier[0][1][i] = 1.2
    cr_mo_op_multiplier[1][0][i] = 1.1
    cr_mo_op_multiplier[4][0][i] = 1.2

# physical attack bonus against bamat
    cr_mo_op_multiplier[0][1][4] = 1.5
    cr_mo_op_multiplier[1][0][4] = 1.2
    cr_mo_op_multiplier[4][0][4] = 1.3

# warmth is slightly overappreciated by ai
for i in range(0, num_of_creatures):
    cr_mo_op_multiplier[0][2][i] = 0.9

# shed skin is overappreciated by AI, really
for i in range(0, num_of_creatures):
    cr_mo_op_multiplier[1][3][i] = 0.7

# same for electrification
for i in range(0, num_of_creatures):
    cr_mo_op_multiplier[1][1][i] = 0.8


# score status deadliness against opponent
# faster = 0.5 means proc might or might not be before opponent's turn
# opponent_attacking = True means opponent is attacking this turn
# damage worth is a damage score multiplier dependant on creature's max health (80 / max)
def score_se(se: cr.StatusEffect, faster: float = 0.5,
             target_self: bool = False, opponent_attacking: bool = False,
             damage_sm: float = 1, thorn_sm: float = 1,
             round_cap: int = 1, dot_damage_worth: float = 1,
             thorn_damage_worth: float = 1, opponent_stunned: bool = False) -> float:
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
    score += m * (se.damage_low + se.damage_high) * damage_sm * status_duration / 2 * 8 * dot_damage_worth

    # damage penalty
    if se.damage_mod_type is None or target_self is True:  # kind of relevant
        score -= m * se.damage_mod * damage_sm * status_duration * 3
    else:  # affects some attacks (I wouldn't bother to check with creature type)
        score -= m * se.damage_mod * damage_sm * status_duration

    # penalty duration and severity
    aim_mod = se.aim_mod
    if aim_mod > 60: # arbitrary point of diminishing returns
        aim_mod = 60
    defense_mod = se.defense_mod
    if defense_mod > 80: # arbitrary point of diminishing returns
        defense_mod = 80
    score -= m * (aim_mod + defense_mod) * status_duration

    # penalty for opponent during casting turn
    if opponent_attacking and target_self:
        score -= m * faster * se.defense_mod * 2
    if opponent_attacking and not target_self:
        score -= m * faster * se.aim_mod * 2

    # stun duration
    if stun_duration >= 0 and not target_self:
        score += m * 120 * faster  # extra turn from stun means way more incentive to use it
    if stun_duration > 0:
        score += m * 80 * stun_duration

    # thorn damage - average damage and assuming 50% hit chance
    if target_self and opponent_attacking and not opponent_stunned:  # 100% hit chance for turn 0 if faster
        thorn_instant_damage = -m * faster * (se.thorn_damage_low + se.thorn_damage_high) * thorn_sm
        if thorn_instant_damage > round_cap * 5: # thorn will likely kill opponent - good move
            score += 40
        score += thorn_instant_damage * 5 * thorn_damage_worth
    score -= m * (se.thorn_damage_low + se.thorn_damage_high) * thorn_sm * status_duration * 2.5 * thorn_damage_worth

    return score

# check if extinguishing score applies
def score_extinguish(ai: cr.CreatureOccurrence, move: cr.Move) -> float:
    score = 0
    so: cr.StatusOccurrence
    for so in ai.active_statuses:
        if ai.__checkTypesWeakness__(so.se.type, move.type):
            if move.target_self: # if it's a good status, this will be negative score
                score += so.se.extinguish_scoring * so.status_d
                score += 30 * so.stun_d
            else: # double negative makes positive, so if it's a positive opponent status, this will be positive score
                score -= so.se.extinguish_scoring * so.status_d
                score -= 30 * so.stun_d
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

        # it is relevant to thorn damage if the opponent is attacking or not
        if move_op.target_self:
            opponent_attacking = False
        else:
            opponent_attacking = True

        # which move will be played first will impact each moves' results
        if move_ai.speed > move_op.speed:
            faster = 1.0
        elif move_ai.speed < move_op.speed:
            faster = 0.0
        else:
            faster = 0.5

        # SELF-TARGETTING PLAYER MOVE
        if move_ai.target_self and is_not_stunned:

            damage_worth = 60 / ai.c.health
            thorn_damage_worth = 60 / opponent.c.health

            # normalized damage score
            damage = -(move_ai.damage_low + move_ai.damage_high) * move_ai.hit_attempts
            heal_limit = ai.c.health - ai.health  # max health that can be healed rn
            if damage > heal_limit:
                damage = heal_limit
            damage_score = 5 * damage * damage_worth

            # add extinguishing score to damage_score
            damage_score += score_extinguish(ai, move_ai)

            # there is a status effect to the move
            if move_ai.status_effect is not None:
                thorn_mp = opponent.__checkTypeRelationship__(move_ai.status_effect.type)

                # normalized status score (inside the score_se function)
                status_score = \
                    score_se(move_ai.status_effect, faster, True, opponent_attacking, 1, thorn_mp, round_cap,
                             damage_worth, thorn_damage_worth, opponent.isStunned) * (move_ai.status_chance / 100) * move_ai.hit_attempts

            else: # there is no status possible with the move
                status_score = 0
            scores[index] = \
                (damage_score + status_score) * \
                cr_mo_op_multiplier[ai.c.id][move_indices[index]][opponent.c.id]

            # if the move makes AI kill itself, set score to something bad!
            # for instance, shed skin with 1 health or reset void with 4 or less :P
            if ai.health - damage <= 0:
                scores[index] = -100
            #print(f"score_move final for {move_ai.name} {scores[index]} with cr_mo_op mp "
            #  f"{cr_mo_op_multiplier[ai.c.id][move_indices[index]][opponent.c.id]}")

        # ATTACKING MOVE
        elif is_not_stunned:

            damage_worth = 60 / opponent.c.health
            thorn_damage_worth = 60 / ai.c.health

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
            if hit_chance > 110:
                hit_chance = 110
            if hit_chance < 0: # fix for double negative
                hit_chance = 0
            damage_mp = opponent.__checkTypeRelationship__(move_ai.type)

            # damage mod gives extra incentive to use that move before the status expires
            # despite the damage being equal value against opponent's health
            damage_mod *= 2

            # calculate damage
            damage = ((((move_ai.damage_low + move_ai.damage_high) / 2)
                       + damage_mod) * damage_mp)
            if damage < 0:
                damage = 0

            damage_score = \
                damage * (hit_chance / 100) * move_ai.hit_attempts

            # if damage will likely instantly kill opponent, add extra score - this is likely no time to heal yourself
            if damage_score > opponent.health:
                damage_score += 5

            # normalized damage score
            damage_score *= 10 * damage_worth

            # add extinguishing score to damage_score
            damage_score += score_extinguish(opponent, move_ai)

            # calculate and normalize retaliation/leech
            thorn_damage = 10 * (thorn_mod_low + thorn_mod_high) / 2
            heal_limit = ai.c.health - ai.health  # max health that can be leeched rn
            if thorn_damage < -heal_limit:
                thorn_damage = -heal_limit * thorn_damage_worth

            # there is a status effect with the move
            if move_ai.status_effect is not None:
                status_mp = opponent.__checkTypeRelationship__(move_ai.status_effect.type)
                # normalized status score (inside the score_se function)
                status_score = \
                    score_se(move_ai.status_effect, faster, False, opponent_attacking, status_mp, 1,
                             round_cap, damage_worth, thorn_damage_worth, opponent.isStunned) * \
                    (move_ai.status_chance / 100) * status_mp * \
                    (hit_chance / 100) * move_ai.hit_attempts
            else: # there is no status effect with the move
                status_score = 0
            scores[index] = \
                (damage_score - thorn_damage + status_score) * \
                cr_mo_op_multiplier[ai.c.id][move_indices[index]][opponent.c.id]
            #print(f"score_move final for {move_ai.name} {scores[index]} with cr_mo_op mp "
            #      f"{cr_mo_op_multiplier[ai.c.id][move_indices[index]][opponent.c.id]}")
        else: # STUNNED
            scores[index] = 0

    return scores[0], scores[1]


class Player:
    def __init__(self, id: int, creatures: list[cr.CreatureOccurrence, ...], ai: int = -1):
        self.id = id
        self.creatures = creatures  # player's creatures
        self.ac_index = 0
        self.ac = creatures[self.ac_index]  # active creature
        self.ai = ai  # ai difficulty (-1 means Player is controlled by a human)
        if self.ai > 10:
            self.ai = 10
        # how much ai appreciates own score against enemy move score
        # 0.5 means equally, 1 means it will do a safe move, 0 means it will make a risky move half the time
        self.risk_aversion_factor = random.uniform(0.2, 0.9)
        # 0.5 means equally, 1 means it assumes a bold opponent move half the time, 0 means it assumes safe move
        self.assume_blunder_factor = random.uniform(0.1, 0.8)
        # max cap for random score factor (AI can make mistakes in calculations that add randomness)
        self.random_score_factor_cap = 0.25 - float(self.ai / 20)
        if self.random_score_factor_cap < 0:
            self.random_score_factor_cap = 0
        # modifier larger and larger than 1 the longer the move isn't used
        # if cooldown is high, modifier increases more slowly
        self.novelty_factor = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

    # was guess correct?
    def risk_evaluation(self, op_assumed: int, op_assumed_name: str, op_roll: int, counter_mode: str):

        if counter_mode != "": # if an assumption was made at all

            text = ["", "", "", ""]

            if counter_mode == "c":
                text[0] = f"PLAYER {self.id} THOUGHT IT'S OPPONENT WILL MAKE"
                text[1] = f'A SAFE MOVE OF "{op_assumed_name}"...'
            else:
                text[0] = f"PLAYER {self.id} THOUGHT IT'S OPPONENT WILL MAKE"
                text[1] = f'A RISKY MOVE OF "{op_assumed_name}"...'

            print(f"pre-round raf and baf for {self.ac.c.name} "
                  f"{self.risk_aversion_factor} {self.assume_blunder_factor}")
            if op_assumed == op_roll: # it was correct
                text[2] = f"PLAYER {self.id} WAS RIGHT!"
                text[3] = "BEHAVIOUR REINFORCED!"

                if counter_mode == "c": # aversion subsides
                    self.risk_aversion_factor -= 0.1
                    if self.risk_aversion_factor < 0.2:
                        self.risk_aversion_factor = 0.2
                else: # blunder assumptions rise
                    self.assume_blunder_factor += 0.1
                    if self.assume_blunder_factor > 0.8:
                        self.assume_blunder_factor = 0.8
            elif op_assumed != -1: # it was incorrect
                text[2] = f"PLAYER {self.id} WAS WRONG!"
                text[3] = "fBEHAVIOUR PUNISHED!"

                if counter_mode == "c": # aversion increases doubly
                    self.risk_aversion_factor += 0.2
                    if self.risk_aversion_factor > 0.9:
                        self.risk_aversion_factor = 0.9
                else: # blunder assumptions decrease doubly
                    self.assume_blunder_factor -= 0.2
                    if self.assume_blunder_factor < 0.1:
                        self.assume_blunder_factor = 0.1
            print(f"post-round raf and baf for {self.ac.c.name} "
                  f"{self.risk_aversion_factor} {self.assume_blunder_factor}")

            if self.ac.bs is not None:
                self.ac.bs.__animateTextbox__(True)
                self.ac.bs.__animateBattleText__(text[0], text[1])
                self.ac.bs.__animateBattleText__(text[2], text[3])
                self.ac.bs.__animateTextbox__(False)

    def __calculateNoveltyFactors__(self, move_roll: int):
        for ind in range(0, 7):
            if ind != move_roll:

                # cap ai level
                if self.ai > 5:
                    ai_lvl = 5
                else:
                    ai_lvl = self.ai

                # novelty factor grows more slowly for better ai, it impacts it's decisions less
                increment = 0.15 - 0.005 * (self.ac.c.moves[ind].cooldown + 1) * ai_lvl
                if increment < 0.001:
                    increment = 0.001
                self.novelty_factor[ind] += increment
                # cap novelty factor lower for better ai, so it cannot overwrite better decisions as much
                if self.novelty_factor[ind] > 1.65 - 0.1 * ai_lvl:
                    self.novelty_factor[ind] = 1.65 - 0.1 * ai_lvl
            else:
                self.novelty_factor[ind] = 1
        print(f"p{self.id} novelty factors {self.novelty_factor}")

    # returns move index and assumed opponent move if risking, else -1, and a string code "" "c" or "cc"
    # "" stands for normal move, "c" for "countermove" and "cc" for "counter-countermove"
    def __calculateMove__(self, opponent: cr.CreatureOccurrence) -> (int, int, str):
        if self.ai <= 0:  # dumb ai makes random moves
            move_roll = random.randrange(0, 7)
            while self.ac.cooldowns[move_roll] >= 1 and self.ac.rage >= self.ac.c.moves[move_roll].rage_cost:
                move_roll = random.randrange(0, 7)

        else:  # ai calculates rewards of each move in every possible scenario

            move_ai_score_sum = [0, 0, 0, 0, 0, 0, 0]
            opponent_score_sum = [0, 0, 0, 0, 0, 0, 0]
            rewards_ai = [0, 0, 0, 0, 0, 0, 0]
            best_avg_moves_ai_0, best_avg_moves_ai_1 = -1, -1
            best_avg_rewards_ai_0, best_avg_rewards_ai_1 = -100000, -100000

            move_opponent_score_sum = [0, 0, 0, 0, 0, 0, 0]
            ai_score_sum = [0, 0, 0, 0, 0, 0, 0]
            n_opponent = [0, 0, 0, 0, 0, 0, 0]
            rewards_opponent = [0, 0, 0, 0, 0, 0, 0]
            best_avg_move_opponent = -1
            best_avg_move_opponent_reward = -100000

            move_opponent_best_ai_counter_move = [-1, -1, -1, -1, -1, -1, -1]
            move_opponent_best_ai_counter_move_score = [-100000, -100000, -100000, -100000, -100000, -100000, -100000]

            move_ai_best_opponent_counter_move = [-1, -1, -1, -1, -1, -1, -1]
            move_ai_best_opponent_counter_move_score = [-100000, -100000, -100000, -100000, -100000, -100000, -100000]

            ami = 0
            while ami < 7:
                n = 0
                if self.ac.cooldowns[ami] <= 0 and self.ac.rage >= self.ac.c.moves[ami].rage_cost:  # ai move to take into account
                    omi = 0
                    while omi < 7:
                        if opponent.cooldowns[omi] <= 0 and opponent.rage >= opponent.c.moves[ami].rage_cost:  # opponent move to take into account

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
                            move_ai_score_sum[ami] += a * self.novelty_factor[ami] # include novelty factor
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
                            # track best counter-moves to each of your moves
                            if b - a > move_ai_best_opponent_counter_move_score[ami]:
                                move_ai_best_opponent_counter_move_score[ami] = b - a
                                move_ai_best_opponent_counter_move[ami] = omi

                        omi += 1
                    if n > 0: # figure out own average reward of average (safe) move
                        rewards_ai[ami] /= n
                        print(f"{self.ac.c.name} rewards[{ami}] = {rewards_ai[ami]}")
                        if rewards_ai[ami] > best_avg_rewards_ai_0:
                            best_avg_moves_ai_1 = best_avg_moves_ai_0
                            best_avg_rewards_ai_1 = best_avg_rewards_ai_0
                            best_avg_moves_ai_0 = ami
                            best_avg_rewards_ai_0 = rewards_ai[ami]
                        elif rewards_ai[ami] > best_avg_rewards_ai_1:
                            best_avg_moves_ai_1 = ami
                            best_avg_rewards_ai_1 = rewards_ai[ami]
                ami += 1

            # figure out opponent average reward of average (safe) move
            for ind in range(0, 7):
                if n_opponent[ind] != 0: # relevant moves only (off-cooldown)
                    rewards_opponent[ind] /= n_opponent[ind]
                    if rewards_opponent[ind] > best_avg_move_opponent_reward:
                        best_avg_move_opponent = ind
                        best_avg_move_opponent_reward = rewards_opponent[ind]

            best_risky_move_opponent = move_ai_best_opponent_counter_move[best_avg_moves_ai_0]
            print(f"best_risky_move_op {best_risky_move_opponent}")
            print(f"best_average_move_op {best_avg_move_opponent}")

            # risk move
            risk_roll = random.uniform(-1, 1)
            if not opponent.isStunned and \
                    risk_roll > self.risk_aversion_factor and best_avg_move_opponent != -1:
                # take a risk - assume enemy will make the best average move
                # counter it with the best move in that situation
                print(f"{self.ac.c.name} is taking risks against {best_avg_move_opponent} with "
                      f"{move_opponent_best_ai_counter_move[best_avg_move_opponent]}")
                move_roll = move_opponent_best_ai_counter_move[best_avg_move_opponent]
                self.__calculateNoveltyFactors__(move_roll)
                return move_roll, best_avg_move_opponent, "c"

            # counter a risk move
            counter_roll = random.uniform(0, 2)
            if not opponent.isStunned and \
                    counter_roll < self.assume_blunder_factor and best_risky_move_opponent != -1:
                print(f"{self.ac.c.name} assumes blunder of {best_risky_move_opponent}, uses "
                      f"{move_opponent_best_ai_counter_move[best_risky_move_opponent]}")
                move_roll = move_opponent_best_ai_counter_move[best_risky_move_opponent]
                self.__calculateNoveltyFactors__(move_roll)
                return move_roll, best_risky_move_opponent, "cc"

            # function finished if took risk, else take an average move
            # when taking an average move, risk aversion subsides a little, blunder assumptions rise
            self.risk_aversion_factor -= 0.02
            if self.risk_aversion_factor < 0.2:
                self.risk_aversion_factor = 0.2
            self.assume_blunder_factor += 0.02
            if self.assume_blunder_factor > 0.8:
                self.assume_blunder_factor = 0.8

            # pick between two best moves
            if best_avg_moves_ai_1 != -1:
                #print(f"best_moves_rewards {best_moves_rewards[0]} {best_moves_rewards[1]}")
                score0 = best_avg_rewards_ai_0
                score1 = best_avg_rewards_ai_1
                #print(f"best_moves_rewards 2 {best_moves_rewards[0]} {best_moves_rewards[1]}")
                abs_score1 = abs(score1) + 1
                score0 += abs_score1
                score1 += abs_score1
                #print(f"score0, score1 {score0}, {score1}")
                #print(f"moves {best_moves[0]} {best_moves[1]}")
                randomized = random.choices([0, 1], weights = [score0, score1])
                if randomized == [1]:
                    move_roll = best_avg_moves_ai_1
                else:
                    #print(f"randomized {randomized}")
                    move_roll = best_avg_moves_ai_0

            else:
                move_roll = best_avg_moves_ai_0
            #print(f"move_roll {move_roll}")

            # calculate new novelty factors
            self.__calculateNoveltyFactors__(move_roll)

        return move_roll, -1, ""

