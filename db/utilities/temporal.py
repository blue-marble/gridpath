#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make temporal subscenarios.
"""

from copy import deepcopy
import os.path
import pandas as pd
import warnings

from db.common_functions import spin_on_database_lock


def insert_into_database(
        conn,
        subscenario_data,
        subproblems,
        subproblem_stages,
        periods,
        subproblem_stage_timepoints,
        subproblem_horizons,
        subproblem_stage_timepoint_horizons
):
    """

    :param conn:
    :param subscenario_data: tuple, (temporal_scenario_id, scenario_name,
        scenario_description)
    :param subproblems: list of tuples (subscenario_id,
        subproblem_id)
    :param subproblem_stages: list of tuples (subscenario_id,
        subproblem_id, stage_id)
    :param periods:
    :param subproblem_horizons: list of tuples
    :param subproblem_stage_timepoints: list of tuples
    :param subproblem_stage_timepoint_horizons: list of tuples
    """

    c = conn.cursor()

    # Create subscenario
    subscenario_sql = """
        INSERT INTO subscenarios_temporal
        (temporal_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subscenario_sql,
                          data=subscenario_data, many=False)

    # Subproblems
    subproblems_sql = """
        INSERT INTO inputs_temporal_subproblems
        (temporal_scenario_id, subproblem_id)
        VALUES (?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subproblems_sql,
                          data=subproblems)

    # Stages
    # TODO: stage_name not currently included; decide whether to keep this
    #  column in the database and how to import data for it if we do want it
    stages_sql = """
        INSERT INTO inputs_temporal_subproblems_stages
        (temporal_scenario_id, subproblem_id, stage_id)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=stages_sql,
                          data=subproblem_stages)

    # Periods
    periods_sql = """
        INSERT INTO inputs_temporal_periods
        (temporal_scenario_id, period, discount_factor, 
        number_years_represented)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=periods_sql,
                          data=periods)

    # Horizons
    # TODO: what to do with the period column
    horizons_sql = """
        INSERT INTO inputs_temporal_horizons
        (temporal_scenario_id, subproblem_id, balancing_type_horizon, horizon, 
        boundary)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=horizons_sql,
                          data=subproblem_horizons)

    # Timepoints
    timepoints_sql = """
        INSERT INTO inputs_temporal_timepoints
        (temporal_scenario_id, subproblem_id, stage_id, timepoint,
        period, number_of_hours_in_timepoint, timepoint_weight, 
        previous_stage_timepoint_map, 
        spinup_or_lookahead, month, hour_of_day)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
    
    spin_on_database_lock(conn=conn, cursor=c, sql=timepoints_sql,
                          data=subproblem_stage_timepoints)

    # TIMEPOINT HORIZONS
    horizon_timepoints_sql = """
        INSERT INTO inputs_temporal_horizon_timepoints
        (temporal_scenario_id, subproblem_id, stage_id, timepoint, 
        balancing_type_horizon, horizon)
        VALUES (?, ?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=horizon_timepoints_sql,
                          data=subproblem_stage_timepoint_horizons)


def load_from_csvs(conn, subscenario_directory):
    """
    :param conn:
    :param subscenario_directory: string, path to the directory containing
        the data for this temporal_scenario_id

    Load temporal subscenario data into the database. The data structure for
    loading  temporal data from CSVs is as follows:

    Each temporal subscenario is a directory, with the scenario ID,
    underscore, and the scenario name as the name of the directory (already
    passed here), so we get this to import from the subscenario_directory path.

    Within each subscenario directory there are four required files:
    description.txt, structure.csv, period_params.csv, and horizon_params.csv.

    1. *description.txt*: contains the description of the subscenario.

    2. *structure.csv*: contains all timepoint-level information for the
    temporal subscenario, including
    subproblem_id, stage_id, timepoint, period, number_of_hours_in_timepoint,
    timepoint_weight, previous_stage_timepoint_map, spinup_or_lookahead,
    month, hour_of_day. Columns must be specified in this order. The horizon
    information for each timepoint must be included as the ending columns of
    this file and must conform to the following structure: the header must
    start with `horizon_` and then include the balancing type, e.g. day
    balancing types will be `horizon_day`. The temporal script will populate
    the subscenarios, stages, timepoints, and horizon_timepoints tables based
    on the information in structure.csv.

    3. *horizon_params.csv*: contains the balancing_type-horizon-level
    information for the temporal subscenario, including subproblem_id,
    balancing_type_horizon, horizon, boundary (must be in this order).
    
    4. *period_params.csv*: contains the period-level information for the
    temporal subscenario, including period, discount_factor,
    number_years_represented (must be in this order).
    """

    # Required input files
    description_file = os.path.join(subscenario_directory, "description.txt")
    timepoints_file = os.path.join(subscenario_directory, "structure.csv")
    periods_file = os.path.join(subscenario_directory, "period_params.csv")
    horizons_file = os.path.join(subscenario_directory, "horizon_params.csv")

    # Get subscenario ID, name, and description
    # The subscenario directory must start with an integer for the
    # subscenario_id followed by "_" and then the subscenario name
    # The subscenario description must be in the description.txt file under
    # the subscenario directory
    directory_basename = os.path.basename(subscenario_directory)
    subscenario_id = int(directory_basename.split("_")[0])
    subscenario_name = directory_basename.split("_")[1]
    with open(description_file, "r") as f:
        subscenario_description = f.read()

    # Load timepoints data into Pandas dataframe
    # The subproblem, stage, and horizon information is also contained here
    tmp_df = pd.read_csv(timepoints_file, delimiter=",")

    # SUBPROBLEMS
    # Get the data for the inputs_temporal_subproblems table from the
    # timepoints CSV
    subproblems_set = set(tmp_df["subproblem_id"])
    subproblems = [(subscenario_id, x) for x in subproblems_set]

    # STAGES
    # Get the data for the inputs_temporal_subproblems_stages table from the
    # timepoints CSV
    subproblem_stages_set = \
        set(zip(tmp_df["subproblem_id"], tmp_df["stage_id"]))
    subproblem_stages = [(subscenario_id, ) + x for x in subproblem_stages_set]

    # PERIODS
    # Load periods data into Pandas dataframe
    prd_df = pd.read_csv(periods_file, delimiter=",")

    # Check if the periods are unique
    if prd_df["period"].duplicated().any():
        warnings.warn("Duplicate periods found in period_params.csv. Periods "
                      "must be unique.")

    # Check if the set of periods in period_params.csv is the same as the set of
    # periods assigned to timepoints in structure.csv.
    tmp_periods = set(tmp_df["period"])
    period_set = set(prd_df["period"])

    if tmp_periods != period_set:
        warnings.warn("The set of periods in structure.csv and "
                      "period_params.csv are not the same. Check your data.")

    periods = [
        (subscenario_id, ) + tuple(x) for x in prd_df.to_records(index=False)
    ]

    # HORIZONS
    # Load horizons data into Pandas dataframe
    hrz_df = pd.read_csv(horizons_file, delimiter=",")

    # Check if balancing_type-horizons are unique
    if hrz_df.duplicated(["balancing_type_horizon", "horizon"]).any():
        warnings.warn("""Duplicate balancing_type-horizons found in 
        horizon_params.csv. Horizons must be unique within each balancing 
        type.""")

    # Check if the set of balancing_type-horizons in horizon_params.csv is the same
    # as the set of balancing_type-horizon assigned to timepoints in
    # structure.csv.
    # Get unique balancing types (which we'll use to find the right columns
    # in structure.csv)
    balancing_types = hrz_df["balancing_type_horizon"].unique()

    for bt in balancing_types:
        timepoints_csv_column = "horizon_{}".format(bt)
        tmp_horizons = set(tmp_df[timepoints_csv_column])
        horizon_set = set(
            hrz_df.loc[
                hrz_df["balancing_type_horizon"] == bt,
                "horizon"
            ]
        )

        if tmp_horizons != horizon_set:
            warnings.warn("""The set of horizons in structure.csv and
                          horizon_params.csv for balancing type {} are not the
                          same. Check your data.""".format(bt))

    subproblem_horizons = [
        (subscenario_id,) + tuple(x) for x in hrz_df.to_records(index=False)
    ]

    # TIMEPOINTS
    timepoints_tmp_df = tmp_df[
        ["subproblem_id", "stage_id", "timepoint", "period",
         "number_of_hours_in_timepoint", "timepoint_weight",
         "previous_stage_timepoint_map", "spinup_or_lookahead", "month",
         "hour_of_day"]
    ]
    subproblem_stage_timepoints = [
        (subscenario_id,) + tuple(x)
        for x in timepoints_tmp_df.to_records(index=False)
    ]

    # TIMEPOINT HORIZONS
    horizon_columns = [
        i for i in tmp_df.columns if i.startswith("horizon")
    ]

    hrz_tmp_dfs_list = list()
    for hrz_col in horizon_columns:
        balancing_type = hrz_col.replace("horizon_", "")
        # Must make bt_df a deepcopy of tmp_df to avoid this error
        # https://stackoverflow.com/questions/44723183/set-value-to-an-entire-column-of-a-pandas-dataframe
        bt_df = deepcopy(tmp_df[
            ["subproblem_id", "stage_id", "timepoint", hrz_col]
        ])
        # Create a balancing_type_horizon column and set it to the current
        # balancing type
        bt_df["balancing_type_horizon"] = balancing_type
        # Rename the horizon_balancing-type column of the dataframe
        bt_df.rename(columns={hrz_col: "horizon"}, inplace=True)
        # Change the order of the balancing_type_horizon and horizon columns
        bt_df = bt_df[["subproblem_id", "stage_id", "timepoint",
                      "balancing_type_horizon", "horizon"]]
        # Append to the list of DFs we'll concatenate
        hrz_tmp_dfs_list.append(bt_df)

    hrz_tmp_df = pd.concat(hrz_tmp_dfs_list)

    # Get the list of tuples to insert into the database
    subproblem_stage_timepoint_horizons = [
        (subscenario_id,) + tuple(x)
        for x in hrz_tmp_df.to_records(index=False)
    ]

    # INSERT INTO THE DATABASE
    insert_into_database(
        conn=conn,
        subscenario_data=(subscenario_id, subscenario_name,
                          subscenario_description),
        subproblems=subproblems,
        subproblem_stages=subproblem_stages,
        periods=periods,
        subproblem_stage_timepoints=subproblem_stage_timepoints,
        subproblem_horizons=subproblem_horizons,
        subproblem_stage_timepoint_horizons=subproblem_stage_timepoint_horizons
    )
