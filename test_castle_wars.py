import unittest

from castle_wars import (convert_percentage, build_computer_strategy,
                         Player, Army, Unit, CastleWars)


class TestCastleWars(unittest.TestCase):

    def test_convert_percentage(self):
        percentage = {'spawn':35, 'income':30,
                      'unit_hp':10, 'unit_dmg':10,
                      'unit_attack_speed':10, 'unit_regen':5}
        expected_output = {5:'unit_regen', 15:'unit_attack_speed',
                           25:'unit_dmg', 35: 'unit_hp', 65: 'income',
                           100: 'spawn'}
        self.assertEqual(sorted(expected_output), sorted(convert_percentage(percentage)))

    def test_build_computer_strategy(self):
        percentage = {'spawn':35, 'income':30,
                      'unit_hp':10, 'unit_dmg':10,
                      'unit_attack_speed':10, 'unit_regen':5}
        expected_strategy = {5:'unit_regen', 15:'unit_attack_speed',
                           25:'unit_dmg', 35: 'unit_hp', 65: 'income',
                           100: 'spawn'}
        strategy, total_percentage = build_computer_strategy(percentage, 200)
        self.assertEqual(sorted(expected_strategy), sorted(strategy))
        self.assertEqual(total_percentage, 100)

        expected_strategy = {5:'unit_regen', 15:'unit_attack_speed',
                             25:'unit_dmg', 35: 'unit_hp', 65: 'income'}
        strategy, total_percentage = build_computer_strategy(percentage, 100)
        self.assertEqual(sorted(expected_strategy), sorted(strategy))
        self.assertEqual(total_percentage, 65)

    def test_remove_dead_units(self):
        unit1 = Unit(hp=5, dmg=1, speed=1, attack_speed=1, regen=0, gold_reward=1)
        unit2 = Unit(hp=0, dmg=5, speed=1, attack_speed=1, regen=0, gold_reward=5)
        unit3 = Unit(hp=0, dmg=5, speed=1, attack_speed=1, regen=5, gold_reward=10)
        player = Player()
        army = Army(units=[unit1, unit2, unit2], enemy=player)
        dead = army.remove_dead_units()
        self.assertEqual(dead, 2)
        self.assertEqual(player.kills, 2)

if __name__ == "__main__":
    unittest.main()
