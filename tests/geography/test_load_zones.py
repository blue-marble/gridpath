#!/usr/bin/env python

import os.path
from pyomo.environ import AbstractModel, DataPortal
import unittest

from modules.geography.load_zones import add_model_components, load_model_data

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "test_data")


class TestLoadZones(unittest.TestCase):
    """

    """
    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
        :return:
        """
        m = AbstractModel()
        add_model_components(m, None)

    def test_load_model_data(self):
        """
        Test that data are loaded with no errors
        :return:
        """
        m = AbstractModel()
        add_model_components(m, None)
        data = DataPortal()
        load_model_data(m, None, data,
                        TEST_DATA_DIRECTORY,
                        None, None)

    def test_load_zone_data_loads_correctly(self):
        """
        Create LOAD_ZONES set and load data; check resulting set is as expected
        :return:
        """
        m = AbstractModel()
        add_model_components(m, None)
        data = DataPortal()
        load_model_data(m, None, data,
                        TEST_DATA_DIRECTORY,
                        None, None)
        instance = m.create_instance(data)
        expected = sorted(["Zone1", "Zone2"])
        actual = sorted([z for z in instance.LOAD_ZONES])
        self.assertListEqual(expected, actual,
                             msg="LOAD_ZONES set data does not load correctly."
                             )


if __name__ == "__main__":
    unittest.main()
