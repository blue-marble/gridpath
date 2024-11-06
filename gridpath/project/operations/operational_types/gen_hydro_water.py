# Copyright 2016-2024 Blue Marble Analytics LLC.
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
This operational type describes the operations of hydro generation projects.
These projects can vary power output between a minimum and maximum level
specified for each horizon, and must produce a pre-specified amount of
energy on each horizon when they are available, some of which may be
curtailed. Negative output is allowed, i.e. this module can be used to model
pumping. The curtailable hydro projects can be allowed to provide upward
and/or downward reserves. Ramp rate limits can optionally be enforced.

Costs for this operational type include variable O&M costs.

"""

import csv
import os.path
from pyomo.environ import (
    Var,
    Set,
    Param,
    Constraint,
    Expression,
    NonNegativeReals,
    value,
    Reals,
    Any,
)

from gridpath.auxiliary.auxiliary import (
    subset_init_by_param_value,
    subset_init_by_set_membership,
)
from gridpath.auxiliary.dynamic_components import headroom_variables, footroom_variables
from gridpath.project.common_functions import (
    check_if_first_timepoint,
    check_boundary_type,
)
from gridpath.project.operations.operational_types.common_functions import (
    load_optype_model_data,
    check_for_tmps_to_link,
)
from gridpath.common_functions import create_results_df


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
    """ """
    # Sets
    ###########################################################################

    m.GEN_HYDRO_WATER = Set(
        within=m.PROJECTS,
        initialize=lambda mod: subset_init_by_param_value(
            mod, "PROJECTS", "operational_type", "gen_hydro_water"
        ),
    )

    m.GEN_HYDRO_WATER_OPR_TMPS = Set(
        dimen=2,
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: subset_init_by_set_membership(
            mod=mod,
            superset="PRJ_OPR_TMPS",
            index=0,
            membership_set=mod.GEN_HYDRO_WATER,
        ),
    )

    m.GEN_HYDRO_WATER_LINKED_TMPS = Set(dimen=2)

    # Required Params
    ###########################################################################

    m.gen_hydro_water_powerhouse = Param(m.GEN_HYDRO_WATER, within=m.POWERHOUSES)

    # Generator efficiency is a constant here, but is actually a function of
    # power output
    m.gen_hydro_water_generator_efficiency = Param(
        m.GEN_HYDRO_WATER, within=NonNegativeReals
    )

    # Linked Params
    ###########################################################################

    m.gen_hydro_water_linked_power = Param(m.GEN_HYDRO_WATER_LINKED_TMPS, within=Reals)

    m.gen_hydro_water_linked_curtailment = Param(
        m.GEN_HYDRO_WATER_LINKED_TMPS, within=NonNegativeReals
    )

    m.gen_hydro_water_linked_upwards_reserves = Param(
        m.GEN_HYDRO_WATER_LINKED_TMPS, within=NonNegativeReals
    )

    m.gen_hydro_water_linked_downwards_reserves = Param(
        m.GEN_HYDRO_WATER_LINKED_TMPS, within=NonNegativeReals
    )

    # Variables
    ###########################################################################

    m.GenHydroWater_Power_MW = Var(m.GEN_HYDRO_WATER_OPR_TMPS, within=Reals)

    # Expressions
    ###########################################################################

    def upwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp] for c in getattr(d, headroom_variables)[g])

    m.GenHydroWater_Upwards_Reserves_MW = Expression(
        m.GEN_HYDRO_WATER_OPR_TMPS, rule=upwards_reserve_rule
    )

    def downwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp] for c in getattr(d, footroom_variables)[g])

    m.GenHydroWater_Downwards_Reserves_MW = Expression(
        m.GEN_HYDRO_WATER_OPR_TMPS, rule=downwards_reserve_rule
    )

    # Constraints
    ###########################################################################

    m.Powerhouse_Based_Power_Constraint = Constraint(
        m.GEN_HYDRO_WATER_OPR_TMPS, rule=enforce_powerhouse_based_power_output
    )
    m.GenHydroWater_Max_Power_Constraint = Constraint(
        m.GEN_HYDRO_WATER_OPR_TMPS, rule=max_power_rule
    )

    m.GenHydroWater_Min_Power_Constraint = Constraint(
        m.GEN_HYDRO_WATER_OPR_TMPS, rule=min_power_rule
    )


# Constraint Formulation Rules
###############################################################################


def max_power_rule(mod, g, tmp):
    """
    **Constraint Name**: GenHydroWater_Max_Power_Constraint
    **Enforced Over**: GEN_HYDRO_WATER_OPR_BT_HRZS

    Power plus upward reserves shall not exceed the generator available
    capacity.

    """
    return (
        mod.GenHydroWater_Power_MW[g, tmp]
        + mod.GenHydroWater_Upwards_Reserves_MW[g, tmp]
        <= mod.Capacity_MW[g, mod.period[tmp]] * mod.Availability_Derate[g, tmp]
    )


def min_power_rule(mod, g, tmp):
    """
    **Constraint Name**: GenHydroWater_Min_Power_Constraint
    **Enforced Over**: GEN_HYDRO_WATER_OPR_BT_HRZS

    Can't provide more downward reserves than current power provision.
    """
    return (
        mod.GenHydroWater_Downwards_Reserves_MW[g, tmp]
        <= mod.GenHydroWater_Power_MW[g, tmp]
    )


def enforce_powerhouse_based_power_output(mod, g, tmp):
    return (
        mod.GenHydroWater_Power_MW[g, tmp]
        == mod.Powerhouse_Output_by_Generator[mod.gen_hydro_water_powerhouse[g], g, tmp]
        * mod.gen_hydro_water_generator_efficiency[g]
    )


# Operational Type Methods
###############################################################################


def power_provision_rule(mod, g, tmp):
    """
    Power provision from curtailable hydro is the gross power minus
    curtailment.
    """
    return mod.GenHydroWater_Power_MW[g, tmp]


def variable_om_cost_rule(mod, g, tmp):
    """
    Variable cost is incurred on all power produced (including what's
    curtailed).
    """
    return mod.GenHydroWater_Power_MW[g, tmp] * mod.variable_om_cost_per_mwh[g]


def variable_om_by_period_cost_rule(mod, prj, tmp):
    """ """
    return (
        mod.GenHydroWater_Power_MW[prj, tmp]
        * mod.variable_om_cost_per_mwh_by_period[prj, mod.period[tmp]]
    )


def power_delta_rule(mod, g, tmp):
    """
    This rule is only used in tuning costs, so fine to skip for linked
    horizon's first timepoint.
    """
    if check_if_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ) and (
        check_boundary_type(
            mod=mod,
            tmp=tmp,
            balancing_type=mod.balancing_type_project[g],
            boundary_type="linear",
        )
        or check_boundary_type(
            mod=mod,
            tmp=tmp,
            balancing_type=mod.balancing_type_project[g],
            boundary_type="linked",
        )
    ):
        pass
    else:
        return (
            mod.GenHydroWater_Power_MW[g, tmp]
            - mod.GenHydroWater_Power_MW[
                g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]
            ]
        )


# Input-Output
###############################################################################


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
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    # Determine list of projects load params from projects.tab (optional
    # ramp rates)
    projects = load_optype_model_data(
        mod=m,
        data_portal=data_portal,
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        op_type="gen_hydro_water",
    )

    # Linked timepoint params
    linked_inputs_filename = os.path.join(
        scenario_directory,
        subproblem,
        stage,
        "inputs",
        "gen_hydro_water_linked_timepoint_params.tab",
    )
    if os.path.exists(linked_inputs_filename):
        data_portal.load(
            filename=linked_inputs_filename,
            index=m.GEN_HYDRO_WATER_LINKED_TMPS,
            param=(
                m.gen_hydro_water_linked_power,
                m.gen_hydro_water_linked_upwards_reserves,
                m.gen_hydro_water_linked_downwards_reserves,
            ),
        )


def add_to_prj_tmp_results(mod):
    results_columns = ["power_mw"]
    data = [
        [
            prj,
            tmp,
            value(mod.GenHydroWater_Power_MW[prj, tmp]),
        ]
        for (prj, tmp) in mod.GEN_HYDRO_WATER_OPR_TMPS
    ]

    optype_dispatch_df = create_results_df(
        index_columns=["project", "timepoint"],
        results_columns=results_columns,
        data=data,
    )

    return results_columns, optype_dispatch_df


def export_results(
    mod,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param mod:
    :param d:
    :return:
    """

    # Dispatch results added to project_timepoint.csv via add_to_prj_tmp_results()

    # If there's a linked_subproblems_map CSV file, check which of the
    # current subproblem TMPS we should export results for to link to the
    # next subproblem
    tmps_to_link, tmp_linked_tmp_dict = check_for_tmps_to_link(
        scenario_directory=scenario_directory, subproblem=subproblem, stage=stage
    )

    # If the list of timepoints to link is not empty, write the linked
    # timepoint results for this module in the next subproblem's input
    # directory
    if tmps_to_link:
        next_subproblem = str(int(subproblem) + 1)

        # Export params by project and timepoint
        with open(
            os.path.join(
                scenario_directory,
                next_subproblem,
                stage,
                "inputs",
                "gen_hydro_water_linked_timepoint_params.tab",
            ),
            "w",
            newline="",
        ) as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")
            writer.writerow(
                [
                    "project",
                    "linked_timepoint",
                    "linked_provide_power",
                    "linked_upward_reserves",
                    "linked_downward_reserves",
                ]
            )
            for p, tmp in sorted(mod.GEN_HYDRO_WATER_OPR_TMPS):
                if tmp in tmps_to_link:
                    writer.writerow(
                        [
                            p,
                            tmp_linked_tmp_dict[tmp],
                            max(value(mod.GenHydroWater_Power_MW[p, tmp]), 0),
                            max(
                                value(mod.GenHydroWater_Upwards_Reserves_MW[p, tmp]), 0
                            ),
                            max(
                                value(mod.GenHydroWater_Downwards_Reserves_MW[p, tmp]),
                                0,
                            ),
                        ]
                    )


# Database
###############################################################################


# Validation
###############################################################################
def validate_inputs(
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
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    pass
