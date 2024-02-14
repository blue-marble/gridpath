# -*- coding: utf-8 -*-
"""
Copyright 2023 Moment Energy Insights LLC.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

"""
Processes unserved energy results from GridPath simulation and prints loss of load metrics and other information

To call in command line:
python process_results.py [subscenario_name]


"""


import sys
import os
import csv
import numpy as np
import pandas as pd


def calculate_timepoint(
    weather_mode, iteration, hour_of_year, hydro_year=0, weather_year=0
):

    if weather_mode == "MonteCarlo":
        timepoint = str(iteration) + str(hour_of_year).zfill(4)
    elif weather_mode == "Synchronized":
        timepoint = (
            str(iteration)
            + str(hydro_year)
            + str(weather_year)
            + str(hour_of_year).zfill(4)
        )

    return timepoint


# case_name = sys.argv[1]

case_name = "GP_RA_recode_Test4"

use_thresh = 1.0


with open("settings/scenario_settings.csv") as csvfile:
    file_reader = csv.reader(csvfile)
    cases = file_reader.__next__()
    if case_name not in cases:
        print("Error - scenario not listed in scenario_settings.csv")
    else:
        case_ind = cases.index(case_name)
        study_year = int(file_reader.__next__()[case_ind])
        weather_mode = file_reader.__next__()[case_ind]
        opt_window = int(file_reader.__next__()[case_ind])
        subproblem_balancing_type = file_reader.__next__()[case_ind]
        hydro_balancing_window = int(file_reader.__next__()[case_ind])
        iterations = int(file_reader.__next__()[case_ind])
        loads_file = file_reader.__next__()[case_ind]
        units_file = file_reader.__next__()[case_ind]
        timeseries_file = file_reader.__next__()[case_ind]
        common_files = file_reader.__next__()[case_ind]
N_subp_per_year = int(np.floor(365 / opt_window))
sim_days_per_year = N_subp_per_year * opt_window


# read in draw information
print("Importing draw information...")
draw_data = pd.read_csv(
    os.path.join("Simulations", case_name + "_log", "draw_data.csv")
)

if weather_mode == "MonteCarlo":

    # Import weather bin information
    print("Importing weather bin information...")
    weather_bins = pd.read_csv(os.path.join("bins", "weather_bins.csv"))

    hydro_years = [0]
    weather_years = [0]


elif weather_mode == "Synchronized":

    print("importing hydro and weather years in simulation...")

    hydro_years = []
    with open("settings/sync_hydro_years.csv") as csvfile:
        csvreader = csv.reader(csvfile)
        csvreader.__next__()
        for row in csvreader:
            if row[0] == case_name:
                for col in range(1, len(row)):
                    if row[col] != "":
                        hydro_years.append(row[col])
    hydro_years = np.array(hydro_years, dtype=int)

    weather_years = []
    with open("settings/sync_weather_years.csv") as csvfile:
        csvreader = csv.reader(csvfile)
        csvreader.__next__()
        for row in csvreader:
            if row[0] == case_name:
                for col in range(1, len(row)):
                    if row[col] != "":
                        weather_years.append(row[col])
    weather_years = np.array(weather_years, dtype=int)

N_years = iterations * len(hydro_years) * len(weather_years)

# calculate weights to align statistics with the number of days per month in the study year
weight = np.zeros(12)
days_in_study_year = (
    np.datetime64(str(study_year + 1) + "-01-01")
    - np.datetime64(str(study_year) + "-01-01")
) / np.timedelta64(1, "D")
for month in range(1, 13):
    if month < 12:
        studyyear_days_per_month = (
            np.datetime64(str(study_year) + "-" + str(month + 1).zfill(2) + "-01")
            - np.datetime64(str(study_year) + "-" + str(month).zfill(2) + "-01")
        ) / np.timedelta64(1, "D")
    else:
        studyyear_days_per_month = 31
    if weather_mode == "MonteCarlo":
        sim_days_per_month = draw_data[draw_data["month"] == month].index.size / N_years
    elif weather_mode == "Synchronized":
        sim_days_per_month = draw_data[
            draw_data["weather month"] == month
        ].index.size / (len(hydro_years) * len(weather_years))
    weight[month - 1] = studyyear_days_per_month / sim_days_per_month


# import GridPath unserved energy results
use = pd.DataFrame(0, index=[], columns=[])
year_count = 0
for i in range(iterations):
    # if weather mode is Synchronized, loop through hydro and weather years for each iteration
    for j in range(len(hydro_years)):
        for k in range(len(weather_years)):
            year_count += 1
            for subp_of_year in range(N_subp_per_year):

                subp = N_subp_per_year * (year_count - 1) + subp_of_year + 1

                if os.path.exists(
                    os.path.join(
                        "Simulations",
                        case_name,
                        str(subp),
                        "results",
                        "load_balance.csv",
                    )
                ):
                    load_balance = pd.read_csv(
                        os.path.join(
                            "Simulations",
                            case_name,
                            str(subp),
                            "results",
                            "load_balance.csv",
                        )
                    )
                    subp_use = load_balance.pivot(
                        index="timepoint", columns="zone", values="unserved_energy_mw"
                    )
                    # NOTE - SHOULD NOT NEED TO RE-SORT, AS LONG AS THE TIMEPOINT DEFINITION IS UNCHANGED AND THE SUBPROBLEM IS 1 YEAR OR SHORTER

                    # calculate total unserved energy for each timepoint
                    subp_use["total_unserved_energy"] = np.sum(subp_use, axis=1)

                    # only keep timepoints with non-negligible unserved energy
                    subp_use = subp_use[subp_use["total_unserved_energy"] > use_thresh]

                    if subp_use.index.size > 0:

                        # log information about the timepoints
                        subp_timepoints = np.array(subp_use.index, dtype=float)
                        hour_of_year = np.mod(subp_timepoints, 10000)
                        day_of_subp = (
                            np.floor(
                                (subp_timepoints - np.min(subp_timepoints)) / 24
                            ).astype(int)
                            + 1
                        )
                        subp_use["subproblem"] = subp
                        subp_use["simulation_day"] = (
                            subp - 1
                        ) * opt_window + day_of_subp
                        subp_use["iteration"] = i + 1
                        subp_use["HE"] = np.mod(hour_of_year - 1, 24) + 1

                        if weather_mode == "MonteCarlo":
                            timestamp = np.datetime64(str(study_year) + "-01-01") + (
                                hour_of_year - 1
                            ) * np.timedelta64(1, "h")
                            month = (
                                timestamp.astype("datetime64[M]").astype(int) % 12 + 1
                            )
                            subp_use["month"] = month
                            subp_use["hydro_year"] = draw_data.loc[
                                (draw_data["subproblem"] == subp), "hydro year"
                            ].to_numpy()[0]
                            subp_use["simulation_year"] = year_count
                            subp_use["weight"] = weight[month - 1]

                        elif weather_mode == "Synchronized":
                            timestamp = np.datetime64(
                                str(weather_years[k]) + "-01-01"
                            ) + (hour_of_year - 1) * np.timedelta64(1, "h")
                            month = (
                                timestamp.astype("datetime64[M]").astype(int) % 12 + 1
                            )
                            subp_use["weather_year"] = weather_years[k]
                            subp_use["weather_date"] = timestamp.astype("datetime64[D]")
                            subp_use["month"] = month
                            subp_use["hydro_year"] = hydro_years[j]
                            subp_use["simulation_year"] = year_count
                            subp_use["weight"] = weight[month - 1]

                        # append subproblem use to use DataFrame
                        use = pd.concat([use, subp_use])


print("Printing loss of load information...")

if os.path.isdir(os.path.join("Results", case_name)) == False:
    os.makedirs(os.path.join("Results", case_name))

# print loss of load hours information
use.to_csv(os.path.join(os.path.join("Results", case_name, "loss_of_load_hours.csv")))

# calculate and print loss of load day information
day_list = list(np.unique(use["simulation_day"]))
if weather_mode == "MonteCarlo":
    cols = [
        "iteration",
        "subproblem",
        "simulation_day",
        "simulation_year",
        "hydro_year",
        "month",
        "weight",
    ]
elif weather_mode == "Synchronized":
    cols = [
        "iteration",
        "subproblem",
        "simulation_day",
        "simulation_year",
        "hydro_year",
        "weather_date",
        "weather_year",
        "month",
        "weight",
    ]
use_day = pd.DataFrame(0, index=day_list, columns=cols)
for sim_day in day_list:

    # pull the day's information for the loss of load day
    use_day_tmp = use[use["simulation_day"] == sim_day]
    use_day.loc[sim_day, cols] = use_day_tmp.loc[use_day_tmp.index[0], cols]

    use_day.loc[sim_day, "max_unserved_energy_mw"] = np.max(
        use_day_tmp["total_unserved_energy"]
    )
    use_day.loc[sim_day, "total_unserved_energy_mwh"] = np.sum(
        use_day_tmp["total_unserved_energy"]
    )
    use_day.loc[sim_day, "duration_hrs"] = np.sum(
        use_day_tmp["total_unserved_energy"] > 0
    )

use_day.to_csv(
    os.path.join(os.path.join("Results", case_name, "loss_of_load_days.csv")),
    index=False,
)


print("Calculating loss of load metrics...")

# annual metrics
LOLH = np.sum(use["weight"]) / N_years
EUE = np.sum(use["total_unserved_energy"] * use["weight"]) / N_years
LOLE = np.sum(use_day["weight"]) / N_years
LOLP_year = len(np.unique(use["simulation_year"])) / N_years

with open(
    os.path.join("Results", case_name, "summary_metrics.csv"), "w", newline=""
) as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(["case", case_name])
    csvwriter.writerow(["LOLH (hrs/yr)", LOLH])
    csvwriter.writerow(["EUE (MWh/yr)", EUE])
    csvwriter.writerow(["LOLE (days/yr)", LOLE])
    csvwriter.writerow(["LOLP_year (% of years)", LOLP_year])


# month-hour heat maps
LOLH_mo_hr = pd.DataFrame(0, index=np.arange(24) + 1, columns=np.arange(12) + 1)
EUE_mo_hr = pd.DataFrame(0, index=np.arange(24) + 1, columns=np.arange(12) + 1)
for month in range(1, 13):
    for HE in range(1, 25):
        mask = (use["month"] == month) & (use["HE"] == HE)
        LOLH_mo_hr.loc[HE, month] = np.sum(use.loc[mask, "weight"]) / N_years
        EUE_mo_hr.loc[HE, month] = (
            np.sum(use.loc[mask, "total_unserved_energy"] * use.loc[mask, "weight"])
            / N_years
        )
LOLH_mo_hr.to_csv(
    os.path.join(os.path.join("Results", case_name, "month_hour_LOLH.csv"))
)
EUE_mo_hr.to_csv(os.path.join(os.path.join("Results", case_name, "month_hour_EUE.csv")))

# hydro/weather-year heat maps
if weather_mode == "Synchronized":

    LOLH_hydroweather = pd.DataFrame(0, index=hydro_years, columns=weather_years)
    EUE_hydroweather = pd.DataFrame(0, index=hydro_years, columns=weather_years)
    LOLE_hydroweather = pd.DataFrame(0, index=hydro_years, columns=weather_years)
    LOLP_year_hydroweather = pd.DataFrame(0, index=hydro_years, columns=weather_years)
    for hydro_year in hydro_years:
        for weather_year in weather_years:

            hourly_mask = (use["hydro_year"] == hydro_year) * (
                use["weather_year"] == weather_year
            )
            daily_mask = (use_day["hydro_year"] == hydro_year) * (
                use_day["weather_year"] == weather_year
            )

            LOLH_hydroweather.loc[hydro_year, weather_year] = (
                np.sum(use.loc[hourly_mask, "weight"]) / iterations
            )
            EUE_hydroweather.loc[hydro_year, weather_year] = (
                np.sum(
                    use.loc[hourly_mask, "total_unserved_energy"]
                    * use.loc[hourly_mask, "weight"]
                )
                / iterations
            )
            LOLE_hydroweather.loc[hydro_year, weather_year] = (
                np.sum(use_day.loc[daily_mask, "weight"]) / iterations
            )
            LOLP_year_hydroweather.loc[hydro_year, weather_year] = (
                len(np.unique(use.loc[hourly_mask, "simulation_year"])) / iterations
            )
    LOLH_hydroweather.to_csv(
        os.path.join(os.path.join("Results", case_name, "hydro_weather_LOLH.csv"))
    )
    EUE_hydroweather.to_csv(
        os.path.join(os.path.join("Results", case_name, "hydro_weather_EUE.csv"))
    )
    LOLE_hydroweather.to_csv(
        os.path.join(os.path.join("Results", case_name, "hydro_weather_LOLE.csv"))
    )
    LOLP_year_hydroweather.to_csv(
        os.path.join(os.path.join("Results", case_name, "hydro_weather_LOLP.csv"))
    )


print("Calculating convergence metrics...")
convergence = pd.DataFrame(
    0,
    index=np.arange(iterations) + 1,
    columns=[
        "LOLH (hrs/yr)",
        "EUE (MWh/yr)",
        "LOLE (days/yr)",
        "LOLP_year (% of years)",
    ],
)
for i in range(iterations):

    N_years_tmp = (i + 1) * len(hydro_years) * len(weather_years)
    hourly_mask = use["iteration"] <= i + 1
    daily_mask = use_day["iteration"] <= i + 1

    convergence.loc[i + 1, "LOLH (hrs/yr)"] = (
        np.sum(use.loc[hourly_mask, "weight"]) / N_years_tmp
    )
    convergence.loc[i + 1, "EUE (MWh/yr)"] = (
        np.sum(
            use.loc[hourly_mask, "total_unserved_energy"]
            * use.loc[hourly_mask, "weight"]
        )
        / N_years_tmp
    )
    convergence.loc[i + 1, "LOLE (days/yr)"] = (
        np.sum(use_day.loc[daily_mask, "weight"]) / N_years_tmp
    )
    convergence.loc[i + 1, "LOLP_year (% of years)"] = (
        len(np.unique(use.loc[hourly_mask, "simulation_year"])) / N_years_tmp
    )
convergence.to_csv(os.path.join(os.path.join("Results", case_name, "convergence.csv")))

print("Complete.")
