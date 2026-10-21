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
The horizon-level water constraints (minimum and maximum total water-link
flow, reservoir target release) and the horizon flow-violation penalty costs
weight every timepoint by hours x timepoint weight, like the hydro energy
budgets, so they apply to the represented volume. The fixture's weights are
all 1, so the instances are built from a copy of the test data with mixed
weights in the 'day' 202001 horizon and each constraint side is evaluated
timepoint by timepoint.
"""

from importlib import import_module
import os.path
import unittest

from pyomo.environ import Var, value

from tests.common_functions import (
    add_components_and_load_data,
    stage_test_data_with_timepoint_weights,
)

TEST_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

RESERVOIR_PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.investment.periods",
    "temporal.operations.horizons",
    "geography.water_network",
    "system.water.water_system_params",
    "system.water.water_nodes",
    "system.water.water_flows",
    "system.water.water_node_inflows_outflows",
]
RESERVOIRS_MODULE_NAME = "system.water.reservoirs"
PENALTY_PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.investment.periods",
    "temporal.operations.horizons",
    "geography.water_network",
    "system.water.water_system_params",
    "system.water.water_nodes",
    "system.water.water_flows",
]
PENALTY_MODULE_NAME = "objective.system.water.aggregate_flow_violation_penalty_costs"

# The 24 timepoints of 'day' horizon 202001 get weights 1, 2, 3, 1, 2, 3, ...
MIXED_WEIGHTS = {20200101 + i: 1 + i % 3 for i in range(24)}
BT, HRZ = "day", 202001


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


def weighted_hours(instance, bt, hrz):
    return sum(
        instance.hrs_in_tmp[tmp] * instance.tmp_weight[tmp]
        for tmp in instance.TMPS_BY_BLN_TYPE_HRZ[bt, hrz]
    )


class TestWaterHorizonConstraintTimepointWeights(unittest.TestCase):
    def build_instance(self, prereq_module_names, module_name):
        staged_dir = stage_test_data_with_timepoint_weights(
            self, TEST_DATA_DIRECTORY, MIXED_WEIGHTS
        )
        m, data = add_components_and_load_data(
            prereq_modules=[
                import_module("." + mdl, package="gridpath")
                for mdl in prereq_module_names
            ],
            module_to_test=import_module("." + module_name, package="gridpath"),
            test_data_dir=staged_dir,
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="",
            stage="",
        )
        instance = m.create_instance(data)
        for var in instance.component_data_objects(Var):
            var.value = 0
        # Guard against a vacuous pass: the horizon must mix weights
        self.assertEqual(
            {
                instance.tmp_weight[tmp]
                for tmp in instance.TMPS_BY_BLN_TYPE_HRZ[BT, HRZ]
            },
            {1, 2, 3},
        )

        return instance

    def check_flow_constraint(self, instance, con, wl, limit):
        """
        With all variables at zero the constraint evaluates to minus the
        limit times the horizon's weighted hours; a flow of 1 in a single
        departure timepoint adds that timepoint's hours x weight.
        """
        hrz_tmps = set(instance.TMPS_BY_BLN_TYPE_HRZ[BT, HRZ])
        oriented_sides(
            self,
            con,
            probe=instance.Water_Link_Flow_Rate_Vol_per_Sec,
            index=lambda tmp: (
                (wl, tmp, instance.arrival_timepoint[wl, tmp])
                if tmp in hrz_tmps
                else None
            ),
            expected_delta=lambda tmp: instance.hrs_in_tmp[tmp]
            * instance.tmp_weight[tmp],
            expected_rhs=limit * weighted_hours(instance, BT, HRZ),
        )

    def test_min_total_hrz_flow_is_weighted(self):
        instance = self.build_instance(
            RESERVOIR_PREREQUISITE_MODULE_NAMES, RESERVOIRS_MODULE_NAME
        )
        wl = "Water_Link_23"
        con = instance.Water_Link_Min_Total_Hrz_Flow_Constraint[wl, BT, HRZ]
        self.check_flow_constraint(
            instance,
            con,
            wl,
            limit=instance.min_bt_hrz_flow_avg_vol_per_second[wl, BT, HRZ],
        )

    def test_max_total_hrz_flow_is_weighted(self):
        instance = self.build_instance(
            RESERVOIR_PREREQUISITE_MODULE_NAMES, RESERVOIRS_MODULE_NAME
        )
        wl = "Water_Link_12"
        con = instance.Water_Link_Max_Total_Hrz_Flow_Constraint[wl, BT, HRZ]
        self.check_flow_constraint(
            instance,
            con,
            wl,
            limit=instance.max_bt_hrz_flow_avg_vol_per_second[wl, BT, HRZ],
        )

    def test_reservoir_target_release_is_weighted(self):
        instance = self.build_instance(
            RESERVOIR_PREREQUISITE_MODULE_NAMES, RESERVOIRS_MODULE_NAME
        )
        wn = "Water_Node_1"
        con = instance.Water_Node_Target_Release_Constraint[wn, BT, HRZ]
        target = instance.reservoir_target_release_avg_flow_volunit_per_sec[wn, BT, HRZ]
        hrz_tmps = set(instance.TMPS_BY_BLN_TYPE_HRZ[BT, HRZ])
        oriented_sides(
            self,
            con,
            probe=instance.Discharge_Water_to_Powerhouse_Rate_Vol_Per_Sec,
            index=lambda tmp: (wn, tmp) if tmp in hrz_tmps else None,
            expected_delta=lambda tmp: 3600
            * instance.hrs_in_tmp[tmp]
            * instance.tmp_weight[tmp],
            expected_rhs=target * 3600 * weighted_hours(instance, BT, HRZ),
        )

    def test_hrz_flow_violation_penalty_costs_are_weighted(self):
        """
        A horizon violation of 1 (an average rate over the horizon) costs
        the per-hour penalty times the horizon's weighted hours, times the
        period's objective weights, matching the other objective terms.
        """
        instance = self.build_instance(
            PENALTY_PREREQUISITE_MODULE_NAMES, PENALTY_MODULE_NAME
        )
        period = instance.period[instance.last_hrz_tmp[BT, HRZ]]
        period_weight = (
            instance.number_years_represented[period]
            * instance.probability_weighted_discount_factor[period]
        )
        for wl, violation, cost, penalty in [
            (
                "Water_Link_23",
                instance.Water_Link_Hrz_Min_Flow_Violation_Avg_Vol_per_Sec,
                instance.Total_Hrz_Min_Flow_Violation_Penalty_Cost,
                instance.hrz_min_flow_violation_penalty_cost_per_hour,
            ),
            (
                "Water_Link_12",
                instance.Water_Link_Hrz_Max_Flow_Violation_Avg_Vol_per_Sec,
                instance.Total_Hrz_Max_Flow_Violation_Penalty_Cost,
                instance.hrz_max_flow_violation_penalty_cost_per_hour,
            ),
        ]:
            self.assertEqual(value(cost), 0)
            violation[wl, BT, HRZ].value = 1
            self.assertAlmostEqual(
                value(cost),
                penalty[wl] * weighted_hours(instance, BT, HRZ) * period_weight,
                places=4,
                msg=wl,
            )
            violation[wl, BT, HRZ].value = 0


if __name__ == "__main__":
    unittest.main()
