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
This operational type describes a battery-based model for a flexible load resource.

"""
import csv
import os.path
from pyomo.environ import (
    Var,
    Set,
    Constraint,
    Param,
    NonNegativeReals,
    PercentFraction,
    value,
)

from gridpath.auxiliary.auxiliary import subset_init_by_param_value
from gridpath.project.common_functions import (
    check_if_first_timepoint,
    check_boundary_type,
)
from gridpath.project.operations.operational_types.common_functions import (
    load_optype_model_data,
    check_for_tmps_to_link,
    validate_opchars,
)


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`FLEX_LOAD`                                                     |
    |                                                                         |
    | The set of projects of the :code:`stor` operational type.               |
    +-------------------------------------------------------------------------+
    | | :code:`FLEX_LOAD_OPR_TMPS`                                            |
    |                                                                         |
    | Two-dimensional set with projects of the :code:`stor`                   |
    | operational type and their operational timepoints.                      |
    +-------------------------------------------------------------------------+
    | | :code:`FLEX_LOAD_LINKED_TMPS`                                         |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`stor`                 |
    | operational type and their linked timepoints.                           |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`flex_load_charging_efficiency`                                 |
    | | *Defined over*: :code:`FLEX_LOAD`                                     |
    | | *Within*: :code:`PercentFraction`                                     |
    |                                                                         |
    | The storage project's charging efficiency (1 = 100% efficient).         |
    +-------------------------------------------------------------------------+
    | | :code:`flex_load_discharging_efficiency`                              |
    | | *Defined over*: :code:`FLEX_LOAD`                                     |
    | | *Within*: :code:`PercentFraction`                                     |
    |                                                                         |
    | The storage project's discharging efficiency (1 = 100% efficient).      |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`flex_load_losses_factor_in_energy_target`                      |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The fraction of storage losses that count against the energy target.    |
    +-------------------------------------------------------------------------+
    | | :code:`flex_load_losses_factor_curtailment`                           |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The fraction of storage losses that count against curtailment.          |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Linked Input Params                                                     |
    +=========================================================================+
    | | :code:`flex_load_linked_starting_energy_in_storage`                   |
    | | *Defined over*: :code:`FLEX_LOAD_LINKED_TMPS`                         |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's starting energy in storage in the linked timepoints.      |
    +-------------------------------------------------------------------------+
    | | :code:`flex_load_linked_discharge`                                    |
    | | *Defined over*: :code:`FLEX_LOAD_LINKED_TMPS`                         |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's dicharging in the linked timepoints.                      |
    +-------------------------------------------------------------------------+
    | | :code:`flex_load_linked_charge`                                       |
    | | *Defined over*: :code:`FLEX_LOAD_LINKED_TMPS`                         |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's charging in the linked timepoints.                        |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`Flex_Load_Charge_MW`                                                |
    | | *Defined over*: :code:`FLEX_LOAD_OPR_TMPS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Charging power in MW from this project in each timepoint in which the   |
    | project is operational (capacity exists and the project is available).  |
    +-------------------------------------------------------------------------+
    | | :code:`Flex_Load_Discharge_MW`                                             |
    | | *Defined over*: :code:`FLEX_LOAD_OPR_TMPS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Discharging power in MW from this project in each timepoint in which the|
    |  project is operational (capacity exists and the project is available). |
    +-------------------------------------------------------------------------+
    | | :code:`Flex_Load_Starting_Energy_in_Storage_MWh`                           |
    | | *Defined over*: :code:`FLEX_LOAD_OPR_TMPS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The state of charge of the storage project at the start of each         |
    | timepoint, in MWh of energy stored.                                     |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | Power and Stage of Charge                                               |
    +-------------------------------------------------------------------------+
    | | :code:`Flex_Load_Max_Charge_Constraint`                                    |
    | | *Defined over*: :code:`FLEX_LOAD_OPR_TMPS`                            |
    |                                                                         |
    | Limits the project's charging power to the available capacity.          |
    +-------------------------------------------------------------------------+
    | | :code:`Flex_Load_Max_Discharge_Constraint`                                 |
    | | *Defined over*: :code:`FLEX_LOAD_OPR_TMPS`                            |
    |                                                                         |
    | Limits the project's discharging power to the available capacity.       |
    +-------------------------------------------------------------------------+
    | | :code:`Flex_Load_Energy_Tracking_Constraint`                               |
    | | *Defined over*: :code:`FLEX_LOAD_OPR_TMPS`                            |
    |                                                                         |
    | Tracks the amount of energy stored in each timepoint based on the       |
    | previous timepoint's energy stored and the charge and discharge         |
    | decisions.                                                              |
    +-------------------------------------------------------------------------+
    | | :code:`Flex_Load_Max_Energy_in_Storage_Constraint`                         |
    | | *Defined over*: :code:`FLEX_LOAD_OPR_TMPS`                            |
    |                                                                         |
    | Limits the project's total energy stored to the available energy        |
    | capacity.                                                               |
    +-------------------------------------------------------------------------+
    | Reserves                                                                |
    +-------------------------------------------------------------------------+
    | | :code:`Flex_Load_Max_Headroom_Power_Constraint`                            |
    | | *Defined over*: :code:`FLEX_LOAD_OPR_TMPS`                            |
    |                                                                         |
    | Limits the project's upward reserves based on available headroom.       |
    | Going from charging to non-charging also counts as headroom, doubling   |
    | the maximum amount of potential headroom.                               |
    +-------------------------------------------------------------------------+
    | | :code:`Flex_Load_Max_Footroom_Power_Constraint`                            |
    | | *Defined over*: :code:`FLEX_LOAD_OPR_TMPS`                            |
    |                                                                         |
    | Limits the project's downward reserves based on available footroom.     |
    | Going from non-charging to charging also counts as footroom, doubling   |
    | the maximum amount of potential footroom.                               |
    +-------------------------------------------------------------------------+
    | | :code:`Flex_Load_Max_Headroom_Energy_Constraint`                           |
    | | *Defined over*: :code:`FLEX_LOAD_OPR_TMPS`                            |
    |                                                                         |
    | Can't provide more upward reserves (times sustained duration required)  |
    | than available energy in storage in that timepoint.                     |
    +-------------------------------------------------------------------------+
    | | :code:`Flex_Load_Max_Footroom_Energy_Constraint`                           |
    | | *Defined over*: :code:`FLEX_LOAD_OPR_TMPS`                            |
    |                                                                         |
    | Can't provide more downard reserves (times sustained duration required) |
    | than available capacity to store energy in that timepoint.              |
    +-------------------------------------------------------------------------+



    """

    # Sets
    ###########################################################################

    m.FLEX_LOAD = Set(
        within=m.PROJECTS,
        initialize=lambda mod: subset_init_by_param_value(
            mod, "PROJECTS", "operational_type", "flex_load"
        ),
    )

    m.FLEX_LOAD_OPR_TMPS = Set(
        dimen=2,
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: list(
            set((g, tmp) for (g, tmp) in mod.PRJ_OPR_TMPS if g in mod.FLEX_LOAD)
        ),
    )

    m.FLEX_LOAD_LINKED_TMPS = Set(dimen=2)

    # Required Params
    ###########################################################################

    m.flex_load_static_load_mw = Param(m.FLEX_LOAD_OPR_TMPS, within=NonNegativeReals)

    m.flex_load_maximum_stored_energy_mwh = Param(
        m.FLEX_LOAD_OPR_TMPS, within=NonNegativeReals
    )

    m.flex_load_charging_efficiency = Param(
        m.FLEX_LOAD, within=PercentFraction, default=1
    )
    m.flex_load_discharging_efficiency = Param(
        m.FLEX_LOAD, within=PercentFraction, default=1
    )
    m.flex_load_storage_efficiency = Param(
        m.FLEX_LOAD, within=PercentFraction, default=1
    )

    # Linked Params
    ###########################################################################

    m.flex_load_linked_starting_energy_in_storage = Param(
        m.FLEX_LOAD_LINKED_TMPS, within=NonNegativeReals
    )

    m.flex_load_linked_discharge = Param(
        m.FLEX_LOAD_LINKED_TMPS, within=NonNegativeReals
    )

    m.flex_load_linked_charge = Param(m.FLEX_LOAD_LINKED_TMPS, within=NonNegativeReals)

    # Variables
    ###########################################################################

    m.Flex_Load_Grid_MW = Var(m.FLEX_LOAD_OPR_TMPS, within=NonNegativeReals)

    m.Flex_Load_Charge_MW = Var(m.FLEX_LOAD_OPR_TMPS, within=NonNegativeReals)

    m.Flex_Load_Discharge_MW = Var(m.FLEX_LOAD_OPR_TMPS, within=NonNegativeReals)

    m.Flex_Load_Starting_Energy_in_Storage_MWh = Var(
        m.FLEX_LOAD_OPR_TMPS, within=NonNegativeReals
    )

    # Constraints
    ###########################################################################

    # Power and State of Charge
    m.Flex_Load_Max_Grid_Load_Constraint = Constraint(
        m.FLEX_LOAD_OPR_TMPS, rule=max_grid_load_constraint_rule
    )

    m.Flex_Load_Level_of_Service_Constraint = Constraint(
        m.FLEX_LOAD_OPR_TMPS, rule=level_of_service_constraint_rule
    )

    m.Flex_Load_Energy_Tracking_Constraint = Constraint(
        m.FLEX_LOAD_OPR_TMPS, rule=energy_tracking_rule
    )

    m.Flex_Load_Max_Energy_in_Storage_Constraint = Constraint(
        m.FLEX_LOAD_OPR_TMPS, rule=max_energy_in_storage_constraint_rule
    )


# Constraint Formulation Rules
###############################################################################


# Power and State of Charge
def max_grid_load_constraint_rule(mod, prj, tmp):
    """
    **Constraint Name**: Flex_Load_Max_Grid_Load_Constraint
    **Enforced Over**: FLEX_LOAD_OPR_TMPS

    The maximum load on the grid after shifting cannot exceed a pre-specified level in any timepoint.
    """
    return (
        mod.Flex_Load_Grid_MW[prj, tmp]
        <= mod.Capacity_MW[prj, mod.period[tmp]] * mod.Availability_Derate[prj, tmp]
    )


def level_of_service_constraint_rule(mod, prj, tmp):
    """
    **Constraint Name**: Flex_Load_Level_of_Service_Constraint
    **Enforced Over**: FLEX_LOAD_OPR_TMPS

    The static load-based level of service must be maintained.
    """
    return (
        mod.Flex_Load_Grid_MW[prj, tmp]
        - mod.Flex_Load_Charge_MW[prj, tmp]
        + mod.Flex_Load_Discharge_MW[prj, tmp]
        == mod.flex_load_static_load_mw[prj, tmp]
    )


def energy_tracking_rule(mod, prj, tmp):
    """
    **Constraint Name**: Flex_Load_Energy_Tracking_Constraint
    **Enforced Over**: FLEX_LOAD_OPR_TMPS

    The energy stored in each timepoint is equal to the energy stored in the
    previous timepoint minus any discharged power (adjusted for discharging
    efficiency and timepoint duration) plus any charged power (adjusted for
    charging efficiency and timepoint duration).
    """
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
        if check_if_first_timepoint(
            mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[prj]
        ) and check_boundary_type(
            mod=mod,
            tmp=tmp,
            balancing_type=mod.balancing_type_project[prj],
            boundary_type="linked",
        ):
            prev_tmp_hrs_in_tmp = mod.hrs_in_linked_tmp[0]
            prev_tmp_starting_energy_in_storage = (
                mod.flex_load_linked_starting_energy_in_storage[prj, 0]
            )
            prev_tmp_discharge = mod.flex_load_linked_discharge[prj, 0]
            prev_tmp_charge = mod.flex_load_linked_charge[prj, 0]
        else:
            prev_tmp_hrs_in_tmp = mod.hrs_in_tmp[
                mod.prev_tmp[tmp, mod.balancing_type_project[prj]]
            ]
            prev_tmp_starting_energy_in_storage = (
                mod.Flex_Load_Starting_Energy_in_Storage_MWh[
                    prj, mod.prev_tmp[tmp, mod.balancing_type_project[prj]]
                ]
            )
            prev_tmp_discharge = mod.Flex_Load_Discharge_MW[
                prj, mod.prev_tmp[tmp, mod.balancing_type_project[prj]]
            ]
            prev_tmp_charge = mod.Flex_Load_Charge_MW[
                prj, mod.prev_tmp[tmp, mod.balancing_type_project[prj]]
            ]

        return (
            mod.Flex_Load_Starting_Energy_in_Storage_MWh[prj, tmp]
            == prev_tmp_starting_energy_in_storage
            * mod.flex_load_storage_efficiency[prj]
            + prev_tmp_charge
            * prev_tmp_hrs_in_tmp
            * mod.flex_load_charging_efficiency[prj]
            - prev_tmp_discharge
            * prev_tmp_hrs_in_tmp
            / mod.flex_load_discharging_efficiency[prj]
        )


def max_energy_in_storage_constraint_rule(mod, prj, tmp):
    """
    **Constraint Name**: Flex_Load_Max_Energy_in_Storage_Constraint
    **Enforced Over**: FLEX_LOAD_OPR_TMPS

    The amount of energy stored in each operational timepoint cannot exceed
    the available energy capacity.
    """
    return (
        mod.Flex_Load_Starting_Energy_in_Storage_MWh[prj, tmp]
        <= mod.flex_load_maximum_stored_energy_mwh[prj, tmp]
    )


# Operational Type Methods
###############################################################################


def power_provision_rule(mod, prj, tmp):
    """
    Negative of the shifted load.
    """
    return -mod.Flex_Load_Grid_MW[prj, tmp]


# Input-Output
###############################################################################


def load_model_data(mod, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    load_optype_model_data(
        mod=mod,
        data_portal=data_portal,
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        op_type="flex_load",
    )

    flex_load_profiles_file = os.path.join(
        scenario_directory,
        subproblem,
        stage,
        "inputs",
        "flex_load_profiles.tab",
    )

    data_portal.load(
        filename=flex_load_profiles_file,
        param=(mod.flex_load_static_load_mw, mod.flex_load_maximum_stored_energy_mwh),
    )

    # # Linked timepoint params
    # linked_inputs_filename = os.path.join(
    #     scenario_directory,
    #     str(subproblem),
    #     str(stage),
    #     "inputs",
    #     "flex_load_linked_timepoint_params.tab",
    # )
    # if os.path.exists(linked_inputs_filename):
    #     data_portal.load(
    #         filename=linked_inputs_filename,
    #         index=mod.FLEX_LOAD_LINKED_TMPS,
    #         param=(
    #             mod.flex_load_linked_starting_energy_in_storage,
    #             mod.flex_load_linked_discharge,
    #             mod.flex_load_linked_charge,
    #         ),
    #     )
    # else:
    #     pass


def export_results(mod, d, scenario_directory, subproblem, stage):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param mod:
    :param d:
    :return:
    """
    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "dispatch_flex_load.csv",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "project",
                "period",
                "balancing_type_project",
                "horizon",
                "timepoint",
                "timepoint_weight",
                "number_of_hours_in_timepoint",
                "technology",
                "load_zone",
                "static_load_mw",
                "flex_load_mw",
                "starting_energy_mwh",
                "charge_mw",
                "discharge_mw",
            ]
        )
        for p, tmp in mod.FLEX_LOAD_OPR_TMPS:
            writer.writerow(
                [
                    p,
                    mod.period[tmp],
                    mod.balancing_type_project[p],
                    mod.horizon[tmp, mod.balancing_type_project[p]],
                    tmp,
                    mod.tmp_weight[tmp],
                    mod.hrs_in_tmp[tmp],
                    mod.technology[p],
                    mod.load_zone[p],
                    mod.flex_load_static_load_mw[p, tmp],
                    value(mod.Flex_Load_Grid_MW[p, tmp]),
                    value(mod.Flex_Load_Starting_Energy_in_Storage_MWh[p, tmp]),
                    value(mod.Flex_Load_Charge_MW[p, tmp]),
                    value(mod.Flex_Load_Discharge_MW[p, tmp]),
                ]
            )

    # # If there's a linked_subproblems_map CSV file, check which of the
    # # current subproblem TMPS we should export results for to link to the
    # # next subproblem
    # tmps_to_link, tmp_linked_tmp_dict = check_for_tmps_to_link(
    #     scenario_directory=scenario_directory, subproblem=subproblem, stage=stage
    # )
    #
    # # If the list of timepoints to link is not empty, write the linked
    # # timepoint results for this module in the next subproblem's input
    # # directory
    # if tmps_to_link:
    #     next_subproblem = str(int(subproblem) + 1)
    #
    #     # Export params by project and timepoint
    #     with open(
    #         os.path.join(
    #             scenario_directory,
    #             next_subproblem,
    #             stage,
    #             "inputs",
    #             "flex_load_linked_timepoint_params.tab",
    #         ),
    #         "w",
    #         newline="",
    #     ) as f:
    #         writer = csv.writer(f, delimiter="\t", lineterminator="\n")
    #         writer.writerow(
    #             [
    #                 "project",
    #                 "linked_timepoint",
    #                 "linked_starting_energy_in_storage",
    #                 "linked_discharge",
    #                 "linked_charge",
    #             ]
    #         )
    #         for p, tmp in sorted(mod.FLEX_LOAD_OPR_TMPS):
    #             if tmp in tmps_to_link:
    #                 writer.writerow(
    #                     [
    #                         p,
    #                         tmp_linked_tmp_dict[tmp],
    #                         max(
    #                             value(
    #                                 mod.Flex_Load_Starting_Energy_in_Storage_MWh[p, tmp]
    #                             ),
    #                             0,
    #                         ),
    #                         max(value(mod.Flex_Load_Discharge_MW[p, tmp]), 0),
    #                         max(value(mod.Flex_Load_Charge_MW[p, tmp]), 0),
    #                     ]
    #                 )


def validate_inputs(scenario_id, subscenarioprj, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Validate operational chars table inputs
    validate_opchars(scenario_id, subscenarioprj, subproblem, stage, conn, "flex_load")
