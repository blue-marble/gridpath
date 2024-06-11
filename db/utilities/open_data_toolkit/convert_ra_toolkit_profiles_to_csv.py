# Copyright 2016-2024 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pandas as pd


# TODO: this needs to be run after getting the data from PUDL, but before
#  loading raw data into the database. Leaving as a task for now to figure out
#   where this intermediary steps should fit in case there are similar ones.

# TODO: NEVP, PGE, SRP, and WAUW have wind plants in EIA, but we don't have
#  wind profiles for them in the RA toolkit; I have added those profiles
#  manually for now

def main():
    df = pd.read_parquet(
        "/Users/ana/dev/gridpath_v2024.1.0+dev/db/csvs_open_data/raw_data"
        "/ra_toolkit_gen_profiles.parquet",
        engine="fastparquet",
    )

    df["datetime_pst"] = df["datetime_utc"] - pd.Timedelta(hours=8)
    df["year"] = pd.DatetimeIndex(df["datetime_pst"]).year
    df["month"] = pd.DatetimeIndex(df["datetime_pst"]).month
    df["day_of_month"] = pd.DatetimeIndex(df["datetime_pst"]).day
    df["hour_of_day"] = pd.DatetimeIndex(df["datetime_pst"]).hour

    df = df.rename(
        columns={"aggregation_group": "unit", "capacity_factor": "cap_factor"})
    cols = df.columns.tolist()
    cols = cols[4:8] + cols[1:3]
    df = df[cols]

    df.to_csv("/Users/ana/dev/gridpath_v2024.1.0+dev/db/csvs_open_data/raw_data"
              "/var_profiles.csv", sep=",", index=False)


if __name__ == "__main__":
    main()
