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
from pyomo.environ import Set, Param, Var, Expression, Constraint, NonNegativeReals

from gridpath.auxiliary.auxiliary import (
    get_required_subtype_modules_from_projects_file,
    join_sets,
)
from gridpath.auxiliary.dynamic_components import capacity_type_vintage_sets
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
    required_capacity_modules = get_required_subtype_modules_from_projects_file(
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        which_type="capacity_type",
    )

    # Import needed capacity type modules
    imported_capacity_modules = load_project_capacity_type_modules(
        required_capacity_modules
    )

    def get_vintages_fin_in_period(mod):
        get_vintages_fin_in_period = {}

        # Add any components specific to the capacity type modules
        for op_m in required_capacity_modules:
            imp_op_m = imported_capacity_modules[op_m]
            if hasattr(imp_op_m, "vintages_fin_in_period_rule"):
                for p in mod.PERIODS:
                    get_vintages_fin_in_period.update(
                        imp_op_m.vintages_fin_in_period_rule(mod, p)
                    )

    m.PRJ_VNTS_FIN_IN_PERIOD = Set(
        m.PERIODS,
        dimen=2,
        within=m.PROJECTS * m.PERIODS,
        initialize=get_vintages_fin_in_period,
    )

    # Define programs
    m.PROGRAMS = Set()

    m.program_budget = Param(m.PROGRAM, m.PERIODS, within=NonNegativeReals)

    m.PROGRAM_PROJECT_VINTAGES = Set(
        dimen=3, within=m.PROGRAMS * m.PROJECTS * m.PERIODS
    )
    m.PROGRAM_ELIGIBLE_PROJECTS = Set(
        within=m.PROJECTS,
        initialize=lambda mod: set(
            [prj for (prg, prj, v) in mod.PROGRAM_PROJECT_VINTAGES]
        ),
    )
    m.PROGRAMS_VINTAGES_BY_PROJECT = Set(
        m.PROJECTS,
        initialize=lambda mod, project, vintage: set(
            [
                prg
                for (prg, prj, v) in mod.PROGRAM_PROJECT_VINTAGES
                if (prj, v) == (project, vintage)
            ]
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
            for prg in mod.PROGRAM_VINTAGES_BY_PROJECT[prj]
            for (project, v) in mod.PRJ_VNTS_FIN_IN_PERIOD[prd]
            if project == prj
        )

    m.Project_Annual_Payment_Reduction_from_Base = Expression(
        m.PRJ_FIN_PRDS, initialize=total_annual_payment_reduction
    )
