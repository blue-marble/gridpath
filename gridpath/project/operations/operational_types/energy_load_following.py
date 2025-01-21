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
This operational type shapes energy on a horizon basis, based on min power, 
max power, and total energy for the horizon. It limits total energy over the 
period to the Energy_MWh for the project.

"""

import csv
import os.path

import pandas as pd
from pyomo.environ import (
    Var,
    Set,
    Param,
    Constraint,
    Expression,
    NonNegativeReals,
    PercentFraction,
    value,
)
import warnings

from gridpath.auxiliary.auxiliary import (
    subset_init_by_param_value,
    subset_init_by_set_membership,
)
from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.auxiliary.dynamic_components import headroom_variables, footroom_variables
from gridpath.project.common_functions import (
    check_if_boundary_type_and_first_timepoint,
    check_if_first_timepoint,
    check_boundary_type,
)
from gridpath.project.operations.operational_types.common_functions import (
    load_optype_model_data,
    load_hydro_opchars,
    get_hydro_inputs_from_database,
    write_tab_file_model_inputs,
    check_for_tmps_to_link,
    validate_opchars,
    validate_hydro_opchars,
    get_prj_temporal_index_opr_inputs_from_db,
    BT_HRZ_INDEX_QUERY_PARAMS,
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
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`ENERGY_LOAD_FOLLOWING`                                           |
    |                                                                         |
    | The set of generators of the :code:`energy_hrz_shaping` operational    |
    | type.                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`ENERGY_LOAD_FOLLOWING_OPR_BT_HRZS`                                  |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`energy_hrz_shaping`  |
    | operational type and their operational horizons.                        |
    +-------------------------------------------------------------------------+
    | | :code:`ENERGY_LOAD_FOLLOWING_OPR_TMPS`                                  |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`energy_hrz_shaping`  |
    | operational type and their operational timepoints.                      |
    +-------------------------------------------------------------------------+
    | | :code:`ENERGY_LOAD_FOLLOWING_LINKED_TMPS`                               |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`energy_hrz_shaping`  |
    | operational type and their linked timepoints.                           |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`energy_hrz_shaping_max_power`                                  |
    | | *Defined over*: :code:`ENERGY_LOAD_FOLLOWING_OPR_BT_HRZS`                |
    | | *Within*: :code:`NonNegativeReals`                                               |
    |                                                                         |
    | The project's maximum power output in each operational horizon as a     |
    | fraction of its available capacity.                                     |
    +-------------------------------------------------------------------------+
    | | :code:`energy_hrz_shaping_min_power`                                  |
    | | *Defined over*: :code:`ENERGY_LOAD_FOLLOWING_OPR_BT_HRZS`                |
    | | *Within*: :code:`NonNegativeReals`                                               |
    |                                                                         |
    | The project's minimum power output in each operational horizon          |
    +-------------------------------------------------------------------------+
    | | :code:`energy_hrz_shaping_hrz_energy_fraction`                              |
    | | *Defined over*: :code:`ENERGY_LOAD_FOLLOWING_OPR_BT_HRZS`                |
    | | *Within*: :code:`NonNegativeReals`                                               |
    |                                                                         |
    | The project's avarage power output in each operational horizon.         |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Linked Input Params                                                     |
    +=========================================================================+
    | | :code:`energy_hrz_shaping_linked_power`                              |
    | | *Defined over*: :code:`ENERGY_LOAD_FOLLOWING_LINKED_TMPS`               |
    | | *Within*: :code:`NonNegativeReals`                                               |
    |                                                                         |
    | The project's power provision in the linked timepoints.                 |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`EnergyLoadFollowing_Provide_Power_MW`                                     |
    | | *Defined over*: :code:`ENERGY_LOAD_FOLLOWING_OPR_TMPS`                   |
    | | *Within*: :code:`NonNegativeReals`                                               |
    |                                                                         |
    | Power provision in MW from this project in each timepoint in which the  |
    | project is operational.                                                 |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | Power                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`EnergyLoadFollowing_Max_Power_Constraint`                         |
    | | *Defined over*: :code:`ENERGY_LOAD_FOLLOWING_OPR_BT_HRZS`                |
    |                                                                         |
    | Limits power to :code:`energy_hrz_shaping_max_power`.                   |
    +-------------------------------------------------------------------------+
    | | :code:`EnergyLoadFollowing_Min_Power_Constraint`                         |
    | | *Defined over*: :code:`ENERGY_LOAD_FOLLOWING_OPR_BT_HRZS`                |
    |                                                                         |
    | Power provision should exceed a certain level                           |
    | :code:`energy_hrz_shaping_min_power`                                    |
    +-------------------------------------------------------------------------+
    | | :code:`EnergyLoadFollowing_Energy_Budget_Constraint`                     |
    | | *Defined over*: :code:`ENERGY_LOAD_FOLLOWING_OPR_BT_HRZS`                |
    |                                                                         |
    | The project's averagepower in each operational horizon, should match    |
    | the specified :code:`energy_hrz_shaping_hrz_energy_fraction`.                 |
    +-------------------------------------------------------------------------+
    | Ramps                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`EnergyLoadFollowing_Ramp_Up_Constraint`                           |
    | | *Defined over*: :code:`ENERGY_LOAD_FOLLOWING_OPR_TMPS`                  |
    |                                                                         |
    | Limits the allowed project upward ramp based on the                     |
    | :code:`energy_hrz_shaping_ramp_up_when_on_rate`.                       |
    +-------------------------------------------------------------------------+
    | | :code:`EnergyLoadFollowing_Ramp_Down_Constraint`                         |
    | | *Defined over*: :code:`ENERGY_LOAD_FOLLOWING_OPR_TMPS`                  |
    |                                                                         |
    | Limits the allowed project downward ramp based on the                   |
    | :code:`energy_hrz_shaping_ramp_down_when_on_rate`.                     |
    +-------------------------------------------------------------------------+

    """
    # Sets
    ###########################################################################

    m.ENERGY_LOAD_FOLLOWING = Set(
        within=m.PROJECTS,
        initialize=lambda mod: subset_init_by_param_value(
            mod, "PROJECTS", "operational_type", "energy_load_following"
        ),
    )

    m.ENERGY_LOAD_FOLLOWING_OPR_TMPS = Set(
        dimen=2,
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: subset_init_by_set_membership(
            mod=mod,
            superset="PRJ_OPR_TMPS",
            index=0,
            membership_set=mod.ENERGY_LOAD_FOLLOWING,
        ),
    )

    m.ENERGY_LOAD_FOLLOWING_OPR_PRDS = Set(
        dimen=2,
        within=m.PRJ_OPR_PRDS,
        initialize=lambda mod: subset_init_by_set_membership(
            mod=mod,
            superset="PRJ_OPR_PRDS",
            index=0,
            membership_set=mod.ENERGY_LOAD_FOLLOWING,
        ),
    )

    m.ENERGY_LOAD_FOLLOWING_LINKED_TMPS = Set(dimen=2)

    # Required Params
    ###########################################################################

    # TODO: does this param make sense at the load zone level instead?
    # TODO: may want to default this to sum of static load
    m.ENERGY_LOAD_FOLLOWING_PRJ_PRDS = Set(dimen=2)
    m.base_net_requirement_mwh = Param(
        m.ENERGY_LOAD_FOLLOWING_PRJ_PRDS, within=NonNegativeReals
    )

    m.energy_load_following_peak_deviation_demand_charge = Param(
        m.ENERGY_LOAD_FOLLOWING, m.PERIODS, m.MONTHS, within=NonNegativeReals, default=0
    )

    # Linked Params
    ###########################################################################

    m.energy_hrz_shaping_linked_power = Param(
        m.ENERGY_LOAD_FOLLOWING_LINKED_TMPS, within=NonNegativeReals
    )

    # Variables
    ###########################################################################

    m.EnergyLoadFollowing_Provide_Power_MW = Var(
        m.ENERGY_LOAD_FOLLOWING_OPR_TMPS, within=NonNegativeReals
    )

    m.EnergyLoadFollowing_Peak_Deviation_in_Month = Var(
        m.ENERGY_LOAD_FOLLOWING_OPR_PRDS,
        m.MONTHS,
        within=NonNegativeReals,
        initialize=0,
    )

    # Constraints
    ###########################################################################

    def load_following_rule(mod, prj, tmp):
        """
        **Constraint Name**: EnergyLoadFollowing_Power_Constraint
        **Enforced Over**: ENERGY_LOAD_FOLLOWING_OPR_TMPS

        Meet everything above a flat block a
        """
        # TODO: replace static_load here with post EE variable
        # TODO: allow less than or equal constraint here?
        return mod.EnergyLoadFollowing_Provide_Power_MW[prj, tmp] == mod.LZ_Load_in_Tmp[
            mod.load_zone[prj], tmp
        ] - (
            mod.base_net_requirement_mwh[prj, mod.period[tmp]]
            - mod.Energy_MWh[prj, mod.period[tmp]]
        ) / sum(
            mod.hrs_in_tmp[prd_tmp] * mod.tmp_weight[prd_tmp]
            for prd_tmp in mod.TMPS_IN_PRD[mod.period[tmp]]
        )

    m.EnergyLoadFollowing_Power_Constraint = Constraint(
        m.ENERGY_LOAD_FOLLOWING_OPR_TMPS, rule=load_following_rule
    )

    # def tmps_by_prd_month_rule(mod, prd, month):
    #     tmps_list = []
    #     for tmp in mod.TMPS_IN_PRD[prd]:
    #         if mod.month[tmp] == month:
    #             tmps_list.append(tmp)
    #
    #     return tmps_list
    #
    # m.TMPS_BY_PRD_MONTH = Set(m.PERIODS, m.MONTHS, initialize=tmps_by_prd_month_rule)
    #
    # def prd_mnth_tmps_rule(mod):
    #     prd_mnth_tmp_list = []
    #     for prd in mod.PERIODS:
    #         for month in mod.MONTHS:
    #             for tmp in mod.TMPS_IN_PRD[prd]:
    #                 if mod.month[tmp] == month:
    #                     prd_mnth_tmp_list.append((prd, month, tmp))
    #
    #     return prd_mnth_tmp_list
    #
    # m.PRD_MONTH_TMPS = Set(dimen=3, initialize=prd_mnth_tmps_rule)
    #
    # def monthly_peak_deviation_rule(mod, prj, prd, mnth, tmp):
    #     if mod.energy_load_following_peak_deviation_demand_charge == 0:
    #         return Constraint.Skip
    #     else:
    #         return mod.EnergyLoadFollowing_Peak_Deviation_in_Month[
    #             prj, prd, mnth
    #         ] >= (
    #             mod.EnergyLoadFollowing_Provide_Power_MW[prj, tmp]
    #             - sum(
    #                 mod.EnergyLoadFollowing_Provide_Power_MW[prj, _tmp]
    #                 for _tmp in mod.TMPS_BY_PRD_MONTH[prd, mnth]
    #             )
    #             / sum(
    #                 mod.hrs_in_tmp[_tmp] * mod.tmp_weight[_tmp]
    #                 for _tmp in mod.TMPS_BY_PRD_MONTH[prd, mnth]
    #             )
    #         )
    #
    # m.EnergyLoadFollowing_Peak_Deviation_in_Month_Constraint = Constraint(
    #     m.ENERGY_LOAD_FOLLOWING, m.PRD_MONTH_TMPS,
    # rule=monthly_peak_deviation_rule
    # )

    def monthly_peak_deviation_rule(mod, prj, tmp):
        if mod.energy_load_following_peak_deviation_demand_charge == 0:
            return Constraint.Skip
        else:
            return mod.EnergyLoadFollowing_Peak_Deviation_in_Month[
                prj, mod.period[tmp], mod.month[tmp]
            ] >= (
                mod.EnergyLoadFollowing_Provide_Power_MW[prj, tmp]
                - sum(
                    mod.EnergyLoadFollowing_Provide_Power_MW[prj, _tmp]
                    * mod.hrs_in_tmp[_tmp]
                    * mod.tmp_weight[_tmp]
                    for _tmp in mod.TMPS_IN_PRD[mod.period[tmp]]
                    if mod.month[tmp] == mod.month[_tmp]
                )
                / sum(
                    mod.hrs_in_tmp[_tmp] * mod.tmp_weight[_tmp]
                    for _tmp in mod.TMPS_IN_PRD[mod.period[tmp]]
                    if mod.month[tmp] == mod.month[_tmp]
                )
            )

    m.EnergyLoadFollowing_Peak_Deviation_in_Month_Constraint = Constraint(
        m.ENERGY_LOAD_FOLLOWING_OPR_TMPS, rule=monthly_peak_deviation_rule
    )

    def total_energy_constraint(mod, prj, prd):
        """
        This constraint is somewhat redundant, but here to prevent degeneracy
        issues when Energy_MWh does not have a cost associated it and could
        be set arbitrarily high.
        """
        return (
            sum(
                mod.EnergyLoadFollowing_Provide_Power_MW[prj, tmp]
                * mod.hrs_in_tmp[tmp]
                * mod.tmp_weight[tmp]
                for tmp in mod.TMPS_IN_PRD[prd]
            )
            == mod.Energy_MWh[prj, prd]
        )

    m.EnergyLoadFollowing_Total_Energy_in_Period_Constraint = Constraint(
        m.ENERGY_LOAD_FOLLOWING_OPR_PRDS, rule=total_energy_constraint
    )


# Operational Type Methods
###############################################################################
def power_provision_rule(mod, prj, tmp):
    """
    Power provision from must-take hydro.
    """
    return mod.EnergyLoadFollowing_Provide_Power_MW[prj, tmp]


def peak_deviation_monthly_demand_charge_cost_rule(mod, prj, prd, mnth):
    return (
        mod.EnergyLoadFollowing_Peak_Deviation_in_Month[prj, prd, mnth]
        * mod.energy_load_following_peak_deviation_demand_charge[prj, prd, mnth]
    )


def power_delta_rule(mod, prj, tmp):
    """
    This rule is only used in tuning costs, so fine to skip for linked
    horizon's first timepoint.
    """
    if check_if_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[prj]
    ) and (
        check_boundary_type(
            mod=mod,
            tmp=tmp,
            balancing_type=mod.balancing_type_project[prj],
            boundary_type="linear",
        )
        or check_boundary_type(
            mod=mod,
            tmp=tmp,
            balancing_type=mod.balancing_type_project[prj],
            boundary_type="linked",
        )
    ):
        pass
    else:
        return (
            mod.EnergyLoadFollowing_Provide_Power_MW[prj, tmp]
            - mod.EnergyLoadFollowing_Provide_Power_MW[
                prj, mod.prev_tmp[tmp, mod.balancing_type_project[prj]]
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
    pass

    # Determine list of projects load params from projects.tab (if any)
    projects = load_optype_model_data(
        mod=m,
        data_portal=data_portal,
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        op_type="energy_load_following",
    )

    # Load data
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "energy_load_following_base_net_requirements.tab",
        ),
        index=m.ENERGY_LOAD_FOLLOWING_PRJ_PRDS,
        param=m.base_net_requirement_mwh,
    )

    demand_charges_tabfile_path = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "energy_load_following_peak_deviation_demand_charges.tab",
    )

    if os.path.exists(demand_charges_tabfile_path):
        data_portal.load(
            filename=demand_charges_tabfile_path,
            param=m.energy_load_following_peak_deviation_demand_charge,
        )

    # Linked timepoint params
    linked_inputs_filename = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "energy_hrz_shaping_linked_timepoint_params.tab",
    )
    if os.path.exists(linked_inputs_filename):
        data_portal.load(
            filename=linked_inputs_filename,
            index=m.ENERGY_LOAD_FOLLOWING_LINKED_TMPS,
            param=(m.energy_hrz_shaping_linked_power,),
        )


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
    pass
    # for prj, prd in mod.ENERGY_LOAD_FOLLOWING_OPR_PRDS:
    #     for month in mod.MONTHS:
    #         print(
    #             value(mod.EnergyLoadFollowing_Peak_Deviation_in_Month[prj, prd, month]),
    #             mod.energy_load_following_peak_deviation_demand_charge[prj, prd, month],
    #         )


# Database
###############################################################################


def get_model_inputs_from_database(
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
    :return: cursor object with query results
    """

    (
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
    ) = directories_to_db_values(
        weather_iteration, hydro_iteration, availability_iteration, subproblem, stage
    )

    base_net_req_sql = f"""
        SELECT project, period, base_net_requirement_mwh
        FROM inputs_project_base_net_requirements
        WHERE project IN (
            SELECT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID}
        )
        AND period IN (
            SELECT period
            FROM inputs_temporal_periods
            WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
        )
        AND (project, base_net_requirement_scenario_id) IN (
            SELECT project, base_net_requirement_scenario_id
            FROM inputs_project_operational_chars
            WHERE project_operational_chars_scenario_id = {subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID}
            AND operational_type = 'energy_load_following'
        );
    """

    c1 = conn.cursor()
    base_net_requirements = c1.execute(base_net_req_sql)

    demand_charge_sql = f"""
            SELECT project, period, month, peak_deviation_demand_charge_per_mw
            FROM inputs_project_peak_deviation_demand_charges
            WHERE project IN (
                SELECT project
                FROM inputs_project_portfolios
                WHERE project_portfolio_scenario_id = {subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID}
            )
            AND period IN (
                SELECT period
                FROM inputs_temporal_periods
                WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
            )
            AND (project, peak_deviation_demand_charge_scenario_id) IN (
                SELECT project, peak_deviation_demand_charge_scenario_id
                FROM inputs_project_operational_chars
                WHERE project_operational_chars_scenario_id = {subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID}
                AND operational_type = 'energy_load_following'
            );
        """

    c2 = conn.cursor()
    demand_charges = c2.execute(demand_charge_sql)

    return base_net_requirements, demand_charges


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
    """
    Get inputs from database and write out the model input
    hydro_conventional_horizon_params.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    base_net_requirements, demand_charges = get_model_inputs_from_database(
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )

    data_files_to_write = [
        ("energy_load_following_base_net_requirements.tab", base_net_requirements),
        ("energy_load_following_peak_deviation_demand_charges.tab", demand_charges),
    ]

    for fname, data_object in data_files_to_write:
        write_tab_file_model_inputs(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            fname,
            data_object,
        )


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

    # Validate operational chars table inputs
    validate_opchars(
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
        "energy_load_following",
    )
