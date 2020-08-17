#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This operational type describes must-run generators that produce constant
power equal to their capacity in all timepoints when they are available.

The available capacity can either be a set input (e.g. for the gen_spec
capacity_type) or a decision variable by period (e.g. for the gen_new_lin
capacity_type). This makes this operational type suitable for both production
simulation type problems and capacity expansion problems.

The heat rate is assumed to be constant and this operational type cannot
provide reserves (since there is no operable range, i.e. no headroom or
footroom).

Costs for this operational type include fuel costs and variable O&M costs.

"""

import os
import warnings
from pyomo.environ import Constraint, Set, Param, NonNegativeReals, \
    PositiveReals

from gridpath.auxiliary.auxiliary import generator_subset_init, cursor_to_df
from gridpath.auxiliary.validations import write_validation_to_database, \
    get_projects_by_reserve, validate_idxs, \
    validate_single_input
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables
from gridpath.project.operations.operational_types.common_functions import \
    load_optype_module_specific_data, \
    load_heat_rate_curves, get_heat_rate_curves_inputs_from_database, \
    validate_opchars, validate_heat_rate_curves


def add_module_specific_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`GEN_MUST_RUN`                                                  |
    |                                                                         |
    | The set of generators of the :code:`gen_must_run` operational type.     |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_MUST_RUN_OPR_TMPS`                                         |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_must_run`         |
    | operational type and their operational timepoints.                      |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_MUST_RUN_FUEL_PRJS_PRDS_SGMS`                              |
    |                                                                         |
    | Three-dimensional set describing fuel projects and their heat rate      |
    | curve segment IDs for each operational period. Unless the project's     |
    | heat rate is constant, the heat rate can be defined by multiple         |
    | piecewise linear segments.                                              |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_must_run_fuel`                                             |
    | | *Defined over*: :code:`GEN_MUST_RUN_FUEL_PRJS`                        |
    | | *Within*: :code:`FUELS`                                               |
    |                                                                         |
    | This param describes each fuel project's fuel.                          |
    +-------------------------------------------------------------------------+
    | | :code:`gen_must_run_fuel_burn_slope_mmbtu_per_mwh`                    |
    | | *Defined over*: :code:`GEN_MUST_RUN_FUEL_PRJS_PRDS_SGMS`              |
    | | *Within*: :code:`PositiveReals`                                       |
    |                                                                         |
    | This param describes the slope of the piecewise linear fuel burn for    |
    | each project's heat rate segment in each operational period. The units  |
    | are MMBtu of fuel burn per MWh of electricity generation.               |
    +-------------------------------------------------------------------------+

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_must_run_variable_om_cost_per_mwh`                         |
    | | *Defined over*: :code:`GEN_MUST_RUN`                                  |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The variable operations and maintenance (O&M) cost for each project in  |
    | $ per MWh.                                                              |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`GenMustRun_No_Upward_Reserves_Constraint`                      |
    | | *Defined over*: :code:`GEN_MUST_RUN_OPR_TMPS`                         |
    |                                                                         |
    | Must-run projects cannot provide upward reserves.                       |
    +-------------------------------------------------------------------------+
    | | :code:`GenMustRun_No_Downward_Reserves_Constraint`                    |
    | | *Defined over*: :code:`GEN_MUST_RUN_OPR_TMPS`                         |
    |                                                                         |
    | Must-run projects cannot provide downward reserves.                     |
    +-------------------------------------------------------------------------+


    """

    # Sets
    ###########################################################################

    m.GEN_MUST_RUN = Set(
        within=m.PROJECTS,
        initialize=generator_subset_init("operational_type", "gen_must_run")
    )

    m.GEN_MUST_RUN_OPR_TMPS = Set(
        dimen=2, within=m.PRJ_OPR_TMPS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PRJ_OPR_TMPS
            if g in mod.GEN_MUST_RUN)
    )

    m.GEN_MUST_RUN_FUEL_PRJS_PRDS_SGMS = Set(
        dimen=3
    )

    # Required Params
    ###########################################################################

    m.gen_must_run_fuel_burn_slope_mmbtu_per_mwh = Param(
        m.GEN_MUST_RUN_FUEL_PRJS_PRDS_SGMS,
        within=PositiveReals
    )

    # Optional Params
    ###########################################################################

    m.gen_must_run_variable_om_cost_per_mwh = Param(
        m.GEN_MUST_RUN, within=NonNegativeReals,
        default=0
    )

    # Constraints
    ###########################################################################

    # TODO: remove this constraint once input validation is in place that
    #  does not allow specifying a reserve_zone if 'gen_must_run' type
    def no_upward_reserve_rule(mod, g, tmp):
        """
        **Constraint Name**: GenMustRun_No_Upward_Reserves_Constraint
        **Enforced Over**: GEN_MUST_RUN_OPR_TMPS

        Upward reserves should be zero in every operational timepoint.
        """
        if getattr(d, headroom_variables)[g]:
            warnings.warn(
                """project {} is of the 'gen_must_run' operational type and 
                should not be assigned any upward reserve BAs since it cannot 
                provide upward reserves. Please replace the upward reserve BA 
                for project {} with '.' (no value) in projects.tab. Model will 
                add constraint to ensure project {} cannot provide upward 
                reserves.
                """.format(g, g, g)
            )
            return sum(getattr(mod, c)[g, tmp]
                       for c in getattr(d, headroom_variables)[g]) == 0
        else:
            return Constraint.Skip
    m.GenMustRun_No_Upward_Reserves_Constraint = Constraint(
        m.GEN_MUST_RUN_OPR_TMPS,
        rule=no_upward_reserve_rule
    )

    # TODO: remove this constraint once input validation is in place that
    #  does not allow specifying a reserve_zone if 'gen_must_run' type
    def no_downward_reserve_rule(mod, g, tmp):
        """
        **Constraint Name**: GenMustRun_No_Downward_Reserves_Constraint
        **Enforced Over**: GEN_MUST_RUN_OPR_TMPS

        Downward reserves should be zero in every operational timepoint.
        """
        if getattr(d, footroom_variables)[g]:
            warnings.warn(
                """project {} is of the 'gen_must_run' operational type and 
                should not be assigned any downward reserve BAs since it cannot
                provide upwards reserves. Please replace the downward reserve 
                BA for project {} with '.' (no value) in projects.tab. Model 
                will add constraint to ensure project {} cannot provide 
                downward reserves.
                """.format(g, g, g)
            )
            return sum(getattr(mod, c)[g, tmp]
                       for c in getattr(d, footroom_variables)[g]) == 0
        else:
            return Constraint.Skip
    m.GenMustRun_No_Downward_Reserves_Constraint = Constraint(
        m.GEN_MUST_RUN_OPR_TMPS,
        rule=no_downward_reserve_rule
    )


# Operational Type Methods
###############################################################################

def power_provision_rule(mod, g, tmp):
    """
    Power provision for must run generators is simply their capacity in all
    timepoints when they are operational.
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Since there is no commitment, all capacity is assumed to be online.
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp]


def fuel_burn_rule(mod, g, tmp):
    """
    """
    return mod.gen_must_run_fuel_burn_slope_mmbtu_per_mwh[g, mod.period[
        tmp], 0] \
        * mod.Power_Provision_MW[g, tmp]


def power_delta_rule(mod, g, tmp):
    """
    """
    return 0


# Input-Output
###############################################################################

def load_module_specific_data(mod, data_portal,
                              scenario_directory, subproblem, stage):
    """
    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    # Load data from projects.tab and get the list of projects of this type
    projects = load_optype_module_specific_data(
        mod=mod, data_portal=data_portal,
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage, op_type="gen_must_run"
    )

    # Load data from heat_rate_curves.tab (if it exists)
    load_heat_rate_curves(
        data_portal=data_portal,
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage, op_type="gen_must_run", projects=projects
    )


# Database
###############################################################################

def get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return: cursor object with query results
    """

    heat_rate_curves = get_heat_rate_curves_inputs_from_database(
        subscenarios, subproblem, stage, conn, "gen_must_run"
    )

    return heat_rate_curves


def write_module_specific_model_inputs(
        scenario_directory, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    startup_chars.tab files.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    heat_rate_curves = get_module_specific_inputs_from_database(
            subscenarios, subproblem, stage, conn)

    hr_df = cursor_to_df(heat_rate_curves)
    if not hr_df.empty:
        hr_df = hr_df.fillna(".")
        fpath = os.path.join(scenario_directory, str(subproblem), str(stage),
                             "inputs", "heat_rate_curves.tab")
        if not os.path.isfile(fpath):
            hr_df.to_csv(fpath, index=False, sep="\t")
        else:
            hr_df.to_csv(fpath, index=False, sep="\t", mode="a", header=False)


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

    # Validate operational chars table inputs
    opchar_df = validate_opchars(subscenarios, subproblem, stage, conn,
                                 "gen_must_run")

    # Validate heat rate curves
    validate_heat_rate_curves(subscenarios, subproblem, stage, conn,
                              "gen_must_run")

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
        """.format(subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
                   "gen_must_run",
                   subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
                   )
    )

    # Convert inputs to data frame
    hr_df = cursor_to_df(heat_rates)

    # Check that there is only one load point (constant heat rate)
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_heat_rate_curves",
        severity="Mid",
        errors=validate_single_input(df=hr_df,
                                     msg="gen_must_run can only have one load "
                                         "point (constant heat rate).")
    )

    # Check that the project does not show up in any of the
    # inputs_project_reserve_bas tables since gen_must_run can't provide any
    # reserves
    projects_by_reserve = get_projects_by_reserve(subscenarios, conn)
    for reserve, projects_w_ba in projects_by_reserve.items():
        table = "inputs_project_" + reserve + "_bas"
        reserve_errors = validate_idxs(
            actual_idxs=opchar_df["project"],
            invalid_idxs=projects_w_ba,
            msg="gen_must_run cannot provide {}.".format(reserve)
        )

        write_validation_to_database(
            conn=conn,
            scenario_id=subscenarios.SCENARIO_ID,
            subproblem_id=subproblem,
            stage_id=stage,
            gridpath_module=__name__,
            db_table=table,
            severity="Mid",
            errors=reserve_errors
        )

