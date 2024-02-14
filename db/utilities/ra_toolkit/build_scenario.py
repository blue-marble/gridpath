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
Generates the  GridPath input data for a scenario using Monte Carlo Simulation or Weather-Synchronized Simulation

To call in command line:
python build_scenario.py [scenario_name] [# of threads]
                                          
Notes:
settings must be populated for [scenario_name] in scenario_settings.csv
files and directories listed in scenario_settings.csv for [scenario_name] must be populated

"""

import numpy as np
import csv
import os
import datetime
import glob
import shutil
import pandas as pd


class Project:
    def __init__(self, name, operational_type):
        self.name = name
        self.operational_type = operational_type
        self.unit_list = []

        # initialize variables to store the total mw from the associated units
        if operational_type == "gen_var_stor_hyb":
            self.total_var_mw = 0
            self.total_stor_mw = 0
        else:
            self.total_mw = 0

        # store the input file names and headers for GridPath
        if operational_type == "gen_var" or operational_type == "gen_var_must_take":
            self.input_filenames = ["variable_generator_profiles"]
            self.input_headers = [["project", "timepoint", "cap_factor"]]

        elif operational_type == "gen_var_stor_hyb":
            self.input_filenames = [
                "variable_generator_profiles",
                "project_availability_exogenous",
            ]
            self.input_headers = [
                ["project", "timepoint", "cap_factor"],
                [
                    "project",
                    "timepoint",
                    "availability_derate",
                    "hyb_stor_cap_availability_derate",
                ],
            ]

        elif operational_type == "gen_hydro_must_take":
            self.input_filenames = ["hydro_conventional_horizon_params"]
            self.input_headers = [
                [
                    "project",
                    "horizon",
                    "average_power_fraction",
                    "min_power_fraction",
                    "max_power_fraction",
                ]
            ]

        else:
            self.input_filenames = ["project_availability_exogenous"]
            self.input_headers = [
                [
                    "project",
                    "timepoint",
                    "availability_derate",
                    "hyb_stor_cap_availability_derate",
                ]
            ]


class Unit:
    def __init__(
        self,
        unit_name,
        project_name,
        unit_type,
        unit_mw,
        unit_timeseries,
        N_units,
        unitModel,
        unitFOR,
        unitMTTR,
        gentieModel,
        gentieFOR,
        gentieMTTR,
    ):

        self.name = unit_name
        self.project = project_name
        self.unit_type = unit_type
        self.mw = unit_mw
        self.timeseries = unit_timeseries
        self.units = int(N_units)
        self.unitModel = unitModel
        self.unitFOR = unitFOR
        self.unitMTTR = unitMTTR
        self.gentieModel = gentieModel
        self.gentieFOR = gentieFOR
        self.gentieMTTR = gentieMTTR

        self.unit_avail_last = []
        self.gentie_avail_last = []


class Load_Zone:
    def __init__(self, name):

        self.name = name
        self.load_list = []

        self.input_filename = "load_mw"
        self.input_header = ["load_zone", "timepoint", "load_mw"]


class Load:
    def __init__(self, load_name, load_zone, load_timeseries, scalar):

        self.name = load_name
        self.load_zone = load_zone
        self.timeseries = load_timeseries
        self.scalar = scalar


class Timeseries:
    def __init__(self, name, stat):
        self.name = name
        self.stat = stat

        # timestamps for the data in the timeseries
        self.header = []
        self.timestamps = []

        # bin assignments for the data in the timeseries
        self.hydro_bins = []
        self.met_bins = []
        self.daytype_bins = []

        # indices for the timeseries data corresponding to each draw
        self.draw_indices = []


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


def write_temporal_files(
    subp,
    subp_of_year,
    case_name,
    weather_mode,
    opt_window,
    hydro_balancing_window,
    subproblem_balancing_type,
    study_year,
    subp_per_year,
    iteration,
    hydro_year=0,
    weather_year=0,
):

    # print periods file
    with open(
        os.path.join("Simulations", case_name, str(subp), "inputs", "periods.tab"),
        "w",
        newline="",
    ) as csvfile:
        csvwriter = csv.writer(csvfile, delimiter="\t")
        csvwriter.writerow(
            [
                "period",
                "discount_factor",
                "period_start_year",
                "period_end_year",
                "hours_in_period_timepoints",
            ]
        )
        csvwriter.writerow(
            [
                study_year,
                "1",
                study_year,
                study_year + 1,
                opt_window * subp_per_year * 24.0,
            ]
        )

    # print horizons file
    with open(
        os.path.join("Simulations", case_name, str(subp), "inputs", "horizons.tab"),
        "w",
        newline="",
    ) as csvfile:
        csvwriter = csv.writer(csvfile, delimiter="\t")
        csvwriter.writerow(["horizon", "balancing_type_horizon", "boundary"])

        # print the horizon information for the full optimization window
        if subproblem_balancing_type == "linked" and subp_of_year == 1:
            csvwriter.writerow([1, "subproblem", "linear"])
        else:
            csvwriter.writerow([1, "subproblem", subproblem_balancing_type])

        # write horizon information for hydro constraints
        # NOTE - OPTIMIZATION WINDOW MUST BE MULTIPLES OF HYDRO BALANCING WINDOWS (e.g. N weeks, if hydro balancing is 1 week)
        N_hydro_horizons = int(opt_window / hydro_balancing_window)
        for i in range(N_hydro_horizons):
            csvwriter.writerow([1 + i, "hydro", "circular"])

    # initialize horizon_timepoints file
    horizon_timepoints_file = open(
        os.path.join(
            "Simulations", case_name, str(subp), "inputs", "horizon_timepoints.tab"
        ),
        "w",
        newline="",
    )
    horizon_timepoints_writer = csv.writer(horizon_timepoints_file, delimiter="\t")
    header = ["horizon", "balancing_type_horizon", "timepoint"]
    horizon_timepoints_writer.writerow(header)

    # initialize timepoints file
    timepoint_file = open(
        os.path.join("Simulations", case_name, str(subp), "inputs", "timepoints.tab"),
        "w",
        newline="",
    )
    timepoint_writer = csv.writer(timepoint_file, delimiter="\t")
    header = [
        "timepoint",
        "period",
        "timepoint_weight",
        "number_of_hours_in_timepoint",
        "previous_stage_timepoint_map",
        "month",
    ]
    timepoint_writer.writerow(header)

    # loop through timepoints
    for t in range(opt_window * 24):

        hour_of_year = (subp_of_year - 1) * opt_window * 24 + t + 1
        timepoint = calculate_timepoint(
            weather_mode, iteration, hour_of_year, hydro_year, weather_year
        )

        if weather_mode == "MonteCarlo":
            month = (
                (
                    np.datetime64(str(study_year) + "-01-01")
                    + np.timedelta64(hour_of_year - 1, "h")
                )
                .astype(object)
                .month
            )
        elif weather_mode == "Synchronized":
            month = (
                (
                    np.datetime64(str(weather_year) + "-01-01")
                    + np.timedelta64(hour_of_year - 1, "h")
                )
                .astype(object)
                .month
            )

        # write the timepoint to file
        timepoint_writer.writerow([timepoint, study_year, "1.0", "1", ".", month])

        # write the timepoint corresponding to the subproblem horizon to file
        horizon_timepoints_writer.writerow([1, "subproblem", timepoint])

        # write the timepoint corresponding to the hydro horizon
        # NOTE - OPTIMIZATION WINDOW MUST BE MULTIPLES OF HYDRO BALANCING WINDOWS (e.g. N weeks, if hydro balancing is 1 week)
        hydro_horizon = int(np.ceil((t + 1) / 24 / hydro_balancing_window))
        horizon_timepoints_writer.writerow([hydro_horizon, "hydro", timepoint])

    timepoint_file.close()
    horizon_timepoints_file.close()


def simulate_outages(outage_model, FOR, MTTR, N_units, dt, starting_outage_states=[]):

    if outage_model == "Derate":
        availability = 1 - np.outer(FOR, np.ones(N_units))

    elif outage_model == "MC_independent":
        # randomly draw whether each unit is out using a uniform distribution
        availability = 1.0 - (
            np.random.rand(len(FOR), N_units) < np.outer(FOR, np.ones(N_units))
        )

    elif outage_model == "MC_sequential":

        # initialize with starting outage states, if they are provided. Otherwise initialize with randomly selected outages
        if np.size(starting_outage_states) == 0:
            avail_last = 1.0 - (
                np.random.rand(1, N_units) < np.outer(FOR[0], np.ones(N_units))
            )
        else:
            avail_last = starting_outage_states

        # calculate mean time to failure
        MTTF = float(MTTR) * (1 / FOR - 1)

        # randomly draw whether each unit fails or is repaired in each time step using an exponential model
        availability = np.zeros([len(FOR), N_units])

        for t in range(len(FOR)):
            avail_tmp = (avail_last == 1) * (
                1.0 - (np.random.exponential(MTTF[t], N_units) < dt)
            ) + (avail_last == 0) * (np.random.exponential(float(MTTR), N_units) < dt)
            availability[t, :] = avail_tmp
            avail_last = avail_tmp

    else:
        availability = np.ones([len(FOR), N_units])

    return availability


def write_load_inputs(
    load_zone,
    case_name,
    study_year,
    loads,
    load_names,
    timeseries,
    timeseries_names,
    weather_mode,
    iterations,
    opt_window,
    load_no,
):

    print("  ..." + load_zone.name + "...")

    # pull the timeseries data for each load in the zone
    timeseries_data = []
    for load_name in load_zone.load_list:

        # find the load object
        load_ind = load_names.index(load_name)
        load = loads[load_ind]

        # identify the corresponding timeseries
        ts_ind = timeseries_names.index(load.timeseries)
        ts = timeseries[ts_ind]

        # add the timeseries data for the load to the dataframe
        timeseries_data.append(
            pd.read_csv(os.path.join("timeseries_data", ts.name, load.name + ".csv"))
        )

    # loop through iterations
    draw_day = 0
    subp = 0
    for i in range(iterations):

        # if using Synchronized weather mode, reset the draw_day counter and iterate through hydro and weather years for each iteration
        if weather_mode == "Synchronized":
            draw_day = 0
        for j in range(len(hydro_years)):
            for k in range(len(weather_years)):

                # loop through the subproblems for the year
                for subp_of_year in range(N_subp_per_year):

                    subp += 1

                    # create a temporary file to store the GridPath availability files for the subproblem and project
                    # NOTE: temporary files are used to support parallelization, so that multiple projects can be written to the same subproblem at the same time
                    load_zone_temp_file = open(
                        os.path.join(
                            "Simulations",
                            case_name,
                            str(subp),
                            "inputs",
                            load_zone.input_filename,
                            load_zone.name + ".csv",
                        ),
                        "w",
                        newline="",
                    )
                    load_zone_writer = csv.writer(load_zone_temp_file)
                    load_zone_writer.writerow(load_zone.input_header)

                    # loop through the days for each subproblem
                    for d in range(opt_window):

                        # initialize the input data for the day
                        load_mw = np.zeros(24)

                        # loop through the loads in the load zone
                        for l in range(len(load_zone.load_list)):

                            # find the unit object
                            load_ind = load_names.index(load_zone.load_list[l])
                            load = loads[load_ind]

                            # pull the timeseries indices for the day
                            ts_ind = timeseries_names.index(load.timeseries)
                            ts = timeseries[ts_ind]
                            ts_indices = ts.draw_indices[draw_day]

                            # pull the timeseries data for the day
                            day_timeseries_data = timeseries_data[l].loc[ts_indices, :]

                            # incorporate the load into the load zone load
                            load_mw += day_timeseries_data["load_mw"].to_numpy(
                                dtype=float
                            )

                        # print load data to the subproblem temporary file
                        for t in range(24):
                            hour_of_year = (
                                subp_of_year * opt_window * 24 + d * 24 + t + 1
                            )
                            timepoint = calculate_timepoint(
                                weather_mode,
                                i + 1,
                                hour_of_year,
                                hydro_years[j],
                                weather_years[k],
                            )
                            load_zone_writer.writerow(
                                [load_zone.name, timepoint, np.round(load_mw[t], 0)]
                            )

                        draw_day += 1

                    load_zone_temp_file.close()


def write_project_inputs(
    project,
    case_name,
    study_year,
    units,
    unit_names,
    timeseries,
    timeseries_names,
    weather_mode,
    iterations,
    opt_window,
    hydro_balancing_window,
    project_no,
):

    print("  ..." + project.name + "...")
    np.random.seed(project_no)

    # determine the number of digits to print to save space
    if project.operational_type == "gen_var_stor_hyb":
        N_round = len(str(int(project.total_var_mw))) + 2
        N_round_stor = len(str(int(project.total_stor_mw))) + 2
    else:
        N_round = len(str(int(project.total_mw))) + 2

    # pull the timeseries data for each unit in the project
    timeseries_data = []
    for unit_name in project.unit_list:

        # find the unit object
        unit_ind = unit_names.index(unit_name)
        unit = units[unit_ind]

        # store timeseries data for the unit if it's available
        if unit.timeseries != "NA":
            ts_ind = timeseries_names.index(unit.timeseries)
            ts = timeseries[ts_ind]
            timeseries_data.append(
                pd.read_csv(
                    os.path.join("timeseries_data", ts.name, unit.name + ".csv")
                )
            )

        else:
            timeseries_data.append([])

    # loop through iterations
    draw_day = 0
    subp = 0
    for i in range(iterations):

        # if using Synchronized weather mode, reset the draw_day counter and iterate through hydro and weather years for each iteration
        if weather_mode == "Synchronized":
            draw_day = 0
        for j in range(len(hydro_years)):
            for k in range(len(weather_years)):

                # loop through the subproblems for the year
                for subp_of_year in range(N_subp_per_year):

                    subp += 1

                    # create temporary files to store the GridPath availability files for the subproblem and project
                    # NOTE: temporary files are used to support parallelization, so that multiple projects can be written to the same subproblem at the same time
                    project_temp_files = []
                    project_writers = []
                    for f in range(len(project.input_filenames)):
                        project_temp_files.append(
                            open(
                                os.path.join(
                                    "Simulations",
                                    case_name,
                                    str(subp),
                                    "inputs",
                                    project.input_filenames[f],
                                    project.name + ".csv",
                                ),
                                "w",
                                newline="",
                            )
                        )
                        project_writers.append(csv.writer(project_temp_files[f]))
                        project_writers[f].writerow(project.input_headers[f])

                    # loop through the days for each subproblem
                    hydro_horizon = 0
                    for d in range(opt_window):

                        # initialize the input data for the day or for the hydro horizon
                        if project.operational_type == "gen_hydro_must_take":
                            if np.mod(d, hydro_balancing_window) == 0:
                                project_data = pd.DataFrame(
                                    0,
                                    index=np.arange(1),
                                    columns=["avg_hydro", "min_hydro", "max_hydro"],
                                )

                        elif (
                            project.operational_type == "gen_var"
                            or project.operational_type == "gen_var_must_take"
                        ):
                            project_data = pd.DataFrame(
                                0, index=np.arange(24), columns=["cap_factor"]
                            )

                        elif project.operational_type == "gen_var_stor_hyb":
                            project_data = pd.DataFrame(
                                0,
                                index=np.arange(24),
                                columns=[
                                    "cap_factor",
                                    "hyb_stor_cap_availability_derate",
                                ],
                            )

                        else:
                            project_data = pd.DataFrame(
                                0, index=np.arange(24), columns=["availability_derate"]
                            )

                        # loop through the units in the project
                        for u in range(len(project.unit_list)):

                            # find the unit object
                            unit_ind = unit_names.index(project.unit_list[u])
                            unit = units[unit_ind]

                            # pull any timeseries data that's available for the day - this could include outage rates
                            if unit.timeseries != "NA":

                                # pull the timeseries indices for the day
                                ts_ind = timeseries_names.index(unit.timeseries)
                                ts = timeseries[ts_ind]
                                ts_indices = ts.draw_indices[draw_day]

                                # pull the timeseries data for the day
                                day_timeseries_data = timeseries_data[u].loc[
                                    ts_indices, :
                                ]
                            else:
                                day_timeseries_data = pd.DataFrame()

                            # determine number of outage timesteps in day and the length of the outage timestep
                            T = project_data.index.size
                            dt = 24.0 / T

                            # pull max output, if available
                            if "max_output" in day_timeseries_data.columns:
                                p_maxoutput = day_timeseries_data[
                                    "max_output"
                                ].to_numpy(dtype=float)
                            else:
                                p_maxoutput = np.ones(T)

                            # pull unit FOR data, if available
                            if "unitFOR" in day_timeseries_data.columns:
                                p_unitFOR = day_timeseries_data["unitFOR"].to_numpy(
                                    dtype=float
                                )
                            else:
                                if unit.unitFOR != "NA":
                                    p_unitFOR = float(unit.unitFOR) * np.ones(T)
                                else:
                                    p_unitFOR = np.zeros(T)

                            # pull gentie FOR data, if available
                            if "gentieFOR" in day_timeseries_data.columns:
                                p_gentieFOR = day_timeseries_data["unitFOR"].to_numpy(
                                    dtype=float
                                )
                            else:
                                if unit.gentieFOR != "NA":
                                    p_gentieFOR = float(unit.gentieFOR) * np.ones(T)
                                else:
                                    p_gentieFOR = np.zeros(T)

                            # for the first iteration of each simulation, use a derate model to approximate outages
                            if i == 0:
                                unit_avail = simulate_outages(
                                    "Derate", p_unitFOR, unit.unitMTTR, unit.units, dt
                                )
                                gentie_avail = simulate_outages(
                                    "Derate", p_gentieFOR, unit.gentieMTTR, 1, dt
                                )

                            # for all other iterations, use the outage model specified for the unit
                            else:
                                # if it's the first day of the year, don't provide prior outage states (function will randomly select prior outage state if needed)
                                if draw_day == 0:
                                    unit_avail = simulate_outages(
                                        unit.unitModel,
                                        p_unitFOR,
                                        unit.unitMTTR,
                                        unit.units,
                                        dt,
                                    )
                                    gentie_avail = simulate_outages(
                                        unit.gentieModel,
                                        p_gentieFOR,
                                        unit.gentieMTTR,
                                        1,
                                        dt,
                                    )
                                # otherwise, provide the outage states for the unit from the prior timestep
                                else:
                                    unit_avail = simulate_outages(
                                        unit.unitModel,
                                        p_unitFOR,
                                        unit.unitMTTR,
                                        unit.units,
                                        dt,
                                        unit.unit_avail_last,
                                    )
                                    gentie_avail = simulate_outages(
                                        unit.gentieModel,
                                        p_gentieFOR,
                                        unit.gentieMTTR,
                                        1,
                                        dt,
                                        unit.gentie_avail_last,
                                    )

                                # store the last outage state for the units to initialize the next day
                                unit.unit_avail_last = unit_avail[-1, :]
                                unit.gentie_avail_last = gentie_avail[-1, :]

                            # calculate total impact of outages on unit avaiability
                            outage_adjustment = np.mean(unit_avail, axis=1) * np.mean(
                                gentie_avail, axis=1
                            )

                            # incorporate unit availability into weighted average project availability
                            if project.operational_type == "gen_hydro_must_take":
                                project_data += (
                                    day_timeseries_data[
                                        ["avg_hydro", "min_hydro", "max_hydro"]
                                    ].to_numpy()
                                    * outage_adjustment[0]
                                    * unit.mw
                                    / project.total_mw
                                    / hydro_balancing_window
                                )

                            elif (
                                project.operational_type == "gen_var"
                                or project.operational_type == "gen_var_must_take"
                            ):
                                project_data["cap_factor"] += (
                                    p_maxoutput
                                    * outage_adjustment
                                    * unit.mw
                                    / project.total_mw
                                )

                            elif project.operational_type == "gen_var_stor_hyb":
                                if unit.unit_type == "var_gen":
                                    project_data["cap_factor"] += (
                                        p_maxoutput
                                        * outage_adjustment
                                        * unit.mw
                                        / project.total_var_mw
                                    )
                                elif unit.unit_type == "stor":
                                    project_data[
                                        "hyb_stor_cap_availability_derate"
                                    ] += (
                                        p_maxoutput
                                        * outage_adjustment
                                        * unit.mw
                                        / project.total_stor_mw
                                    )

                            else:
                                project_data["availability_derate"] += (
                                    p_maxoutput
                                    * outage_adjustment
                                    * unit.mw
                                    / project.total_mw
                                )

                        # print project availability data to the subproblem temporary files
                        for f in range(len(project_temp_files)):

                            if (
                                project.input_filenames[f]
                                == "hydro_conventional_horizon_params"
                            ):
                                # only print hydro data if it's the last day of a hydro horizon
                                if (
                                    np.mod(d, hydro_balancing_window)
                                    == hydro_balancing_window - 1
                                ):
                                    hydro_horizon += 1
                                    project_data = np.round(project_data, N_round)
                                    project_writers[f].writerow(
                                        [
                                            project.name,
                                            hydro_horizon,
                                            project_data.loc[0, "avg_hydro"],
                                            project_data.loc[0, "min_hydro"],
                                            project_data.loc[0, "max_hydro"],
                                        ]
                                    )

                            elif (
                                project.input_filenames[f]
                                == "variable_generator_profiles"
                            ):
                                for t in range(24):
                                    hour_of_year = (
                                        subp_of_year * opt_window * 24 + d * 24 + t + 1
                                    )
                                    timepoint = calculate_timepoint(
                                        weather_mode,
                                        i + 1,
                                        hour_of_year,
                                        hydro_years[j],
                                        weather_years[k],
                                    )
                                    project_data = np.round(project_data, N_round)
                                    project_writers[f].writerow(
                                        [
                                            project.name,
                                            timepoint,
                                            project_data.loc[t, "cap_factor"],
                                        ]
                                    )

                            else:
                                for t in range(24):
                                    hour_of_year = (
                                        subp_of_year * opt_window * 24 + d * 24 + t + 1
                                    )
                                    timepoint = calculate_timepoint(
                                        weather_mode,
                                        i + 1,
                                        hour_of_year,
                                        hydro_years[j],
                                        weather_years[k],
                                    )
                                    if project.operational_type == "gen_var_stor_hyb":
                                        project_data[
                                            "hyb_stor_cap_availability_derate"
                                        ] = np.round(
                                            project_data[
                                                "hyb_stor_cap_availability_derate"
                                            ],
                                            N_round_stor,
                                        )
                                        project_writers[f].writerow(
                                            [
                                                project.name,
                                                timepoint,
                                                ".",
                                                project_data.loc[
                                                    t,
                                                    "hyb_stor_cap_availability_derate",
                                                ],
                                            ]
                                        )
                                    else:
                                        project_data["availability_derate"] = np.round(
                                            project_data["availability_derate"], N_round
                                        )
                                        project_writers[f].writerow(
                                            [
                                                project.name,
                                                timepoint,
                                                project_data.loc[
                                                    t, "availability_derate"
                                                ],
                                                ".",
                                            ]
                                        )

                        draw_day += 1

                    for project_temp_file in project_temp_files:
                        project_temp_file.close()


def consolidate_files(case_name, subp):

    input_files = os.listdir(
        os.path.join("Simulations", case_name, str(subp), "inputs")
    )

    for input_file in input_files:

        with open(
            os.path.join(
                "Simulations", case_name, str(subp), "inputs", input_file + ".tab"
            ),
            "w",
            newline="",
        ) as final_file:
            input_writer = csv.writer(final_file, delimiter="\t")

            # loop through the output files
            i = 0
            for temporary_file in os.listdir(
                os.path.join("Simulations", case_name, str(subp), "inputs", input_file)
            ):
                with open(
                    os.path.join(
                        "Simulations",
                        case_name,
                        str(subp),
                        "inputs",
                        input_file,
                        temporary_file,
                    )
                ) as temp_file:
                    temp_reader = csv.reader(temp_file)
                    # only print the header to the GridPath input file if it's the first file being read
                    if i == 0:
                        input_writer.writerow(temp_reader.__next__())
                    else:
                        temp_reader.__next__()

                    # print the rest of the rows to the GridPath input file
                    for row in temp_reader:
                        input_writer.writerow(row)
                i += 1

        # delete temporary files
        shutil.rmtree(
            os.path.join("Simulations", case_name, str(subp), "inputs", input_file)
        )


if __name__ == "__main__":

    case_name = sys.argv[1]
    # no_jobs = int(sys.argv[2])

    ###########################################################################
    # Remove old directories
    ###########################################################################

    print("removing old directories...")

    # NOTE - TYPICALLY PARALLELIZE DELETING SUBPROBLEMS TO SPEED IT UP
    if os.path.isdir(os.path.join("Simulations", case_name)) == True:
        for subproblem_folder in glob.glob(os.path.join("Simulations", case_name, "*")):
            if os.path.isdir(subproblem_folder):
                shutil.rmtree(subproblem_folder)

    # remove the rest of the directory and its contents
    if os.path.isdir(os.path.join("Simulations", case_name)):
        shutil.rmtree(os.path.join("Simulations", case_name))

    if os.path.isdir(os.path.join("Simulations", case_name + "_log")):
        shutil.rmtree(os.path.join("Simulations", case_name + "_log"))

    ###########################################################################
    # Import settings
    ###########################################################################

    print("importing scenario information...")

    with open("settings/scenario_settings.csv") as csvfile:
        file_reader = csv.reader(csvfile)
        scenarios = file_reader.__next__()
        if case_name not in scenarios:
            print("Error - scenario not listed in scenario_settings.csv")
        else:
            scenario_ind = scenarios.index(case_name)
            study_year = int(file_reader.__next__()[scenario_ind])
            weather_mode = file_reader.__next__()[scenario_ind]
            opt_window = int(file_reader.__next__()[scenario_ind])
            subproblem_balancing_type = file_reader.__next__()[scenario_ind]
            hydro_balancing_window = int(file_reader.__next__()[scenario_ind])
            iterations = int(file_reader.__next__()[scenario_ind])
            loads_file = file_reader.__next__()[scenario_ind]
            units_file = file_reader.__next__()[scenario_ind]
            timeseries_file = file_reader.__next__()[scenario_ind]
            common_files = file_reader.__next__()[scenario_ind]
    N_subp_per_year = int(np.floor(365 / opt_window))

    # import load zones
    print("reading load zone information...")
    load_zone_names = []
    load_zones = []
    if os.path.exists(
        os.path.join("common_files", common_files, "subproblems", "load_zones.tab")
    ):
        with open(
            os.path.join("common_files", common_files, "subproblems", "load_zones.tab")
        ) as csvfile:
            file_reader = csv.reader(csvfile, delimiter="\t")
            file_reader.__next__()
            for row in file_reader:
                name = row[0]
                load_zone_names.append(name)
                load_zones.append(Load_Zone(name))
    else:
        print("Error - project file not found.")

    # import loads
    print("importing loads...")
    load_names = []
    loads = []
    if os.path.exists(os.path.join("settings", loads_file)):
        with open(os.path.join("settings", loads_file)) as csvfile:
            file_reader = csv.reader(csvfile, delimiter=",")
            file_reader.__next__()
            for row in file_reader:
                load_name = row[0]
                load_zone_name = row[1]
                if load_zone_name in load_zone_names:
                    load_timeseries = row[2]
                    load_scalar = float(row[3])

                    load_names.append(load_name)
                    loads.append(
                        Load(load_name, load_zone_name, load_timeseries, load_scalar)
                    )

                    # add load to load zone load list
                    load_zone_ind = load_zone_names.index(load_zone_name)
                    load_zone = load_zones[load_zone_ind]
                    load_zone.load_list.append(load_name)

    else:
        print("Error - loads file not found.")

    # import projects
    print("reading project information...")
    project_names = []
    projects = []
    if os.path.exists(
        os.path.join("common_files", common_files, "subproblems", "projects.tab")
    ):
        with open(
            os.path.join("common_files", common_files, "subproblems", "projects.tab")
        ) as csvfile:
            file_reader = csv.reader(csvfile, delimiter="\t")
            file_reader.__next__()
            for row in file_reader:
                name = row[0]
                operational_type = row[3]
                project_names.append(name)
                projects.append(Project(name, operational_type))

    else:
        print("Error - project file not found.")

    # import units
    print("importing units...")
    unit_names = []
    units = []
    if os.path.exists(os.path.join("settings", units_file)):
        with open(os.path.join("settings", units_file)) as csvfile:
            file_reader = csv.reader(csvfile)
            file_reader.__next__()
            for row in file_reader:

                unit_name = row[0]
                project_name = row[1]
                unit_type = row[2]
                unit_mw = float(row[3])
                unit_timeseries = row[4]
                N_units = row[5]
                unitModel = row[6]
                unitFOR = row[7]
                unitMTTR = row[8]
                gentieModel = row[9]
                gentieFOR = row[10]
                gentieMTTR = row[11]

                # add the unit to the units array
                if project_name in project_names:

                    unit_names.append(unit_name)
                    units.append(
                        Unit(
                            unit_name,
                            project_name,
                            unit_type,
                            unit_mw,
                            unit_timeseries,
                            N_units,
                            unitModel,
                            unitFOR,
                            unitMTTR,
                            gentieModel,
                            gentieFOR,
                            gentieMTTR,
                        )
                    )

                    # add unit to project unit list and mw to project mw totals
                    project_ind = project_names.index(project_name)
                    project = projects[project_ind]
                    project.unit_list.append(unit_name)
                    if project.operational_type == "gen_var_stor_hyb":
                        if unit_type == "var_gen":
                            project.total_var_mw += unit_mw
                        elif unit_type == "stor":
                            project.total_stor_mw += unit_mw
                    else:
                        project.total_mw += unit_mw
                else:
                    print("Error - project not found.")
    else:
        print("Error - units file not found.")

    # import timeseries settings
    print("importing timeseries settings...")
    timeseries_names = []
    timeseries = []
    if os.path.exists(os.path.join("settings", timeseries_file)):
        with open(os.path.join("settings", timeseries_file)) as csvfile:
            file_reader = csv.reader(csvfile, delimiter=",")
            file_reader.__next__()
            for row in file_reader:
                timeseries_name = row[0]
                timeseries_names.append(timeseries_name)
                timeseries.append(Timeseries(timeseries_name, row[1]))
    else:
        print("Error - timeseries file not found.")

    ###########################################################################
    # Import bin information
    ###########################################################################

    # if in Monte Carlo weather mode, import bin information
    if weather_mode == "MonteCarlo":

        print("importing bin information...")

        # Import bin data
        print("  ...weather and day-type bins...")
        weather_bins = pd.read_csv(os.path.join("bins", "weather_bins.csv"))

        print("  ...hydro bins...")
        hydro_bins = pd.read_csv(os.path.join("bins", "hydro_bins.csv"))

        weather_years = [0]
        hydro_years = [0]

    ###########################################################################
    # Import hydro and weather years to run
    ###########################################################################

    # if in Synchronized weather mode, import the list of hydro years and weather years to run
    elif weather_mode == "Synchronized":

        print("importing hydro and weather years to run...")

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

    ###########################################################################
    # Bin the timeseries data
    ###########################################################################

    print("binning/indexing timeseries data...")

    # assign timestamps corresponding to each timeseries to their corresponding bins
    for ts in timeseries:

        print("  ..." + ts.name + "...")

        # pull in timestamps, excluding HE column
        timestamps_tmp = pd.read_csv(
            os.path.join("timeseries_data", ts.name, "timestamps.csv")
        )
        ts.timestamps = timestamps_tmp.loc[:, timestamps_tmp.columns != "HE"]
        timestamp_years = list(np.unique(ts.timestamps["year"]))

        if weather_mode == "MonteCarlo":

            if ts.stat == "hyd":
                ts.hydro_bins = np.zeros(ts.timestamps.index.size, dtype=int)
                for hydro_bin in hydro_bins.index:
                    year = hydro_bins.loc[hydro_bin, "year"]
                    if year in timestamp_years:
                        month = hydro_bins.loc[hydro_bin, "month"]
                        mask = (ts.timestamps["year"] == year) & (
                            ts.timestamps["month"] == month
                        )
                        ts.hydro_bins[mask] = hydro_bins.loc[hydro_bin, "hydro_bin"]

            else:
                ts.met_bins = np.zeros(ts.timestamps.index.size, dtype=int)
                if ts.stat == "cmb":
                    ts.daytype_bins = np.zeros(ts.timestamps.index.size, dtype=int)
                for met_bin in weather_bins.index:
                    year = weather_bins.loc[met_bin, "year"]
                    if year in timestamp_years:
                        month = weather_bins.loc[met_bin, "month"]
                        day = weather_bins.loc[met_bin, "day"]
                        mask = (
                            (ts.timestamps["year"] == year)
                            & (ts.timestamps["month"] == month)
                            & (ts.timestamps["day"] == day)
                        )
                        ts.met_bins[mask] = weather_bins.loc[met_bin, "weather_bin"]
                        if ts.stat == "cmb":
                            ts.daytype_bins[mask] = weather_bins.loc[
                                met_bin, "daytype_bin"
                            ]

    ###########################################################################
    # Create directory structure
    ###########################################################################

    print("creating directory structure...")

    # create new directories
    subp = 0
    for i in range(iterations):
        # if weather mode is Synchronized, loop through hydro and weather years for each iteration
        for j in range(len(hydro_years)):
            for k in range(len(weather_years)):
                for subp_of_year in range(N_subp_per_year):
                    subp += 1
                    # create the temporary file directories for the subproblem
                    for load_zone in load_zones:
                        input_filename = load_zone.input_filename
                        if (
                            os.path.exists(
                                os.path.join(
                                    "Simulations",
                                    case_name,
                                    str(subp),
                                    "inputs",
                                    input_filename,
                                )
                            )
                            == False
                        ):
                            os.makedirs(
                                os.path.join(
                                    "Simulations",
                                    case_name,
                                    str(subp),
                                    "inputs",
                                    input_filename,
                                )
                            )
                    for project in projects:
                        for input_filename in project.input_filenames:
                            if (
                                os.path.exists(
                                    os.path.join(
                                        "Simulations",
                                        case_name,
                                        str(subp),
                                        "inputs",
                                        input_filename,
                                    )
                                )
                                == False
                            ):
                                os.makedirs(
                                    os.path.join(
                                        "Simulations",
                                        case_name,
                                        str(subp),
                                        "inputs",
                                        input_filename,
                                    )
                                )

    if os.path.isdir(os.path.join("Simulations", case_name + "_log")) == False:
        os.makedirs(os.path.join("Simulations", case_name + "_log"))

    ###########################################################################
    # Draw conditions and corresponding timeseries indices
    ###########################################################################

    # initialize file to store draw data for each timeseries
    draw_data_file = open(
        os.path.join("Simulations", case_name + "_log", "draw_data.csv"),
        "w",
        newline="",
    )
    draw_data_writer = csv.writer(draw_data_file)

    if weather_mode == "MonteCarlo":

        print("randomly drawing conditions...")

        # print the header for the draw information
        header = ["subproblem", "day", "hydro year", "month", "weather bin", "weekend"]
        for ts in timeseries:
            for h in ts.timestamps.columns:
                header.append(ts.name + " " + h)
        draw_data_writer.writerow(header)

        # Simulate weather days over 52 weeks for each simulation year
        np.random.seed(seed=0)
        for yr in range(iterations):

            # print every 10th year to screen
            if np.mod(yr + 1, 10) == 0:
                print("  ...year " + str(yr + 1) + " of " + str(iterations) + "..")

            # randomly draw hydro conditions for the year from the list of hydro bins
            hydrobin_tmp = hydro_bins["hydro_bin"][
                np.random.randint(hydro_bins.index.size)
            ]

            # randomly draw the weather conditions on the first day of the year from all of the January weather days
            # starting_met_options = metbin[(cmbbin_month == 1)]
            starting_met_options = weather_bins[weather_bins["month"] == 1][
                "weather_bin"
            ].to_numpy()
            simmetbin = starting_met_options[
                np.random.randint(len(starting_met_options))
            ]
            prior_metbin = simmetbin

            # start with the last calendar day prior to the study year
            simdate = np.datetime64(str(study_year) + "-01-01") - np.timedelta64(1, "D")

            # loop through the subproblems for the year
            for subp in range(N_subp_per_year):
                # loop through the days for each subproblem
                for d in range(opt_window):

                    # move forward 1 day
                    simdate += np.timedelta64(1, "D")
                    # determine the month
                    simmonth = simdate.astype(object).month
                    # determine the day type (1 if weekend, 0 if weekday, must match day-type bin convention)
                    simdaytype = (
                        simdate.astype(datetime.datetime).isoweekday() > 5
                    ) * 1

                    # randomly select the weather bin from all days that follow the prior weather bin in the month
                    if i > 0:
                        # pull the weather bins across all days in the month
                        # met_options_tmp = metbin[(cmbbin_month == simmonth)]
                        met_options_tmp = weather_bins[
                            weather_bins["month"] == simmonth
                        ]["weather_bin"].to_numpy()
                        # find the indices where the weather bin matches the prior weather bin, and add 1
                        nextbin_inds = (
                            np.array(np.where(met_options_tmp == prior_metbin)) + 1
                        )
                        # remove indices that exceed the maximum index (in case the last day of weather matched the prior bin)
                        nextbin_inds = nextbin_inds[nextbin_inds < len(met_options_tmp)]
                        # find the weather bins that fall after the prior weather bin
                        nextbin_options = met_options_tmp[nextbin_inds]
                        # randomly randomly select the next weather bin from this list
                        simmetbin = nextbin_options[
                            np.random.randint(len(nextbin_options))
                        ]
                        prior_metbin = simmetbin

                    # prepare draw information to print
                    draw_data = np.array(
                        [
                            N_subp_per_year * yr + subp + 1,
                            d + 1,
                            hydrobin_tmp,
                            simmonth,
                            simmetbin,
                            simdaytype,
                        ]
                    )

                    # randomly select periods within the current bin for each timeseries
                    for ts in timeseries:

                        # if hydro statistical model, find intervals with matching hydro years and months
                        if ts.stat == "hyd":
                            bin_mask = (ts.timestamps["month"] == simmonth) & (
                                ts.hydro_bins == hydrobin_tmp
                            )

                        # if meteorological model, find intervals with matching months and weather
                        if ts.stat == "met":
                            bin_mask = (ts.timestamps["month"] == simmonth) & (
                                ts.met_bins == simmetbin
                            )

                        # if combined meteorological and daytype model, find intervals with matching months, weather, and day-types
                        if ts.stat == "cmb":
                            bin_mask = (
                                (ts.timestamps["month"] == simmonth)
                                & (ts.met_bins == simmetbin)
                                & (ts.daytype_bins == simdaytype)
                            )

                        # pull the intervals and corresponding indices that fall within the bin
                        bin_timestamps = np.array(ts.timestamps.loc[bin_mask, :])

                        # randomly select an interval from the bin - note, if the data is hourly, this will select an hour, but need to pull the whole day
                        draw = np.random.randint(np.sum(bin_mask))
                        draw_timestamp = bin_timestamps[draw, :]

                        # store all indices in the timeseries data corresponding to the drawn day
                        ts.draw_indices.append((ts.timestamps == draw_timestamp).all(1))

                        # record the draw information
                        draw_data = np.append(draw_data, draw_timestamp)

                    # print draw data
                    draw_data_writer.writerow(draw_data)

    elif weather_mode == "Synchronized":

        print("pulling synchronized conditions...")

        # print the header for the draw information
        header = [
            "subproblem",
            "day",
            "hydro year",
            "weather year",
            "weather month",
            "weather day",
        ]
        for ts in timeseries:
            for h in ts.timestamps.columns:
                header.append(ts.name + " " + h)
        draw_data_writer.writerow(header)

        # loop through hydro years
        for i in range(len(hydro_years)):

            print("  ...hydro year: " + str(hydro_years[i]))

            # loop through weather years
            for j in range(len(weather_years)):

                print("     ...weather year: " + str(weather_years[j]))

                # determine starting hydro and weather year - NOTE THIS IS DIFFERENTIATED FROM CURRENT WEATHER AND HYDRO YEAR, HELPFUL IF NOT STARTING ON JAN 1
                starting_hydroyear = hydro_years[i]
                starting_weatheryear = weather_years[j]

                # start with the last calendar day prior to the weather year - NOTE THIS IS DIFFERENT FROM MONTE CARLO, which follows the calendar of the study year
                weatherdate = np.datetime64(
                    str(starting_weatheryear) + "-01-01"
                ) - np.timedelta64(1, "D")

                # loop through the subproblems for the year
                for subp in range(N_subp_per_year):
                    # loop through the days for each subproblem
                    for d in range(opt_window):

                        # move forward 1 day
                        weatherdate += np.timedelta64(1, "D")

                        # determine the weather timestamp
                        weatheryear = weatherdate.astype(object).year
                        # loop around if needed
                        # NOTE THIS WILL BE HELPFUL IF NOT STARTING ON JAN 1
                        if weatheryear not in weather_years:
                            if starting_weatheryear == weather_years[-1]:
                                weatheryear = weather_years[0]
                            else:
                                weatheryear = starting_weatheryear
                        weathermonth = weatherdate.astype(object).month
                        weatherdayofmonth = weatherdate.astype(object).day
                        weather_timestamp = [
                            weatheryear,
                            weathermonth,
                            weatherdayofmonth,
                        ]

                        # if in a new weather year, update the hydro year to the next year, or loop around if needed
                        # NOTE THIS WILL BE HELPFUL IF NOT STARTING ON JAN 1
                        hydroyear = (
                            starting_hydroyear + weatheryear - starting_weatheryear
                        )
                        if hydroyear not in hydro_years:
                            if starting_hydroyear == hydro_years[-1]:
                                hydroyear = hydro_years[0]
                            else:
                                hydroyear = starting_hydroyear
                        hydro_timestamp = [hydroyear, weathermonth]

                        # print draw data
                        draw_data_writer.writerow(
                            [
                                subp + 1,
                                d + 1,
                                hydroyear,
                                weatheryear,
                                weathermonth,
                                weatherdayofmonth,
                            ]
                        )

                        # find the indices corresponding to the draw in each timeseries
                        for ts in timeseries:
                            # if hydro statistical model, find intervals with matching hydro years and months
                            if ts.stat == "hyd":
                                ts.draw_indices.append(
                                    (ts.timestamps == hydro_timestamp).all(1)
                                )
                            # if meteorological or combined meteorological/daytype model, find intervals with matching weather year, month, and day
                            elif ts.stat == "met" or ts.stat == "cmb":
                                ts.draw_indices.append(
                                    (ts.timestamps == weather_timestamp).all(1)
                                )

    draw_data_file.close()

    ###########################################################################
    # Write load and project availability inputs
    ###########################################################################

    print("simulating load...")
    i = 0
    for load_zone in load_zones:
        write_load_inputs(
            load_zone,
            case_name,
            study_year,
            loads,
            load_names,
            timeseries,
            timeseries_names,
            weather_mode,
            iterations,
            opt_window,
            i,
        )
        i += 1

    print("simulating project availability...")
    i = 0
    for project in projects:
        write_project_inputs(
            project,
            case_name,
            study_year,
            units,
            unit_names,
            timeseries,
            timeseries_names,
            weather_mode,
            iterations,
            opt_window,
            hydro_balancing_window,
            i,
        )
        i += 1

    ###########################################################################
    # Finalize input files for GridPath
    ###########################################################################

    print("finalizing input files...")

    # loop through iterations
    subp = 0
    for i in range(iterations):

        # if weather mode is Synchronized, add loops for hydro and weather years for each iteration
        for j in range(len(hydro_years)):
            for k in range(len(weather_years)):
                for subp_of_year in range(N_subp_per_year):
                    subp += 1

                    # consolidate project inputs from temporary files into final GridPath input files - NOTE: typically parallelize this
                    consolidate_files(case_name, subp)

                    # copy common files into subproblem directory
                    subproblem_dir = os.path.join(
                        "common_files", common_files, "subproblems"
                    )
                    for file in os.listdir(subproblem_dir):
                        shutil.copy(
                            os.path.join(subproblem_dir, file),
                            os.path.join(
                                "Simulations", case_name, str(subp), "inputs", file
                            ),
                        )

                    # print temporal files - NOTE: typically parallelize this
                    if weather_mode == "MonteCarlo":
                        write_temporal_files(
                            subp,
                            subp_of_year + 1,
                            case_name,
                            weather_mode,
                            opt_window,
                            hydro_balancing_window,
                            subproblem_balancing_type,
                            study_year,
                            N_subp_per_year,
                            i + 1,
                        )
                    elif weather_mode == "Synchronized":
                        write_temporal_files(
                            subp,
                            subp_of_year + 1,
                            case_name,
                            weather_mode,
                            opt_window,
                            hydro_balancing_window,
                            subproblem_balancing_type,
                            study_year,
                            N_subp_per_year,
                            i + 1,
                            hydro_years[j],
                            weather_years[k],
                        )

    # copy common files for the scenario
    case_dir = os.path.join("common_files", common_files, "case")
    for file in os.listdir(case_dir):
        shutil.copy(
            os.path.join(case_dir, file), os.path.join("Simulations", case_name, file)
        )

    # revise scenario_description to reflect case name
    scen_file = open(
        os.path.join("Simulations", case_name, "scenario_description.csv"),
        "w",
        newline="",
    )
    scen_writer = csv.writer(scen_file)
    with open(
        os.path.join("Simulations", case_name, "scenario_description_base.csv")
    ) as basefile:
        csvreader = csv.reader(basefile)
        for row in csvreader:
            if row[1] == "case_name":
                scen_writer.writerow([row[0], case_name])
            else:
                scen_writer.writerow(row)
    scen_file.close()
    os.remove(os.path.join("Simulations", case_name, "scenario_description_base.csv"))

    print("GridPath input files written.")
