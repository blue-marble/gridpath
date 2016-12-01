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
PREREQUISITE_MODULE_NAMES = [
     "temporal.operations.timepoints", "temporal.operations.horizons",
     "temporal.investment.periods", "geography.load_zones", "project",
     "project.capacity.capacity", "project.operations.operations"]
NAME_OF_MODULE_BEING_TESTED = "project.operations.fix_commitment"
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


class TestOperationalCosts(unittest.TestCase):
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
                              horizon="202001",
                              stage="ha"
                              )

    def test_load_model_data(self):
        """
        Test that data are loaded with no errors
        :return:
        """
        add_components_and_load_data(prereq_modules=IMPORTED_PREREQ_MODULES,
                                     module_to_test=MODULE_BEING_TESTED,
                                     test_data_dir=TEST_DATA_DIRECTORY,
                                     horizon="202001",
                                     stage="ha"
                                     )

    def test_data_loaded_correctly(self):
        """
        Test that the data loaded are as expected
        :return:
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            horizon="202001",
            stage="ha"
        )
        instance = m.create_instance(data)

        # Set: FINAL_COMMITMENT_PROJECTS
        expected_final_projects = sorted([
            "Gas_CCGT", "Gas_CCGT_New", "Gas_CCGT_z2", "Disp_Binary_Commit",
            "Disp_Cont_Commit"
        ])
        actual_final_projects = sorted([
            prj for prj in instance.FINAL_COMMITMENT_PROJECTS
        ])
        self.assertListEqual(expected_final_projects, actual_final_projects)

        # Set: FINAL_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS
        # Note: this should be getting the timepoints from the
        # scenario-horizon-stage inputs directory, not the timepoints from the
        # root scenario director (so 2030 and horizon 202002 shouldn't be here)
        expected_final_prj_op_tmps = sorted([
            ("Gas_CCGT", 20200101), ("Gas_CCGT", 20200102),
            ("Gas_CCGT", 20200103), ("Gas_CCGT", 20200104),
            ("Gas_CCGT", 20200105), ("Gas_CCGT", 20200106),
            ("Gas_CCGT", 20200107), ("Gas_CCGT", 20200108),
            ("Gas_CCGT", 20200109), ("Gas_CCGT", 20200110),
            ("Gas_CCGT", 20200111), ("Gas_CCGT", 20200112),
            ("Gas_CCGT", 20200113), ("Gas_CCGT", 20200114),
            ("Gas_CCGT", 20200115), ("Gas_CCGT", 20200116),
            ("Gas_CCGT", 20200117), ("Gas_CCGT", 20200118),
            ("Gas_CCGT", 20200119), ("Gas_CCGT", 20200120),
            ("Gas_CCGT", 20200121), ("Gas_CCGT", 20200122),
            ("Gas_CCGT", 20200123), ("Gas_CCGT", 20200124),
            ("Gas_CCGT_z2", 20200101), ("Gas_CCGT_z2", 20200102),
            ("Gas_CCGT_z2", 20200103), ("Gas_CCGT_z2", 20200104),
            ("Gas_CCGT_z2", 20200105), ("Gas_CCGT_z2", 20200106),
            ("Gas_CCGT_z2", 20200107), ("Gas_CCGT_z2", 20200108),
            ("Gas_CCGT_z2", 20200109), ("Gas_CCGT_z2", 20200110),
            ("Gas_CCGT_z2", 20200111), ("Gas_CCGT_z2", 20200112),
            ("Gas_CCGT_z2", 20200113), ("Gas_CCGT_z2", 20200114),
            ("Gas_CCGT_z2", 20200115), ("Gas_CCGT_z2", 20200116),
            ("Gas_CCGT_z2", 20200117), ("Gas_CCGT_z2", 20200118),
            ("Gas_CCGT_z2", 20200119), ("Gas_CCGT_z2", 20200120),
            ("Gas_CCGT_z2", 20200121), ("Gas_CCGT_z2", 20200122),
            ("Gas_CCGT_z2", 20200123), ("Gas_CCGT_z2", 20200124),
            ("Gas_CCGT_New", 20200101), ("Gas_CCGT_New", 20200102),
            ("Gas_CCGT_New", 20200103), ("Gas_CCGT_New", 20200104),
            ("Gas_CCGT_New", 20200105), ("Gas_CCGT_New", 20200106),
            ("Gas_CCGT_New", 20200107), ("Gas_CCGT_New", 20200108),
            ("Gas_CCGT_New", 20200109), ("Gas_CCGT_New", 20200110),
            ("Gas_CCGT_New", 20200111), ("Gas_CCGT_New", 20200112),
            ("Gas_CCGT_New", 20200113), ("Gas_CCGT_New", 20200114),
            ("Gas_CCGT_New", 20200115), ("Gas_CCGT_New", 20200116),
            ("Gas_CCGT_New", 20200117), ("Gas_CCGT_New", 20200118),
            ("Gas_CCGT_New", 20200119), ("Gas_CCGT_New", 20200120),
            ("Gas_CCGT_New", 20200121), ("Gas_CCGT_New", 20200122),
            ("Gas_CCGT_New", 20200123), ("Gas_CCGT_New", 20200124),
            ("Disp_Binary_Commit", 20200101), ("Disp_Binary_Commit", 20200102),
            ("Disp_Binary_Commit", 20200103), ("Disp_Binary_Commit", 20200104),
            ("Disp_Binary_Commit", 20200105), ("Disp_Binary_Commit", 20200106),
            ("Disp_Binary_Commit", 20200107), ("Disp_Binary_Commit", 20200108),
            ("Disp_Binary_Commit", 20200109), ("Disp_Binary_Commit", 20200110),
            ("Disp_Binary_Commit", 20200111), ("Disp_Binary_Commit", 20200112),
            ("Disp_Binary_Commit", 20200113), ("Disp_Binary_Commit", 20200114),
            ("Disp_Binary_Commit", 20200115), ("Disp_Binary_Commit", 20200116),
            ("Disp_Binary_Commit", 20200117), ("Disp_Binary_Commit", 20200118),
            ("Disp_Binary_Commit", 20200119), ("Disp_Binary_Commit", 20200120),
            ("Disp_Binary_Commit", 20200121), ("Disp_Binary_Commit", 20200122),
            ("Disp_Binary_Commit", 20200123), ("Disp_Binary_Commit", 20200124),
            ("Disp_Cont_Commit", 20200101), ("Disp_Cont_Commit", 20200102),
            ("Disp_Cont_Commit", 20200103), ("Disp_Cont_Commit", 20200104),
            ("Disp_Cont_Commit", 20200105), ("Disp_Cont_Commit", 20200106),
            ("Disp_Cont_Commit", 20200107), ("Disp_Cont_Commit", 20200108),
            ("Disp_Cont_Commit", 20200109), ("Disp_Cont_Commit", 20200110),
            ("Disp_Cont_Commit", 20200111), ("Disp_Cont_Commit", 20200112),
            ("Disp_Cont_Commit", 20200113), ("Disp_Cont_Commit", 20200114),
            ("Disp_Cont_Commit", 20200115), ("Disp_Cont_Commit", 20200116),
            ("Disp_Cont_Commit", 20200117), ("Disp_Cont_Commit", 20200118),
            ("Disp_Cont_Commit", 20200119), ("Disp_Cont_Commit", 20200120),
            ("Disp_Cont_Commit", 20200121), ("Disp_Cont_Commit", 20200122),
            ("Disp_Cont_Commit", 20200123), ("Disp_Cont_Commit", 20200124)
        ])
        actual_final_prj_op_tmps = sorted([
            (prj, tmp) for (prj, tmp)
            in instance.FINAL_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS
        ])
        self.assertListEqual(expected_final_prj_op_tmps,
                             actual_final_prj_op_tmps)

        # Set: FIXED_COMMITMENT_PROJECTS
        expected_fixed_projects = sorted([
            "Coal", "Coal_z2"
        ])
        actual_fixed_projects = sorted([
            prj for prj in instance.FIXED_COMMITMENT_PROJECTS
        ])
        self.assertListEqual(expected_fixed_projects,
                             actual_fixed_projects)
        
        # Set: FIXED_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS
        expected_fixed_prj_op_tmps = sorted([
            ("Coal", 20200101), ("Coal", 20200102),
            ("Coal", 20200103), ("Coal", 20200104),
            ("Coal", 20200105), ("Coal", 20200106),
            ("Coal", 20200107), ("Coal", 20200108),
            ("Coal", 20200109), ("Coal", 20200110),
            ("Coal", 20200111), ("Coal", 20200112),
            ("Coal", 20200113), ("Coal", 20200114),
            ("Coal", 20200115), ("Coal", 20200116),
            ("Coal", 20200117), ("Coal", 20200118),
            ("Coal", 20200119), ("Coal", 20200120),
            ("Coal", 20200121), ("Coal", 20200122),
            ("Coal", 20200123), ("Coal", 20200124),
            ("Coal_z2", 20200101), ("Coal_z2", 20200102),
            ("Coal_z2", 20200103), ("Coal_z2", 20200104),
            ("Coal_z2", 20200105), ("Coal_z2", 20200106),
            ("Coal_z2", 20200107), ("Coal_z2", 20200108),
            ("Coal_z2", 20200109), ("Coal_z2", 20200110),
            ("Coal_z2", 20200111), ("Coal_z2", 20200112),
            ("Coal_z2", 20200113), ("Coal_z2", 20200114),
            ("Coal_z2", 20200115), ("Coal_z2", 20200116),
            ("Coal_z2", 20200117), ("Coal_z2", 20200118),
            ("Coal_z2", 20200119), ("Coal_z2", 20200120),
            ("Coal_z2", 20200121), ("Coal_z2", 20200122),
            ("Coal_z2", 20200123), ("Coal_z2", 20200124)
        ])
        actual_fixed_prj_op_tmps = sorted([
            (prj, tmp) for (prj, tmp) 
            in instance.FIXED_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS
        ])
        self.assertListEqual(expected_fixed_prj_op_tmps,
                             actual_fixed_prj_op_tmps)
        
        # Param: fixed_commitment
        expected_fixed_commitment = OrderedDict(sorted({
            ("Coal", 20200101): 4, ("Coal", 20200102): 6,
            ("Coal", 20200103): 6, ("Coal", 20200104): 6,
            ("Coal", 20200105): 6, ("Coal", 20200106): 6,
            ("Coal", 20200107): 6, ("Coal", 20200108): 6,
            ("Coal", 20200109): 6, ("Coal", 20200110): 6,
            ("Coal", 20200111): 6, ("Coal", 20200112): 6,
            ("Coal", 20200113): 6, ("Coal", 20200114): 6,
            ("Coal", 20200115): 6, ("Coal", 20200116): 6,
            ("Coal", 20200117): 6, ("Coal", 20200118): 6,
            ("Coal", 20200119): 6, ("Coal", 20200120): 6,
            ("Coal", 20200121): 6, ("Coal", 20200122): 6,
            ("Coal", 20200123): 6, ("Coal", 20200124): 6,
            ("Coal_z2", 20200101): 6, ("Coal_z2", 20200102): 6,
            ("Coal_z2", 20200103): 6, ("Coal_z2", 20200104): 6,
            ("Coal_z2", 20200105): 6, ("Coal_z2", 20200106): 6,
            ("Coal_z2", 20200107): 6, ("Coal_z2", 20200108): 6,
            ("Coal_z2", 20200109): 6, ("Coal_z2", 20200110): 6,
            ("Coal_z2", 20200111): 6, ("Coal_z2", 20200112): 6,
            ("Coal_z2", 20200113): 6, ("Coal_z2", 20200114): 6,
            ("Coal_z2", 20200115): 6, ("Coal_z2", 20200116): 6,
            ("Coal_z2", 20200117): 6, ("Coal_z2", 20200118): 6,
            ("Coal_z2", 20200119): 6, ("Coal_z2", 20200120): 6,
            ("Coal_z2", 20200121): 6, ("Coal_z2", 20200122): 6,
            ("Coal_z2", 20200123): 6, ("Coal_z2", 20200124): 6}.items()
                                                       )
                                                )
        actual_fixed_commitment = OrderedDict(sorted({
            (prj, tmp): instance.fixed_commitment[prj, tmp] for (prj, tmp)
            in instance.FIXED_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS}.items()
                                                     )
                                              )
        self.assertDictEqual(expected_fixed_commitment,
                             actual_fixed_commitment)
