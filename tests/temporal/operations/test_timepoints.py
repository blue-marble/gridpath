#!/usr/bin/env python

import os.path
from pyomo.environ import AbstractModel, DataPortal
import unittest

from modules.temporal.operations.timepoints import add_model_components, \
    load_model_data


TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data")


class TestTimepoints(unittest.TestCase):
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
        load_model_data(m, None, data, TEST_DATA_DIRECTORY, "", "")

    def test_timepoints_data_loads_correctly(self):
        """
        Create components; check inputs load as expected
        :return:
        """
        m = AbstractModel()
        add_model_components(m, None)
        data = DataPortal()
        load_model_data(m, None, data, TEST_DATA_DIRECTORY, "", "")
        instance = m.create_instance(data)
        expected_tmp = [1, 2, 3, 4]
        actual_tmp = [tmp for tmp in instance.TIMEPOINTS]
        self.assertListEqual(expected_tmp, actual_tmp,
                             msg="TIMEPOINTS set data does not load correctly."
                             )

        expected_num_hrs_param = {1: 1, 2: 1, 3: 1, 4: 1}
        actual_num_hrs_param = \
            {tmp: instance.number_of_hours_in_timepoint[tmp]
             for tmp in instance.TIMEPOINTS
             }
        self.assertDictEqual(expected_num_hrs_param, actual_num_hrs_param,
                             msg="Data for param 'number_of_hours_in_timepoint'"
                                 " not loaded correctly")

if __name__ == "__main__":
    unittest.main()

