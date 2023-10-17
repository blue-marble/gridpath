# Copyright 2016-2020 Blue Marble Analytics LLC.
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

"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Param, Set, NonNegativeReals, Reals, Any
from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.validations import (
    write_validation_to_database,
    validate_dtypes,
    get_expected_dtypes,
    validate_columns,
    validate_idxs,
)


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """
    m.FUELS = Set()
    m.FUEL_GROUPS = Set()
    m.FUEL_GROUPS_FUELS = Set(within=m.FUEL_GROUPS * m.FUELS)
    m.FUELS_BY_FUEL_GROUP = Set(
        m.FUEL_GROUPS,
        within=m.FUELS,
        initialize=lambda mod, fg: sorted([
            f for (group, f) in mod.FUEL_GROUPS_FUELS if group == fg
        ]),
    )

    # Allow negative emissions
    m.co2_intensity_tons_per_mmbtu = Param(m.FUELS, within=Reals)

    m.fuel_price_per_mmbtu = Param(
        m.FUELS, m.PERIODS, m.MONTHS, within=NonNegativeReals
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param stage:
    :param stage:
    :return:
    """
    # Load fuel chars only if there are data
    # There will be no data in this file if the database is used and there
    # are no projects with fuels in the scenario
    # Fuel group column is optional
    fuels_file = os.path.join(
        scenario_directory, subproblem, stage, "inputs", "fuels.tab"
    )
    fuels_df = pd.read_csv(fuels_file, delimiter="\t")
    if not fuels_df.empty:
        data_portal.load(
            filename=fuels_file,
            index=m.FUELS,
            select=("fuel", "co2_intensity_tons_per_mmbtu"),
            param=m.co2_intensity_tons_per_mmbtu,
        )

        header = pd.read_csv(
            os.path.join(
                scenario_directory, str(subproblem), str(stage), "inputs", "fuels.tab"
            ),
            sep="\t",
            header=None,
            nrows=1,
        ).values[0]

        if "fuel_group" in header:
            data_portal.data()["FUEL_GROUPS"] = fuels_df["fuel_group"].unique()

            data_portal.load(
                filename=fuels_file,
                index=m.FUEL_GROUPS_FUELS,
                select=("fuel_group", "fuel"),
                param=(),
            )

    # Load fuel prices only if there are data
    # There will be no data in this file if the database is used and there
    # are no projects with fuels in the scenario
    fuels_prices_file = os.path.join(
        scenario_directory, subproblem, stage, "inputs", "fuel_prices.tab"
    )
    fuel_prices_df = pd.read_csv(fuels_prices_file)
    if not fuel_prices_df.empty:
        data_portal.load(filename=fuels_prices_file, param=m.fuel_price_per_mmbtu)


def get_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c1 = conn.cursor()
    fuels = c1.execute(
        """SELECT DISTINCT fuel, co2_intensity_tons_per_mmbtu, fuel_group
        FROM (
        SELECT project, fuel, min_fraction_in_fuel_blend, max_fraction_in_fuel_blend
        FROM inputs_project_portfolios
        -- select the correct operational characteristics subscenario
        INNER JOIN
        (SELECT project, project_fuel_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {opchar_scenario_id}
        ) AS op_char
        USING(project)
        -- select only heat curves of matching projects
        INNER JOIN
        inputs_project_fuels
        USING(project, project_fuel_scenario_id)
        -- Get only the subset of projects in the portfolio based on the 
        -- project_portfolio_scenario_id 
        WHERE project_portfolio_scenario_id = {portfolio_scenario_id}
        ) as project_fuels_tbl
        LEFT OUTER JOIN (
        -- Get the fuel chars for the relevant fuels
        SELECT fuel, co2_intensity_tons_per_mmbtu, fuel_group
        FROM inputs_fuels
        WHERE fuel_scenario_id = {fuel_scenario_id}
        ) AS fuels_tbl
        USING (fuel)
        -- Filter out the NULLs (from projects with no fuels)
        WHERE fuel NOT NULL
        ;
        """.format(
            opchar_scenario_id=subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            portfolio_scenario_id=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            fuel_scenario_id=subscenarios.FUEL_SCENARIO_ID,
        )
    )

    c2 = conn.cursor()
    fuel_prices = c2.execute(
        """SELECT DISTINCT fuel, period, month, fuel_price_per_mmbtu
        FROM (
       SELECT project, fuel, min_fraction_in_fuel_blend, max_fraction_in_fuel_blend
        FROM inputs_project_portfolios
        -- select the correct operational characteristics subscenario
        INNER JOIN
        (SELECT project, project_fuel_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {opchar_scenario_id}
        ) AS op_char
        USING(project)
        -- select only heat curves of matching projects
        INNER JOIN
        inputs_project_fuels
        USING(project, project_fuel_scenario_id)
        -- Get only the subset of projects in the portfolio based on the 
        -- project_portfolio_scenario_id 
        WHERE project_portfolio_scenario_id = {portfolio_scenario_id}
        ) as project_fuels_tbl
        LEFT OUTER JOIN (
        -- Get the fuel chars for the relevant fuels
        SELECT fuel, period, month, fuel_price_per_mmbtu
        FROM inputs_fuel_prices
        WHERE fuel_price_scenario_id = {fuel_price_scenario_id}
        ) AS fuels_tbl
        USING (fuel)
        -- Only get periods in the relevant temporal_scenario_id
        INNER JOIN (
        SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {temporal_scenario_id}
        ) as periods_tbl
        USING (period)
        -- Filter out the NULLs (from projects with no fuels)
        WHERE fuel NOT NULL
        ;
        """.format(
            opchar_scenario_id=subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            portfolio_scenario_id=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            fuel_price_scenario_id=subscenarios.FUEL_PRICE_SCENARIO_ID,
            temporal_scenario_id=subscenarios.TEMPORAL_SCENARIO_ID,
        )
    )

    return fuels, fuel_prices


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Get the fuel input data
    fuels, fuel_prices = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    # Get the projects fuels
    c1 = conn.cursor()
    projects = c1.execute(
        """
        SELECT project, fuel, min_fraction_in_fuel_blend, max_fraction_in_fuel_blend
        FROM inputs_project_portfolios
        -- select the correct operational characteristics subscenario
        INNER JOIN
        (SELECT project, project_fuel_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        ) AS op_char
        USING(project)
        -- select only heat curves of matching projects
        INNER JOIN
        inputs_project_fuels
        USING(project, project_fuel_scenario_id)
        -- Get only the subset of projects in the portfolio based on the 
        -- project_portfolio_scenario_id 
        WHERE project_portfolio_scenario_id = {}
        """.format(
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        )
    )

    # Get the relevant periods and months
    c2 = conn.cursor()
    periods_months = c2.execute(
        """SELECT DISTINCT period, month
        FROM inputs_temporal
        WHERE temporal_scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID, subproblem, stage
        )
    )

    # Convert input data into pandas DataFrame
    fuels_df = cursor_to_df(fuels)
    fuel_prices_df = cursor_to_df(fuel_prices)
    prj_df = cursor_to_df(projects)

    # Get relevant lists
    fuels = fuels_df["fuel"].to_list()
    actual_fuel_periods_months = list(
        fuel_prices_df[["fuel", "period", "month"]].itertuples(index=False, name=None)
    )
    req_fuel_periods_months = [(f, p, m) for (p, m) in periods_months for f in fuels]

    # Check data types
    expected_dtypes = get_expected_dtypes(conn, ["inputs_fuels", "inputs_fuel_prices"])

    dtype_errors, error_columns = validate_dtypes(fuels_df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_fuels",
        severity="High",
        errors=dtype_errors,
    )

    dtype_errors, error_columns = validate_dtypes(fuel_prices_df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_fuel_prices",
        severity="High",
        errors=dtype_errors,
    )

    # TODO: couldn't this be a simple foreign key or is NULL not allowed then?
    # TODO: should this check be in projects.init instead?
    # Check that fuels specified for projects are valid fuels
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars",
        severity="High",
        errors=validate_columns(prj_df, "fuel", valids=fuels),
    )

    # Check that fuel prices exist for the period and month
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_fuel_prices",
        severity="High",
        errors=validate_idxs(
            actual_idxs=actual_fuel_periods_months,
            req_idxs=req_fuel_periods_months,
            idx_label="(fuel, period, month)",
        ),
    )


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    fuels.tab and fuel_prices.tab files.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    fuels, fuel_prices = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
        os.path.join(
            scenario_directory, str(subproblem), str(stage), "inputs", "fuels.tab"
        ),
        "w",
        newline="",
    ) as fuels_tab_file:
        writer = csv.writer(fuels_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(["fuel", "co2_intensity_tons_per_mmbtu", "fuel_group"])

        for row in fuels:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    with open(
        os.path.join(
            scenario_directory, str(subproblem), str(stage), "inputs", "fuel_prices.tab"
        ),
        "w",
        newline="",
    ) as fuel_prices_tab_file:
        writer = csv.writer(fuel_prices_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(["fuel", "period", "month", "fuel_price_per_mmbtu"])

        for row in fuel_prices:
            writer.writerow(row)





# # Copyright 2016-2020 Blue Marble Analytics LLC.
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #     http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
#
# """
# This module keeps track of fuel burn for each project. Fuel burn consists of
# both operational fuel burn for power production, and startup fuel burn (if
# applicable).
# """
#
# import csv
# import os.path
# from pyomo.environ import (
#     Set,
#     Param,
#     Var,
#     Expression,
#     Constraint,
#     NonNegativeReals,
#     PercentFraction,
#     value,
# )
#
# from gridpath.auxiliary.db_interface import import_csv
# from gridpath.auxiliary.auxiliary import get_required_subtype_modules
# from gridpath.project.operations.common_functions import load_operational_type_modules
# import gridpath.project.operations.operational_types as op_type_init
#
#
# def add_model_components(m, d, scenario_directory, subproblem, stage):
#     """
#     The following Pyomo model components are defined in this module:
#
#     +-------------------------------------------------------------------------+
#     | Sets                                                                    |
#     +=========================================================================+
#     | | :code:`FUEL_PRJ_OPR_TMPS`                                             |
#     | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
#     |                                                                         |
#     | The two-dimensional set of projects for which a fuel is specified and   |
#     | their operational timepoints.                                           |
#     +-------------------------------------------------------------------------+
#     | | :code:`HR_CURVE_PRJS_OPR_TMPS_SGMS`                                   |
#     |                                                                         |
#     | The three-dimensional set of projects for which a heat rate curve is    |
#     | specified along with the heat rate curve segments and the project       |
#     | operational timepoints.                                                 |
#     +-------------------------------------------------------------------------+
#     | | :code:`HR_CURVE_PRJS_OPR_TMPS`                                        |
#     | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
#     |                                                                         |
#     | The two-dimensional set of projects for which a heat rate curve is      |
#     | specified along with their operational timepoints.                      |
#     +-------------------------------------------------------------------------+
#     | | :code:`STARTUP_FUEL_PRJ_OPR_TMPS`                                     |
#     | | *Within*: :code:`FUEL_PRJ_OPR_TMPS`                                   |
#     |                                                                         |
#     | The two-dimensional set of projects for which startup fuel burn is      |
#     | specified and their operational timepoints.                             |
#     +-------------------------------------------------------------------------+
#
#     |
#
#     +-------------------------------------------------------------------------+
#     | Variables                                                               |
#     +=========================================================================+
#     | | :code:`HR_Curve_Prj_Fuel_Burn`                                        |
#     | | *Defined over*: :code:`HR_CURVE_PRJS_OPR_TMPS`                        |
#     | | *Within*: :code:`NonNegativeReals`                                    |
#     |                                                                         |
#     | Fuel burn in each operational timepoint of projects with a heat rate    |
#     | curve.                                                                  |
#     +-------------------------------------------------------------------------+
#     | | :code:`Project_Opr_Fuel_Burn_by_Fuel`                                 |
#     | | *Defined over*: :code:`FUEL_PRJS_FUEL_OPR_TMPS`                       |
#     | | *Within*: :code:`NonNegativeReals`                                    |
#     |                                                                         |
#     | Fuel burn by fuel in each operational timepoint of each fuel project.   |
#     +-------------------------------------------------------------------------+
#     | | :code:`Project_Startup_Fuel_Burn_by_Fuel`                             |
#     | | *Defined over*: :code:`FUEL_PRJS_FUEL_OPR_TMPS`                       |
#     | | *Within*: :code:`NonNegativeReals`                                    |
#     |                                                                         |
#     | Startup fuel burn by fuel in each operational timepoint of each startup |
#     | fuel project.                                                           |
#     +-------------------------------------------------------------------------+
#
#     |
#
#     +-------------------------------------------------------------------------+
#     | Expressions                                                             |
#     +=========================================================================+
#     | | :code:`Operations_Fuel_Burn_MMBtu`                                    |
#     | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
#     |                                                                         |
#     | This expression describes each project's operational fuel consumption   |
#     | (in MMBtu) in all operational timepoints. We obtain it by calling the   |
#     | *fuel_burn_rule* method in the relevant *operational_type*. This does   |
#     | not include fuel burn for startups, which has a separate expression.    |
#     +-------------------------------------------------------------------------+
#     | | :code:`Startup_Fuel_Burn_MMBtu`                                       |
#     | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
#     |                                                                         |
#     | This expression describes each project's startup fuel consumption       |
#     | (in MMBtu) in all operational timepoints. We obtain it by calling the   |
#     | *startup_fuel_burn_rule* method in the relevant *operational_type*.     |
#     | Only operational types with commitment variables can have startup fuel  |
#     | burn (for others it will always return zero).                           |
#     +-------------------------------------------------------------------------+
#     | | :code:`Total_Fuel_Burn_by_Fuel_MMBtu`                                 |
#     | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
#     |                                                                         |
#     | Total fuel burn is the sum of operational fuel burn for power           |
#     | production and startup fuel burn (by fuel).                             |
#     +-------------------------------------------------------------------------+
#
#     |
#
#     +-------------------------------------------------------------------------+
#     | Constraints                                                             |
#     +=========================================================================+
#     | | :code:`HR_Curve_Prj_Fuel_Burn_Constraint`                             |
#     | | *Defined over*: :code:`HR_CURVE_PRJS_OPR_TMPS_SGMS`                   |
#     |                                                                         |
#     | Determines fuel burn from the project in each timepoint based on its    |
#     | heat rate curve.                                                        |
#     +-------------------------------------------------------------------------+
#     | | :code:`Fuel_Blending_Opr_Fuel_Burn_Constraint`                        |
#     | | *Defined over*: :code:`FUEL_PRJ_OPR_TMPS`                             |
#     |                                                                         |
#     | The sum of operations fuel burn across all fuels should equal the total |
#     | operations fuel burn.                                                   |
#     +-------------------------------------------------------------------------+
#     | | :code:`Fuel_Blending_Startup_Fuel_Burn_Constraint`                    |
#     | | *Defined over*: :code:`STARTUP_FUEL_PRJ_OPR_TMPS`                     |
#     |                                                                         |
#     | The sum of startup fuel burn across all fuels should equal the total    |
#     | operations fuel burn.                                                   |
#     +-------------------------------------------------------------------------+
#
#     """
#
#     # Dynamic Inputs
#     ###########################################################################
#
#     required_operational_modules = get_required_subtype_modules(
#         scenario_directory=scenario_directory,
#         subproblem=subproblem,
#         stage=stage,
#         which_type="operational_type",
#     )
#
#     imported_operational_modules = load_operational_type_modules(
#         required_operational_modules
#     )
#
#     # Sets
#     ###########################################################################
#
#     m.FUEL_PRJ_OPR_TMPS = Set(
#         dimen=2,
#         within=m.PRJ_OPR_TMPS,
#         initialize=lambda mod: sorted([
#             (p, tmp) for (p, tmp) in mod.PRJ_OPR_TMPS if p in mod.FUEL_PRJS
#         ]),
#     )
#
#     m.FUEL_PRJS_FUEL_OPR_TMPS = Set(
#         dimen=3,
#         initialize=lambda mod: sorted(list(set(
#             (g, f, tmp)
#             for (g, tmp) in mod.FUEL_PRJ_OPR_TMPS
#             for _g, f in mod.FUEL_PRJ_FUELS
#             if g == _g
#         ))),
#     )
#
#     m.FUEL_PRJS_FUEL_GROUP_OPR_TMPS = Set(
#         dimen=3,
#         initialize=lambda mod: sorted(list(set(
#             (g, fg, tmp)
#             for (g, tmp) in mod.FUEL_PRJ_OPR_TMPS
#             for _g, fg, f in mod.FUEL_PRJ_FUELS_FUEL_GROUP
#             if g == _g
#         ))),
#     )
#
#     m.HR_CURVE_PRJS_OPR_TMPS_SGMS = Set(
#         dimen=3,
#         initialize=lambda mod: sorted(list(set(
#             (g, tmp, s)
#             for (g, tmp) in mod.PRJ_OPR_TMPS
#             for _g, p, s in mod.HR_CURVE_PRJS_PRDS_SGMS
#             if g == _g and mod.period[tmp] == p
#         ))),
#     )
#
#     m.HR_CURVE_PRJS_OPR_TMPS = Set(
#         dimen=2,
#         within=m.FUEL_PRJ_OPR_TMPS,
#         initialize=lambda mod: sorted(list(set(
#             (g, tmp) for (g, tmp, s) in mod.HR_CURVE_PRJS_OPR_TMPS_SGMS
#         ))),
#     )
#
#     m.STARTUP_FUEL_PRJ_OPR_TMPS = Set(
#         dimen=2,
#         within=m.FUEL_PRJ_OPR_TMPS,
#         initialize=lambda mod: sorted([
#             (p, tmp) for (p, tmp) in mod.FUEL_PRJ_OPR_TMPS if p in mod.STARTUP_FUEL_PRJS
#         ]),
#     )
#
#     m.STARTUP_FUEL_PRJS_FUEL_OPR_TMPS = Set(
#         dimen=3,
#         initialize=lambda mod: sorted(list(set(
#             (g, f, tmp)
#             for (g, tmp) in mod.STARTUP_FUEL_PRJ_OPR_TMPS
#             for _g, f in mod.FUEL_PRJ_FUELS
#             if g == _g
#         ))),
#     )
#
#     # Params
#     m.min_fraction_in_fuel_blend = Param(
#         m.FUEL_PRJ_FUELS, within=PercentFraction, default=0
#     )
#
#     m.max_fraction_in_fuel_blend = Param(
#         m.FUEL_PRJ_FUELS, within=PercentFraction, default=1
#     )
#
#     # Variables
#     ###########################################################################
#
#     m.HR_Curve_Prj_Fuel_Burn = Var(m.HR_CURVE_PRJS_OPR_TMPS, within=NonNegativeReals)
#
#     m.Project_Opr_Fuel_Burn_by_Fuel = Var(
#         m.FUEL_PRJS_FUEL_OPR_TMPS, within=NonNegativeReals
#     )
#
#     m.Project_Startup_Fuel_Burn_by_Fuel = Var(
#         m.STARTUP_FUEL_PRJS_FUEL_OPR_TMPS, within=NonNegativeReals
#     )
#
#     m.Project_Fuel_Contribution_by_Fuel = Param(
#         m.FUEL_PRJS_FUEL_OPR_TMPS, within=NonNegativeReals, default=0
#     )
#
#     # Expressions
#     ###########################################################################
#
#     def fuel_burn_rule(mod, prj, tmp):
#         """
#         Emissions from each project based on operational type
#         (and whether a project burns fuel)
#         """
#         op_type = mod.operational_type[prj]
#         if hasattr(imported_operational_modules[op_type], "fuel_burn_rule"):
#             fuel_burn_simple = imported_operational_modules[op_type].fuel_burn_rule(
#                 mod, prj, tmp
#             )
#         else:
#             fuel_burn_simple = op_type_init.fuel_burn_rule(mod, prj, tmp)
#
#         return fuel_burn_simple + (
#             mod.HR_Curve_Prj_Fuel_Burn[prj, tmp] if prj in mod.HR_CURVE_PRJS else 0
#         )
#
#     m.Operations_Fuel_Burn_MMBtu = Expression(m.FUEL_PRJ_OPR_TMPS, rule=fuel_burn_rule)
#
#     def startup_fuel_burn_rule(mod, prj, tmp):
#         """
#         Startup fuel burn is defined for some operational types while
#         they are zero for others. Get the appropriate expression for each
#         generator based on its operational type.
#         """
#         op_type = mod.operational_type[prj]
#         if hasattr(imported_operational_modules[op_type], "startup_fuel_burn_rule"):
#             return imported_operational_modules[op_type].startup_fuel_burn_rule(
#                 mod, prj, tmp
#             )
#         else:
#             return op_type_init.startup_fuel_burn_rule(mod, prj, tmp)
#
#     m.Startup_Fuel_Burn_MMBtu = Expression(
#         m.STARTUP_FUEL_PRJ_OPR_TMPS, rule=startup_fuel_burn_rule
#     )
#
#     def total_fuel_burn_by_fuel_rule(mod, g, f, tmp):
#         """
#         *Expression Name*: :code:`Total_Fuel_Burn_by_Fuel_MMBtu`
#         *Defined Over*: :code:`PRJ_OPR_TMPS`
#
#         Total fuel burn is the sum of operational fuel burn (power production)
#         and startup fuel burn.
#         """
#         return mod.Project_Opr_Fuel_Burn_by_Fuel[g, f, tmp] + (
#             mod.Project_Startup_Fuel_Burn_by_Fuel[g, f, tmp]
#             if g in mod.STARTUP_FUEL_PRJS
#             else 0
#         )
#
#     m.Total_Fuel_Burn_by_Fuel_MMBtu = Expression(
#         m.FUEL_PRJS_FUEL_OPR_TMPS, rule=total_fuel_burn_by_fuel_rule
#     )
#
#     def fuel_contribution_rule(mod, prj, tmp):
#         """
#         Fuel contribution from each fuel project based on operational type.
#         """
#         op_type = mod.operational_type[prj]
#         if hasattr(imported_operational_modules[op_type], "fuel_contribution_rule"):
#             fuel_contribution = imported_operational_modules[
#                 op_type
#             ].fuel_contribution_rule(mod, prj, tmp)
#         else:
#             fuel_contribution = op_type_init.fuel_contribution_rule(mod, prj, tmp)
#
#         return fuel_contribution
#
#     m.Fuel_Contribution_FuelUnit = Expression(
#         m.FUEL_PRJ_OPR_TMPS, rule=fuel_contribution_rule
#     )
#
#     # Fuel groups by project; we put limits on total fuel burn for grouped fuels
#     def opr_fuel_burn_by_fuel_group_rule(mod, g, fg, tmp):
#         """
#         *Expression Name*: :code:`Opr_Fuel_Burn_by_Fuel_Group_MMBtu`
#         *Defined Over*: :code:`FUEL_PRJS_FUEL_GROUP_OPR_TMPS`
#
#         Operating fuel burn per fuel group is the sum of operating fuel burn by fuel group.
#         """
#         return sum(
#             mod.Project_Opr_Fuel_Burn_by_Fuel[g, f, tmp]
#             for (_g, _fg, f) in mod.FUEL_PRJ_FUELS_FUEL_GROUP
#             if f in mod.FUELS_BY_FUEL_GROUP[fg] and fg == _fg and g == _g
#         )
#
#     m.Opr_Fuel_Burn_by_Fuel_Group_MMBtu = Expression(
#         m.FUEL_PRJS_FUEL_GROUP_OPR_TMPS, rule=opr_fuel_burn_by_fuel_group_rule
#     )
#
#     # Constraints
#     ###########################################################################
#
#     def fuel_burn_by_ll_constraint_rule(mod, prj, tmp, s):
#         """
#         **Constraint Name**: HR_Curve_Prj_Fuel_Burn_Constraint
#         **Enforced Over**: HR_CURVE_PRJS_OPR_TMPS_SGMS
#
#         Fuel burn is set by piecewise linear representation of input/output
#         curve.
#
#         Note: we assume that when projects are de-rated for availability, the
#         input/output curve is de-rated by the same amount. The implicit
#         assumption is that when a generator is de-rated, some of its units
#         are out rather than it being forced to run below minimum stable level
#         at very inefficient operating points.
#         """
#         gen_op_type = mod.operational_type[prj]
#         if hasattr(imported_operational_modules[gen_op_type], "fuel_burn_by_ll_rule"):
#             fuel_burn_by_ll = imported_operational_modules[
#                 gen_op_type
#             ].fuel_burn_by_ll_rule(mod, prj, tmp, s)
#         else:
#             fuel_burn_by_ll = op_type_init.fuel_burn_by_ll_rule(mod, prj, tmp, s)
#
#         return mod.HR_Curve_Prj_Fuel_Burn[prj, tmp] >= fuel_burn_by_ll
#
#     m.HR_Curve_Prj_Fuel_Burn_Constraint = Constraint(
#         m.HR_CURVE_PRJS_OPR_TMPS_SGMS, rule=fuel_burn_by_ll_constraint_rule
#     )
#
#     def blend_fuel_operations_rule(mod, prj, tmp):
#         """
#         The sum of operations fuel burn across all fuels should equal the total
#         operations fuel burn.
#         """
#         return (
#             sum(
#                 mod.Project_Opr_Fuel_Burn_by_Fuel[prj, f, tmp]
#                 for f in mod.FUELS_BY_PRJ[prj]
#             )
#             == mod.Operations_Fuel_Burn_MMBtu[prj, tmp]
#         )
#
#     m.Fuel_Blending_Opr_Fuel_Burn_Constraint = Constraint(
#         m.FUEL_PRJ_OPR_TMPS, rule=blend_fuel_operations_rule
#     )
#     #
#     # def min_fraction_of_fuel_blend_opr_rule(mod, prj, f, tmp):
#     #     """
#     #     In each timepoint, enforce a minimum on the proportion in the blend of each
#     #     fuel.
#     #     """
#     #     return (
#     #         mod.Project_Opr_Fuel_Burn_by_Fuel[prj, f, tmp]
#     #         >= mod.min_fraction_in_fuel_blend[prj, f]
#     #         * mod.Operations_Fuel_Burn_MMBtu[prj, tmp]
#     #     )
#     #
#     # m.Min_Fuel_Fraction_of_Blend_Opr_Constraint = Constraint(
#     #     m.FUEL_PRJS_FUEL_OPR_TMPS, rule=min_fraction_of_fuel_blend_opr_rule
#     # )
#     #
#     # def max_fraction_of_fuel_blend_opr_rule(mod, prj, f, tmp):
#     #     """
#     #     In each timepoint, enforce a maximum on the proportion in the blend of each
#     #     fuel.
#     #     """
#     #     return (
#     #         mod.Project_Opr_Fuel_Burn_by_Fuel[prj, f, tmp]
#     #         <= mod.max_fraction_in_fuel_blend[prj, f]
#     #         * mod.Operations_Fuel_Burn_MMBtu[prj, tmp]
#     #     )
#     #
#     # m.Max_Fuel_Fraction_of_Blend_Opr_Constraint = Constraint(
#     #     m.FUEL_PRJS_FUEL_OPR_TMPS, rule=max_fraction_of_fuel_blend_opr_rule
#     # )
#     #
#     # def blend_fuel_startup_rule(mod, prj, tmp):
#     #     """
#     #     The sum of startup fuel burn across all fuels should equal the total
#     #     operations fuel burn.
#     #     """
#     #     return (
#     #         sum(
#     #             mod.Project_Startup_Fuel_Burn_by_Fuel[prj, f, tmp]
#     #             for f in mod.FUELS_BY_PRJ[prj]
#     #         )
#     #         == mod.Startup_Fuel_Burn_MMBtu[prj, tmp]
#     #     )
#     #
#     # m.Fuel_Blending_Startup_Fuel_Burn_Constraint = Constraint(
#     #     m.STARTUP_FUEL_PRJ_OPR_TMPS, rule=blend_fuel_startup_rule
#     # )
#     #
#     # def min_fraction_of_fuel_blend_startup_rule(mod, prj, f, tmp):
#     #     """
#     #     In each timepoint, enforce a minimum on the proportion in the blend of each
#     #     fuel.
#     #     """
#     #     return (
#     #         mod.Project_Startup_Fuel_Burn_by_Fuel[prj, f, tmp]
#     #         >= mod.min_fraction_in_fuel_blend[prj, f]
#     #         * mod.Startup_Fuel_Burn_MMBtu[prj, tmp]
#     #     )
#     #
#     # m.Min_Fuel_Fraction_of_Blend_Startup_Constraint = Constraint(
#     #     m.STARTUP_FUEL_PRJS_FUEL_OPR_TMPS, rule=min_fraction_of_fuel_blend_startup_rule
#     # )
#     #
#     # def max_fraction_of_fuel_blend_startup_rule(mod, prj, f, tmp):
#     #     """
#     #     In each timepoint, enforce a maximum on the proportion in the blend of each
#     #     fuel.
#     #     """
#     #     return (
#     #         mod.Project_Startup_Fuel_Burn_by_Fuel[prj, f, tmp]
#     #         <= mod.max_fraction_in_fuel_blend[prj, f]
#     #         * mod.Startup_Fuel_Burn_MMBtu[prj, tmp]
#     #     )
#     #
#     # m.Max_Fuel_Fraction_of_Blend_Startup_Constraint = Constraint(
#     #     m.STARTUP_FUEL_PRJS_FUEL_OPR_TMPS, rule=max_fraction_of_fuel_blend_startup_rule
#     # )
#     #
#     # Constrain blending for fuel contributions
#     # def blend_fuel_contributions_rule(mod, prj, tmp):
#     #     """
#     #     The sum of operations fuel contributions across all fuels should equal the total
#     #     operations fuel contribution.
#     #     """
#     #     return (
#     #         sum(
#     #             mod.Project_Fuel_Contribution_by_Fuel[prj, f, tmp]
#     #             for f in mod.FUELS_BY_PRJ[prj]
#     #         )
#     #         == mod.Fuel_Contribution_FuelUnit[prj, tmp]
#     #     )
#     #
#     # m.Fuel_Blending_Opr_Fuel_Contribution_Constraint = Constraint(
#     #     m.FUEL_PRJ_OPR_TMPS, rule=blend_fuel_contributions_rule
#     # )
#
#     # def min_fraction_of_fuel_blend_contribution_rule(mod, prj, f, tmp):
#     #     """
#     #     In each timepoint, enforce a minimum on the proportion in the blend of each
#     #     fuel.
#     #     """
#     #     return (
#     #         mod.Project_Fuel_Contribution_by_Fuel[prj, f, tmp]
#     #         >= mod.min_fraction_in_fuel_blend[prj, f]
#     #         * mod.Fuel_Contribution_FuelUnit[prj, tmp]
#     #     )
#     #
#     # m.Min_Fuel_Fraction_of_Blend_Contribution_Constraint = Constraint(
#     #     m.FUEL_PRJS_FUEL_OPR_TMPS, rule=min_fraction_of_fuel_blend_contribution_rule
#     # )
#     #
#     # def max_fraction_of_fuel_blend_contribution_rule(mod, prj, f, tmp):
#     #     """
#     #     In each timepoint, enforce a maximum on the proportion in the blend of each
#     #     fuel.
#     #     """
#     #     return (
#     #         mod.Project_Fuel_Contribution_by_Fuel[prj, f, tmp]
#     #         <= mod.max_fraction_in_fuel_blend[prj, f]
#     #         * mod.Fuel_Contribution_FuelUnit[prj, tmp]
#     #     )
#     #
#     # m.Max_Fuel_Fraction_of_Blend_Contribution_Constraint = Constraint(
#     #     m.FUEL_PRJS_FUEL_OPR_TMPS, rule=max_fraction_of_fuel_blend_contribution_rule
#     # )
#
#
# # Input-Output
# ###############################################################################
#
#
# def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
#     """
#
#     :param m:
#     :param d:
#     :param data_portal:
#     :param scenario_directory:
#     :param subproblem:
#     :param stage:
#     :return:
#     """
#     project_fuels_file = os.path.join(
#         scenario_directory, str(subproblem), str(stage), "inputs", "project_fuels.tab"
#     )
#     if os.path.exists(project_fuels_file):
#         data_portal.load(
#             filename=project_fuels_file,
#             index=m.FUEL_PRJ_FUELS,
#             param=(
#                 m.min_fraction_in_fuel_blend,
#                 m.max_fraction_in_fuel_blend,
#             ),
#         )
#
#
# def export_results(scenario_directory, subproblem, stage, m, d):
#     """
#     Export fuel burn results.
#     :param scenario_directory:
#     :param subproblem:
#     :param stage:
#     :param m:
#     The Pyomo abstract model
#     :param d:
#     Dynamic components
#     :return:
#     Nothing
#     """
#
#     with open(
#         os.path.join(
#             scenario_directory,
#             str(subproblem),
#             str(stage),
#             "results",
#             "project_fuel_burn.csv",
#         ),
#         "w",
#         newline="",
#     ) as results_f:
#         writer = csv.writer(results_f)
#         writer.writerow(
#             [
#                 "project",
#                 "period",
#                 "horizon",
#                 "timepoint",
#                 "timepoint_weight",
#                 "number_of_hours_in_timepoint",
#                 "load_zone",
#                 "technology",
#                 "fuel",
#                 "operations_fuel_burn_mmbtu",
#                 "startup_fuel_burn_mmbtu",
#                 "total_fuel_burn_mmbtu",
#                 "fuel_contribution_fuelunit",
#                 "net_fuel_burn_fuelunit",
#             ]
#         )
#         for p, f, tmp in sorted(m.FUEL_PRJS_FUEL_OPR_TMPS):
#             writer.writerow(
#                 [
#                     p,
#                     m.period[tmp],
#                     m.horizon[tmp, m.balancing_type_project[p]],
#                     tmp,
#                     m.tmp_weight[tmp],
#                     m.hrs_in_tmp[tmp],
#                     m.load_zone[p],
#                     m.technology[p],
#                     f,
#                     value(m.Project_Opr_Fuel_Burn_by_Fuel[p, f, tmp]),
#                     value(m.Project_Startup_Fuel_Burn_by_Fuel[p, f, tmp])
#                     if p in m.STARTUP_FUEL_PRJS
#                     else None,
#                     value(m.Total_Fuel_Burn_by_Fuel_MMBtu[p, f, tmp]),
#                     value(m.Project_Fuel_Contribution_by_Fuel[p, f, tmp]),
#                     (
#                         value(m.Total_Fuel_Burn_by_Fuel_MMBtu[p, f, tmp])
#                         - value(m.Project_Fuel_Contribution_by_Fuel[p, f, tmp])
#                     ),
#                 ]
#             )
#
#
# # Database
# ###############################################################################
#
#
# def import_results_into_database(
#     scenario_id, subproblem, stage, c, db, results_directory, quiet
# ):
#     """
#
#     :param scenario_id:
#     :param c:
#     :param db:
#     :param results_directory:
#     :param quiet:
#     :return:
#     """
#     import_csv(
#         conn=db,
#         cursor=c,
#         scenario_id=scenario_id,
#         subproblem=subproblem,
#         stage=stage,
#         quiet=quiet,
#         results_directory=results_directory,
#         which_results="project_fuel_burn",
#     )
