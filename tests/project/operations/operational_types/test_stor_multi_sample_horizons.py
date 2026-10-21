# Copyright 2026 Sylvan Energy Analytics LLC
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

"""
Storage state-of-charge tracking on multi-sample horizons: a horizon whose
timepoints carry different weights is read as a sequence of sample blocks
(runs of equal weight), each repeated as many times as its weight. The
fixture's weights are all 1, so the instances are built from a copy of the
test data in which the second half of 'day' horizon 202001 (timepoints
20200113-20200124) has weight 3. That horizon is Battery_Specified's
(balancing type 'day', circular, storage efficiency 0.5); the 'year' 2020
horizon of Battery and Battery_Binary contains it as well.

The repeat expressions are checked against a direct simulation of the
chain over the repeats, and the two refused configurations (a linked
horizon, an exogenous state of charge inside a repeated block) are checked
to raise.
"""

from importlib import import_module
import os.path
import random
from types import SimpleNamespace
import unittest

from pyomo.environ import value

from tests.common_functions import (
    add_components_and_load_data,
    stage_test_data_with_timepoint_weights,
    _edit_tab_file,
)

TEST_DATA_DIRECTORY = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "test_data"
)

PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.investment.periods",
    "temporal.operations.horizons",
    "geography.load_zones",
    "project",
    "project.capacity.capacity",
    "project.availability.availability",
    "project.fuels",
    "project.operations",
]
IMPORTED_PREREQ_MODULES = [
    import_module("." + mdl, package="gridpath") for mdl in PREREQUISITE_MODULE_NAMES
]
STOR_MODULE = import_module(
    ".project.operations.operational_types.stor", package="gridpath"
)

PRJ = "Battery_Specified"
BLOCK_FIRST_TMP = 20200113
BLOCK_TMPS = list(range(20200113, 20200125))
WEIGHT = 3
MIXED_WEIGHTS = {tmp: WEIGHT for tmp in BLOCK_TMPS}


def build_instance(test_case, edit_staged_dir=None):
    staged_dir = stage_test_data_with_timepoint_weights(
        test_case, TEST_DATA_DIRECTORY, MIXED_WEIGHTS
    )
    if edit_staged_dir is not None:
        edit_staged_dir(staged_dir)
    m, data = add_components_and_load_data(
        prereq_modules=IMPORTED_PREREQ_MODULES,
        module_to_test=STOR_MODULE,
        test_data_dir=staged_dir,
        weather_iteration="",
        hydro_iteration="",
        availability_iteration="",
        subproblem="",
        stage="",
    )
    return m.create_instance(data)


def simulate_repeats(instance, prj, first_tmp, starting_energy, n_repeats):
    """
    Run the storage chain over *n_repeats* repeats of the sample block from
    *starting_energy*, using the instance's charge/discharge values. Returns
    the starting energy at each timepoint of the first and of the last
    repeat (dicts) and the energy at the end of the first and of the last
    repeat.
    """
    tmps = list(instance.STOR_SAMPLE_BLOCK_TMPS[prj, first_tmp])
    eta_s = instance.stor_storage_efficiency[prj]
    soc = starting_energy
    first, last, end_first, end_last = {}, {}, None, None
    for k in range(n_repeats):
        for tmp in tmps:
            if k == 0:
                first[tmp] = soc
            if k == n_repeats - 1:
                last[tmp] = soc
            soc = soc * eta_s + value(STOR_MODULE.energy_step_rule(instance, prj, tmp))
        if k == 0:
            end_first = soc
    end_last = soc
    return first, last, end_first, end_last


class TestStorMultiSampleHorizons(unittest.TestCase):
    def test_sample_block_structure(self):
        instance = build_instance(self)
        self.assertEqual(instance.stor_storage_efficiency[PRJ], 0.5, "fixture changed")
        # Battery_Specified's day horizon: one repeated block, which wraps
        # into the horizon's first timepoint (circular boundary); the
        # year-horizon projects see the same block, followed by day 202002
        self.assertIn((PRJ, BLOCK_FIRST_TMP), instance.STOR_SAMPLE_BLOCKS)
        self.assertEqual(
            list(instance.STOR_SAMPLE_BLOCK_TMPS[PRJ, BLOCK_FIRST_TMP]), BLOCK_TMPS
        )
        self.assertEqual(instance.stor_sample_block_weight[PRJ, BLOCK_FIRST_TMP], 3)
        self.assertEqual(
            sorted(instance.STOR_SAMPLE_BLOCKS),
            [
                ("Battery", BLOCK_FIRST_TMP),
                ("Battery_Binary", BLOCK_FIRST_TMP),
                (PRJ, BLOCK_FIRST_TMP),
            ],
        )
        for position, tmp in enumerate(BLOCK_TMPS):
            self.assertIn((PRJ, tmp), instance.STOR_SAMPLE_BLOCK_OPR_TMPS)
            self.assertEqual(instance.stor_sample_block[PRJ, tmp], BLOCK_FIRST_TMP)
            self.assertEqual(instance.stor_sample_block_position[PRJ, tmp], position)
        self.assertNotIn((PRJ, 20200101), instance.STOR_SAMPLE_BLOCK_OPR_TMPS)
        self.assertEqual(
            sorted(instance.STOR_SAMPLE_BLOCK_TRANSITION_OPR_TMPS),
            [("Battery", 20200201), ("Battery_Binary", 20200201), (PRJ, 20200101)],
        )
        self.assertEqual(
            instance.stor_sample_block_before[PRJ, 20200101], BLOCK_FIRST_TMP
        )

    def test_repeat_expressions_match_simulation(self):
        instance = build_instance(self)
        rng = random.Random(2026)
        for tmp in BLOCK_TMPS:
            instance.Stor_Charge_MW[PRJ, tmp].value = rng.uniform(0, 2)
            instance.Stor_Discharge_MW[PRJ, tmp].value = rng.uniform(0, 2)
        starting_energy = 7.5
        first, last, end_first, end_last = simulate_repeats(
            instance, PRJ, BLOCK_FIRST_TMP, starting_energy, WEIGHT
        )
        # The variables hold the first repeat's chain
        for tmp in BLOCK_TMPS:
            instance.Stor_Starting_Energy_in_Storage_MWh[PRJ, tmp].value = first[tmp]

        self.assertAlmostEqual(
            value(instance.Stor_Sample_Block_End_Energy_MWh[PRJ, BLOCK_FIRST_TMP]),
            end_first
            - starting_energy
            * instance.stor_storage_efficiency[PRJ] ** len(BLOCK_TMPS),
            places=9,
        )
        for tmp in BLOCK_TMPS:
            self.assertAlmostEqual(
                value(instance.Stor_Last_Repeat_SOC_Offset_MWh[PRJ, tmp]),
                last[tmp] - first[tmp],
                places=9,
                msg=str(tmp),
            )
        self.assertAlmostEqual(
            value(
                instance.Stor_Sample_Block_Repeat_Carryover_MWh[PRJ, BLOCK_FIRST_TMP]
            ),
            end_last - end_first,
            places=9,
        )

    def test_tracking_constraint_carries_the_repeats_over(self):
        """
        The first timepoint of the circular horizon starts from the energy
        at the end of the block's LAST repeat.
        """
        instance = build_instance(self)
        rng = random.Random(7)
        for tmp in BLOCK_TMPS:
            instance.Stor_Charge_MW[PRJ, tmp].value = rng.uniform(0, 2)
            instance.Stor_Discharge_MW[PRJ, tmp].value = rng.uniform(0, 2)
        first, last, end_first, end_last = simulate_repeats(
            instance, PRJ, BLOCK_FIRST_TMP, 4.0, WEIGHT
        )
        for tmp in BLOCK_TMPS:
            instance.Stor_Starting_Energy_in_Storage_MWh[PRJ, tmp].value = first[tmp]
        con = instance.Stor_Energy_Tracking_Constraint[PRJ, 20200101]
        instance.Stor_Starting_Energy_in_Storage_MWh[PRJ, 20200101].value = end_last
        self.assertAlmostEqual(value(con.body) - value(con.upper), 0, places=9)
        instance.Stor_Starting_Energy_in_Storage_MWh[PRJ, 20200101].value = end_first
        self.assertNotAlmostEqual(value(con.body) - value(con.upper), 0, places=6)

    def test_last_repeat_bounds_are_built(self):
        instance = build_instance(self)
        for tmp in BLOCK_TMPS:
            self.assertIn(
                (PRJ, tmp), instance.Stor_Last_Repeat_Min_Energy_in_Storage_Constraint
            )
            self.assertIn(
                (PRJ, tmp), instance.Stor_Last_Repeat_Max_Energy_in_Storage_Constraint
            )
        self.assertNotIn(
            (PRJ, 20200101), instance.Stor_Last_Repeat_Max_Energy_in_Storage_Constraint
        )
        # Storage efficiency below 1 keeps the footroom energy constraint
        # (and its last-repeat twin); no reserves, so the headroom one is
        # skipped except where the next timepoint does not track energy
        self.assertIn(
            (PRJ, BLOCK_TMPS[0]),
            instance.Stor_Last_Repeat_Max_Footroom_Energy_Constraint,
        )
        self.assertEqual(
            len(instance.Stor_Last_Repeat_Max_Headroom_Energy_Constraint), 0
        )

    def test_uniform_weights_build_nothing(self):
        """
        With the fixture's own weights (all 1) every multi-sample component
        is empty and the model is the single-sample one.
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=STOR_MODULE,
            test_data_dir=TEST_DATA_DIRECTORY,
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="",
            stage="",
        )
        instance = m.create_instance(data)
        self.assertEqual(len(instance.STOR_SAMPLE_BLOCKS), 0)
        self.assertEqual(len(instance.STOR_SAMPLE_BLOCK_OPR_TMPS), 0)
        self.assertEqual(len(instance.STOR_SAMPLE_BLOCK_TRANSITION_OPR_TMPS), 0)
        self.assertEqual(
            len(instance.Stor_Last_Repeat_Max_Energy_in_Storage_Constraint), 0
        )

    def test_linked_horizon_is_refused(self):
        """
        A linked boundary needs linked-timepoint inputs the fixture does
        not carry, so the check is exercised on the structure builder with
        the built instance's components and the boundary overridden.
        """
        instance = build_instance(self)
        boundary = {idx: instance.boundary[idx] for idx in instance.boundary}
        boundary["day", 202001] = "linked"
        stub = SimpleNamespace(
            STOR=instance.STOR,
            balancing_type_project=instance.balancing_type_project,
            HRZS_BY_BLN_TYPE=instance.HRZS_BY_BLN_TYPE,
            TMPS_BY_BLN_TYPE_HRZ=instance.TMPS_BY_BLN_TYPE_HRZ,
            STOR_OPR_TMPS=instance.STOR_OPR_TMPS,
            STOR_EXOG_SOC_TMPS=instance.STOR_EXOG_SOC_TMPS,
            tmp_weight=instance.tmp_weight,
            boundary=boundary,
        )
        with self.assertRaisesRegex(ValueError, "linked boundary"):
            STOR_MODULE.get_stor_sample_block_structure(stub)

    def test_exogenous_soc_in_repeated_block_is_refused(self):
        def add_exog_soc(staged_dir):
            path = os.path.join(
                staged_dir, "inputs", "stor_exogenous_state_of_charge.tab"
            )
            with open(path, "a", newline="") as f:
                f.write(f"\n{PRJ}\t{BLOCK_TMPS[2]}\t1")

        with self.assertRaisesRegex(ValueError, "exogenous state of charge"):
            build_instance(self, add_exog_soc)


if __name__ == "__main__":
    unittest.main()
