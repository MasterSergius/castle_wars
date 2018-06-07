#!/usr/bin/env python3
#
# Game "Castle Wars"
#
# Author: Master Sergius <master.sergius@gmail.com>

import copy
import math
import os
import random
import sys
import time

from abc import ABCMeta, abstractmethod

from constants import *


def help():
    """ Show all necessary information to play this game.

    Show help with pagination to fit small screen
    """
    start_row, end_row = 0, HELP_ROWS_PER_PAGE
    help_rows = HELP_STRING.split('\n')
    page = 1
    pages = math.ceil(len(help_rows) // HELP_ROWS_PER_PAGE + 1)
    while start_row < len(help_rows):
        print('\n'.join(help_rows[start_row:end_row]))
        print('\nHelp page %s/%s' % (page, pages))
        help_choice = input("Press Enter to continue or type 'q' to quit help: ")
        os.system('clear')
        if help_choice == 'q':
            break
        start_row += HELP_ROWS_PER_PAGE
        end_row += HELP_ROWS_PER_PAGE
        page += 1


def exit(confirm=False):
    """ Actions to perform on exit. """
    if not confirm:
        sys.exit(0)

    confirm = input('Are you sure you want to exit? (y/n): ')
    if confirm.lower() == 'y':
        sys.exit(0)


def put_substr_in_position(substr, pos, string):
    """Puts substr inside string instead of symbols in defined positions.

    Args:
        - `substr`: str, represents string which must be inserted
        - `pos`: int, position to insert string
        - `string`: str, string which substr must be inserted to

    Return:
        str, new string with replaces symbols with substr
    """
    pos = max(pos, 0)
    pos = min(pos, len(string) - 1)
    return string[:pos] + substr + string[pos+len(substr):]


def get_enemy_army_in_position(position, enemy_armies):
    """Find enemy army in given position.

    Args:
        - `position`: int, LAND position (from 1 to length of LAND)
        - `enemy_armies`: list, list of all spawned enemy armies

    Return:
        instance of Army if it is placed in given position, None otherwise
    """
    for army in enemy_armies:
        if position == army.position:
            return army
    return None


def prettify_number(number):
    """ Prettify long number by separating groups with 3 digits.

    Args:
        - `number`: int

    Return:
        str

    Example:
        >>> prettify_number(10000)
        '10,000'
    """
    return '{:,}'.format(number)


class GameStats(object):

    """ Class designed to keep all game statistic and show after game over.

    This class must be declared before all other classes.
    """

    player = copy.copy(STATISTICS_PARAMS)
    computer = copy.copy(STATISTICS_PARAMS)

    @staticmethod
    def enemy(player_name):
        """Return name of enemy of given player.

        Args:
            - player_name, str

        Return:
            - str, enemy player's name
        """
        return 'player' if player_name == 'computer' else 'computer'

    @staticmethod
    def update_damage_stats(f):
        """ Update damage dealt to units statistics. Decorator.

        Args:
            f: method, which receive damage to units
        """
        def inner(*args):
            player = getattr(GameStats, GameStats.enemy(args[0].owner))
            player['dmg_dealt_to_units'] += args[1]
            return f(*args)
        return inner

    @staticmethod
    def update_castle_damage_stats(f):
        """ Update damage dealt to castle statistics. Decorator.

        Args:
            f: method, which receive damage to castle
        """
        def inner(*args):
            player = getattr(GameStats, GameStats.enemy(args[0].owner))
            player['dmg_dealt_to_castle'] += args[1]
            return f(*args)
        return inner

    @staticmethod
    def update_kills_and_deaths_stats(f):
        """ Update killed units statistics. Decorator.

        Args:
            f: method, which count dead enemy units
        """
        def inner(*args):
            player = getattr(GameStats, args[0].enemy.name)
            dead = f(*args)
            player['kills'] += dead
            return dead
        return inner

    @staticmethod
    def update_gold_stats(f):
        """ Update earned gold statistics. Decorator.

        Args:
            f: method, which add gold to players
        """
        def inner(*args):
            player = getattr(GameStats, args[0].name)
            player['gold_earned'] += args[1]
            return f(*args)
        return inner

    @staticmethod
    def show_statistics():
        """ Print game statistics along with players' names. """
        GameStats.player['name'] = 'player'
        GameStats.computer['name'] = 'computer'
        print(STATISTICS_TEMPLATE % (PLAYER_STATISTICS_TEMPLATE % GameStats.player,
                                     PLAYER_STATISTICS_TEMPLATE % GameStats.computer))


class GameObject(metaclass=ABCMeta):

    """Abstract class which is base class for all game objects."""

    @abstractmethod
    def __init__(self):
        """Method must be overriden in child class."""
        pass

    @GameStats.update_damage_stats
    def get_damage(self, damage):
        """Recieve damage from enemy unit or castle.

        Subtract damage amount from health points.

        Args:
            - `damage`: int, incoming damage
        """
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0

    def regenerate(self):
        """Add unit's regen value to health points."""
        if self.hp < self.max_hp:
            self.hp += self.regen
            if self.hp > self.max_hp:
                self.hp = self.max_hp


class Castle(GameObject):

    """Class represents player's castle."""

    def __init__(self, hp=CASTLE_HP, dmg=0, regen=0, position=0, direction=0,
                 player_name=None):
        self.hp = hp
        self.max_hp = hp
        self.position = position
        self.dmg = dmg
        self.regen = 0
        self.income = 0
        self.direction = direction
        self.target = None
        self.owner = player_name

    def has_target(self):
        """Check if castle has target to attack.

        Return:
            - instance of Army if it has target, None otherwise
        """
        return self.target

    def get_target(self, enemy_armies):
        """ Find target to attack.

        Set self.target to enemy_army if it can be attacked.

        Args:
            - `enemy_armies`: list of all enemy armies

        Return:
            - True if target successfully set, False otherwise
        """
        self.target = get_enemy_army_in_position(self.position, enemy_armies)
        if not self.target:
            self.target = get_enemy_army_in_position(self.position+self.direction, enemy_armies)
        if not self.target:
            self.target = None
            return False
        return True

    def attack(self):
        """ Castle do damage to all units in army """
        if self.has_target():
            for unit in self.target.units:
                unit.get_damage(self.dmg)
            if self.target.hp == 0:
                self.target = None

    @GameStats.update_castle_damage_stats
    def get_damage(self, damage):
        """ Castle receive only small percentage of damage.

        If incoming damage == 0, castle receive damage equals to 1.
        """
        damage = damage * CASTLE_RECEIVE_DAMAGE
        if damage == 0:
            damage = 1

        # Can't use super to separate game stats
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0


class Player(object):

    """ Class designed to store player related data and organise methods """

    def __init__(self, castle=Castle(), player_name='player'):
        self.name = player_name
        self.gold = GOLD
        self.gold_earned = GOLD
        self.income = 0
        self.spawns = 0
        self.kills = 0
        self.deaths = 0
        self.castle = castle
        self.armies = []
        self.unit_hp = UNIT_HP
        self.unit_dmg = UNIT_DMG
        self.unit_speed = UNIT_SPD
        self.unit_attack_speed = UNIT_ATSPD
        self.unit_regen = UNIT_REGEN
        self.unit_hp_lvl = 0
        self.unit_dmg_lvl = 0
        self.unit_speed_lvl = 0
        self.unit_attack_speed_lvl = 0
        self.unit_regen_lvl = 0
        self.unit_price = UNIT_PRICE
        self.unit_gold_reward = REWARD_FOR_KILLING
        self.castle_income = 0
        self.castle_dmg = 0
        self.castle_hp = CASTLE_HP
        self.castle_regen = 0
        self.castle_income_lvl = 0
        self.castle_dmg_lvl = 0
        self.castle_regen_lvl = 0
        self.castle_hp_lvl = 0
        self.player_view = PlayerView(self)

    def spawn_units(self):
        """ Spawn unit from each player spawn with current upgrades.

        Return:
            list, spawned units if it is time, None otherwise
        """
        units = []
        parameters = {'hp': self.unit_hp, 'dmg': self.unit_dmg,
                      'speed': self.unit_speed, 'regen': self.unit_regen,
                      'attack_speed': self.unit_attack_speed,
                      'gold_reward': self.unit_gold_reward,
                      'owner': self.name}
        for unit in range(self.spawns):
            if self.gold >= self.unit_price:
                units.append(Unit(**parameters))
                self.gold -= self.unit_price
            else:
                break
        return units

    def union_armies(self, army1, army2):
        """ Union two armies in one if they are in one position.

        Args:
            - army1: instance of Army
            - army2: instance of Army
        """
        army1.copy_target(army2.target)
        for unit in army1.units:
            army2.units.append(unit)
        self.armies.remove(army1)

    def check_armies_collision(self, army):
        """ Check if given army come to position with other army.

        Args:
            - army: instance or Army
        """
        for other_army in self.armies:
            if not army is other_army and army.position == other_army.position:
                self.union_armies(army, other_army)
                break

    def remove_dead_armies(self):
        """ Remove armies from player if all units are dead. """
        alive = [army for army in self.armies if army.units]
        self.armies = alive[:]

    @GameStats.update_gold_stats
    def add_gold(self, gold):
        """ Add given gold amount to player's total gold.

        Args:
            - `gold`: int, gold to be added
        """
        self.gold += gold
        self.gold_earned += gold

    def not_enough_gold(self):
        """ Print message which inform about lack of gold.

        Wait till player press Enter.
        """
        print("Not enough gold!")
        input("Press Enter to continue")

    def build_spawn(self, count=1):
        """ Build unit spawn.

        Args:
            - `count`: int, amount of spawns to build
        """
        if count == 'max':
            count = self.gold // SPAWN_COST
        elif self.gold < SPAWN_COST * count:
            self.not_enough_gold()
            return

        self.spawns += count
        self.gold -= SPAWN_COST * count;

    def upgrade_units_attr(self, attr, count=1):
        """ Upgrades chosen unit's attribute.
            Unit becomes more expensive with each upgrade.

        Args:
            - `attr`: str, unit's attribute to upgrade
            - `count`: int, amount of upgrades of selected attribute
        """
        if count == 'max':
            count = self.gold // UNIT_UPGRADE_PRICES[attr]
        elif self.gold < UNIT_UPGRADE_PRICES[attr] * count:
            self.not_enough_gold()
            return

        self.__dict__["unit_%s_lvl" % attr] += count
        self.__dict__["unit_%s" % attr] += UNIT_UPGRADES[attr] * count
        self.gold -= UNIT_UPGRADE_PRICES[attr] * count;
        self.unit_price += count * UPGRADE_GOLD_REWARD
        self.unit_gold_reward += count * UPGRADE_GOLD_REWARD

    def upgrade_castle_attr(self, attr, count=1):
        """ Upgrades chosen castle's attribute.

        Args:
            - `attr`: str, castle's attribute to upgrade
            - `count`: int, amount of upgrades of selected attribute
        """
        if count == 'max':
            count = self.gold // CASTLE_UPGRADE_PRICES[attr]
        elif self.gold < CASTLE_UPGRADE_PRICES[attr] * count:
            self.not_enough_gold()
            return

        self.__dict__["castle_%s_lvl" % attr] += count
        self.__dict__["castle_%s" % attr] += CASTLE_UPGRADES[attr] * count
        self.gold -= CASTLE_UPGRADE_PRICES[attr] * count;
        self.castle.__dict__[attr] += CASTLE_UPGRADES[attr] * count
        if attr == 'income':
            self.income += CASTLE_UPGRADES['income'] * count
        if attr == 'hp':
            self.castle.max_hp += CASTLE_UPGRADES['hp'] * count

    def show_upgrades(self):
        """ Show player upgrades. """
        self.player_view.show_upgrades()

    def player_action(self, choice, count):
        """ Perform player's action according to his choice.

        Args:
            - `choice`: str, one character related to menu item
            - `count`: amount of same actions must be performed
        """
        if choice == 'q':
            exit(confirm=True)
        elif choice == 'e':
            return "end_turn"
        elif choice == 'h':
            os.system("clear")
            help()
        elif choice == 's':
            self.show_upgrades()
        elif choice == 'i':
            self.enemy.show_upgrades()
        elif choice == 'b':
            self.build_spawn(count=count)
        elif choice == '1':
            self.upgrade_units_attr('hp', count=count)
        elif choice == '2':
            self.upgrade_units_attr('dmg', count=count)
        elif choice == '3':
            self.upgrade_units_attr('attack_speed', count=count)
        elif choice == '4':
            self.upgrade_units_attr('regen', count=count)
        elif choice == '5':
            self.upgrade_castle_attr('income', count=count)
        elif choice == '6':
            self.upgrade_castle_attr('dmg', count=count)
        elif choice == '7':
            self.upgrade_castle_attr('regen', count=count)
        elif choice == '8':
            self.upgrade_castle_attr('hp', count=count)

    def prompt(self):
        """Ask player to make his game choices.

        Return:
            tuple (choice, count) - parsed user input

        Example:
            b - build one spawn
            b*2 - build two spawns
            b** - build spawns for all available gold
        """
        choice = input("Your choice > ")
        count = 1
        if '**' in choice:
            # all choices - should be one char length
            choice = choice[0]
            count = 'max'
        elif '*' in choice:
            try:
                choice, count = choice.split('*')
                choice = choice.strip()
                count = int(count)
            except:
                print("Wrong input!\n")
                print("Press Enter to Continue")
                return None
        return self.player_action(choice, count)

    def make_turn(self, draw_scene):
        """ Make player's turn.

        Player will be asked to make choice till player choose 'end turn'.
        After this computer will make its turn.
        """
        while True:
            value = self.prompt()
            draw_scene()
            if value == 'end_turn':
                break


class PlayerView(object):

    """ Class designed to provide interface to view player upgrades. """

    def __init__(self, player):
        self.__player = player

    def get_player_stats(self):
        """ Get all player upgrades, buildings and hp.

        Used for building computer strategy. The same info player can see
        on screen.

        Return:
            dict, which represents player stats
        """
        return {'unit_hp': self.__player.unit_hp,
                'unit_hp_lvl': self.__player.unit_hp_lvl,
                'unit_dmg': self.__player.unit_dmg,
                'unit_dmg_lvl': self.__player.unit_dmg_lvl,
                'unit_as': self.__player.unit_attack_speed,
                'unit_as_lvl': self.__player.unit_attack_speed_lvl,
                'unit_regen': self.__player.unit_regen,
                'unit_regen_lvl': self.__player.unit_regen_lvl,
                'castle_income': self.__player.castle_income,
                'castle_income_lvl': self.__player.castle_income_lvl,
                'castle_dmg': self.__player.castle_dmg,
                'castle_dmg_lvl': self.__player.castle_dmg_lvl,
                'castle_regen': self.__player.castle_regen,
                'castle_regen_lvl': self.__player.castle_regen_lvl,
                'castle_hp': self.__player.castle.max_hp,
                'castle_hp_lvl': self.__player.castle_hp_lvl,
                'spawns': self.__player.spawns}

    def show_upgrades(self):
        """ Show player upgrades. """
        player_stats = self.get_player_stats()
        print(UPGRADES_TEMPLATE % player_stats)
        input("\nPress Enter to continue")


class Unit(GameObject):

    """ Class designed to store unit related data and organise methods """

    def __init__(self, hp=UNIT_HP, dmg=UNIT_DMG, speed=UNIT_SPD,
                 attack_speed=UNIT_ATSPD, regen=UNIT_REGEN,
                 gold_reward=REWARD_FOR_KILLING, owner=None):
        self.hp = hp
        self.max_hp = hp
        self.dmg = dmg
        self.speed = speed
        self.attack_speed = attack_speed
        self.regen = regen
        self.attack_rate = ATTACK_RATE if ATTACK_RATE > self.attack_speed else self.attack_speed
        self.target = None
        self.gold_reward = gold_reward
        self.owner = owner


    def has_target(self):
        """ Check if unit has alive target.

        Return:
            True if unit has target and target's hp > 0, False otherwise
        """
        return self.target is not None and self.target.hp

    def set_target(self, target):
        """ Set target to attack.

        Args:
            - `target`: instance of Unit or Castle
        """
        self.target = target

    def attack(self):
        """ Hit target with unit's damage value.

        Unit can attack if its attack rate higher or equal ATTACK_RATE.
        After hit, its attack rate decreased by ATTACK_RATE.
        Unit will hit target until its attack rate become lower than
        ATTACK_RATE.
        """
        while self.attack_rate >= ATTACK_RATE:
            self.target.get_damage(self.dmg)
            self.attack_rate -= ATTACK_RATE
        else:
            self.attack_rate += self.attack_speed

    def refresh_attack_rate(self):
        """ Refresh unit's attack rate.

        This is usually done when battle with enemy army is over.
        """
        self.attack_rate = max(ATTACK_RATE, self.attack_speed)


class Army(object):

    """ Class designed to store army related data and organise methods """

    def __init__(self, position=0, movement=0, units=None,
                 enemy_castle=None, enemy=None):
        self.position = position
        self.movement = movement
        self.units = None
        self.speed = 0
        self.target = None
        self.enemy_castle = enemy_castle
        self.enemy = enemy
        if units:
            self.units = units[:]
            #Consider scenario when players can upgrade units speed
            #self.speed = get_lowest_speed(units)
            self.speed = 1
        else:
            self.units = []

    def move(self):
        """Move army by setting new position."""
        self.position += self.movement * self.speed

    def draw(self, player_name):
        """Return image of army.

        Args:
            - `player_name`: name of army owner

        Return:
            str, string represents image of army
        """
        if self.has_target():
            return ARMY_FIGHTING_PIC[player_name] % len(self.units)
        return ARMY_PIC[player_name] % len(self.units)

    def is_enemy_castle_reachable(self):
        """ Check if army can attack enemy's castle.

        Return:
            True if castle is in neigbour cell, False otherwise
        """
        return abs(self.position-self.enemy_castle.position) <= 1

    def has_target(self):
        """Check if army has target to attack.

        Return:
            instance of Army or Castle if it has target, None otherwise
        """
        if self.target and self.target.hp == 0:
            self.target = None
        return self.target

    def get_target(self, enemy_armies):
        """ Find target for army to fight with.
            Preferable target - enemy's army.

        Args:
            - `enemy_armies`: list of all enemy armies

        Return:
            True if Army or Castle can be attacked, False otherwise
        """
        self.target = get_enemy_army_in_position(self.position, enemy_armies)
        if not self.target:
            self.target = get_enemy_army_in_position(self.position+self.movement, enemy_armies)
            if self.target:
                for unit in self.units:
                    unit.set_target(random.choice(self.target.units))
        if not self.target and self.is_enemy_castle_reachable():
            self.target = self.enemy_castle
            for unit in self.units:
                unit.set_target(self.target)
        if not self.target:
            return False
        return True

    def copy_target(self, other_army_target):
        """ Copy other friendly army's target.

        This method used when two armies union in one army.

        Args:
            - `other_army_target`: instance of Army or Castle, or None
        """
        if isinstance(other_army_target, Army):
            for unit in self.units:
                unit.set_target(random.choice(other_army_target.units))
        if isinstance(other_army_target, Castle):
            for unit in self.units:
                unit.set_target(other_army_target)

    def refresh_units_target(self):
        """ Check if any unit has his target dead. Set new target.
            In case of castle, game ends immediately
        """
        if self.target:
            for unit in self.units:
                if not unit.has_target() and not isinstance(unit.target, Castle):
                    unit.set_target(random.choice(self.target.units))

    def refresh_attack_rate(self):
        """ Refresh units' attack rate when battle is over. """
        for unit in self.units:
            unit.refresh_attack_rate()

    @GameStats.update_kills_and_deaths_stats
    def remove_dead_units(self):
        """ Remove dead units from army.

        Additionally, calculate deads for game statistics.
        """
        alive = []
        dead = 0
        for unit in self.units:
            if unit.hp > 0:
                alive.append(unit)
            else:
                self.give_gold_reward(unit.gold_reward)
                dead += 1
        self.units = alive[:]
        self.enemy.kills += dead
        return dead

    def give_gold_reward(self, gold):
        """ Give gold reward to enemy for dead unit.

        Args:
            - `gold`: int, amount of gold reward for dead unit
        """
        self.enemy.add_gold(gold)

    def regen_units(self):
        """ Regenerate health of all units in army. """
        for unit in self.units:
            unit.regenerate()

    @property
    def hp(self):
        """ Calculate overall units' health points in army.

        Return:
            int - total units' hp
        """
        units_health = 0
        for unit in self.units:
            units_health += unit.hp
        return units_health


class AIPlayer(Player):

    """ Class designed to control AI player, simulate strategy. """

    def random_choice(self, max_rand, strategy):
        """ Simulate computer choice.

        Args:
            - `max_rand`: int, max random integer for current strategy
            - `strategy`: dict, represents possible computer actions

        Return:
            str, randomly selected computer action
        """
        random_number = random.randint(1, max_rand)
        for key in sorted(strategy.keys()):
            if random_number <= key:
                return strategy[key]

    def convert_percentage(self, percentage):
        """ Build correct dict for random choice from percentage.

        For example, there are three actions, first action must be performed
        in 20% of all occurance, second in 50% and third in 30%. So, random from
        1 to 100 should point to correct action. All random numbers 1-20 should
        point to 1st action (20%), next 50 numbers 21-70 (50%) should point to
        2nd action and rest 30 numbers 71-100 - 3rd action.
        Thus, we can build dict with numbers 20, 70, 100 as keys and actions as
        values and compare random number with keys.

        Args:
            - `percentage`: dict, represents computer strategy in percentage

        Return:
            - `dict`, converted percentage to deal with random

        Example:
            percentage = {'spawn':35, 'income':30,
                          'unit_hp':10, 'unit_dmg':10,
                          'unit_attack_speed':10, 'unit_regen':5}

            converted_percentage = {5:'unit_regen', 15:'unit_attack_speed',
                                    25:'unit_dmg', 35: 'unit_hp', 65: 'income',
                                    100: 'spawn'}
        """
        strategy = {}
        number = 0
        for action in sorted(percentage, key=percentage.get):
            number += percentage[action]
            strategy[number] = action
            if number > 100:
                os.system('clear')
                print('Incorrect computer strategy.')
                input('Press Enter to exit.')
                sys.exit(0)
        return strategy


    def build_computer_strategy(self, percentage, gold):
        """Filters possible actions. Leave only those which are affordable.

        After each action computer must rebuild strategy according to gold amount.
        If some action can't be performed because of lack of gold, it will be
        dropped and total amount of percentage will decrease by its percentage.

        Args:
            - `percentage`: dict, represents computer strategy in percentage
            - `gold`: int, amount of computer player's gold

        Return:
            tuple (dict, int) - (converted percentage, total percentage (<=100))
        """
        total_percentage = 0
        filtered_percentage = {}
        for action, percent in percentage.items():
            if COSTS[action] <= gold:
                filtered_percentage[action] = percent
                total_percentage += percent
        return (self.convert_percentage(filtered_percentage), total_percentage)

    def choose_strategy(self, turns_to_spawn):
        """ Choose AI strategy in percentage.

        Build different strategies depending on situation.

        Args:
            - `turns_to_spawn`: int, count of turns to next spawn

        Return:
            dict, represents computer strategy in percentage
        """
        # setup basic strategy
        percentage = {'spawn':25, 'income':45, 'unit_hp':10, 'unit_dmg':10,
                      'unit_attack_speed':10}

        if self.spawns == 0:
            percentage = {'spawn':100}
        elif self.income < 500:
            percentage = {'income':70, 'spawn':20, 'unit_hp':5, 'unit_dmg':3,
                          'unit_attack_speed':1, 'unit_regen':1}
        elif self.income < 5000:
            percentage = {'income':90, 'spawn':5, 'unit_hp':2, 'unit_dmg':1,
                          'unit_attack_speed':1, 'unit_regen':1}
        elif self.income < 10000:
            percentage = {'income':60, 'spawn':10, 'unit_hp':10, 'unit_dmg':10,
                          'unit_attack_speed':9, 'unit_regen':1}
        elif self.unit_hp_lvl < 4:
            percentage = {'spawn':30, 'income':35, 'unit_hp':15,
                          'unit_dmg':10, 'unit_attack_speed':10}
        elif self.spawns > 2:
            percentage = {'spawn':10, 'income':45, 'unit_hp':15,
                          'unit_dmg':15, 'unit_attack_speed':10,
                          'unit_regen':5}

        # improvement
        enemy_stats = self.enemy.get_player_stats()
        enemy_unit_lvl = enemy_stats['unit_hp_lvl'] + \
                         enemy_stats['unit_dmg_lvl'] + \
                         enemy_stats['unit_as_lvl'] + \
                         enemy_stats['unit_regen_lvl']

        if enemy_unit_lvl > 200:
            percentage = {'spawn':10, 'income':50, 'unit_hp':10,
                          'unit_dmg':10, 'unit_attack_speed':10,
                          'unit_regen':10}
        if enemy_unit_lvl > 500:
            percentage = {'spawn':10, 'income':45, 'unit_hp':10,
                          'unit_dmg':10, 'unit_attack_speed':10,
                          'unit_regen':10, 'castle_hp': 5}
        if enemy_unit_lvl > 1000:
            percentage = {'spawn':20, 'income':40, 'unit_hp':10,
                          'unit_dmg':10, 'unit_attack_speed':10,
                          'castle_hp': 10}
        if enemy_unit_lvl > 2000:
            percentage = {'spawn':20, 'income':30, 'unit_hp':10,
                          'unit_dmg':10, 'unit_attack_speed':10,
                          'castle_dmg':5, 'castle_hp': 15}

        # can be done if this is not spawn turn
        if turns_to_spawn > 0:
            percentage = {'income': 100}

        # castle rescue
        if self.castle.hp < CASTLE_HP:
            percentage = {'spawn':10, 'income':10, 'unit_hp':10,
                          'unit_dmg':10, 'unit_attack_speed':10,
                          'castle_dmg':40, 'castle_regen':10}
        if self.castle.hp < CASTLE_HP * 0.9:
            percentage = {'spawn':1, 'income':1, 'unit_hp':1,
                          'unit_dmg':1, 'unit_attack_speed':1,
                          'unit_regen':1, 'castle_dmg':70, 'castle_regen':19,
                          'castle_hp': 5}
        if self.castle.hp < CASTLE_HP * 0.4:
            percentage = {'spawn':10, 'income':5, 'unit_hp':5,
                          'unit_dmg':5, 'unit_attack_speed':5,
                          'unit_regen':5, 'castle_dmg':25, 'castle_regen':20,
                          'castle_hp':20}
        return percentage

    def computer_action(self, turns_to_spawn):
        """ Perform computer action.

        Args:
            - `turns_to_spawn`: int, count of turns to next spawn

        Return:
            bool, False if no actions can be done because of lack of gold,
                  True - otherwise
        """
        prices = [SPAWN_COST]
        prices.extend(list(UNIT_UPGRADE_PRICES.values()))
        prices.extend(list(CASTLE_UPGRADE_PRICES.values()))
        if self.gold < min(prices):
            return False

        percentage = self.choose_strategy(turns_to_spawn)
        strategy, max_rand = self.build_computer_strategy(percentage,
                                                          self.gold)

        choice = self.random_choice(max_rand, strategy)
        if choice == 'spawn':
            self.build_spawn()
        elif choice == 'unit_hp':
            self.upgrade_units_attr('hp')
        elif choice == 'unit_dmg':
            self.upgrade_units_attr('dmg')
        elif choice == 'unit_attack_speed':
            self.upgrade_units_attr('attack_speed')
        elif choice == 'unit_regen':
            self.upgrade_units_attr('regen')
        elif choice == 'income':
            self.upgrade_castle_attr('income')
        elif choice == 'castle_dmg':
            self.upgrade_castle_attr('dmg')
        elif choice == 'castle_regen':
            self.upgrade_castle_attr('regen')
        elif choice == 'castle_hp':
            self.upgrade_castle_attr('hp')
        return True

    def is_enough_gold(self, turns_to_spawn):
        """ Check if computer will have enough gold to spawn units. """
        costs = self.spawns * self.unit_price
        return self.gold + (self.income * turns_to_spawn + 1) > costs

    def make_turn(self, turns_to_spawn):
        """ Simulate AI turn.

        Args:
            - `turns_to_spawn`: int, count of turns before new spawn

        """
        while self.is_enough_gold(turns_to_spawn):
            success = self.computer_action(turns_to_spawn)
            if not success:
                break


class CastleWars(object):

    """ Class designed to control game flow. """

    def __init__(self):
        self.castle_player = Castle(position=0, direction=1, player_name='player')
        self.player = Player(castle=self.castle_player, player_name='player')
        self.castle_computer = Castle(position=DISTANCE+1, direction=-1, player_name='computer')
        self.computer = AIPlayer(castle=self.castle_computer, player_name='computer')
        self.castles = {'player': self.castle_player, 'computer': self.castle_computer}
        self.players = {'player': self.player, 'computer': self.computer}
        self.player.enemy = PlayerView(self.computer)
        self.computer.enemy = PlayerView(self.player)
        self.income_line = INCOME_LINE
        self.player_health_line = HEALTH_LINE
        self.computer_health_line = HEALTH_LINE
        self.spawn_rate = SPAWN_RATE_IN_TURNS

    def put_in_position(self, pic, position, player_name):
        """ Put image of army, health, etc. in apropriate position on screen.

        Args:
            - `pic`: str, picture (image) to put in given position
            - `position`: int, number of cell of land or health line
            - `player_name`: str, player or computer
        """
        if player_name == 'player':
            # number and > or x = 2 symbols
            position = position - len(pic) + 2
        self.warline = put_substr_in_position(pic, position, self.warline)

    def draw_game_field(self):
        """ Draw game field by printing characters on screen. """
        # create appropriate string to show castles' hp
        half = (DISTANCE + len(HOME_PIC) * 2) // 2
        player_castle_hp = ("%" + str(-half) + "s") % int(self.player.castle.hp)
        computer_castle_hp = ("%" + str(half) + "s") % int(self.computer.castle.hp)
        # print string with castles' hp
        print(player_castle_hp + computer_castle_hp)
        # print castles, road and units
        print("%s%s%s" % (HOME_PIC, self.income_line, HOME_PIC))
        self.warline = LAND
        for player_name, player in self.players.items():
            for army in player.armies:
                self.put_in_position(army.draw(player_name), army.position, player_name)
        print(self.warline)
        print(self.player_health_line)
        print(self.computer_health_line, '\n')

    def print_status(self):
        """ Print status line with players stats. """
        status_line = "Gold: %s   Income: %s   Spawns: %s   Kills: %s   Deaths: %s\n"
        print(status_line % (prettify_number(self.player.gold),
                             prettify_number(self.player.income),
                             prettify_number(self.player.spawns),
                             prettify_number(self.player.kills),
                             prettify_number(self.player.deaths)))
        print("Current unit price: %s\tGold needed to spawn all: %s\tTurns to spawn: %s\n" %
              (prettify_number(self.player.unit_price),
               prettify_number(self.player.unit_price * self.player.spawns),
               SPAWN_RATE_IN_TURNS - self.spawn_rate))

    def print_short_help(self):
        """ Print short help with list of possible actions.

        This short help is always visible below game stats.
        """
        print(SHORT_HELP_STRING)

    def spawn_units(self):
        """ Spawn units and create new army. """
        if self.spawn_rate == SPAWN_RATE_IN_TURNS:
            for player_name, player in self.players.items():
                units = player.spawn_units()
                self.spawn_rate = 0
                if units:
                    position = PLAYER_POSITIONS[player_name]
                    movement = PLAYER_MOVEMENTS[player_name]
                    if player_name == 'player':
                        enemy_castle = self.castles['computer']
                        enemy = self.computer
                    else:
                        enemy_castle = self.castles['player']
                        enemy = self.player
                    new_army = Army(position=position, movement=movement,
                                    units=units, enemy_castle=enemy_castle,
                                    enemy=enemy)
                    player.armies.append(new_army)
        else:
            self.spawn_rate += 1

    def add_gold_as_income(self):
        """ Add gold to players as their income. """
        for player_name, player in self.players.items():
            # get income
            player.add_gold(player.income)

    def move_armies(self):
        """ Move players' armies, fight, remove dead armies. """
        enemy_armies = []
        self.player_health_line = HEALTH_LINE
        self.computer_health_line = HEALTH_LINE
        for player_name, player in self.players.items():
            # get list of enemy armies
            if player_name == 'player':
                enemy_armies = self.players['computer'].armies
            else:
                enemy_armies = self.players['player'].armies
            # check for fight
            for army in player.armies:
                # enemy's army is preferable target
                if army.has_target() and isinstance(army.target, Castle):
                    army.get_target(enemy_armies)
                if army.has_target() or army.get_target(enemy_armies):
                    self.fight_tick(army)
                else:
                    army.move()
                    army.refresh_attack_rate()
                    player.check_armies_collision(army)
                if player_name == 'player':
                    self.player_health_line = put_substr_in_position(str(army.hp),
                                                                     army.position,
                                                                     self.player_health_line)
                else:
                    self.computer_health_line = put_substr_in_position(str(army.hp),
                                                                       army.position,
                                                                       self.computer_health_line)
            # check if castle can attack
            if player.castle.has_target() or player.castle.get_target(enemy_armies):
                player.castle.attack()

        for player in self.players.values():
            for army in player.armies:
                # remove dead units and armies
                dead = army.remove_dead_units()
                player.deaths += dead
            player.remove_dead_armies()

    def finish_turn(self):
        """ Finish turn for player and computer.

        Spawn units, move armies, get income, etc.
        """
        self.add_gold_as_income()
        self.spawn_units()

        for tick in range(TIME_TICKS_PER_TURN):
            self.move_armies()
            self.check_game_over()
            # small sleep to simulate animation
            time.sleep(1/TIME_TICKS_PER_TURN)
            self.set_income()
            self.draw_scene()

        # regenerate units' and castles' hp after each turn
        for player in self.players.values():
            for army in player.armies:
                # regenerate units' hp
                army.regen_units()
            # regenerate castle's hp
            player.castle.regenerate()

    def set_income(self):
        """ Set income which include land income and castle income. """
        highest_player_position = 0
        for army in self.player.armies:
            if army.position > highest_player_position:
                highest_player_position = army.position

        # computer direction is reversed
        highest_computer_position = DISTANCE + 1
        for army in self.computer.armies:
            if army.position < highest_computer_position:
                highest_computer_position = army.position

        self.income_line = INCOME_LINE
        self.income_line = ('+' * highest_player_position +
                            self.income_line[highest_player_position:])

        computer_land_length = DISTANCE - highest_computer_position + 1
        self.income_line = (self.income_line[:highest_computer_position-1] +
                            '-' * computer_land_length)
        self.player.income = self.player.castle_income + LAND_INCOME * highest_player_position
        self.computer.income = self.computer.castle_income + LAND_INCOME * computer_land_length

    def fight_tick(self, army):
        """ Perform fight actions per each time tick.

        Args:
            - `army`: instance of Army
        """
        for unit in army.units:
            unit.attack()
        army.refresh_units_target()

    def show_game_stats(self):
        """ Print simple game statistics after game is over. """
        GameStats.show_statistics()

    def game_over(self, message):
        """ Actions to be done on game over.

        Args:
            - `message`: str, win/loose message
        """
        os.system('clear')
        print(message)
        self.show_game_stats()
        input("Press Enter to exit")
        exit()

    def check_game_over(self):
        """ Check if any castle has hp equals 0.
        If yes, game must be ended
        """
        if self.castles['player'].hp == 0:
            self.game_over('You loose!\n')

        if self.castles['computer'].hp == 0:
            self.game_over('You win!\n')

    def draw_scene(self):
        """ Draw scene on each time tick. """
        os.system('clear')
        self.draw_game_field()
        self.print_status()
        self.print_short_help()

    def start(self):
        """ Start and run game in endless loop. """
        while True:
            self.draw_scene()
            self.player.make_turn(self.draw_scene)
            self.computer.make_turn(SPAWN_RATE_IN_TURNS - self.spawn_rate)
            self.finish_turn()


if __name__ == "__main__":
    game = CastleWars()
    game.start()
