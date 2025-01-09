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


"""
Form EIA 860 Projects User-Defined Operating Characteristics
************************************************************

Create opchar CSV for a EIA860-based project portfolio. Note that most of
operating characteristics are user-defined in the
user_defined_eia_gridpath_key table and will take default values until more
detailed data are available.

.. note:: The query in this module is consistent with the project selection
    from ``eia860_to_project_portfolio_input_csvs``.

=====
Usage
=====

>>> gridpath_run_data_toolkit --single_step eia860_to_project_opchar_input_csvs --settings_csv PATH/TO/SETTINGS/CSV

===================
Input prerequisites
===================

This module assumes the following raw input database tables have been populated:
    * raw_data_eia860_generators
    * user_defined_eia_gridpath_key

=========
Settings
=========
    * database
    * output_directory
    * study_year
    * region
    * project_operational_chars_scenario_id
    * project_operational_chars_scenario_name
    * project_fuel_scenario_id
    * variable_generator_profile_scenario_id
    * hydro_operational_chars_scenario_id

"""

from argparse import ArgumentParser
import os.path
import pandas as pd
import sys

from db.common_functions import connect_to_database
from data_toolkit.project.project_data_filters_common import (
    get_eia860_sql_filter_string,
    VAR_GEN_FILTER_STR,
    HYDRO_FILTER_STR,
    FUEL_FILTER_STR,
    HEAT_RATE_FILTER_STR,
    STOR_FILTER_STR,
    DISAGG_PROJECT_NAME_STR,
    AGG_PROJECT_NAME_STR,
)


# TODO: add var costs, startup and shutdown costs, and startup fuel use


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    parser.add_argument("-db", "--database", default="../../open_data_raw.db")
    parser.add_argument("-y", "--study_year", default=2026)
    parser.add_argument("-r", "--region", default="WECC")
    parser.add_argument(
        "-o",
        "--output_directory",
        default="../../csvs_open_data/project/opchar",
    )
    parser.add_argument(
        "-opchar_id", "--project_operational_chars_scenario_id", default=1
    )
    parser.add_argument(
        "-opchar_name",
        "--project_operational_chars_scenario_name",
        default="wecc_plants_opchar",
    )
    parser.add_argument("-fuel_id", "--project_fuel_scenario_id", default=1)
    parser.add_argument("-hr_id", "--heat_rate_curves_scenario_id", default=1)
    parser.add_argument(
        "-var_id", "--variable_generator_profile_scenario_id", default=1
    )
    parser.add_argument("-hy_id", "--hydro_operational_chars_scenario_id", default=1)

    parser.add_argument("-q", "--quiet", default=False, action="store_true")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def get_project_opchar(
    conn,
    eia860_sql_filter_string,
    fuel_filter_str,
    heat_rate_filter_str,
    stor_filter_str,
    var_gen_filter_str,
    hydro_filter_str,
    disagg_project_name_str,
    agg_project_name_str,
    csv_location,
    subscenario_id,
    subscenario_name,
    fuel_id,
    hr_id,
    var_id,
    hy_id,
):
    # Wind, offshore wind, and PV are aggregated, so treated separately since
    # they are aggregated, so here we make a UNION between tables filtering
    # based on var_gen_filter_str

    non_var_opchars_str = make_opchar_sql_str(
        technology="gridpath_technology",
        operational_type="gridpath_operational_type",
        balancing_type_project="gridpath_balancing_type",
        variable_om_cost_per_mwh="default_variable_om_cost_per_mwh",
        project_fuel_scenario_id=f"""CASE WHEN {fuel_filter_str} THEN {fuel_id} ELSE 
        NULL END""",
        heat_rate_curves_scenario_id=f"""CASE WHEN {heat_rate_filter_str} 
        THEN {hr_id} ELSE NULL END""",
        min_stable_level_fraction=f"""CASE WHEN {heat_rate_filter_str} THEN min_load_fraction ELSE NULL END""",
        storage_efficiency=f"""CASE WHEN {stor_filter_str} THEN default_storage_efficiency ELSE NULL END""",
        charging_efficiency=f"""CASE WHEN {stor_filter_str} THEN default_charging_efficiency ELSE NULL END""",
        discharging_efficiency=f"""CASE WHEN {stor_filter_str} THEN 
        default_discharging_efficiency ELSE NULL END""",
    )

    var_opchars_str = make_opchar_sql_str(
        technology="gridpath_technology",
        operational_type="gridpath_operational_type",
        balancing_type_project="gridpath_balancing_type",
        variable_om_cost_per_mwh="default_variable_om_cost_per_mwh",
        variable_generator_profile_scenario_id=f"{var_id}",
    )

    hydro_opchars_str = make_opchar_sql_str(
        technology="gridpath_technology",
        operational_type="gridpath_operational_type",
        balancing_type_project="gridpath_balancing_type",
        variable_om_cost_per_mwh="default_variable_om_cost_per_mwh",
        hydro_operational_chars_scenario_id=f"{hy_id}",
    )

    sql = f"""
     SELECT {disagg_project_name_str} AS project,
         {non_var_opchars_str}
     FROM raw_data_eia860_generators
     JOIN user_defined_eia_gridpath_key ON
            raw_data_eia860_generators.prime_mover_code = 
            user_defined_eia_gridpath_key.prime_mover_code
            AND energy_source_code_1 = energy_source_code
     WHERE 1 = 1
     AND {eia860_sql_filter_string}
     AND NOT {var_gen_filter_str}
     AND NOT {hydro_filter_str}
     -- Variable gen
     UNION
     SELECT {agg_project_name_str} AS project,
         {var_opchars_str}
     FROM raw_data_eia860_generators
     JOIN user_defined_eia_gridpath_key ON
            raw_data_eia860_generators.prime_mover_code = 
            user_defined_eia_gridpath_key.prime_mover_code
            AND energy_source_code_1 = energy_source_code
     WHERE 1 = 1
     AND {eia860_sql_filter_string}
     AND {var_gen_filter_str}
     GROUP BY project
     -- Hydro
     UNION
     SELECT {agg_project_name_str} AS project,
         {hydro_opchars_str}
     FROM raw_data_eia860_generators
     JOIN user_defined_eia_gridpath_key ON
            raw_data_eia860_generators.prime_mover_code = 
            user_defined_eia_gridpath_key.prime_mover_code
            AND energy_source_code_1 = energy_source_code
     WHERE 1 = 1
     AND {eia860_sql_filter_string}
     AND {hydro_filter_str}
     GROUP BY project
     ;
     """

    df = pd.read_sql(sql, conn)

    # Enforce integer for ID columns
    # Can add column names to the list
    # Note that this must be 'Int64'
    df[["variable_generator_profile_scenario_id"]] = df[
        ["variable_generator_profile_scenario_id"]
    ].astype("Int64")

    df.to_csv(
        os.path.join(csv_location, f"{subscenario_id}_" f"{subscenario_name}.csv"),
        index=False,
    )


def make_opchar_sql_str(
    technology="NULL",
    operational_type="NULL",
    balancing_type_project="NULL",
    variable_om_cost_per_mwh="NULL",
    variable_om_cost_by_period_scenario_id="NULL",
    variable_om_cost_by_timepoint_scenario_id="NULL",
    project_fuel_scenario_id="NULL",
    heat_rate_curves_scenario_id="NULL",
    variable_om_curves_scenario_id="NULL",
    startup_chars_scenario_id="NULL",
    min_stable_level_fraction="NULL",
    unit_size_mw="NULL",
    startup_cost_per_mw="NULL",
    shutdown_cost_per_mw="NULL",
    startup_fuel_mmbtu_per_mw="NULL",
    startup_plus_ramp_up_rate="NULL",
    shutdown_plus_ramp_down_rate="NULL",
    ramp_up_when_on_rate="NULL",
    ramp_down_when_on_rate="NULL",
    ramp_up_violation_penalty="NULL",
    ramp_down_violation_penalty="NULL",
    min_up_time_hours="NULL",
    min_up_time_violation_penalty="NULL",
    min_down_time_hours="NULL",
    min_down_time_violation_penalty="NULL",
    cycle_selection_scenario_id="NULL",
    supplemental_firing_scenario_id="NULL",
    allow_startup_shutdown_power="NULL",
    storage_efficiency="NULL",
    charging_efficiency="NULL",
    discharging_efficiency="NULL",
    charging_capacity_multiplier="NULL",
    discharging_capacity_multiplier="NULL",
    soc_penalty_cost_per_energyunit="NULL",
    soc_last_tmp_penalty_cost_per_energyunit="NULL",
    flex_load_static_profile_scenario_id="NULL",
    minimum_duration_hours="NULL",
    maximum_duration_hours="NULL",
    aux_consumption_frac_capacity="NULL",
    aux_consumption_frac_power="NULL",
    last_commitment_stage="NULL",
    variable_generator_profile_scenario_id="NULL",
    curtailment_cost_per_pwh="NULL",
    hydro_operational_chars_scenario_id="NULL",
    energy_profile_scenario_id="NULL",
    energy_hrz_shaping_scenario_id="NULL",
    energy_slice_hrz_shaping_scenario_id="NULL",
    base_net_requirement_scenario_id="NULL",
    peak_deviation_demand_charge_scenario_id="NULL",
    lf_reserves_up_derate="NULL",
    lf_reserves_down_derate="NULL",
    regulation_up_derate="NULL",
    regulation_down_derate="NULL",
    frequency_response_derate="NULL",
    spinning_reserves_derate="NULL",
    lf_reserves_up_ramp_rate="NULL",
    lf_reserves_down_ramp_rate="NULL",
    regulation_up_ramp_rate="NULL",
    regulation_down_ramp_rate="NULL",
    frequency_response_ramp_rate="NULL",
    spinning_reserves_ramp_rate="NULL",
    powerunithour_per_fuelunit="NULL",
    cap_factor_limits_scenario_id="NULL",
    partial_availability_threshold="NULL",
    stor_exog_state_of_charge_scenario_id="NULL",
    nonfuel_carbon_emissions_per_mwh="NULL",
    powerhouse="NULL",
    generator_efficiency="NULL",
):
    """ """

    opchar_sql_str = f"""
     {technology} AS technology,
     {operational_type} AS operational_type,
     {balancing_type_project} AS balancing_type_project,
     {variable_om_cost_per_mwh} AS variable_om_cost_per_mwh,
     {variable_om_cost_by_period_scenario_id} AS variable_om_cost_by_period_scenario_id,
     {variable_om_cost_by_timepoint_scenario_id} AS 
     variable_om_cost_by_timepoint_scenario_id,	
     {project_fuel_scenario_id} AS project_fuel_scenario_id,
     {heat_rate_curves_scenario_id} AS heat_rate_curves_scenario_id,	
     {variable_om_curves_scenario_id} AS variable_om_curves_scenario_id,
     {startup_chars_scenario_id} AS startup_chars_scenario_id,	
     {min_stable_level_fraction} AS min_stable_level_fraction,
     {unit_size_mw} AS unit_size_mw,
     {startup_cost_per_mw} AS startup_cost_per_mw,	
     {shutdown_cost_per_mw} AS shutdown_cost_per_mw,
     {startup_fuel_mmbtu_per_mw} AS startup_fuel_mmbtu_per_mw,	
     {startup_plus_ramp_up_rate} AS startup_plus_ramp_up_rate,
     {shutdown_plus_ramp_down_rate} AS shutdown_plus_ramp_down_rate,	
     {ramp_up_when_on_rate} AS ramp_up_when_on_rate,
     {ramp_down_when_on_rate} AS ramp_down_when_on_rate,	
     {ramp_up_violation_penalty} AS ramp_up_violation_penalty,
     {ramp_down_violation_penalty} AS ramp_down_violation_penalty,	
     {min_up_time_hours} AS min_up_time_hours,
     {min_up_time_violation_penalty} AS min_up_time_violation_penalty,	
     {min_down_time_hours} AS min_down_time_hours,
     {min_down_time_violation_penalty} AS min_down_time_violation_penalty,	
     {cycle_selection_scenario_id} AS cycle_selection_scenario_id,
     {supplemental_firing_scenario_id} AS supplemental_firing_scenario_id,	
     {allow_startup_shutdown_power} AS allow_startup_shutdown_power,
     {storage_efficiency} AS storage_efficiency,	
     {charging_efficiency} AS charging_efficiency,
     {discharging_efficiency} AS discharging_efficiency,	
     {charging_capacity_multiplier} AS charging_capacity_multiplier,
     {discharging_capacity_multiplier} AS discharging_capacity_multiplier,	
     {soc_penalty_cost_per_energyunit} AS soc_penalty_cost_per_energyunit,
     {soc_last_tmp_penalty_cost_per_energyunit} AS soc_last_tmp_penalty_cost_per_energyunit,
     {flex_load_static_profile_scenario_id} AS flex_load_static_profile_scenario_id,
     {minimum_duration_hours} AS minimum_duration_hours,	
     {maximum_duration_hours} AS maximum_duration_hours,
     {aux_consumption_frac_capacity} AS aux_consumption_frac_capacity,	
     {aux_consumption_frac_power} AS aux_consumption_frac_power,
     {last_commitment_stage} AS last_commitment_stage,	
     {variable_generator_profile_scenario_id} AS variable_generator_profile_scenario_id,
     {curtailment_cost_per_pwh} AS curtailment_cost_per_pwh,	
     {hydro_operational_chars_scenario_id} AS hydro_operational_chars_scenario_id,
     {energy_profile_scenario_id} AS "energy_profile_scenario_id",
     {energy_hrz_shaping_scenario_id} AS "energy_hrz_shaping_scenario_id",
     {energy_slice_hrz_shaping_scenario_id} AS 
     "energy_slice_hrz_shaping_scenario_id",
     {base_net_requirement_scenario_id} AS "base_net_requirement_scenario_id",
     {peak_deviation_demand_charge_scenario_id} AS 
     "peak_deviation_demand_charge_scenario_id",
     {lf_reserves_up_derate} AS lf_reserves_up_derate,	
     {lf_reserves_down_derate} AS lf_reserves_down_derate,
     {regulation_up_derate} AS regulation_up_derate,	
     {regulation_down_derate} AS regulation_down_derate,
     {frequency_response_derate} AS frequency_response_derate,	
     {spinning_reserves_derate} AS spinning_reserves_derate,
     {lf_reserves_up_ramp_rate} AS lf_reserves_up_ramp_rate,	
     {lf_reserves_down_ramp_rate} AS lf_reserves_down_ramp_rate,
     {regulation_up_ramp_rate} AS regulation_up_ramp_rate,
     {regulation_down_ramp_rate} AS regulation_down_ramp_rate,
     {frequency_response_ramp_rate} AS frequency_response_ramp_rate,
     {spinning_reserves_ramp_rate} AS spinning_reserves_ramp_rate,
     {powerunithour_per_fuelunit} AS powerunithour_per_fuelunit,
     {cap_factor_limits_scenario_id} AS cap_factor_limits_scenario_id,
     {partial_availability_threshold} AS partial_availability_threshold,
     {stor_exog_state_of_charge_scenario_id} AS stor_exog_state_of_charge_scenario_id,
     {nonfuel_carbon_emissions_per_mwh} AS nonfuel_carbon_emissions_per_mwh,
     {powerhouse} AS powerhouse,
     {generator_efficiency} AS generator_efficiency
    """

    return opchar_sql_str


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    if not parsed_args.quiet:
        print("Creating project opchar inputs")

    os.makedirs(parsed_args.output_directory, exist_ok=True)

    conn = connect_to_database(db_path=parsed_args.database)

    get_project_opchar(
        conn=conn,
        eia860_sql_filter_string=get_eia860_sql_filter_string(
            study_year=parsed_args.study_year, region=parsed_args.region
        ),
        fuel_filter_str=FUEL_FILTER_STR,
        heat_rate_filter_str=HEAT_RATE_FILTER_STR,
        stor_filter_str=STOR_FILTER_STR,
        var_gen_filter_str=VAR_GEN_FILTER_STR,
        hydro_filter_str=HYDRO_FILTER_STR,
        disagg_project_name_str=DISAGG_PROJECT_NAME_STR,
        agg_project_name_str=AGG_PROJECT_NAME_STR,
        csv_location=parsed_args.output_directory,
        subscenario_id=parsed_args.project_operational_chars_scenario_id,
        subscenario_name=parsed_args.project_operational_chars_scenario_name,
        fuel_id=parsed_args.project_fuel_scenario_id,
        hr_id=parsed_args.heat_rate_curves_scenario_id,
        var_id=parsed_args.variable_generator_profile_scenario_id,
        hy_id=parsed_args.hydro_operational_chars_scenario_id,
    )


if __name__ == "__main__":
    main()
