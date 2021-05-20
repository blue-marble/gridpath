# Copyright 2016-2020 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writinprj, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""

"""
import csv
import os.path
from pyomo.environ import Param, Set, Var, Constraint, NonNegativeReals, \
    PercentFraction, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import subset_init_by_param_value
from gridpath.auxiliary.dynamic_components import \
    footroom_variables, headroom_variables, reserve_variable_derate_params
# from gridpath.project.operations.reserves.subhourly_energy_adjustment import \
#     footroom_subhourly_energy_adjustment_rule, \
#     headroom_subhourly_energy_adjustment_rule
from gridpath.project.common_functions import \
    check_if_first_timepoint, check_boundary_type
from gridpath.project.operations.operational_types.common_functions import \
    update_dispatch_results_table, load_var_profile_inputs, \
    get_var_profile_inputs_from_database, write_tab_file_model_inputs, \
    validate_opchars, validate_var_profiles, load_optype_model_data


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`GEN_VAR_STOR_HYB`                                              |
    |                                                                         |
    | The set of generators of the :code:`gen_var_stor_hyb` operational type. |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_VAR_STOR_HYB_OPR_TMPS`                                     |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_var_stor_hyb`     |
    | operational type and their operational timepoints.                      |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_var_stor_hyb_cap_factor`                                   |
    | | *Defined over*: :code:`GEN_VAR_STOR_HYB`                              |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's power output in each operational timepoint as a fraction  |
    | of its available capacity (i.e. the capacity factor).                   |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`GenVarStorHyb_Provide_Power_MW`                                |
    | | *Defined over*: :code:`GEN_VAR_STOR_HYB_OPR_TMPS`                     |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Power provision in MW from this project in each timepoint in which the  |
    | project is operational (capacity exists and the project is available).  |
    +-------------------------------------------------------------------------+
    | | :code:`GenVarStorHyb_Charge_MW`                                       |
    | | *Defined over*: :code:`GEN_VAR_STOR_HYB_OPR_TMPS`                     |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Charging power in MW from this project in each timepoint in which the   |
    | project is operational (capacity exists and the project is available).  |
    +-------------------------------------------------------------------------+
    | | :code:`GenVarStorHyb_Discharge_MW`                                    |
    | | *Defined over*: :code:`GEN_VAR_STOR_HYB_OPR_TMPS`                     |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Discharging power in MW from this project in each timepoint in which the|
    |  project is operational (capacity exists and the project is available). |
    +-------------------------------------------------------------------------+
    | | :code:`GenVarStorHyb_Starting_Energy_in_Storage_MWh`                  |
    | | *Defined over*: :code:`GEN_VAR_STOR_HYB_OPR_TMPS`                     |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The state of charge of the storage project at the start of each         |
    | timepoint, in MWh of energy stored.                                     |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`GenVarStorHyb_Scheduled_Curtailment_MW`                        |
    | | *Defined over*: :code:`GEN_VAR_STOR_HYB_OPR_TMPS`                     |
    |                                                                         |
    | The available power minus what was actually provided (in MW).           |
    +-------------------------------------------------------------------------+
    | | :code:`GenVarStorHyb_Total_Curtailment_MW`                            |
    | | *Defined over*: :code:`GEN_VAR_STOR_HYB_OPR_TMPS`                     |
    |                                                                         |
    | Scheduled curtailment (in MW) plus an upward adjustment for additional  |
    | curtailment when providing downward reserves, and a downward adjustment |
    | adjustment for a reduction in curtailment when providing upward         |
    | reserves, to account for sub-hourly dispatch when providing reserves.   |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | Power                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`GenVarStorHyb_Max_Available_Power_Constraint`                            |
    | | *Defined over*: :code:`GEN_VAR_STOR_HYB_OPR_TMPS`                     |
    |                                                                         |
    | Limits the power plus upward reserves in each timepoint based on the    |
    | :code:`gen_var_stor_hyb_cap_factor` and the available capacity.         |
    +-------------------------------------------------------------------------+
    | | :code:`GenVarStorHyb_Min_Power_Constraint`                            |
    | | *Defined over*: :code:`GEN_VAR_STOR_HYB_OPR_TMPS`                     |
    |                                                                         |
    | Power provision minus downward reserves should exceed zero.             |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################
    m.GEN_VAR_STOR_HYB = Set(
        within=m.PROJECTS,
        initialize=lambda mod: subset_init_by_param_value(
            mod, "PROJECTS", "operational_type", "gen_var_stor_hyb"
        )
    )

    m.GEN_VAR_STOR_HYB_OPR_TMPS = Set(
        dimen=2, within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: list(
            set((prj, tmp) for (prj, tmp) in mod.PRJ_OPR_TMPS
                if prj in mod.GEN_VAR_STOR_HYB)
        )
    )

    # Required Params
    ###########################################################################

    m.gen_var_stor_hyb_cap_factor = Param(
        m.GEN_VAR_STOR_HYB_OPR_TMPS,
        within=NonNegativeReals
    )

    m.gen_var_stor_hyb_charging_efficiency = Param(
        m.GEN_VAR_STOR_HYB, within=PercentFraction
    )

    m.gen_var_stor_hyb_discharging_efficiency = Param(
        m.GEN_VAR_STOR_HYB, within=PercentFraction
    )

    # Optional Params
    ###########################################################################

    m.gen_var_stor_hyb_charging_capacity_multiplier = Param(
        m.GEN_VAR_STOR_HYB, within=NonNegativeReals, default=1.0
    )

    m.gen_var_stor_hyb_discharging_capacity_multiplier = Param(
        m.GEN_VAR_STOR_HYB, within=NonNegativeReals, default=1.0
    )

    # Variables
    ###########################################################################

    m.GenVarStorHyb_Provide_Power_MW = Var(
        m.GEN_VAR_STOR_HYB_OPR_TMPS,
        within=NonNegativeReals
    )
    
    m.GenVarStorHyb_Charge_MW = Var(
        m.GEN_VAR_STOR_HYB_OPR_TMPS,
        within=NonNegativeReals
    )

    m.GenVarStorHyb_Discharge_MW = Var(
        m.GEN_VAR_STOR_HYB_OPR_TMPS,
        within=NonNegativeReals
    )

    m.GenVarStorHyb_Starting_Energy_in_Storage_MWh = Var(
        m.GEN_VAR_STOR_HYB_OPR_TMPS,
        within=NonNegativeReals
    )

    # Expressions
    ###########################################################################

    def available_power_rule(mod, prj, tmp):
        """
        The amount of power from the variable resource generation component 
        (e.g. solar field) available in every timepoint.
        """
        return mod.Hyb_Gen_Capacity_MW[prj, mod.period[tmp]] \
            * mod.Availability_Derate[prj, tmp] \
            * mod.gen_var_stor_hyb_cap_factor[prj, tmp]
    
    m.GenVarStorHyb_Available_Power_MW = Expression(
        m.GEN_VAR_STOR_HYB_OPR_TMPS,
        rule=available_power_rule
    )
        
    def upwards_reserve_rule(mod, prj, tmp):
        """
        Gather all headroom variables, and de-rate the total reserves offered
        to account for the fact that gen_var_stor_hyb output is uncertain.
        """
        return sum(
            getattr(mod, c)[prj, tmp]
            / getattr(mod, getattr(d, reserve_variable_derate_params)[c])[prj]
            for c in getattr(d, headroom_variables)[prj]
        )

    m.GenVarStorHyb_Upwards_Reserves_MW = Expression(
        m.GEN_VAR_STOR_HYB_OPR_TMPS,
        rule=upwards_reserve_rule
    )

    def downwards_reserve_rule(mod, prj, tmp):
        """
        Gather all footroom variables, and de-rate the total reserves offered
        to account for the fact that gen_var_stor_hyb output is uncertain.
        """
        return sum(
            getattr(mod, c)[prj, tmp]
            / getattr(mod, getattr(d, reserve_variable_derate_params)[c])[prj]
            for c in getattr(d, footroom_variables)[prj]
        )

    m.GenVarStorHyb_Downwards_Reserves_MW = Expression(
        m.GEN_VAR_STOR_HYB_OPR_TMPS,
        rule=downwards_reserve_rule
    )

    # TODO: ignore subtimepoint reserve dynamics for now
    # def subhourly_curtailment_expression_rule(mod, prj, tmp):
    #     """
    #     Sub-hourly curtailment from providing downward reserves.
    #     """
    #     return footroom_subhourly_energy_adjustment_rule(d, mod, prj, tmp)
    #
    # m.GenVarStorHyb_Subhourly_Curtailment_MW = Expression(
    #     m.GEN_VAR_STOR_HYB_OPR_TMPS,
    #     rule=subhourly_curtailment_expression_rule
    # )
    #
    # def subhourly_delivered_energy_expression_rule(mod, prj, tmp):
    #     """
    #     Sub-hourly energy delivered from providing upward reserves.
    #     """
    #     return headroom_subhourly_energy_adjustment_rule(d, mod, prj, tmp)
    #
    # m.GenVarStorHyb_Subhourly_Energy_Delivered_MW = Expression(
    #     m.GEN_VAR_STOR_HYB_OPR_TMPS,
    #     rule=subhourly_delivered_energy_expression_rule
    # )

    m.GenVarStorHyb_Scheduled_Curtailment_MW = Expression(
        m.GEN_VAR_STOR_HYB_OPR_TMPS,
        rule=scheduled_curtailment_expression_rule
    )

    # m.GenVarStorHyb_Total_Curtailment_MW = Expression(
    #     m.GEN_VAR_STOR_HYB_OPR_TMPS,
    #     rule=total_curtailment_expression_rule
    # )

    # Constraints
    ###########################################################################

    m.GenVarStorHyb_Max_Available_Power_Constraint = Constraint(
        m.GEN_VAR_STOR_HYB_OPR_TMPS,
        rule=max_available_power_rule
    )

    m.GenVarStorHyb_Max_Available_Capacity_Constraint = Constraint(
        m.GEN_VAR_STOR_HYB_OPR_TMPS,
        rule=max_capacity_rule
    )

    m.GenVarStorHyb_Min_Power_Constraint = Constraint(
        m.GEN_VAR_STOR_HYB_OPR_TMPS,
        rule=min_power_rule
    )
    
    # Power and State of Charge
    m.GenVarStorHyb_Max_Charge_Constraint = Constraint(
        m.GEN_VAR_STOR_HYB_OPR_TMPS,
        rule=max_charge_rule
    )

    m.GenVarStorHyb_Max_Discharge_Constraint = Constraint(
        m.GEN_VAR_STOR_HYB_OPR_TMPS,
        rule=max_discharge_rule
    )

    m.GenVarStorHyb_Energy_Tracking_Constraint = Constraint(
        m.GEN_VAR_STOR_HYB_OPR_TMPS,
        rule=energy_tracking_rule
    )

    m.GenVarStorHyb_Max_Energy_in_Storage_Constraint = Constraint(
        m.GEN_VAR_STOR_HYB_OPR_TMPS,
        rule=max_energy_in_storage_rule
    )
    
    # # Reserves
    # m.Stor_Max_Headroom_Power_Constraint = Constraint(
    #     m.GEN_VAR_STOR_HYB_OPR_TMPS,
    #     rule=max_headroom_power_rule
    # )
    # 
    # m.Stor_Max_Footroom_Power_Constraint = Constraint(
    #     m.GEN_VAR_STOR_HYB_OPR_TMPS,
    #     rule=max_footroom_power_rule
    # )
    # 
    # m.Stor_Max_Headroom_Energy_Constraint = Constraint(
    #     m.GEN_VAR_STOR_HYB_OPR_TMPS,
    #     rule=max_headroom_energy_rule
    # )
    # 
    # m.Stor_Max_Footroom_Energy_Constraint = Constraint(
    #     m.GEN_VAR_STOR_HYB_OPR_TMPS,
    #     rule=max_footroom_energy_rule
    # )


# Expression Methods
###############################################################################

def scheduled_curtailment_expression_rule(mod, prj, tmp):
    """
    **Expression Name**: GenVarStorHyb_Scheduled_Curtailment_MW
    **Defined Over**: GEN_VAR_STOR_HYB_OPR_TMPS

    Scheduled curtailment is the available power (variable resource + net
    power from storage) minus what was actually provided to the grid.
    """
    return mod.GenVarStorHyb_Available_Power_MW[prj, tmp] \
        + mod.GenVarStorHyb_Discharge_MW[prj, tmp] \
        - mod.GenVarStorHyb_Charge_MW[prj, tmp] \
        - mod.GenVarStorHyb_Provide_Power_MW[prj, tmp]


def total_curtailment_expression_rule(mod, prj, tmp):
    """
    **Expression Name**: GenVarStorHyb_Total_Curtailment_MW
    **Defined Over**: GEN_VAR_STOR_HYB_OPR_TMPS

    Available energy that was not delivered
    There's an adjustment for subhourly reserve provision:
    1) if downward reserves are provided, they will be called upon
    occasionally, so power provision will have to decrease and additional
    curtailment will be incurred;
    2) if upward reserves are provided (energy is being curtailed),
    they will be called upon occasionally, so power provision will have to
    increase and less curtailment will be incurred
    The subhourly adjustment here is a simple linear function of reserve

    Assume cap factors don't incorporate availability derates,
    so don't multiply capacity by Availability_Derate here (will count
    as curtailment).
    """

    return mod.Hyb_Gen_Capacity_MW[prj, mod.period[tmp]] \
        * mod.gen_var_stor_hyb_cap_factor[prj, tmp] \
        - mod.GenVarStorHyb_Provide_Power_MW[prj, tmp] \
        + mod.GenVarStorHyb_Subhourly_Curtailment_MW[prj, tmp] \
        - mod.GenVarStorHyb_Subhourly_Energy_Delivered_MW[prj, tmp]


# Constraint Formulation Rules
###############################################################################

def max_available_power_rule(mod, prj, tmp):
    """
    **Constraint Name**: GenVarStorHyb_Max_Available_Power_Constraint
    **Enforced Over**: GEN_VAR_STOR_HYB_OPR_TMPS

    Power provision plus upward services cannot exceed available power, which
    is equal to the available capacity multiplied by the capacity factor
    plus the net power from storage.
    """
    return mod.GenVarStorHyb_Provide_Power_MW[prj, tmp] \
        + mod.GenVarStorHyb_Upwards_Reserves_MW[prj, tmp] \
        <= mod.GenVarStorHyb_Available_Power_MW[prj, tmp] \
        + mod.GenVarStorHyb_Discharge_MW[prj, tmp] \
        - mod.GenVarStorHyb_Charge_MW[prj, tmp]


def max_capacity_rule(mod, prj, tmp):
    """
    **Constraint Name**: GenVarStorHyb_Max_Available_Capacity_Constraint
    **Enforced Over**: GEN_VAR_STOR_HYB_OPR_TMPS
    
    Can't provide more power than project total power capacity.
    """
    return mod.GenVarStorHyb_Provide_Power_MW[prj, tmp] \
        + mod.GenVarStorHyb_Upwards_Reserves_MW[prj, tmp] \
        <= mod.Capacity_MW[prj, mod.period[tmp]] \
        * mod.Availability_Derate[prj, tmp]


def min_power_rule(mod, prj, tmp):
    """
    **Constraint Name**: GenVarStorHyb_Min_Power_Constraint
    **Enforced Over**: GEN_VAR_STOR_HYB_OPR_TMPS

    Power provision minus downward services cannot be less than 0. Here,
    we are assuming that the hybrid storage cannot charge from the grid (so 
    power provision cannot go negative).
    """
    return mod.GenVarStorHyb_Provide_Power_MW[prj, tmp] \
        - mod.GenVarStorHyb_Downwards_Reserves_MW[prj, tmp] \
        >= 0


# TODO: can some of this be consolidated with the 'stor' optype methods
# Power and State of Charge
def max_discharge_rule(mod, s, tmp):
    """
    **Constraint Name**: GenVarStorHyb_Max_Discharge_Constraint
    **Enforced Over**: GEN_VAR_STOR_HYB_OPR_TMPS

    Storage discharging power can't exceed available storage component 
    capacity.
    """
    # TODO: capacity multipliers
    return mod.GenVarStorHyb_Discharge_MW[s, tmp] \
        <= mod.Hyb_Stor_Capacity_MW[s, mod.period[tmp]] \
        * mod.Availability_Derate[s, tmp]
        # * mod.gen_var_stor_hyb_discharging_capacity_multiplier[s]


def max_charge_rule(mod, s, tmp):
    """
    **Constraint Name**: GenVarStorHyb_Max_Charge_Constraint
    **Enforced Over**: GEN_VAR_STOR_HYB_OPR_TMPS

    Storage charging power can't exceed available storage component capacity.
    """
    # TODO: capacity multipliers
    return mod.GenVarStorHyb_Charge_MW[s, tmp] \
        <= mod.Hyb_Stor_Capacity_MW[s, mod.period[tmp]] \
        * mod.Availability_Derate[s, tmp]
        # * mod.gen_var_stor_hyb_charging_capacity_multiplier[s]


# TODO: adjust storage energy for reserves provided
def energy_tracking_rule(mod, s, tmp):
    """
    **Constraint Name**: GenVarStorHyb_Energy_Tracking_Constraint
    **Enforced Over**: GEN_VAR_STOR_HYB_OPR_TMPS

    The energy stored in each timepoint is equal to the energy stored in the
    previous timepoint minus any discharged power (adjusted for discharging
    efficiency and timepoint duration) plus any charged power (adjusted for
    charging efficiency and timepoint duration).
    """
    if check_if_first_timepoint(
            mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[s]
    ) and check_boundary_type(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[s],
        boundary_type="linear"
    ):
        return Constraint.Skip
    else:
        if check_if_first_timepoint(
            mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[s]
        ) and check_boundary_type(
            mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[s],
            boundary_type="linked"
        ):
            prev_tmp_hrs_in_tmp = mod.hrs_in_linked_tmp[0]
            prev_tmp_starting_energy_in_storage = \
                mod.gen_var_stor_hyb_linked_starting_energy_in_storage[s, 0]
            prev_tmp_discharge = mod.gen_var_stor_hyb_linked_discharge[s, 0]
            prev_tmp_charge = mod.gen_var_stor_hyb_linked_charge[s, 0]
        else:
            prev_tmp_hrs_in_tmp = mod.hrs_in_tmp[
                mod.prev_tmp[tmp, mod.balancing_type_project[s]]
            ]
            prev_tmp_starting_energy_in_storage = \
                mod.GenVarStorHyb_Starting_Energy_in_Storage_MWh[
                    s, mod.prev_tmp[tmp, mod.balancing_type_project[s]]
                ]
            prev_tmp_discharge = \
                mod.GenVarStorHyb_Discharge_MW[
                    s, mod.prev_tmp[tmp, mod.balancing_type_project[s]]
                ]
            prev_tmp_charge = \
                mod.GenVarStorHyb_Charge_MW[
                    s, mod.prev_tmp[tmp, mod.balancing_type_project[s]]
                ]

        return \
            mod.GenVarStorHyb_Starting_Energy_in_Storage_MWh[s, tmp] \
            == prev_tmp_starting_energy_in_storage \
            + prev_tmp_charge * prev_tmp_hrs_in_tmp \
            * mod.gen_var_stor_hyb_charging_efficiency[s] \
            - prev_tmp_discharge * prev_tmp_hrs_in_tmp \
            / mod.gen_var_stor_hyb_discharging_efficiency[s]


def max_energy_in_storage_rule(mod, s, tmp):
    """
    **Constraint Name**: GenVarStorHyb_Max_Energy_in_Stor_Constraint
    **Enforced Over**: GEN_VAR_STOR_HYB_OPR_TMPS

    The amount of energy stored in each operational timepoint cannot exceed
    the available energy capacity.
    """
    return mod.GenVarStorHyb_Starting_Energy_in_Storage_MWh[s, tmp] \
        <= mod.Energy_Capacity_MWh[s, mod.period[tmp]] \
        * mod.Availability_Derate[s, tmp]


# Operational Type Methods
###############################################################################

def power_provision_rule(mod, prj, tmp):
    """
    Power provision from variable generators is their capacity times the
    capacity factor in each timepoint minus any upward reserves/curtailment.
    """

    return mod.GenVarStorHyb_Provide_Power_MW[prj, tmp]


def variable_om_cost_rule(mod, prj, tmp):
    """
    Variable cost is incurred on all power produced (including what's
    curtailed).
    """
    return mod.Capacity_MW[prj, mod.period[tmp]] \
        * mod.Availability_Derate[prj, tmp] \
        * mod.gen_var_stor_hyb_cap_factor[prj, tmp] \
        * mod.variable_om_cost_per_mwh[prj]


def scheduled_curtailment_rule(mod, prj, tmp):
    """
    Variable generation can be dispatched down, i.e. scheduled below the
    available energy
    """
    return mod.GenVarStorHyb_Scheduled_Curtailment_MW[prj, tmp]


# def subhourly_curtailment_rule(mod, prj, tmp):
#     """
#     If providing downward reserves, variable generators will occasionally
#     have to be dispatched down relative to their schedule, resulting in
#     additional curtailment within the hour
#     """
#     return mod.GenVarStorHyb_Subhourly_Curtailment_MW[prj, tmp]


# def subhourly_energy_delivered_rule(mod, prj, tmp):
#     """
#     If providing upward reserves, variable generators will occasionally be
#     dispatched up, so additional energy will be delivered within the hour
#     relative to their schedule (less curtailment)
#     """
#     return mod.GenVarStorHyb_Subhourly_Energy_Delivered_MW[prj, tmp]


def curtailment_cost_rule(mod, prj, tmp):
    """
    Apply curtailment cost to scheduled and subhourly curtailment
    """
    # return (mod.GenVarStorHyb_Scheduled_Curtailment_MW[prj, tmp] +
    #         mod.GenVarStorHyb_Subhourly_Curtailment_MW[prj, tmp]) \
    #     * mod.curtailment_cost_per_pwh[prj]

    return mod.GenVarStorHyb_Scheduled_Curtailment_MW[prj, tmp] \
        * mod.curtailment_cost_per_pwh[prj]


def power_delta_rule(mod, prj, tmp):
    """
    Curtailment is counted as part of the ramp here; excludes any ramping from
    reserve provision.

    This rule is only used in tuning costs, so fine to skip for linked
    horizon's first timepoint.
    """
    if check_if_first_timepoint(
            mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[prj]
    ) and (
            check_boundary_type(
                mod=mod, tmp=tmp,
                balancing_type=mod.balancing_type_project[prj],
                boundary_type="linear"
            ) or
            check_boundary_type(
                mod=mod, tmp=tmp,
                balancing_type=mod.balancing_type_project[prj],
                boundary_type="linked"
            )
    ):
        pass
    else:
        return \
            (mod.Capacity_MW[prj, mod.period[tmp]]
             * mod.Availability_Derate[prj, tmp]
             * mod.gen_var_stor_hyb_cap_factor[prj, tmp]) \
            - (mod.Capacity_MW[prj, mod.period[mod.prev_tmp[
                tmp, mod.balancing_type_project[prj]]]]
               * mod.Availability_Derate[prj, mod.prev_tmp[
                        tmp, mod.balancing_type_project[prj]]]
               * mod.gen_var_stor_hyb_cap_factor[prj, mod.prev_tmp[
                        tmp, mod.balancing_type_project[prj]]])


# Inputs-Outputs
###############################################################################

def load_model_data(
    mod, d, data_portal, scenario_directory, subproblem, stage
):
    """
    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    # Load data from projects.tab and get the list of projects of this type
    projects = load_optype_model_data(
        mod=mod, data_portal=data_portal,
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage, op_type="gen_var_stor_hyb"
    )

    load_var_profile_inputs(
        data_portal, scenario_directory, subproblem, stage, "gen_var_stor_hyb"
    )


def export_results(
    mod, d, scenario_directory, subproblem, stage
):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param mod:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, str(subproblem), str(stage),
                           "results",
                           "dispatch_gen_var_stor_hybrid.csv"), "w",
              newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "balancing_type_project",
                         "horizon", "timepoint", "timepoint_weight",
                         "number_of_hours_in_timepoint",
                         "technology", "load_zone",
                         "power_mw", "scheduled_curtailment_mw",
                         "hyb_storage_charge_mw", "hyb_storage_discharge_mw"
                         ])

        for (p, tmp) in mod.GEN_VAR_STOR_HYB_OPR_TMPS:
            writer.writerow([
                p,
                mod.period[tmp],
                mod.balancing_type_project[p],
                mod.horizon[tmp, mod.balancing_type_project[p]],
                tmp,
                mod.tmp_weight[tmp],
                mod.hrs_in_tmp[tmp],
                mod.technology[p],
                mod.load_zone[p],
                value(mod.GenVarStorHyb_Provide_Power_MW[p, tmp]),
                value(mod.GenVarStorHyb_Scheduled_Curtailment_MW[p, tmp]),
                value(mod.GenVarStorHyb_Charge_MW[p, tmp]),
                value(mod.GenVarStorHyb_Discharge_MW[p, tmp])
            ])


# Database
###############################################################################

def get_model_inputs_from_database(
    scenario_id, subscenarios, subproblem, stage, conn
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return: cursor object with query results
    """

    return get_var_profile_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn, "gen_var_stor_hyb"
    )


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    variable_generator_profiles.tab file.
    :param scenario_directory: string; the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    data = get_model_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )
    fname = "variable_generator_profiles.tab"

    write_tab_file_model_inputs(
        scenario_directory, subproblem, stage, fname, data
    )


def import_model_results_to_database(
    scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c: 
    :param db: 
    :param results_directory:
    :param quiet:
    :return: 
    """
    if not quiet:
        print("project dispatch gen_var_stor_hyb")

    update_dispatch_results_table(
        db=db, c=c, results_directory=results_directory,
        scenario_id=scenario_id, subproblem=subproblem, stage=stage,
        results_file="dispatch_gen_var_stor_hybrid.csv"
    )


def process_model_results(db, c, scenario_id, subscenarios, quiet):
    """
    Aggregate scheduled curtailment
    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """
    if not quiet:
        print("aggregate variable curtailment")

    # Delete old aggregated variable curtailment results
    del_sql = """
        DELETE FROM results_project_curtailment_variable 
        WHERE scenario_id = ?;
        """
    spin_on_database_lock(conn=db, cursor=c, sql=del_sql,
                          data=(scenario_id,),
                          many=False)

    # Aggregate variable curtailment (just scheduled curtailment)
    insert_sql = """
        INSERT INTO results_project_curtailment_variable
        (scenario_id, subproblem_id, stage_id, period, timepoint, 
        timepoint_weight, number_of_hours_in_timepoint, month, hour_of_day,
        load_zone, scheduled_curtailment_mw)
        SELECT
        scenario_id, subproblem_id, stage_id, period, timepoint, 
        timepoint_weight, number_of_hours_in_timepoint, month, hour_of_day,
        load_zone, scheduled_curtailment_mw
        FROM (
            SELECT scenario_id, subproblem_id, stage_id, period, 
            timepoint, timepoint_weight, number_of_hours_in_timepoint, 
            load_zone, 
            sum(scheduled_curtailment_mw) AS scheduled_curtailment_mw
            FROM results_project_dispatch
            WHERE operational_type = 'gen_var_stor_hyb'
            GROUP BY scenario_id, subproblem_id, stage_id, timepoint, load_zone
        ) as agg_curtailment_tbl
        JOIN (
            SELECT subproblem_id, stage_id, timepoint, month, hour_of_day
            FROM inputs_temporal
            WHERE temporal_scenario_id = (
                SELECT temporal_scenario_id 
                FROM scenarios
                WHERE scenario_id = ?
                )
        ) as tmp_info_tbl
        USING (subproblem_id, stage_id, timepoint)
        WHERE scenario_id = ?
        ORDER BY subproblem_id, stage_id, load_zone, timepoint;"""

    spin_on_database_lock(
        conn=db, cursor=c, sql=insert_sql,
        data=(scenario_id, scenario_id),
        many=False
    )


# Validation
###############################################################################

def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Validate operational chars table inputs
    validate_opchars(scenario_id, subscenarios, subproblem, stage, conn,
                     "gen_var_stor_hyb")

    # Validate var profiles input table
    validate_var_profiles(scenario_id, subscenarios, subproblem, stage, conn,
                          "gen_var_stor_hyb")
