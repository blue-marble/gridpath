#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

import os
import pandas as pd


def get_profiles_as_df():
    all_profiles_df = pd.read_csv(
        "/db/strategen_lds_csvs/project/resolve_var_profiles.csv"
    )

    return all_profiles_df


def create_gp_profile(resolve_profile, project):

    # # Create index for faster processing
    # resolve_profile.set_index(["Day", "Hour"])

    # Make dataframe for the GridPath profile with headers
    gp_profile_df = pd.DataFrame(
        columns=["stage_id", "timepoint", "cap_factor"]
    )

    row = 0
    # Make profiles for every year until 2050, for each of the 37 RESOLVE days
    for year in range(2020, 2051):
        print(year)
        for resolve_day in range(1, 38):
            for hour in range(1, 25):
                tmp = year * 10**4 + resolve_day * 10**2 + hour
                gp_profile_df.loc[row] = [
                    1, tmp,
                    resolve_profile[
                        (resolve_profile['Day'] == resolve_day) &
                        (resolve_profile['Hour'] == hour)
                        ].iloc[0][project]
                ]
                row += 1

    return gp_profile_df


def save_project_profile_to_csv(prj, profile):
    profile_filename = os.path.join(
        "/db/strategen_lds_csvs/project/opchar/var_profiles", "{}-1-resolve_profile.csv".format(prj)
    )
    profile.to_csv(profile_filename, index=False)


if __name__ == "__main__":
    profiles_df = get_profiles_as_df()

    # Iterate over the projects (dataframe columns)
    for header in profiles_df:
        if header in ["Day", "Hour", "Day_Weight"]:
            pass
        else:
            project = header
            print("Creating profile for project {}".format(project))
            project_resolve_profile_df = profiles_df[["Day", "Hour", project]]
            project_gp_profile_df = \
                create_gp_profile(project_resolve_profile_df, project)
            save_project_profile_to_csv(
                prj=project,
                profile=project_gp_profile_df
            )
