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
        temporal_scenario_id,
        scenario_name,
        scenario_description,
        subproblems,
        subproblem_stages,
        periods,
        subproblem_stage_timepoints,
        subproblem_horizons,
        subproblem_stage_timepoint_horizons
):
    """

    :param conn:
    :param temporal_scenario_id:
    :param scenario_name:
    :param scenario_description:
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
    subscenario_data = [
        (temporal_scenario_id, scenario_name, scenario_description)
    ]
    subscenario_sql = """
        INSERT INTO subscenarios_temporal
        (temporal_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subscenario_sql,
                          data=subscenario_data)

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
    :param subscenario_directory:
    :return:
    """
    print(subscenario_directory)
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
    subproblems_set = set(tmp_df["subproblem_id"].to_list())
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
        warnings.warn("Duplicate periods found in periods.csv. Periods must "
                      "be unique.")

    # Check if the set of periods in periods.csv is the same as the set of
    # periods assigned to timepoints in timepoints.csv.
    tmp_periods = set(tmp_df["period"].tolist())
    period_set = set(prd_df["period"].tolist())

    if tmp_periods != period_set:
        warnings.warn("The set of periods in timepoints.csv and periods.csv "
                      "are not the same. Check your data.")

    periods = [
        (subscenario_id, ) + tuple(x) for x in prd_df.to_records(index=False)
    ]

    # HORIZONS
    # Load horizons data into Pandas dataframe
    hrz_df = pd.read_csv(horizons_file, delimiter=",")

    # Check if balancing_type-horizons are unique
    if not hrz_df.set_index(["balancing_type_horizon",
                             "horizon"]).index.is_unique:
        warnings.warn("""Duplicate balancing_type-horizons found in 
        horizons.csv. Horizons must be unique within each balancing type.""")

    # Check if the set of balancing_type-horizons in horizons.csv is the same
    # as the set of balancing_type-horizon assigned to timepoints in
    # timepoints.csv.
    # Get unique balancing types (which we'll use to find the right columns
    # in timepoints.csv)
    balancing_types = hrz_df["balancing_type_horizon"].unique()

    for bt in balancing_types:
        timeponts_csv_column = "horizon_{}".format(bt)
        tmp_horizons = set(tmp_df[timeponts_csv_column].tolist())
        horizon_set = set(
            hrz_df.loc[
                hrz_df["balancing_type_horizon"] == bt,
                "horizon"
            ].tolist()
        )

        if tmp_horizons != horizon_set:
            warnings.warn("""The set of horizons in timepoints.csv and
                          horizons.csv for balancing type {} are not the
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
        i for i in list(tmp_df.columns.values) if i.startswith("horizon")
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
        temporal_scenario_id=subscenario_id,
        scenario_name=subscenario_name,
        scenario_description=subscenario_description,
        subproblems=subproblems,
        subproblem_stages=subproblem_stages,
        periods=periods,
        subproblem_stage_timepoints=subproblem_stage_timepoints,
        subproblem_horizons=subproblem_horizons,
        subproblem_stage_timepoint_horizons=subproblem_stage_timepoint_horizons
    )


# TODO: add argument parser so that this script can be used stand-alone easily
if __name__ == "__main__":
    load_from_csvs(None, "/Users/ana/dev/gridpath_dev/db/csvs_test_examples"
                         "/temporal/1_1horizon_1period")
