#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

import os
import pandas as pd


def get_chars_as_df():
    all_chars_df = pd.read_csv(
        "/Users/ana/dev/gridpath_dev/db/strategen_lds_csvs/project"
        "/resolve_hydro_chars.csv"
    )

    return all_chars_df


def create_gp_chars(resolve_chars, project):

    # Make dataframe for the GridPath profile with headers
    gp_chars_df = pd.DataFrame(
        columns=["balancing_type", "horizon", "period", "avg", "min", "max"]
    )

    row = 0
    # Make profiles for every year until 2050, for each of the 37 RESOLVE days
    for year in range(2020, 2051):
        print(year)
        for resolve_day in range(1, 38):
            hrzn = year * 10**2 + resolve_day
            gp_chars_df.loc[row] = [
                "day", hrzn, year,
                resolve_chars[
                    (resolve_chars['Day'] == resolve_day)
                    ].iloc[0]["{}_avg".format(project)],
                resolve_chars[
                    (resolve_chars['Day'] == resolve_day)
                ].iloc[0]["{}_min".format(project)],
                resolve_chars[
                    (resolve_chars['Day'] == resolve_day)
                ].iloc[0]["{}_max".format(project)]
            ]
            row += 1

    return gp_chars_df


def save_project_chars_to_csv(prj, chars):
    profile_filename = os.path.join(
        "/Users/ana/dev/gridpath_dev/db/strategen_lds_csvs/project/opchar"
        "/hydro_chars", "{}-1-resolve_chars.csv".format(prj)
    )
    chars.to_csv(profile_filename, index=False)


if __name__ == "__main__":
    chars_df = get_chars_as_df()

    # Get unique list of projects
    projects = set([p[:-4] for p in chars_df if p != "Day"])
    # Iterate over the projects (dataframe columns)
    for project in projects:
        print("Creating chars for project {}".format(project))
        project_resolve_chars_df = chars_df[
            ["Day", "{}_avg".format(project), "{}_min".format(project),
             "{}_max".format(project)]
        ]
        project_gp_chars_df = \
            create_gp_chars(project_resolve_chars_df, project)
        save_project_chars_to_csv(
            prj=project,
            chars=project_gp_chars_df
        )
