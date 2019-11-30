# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Functions to save data from the UI to CSVs.
"""

from importlib import import_module

from db.common_functions import connect_to_database


def save_plot_data_to_csv(db_path, download_path, scenario_id, plot_type,
                          load_zone, carbon_cap_zone, rps_zone,
                          period, horizon, subproblem, stage, project):
    """
    :param db_path: string, the path to the database
    :param download_path: string, the CSV file path
    :param scenario_id: integer, the scenario_id
    :param plot_type: string, which plot
    :param load_zone: string, load zone parameter for the plot
    :param carbon_cap_zone: string, carbon cap zone parameter for the plot
    :param rps_zone: string, RPS zone parameter for the plot
    :param period: integer, period parameter for the plot
    :param horizon: integer, horizon parameter for the plot
    :param subproblem: integer, subproblem parameter for the plot
    :param stage: integer, stage parameter for the plot
    :param project: string, project parameter for the plot
    :return:

    Save plot data to CSV.
    """
    # Assume 1 for "default" subproblem and stage
    subproblem = 1 if subproblem == "default" else subproblem
    stage = 1 if stage == "default" else subproblem

    # Connect to the database
    conn = connect_to_database(db_path=db_path)

    # Import viz module, get the dataframe, and export it to CSV
    try:
        imp_m = \
            import_module(
              "." + plot_type,
              package="viz"
            )
        df = imp_m.get_plotting_data(
            conn=conn,
            scenario_id=scenario_id,
            load_zone=load_zone,
            carbon_cap_zone=carbon_cap_zone,
            rps_zone=rps_zone,
            period=period,
            horizon=horizon,
            subproblem=subproblem,
            stage=stage,
            project=project,
        )
        df.to_csv(download_path, index=False)
    except ImportError:
        print("ERROR! Visualization module " + plot_type + " not found.")

