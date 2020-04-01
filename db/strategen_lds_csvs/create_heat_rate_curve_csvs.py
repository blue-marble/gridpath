#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

import os
import pandas as pd


def get_projects_w_tech():
    """
    :return: dictionary with projects as keys and their technology as value
    """
    project_tech_df = pd.read_csv(
        "/Users/ana/dev/gridpath_dev/db/strategen_lds_csvs/project"
        "/resolve_project_tech.csv"
    )

    return project_tech_df


def get_hr_by_tech():
    """
    :return: dictionary with heat rate curve parameters by technology

    In RESOLVE, heat rates are by technology.
    """
    hr_by_tech_df = pd.read_csv(
        "/Users/ana/dev/gridpath_dev/db/strategen_lds_csvs/project"
        "/resolve_hr_by_tech.csv"
    )

    hr_by_tech_dict = hr_by_tech_df.set_index("technology").T.to_dict()

    return hr_by_tech_dict


def create_hr_df(hr_params):
    """
    :param hr_params: dictionary of the heat rate parameters
    :return: the heat rate parameters as a pandas dataframe
    """
    # Make dataframe with headers
    hr_df = pd.DataFrame(
        columns=["load_point_fraction", "average_heat_rate_mmbtu_per_mwh"]
    )

    # If this is a must-run plant, we only have one load point
    if hr_params["min_loading"] == 1:
        hr_df.loc[0] = [1, hr_params["avg_hr_max_loading"]]
    # Otherwise, there are two load points, one at min loading and one at
    # max loading
    else:
        hr_df.loc[0] = [
            hr_params["min_loading"],
            hr_params["avg_hr_min_loading"]
        ]
        hr_df.loc[1] = [
            1,
            hr_params["avg_hr_max_loading"]
        ]

    return hr_df


def save_project_hr_to_csv(prj, hr):
    """
    :param prj: the project name
    :param hr: dataframe of the heat rate curve for the project
    :return:
    """
    hr_filename = os.path.join(
        "/Users/ana/dev/gridpath_dev/db/strategen_lds_csvs/project/opchar"
        "/heat_rates", "{}-1-base_hr.csv".format(prj)
    )
    hr.to_csv(hr_filename, index=False)


if __name__ == "__main__":
    # Get the projects with their technologies
    projects_w_tech = get_projects_w_tech()
    # Get the heat rate data by technology
    hr_by_tech = get_hr_by_tech()

    # Iterate over the projects
    for [project, tech] in projects_w_tech.values:
        # If the project technology is one that we have a heat rate for,
        # create the heat rate curve dataframe and save it to a CSV for the
        # project
        if tech in hr_by_tech.keys():
            print(project)
            hr_df = create_hr_df(
                hr_params=hr_by_tech[tech]
            )
            save_project_hr_to_csv(
                prj=project,
                hr=hr_df
            )
        # If there is no heat rate for this project's technology, move on to
        # the next project
        else:
            pass
