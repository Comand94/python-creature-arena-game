from __future__ import annotations  # type hinting instance of class to it's own functions
from enum import Enum  # enumeration for Speed
import random # random damage, status chance and hit chance


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
    def __isNewTypeRelationship__(self, type: Type) -> bool:
        for t in self.weaknesses:
            if t == type: return False
        for t in self.resistances:
            if t == type: return False
        for t in self.immunities:
            if t == type: return False
        return True

    # a type this type of creature is weak to - deals extra damage, more severe penalties
    def __addWeakness__(self, weakness: Type):
        if self.__isNewTypeRelationship__(weakness):
            self.weaknesses.append(weakness)

    # a type this type of creature is resilient to - deals less damage, less severe penalties
    def __addResistances__(self, resistance: Type):
        if self.__isNewTypeRelationship__(resistance):
            self.resistances.append(resistance)

    # a type this type of creature is immune to - deals no damage, does not proc status
    def __addImmunities__(self, immunity: Type):
        if self.__isNewTypeRelationship__(immunity):
            self.immunities.append(immunity)


# a status effect is an affliction or a buff applied over time to a creature
# damage has a range
# with negative values, damage can heal back health permanently over time
# with positive values, aim_mod and defense_mod can provide a temporary buff
# with negative values, damage_mod can temporarily weaken attacks of type damage_mod_type
# if damage_mod_type is None, modifier applies to all attack types
# stun has a separate duration from the rest of effects and it disables all moves
# thorn damage means the status effect will damage the attacker of the creature under status
# thorn damage has a range
class StatusEffect:

    def __init__(self, name: str, type: Type, damage_low: int = 0, damage_high: int = 0,
                 aim_mod: int = 0, defense_mod: int = 0, damage_mod: int = 0, damage_mod_type: Type = None,
                 status_duration: int = 0, stun_duration: int = 0,
                 thorn_damage_low: int = 0, thorn_damage_high: int = 0):
        self.name = name
        self.type = type
        self.damage_low = damage_low
        self.damage_high = damage_high
        self.aim_mod = aim_mod
        self.defense_mod = defense_mod
        self.damage_mod = damage_mod
        self.damage_mod_type = damage_mod_type
        self.status_duration = status_duration
        self.stun_duration = stun_duration
        self.thorn_damage_low = thorn_damage_low
        self.thorn_damage_high = thorn_damage_high
        self.extinguishers = []

    # types of moves that remove the status effect
    # separate from weaknesses for more possibilities
    # status can be removed by either party
    def __addExtinguisher__(self, extinguisher: Type):
        self.extinguishers.append(extinguisher)


# applied status copy
class StatusOccurrence:
    def __init__(self, se: StatusEffect):
        self.se = se
        self.status_d = se.status_duration
        self.stun_d = se.stun_duration


# speed determines priority of moves (whether they are made simultaneously with opponent's move, before or after)
class Speed(Enum):
    SLOWEST: 1
    SLOW: 2
    NORMAL: 3
    FAST: 4
    FASTEST: 5


# each creature has four moves
# negative damage acts as healing
# damage has a range
# aim denotes chance to hit (percentage)
# hit attempts denotes the number of times the move will attempt to hit
# cooldown of 0 means no cooldown, 1 means one turn, etc.
class Move:

    def __init__(self, name: str,
                 type: Type, speed: Speed = Speed.NORMAL, target_self: bool = False,
                 damage_low: int = 0, damage_high: int = 0, aim: int = 90, hit_attempts: int = 1,
                 status_effect: StatusEffect = None, status_chance: int = 0, cooldown: int = 1):
        self.name = name
        self.type = type
        self.speed = speed
        self.target_self = target_self
        self.damage_low = damage_low
        self.damage_high = damage_high
        self.aim = aim
        if hit_attempts < 1: hit_attempts = 1
        self.hit_attempts = hit_attempts
        self.status_effect = status_effect
        self.status_chance = status_chance
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
        self.active_statuses: list[StatusOccurrence, ...]
        self.active_statuses = []
        self.isStunned = False

    def __applyStatus__(self, status_effect: StatusEffect):
        so = StatusOccurrence(status_effect)
        self.active_statuses.append(so)
        self.defense = self.defense + so.se.defense_mod


    def __tickStatus__(self):
        so: StatusOccurrence
        for so in self.active_statuses:
            # activate/deactivate stun
            if so.stun_d >= 1:
                self.isStunned = True
            else:
                self.isStunned = False
            so.stun_d -= 1

            if so.status_d >= 1:
                tick_damage = random.randrange(so.se.damage_low, so.se.damage_high)
                # todo: play animation (dir based on creature's name) depending on whether it healed or took damage
                self.health = self.health - tick_damage

            # end of status
            if so.status_d == 0:
                self.defense = self.defense - so.se.defense_mod
                self.active_statuses.remove(so)
            so.status_d -= 1

    # todo
    def __makeMove__(self, opponent: Creature, move: Move):
        if move.target_self:
            hit_chance = move.aim - self.defense


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
        StatusEffect(name="BURNING", type=all_types["FIRE"], damage_low=1, damage_high=1,
                     aim_mod=-2, defense_mod=0, damage_mod=0, damage_mod_type=None,
                     status_duration=3, stun_duration=0,
                     thorn_damage_low=0, thorn_damage_high=0),
    "WARMING":
        StatusEffect(name="WARMING", type=all_types["FIRE"], damage_low=-6, damage_high=-8,
                     aim_mod=0, defense_mod=0, damage_mod=0, damage_mod_type=None,
                     status_duration=4, stun_duration=0,
                     thorn_damage_low=0, thorn_damage_high=0),
    "AIRBORNE":
        StatusEffect(name="AIRBORNE", type=all_types["FLYING"], damage_low=0, damage_high=0,
                     aim_mod=0, defense_mod=40, damage_mod=0, damage_mod_type=None,
                     status_duration=1, stun_duration=0,
                     thorn_damage_low=0, thorn_damage_high=0),
    "BITING FLAMES":
        StatusEffect(name="FIREWALL", type=all_types["FIRE"], damage_low=0, damage_high=0,
                     aim_mod=0, defense_mod=0, damage_mod=0, damage_mod_type=None,
                     status_duration=1, stun_duration=0,
                     thorn_damage_low=20, thorn_damage_high=30),

    # SCHONIPS THE SHOCK SNAKE
    "ELECTRIC FORTIFICATION":
        StatusEffect(name="ELECTRIC FORTIFICATION", type=all_types["ELECTRIC"], damage_low=0, damage_high=0,
                     aim_mod=0, defense_mod=0, damage_mod=4, damage_mod_type=all_types["ELECTRIC"],
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
             type=all_types["FIRE"], speed=Speed.NORMAL, target_self=False,
             damage_low=2, damage_high=4, aim=70, hit_attempts=4,
             status_effect=all_status_effects["BURNING"], status_chance=80, cooldown=2),
    "DRAGON CLAW":
        Move(name="DRAGON CLAW",
             type=all_types["PHYSICAL"], speed=Speed.NORMAL, target_self=False,
             damage_low=8, damage_high=16, aim=90, hit_attempts=1,
             status_effect=None, status_chance=0, cooldown=1),
    "WARMTH":
        Move(name="WARMTH",
             type=all_types["FIRE"], speed=Speed.SLOW, target_self=True,
             damage_low=0, damage_high=0, aim=200, hit_attempts=1,
             status_effect=all_status_effects["WARMING"], status_chance=100, cooldown=5),
    "FLIGHT":
        Move(name="FLIGHT",
             type=all_types["FLYING"], speed=Speed.FAST, target_self=True,
             damage_low=0, damage_high=0, aim=200, hit_attempts=1,
             status_effect=all_status_effects["AIRBORNE"], status_chance=100, cooldown=1),
    "FIREWALL":
        Move(name="FIREWALL",
             type=all_types["FIRE"], speed=Speed.FASTEST, target_self=True,
             damage_low=0, damage_high=0, aim=200, hit_attempts=1,
             status_effect=all_status_effects["BITING FLAMES"], status_chance=100, cooldown=4),

    # SCHONIPS THE SHOCK SNAKE
    "SNAKE BITE":
        Move(name="SNAKE BITE",
             type=all_types["PHYSICAL"], speed=Speed.FASTEST, target_self=False,
             damage_low=6, damage_high=12, aim=115, hit_attempts=1,
             status_effect=None, status_chance=0, cooldown=1),
    "ELECTRIFICATION":
        Move(name="ELECTRIFICATION",
             type=all_types["ELECTRIC"], speed=Speed.FAST, target_self=True,
             damage_low=0, damage_high=0, aim=200, hit_attempts=1,
             status_effect=all_status_effects["ELECTRIC FORTIFICATION"], status_chance=100, cooldown=2),
    "ELECTRIC DISCHARGE":
        Move(name="ELECTRIC DISCHARGE",
             type=all_types["ELECTRIC"], speed=Speed.NORMAL, target_self=False,
             damage_low=12, damage_high=18, aim=70, hit_attempts=1,
             status_effect=all_status_effects["SHOCKED"], status_chance=100, cooldown=5),
    "SHED SKIN":
        Move(name="SHED SKIN",
             type=all_types["PHYSICAL"], speed=Speed.SLOW, target_self=True,
             damage_low=1, damage_high=1, aim=200, hit_attempts=1,
             status_effect=all_status_effects["SNAKE REGENERATION"], status_chance=100, cooldown=8),
    "SHOCK SCREAM":
        Move(name="SHOCK SCREAM",
             type=all_types["ELECTRIC"], speed=Speed.NORMAL, target_self=False,
             damage_low=4, damage_high=8, aim=80, hit_attempts=3,
             status_effect=None, status_chance=0, cooldown=1),

}

all_creatures = {
    "FRAGONIRE":
        Creature(name="FRAGONIRE", desc="The Fire Dragon Fragonire",
                 health=100, defense=0, move1=all_moves["FIRE BREATH"], move2=all_moves["DRAGON CLAW"],
                 move3=all_moves["WARMTH"], move4=all_moves["FLIGHT"], move5=all_moves["FIREWALL"],
                 types=(all_types["FIRE"], all_types["PHYSICAL"])),
    "SCHONIPS":
        Creature(name="SCHONIPS", desc="The Shock Snake Schonips",
                 health=80, defense=20, move1=all_moves["SNAKE BITE"], move2=all_moves["ELECTRIFICATION"],
                 move3=all_moves["ELECTRIC DISCHARGE"], move4=all_moves["SHED SKIN"], move5=all_moves["SHOCK SCREAM"],
                 types=(all_types["ELECTRIC"], all_types["PHYSICAL"]))
}
