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
This operational type describes generators that can vary their output
between zero and full capacity in every timepoint in which they are available
(i.e. they have a power output variable but no commitment variables associated
with them).

The heat rate of these generators does not degrade below full load and they
can be allowed to provide upward and/or downward reserves subject to
available headroom and footroom. Ramp limits can be optionally specified.

Costs for this operational type include fuel costs, variable O&M costs, and
startup and shutdown costs.

"""

import csv
import os
from pyomo.environ import (
    Set,
    Var,
    Constraint,
    NonNegativeReals,
    Param,
    PercentFraction,
    Expression,
    value,
)

from gridpath.auxiliary.auxiliary import (
    subset_init_by_param_value,
    cursor_to_df,
    subset_init_by_set_membership,
)
from gridpath.auxiliary.validations import (
    write_validation_to_database,
    validate_single_input,
)
from gridpath.auxiliary.dynamic_components import headroom_variables, footroom_variables
from gridpath.project.common_functions import (
    check_if_boundary_type_and_first_timepoint,
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
    | | :code:`GEN_SIMPLE`                                                    |
    |                                                                         |
    | The set of generators of the :code:`gen_simple` operational type.       |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_SIMPLE_OPR_TMPS`                                           |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_simple`           |
    | operational type and their operational timepoints.                      |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_SIMPLE_LINKED_TMPS`                                        |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_simple`           |
    | operational type and their linked timepoints.                           |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_simple_ramp_up_when_on_rate`                               |
    | | *Defined over*: :code:`GEN_SIMPLE`                                    |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's upward ramp rate limit during operations, defined as a    |
    | fraction of its capacity per minute.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`gen_simple_ramp_down_when_on_rate`                             |
    | | *Defined over*: :code:`GEN_SIMPLE`                                    |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's downward ramp rate limit during operations, defined as a  |
    | fraction of its capacity per minute.                                    |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Linked Input Params                                                     |
    +=========================================================================+
    | | :code:`gen_simple_linked_power`                                       |
    | | *Defined over*: :code:`GEN_SIMPLE_LINKED_TMPS`                        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's power provision in the linked timepoints.                 |
    +-------------------------------------------------------------------------+
    | | :code:`gen_simple_linked_upwards_reserves`                            |
    | | *Defined over*: :code:`GEN_SIMPLE_LINKED_TMPS`                        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's upward reserve provision in the linked timepoints.        |
    +-------------------------------------------------------------------------+
    | | :code:`gen_simple_linked_downwards_reserves`                          |
    | | *Defined over*: :code:`GEN_SIMPLE_LINKED_TMPS`                        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's downward reserve provision in the linked timepoints.      |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`GenSimple_Provide_Power_MW`                                    |
    | | *Defined over*: :code:`GEN_SIMPLE_OPR_TMPS`                           |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Power provision in MW from this project in each timepoint in which the  |
    | project is operational (capacity exists and the project is available).  |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | Power                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`GenSimple_Max_Power_Constraint`                                |
    | | *Defined over*: :code:`GEN_SIMPLE_OPR_TMPS`                           |
    |                                                                         |
    | Limits the power plus upward reserves to the available capacity.        |
    +-------------------------------------------------------------------------+
    | | :code:`GenSimple_Min_Power_Constraint`                                |
    | | *Defined over*: :code:`GEN_SIMPLE_OPR_TMPS`                           |
    |                                                                         |
    | Power provision minus downward reserves should exceed the minimum       |
    | stable level for the project.                                           |
    +-------------------------------------------------------------------------+
    | Ramps                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`GenSimple_Ramp_Up_Constraint`                                  |
    | | *Defined over*: :code:`GEN_SIMPLE_OPR_TMPS`                           |
    |                                                                         |
    | Limits the allowed project upward ramp based on the                     |
    | :code:`gen_simple_ramp_up_when_on_rate`.                                |
    +-------------------------------------------------------------------------+
    | | :code:`GenSimple_Ramp_Down_Constraint`                                |
    | | *Defined over*: :code:`GEN_SIMPLE_OPR_TMPS`                           |
    |                                                                         |
    | Limits the allowed project downward ramp based on the                   |
    | :code:`gen_simple_ramp_down_when_on_rate`.                              |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.GEN_SIMPLE = Set(
        within=m.PROJECTS,
        initialize=lambda mod: subset_init_by_param_value(
            mod, "PROJECTS", "operational_type", "gen_simple"
        ),
    )

    m.GEN_SIMPLE_OPR_TMPS = Set(
        dimen=2,
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: subset_init_by_set_membership(
            mod=mod, superset="PRJ_OPR_TMPS", index=0, membership_set=mod.GEN_SIMPLE
        ),
    )

    m.GEN_SIMPLE_LINKED_TMPS = Set(dimen=2)

    # Optional Params
    ###########################################################################

    m.gen_simple_ramp_up_when_on_rate = Param(
        m.GEN_SIMPLE, within=PercentFraction, default=1
    )
    m.gen_simple_ramp_down_when_on_rate = Param(
        m.GEN_SIMPLE, within=PercentFraction, default=1
    )

    # Linked Params
    ###########################################################################

    m.gen_simple_linked_power = Param(m.GEN_SIMPLE_LINKED_TMPS, within=NonNegativeReals)

    m.gen_simple_linked_upwards_reserves = Param(
        m.GEN_SIMPLE_LINKED_TMPS, within=NonNegativeReals
    )

    m.gen_simple_linked_downwards_reserves = Param(
        m.GEN_SIMPLE_LINKED_TMPS, within=NonNegativeReals
    )

    # Variables
    ###########################################################################

    m.GenSimple_Provide_Power_MW = Var(m.GEN_SIMPLE_OPR_TMPS, within=NonNegativeReals)

    # Expressions
    ###########################################################################

    def upwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp] for c in getattr(d, headroom_variables)[g])

    m.GenSimple_Upwards_Reserves_MW = Expression(
        m.GEN_SIMPLE_OPR_TMPS, rule=upwards_reserve_rule
    )

    def downwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp] for c in getattr(d, footroom_variables)[g])

    m.GenSimple_Downwards_Reserves_MW = Expression(
        m.GEN_SIMPLE_OPR_TMPS, rule=downwards_reserve_rule
    )

    # Constraints
    ###########################################################################

    m.GenSimple_Max_Power_Constraint = Constraint(
        m.GEN_SIMPLE_OPR_TMPS, rule=max_power_rule
    )

    m.GenSimple_Min_Power_Constraint = Constraint(
        m.GEN_SIMPLE_OPR_TMPS, rule=min_power_rule
    )

    m.GenSimple_Ramp_Up_Constraint = Constraint(
        m.GEN_SIMPLE_OPR_TMPS, rule=ramp_up_rule
    )

    m.GenSimple_Ramp_Down_Constraint = Constraint(
        m.GEN_SIMPLE_OPR_TMPS, rule=ramp_down_rule
    )


# Constraint Formulation Rules
###############################################################################


# Power
def max_power_rule(mod, g, tmp):
    """
    **Constraint Name**: GenSimple_Max_Power_Constraint
    **Enforced Over**: GEN_SIMPLE_OPR_TMPS

    Power plus upward services cannot exceed capacity.
    """
    return (
        mod.GenSimple_Provide_Power_MW[g, tmp]
        + mod.GenSimple_Upwards_Reserves_MW[g, tmp]
        <= mod.Capacity_MW[g, mod.period[tmp]] * mod.Availability_Derate[g, tmp]
    )


def min_power_rule(mod, g, tmp):
    """
    **Constraint Name**: GenSimple_Min_Power_Constraint
    **Enforced Over**: GEN_SIMPLE_OPR_TMPS

    Power minus downward services cannot be below zero.
    """
    return (
        mod.GenSimple_Provide_Power_MW[g, tmp]
        - mod.GenSimple_Downwards_Reserves_MW[g, tmp]
        >= 0
    )


# Ramps
def ramp_up_rule(mod, g, tmp):
    """
    **Constraint Name**: GenSimple_Ramp_Up_Constraint
    **Enforced Over**: GEN_SIMPLE_OPR_TMPS

    Difference between power generation of consecutive timepoints, adjusted
    for reserve provision in current and previous timepoint, has to obey
    ramp up rate limits.

    We assume that a unit has to reach its setpoint at the start of the
    timepoint; as such, the ramping between 2 timepoints is assumed to
    take place during the duration of the first timepoint, and the
    ramp rate limit is adjusted for the duration of the first timepoint.
    """
    if check_if_boundary_type_and_first_timepoint(
        mod=mod,
        tmp=tmp,
        balancing_type=mod.balancing_type_project[g],
        boundary_type="linear",
    ):
        return Constraint.Skip
    else:
        if check_if_boundary_type_and_first_timepoint(
            mod=mod,
            tmp=tmp,
            balancing_type=mod.balancing_type_project[g],
            boundary_type="linked",
        ):
            prev_tmp_hrs_in_tmp = mod.hrs_in_linked_tmp[0]
            prev_tmp_power = mod.gen_simple_linked_power[g, 0]
            prev_tmp_downwards_reserves = mod.gen_simple_linked_downwards_reserves[g, 0]
        else:
            prev_tmp_hrs_in_tmp = mod.hrs_in_tmp[
                mod.prev_tmp[tmp, mod.balancing_type_project[g]]
            ]
            prev_tmp_power = mod.GenSimple_Provide_Power_MW[
                g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]
            ]
            prev_tmp_downwards_reserves = mod.GenSimple_Downwards_Reserves_MW[
                g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]
            ]
        # If ramp rate limits, adjusted for timepoint duration, allow you to
        # ramp up the full operable range between timepoints, constraint won't
        # bind, so skip
        if mod.gen_simple_ramp_up_when_on_rate[g] * 60 * prev_tmp_hrs_in_tmp >= 1:
            return Constraint.Skip
        else:
            return (
                mod.GenSimple_Provide_Power_MW[g, tmp]
                + mod.GenSimple_Upwards_Reserves_MW[g, tmp]
                - (prev_tmp_power - prev_tmp_downwards_reserves)
                <= mod.gen_simple_ramp_up_when_on_rate[g]
                * 60
                * prev_tmp_hrs_in_tmp
                * mod.Capacity_MW[g, mod.period[tmp]]
                * mod.Availability_Derate[g, tmp]
            )


def ramp_down_rule(mod, g, tmp):
    """
    **Constraint Name**: GenSimple_Ramp_Down_Constraint
    **Enforced Over**: GEN_SIMPLE_OPR_TMPS

    Difference between power generation of consecutive timepoints, adjusted
    for reserve provision in current and previous timepoint, has to obey
    ramp down rate limits.

    We assume that a unit has to reach its setpoint at the start of the
    timepoint; as such, the ramping between 2 timepoints is assumed to
    take place during the duration of the first timepoint, and the
    ramp rate limit is adjusted for the duration of the first timepoint.
    """
    if check_if_boundary_type_and_first_timepoint(
        mod=mod,
        tmp=tmp,
        balancing_type=mod.balancing_type_project[g],
        boundary_type="linear",
    ):
        return Constraint.Skip
    else:
        if check_if_boundary_type_and_first_timepoint(
            mod=mod,
            tmp=tmp,
            balancing_type=mod.balancing_type_project[g],
            boundary_type="linked",
        ):
            prev_tmp_hrs_in_tmp = mod.hrs_in_linked_tmp[0]
            prev_tmp_power = mod.gen_simple_linked_power[g, 0]
            prev_tmp_upwards_reserves = mod.gen_simple_linked_upwards_reserves[g, 0]
        else:
            prev_tmp_hrs_in_tmp = mod.hrs_in_tmp[
                mod.prev_tmp[tmp, mod.balancing_type_project[g]]
            ]
            prev_tmp_power = mod.GenSimple_Provide_Power_MW[
                g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]
            ]
            prev_tmp_upwards_reserves = mod.GenSimple_Upwards_Reserves_MW[
                g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]
            ]
        # If ramp rate limits, adjusted for timepoint duration, allow you to
        # ramp down the full operable range between timepoints, constraint
        # won't bind, so skip
        if mod.gen_simple_ramp_down_when_on_rate[g] * 60 * prev_tmp_hrs_in_tmp >= 1:
            return Constraint.Skip
        else:
            return (
                mod.GenSimple_Provide_Power_MW[g, tmp]
                - mod.GenSimple_Downwards_Reserves_MW[g, tmp]
                - (prev_tmp_power + prev_tmp_upwards_reserves)
                >= -mod.gen_simple_ramp_down_when_on_rate[g]
                * 60
                * prev_tmp_hrs_in_tmp
                * mod.Capacity_MW[g, mod.period[tmp]]
                * mod.Availability_Derate[g, tmp]
            )


# Operational Type Methods
###############################################################################


def power_provision_rule(mod, g, tmp):
    """
    Power provision from simple generators is an endogenous variable.
    """
    return mod.GenSimple_Provide_Power_MW[g, tmp]


def fuel_burn_rule(mod, g, tmp):
    """
    Fuel burn is the product of the fuel burn slope and the power output. For
    simple generators we assume only one average heat rate is specified in
    heat_rate_curves.tab, so the fuel burn slope is equal to the specified
    heat rate and the intercept is zero.
    """
    return (
        mod.fuel_burn_slope_mmbtu_per_mwh[g, mod.period[tmp], 0]
        * mod.GenSimple_Provide_Power_MW[g, tmp]
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
            mod.GenSimple_Provide_Power_MW[g, tmp]
            - mod.GenSimple_Provide_Power_MW[
                g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]
            ]
        )


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

    projects = load_optype_model_data(
        mod=mod,
        data_portal=data_portal,
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        op_type="gen_simple",
    )

    # Linked timepoint params
    linked_inputs_filename = os.path.join(
        scenario_directory,
        str(subproblem),
        str(stage),
        "inputs",
        "gen_simple_linked_timepoint_params.tab",
    )
    if os.path.exists(linked_inputs_filename):
        data_portal.load(
            filename=linked_inputs_filename,
            index=mod.GEN_SIMPLE_LINKED_TMPS,
            param=(
                mod.gen_simple_linked_power,
                mod.gen_simple_linked_upwards_reserves,
                mod.gen_simple_linked_downwards_reserves,
            ),
        )


def export_results(mod, d, scenario_directory, subproblem, stage):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param mod:
    :param d:
    :return:
    """
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
                "gen_simple_linked_timepoint_params.tab",
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
            for p, tmp in sorted(mod.GEN_SIMPLE_OPR_TMPS):
                if tmp in tmps_to_link:
                    writer.writerow(
                        [
                            p,
                            tmp_linked_tmp_dict[tmp],
                            max(value(mod.GenSimple_Provide_Power_MW[p, tmp]), 0),
                            max(value(mod.GenSimple_Upwards_Reserves_MW[p, tmp]), 0),
                            max(value(mod.GenSimple_Downwards_Reserves_MW[p, tmp]), 0),
                        ]
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
    validate_opchars(scenario_id, subscenarios, subproblem, stage, conn, "gen_simple")

    # Other module specific validations

    c = conn.cursor()
    heat_rates = c.execute(
        """
        SELECT project, load_point_fraction
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, operational_type, heat_rate_curves_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        AND operational_type = '{}') AS op_char
        USING(project)
        INNER JOIN
        (SELECT project, heat_rate_curves_scenario_id, load_point_fraction
        FROM inputs_project_heat_rate_curves) as heat_rates
        USING(project, heat_rate_curves_scenario_id)
        WHERE project_portfolio_scenario_id = {}
        """.format(
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            "gen_simple",
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        )
    )

    # Convert inputs to dataframe
    hr_df = cursor_to_df(heat_rates)

    # Check that there is only one load point (constant heat rate)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_heat_rate_curves",
        severity="Mid",
        errors=validate_single_input(
            df=hr_df,
            msg="gen_simple can only have one load " "point (constant heat rate).",
        ),
    )
