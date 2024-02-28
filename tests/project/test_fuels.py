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
import pandas as pd
import sys
import unittest

from tests.common_functions import create_abstract_model, add_components_and_load_data


TEST_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.operations.horizons",
    "temporal.investment.periods",
]
NAME_OF_MODULE_BEING_TESTED = "project.fuels"
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


class TestFuels(unittest.TestCase):
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

    def test_initialized_components(self):
        """
        Create components; check they are initialized with data as expected
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

        # Load test data
        fuels_df = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "fuels.tab"), sep="\t"
        )
        fuel_prices_df = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "fuel_prices.tab"), sep="\t"
        )

        # Set: FUELS
        expected_fuels = sorted(fuels_df["fuel"].tolist())
        actual_fuels = sorted([fuel for fuel in instance.FUELS])
        self.assertListEqual(expected_fuels, actual_fuels)

        # Set: FUEL_GROUPS
        expected_fuel_groups = sorted(fuels_df["fuel_group"].tolist())
        actual_fuel_groups = sorted([fuel_group for fuel_group in instance.FUEL_GROUPS])
        self.assertListEqual(expected_fuel_groups, actual_fuel_groups)

        # Set: FUEL_GROUPS_FUELS
        expected_fuel_groups_fuels = list(
            fuels_df[["fuel_group", "fuel"]].to_records(index=False)
        )

        # Need to convert to tuples from numpy arrays to allow assert below
        expected_fuel_groups_fuels = sorted(
            [tuple(i) for i in expected_fuel_groups_fuels]
        )

        actual_fuel_groups_fuels = sorted(
            [(fg, f) for (fg, f) in instance.FUEL_GROUPS_FUELS]
        )

        self.assertListEqual(expected_fuel_groups_fuels, actual_fuel_groups_fuels)

        # Set: FUELS_BY_FUEL_GROUP
        expected_fuels_by_fg = {}
        for fg, f in expected_fuel_groups_fuels:
            if fg not in expected_fuels_by_fg.keys():
                expected_fuels_by_fg[fg] = [f]
            else:
                expected_fuels_by_fg[fg].append(f)
        expected_fuels_by_fg_od = OrderedDict(sorted(expected_fuels_by_fg.items()))

        actual_fuels_by_fg = {
            fg: [f for f in instance.FUELS_BY_FUEL_GROUP[fg]]
            for fg in instance.FUELS_BY_FUEL_GROUP.keys()
        }
        for fg in actual_fuels_by_fg.keys():
            actual_fuels_by_fg[fg] = sorted(actual_fuels_by_fg[fg])
        actual_fuels_by_fg_od = OrderedDict(sorted(actual_fuels_by_fg.items()))

        self.assertDictEqual(expected_fuels_by_fg_od, actual_fuels_by_fg_od)

        # Param: co2_intensity_tons_per_mmbtu
        # Rounding to 5 digits here to avoid precision-related error
        expected_co2 = OrderedDict(
            sorted(
                fuels_df.round(5)
                .set_index("fuel")
                .to_dict()["co2_intensity_tons_per_mmbtu"]
                .items()
            )
        )
        actual_co2 = OrderedDict(
            sorted(
                {
                    f: instance.co2_intensity_tons_per_mmbtu[f] for f in instance.FUELS
                }.items()
            )
        )
        self.assertDictEqual(expected_co2, actual_co2)

        # Param: fuel_price_per_mmbtu
        expected_price = OrderedDict(
            sorted(
                fuel_prices_df.set_index(["fuel", "period", "month"])
                .to_dict()["fuel_price_per_mmbtu"]
                .items()
            )
        )
        actual_price = OrderedDict(
            sorted(
                {
                    (f, p, m): instance.fuel_price_per_mmbtu[f, p, m]
                    for f in instance.FUELS
                    for p in instance.PERIODS
                    for m in instance.MONTHS
                }.items()
            )
        )
        self.assertDictEqual(expected_price, actual_price)


if __name__ == "__main__":
    unittest.main()
