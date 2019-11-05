#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Port India data to GridPath
"""

from collections import OrderedDict
import csv
import os
import sqlite3
import warnings
import pandas as pd
import calendar
import numpy as np
import csv
import xlrd
import scipy.stats as stats
import math
import time
import datetime as dt


# Provide path for gripath modules
import sys
# Relative path to directory
##path_to_gridpath_modules = os.path.abspath(os.path.join(__file__,"../../3repo/gridpath/db/utilities"))
# Absolute path to directory
#path_to_gridpath_modules = os.path.abspath(os.path.join(__file__,"/Users/ranjitster/Dropbox/GridPath/1repo/gridpath/db/utilities"))
##sys.path.insert(0, path_to_gridpath_modules)

# Data-import modules

from db.utilities import temporal, geography, project_list, project_zones, \
    project_operational_chars, project_availability, fuels, \
    project_portfolios, project_existing_params, project_new_costs, \
    project_new_potentials, project_prm, transmission_portfolios, \
    transmission_zones, transmission_capacities, simultaneous_flow_groups, \
    simultaneous_flows, transmission_hurdle_rates, carbon_cap, system_load, \
    system_reserves, system_prm, rps, scenario

from db.csvs_to_db_utilities import csvs_read, load_geography




## MODULES FOR PORTING DATA TO SQL DATABASE
# import port_data_to_gridpath_project_modules
# import port_data_to_gridpath_demand_modules

## INPUTS
# SQL database
sql_database = 'io.db'  # e.g. MH.db

# Input csv path
inputPath = os.path.join(os.getcwd(), "db")
dbPath = os.path.join(os.getcwd(), "db")

# csv with periods data
periods_csv = inputPath + '/inputs/periods_4periods.csv'

# csv with horizons data
horizons_csv = inputPath + '/inputs/horizons_12_1dayPerMonth.csv'

# csv with existing generators data
existing_projects_csv = inputPath + '/inputs/gen_all_input_cc_ccgt_diesel.csv'

# csv with new variable generation projects data
new_projects_wind_csv = inputPath + '/inputs/variable_gen_projects/wind_candidate_projects.csv'
new_projects_solar_csv = inputPath + '/inputs/variable_gen_projects/solar_candidate_projects.csv'
new_projects_wind_timeseries_csv = inputPath + '/inputs/variable_gen_projects/wind_candidate_project_timeseries.csv'
new_projects_solar_timeseries_csv = inputPath + '/inputs/variable_gen_projects/solar_candidate_project_timeseries.csv'

# csv with hourly demand forecasts
load_csv = inputPath + '/inputs/demand/demand_2014_2032_hourly.csv'

# csv with year, month, days selected - sample days
year_month_days_selected_csv = inputPath + '/inputs/demand/year_month_days_selected.csv'
year_month_days_selected = pd.read_csv(year_month_days_selected_csv)

# csv with hydro data
hydro_max_energy_csv = inputPath + '/inputs/hydro_max_energy.csv'
hydro_min_gen_csv = inputPath + '/inputs/hydro_min_gen.csv'
mustrun_gen_csv = inputPath + '/inputs/mustrun_gen.csv'
# This is the curated hydro parameters output file
projects_hydro_horizon_chars_csv = inputPath + '/inputs/projects_hydro_horizon_chars.csv'
# This is the curated variable non-curtailable time series
projects_variable_noncurtailable_timeseries_csv = inputPath + '/inputs/variable_gen_projects/variable_noncurtailable_timeseries.csv'

# data with heat rate curves and variable om costs
projects_hr_var_costs_excel = inputPath + '/inputs/projects_hr_var_costs.xlsx'

# data with new projects costs and operational characteristics
new_projects_excel = inputPath + '/inputs/new_projects.xlsx'

# main_scenarios to run
main_scenarios_csv = inputPath + '/inputs/main_scenarios.csv'

# RPS targets by zones and scenarios
rps_targets_excel = inputPath + '/inputs/rps_targets.xlsx'

# Path to input data files
#plexos_model_path = inputPath + 'MH_Plexos_Model/Plexos_26-27_MSEDCL_Model_Inputs-20181120.xlsx'
#plexos_model_data_files_folder = 'MH_Plexos_Model/MH_Plexos_Model_Data_Files/'

discount_rate = 0.07
base_year = 2018
horizons_per_year = 12
number_of_hours_in_timepoint = 1  # 0.25 for 15 minutes
inr_to_usd = 70

# TIME INDEXES
day_array_365 = np.arange(1,366)
day_array_8760 = np.repeat(day_array_365, 24)
hour_array_8760 = np.arange(1,8761)
hour_of_day_array = np.tile(np.arange(1,25), 365)

# Connect to database
io = sqlite3.connect(
    os.path.join(dbPath, sql_database)
)

c2 = io.cursor()


#### Functions to read csv data
# Read the tables_feature_subscenarios csv

# if include flag is 1, then read the feature, subscenario_id, table, and path into a dictionary and call the specific function for the feature



#### LOAD GEORGRAPHY DATA ####

## LOAD LOAD ZONES ##
data_folder_path = os.path.join(os.getcwd(), 'db', 'csvs', 'geography', 'geography_load_zones')

(csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path)

csv_subscenario_input = OrderedDict(sorted(csv_subscenario_input.items()))

load_geography.load_geography_load_zones(io, c2, csv_subscenario_input, csv_data_input)

## LOAD RPS ZONES ##

def load_geography_rps_zones():
    """
    single rps zone
    :return:
    """
    geography.geography_rps_zones(
        io=io, c=c2,
        rps_zone_scenario_id=1,
        scenario_name='india_rps',
        scenario_description='INDIA RPS',
        zones=['India']
    )

#### LOAD TEMPORAL DATA ####

def load_temporal_data():
    """
    Add timepoints/days into database
    Investment periods are 2018, 2022, 2026, and 2030
    Discount factors are calculated using an input discount rate and a base year
    Number of years represented by a period is 4 but arbitrarily set to a
    higher number for the last period
    Horizon boundary is circular
    :return:
    """

    # Useful functions ######
    # from https://stackoverflow.com/questions/50929768/pandas-multiindex-more-than-2-levels-dataframe-to-nested-dict-json?noredirect=1&lq=1
    # TOD: Can we move this functions out of this function so they are available to the rest of the functions?

    def nest(d: dict) -> dict:
        result = {}
        for key, value in d.items():
            target = result
            for k in key[:-1]:  # traverse all keys but the last
                target = target.setdefault(k, {})
            target[key[-1]] = value
        return result

    def df_to_nested_dict(df: pd.DataFrame) -> dict:
        d = df.to_dict(orient='index')
        return {k: nest(v) for k, v in d.items()}

    #########

    # PERIODS
    global periods_df
    periods_df = pd.read_csv(periods_csv, sep=',')

    # Make a dictionary with the discount factor and number of years
    # represented for each investment period

    # DELETE
    # discount_factors_and_years_represented = dict(dict())
    #
    # for p in periods_df["period"]:
    #     discount_factors_and_years_represented[p] = {}
    #     discount_factors_and_years_represented[p]["df"] = 1 / (
    #             (1 + discount_rate) ** (p - base_year)) # CHECK THIS FORMULA. Removed +1 after base_year
    #     discount_factors_and_years_represented[p]["y"] = periods_df.loc[
    #         periods_df["period"] == p]["number_years_represented"].iloc[0]
    # DELETE

    # Calculate the discount factors
    periods_df['discount_factor'] = 1 / (
                (1 + discount_rate) ** (periods_df['period'] - base_year)) # CHECK THIS FORMULA. Removed +1 after base_year

    periods = dict(dict())
    for p in periods_df['period']:
        periods[p] = {}
        periods[p]['discount_factor'] = periods_df.loc[
            periods_df["period"] == p]['discount_factor'].iloc[0]
        periods[p]['number_years_represented'] = periods_df.loc[
            periods_df["period"] == p]['number_years_represented'].iloc[0]

    # TODO: CAN WE USE THIS ALTERNATE CODE TO POPULATE DICTIONARIES?
    periods_alt = dict(dict())
    periods_df_alt = periods_df.copy()
    periods_df_alt = periods_df_alt.set_index("period")
    periods_alt = periods_df_alt.to_dict(orient='index')


    # HORIZONS
    # Read csv, add horizon as index, and convert to dictionary
    global horizon_array  # So other modules can use this variable
    #global month_array
    global horizon_weights_and_months_df
    if horizons_csv != '':
        horizon_weights_and_months_df = pd.read_csv(horizons_csv, sep=',')
        horizon_array = horizon_weights_and_months_df['horizon'].values
        #month_array = horizon_weights_and_months_df['month'].values
    else:
        horizon_array = np.arange(1, horizons_per_year + 1, 1)
        weights_array = np.repeat(1, horizons_per_year)
        # weights_array = np.repeat(1, (366 if calendar.isleap(base_year) else 365))
        month_array = []
        # This month array is for 1 day horizon with 365 days. For less number of days, use a csv.
        for m in range(1, 12 + 1, 1):
            month_array = np.append(month_array, np.repeat(m, monthrange(base_year, m)[1])).astype(int)
        horizon_weights_and_months_df = pd.DataFrame(
            {'horizon': horizon_array, 'weight': weights_array, 'month': month_array})

    horizon_weights_and_months_df = horizon_weights_and_months_df.set_index("horizon")
    horizon_weights_and_months = horizon_weights_and_months_df.to_dict(orient='index')


    # Subproblems and stages (one subproblem, one stage)
    subproblems = [1]
    subproblem_stages = {sid: [(1, "single stage")] for sid in subproblems}


    # Timepoints
    subproblem_stage_timepoints = dict()
    for subproblem_id in subproblem_stages.keys():
        print(subproblem_id)
        subproblem_stage_timepoints[subproblem_id] = dict()
        for stage in subproblem_stages[subproblem_id]:
            stage_id = stage[0]
            subproblem_stage_timepoints[subproblem_id][stage_id] = dict()
            for _period in periods.keys():
                for _day in horizon_weights_and_months.keys():
                    for hour in range(1, 25):
                        timepoint = _period * 10**4 + _day * 10**2 + hour
                        subproblem_stage_timepoints[subproblem_id][
                            stage_id][timepoint] = dict()
                        subproblem_stage_timepoints[subproblem_id][
                            stage_id][timepoint]["period"] = _period
                        subproblem_stage_timepoints[subproblem_id][
                            stage_id][timepoint][
                            "number_of_hours_in_timepoint"] = 1
                        subproblem_stage_timepoints[subproblem_id][
                            stage_id][timepoint]["timepoint_weight"] = \
                            horizon_weights_and_months[_day]["weight"]
                        subproblem_stage_timepoints[subproblem_id][
                            stage_id][timepoint][
                            "previous_stage_timepoint_map"] = None
                        subproblem_stage_timepoints[subproblem_id][
                            stage_id][timepoint][
                            "spinup_or_lookahead"] = None
                        subproblem_stage_timepoints[subproblem_id][
                            stage_id][timepoint]["month"] = \
                            int(horizon_weights_and_months[_day]["month"])
                        subproblem_stage_timepoints[subproblem_id][
                            stage_id][timepoint]["hour_of_day"] = hour

    # Horizons
    subproblem_horizons = dict()
    for subproblem_id in subproblem_stages.keys():
        subproblem_horizons[subproblem_id] = dict()
        for period in periods.keys():
            for day in horizon_weights_and_months.keys():
                horizon = period * 10**2 + day
                subproblem_horizons[subproblem_id][horizon] = dict()
                subproblem_horizons[subproblem_id][horizon]["period"] = period
                subproblem_horizons[subproblem_id][horizon]["boundary"] = \
                    "circular"
                subproblem_horizons[subproblem_id][horizon][
                    "balancing_type_horizon"] = "day"

    # Timepoint horizons
    subproblem_stage_timepoint_horizons = dict()
    for subproblem_id in subproblem_stage_timepoints.keys():
        subproblem_stage_timepoint_horizons[subproblem_id] = dict()
        for stage_id in subproblem_stage_timepoints[subproblem_id].keys():
            subproblem_stage_timepoint_horizons[subproblem_id][stage_id] = \
                dict()
            for timepoint in subproblem_stage_timepoints[subproblem_id][
                    stage_id].keys():
                subproblem_stage_timepoint_horizons[subproblem_id][
                    stage_id][timepoint] = [(int(timepoint/10**2), 'day')]

    # Load data into GridPath database
    temporal.temporal(
            io=io, c=c2,
            temporal_scenario_id=1,
            scenario_name="default_4_periods_12_days_24_hours",
            scenario_description="2018, 2022, 2026, 2030; 12 average days, "
                                 "24 hours each",
            periods=periods,
            subproblems=[1],
            subproblem_stages={1: [(1, "single stage")]},
            subproblem_stage_timepoints=subproblem_stage_timepoints,
            subproblem_horizons=subproblem_horizons,
            subproblem_stage_timepoint_horizons=subproblem_stage_timepoint_horizons
    )






    #### REDO WITH DATA FRAMES SO WE CAN IMPORT FROM CSVS ####
    # Subproblems and stages (one subproblem, one stage)
    subproblems = [1]
    subproblem_stages = {sid: [(1, "single stage")] for sid in subproblems}

    global subproblem_stages_df
    subproblem_stages_df = pd.DataFrame()
    subproblem_stages_df['subproblem_id'] = [1, 1]
    subproblem_stages_df['stage_id'] = [1, 2]
    subproblem_stages_df['stage_name'] = ['single stage', 'd']

    subproblem_stages_df = subproblem_stages_df.set_index("subproblem_id")
    subproblem_stages = subproblem_stages_df.to_dict(orient='index')

    global subproblem_stage_timepoints_df
    subproblem_stage_timepoints_df = pd.DataFrame()

    # Get length of the maximum horizon to feed into length of timepoint. e.g. for 365 day horizons, length is 3.
    max_length_horizon = len(str(max(horizon_weights_and_months.keys())))
    number_of_timepoints_per_day = int(24 / number_of_hours_in_timepoint)

    for index, row in subproblem_stage_df.iterrows():
        print(row['subproblem_id'])
        subproblem_id = row['subproblem_id']
        stage_id = row['stage_id']
        for _period in periods_df['period'].to_list():
            print(_period)
            for _day in horizon_weights_and_months.keys():
                # tmp is timepoint within a day
                for tmp in range(1, 2):
                    print(tmp)
                    subproblem_stage_timepoints_df_p = pd.DataFrame()
                    subproblem_stage_timepoints_df_p['subproblem_id'] = subproblem_id
                    subproblem_stage_timepoints_df_p['stage_id'] = stage_id

                    subproblem_stage_timepoints_df = subproblem_stage_timepoints_df.append(subproblem_stage_timepoints_df_p,
                                                                                 ignore_index=True)


                    # Multiply by 5 if horizons are 3 digit e.g. for production cost models; else 4
                    subproblem_stage_timepoints_df_p['timepoint'] = _period * 10 ** 4 + \
                                                              _day * 10 ** 2 + tmp
                    subproblem_stage_timepoints_df_p['period'] = _period
                    subproblem_stage_timepoints_df_p[
                        "number_of_hours_in_timepoint"] = number_of_hours_in_timepoint
                    subproblem_stage_timepoints_df_p["timepoint_weight"] = horizon_weights_and_months[_day]["weight"]
                    subproblem_stage_timepoints_df_p["previous_stage_timepoint_map"] = None
                    subproblem_stage_timepoints_df_p["spinup_or_lookahead"] = None
                    subproblem_stage_timepoints_df_p["month"] = \
                        int(horizon_weights_and_months[_day]["month"])
                    subproblem_stage_timepoints_df_p["hour_of_day"] = int((tmp - 1) * number_of_hours_in_timepoint) + 1
                    subproblem_stage_timepoints_df = subproblem_stage_timepoints_df.append(subproblem_stage_timepoints_df_p,
                                                                                 ignore_index=True)





            subproblem_stage_timepoints_df_p = pd.DataFrame()
            subproblem_stage_timepoints_df_p['subproblem_id'] = np.repeat(p, horizons_per_year * 24 * timepoints_per_hour)
            subproblem_stage_timepoints_df_p['stage_id'] = np.repeat(p, horizons_per_year * 24 * timepoints_per_hour)
            # Multiply by 5 if horizons are 3 digit e.g. for production cost models; else 4
            subproblem_stage_timepoints_df_p['tmp'] = subproblem_stage_timepoints_df_p['period'] * 10 ** 4 + \
                                                 subproblem_stage_timepoints_df_p['horizonstep'] * 10 ** 2 + \
                                                 subproblem_stage_timepoints_df_p['timestep']


            subproblem_stage_timepoints_df_p['period'] = np.repeat(p, horizons_per_year * 24 * timepoints_per_hour)




            subproblem_stage_timepoints_df_p['horizonstep'] = np.repeat(range(1, horizons_per_year + 1, 1),
                                                                   24 * timepoints_per_hour)
            # Multiply by 3 if horizons are 3 digit e.g. for production cost models; else 2
            subproblem_stage_timepoints_df_p['horizon'] = subproblem_stage_timepoints_df_p['period'] * 10 ** 2 + \
                                                     subproblem_stage_timepoints_df_p['horizonstep']
            subproblem_stage_timepoints_df_p['timestep'] = np.tile(range(1, 24 * timepoints_per_hour + 1, 1),
                                                              horizons_per_year)
            # Multiply by 5 if horizons are 3 digit e.g. for production cost models; else 4
            subproblem_stage_timepoints_df_p['tmp'] = subproblem_stage_timepoints_df_p['period'] * 10 ** 4 + \
                                                 subproblem_stage_timepoints_df_p['horizonstep'] * 10 ** 2 + \
                                                 subproblem_stage_timepoints_df_p['timestep']
            period_horizon_timepoints = period_horizon_timepoints.append(subproblem_stage_timepoints_df_p, ignore_index=True)

    #### REDO WITH DATAFRAMES ####



    ## Create period, horizon, timepoint dataframe
    global period_horizon_timepoints
    period_horizon_timepoints = pd.DataFrame()

    for p in periods_df['period'].to_list():
        print(p)
        period_horizon_timepoints_p = pd.DataFrame()
        period_horizon_timepoints_p['period'] = np.repeat(p, horizons_per_year * 24 * timepoints_per_hour)
        period_horizon_timepoints_p['horizonstep'] = np.repeat(range(1, horizons_per_year + 1, 1),
                                                               24 * timepoints_per_hour)
        # Multiply by 3 if horizons are 3 digit e.g. for production cost models; else 2
        period_horizon_timepoints_p['horizon'] = period_horizon_timepoints_p['period'] * 10 ** 2 + \
                                                 period_horizon_timepoints_p['horizonstep']
        period_horizon_timepoints_p['timestep'] = np.tile(range(1, 24 * timepoints_per_hour + 1, 1), horizons_per_year)
        # Multiply by 5 if horizons are 3 digit e.g. for production cost models; else 4
        period_horizon_timepoints_p['tmp'] = period_horizon_timepoints_p['period'] * 10 ** 4 + \
                                             period_horizon_timepoints_p['horizonstep'] * 10 ** 2 + \
                                             period_horizon_timepoints_p['timestep']
        period_horizon_timepoints = period_horizon_timepoints.append(period_horizon_timepoints_p, ignore_index=True)

    ## Create period, horizon dataframe
    global period_horizon
    period_horizon = pd.DataFrame()
    for p in periods_df['period'].to_list():
        print(p)
        period_horizon_p = pd.DataFrame()
        period_horizon_p['period'] = np.repeat(p, horizons_per_year)
        period_horizon_p['horizonstep'] = range(1, horizons_per_year + 1, 1)
        period_horizon_p['horizon'] = period_horizon_p['period'] * 10 ** 2 + \
                                      period_horizon_p['horizonstep']
        period_horizon = period_horizon.append(period_horizon_p, ignore_index=True)









# Default subscenario IDs for
defaults = {
    "of_fuels": 1,
    "of_multi_stage": 0,
    "of_transmission": 0,
    "of_transmission_hurdle_rates": 0,
    "of_simultaneous_flow_limits": 0,
    "of_lf_reserves_up": 0,
    "of_lf_reserves_down": 0,
    "of_regulation_up": 0,
    "of_regulation_down": 0,
    "of_frequency_response": 0,
    "of_spinning_reserves": 0,
    "of_rps": 1,
    "of_carbon_cap": 0,
    "of_track_carbon_imports": 0,
    "of_prm": 0,
    "of_local_capacity": 0,
    "of_elcc_surface": 0,
    "temporal_scenario_id": 1,
    "load_zone_scenario_id": 1,
    "lf_reserves_up_ba_scenario_id": 'NULL',
    "lf_reserves_down_ba_scenario_id": 'NULL',
    "regulation_up_ba_scenario_id": 'NULL',
    "regulation_down_ba_scenario_id": 'NULL',
    "frequency_response_ba_scenario_id": 'NULL',
    "spinning_reserves_ba_scenario_id": 'NULL',
    "rps_zone_scenario_id": 1,
    "carbon_cap_zone_scenario_id": 'NULL',
    "prm_zone_scenario_id": 'NULL',
    "local_capacity_zone_scenario_id": 'NULL',
    "project_portfolio_scenario_id": 1,
    "project_operational_chars_scenario_id": 1,
    "project_availability_scenario_id": 'NULL',
    "fuel_scenario_id": 1,
    "project_load_zone_scenario_id": 1,
    "project_lf_reserves_up_ba_scenario_id": 'NULL',
    "project_lf_reserves_down_ba_scenario_id": 'NULL',  # Allow renewables
    "project_regulation_up_ba_scenario_id": 'NULL',
    "project_regulation_down_ba_scenario_id": 'NULL',
    "project_frequency_response_ba_scenario_id": 'NULL',
    "project_spinning_reserves_ba_scenario_id": 'NULL',
    "project_rps_zone_scenario_id": 1,
    "project_carbon_cap_zone_scenario_id": 'NULL',
    "project_prm_zone_scenario_id": 'NULL',
    "project_elcc_chars_scenario_id": 'NULL',
    "prm_energy_only_scenario_id": 'NULL',
    "project_local_capacity_zone_scenario_id": 'NULL',
    "project_local_capacity_chars_scenario_id": 'NULL',
    "project_existing_capacity_scenario_id": 1,
    "project_existing_fixed_cost_scenario_id": 1,
    "fuel_price_scenario_id": 1,
    "project_new_cost_scenario_id": 1,
    "project_new_potential_scenario_id": 1,
    "transmission_portfolio_scenario_id": 'NULL',
    "transmission_load_zone_scenario_id": 'NULL',
    "transmission_existing_capacity_scenario_id": 'NULL',
    "transmission_operational_chars_scenario_id": 'NULL',
    "transmission_hurdle_rate_scenario_id": 'NULL',
    "transmission_carbon_cap_zone_scenario_id": 'NULL',
    "transmission_simultaneous_flow_limit_scenario_id": 'NULL',
    "transmission_simultaneous_flow_limit_line_group_scenario_id": 'NULL',
    "load_scenario_id": 1,
    "lf_reserves_up_scenario_id": 'NULL',
    "lf_reserves_down_scenario_id": 'NULL',
    "regulation_up_scenario_id": 'NULL',
    "regulation_down_scenario_id": 'NULL',
    "frequency_response_scenario_id": 'NULL',
    "spinning_reserves_scenario_id": 'NULL',
    "rps_target_scenario_id": 1,
    "carbon_cap_target_scenario_id": 'NULL',
    "prm_requirement_scenario_id": 'NULL',
    "elcc_surface_scenario_id": 'NULL',
    "local_capacity_requirement_scenario_id": 'NULL',
    "tuning_scenario_id": 0  # No tuning
}


def create_scenarios():
    """

    :return:
    """

    # Create 'Base_42MMT' scenario
    create_scenario.create_scenario(
        io=io, c=c2,
        scenario_name=main_sc,
        of_fuels=defaults["of_fuels"],
        of_multi_stage=defaults["of_multi_stage"],
        of_transmission=defaults["of_transmission"],
        of_transmission_hurdle_rates=defaults["of_transmission_hurdle_rates"],
        of_simultaneous_flow_limits=defaults["of_simultaneous_flow_limits"],
        of_lf_reserves_up=defaults["of_lf_reserves_up"],
        of_lf_reserves_down=defaults["of_lf_reserves_down"],
        of_regulation_up=defaults["of_regulation_up"],
        of_regulation_down=defaults["of_regulation_down"],
        of_frequency_response=defaults["of_frequency_response"],
        of_spinning_reserves=defaults["of_spinning_reserves"],
        of_rps=defaults["of_rps"],
        of_carbon_cap=defaults["of_carbon_cap"],
        of_track_carbon_imports=defaults["of_track_carbon_imports"],
        of_prm=defaults["of_prm"],
        of_local_capacity=defaults["of_local_capacity"],
        of_elcc_surface=defaults["of_elcc_surface"],
        temporal_scenario_id=defaults["temporal_scenario_id"],
        load_zone_scenario_id=defaults["load_zone_scenario_id"],
        lf_reserves_up_ba_scenario_id=
        defaults["lf_reserves_up_ba_scenario_id"],
        lf_reserves_down_ba_scenario_id=
        defaults["lf_reserves_down_ba_scenario_id"],
        regulation_up_ba_scenario_id=defaults["regulation_up_ba_scenario_id"],
        regulation_down_ba_scenario_id=
        defaults["regulation_down_ba_scenario_id"],
        frequency_response_ba_scenario_id=
        defaults["frequency_response_ba_scenario_id"],
        spinning_reserves_ba_scenario_id=
        defaults["spinning_reserves_ba_scenario_id"],
        rps_zone_scenario_id=defaults["rps_zone_scenario_id"],
        carbon_cap_zone_scenario_id=defaults["carbon_cap_zone_scenario_id"],
        prm_zone_scenario_id=defaults["prm_zone_scenario_id"],
        local_capacity_zone_scenario_id=defaults[
            "local_capacity_zone_scenario_id"],
        project_portfolio_scenario_id=
        defaults["project_portfolio_scenario_id"],
        project_operational_chars_scenario_id=
        defaults["project_operational_chars_scenario_id"],
        project_availability_scenario_id=
        defaults["project_availability_scenario_id"],
        fuel_scenario_id=defaults["fuel_scenario_id"],
        project_load_zone_scenario_id=
        defaults["project_load_zone_scenario_id"],
        project_lf_reserves_up_ba_scenario_id=
        defaults["project_lf_reserves_up_ba_scenario_id"],
        project_lf_reserves_down_ba_scenario_id=
        defaults["project_lf_reserves_down_ba_scenario_id"],
        project_regulation_up_ba_scenario_id=
        defaults["project_regulation_up_ba_scenario_id"],
        project_regulation_down_ba_scenario_id=
        defaults["project_regulation_down_ba_scenario_id"],
        project_frequency_response_ba_scenario_id=
        defaults["project_frequency_response_ba_scenario_id"],
        project_spinning_reserves_ba_scenario_id=
        defaults["project_spinning_reserves_ba_scenario_id"],
        project_rps_zone_scenario_id=defaults["project_rps_zone_scenario_id"],
        project_carbon_cap_zone_scenario_id=
        defaults["project_carbon_cap_zone_scenario_id"],
        project_prm_zone_scenario_id=defaults["project_prm_zone_scenario_id"],
        project_elcc_chars_scenario_id=
        defaults["project_elcc_chars_scenario_id"],
        prm_energy_only_scenario_id=
        defaults["prm_energy_only_scenario_id"],
        project_local_capacity_zone_scenario_id=defaults[
            "project_local_capacity_zone_scenario_id"],
        project_local_capacity_chars_scenario_id=
        defaults["project_local_capacity_chars_scenario_id"],
        project_existing_capacity_scenario_id=
        defaults["project_existing_capacity_scenario_id"],
        project_existing_fixed_cost_scenario_id=
        defaults["project_existing_fixed_cost_scenario_id"],
        fuel_price_scenario_id=defaults["fuel_price_scenario_id"],
        project_new_cost_scenario_id=project_new_cost_scenario_id, # defaults["project_new_cost_scenario_id"]
        project_new_potential_scenario_id=
        defaults["project_new_potential_scenario_id"],
        transmission_portfolio_scenario_id=
        defaults["transmission_portfolio_scenario_id"],
        transmission_load_zone_scenario_id=
        defaults["transmission_load_zone_scenario_id"],
        transmission_existing_capacity_scenario_id=
        defaults["transmission_existing_capacity_scenario_id"],
        transmission_operational_chars_scenario_id=
        defaults["transmission_operational_chars_scenario_id"],
        transmission_hurdle_rate_scenario_id=
        defaults["transmission_hurdle_rate_scenario_id"],
        transmission_carbon_cap_zone_scenario_id=
        defaults["transmission_carbon_cap_zone_scenario_id"],
        transmission_simultaneous_flow_limit_scenario_id=
        defaults["transmission_simultaneous_flow_limit_scenario_id"],
        transmission_simultaneous_flow_limit_line_group_scenario_id=
        defaults[
            "transmission_simultaneous_flow_limit_line_group_scenario_id"],
        load_scenario_id=defaults["load_scenario_id"],
        lf_reserves_up_scenario_id=defaults["lf_reserves_up_scenario_id"],
        lf_reserves_down_scenario_id=defaults["lf_reserves_down_scenario_id"],
        regulation_up_scenario_id=defaults["regulation_up_scenario_id"],
        regulation_down_scenario_id=defaults["regulation_down_scenario_id"],
        frequency_response_scenario_id=
        defaults["frequency_response_scenario_id"],
        spinning_reserves_scenario_id=
        defaults["spinning_reserves_scenario_id"],
        rps_target_scenario_id=rps_target_scenario_id, #defaults["rps_target_scenario_id"]
        carbon_cap_target_scenario_id=defaults["carbon_cap_target_scenario_id"],
        prm_requirement_scenario_id=defaults["prm_requirement_scenario_id"],
        elcc_surface_scenario_id=defaults["elcc_surface_scenario_id"],
        local_capacity_requirement_scenario_id=defaults[
            "local_capacity_requirement_scenario_id"],
        tuning_scenario_id=defaults["tuning_scenario_id"]
    )





load_temporal_data()
load_geography_load_zones()
load_geography_rps_zones()
create_projects_data()
create_hydro_opchar()
create_loads()
load_loads()
load_projects(projects_all = projects_all)
load_project_load_zones(projects_all)
load_project_operational_chars(projects_all)
load_project_hr_curves()
load_project_variable_profiles()
load_project_hydro_opchar()
load_project_portfolios()
load_project_capacities()
load_project_new_potentials()
load_project_fixed_costs()
load_project_new_costs()
load_fuels()
load_fuel_prices()
load_project_rps_zones()
load_rps_targets()

tuning()

### scenarios ###
# RPS0_VRElow_SThigh_CONVhigh
# RPS0_VREhigh_SThigh_CONVhigh
# RPS0_VRElow_STlow_CONVhigh
# RPS0_VREhigh_STlow_CONVhigh
# RPS30_VRElow_SThigh_CONVhigh
# RPS30_VREhigh_SThigh_CONVhigh
# RPS30_VRElow_STlow_CONVhigh
# RPS30_VREhigh_STlow_CONVhigh
# RPS50_VRElow_SThigh_CONVhigh
# RPS50_VREhigh_SThigh_CONVhigh
# RPS50_VRElow_STlow_CONVhigh
# RPS50_VREhigh_STlow_CONVhigh
# RPS70_VRElow_SThigh_CONVhigh
# RPS70_VREhigh_SThigh_CONVhigh
# RPS70_VRElow_STlow_CONVhigh
# RPS70_VREhigh_STlow_CONVhigh

main_scenarios = pd.read_csv(main_scenarios_csv)

for main_sc in main_scenarios['main_scenario_name'].to_list():
    if main_scenarios.loc[main_scenarios['main_scenario_name'] == main_sc, 'include'].iloc[0] == 1:
        project_new_cost_scenario_id = main_scenarios.loc[main_scenarios['main_scenario_name'] == main_sc, 'project_new_cost_scenario_id'].iloc[0]
        rps_target_scenario_id = main_scenarios.loc[main_scenarios['main_scenario_name'] == main_sc, 'rps_target_scenario_id'].iloc[0]
        print(main_sc)
        create_scenarios()



# port_data_to_gridpath_project_modules.load_projects(projects_all = projects_all)
# port_data_to_gridpath_project_modules.load_project_load_zones(projects_all)
# port_data_to_gridpath_project_modules.load_project_operational_chars()
# port_data_to_gridpath_project_modules.load_project_variable_profiles()
#
# port_data_to_gridpath_project_modules.load_fuels()
# port_data_to_gridpath_project_modules.load_fuel_prices()
#
# port_data_to_gridpath_demand_modules.load_loads()
#

