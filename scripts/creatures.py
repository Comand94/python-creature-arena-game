from __future__ import annotations  # type hinting instance of class to it's own functions
from enum import Enum # enum for Speed to limit mistakes on my part
import pygame  # goodies like pygame.image


# type of move's initial damage or status effect
# creature's type is all the types it has on it's moves
class Type:

    def __init__(self, name: str, image: pygame.image):
        self.name = name
        self.image = image
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
# with negative values, damage can heal permanently over time
# with negative values, aim_mod and defense_mod can provide a temporary buff
# with negative values, damage_mod can temporarily weaken attacks of type damage_mod_type
# if damage_mod_type is None, modifier applies to all attack types
# stun has a separate duration from the rest of effects and it disables all moves
class StatusEffect:

    def __init__(self, name: str, type: Type, damage: int = 0, aim_mod: int = 0, defense_mod: int = 0,
                 damage_mod: int = 0, damage_mod_type: Type = None, status_duration: int = 0,
                 stun_duration: int = 0):
        self.name = name
        self.type = type
        self.damage = damage
        self.aim_mod = aim_mod
        self.defense_mod = defense_mod
        self.status_duration = status_duration
        self.stun_duration = stun_duration
        self.damage_mod = damage_mod
        self.damage_mod_type = damage_mod_type
        self.extinguishers = []

    # types of moves that remove the status effect
    # separate from weaknesses for more possibilities
    # status can be removed by either party
    def __addExtinguisher__(self, extinguisher: Type):
        self.extinguishers.append(extinguisher)


# speed determines priority of moves (whether they are made simultaneously with opponent's move, before or after)
class Speed(Enum):
    slowest: 1
    slow: 2
    normal: 3
    fast: 4
    fastest: 5


# each creature has four moves
# aim denotes chance to hit (percentage)
# hit attempts denotes the number of times the move will attempt to hit
# negative damage acts as healing
class Move:
    def __init__(self, name: str, type: Type, speed: Speed = Speed.normal, target_self: bool = False, damage: int = 0,
                 aim: int = 90, hit_attempts: int = 1, status_effect: StatusEffect = None, status_chance: int = 0):
        self.name = name
        self.type = type
        self.speed = speed
        self.target_self = target_self
        self.damage = damage
        self.aim = aim
        if hit_attempts < 1: hit_attempts = 1
        self.hit_attempts = hit_attempts
        self.status_effect = status_effect
        self.status_chance = status_chance


# tbd
# class Creature:

