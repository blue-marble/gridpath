#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Operations of noncurtailable conventional hydro generators
"""

from builtins import zip
import csv
import os.path
import pandas as pd
from pyomo.environ import Var, Set, Param, Constraint, \
    Expression, NonNegativeReals, PercentFraction, value

from gridpath.auxiliary.auxiliary import generator_subset_init
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables


def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    Here, we define the set of non-curtailable hydro projects:
    *HYDRO_NONCURTAILABLE_PROJECTS*
    (:math:`NCHG`, index :math:`nchg`) and use this set to get the subset of
    *PROJECT_OPERATIONAL_TIMEPOINTS* with :math:`g \in NCHG` -- the
    *HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS* (:math:`NCHG\_OT`).

    We also need the *HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_HORIZONS* set
    (:math:`NCHG\_OH`) over which we will define hydro's main operational
    parameters including:
    *hydro_noncurtailable_average_power_mwa* \ :sub:`nchg, oh`\ -- the
    average power on a given horizon *oh* (multiply by the timepoint number of
    hours represented and sum across all timepoints on the horizon to get
    the horizon energy budget) \n
    *hydro_noncurtailable_min_power_mw* \ :sub:`nchg, oh`\ -- the minimum
    power output on each timepoint on horizon *oh* \n
    *hydro_noncurtailable_max_power_mw* \ :sub:`nchg, oh`\ -- the maximum
    power output on each timepoint on horizon *oh* \n
    *hydro_noncurtailable_ramp_up_rate* \ :sub:`nchg`\ -- the project's upward
    ramp rate limit, defined as a fraction of its capacity per minute \n
    *hydro_noncurtailable_ramp_down_rate* \ :sub:`nchg`\ -- the project's
    downward ramp rate limit, defined as a fraction of its capacity per minute\n

    The power provision variable for non-curtailable hydro projects,
    *Hydro_Noncurtailable_Provide_Power_MW*, is defined over
    *HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS*.

    The main constraints on non-curtailable-hydro project power provision
    are as follows:

    For :math:`(nchg, oh) \in CCG\_OH`: \n

    :math:`\sum_{{tmp}\in T_h}{Hydro\_Noncurtailable\_Provide\_Power\_MW_{
    nchg, tmp}} \\times number\_of\_hours\_in\_timepoint_{tmp} = \sum_{{
    tmp}\in T_h}{hydro\_noncurtailable\_average\_power\_mwa_{
    nchg, tmp}} \\times number\_of\_hours\_in\_timepoint_{tmp}`

    For :math:`(nchg, tmp) \in NCHG\_OT`: \n
    :math:`Hydro\_Noncurtailable\_Provide\_Power\_MW_{nchg, tmp} \geq
    hydro\_noncurtailable\_min\_power\_mwa_{nchg, tmp}`
    :math:`Hydro\_Noncurtailable\_Provide\_Power\_MW_{nchg, tmp} \leq
    hydro\_noncurtailable\_max\_power\_mwa_{nchg, tmp}`

    Hydro ramps can be constrained: documentation to be added.

    """
    # Sets and params
    m.HYDRO_NONCURTAILABLE_PROJECTS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type",
                              "hydro_noncurtailable")
    )

    m.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_HORIZONS = \
        Set(dimen=2)

    m.hydro_noncurtailable_average_power_mwa = \
        Param(m.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_HORIZONS,
              within=NonNegativeReals)
    m.hydro_noncurtailable_min_power_mw = \
        Param(m.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_HORIZONS,
              within=NonNegativeReals)
    m.hydro_noncurtailable_max_power_mw = \
        Param(m.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_HORIZONS,
              within=NonNegativeReals)

    # TODO: hydro operational horizon validation:
    #  we  should probably get the operational timepoints from the
    #  operational horizons and validate that they are within the
    #  operational timepoints we would get by looking at the project's
    #  capacity module; or, alternatively, validate that the operational
    #  horizons loaded above match the operational timepoints we get via the
    #  capacity module
    m.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.HYDRO_NONCURTAILABLE_PROJECTS))

    # Ramp rates can be optionally specified and will default to 1 if not
    # Ramp rate units are "percent of project capacity per minute"
    m.hydro_noncurtailable_ramp_up_rate = \
        Param(m.HYDRO_NONCURTAILABLE_PROJECTS, within=PercentFraction,
              default=1)
    m.hydro_noncurtailable_ramp_down_rate = \
        Param(m.HYDRO_NONCURTAILABLE_PROJECTS, within=PercentFraction,
              default=1)

    # Variables
    m.Hydro_Noncurtailable_Provide_Power_MW = \
        Var(m.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    # Expressions
    def upwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, headroom_variables)[g])
    m.Hydro_Noncurtailable_Upwards_Reserves_MW = Expression(
        m.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=upwards_reserve_rule)

    def downwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, footroom_variables)[g])
    m.Hydro_Noncurtailable_Downwards_Reserves_MW = Expression(
        m.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=downwards_reserve_rule)


    # Operational constraints
    def hydro_energy_budget_rule(mod, g, h):
        """

        :param mod:
        :param g:
        :param h:
        :return:
        """
        return sum(mod.Hydro_Noncurtailable_Provide_Power_MW[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   for tmp in mod.TIMEPOINTS_ON_HORIZON[h]) \
            == \
            sum(mod.hydro_noncurtailable_average_power_mwa[g, h]
                * mod.number_of_hours_in_timepoint[tmp]
                for tmp in mod.TIMEPOINTS_ON_HORIZON[h])

    m.Noncurtailable_Hydro_Energy_Budget_Constraint = \
        Constraint(m.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_HORIZONS,
                   rule=hydro_energy_budget_rule)

    def max_power_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Hydro_Noncurtailable_Provide_Power_MW[g, tmp] \
            + mod.Hydro_Noncurtailable_Upwards_Reserves_MW[g, tmp] \
            <= mod.hydro_noncurtailable_max_power_mw[g, mod.horizon[tmp]]
    m.Hydro_Noncurtailable_Max_Power_Constraint = \
        Constraint(
            m.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=max_power_rule
        )

    def min_power_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Hydro_Noncurtailable_Provide_Power_MW[g, tmp]\
            - mod.Hydro_Noncurtailable_Downwards_Reserves_MW[g, tmp] \
            >= mod.hydro_noncurtailable_min_power_mw[g, mod.horizon[tmp]]
    m.Hydro_Noncurtailable_Min_Power_Constraint = \
        Constraint(
            m.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
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
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        # If you can ramp up the the total project's capacity within the
        # previous timepoint, skip the constraint (it won't bind)
        elif mod.hydro_noncurtailable_ramp_up_rate[g] * 60 \
             * mod.number_of_hours_in_timepoint[mod.previous_timepoint[tmp]] \
             >= 1:
            return Constraint.Skip
        else:
            return (mod.Hydro_Noncurtailable_Provide_Power_MW[g, tmp]
                    + mod.Hydro_Noncurtailable_Upwards_Reserves_MW[g, tmp]) \
                - (mod.Hydro_Noncurtailable_Provide_Power_MW[
                        g, mod.previous_timepoint[tmp]]
                   - mod.Hydro_Noncurtailable_Downwards_Reserves_MW[
                        g, mod.previous_timepoint[tmp]]) \
                <= \
                mod.hydro_noncurtailable_ramp_up_rate[g] * 60 \
                * mod.number_of_hours_in_timepoint[
                       mod.previous_timepoint[tmp]] \
                * mod.Capacity_MW[g, mod.period[tmp]] \
                * mod.availability_derate[g, mod.horizon[tmp]]
    m.Hydro_Noncurtailable_Ramp_Up_Constraint = \
        Constraint(
            m.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
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
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        # If you can ramp down the the total project's capacity within the
        # previous timepoint, skip the constraint (it won't bind)
        elif mod.hydro_noncurtailable_ramp_down_rate[g] * 60 \
             * mod.number_of_hours_in_timepoint[mod.previous_timepoint[tmp]] \
             >= 1:
            return Constraint.Skip
        else:
            return (mod.Hydro_Noncurtailable_Provide_Power_MW[g, tmp]
                    - mod.Hydro_Noncurtailable_Downwards_Reserves_MW[g, tmp]) \
                - (mod.Hydro_Noncurtailable_Provide_Power_MW[
                        g, mod.previous_timepoint[tmp]]
                   + mod.Hydro_Noncurtailable_Upwards_Reserves_MW[
                        g, mod.previous_timepoint[tmp]]) \
                >= \
                - mod.hydro_noncurtailable_ramp_down_rate[g] * 60 \
                * mod.number_of_hours_in_timepoint[
                    mod.previous_timepoint[tmp]] \
                * mod.Capacity_MW[g, mod.period[tmp]] \
                * mod.availability_derate[g, mod.horizon[tmp]]
    m.Hydro_Noncurtailable_Ramp_Down_Constraint = \
        Constraint(
            m.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=ramp_down_rule
        )


def power_provision_rule(mod, g, tmp):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param tmp: the operational timepoint
    :return: expression for power provision by non-curtailable hydropower
     generators

    Power provision for non-curtailable hydro generators is a variable
    constrained to be between the minimum and maximum level on each horizon,
    and to average to a pre-specified number on each horizon.
    """
    return mod.Hydro_Noncurtailable_Provide_Power_MW[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Since no commitment, all capacity assumed online
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.availability_derate[g, mod.horizon[tmp]]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision from noncurtailable hydro if eligible
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Hydro_Noncurtailable_Provide_Power_MW[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    This treatment does not allow curtailment
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


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
            "ERROR! Noncurtailable hydro projects should not use fuel." + "\n" +
            "Check input data for project '{}'".format(g) + "\n" +
            "and change its fuel to '.' (no value)."
        )
    else:
        raise ValueError(error_message)


def startup_shutdown_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise ValueError(
        "ERROR! Hydro generators should not incur startup/shutdown costs." +
        "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup/shutdown costs to '.' (no value)."
    )


def power_delta_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
            and mod.boundary[mod.horizon[tmp]] == "linear":
        pass
    else:
        return mod.Hydro_Noncurtailable_Provide_Power_MW[g, tmp] - \
               mod.Hydro_Noncurtailable_Provide_Power_MW[
                   g, mod.previous_timepoint[tmp]
               ]


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
        if row[1] == 'hydro_noncurtailable':
            projects.append(row[0])
        else:
            pass

    # Determine subset of project-timepoints in variable profiles file
    project_horizons = list()
    mwa = dict()
    min_mw = dict()
    max_mw = dict()

    prj_tmp_cf_df = \
        pd.read_csv(
            os.path.join(scenario_directory, subproblem, stage, "inputs",
                         "hydro_conventional_horizon_params.tab"),
            sep="\t", usecols=[
                "project", "horizon",
                "hydro_average_power_mwa",
                "hydro_min_power_mw",
                "hydro_max_power_mw"
            ]
        )
    for row in zip(prj_tmp_cf_df["project"],
                   prj_tmp_cf_df["horizon"],
                   prj_tmp_cf_df["hydro_average_power_mwa"],
                   prj_tmp_cf_df["hydro_min_power_mw"],
                   prj_tmp_cf_df["hydro_max_power_mw"]):
        if row[0] in projects:
            project_horizons.append((row[0], row[1]))
            mwa[(row[0], row[1])] = float(row[2])
            min_mw[(row[0], row[1])] = float(row[3])
            max_mw[(row[0], row[1])] = float(row[4])
        else:
            pass

    # Load data
    data_portal.data()[
        "HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_HORIZONS"
    ] = {
        None: project_horizons
    }
    data_portal.data()["hydro_noncurtailable_average_power_mwa"] = mwa
    data_portal.data()["hydro_noncurtailable_min_power_mw"] = min_mw
    data_portal.data()["hydro_noncurtailable_max_power_mw"] = max_mw

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
            if row[1] == "hydro_noncurtailable" and row[2] != ".":
                ramp_up_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "hydro_noncurtailable_ramp_up_rate"] = \
            ramp_up_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_down_when_on_rate"]
                       ):
            if row[1] == "hydro_noncurtailable" and row[2] != ".":
                ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "hydro_noncurtailable_ramp_down_rate"] = \
            ramp_down_rate


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
    # Select only budgets/min/max of projects with 'hydro_curtailable'
    # Select only budgets/min/max for horizons from the correct temporal
    # scenario and subproblem
    # Select only horizons on periods when the project is operational
    # (periods with existing project capacity for existing projects or
    # with costs specified for new projects)
    hydro_chars = c.execute(
        """SELECT project, horizon, average_power_mwa, min_power_mw,
        max_power_mw
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, hydro_operational_chars_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        AND operational_type = 'hydro_noncurtailable') AS op_char
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
                 "hydro_average_power_mwa",
                 "hydro_min_power_mw",
                 "hydro_max_power_mw"]
            )
            for row in hydro_chars:
                writer.writerow(row)





