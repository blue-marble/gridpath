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
The timepoint- and horizon-indexed operational inputs of projects of the
specified capacity types are written only for the periods in which the
projects are operational, i.e. have a specified capacity row.
"""

import ast
import glob
import os.path
import sqlite3
import unittest

from gridpath.project.capacity.capacity_types.common_methods import (
    SPEC_CAPACITY_TYPES,
)
from gridpath.project.operations.operational_types.common_functions import (
    BT_HRZ_INDEX_QUERY_PARAMS,
    get_prj_temporal_index_opr_inputs_from_db,
    require_bt_hrz_rows_for_every_project,
)

DB_SCHEMA_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "db", "db_schema.sql"
)
CAPACITY_TYPES_DIRECTORY = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "..",
    "gridpath",
    "project",
    "capacity",
    "capacity_types",
)

# Two timepoints in each of two periods
TMPS_BY_PERIOD = {2020: [20200101, 20200102], 2030: [20300101, 20300102]}


class SubScenariosStub:
    PROJECT_PORTFOLIO_SCENARIO_ID = 1
    PROJECT_OPERATIONAL_CHARS_SCENARIO_ID = 1
    PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID = 1
    PROJECT_NEW_COST_SCENARIO_ID = 1
    TEMPORAL_SCENARIO_ID = 1


class TestSpecNonOperationalOpcharInputs(unittest.TestCase):
    """
    In-memory database from the real schema: a 'day' horizon per period and
    a 'subproblem' horizon spanning both periods. Projects:

    * Wind_Retired (gen_spec): a capacity row for 2020 only
    * Wind_Blank (gen_spec): a 2030 row with every capacity column blank
      (a validation error, not a way to make the project absent)
    * Wind_Every (gen_spec): a period = 0 row
    * Wind_New (gen_new_lin): no specified capacity rows
    * Wind_Mapped (gen_spec): a capacity row for 2020 only, reading its
      profile through a timepoint map whose 2030 data timepoints have no
      data
    * Hydro_Retired (gen_spec): a capacity row for 2020 only
    * Hydro_Gone (gen_spec): no capacity rows and no hydro rows

    Every project has data for every timepoint (horizon).
    """

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.addCleanup(self.conn.close)
        with open(DB_SCHEMA_FILE) as f:
            self.conn.executescript(f.read())
        c = self.conn.cursor()

        for period, tmps in TMPS_BY_PERIOD.items():
            c.execute(
                """INSERT INTO inputs_temporal_periods
                (temporal_scenario_id, period) VALUES (1, ?)""",
                (period,),
            )
            for tmp in tmps:
                c.execute(
                    """INSERT INTO inputs_temporal
                    (temporal_scenario_id, subproblem_id, stage_id,
                    timepoint, period, number_of_hours_in_timepoint,
                    timepoint_weight, spinup_or_lookahead)
                    VALUES (1, 1, 1, ?, ?, 1, 1, 0)""",
                    (tmp, period),
                )
                for bt, hrz in [("day", period * 100 + 1), ("subproblem", 1)]:
                    c.execute(
                        """INSERT INTO inputs_temporal_horizon_timepoints
                        (temporal_scenario_id, subproblem_id, stage_id,
                        timepoint, balancing_type_horizon, horizon)
                        VALUES (1, 1, 1, ?, ?, ?)""",
                        (tmp, bt, hrz),
                    )

        wind = ["Wind_Retired", "Wind_Blank", "Wind_Every", "Wind_New", "Wind_Mapped"]
        hydro = ["Hydro_Retired", "Hydro_Gone"]
        c.executemany(
            """INSERT INTO inputs_project_portfolios
            (project_portfolio_scenario_id, project, capacity_type)
            VALUES (1, ?, ?)""",
            [
                (prj, "gen_new_lin" if prj == "Wind_New" else "gen_spec")
                for prj in wind + hydro
            ],
        )
        c.executemany(
            """INSERT INTO inputs_project_specified_capacity
            (project_specified_capacity_scenario_id, project, period,
            specified_capacity_mw)
            VALUES (1, ?, ?, ?)""",
            [
                ("Wind_Retired", 2020, 1),
                ("Wind_Blank", 2020, 1),
                ("Wind_Blank", 2030, None),
                ("Wind_Every", 0, 1),
                ("Wind_Mapped", 2020, 1),
                ("Hydro_Retired", 2020, 1),
            ],
        )

        c.executemany(
            """INSERT INTO inputs_project_operational_chars
            (project_operational_chars_scenario_id, project,
            operational_type, balancing_type_project,
            variable_generator_profile_scenario_id,
            variable_generator_profile_tmp_map_scenario_id)
            VALUES (1, ?, 'gen_var', 'day', 1, ?)""",
            [(prj, 1 if prj == "Wind_Mapped" else None) for prj in wind],
        )
        c.executemany(
            """INSERT INTO inputs_project_operational_chars
            (project_operational_chars_scenario_id, project,
            operational_type, balancing_type_project,
            hydro_operational_chars_scenario_id)
            VALUES (1, ?, 'gen_hydro', 'day', 1)""",
            [(prj,) for prj in hydro],
        )

        # Map 1: 2020 timepoints read themselves, 2030 timepoints read data
        # timepoints without data
        c.execute("""INSERT INTO subscenarios_project_opchar_timepoint_map
            (opchar_timepoint_map_scenario_id, name) VALUES (1, 'test')""")
        c.executemany(
            """INSERT INTO inputs_project_opchar_timepoint_map
            (opchar_timepoint_map_scenario_id, timepoint, data_timepoint)
            VALUES (1, ?, ?)""",
            [(tmp, tmp + 9) for tmp in TMPS_BY_PERIOD[2030]],
        )

        all_tmps = [tmp for tmps in TMPS_BY_PERIOD.values() for tmp in tmps]
        for prj in wind:
            c.execute(
                """INSERT INTO inputs_project_variable_generator_profiles_iterations
                (project, variable_generator_profile_scenario_id,
                varies_by_weather_iteration, varies_by_hydro_iteration)
                VALUES (?, 1, 0, 0)""",
                (prj,),
            )
            c.executemany(
                """INSERT INTO inputs_project_variable_generator_profiles
                (project, variable_generator_profile_scenario_id,
                weather_iteration, hydro_iteration, stage_id, timepoint,
                cap_factor)
                VALUES (?, 1, 0, 0, 1, ?, 0.5)""",
                [(prj, tmp) for tmp in all_tmps],
            )
        c.execute("""INSERT INTO inputs_project_hydro_operational_chars_iterations
            (project, hydro_operational_chars_scenario_id,
            varies_by_weather_iteration, varies_by_hydro_iteration)
            VALUES ('Hydro_Retired', 1, 0, 0)""")
        c.executemany(
            """INSERT INTO inputs_project_hydro_operational_chars
            (project, hydro_operational_chars_scenario_id, weather_iteration,
            hydro_iteration, stage_id, balancing_type_project, horizon,
            average_power_fraction, min_power_fraction, max_power_fraction)
            VALUES ('Hydro_Retired', 1, 0, 0, 1, ?, ?, 0.5, 0, 1)""",
            [("day", 202001), ("day", 203001), ("subproblem", 1)],
        )
        self.conn.commit()

    def var_profile_rows(self):
        return sorted(
            get_prj_temporal_index_opr_inputs_from_db(
                subscenarios=SubScenariosStub(),
                weather_iteration=0,
                hydro_iteration=0,
                availability_iteration=0,
                subproblem=1,
                stage=1,
                conn=self.conn,
                op_type="gen_var",
                table="inputs_project_variable_generator_profiles",
                subscenario_id_column="variable_generator_profile_scenario_id",
                data_column="cap_factor",
            ).fetchall()
        )

    def hydro_rows(self):
        return sorted(
            get_prj_temporal_index_opr_inputs_from_db(
                subscenarios=SubScenariosStub(),
                weather_iteration=0,
                hydro_iteration=0,
                availability_iteration=0,
                subproblem=1,
                stage=1,
                conn=self.conn,
                op_type="gen_hydro",
                table="inputs_project_hydro_operational_chars",
                subscenario_id_column="hydro_operational_chars_scenario_id",
                data_column="average_power_fraction",
                opr_index_dict=BT_HRZ_INDEX_QUERY_PARAMS,
            ).fetchall()
        )

    def test_timepoints_of_operational_periods_only(self):
        """
        Wind_Retired gets its 2020 timepoints only; Wind_Every (period = 0)
        and Wind_New (not a specified capacity type) get every timepoint.
        Wind_Blank's blank 2030 row is a row, so its 2030 timepoints are
        written too (the model then fails to load, as validation reports).
        Wind_Mapped's 2030 timepoints, whose data timepoints have no data,
        are neither written nor reported as gaps.
        """
        tmps_by_prj = {}
        for prj, tmp, _ in self.var_profile_rows():
            tmps_by_prj.setdefault(prj, []).append(tmp)
        all_tmps = TMPS_BY_PERIOD[2020] + TMPS_BY_PERIOD[2030]
        self.assertDictEqual(
            {
                "Wind_Blank": all_tmps,
                "Wind_Every": all_tmps,
                "Wind_Mapped": TMPS_BY_PERIOD[2020],
                "Wind_New": all_tmps,
                "Wind_Retired": TMPS_BY_PERIOD[2020],
            },
            tmps_by_prj,
        )

    def test_horizons_with_an_operational_timepoint_only(self):
        """
        Hydro_Retired keeps its 2020 day horizon and the subproblem horizon,
        which has 2020 timepoints, but not its 2030 day horizon.
        """
        self.assertListEqual(
            [
                ("Hydro_Retired", "day", 202001, 0.5),
                ("Hydro_Retired", "subproblem", 1, 0.5),
            ],
            self.hydro_rows(),
        )

    def test_unchanged_without_non_operational_periods(self):
        """
        With every specified capacity project operational in every period,
        every row is written.
        """
        c = self.conn.cursor()
        c.execute("""DELETE FROM inputs_project_portfolios
            WHERE project IN ('Wind_Retired', 'Wind_Blank', 'Wind_Mapped',
            'Hydro_Retired', 'Hydro_Gone')""")
        self.conn.commit()
        self.assertEqual(8, len(self.var_profile_rows()))

    def test_projects_not_operational_need_no_rows(self):
        """
        The get_inputs check for per-horizon rows skips Hydro_Gone, which
        isn't operational in the subproblem, but not Hydro_Retired.
        """
        check_rows = require_bt_hrz_rows_for_every_project(
            conn=self.conn,
            subscenarios=SubScenariosStub(),
            subproblem="",
            op_type="gen_hydro",
            db_table="inputs_project_hydro_operational_chars",
        )
        check_rows(self.hydro_rows())
        with self.assertRaisesRegex(ValueError, r"\['Hydro_Retired'\]"):
            check_rows([])


class TestSpecCapacityTypes(unittest.TestCase):
    def test_spec_capacity_types_are_the_modules_using_spec_inputs(self):
        """
        SPEC_CAPACITY_TYPES lists exactly the capacity types whose
        operational periods are their specified capacity rows, i.e. the
        modules writing their inputs with spec_get_inputs_from_database.
        """
        modules = set()
        for path in glob.glob(os.path.join(CAPACITY_TYPES_DIRECTORY, "*.py")):
            with open(path) as f:
                tree = ast.parse(f.read())
            if any(
                isinstance(node, ast.Call)
                and getattr(node.func, "id", None) == "spec_get_inputs_from_database"
                for node in ast.walk(tree)
            ):
                modules.add(os.path.splitext(os.path.basename(path))[0])
        self.assertSetEqual(modules, set(SPEC_CAPACITY_TYPES))


if __name__ == "__main__":
    unittest.main()
