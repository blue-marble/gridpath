#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Operations of curtailable conventional hydro generators
"""
from __future__ import print_function

from builtins import next
from builtins import zip
from builtins import str
import csv
import os.path
import pandas as pd
from pyomo.environ import Var, Set, Param, Constraint, \
    Expression, NonNegativeReals, PercentFraction, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import generator_subset_init, \
    setup_results_import
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables


def add_module_specific_components(m, d):
    """
    *hydro_curtailable_ramp_up_rate* \ :sub:`chg`\ -- the project's upward
    ramp rate limit, defined as a fraction of its capacity per minute \n
    *hydro_curtailable_ramp_down_rate* \ :sub:`chg`\ -- the project's downward
    ramp rate limit, defined as a fraction of its capacity per minute \n
    :param m:
    :param d:
    :return:
    """
    # Sets and params
    m.HYDRO_CURTAILABLE_PROJECTS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type", "gen_hydro")
    )

    m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS = Set(dimen=2)

    m.hydro_curtailable_average_power_fraction = \
        Param(m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS,
              within=NonNegativeReals)
    m.hydro_curtailable_min_power_fraction = \
        Param(m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS,
              within=NonNegativeReals)
    m.hydro_curtailable_max_power_fraction = \
        Param(m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS,
              within=NonNegativeReals)

    m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.HYDRO_CURTAILABLE_PROJECTS))

    # Ramp rates can be optionally specified and will default to 1 if not
    # Ramp rate units are "percent of project capacity per minute"
    m.hydro_curtailable_ramp_up_rate = \
        Param(m.HYDRO_CURTAILABLE_PROJECTS, within=PercentFraction, default=1)
    m.hydro_curtailable_ramp_down_rate = \
        Param(m.HYDRO_CURTAILABLE_PROJECTS, within=PercentFraction, default=1)

    # Variables
    m.Hydro_Curtailable_Provide_Power_MW = \
        Var(m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    m.Hydro_Curtailable_Curtail_MW = \
        Var(m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    # Expressions
    def upwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, headroom_variables)[g])
    m.Hydro_Curtailable_Upwards_Reserves_MW = Expression(
        m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=upwards_reserve_rule)

    def downwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, footroom_variables)[g])
    m.Hydro_Curtailable_Downwards_Reserves_MW = Expression(
        m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=downwards_reserve_rule)

    # Operational constraints
    def hydro_energy_budget_rule(mod, g, h):
        """

        :param mod:
        :param g:
        :param h:
        :return:
        """
        return sum((mod.Hydro_Curtailable_Provide_Power_MW[g, tmp] +
                    mod.Hydro_Curtailable_Curtail_MW[g, tmp])
                   * mod.number_of_hours_in_timepoint[tmp]
                   for tmp in mod.TIMEPOINTS_ON_HORIZON[h]) \
            == \
            sum(mod.hydro_curtailable_average_power_fraction[g, h]
                * mod.Capacity_MW[g, mod.period[tmp]]
                * mod.number_of_hours_in_timepoint[tmp]
                for tmp in mod.TIMEPOINTS_ON_HORIZON[h])

    m.Curtailable_Hydro_Energy_Budget_Constraint = \
        Constraint(m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS,
                   rule=hydro_energy_budget_rule)

    def max_power_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Hydro_Curtailable_Provide_Power_MW[g, tmp] \
            + mod.Hydro_Curtailable_Upwards_Reserves_MW[g, tmp] \
            <= mod.hydro_curtailable_max_power_fraction[
                   g, mod.horizon[tmp, mod.balancing_type_project[g]]] \
            * mod.Capacity_MW[g, mod.period[tmp]]

    m.Hydro_Curtailable_Max_Power_Constraint = \
        Constraint(
            m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=max_power_rule
        )

    def min_power_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Hydro_Curtailable_Provide_Power_MW[g, tmp] \
            - mod.Hydro_Curtailable_Downwards_Reserves_MW[g, tmp] \
            >= mod.hydro_curtailable_min_power_fraction[
                   g, mod.horizon[tmp, mod.balancing_type_project[g]]] \
            * mod.Capacity_MW[g, mod.period[tmp]]

    m.Hydro_Curtailable_Min_Power_Constraint = \
        Constraint(
            m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=min_power_rule
        )

    def ramp_up_rule(mod, g, tmp):
        """
        Difference between power generation of consecutive timepoints, adjusted
        for reserve provision in current and previous timepoint, has to obey
        ramp up rate limits.

        We assume that a unit has to reach its setpoint at the start of the
        timepoint; as such, the ramping between 2 timepoints is assumed to
        take place during the duration of the first timepoint, and the
        ramp rate limit is adjusted for the duration of the first timepoint.
        :param mod: 
        :param g: 
        :param tmp: 
        :return: 
        """
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        # If you can ramp up the the total project's capacity within the
        # previous timepoint, skip the constraint (it won't bind)
        elif mod.hydro_curtailable_ramp_up_rate[g] * 60 \
                * mod.number_of_hours_in_timepoint[
                    mod.previous_timepoint[tmp, mod.balancing_type_project[g]]] \
                >= 1:
            return Constraint.Skip
        else:
            return (mod.Hydro_Curtailable_Provide_Power_MW[g, tmp]
                    + mod.Hydro_Curtailable_Curtail_MW[g, tmp]
                    + mod.Hydro_Curtailable_Upwards_Reserves_MW[g, tmp]) \
                - (mod.Hydro_Curtailable_Provide_Power_MW[
                        g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
                   + mod.Hydro_Curtailable_Curtail_MW[
                        g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
                   - mod.Hydro_Curtailable_Downwards_Reserves_MW[
                        g, mod.previous_timepoint[
                            tmp, mod.balancing_type_project[g]]]) \
                <= \
                mod.hydro_curtailable_ramp_up_rate[g] * 60 \
                * mod.number_of_hours_in_timepoint[
                    mod.previous_timepoint[tmp, mod.balancing_type_project[g]]] \
                * mod.Capacity_MW[g, mod.period[tmp]] \
                * mod.Availability_Derate[g, tmp]
    m.Hydro_Curtailable_Ramp_Up_Constraint = \
        Constraint(
            m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=ramp_up_rule
        )

    def ramp_down_rule(mod, g, tmp):
        """
        Difference between power generation of consecutive timepoints, adjusted
        for reserve provision in current and previous timepoint, has to obey
        ramp down rate limits.

        We assume that a unit has to reach its setpoint at the start of the
        timepoint; as such, the ramping between 2 timepoints is assumed to
        take place during the duration of the first timepoint, and the
        ramp rate limit is adjusted for the duration of the first timepoint.
        :param mod: 
        :param g: 
        :param tmp: 
        :return: 
        """
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        # If you can ramp down the the total project's capacity within the
        # previous timepoint, skip the constraint (it won't bind)
        elif mod.hydro_curtailable_ramp_down_rate[g] * 60 \
            * mod.number_of_hours_in_timepoint[
            mod.previous_timepoint[tmp, mod.balancing_type_project[g]]] \
                >= 1:
            return Constraint.Skip
        else:
            return (mod.Hydro_Curtailable_Provide_Power_MW[g, tmp]
                    + mod.Hydro_Curtailable_Curtail_MW[g, tmp]
                    - mod.Hydro_Curtailable_Downwards_Reserves_MW[g, tmp]) \
                - (mod.Hydro_Curtailable_Provide_Power_MW[
                        g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
                   + mod.Hydro_Curtailable_Curtail_MW[
                        g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
                   + mod.Hydro_Curtailable_Upwards_Reserves_MW[
                        g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]) \
                >= \
                - mod.hydro_curtailable_ramp_down_rate[g] * 60 \
                * mod.number_of_hours_in_timepoint[
                    mod.previous_timepoint[tmp, mod.balancing_type_project[g]]] \
                * mod.Capacity_MW[g, mod.period[tmp]] \
                * mod.Availability_Derate[g, tmp]
    m.Hydro_Curtailable_Ramp_Down_Constraint = \
        Constraint(
            m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=ramp_down_rule
        )


def power_provision_rule(mod, g, tmp):
    """
    Power provision from curtailable hydro
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Hydro_Curtailable_Provide_Power_MW[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Since no commitment, all capacity assumed online
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision from curtailable hydro if eligible
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Hydro_Curtailable_Provide_Power_MW[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    This treatment does not allow curtailment
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Hydro_Curtailable_Curtail_MW[g, tmp]


# TODO: ignoring subhourly behavior for hydro for now
def subhourly_curtailment_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def subhourly_energy_delivered_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def fuel_burn_rule(mod, g, tmp, error_message):
    """

    :param mod:
    :param g:
    :param tmp:
    :param error_message:
    :return:
    """
    if g in mod.FUEL_PROJECTS:
        raise ValueError(
            "ERROR! Curtailable hydro projects should not use fuel." + "\n" +
            "Check input data for project '{}'".format(g) + "\n" +
            "and change its fuel to '.' (no value)."
        )
    else:
        raise ValueError(error_message)


def startup_rule(mod, g, tmp):
    """
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise ValueError(
        "ERROR! Hydro generators should not incur startup "
        "costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup/shutdown costs to '.' (no value)."
    )


def shutdown_rule(mod, g, tmp):
    """
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise ValueError(
        "ERROR! Hydro generators should not incur shutdown "
        "costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup/shutdown costs to '.' (no value)."
    )


def power_delta_rule(mod, g, tmp, l):
    """

    :param mod:
    :param g:
    :param tmp:
    :param l:
    :return:
    """
    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        pass
    else:
        return (mod.Hydro_Curtailable_Provide_Power_MW[g, tmp] +
                mod.Hydro_Curtailable_Curtail_MW[g, tmp]) - \
               (mod.Hydro_Curtailable_Provide_Power_MW[
                    g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]
                ]
                + mod.Hydro_Curtailable_Curtail_MW[
                    g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]
                ])


def load_module_specific_data(m, data_portal,
                              scenario_directory, subproblem, stage):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    # Determine list of projects
    projects = list()

    prj_op_type_df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t",
        usecols=["project", "operational_type"]
    )

    for row in zip(prj_op_type_df["project"],
                   prj_op_type_df["operational_type"]):
        if row[1] == 'gen_hydro':
            projects.append(row[0])
        else:
            pass

    # Determine subset of project-horizons in hydro budgets file
    project_horizons = list()
    avg = dict()
    min = dict()
    max = dict()

    prj_hor_opchar_df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage, "inputs",
                     "hydro_conventional_horizon_params.tab"),
        sep="\t",
        usecols=["project", "horizon", "hydro_average_power_fraction",
                 "hydro_min_power_fraction", "hydro_max_power_fraction"]
    )
    for row in zip(prj_hor_opchar_df["project"],
                   prj_hor_opchar_df["horizon"],
                   prj_hor_opchar_df["hydro_average_power_fraction"],
                   prj_hor_opchar_df["hydro_min_power_fraction"],
                   prj_hor_opchar_df["hydro_max_power_fraction"]):
        if row[0] in projects:
            project_horizons.append((row[0], row[1]))
            avg[(row[0], row[1])] = float(row[2])
            min[(row[0], row[1])] = float(row[3])
            max[(row[0], row[1])] = float(row[4])
        else:
            pass

    # Load data
    data_portal.data()[
        "HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS"
    ] = {
        None: project_horizons
    }
    data_portal.data()["hydro_curtailable_average_power_fraction"] = avg
    data_portal.data()["hydro_curtailable_min_power_fraction"] = min
    data_portal.data()["hydro_curtailable_max_power_fraction"] = max

    # Ramp rate limits are optional; will default to 1 if not specified
    ramp_up_rate = dict()
    ramp_down_rate = dict()
    header = pd.read_csv(os.path.join(scenario_directory, subproblem, stage, "inputs",
                                      "projects.tab"),
                         sep="\t", header=None, nrows=1).values[0]

    optional_columns = ["ramp_up_when_on_rate",
                        "ramp_down_when_on_rate"]
    used_columns = [c for c in optional_columns if c in header]

    dynamic_components = \
        pd.read_csv(
            os.path.join(scenario_directory, subproblem, stage, "inputs", "projects.tab"),
            sep="\t",
            usecols=["project", "operational_type"] + used_columns
            )

    if "ramp_up_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_up_when_on_rate"]
                       ):
            if row[1] == "gen_hydro" and row[2] != ".":
                ramp_up_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "hydro_curtailable_ramp_up_rate"] = \
            ramp_up_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_down_when_on_rate"]
                       ):
            if row[1] == "gen_hydro" and row[2] != ".":
                ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "hydro_curtailable_ramp_down_rate"] = \
            ramp_down_rate


def export_module_specific_results(mod, d,
                                   scenario_directory, subproblem, stage):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param mod:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "dispatch_gen_hydro.csv"),
              "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "balancing_type_project", "horizon",
                         "timepoint", "timepoint_weight",
                         "number_of_hours_in_timepoint",
                         "technology", "load_zone",
                         "power_mw", "scheduled_curtailment_mw"
                         ])

        for (p, tmp) in mod.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                mod.period[tmp],
                mod.balancing_type_project[p],
                mod.horizon[tmp, mod.balancing_type_project[p]],
                tmp,
                mod.timepoint_weight[tmp],
                mod.number_of_hours_in_timepoint[tmp],
                mod.technology[p],
                mod.load_zone[p],
                value(mod.Hydro_Curtailable_Provide_Power_MW[p, tmp]),
                value(mod.Hydro_Curtailable_Curtail_MW[p, tmp])
            ])


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
    # Select only budgets/min/max of projects in the portfolio
    # Select only budgets/min/max of projects with 'gen_hydro'
    # Select only budgets/min/max for horizons from the correct temporal
    # scenario and subproblem
    # Select only horizons on periods when the project is operational
    # (periods with existing project capacity for existing projects or
    # with costs specified for new projects)
    # TODO: should we ensure that the project balancing type and the horizon
    #  length type match (e.g. by joining on them being equal here)
    hydro_chars = c.execute(
        """SELECT project, horizon, average_power_fraction, min_power_fraction,
        max_power_fraction
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, hydro_operational_chars_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        AND operational_type = 'gen_hydro') AS op_char
        USING (project)
        CROSS JOIN
        (SELECT horizon
        FROM inputs_temporal_horizons
        WHERE temporal_scenario_id = {}
        AND subproblem_id = {})
        LEFT OUTER JOIN
        inputs_project_hydro_operational_chars
        USING (hydro_operational_chars_scenario_id, project, horizon)
        INNER JOIN
        (SELECT project, period
        FROM
        (SELECT project, period
        FROM inputs_project_existing_capacity
        INNER JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {})
        USING (period)
        WHERE project_existing_capacity_scenario_id = {}
        AND existing_capacity_mw > 0) as existing
        UNION
        SELECT project, period
        FROM inputs_project_new_cost
        INNER JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {})
        USING (period)
        WHERE project_new_cost_scenario_id = {})
        USING (project, period)
        WHERE project_portfolio_scenario_id = {}
        """.format(
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_EXISTING_CAPACITY_SCENARIO_ID,
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    return hydro_chars


def validate_module_specific_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # hydro_chars = get_module_specific_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)

    # do stuff here to validate inputs


def write_module_specific_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    hydro_conventional_horizon_params.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    hydro_chars = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # If hydro_conventional_horizon_params.tab file already exists,
    # append rows to it
    if os.path.isfile(os.path.join(inputs_directory,
                                   "hydro_conventional_horizon_params.tab")
                      ):
        with open(os.path.join(inputs_directory,
                               "hydro_conventional_horizon_params.tab"),
                  "a") as \
                hydro_chars_tab_file:
            writer = csv.writer(hydro_chars_tab_file, delimiter="\t")
            for row in hydro_chars:
                writer.writerow(row)
    # If hydro_conventional_horizon_params.tab does not exist, write header
    # first, then add inputs data
    else:
        with open(os.path.join(inputs_directory,
                               "hydro_conventional_horizon_params.tab"),
                  "w", newline="") as \
                hydro_chars_tab_file:
            writer = csv.writer(hydro_chars_tab_file, delimiter="\t")

            # Write header
            writer.writerow(
                ["project", "horizon",
                 "hydro_average_power_fraction",
                 "hydro_min_power_fraction",
                 "hydro_max_power_fraction"]
            )
            for row in hydro_chars:
                writer.writerow(row)


def import_module_specific_results_to_database(
        scenario_id, subproblem, stage, c, db, results_directory
):
    """

    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c: 
    :param db: 
    :param results_directory: 
    :return: 
    """
    print("project dispatch hydro curtailable")
    # dispatch_gen_hydro.csv
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="project_dispatch_gen_hydro",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "dispatch_gen_hydro.csv"),
              "r") as h_dispatch_file:
        reader = csv.reader(h_dispatch_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            balancing_type_project = row[2]
            horizon = row[3]
            timepoint = row[4]
            timepoint_weight = row[5]
            number_of_hours_in_timepoint = row[6]
            load_zone = row[8]
            technology = row[7]
            power_mw = row[9]
            scheduled_curtailment_mw = row[10]
            
            results.append(
                (scenario_id, project, period, subproblem, stage,
                 balancing_type_project, horizon, timepoint, timepoint_weight,
                 number_of_hours_in_timepoint,
                 load_zone, technology, power_mw, scheduled_curtailment_mw)
            )
    insert_temp_sql = """
        INSERT INTO
        temp_results_project_dispatch_gen_hydro{}
            (scenario_id, project, period, subproblem_id, stage_id, 
            balancing_type_project, horizon, timepoint,
            timepoint_weight, number_of_hours_in_timepoint, 
            load_zone, technology, power_mw, scheduled_curtailment_mw)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_dispatch_gen_hydro
        (scenario_id, project, period, subproblem_id, stage_id, 
        balancing_type_project, horizon, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint,
        load_zone, technology, power_mw, scheduled_curtailment_mw)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        balancing_type_project, horizon, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint,
        load_zone, technology, power_mw, scheduled_curtailment_mw
        FROM temp_results_project_dispatch_gen_hydro{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)


def process_module_specific_results(db, c, subscenarios):
    """
    Aggregate scheduled curtailment
    :param db:
    :param c:
    :param subscenarios:
    :return:
    """

    print("aggregate hydro curtailment")

    # Delete old aggregated hydro curtailment results
    del_sql = """
        DELETE FROM results_project_curtailment_hydro 
        WHERE scenario_id = ?
        """
    spin_on_database_lock(conn=db, cursor=c, sql=del_sql,
                          data=(subscenarios.SCENARIO_ID,),
                          many=False)

    # Aggregate hydro curtailment (just scheduled curtailment)
    agg_sql = """
        INSERT INTO results_project_curtailment_hydro
        (scenario_id, subproblem_id, stage_id, period, horizon, timepoint, 
        timepoint_weight, number_of_hours_in_timepoint, month, hour_of_day,
        load_zone, scheduled_curtailment_mw)
        SELECT
        scenario_id, subproblem_id, stage_id, period, horizon, timepoint, 
        timepoint_weight, number_of_hours_in_timepoint, month, hour_of_day,
        load_zone, scheduled_curtailment_mw
        FROM (
            SELECT scenario_id, subproblem_id, stage_id, period, horizon, 
            timepoint, timepoint_weight, number_of_hours_in_timepoint, 
            load_zone, 
            sum(scheduled_curtailment_mw) AS scheduled_curtailment_mw
            FROM results_project_dispatch_gen_hydro
            GROUP BY subproblem_id, stage_id, timepoint, load_zone
        ) as agg_curtailment_tbl
        JOIN (
            SELECT subproblem_id, period, timepoint, month, hour_of_day
            FROM inputs_temporal_timepoints
            WHERE temporal_scenario_id = (
                SELECT temporal_scenario_id 
                FROM scenarios
                WHERE scenario_id = ?
                )
        ) as tmp_info_tbl
        USING (subproblem_id, period, timepoint)
        WHERE scenario_id = ?
        ORDER BY subproblem_id, stage_id, load_zone, timepoint;
        """
    spin_on_database_lock(conn=db, cursor=c, sql=agg_sql,
                          data=(subscenarios.SCENARIO_ID,
                                subscenarios.SCENARIO_ID),
                          many=False)
