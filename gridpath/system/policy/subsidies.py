# Copyright 2016-2022 Blue Marble Analytics LLC.
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
    value,
)

from gridpath.auxiliary.auxiliary import get_required_subtype_modules
from gridpath.project.capacity.common_functions import (
    load_project_capacity_type_modules,
)
import gridpath.project.capacity.capacity_types as cap_type_init


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """
    # We'll need the project vintages financial in each period
    required_capacity_modules = get_required_subtype_modules(
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        which_type="capacity_type",
    )

    # Import needed capacity type modules
    imported_capacity_modules = load_project_capacity_type_modules(
        required_capacity_modules
    )

    # TODO: make this work with all new capacity types; will need to standardize set
    #  names
    def get_vintages_fin_in_period(mod, p):
        # # Add any components specific to the capacity type modules
        # for op_m in required_capacity_modules:
        #     imp_op_m = imported_capacity_modules[op_m]
        #     if hasattr(imp_op_m, "vintages_fin_in_period_rule"):
        #         for p in mod.PERIODS:
        #             vintages_fin_in_period.update(
        #                 imp_op_m.vintages_fin_in_period_rule(mod, p)
        #             )
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

    # Define programs
    # TODO: currently requires budget to be specified for every period, I think
    m.PROGRAM_PERIODS = Set(dimen=2)
    m.program_budget = Param(m.PROGRAM_PERIODS, within=NonNegativeReals)

    m.PROGRAMS = Set(
        initialize=lambda mod: list(set(prg for (prg, prd) in mod.PROGRAM_PERIODS))
    )

    m.PROGRAM_PROJECT_VINTAGES = Set(
        dimen=3, within=m.PROGRAMS * m.PROJECTS * m.PERIODS
    )
    m.PROGRAM_ELIGIBLE_PROJECTS = Set(
        within=m.PROJECTS,
        initialize=lambda mod: list(
            set([prj for (prg, prj, v) in mod.PROGRAM_PROJECT_VINTAGES])
        ),
    )
    m.PROGRAM_VINTAGES_BY_PROJECT = Set(
        m.PROJECTS,
        initialize=lambda mod, project: list(
            set(
                [
                    (prg, v)
                    for (prg, prj, v) in mod.PROGRAM_PROJECT_VINTAGES
                    if prj == project
                ]
            )
        ),
    )

    m.PROJECT_VINTAGES_BY_PROGRAM = Set(
        m.PROGRAMS,
        initialize=lambda mod, program: list(
            set(
                [
                    (prj, v)
                    for (prg, prj, v) in mod.PROGRAM_PROJECT_VINTAGES
                    if prg == program
                ]
            )
        ),
    )

    m.annual_payment_subsidy = Param(
        m.PROGRAM_PROJECT_VINTAGES, within=NonNegativeReals
    )

    m.Subsidize_MW = Var(m.PROGRAM_PROJECT_VINTAGES, within=NonNegativeReals)

    # TODO: this is copied and pasted from potential module, should factor out
    def new_capacity_rule(mod, prj, prd):
        cap_type = mod.capacity_type[prj]
        # The capacity type modules check if this period is a "vintage" for
        # this project and return 0 if not
        if hasattr(imported_capacity_modules[cap_type], "new_capacity_rule"):
            return imported_capacity_modules[cap_type].new_capacity_rule(mod, prj, prd)
        else:
            return cap_type_init.new_capacity_rule(mod, prj, prd)

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

    def max_subsidized_rule(mod, prg, prj, v):
        """Can't subsidize more capacity than has been built in this period."""
        return mod.Subsidize_MW[prg, prj, v] <= new_capacity_rule(mod, prj, v)

    m.Max_Subsidized_MW = Constraint(
        m.PROGRAM_PROJECT_VINTAGES, rule=max_subsidized_rule
    )

    def total_annual_payment_reduction(mod, prj, prd):
        return sum(
            mod.Subsidize_MW[prg, prj, v] * mod.annual_payment_subsidy[prg, prj, v]
            for (project, v) in mod.PRJ_VNTS_FIN_IN_PERIOD[prd]
            for (prg, vintage) in mod.PROGRAM_VINTAGES_BY_PROJECT[prj]
            if vintage == v and project == prj
        )

    m.Project_Annual_Payment_Reduction_from_Base = Expression(
        m.PRJ_FIN_PRDS, initialize=total_annual_payment_reduction
    )

    def max_program_budget_rule(mod, prg, prd):
        projects_subsidized_in_period = [
            (prj, v) for (prj, v) in mod.PROJECT_VINTAGES_BY_PROGRAM[prg] if v == prd
        ]
        if projects_subsidized_in_period:  # projects to subsidize in period
            return (
                sum(
                    mod.Subsidize_MW[prg, prj, v]
                    * mod.annual_payment_subsidy[prg, prj, v]
                    * getattr(
                        mod,
                        "{capacity_type}_financial_lifetime_yrs_by_vintage".format(
                            capacity_type=mod.capacity_type[prj]
                        ),
                    )[prj, v]
                    for (prj, v) in mod.PROJECT_VINTAGES_BY_PROGRAM[prg]
                    if v == prd
                )
                <= mod.program_budget[prg, prd]
            )
        else:
            return Constraint.Feasible

    m.Max_Program_Budget_in_Period_Constraint = Constraint(
        m.PROGRAM_PERIODS, rule=max_program_budget_rule
    )


# ### Input-Output ### #
def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """ """
    # Only load data if the input files were written; otehrwise, we won't
    # initialize the components in this module

    budgets_file = os.path.join(
        scenario_directory,
        subproblem,
        stage,
        "inputs",
        "subsidies_program_budgets.tab",
    )
    data_portal.load(
        filename=budgets_file,
        index=m.PROGRAM_PERIODS,
        param=m.program_budget,
    )

    prj_file = os.path.join(
        scenario_directory, subproblem, stage, "inputs", "subsidies_projects.tab"
    )
    data_portal.load(
        filename=prj_file,
        index=m.PROGRAM_PROJECT_VINTAGES,
        param=m.annual_payment_subsidy,
    )


def export_results(scenario_directory, subproblem, stage, m, d):
    """ """
    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
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
                "project",
                "vintage",
                "subsidized_mw",
            ]
        )
        for prg, prj, v in m.PROGRAM_PROJECT_VINTAGES:
            writer.writerow(
                [
                    prg,
                    prj,
                    v,
                    value(m.Subsidize_MW[prg, prj, v]),
                ]
            )


# ### Database ### #
def get_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
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
        SELECT program, period, program_budget
        FROM inputs_system_subsidies
        WHERE subsidy_scenario_id = {subsidy_scenario_id}
        AND period in (
        SELECT period FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {temporal_scenario_id})
        """.format(
            subsidy_scenario_id=subscenarios.SUBSIDY_SCENARIO_ID,
            temporal_scenario_id=subscenarios.TEMPORAL_SCENARIO_ID,
        )
    )

    c2 = conn.cursor()
    project_subsidies = c2.execute(
        """
        SELECT program, project, vintage, annual_payment_subsidy
        FROM inputs_system_subsidies_projects
        WHERE subsidy_scenario_id = {subsidy_scenario_id}
        AND project in (
            SELECT project FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {portfolio_scenario_id}
        )
        AND vintage in (
        SELECT period FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {temporal_scenario_id})
        """.format(
            subsidy_scenario_id=subscenarios.SUBSIDY_SCENARIO_ID,
            portfolio_scenario_id=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            temporal_scenario_id=subscenarios.TEMPORAL_SCENARIO_ID,
        )
    )

    return program_budgets, project_subsidies


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """ """
    program_budgets, project_subsidies = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
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
                "period",
                "program_budget",
            ]
        )

        for row in program_budgets:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
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
                "project",
                "period",
                "annual_payment_subsidy",
            ]
        )

        for row in project_subsidies:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
