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
The hydro energy budget constraints (gen_hydro, gen_hydro_must_take) and the
budget-allocation energy and parent-budget expressions weight every
timepoint by hours x timepoint weight, so that a horizon whose timepoints
carry different weights (e.g. a peak day of weight 1 and a median day of
weight 14) constrains the represented energy, the quantity the objective
function values. The fixture's weights are all 1 (where the weight cancels),
so the instances here are built from a copy of the test data with mixed
weights in the 'day' 202001 horizon, which the 'year' 2020 horizon
contains, and each constraint side is evaluated timepoint by timepoint.
"""

from importlib import import_module
import os.path
import unittest

from pyomo.environ import Var, value

from tests.common_functions import (
    add_components_and_load_data,
    stage_test_data_with_timepoint_weights,
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
GEN_HYDRO_MODULE = import_module(
    ".project.operations.operational_types.gen_hydro", package="gridpath"
)
GEN_HYDRO_MUST_TAKE_MODULE = import_module(
    ".project.operations.operational_types.gen_hydro_must_take", package="gridpath"
)

# The 24 timepoints of 'day' horizon 202001 get weights 1, 2, 3, 1, 2, 3, ...
MIXED_WEIGHTS = {20200101 + i: 1 + i % 3 for i in range(24)}


def body_minus_bound(constraint):
    """
    The value of the constraint's body minus its bound at the current
    variable values: zero exactly when an equality constraint holds. Pyomo
    may store either side of the written expression as the body, so the
    sign of the result is only meaningful relative to another evaluation.
    """
    body = value(constraint.body)
    if constraint.upper is not None:
        return body - value(constraint.upper)
    return body - value(constraint.lower)


def oriented_sides(test_case, constraint, probe, index, expected_delta, expected_rhs):
    """
    Check that *constraint* reads "sum over timepoints of a variable term
    == (or <=, >=) a constant" with the expected per-timepoint variable
    coefficients and constant: with every variable at zero the constraint
    evaluates to minus the constant, and setting the variable *probe[index
    of a timepoint]* to 1 adds that timepoint's coefficient. The sign that
    Pyomo gave the body is detected from the first timepoint, so the check
    does not depend on which written side became the body.

    :param probe: indexed Var whose entries are set to 1 one at a time
    :param index: callable timepoint -> index of *probe*
    :param expected_delta: callable timepoint -> expected coefficient
    :param expected_rhs: the expected constant side
    """
    base = body_minus_bound(constraint)
    sign = None
    for tmp in constraint.parent_component().model().TMPS:
        idx = index(tmp)
        if idx is None:
            continue
        probe[idx].value = 1
        delta = body_minus_bound(constraint) - base
        probe[idx].value = 0
        if sign is None:
            sign = 1 if delta > 0 else -1
        test_case.assertAlmostEqual(
            sign * delta, expected_delta(tmp), places=4, msg=str(tmp)
        )
    test_case.assertIsNotNone(sign)
    test_case.assertAlmostEqual(sign * base, -expected_rhs, places=4)


def zero_all_variables(instance):
    for var in instance.component_data_objects(Var):
        var.value = 0


def expected_budget(instance, avg_fraction, prj, bt, hrz):
    """
    The average power fraction x available capacity x hours x weight, summed
    over the horizon's timepoints.
    """
    return sum(
        value(avg_fraction[prj, bt, hrz])
        * value(instance.Capacity_MW[prj, instance.period[tmp]])
        * value(instance.Availability_Derate[prj, tmp])
        * instance.hrs_in_tmp[tmp]
        * instance.tmp_weight[tmp]
        for tmp in instance.TMPS_BY_BLN_TYPE_HRZ[bt, hrz]
    )


class TestHydroBudgetTimepointWeights(unittest.TestCase):
    def build_instance(self, module):
        staged_dir = stage_test_data_with_timepoint_weights(
            self, TEST_DATA_DIRECTORY, MIXED_WEIGHTS
        )
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=module,
            test_data_dir=staged_dir,
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="",
            stage="",
        )
        instance = m.create_instance(data)
        zero_all_variables(instance)
        # Guard against a vacuous pass: the horizon must mix weights
        weights = {
            instance.tmp_weight[tmp]
            for tmp in instance.TMPS_BY_BLN_TYPE_HRZ["day", 202001]
        }
        self.assertEqual(weights, {1, 2, 3})

        return instance

    def check_budget_constraint(self, instance, constraint, power, avg_fraction):
        """
        With all variables at zero the constraint evaluates to minus the
        weighted budget; 1 MW in a single timepoint adds that timepoint's
        hours x weight.
        """
        for prj, bt, hrz in constraint:
            hrz_tmps = set(instance.TMPS_BY_BLN_TYPE_HRZ[bt, hrz])
            oriented_sides(
                self,
                constraint[prj, bt, hrz],
                probe=power,
                index=lambda tmp: (prj, tmp) if tmp in hrz_tmps else None,
                expected_delta=lambda tmp: instance.hrs_in_tmp[tmp]
                * instance.tmp_weight[tmp],
                expected_rhs=expected_budget(instance, avg_fraction, prj, bt, hrz),
            )

    def test_gen_hydro_energy_budget_is_weighted(self):
        instance = self.build_instance(GEN_HYDRO_MODULE)
        self.assertIn(
            ("Hydro", "day", 202001), instance.GenHydro_Energy_Budget_Constraint
        )
        self.check_budget_constraint(
            instance,
            instance.GenHydro_Energy_Budget_Constraint,
            instance.GenHydro_Gross_Power_MW,
            instance.gen_hydro_average_power_fraction,
        )

    def test_gen_hydro_must_take_energy_budget_is_weighted(self):
        instance = self.build_instance(GEN_HYDRO_MUST_TAKE_MODULE)
        # The yearly budget horizon contains the mixed-weight day
        self.assertIn(
            ("Hydro_NonCurtailable", "year", 2020),
            instance.GenHydroMustTake_Energy_Budget_Constraint,
        )
        self.check_budget_constraint(
            instance,
            instance.GenHydroMustTake_Energy_Budget_Constraint,
            instance.GenHydroMustTake_Gross_Power_MW,
            instance.gen_hydro_must_take_average_power_fraction,
        )

    def test_budget_allocation_energy_and_parent_budget_are_weighted(self):
        instance = self.build_instance(GEN_HYDRO_MUST_TAKE_MODULE)
        prj = "Hydro_NonCurtailable"
        energy = instance.GenHydroMustTake_Budget_Alloc_Energy_MWh
        budget = instance.GenHydroMustTake_Parent_Hrz_Energy_Budget_MWh
        self.assertIn((prj, "day", 202001), energy)
        self.assertIn((prj, "year", 2020), budget)

        self.assertAlmostEqual(
            value(budget[prj, "year", 2020]),
            expected_budget(
                instance,
                instance.gen_hydro_must_take_average_power_fraction,
                prj,
                "year",
                2020,
            ),
            places=6,
        )

        power = instance.GenHydroMustTake_Gross_Power_MW
        self.assertEqual(value(energy[prj, "day", 202001]), 0)
        for tmp in instance.TMPS_BY_BLN_TYPE_HRZ["day", 202001]:
            power[prj, tmp].value = 1
            self.assertAlmostEqual(
                value(energy[prj, "day", 202001]),
                instance.hrs_in_tmp[tmp] * instance.tmp_weight[tmp],
                places=6,
                msg=str(tmp),
            )
            power[prj, tmp].value = 0


if __name__ == "__main__":
    unittest.main()
