# Copyright 2016-2023 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pyomo.environ import AbstractModel
import unittest

import gridpath.auxiliary.auxiliary as auxiliary_module_to_test


class TestAuxiliary(unittest.TestCase):
    """ """

    def test_join_sets(self):
        """

        :return:
        """
        mod = AbstractModel()

        # If set list empty
        set_list_empty_actual = auxiliary_module_to_test.join_sets(mod, [])
        self.assertListEqual(set_list_empty_actual, [])

        # If single set in list
        mod.set1 = [1, 2, 3]
        set_list_single_set = ["set1"]
        single_set_expected = [1, 2, 3]
        single_set_actual = auxiliary_module_to_test.join_sets(mod, set_list_single_set)
        self.assertListEqual(single_set_expected, single_set_actual)

        # If more than one set
        mod.set2 = [4, 5, 6]
        set_list_two_sets = ["set1", "set2"]
        two_sets_joined_expected = [1, 2, 3, 4, 5, 6]
        two_sets_joined_actual = auxiliary_module_to_test.join_sets(
            mod, set_list_two_sets
        )
        self.assertListEqual(two_sets_joined_expected, two_sets_joined_actual)

    def test_check_list_has_single_item(self):
        """

        :return:
        """
        with self.assertRaises(ValueError):
            auxiliary_module_to_test.check_list_has_single_item([1, 2], "Error_Msg")

    def test_find_item_position(self):
        """

        :return:
        """
        l = [1, 2, 3]
        self.assertEqual(
            [0], auxiliary_module_to_test.find_list_item_position(l=l, item=1)
        )

        self.assertEqual(
            [1], auxiliary_module_to_test.find_list_item_position(l=l, item=2)
        )

        self.assertEqual(
            [2], auxiliary_module_to_test.find_list_item_position(l=l, item=3)
        )

    def test_check_list_items_are_unique(self):
        """

        :return:
        """
        with self.assertRaises(ValueError):
            auxiliary_module_to_test.check_list_items_are_unique([1, 1])

    def test_is_number(self):
        """

        :return:
        """
        self.assertEqual(True, auxiliary_module_to_test.is_number(1))
        self.assertEqual(True, auxiliary_module_to_test.is_number(100.5))
        self.assertEqual(False, auxiliary_module_to_test.is_number("string"))


if __name__ == "__main__":
    unittest.main()
