from __future__ import annotations  # type hinting instance of class to it's own functions
import random  # random damage, status chance and hit chance


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

    # a type this type of creature is resilient to - deals less damage, less status chance
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
                 status_duration: int = 0, stun_duration: int = 0,
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
        self.status_duration = status_duration
        # stun has a separate duration from the rest of effects and it disables all moves
        self.stun_duration = stun_duration
        # thorn damage means the damage taken by attacker of the creature under status
        # thorn damage has a range
        self.thorn_damage_low = thorn_damage_low
        self.thorn_damage_high = thorn_damage_high
        # todo: extinguishers functionality
        self.extinguishers = []

    # types of moves that remove the status effect
    # separate from weaknesses for more possibilities
    # status can be removed by either party - oneself or opponent
    def __addExtinguisher__(self, extinguisher: Type):
        self.extinguishers.append(extinguisher)


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

    def __init__(self, name: str, desc: str, health: int, defense: int,
                 move1: Move, move2: Move, move3: Move, move4: Move, move5: Move,
                 types: tuple[Type, ...]):
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
        self.cooldowns = [0, 0, 0, 0, 0]

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
                    damage_modifier = 1.5
                    break
            if modifier: break
            for r in t.resistances:
                if type == r:
                    modifier = True
                    damage_modifier = 0.67
                    break
            if modifier: break
            for i in t.immunities:
                if type == i:
                    modifier = True
                    damage_modifier = 0
                    break
            if modifier: break
        return damage_modifier

    def __takeDamage__(self, damage: int):

        if damage > 0:
            print(f"{self.c.name} takes {damage} damage!")
        elif damage < 0:
            if self.health > 0:
                print(f"{self.c.name} regains {-damage} health!")

        # apply damage
        self.health -= damage

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
        so = StatusOccurrence(status_effect)
        so.damage_modifier = self.__checkTypeRelationship__(so.se.type)
        self.active_statuses.append(so)

    def __checkIfStunned__(self):
        for so in self.active_statuses:
            if so.stun_d >= 1:
                self.isStunned = True
                return
        self.isStunned = False

    def __tickStatus__(self):

        print(f"tickStatus for {self.c.name}:")

        num_of_statuses = len(self.active_statuses)
        i = 0

        # for element in list doesn't work here properly
        # list is dynamically modified when status is expired
        while i < num_of_statuses:
            so = self.active_statuses[i]

            # check for end of status
            if so.status_d <= 0:
                print(f"Status {so.se.name} expired for {self.c.name}")
                self.active_statuses.remove(so)
                i -= 1
                num_of_statuses -= 1
            else:
                print(f"Ticking status {so.se.name} (turns before expired: {so.status_d}|{so.stun_d}) for {self.c.name}...")
                so.status_d -= 1

                # activate/deactivate stun
                if so.stun_d >= 1:
                    so.stun_d -= 1

                if so.se.damage_low != so.se.damage_high:
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

    def __makeMove__(self, opponent: CreatureOccurrence, move: Move):

        print(f"{self.c.name} uses {move.name}!")
        # creature targets self
        if move.target_self:
            for i in range(0, move.hit_attempts):
                if move.damage_low != move.damage_high:
                    damage = random.randrange(move.damage_low, move.damage_high+1)
                else:
                    damage = move.damage_high
                hit_text = "Move connected!"
                effectiveness_text = "It's effective!"
                status_chance = move.status_chance
                status_roll = random.randrange(0, 100)

                # status proc
                if status_roll < status_chance:
                    self.__applyStatus__(move.status_effect)

                print(f"{hit_text} ")

                self.__takeDamage__(damage)

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

            for i in range(0, move.hit_attempts):
                hit_roll = random.randrange(0, 100)

                damage_multiplier = opponent.__checkTypeRelationship__(move.type)
                if damage_multiplier == 0:
                    effectiveness_text = "It had no effect!"
                elif damage_multiplier < 1:
                    effectiveness_text = "It's not very effective!"
                elif damage_multiplier > 1:
                    effectiveness_text = "It's super effective!"
                else:
                    effectiveness_text = "It's effective!"

                # move connects
                if hit_roll < hit_chance:
                    if move.damage_low != move.damage_high:
                        damage = int((random.randrange(move.damage_low, move.damage_high+1) + damage_mod) * damage_multiplier)
                    else:
                        damage = int((move.damage_high + damage_mod) * damage_multiplier)
                    hit_text = "Hit!"
                    if move.status_effect is not None:
                        status_multiplier = opponent.__checkTypeRelationship__(move.status_effect.type)
                        status_chance = move.status_chance * status_multiplier
                        status_roll = random.randrange(0, 100)
                        # status proc
                        if status_roll < status_chance:
                            print(f"Applied status effect {move.status_effect.name} to {opponent.c.name}! ({status_roll}|{status_chance})")
                            opponent.__applyStatus__(move.status_effect)
                        else:
                            print(f"Missed status effect {move.status_effect.name}! ({status_roll}|{status_chance})")

                # graze or miss
                else:
                    if move.damage_low != move.damage_high:
                        damage = int((random.randrange(move.damage_low, move.damage_high+1) + damage_mod - move.damage_low) * damage_multiplier)
                    else:
                        damage = 0
                    # teensy extra miss chance
                    damage -= 1
                    hit_text = "Grazed!"

                # prevent being healed by an enemy when he shoots fire at you (yeah, that happened)
                if damage < 0:
                    damage = 0
                    hit_text = "Missed!"

                if hit_text != "Missed!":
                    print(f"{hit_text} ({hit_roll}|{hit_chance})\n{effectiveness_text}")
                else:
                    print(f"{hit_text} ({hit_roll}|{hit_chance})")

                opponent.__takeDamage__(damage)

            if thorn_mod_low > 0:
                print(f"{opponent.c.name} retaliates!")
                if thorn_mod_low != thorn_mod_high:
                    thorn_damage = random.randrange(thorn_mod_low, thorn_mod_high + 1)
                else:
                    thorn_damage = thorn_mod_high
                self.__takeDamage__(thorn_damage)



# dictionaries of content
all_types = {
    "FIRE": Type("FIRE"),
    "PHYSICAL": Type("PHYSICAL"),
    "FLYING": Type("FLYING"),
    "ELECTRIC": Type("ELECTRIC"),
}
all_types["FIRE"].__addResistances__(all_types["FIRE"])
all_types["ELECTRIC"].__addResistances__(all_types["ELECTRIC"])

all_status_effects = {
    # FRAGONITE THE FIRE DRAGON
    "BURNING":
        StatusEffect(name="BURNING", type=all_types["FIRE"], damage_low=2, damage_high=2,
                     aim_mod=-4, defense_mod=0, damage_mod=0, damage_mod_type=None,
                     status_duration=3, stun_duration=0,
                     thorn_damage_low=0, thorn_damage_high=0),
    "WARMING":
        StatusEffect(name="WARMING", type=all_types["FIRE"], damage_low=-4, damage_high=-3,
                     aim_mod=0, defense_mod=0, damage_mod=0, damage_mod_type=None,
                     status_duration=4, stun_duration=0,
                     thorn_damage_low=0, thorn_damage_high=0),
    "AIRBORNE":
        StatusEffect(name="AIRBORNE", type=all_types["FLYING"], damage_low=0, damage_high=0,
                     aim_mod=0, defense_mod=50, damage_mod=0, damage_mod_type=None,
                     status_duration=1, stun_duration=0,
                     thorn_damage_low=0, thorn_damage_high=0),
    "BITING FLAMES":
        StatusEffect(name="FIREWALL", type=all_types["FIRE"], damage_low=0, damage_high=0,
                     aim_mod=0, defense_mod=0, damage_mod=0, damage_mod_type=None,
                     status_duration=0, stun_duration=0,
                     thorn_damage_low=16, thorn_damage_high=24),

    # SCHONIPS THE SHOCK SNAKE
    "ELECTRIC FORTIFICATION":
        StatusEffect(name="ELECTRIC FORTIFICATION", type=all_types["ELECTRIC"], damage_low=0, damage_high=0,
                     aim_mod=0, defense_mod=0, damage_mod=2, damage_mod_type=all_types["ELECTRIC"],
                     status_duration=3, stun_duration=0,
                     thorn_damage_low=2, thorn_damage_high=6),
    "SHOCKED":
        StatusEffect(name="SHOCKED", type=all_types["ELECTRIC"], damage_low=0, damage_high=0,
                     aim_mod=0, defense_mod=-10, damage_mod=-2, damage_mod_type=None,
                     status_duration=3, stun_duration=1,
                     thorn_damage_low=0, thorn_damage_high=0),
    "SNAKE REGENERATION":
        StatusEffect(name="SNAKE REGENERATION", type=all_types["PHYSICAL"], damage_low=-4, damage_high=-4,
                     aim_mod=0, defense_mod=10, damage_mod=0, damage_mod_type=None,
                     status_duration=6, stun_duration=0,
                     thorn_damage_low=0, thorn_damage_high=0)

}

all_moves = {
    # FRAGONIRE THE FIRE DRAGON
    "FIRE BREATH":
        Move(name="FIRE BREATH",
             type=all_types["FIRE"], speed=3, target_self=False,
             damage_low=3, damage_high=6, aim=80, hit_attempts=3,
             status_effect=all_status_effects["BURNING"], status_chance=70, cooldown=2),
    "DRAGON CLAW":
        Move(name="DRAGON CLAW",
             type=all_types["PHYSICAL"], speed=3, target_self=False,
             damage_low=8, damage_high=16, aim=95, hit_attempts=1,
             status_effect=None, status_chance=0, cooldown=1),
    "WARMTH":
        Move(name="WARMTH",
             type=all_types["FIRE"], speed=2, target_self=True,
             damage_low=0, damage_high=0, aim=200, hit_attempts=1,
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
             type=all_types["ELECTRIC"], speed=3, target_self=False,
             damage_low=8, damage_high=12, aim=75, hit_attempts=1,
             status_effect=all_status_effects["SHOCKED"], status_chance=100, cooldown=5),
    "SHED SKIN":
        Move(name="SHED SKIN",
             type=all_types["PHYSICAL"], speed=2, target_self=True,
             damage_low=1, damage_high=1, aim=200, hit_attempts=1,
             status_effect=all_status_effects["SNAKE REGENERATION"], status_chance=100, cooldown=8),
    "SHOCK SCREAM":
        Move(name="SHOCK SCREAM",
             type=all_types["ELECTRIC"], speed=3, target_self=False,
             damage_low=4, damage_high=6, aim=80, hit_attempts=3,
             status_effect=None, status_chance=0, cooldown=2),

}

all_creatures = {
    "FRAGONIRE":
        Creature(name="FRAGONIRE", desc="The Fire Dragon Fragonire",
                 health=80, defense=0, move1=all_moves["FIRE BREATH"], move2=all_moves["DRAGON CLAW"],
                 move3=all_moves["WARMTH"], move4=all_moves["FLIGHT"], move5=all_moves["FIREWALL"],
                 types=(all_types["FIRE"], all_types["PHYSICAL"])),
    "SCHONIPS":
        Creature(name="SCHONIPS", desc="The Shock Snake Schonips",
                 health=65, defense=20, move1=all_moves["SNAKE BITE"], move2=all_moves["ELECTRIFICATION"],
                 move3=all_moves["ELECTRIC DISCHARGE"], move4=all_moves["SHED SKIN"], move5=all_moves["SHOCK SCREAM"],
                 types=(all_types["ELECTRIC"], all_types["PHYSICAL"]))
}
