#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.project.operations** package contains modules to describe the
operational capabilities, constraints, and costs of generation, storage,
and demand-side infrastructure 'projects' in the optimization problem.
"""

import os.path
import pandas as pd
from pyomo.environ import Set, Param, Any, NonNegativeReals

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.validations import write_validation_to_database, \
    validate_dtypes, get_expected_dtypes, validate_values
from gridpath.project.common_functions import append_to_input_file


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # Variable O&M cost projects (simple)
    m.VAR_OM_COST_PRJS = Set(within=m.PROJECTS)

    m.variable_om_cost_per_mwh = Param(
        m.VAR_OM_COST_PRJS, within=NonNegativeReals
    )

    # Variable O&M cost projects (by loading level)

    # Startup cost projects (simple)
    m.STARTUP_COST_SIMPLE_PRJS = Set(within=m.PROJECTS)

    m.startup_cost_per_mw = Param(
        m.STARTUP_COST_SIMPLE_PRJS, within=NonNegativeReals
    )

    # Startup cost by startup type projects
    m.STARTUP_COST_BY_ST_PRJS_TYPES = Set(dimen=2, ordered=True)
    m.STARTUP_COST_BY_ST_PRJS = Set(
        initialize=lambda mod: set(
            [p for (p, t) in mod.STARTUP_COST_BY_ST_PRJS_TYPES]
        )
    )

    m.startup_cost_by_st_per_mw = Param(
        m.STARTUP_COST_BY_ST_PRJS_TYPES, within=NonNegativeReals
    )

    # All startup cost projects
    m.STARTUP_COST_PRJS = Set(
        within=m.PROJECTS,
        initialize=lambda mod: set(
            [p for p in mod.STARTUP_COST_SIMPLE_PRJS ] +
            [p for p in mod.STARTUP_COST_BY_ST_PRJS]
        )
    )

    # Shutdown cost projects
    m.SHUTDOWN_COST_PRJS = Set(within=m.PROJECTS)

    m.shutdown_cost_per_mw = Param(
        m.SHUTDOWN_COST_PRJS, within=NonNegativeReals
    )

    # Projects that burn fuel
    m.FUEL_PRJS = Set(within=m.PROJECTS)

    m.fuel = Param(m.FUEL_PRJS, within=Any)

    # Fuel projects that incur fuel burn on startup
    m.STARTUP_FUEL_PRJS = Set(within=m.FUEL_PRJS)

    m.startup_fuel_mmbtu_per_mw = Param(
        m.STARTUP_FUEL_PRJS, within=NonNegativeReals
    )


# Input-Output
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    data_portal.load(
        filename=os.path.join(scenario_directory, str(subproblem), str(stage),
                              "inputs", "projects.tab"),
        select=("project", "variable_om_cost_per_mwh", "fuel",
                "startup_fuel_mmbtu_per_mw", "startup_cost_per_mw",
                "shutdown_cost_per_mw"),
        param=(m.variable_om_cost_per_mwh, m.fuel,
               m.startup_fuel_mmbtu_per_mw, m.startup_cost_per_mw,
               m.shutdown_cost_per_mw)
    )

    data_portal.data()['VAR_OM_COST_PRJS'] = {
        None: list(data_portal.data()['variable_om_cost_per_mwh'].keys())
    }

    data_portal.data()['FUEL_PRJS'] = {
        None: list(data_portal.data()['fuel'].keys())
    }

    data_portal.data()['STARTUP_FUEL_PRJS'] = {
        None: list(data_portal.data()['startup_fuel_mmbtu_per_mw'].keys())
    }

    data_portal.data()['STARTUP_COST_SIMPLE_PRJS'] = {
        None: list(data_portal.data()['startup_cost_per_mw'].keys())
    }

    data_portal.data()['SHUTDOWN_COST_PRJS'] = {
        None: list(data_portal.data()['shutdown_cost_per_mw'].keys())
    }

    startup_chars_file = os.path.join(
        scenario_directory, str(subproblem), str(stage),
        "inputs", "startup_chars.tab"
    )

    if os.path.exists(startup_chars_file):
        df = pd.read_csv(startup_chars_file, sep="\t")

        # Note: the rank function requires at least one numeric input in the
        # down_time_cutoff_hours column (can't be all NULL/None).
        if len(df) > 0:
            df["startup_type_id"] = df.groupby("project")[
                "down_time_cutoff_hours"].rank()

        startup_ramp_projects_types = list()
        startup_cost_dict = dict()
        for i, row in df.iterrows():
            project = row["project"]
            startup_type_id = row["startup_type_id"]
            startup_cost = row["startup_cost_per_mw"]

            startup_ramp_projects_types.append((project, startup_type_id))
            startup_cost_dict[(project, startup_type_id)] = \
                float(startup_cost)

        data_portal.data()["STARTUP_COST_BY_ST_PRJS_TYPES"] = \
            {None: startup_ramp_projects_types}
        data_portal.data()["startup_cost_by_st_per_mw"] = startup_cost_dict


# Database
###############################################################################

def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()
    proj_opchar = c.execute("""
        SELECT project, fuel, variable_om_cost_per_mwh,
        min_stable_level_fraction, unit_size_mw,
        startup_cost_per_mw, shutdown_cost_per_mw,
        startup_fuel_mmbtu_per_mw,
        startup_plus_ramp_up_rate,
        shutdown_plus_ramp_down_rate,
        ramp_up_when_on_rate,
        ramp_down_when_on_rate,
        min_up_time_hours, min_down_time_hours,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours, maximum_duration_hours,
        aux_consumption_frac_capacity, aux_consumption_frac_power,
        last_commitment_stage
        -- Get only the subset of projects in the portfolio with their 
        -- capacity types based on the project_portfolio_scenario_id 
        FROM
        (SELECT project, capacity_type
        FROM inputs_project_portfolios
        WHERE project_portfolio_scenario_id = {}) as portfolio_tbl
        LEFT OUTER JOIN
        -- Select the operational characteristics based on the 
        -- project_operational_chars_scenario_id
        inputs_project_operational_chars
        USING (project)
        WHERE project_operational_chars_scenario_id = {}
        ;
        """.format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
        )
    )

    return proj_opchar


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model inputs
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    proj_opchar = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Update the projects.tab file
    new_columns = [
        "fuel", "variable_om_cost_per_mwh",
        "min_stable_level_fraction",
        "unit_size_mw",
        "startup_cost_per_mw", "shutdown_cost_per_mw",
        "startup_fuel_mmbtu_per_mw",
        "startup_plus_ramp_up_rate",
        "shutdown_plus_ramp_down_rate",
        "ramp_up_when_on_rate",
        "ramp_down_when_on_rate",
        "min_up_time_hours", "min_down_time_hours",
        "charging_efficiency", "discharging_efficiency",
        "minimum_duration_hours", "maximum_duration_hours",
        "aux_consumption_frac_capacity", "aux_consumption_frac_power",
        "last_commitment_stage"
    ]
    append_to_input_file(
        inputs_directory=os.path.join(scenario_directory, str(subproblem), str(stage),
                                      "inputs"),
        input_file="projects.tab",
        query_results=proj_opchar,
        index_n_columns=1,
        new_column_names=new_columns
    )


# Validation
###############################################################################

def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Get the project input data
    proj_opchar = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Convert input data into DataFrame
    prj_df = cursor_to_df(proj_opchar)

    # Check data types operational chars:
    expected_dtypes = get_expected_dtypes(
        conn, ["inputs_project_operational_chars"]
    )

    dtype_errors, error_columns = validate_dtypes(prj_df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars",
        severity="High",
        errors=dtype_errors
    )

    # Check valid numeric columns are non-negative
    numeric_columns = [c for c in prj_df.columns
                       if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars",
        severity="High",
        errors=validate_values(prj_df, valid_numeric_columns, min=0)
    )

    # Check min_stable_level_fraction within (0, 1]
    if "min_stable_level_fraction" not in error_columns:
        write_validation_to_database(
            conn=conn,
            scenario_id=subscenarios.SCENARIO_ID,
            subproblem_id=subproblem,
            stage_id=stage,
            gridpath_module=__name__,
            db_table="inputs_project_operational_chars",
            severity="Mid",
            errors=validate_values(prj_df, ["min_stable_level_fraction"],
                                   min=0, max=1, strict_min=True)
        )

