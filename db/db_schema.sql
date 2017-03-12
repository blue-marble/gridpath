-- Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

-----------------
-- -- MODEL -- --
-----------------

-- Implemented horizon boundary types
DROP TABLE IF EXISTS mod_horizon_boundary_types;
CREATE TABLE mod_horizon_boundary_types(
horizon_boundary_type VARCHAR(16) PRIMARY KEY,
description VARCHAR(128)
);
-- TODO: add descriptions
INSERT INTO mod_horizon_boundary_types (horizon_boundary_type, description)
VALUES
('circular',
'Last horizon timepoint is previous timepoint for first horizon timepoint'),
('linear',
'No previous timepoint for first horizon timepoint');

-- Implemented capacity types
DROP TABLE IF EXISTS mod_capacity_types;
CREATE TABLE mod_capacity_types(
capacity_type VARCHAR(32) PRIMARY KEY,
description VARCHAR(128)
);

-- TODO: add descriptions
INSERT INTO mod_capacity_types (capacity_type)
VALUES ('existing_gen_linear_economic_retirement'),
('existing_gen_no_economic_retirement'), ('new_build_generator'),
('new_build_storage'), ('storage_specified_no_economic_retirement');

-- Implemented operational types
DROP TABLE IF EXISTS mod_operational_types;
CREATE TABLE mod_operational_types(
operational_type VARCHAR(32) PRIMARY KEY,
description VARCHAR(128)
);

INSERT INTO mod_operational_types (operational_type)
VALUES ('dispatchable_binary_commit'), ('dispatchable_capacity_commit'),
('dispatchable_continuous_commit'), ('dispatchable_no_commit'),
('hydro_conventional'), ('must_run'), ('storage_generic'), ('variable');


--------------------
-- -- TEMPORAL -- --
--------------------

-- Timepoints
-- These are the timepoints that go into the model, with horizons
-- and periods specified
-- Usually, this a timepoint_scenario_id is a subset of a much larger set of
-- timepoints
DROP TABLE IF EXISTS subscenarios_temporal_timepoints;
CREATE TABLE subscenarios_temporal_timepoints(
timepoint_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_temporal_timepoints;
CREATE TABLE inputs_temporal_timepoints(
timepoint_scenario_id INTEGER,
timepoint INTEGER,
period INTEGER,
horizon INTEGER,
number_of_hours_in_timepoint INTEGER,
PRIMARY KEY (timepoint_scenario_id, timepoint),
FOREIGN KEY (timepoint_scenario_id) REFERENCES subscenarios_timepoints
(timepoint_scenario_id)
);

-- Periods
DROP TABLE IF EXISTS inputs_temporal_periods;
CREATE TABLE inputs_temporal_periods(
timepoint_scenario_id INTEGER,
period INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
PRIMARY KEY (timepoint_scenario_id, period),
FOREIGN KEY (timepoint_scenario_id) REFERENCES subscenarios_temporal_timepoints
(timepoint_scenario_id),
-- Make sure period exists in this timepoint_id
FOREIGN KEY (timepoint_scenario_id, period) REFERENCES
inputs_temporal_timepoints (timepoint_scenario_id, period)
);

-- Horizons
DROP TABLE IF EXISTS inputs_temporal_horizons;
CREATE TABLE inputs_temporal_horizons(
timepoint_scenario_id INTEGER,
horizon INTEGER,
period INTEGER,
boundary VARCHAR(16),
horizon_weight FLOAT,
PRIMARY KEY (timepoint_scenario_id, horizon),
FOREIGN KEY (timepoint_scenario_id) REFERENCES subscenarios_temporal_timepoints
(timepoint_scenario_id),
-- Make sure horizon exists in this timepoint_id
FOREIGN KEY (timepoint_scenario_id, horizon) REFERENCES
inputs_temporal_timepoints (timepoint_scenario_id, horizon),
-- Make sure boundary type is correct
FOREIGN KEY (boundary) REFERENCES mod_horizon_boundary_types
(horizon_boundary_type)
);


---------------------
-- -- GEOGRAPHY -- --
---------------------

-- Load zones
-- This is the unit at which load is met in the model: it could be one zone
-- or many zones
DROP TABLE IF EXISTS subscenarios_geography_load_zones;
CREATE TABLE subscenarios_geography_load_zones(
load_zone_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_geography_load_zones;
CREATE TABLE inputs_geography_load_zones(
load_zone_scenario_id INTEGER,
load_zone VARCHAR(32),
overgeneration_penalty_per_mw FLOAT,
unserved_energy_penalty_per_mw FLOAT,
PRIMARY KEY (load_zone_scenario_id, load_zone),
FOREIGN KEY (load_zone_scenario_id) REFERENCES
subscenarios_geography_load_zones (load_zone_scenario_id)
);


-- Reserves
-- This is the unit at which reserves are met at the model; it can be
-- different from the load zones
DROP TABLE IF EXISTS subscenarios_geography_lf_reserves_up_bas;
CREATE TABLE subscenarios_geography_lf_reserves_up_bas(
lf_reserves_up_ba_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_geography_lf_reserves_up_bas;
CREATE TABLE inputs_geography_lf_reserves_up_bas(
lf_reserves_up_ba_scenario_id INTEGER,
lf_reserves_up_ba VARCHAR(32),
violation_penalty_per_mw FLOAT,
PRIMARY KEY (lf_reserves_up_ba_scenario_id, lf_reserves_up_ba),
FOREIGN KEY (lf_reserves_up_ba_scenario_id) REFERENCES
subscenarios_geography_lf_reserves_up_bas (lf_reserves_up_ba_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_geography_lf_reserves_down_bas;
CREATE TABLE subscenarios_geography_lf_reserves_down_bas(
lf_reserves_down_ba_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_geography_lf_reserves_down_bas;
CREATE TABLE inputs_geography_lf_reserves_down_bas(
lf_reserves_down_ba_scenario_id INTEGER,
lf_reserves_down_ba VARCHAR(32),
violation_penalty_per_mw FLOAT,
PRIMARY KEY (lf_reserves_down_ba_scenario_id, lf_reserves_down_ba),
FOREIGN KEY (lf_reserves_down_ba_scenario_id) REFERENCES
subscenarios_geography_lf_reserves_down_bas (lf_reserves_down_ba_scenario_id)
);

-- RPS
-- This is the unit at which RPS requirements are met in the model; it can be
-- different from the load zones
DROP TABLE IF EXISTS subscenarios_geography_rps_zones;
CREATE TABLE subscenarios_geography_rps_zones(
rps_zone_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_geography_rps_zones;
CREATE TABLE inputs_geography_rps_zones(
rps_zone_scenario_id INTEGER,
rps_zone VARCHAR(32),
PRIMARY KEY (rps_zone_scenario_id, rps_zone),
FOREIGN KEY (rps_zone_scenario_id) REFERENCES
subscenarios_geography_rps_zones (rps_zone_scenario_id)
);

-- Carbon cap
-- This is the unit at which the carbon cap is applied in the model; it can be
-- different from the load zones
DROP TABLE IF EXISTS subscenarios_geography_carbon_cap_zones;
CREATE TABLE subscenarios_geography_carbon_cap_zones(
carbon_cap_zone_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_geography_carbon_cap_zones;
CREATE TABLE inputs_geography_carbon_cap_zones(
carbon_cap_zone_scenario_id INTEGER,
carbon_cap_zone VARCHAR(32),
PRIMARY KEY (carbon_cap_zone_scenario_id, carbon_cap_zone),
FOREIGN KEY (carbon_cap_zone_scenario_id) REFERENCES
subscenarios_geography_carbon_cap_zones (carbon_cap_zone_scenario_id)
);


-------------------
-- -- PROJECT -- --
-------------------

-- All projects: a list of all projects we may model
DROP TABLE IF EXISTS inputs_project_all;
CREATE TABLE inputs_project_all(
project VARCHAR(64) PRIMARY KEY
);

-- -- Capacity -- --

-- Project portfolios
-- Subsets of projects allowed in a scenario: includes both existing and
-- potential projects
DROP TABLE IF EXISTS subscenarios_project_portfolios;
CREATE TABLE subscenarios_project_portfolios(
project_portfolio_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_portfolios;
CREATE TABLE inputs_project_portfolios(
project_portfolio_scenario_id INTEGER,
project VARCHAR(64),
existing INTEGER,
new_build INTEGER,
capacity_type VARCHAR(32),
PRIMARY KEY (project_portfolio_scenario_id, project),
FOREIGN KEY (project_portfolio_scenario_id) REFERENCES
subscenarios_project_portfolios (project_portfolio_scenario_id),
FOREIGN KEY (capacity_type) REFERENCES capacity_types (capacity_type)
);

-- Existing project capacity and fixed costs
-- The capacity and fixed costs of 'existing' projects, i.e. exogenously
-- specified capacity that is not a variable in the model
-- Retirement can be allowed, in which case the fixed cost will determine
-- whether the economics of retirement are favorable
DROP TABLE IF EXISTS subscenarios_project_existing_capacity;
CREATE TABLE subscenarios_project_existing_capacity(
project_existing_capacity_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_existing_capacity;
CREATE TABLE inputs_project_existing_capacity(
project_existing_capacity_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
existing_capacity_mw FLOAT,
existing_capacity_mwh FLOAT,
PRIMARY KEY (project_existing_capacity_scenario_id, project, period)
);

DROP TABLE IF EXISTS subscenarios_project_existing_fixed_cost;
CREATE TABLE subscenarios_project_existing_fixed_cost(
project_existing_fixed_cost_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_existing_fixed_cost;
CREATE TABLE inputs_project_existing_fixed_cost(
project_existing_fixed_cost_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
annual_fixed_cost_per_mw_year FLOAT,
annual_fixed_cost_per_mwh_year FLOAT,
PRIMARY KEY (project_existing_fixed_cost_scenario_id, project, period),
FOREIGN KEY (project_existing_fixed_cost_scenario_id) REFERENCES
subscenarios_project_existing_fixed_cost
(project_existing_fixed_cost_scenario_id)
);

-- New project capital costs and potential
-- The annualized all-in cost of potential new project (capital + fixed o&m
-- with financing)
-- In each 'period,' the minimum build required and maximum build allowed
-- can also be specified
DROP TABLE IF EXISTS subscenarios_project_new_cost;
CREATE TABLE subscenarios_project_new_cost(
project_new_cost_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_new_cost;
CREATE TABLE inputs_project_new_cost(
project_new_cost_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
lifetime_yrs INTEGER,
annualized_real_cost_per_kw_yr FLOAT,
annualized_real_cost_per_kwh_yr FLOAT,
levelized_cost_per_mwh FLOAT,  -- useful if available, although not used
PRIMARY KEY (project_new_cost_scenario_id, project, period),
FOREIGN KEY (project_new_cost_scenario_id) REFERENCES
subscenarios_project_new_cost (project_new_cost_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_new_potential;
CREATE TABLE subscenarios_project_new_potential(
project_new_potential_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Projects with no min or max build requirements can be included here with
-- NULL values or excluded from this table
DROP TABLE IF EXISTS inputs_project_new_potential;
CREATE TABLE inputs_project_new_potential(
project_new_potential_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
minimum_cumulative_new_build_mw FLOAT,
maximum_cumulative_new_build_mw FLOAT,
minimum_cumulative_new_build_mwh FLOAT,
maximum_cumulative_new_build_mwh FLOAT,
PRIMARY KEY (project_new_potential_scenario_id, project, period),
FOREIGN KEY (project_new_potential_scenario_id) REFERENCES
subscenarios_project_new_potential (project_new_potential_scenario_id)
);

-- -- Operations -- --

-- Project operational characteristics
-- These vary by operational type
-- Generators that do not have certain characteristics (e.g. hydro does not
-- have a heat rate) should be included with NULL values in these columns
-- For variable generators, specify a variable_generator_profile_scenario_id
-- For conventional hydro generators, specify a
-- hydro_operational_chars_scenario_id
DROP TABLE IF EXISTS subscenarios_project_operational_chars;
CREATE TABLE subscenarios_project_operational_chars(
project_operational_chars_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_operational_chars;
CREATE TABLE inputs_project_operational_chars(
project_operational_chars_scenario_id INTEGER,
project VARCHAR(64),
operational_type VARCHAR(32),
variable_cost_per_mwh FLOAT,
fuel VARCHAR(32),
minimum_input_mmbtu_per_hr FLOAT,
inc_heat_rate_mmbtu_per_mwh FLOAT,
min_stable_level FLOAT,
unit_size_mw FLOAT,
startup_cost_per_mw FLOAT,
shutdown_cost_per_mw FLOAT,
ramp_rate_fraction FLOAT,
min_up_time_hours INTEGER,
min_down_time_hours INTEGER,
charging_efficiency FLOAT,
discharging_efficiency FLOAT,
minimum_duration_hours FLOAT,
technology VARCHAR(32),
variable_generator_profile_scenario_id INTEGER,  -- determines var profiles
hydro_operational_chars_scenario_id INTEGER,  -- determines hydro MWa, min, max
PRIMARY KEY (project_operational_chars_scenario_id, project),
FOREIGN KEY (project_operational_chars_scenario_id) REFERENCES
subscenarios_project_operational_chars (project_operational_chars_scenario_id),
-- Ensure operational characteristics for variable and hydro exist
FOREIGN KEY (variable_generator_profile_scenario_id, project) REFERENCES
inputs_project_variable_generator_profiles
(variable_generator_profile_scenario_id, project),
FOREIGN KEY (hydro_operational_chars_scenario_id, project) REFERENCES
inputs_project_hydro_operational_chars
(hydro_operational_chars_scenario_id, project)
);

-- Variable generator profiles
-- TODO: this is not exactly a subscenario, as a variable profile will be
-- assigned to variable projects in the project_operational_chars table and
-- be passed to scenarios via the project_operational_chars_scenario_id
-- perhaps a better name is needed for this table
DROP TABLE IF EXISTS subscenarios_project_variable_generator_profiles;
CREATE TABLE subscenarios_project_variable_generator_profiles(
variable_generator_profile_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_variable_generator_profiles;
CREATE TABLE inputs_project_variable_generator_profiles(
variable_generator_profile_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
cap_factor FLOAT,
PRIMARY KEY (variable_generator_profile_scenario_id, project, timepoint),
FOREIGN KEY (variable_generator_profile_scenario_id) REFERENCES
subscenarios_project_variable_generator_profiles
(variable_generator_profile_scenario_id)
);

-- Hydro operational characteristics
DROP TABLE IF EXISTS subscenarios_project_hydro_operational_chars;
CREATE TABLE subscenarios_project_hydro_operational_chars(
hydro_operational_chars_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_hydro_operational_chars;
CREATE TABLE inputs_project_hydro_operational_chars(
hydro_operational_chars_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
average_power_mwa FLOAT,
min_power_mw FLOAT,
max_power_mw FLOAT,
PRIMARY KEY (hydro_operational_chars_scenario_id, project, horizon),
FOREIGN KEY (hydro_operational_chars_scenario_id) REFERENCES
subscenarios_project_hydro_operational_chars
(hydro_operational_chars_scenario_id)
);


-- Project load zones
-- Where projects are modeled to be physically located
-- Depends on the load_zone_scenario_id, i.e. how geography is modeled
-- (project can be in one zone if modeling a single zone, but a different
-- zone if modeling several zones, etc.)
DROP TABLE IF EXISTS subscenarios_project_load_zones;
CREATE TABLE subscenarios_project_load_zones(
load_zone_scenario_id INTEGER,
project_load_zone_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (load_zone_scenario_id, project_load_zone_scenario_id),
FOREIGN KEY (load_zone_scenario_id) REFERENCES
subscenarios_geography_load_zones (load_zone_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_load_zones;
CREATE TABLE inputs_project_load_zones(
load_zone_scenario_id INTEGER,
project_load_zone_scenario_id INTEGER,
project VARCHAR(64),
load_zone VARCHAR(32),
PRIMARY KEY (load_zone_scenario_id, project_load_zone_scenario_id, project),
FOREIGN KEY (load_zone_scenario_id, project_load_zone_scenario_id) REFERENCES
 subscenarios_project_load_zones
 (load_zone_scenario_id, project_load_zone_scenario_id),
FOREIGN KEY (load_zone_scenario_id) REFERENCES
subscenarios_geography_load_zones (load_zone_scenario_id)
);

-- Project BAs
-- Which projects can contribute to a reserve requirement
-- Depends on how reserve balancing area are specified (xyz_ba_scenario_id)
-- This table can included all project with NULLs for projects not
-- contributing or just the contributing projects
DROP TABLE IF EXISTS subscenarios_project_lf_reserves_up_bas;
CREATE TABLE subscenarios_project_lf_reserves_up_bas(
lf_reserves_up_ba_scenario_id INTEGER,
project_lf_reserves_up_ba_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (lf_reserves_up_ba_scenario_id,
project_lf_reserves_up_ba_scenario_id),
FOREIGN KEY (lf_reserves_up_ba_scenario_id) REFERENCES
subscenarios_geography_lf_reserves_up_bas (lf_reserves_up_ba_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_lf_reserves_up_bas;
CREATE TABLE inputs_project_lf_reserves_up_bas(
lf_reserves_up_ba_scenario_id INTEGER,
project_lf_reserves_up_ba_scenario_id INTEGER,
project VARCHAR(64),
lf_reserves_up_ba VARCHAR(32),
PRIMARY KEY (lf_reserves_up_ba_scenario_id,
project_lf_reserves_up_ba_scenario_id, project),
FOREIGN KEY (lf_reserves_up_ba_scenario_id,
project_lf_reserves_up_ba_scenario_id)
REFERENCES subscenarios_project_lf_reserves_up_bas
 (lf_reserves_up_ba_scenario_id, project_lf_reserves_up_ba_scenario_id),
FOREIGN KEY (lf_reserves_up_ba_scenario_id) REFERENCES
subscenarios_geography_lf_reserves_up_bas (lf_reserves_up_ba_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_lf_reserves_down_bas;
CREATE TABLE subscenarios_project_lf_reserves_down_bas(
lf_reserves_down_ba_scenario_id INTEGER,
project_lf_reserves_down_ba_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (lf_reserves_down_ba_scenario_id,
project_lf_reserves_down_ba_scenario_id),
FOREIGN KEY (lf_reserves_down_ba_scenario_id) REFERENCES
subscenarios_geography_lf_reserves_down_bas (lf_reserves_down_ba_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_lf_reserves_down_bas;
CREATE TABLE inputs_project_lf_reserves_down_bas(
lf_reserves_down_ba_scenario_id INTEGER,
project_lf_reserves_down_ba_scenario_id INTEGER,
project VARCHAR(64),
lf_reserves_down_ba VARCHAR(32),
PRIMARY KEY (lf_reserves_down_ba_scenario_id,
project_lf_reserves_down_ba_scenario_id, project),
FOREIGN KEY (lf_reserves_down_ba_scenario_id,
project_lf_reserves_down_ba_scenario_id)
REFERENCES subscenarios_project_lf_reserves_down_bas
 (lf_reserves_down_ba_scenario_id, project_lf_reserves_down_ba_scenario_id),
FOREIGN KEY (lf_reserves_down_ba_scenario_id) REFERENCES
subscenarios_geography_lf_reserves_down_bas (lf_reserves_down_ba_scenario_id)
);

-- Project RPS zones
-- Which projects can contribute to RPS requirements
-- Depends on how RPS zones are specified
-- This table can included all project with NULLs for projects not
-- contributing or just the contributing projects

DROP TABLE IF EXISTS subscenarios_project_rps_zones;
CREATE TABLE subscenarios_project_rps_zones(
rps_zone_scenario_id INTEGER,
project_rps_zone_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (rps_zone_scenario_id,
project_rps_zone_scenario_id),
FOREIGN KEY (rps_zone_scenario_id) REFERENCES
subscenarios_geography_rps_zones (rps_zone_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_rps_zones;
CREATE TABLE inputs_project_rps_zones(
rps_zone_scenario_id INTEGER,
project_rps_zone_scenario_id INTEGER,
project VARCHAR(64),
rps_zone VARCHAR(32),
PRIMARY KEY (rps_zone_scenario_id, project_rps_zone_scenario_id, project),
FOREIGN KEY (rps_zone_scenario_id, project_rps_zone_scenario_id) REFERENCES
 subscenarios_project_rps_zones
 (rps_zone_scenario_id, project_rps_zone_scenario_id),
FOREIGN KEY (rps_zone_scenario_id) REFERENCES
subscenarios_geography_rps_zones (rps_zone_scenario_id)
);

-- Project carbon cap zones
-- Which projects count toward the carbon cap
-- Depends on carbon cap zone geography
-- This table can included all project with NULLs for projects not
-- contributing or just the contributing projects
DROP TABLE IF EXISTS subscenarios_project_carbon_cap_zones;
CREATE TABLE subscenarios_project_carbon_cap_zones(
carbon_cap_zone_scenario_id INTEGER,
project_carbon_cap_zone_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (carbon_cap_zone_scenario_id,
project_carbon_cap_zone_scenario_id),
FOREIGN KEY (carbon_cap_zone_scenario_id) REFERENCES
subscenarios_geography_carbon_cap_zones (carbon_cap_zone_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_carbon_cap_zones;
CREATE TABLE inputs_project_carbon_cap_zones(
carbon_cap_zone_scenario_id INTEGER,
project_carbon_cap_zone_scenario_id INTEGER,
project VARCHAR(64),
carbon_cap_zone VARCHAR(32),
PRIMARY KEY (carbon_cap_zone_scenario_id,
project_carbon_cap_zone_scenario_id, project),
FOREIGN KEY (carbon_cap_zone_scenario_id,
project_carbon_cap_zone_scenario_id) REFERENCES
 subscenarios_project_carbon_cap_zones
 (carbon_cap_zone_scenario_id, project_carbon_cap_zone_scenario_id),
FOREIGN KEY (carbon_cap_zone_scenario_id) REFERENCES
subscenarios_geography_carbon_cap_zones (carbon_cap_zone_scenario_id)
);

-- Fuels
DROP TABLE IF EXISTS subscenarios_project_fuels;
CREATE TABLE subscenarios_project_fuels(
fuel_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_fuels;
CREATE TABLE inputs_project_fuels(
fuel_scenario_id INTEGER,
fuel VARCHAR(32),
fuel_price_per_mmbtu FLOAT,
co2_intensity_tons_per_mmbtu FLOAT,
PRIMARY KEY (fuel_scenario_id, fuel),
FOREIGN KEY (fuel_scenario_id) REFERENCES subscenarios_project_fuels
(fuel_scenario_id)
);



------------------
-- TRANSMISSION --
------------------

-- Transmission portfolios
DROP TABLE IF EXISTS subscenarios_transmission_portfolios;
CREATE TABLE subscenarios_transmission_portfolios(
transmission_portfolio_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_transmission_portfolios;
CREATE TABLE inputs_transmission_portfolios(
transmission_portfolio_scenario_id INTEGER,
transmission_line VARCHAR(64),
capacity_type VARCHAR(32),
PRIMARY KEY (transmission_portfolio_scenario_id, transmission_line),
FOREIGN KEY (transmission_portfolio_scenario_id) REFERENCES
subscenarios_transmission_portfolios
(transmission_portfolio_scenario_id)
);

-- Transmission geography
-- Load zones
DROP TABLE IF EXISTS subscenarios_transmission_load_zones;
CREATE TABLE subscenarios_transmission_load_zones(
load_zone_scenario_id INTEGER,
transmission_load_zone_scenario_id,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (load_zone_scenario_id, transmission_load_zone_scenario_id),
FOREIGN KEY (load_zone_scenario_id) REFERENCES
subscenarios_geography_load_zones (load_zone_scenario_id)
);

DROP TABLE IF EXISTS inputs_transmission_load_zones;
CREATE TABLE inputs_transmission_load_zones(
load_zone_scenario_id INTEGER,
transmission_load_zone_scenario_id INTEGER,
transmission_line VARCHAR(64),
load_zone_from VARCHAR(32),
load_zone_to VARCHAR(32),
PRIMARY KEY (load_zone_scenario_id, transmission_load_zone_scenario_id,
transmission_line),
FOREIGN KEY (load_zone_scenario_id) REFERENCES
subscenarios_geography_load_zones
(load_zone_scenario_id)
);

-- Carbon cap zones
-- This is needed if the carbon cap module is enabled and we want to track
-- emission imports
DROP TABLE IF EXISTS subscenarios_transmission_carbon_cap_zones;
CREATE TABLE subscenarios_transmission_carbon_cap_zones(
carbon_cap_zone_scenario_id INTEGER,
transmission_carbon_cap_zone_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (carbon_cap_zone_scenario_id,
transmission_carbon_cap_zone_scenario_id),
FOREIGN KEY (carbon_cap_zone_scenario_id) REFERENCES
subscenarios_geography_carbon_cap_zones (carbon_cap_zone_scenario_id)
);

DROP TABLE IF EXISTS inputs_transmission_carbon_cap_zones;
CREATE TABLE inputs_transmission_carbon_cap_zones(
carbon_cap_zone_scenario_id INTEGER,
transmission_carbon_cap_zone_scenario_id INTEGER,
transmission_line VARCHAR(64),
carbon_cap_zone VARCHAR(32),
import_direction VARCHAR(8),
tx_co2_intensity_tons_per_mwh FLOAT,
PRIMARY KEY (carbon_cap_zone_scenario_id,
transmission_carbon_cap_zone_scenario_id,
transmission_line),
FOREIGN KEY (carbon_cap_zone_scenario_id) REFERENCES
subscenarios_geography_carbon_cap_zones
(carbon_cap_zone_scenario_id)
);

-- Existing transmission capacity
DROP TABLE IF EXISTS subscenarios_transmission_existing_capacity;
CREATE TABLE subscenarios_transmission_existing_capacity(
transmission_existing_capacity_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_transmission_existing_capacity;
CREATE TABLE inputs_transmission_existing_capacity(
transmission_existing_capacity_scenario_id INTEGER,
transmission_line VARCHAR(64),
period INTEGER,
min_mw FLOAT,
max_mw FLOAT,
PRIMARY KEY (transmission_existing_capacity_scenario_id, transmission_line,
period),
FOREIGN KEY (transmission_existing_capacity_scenario_id) REFERENCES
subscenarios_transmission_existing_capacity
(transmission_existing_capacity_scenario_id)
);

-- Operational characteristics
-- This currently makes no difference, as we only have one operational type
-- for transmission
DROP TABLE IF EXISTS subscenarios_transmission_operational_chars;
CREATE TABLE subscenarios_transmission_operational_chars(
transmission_operational_chars_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_transmission_operational_chars;
CREATE TABLE inputs_transmission_operational_chars(
transmission_operational_chars_scenario_id INTEGER,
transmission_line VARCHAR(64),
PRIMARY KEY (transmission_operational_chars_scenario_id, transmission_line),
FOREIGN KEY (transmission_operational_chars_scenario_id) REFERENCES
subscenarios_transmission_operational_chars
(transmission_operational_chars_scenario_id)
);

-- Simultaneous flows
-- Limits on net flows on groups of lines (e.g. all lines connected to a zone)
DROP TABLE IF EXISTS subscenarios_transmission_simultaneous_flow_limits;
CREATE TABLE subscenarios_transmission_simultaneous_flow_limits(
transmission_simultaneous_flow_limit_scenario_id INTEGER
PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_transmission_simultaneous_flow_limits;
CREATE TABLE inputs_transmission_simultaneous_flow_limits(
transmission_simultaneous_flow_limit_scenario_id INTEGER,
transmission_simultaneous_flow_limit VARCHAR(64),
period INTEGER,
max_flow_mw FLOAT,
PRIMARY KEY (transmission_simultaneous_flow_limit_scenario_id,
transmission_simultaneous_flow_limit, period),
FOREIGN KEY (transmission_simultaneous_flow_limit_scenario_id) REFERENCES
subscenarios_transmission_simultaneous_flow_limits
(transmission_simultaneous_flow_limit_scenario_id)
);


DROP TABLE IF EXISTS
subscenarios_transmission_simultaneous_flow_limit_line_groups;
CREATE TABLE subscenarios_transmission_simultaneous_flow_limit_line_groups(
transmission_simultaneous_flow_limit_line_group_scenario_id INTEGER PRIMARY KEY
AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_transmission_simultaneous_flow_limit_line_groups;
CREATE TABLE inputs_transmission_simultaneous_flow_limit_line_groups(
transmission_simultaneous_flow_limit_line_group_scenario_id INTEGER,
transmission_simultaneous_flow_limit VARCHAR(64),
transmission_line VARCHAR(64),
simultaneous_flow_direction INTEGER,
PRIMARY KEY (transmission_simultaneous_flow_limit_line_group_scenario_id,
transmission_simultaneous_flow_limit, transmission_line),
FOREIGN KEY (transmission_simultaneous_flow_limit_line_group_scenario_id)
REFERENCES subscenarios_transmission_simultaneous_flow_limit_line_groups
(transmission_simultaneous_flow_limit_line_group_scenario_id)
);


------------------
-- -- SYSTEM -- --
------------------

-- -- Load balance -- --
DROP TABLE IF EXISTS subscenarios_system_load;
CREATE TABLE subscenarios_system_load(
load_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include timepoints and zones other than the ones in a scenario, as
-- correct timepoints and zones will be pulled depending on
-- timepoint_scenario_id and load_zone_scenario_id
DROP TABLE IF EXISTS inputs_system_load;
CREATE TABLE inputs_system_load(
load_scenario_id INTEGER,
load_zone VARCHAR(32),
timepoint INTEGER,
load_mw FLOAT,
PRIMARY KEY (load_scenario_id, load_zone, timepoint),
FOREIGN KEY (load_scenario_id) REFERENCES subscenarios_system_load
(load_scenario_id)
);

-- -- Reserves -- --

-- LF reserves up
DROP TABLE IF EXISTS subscenarios_system_lf_reserves_up;
CREATE TABLE subscenarios_system_lf_reserves_up(
lf_reserves_up_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include timepoints and zones other than the ones in a scenario, as
-- correct timepoints and zones will be pulled depending on
-- timepoint_scenario_id and reserves_scenario_id
DROP TABLE IF EXISTS inputs_system_lf_reserves_up;
CREATE TABLE inputs_system_lf_reserves_up(
lf_reserves_up_scenario_id INTEGER,
lf_reserves_up_ba VARCHAR(32),
timepoint INTEGER,
lf_reserves_up_mw FLOAT,
PRIMARY KEY (lf_reserves_up_scenario_id, lf_reserves_up_ba, timepoint),
FOREIGN KEY (lf_reserves_up_scenario_id) REFERENCES
subscenarios_system_lf_reserves_up (lf_reserves_up_scenario_id)
);

-- LF reserves down
DROP TABLE IF EXISTS subscenarios_system_lf_reserves_down;
CREATE TABLE subscenarios_system_lf_reserves_down(
lf_reserves_down_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include timepoints and zones other than the ones in a scenario, as
-- correct timepoints and zones will be pulled depending on
-- timepoint_scenario_id and reserves_scenario_id
DROP TABLE IF EXISTS inputs_system_lf_reserves_down;
CREATE TABLE inputs_system_lf_reserves_down(
lf_reserves_down_scenario_id INTEGER,
lf_reserves_down_ba VARCHAR(32),
timepoint INTEGER,
lf_reserves_down_mw FLOAT,
PRIMARY KEY (lf_reserves_down_scenario_id, lf_reserves_down_ba, timepoint),
FOREIGN KEY (lf_reserves_down_scenario_id) REFERENCES
subscenarios_system_lf_reserves_down (lf_reserves_down_scenario_id)
);

-- -- Policy -- --

-- RPS requirements

DROP TABLE IF EXISTS subscenarios_system_rps_targets;
CREATE TABLE subscenarios_system_rps_targets(
rps_target_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include periods and zones other than the ones in a scenario, as correct
-- periods and zones will be pulled depending on timepoint_scenario_id and
-- rps_zone_scenario_id
DROP TABLE IF EXISTS inputs_system_rps_targets;
CREATE TABLE inputs_system_rps_targets(
rps_target_scenario_id INTEGER,
rps_zone VARCHAR(32),
period INTEGER,
rps_target_mwh FLOAT,
rps_zone_scenario_id INTEGER,
PRIMARY KEY (rps_target_scenario_id, rps_zone, period),
FOREIGN KEY (rps_zone_scenario_id, rps_zone) REFERENCES
inputs_geography_rps_zones (rps_zone_scenario_id, rps_zone)
);

-- Carbon cap
DROP TABLE IF EXISTS subscenarios_system_carbon_cap_targets;
CREATE TABLE subscenarios_system_carbon_cap_targets(
carbon_cap_target_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include periods and zones other than the ones in a scenario, as correct
-- periods and zones will be pulled depending on timepoint_scenario_id and
-- carbon_cap_zone_scenario_id
DROP TABLE IF EXISTS inputs_system_carbon_cap_targets;
CREATE TABLE inputs_system_carbon_cap_targets(
carbon_cap_target_scenario_id INTEGER,
carbon_cap_zone VARCHAR(32),
period INTEGER,
carbon_cap_mmt FLOAT,
PRIMARY KEY (carbon_cap_target_scenario_id, carbon_cap_zone, period)
);


---------------------
-- -- SCENARIOS -- --
---------------------
DROP TABLE IF EXISTS scenarios;
CREATE TABLE scenarios(
scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
scenario_name VARCHAR(64),
om_fuels INTEGER,
om_multi_stage INTEGER,
om_transmission INTEGER,
om_simultaneous_flow_limits INTEGER,
om_lf_reserves_up INTEGER,
om_lf_reserves_down INTEGER,
om_regulation_up INTEGER,
om_regulation_down INTEGER,
om_rps INTEGER,
om_carbon_cap INTEGER,
om_track_carbon_imports INTEGER,
timepoint_scenario_id INTEGER,
load_zone_scenario_id INTEGER,
lf_reserves_up_ba_scenario_id INTEGER,
lf_reserves_down_ba_scenario_id INTEGER,
rps_zone_scenario_id INTEGER,
carbon_cap_zone_scenario_id INTEGER,
project_portfolio_scenario_id INTEGER,
project_load_zone_scenario_id INTEGER,
project_lf_reserves_up_ba_scenario_id INTEGER,
project_lf_reserves_down_ba_scenario_id INTEGER,
project_rps_zone_scenario_id INTEGER,
project_carbon_cap_zone_scenario_id INTEGER,
project_existing_capacity_scenario_id INTEGER,
project_existing_fixed_cost_scenario_id INTEGER,
project_operational_chars_scenario_id INTEGER,
fuel_scenario_id INTEGER,
project_new_cost_scenario_id INTEGER,
project_new_potential_scenario_id INTEGER,
transmission_portfolio_scenario_id INTEGER,
transmission_load_zone_scenario_id INTEGER,
transmission_existing_capacity_scenario_id INTEGER,
transmission_operational_chars_scenario_id INTEGER,
transmission_carbon_cap_zone_scenario_id INTEGER,
transmission_simultaneous_flow_limit_scenario_id INTEGER,
transmission_simultaneous_flow_limit_line_group_scenario_id INTEGER,
load_scenario_id INTEGER,
lf_reserves_up_scenario_id INTEGER,
lf_reserves_down_scenario_id INTEGER,
rps_target_scenario_id INTEGER,
carbon_cap_target_scenario_id INTEGER,
FOREIGN KEY (timepoint_scenario_id) REFERENCES
subscenarios_temporal_timepoints (timepoint_scenario_id),
FOREIGN KEY (load_zone_scenario_id) REFERENCES
subscenarios_geography_load_zones (load_zone_scenario_id),
FOREIGN KEY (lf_reserves_up_ba_scenario_id) REFERENCES
subscenarios_geography_lf_reserves_up_bas (lf_reserves_up_ba_scenario_id),
FOREIGN KEY (lf_reserves_down_ba_scenario_id) REFERENCES
subscenarios_geography_lf_reserves_down_bas (lf_reserves_down_ba_scenario_id),
FOREIGN KEY (rps_zone_scenario_id) REFERENCES
subscenarios_geography_rps_zones (rps_zone_scenario_id),
FOREIGN KEY (carbon_cap_zone_scenario_id) REFERENCES
subscenarios_geography_carbon_cap_zones (carbon_cap_zone_scenario_id),
FOREIGN KEY (project_operational_chars_scenario_id) REFERENCES
subscenarios_project_operational_chars (project_operational_chars_scenario_id),
FOREIGN KEY (fuel_scenario_id) REFERENCES
subscenarios_project_fuels (fuel_scenario_id),
FOREIGN KEY (project_portfolio_scenario_id) REFERENCES
subscenarios_project_portfolios (project_portfolio_scenario_id),
FOREIGN KEY (load_zone_scenario_id, project_load_zone_scenario_id) REFERENCES
subscenarios_project_load_zones
(load_zone_scenario_id, project_load_zone_scenario_id),
FOREIGN KEY (lf_reserves_up_ba_scenario_id,
project_lf_reserves_up_ba_scenario_id) REFERENCES
subscenarios_project_lf_reserves_up_bas
(lf_reserves_up_ba_scenario_id, project_lf_reserves_up_ba_scenario_id),
FOREIGN KEY (lf_reserves_down_ba_scenario_id,
project_lf_reserves_down_ba_scenario_id) REFERENCES
subscenarios_project_lf_reserves_down_bas
(lf_reserves_down_ba_scenario_id, project_lf_reserves_down_ba_scenario_id),
FOREIGN KEY (rps_zone_scenario_id, project_rps_zone_scenario_id) REFERENCES
subscenarios_project_rps_zones
(rps_zone_scenario_id, project_rps_zone_scenario_id),
FOREIGN KEY (carbon_cap_zone_scenario_id,
project_carbon_cap_zone_scenario_id) REFERENCES
subscenarios_project_carbon_cap_zones
(carbon_cap_zone_scenario_id, project_carbon_cap_zone_scenario_id),
FOREIGN KEY (project_existing_capacity_scenario_id) REFERENCES
subscenarios_project_existing_capacity (project_existing_capacity_scenario_id),
FOREIGN KEY (project_existing_fixed_cost_scenario_id) REFERENCES
subscenarios_project_existing_fixed_cost
(project_existing_fixed_cost_scenario_id),
FOREIGN KEY (project_new_cost_scenario_id) REFERENCES
subscenarios_project_new_cost (project_new_cost_scenario_id),
FOREIGN KEY (project_new_potential_scenario_id) REFERENCES
subscenarios_project_new_potential (project_new_potential_scenario_id)
FOREIGN KEY (transmission_portfolio_scenario_id) REFERENCES
subscenarios_transmission_portfolios
(transmission_portfolio_scenario_id),
FOREIGN KEY (load_zone_scenario_id, transmission_load_zone_scenario_id)
REFERENCES subscenarios_transmission_load_zones (load_zone_scenario_id,
transmission_load_zone_scenario_id),
FOREIGN KEY (transmission_existing_capacity_scenario_id) REFERENCES
subscenarios_transmission_existing_capacity
(transmission_existing_capacity_scenario_id),
FOREIGN KEY (transmission_operational_chars_scenario_id) REFERENCES
subscenarios_transmission_operational_chars
(transmission_operational_chars_scenario_id),
FOREIGN KEY (carbon_cap_zone_scenario_id,
transmission_carbon_cap_zone_scenario_id)
REFERENCES subscenarios_transmission_carbon_cap_zones
(carbon_cap_zone_scenario_id, transmission_carbon_cap_zone_scenario_id),
FOREIGN KEY (transmission_simultaneous_flow_limit_scenario_id)
REFERENCES subscenarios_transmission_simultaneous_flow_limits
(transmission_simultaneous_flow_limit_scenario_id),
FOREIGN KEY (transmission_simultaneous_flow_limit_line_group_scenario_id)
REFERENCES subscenarios_transmission_simultaneous_flow_limit_line_groups
(transmission_simultaneous_flow_limit_line_group_scenario_id),
FOREIGN KEY (load_scenario_id) REFERENCES subscenarios_system_load
(load_scenario_id),
FOREIGN KEY (lf_reserves_up_scenario_id) REFERENCES
subscenarios_system_lf_reserves_up (lf_reserves_up_scenario_id),
FOREIGN KEY (lf_reserves_down_scenario_id) REFERENCES
subscenarios_system_lf_reserves_down (lf_reserves_down_scenario_id),
FOREIGN KEY (rps_target_scenario_id) REFERENCES
subscenarios_system_rps_targets (rps_target_scenario_id),
FOREIGN KEY (carbon_cap_target_scenario_id) REFERENCES
subscenarios_system_carbon_cap_targets (carbon_cap_target_scenario_id)
);

--------------------------
-- -- DATA INTEGRITY -- --
--------------------------

-- Allowed combinations of subscenario IDs -- some should not be used together

-- Project portfolio scenario, reserves scenario

-- Load scenario, RPS target scenario, PV BTM scenario

-- Project op char scenario, load_zone scenario, reserves BA scenario, RPS
-- zone scenario, carbon cap scenario

-- Sim Tx flow limits, sim Tx flow limit groups, Tx lines

-- Project operational chars ID and fuel ID


-------------------
-- -- RESULTS -- --
-------------------

DROP TABLE IF EXISTS results_project_capacity_all;
CREATE TABLE results_project_capacity_all(
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
technology VARCHAR(32),
load_zone VARCHAR(32),
capacity_mw FLOAT,
energy_capacity_mwh FLOAT,
PRIMARY KEY (scenario_id, project, period)
);

DROP TABLE IF EXISTS results_project_dispatch_all;
CREATE TABLE results_project_dispatch_all(
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
technology VARCHAR(32),
power_mw FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_dispatch_variable;
CREATE TABLE results_project_dispatch_variable(
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
technology VARCHAR(32),
power_mw FLOAT,
scheduled_curtailment_mw FLOAT,
subhourly_curtailment_mw FLOAT,
subhourly_energy_delivered_mw FLOAT,
total_curtailment_mw FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_dispatch_capacity_commit;
CREATE TABLE results_project_dispatch_capacity_commit(
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
technology VARCHAR(32),
power_mw FLOAT,
committed_mw FLOAT,
committed_units FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_costs_capacity;
CREATE TABLE results_project_costs_capacity(
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
technology VARCHAR(32),
load_zone VARCHAR(32),
annualized_capacity_cost FLOAT,
PRIMARY KEY (scenario_id, project, period)
);

DROP TABLE IF EXISTS results_project_costs_operations_variable_om;
CREATE TABLE results_project_costs_operations_variable_om(
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
technology VARCHAR(32),
variable_om_cost FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_costs_operations_fuel;
CREATE TABLE results_project_costs_operations_fuel(
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
technology VARCHAR(32),
fuel_cost FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_costs_operations_startup;
CREATE TABLE results_project_costs_operations_startup(
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
technology VARCHAR(32),
startup_cost FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_costs_operations_shutdown;
CREATE TABLE results_project_costs_operations_shutdown(
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
technology VARCHAR(32),
shutdown_cost FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);


DROP TABLE IF EXISTS results_transmission_imports_exports;
CREATE TABLE results_transmission_imports_exports(
scenario_id INTEGER,
load_zone VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
imports_mw FLOAT,
exports_mw FLOAT,
net_imports_mw FLOAT,
PRIMARY KEY (scenario_id, load_zone, timepoint)
);