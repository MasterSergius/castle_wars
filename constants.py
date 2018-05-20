HOME_PIC = "|^|"
PLAYER_PIC = "%s>"
ENEMY_PIC = "<%s"
ARMY_PIC = {'player': PLAYER_PIC, 'computer': ENEMY_PIC}
PLAYER_FIGHTING_PIC = "%sx"
ENEMY_FIGHTING_PIC = "x%s"
ARMY_FIGHTING_PIC = {'player': PLAYER_FIGHTING_PIC,
                     'computer': ENEMY_FIGHTING_PIC}

DISTANCE = 70
INCOME_LINE = "." * DISTANCE
LAND = "_" * DISTANCE + '_' * len(HOME_PIC) * 2
HEALTH_LINE = ' ' * len(LAND)

TIME_TICKS_PER_TURN = 15
SPAWN_RATE_IN_TURNS = 3
SPAWN_RATE = TIME_TICKS_PER_TURN * SPAWN_RATE_IN_TURNS

CASTLE_HP = 10000
CASTLE_RECEIVE_DAMAGE = 0.1

UNIT_HP = 5
UNIT_DMG = 1
UNIT_SPD = 1
UNIT_ATSPD = 1
UNIT_REGEN = 0

GOLD = 1000

UNIT_PRICE = 5
REWARD_FOR_KILLING = 1
UPGRADE_GOLD_REWARD = 1

# Income per one piece of land owning
LAND_INCOME = 10

SPAWN_COST = 200

ATTACK_RATE = 5
UNIT_UPGRADES = {'hp': 5,
                 'dmg': 1,
                 'speed': 1,
                 'attack_speed': 0.1,
                 'regen': 1}

UNIT_UPGRADE_PRICES = {'hp': 100,
                       'dmg': 100,
                       'speed': 100,
                       'attack_speed': 100,
                       'regen': 100}

CASTLE_UPGRADES = {'income': 10,
                   'dmg': 5,
                   'regen': 10,
                   'hp': 1000}

CASTLE_UPGRADE_PRICES = {'income': 100,
                         'dmg': 300,
                         'regen': 200,
                         'hp': 500}

PLAYER_POSITIONS = {'player': 0, 'computer': DISTANCE+1}
PLAYER_MOVEMENTS = {'player': 1, 'computer': -1}

# TODO: BONUS SKILLS
BONUS_UPGRADE_POISON = 200
BONUS_UPGRADE_STUN = 200
BONUS_UPGRADE_EVASION = 200

# All costs for computer strategy
COSTS = {'spawn': SPAWN_COST, 'unit_hp': UNIT_UPGRADE_PRICES['hp'],
         'unit_dmg': UNIT_UPGRADE_PRICES['dmg'],
         'unit_attack_speed': UNIT_UPGRADE_PRICES['attack_speed'],
         'unit_regen': UNIT_UPGRADE_PRICES['regen'],
         'income': CASTLE_UPGRADE_PRICES['income'],
         'castle_dmg': CASTLE_UPGRADE_PRICES['dmg'],
         'castle_regen': CASTLE_UPGRADE_PRICES['regen'],
         'castle_hp': CASTLE_UPGRADE_PRICES['hp']}

help_string = """<= Goal =>
Destroy enemy's Castle.

<= Units =>
Unit - the main object in game. Upgrading units doesn't affect spawned units,
but new units which are about to spawn. Units move forward for one piece of
land (cell) with each time tick or attack if it has enough attack rate.
With each time tick attack rate increases by unit's attack speed value.
Unit must have %(attack_rate)s attack rate to make damage.

<= Spawns =>
Units spawn once per %(spawn_rate)s turns and move towards enemy's castle. Each
spawn can produce one unit, but you must have enough gold for it. Each upgrade
give +%(upgrade_gold_reward)s to unit price.
Basic unit price - %(unit_price)s gold.

<= Income & Gold =>
You get income - %(land_income)s gold for each piece of land you own. You own
land from your castle to your army which is furthest. It is shown as "+" on
"income line". Enemy's land shown as "-". Another type of income can be
upgraded via castle upgrades. Also, you get gold for killing enemy units. Each
upgrade give +%(upgrade_gold_reward)s to gold reward for killing.

<= Upgrades =>
All upgrades have no limits, i.e. you can upgrade any attribute infinitely.

<= Castle =>
Castle can do damage to attackers. It targets army on cell next to Castle and
do damage to all units in army simultaneously with each time tick. Castle can
regenerate it's HP once per turn.

<= Time tick & Turn =>
Each turn consists of %(time_ticks_per_turn)s time ticks. Thus, basic units
with no upgrades can attack %(attacks_per_turn)s times and castle can attack
nearest units %(time_ticks_per_turn)s times.

<= Tips & Tricks =>
You can type "b*3" to build 3 spawn at once or "b**" to build spawns for all
available gold. The same works for upgrades.

<= Contacts =>
In case of any bugs or suggestions send an email to master.sergius@gmail.com

Thank you for playing this game! First playable version released in 2017
"""

substitute_params = {'unit_price': UNIT_PRICE, 'attack_rate': ATTACK_RATE,
                     'upgrade_gold_reward': UPGRADE_GOLD_REWARD,
                     'land_income': LAND_INCOME, 'spawn_rate': SPAWN_RATE_IN_TURNS,
                     'time_ticks_per_turn': TIME_TICKS_PER_TURN,
                     'attacks_per_turn': TIME_TICKS_PER_TURN // ATTACK_RATE}

HELP_STRING = help_string % substitute_params

HELP_ROWS_PER_PAGE = 30

def short_help_string():
    """ Build short help string using defined constants """
    unit_attrs = ('hp', 'dmg', 'attack_speed', 'regen')
    castle_attrs = ('income', 'dmg', 'regen', 'hp')

    attr_name_map = {'dmg': 'damage', 'attack_speed': 'attack_speed'}

    def map_name(attr):
        return attr_name_map[attr] if attr in attr_name_map else attr

    short_help = 's - show upgrades   e - end turn   i - enemy info   ' \
                 'h - help   q - exit\n\n' \
                 'b - build spawn, cost: %s\n' % (SPAWN_COST,)
    number = 1
    for attribute in unit_attrs:
        short_help += '%s - upgrade units %s +%s, cost %s\n' \
                       % (number,
                       map_name(attribute),
                       UNIT_UPGRADES[attribute],
                       UNIT_UPGRADE_PRICES[attribute])
        number += 1

    for attribute in castle_attrs:
        short_help += '%s - upgrade castle %s +%s, cost %s\n' \
                       % (number,
                       map_name(attribute),
                       CASTLE_UPGRADES[attribute],
                       CASTLE_UPGRADE_PRICES[attribute])
        number += 1

    return short_help

SHORT_HELP_STRING = short_help_string()
