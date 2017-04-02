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


if __name__ == "__main__":
    unittest.main()
