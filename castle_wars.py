#!/usr/bin/env python3
#
# Game "Castle Wars"
#
# Author: Master Sergius <master.sergius@gmail.com>

import math
import os
import random
import sys
import time

from abc import ABCMeta, abstractmethod

from constants import *


#TODO: remove log function
def log(string):
    """ Temporary logging for dev/debug purposes """
    with open('/tmp/castle_wars.log', 'a') as f:
        f.write(string)

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

def convert_percentage(percentage):
    """ Build correct dict for random choice from percentage """
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

def build_computer_strategy(percentage, gold):
    """Filters possible actions. Leave only those which are affordable."""
    total_percentage = 0
    filtered_percentage = {}
    for action, percent in percentage.items():
        if COSTS[action] <= gold:
            filtered_percentage[action] = percent
            total_percentage += percent
    return (convert_percentage(filtered_percentage), total_percentage)

def put_substr_in_position(substr, pos, string):
    return string[:pos] + substr + string[pos+len(substr):]

def get_enemy_army_in_position(position, enemy_armies):
    for army in enemy_armies:
        if position == army.position:
            return army
    return None


class GameObject(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self):
        pass

    def get_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0

    def regenerate(self):
        if self.hp < self.max_hp:
            self.hp += self.regen
            if self.hp > self.max_hp:
                self.hp = self.max_hp


class Castle(GameObject):
    def __init__(self, hp=CASTLE_HP, dmg=0, regen=0, position=0, direction=0):
        self.hp = hp
        self.max_hp = hp
        self.position = position
        self.dmg = dmg
        self.regen = 0
        self.income = 0
        self.direction = direction
        self.target = None

    def has_target(self):
        return self.target

    def get_target(self, enemy_armies):
        """ Find target for army to fight with.
            Preferable target - enemy's army.
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

    def get_damage(self, damage):
        """ Castle receive only small percentage of damage.

        If incoming damage == 0, castle receive damage equals to 1.
        """
        damage = damage * CASTLE_RECEIVE_DAMAGE
        if damage == 0:
            damage = 1
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0


class Player(object):
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
        self.spawn_rate = SPAWN_RATE

    def spawn_units(self):
        """ Spawn unit from each player spawn with current upgrades """
        units = []
        if self.spawn_rate == SPAWN_RATE:
            parameters = {'hp': self.unit_hp, 'dmg': self.unit_dmg,
                          'speed': self.unit_speed, 'regen': self.unit_regen,
                          'attack_speed': self.unit_attack_speed,
                          'gold_reward': self.unit_gold_reward}
            for unit in range(self.spawns):
                if self.gold >= self.unit_price:
                    units.append(Unit(**parameters))
                    self.gold -= self.unit_price
                else:
                    break
            if units:
                self.spawn_rate = 0
        else:
            self.spawn_rate += 1
        return units

    def union_armies(self, army1, army2):
        army1.copy_target(army2.target)
        for unit in army1.units:
            army2.units.append(unit)
        self.armies.remove(army1)

    def check_armies_collision(self, army):
        for other_army in self.armies:
            if not army is other_army and army.position == other_army.position:
                self.union_armies(army, other_army)
                break

    def remove_dead_armies(self):
        alive = [army for army in self.armies if army.units]
        self.armies = alive[:]

    def add_gold(self, gold):
        self.gold += gold
        self.gold_earned += gold


class Unit(GameObject):
    def __init__(self, hp=UNIT_HP, dmg=UNIT_DMG, speed=UNIT_SPD,
                 attack_speed=UNIT_ATSPD, regen=UNIT_REGEN,
                 gold_reward=REWARD_FOR_KILLING):
        self.hp = hp
        self.max_hp = hp
        self.dmg = dmg
        self.speed = speed
        self.attack_speed = attack_speed
        self.regen = regen
        self.attack_rate = ATTACK_RATE if ATTACK_RATE > self.attack_speed else self.attack_speed
        self.target = None
        self.gold_reward = gold_reward

    def set_target(self, target):
        self.target = target

    def attack(self):
        while self.attack_rate >= ATTACK_RATE:
            self.target.get_damage(self.dmg)
            self.attack_rate -= ATTACK_RATE
        else:
            self.attack_rate += self.attack_speed

    def refresh_attack_rate(self):
        self.attack_rate = ATTACK_RATE if ATTACK_RATE > self.attack_speed else self.attack_speed


class Army(object):
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

    def draw(self, player):
        """Return image of army."""
        if self.has_target():
            return ARMY_FIGHTING_PIC[player] % len(self.units)
        return ARMY_PIC[player] % len(self.units)

    def is_enemy_castle_reachable(self):
        return abs(self.position-self.enemy_castle.position) <= 1

    def has_target(self):
        if self.target and self.target.hp == 0:
            self.target = None
        return self.target

    def get_target(self, enemy_armies):
        """ Find target for army to fight with.
            Preferable target - enemy's army.
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
            self.target = None
            return False
        return True

    def copy_target(self, other_army_target):
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
                if unit.target and unit.target.hp == 0 and not isinstance(unit.target, Castle):
                    unit.set_target(random.choice(self.target.units))

    def refresh_attack_rate(self):
        for unit in self.units:
            unit.refresh_attack_rate()

    def remove_dead_units(self):
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
        self.enemy.add_gold(gold)

    def regen_units(self):
        for unit in self.units:
            unit.regenerate()

    @property
    def hp(self):
        units_health = 0
        for unit in self.units:
            units_health += unit.hp
        return units_health


class CastleWars(object):

    def __init__(self):
        self.castle_player = Castle(position=0, direction=1)
        self.player = Player(castle=self.castle_player, player_name='player')
        self.castle_computer = Castle(position=DISTANCE+1, direction=-1)
        self.computer = Player(castle=self.castle_computer, player_name='computer')
        self.castles = {'player': self.castle_player, 'computer': self.castle_computer}
        self.players = {'player': self.player, 'computer': self.computer}
        self.income_line = INCOME_LINE
        self.player_health_line = HEALTH_LINE
        self.computer_health_line = HEALTH_LINE

    def put_in_position(self, pic, position):
        self.warline = self.warline[:position] + pic + self.warline[position+len(pic):]

    def draw_game_field(self):
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
                self.put_in_position(army.draw(player_name), army.position)
        print(self.warline)
        print(self.player_health_line)
        print(self.computer_health_line, '\n')

    def print_status(self):
        status_line = "Gold: %s   Income: %s   Spawns: %s   Kills: %s   Deaths: %s\n"
        print(status_line % (self.player.gold, self.player.income,
                             self.player.spawns, self.player.kills,
                             self.player.deaths))
        print("Current unit price: %s\tGold needed to spawn all: %s\n" %
              (self.player.unit_price, self.player.unit_price * self.player.spawns))

    def print_short_help(self):
        print("s - show upgrades   e - end turn   i - enemy info   h - help   q - exit\n")
        print("b - build spawn, cost: %s" % (SPAWN_COST,))
        print("1 - upgrade units hp +%s, cost: %s" % (UNIT_UPGRADES['hp'],
                                                      UNIT_UPGRADE_PRICES['hp']))
        print("2 - upgrade units damage +%s, cost: %s" % (UNIT_UPGRADES['dmg'],
                                                      UNIT_UPGRADE_PRICES['dmg']))
        print("3 - upgrade units attack speed +%s, cost: %s" % (UNIT_UPGRADES['attack_speed'],
                                                                UNIT_UPGRADE_PRICES['attack_speed']))
        print("4 - upgrade units regen +%s, cost: %s" % (UNIT_UPGRADES['regen'],
                                                     UNIT_UPGRADE_PRICES['regen']))
        print("5 - upgrade castle income +%s, cost: %s" % (CASTLE_UPGRADES['income'],
                                                           CASTLE_UPGRADE_PRICES['income']))
        print("6 - upgrade castle damage +%s, cost: %s" % (CASTLE_UPGRADES['dmg'],
                                                           CASTLE_UPGRADE_PRICES['dmg']))
        print("7 - upgrade castle regen +%s, cost: %s" % (CASTLE_UPGRADES['regen'],
                                                          CASTLE_UPGRADE_PRICES['regen']))
        print("8 - upgrade castle hp +%s, cost: %s" % (CASTLE_UPGRADES['hp'],
                                                       CASTLE_UPGRADE_PRICES['hp']))
        print("\n")

    def show_upgrades(self, player):
        print("\nUnit upgrades: ")
        print("hp: %s (%s level)" % (self.players[player].unit_hp,
                                     self.players[player].unit_hp_lvl))
        print("dmg: %s (%s level)" % (self.players[player].unit_dmg,
                                      self.players[player].unit_dmg_lvl))
        print("attack speed: %.1f (%s level)" % (self.players[player].unit_attack_speed,
                                               self.players[player].unit_attack_speed_lvl))
        print("regen: %s (%s level)" % (self.players[player].unit_regen,
                                        self.players[player].unit_regen_lvl))
        print("\nCastle upgrades: ")
        print("income: %s (%s level)" % (self.players[player].castle_income,
                                     self.players[player].castle_income_lvl))
        print("dmg: %s (%s level)" % (self.players[player].castle_dmg,
                                      self.players[player].castle_dmg_lvl))
        print("regen: %s (%s level)" % (self.players[player].castle_regen,
                                        self.players[player].castle_regen_lvl))
        input("\nPress Enter to continue")

    def prompt(self):
        """Ask player to make his game choices.

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
        if choice == 'q':
            self.exit()
        elif choice == 'e':
            return "end_turn"
        elif choice == 'h':
            os.system("clear")
            help()
        elif choice == 's':
            self.show_upgrades('player')
        elif choice == 'i':
            self.show_upgrades('computer')
        elif choice == 'b':
            self.build_spawn('player', count=count)
        elif choice == '1':
            self.upgrade_units_attr('player', 'hp', count=count)
        elif choice == '2':
            self.upgrade_units_attr('player', 'dmg', count=count)
        elif choice == '3':
            self.upgrade_units_attr('player', 'attack_speed', count=count)
        elif choice == '4':
            self.upgrade_units_attr('player', 'regen', count=count)
        elif choice == '5':
            self.upgrade_castle_attr('player', 'income', count=count)
        elif choice == '6':
            self.upgrade_castle_attr('player', 'dmg', count=count)
        elif choice == '7':
            self.upgrade_castle_attr('player', 'regen', count=count)
        elif choice == '8':
            self.upgrade_castle_attr('player', 'hp', count=count)

    def not_enough_gold(self):
        print("Not enough gold!")
        input("Press Enter to continue")

    def build_spawn(self, player, count=1):
        if count == 'max':
            count = self.players[player].gold // SPAWN_COST
        elif self.players[player].gold < SPAWN_COST * count:
            self.not_enough_gold()
            return

        self.players[player].spawns += count
        self.players[player].gold -= SPAWN_COST * count;

    def upgrade_units_attr(self, player, attr, count=1):
        """ Upgrades chosen unit's attribute.
            Unit becomes more expensive per each upgrade.
        """
        if count == 'max':
            count = self.players[player].gold // UNIT_UPGRADE_PRICES[attr]
        elif self.players[player].gold < UNIT_UPGRADE_PRICES[attr] * count:
            self.not_enough_gold()
            return

        self.players[player].__dict__["unit_%s_lvl" % attr] += count
        self.players[player].__dict__["unit_%s" % attr] += UNIT_UPGRADES[attr] * count
        self.players[player].gold -= UNIT_UPGRADE_PRICES[attr] * count;
        self.players[player].unit_price += count * UPGRADE_GOLD_REWARD
        self.players[player].unit_gold_reward += count * UPGRADE_GOLD_REWARD

    def upgrade_castle_attr(self, player, attr, count=1):
        """ Upgrades chosen castle's attribute """
        if count == 'max':
            count = self.players[player].gold // CASTLE_UPGRADE_PRICES[attr]
        elif self.players[player].gold < CASTLE_UPGRADE_PRICES[attr] * count:
            self.not_enough_gold()
            return

        self.players[player].__dict__["castle_%s_lvl" % attr] += count
        self.players[player].__dict__["castle_%s" % attr] += CASTLE_UPGRADES[attr] * count
        self.players[player].gold -= CASTLE_UPGRADE_PRICES[attr] * count;
        self.castles[player].__dict__[attr] += CASTLE_UPGRADES[attr] * count
        if attr == 'income':
            self.players[player].income += CASTLE_UPGRADES['income'] * count
        if attr == 'hp':
            self.castles[player].max_hp += CASTLE_UPGRADES['hp'] * count

    def make_turn(self):
        while True:
            value = self.prompt()
            self.draw_scene()
            if value == 'end_turn':
                break

    def computer_choice(self, random_number, strategy):
        for key in sorted(strategy.keys()):
            if random_number <= key:
                return strategy[key]

    def computer_action(self):
        if self.computer.gold < 100:
            return False
        # setup strategy
        percentage = {'spawn':35, 'income':30, 'unit_hp':10, 'unit_dmg':10,
                      'unit_attack_speed':10, 'unit_regen':5}
        if self.computer.spawns == 0:
            percentage = {'spawn':100}
        elif self.computer.income < 5000:
            percentage = {'income':90, 'spawn':5, 'unit_hp':2, 'unit_dmg':1,
                          'unit_attack_speed':1, 'unit_regen':1}
        elif self.computer.unit_hp_lvl < 4:
            percentage = {'spawn':30, 'income':35, 'unit_hp':15,
                          'unit_dmg':10, 'unit_attack_speed':10}
        elif self.computer.spawns > 2:
            percentage = {'spawn':10, 'income':35, 'unit_hp':15,
                          'unit_dmg':20, 'unit_attack_speed':15,
                          'unit_regen':5}

        # castle rescue
        if self.computer.castle.hp < CASTLE_HP * 0.9:
            percentage = {'spawn':1, 'income':1, 'unit_hp':1,
                          'unit_dmg':1, 'unit_attack_speed':1,
                          'unit_regen':1, 'castle_dmg':70, 'castle_regen':24}
        if self.computer.castle.hp < CASTLE_HP * 0.4:
            percentage = {'spawn':10, 'income':20, 'unit_hp':5,
                          'unit_dmg':5, 'unit_attack_speed':5,
                          'unit_regen':5, 'castle_dmg':25, 'castle_regen':25}
        strategy, max_rand = build_computer_strategy(percentage, self.computer.gold)

        choice = self.computer_choice(random.randint(1, max_rand), strategy)
        if choice == 'spawn':
            self.build_spawn('computer')
        elif choice == 'unit_hp':
            self.upgrade_units_attr('computer', 'hp')
        elif choice == 'unit_dmg':
            self.upgrade_units_attr('computer', 'dmg')
        elif choice == 'unit_attack_speed':
            self.upgrade_units_attr('computer', 'attack_speed')
        elif choice == 'unit_regen':
            self.upgrade_units_attr('computer', 'regen')
        elif choice == 'income':
            self.upgrade_castle_attr('computer', 'income')
        elif choice == 'castle_dmg':
            self.upgrade_castle_attr('computer', 'dmg')
        elif choice == 'castle_regen':
            self.upgrade_castle_attr('computer', 'regen')
        return True

    def computer_turn(self):
        costs = self.computer.spawns * self.computer.unit_price
        while self.computer.gold + self.computer.income > costs:
            success = self.computer_action()
            if not success:
                break

    def finish_turn(self):
        enemy_armies = []
        for player_name, player in self.players.items():
            # get income
            player.add_gold(player.income)

        # move armies or fight
        for tick in range(TIME_TICKS_PER_TURN):
            self.player_health_line = HEALTH_LINE
            self.computer_health_line = HEALTH_LINE
            for player_name, player in self.players.items():
                # spawn new units
                units = player.spawn_units()
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
        for unit in army.units:
            unit.attack()
        army.refresh_units_target()

    def show_game_stats(self):
        print('Game statistics\n')
        print('-= Player =-\n')
        print('Gold earned: %s\n' % (self.player.gold_earned,))
        print('Kills: %10s   Deaths: %10s\n' % (self.player.kills, self.player.deaths))
        print('-= Computer =-\n')
        print('Gold earned: %s\n' % (self.computer.gold_earned,))
        print('Kills: %10s   Deaths: %10s\n' % (self.computer.kills, self.computer.deaths))

    def game_over(self, message):
        os.system('clear')
        print(message)
        self.show_game_stats()
        input("Press Enter to exit")
        self.exit()

    def check_game_over(self):
        """ Check if any castle has hp equals 0.
        If yes, game must be ended
        """
        if self.castles['player'].hp == 0:
            self.game_over('You loose!\n')

        if self.castles['computer'].hp == 0:
            self.game_over('You win!\n')

    def exit(self):
        sys.exit(0)

    def draw_scene(self):
        os.system('clear')
        self.draw_game_field()
        self.print_status()
        self.print_short_help()

    def start(self):
        while True:
            self.draw_scene()
            self.make_turn()
            self.computer_turn()
            self.finish_turn()


if __name__ == "__main__":
    game = CastleWars()
    game.start()
