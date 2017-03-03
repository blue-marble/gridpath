#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from argparse import ArgumentParser
import csv
import os.path
import sqlite3
import sys


arguments = sys.argv[1:]
parser = ArgumentParser(add_help=True)
parser.add_argument("--scenario_id", help="The scenario_id from the database.")
parsed_arguments = parser.parse_known_args(args=arguments)[0]

SCENARIO_ID = parsed_arguments.scenario_id

# Assume script is run from same directory a the database, which is named io.db
io = sqlite3.connect(
    os.path.join(os.getcwd(), 'io.db')
)
c = io.cursor()

# Get scenario name and make inputs directory
SCENARIO_NAME = c.execute(
    """SELECT scenario_name
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

SCENARIOS_MAIN_DIRECTORY = os.path.join(
    os.getcwd(), "..", "scenarios")
if not os.path.exists(SCENARIOS_MAIN_DIRECTORY):
    os.makedirs(SCENARIOS_MAIN_DIRECTORY)

SCENARIO_DIRECTORY = os.path.join(
    SCENARIOS_MAIN_DIRECTORY, str(SCENARIO_ID) + "_" + str(SCENARIO_NAME))
if not os.path.exists(SCENARIO_DIRECTORY):
    os.makedirs(SCENARIO_DIRECTORY)

INPUTS_DIRECTORY = os.path.join(
    SCENARIO_DIRECTORY, "inputs")
if not os.path.exists(INPUTS_DIRECTORY):
    os.makedirs(INPUTS_DIRECTORY)

# Get modules we'll be using
MODULE_LIST = list()

OPTIONAL_MODULE_FUELS = c.execute(
    """SELECT om_fuels
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_FUELS:
    MODULE_LIST.append("fuels")

OPTIONAL_MULTI_STAGE = c.execute(
    """SELECT om_multi_stage
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MULTI_STAGE:
    MODULE_LIST.append("multi_stage")

OPTIONAL_MODULE_TRANSMISSION = c.execute(
    """SELECT om_transmission
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_TRANSMISSION:
    MODULE_LIST.append("transmission")

OPTIONAL_MODULE_SIMULTANEOUS_FLOW_LIMITS = c.execute(
    """SELECT om_simultaneous_flow_limits
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_SIMULTANEOUS_FLOW_LIMITS:
    MODULE_LIST.append("simultaneous_flow_limits")

OPTIONAL_MODULE_LF_RESERVES_UP = c.execute(
    """SELECT om_lf_reserves_up
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_LF_RESERVES_UP:
    MODULE_LIST.append("lf_reserves_up")

OPTIONAL_MODULE_LF_RESERVES_DOWN = c.execute(
    """SELECT om_lf_reserves_down
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_LF_RESERVES_DOWN:
    MODULE_LIST.append("lf_reserves_down")

OPTIONAL_MODULE_REGULATION_UP = c.execute(
    """SELECT om_regulation_up
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_REGULATION_UP:
    MODULE_LIST.append("regulation_up")

OPTIONAL_MODULE_REGULATION_DOWN = c.execute(
    """SELECT om_regulation_down
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_REGULATION_DOWN:
    MODULE_LIST.append("regulation_down")

OPTIONAL_MODULE_RPS = c.execute(
    """SELECT om_rps
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_RPS:
    MODULE_LIST.append("rps")

OPTIONAL_MODULE_CARBON_CAP = c.execute(
    """SELECT om_carbon_cap
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_CARBON_CAP:
    MODULE_LIST.append("carbon_cap")

OPTIONAL_MODULE_TRACK_CARBON_IMPORTS = c.execute(
    """SELECT om_track_carbon_imports
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_TRACK_CARBON_IMPORTS:
    MODULE_LIST.append("track_carbon_imports")

# modules.csv
with open(os.path.join(SCENARIO_DIRECTORY, "modules.csv"), "w") as \
        modules_csv_file:
    writer = csv.writer(modules_csv_file, delimiter=",")

    # Write header
    writer.writerow(["modules"])

    for module in MODULE_LIST:
        writer.writerow([module])

# Get subscenarios
HORIZON_SCENARIO_ID = c.execute(
    """SELECT horizon_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

TIMEPOINT_SCENARIO_ID = c.execute(
    """SELECT timepoint_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

PERIOD_SCENARIO_ID = c.execute(
    """SELECT period_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

LOAD_ZONE_SCENARIO_ID = c.execute(
    """SELECT load_zone_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

LF_RESERVES_UP_BA_SCENARIO_ID = c.execute(
    """SELECT lf_reserves_up_ba_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

LF_RESERVES_DOWN_BA_SCENARIO_ID = c.execute(
    """SELECT lf_reserves_down_ba_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

RPS_ZONE_SCENARIO_ID = c.execute(
    """SELECT rps_zone_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

RPS_TARGET_SCENARIO_ID = c.execute(
    """SELECT rps_target_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

CARBON_CAP_ZONE_SCENARIO_ID = c.execute(
    """SELECT carbon_cap_zone_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

CARBON_CAP_TARGET_SCENARIO_ID = c.execute(
    """SELECT carbon_cap_target_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

PROJECT_LOAD_ZONE_SCENARIO_ID = c.execute(
    """SELECT project_load_zone_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

PROJECT_LF_RESERVES_UP_BA_SCENARIO_ID = c.execute(
    """SELECT project_lf_reserves_up_ba_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

PROJECT_LF_RESERVES_DOWN_BA_SCENARIO_ID = c.execute(
    """SELECT project_lf_reserves_down_ba_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

PROJECT_RPS_ZONE_SCENARIO_ID = c.execute(
    """SELECT project_rps_zone_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

PROJECT_CARBON_CAP_ZONE_SCENARIO_ID = c.execute(
    """SELECT project_carbon_cap_zone_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

EXISTING_PROJECT_SCENARIO_ID = c.execute(
    """SELECT existing_project_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

NEW_PROJECT_SCENARIO_ID = c.execute(
    """SELECT new_project_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

EXISTING_PROJECT_CAPACITY_SCENARIO_ID = c.execute(
    """SELECT existing_project_capacity_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

NEW_PROJECT_COST_SCENARIO_ID = c.execute(
    """SELECT new_project_cost_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

NEW_PROJECT_POTENTIAL_SCENARIO_ID = c.execute(
    """SELECT new_project_potential_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

FUEL_SCENARIO_ID = c.execute(
    """SELECT fuel_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

PROJECT_OPERATIONAL_CHARS_SCENARIO_ID = c.execute(
    """SELECT project_operational_chars_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

HYDRO_OPERATIONAL_CHARS_SCENARIO_ID = c.execute(
    """SELECT hydro_operational_chars_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

VARIABLE_GENERATOR_PROFILES_SCENARIO_ID = c.execute(
    """SELECT variable_generator_profiles_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

LOAD_SCENARIO_ID = c.execute(
    """SELECT load_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

LF_RESERVES_UP_SCENARIO_ID = c.execute(
    """SELECT lf_reserves_up_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

LF_RESERVES_DOWN_SCENARIO_ID = c.execute(
    """SELECT lf_reserves_down_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

TRANSMISSION_LINE_SCENARIO_ID = c.execute(
    """SELECT transmission_line_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

TRANSMISSION_LINE_EXISTING_CAPACITY_SCENARIO_ID = c.execute(
    """SELECT transmission_line_existing_capacity_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

TRANSMISSION_SIMULTANEOUS_FLOW_GROUP_LINES_SCENARIO_ID = c.execute(
    """SELECT transmission_simultaneous_flow_group_lines_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

TRANSMISSION_SIMULTANEOUS_FLOW_LIMIT_SCENARIO_ID = c.execute(
    """SELECT transmission_simultaneous_flow_limit_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

TRANSMISSION_LINE_CARBON_CAP_ZONE_SCENARIO_ID = c.execute(
    """SELECT transmission_line_carbon_cap_zone_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

# periods.tab
with open(os.path.join(INPUTS_DIRECTORY, "periods.tab"), "w") as \
        periods_tab_file:
    writer = csv.writer(periods_tab_file, delimiter="\t")

    # Write header
    writer.writerow(["PERIODS", "discount_factor", "number_years_represented"])

    periods = c.execute(
        """SELECT period, discount_factor, number_years_represented
           FROM periods
           WHERE period_scenario_id = {};""".format(
            PERIOD_SCENARIO_ID
        )
    ).fetchall()

    for row in periods:
        writer.writerow(row)

# horizons.tab
with open(os.path.join(INPUTS_DIRECTORY, "horizons.tab"), "w") as \
        horizons_tab_file:
    writer = csv.writer(horizons_tab_file, delimiter="\t")

    # Write header
    writer.writerow(["HORIZONS", "boundary", "horizon_weight"])

    horizons = c.execute(
        """SELECT horizon, boundary, horizon_weight
           FROM horizons
           WHERE period_scenario_id = {}
           AND horizon_scenario_id = {};""".format(
            PERIOD_SCENARIO_ID, HORIZON_SCENARIO_ID
        )
    ).fetchall()

    for row in horizons:
        writer.writerow(row)

# timepoints.tab
with open(os.path.join(INPUTS_DIRECTORY, "timepoints.tab"), "w") as \
        timepoints_tab_file:
    writer = csv.writer(timepoints_tab_file, delimiter="\t")

    # Write header
    writer.writerow(["TIMEPOINTS", "period", "horizon",
                     "number_of_hours_in_timepoint"])

    timepoints = c.execute(
        """SELECT timepoint, period, horizon, number_of_hours_in_timepoint
           FROM timepoints
           WHERE period_scenario_id = {}
           AND horizon_scenario_id = {}
           AND timepoint_scenario_id = {};""".format(
            HORIZON_SCENARIO_ID, PERIOD_SCENARIO_ID, TIMEPOINT_SCENARIO_ID
        )
    ).fetchall()

    for row in timepoints:
        writer.writerow(row)

# load_zones.tab
with open(os.path.join(INPUTS_DIRECTORY, "load_zones.tab"), "w") as \
        load_zones_tab_file:
    writer = csv.writer(load_zones_tab_file, delimiter="\t")

    # Write header
    writer.writerow(["load_zone", "overgeneration_penalty_per_mw",
                     "unserved_energy_penalty_per_mw"])

    load_zones = c.execute(
        """SELECT load_zone, overgeneration_penalty_per_mw,
           unserved_energy_penalty_per_mw
           FROM load_zones
           WHERE load_zone_scenario_id = {};""".format(
            LOAD_ZONE_SCENARIO_ID
        )
    ).fetchall()

    for row in load_zones:
        writer.writerow(row)

# load_following_up_balancing_areas.tab
# part of optional lf_reserves_up module
if OPTIONAL_MODULE_LF_RESERVES_UP:
    with open(os.path.join(INPUTS_DIRECTORY,
                           "load_following_up_balancing_areas.tab"),
              "w") as \
            lf_up_bas_tab_file:
        writer = csv.writer(lf_up_bas_tab_file, delimiter="\t")

        # Write header
        writer.writerow(["balancing_area",
                         "violation_penalty_per_mw"])

        lf_up_bas = c.execute(
            """SELECT lf_reserves_up_ba, lf_reserves_up_violation_penalty_per_mw
               FROM lf_reserves_up_bas
               WHERE lf_reserves_up_ba_scenario_id = {};""".format(
                LF_RESERVES_UP_BA_SCENARIO_ID
            )
        ).fetchall()

        for row in lf_up_bas:
            writer.writerow(row)

# load_following_down_balancing_areas.tab
# part of optional lf_reserves_down module
if OPTIONAL_MODULE_LF_RESERVES_DOWN:
    with open(os.path.join(INPUTS_DIRECTORY,
                           "load_following_down_balancing_areas.tab"),
              "w") as \
            lf_down_bas_tab_file:
        writer = csv.writer(lf_down_bas_tab_file, delimiter="\t")

        # Write header
        writer.writerow(["balancing_area",
                         "violation_penalty_per_mw"])

        lf_down_bas = c.execute(
            """SELECT lf_reserves_down_ba,
            lf_reserves_down_violation_penalty_per_mw
               FROM lf_reserves_down_bas
               WHERE lf_reserves_down_ba_scenario_id = {};""".format(
                LF_RESERVES_DOWN_BA_SCENARIO_ID
            )
        ).fetchall()

        for row in lf_down_bas:
            writer.writerow(row)

# rps_zones.tab
# part of optional rps module
if OPTIONAL_MODULE_RPS:
    with open(os.path.join(INPUTS_DIRECTORY, "rps_zones.tab"),
              "w") as \
            rps_zones_tab_file:
        writer = csv.writer(rps_zones_tab_file, delimiter="\t")

        # Write header
        writer.writerow(["rps_zone"])

        rps_zones = c.execute(
            """SELECT rps_zone
               FROM rps_zones
               WHERE rps_zone_scenario_id = {};""".format(
                RPS_ZONE_SCENARIO_ID
            )
        ).fetchall()

        for row in rps_zones:
            writer.writerow(row)


# TODO: how to handle optional columns (e.g. lf_reserves_up_ba, rps_zone, etc.)
# TODO: add heat rate for new advanced ccgt and aero ct
# TODO: if fuel specified, can't have '.' -- must be 0 instead
# TODO: why is there a startup cost for CAISO_Nuclear and CAISO_CHP
# projects.tab
prj_db_table_optional_select = dict()
prj_file_optional_headers = list()
if OPTIONAL_MODULE_LF_RESERVES_UP:
    prj_db_table_optional_select["lf_reserves_up"] = {
        "db_column_name": ", lf_reserves_up_ba",
        "db_join_statement": "\nJOIN project_lf_reserves_up_bas "
                             "USING (existing_project_scenario_id, "
                             "new_project_scenario_id, project) ",
        "db_and_statement": "\nAND lf_reserves_up_ba_scenario_id = {} "
                            "AND project_lf_reserves_up_ba_scenario_id = {}"
        }
    prj_file_optional_headers.append("lf_reserves_up_zone")
else:
    prj_db_table_optional_select["lf_reserves_up"] = {
        "db_column_name": "",
        "db_join_statement": ""
        }
    
if OPTIONAL_MODULE_LF_RESERVES_DOWN:
    prj_db_table_optional_select["lf_reserves_down"] = {
        "db_column_name": ", lf_reserves_down_ba",
        "db_join_statement": "\nJOIN project_lf_reserves_down_bas "
                               "USING (existing_project_scenario_id, "
                               "new_project_scenario_id, project) ",
        "db_and_statement": "\nAND lf_reserves_down_ba_scenario_id = {} "
                            "AND project_lf_reserves_down_ba_scenario_id = "
                            "{}"
        }
    prj_file_optional_headers.append("lf_reserves_down_zone")
else:
    prj_db_table_optional_select["lf_reserves_down"] = {
        "db_column_name": "",
        "db_join_statement": ""
        }

if OPTIONAL_MODULE_RPS:
    prj_db_table_optional_select["rps"] = {
        "db_column_name": ", rps_zone",
        "db_join_statement": "\nJOIN project_rps_zones "
                             "USING (existing_project_scenario_id, "
                             "new_project_scenario_id, project) ",
        "db_and_statement": "\nAND rps_zone_scenario_id = {} "
                            "AND project_rps_zone_scenario_id = {}"
    }
    prj_file_optional_headers.append("rps_zone")
else:
    prj_db_table_optional_select["rps"] = {
        "db_column_name": "",
        "db_join_statement": ""
    }

if OPTIONAL_MODULE_CARBON_CAP:
    prj_db_table_optional_select["carbon_cap"] = {
        "db_column_name": ", carbon_cap_zone",
        "db_join_statement": "\nJOIN project_carbon_cap_zones "
                             "USING (existing_project_scenario_id, "
                             "new_project_scenario_id, project) ",
        "db_and_statement": "\nAND carbon_cap_zone_scenario_id = {} "
                            "AND project_carbon_cap_zone_scenario_id = {}"
    }
    prj_file_optional_headers.append("carbon_cap_zone")
else:
    prj_db_table_optional_select["carbon_cap"] = {
        "db_column_name": "",
        "db_join_statement": ""
    }


with open(os.path.join(INPUTS_DIRECTORY, "projects.tab"), "w") as \
        projects_tab_file:
    writer = csv.writer(projects_tab_file, delimiter="\t")

    # Write header
    writer.writerow(
        ["project", "load_zone",
         "capacity_type", "operational_type", "fuel",
         "minimum_input_mmbtu_per_hr", "inc_heat_rate_mmbtu_per_mwh",
         "min_stable_level_fraction", "unit_size_mw", "startup_cost",
         "shutdown_cost", "min_up_time_hours", "min_down_time_hours",
         "charging_efficiency", "discharging_efficiency",
         "minimum_duration_hours", "variable_om_cost_per_mwh", "technology"]
        + prj_file_optional_headers
    )

    query = \
        """SELECT project, load_zone, capacity_type, operational_type, fuel,
        minimum_input_mmbtu_per_hr, inc_heat_rate_mmbtu_per_mwh,
        min_stable_level, unit_size_mw, startup_cost, shutdown_cost,
        min_up_time_hours, min_down_time_hours,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours, variable_cost_per_mwh, technology""" + \
        prj_db_table_optional_select["lf_reserves_up"]["db_column_name"] + \
        prj_db_table_optional_select["lf_reserves_down"]["db_column_name"] +\
        prj_db_table_optional_select["rps"]["db_column_name"] + \
        prj_db_table_optional_select["carbon_cap"]["db_column_name"] +\
        """ FROM all_projects
        JOIN project_operational_chars
        USING (project)
        JOIN project_load_zones
        USING (existing_project_scenario_id, new_project_scenario_id,
        project)""" + \
        prj_db_table_optional_select["lf_reserves_up"]["db_join_statement"] + \
        prj_db_table_optional_select["lf_reserves_down"][
            "db_join_statement"] \
        + \
        prj_db_table_optional_select["rps"]["db_join_statement"] + \
        prj_db_table_optional_select["carbon_cap"]["db_join_statement"] + \
        """
        WHERE load_zone_scenario_id = {}
        AND existing_project_scenario_id = {}
        AND new_project_scenario_id = {}
        AND project_operational_chars_scenario_id = {}
        AND project_load_zone_scenario_id = {}""" + \
        prj_db_table_optional_select["lf_reserves_up"]["db_and_statement"] + \
        prj_db_table_optional_select["lf_reserves_down"]["db_and_statement"] \
        + \
        prj_db_table_optional_select["rps"]["db_and_statement"] + \
        prj_db_table_optional_select["carbon_cap"]["db_and_statement"] + \
        """;"""

    projects = c.execute(query.format(
            LOAD_ZONE_SCENARIO_ID,
            EXISTING_PROJECT_SCENARIO_ID,
            NEW_PROJECT_SCENARIO_ID,
            PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            PROJECT_LOAD_ZONE_SCENARIO_ID,
            LF_RESERVES_UP_BA_SCENARIO_ID,
            PROJECT_LF_RESERVES_UP_BA_SCENARIO_ID,
            LF_RESERVES_DOWN_BA_SCENARIO_ID,
            PROJECT_LF_RESERVES_DOWN_BA_SCENARIO_ID,
            RPS_ZONE_SCENARIO_ID,
            PROJECT_RPS_ZONE_SCENARIO_ID,
            CARBON_CAP_ZONE_SCENARIO_ID,
            PROJECT_CARBON_CAP_ZONE_SCENARIO_ID
        )
    ).fetchall()


    for row in projects:
        replace_nulls = ["." if i is None else i for i in row]
        writer.writerow(replace_nulls)

# existing_generation_period_params.tab
with open(os.path.join(INPUTS_DIRECTORY,
                       "existing_generation_period_params.tab"), "w") as \
        existing_project_capacity_tab_file:
    writer = csv.writer(existing_project_capacity_tab_file, delimiter="\t")

    # Write header
    writer.writerow(
        ["GENERATORS", "PERIODS", "existing_capacity_mw",
         "fixed_cost_per_mw_yr"]
    )

    ep_capacities = c.execute(
        """SELECT project, period, existing_capacity_mw,
        annual_fixed_cost_per_mw_year
        FROM existing_project_capacity
        WHERE existing_project_scenario_id = {}
        AND period_scenario_id = {}
        AND existing_project_capacity_scenario_id = {};""".format(
            EXISTING_PROJECT_SCENARIO_ID, PERIOD_SCENARIO_ID,
            EXISTING_PROJECT_CAPACITY_SCENARIO_ID
        )
    )
    for row in ep_capacities:
        writer.writerow(row)

# storage_specified_capacities.tab
with open(os.path.join(INPUTS_DIRECTORY,
                       "storage_specified_capacities.tab"), "w") as \
        storage_specified_capacities_tab_file:
    writer = csv.writer(storage_specified_capacities_tab_file, delimiter="\t")

    # Write header
    writer.writerow(
        ["storage_project", "period",
         "storage_specified_power_capacity_mw",
         "storage_specified_energy_capacity_mwh"]
    )

    # TODO: more robust way to get storage projects than selecting non-null
    # rows
    stor_capacities = c.execute(
        """SELECT project, period, existing_capacity_mw, existing_capacity_mwh,
        annual_fixed_cost_per_mw_year, annual_fixed_cost_per_mwh_year
        FROM existing_project_capacity
        WHERE existing_project_scenario_id = {}
        AND period_scenario_id = {}
        AND existing_project_capacity_scenario_id = {}
        AND existing_capacity_mwh IS NOT NULL;""".format(
            EXISTING_PROJECT_SCENARIO_ID, PERIOD_SCENARIO_ID,
            EXISTING_PROJECT_CAPACITY_SCENARIO_ID
        )
    )
    for row in stor_capacities:
        writer.writerow(row)

# new_build_generator_vintage_costs.tab
with open(os.path.join(INPUTS_DIRECTORY,
                       "new_build_generator_vintage_costs.tab"), "w") as \
        new_gen_costs_tab_file:
    writer = csv.writer(new_gen_costs_tab_file, delimiter="\t")

    # Write header
    writer.writerow(
        ["new_build_generator", "vintage", "lifetime_yrs",
         "annualized_real_cost_per_mw_yr", "min_cumulative_new_build_mw",
         "max_cumulative_new_build_mw"]
    )

    # TODO: select only rows with NULL for cost per kWh-yr for generators
    # only (i.e to exclude storage), but need to make this more robust
    new_gen_costs = c.execute(
        """SELECT project, period, lifetime_yrs,
        annualized_real_cost_per_kw_yr * 1000,
        minimum_cumulative_new_build_mw, maximum_cumulative_new_build_mw
        FROM new_project_cost
        JOIN new_project_potential
        USING (new_project_scenario_id, period_scenario_id, project, period)
        WHERE annualized_real_cost_per_kwh_yr IS NULL
        AND new_project_scenario_id = {}
        AND period_scenario_id = {}
        AND new_project_cost_scenario_id = {}
        AND new_project_potential_scenario_id = {};""".format(
            NEW_PROJECT_SCENARIO_ID, PERIOD_SCENARIO_ID,
            NEW_PROJECT_COST_SCENARIO_ID,
            NEW_PROJECT_POTENTIAL_SCENARIO_ID
        )
    )
    for row in new_gen_costs:
        replace_nulls = ["." if i is None else i for i in row]
        writer.writerow(replace_nulls)

# new_build_storage_vintage_costs.tab
with open(os.path.join(INPUTS_DIRECTORY,
                       "new_build_storage_vintage_costs.tab"), "w") as \
        new_storage_costs_tab_file:
    writer = csv.writer(new_storage_costs_tab_file, delimiter="\t")

    # Write header
    writer.writerow(
        ["new_build_storage", "vintage", "lifetime_yrs",
         "annualized_real_cost_per_mw_yr", "annualized_real_cost_per_mwh_yr"]
    )

    # TODO: select only rows with non NULL for cost per kWh-yr for storage
    # only (not generators), but need to make this more robust
    new_stor_costs = c.execute(
        """SELECT project, period, lifetime_yrs,
        annualized_real_cost_per_kw_yr * 1000,
        annualized_real_cost_per_kwh_yr * 1000
        FROM new_project_cost
        WHERE annualized_real_cost_per_kwh_yr IS NOT NULL
        AND new_project_scenario_id = {}
        AND period_scenario_id = {}
        AND new_project_cost_scenario_id = {};""".format(
            NEW_PROJECT_SCENARIO_ID, PERIOD_SCENARIO_ID,
            NEW_PROJECT_COST_SCENARIO_ID
        )
    )
    for row in new_stor_costs:
        writer.writerow(row)

# fuels.tab
with open(os.path.join(INPUTS_DIRECTORY,
                       "fuels.tab"), "w") as \
        fuels_tab_file:
    writer = csv.writer(fuels_tab_file, delimiter="\t")

    # Write header
    writer.writerow(
        ["FUELS", "fuel_price_per_mmbtu", "co2_intensity_tons_per_mmbtu"]
    )

    fuels = c.execute(
        """SELECT fuel, fuel_price_per_mmbtu, co2_intensity_tons_per_mmbtu
        FROM fuels
        WHERE fuel_scenario_id = {}""".format(
            FUEL_SCENARIO_ID
        )
    )
    for row in fuels:
        writer.writerow(row)

# hydro_conventional_horizon_params.tab
with open(os.path.join(INPUTS_DIRECTORY,
                       "hydro_conventional_horizon_params.tab"), "w") as \
        hydro_chars_tab_file:
    writer = csv.writer(hydro_chars_tab_file, delimiter="\t")

    # Write header
    writer.writerow(
        ["hydro_project", "horizon", "hydro_specified_average_power_mwa",
         "hydro_specified_min_power_mw", "hydro_specified_max_power_mw"]
    )

    hydro_chars = c.execute(
        """SELECT project, horizon, average_power_mwa, min_power_mw,
        max_power_mw
        FROM hydro_operational_chars
        WHERE existing_project_scenario_id = {}
        AND period_scenario_id = {}
        AND horizon_scenario_id = {}
        AND hydro_operational_chars_scenario_id = {}
        """.format(
            EXISTING_PROJECT_SCENARIO_ID,
            PERIOD_SCENARIO_ID, HORIZON_SCENARIO_ID,
            HYDRO_OPERATIONAL_CHARS_SCENARIO_ID
        )
    )
    for row in hydro_chars:
        writer.writerow(row)

# variable_generator_profiles.tab
with open(os.path.join(INPUTS_DIRECTORY,
                       "variable_generator_profiles.tab"), "w") as \
        variable_profiles_tab_file:
    writer = csv.writer(variable_profiles_tab_file, delimiter="\t")

    # Write header
    writer.writerow(
        ["GENERATORS", "TIMEPOINTS", "cap_factor"]
    )

    variable_profiles = c.execute(
        """SELECT project, timepoint, cap_factor
        FROM variable_generator_profiles
        WHERE existing_project_scenario_id = {}
        AND new_project_scenario_id = {}
        AND project_operational_chars_scenario_id = {}
        AND period_scenario_id = {}
        AND horizon_scenario_id = {}
        AND timepoint_scenario_id = {}
        AND variable_generator_profiles_scenario_id = {}
        """.format(
            EXISTING_PROJECT_SCENARIO_ID, NEW_PROJECT_SCENARIO_ID,
            PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            PERIOD_SCENARIO_ID, HORIZON_SCENARIO_ID, TIMEPOINT_SCENARIO_ID,
            VARIABLE_GENERATOR_PROFILES_SCENARIO_ID
        )
    )
    for row in variable_profiles:
        writer.writerow(row)

# load_mw.tab
with open(os.path.join(INPUTS_DIRECTORY,
                       "load_mw.tab"), "w") as \
        load_tab_file:
    writer = csv.writer(load_tab_file, delimiter="\t")

    # Write header
    writer.writerow(
        ["LOAD_ZONES", "TIMEPOINTS", "load_mw"]
    )

    loads = c.execute(
        """SELECT load_zone, timepoint, load_mw
        FROM loads
        WHERE period_scenario_id = {}
        AND horizon_scenario_id = {}
        AND timepoint_scenario_id = {}
        AND load_zone_scenario_id = {}
        AND load_scenario_id = {}
        """.format(
            PERIOD_SCENARIO_ID, HORIZON_SCENARIO_ID, TIMEPOINT_SCENARIO_ID,
            LOAD_ZONE_SCENARIO_ID, LOAD_SCENARIO_ID
        )
    )
    for row in loads:
        writer.writerow(row)

# lf_reserves_up_requirement.tab
# part of optional lf_reserves_up module
if OPTIONAL_MODULE_LF_RESERVES_UP:
    with open(os.path.join(INPUTS_DIRECTORY,
                           "lf_reserves_up_requirement.tab"), "w") as \
            lf_reserves_up_tab_file:
        writer = csv.writer(lf_reserves_up_tab_file, delimiter="\t")

        # Write header
        # TODO: change these headers
        writer.writerow(
            ["LOAD_ZONES", "TIMEPOINTS", "upward_reserve_requirement"]
        )

        lf_reserves_up = c.execute(
            """SELECT lf_reserves_up_ba, timepoint, lf_reserves_up_mw
            FROM lf_reserves_up
            WHERE period_scenario_id = {}
            AND horizon_scenario_id = {}
            AND timepoint_scenario_id = {}
            AND existing_project_scenario_id = {}
            AND new_project_scenario_id = {}
            AND lf_reserves_up_ba_scenario_id = {}
            AND lf_reserves_up_scenario_id = {}
            """.format(
                PERIOD_SCENARIO_ID, HORIZON_SCENARIO_ID, TIMEPOINT_SCENARIO_ID,
                EXISTING_PROJECT_SCENARIO_ID, NEW_PROJECT_SCENARIO_ID,
                LF_RESERVES_UP_BA_SCENARIO_ID, LF_RESERVES_UP_SCENARIO_ID
            )
        )
        for row in lf_reserves_up:
            writer.writerow(row)
        
# lf_reserves_down_requirement.tab
# part of optional lf_reserves_down module
if OPTIONAL_MODULE_LF_RESERVES_DOWN:
    with open(os.path.join(INPUTS_DIRECTORY,
                           "lf_reserves_down_requirement.tab"), "w") as \
            lf_reserves_down_tab_file:
        writer = csv.writer(lf_reserves_down_tab_file, delimiter="\t")

        # Write header
        # TODO: change these headers
        writer.writerow(
            ["LOAD_ZONES", "TIMEPOINTS", "downward_reserve_requirement"]
        )

        lf_reserves_down = c.execute(
            """SELECT lf_reserves_down_ba, timepoint, lf_reserves_down_mw
            FROM lf_reserves_down
            WHERE period_scenario_id = {}
            AND horizon_scenario_id = {}
            AND timepoint_scenario_id = {}
            AND existing_project_scenario_id = {}
            AND new_project_scenario_id = {}
            AND lf_reserves_down_ba_scenario_id = {}
            AND lf_reserves_down_scenario_id = {}
            """.format(
                PERIOD_SCENARIO_ID, HORIZON_SCENARIO_ID, TIMEPOINT_SCENARIO_ID,
                EXISTING_PROJECT_SCENARIO_ID, NEW_PROJECT_SCENARIO_ID,
                LF_RESERVES_DOWN_BA_SCENARIO_ID, LF_RESERVES_DOWN_SCENARIO_ID
            )
        )
        for row in lf_reserves_down:
            writer.writerow(row)

if OPTIONAL_MODULE_TRANSMISSION:
    # transmission_lines.tab
    with open(os.path.join(INPUTS_DIRECTORY,
                           "transmission_lines.tab"), "w") as \
            transmission_lines_tab_file:
        writer = csv.writer(transmission_lines_tab_file, delimiter="\t")

        # Are we tracking carbon?
        line_file_optional_headers = list()
        line_db_table_optional_args = {}

        if OPTIONAL_MODULE_CARBON_CAP and OPTIONAL_MODULE_TRACK_CARBON_IMPORTS:
            line_file_optional_headers = [
                "carbon_cap_zone", "carbon_cap_zone_import_direction",
                "tx_co2_intensity_tons_per_mwh"
            ]
            line_db_table_optional_args["select"] = \
                """, carbon_cap_zone, carbon_cap_zone_import_direction,
                tx_co2_intensity_tons_per_mwh """
            line_db_table_optional_args["join"] = \
                """\nJOIN transmission_line_carbon_cap_zones
                USING (load_zone_scenario_id, transmission_line_scenario_id,
                transmission_line)"""
            line_db_table_optional_args["and"] = \
                """\nAND carbon_cap_zone_scenario_id = {}
                AND transmission_line_carbon_cap_zone_scenario_id = {}"""
        else:
            prj_db_table_optional_select["lf_reserves_up"] = {
                "db_column_name": "",
                "db_join_statement": ""
            }

        # Write header
        writer.writerow(
            ["TRANSMISSION_LINES", "tx_capacity_type", "load_zone_from",
             "load_zone_to"] + line_file_optional_headers
        )

        tx_query = \
            """SELECT transmission_lines.transmission_line, tx_capacity_type,
            load_zone_from, load_zone_to""" \
            + line_db_table_optional_args["select"] + \
            """FROM transmission_lines""" + \
            line_db_table_optional_args["join"] + \
            """
            WHERE load_zone_scenario_id = {}
            AND transmission_line_scenario_id = {} """ + \
            line_db_table_optional_args["and"] + \
            """;"""

        transmission_lines = c.execute(
            tx_query.format(
                LOAD_ZONE_SCENARIO_ID, TRANSMISSION_LINE_SCENARIO_ID,
                CARBON_CAP_ZONE_SCENARIO_ID,
                TRANSMISSION_LINE_CARBON_CAP_ZONE_SCENARIO_ID
            )
        ).fetchall()
        for row in transmission_lines:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    # specified_transmission_line_capacities.tab
    with open(os.path.join(INPUTS_DIRECTORY,
                           "specified_transmission_line_capacities.tab"), "w")\
            as transmission_lines_specified_capacities_tab_file:
        writer = csv.writer(transmission_lines_specified_capacities_tab_file,
                            delimiter="\t")

        # Write header
        writer.writerow(
            ["transmission_line", "period", "specified_tx_min_mw",
             "specified_tx_max_mw"]
        )

        transmission_lines_specified_capacities = c.execute(
            """SELECT transmission_line, period, min_mw, max_mw
            FROM transmission_line_existing_capacity
            WHERE load_zone_scenario_id = {}
            AND transmission_line_scenario_id = {}
            AND period_scenario_id = {}
            AND transmission_line_existing_capacity_scenario_id = {};
            """.format(
                LOAD_ZONE_SCENARIO_ID, TRANSMISSION_LINE_SCENARIO_ID,
                PERIOD_SCENARIO_ID,
                TRANSMISSION_LINE_EXISTING_CAPACITY_SCENARIO_ID
            )
        )
        for row in transmission_lines_specified_capacities:
            writer.writerow(row)


# rps_targets.tab
# part of optional rps module
if OPTIONAL_MODULE_RPS:
    with open(os.path.join(INPUTS_DIRECTORY,
                           "rps_targets.tab"), "w") as \
            rps_targets_tab_file:
        writer = csv.writer(rps_targets_tab_file,
                            delimiter="\t")

        # Write header
        writer.writerow(
            ["rps_zone", "period", "rps_target_mwh"]
        )

        rps_targets = c.execute(
            """SELECT rps_zone, period, rps_target_mwh
            FROM rps_targets
            WHERE period_scenario_id = {}
            AND horizon_scenario_id = {}
            AND timepoint_scenario_id = {}
            AND load_zone_scenario_id = {}
            AND rps_zone_scenario_id = {}
            AND rps_target_scenario_id = {};
            """.format(
                PERIOD_SCENARIO_ID, HORIZON_SCENARIO_ID, TIMEPOINT_SCENARIO_ID,
                LOAD_ZONE_SCENARIO_ID, RPS_ZONE_SCENARIO_ID, RPS_TARGET_SCENARIO_ID
            )
        )
        for row in rps_targets:
            writer.writerow(row)


# Simultaneous flow
# transmission_simultaneous_flow_group_lines.tab
if OPTIONAL_MODULE_TRANSMISSION and OPTIONAL_MODULE_SIMULTANEOUS_FLOW_LIMITS:
    with open(os.path.join(INPUTS_DIRECTORY,
                           "transmission_simultaneous_flow_group_lines.tab"),
              "w") as \
            sim_flow_group_lines_file:
        writer = csv.writer(sim_flow_group_lines_file,
                            delimiter="\t")

        # Write header
        writer.writerow(
            ["simultaneous_flow_group", "transmission_line",
             "simultaneous_flow_direction"]
        )

        group_lines = c.execute(
            """SELECT transmission_simultaneous_flow_group, transmission_line,
            simultaneous_flow_direction
            FROM transmission_simultaneous_flow_group_lines
            WHERE load_zone_scenario_id = {}
            AND transmission_line_scenario_id = {}
            AND transmission_simultaneous_flow_group_lines_scenario_id = {};
            """.format(
                LOAD_ZONE_SCENARIO_ID, TRANSMISSION_LINE_SCENARIO_ID,
                TRANSMISSION_SIMULTANEOUS_FLOW_GROUP_LINES_SCENARIO_ID
            )
        )
        for row in group_lines:
            writer.writerow(row)

    # transmission_simultaneous_flows.tab
    with open(os.path.join(INPUTS_DIRECTORY,
                           "transmission_simultaneous_flows.tab"), "w") as \
            sim_flows_file:
        writer = csv.writer(sim_flows_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["simultaneous_flow_group", "period", "simultaneous_flow_limit_mw"]
        )

        flow_limits = c.execute(
            """SELECT transmission_simultaneous_flow_group, period, max_flow_mw
            FROM transmission_simultaneous_flow_limits
            WHERE load_zone_scenario_id = {}
            AND transmission_line_scenario_id = {}
            AND transmission_simultaneous_flow_group_lines_scenario_id = {}
            AND period_scenario_id = {}
            AND transmission_simultaneous_flow_limit_scenario_id = {};
            """.format(
                LOAD_ZONE_SCENARIO_ID, TRANSMISSION_LINE_SCENARIO_ID,
                TRANSMISSION_SIMULTANEOUS_FLOW_GROUP_LINES_SCENARIO_ID,
                PERIOD_SCENARIO_ID,
                TRANSMISSION_SIMULTANEOUS_FLOW_LIMIT_SCENARIO_ID
            )
        )
        for row in flow_limits:
            writer.writerow(row)

if OPTIONAL_MODULE_CARBON_CAP:
    # carbon_cap_zones.tab
    with open(os.path.join(INPUTS_DIRECTORY,
                           "carbon_cap_zones.tab"), "w") as \
            carbon_cap_zones_file:
        writer = csv.writer(carbon_cap_zones_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["carbon_cap_zone"]
        )

        carbon_cap_zone = c.execute(
            """SELECT carbon_cap_zone
            FROM carbon_cap_zones
            WHERE carbon_cap_zone_scenario_id = {};
            """.format(
                CARBON_CAP_ZONE_SCENARIO_ID
            )
        )
        for row in carbon_cap_zone:
            writer.writerow(row)

    # carbon_cap.tab
    with open(os.path.join(INPUTS_DIRECTORY,
                           "carbon_cap.tab"), "w") as \
            carbon_cap_file:
        writer = csv.writer(carbon_cap_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["carbon_cap_zone", "period", "carbon_cap_target_mmt"]
        )

        carbon_cap = c.execute(
            """SELECT carbon_cap_zone, period, carbon_cap_target_mmt
            FROM carbon_cap_targets
            WHERE period_scenario_id = {}
            AND carbon_cap_zone_scenario_id = {}
            AND carbon_cap_target_scenario_id = {};
            """.format(
                PERIOD_SCENARIO_ID, CARBON_CAP_ZONE_SCENARIO_ID,
                CARBON_CAP_TARGET_SCENARIO_ID
            )
        )
        for row in carbon_cap:
            writer.writerow(row)
