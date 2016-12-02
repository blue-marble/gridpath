#!/usr/bin/env python

from collections import OrderedDict
from importlib import import_module
import os.path
import sys
import unittest

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = ["temporal.operations.timepoints",
                             "geography.load_zones"]
NAME_OF_MODULE_BEING_TESTED = "system.load_balance.load_balance"
IMPORTED_PREREQ_MODULES = list()
for mdl in PREREQUISITE_MODULE_NAMES:
    try:
        imported_module = import_module("." + str(mdl), package="modules")
        IMPORTED_PREREQ_MODULES.append(imported_module)
    except ImportError:
        print("ERROR! Module " + str(mdl) + " not found.")
        sys.exit(1)
# Import the module we'll test
try:
    MODULE_BEING_TESTED = import_module("." + NAME_OF_MODULE_BEING_TESTED,
                                        package="modules")
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED +
          " to test.")


class TestLoadBalance(unittest.TestCase):
    """

    """
    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
        :return:
        """
        create_abstract_model(prereq_modules=IMPORTED_PREREQ_MODULES,
                              module_to_test=MODULE_BEING_TESTED,
                              test_data_dir=TEST_DATA_DIRECTORY,
                              horizon="",
                              stage=""
                              )

    def test_load_model_data(self):
        """
        Test that data are loaded with no errors
        :return:
        """
        add_components_and_load_data(prereq_modules=IMPORTED_PREREQ_MODULES,
                                     module_to_test=MODULE_BEING_TESTED,
                                     test_data_dir=TEST_DATA_DIRECTORY,
                                     horizon="",
                                     stage=""
                                     )

    def test_data_loaded_correctly(self):
        """
        Test components initialized with data as expected
        :return:
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            horizon="",
            stage=""
        )
        instance = m.create_instance(data)

        # Param: static_load_mw
        expected_static_load = OrderedDict(sorted({
            ("Zone1", 20200101): 50,
            ("Zone1", 20200102): 40,
            ("Zone1", 20200103): 40,
            ("Zone1", 20200104): 50,
            ("Zone1", 20200105): 50,
            ("Zone1", 20200106): 40,
            ("Zone1", 20200107): 40,
            ("Zone1", 20200108): 50,
            ("Zone1", 20200109): 50,
            ("Zone1", 20200110): 40,
            ("Zone1", 20200111): 40,
            ("Zone1", 20200112): 50,
            ("Zone1", 20200113): 50,
            ("Zone1", 20200114): 40,
            ("Zone1", 20200115): 40,
            ("Zone1", 20200116): 50,
            ("Zone1", 20200117): 50,
            ("Zone1", 20200118): 40,
            ("Zone1", 20200119): 40,
            ("Zone1", 20200120): 50,
            ("Zone1", 20200121): 50,
            ("Zone1", 20200122): 40,
            ("Zone1", 20200123): 40,
            ("Zone1", 20200124): 50,
            ("Zone1", 20200201): 50,
            ("Zone1", 20200202): 40,
            ("Zone1", 20200203): 40,
            ("Zone1", 20200204): 50,
            ("Zone1", 20200205): 50,
            ("Zone1", 20200206): 40,
            ("Zone1", 20200207): 40,
            ("Zone1", 20200208): 50,
            ("Zone1", 20200209): 50,
            ("Zone1", 20200210): 40,
            ("Zone1", 20200211): 40,
            ("Zone1", 20200212): 50,
            ("Zone1", 20200213): 50,
            ("Zone1", 20200214): 40,
            ("Zone1", 20200215): 40,
            ("Zone1", 20200216): 50,
            ("Zone1", 20200217): 50,
            ("Zone1", 20200218): 40,
            ("Zone1", 20200219): 40,
            ("Zone1", 20200220): 50,
            ("Zone1", 20200221): 50,
            ("Zone1", 20200222): 40,
            ("Zone1", 20200223): 40,
            ("Zone1", 20200224): 50,
            ("Zone2", 20200101): 50,
            ("Zone2", 20200102): 40,
            ("Zone2", 20200103): 40,
            ("Zone2", 20200104): 50,
            ("Zone2", 20200105): 50,
            ("Zone2", 20200106): 40,
            ("Zone2", 20200107): 40,
            ("Zone2", 20200108): 50,
            ("Zone2", 20200109): 50,
            ("Zone2", 20200110): 40,
            ("Zone2", 20200111): 40,
            ("Zone2", 20200112): 50,
            ("Zone2", 20200113): 50,
            ("Zone2", 20200114): 40,
            ("Zone2", 20200115): 40,
            ("Zone2", 20200116): 50,
            ("Zone2", 20200117): 50,
            ("Zone2", 20200118): 40,
            ("Zone2", 20200119): 40,
            ("Zone2", 20200120): 50,
            ("Zone2", 20200121): 50,
            ("Zone2", 20200122): 40,
            ("Zone2", 20200123): 40,
            ("Zone2", 20200124): 50,
            ("Zone2", 20200201): 50,
            ("Zone2", 20200202): 40,
            ("Zone2", 20200203): 40,
            ("Zone2", 20200204): 50,
            ("Zone2", 20200205): 50,
            ("Zone2", 20200206): 40,
            ("Zone2", 20200207): 40,
            ("Zone2", 20200208): 50,
            ("Zone2", 20200209): 50,
            ("Zone2", 20200210): 40,
            ("Zone2", 20200211): 40,
            ("Zone2", 20200212): 50,
            ("Zone2", 20200213): 50,
            ("Zone2", 20200214): 40,
            ("Zone2", 20200215): 40,
            ("Zone2", 20200216): 50,
            ("Zone2", 20200217): 50,
            ("Zone2", 20200218): 40,
            ("Zone2", 20200219): 40,
            ("Zone2", 20200220): 50,
            ("Zone2", 20200221): 50,
            ("Zone2", 20200222): 40,
            ("Zone2", 20200223): 40,
            ("Zone2", 20200224): 50,
            ("Zone1", 20300101): 50,
            ("Zone1", 20300102): 40,
            ("Zone1", 20300103): 40,
            ("Zone1", 20300104): 50,
            ("Zone1", 20300105): 50,
            ("Zone1", 20300106): 40,
            ("Zone1", 20300107): 40,
            ("Zone1", 20300108): 50,
            ("Zone1", 20300109): 50,
            ("Zone1", 20300110): 40,
            ("Zone1", 20300111): 40,
            ("Zone1", 20300112): 50,
            ("Zone1", 20300113): 50,
            ("Zone1", 20300114): 40,
            ("Zone1", 20300115): 40,
            ("Zone1", 20300116): 50,
            ("Zone1", 20300117): 50,
            ("Zone1", 20300118): 40,
            ("Zone1", 20300119): 40,
            ("Zone1", 20300120): 50,
            ("Zone1", 20300121): 50,
            ("Zone1", 20300122): 40,
            ("Zone1", 20300123): 40,
            ("Zone1", 20300124): 50,
            ("Zone1", 20300201): 50,
            ("Zone1", 20300202): 40,
            ("Zone1", 20300203): 40,
            ("Zone1", 20300204): 50,
            ("Zone1", 20300205): 50,
            ("Zone1", 20300206): 40,
            ("Zone1", 20300207): 40,
            ("Zone1", 20300208): 50,
            ("Zone1", 20300209): 50,
            ("Zone1", 20300210): 40,
            ("Zone1", 20300211): 40,
            ("Zone1", 20300212): 50,
            ("Zone1", 20300213): 50,
            ("Zone1", 20300214): 40,
            ("Zone1", 20300215): 40,
            ("Zone1", 20300216): 50,
            ("Zone1", 20300217): 50,
            ("Zone1", 20300218): 40,
            ("Zone1", 20300219): 40,
            ("Zone1", 20300220): 50,
            ("Zone1", 20300221): 50,
            ("Zone1", 20300222): 40,
            ("Zone1", 20300223): 40,
            ("Zone1", 20300224): 50,
            ("Zone2", 20300101): 50,
            ("Zone2", 20300102): 40,
            ("Zone2", 20300103): 40,
            ("Zone2", 20300104): 50,
            ("Zone2", 20300105): 50,
            ("Zone2", 20300106): 40,
            ("Zone2", 20300107): 40,
            ("Zone2", 20300108): 50,
            ("Zone2", 20300109): 50,
            ("Zone2", 20300110): 40,
            ("Zone2", 20300111): 40,
            ("Zone2", 20300112): 50,
            ("Zone2", 20300113): 50,
            ("Zone2", 20300114): 40,
            ("Zone2", 20300115): 40,
            ("Zone2", 20300116): 50,
            ("Zone2", 20300117): 50,
            ("Zone2", 20300118): 40,
            ("Zone2", 20300119): 40,
            ("Zone2", 20300120): 50,
            ("Zone2", 20300121): 50,
            ("Zone2", 20300122): 40,
            ("Zone2", 20300123): 40,
            ("Zone2", 20300124): 50,
            ("Zone2", 20300201): 50,
            ("Zone2", 20300202): 40,
            ("Zone2", 20300203): 40,
            ("Zone2", 20300204): 50,
            ("Zone2", 20300205): 50,
            ("Zone2", 20300206): 40,
            ("Zone2", 20300207): 40,
            ("Zone2", 20300208): 50,
            ("Zone2", 20300209): 50,
            ("Zone2", 20300210): 40,
            ("Zone2", 20300211): 40,
            ("Zone2", 20300212): 50,
            ("Zone2", 20300213): 50,
            ("Zone2", 20300214): 40,
            ("Zone2", 20300215): 40,
            ("Zone2", 20300216): 50,
            ("Zone2", 20300217): 50,
            ("Zone2", 20300218): 40,
            ("Zone2", 20300219): 40,
            ("Zone2", 20300220): 50,
            ("Zone2", 20300221): 50,
            ("Zone2", 20300222): 40,
            ("Zone2", 20300223): 40,
            ("Zone2", 20300224): 50
                                                  }.items()
                                                  )
                                           )
        actual_static_load = OrderedDict(sorted({
            (z, tmp): instance.static_load_mw[z, tmp]
            for z in instance.LOAD_ZONES for tmp in instance.TIMEPOINTS
                                                }.items()
                                                )
                                         )
        self.assertDictEqual(expected_static_load, actual_static_load)
