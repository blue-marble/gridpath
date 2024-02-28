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

"""
Subsidy programs (e.g. investment tax credits).
"""
import csv
import os.path
from pyomo.environ import (
    Set,
    Param,
    Var,
    Expression,
    Constraint,
    NonNegativeReals,
    Boolean,
    value,
)

from gridpath.auxiliary.auxiliary import get_required_subtype_modules
from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.project.capacity.common_functions import (
    load_project_capacity_type_modules,
)
import gridpath.project.capacity.capacity_types as cap_type_init
import gridpath.transmission.capacity.capacity_types as tx_cap_type_init


def add_model_components(
    m,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """

    :param m:
    :param d:
    :return:
    """
    # First, check if we have transmission lines, so that we know whether to
    # include them in the sets below
    include_tx_lines = True if hasattr(m, "TX_LINES") else False

    # We'll need the project vintages financial in each period
    required_capacity_modules = get_required_subtype_modules(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        which_type="capacity_type",
    )

    # Add transmission capacity types if transmission feature is included
    required_tx_capacity_modules = (
        get_required_subtype_modules(
            scenario_directory=scenario_directory,
            weather_iteration=weather_iteration,
            hydro_iteration=hydro_iteration,
            availability_iteration=availability_iteration,
            subproblem=subproblem,
            stage=stage,
            which_type="tx_capacity_type",
            prj_or_tx="transmission_line",
        )
        if include_tx_lines
        else []
    )

    # Import needed capacity type modules
    imported_capacity_modules = load_project_capacity_type_modules(
        required_capacity_modules
    )

    imported_tx_capacity_modules = load_project_capacity_type_modules(
        required_tx_capacity_modules, prj_or_tx="transmission"
    )

    # TODO: make this work with all new capacity types; will need to standardize set
    #  names
    def get_vintages_fin_in_period(mod, p):
        fin_periods = []
        if hasattr(mod, "GEN_NEW_LIN_VNTS_FIN_IN_PERIOD"):
            fin_periods += [
                (prj, v) for (prj, v) in mod.GEN_NEW_LIN_VNTS_FIN_IN_PERIOD[p]
            ]

        if hasattr(mod, "STOR_NEW_LIN_VNTS_FIN_IN_PRD"):
            fin_periods += [
                (prj, v) for (prj, v) in mod.STOR_NEW_LIN_VNTS_FIN_IN_PRD[p]
            ]

        return fin_periods

    m.PRJ_VNTS_FIN_IN_PERIOD = Set(
        m.PERIODS,
        dimen=2,
        within=m.PROJECTS * m.PERIODS,
        initialize=lambda mod, p: get_vintages_fin_in_period(mod, p),
    )

    def get_tx_vintages_fin_in_period(mod, p):
        fin_periods = []
        if hasattr(mod, "TX_NEW_LIN_VNTS_FIN_IN_PRD"):
            fin_periods += [(prj, v) for (prj, v) in mod.TX_NEW_LIN_VNTS_FIN_IN_PRD[p]]

        return fin_periods

    m.TX_VNTS_FIN_IN_PERIOD = Set(
        m.PERIODS,
        dimen=2,
        within=m.TX_LINES * m.PERIODS if include_tx_lines else [],
        initialize=lambda mod, p: get_tx_vintages_fin_in_period(mod, p),
    )

    m.PRJ_OR_TX_VNTS_FIN_IN_PERIOD = Set(
        m.PERIODS,
        initialize=lambda mod, prd: [prj for prj in mod.PRJ_VNTS_FIN_IN_PERIOD[prd]]
        + [tx for tx in mod.TX_VNTS_FIN_IN_PERIOD[prd]],
    )

    # Make a set of all projects and Tx lines
    m.PROJECTS_TX_LINES = Set(
        initialize=lambda mod: [prj for prj in mod.PROJECTS]
        + ([tx for tx in mod.TX_LINES] if hasattr(mod, "TX_LINES") else [])
    )

    # Define programs
    m.PROGRAM_SUPERPERIODS = Set(dimen=2)
    m.program_budget = Param(m.PROGRAM_SUPERPERIODS, within=NonNegativeReals)

    m.PROGRAMS = Set(
        initialize=lambda mod: sorted(
            list(set(prg for (prg, prd) in mod.PROGRAM_SUPERPERIODS))
        )
    )

    m.PROGRAM_PROJECT_OR_TX_VINTAGES = Set(
        dimen=3, within=m.PROGRAMS * m.PROJECTS_TX_LINES * m.PERIODS
    )

    m.PROGRAM_VINTAGES_BY_PROJECT_OR_TX_LINE = Set(
        m.PROJECTS_TX_LINES,
        initialize=lambda mod, project: sorted(
            list(
                set(
                    [
                        (prg, v)
                        for (prg, prj, v) in mod.PROGRAM_PROJECT_OR_TX_VINTAGES
                        if prj == project
                    ]
                )
            ),
        ),
    )

    m.PROJECT_OR_TX_VINTAGES_BY_PROGRAM = Set(
        m.PROGRAMS,
        initialize=lambda mod, program: sorted(
            list(
                set(
                    [
                        (prj, v)
                        for (prg, prj, v) in mod.PROGRAM_PROJECT_OR_TX_VINTAGES
                        if prg == program
                    ]
                )
            ),
        ),
    )

    m.is_tx = Param(m.PROGRAM_PROJECT_OR_TX_VINTAGES, within=Boolean)
    m.annual_payment_subsidy = Param(
        m.PROGRAM_PROJECT_OR_TX_VINTAGES, within=NonNegativeReals
    )

    m.Subsidize_MW = Var(m.PROGRAM_PROJECT_OR_TX_VINTAGES, within=NonNegativeReals)

    # TODO: this is copied and pasted from potential module, should factor out
    def new_capacity_rule_project_or_tx(mod, prg, prj_or_tx, prd):
        if not mod.is_tx[prg, prj_or_tx, prd]:
            cap_type = mod.capacity_type[prj_or_tx]
            # The capacity type modules check if this period is a "vintage" for
            # this project and return 0 if not
            if hasattr(imported_capacity_modules[cap_type], "new_capacity_rule"):
                return imported_capacity_modules[cap_type].new_capacity_rule(
                    mod, prj_or_tx, prd
                )
            else:
                return cap_type_init.new_capacity_rule(mod, prj_or_tx, prd)
        else:
            tx_cap_type = mod.tx_capacity_type[prj_or_tx]
            # The capacity type modules check if this period is a "vintage" for
            # this project and return 0 if not
            if hasattr(imported_tx_capacity_modules[tx_cap_type], "new_capacity_rule"):
                return imported_tx_capacity_modules[tx_cap_type].new_capacity_rule(
                    mod, prj_or_tx, prd
                )
            else:
                return tx_cap_type_init.new_capacity_rule(mod, prj_or_tx, prd)

    # TODO: add subsidy per MWh
    def new_energy_capacity_rule(mod, prj, prd):
        cap_type = mod.capacity_type[prj]
        # The capacity type modules check if this period is a "vintage" for
        # this project and return 0 if not
        if hasattr(imported_capacity_modules[cap_type], "new_energy_capacity_rule"):
            return imported_capacity_modules[cap_type].new_energy_capacity_rule(
                mod, prj, prd
            )
        else:
            return cap_type_init.new_energy_capacity_rule(mod, prj, prd)

    def max_subsidized_rule(mod, prg, prj_or_tx, v):
        """Can't subsidize more capacity than has been built in this period."""
        return mod.Subsidize_MW[prg, prj_or_tx, v] <= new_capacity_rule_project_or_tx(
            mod, prg, prj_or_tx, v
        )

    m.Max_Subsidized_MW = Constraint(
        m.PROGRAM_PROJECT_OR_TX_VINTAGES, rule=max_subsidized_rule
    )

    def total_annual_payment_reduction(mod, prj_or_tx, prd):
        return sum(
            mod.Subsidize_MW[prg, prj_or_tx, v]
            * mod.annual_payment_subsidy[prg, prj_or_tx, v]
            for (project, v) in mod.PRJ_OR_TX_VNTS_FIN_IN_PERIOD[prd]
            for (prg, vintage) in mod.PROGRAM_VINTAGES_BY_PROJECT_OR_TX_LINE[prj_or_tx]
            if vintage == v and project == prj_or_tx
        )

    m.Project_Annual_Payment_Reduction_from_Base = Expression(
        m.PRJ_FIN_PRDS, initialize=total_annual_payment_reduction
    )
    if include_tx_lines:
        m.Tx_Annual_Payment_Reduction_from_Base = Expression(
            m.TX_FIN_PRDS, initialize=total_annual_payment_reduction
        )

    def max_program_budget_rule(mod, prg, superperiod):
        periods_in_superperiod = [
            prd for (s_prd, prd) in mod.SUPERPERIOD_PERIODS if s_prd == superperiod
        ]
        # Projects that can be subsidized in this superperiod
        projects_subsidized_in_superperiod = [
            (prj, v)
            for (prj, v) in mod.PROJECT_OR_TX_VINTAGES_BY_PROGRAM[prg]
            if v in periods_in_superperiod
        ]
        if projects_subsidized_in_superperiod:
            return (
                sum(
                    mod.Subsidize_MW[prg, prj_or_tx_line, v]
                    * mod.annual_payment_subsidy[prg, prj_or_tx_line, v]
                    * getattr(
                        mod,
                        "{capacity_type}_financial_lifetime_yrs_by_vintage".format(
                            capacity_type=(
                                mod.capacity_type[prj_or_tx_line]
                                if not mod.is_tx[prg, prj_or_tx_line, v]
                                else mod.tx_capacity_type[prj_or_tx_line]
                            )
                        ),
                    )[prj_or_tx_line, v]
                    for (prj_or_tx_line, v) in mod.PROJECT_OR_TX_VINTAGES_BY_PROGRAM[
                        prg
                    ]
                    if v in periods_in_superperiod
                )
                <= mod.program_budget[prg, superperiod]
            )
        else:
            return Constraint.Feasible

    m.Max_Program_Budget_in_Period_Constraint = Constraint(
        m.PROGRAM_SUPERPERIODS, rule=max_program_budget_rule
    )


# ### Input-Output ### #
def load_model_data(
    m,
    d,
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """ """
    # Only load data if the input files were written; otehrwise, we won't
    # initialize the components in this module

    budgets_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "subsidies_program_budgets.tab",
    )
    data_portal.load(
        filename=budgets_file,
        index=m.PROGRAM_SUPERPERIODS,
        param=m.program_budget,
    )

    prj_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "subsidies_projects.tab",
    )
    data_portal.load(
        filename=prj_file,
        index=m.PROGRAM_PROJECT_OR_TX_VINTAGES,
        param=(
            m.is_tx,
            m.annual_payment_subsidy,
        ),
    )


def export_results(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    m,
    d,
):
    """ """
    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "results",
            "subsidies.csv",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "program",
                "project_or_tx",
                "vintage",
                "is_tx",
                "subsidized_mw",
            ]
        )
        for prg, prj_or_tx, v in m.PROGRAM_PROJECT_OR_TX_VINTAGES:
            writer.writerow(
                [
                    prg,
                    prj_or_tx,
                    v,
                    m.is_tx[prg, prj_or_tx, v],
                    value(m.Subsidize_MW[prg, prj_or_tx, v]),
                ]
            )


# ### Database ### #
def get_inputs_from_database(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    c1 = conn.cursor()
    program_budgets = c1.execute(
        """
        SELECT program, superperiod, program_budget
        FROM inputs_system_subsidies
        WHERE subsidy_scenario_id = {subsidy_scenario_id}
        AND superperiod in (
        SELECT superperiod FROM inputs_temporal_superperiods
        WHERE temporal_scenario_id = {temporal_scenario_id})
        """.format(
            subsidy_scenario_id=subscenarios.SUBSIDY_SCENARIO_ID,
            temporal_scenario_id=subscenarios.TEMPORAL_SCENARIO_ID,
        )
    )

    c2 = conn.cursor()
    project_subsidies = c2.execute(
        f"""
        SELECT program, project_or_tx, vintage, is_tx, 
        annual_payment_subsidy
        FROM inputs_system_subsidies_projects
        WHERE subsidy_scenario_id = {subscenarios.SUBSIDY_SCENARIO_ID}
        AND (
            project_or_tx in (
            SELECT project FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID}
            ) OR 
            project_or_tx in (
                SELECT transmission_line FROM inputs_transmission_portfolios
                WHERE transmission_portfolio_scenario_id = 
                {subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID}
            )
        )
        AND vintage in (
        SELECT period FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID})
        """
    )

    return program_budgets, project_subsidies


def write_model_inputs(
    scenario_directory,
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """ """

    (
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
    ) = directories_to_db_values(
        weather_iteration, hydro_iteration, availability_iteration, subproblem, stage
    )

    program_budgets, project_subsidies = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "subsidies_program_budgets.tab",
        ),
        "w",
        newline="",
    ) as req_file:
        writer = csv.writer(req_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "program",
                "superperiod",
                "program_budget",
            ]
        )

        for row in program_budgets:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "subsidies_projects.tab",
        ),
        "w",
        newline="",
    ) as req_file:
        writer = csv.writer(req_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "program",
                "project_or_tx",
                "period",
                "is_tx",
                "annual_payment_subsidy",
            ]
        )

        for row in project_subsidies:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
