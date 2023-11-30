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
This operational type describes direct air capture facilities that consume power in 
order to capture carbon from the atmosphere. Note that this should be modeled to burn
a fuel with a negative emissions intensity and they do require a simple heat rate.
Also note that projects of this type must be assigned a carbon cap zone in order to
contribute net negative emissions to the carbon constraint.
"""

from pyomo.environ import (
    Set,
    Var,
    Constraint,
    NonNegativeReals,
    PercentFraction,
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
from gridpath.project.common_functions import (
    check_if_first_timepoint,
    check_boundary_type,
)
from gridpath.project.operations.operational_types.common_functions import (
    load_optype_model_data,
    validate_opchars,
)


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
    | | :code:`DAC`                                                           |
    |                                                                         |
    | The set of generators of the :code:`dac` operational type.              |
    +-------------------------------------------------------------------------+
    | | :code:`DAC_OPR_TMPS`                                                  |
    |                                                                         |
    | Two-dimensional set with projects of the :code:`dac` operational type   |
    | and their operational timepoints.                                       |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`DAC_Consume_Power_MW`                                          |
    | | *Defined over*: :code:`DAC_OPR_TMPS`                                  |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Power consumption in MW from this project in each timepoint in which    |
    | the project is operational (capacity exists and the project is          |
    | available).                                                             |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | Power                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`DAC_Max_Power_Constraint`                                      |
    | | *Defined over*: :code:`DAC_OPR_TMPS`                                  |
    |                                                                         |
    | Limits the power consumption to the available capacity.                 |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.DAC = Set(
        within=m.PROJECTS,
        initialize=lambda mod: subset_init_by_param_value(
            mod, "PROJECTS", "operational_type", "dac"
        ),
    )

    m.DAC_OPR_TMPS = Set(
        dimen=2,
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: subset_init_by_set_membership(
            mod=mod, superset="PRJ_OPR_TMPS", index=0, membership_set=mod.DAC
        ),
    )

    # Variables
    ###########################################################################

    m.DAC_Consume_Power_MW = Var(m.DAC_OPR_TMPS, within=NonNegativeReals)

    # Constraints
    ###########################################################################

    m.DAC_Max_Power_Constraint = Constraint(m.DAC_OPR_TMPS, rule=max_power_rule)


# Constraint Formulation Rules
###############################################################################


# Power
def max_power_rule(mod, g, tmp):
    """
    **Constraint Name**: DAC_Max_Power_Constraint
    **Enforced Over**: DAC_OPR_TMPS

    Power consumption cannot exceed capacity.
    """
    return (
        mod.DAC_Consume_Power_MW[g, tmp]
        <= mod.Capacity_MW[g, mod.period[tmp]] * mod.Availability_Derate[g, tmp]
    )


# Operational Type Methods
###############################################################################


def power_provision_rule(mod, g, tmp):
    """
    Power provision from DAC is the negative of the power consumption.
    """
    return -mod.DAC_Consume_Power_MW[g, tmp]


def fuel_burn_rule(mod, g, tmp):
    """
    Fuel burn is the product of the fuel burn slope and the power output. The
    project fuel burn is later multiplied by the fuel emissions intensity to get the
    total captured emissions, so fuel_burn_slope x emissions_intensity should equal
    the amount of emissions captured per unit of consumed power.
    """
    return (
        mod.fuel_burn_slope_mmbtu_per_mwh[g, mod.period[tmp], 0]
        * mod.DAC_Consume_Power_MW[g, tmp]
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
            mod.DAC_Consume_Power_MW[g, tmp]
            - mod.DAC_Consume_Power_MW[
                g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]
            ]
        )


# Input-Output
###############################################################################


def load_model_data(
    mod,
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
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        op_type="dac",
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
        "dac",
    )

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
            "dac",
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        )
    )

    # Convert inputs to dataframe
    hr_df = cursor_to_df(heat_rates)

    # Check that there is only one load point (constant heat rate)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_heat_rate_curves",
        severity="Mid",
        errors=validate_single_input(
            df=hr_df,
            msg="dac can only have one load " "point (constant heat rate).",
        ),
    )
