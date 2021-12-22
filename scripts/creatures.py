from __future__ import annotations  # type hinting instance of class to it's own functions
import random  # random damage, status chance and hit chance
import scripts.gui as g


testing_wout_type = False #testing balance w/out type relationships

# type of move's initial damage or status effect
# creature's types might be different to types of moves it has
# creature's types determine weaknesses, resistances and immunities it has
class Type:

    def __init__(self, name: str):
        self.name = name
        self.weaknesses = []
        self.resistances = []
        self.immunities = []

    # checks if type relationships don't already exist or if they exclude each other
    # this should prevent situations like element X is weak to Y and also immune to Y
    # returns false if new weakness/resistance/immunity cannot be added
    # weaknesses, resistances and immunities do not apply to self-inflicted moves!
    def __isNewTypeRelationship__(self, type: Type) -> bool:
        for t in self.weaknesses:
            if t == type: return False
        for t in self.resistances:
            if t == type: return False
        for t in self.immunities:
            if t == type: return False
        return True

    # a type this type of creature is weak to - deals extra damage, extra status chance
    def __addWeakness__(self, weakness: Type):
        if self.__isNewTypeRelationship__(weakness):
            self.weaknesses.append(weakness)

    # a type this type of creature is resilient to - deals less damage, extra status chance
    def __addResistances__(self, resistance: Type):
        if self.__isNewTypeRelationship__(resistance):
            self.resistances.append(resistance)

    # a type this type of creature is immune to - deals no damage, does not proc status
    def __addImmunities__(self, immunity: Type):
        if self.__isNewTypeRelationship__(immunity):
            self.immunities.append(immunity)


# a status effect is an affliction or a buff applied over time to a creature
class StatusEffect:

    def __init__(self, name: str, type: Type, damage_low: int = 0, damage_high: int = 0,
                 aim_mod: int = 0, defense_mod: int = 0, damage_mod: int = 0, damage_mod_type: Type = None,
                 status_duration: int = 0, stun_duration: int = -1,
                 thorn_damage_low: int = 0, thorn_damage_high: int = 0):
        self.name = name
        self.type = type
        # damage has a range, with negative values, damage can heal back health permanently over time
        self.damage_low = damage_low
        self.damage_high = damage_high
        # with positive values, aim_mod and defense_mod can provide a temporary buff
        self.aim_mod = aim_mod
        self.defense_mod = defense_mod
        # with negative values, damage_mod can temporarily weaken attacks of type damage_mod_type
        self.damage_mod = damage_mod
        # if damage_mod_type is None, modifier applies to all attack types
        self.damage_mod_type = damage_mod_type
        # duration of 0 means current turn only (no damage ticks will be applied, but effects like defense, thorn, etc.),
        # duration of -1 means no duration
        # this means a move that stuns opponent out of action only in current turn is possible to implement,
        # or a move like firewall which gives the fire dragon creature thorn for current turn only,
        # but it is impossible to trigger damage over time or heal over time without ticking status, which happens at the start of a turn
        self.status_duration = status_duration
        # stun has a separate duration from the rest of effects and it disables all moves
        self.stun_duration = stun_duration
        # thorn damage means the damage taken by attacker of the creature under status
        # thorn damage has a range
        # thorn on negative values allows healing ("leeching" health)
        self.thorn_damage_low = thorn_damage_low
        self.thorn_damage_high = thorn_damage_high


# applied status copy and damage_modifier reflecting weakness/resistance/immunity
class StatusOccurrence:
    def __init__(self, se: StatusEffect):
        self.se = se
        self.status_d = se.status_duration
        self.stun_d = se.stun_duration
        self.damage_modifier = 1


class Move:

    def __init__(self, name: str,
                 type: Type, speed: int = 3, target_self: bool = False,
                 damage_low: int = 0, damage_high: int = 0, aim: int = 90, hit_attempts: int = 1,
                 status_effect: StatusEffect = None, status_chance: int = 0, cooldown: int = 1):
        self.name = name
        self.type = type
        self.speed = speed
        self.target_self = target_self
        # damage has a range, negative damage acts as healing
        self.damage_low = damage_low
        self.damage_high = damage_high
        # aim denotes chance to hit (percentage)
        self.aim = aim
        # hit attempts denotes the number of times the move will attempt to hit
        if hit_attempts < 1: hit_attempts = 1
        self.hit_attempts = hit_attempts
        self.status_effect = status_effect
        self.status_chance = status_chance
        # cooldown of 0 means no cooldown, 1 means one turn, etc.
        if cooldown < 0: cooldown = 0
        self.cooldown = cooldown


# straight-forward
class Creature:

    def __init__(self, id: int, name: str, desc: str, health: int, defense: int,
                 move1: Move, move2: Move, move3: Move, move4: Move, move5: Move,
                 types: tuple[Type, ...]):
        self.id = id
        self.name = name
        self.desc = desc
        self.health = health
        self.defense = defense
        self.moves = []
        self.moves.append(move1)
        self.moves.append(move2)
        self.moves.append(move3)
        self.moves.append(move4)
        self.moves.append(move5)
        self.types = []
        for t in types:
            self.types.append(t)


class CreatureOccurrence:

    def __init__(self, c: Creature):
        self.c = c
        self.health = c.health
        self.active_statuses: list[StatusOccurrence, ...]
        self.active_statuses = []
        self.isStunned = False
        self.cooldowns = [0, 0, 0, 0, 0, 0]
        self.total_damage_healed = 0 # for statistics


    def __joinBattleScene__(self, battle_scene: g.BattleScene):
        self.bs = battle_scene

    def __tickCooldowns__(self):
        print(f"Cooldowns of {self.c.name}: ")
        for i in range(0, 5):
            if self.cooldowns[i] >= 1:
                self.cooldowns[i] -= 1
            print(self.cooldowns[i], end=", ")
        print()

    # check if creature is weak, resistant or immune to type of status or attack
    # returned damage modifier will reflect the result
    def __checkTypeRelationship__(self, type: Type) -> float:

        # break out of checks if confirmed weakness/resistance/immunity
        damage_modifier = 1
        modifier = False
        for t in self.c.types:
            for w in t.weaknesses:
                if type == w:
                    modifier = True
                    damage_modifier = 1.2
                    break
            if modifier: break
            for r in t.resistances:
                if type == r:
                    modifier = True
                    damage_modifier = 0.8
                    break
            if modifier: break
            for i in t.immunities:
                if type == i:
                    modifier = True
                    damage_modifier = 0
                    break
            if modifier: break
        if not testing_wout_type:
            return damage_modifier # normal
        else:
            return 1 # testing balance w/out type relationships

    @staticmethod
    def __checkTypesWeakness__(type1: Type, type2: Type) -> bool:
        for w in type1.weaknesses:
            if w == type2:
                return True
        return False

    # extinguishes effects
    def __checkForExtinguishing__(self, type: Type):
        if type is not all_types["PHYSICAL"]: # physical type does not extinguish
            # extinguishing functionality
            # for element in list doesn't work here properly
            # list is dynamically modified when status is expired
            i = 0
            if testing_wout_type:
                num_of_statuses = 0 # testing balance w/out type relationships
            else:
                num_of_statuses = len(self.active_statuses)
            while i < num_of_statuses:
                so = self.active_statuses[i]

                # check for weakness
                if self.__checkTypesWeakness__(so.se.type, type):
                    print(f"Status {so.se.name} extinguished for {self.c.name}")
                    self.active_statuses.remove(so)
                    i -= 1
                    num_of_statuses -= 1
                i += 1

    def __takeDamage__(self, damage: int):

        if damage > 0:
            print(f"{self.c.name} takes {damage} damage!")
            self.bs.__blitBattleText__(f"{self.c.name} TAKES {damage} DAMAGE!")
        elif damage < 0:
            if self.health > 0:
                print(f"{self.c.name} regains {-damage} health!")
                self.bs.__blitBattleText__(f"{self.c.name} REGAINS {-damage} HEALTH!")
                self.total_damage_healed -= damage

        prev_health = self.health

        # apply damage
        self.health -= damage

        # animate health bar and numbers
        if self.bs is not None:
            self.bs.__animateHealth__(self, prev_health)

        # if damage > 0:
            # todo: damage animation
        # elif damage < 0:
            # todo: heal animation

        # check health values: max health, negative health
        if self.health > self.c.health:
            self.health = self.c.health
        if self.health <= 0:
            self.health = 0
            # todo: death event

    def __applyStatus__(self, status_effect: StatusEffect):

        # check the damage modifier
        so = StatusOccurrence(status_effect)
        so.damage_modifier = self.__checkTypeRelationship__(so.se.type)

        print(f"Applied status effect {so.se.name} to {self.c.name}!")

        if so.status_d == 0:
            self.bs.__blitBattleText__(f'"{so.se.name}" APPLIED TO ', f"{self.c.name} FOR THIS TURN!")
        else:
            self.bs.__blitBattleText__(f'"{so.se.name}" APPLIED TO ', f"{self.c.name} FOR {so.status_d} TURN(S)!")
        if so.stun_d == 0:
            self.bs.__blitBattleText__(f'"{so.se.name}" STUNS ', f"{self.c.name} FOR THIS TURN!")
        elif so.stun_d > 0:
            self.bs.__blitBattleText__(f'"{so.se.name}" STUNS ', f"{self.c.name} FOR THE NEXT {so.stun_d} TURN(S)!")

        # actually activate the status
        self.active_statuses.append(so)

    def __checkIfStunned__(self):
        for so in self.active_statuses:
            if so.stun_d >= 0:
                self.isStunned = True
                return
        self.isStunned = False

    def __tickStatus__(self):

        print(f"tickStatus for {self.c.name}:")
        num_of_statuses = len(self.active_statuses)
        n = num_of_statuses # for blit
        i = 0
        j = i + 1 # for blit

        # for element in list doesn't work here properly
        # list is dynamically modified when status is expired
        while i < num_of_statuses:
            if not self.bs.textbox_up: # introduce the textbox
                self.bs.__animateTextbox__(True)

            so = self.active_statuses[i]
            # check for end of status
            if so.status_d <= 0:
                print(f"Status {so.se.name} expired for {self.c.name}")
                self.bs.__blitBattleText__(f'STATUS "{so.se.name}" ', f"EXPIRED FOR {self.c.name} ({j}/{n})")
                self.active_statuses.remove(so)
                i -= 1
                num_of_statuses -= 1
            else:
                print(f"Ticking status {so.se.name} (turns before expired: {so.status_d}|{so.stun_d}) for {self.c.name}...")
                self.bs.__blitBattleText__(f'"{so.se.name}" IS STILL ', f"APPLIED TO {self.c.name} ({j}/{n})")
                so.status_d -= 1

                # activate/deactivate stun
                if so.stun_d >= 0:
                    so.stun_d -= 1

                if so.se.damage_low < so.se.damage_high:
                    tick_damage = random.randrange(so.se.damage_low, so.se.damage_high+1)
                else:
                    tick_damage = so.se.damage_high

                # if it's not a heal, apply modifiers
                if tick_damage > 0:
                    tick_damage = int(tick_damage * so.damage_modifier)
                    # todo: play damage animation
                # elif tick_damage < 0:
                    # todo: play heal animation

                # change health
                self.__takeDamage__(tick_damage)
            i += 1
            j += 1

        # get rid of the textbox
        if self.bs.textbox_up:
            self.bs.__animateTextbox__(False)

    def __makeMove__(self, opponent: CreatureOccurrence, move: Move):

        print(f"{self.c.name} USES {move.name}!")
        self.bs.__animateTextbox__(True)
        move_text = f'{self.c.name} USES "{move.name}"!'
        self.bs.__blitBattleText__(move_text)
        hit_roll = 0

        # creature targets self
        if move.target_self:
            for i in range(0, move.hit_attempts):

                if move.damage_low < move.damage_high:
                    damage = random.randrange(move.damage_low, move.damage_high+1)
                else:
                    damage = move.damage_high
                hit_text = "MOVE CONNECTED!"
                status_chance = move.status_chance
                status_roll = random.randrange(0, 100)

                print(f"{hit_text}")
                if move.hit_attempts == 1:
                    self.bs.__blitBattleText__(f"{hit_text}")
                else:
                    self.bs.__blitBattleText__(f"{hit_text} ({i + 1}/{move.hit_attempts})")

                # status proc
                self.bs.__animateRoll__(status_roll, status_chance, hit_text, True)
                if status_roll > 100 - status_chance:
                    self.__applyStatus__(move.status_effect)
                    self.__checkForExtinguishing__(move.status_effect.type)

                self.__takeDamage__(damage)
                self.__checkForExtinguishing__(move.type)

        # creature targets opponent
        else:
            aim_mod = 0
            damage_mod = 0
            defense_mod = 0
            thorn_mod_low = 0
            thorn_mod_high = 0

            so: StatusOccurrence
            for so in self.active_statuses:
                aim_mod += so.se.aim_mod
                if so.se.damage_mod_type is None:
                    damage_mod += so.se.damage_mod
                elif move.type == so.se.damage_mod_type:
                    damage_mod += so.se.damage_mod
            for so in opponent.active_statuses:
                defense_mod += so.se.defense_mod
                thorn_mod_low += so.se.thorn_damage_low
                thorn_mod_high += so.se.thorn_damage_high

            hit_chance = move.aim + aim_mod - opponent.c.defense - defense_mod
            damage_multiplier = opponent.__checkTypeRelationship__(move.type)

            for i in range(0, move.hit_attempts):
                hit_roll = random.randrange(0, 100)

                if damage_multiplier == 0:
                    effectiveness_text = "IT HAD NO EFFECT!"
                elif damage_multiplier < 1:
                    effectiveness_text = "IT'S NOT VERY EFFECTIVE!"
                elif damage_multiplier > 1:
                    effectiveness_text = "IT'S SUPER EFFECTIVE!"
                else:
                    effectiveness_text = "IT'S EFFECTIVE!"

                # move connects
                if hit_roll > 100 - hit_chance:
                    if move.damage_low < move.damage_high:
                        damage = int((random.randrange(move.damage_low, move.damage_high+1) + damage_mod) * damage_multiplier)
                    else:
                        damage = int((move.damage_high + damage_mod) * damage_multiplier)
                    hit_text = f"TARGET HIT!"

                # graze or miss
                else:
                    if move.damage_low < move.damage_high:
                        damage = int((random.randrange(move.damage_low, move.damage_high+1) + damage_mod - move.damage_low) * damage_multiplier)
                    else:
                        damage = 0
                    # teensy extra miss chance
                    damage -= 1
                    if damage > 0:
                        hit_text = f"TARGET GRAZED!"
                    else:
                        hit_text = f"TARGET MISSED!"

                # prevent being healed by an enemy when he shoots fire at you (yeah, that happened)
                if damage < 0:
                    damage = 0

                if i > 0: # do not repeat "USES" text in roll animation
                    move_text = ''
                self.bs.__animateRoll__(hit_roll, hit_chance, move_text, False)
                if hit_roll > 100 - hit_chance:
                    print(f"{hit_text} ({hit_roll}|{hit_chance})\n{effectiveness_text}")
                    if move.hit_attempts == 1:
                        self.bs.__blitBattleText__(f"{hit_text}", f"{effectiveness_text}")
                    else:
                        self.bs.__blitBattleText__(f"{hit_text} ({i + 1}/{move.hit_attempts})", f"{effectiveness_text}")
                else:
                    print(f"{hit_text} ({hit_roll}|{hit_chance})")
                    if move.hit_attempts == 1:
                        self.bs.__blitBattleText__(f"{hit_text}")
                    else:
                        self.bs.__blitBattleText__(f"{hit_text} ({i + 1}/{move.hit_attempts})")

                opponent.__takeDamage__(damage)
                opponent.__checkForExtinguishing__(move.type)

                if hit_roll > 100 - hit_chance and move.status_effect is not None:
                    status_multiplier = opponent.__checkTypeRelationship__(move.status_effect.type)
                    status_chance = int(move.status_chance * status_multiplier)
                    status_roll = random.randrange(0, 100)
                    # status proc
                    self.bs.__animateRoll__(status_roll, status_chance, "", True)
                    if status_roll > 100 - status_chance:
                        opponent.__applyStatus__(move.status_effect)
                        opponent.__checkForExtinguishing__(move.status_effect.type)
                    else:
                        print(f"Missed status effect {move.status_effect.name}!")

            # thorn calculations and appliance
            if thorn_mod_low < thorn_mod_high:
                thorn_damage = random.randrange(thorn_mod_low, thorn_mod_high + 1)
            else:
                thorn_damage = thorn_mod_high

            if thorn_damage > 0: # take damage
                print(f"{opponent.c.name} retaliates!")
                self.bs.__blitBattleText__(f"{opponent.c.name} RETALIATES!")
                self.__takeDamage__(thorn_damage)
            elif thorn_mod_low < 0 and hit_roll > 100 - hit_chance: # heal yourself if you got a hit
                print(f"{self.c.name} leeches health from it's opponent!")
                self.bs.__blitBattleText__(f"{self.c.name} leeches health from it's opponent!")
                self.__takeDamage__(thorn_damage)

        # textbox out
        self.bs.__animateTextbox__(False)


# dictionaries of content
all_types = {
    "FIRE": Type("FIRE"),
    "PHYSICAL": Type("PHYSICAL"),
    "FLYING": Type("FLYING"),
    "ELECTRIC": Type("ELECTRIC"),
    "WATER": Type("WATER"),
    "PSYCHIC": Type("PSYCHIC"),
    "GHOST": Type("GHOST"),
    "WIND": Type("WIND"),
    "NULLIFY": Type("NULLIFY"),
    "VAMPIRIC": Type("VAMPIRIC"),
    "MAGIC": Type("MAGIC"),
    "GRASS": Type("GRASS")
}

all_types["FIRE"].__addResistances__(all_types["FIRE"])
all_types["FIRE"].__addWeakness__(all_types["WATER"])
all_types["FIRE"].__addResistances__(all_types["GRASS"])

all_types["ELECTRIC"].__addResistances__(all_types["ELECTRIC"])
all_types["ELECTRIC"].__addResistances__(all_types["WATER"])

all_types["WATER"].__addResistances__(all_types["WATER"])
all_types["WATER"].__addResistances__(all_types["FIRE"])
all_types["WATER"].__addWeakness__(all_types["ELECTRIC"])
all_types["WATER"].__addWeakness__(all_types["GRASS"])

all_types["PSYCHIC"].__addResistances__(all_types["PSYCHIC"])

all_types["GHOST"].__addImmunities__(all_types["PHYSICAL"])
all_types["GHOST"].__addWeakness__(all_types["PSYCHIC"])

all_types["WIND"].__addResistances__(all_types["WIND"])

all_types["VAMPIRIC"].__addResistances__(all_types["VAMPIRIC"])

all_types["MAGIC"].__addResistances__(all_types["MAGIC"])
all_types["MAGIC"].__addResistances__(all_types["FIRE"])
all_types["MAGIC"].__addResistances__(all_types["WATER"])
all_types["MAGIC"].__addResistances__(all_types["ELECTRIC"])
all_types["MAGIC"].__addResistances__(all_types["PSYCHIC"])
all_types["MAGIC"].__addResistances__(all_types["GRASS"])
all_types["MAGIC"].__addWeakness__(all_types["PHYSICAL"])

all_types["GRASS"].__addResistances__(all_types["GRASS"])
all_types["GRASS"].__addWeakness__(all_types["FIRE"])
all_types["GRASS"].__addResistances__(all_types["WATER"])

all_types["FIRE"].__addWeakness__(all_types["NULLIFY"])
all_types["PHYSICAL"].__addWeakness__(all_types["NULLIFY"])
all_types["FLYING"].__addWeakness__(all_types["NULLIFY"])
all_types["ELECTRIC"].__addWeakness__(all_types["NULLIFY"])
all_types["WATER"].__addWeakness__(all_types["NULLIFY"])
all_types["PSYCHIC"].__addWeakness__(all_types["NULLIFY"])
all_types["GHOST"].__addWeakness__(all_types["NULLIFY"])
all_types["WIND"].__addWeakness__(all_types["NULLIFY"])
all_types["VAMPIRIC"].__addWeakness__(all_types["NULLIFY"])
all_types["MAGIC"].__addWeakness__(all_types["NULLIFY"])
all_types["GRASS"].__addWeakness__(all_types["NULLIFY"])

all_status_effects = {
    # FRAGONITE THE FIRE DRAGON
    "BURNING":
        StatusEffect(name="BURNING", type=all_types["FIRE"], damage_low=2, damage_high=2,
                     aim_mod=-4, defense_mod=0, damage_mod=0, damage_mod_type=None,
                     status_duration=3, stun_duration=-1,
                     thorn_damage_low=0, thorn_damage_high=0),
    "WARMING":
        StatusEffect(name="WARMING", type=all_types["FIRE"], damage_low=-4, damage_high=-3,
                     aim_mod=0, defense_mod=0, damage_mod=0, damage_mod_type=None,
                     status_duration=4, stun_duration=-1,
                     thorn_damage_low=0, thorn_damage_high=0),
    "AIRBORNE":
        StatusEffect(name="AIRBORNE", type=all_types["FLYING"], damage_low=0, damage_high=0,
                     aim_mod=20, defense_mod=50, damage_mod=1, damage_mod_type=all_types["FIRE"],
                     status_duration=1, stun_duration=-1,
                     thorn_damage_low=0, thorn_damage_high=0),
    "BITING FLAMES":
        StatusEffect(name="BITING FLAMES", type=all_types["FIRE"], damage_low=0, damage_high=0,
                     aim_mod=0, defense_mod=0, damage_mod=0, damage_mod_type=None,
                     status_duration=0, stun_duration=-1,
                     thorn_damage_low=20, thorn_damage_high=24),

    # SCHONIPS THE SHOCK SNAKE
    "ELECTRIC FORTIFICATION":
        StatusEffect(name="ELECTRIC FORTIFICATION", type=all_types["ELECTRIC"], damage_low=0, damage_high=0,
                     aim_mod=0, defense_mod=0, damage_mod=2, damage_mod_type=all_types["ELECTRIC"],
                     status_duration=3, stun_duration=-1,
                     thorn_damage_low=2, thorn_damage_high=6),
    "SHOCKED":
        StatusEffect(name="SHOCKED", type=all_types["ELECTRIC"], damage_low=0, damage_high=0,
                     aim_mod=0, defense_mod=-5, damage_mod=-1, damage_mod_type=None,
                     status_duration=3, stun_duration=1,
                     thorn_damage_low=0, thorn_damage_high=0),
    "SNAKE REGENERATION":
        StatusEffect(name="SNAKE REGENERATION", type=all_types["PHYSICAL"], damage_low=-3, damage_high=-2,
                     aim_mod=0, defense_mod=5, damage_mod=0, damage_mod_type=None,
                     status_duration=6, stun_duration=-1,
                     thorn_damage_low=0, thorn_damage_high=0),

    # PSAWARCA THE PSYCHIC WATER ORCA
    "MENTAL IMPAIRMENT":
        StatusEffect(name="MENTAL IMPAIRMENT", type=all_types["PSYCHIC"], damage_low=0, damage_high=0,
                     aim_mod=-10, defense_mod=-5, damage_mod=-1, damage_mod_type=None,
                     status_duration=1, stun_duration=-1,
                     thorn_damage_low=0, thorn_damage_high=0),
    "WET":
        StatusEffect(name="WET", type=all_types["WATER"], damage_low=0, damage_high=0,
                     aim_mod=0, defense_mod=-5, damage_mod=-3, damage_mod_type=all_types["FIRE"],
                     status_duration=2, stun_duration=-1,
                     thorn_damage_low=0, thorn_damage_high=0),
    "PSYCHIC SHIELD":
        StatusEffect(name="PSYCHIC SHIELD", type=all_types["PSYCHIC"], damage_low=0, damage_high=0,
                     aim_mod=0, defense_mod=25, damage_mod=0, damage_mod_type=None,
                     status_duration=3, stun_duration=-1,
                     thorn_damage_low=2, thorn_damage_high=3),

    # SHIGOWI THE WIND SHAPESHIFTER
    "HIDDEN BY VOID":
        StatusEffect(name="HIDDEN BY VOID", type=all_types["GHOST"], damage_low=0, damage_high=0,
                     aim_mod=0, defense_mod=400, damage_mod=0, damage_mod_type=None,
                     status_duration=0, stun_duration=-1,
                     thorn_damage_low=4, thorn_damage_high=8),
    "TRIPPED":
        StatusEffect(name="TRIPPED", type=all_types["PHYSICAL"], damage_low=0, damage_high=4,
                     aim_mod=0, defense_mod=0, damage_mod=0, damage_mod_type=None,
                     status_duration=0, stun_duration=0,
                     thorn_damage_low=0, thorn_damage_high=0),
    "NULLIFICATION":
        StatusEffect(name="NULLIFICATION", type=all_types["NULLIFY"], damage_low=0, damage_high=0,
                     aim_mod=0, defense_mod=10, damage_mod=0, damage_mod_type=None,
                     status_duration=1, stun_duration=1,
                     thorn_damage_low=20, thorn_damage_high=30),

    # BAMAT THE LARGE MAGICAL BAT
    "VAMPIRIC PHEROMONES":
        StatusEffect(name="VAMPIRIC PHEROMONES", type=all_types["VAMPIRIC"], damage_low=0, damage_high=0,
                     aim_mod=0, defense_mod=-10, damage_mod=0, damage_mod_type=None,
                     status_duration=3, stun_duration=-1,
                     thorn_damage_low=-6, thorn_damage_high=-4),
    "HUNGER":
        StatusEffect(name="HUNGER", type=all_types["VAMPIRIC"], damage_low=1, damage_high=2,
                     aim_mod=-2, defense_mod=-2, damage_mod=0, damage_mod_type=None,
                     status_duration=9, stun_duration=-1,
                     thorn_damage_low=0, thorn_damage_high=0),
    "BLIND":
        StatusEffect(name="BLIND", type=all_types["MAGIC"], damage_low=0, damage_high=0,
                     aim_mod=-20, defense_mod=-10, damage_mod=-1, damage_mod_type=None,
                     status_duration=2, stun_duration=1,
                     thorn_damage_low=0, thorn_damage_high=0),
    "MAGIC SHIELD":
        StatusEffect(name="MAGIC SHIELD", type=all_types["MAGIC"], damage_low=-2, damage_high=0,
                     aim_mod=0, defense_mod=5, damage_mod=0, damage_mod_type=None,
                     status_duration=4, stun_duration=-1,
                     thorn_damage_low=0, thorn_damage_high=3),
}

all_moves = {
    # FRAGONIRE THE FIRE DRAGON
    "FIRE BREATH":
        Move(name="FIRE BREATH",
             type=all_types["FIRE"], speed=3, target_self=False,
             damage_low=3, damage_high=5, aim=80, hit_attempts=3,
             status_effect=all_status_effects["BURNING"], status_chance=70, cooldown=2),
    "DRAGON CLAW":
        Move(name="DRAGON CLAW",
             type=all_types["PHYSICAL"], speed=3, target_self=False,
             damage_low=8, damage_high=16, aim=95, hit_attempts=1,
             status_effect=None, status_chance=0, cooldown=1),
    "WARMTH":
        Move(name="WARMTH",
             type=all_types["FIRE"], speed=2, target_self=True,
             damage_low=-4, damage_high=-3, aim=200, hit_attempts=1,
             status_effect=all_status_effects["WARMING"], status_chance=100, cooldown=5),
    "FLIGHT":
        Move(name="FLIGHT",
             type=all_types["FLYING"], speed=4, target_self=True,
             damage_low=0, damage_high=0, aim=200, hit_attempts=1,
             status_effect=all_status_effects["AIRBORNE"], status_chance=100, cooldown=2),
    "FIREWALL":
        Move(name="FIREWALL",
             type=all_types["FIRE"], speed=5, target_self=True,
             damage_low=0, damage_high=0, aim=200, hit_attempts=1,
             status_effect=all_status_effects["BITING FLAMES"], status_chance=100, cooldown=7),

    # SCHONIPS THE SHOCK SNAKE
    "SNAKE BITE":
        Move(name="SNAKE BITE",
             type=all_types["PHYSICAL"], speed=5, target_self=False,
             damage_low=6, damage_high=12, aim=115, hit_attempts=1,
             status_effect=None, status_chance=0, cooldown=1),
    "ELECTRIFICATION":
        Move(name="ELECTRIFICATION",
             type=all_types["ELECTRIC"], speed=2, target_self=True,
             damage_low=0, damage_high=0, aim=200, hit_attempts=1,
             status_effect=all_status_effects["ELECTRIC FORTIFICATION"], status_chance=100, cooldown=2),
    "ELECTRIC DISCHARGE":
        Move(name="ELECTRIC DISCHARGE",
             type=all_types["ELECTRIC"], speed=4, target_self=False,
             damage_low=4, damage_high=8, aim=80, hit_attempts=1,
             status_effect=all_status_effects["SHOCKED"], status_chance=100, cooldown=6),
    "SHED SKIN":
        Move(name="SHED SKIN",
             type=all_types["PHYSICAL"], speed=2, target_self=True,
             damage_low=1, damage_high=1, aim=200, hit_attempts=1,
             status_effect=all_status_effects["SNAKE REGENERATION"], status_chance=100, cooldown=7),
    "SHOCK SCREAM":
        Move(name="SHOCK SCREAM",
             type=all_types["ELECTRIC"], speed=3, target_self=False,
             damage_low=4, damage_high=6, aim=90, hit_attempts=3,
             status_effect=None, status_chance=0, cooldown=1),

    # PSAWARCA THE PSYCHIC WATER ORCA
    "PSYCHIC CHALLENGE":
        Move(name="PSYCHIC CHALLENGE",
             type=all_types["PSYCHIC"], speed=3, target_self=False,
             damage_low=2, damage_high=6, aim=80, hit_attempts=3,
             status_effect=all_status_effects["MENTAL IMPAIRMENT"], status_chance=100, cooldown=2),
    "WATER CANNON":
        Move(name="WATER CANNON",
             type=all_types["WATER"], speed=3, target_self=False,
             damage_low=8, damage_high=16, aim=90, hit_attempts=1,
             status_effect=all_status_effects["WET"], status_chance=100, cooldown=2),
    "ILLUSORY SHIELDING":
        Move(name="ILLUSORY SHIELDING",
             type=all_types["PSYCHIC"], speed=4, target_self=True,
             damage_low=0, damage_high=0, aim=200, hit_attempts=1,
             status_effect=all_status_effects["PSYCHIC SHIELD"], status_chance=100, cooldown=5),
    "MIRACLE REGENERATION":
        Move(name="MIRACLE REGENERATION",
             type=all_types["PSYCHIC"], speed=2, target_self=True,
             damage_low=-5, damage_high=0, aim=200, hit_attempts=5,
             status_effect=None, status_chance=0, cooldown=5),
    "WATER WAVE":
        Move(name="WATER WAVE",
             type=all_types["WATER"], speed=4, target_self=False,
             damage_low=12, damage_high=14, aim=80, hit_attempts=1,
             status_effect=all_status_effects["WET"], status_chance=100, cooldown=2),

    # SHIGOWI THE WIND GHOST SHAPESHIFTER
    "PHANTOM JAVELINS":
        Move(name="PHANTOM JAVELINS", type=all_types["GHOST"], speed=3, target_self=False,
             damage_low=4, damage_high=8, aim=75, hit_attempts=3,
             status_effect=None, status_chance=0, cooldown=1),
    "ESCAPE TO VOID":
        Move(name="ESCAPE TO VOID", type=all_types["GHOST"], speed=5, target_self=True,
             damage_low=-8, damage_high=-4, aim=200, hit_attempts=1,
             status_effect=all_status_effects["HIDDEN BY VOID"], status_chance=100, cooldown=3),
    "TRIP OVER":
        Move(name="TRIP OVER", type=all_types["WIND"], speed=4, target_self=False,
             damage_low=2, damage_high=6, aim=100, hit_attempts=1,
             status_effect=all_status_effects["TRIPPED"], status_chance=90, cooldown=3),
    "HURRICANE":
        Move(name="HURRICANE", type=all_types["WIND"], speed=1, target_self=False,
             damage_low=12, damage_high=24, aim=85, hit_attempts=1,
             status_effect=all_status_effects["TRIPPED"], status_chance=100, cooldown=3),
    "RESET VOID":
        Move(name="RESET VOID", type=all_types["NULLIFY"], speed=5, target_self=True,
             damage_low=4, damage_high=4, aim=200, hit_attempts=1,
             status_effect=all_status_effects["NULLIFICATION"], status_chance=100, cooldown=6),

    # BAMAT THE LARGE MAGICAL BAT
    "BAT BITE":
        Move(name="BAT BITE", type=all_types["PHYSICAL"], speed=3, target_self=False,
             damage_low=8, damage_high=16, aim=85, hit_attempts=1,
             status_effect=None, status_chance=0, cooldown=0),
    "DROP OF BLOOD":
        Move(name="DROP OF BLOOD", type=all_types["VAMPIRIC"], speed=5, target_self=False,
             damage_low=1, damage_high=1, aim=200, hit_attempts=1,
             status_effect=all_status_effects["VAMPIRIC PHEROMONES"], status_chance=100, cooldown=6),
    "STARVE OPPONENT":
        Move(name="STARVE OPPONENT", type=all_types["VAMPIRIC"], speed=3, target_self=False,
             damage_low=0, damage_high=0, aim=110, hit_attempts=1,
             status_effect=all_status_effects["HUNGER"], status_chance=100, cooldown=3),
    "BLINDING LIGHT":
        Move(name="BLINDING LIGHT", type=all_types["MAGIC"], speed=2, target_self=False,
             damage_low=4, damage_high=8, aim=110, hit_attempts=1,
             status_effect=all_status_effects["BLIND"], status_chance=80, cooldown=7),
    "MAGICAL REINFORCEMENT":
        Move(name="MAGICAL REINFORCEMENT", type=all_types["MAGIC"], speed=2, target_self=True,
             damage_low=0, damage_high=0, aim=200, hit_attempts=1,
             status_effect=all_status_effects["MAGIC SHIELD"], status_chance=100, cooldown=0),

}

all_creatures = {
    "FRAGONIRE":
        Creature(id=0, name="FRAGONIRE", desc="The Fire Dragon Fragonire",
                 health=60, defense=0, move1=all_moves["FIRE BREATH"], move2=all_moves["DRAGON CLAW"],
                 move3=all_moves["WARMTH"], move4=all_moves["FLIGHT"], move5=all_moves["FIREWALL"],
                 types=(all_types["FIRE"], all_types["PHYSICAL"])),
    "SCHONIPS":
        Creature(id=1, name="SCHONIPS", desc="The Shock Snake Schonips",
                 health=45, defense=20, move1=all_moves["SNAKE BITE"], move2=all_moves["ELECTRIFICATION"],
                 move3=all_moves["ELECTRIC DISCHARGE"], move4=all_moves["SHED SKIN"], move5=all_moves["SHOCK SCREAM"],
                 types=(all_types["ELECTRIC"], all_types["PHYSICAL"])),
    "PSAWARCA":
        Creature(id=2, name="PSAWARCA", desc="The Psychic Water Orca Psawarca",
                 health=65, defense=0, move1=all_moves["PSYCHIC CHALLENGE"], move2=all_moves["WATER CANNON"],
                 move3=all_moves["ILLUSORY SHIELDING"], move4=all_moves["MIRACLE REGENERATION"], move5=all_moves["WATER WAVE"],
                 types=(all_types["PSYCHIC"], all_types["WATER"], all_types["PHYSICAL"])),

    "SHIGOWI":
        Creature(id=3, name="SHIGOWI", desc="The Wind Shapeshifter Shigowi",
                 health=40, defense=25, move1=all_moves["PHANTOM JAVELINS"], move2=all_moves["ESCAPE TO VOID"],
                 move3=all_moves["TRIP OVER"], move4=all_moves["HURRICANE"], move5=all_moves["RESET VOID"],
                 types=(all_types["GHOST"], all_types["WIND"])),

    "BAMAT":
        Creature(id=4, name="BAMAT", desc="The Large Magical Bat Bamat",
                 health=75, defense=-10, move1=all_moves["BAT BITE"], move2=all_moves["DROP OF BLOOD"],
                 move3=all_moves["STARVE OPPONENT"], move4=all_moves["BLINDING LIGHT"], move5=all_moves["MAGICAL REINFORCEMENT"],
                 types=(all_types["VAMPIRIC"], all_types["MAGIC"], all_types["PHYSICAL"]))
}

