#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This operational type is like the *gen_var* type with two main differences.
First, the project's output is must-take, i.e. curtailment (dispatch down) is
not allowed. Second, because the project's output is not controllable, projects
of this operational type cannot provide operational reserves .
"""

from builtins import zip
import csv
import os.path
import pandas as pd
from pyomo.environ import Param, Set, NonNegativeReals, Constraint
import warnings

from gridpath.auxiliary.auxiliary import generator_subset_init, \
    write_validation_to_database, get_projects_by_reserve, \
    check_projects_for_reserves
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables
from gridpath.project.common_functions import \
    check_if_first_timepoint, check_boundary_type


def add_module_specific_components(m, d):
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
    | | *Within*: :code:`NonNegativeReals`                                    |
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
        initialize=generator_subset_init("operational_type",
                                         "gen_var_must_take")
    )

    m.GEN_VAR_MUST_TAKE_OPR_TMPS = Set(
        dimen=2, within=m.PRJ_OPR_TMPS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PRJ_OPR_TMPS
            if g in mod.GEN_VAR_MUST_TAKE)
    )

    # Required Params
    ###########################################################################

    # TODO: allow cap factors greater than 1, but throw a warning?
    m.gen_var_must_take_cap_factor = Param(
        m.GEN_VAR_MUST_TAKE_OPR_TMPS,
        within=NonNegativeReals
    )

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
                """.format(g, g, g)
            )
            return sum(getattr(mod, c)[g, tmp]
                       for c in getattr(d, headroom_variables)[g]) == 0
        else:
            return Constraint.Skip

    m.GenVarMustTake_No_Upward_Reserves_Constraint = Constraint(
        m.GEN_VAR_MUST_TAKE_OPR_TMPS,
        rule=no_upward_reserve_rule
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
                """.format(g, g, g)
            )
            return sum(getattr(mod, c)[g, tmp]
                       for c in getattr(d, footroom_variables)[g]) == 0
        else:
            return Constraint.Skip

    m.GenVarMustTake_No_Downward_Reserves_Constraint = Constraint(
        m.GEN_VAR_MUST_TAKE_OPR_TMPS,
        rule=no_downward_reserve_rule
    )


# Operational Type Methods
###############################################################################

def power_provision_rule(mod, g, tmp):
    """
    Power provision from variable must-take generators is their capacity times
    the capacity factor in each timepoint.
    """

    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp] \
        * mod.gen_var_must_take_cap_factor[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Since there is no commitment, all capacity is assumed to be online.
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision from variable must-take generators is the same as power
    provision: their capacity times the capacity factor in each timepoint.
    """

    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp] \
        * mod.gen_var_must_take_cap_factor[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    No curtailment allowed for must-take variable generators.
    """
    return 0


def subhourly_curtailment_rule(mod, g, tmp):
    """
    Can't provide downward reserves, so no sub-hourly curtailment.
    """
    return 0


def subhourly_energy_delivered_rule(mod, g, tmp):
    """
    Can't provide upward reserves, so no sub-hourly energy delivered.
    """
    return 0


def fuel_burn_rule(mod, g, tmp):
    """
    Variable generators should not have fuel use.
    """
    if g in mod.FUEL_PRJS:
        raise ValueError(
            "ERROR! Variable projects should not use fuel." + "\n" +
            "Check input data for project '{}'".format(g) + "\n" +
            "and change its fuel to '.' (no value)."
        )
    else:
        return 0


def variable_om_cost_rule(mod, g, tmp):
    """
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp] \
        * mod.gen_var_must_take_cap_factor[g, tmp] \
        * mod.variable_om_cost_per_mwh[g]


def startup_cost_rule(mod, g, tmp):
    """
    Since there is no commitment, there is no concept of starting up.
    """
    return 0


def shutdown_cost_rule(mod, g, tmp):
    """
    Since there is no commitment, there is no concept of shutting down.
    """
    return 0


def startup_fuel_burn_rule(mod, g, tmp):
    """
    Since there is no commitment, there is no concept of starting up.
    """
    return 0


def power_delta_rule(mod, g, tmp):
    """
    Exogenously defined ramp for variable must-take generators.
    """
    if check_if_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ) and check_boundary_type(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g],
        boundary_type="linear"
    ):
        pass
    else:
        return \
            (mod.Capacity_MW[g, mod.period[tmp]]
             * mod.Availability_Derate[g, tmp]
             * mod.gen_var_must_take_cap_factor[g, tmp]) \
            - (mod.Capacity_MW[g, mod.period[mod.prev_tmp[
                    tmp, mod.balancing_type_project[g]]]]
               * mod.Availability_Derate[g, mod.prev_tmp[
                    tmp, mod.balancing_type_project[g]]]
               * mod.gen_var_must_take_cap_factor[g, mod.prev_tmp[
                    tmp, mod.balancing_type_project[g]]])


# Inputs-Outputs
###############################################################################

def load_module_specific_data(mod, data_portal,
                              scenario_directory, subproblem, stage):
    """
    Capacity factors vary by horizon and stage, so get inputs from appropriate
    directory
    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    # Determine list of projects
    projects = list()
    # Also get a list of the projects of the 'gen_var' operational_type,
    # needed for the data check below (to avoid throwing warning unnecessarily)
    var_proj = list()

    prj_op_type_df = pd.read_csv(
        os.path.join(scenario_directory, str(subproblem), str(stage),
                     "inputs", "projects.tab"),
        sep="\t",
        usecols=["project", "operational_type"]
    )

    for row in zip(prj_op_type_df["project"],
                   prj_op_type_df["operational_type"]):
        if row[1] == 'gen_var_must_take':
            projects.append(row[0])
        elif row[1] == 'gen_var':
            var_proj.append(row[0])
        else:
            pass

    # Determine subset of project-timepoints in variable profiles file
    cap_factor = dict()

    prj_tmp_cf_df = pd.read_csv(
        os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                     "variable_generator_profiles.tab"),
        sep="\t",
        usecols=["project", "timepoint", "cap_factor"]
    )
    for row in zip(prj_tmp_cf_df["project"],
                   prj_tmp_cf_df["timepoint"],
                   prj_tmp_cf_df["cap_factor"]):
        if row[0] in projects:
            cap_factor[(row[0], row[1])] = float(row[2])
        # Profile could be for a 'gen_var' project, in which case ignore
        elif row[0] in var_proj:
            pass
        # Throw warning if profile exists for a project not in projects.tab
        # (as 'gen_var' or 'gen_var_must_take')
        else:
            warnings.warn(
                """WARNING: Profiles are specified for '{}' in 
                variable_generator_profiles.tab, but '{}' is not in 
                projects.tab.""".format(
                    row[0], row[0]
                )
            )

    # Load data
    data_portal.data()["gen_var_must_take_cap_factor"] = cap_factor


# Database
###############################################################################

def get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    # Select only profiles of projects in the portfolio
    # Select only profiles of projects with 'gen_var_must_take'
    # operational type
    # Select only profiles for timepoints from the correct timepoint
    # scenario
    # Select only timepoints on periods when the project is operational
    # (periods with existing project capacity for existing projects or
    # with costs specified for new projects)
    variable_profiles = c.execute("""
        SELECT project, timepoint, cap_factor
        FROM (
        -- Select only projects from the relevant portfolio
        SELECT project
        FROM inputs_project_portfolios
        WHERE project_portfolio_scenario_id = {}
        ) as portfolio_tbl
        -- Of the projects in the portfolio, select only those that are in 
        -- this project_operational_chars_scenario_id and have 'gen_var_must_take' as 
        -- their operational_type
        INNER JOIN
        (SELECT project, variable_generator_profile_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        AND operational_type = 'gen_var_must_take'
        ) AS op_char
        USING (project)
        -- Cross join to the timepoints in the relevant 
        -- temporal_scenario_id, subproblem_id, and stage_id
        -- Get the period since we'll need that to get only the operational 
        -- timepoints for a project via an INNER JOIN below
        CROSS JOIN
        (SELECT stage_id, timepoint, period
        FROM inputs_temporal_timepoints
        WHERE temporal_scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {}
        ) as tmps_tbl
        -- Now that we have the relevant projects and timepoints, get the 
        -- respective cap_factor (and no others) from 
        -- inputs_project_variable_generator_profiles through a LEFT OUTER JOIN
        LEFT OUTER JOIN
        inputs_project_variable_generator_profiles
        USING (variable_generator_profile_scenario_id, project, 
        stage_id, timepoint)
        -- We also only want timepoints in periods when the project actually 
        -- exists, so we figure out the operational periods for each of the  
        -- projects below and INNER JOIN to that
        INNER JOIN
            (SELECT project, period
            FROM (
                -- Get the operational periods for each 'existing' and 
                -- 'new' project
                SELECT project, period
                FROM inputs_project_specified_capacity
                WHERE project_specified_capacity_scenario_id = {}
                UNION
                SELECT project, period
                FROM inputs_project_new_cost
                WHERE project_new_cost_scenario_id = {}
                ) as all_operational_project_periods
            -- Only use the periods in temporal_scenario_id via an INNER JOIN
            INNER JOIN (
                SELECT period
                FROM inputs_temporal_periods
                WHERE temporal_scenario_id = {}
                ) as relevant_periods_tbl
            USING (period)
            ) as relevant_op_periods_tbl
        USING (project, period);
        """.format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage,
            subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID,
            subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
            subscenarios.TEMPORAL_SCENARIO_ID
        )
    )

    return variable_profiles


def write_module_specific_model_inputs(
        scenario_directory, subscenarios, subproblem, stage, conn
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
    variable_profiles = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # If variable_generator_profiles.tab file already exists, append rows to it
    if os.path.isfile(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                                   "variable_generator_profiles.tab")
                      ):
        with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                               "variable_generator_profiles.tab"), "a") as \
                variable_profiles_tab_file:
            writer = csv.writer(variable_profiles_tab_file, delimiter="\t", lineterminator="\n")
            for row in variable_profiles:
                writer.writerow(row)
    # If variable_generator_profiles.tab does not exist, write header first,
    # then add profiles data
    else:
        with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                               "variable_generator_profiles.tab"), "w", newline="") as \
                variable_profiles_tab_file:
            writer = csv.writer(variable_profiles_tab_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                ["project", "timepoint", "cap_factor"]
            )
            for row in variable_profiles:
                writer.writerow(row)


# Validation
###############################################################################

def validate_module_specific_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    validation_results = []

    # TODO: validate timepoints: make sure timepoints specified are consistent
    #   with the temporal timepoints (more is okay, less is not)
    # variable_profiles = get_module_specific_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)

    # Get list of gen_var_must_take projects
    c = conn.cursor()
    var_projects = c.execute(
        """SELECT project
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, operational_type
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}) as prj_chars
        USING (project)
        WHERE project_portfolio_scenario_id = {}
        AND operational_type = '{}'""".format(
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            "gen_var_must_take"
        )
    )
    var_projects = [p[0] for p in var_projects.fetchall()]

    # Check that the project does not show up in any of the
    # inputs_project_reserve_bas tables since gen_var_must_take can't
    # provide any reserves
    projects_by_reserve = get_projects_by_reserve(subscenarios, conn)
    for reserve, projects in projects_by_reserve.items():
        project_ba_id = "project_" + reserve + "_ba_scenario_id"
        table = "inputs_project_" + reserve + "_bas"
        validation_errors = check_projects_for_reserves(
            projects_op_type=var_projects,
            projects_w_ba=projects,
            operational_type="gen_var_must_take",
            reserve=reserve
        )
        for error in validation_errors:
            validation_results.append(
                (subscenarios.SCENARIO_ID,
                 subproblem,
                 stage,
                 __name__,
                 project_ba_id.upper(),
                 table,
                 "Mid",
                 "Invalid {} BA inputs".format(reserve),
                 error
                 )
            )

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)
