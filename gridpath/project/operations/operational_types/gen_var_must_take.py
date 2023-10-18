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
This operational type is like the *gen_var* type with two main differences.
First, the project's output is must-take, i.e. curtailment (dispatch down) is
not allowed. Second, because the project's output is not controllable, projects
of this operational type cannot provide operational reserves .
"""

from pyomo.environ import Param, Set, Reals, Constraint
import warnings

from gridpath.auxiliary.auxiliary import (
    subset_init_by_param_value,
    subset_init_by_set_membership,
)
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
    get_prj_tmp_opr_inputs_from_db,
    write_tab_file_model_inputs,
    validate_opchars,
    validate_var_profiles,
    load_optype_model_data,
)


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`GEN_VAR_MUST_TAKE`                                             |
    |                                                                         |
    | The set of generators of the :code:`gen_var_must_take` operational type.|
    +-------------------------------------------------------------------------+
    | | :code:`GEN_VAR_MUST_TAKE_OPR_TMPS`                                    |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_var_must_take`    |
    | operational type and their operational timepoints.                      |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_var_must_take_cap_factor`                                  |
    | | *Defined over*: :code:`GEN_VAR_MUST_TAKE`                             |
    | | *Within*: :code:`Reals`                                               |
    |                                                                         |
    | The project's power output in each operational timepoint as a fraction  |
    | of its available capacity (i.e. the capacity factor).                   |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`GenVarMustTake_No_Upward_Reserves_Constraint`                  |
    | | *Defined over*: :code:`GEN_VAR_MUST_TAKE_OPR_TMPS`                    |
    |                                                                         |
    | Variable must-take generator projects cannot provide upward reserves.   |
    +-------------------------------------------------------------------------+
    | | :code:`GenVarMustTake_No_Downward_Reserves_Constraint`                |
    | | *Defined over*: :code:`GEN_VAR_MUST_TAKE_OPR_TMPS`                    |
    |                                                                         |
    | Variable must-take generator projects cannot provide downward reserves. |
    +-------------------------------------------------------------------------+


    """

    # Sets
    ###########################################################################

    m.GEN_VAR_MUST_TAKE = Set(
        within=m.PROJECTS,
        initialize=lambda mod: subset_init_by_param_value(
            mod, "PROJECTS", "operational_type", "gen_var_must_take"
        ),
    )

    m.GEN_VAR_MUST_TAKE_OPR_TMPS = Set(
        dimen=2,
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: subset_init_by_set_membership(
            mod=mod,
            superset="PRJ_OPR_TMPS",
            index=0,
            membership_set=mod.GEN_VAR_MUST_TAKE,
        ),
    )

    # Required Params
    ###########################################################################

    m.gen_var_must_take_cap_factor = Param(m.GEN_VAR_MUST_TAKE_OPR_TMPS, within=Reals)

    # Constraints
    ###########################################################################

    # TODO: remove this constraint once input validation is in place that
    #  does not allow specifying a reserve_zone if 'gen_var_must_take' type
    def no_upward_reserve_rule(mod, g, tmp):
        """
        **Constraint Name**: GenVarMustTake_No_Upward_Reserves_Constraint
        **Enforced Over**: GEN_VAR_MUST_TAKE_OPR_TMPS

        Upward reserves should be zero in every operational timepoint.
        """
        if getattr(d, headroom_variables)[g]:
            warnings.warn(
                """project {} is of the 'gen_var_must_take' operational 
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

    m.GenVarMustTake_No_Upward_Reserves_Constraint = Constraint(
        m.GEN_VAR_MUST_TAKE_OPR_TMPS, rule=no_upward_reserve_rule
    )

    # TODO: remove this constraint once input validation is in place that
    #  does not allow specifying a reserve_zone if 'gen_var_must_take' type
    def no_downward_reserve_rule(mod, g, tmp):
        """
        **Constraint Name**: GenVarMustTake_No_Downward_Reserves_Constraint
        **Enforced Over**: GEN_VAR_MUST_TAKE_OPR_TMPS

        Downward reserves should be zero in every operational timepoint.
        """
        if getattr(d, footroom_variables)[g]:
            warnings.warn(
                """project {} is of the 'gen_var_must_take' operational 
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

    m.GenVarMustTake_No_Downward_Reserves_Constraint = Constraint(
        m.GEN_VAR_MUST_TAKE_OPR_TMPS, rule=no_downward_reserve_rule
    )


# Operational Type Methods
###############################################################################


def power_provision_rule(mod, g, tmp):
    """
    Power provision from variable must-take generators is their capacity times
    the capacity factor in each timepoint.
    """

    return (
        mod.Capacity_MW[g, mod.period[tmp]]
        * mod.Availability_Derate[g, tmp]
        * mod.gen_var_must_take_cap_factor[g, tmp]
    )


def power_delta_rule(mod, g, tmp):
    """
    Exogenously defined ramp for variable must-take generators.

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
            mod.Capacity_MW[g, mod.period[tmp]]
            * mod.Availability_Derate[g, tmp]
            * mod.gen_var_must_take_cap_factor[g, tmp]
        ) - (
            mod.Capacity_MW[
                g, mod.period[mod.prev_tmp[tmp, mod.balancing_type_project[g]]]
            ]
            * mod.Availability_Derate[
                g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]
            ]
            * mod.gen_var_must_take_cap_factor[
                g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]
            ]
        )


# Inputs-Outputs
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

    # Load data from projects.tab and get the list of projects of this type
    projects = load_optype_model_data(
        mod=mod,
        data_portal=data_portal,
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        op_type="gen_var_must_take",
    )

    load_var_profile_inputs(
        data_portal, scenario_directory, subproblem, stage, "gen_var_must_take"
    )


# Database
###############################################################################


def get_model_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return: cursor object with query results
    """
    prj_tmp_data = get_prj_tmp_opr_inputs_from_db(
        subscenarios=subscenarios,
        subproblem=subproblem,
        stage=stage,
        conn=conn,
        op_type="gen_var_must_take",
        table="inputs_project_variable_generator_profiles" "",
        subscenario_id_column="variable_generator_profile_scenario_id",
        data_column="cap_factor",
    )

    return prj_tmp_data


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
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
        scenario_id, subscenarios, subproblem, stage, conn
    )
    fname = "variable_generator_profiles.tab"

    write_tab_file_model_inputs(scenario_directory, subproblem, stage, fname, data)


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
    opchar_df = validate_opchars(
        scenario_id, subscenarios, subproblem, stage, conn, "gen_var_must_take"
    )

    # Validate var profiles input table
    cap_factor_validation_error = validate_var_profiles(
        scenario_id, subscenarios, subproblem, stage, conn, "gen_var_must_take"
    )
    if cap_factor_validation_error:
        warnings.warn(
            """
            Found gen_var_must_take cap factors that are <0 or >1. This is 
            allowed but this warning is here to make sure it is intended.
            """
        )

    # Other module specific validations

    # Check that the project does not show up in any of the
    # inputs_project_reserve_bas tables since gen_var_must_take can't
    # provide any reserves
    projects_by_reserve = get_projects_by_reserve(scenario_id, subscenarios, conn)
    for reserve, projects_w_ba in projects_by_reserve.items():
        table = "inputs_project_" + reserve + "_bas"
        reserve_errors = validate_idxs(
            actual_idxs=opchar_df["project"],
            invalid_idxs=projects_w_ba,
            msg="gen_var_must_take cannot provide {}.".format(reserve),
        )

        write_validation_to_database(
            conn=conn,
            scenario_id=scenario_id,
            subproblem_id=subproblem,
            stage_id=stage,
            gridpath_module=__name__,
            db_table=table,
            severity="Mid",
            errors=reserve_errors,
        )
