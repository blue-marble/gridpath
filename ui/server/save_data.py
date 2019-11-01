# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from importlib import import_module
import os.path

from db.common_functions import connect_to_database


def save_plot_data_to_csv(plot_type, directory, filename,
                          db_path, scenario_id, load_zone,
                          carbon_cap_zone, rps_zone,
                          period, horizon, subproblem,
                          stage, project):
    """

    :param plot_type:
    :param load_zone:
    :param carbon_cap_zone:
    :param period:
    :param horizon:
    :param subproblem:
    :param stage:
    :param project:
    :return:
    """
    # Assume 1 for "default" subproblem and stage
    subproblem = 1 if subproblem == "default" else subproblem
    stage = 1 if stage == "default" else subproblem

    # Connect to the database
    conn = connect_to_database(db_path=db_path)

    # Filename and location
    file_location = os.path.join(directory, filename)

    # Import viz module and get the dataframe
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
        df.to_csv(file_location, index=False)
    except ImportError:
        print("ERROR! Visualization module " + plot_type + " not found.")

