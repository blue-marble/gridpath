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
Differential tests for the reserve constraints that are skipped for
projects without reserve variables (storage headroom/footroom and
variable-generator upward reserves). The example tests pin the objective
function values; these tests check, on a solved example without reserves,
that every skipped constraint holds at the solution found, i.e. that the
solution is feasible, and hence optimal, for the model that includes them.

The example is solved into a temporary directory so that the committed
example directory is not touched; a copy with linear horizon boundaries
exercises the timepoints where the energy constraints must be kept.
"""

import os
import shutil
import tempfile
import unittest
import warnings

from pyomo.environ import value

from db import create_database
from db.utilities import port_csvs_to_db, scenario
from gridpath import get_scenario_inputs, run_scenario
from gridpath.project.operations.operational_types import gen_var, stor

REPO_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_TEMPLATE_ENV_VAR = "GRIDPATH_TEST_EXAMPLES_DB_TEMPLATE"
# Storage and variable generators, no reserves, circular day horizons
EXAMPLE = "generic_policy_sod_test"
LINEAR_COPY = "generic_policy_sod_test_linear_horizons"

STOR_CONSTRAINT_RULES = {
    "Stor_Max_Headroom_Power_Constraint": stor.max_headroom_power_rule,
    "Stor_Max_Footroom_Power_Constraint": stor.max_footroom_power_rule,
    "Stor_Max_Headroom_Energy_Constraint": stor.max_headroom_energy_rule,
    "Stor_Max_Footroom_Energy_Constraint": stor.max_footroom_energy_rule,
}
TOLERANCE = 1e-6


def constraint_violation(expr):
    """
    The violation of a relational expression at the current variable values
    (0 if satisfied).
    """
    lhs, rhs = expr.args
    if expr.__class__.__name__ == "EqualityExpression":
        return abs(value(lhs) - value(rhs))
    return max(0.0, value(lhs) - value(rhs))


class TestSkippedConstraintEquivalence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp_dir.name, "examples.db")
        cls.scenario_location = os.path.join(cls.tmp_dir.name, "scenarios")
        os.makedirs(cls.scenario_location)

        template_path = os.environ.get(DB_TEMPLATE_ENV_VAR)
        if template_path and os.path.exists(template_path):
            shutil.copyfile(template_path, cls.db_path)
        else:
            csv_path = os.path.join(REPO_DIRECTORY, "db", "csvs_test_examples")
            create_database.main(
                [
                    "--database",
                    cls.db_path,
                    "--db_schema",
                    os.path.join(REPO_DIRECTORY, "db", "db_schema.sql"),
                    "--data_directory",
                    os.path.join(REPO_DIRECTORY, "db", "data"),
                ]
            )
            port_csvs_to_db.main(
                ["--database", cls.db_path, "--csv_location", csv_path, "--quiet"]
            )
            scenario.main(
                [
                    "--database",
                    cls.db_path,
                    "--csv_path",
                    os.path.join(csv_path, "scenarios.csv"),
                    "--quiet",
                ]
            )

        get_scenario_inputs.main(
            [
                "--database",
                cls.db_path,
                "--scenario",
                EXAMPLE,
                "--scenario_location",
                cls.scenario_location,
                "--quiet",
            ]
        )

        # A copy with linear instead of circular horizon boundaries
        example_dir = os.path.join(cls.scenario_location, EXAMPLE)
        linear_dir = os.path.join(cls.scenario_location, LINEAR_COPY)
        shutil.copytree(example_dir, linear_dir)
        horizons_file = os.path.join(linear_dir, "inputs", "horizons_user_defined.tab")
        with open(horizons_file) as f:
            horizons = f.read()
        assert "\tcircular" in horizons
        with open(horizons_file, "w") as f:
            f.write(horizons.replace("\tcircular", "\tlinear"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp_dir.cleanup()

    def build_and_solve(self, scenario_name):
        parsed_arguments = run_scenario.parse_arguments(
            [
                "--scenario",
                scenario_name,
                "--scenario_location",
                self.scenario_location,
                "--quiet",
                "--mute_solver_output",
            ]
        )
        # The example's year horizon spans its two periods by design
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message="Horizon found that spans periods"
            )
            _, instance = run_scenario.create_problem(
                scenario_directory=os.path.join(self.scenario_location, scenario_name),
                weather_iteration="",
                hydro_iteration="",
                availability_iteration="",
                subproblem="",
                stage="",
                multi_stage=False,
                parsed_arguments=parsed_arguments,
            )
        run_scenario.solve(instance, parsed_arguments)
        return instance

    def assert_skipped_constraints_hold(self, instance, constraint_name, rule):
        """
        Build the constraint's expression for every index at which it was
        skipped and check that the solution satisfies it.
        """
        built = set(getattr(instance, constraint_name).keys())
        skipped = [idx for idx in instance.STOR_OPR_TMPS if idx not in built]
        self.assertTrue(skipped, constraint_name)
        violations = {
            idx: constraint_violation(rule(instance, *idx)) for idx in skipped
        }
        worst = max(violations.values())
        self.assertLessEqual(worst, TOLERANCE, f"{constraint_name}: {violations}")

    def test_circular_horizons(self):
        """
        With circular horizons, every storage timepoint has a next
        timepoint and (the derate being constant and the storage
        efficiency 1) all four reserve constraints are skipped everywhere.
        """
        instance = self.build_and_solve(EXAMPLE)
        for constraint_name, rule in STOR_CONSTRAINT_RULES.items():
            self.assertEqual(len(getattr(instance, constraint_name)), 0)
            self.assert_skipped_constraints_hold(instance, constraint_name, rule)

        self.assertEqual(len(instance.GenVar_Max_Upward_Reserves_Constraint), 0)
        for g, tmp in instance.GEN_VAR_OPR_TMPS:
            self.assertLessEqual(
                constraint_violation(
                    gen_var.max_upward_reserves_rule(instance, g, tmp)
                ),
                TOLERANCE,
            )

    def test_linear_horizons(self):
        """
        With linear horizons, the energy constraints are kept in the last
        timepoint of each horizon, where they are the only bound on the
        ending energy, and skipped elsewhere.
        """
        instance = self.build_and_solve(LINEAR_COPY)
        last_tmps = {
            (s, tmp)
            for (s, tmp) in instance.STOR_OPR_TMPS
            if instance.next_tmp[tmp, instance.balancing_type_project[s]] == "."
        }
        self.assertTrue(last_tmps)
        for constraint_name in [
            "Stor_Max_Headroom_Power_Constraint",
            "Stor_Max_Footroom_Power_Constraint",
        ]:
            self.assertEqual(len(getattr(instance, constraint_name)), 0)
        for constraint_name in [
            "Stor_Max_Headroom_Energy_Constraint",
            "Stor_Max_Footroom_Energy_Constraint",
        ]:
            self.assertEqual(set(getattr(instance, constraint_name).keys()), last_tmps)
        for constraint_name, rule in STOR_CONSTRAINT_RULES.items():
            self.assert_skipped_constraints_hold(instance, constraint_name, rule)


if __name__ == "__main__":
    unittest.main()
