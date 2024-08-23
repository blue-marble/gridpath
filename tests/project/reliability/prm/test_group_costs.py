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


from collections import OrderedDict
from importlib import import_module
import os.path
import sys
import unittest

from tests.common_functions import create_abstract_model, add_components_and_load_data

TEST_DATA_DIRECTORY = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "test_data"
)

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.operations.horizons",
    "temporal.investment.periods",
    "geography.load_zones",
    "geography.prm_zones",
    "project",
    "project.capacity.capacity",
    "project.reliability.prm",
    "project.reliability.prm.prm_types",
]
NAME_OF_MODULE_BEING_TESTED = "project.reliability.prm.group_costs"
IMPORTED_PREREQ_MODULES = list()
for mdl in PREREQUISITE_MODULE_NAMES:
    try:
        imported_module = import_module("." + str(mdl), package="gridpath")
        IMPORTED_PREREQ_MODULES.append(imported_module)
    except ImportError:
        print("ERROR! Module " + str(mdl) + " not found.")
        sys.exit(1)
# Import the module we'll test
try:
    MODULE_BEING_TESTED = import_module(
        "." + NAME_OF_MODULE_BEING_TESTED, package="gridpath"
    )
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED + " to test.")


class TestDeliverabilityGroupCosts(unittest.TestCase):
    """ """

    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
        :return:
        """
        create_abstract_model(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="",
            stage="",
        )

    def test_load_model_data(self):
        """
        Test that data are loaded with no errors
        :return:
        """
        add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="",
            stage="",
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
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="",
            stage="",
        )
        instance = m.create_instance(data)

        # Set: DELIVERABILITY_GROUP_VINTAGES
        expected_deliverability_group_periods_set = sorted(
            [("Threshold_Group_1", 2020), ("Threshold_Group_2", 2030)]
        )
        actual_deliverability_group_periods_set = sorted(
            [(g, v) for (g, v) in instance.DELIVERABILITY_GROUP_VINTAGES]
        )

        self.assertListEqual(
            expected_deliverability_group_periods_set,
            actual_deliverability_group_periods_set,
        )

        # Set: DELIVERABILITY_GROUPS
        expected_deliverability_groups_set = sorted(
            ["Threshold_Group_1", "Threshold_Group_2"]
        )
        actual_deliverability_groups_set = sorted(
            [g for g in instance.DELIVERABILITY_GROUPS]
        )

        self.assertListEqual(
            expected_deliverability_groups_set, actual_deliverability_groups_set
        )

        # Param: deliverability_lifetime_yrs
        expected_lifetime = OrderedDict(
            sorted(
                {
                    ("Threshold_Group_1", 2020): float("inf"),
                    ("Threshold_Group_2", 2030): 10,
                }.items()
            )
        )
        actual_lifetime = OrderedDict(
            sorted(
                {
                    (g, p): instance.deliverability_lifetime_yrs[g, p]
                    for (g, p) in instance.DELIVERABILITY_GROUP_VINTAGES
                }.items()
            )
        )

        self.assertDictEqual(expected_lifetime, actual_lifetime)

        # Param: deliverability_cost_per_mw_yr
        expected_deliv_cost = OrderedDict(
            sorted(
                {
                    ("Threshold_Group_1", 2020): 37.0,
                    ("Threshold_Group_2", 2030): 147.0,
                }.items()
            )
        )
        actual_deliv_cost = OrderedDict(
            sorted(
                {
                    (g, p): instance.deliverability_cost_per_mw_yr[g, p]
                    for (g, p) in instance.DELIVERABILITY_GROUP_VINTAGES
                }.items()
            )
        )

        self.assertDictEqual(expected_deliv_cost, actual_deliv_cost)

        # Param: existing_deliverability_mw
        expected_deliverable_limit = OrderedDict(
            sorted(
                {
                    ("Threshold_Group_1", 2020, "deliverable", "peak_highest"): 0,
                    ("Threshold_Group_1", 2030, "deliverable", "peak_highest"): 0,
                    ("Threshold_Group_1", 2020, "deliverable", "peak_secondary"): 200,
                    ("Threshold_Group_1", 2030, "deliverable", "peak_secondary"): 0,
                    ("Threshold_Group_1", 2020, "deliverable", "offpeak"): 0,
                    ("Threshold_Group_1", 2030, "deliverable", "offpeak"): 0,
                    ("Threshold_Group_1", 2020, "total", "peak_highest"): 0,
                    ("Threshold_Group_1", 2030, "total", "peak_highest"): 0,
                    ("Threshold_Group_1", 2020, "total", "peak_secondary"): 0,
                    ("Threshold_Group_1", 2030, "total", "peak_secondary"): 0,
                    ("Threshold_Group_1", 2020, "total", "offpeak"): 1000,
                    ("Threshold_Group_1", 2030, "total", "offpeak"): 0,
                    ("Threshold_Group_2", 2020, "deliverable", "peak_highest"): 0,
                    ("Threshold_Group_2", 2030, "deliverable", "peak_highest"): 200,
                    ("Threshold_Group_2", 2020, "deliverable", "peak_secondary"): 0,
                    ("Threshold_Group_2", 2030, "deliverable", "peak_secondary"): 0,
                    ("Threshold_Group_2", 2020, "deliverable", "offpeak"): 0,
                    ("Threshold_Group_2", 2030, "deliverable", "offpeak"): 0,
                    ("Threshold_Group_2", 2020, "total", "peak_highest"): 0,
                    ("Threshold_Group_2", 2030, "total", "peak_highest"): 0,
                    ("Threshold_Group_2", 2020, "total", "peak_secondary"): 0,
                    ("Threshold_Group_2", 2030, "total", "peak_secondary"): 0,
                    ("Threshold_Group_2", 2020, "total", "offpeak"): 0,
                    ("Threshold_Group_2", 2030, "total", "offpeak"): 999,
                }.items()
            )
        )
        actual_deliverable_limit = OrderedDict(
            sorted(
                {
                    (g, p, t, d): instance.existing_deliverability_mw[g, p, t, d]
                    for g in instance.DELIVERABILITY_GROUPS
                    for p in instance.PERIODS
                    for t in instance.CONSTRAINT_TYPES
                    for d in instance.PEAK_DESIGNATIONS
                }.items()
            )
        )

        self.assertDictEqual(expected_deliverable_limit, actual_deliverable_limit)

        # Param: deliverable_capacity_limit_mw
        expected_deliverable_limit = OrderedDict(
            sorted(
                {
                    ("Threshold_Group_1", 2020): 5000,
                    ("Threshold_Group_1", 2030): float("inf"),
                    ("Threshold_Group_2", 2020): float("inf"),
                    ("Threshold_Group_2", 2030): 4000,
                }.items()
            )
        )
        actual_deliverable_limit = OrderedDict(
            sorted(
                {
                    (g, p): instance.deliverable_capacity_limit_mw[g, p]
                    for g in instance.DELIVERABILITY_GROUPS
                    for p in instance.PERIODS
                }.items()
            )
        )

        self.assertDictEqual(expected_deliverable_limit, actual_deliverable_limit)

        # Set: DELIVERABILITY_GROUP_PROJECTS
        expected_projects = sorted(
            [("Threshold_Group_1", "Wind"), ("Threshold_Group_2", "Wind_z2")]
        )
        actual_projects = sorted(
            [(g, p) for (g, p) in instance.DELIVERABILITY_GROUP_PROJECTS]
        )

        self.assertListEqual(expected_projects, actual_projects)

        # Set: PROJECT_CONSTRAINT_TYPE_PEAK_DESIGNATIONS
        expected_type_peak_design = sorted(
            [
                ("Wind", "deliverable", "peak_highest"),
                ("Wind", "deliverable", "peak_secondary"),
                ("Wind", "total", "offpeak"),
                ("Wind_z2", "deliverable", "peak_highest"),
                ("Wind_z2", "deliverable", "peak_secondary"),
                ("Wind_z2", "total", "offpeak"),
            ]
        )
        actual_type_peak_design = sorted(
            [
                (prj, t, d)
                for (prj, t, d) in instance.PROJECT_CONSTRAINT_TYPE_PEAK_DESIGNATIONS
            ]
        )

        self.assertListEqual(expected_type_peak_design, actual_type_peak_design)

        # Param: peak_designation_multiplier
        expected_multipliers = OrderedDict(
            sorted(
                {
                    ("Wind", "deliverable", "peak_highest"): 0.2,
                    ("Wind", "deliverable", "peak_secondary"): 0.3,
                    ("Wind", "total", "offpeak"): 0.5,
                    ("Wind_z2", "deliverable", "peak_highest"): 0.25,
                    ("Wind_z2", "deliverable", "peak_secondary"): 0.4,
                    ("Wind_z2", "total", "offpeak"): 0.6,
                }.items()
            )
        )
        actual_multipliers = OrderedDict(
            sorted(
                {
                    (prj, tp, des): instance.peak_designation_multiplier[prj, tp, des]
                    for (
                        prj,
                        tp,
                        des,
                    ) in instance.PROJECT_CONSTRAINT_TYPE_PEAK_DESIGNATIONS
                }.items()
            )
        )

        self.assertDictEqual(expected_multipliers, actual_multipliers)

        # Set: OPR_PRDS_BY_GROUP_VINTAGE
        expected_opr_prds_by_grp_vintage = OrderedDict(
            sorted(
                {
                    ("Threshold_Group_1", 2020): [2020, 2030],
                    ("Threshold_Group_2", 2030): [2030],
                }.items()
            )
        )
        actual_opr_prds_by_grp_vintage = OrderedDict(
            sorted(
                {
                    (g, v): [p for p in instance.OPR_PRDS_BY_GROUP_VINTAGE[g, v]]
                    for (g, v) in instance.DELIVERABILITY_GROUP_VINTAGES
                }.items()
            )
        )

        self.assertDictEqual(
            expected_opr_prds_by_grp_vintage, actual_opr_prds_by_grp_vintage
        )

        # Set: GROUP_VNTS_OPR_IN_PERIOD
        expected_g_v_by_period = OrderedDict(
            sorted(
                {
                    2020: [("Threshold_Group_1", 2020)],
                    2030: [
                        ("Threshold_Group_1", 2020),
                        ("Threshold_Group_2", 2030),
                    ],
                }.items()
            )
        )
        actual_g_v_by_period = OrderedDict(
            sorted(
                {
                    p: [(g, v) for (g, v) in instance.GROUP_VNTS_OPR_IN_PERIOD[p]]
                    for p in instance.PERIODS
                }.items()
            )
        )

        self.assertDictEqual(expected_g_v_by_period, actual_g_v_by_period)

        # Projects
        # Set: DELIVERABILITY_GROUP_PROJECTS
        expected_projects = sorted(
            [("Threshold_Group_1", "Wind"), ("Threshold_Group_2", "Wind_z2")]
        )
        actual_projects = sorted(
            [(g, p) for (g, p) in instance.DELIVERABILITY_GROUP_PROJECTS]
        )

        self.assertListEqual(expected_projects, actual_projects)

        # Set: PROJECTS_BY_DELIVERABILITY_GROUP
        expected_prj_by_grp = OrderedDict(
            sorted(
                {
                    "Threshold_Group_1": ["Wind"],
                    "Threshold_Group_2": ["Wind_z2"],
                }.items()
            )
        )
        actual_prj_by_grp = OrderedDict(
            sorted(
                {
                    g: [p for p in instance.PROJECTS_BY_DELIVERABILITY_GROUP[g]]
                    for g in instance.DELIVERABILITY_GROUPS
                }.items()
            )
        )

        self.assertDictEqual(expected_prj_by_grp, actual_prj_by_grp)


if __name__ == "__main__":
    unittest.main()
