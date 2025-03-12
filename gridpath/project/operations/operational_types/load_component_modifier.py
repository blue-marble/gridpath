# Copyright 2016-2025 Blue Marble Analytics LLC.
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
This operational type is linked to a specific load component that it modifies
based on 1) the project capacity relative to the load component peak load and
2) a load modification profile (fractional reduction or increase); positive
values indicate a load reduction and negative values indicate a load increase.
"""

from pyomo.environ import Param, Set, Reals, Constraint, Var, Any
import warnings

from gridpath.auxiliary.auxiliary import (
    subset_init_by_param_value,
    subset_init_by_set_membership,
)
from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.auxiliary.validations import (
    write_validation_to_database,
    get_projects_by_reserve,
    validate_idxs,
)
from gridpath.auxiliary.dynamic_components import headroom_variables, footroom_variables
from gridpath.project.common_functions import (
    check_if_first_timepoint,
    check_boundary_type,
)
from gridpath.project.operations.operational_types.common_functions import (
    load_var_profile_inputs,
    get_prj_temporal_index_opr_inputs_from_db,
    write_tab_file_model_inputs,
    validate_opchars,
    validate_var_profiles,
    load_optype_model_data,
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
    | | :code:`LOAD_COMPONENT_MODIFIER_PRJS`                                       |
    |                                                                         |
    | The set of generators of the :code:`load_component_modifier`            |
    | operational type.                                                       |
    +-------------------------------------------------------------------------+
    | | :code:`LOAD_COMPONENT_MODIFIER_PRJS_OPR_TMPS`                              |
    |                                                                         |
    | Two-dimensional set with generators of the                              |
    | :code:`load_component_modifier` operational type and their operational  |
    | timepoints.                                                             |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`load_component_modifier_fraction`                            |
    | | *Defined over*: :code:`LOAD_COMPONENT_MODIFIER_PRJS`                       |
    | | *Within*: :code:`Reals`                                               |
    |                                                                         |
    | The project's power output in each operational timepoint as a fraction  |
    | of its available capacity (i.e. the capacity factor).                   |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.LOAD_COMPONENT_MODIFIER_PRJS = Set(
        within=m.PROJECTS,
        initialize=lambda mod: subset_init_by_param_value(
            mod, "PROJECTS", "operational_type", "load_component_modifier"
        ),
    )

    m.LOAD_COMPONENT_MODIFIER_PRJS_OPR_TMPS = Set(
        dimen=2,
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: subset_init_by_set_membership(
            mod=mod,
            superset="PRJ_OPR_TMPS",
            index=0,
            membership_set=mod.LOAD_COMPONENT_MODIFIER_PRJS,
        ),
    )

    # Derived sets
    m.LOAD_COMPONENT_MODIFIER_PRJS_OPR_PRDS = Set(
        within=m.PRJ_OPR_PRDS,
        initialize=lambda mod: subset_init_by_set_membership(
            mod=mod,
            superset="PRJ_OPR_PRDS",
            index=0,
            membership_set=mod.LOAD_COMPONENT_MODIFIER_PRJS,
        ),
    )

    # Required Params
    ###########################################################################

    m.load_component_modifier_linked_load_component = Param(
        m.LOAD_COMPONENT_MODIFIER_PRJS,
        within=Any,
    )

    m.load_component_modifier_fraction = Param(
        m.LOAD_COMPONENT_MODIFIER_PRJS_OPR_TMPS, within=Reals
    )

    # Derived params
    m.load_component_modifier_load_component_peak_load_in_period = Param(
        m.LOAD_COMPONENT_MODIFIER_PRJS_OPR_PRDS,
        initialize=lambda mod, prj, prd: max(
            [
                mod.component_static_load_mw[
                    mod.load_zone[prj],
                    tmp,
                    mod.load_component_modifier_linked_load_component[prj],
                ]
                for tmp in mod.TMPS_IN_PRD[prd]
            ]
        ),
    )

    m.Load_Component_Modifier_Fraction_Invested = Var(
        m.LOAD_COMPONENT_MODIFIER_PRJS_OPR_PRDS, bounds=(0, 1), initialize=0
    )

    # Constraints
    ###########################################################################

    def fraction_invested_constraint_rule(mod, prj, prd):
        return (
            mod.Load_Component_Modifier_Fraction_Invested[prj, prd]
            == mod.Capacity_MW[prj, prd]
            / mod.load_component_modifier_load_component_peak_load_in_period[prj, prd]
        )

    m.Load_Component_Modifier_Fraction_Invested_Constraint = Constraint(
        m.LOAD_COMPONENT_MODIFIER_PRJS_OPR_PRDS, rule=fraction_invested_constraint_rule
    )

    # TODO: remove this constraint once input validation is in place that
    #  does not allow specifying a reserve_zone for 'load_component_modifier'
    #  type
    def no_upward_reserve_rule(mod, g, tmp):
        """
        **Constraint Name**: LoadComponentModifier_No_Upward_Reserves_Constraint
        **Enforced Over**: LOAD_COMPONENT_MODIFIER_PRJS_OPR_TMPS

        Upward reserves should be zero in every operational timepoint.
        """
        if getattr(d, headroom_variables)[g]:
            warnings.warn(
                """project {} is of the 'load_component_modifier' operational 
                type and should not be assigned any upward reserve BAs since it 
                cannot provide  upward reserves. Please replace the upward 
                reserve BA for project {} with '.' (no value) in projects.tab. 
                Model will add  constraint to ensure project {} cannot provide 
                upward reserves
                """.format(
                    g, g, g
                )
            )
            return (
                sum(getattr(mod, c)[g, tmp] for c in getattr(d, headroom_variables)[g])
                == 0
            )
        else:
            return Constraint.Skip

    m.LoadComponentModifier_No_Upward_Reserves_Constraint = Constraint(
        m.LOAD_COMPONENT_MODIFIER_PRJS_OPR_TMPS, rule=no_upward_reserve_rule
    )

    # TODO: remove this constraint once input validation is in place that
    #  does not allow specifying a reserve_zone if 'load_component_modifier' type
    def no_downward_reserve_rule(mod, g, tmp):
        """
        **Constraint Name**: LoadComponentModifier_No_Downward_Reserves_Constraint
        **Enforced Over**: LOAD_COMPONENT_MODIFIER_PRJS_OPR_TMPS

        Downward reserves should be zero in every operational timepoint.
        """
        if getattr(d, footroom_variables)[g]:
            warnings.warn(
                """project {} is of the 'load_component_modifier' operational 
                type and should not be assigned any downward reserve BAs since 
                it cannot provide downward reserves. Please replace the
                downward reserve BA for project {} with '.' (no value) in 
                projects.tab. Model will add constraint to ensure project {} 
                cannot provide downward reserves.
                """.format(
                    g, g, g
                )
            )
            return (
                sum(getattr(mod, c)[g, tmp] for c in getattr(d, footroom_variables)[g])
                == 0
            )
        else:
            return Constraint.Skip

    m.LoadComponentModifier_No_Downward_Reserves_Constraint = Constraint(
        m.LOAD_COMPONENT_MODIFIER_PRJS_OPR_TMPS, rule=no_downward_reserve_rule
    )


# Operational Type Methods
###############################################################################


def power_provision_rule(mod, prj, tmp):
    """
    Power provision from variable must-take generators is their capacity times
    the capacity factor in each timepoint.
    """

    return (
        mod.Load_Component_Modifier_Fraction_Invested[prj, mod.period[tmp]]
        * mod.Availability_Derate[prj, tmp]
        * mod.load_component_modifier_fraction[prj, tmp]
        * mod.component_static_load_mw[
            mod.load_zone[prj],
            tmp,
            mod.load_component_modifier_linked_load_component[prj],
        ]
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
        return power_provision_rule(mod, prj, tmp) - power_provision_rule(
            mod, prj, mod.prev_tmp[tmp, mod.balancing_type_project[prj]]
        )


# Inputs-Outputs
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

    # Load data from projects.tab and get the list of projects of this type
    projects = load_optype_model_data(
        mod=mod,
        data_portal=data_portal,
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        op_type="load_component_modifier",
    )

    load_var_profile_inputs(
        data_portal=data_portal,
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        op_type="load_component_modifier",
        tab_filename="load_component_modifier_fractions.tab",
        param_name="fraction",
    )


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

    prj_tmp_data = get_prj_temporal_index_opr_inputs_from_db(
        subscenarios=subscenarios,
        weather_iteration=db_weather_iteration,
        hydro_iteration=db_hydro_iteration,
        availability_iteration=db_availability_iteration,
        subproblem=db_subproblem,
        stage=db_stage,
        conn=conn,
        op_type="load_component_modifier",
        table="inputs_project_load_modifier_profiles",
        subscenario_id_column="load_modifier_profile_scenario_id",
        data_column="fraction",
    )

    return prj_tmp_data


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
    variable_generator_profiles.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    data = get_model_inputs_from_database(
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )
    fname = "load_component_modifier_fractions.tab"

    write_tab_file_model_inputs(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        fname,
        data,
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

    pass
