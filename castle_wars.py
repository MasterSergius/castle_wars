#!/usr/bin/env python3
#
# Game "Castle Wars"
#
# Author: Master Sergius <master.sergius@gmail.com>

import os
import random
import sys
import time

from abc import ABCMeta, abstractmethod


HOME_PIC = "|^|"
PLAYER_PIC = "%s>"
ENEMY_PIC = "<%s"
ARMY_PIC = {'player': PLAYER_PIC, 'computer': ENEMY_PIC}

DISTANCE = 70
INCOME_LINE = "." * DISTANCE
LAND = "_" * DISTANCE + '_' * len(HOME_PIC) * 2
HEALTH_LINE = ' ' * len(LAND)

TIME_TICKS_PER_TURN = 15
SPAWN_RATE = TIME_TICKS_PER_TURN * 2

CASTLE_HP = 5000

UNIT_HP = 5
UNIT_DMG = 1
UNIT_SPD = 1
UNIT_ATSPD = 1
UNIT_REGEN = 0

GOLD = 1000

UNIT_PRICE = 5
REWARD_FOR_KILLING = 1

# Income per one piece of land owning
LAND_INCOME = 2

SPAWN_COST = 200

ATTACK_RATE = 5
UNIT_UPGRADES = {'hp': 5,
                 'dmg': 1,
                 'speed': 1,
                 'attack_speed': 0.5,
                 'regen': 1}

UNIT_UPGRADE_PRICES = {'hp': 100,
                       'dmg': 100,
                       'speed': 100,
                       'attack_speed': 100,
                       'regen': 100}

CASTLE_UPGRADES = {'income': 10,
                   'dmg': 1,
                   'regen': 1}

CASTLE_UPGRADE_PRICES = {'income': 100,
                         'dmg': 300,
                         'regen': 200}

PLAYER_POSITIONS = {'player': 0, 'computer': DISTANCE+1}
PLAYER_MOVEMENTS = {'player': 1, 'computer': -1}

# TODO: BONUS SKILLS
BONUS_UPGRADE_POISON = 200
BONUS_UPGRADE_STUN = 200
BONUS_UPGRADE_EVASION = 200


def log(string):
    with open('/tmp/castle_wars.log', 'a') as f:
        f.write(string)

def help():
    """ Returns all necessary information to play this game """
    help_string = """ Goal: Destroy enemy's Castle.
    Upgrades:
    All upgrades have no limits.
    Income:
    You get 2 gold for each piece of land you own.
    """
    return help_string

def put_substr_in_position(substr, pos, string):
    return string[:pos] + substr + string[pos+len(substr):]


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


class Castle(GameObject):
    def __init__(self, hp=CASTLE_HP, dmg=0, regen=0, position=0):
        self.hp = hp
        self.max_hp = hp
        self.position = position
        self.dmg = dmg
        self.regen = 0


class Player(object):
    def __init__(self, castle=Castle(), player_name='player'):
        self.name = player_name
        self.gold = GOLD
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
        self.castle_regen = 0
        self.castle_income_lvl = 0
        self.castle_dmg_lvl = 0
        self.castle_regen_lvl = 0
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
        self.position += self.movement * self.speed

    def draw(self, player):
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
        self.target = self.get_enemy_army_in_position(self.position, enemy_armies)
        if not self.target:
            self.target = self.get_enemy_army_in_position(self.position+self.movement, enemy_armies)
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

    def get_enemy_army_in_position(self, position, enemy_armies):
        for army in enemy_armies:
            if position == army.position:
                return army
        return None

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

class CivilizationsFight(object):

    def __init__(self):
        self.castle_player = Castle(position=0)
        self.player = Player(castle=self.castle_player, player_name='player')
        self.castle_computer = Castle(position=DISTANCE+1)
        self.computer = Player(castle=self.castle_computer, player_name='computer')
        self.castles = {'player': self.castle_player, 'computer': self.castle_computer}
        self.players = {'player': self.player, 'computer': self.computer}
        self.income_line = INCOME_LINE
        self.health_line = HEALTH_LINE

    def put_in_position(self, pic, position):
        self.warline = self.warline[:position] + pic + self.warline[position+len(pic):]

    def draw_game_field(self):
        # create appropriate string to show castles' hp
        half = (DISTANCE + len(HOME_PIC) * 2) // 2
        player_castle_hp = ("%" + str(-half) + "s") % self.player.castle.hp
        computer_castle_hp = ("%" + str(half) + "s") % self.computer.castle.hp
        # print string with castles' hp
        print(player_castle_hp + computer_castle_hp)
        # print castles, road and units
        print("%s%s%s" % (HOME_PIC, self.income_line, HOME_PIC))
        self.warline = LAND
        for player_name, player in self.players.items():
            for army in player.armies:
                self.put_in_position(army.draw(player_name), army.position)
        print(self.warline, '\n')
        print(self.health_line, '\n')

    def print_status(self):
        status_line = "Gold: %s   Income: %s   Spawns: %s   Kills: %s   Deaths: %s\n"
        print(status_line % (self.player.gold, self.player.income,
                             self.player.spawns, self.player.kills,
                             self.player.deaths))
        print("Current unit price: %s\n" % (self.player.unit_price,))

    def print_short_help(self):
        print("s - show upgrades   e - end turn   i - enemy info   h - help   q - exit\n")
        print("b - build spawn, cost: %s" % (SPAWN_COST,))
        print("1 - upgrade units hp, cost: %s" % (UNIT_UPGRADE_PRICES['hp'],))
        print("2 - upgrade units damage, cost: %s" % (UNIT_UPGRADE_PRICES['dmg'],))
        print("3 - upgrade units attack speed, cost: %s" % (UNIT_UPGRADE_PRICES['attack_speed'],))
        print("4 - upgrade units regen, cost: %s" % (UNIT_UPGRADE_PRICES['regen'],))
        print("5 - upgrade castle income, cost: %s" % (CASTLE_UPGRADE_PRICES['income'],))
        print("6 - upgrade castle damage, cost: %s" % (CASTLE_UPGRADE_PRICES['dmg'],))
        print("7 - upgrade castle regen, cost: %s" % (CASTLE_UPGRADE_PRICES['regen'],))
        print("\n")

    def show_upgrades(self, player):
        print("\nUnit upgrades: ")
        print("hp: %s (%s level)" % (self.players[player].unit_hp,
                                     self.players[player].unit_hp_lvl))
        print("dmg: %s (%s level)" % (self.players[player].unit_dmg,
                                      self.players[player].unit_dmg_lvl))
        print("attack speed: %s (%s level)" % (self.players[player].unit_attack_speed,
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
        choice = input("Your choice > ")
        if choice == 'q':
            self.exit()
        elif choice == 'e':
            return "end_turn"
        elif choice == 'h':
            pass
        elif choice == 's':
            self.show_upgrades('player')
        elif choice == 'i':
            self.show_upgrades('computer')
        elif choice == 'b':
            self.build_spawn('player')
        elif choice == '1':
            self.upgrade_units_attr('player', 'hp')
        elif choice == '2':
            self.upgrade_units_attr('player', 'dmg')
        elif choice == '3':
            self.upgrade_units_attr('player', 'attack_speed')
        elif choice == '4':
            self.upgrade_units_attr('player', 'regen')
        elif choice == '5':
            self.upgrade_castle_attr('player', 'income')
        elif choice == '6':
            self.upgrade_castle_attr('player', 'dmg')
        elif choice == '7':
            self.upgrade_castle_attr('player', 'regen')

    def not_enough_gold(self):
        print("Not enough gold!")
        input("Press Enter to continue")

    def build_spawn(self, player):
        if self.players[player].gold >= SPAWN_COST:
            self.players[player].spawns += 1
            self.players[player].gold -= SPAWN_COST;
        else:
            self.not_enough_gold()

    def upgrade_units_attr(self, player, attr):
        """ Upgrades chosen unit's attribute.
            Unit becomes more expensive per each upgrade.
        """
        if self.players[player].gold >= UNIT_UPGRADE_PRICES[attr]:
            self.players[player].__dict__["unit_%s_lvl" % attr] += 1
            self.players[player].__dict__["unit_%s" % attr] += UNIT_UPGRADES[attr]
            self.players[player].gold -= UNIT_UPGRADE_PRICES[attr];
            self.players[player].unit_price += 1
            self.players[player].unit_gold_reward += 1
        else:
            self.not_enough_gold()

    def upgrade_castle_attr(self, player, attr):
        """ Upgrades chosen castle's attribute """
        if self.players[player].gold >= CASTLE_UPGRADE_PRICES[attr]:
            self.players[player].__dict__["castle_%s_lvl" % attr] += 1
            self.players[player].__dict__["castle_%s" % attr] += CASTLE_UPGRADES[attr]
            self.players[player].gold -= CASTLE_UPGRADE_PRICES[attr];
            if attr == 'income':
                self.players[player].income += CASTLE_UPGRADES['income']
        else:
            self.not_enough_gold()

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

    def computer_turn(self):
        # setup strategy
        strategy = {40:'spawn', 65:'income',
                    75:'unit_hp', 85:'unit_dmg',
                    95:'unit_attack_speed', 100:'unit_regen'}
        if self.computer.castle.hp < CASTLE_HP * 0.8:
            strategy = {40:'spawn', 70:'income',
                        75:'castle_dmg', 80:'castle_regen',
                        85:'unit_hp', 90:'unit_dmg',
                        95:'unit_attack_speed', 100:'unit_regen'}
        if self.computer.castle.hp < CASTLE_HP * 0.4:
            strategy = {40:'income', 70:'castle_regen',
                        80:'castle_dmg',
                        85:'unit_hp', 90:'unit_dmg',
                        95:'unit_attack_speed', 100:'unit_regen'}
        while self.computer.gold > self.computer.spawns * self.computer.unit_price + 200:
            choice = self.computer_choice(random.randint(1,100), strategy)
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

    def finish_turn(self):
        enemy_armies = []
        for player_name, player in self.players.items():
            # get income
            player.gold += player.income

        # move armies or fight
        for tick in range(TIME_TICKS_PER_TURN):
            self.health_line = HEALTH_LINE
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
                    if army.has_target() or army.get_target(enemy_armies):
                        self.fight_tick(army)
                    else:
                        army.move()
                        army.refresh_attack_rate()
                        player.check_armies_collision(army)
                    self.health_line = put_substr_in_position(str(army.hp),
                                                              army.position,
                                                              self.health_line)
            for player in self.players.values():
                for army in player.armies:
                    # remove dead units and armies
                    dead = army.remove_dead_units()
                    self.player.deaths += dead
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

    def check_game_over(self):
        """ Check if any castle has hp equals 0.
        If yes, game must be ended
        """
        if self.castles['player'].hp == 0:
            os.system('clear')
            print("You loose!\n")
            input("Press Enter to exit")
            self.exit()
        if self.castles['computer'].hp == 0:
            os.system('clear')
            print("You win!\n")
            input("Press Enter to exit")
            self.exit()

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

game = CivilizationsFight()
game.start()
