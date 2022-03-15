# Copyright 2016-2021 Blue Marble Analytics LLC.
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
This operational type describes fuel production facilities.

The type is associated with three main variables in each timepoint when the
project is available: the fuel production level, the fuel release level, and the
fuel available in storage. The first two are constrained to be less than
or equal to the project's fuel production and fuel release capacity respectively. The
third is constrained to be less than or equal to the project's fuel storage capacity.
The model tracks the amount of fuel available in storage in each timepoint based on the
fuel production and fuel release decisions decisions in the previous timepoint. Fuel
production projects do not provide reserves or other system services.

Costs for this operational type include variable O&M costs. (?)

"""

from pyomo.environ import Set, Param, Var, Constraint, NonNegativeReals

from gridpath.auxiliary.auxiliary import subset_init_by_param_value
from gridpath.project.common_functions import (
    check_if_first_timepoint,
    check_boundary_type,
)


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    """
    # Sets
    ###########################################################################

    m.FUEL_PROD = Set(
        within=m.PROJECTS,
        initialize=lambda mod: subset_init_by_param_value(
            mod, "PROJECTS", "operational_type", "fuel_prod"
        ),
    )

    m.FUEL_PROD_OPR_TMPS = Set(
        dimen=2,
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: list(
            set((g, tmp) for (g, tmp) in mod.PRJ_OPR_TMPS if g in mod.STOR)
        ),
    )

    # TODO: link fuel storage
    m.FUEL_PROD_LINKED_TMPS = Set(dimen=2)

    # Required Params
    ###########################################################################

    m.fuel_prod_fuelunit_per_powerunit = Param(m.FUEL_PROD, within=NonNegativeReals)

    # TODO: how should variable cost be defined
    # m.fuel_prod_var_cost = Param(m.FUEL_PROD, within=NonNegativeReals)

    # Variables
    ###########################################################################

    m.Produce_Fuel_FuelUnit = Var(m.FUEL_PROD_OPR_TMPS, within=NonNegativeReals)

    m.Release_Fuel_FuelUnit = Var(m.FUEL_PROD_OPR_TMPS, within=NonNegativeReals)

    m.Fuel_Prod_Fuel_in_Storage_FuelUnit = Var(
        m.FUEL_PROD_OPR_TMPS, within=NonNegativeReals
    )
    
    m.Fuel_Prod_Consume_Power_PowerUnit = Var(m.FUEL_PROD_OPR_TMPS, within=NonNegativeReals)
    
    # Constraints
    ###########################################################################

    m.Fuel_Prod_Max_Production_Constraint = Constraint(
        m.FUEL_PROD_OPR_TMPS, rule=max_production_rule
    )

    m.Fuel_Prod_Max_Release_Constraint = Constraint(
        m.FUEL_PROD_OPR_TMPS, rule=max_release_rule
    )

    m.Fuel_Prod_Fuel_Tracking_Constraint = Constraint(
        m.FUEL_PROD_OPR_TMPS, rule=fuel_in_storage_tracking_rule
    )

    m.Fuel_Prod_Max_Fuel_in_Storage_Constraint = Constraint(
        m.FUEL_PROD_OPR_TMPS, rule=max_fuel_in_storage_rule
    )
    
    # Fuel produced
    m.Fuel_Production_in_Timepoint = Constraint(
        m.FUEL_PROD_OPR_TMPS, rule=fuel_production_rule
    )


# Constraint Formulation Rules
###############################################################################

# Power and State of Charge
def max_production_rule(mod, prj, tmp):
    """
    **Constraint Name**: Fuel_Prod_Max_Production_Constraint
    **Enforced Over**: FUEL_PROD_OPR_TMPS

    Fuel production can't exceed available production capacity.
    """
    return (
        mod.Produce_Fuel_FuelUnit[prj, tmp]
        <= mod.Fuel_Production_Capacity_FuelUnitHour[prj, mod.period[tmp]]
        * mod.Availability_Derate[prj, tmp]
    )


def max_release_rule(mod, prj, tmp):
    """
    **Constraint Name**: Fuel_Prod_Max_Release_Constraint
    **Enforced Over**: FUEL_PROD_OPR_TMPS

    Fuel production can't exceed available production capacity.
    """
    return (
        mod.Release_Fuel_FuelUnit[prj, tmp]
        <= mod.Fuel_Release_Capacity_FuelUnitHour[prj, mod.period[tmp]]
        * mod.Availability_Derate[prj, tmp]
    )


def fuel_in_storage_tracking_rule(mod, prj, tmp):
    """
    **Constraint Name**: Fuel_Prod_Fuel_Tracking_Constraint
    **Enforced Over**: FUEL_PROD_OPR_TMPS

    The fuel in storage in each timepoint is equal to the fuel in storage in the
    previous timepoint plus fuel production in the previous timepoint (adjusted for
    timepoint duration) minus fuel release in the previous timepoint (adjusted for 
    timepoint duration).
    """
    # No constraint enforced if this is the first timepoint of a linear horizon type
    if check_if_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[prj]
    ) and check_boundary_type(
        mod=mod,
        tmp=tmp,
        balancing_type=mod.balancing_type_project[prj],
        boundary_type="linear",
    ):
        return Constraint.Skip
    else:
        # If the boundary type is linked, we need find the linked params; otherwise, 
        # we look at the previous timepoint
        if check_if_first_timepoint(
            mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[prj]
        ) and check_boundary_type(
            mod=mod,
            tmp=tmp,
            balancing_type=mod.balancing_type_project[prj],
            boundary_type="linked",
        ):
            # prev_tmp_hrs_in_tmp = mod.hrs_in_linked_tmp[0]
            # prev_tmp_starting_energy_in_storage = (
            #     mod.stor_linked_starting_energy_in_storage[prj, 0]
            # )
            # prev_tmp_discharge = mod.stor_linked_discharge[prj, 0]
            # prev_tmp_charge = mod.stor_linked_charge[prj, 0]
            raise("Linked horizons are not implemented yet for fuel production "
                  "facilities.")
        else:
            prev_tmp_hrs_in_tmp = mod.hrs_in_tmp[
                mod.prev_tmp[tmp, mod.balancing_type_project[prj]]
            ]
            prev_tmp_starting_fuel_in_storage = (
                mod.Fuel_Prod_Fuel_in_Storage_FuelUnit[
                    prj, mod.prev_tmp[tmp, mod.balancing_type_project[prj]]
                ]
            )
            prev_tmp_production = mod.Produce_Fuel_FuelUnit[
                prj, mod.prev_tmp[tmp, mod.balancing_type_project[prj]]
            ]
            prev_tmp_release = mod.Release_Fuel_FuelUnit[
                prj, mod.prev_tmp[tmp, mod.balancing_type_project[prj]]
            ]

        return (
            mod.Stor_Starting_Energy_in_Storage_MWh[prj, tmp]
            == prev_tmp_starting_fuel_in_storage
            + prev_tmp_production * prev_tmp_hrs_in_tmp * mod.stor_charging_efficiency[prj]
            - prev_tmp_release
            * prev_tmp_hrs_in_tmp
            / mod.stor_discharging_efficiency[prj]
        )


def max_fuel_in_storage_rule(mod, prj, tmp):
    """
    **Constraint Name**: Fuel_Prod_Max_Fuel_in_Storage_Constraint
    **Enforced Over**: FUEL_PROD_OPR_TMPS

    The amount of fuel stored in each operational timepoint cannot exceed
    the available fuel storage capacity.
    """
    return (
        mod.Fuel_Prod_Fuel_in_Storage_FuelUnit[prj, tmp]
        <= mod.Fuel_Storage_Capacity_FuelUnit[prj, mod.period[tmp]] *
        mod.Availability_Derate[prj, tmp]
    )


def fuel_production_rule(mod, prj, tmp):
    """

    """
    return mod.Produce_Fuel_FuelUnit[prj, tmp] <= \
        mod.Fuel_Prod_Consume_Power_PowerUnit[prj, tmp] * mod.fuel_prod_fuelunit_per_mwh[prj]


# Operational Type Methods
###############################################################################

def power_provision_rule(mod, prj, tmp):
    """
    Power provision is a load, so a negative number is return here whenever fuel is
    being produced.
    """
    return - mod.Fuel_Prod_Consume_Power_PowerUnit[prj, tmp]


# # TODO: confirm how to apply variable costs
# def variable_om_cost_rule(mod, g, tmp):
#     """
#     """
#     return

# # TODO: finish this
# def power_delta_rule(mod, g, tmp):
#     """
#     This rule is only used in tuning costs, so fine to skip for linked
#     horizon's first timepoint.
#     """
#     return

def fuel_burn_rule(mod, prj, tmp):
    """
    Fuel burn returned is negative (i.e. added to the fuel availability)
    """
    return -mod.Release_Fuel_FuelUnit[prj, tmp]
