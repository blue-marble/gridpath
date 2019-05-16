-- Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

-----------------
-- -- MODEL -- --
-----------------

-- Implemented horizon boundary types
DROP TABLE IF EXISTS mod_horizon_boundary_types;
CREATE TABLE mod_horizon_boundary_types (
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
CREATE TABLE mod_capacity_types (
capacity_type VARCHAR(32) PRIMARY KEY,
description VARCHAR(128)
);

-- TODO: add descriptions
INSERT INTO mod_capacity_types (capacity_type)
VALUES ('existing_gen_linear_economic_retirement'),
('existing_gen_binary_economic_retirement'),
('existing_gen_no_economic_retirement'), ('new_build_generator'),
('new_build_storage'), ('new_shiftable_load_supply_curve'),
('storage_specified_no_economic_retirement');

-- Implemented operational types
DROP TABLE IF EXISTS mod_operational_types;
CREATE TABLE mod_operational_types (
operational_type VARCHAR(32) PRIMARY KEY,
description VARCHAR(128)
);

INSERT INTO mod_operational_types (operational_type)
VALUES ('dispatchable_binary_commit'), ('dispatchable_capacity_commit'),
('dispatchable_continuous_commit'), ('dispatchable_no_commit'),
('hydro_curtailable'), ('hydro_noncurtailable'), ('must_run'),
('storage_generic'), ('variable'), ('always_on');


--------------------
-- -- TEMPORAL -- --
--------------------

-- Timepoints
-- These are the timepoints that go into the model, with horizons
-- and periods specified
-- Usually, this timepoint_scenario_id is a subset of a much larger set of
-- timepoints
DROP TABLE IF EXISTS subscenarios_temporal_timepoints;
CREATE TABLE subscenarios_temporal_timepoints (
timepoint_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_temporal_timepoints;
CREATE TABLE inputs_temporal_timepoints (
timepoint_scenario_id INTEGER,
timepoint INTEGER,
period INTEGER,
horizon INTEGER,
number_of_hours_in_timepoint INTEGER,
PRIMARY KEY (timepoint_scenario_id, timepoint),
FOREIGN KEY (timepoint_scenario_id) REFERENCES subscenarios_temporal_timepoints
(timepoint_scenario_id)
);

-- Periods
DROP TABLE IF EXISTS inputs_temporal_periods;
CREATE TABLE inputs_temporal_periods (
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
CREATE TABLE inputs_temporal_horizons (
timepoint_scenario_id INTEGER,
horizon INTEGER,
period INTEGER,
boundary VARCHAR(16),
horizon_weight FLOAT,
month INTEGER,
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
CREATE TABLE subscenarios_geography_load_zones (
load_zone_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_geography_load_zones;
CREATE TABLE inputs_geography_load_zones (
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
CREATE TABLE subscenarios_geography_lf_reserves_up_bas (
lf_reserves_up_ba_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_geography_lf_reserves_up_bas;
CREATE TABLE inputs_geography_lf_reserves_up_bas (
lf_reserves_up_ba_scenario_id INTEGER,
lf_reserves_up_ba VARCHAR(32),
violation_penalty_per_mw FLOAT,
reserve_to_energy_adjustment FLOAT,
PRIMARY KEY (lf_reserves_up_ba_scenario_id, lf_reserves_up_ba),
FOREIGN KEY (lf_reserves_up_ba_scenario_id) REFERENCES
subscenarios_geography_lf_reserves_up_bas (lf_reserves_up_ba_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_geography_lf_reserves_down_bas;
CREATE TABLE subscenarios_geography_lf_reserves_down_bas (
lf_reserves_down_ba_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_geography_lf_reserves_down_bas;
CREATE TABLE inputs_geography_lf_reserves_down_bas (
lf_reserves_down_ba_scenario_id INTEGER,
lf_reserves_down_ba VARCHAR(32),
violation_penalty_per_mw FLOAT,
reserve_to_energy_adjustment FLOAT,
PRIMARY KEY (lf_reserves_down_ba_scenario_id, lf_reserves_down_ba),
FOREIGN KEY (lf_reserves_down_ba_scenario_id) REFERENCES
subscenarios_geography_lf_reserves_down_bas (lf_reserves_down_ba_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_geography_regulation_up_bas;
CREATE TABLE subscenarios_geography_regulation_up_bas (
regulation_up_ba_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_geography_regulation_up_bas;
CREATE TABLE inputs_geography_regulation_up_bas (
regulation_up_ba_scenario_id INTEGER,
regulation_up_ba VARCHAR(32),
violation_penalty_per_mw FLOAT,
reserve_to_energy_adjustment FLOAT,
PRIMARY KEY (regulation_up_ba_scenario_id, regulation_up_ba),
FOREIGN KEY (regulation_up_ba_scenario_id) REFERENCES
subscenarios_geography_regulation_up_bas (regulation_up_ba_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_geography_regulation_down_bas;
CREATE TABLE subscenarios_geography_regulation_down_bas (
regulation_down_ba_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_geography_regulation_down_bas;
CREATE TABLE inputs_geography_regulation_down_bas (
regulation_down_ba_scenario_id INTEGER,
regulation_down_ba VARCHAR(32),
violation_penalty_per_mw FLOAT,
reserve_to_energy_adjustment FLOAT,
PRIMARY KEY (regulation_down_ba_scenario_id, regulation_down_ba),
FOREIGN KEY (regulation_down_ba_scenario_id) REFERENCES
subscenarios_geography_regulation_down_bas (regulation_down_ba_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_geography_frequency_response_bas;
CREATE TABLE subscenarios_geography_frequency_response_bas (
frequency_response_ba_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_geography_frequency_response_bas;
CREATE TABLE inputs_geography_frequency_response_bas (
frequency_response_ba_scenario_id INTEGER,
frequency_response_ba VARCHAR(32),
violation_penalty_per_mw FLOAT,
reserve_to_energy_adjustment FLOAT,
PRIMARY KEY (frequency_response_ba_scenario_id, frequency_response_ba),
FOREIGN KEY (frequency_response_ba_scenario_id) REFERENCES
subscenarios_geography_frequency_response_bas
(frequency_response_ba_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_geography_spinning_reserves_bas;
CREATE TABLE subscenarios_geography_spinning_reserves_bas (
spinning_reserves_ba_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_geography_spinning_reserves_bas;
CREATE TABLE inputs_geography_spinning_reserves_bas (
spinning_reserves_ba_scenario_id INTEGER,
spinning_reserves_ba VARCHAR(32),
violation_penalty_per_mw FLOAT,
reserve_to_energy_adjustment FLOAT,
PRIMARY KEY (spinning_reserves_ba_scenario_id, spinning_reserves_ba),
FOREIGN KEY (spinning_reserves_ba_scenario_id) REFERENCES
subscenarios_geography_spinning_reserves_bas (spinning_reserves_ba_scenario_id)
);

-- RPS
-- This is the unit at which RPS requirements are met in the model; it can be
-- different from the load zones
DROP TABLE IF EXISTS subscenarios_geography_rps_zones;
CREATE TABLE subscenarios_geography_rps_zones (
rps_zone_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_geography_rps_zones;
CREATE TABLE inputs_geography_rps_zones (
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
CREATE TABLE subscenarios_geography_carbon_cap_zones (
carbon_cap_zone_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_geography_carbon_cap_zones;
CREATE TABLE inputs_geography_carbon_cap_zones (
carbon_cap_zone_scenario_id INTEGER,
carbon_cap_zone VARCHAR(32),
PRIMARY KEY (carbon_cap_zone_scenario_id, carbon_cap_zone),
FOREIGN KEY (carbon_cap_zone_scenario_id) REFERENCES
subscenarios_geography_carbon_cap_zones (carbon_cap_zone_scenario_id)
);

-- PRM
-- This is the unit at which PRM requirements are met in the model; it can be
-- different from the load zones
DROP TABLE IF EXISTS subscenarios_geography_prm_zones;
CREATE TABLE subscenarios_geography_prm_zones (
prm_zone_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_geography_prm_zones;
CREATE TABLE inputs_geography_prm_zones (
prm_zone_scenario_id INTEGER,
prm_zone VARCHAR(32),
PRIMARY KEY (prm_zone_scenario_id, prm_zone),
FOREIGN KEY (prm_zone_scenario_id) REFERENCES
subscenarios_geography_prm_zones (prm_zone_scenario_id)
);

-- Local capacity
-- This is the unit at which local capacity requirements are met in the model;
-- it can be different from the load zones
DROP TABLE IF EXISTS subscenarios_geography_local_capacity_zones;
CREATE TABLE subscenarios_geography_local_capacity_zones (
local_capacity_zone_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_geography_local_capacity_zones;
CREATE TABLE inputs_geography_local_capacity_zones (
local_capacity_zone_scenario_id INTEGER,
local_capacity_zone VARCHAR(32),
local_capacity_shortage_penalty_per_mw FLOAT,
PRIMARY KEY (local_capacity_zone_scenario_id, local_capacity_zone),
FOREIGN KEY (local_capacity_zone_scenario_id) REFERENCES
subscenarios_geography_local_capacity_zones (local_capacity_zone_scenario_id)
);


-------------------
-- -- PROJECT -- --
-------------------

-- All projects: a list of all projects we may model
DROP TABLE IF EXISTS inputs_project_all;
CREATE TABLE inputs_project_all (
project VARCHAR(64) PRIMARY KEY
);

-- -- Capacity -- --

-- Project portfolios
-- Subsets of projects allowed in a scenario: includes both existing and
-- potential projects
DROP TABLE IF EXISTS subscenarios_project_portfolios;
CREATE TABLE subscenarios_project_portfolios (
project_portfolio_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_portfolios;
CREATE TABLE inputs_project_portfolios (
project_portfolio_scenario_id INTEGER,
project VARCHAR(64),
existing INTEGER,
new_build INTEGER,
capacity_type VARCHAR(32),
PRIMARY KEY (project_portfolio_scenario_id, project),
FOREIGN KEY (project_portfolio_scenario_id) REFERENCES
subscenarios_project_portfolios (project_portfolio_scenario_id),
FOREIGN KEY (capacity_type) REFERENCES mod_capacity_types (capacity_type)
);

-- Existing project capacity and fixed costs
-- The capacity and fixed costs of 'existing' projects, i.e. exogenously
-- specified capacity that is not a variable in the model
-- Retirement can be allowed, in which case the fixed cost will determine
-- whether the economics of retirement are favorable
DROP TABLE IF EXISTS subscenarios_project_existing_capacity;
CREATE TABLE subscenarios_project_existing_capacity (
project_existing_capacity_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_existing_capacity;
CREATE TABLE inputs_project_existing_capacity (
project_existing_capacity_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
existing_capacity_mw FLOAT,
existing_capacity_mwh FLOAT,
PRIMARY KEY (project_existing_capacity_scenario_id, project, period),
FOREIGN KEY (project_existing_capacity_scenario_id) REFERENCES
subscenarios_project_existing_capacity (project_existing_capacity_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_existing_fixed_cost;
CREATE TABLE subscenarios_project_existing_fixed_cost (
project_existing_fixed_cost_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_existing_fixed_cost;
CREATE TABLE inputs_project_existing_fixed_cost (
project_existing_fixed_cost_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
annual_fixed_cost_per_kw_year FLOAT,
annual_fixed_cost_per_kwh_year FLOAT,
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
CREATE TABLE subscenarios_project_new_cost (
project_new_cost_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_new_cost;
CREATE TABLE inputs_project_new_cost (
project_new_cost_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
lifetime_yrs INTEGER,
annualized_real_cost_per_kw_yr FLOAT,
annualized_real_cost_per_kwh_yr FLOAT,
levelized_cost_per_mwh FLOAT,  -- useful if available, although not used
supply_curve_scenario_id INTEGER,
PRIMARY KEY (project_new_cost_scenario_id, project, period),
FOREIGN KEY (project_new_cost_scenario_id) REFERENCES
subscenarios_project_new_cost (project_new_cost_scenario_id)
);


-- Shiftable load supply curve
DROP TABLE IF EXISTS inputs_project_shiftable_load_supply_curve;
CREATE TABLE inputs_project_shiftable_load_supply_curve (
supply_curve_scenario_id INTEGER,
project VARCHAR(64),
supply_curve_point INTEGER,
supply_curve_slope FLOAT,
supply_curve_intercept FLOAT,
PRIMARY KEY (supply_curve_scenario_id, project, supply_curve_point)
);


DROP TABLE IF EXISTS subscenarios_project_new_potential;
CREATE TABLE subscenarios_project_new_potential (
project_new_potential_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Projects with no min or max build requirements can be included here with
-- NULL values or excluded from this table
DROP TABLE IF EXISTS inputs_project_new_potential;
CREATE TABLE inputs_project_new_potential (
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
-- For hydro generators (curtailable or nonocurtailable), specify a
-- hydro_operational_chars_scenario_id
DROP TABLE IF EXISTS subscenarios_project_operational_chars;
CREATE TABLE subscenarios_project_operational_chars (
project_operational_chars_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_operational_chars;
CREATE TABLE inputs_project_operational_chars (
project_operational_chars_scenario_id INTEGER,
project VARCHAR(64),
technology VARCHAR(32),
operational_type VARCHAR(32),
variable_cost_per_mwh FLOAT,
fuel VARCHAR(32),
minimum_input_mmbtu_per_hr FLOAT,
inc_heat_rate_mmbtu_per_mwh FLOAT,
min_stable_level FLOAT,
unit_size_mw FLOAT,
startup_cost_per_mw FLOAT,
shutdown_cost_per_mw FLOAT,
startup_fuel_mmbtu_per_mw FLOAT,
startup_plus_ramp_up_rate FLOAT,
shutdown_plus_ramp_down_rate FLOAT,
ramp_up_when_on_rate FLOAT,
ramp_down_when_on_rate FLOAT,
min_up_time_hours INTEGER,
min_down_time_hours INTEGER,
charging_efficiency FLOAT,
discharging_efficiency FLOAT,
minimum_duration_hours FLOAT,
variable_generator_profile_scenario_id INTEGER,  -- determines var profiles
hydro_operational_chars_scenario_id INTEGER,  -- determines hydro MWa, min, max
lf_reserves_up_derate FLOAT,
lf_reserves_down_derate FLOAT,
regulation_up_derate FLOAT,
regulation_down_derate FLOAT,
frequency_response_derate FLOAT,
spinning_reserves_derate FLOAT,
lf_reserves_up_ramp_rate FLOAT,
lf_reserves_down_ramp_rate FLOAT,
regulation_up_ramp_rate FLOAT,
regulation_down_ramp_rate FLOAT,
frequency_response_ramp_rate FLOAT,
spinning_reserves_ramp_rate FLOAT,
PRIMARY KEY (project_operational_chars_scenario_id, project),
FOREIGN KEY (project_operational_chars_scenario_id) REFERENCES
subscenarios_project_operational_chars (project_operational_chars_scenario_id),
-- Ensure operational characteristics for variable and hydro exist
FOREIGN KEY (variable_generator_profile_scenario_id, project) REFERENCES
inputs_project_variable_generator_profiles
(variable_generator_profile_scenario_id, project),
FOREIGN KEY (hydro_operational_chars_scenario_id, project) REFERENCES
inputs_project_hydro_operational_chars
(hydro_operational_chars_scenario_id, project),
FOREIGN KEY (operational_type) REFERENCES mod_operational_types
(operational_type)
);

-- Variable generator profiles
-- TODO: this is not exactly a subscenario, as a variable profile will be
-- assigned to variable projects in the project_operational_chars table and
-- be passed to scenarios via the project_operational_chars_scenario_id
-- perhaps a better name is needed for this table
DROP TABLE IF EXISTS subscenarios_project_variable_generator_profiles;
CREATE TABLE subscenarios_project_variable_generator_profiles (
variable_generator_profile_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_variable_generator_profiles;
CREATE TABLE inputs_project_variable_generator_profiles (
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
CREATE TABLE subscenarios_project_hydro_operational_chars (
hydro_operational_chars_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_hydro_operational_chars;
CREATE TABLE inputs_project_hydro_operational_chars (
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

-- Project availability (e.g. due to planned outages/maintenance)
DROP TABLE IF EXISTS subscenarios_project_availability;
CREATE TABLE subscenarios_project_availability (
project_availability_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_availability;
CREATE TABLE inputs_project_availability (
project_availability_scenario_id INTEGER,
project VARCHAR(64),
horizon INTEGER,
availability FLOAT,
PRIMARY KEY (project_availability_scenario_id, project, horizon),
FOREIGN KEY (project_availability_scenario_id) REFERENCES
subscenarios_project_availability (project_availability_scenario_id)
);


-- Project load zones
-- Where projects are modeled to be physically located
-- Depends on the load_zone_scenario_id, i.e. how geography is modeled
-- (project can be in one zone if modeling a single zone, but a different
-- zone if modeling several zones, etc.)
DROP TABLE IF EXISTS subscenarios_project_load_zones;
CREATE TABLE subscenarios_project_load_zones (
load_zone_scenario_id INTEGER,
project_load_zone_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (load_zone_scenario_id, project_load_zone_scenario_id),
FOREIGN KEY (load_zone_scenario_id) REFERENCES
subscenarios_geography_load_zones (load_zone_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_load_zones;
CREATE TABLE inputs_project_load_zones (
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
CREATE TABLE subscenarios_project_lf_reserves_up_bas (
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
CREATE TABLE inputs_project_lf_reserves_up_bas (
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
CREATE TABLE subscenarios_project_lf_reserves_down_bas (
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
CREATE TABLE inputs_project_lf_reserves_down_bas (
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


DROP TABLE IF EXISTS subscenarios_project_regulation_up_bas;
CREATE TABLE subscenarios_project_regulation_up_bas (
regulation_up_ba_scenario_id INTEGER,
project_regulation_up_ba_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (regulation_up_ba_scenario_id,
project_regulation_up_ba_scenario_id),
FOREIGN KEY (regulation_up_ba_scenario_id) REFERENCES
subscenarios_geography_regulation_up_bas (regulation_up_ba_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_regulation_up_bas;
CREATE TABLE inputs_project_regulation_up_bas (
regulation_up_ba_scenario_id INTEGER,
project_regulation_up_ba_scenario_id INTEGER,
project VARCHAR(64),
regulation_up_ba VARCHAR(32),
PRIMARY KEY (regulation_up_ba_scenario_id,
project_regulation_up_ba_scenario_id, project),
FOREIGN KEY (regulation_up_ba_scenario_id,
project_regulation_up_ba_scenario_id)
REFERENCES subscenarios_project_regulation_up_bas
 (regulation_up_ba_scenario_id, project_regulation_up_ba_scenario_id),
FOREIGN KEY (regulation_up_ba_scenario_id) REFERENCES
subscenarios_geography_regulation_up_bas (regulation_up_ba_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_regulation_down_bas;
CREATE TABLE subscenarios_project_regulation_down_bas (
regulation_down_ba_scenario_id INTEGER,
project_regulation_down_ba_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (regulation_down_ba_scenario_id,
project_regulation_down_ba_scenario_id),
FOREIGN KEY (regulation_down_ba_scenario_id) REFERENCES
subscenarios_geography_regulation_down_bas (regulation_down_ba_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_regulation_down_bas;
CREATE TABLE inputs_project_regulation_down_bas (
regulation_down_ba_scenario_id INTEGER,
project_regulation_down_ba_scenario_id INTEGER,
project VARCHAR(64),
regulation_down_ba VARCHAR(32),
PRIMARY KEY (regulation_down_ba_scenario_id,
project_regulation_down_ba_scenario_id, project),
FOREIGN KEY (regulation_down_ba_scenario_id,
project_regulation_down_ba_scenario_id)
REFERENCES subscenarios_project_regulation_down_bas
 (regulation_down_ba_scenario_id, project_regulation_down_ba_scenario_id),
FOREIGN KEY (regulation_down_ba_scenario_id) REFERENCES
subscenarios_geography_regulation_down_bas (regulation_down_ba_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_frequency_response_bas;
CREATE TABLE subscenarios_project_frequency_response_bas (
frequency_response_ba_scenario_id INTEGER,
project_frequency_response_ba_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (frequency_response_ba_scenario_id,
project_frequency_response_ba_scenario_id),
FOREIGN KEY (frequency_response_ba_scenario_id) REFERENCES
subscenarios_geography_frequency_response_bas
(frequency_response_ba_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_frequency_response_bas;
CREATE TABLE inputs_project_frequency_response_bas (
frequency_response_ba_scenario_id INTEGER,
project_frequency_response_ba_scenario_id INTEGER,
project VARCHAR(64),
frequency_response_ba VARCHAR(32),
contribute_to_partial INTEGER,
PRIMARY KEY (frequency_response_ba_scenario_id,
project_frequency_response_ba_scenario_id, project),
FOREIGN KEY (frequency_response_ba_scenario_id,
project_frequency_response_ba_scenario_id)
REFERENCES subscenarios_project_frequency_response_bas
 (frequency_response_ba_scenario_id, project_frequency_response_ba_scenario_id),
FOREIGN KEY (frequency_response_ba_scenario_id) REFERENCES
subscenarios_geography_frequency_response_bas
(frequency_response_ba_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_spinning_reserves_bas;
CREATE TABLE subscenarios_project_spinning_reserves_bas (
spinning_reserves_ba_scenario_id INTEGER,
project_spinning_reserves_ba_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (spinning_reserves_ba_scenario_id,
project_spinning_reserves_ba_scenario_id),
FOREIGN KEY (spinning_reserves_ba_scenario_id) REFERENCES
subscenarios_geography_spinning_reserves_bas (spinning_reserves_ba_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_spinning_reserves_bas;
CREATE TABLE inputs_project_spinning_reserves_bas (
spinning_reserves_ba_scenario_id INTEGER,
project_spinning_reserves_ba_scenario_id INTEGER,
project VARCHAR(64),
spinning_reserves_ba VARCHAR(32),
PRIMARY KEY (spinning_reserves_ba_scenario_id,
project_spinning_reserves_ba_scenario_id, project),
FOREIGN KEY (spinning_reserves_ba_scenario_id,
project_spinning_reserves_ba_scenario_id)
REFERENCES subscenarios_project_spinning_reserves_bas
 (spinning_reserves_ba_scenario_id, project_spinning_reserves_ba_scenario_id),
FOREIGN KEY (spinning_reserves_ba_scenario_id) REFERENCES
subscenarios_geography_spinning_reserves_bas (spinning_reserves_ba_scenario_id)
);

-- Project RPS zones
-- Which projects can contribute to RPS requirements
-- Depends on how RPS zones are specified
-- This table can include all project with NULLs for projects not
-- contributing or just the contributing projects
DROP TABLE IF EXISTS subscenarios_project_rps_zones;
CREATE TABLE subscenarios_project_rps_zones (
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
CREATE TABLE inputs_project_rps_zones (
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
-- This table can include all project with NULLs for projects not
-- contributing or just the contributing projects
DROP TABLE IF EXISTS subscenarios_project_carbon_cap_zones;
CREATE TABLE subscenarios_project_carbon_cap_zones (
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
CREATE TABLE inputs_project_carbon_cap_zones (
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

-- Project PRM zones
-- Which projects can contribute to PRM requirements
-- Depends on how PRM zones are specified
-- This table can include all project with NULLs for projects not
-- contributing or just the contributing projects

DROP TABLE IF EXISTS subscenarios_project_prm_zones;
CREATE TABLE subscenarios_project_prm_zones (
prm_zone_scenario_id INTEGER,
project_prm_zone_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (prm_zone_scenario_id,
project_prm_zone_scenario_id),
FOREIGN KEY (prm_zone_scenario_id) REFERENCES
subscenarios_geography_prm_zones (prm_zone_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_prm_zones;
CREATE TABLE inputs_project_prm_zones (
prm_zone_scenario_id INTEGER,
project_prm_zone_scenario_id INTEGER,
project VARCHAR(64),
prm_zone VARCHAR(32),
PRIMARY KEY (prm_zone_scenario_id, project_prm_zone_scenario_id, project),
FOREIGN KEY (prm_zone_scenario_id, project_prm_zone_scenario_id) REFERENCES
 subscenarios_project_prm_zones
 (prm_zone_scenario_id, project_prm_zone_scenario_id),
FOREIGN KEY (prm_zone_scenario_id) REFERENCES
subscenarios_geography_prm_zones (prm_zone_scenario_id)
);

-- Project capacity contribution characteristics (simple ELCC treatment or
-- treatment via an ELCC surface
DROP TABLE IF EXISTS subscenarios_project_elcc_chars;
CREATE TABLE subscenarios_project_elcc_chars (
project_elcc_chars_scenario_id INTEGER PRIMARY KEY,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_elcc_chars;
CREATE TABLE inputs_project_elcc_chars (
project_elcc_chars_scenario_id INTEGER,
project VARCHAR(64),
prm_type VARCHAR(32),
elcc_simple_fraction FLOAT,
contributes_to_elcc_surface INTEGER,
min_duration_for_full_capacity_credit_hours FLOAT,
deliverability_group VARCHAR(64),  --optional
PRIMARY KEY (project_elcc_chars_scenario_id, project),
FOREIGN KEY (project_elcc_chars_scenario_id) REFERENCES
subscenarios_project_elcc_chars (project_elcc_chars_scenario_id)
);

-- ELCC surface
-- Depends on how PRM zones are defined
DROP TABLE IF EXISTS subscenarios_system_elcc_surface;
CREATE TABLE subscenarios_system_elcc_surface (
prm_zone_scenario_id INTEGER,
elcc_surface_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (prm_zone_scenario_id, elcc_surface_scenario_id),
FOREIGN KEY (prm_zone_scenario_id) REFERENCES
subscenarios_geography_prm_zones (prm_zone_scenario_id)
);

-- ELCC surface intercept by PRM zone
DROP TABLE IF EXISTS inputs_system_prm_zone_elcc_surface;
CREATE TABLE inputs_system_prm_zone_elcc_surface (
prm_zone_scenario_id INTEGER,
elcc_surface_scenario_id INTEGER,
prm_zone VARCHAR(32),
period INTEGER,
facet INTEGER,
elcc_surface_intercept FLOAT,
PRIMARY KEY (prm_zone_scenario_id, elcc_surface_scenario_id, prm_zone, period,
facet),
FOREIGN KEY (prm_zone_scenario_id, elcc_surface_scenario_id) REFERENCES
subscenarios_system_elcc_surface (prm_zone_scenario_id,
elcc_surface_scenario_id),
FOREIGN KEY (prm_zone_scenario_id, prm_zone) REFERENCES
inputs_geography_prm_zones (prm_zone_scenario_id, prm_zone)
);

DROP TABLE IF EXISTS inputs_project_elcc_surface;
CREATE TABLE inputs_project_elcc_surface (
prm_zone_scenario_id INTEGER,
project_prm_zone_scenario_id INTEGER,
elcc_surface_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
facet INTEGER,
elcc_surface_coefficient FLOAT,
PRIMARY KEY (project_prm_zone_scenario_id, elcc_surface_scenario_id,
project, period, facet),
FOREIGN KEY (prm_zone_scenario_id, project_prm_zone_scenario_id) REFERENCES
subscenarios_project_prm_zones
(prm_zone_scenario_id, project_prm_zone_scenario_id)
);

-- Energy-only parameters
DROP TABLE IF EXISTS subscenarios_project_prm_energy_only;
CREATE TABLE subscenarios_project_prm_energy_only (
prm_energy_only_scenario_id INTEGER PRIMARY KEY
AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_prm_energy_only;
CREATE TABLE inputs_project_prm_energy_only (
prm_energy_only_scenario_id INTEGER,
deliverability_group VARCHAR(64),
deliverability_group_no_cost_deliverable_capacity_mw FLOAT,
deliverability_group_deliverability_cost_per_mw FLOAT,
deliverability_group_energy_only_capacity_limit_mw FLOAT,
PRIMARY KEY (prm_energy_only_scenario_id, deliverability_group),
FOREIGN KEY (prm_energy_only_scenario_id) REFERENCES
subscenarios_project_prm_energy_only
(prm_energy_only_scenario_id)
);


-- Project local capacity zones and chars
-- Which projects can contribute to local capacity requirements
-- Depends on how local capacity zones are specified
-- This table can include all project with NULLs for projects not
-- contributing or just the contributing projects

DROP TABLE IF EXISTS subscenarios_project_local_capacity_zones;
CREATE TABLE subscenarios_project_local_capacity_zones (
local_capacity_zone_scenario_id INTEGER,
project_local_capacity_zone_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (local_capacity_zone_scenario_id,
project_local_capacity_zone_scenario_id),
FOREIGN KEY (local_capacity_zone_scenario_id) REFERENCES
subscenarios_geography_local_capacity_zones (local_capacity_zone_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_local_capacity_zones;
CREATE TABLE inputs_project_local_capacity_zones (
local_capacity_zone_scenario_id INTEGER,
project_local_capacity_zone_scenario_id INTEGER,
project VARCHAR(64),
local_capacity_zone VARCHAR(32),
PRIMARY KEY (local_capacity_zone_scenario_id,
project_local_capacity_zone_scenario_id, project),
FOREIGN KEY (local_capacity_zone_scenario_id,
project_local_capacity_zone_scenario_id) REFERENCES
 subscenarios_project_local_capacity_zones
 (local_capacity_zone_scenario_id, project_local_capacity_zone_scenario_id),
FOREIGN KEY (local_capacity_zone_scenario_id) REFERENCES
subscenarios_geography_local_capacity_zones (local_capacity_zone_scenario_id)
);

-- Project capacity contribution characteristics
DROP TABLE IF EXISTS subscenarios_project_local_capacity_chars;
CREATE TABLE subscenarios_project_local_capacity_chars (
project_local_capacity_chars_scenario_id INTEGER PRIMARY KEY,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_local_capacity_chars;
CREATE TABLE inputs_project_local_capacity_chars (
project_local_capacity_chars_scenario_id INTEGER,
project VARCHAR(64),
local_capacity_fraction FLOAT,
min_duration_for_full_capacity_credit_hours FLOAT,
PRIMARY KEY (project_local_capacity_chars_scenario_id, project),
FOREIGN KEY (project_local_capacity_chars_scenario_id) REFERENCES
subscenarios_project_local_capacity_chars
(project_local_capacity_chars_scenario_id)
);

-- Fuels
DROP TABLE IF EXISTS subscenarios_project_fuels;
CREATE TABLE subscenarios_project_fuels (
fuel_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_fuels;
CREATE TABLE inputs_project_fuels (
fuel_scenario_id INTEGER,
fuel VARCHAR(32),
co2_intensity_tons_per_mmbtu FLOAT,
PRIMARY KEY (fuel_scenario_id, fuel),
FOREIGN KEY (fuel_scenario_id) REFERENCES subscenarios_project_fuels
(fuel_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_fuel_prices;
CREATE TABLE subscenarios_project_fuel_prices (
fuel_price_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_fuel_prices;
CREATE TABLE inputs_project_fuel_prices (
fuel_price_scenario_id INTEGER,
fuel VARCHAR(32),
period INTEGER,
month INTEGER,
fuel_price_per_mmbtu FLOAT,
PRIMARY KEY (fuel_price_scenario_id, fuel, period, month),
FOREIGN KEY (fuel_price_scenario_id) REFERENCES
subscenarios_project_fuel_prices (fuel_price_scenario_id)
);



------------------
-- TRANSMISSION --
------------------

-- Transmission portfolios
DROP TABLE IF EXISTS subscenarios_transmission_portfolios;
CREATE TABLE subscenarios_transmission_portfolios (
transmission_portfolio_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_transmission_portfolios;
CREATE TABLE inputs_transmission_portfolios (
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
CREATE TABLE subscenarios_transmission_load_zones (
load_zone_scenario_id INTEGER,
transmission_load_zone_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (load_zone_scenario_id, transmission_load_zone_scenario_id),
FOREIGN KEY (load_zone_scenario_id) REFERENCES
subscenarios_geography_load_zones (load_zone_scenario_id)
);

DROP TABLE IF EXISTS inputs_transmission_load_zones;
CREATE TABLE inputs_transmission_load_zones (
load_zone_scenario_id INTEGER,
transmission_load_zone_scenario_id INTEGER,
transmission_line VARCHAR(64),
load_zone_from VARCHAR(32),
load_zone_to VARCHAR(32),
PRIMARY KEY (load_zone_scenario_id, transmission_load_zone_scenario_id,
transmission_line),
FOREIGN KEY (load_zone_scenario_id, transmission_load_zone_scenario_id)
REFERENCES subscenarios_transmission_load_zones (load_zone_scenario_id,
transmission_load_zone_scenario_id),
FOREIGN KEY (load_zone_scenario_id) REFERENCES
subscenarios_geography_load_zones
(load_zone_scenario_id)
);

-- Carbon cap zones
-- This is needed if the carbon cap module is enabled and we want to track
-- emission imports
DROP TABLE IF EXISTS subscenarios_transmission_carbon_cap_zones;
CREATE TABLE subscenarios_transmission_carbon_cap_zones (
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
CREATE TABLE inputs_transmission_carbon_cap_zones (
carbon_cap_zone_scenario_id INTEGER,
transmission_carbon_cap_zone_scenario_id INTEGER,
transmission_line VARCHAR(64),
carbon_cap_zone VARCHAR(32),
import_direction VARCHAR(8),
tx_co2_intensity_tons_per_mwh FLOAT,
PRIMARY KEY (carbon_cap_zone_scenario_id,
transmission_carbon_cap_zone_scenario_id,
transmission_line),
FOREIGN KEY (carbon_cap_zone_scenario_id,
transmission_carbon_cap_zone_scenario_id) REFERENCES
subscenarios_transmission_carbon_cap_zones (carbon_cap_zone_scenario_id,
transmission_carbon_cap_zone_scenario_id),
FOREIGN KEY (carbon_cap_zone_scenario_id) REFERENCES
subscenarios_geography_carbon_cap_zones
(carbon_cap_zone_scenario_id)
);

-- Existing transmission capacity
DROP TABLE IF EXISTS subscenarios_transmission_existing_capacity;
CREATE TABLE subscenarios_transmission_existing_capacity (
transmission_existing_capacity_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_transmission_existing_capacity;
CREATE TABLE inputs_transmission_existing_capacity (
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
CREATE TABLE subscenarios_transmission_operational_chars (
transmission_operational_chars_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_transmission_operational_chars;
CREATE TABLE inputs_transmission_operational_chars (
transmission_operational_chars_scenario_id INTEGER,
transmission_line VARCHAR(64),
PRIMARY KEY (transmission_operational_chars_scenario_id, transmission_line),
FOREIGN KEY (transmission_operational_chars_scenario_id) REFERENCES
subscenarios_transmission_operational_chars
(transmission_operational_chars_scenario_id)
);

-- Hurdle rates
DROP TABLE IF EXISTS subscenarios_transmission_hurdle_rates;
CREATE TABLE subscenarios_transmission_hurdle_rates (
transmission_hurdle_rate_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_transmission_hurdle_rates;
CREATE TABLE inputs_transmission_hurdle_rates (
transmission_hurdle_rate_scenario_id INTEGER,
transmission_line INTEGER,
period INTEGER,
hurdle_rate_positive_direction_per_mwh FLOAT,
hurdle_rate_negative_direction_per_mwh FLOAT,
PRIMARY KEY (transmission_hurdle_rate_scenario_id, transmission_line, period),
FOREIGN KEY (transmission_hurdle_rate_scenario_id) REFERENCES
subscenarios_transmission_hurdle_rates (transmission_hurdle_rate_scenario_id)
);

-- Simultaneous flows
-- Limits on net flows on groups of lines (e.g. all lines connected to a zone)
DROP TABLE IF EXISTS subscenarios_transmission_simultaneous_flow_limits;
CREATE TABLE subscenarios_transmission_simultaneous_flow_limits (
transmission_simultaneous_flow_limit_scenario_id INTEGER
PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_transmission_simultaneous_flow_limits;
CREATE TABLE inputs_transmission_simultaneous_flow_limits (
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
CREATE TABLE subscenarios_transmission_simultaneous_flow_limit_line_groups (
transmission_simultaneous_flow_limit_line_group_scenario_id INTEGER PRIMARY KEY
AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_transmission_simultaneous_flow_limit_line_groups;
CREATE TABLE inputs_transmission_simultaneous_flow_limit_line_groups (
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
CREATE TABLE subscenarios_system_load (
load_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include timepoints and zones other than the ones in a scenario, as
-- correct timepoints and zones will be pulled depending on
-- timepoint_scenario_id and load_zone_scenario_id
DROP TABLE IF EXISTS inputs_system_load;
CREATE TABLE inputs_system_load (
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
CREATE TABLE subscenarios_system_lf_reserves_up (
lf_reserves_up_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include timepoints and zones other than the ones in a scenario, as
-- correct timepoints and zones will be pulled depending on
-- timepoint_scenario_id and reserves_scenario_id
DROP TABLE IF EXISTS inputs_system_lf_reserves_up;
CREATE TABLE inputs_system_lf_reserves_up (
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
CREATE TABLE subscenarios_system_lf_reserves_down (
lf_reserves_down_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include timepoints and zones other than the ones in a scenario, as
-- correct timepoints and zones will be pulled depending on
-- timepoint_scenario_id and reserves_scenario_id
DROP TABLE IF EXISTS inputs_system_lf_reserves_down;
CREATE TABLE inputs_system_lf_reserves_down (
lf_reserves_down_scenario_id INTEGER,
lf_reserves_down_ba VARCHAR(32),
timepoint INTEGER,
lf_reserves_down_mw FLOAT,
PRIMARY KEY (lf_reserves_down_scenario_id, lf_reserves_down_ba, timepoint),
FOREIGN KEY (lf_reserves_down_scenario_id) REFERENCES
subscenarios_system_lf_reserves_down (lf_reserves_down_scenario_id)
);

-- Regulation up
DROP TABLE IF EXISTS subscenarios_system_regulation_up;
CREATE TABLE subscenarios_system_regulation_up (
regulation_up_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include timepoints and zones other than the ones in a scenario, as
-- correct timepoints and zones will be pulled depending on
-- timepoint_scenario_id and reserves_scenario_id
DROP TABLE IF EXISTS inputs_system_regulation_up;
CREATE TABLE inputs_system_regulation_up (
regulation_up_scenario_id INTEGER,
regulation_up_ba VARCHAR(32),
timepoint INTEGER,
regulation_up_mw FLOAT,
PRIMARY KEY (regulation_up_scenario_id, regulation_up_ba, timepoint),
FOREIGN KEY (regulation_up_scenario_id) REFERENCES
subscenarios_system_regulation_up (regulation_up_scenario_id)
);

-- Regulation down
DROP TABLE IF EXISTS subscenarios_system_regulation_down;
CREATE TABLE subscenarios_system_regulation_down (
regulation_down_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include timepoints and zones other than the ones in a scenario, as
-- correct timepoints and zones will be pulled depending on
-- timepoint_scenario_id and reserves_scenario_id
DROP TABLE IF EXISTS inputs_system_regulation_down;
CREATE TABLE inputs_system_regulation_down (
regulation_down_scenario_id INTEGER,
regulation_down_ba VARCHAR(32),
timepoint INTEGER,
regulation_down_mw FLOAT,
PRIMARY KEY (regulation_down_scenario_id, regulation_down_ba, timepoint),
FOREIGN KEY (regulation_down_scenario_id) REFERENCES
subscenarios_system_regulation_down (regulation_down_scenario_id)
);

-- Frequency response
DROP TABLE IF EXISTS subscenarios_system_frequency_response;
CREATE TABLE subscenarios_system_frequency_response (
frequency_response_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include timepoints and zones other than the ones in a scenario, as
-- correct timepoints and zones will be pulled depending on
-- timepoint_scenario_id and reserves_scenario_id
DROP TABLE IF EXISTS inputs_system_frequency_response;
CREATE TABLE inputs_system_frequency_response (
frequency_response_scenario_id INTEGER,
frequency_response_ba VARCHAR(32),
timepoint INTEGER,
frequency_response_mw FLOAT,
frequency_response_partial_mw FLOAT,
PRIMARY KEY (frequency_response_scenario_id, frequency_response_ba, timepoint),
FOREIGN KEY (frequency_response_scenario_id) REFERENCES
subscenarios_system_frequency_response (frequency_response_scenario_id)
);

-- Spinning reserves
DROP TABLE IF EXISTS subscenarios_system_spinning_reserves;
CREATE TABLE subscenarios_system_spinning_reserves (
spinning_reserves_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include timepoints and zones other than the ones in a scenario, as
-- correct timepoints and zones will be pulled depending on
-- timepoint_scenario_id and reserves_scenario_id
DROP TABLE IF EXISTS inputs_system_spinning_reserves;
CREATE TABLE inputs_system_spinning_reserves (
spinning_reserves_scenario_id INTEGER,
spinning_reserves_ba VARCHAR(32),
timepoint INTEGER,
spinning_reserves_mw FLOAT,
PRIMARY KEY (spinning_reserves_scenario_id, spinning_reserves_ba, timepoint),
FOREIGN KEY (spinning_reserves_scenario_id) REFERENCES
subscenarios_system_spinning_reserves (spinning_reserves_scenario_id)
);

-- -- Policy -- --

-- RPS requirements

DROP TABLE IF EXISTS subscenarios_system_rps_targets;
CREATE TABLE subscenarios_system_rps_targets (
rps_target_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include periods and zones other than the ones in a scenario, as correct
-- periods and zones will be pulled depending on timepoint_scenario_id and
-- rps_zone_scenario_id
DROP TABLE IF EXISTS inputs_system_rps_targets;
CREATE TABLE inputs_system_rps_targets (
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
CREATE TABLE subscenarios_system_carbon_cap_targets (
carbon_cap_target_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include periods and zones other than the ones in a scenario, as correct
-- periods and zones will be pulled depending on timepoint_scenario_id and
-- carbon_cap_zone_scenario_id
DROP TABLE IF EXISTS inputs_system_carbon_cap_targets;
CREATE TABLE inputs_system_carbon_cap_targets (
carbon_cap_target_scenario_id INTEGER,
carbon_cap_zone VARCHAR(32),
period INTEGER,
carbon_cap_mmt FLOAT,
PRIMARY KEY (carbon_cap_target_scenario_id, carbon_cap_zone, period),
FOREIGN KEY (carbon_cap_target_scenario_id) REFERENCES
subscenarios_system_carbon_cap_targets (carbon_cap_target_scenario_id)
);

-- PRM requirements
DROP TABLE IF EXISTS subscenarios_system_prm_requirement;
CREATE TABLE subscenarios_system_prm_requirement (
prm_requirement_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include periods and zones other than the ones in a scenario, as correct
-- periods and zones will be pulled depending on timepoint_scenario_id and
-- prm_zone_scenario_id
DROP TABLE IF EXISTS inputs_system_prm_requirement;
CREATE TABLE inputs_system_prm_requirement (
prm_requirement_scenario_id INTEGER,
prm_zone VARCHAR(32),
period INTEGER,
prm_requirement_mw FLOAT,
prm_zone_scenario_id INTEGER,
PRIMARY KEY (prm_requirement_scenario_id, prm_zone, period),
FOREIGN KEY (prm_zone_scenario_id, prm_zone) REFERENCES
inputs_geography_prm_zones (prm_zone_scenario_id, prm_zone)
);

-- Local capacity requirements
DROP TABLE IF EXISTS subscenarios_system_local_capacity_requirement;
CREATE TABLE subscenarios_system_local_capacity_requirement (
local_capacity_requirement_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include periods and zones other than the ones in a scenario, as correct
-- periods and zones will be pulled depending on timepoint_scenario_id and
-- local_capacity_zone_scenario_id
DROP TABLE IF EXISTS inputs_system_local_capacity_requirement;
CREATE TABLE inputs_system_local_capacity_requirement (
local_capacity_requirement_scenario_id INTEGER,
local_capacity_zone VARCHAR(32),
period INTEGER,
local_capacity_requirement_mw FLOAT,
local_capacity_zone_scenario_id INTEGER,
PRIMARY KEY (local_capacity_requirement_scenario_id, local_capacity_zone,
period),
FOREIGN KEY (local_capacity_zone_scenario_id, local_capacity_zone) REFERENCES
inputs_geography_local_capacity_zones (local_capacity_zone_scenario_id,
local_capacity_zone)
);

-- Case tuning
DROP TABLE IF EXISTS subscenarios_tuning;
CREATE TABLE subscenarios_tuning (
tuning_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_tuning;
CREATE TABLE inputs_tuning (
tuning_scenario_id INTEGER PRIMARY KEY,
import_carbon_tuning_cost DOUBLE,
ramp_tuning_cost DOUBLE,
dynamic_elcc_tuning_cost DOUBLE,
FOREIGN KEY (tuning_scenario_id) REFERENCES subscenarios_tuning
(tuning_scenario_id)
);

---------------------
-- -- SCENARIOS -- --
---------------------
DROP TABLE IF EXISTS scenarios;
CREATE TABLE scenarios (
scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
scenario_name VARCHAR(64) UNIQUE,
of_fuels INTEGER,
of_multi_stage INTEGER,
of_transmission INTEGER,
of_transmission_hurdle_rates INTEGER,
of_simultaneous_flow_limits INTEGER,
of_lf_reserves_up INTEGER,
of_lf_reserves_down INTEGER,
of_regulation_up INTEGER,
of_regulation_down INTEGER,
of_frequency_response INTEGER,
of_spinning_reserves INTEGER,
of_rps INTEGER,
of_carbon_cap INTEGER,
of_track_carbon_imports INTEGER,
of_prm INTEGER,
of_elcc_surface INTEGER,
of_local_capacity INTEGER,
timepoint_scenario_id INTEGER,
load_zone_scenario_id INTEGER,
lf_reserves_up_ba_scenario_id INTEGER,
lf_reserves_down_ba_scenario_id INTEGER,
regulation_up_ba_scenario_id INTEGER,
regulation_down_ba_scenario_id INTEGER,
frequency_response_ba_scenario_id INTEGER,
spinning_reserves_ba_scenario_id INTEGER,
rps_zone_scenario_id INTEGER,
carbon_cap_zone_scenario_id INTEGER,
prm_zone_scenario_id INTEGER,
local_capacity_zone_scenario_id INTEGER,
project_portfolio_scenario_id INTEGER,
project_operational_chars_scenario_id INTEGER,
project_availability_scenario_id INTEGER,
fuel_scenario_id INTEGER,
project_load_zone_scenario_id INTEGER,
project_lf_reserves_up_ba_scenario_id INTEGER,
project_lf_reserves_down_ba_scenario_id INTEGER,
project_regulation_up_ba_scenario_id INTEGER,
project_regulation_down_ba_scenario_id INTEGER,
project_frequency_response_ba_scenario_id INTEGER,
project_spinning_reserves_ba_scenario_id INTEGER,
project_rps_zone_scenario_id INTEGER,
project_carbon_cap_zone_scenario_id INTEGER,
project_prm_zone_scenario_id INTEGER,
project_elcc_chars_scenario_id INTEGER,
prm_energy_only_scenario_id INTEGER,
project_local_capacity_zone_scenario_id INTEGER,
project_local_capacity_chars_scenario_id INTEGER,
project_existing_capacity_scenario_id INTEGER,
project_existing_fixed_cost_scenario_id INTEGER,
fuel_price_scenario_id INTEGER,
project_new_cost_scenario_id INTEGER,
project_new_potential_scenario_id INTEGER,
transmission_portfolio_scenario_id INTEGER,
transmission_load_zone_scenario_id INTEGER,
transmission_existing_capacity_scenario_id INTEGER,
transmission_operational_chars_scenario_id INTEGER,
transmission_hurdle_rate_scenario_id INTEGER,
transmission_carbon_cap_zone_scenario_id INTEGER,
transmission_simultaneous_flow_limit_scenario_id INTEGER,
transmission_simultaneous_flow_limit_line_group_scenario_id INTEGER,
load_scenario_id INTEGER,
lf_reserves_up_scenario_id INTEGER,
lf_reserves_down_scenario_id INTEGER,
regulation_up_scenario_id INTEGER,
regulation_down_scenario_id INTEGER,
frequency_response_scenario_id INTEGER,
spinning_reserves_scenario_id INTEGER,
rps_target_scenario_id INTEGER,
carbon_cap_target_scenario_id INTEGER,
prm_requirement_scenario_id INTEGER,
local_capacity_requirement_scenario_id INTEGER,
elcc_surface_scenario_id INTEGER,
tuning_scenario_id INTEGER,
FOREIGN KEY (timepoint_scenario_id) REFERENCES
subscenarios_temporal_timepoints (timepoint_scenario_id),
FOREIGN KEY (load_zone_scenario_id) REFERENCES
subscenarios_geography_load_zones (load_zone_scenario_id),
FOREIGN KEY (lf_reserves_up_ba_scenario_id) REFERENCES
subscenarios_geography_lf_reserves_up_bas (lf_reserves_up_ba_scenario_id),
FOREIGN KEY (lf_reserves_down_ba_scenario_id) REFERENCES
subscenarios_geography_lf_reserves_down_bas (lf_reserves_down_ba_scenario_id),
FOREIGN KEY (regulation_up_ba_scenario_id) REFERENCES
subscenarios_geography_regulation_up_bas (regulation_up_ba_scenario_id),
FOREIGN KEY (regulation_down_ba_scenario_id) REFERENCES
subscenarios_geography_regulation_down_bas (regulation_down_ba_scenario_id),
FOREIGN KEY (frequency_response_ba_scenario_id) REFERENCES
subscenarios_geography_frequency_response_bas
(frequency_response_ba_scenario_id),
FOREIGN KEY (spinning_reserves_ba_scenario_id) REFERENCES
subscenarios_geography_spinning_reserves_bas (spinning_reserves_ba_scenario_id),
FOREIGN KEY (rps_zone_scenario_id) REFERENCES
subscenarios_geography_rps_zones (rps_zone_scenario_id),
FOREIGN KEY (carbon_cap_zone_scenario_id) REFERENCES
subscenarios_geography_carbon_cap_zones (carbon_cap_zone_scenario_id),
FOREIGN KEY (prm_zone_scenario_id) REFERENCES
subscenarios_geography_prm_zones (prm_zone_scenario_id),
FOREIGN KEY (local_capacity_zone_scenario_id) REFERENCES
subscenarios_geography_local_capacity_zones (local_capacity_zone_scenario_id),
FOREIGN KEY (project_portfolio_scenario_id) REFERENCES
subscenarios_project_portfolios (project_portfolio_scenario_id),
FOREIGN KEY (project_operational_chars_scenario_id) REFERENCES
subscenarios_project_operational_chars (project_operational_chars_scenario_id),
FOREIGN KEY (project_availability_scenario_id) REFERENCES
subscenarios_project_availability (project_availability_scenario_id),
FOREIGN KEY (fuel_scenario_id) REFERENCES
subscenarios_project_fuels (fuel_scenario_id),
FOREIGN KEY (fuel_price_scenario_id) REFERENCES
subscenarios_project_fuel_prices (fuel_price_scenario_id),
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
FOREIGN KEY (regulation_up_ba_scenario_id,
project_regulation_up_ba_scenario_id) REFERENCES
subscenarios_project_regulation_up_bas
(regulation_up_ba_scenario_id, project_regulation_up_ba_scenario_id),
FOREIGN KEY (regulation_down_ba_scenario_id,
project_regulation_down_ba_scenario_id) REFERENCES
subscenarios_project_regulation_down_bas
(regulation_down_ba_scenario_id, project_regulation_down_ba_scenario_id),
FOREIGN KEY (frequency_response_ba_scenario_id,
project_frequency_response_ba_scenario_id) REFERENCES
subscenarios_project_frequency_response_bas
(frequency_response_ba_scenario_id, project_frequency_response_ba_scenario_id),
FOREIGN KEY (spinning_reserves_ba_scenario_id,
project_spinning_reserves_ba_scenario_id) REFERENCES
subscenarios_project_spinning_reserves_bas
(spinning_reserves_ba_scenario_id, project_spinning_reserves_ba_scenario_id),
FOREIGN KEY (rps_zone_scenario_id, project_rps_zone_scenario_id) REFERENCES
subscenarios_project_rps_zones
(rps_zone_scenario_id, project_rps_zone_scenario_id),
FOREIGN KEY (carbon_cap_zone_scenario_id,
project_carbon_cap_zone_scenario_id) REFERENCES
subscenarios_project_carbon_cap_zones
(carbon_cap_zone_scenario_id, project_carbon_cap_zone_scenario_id),
FOREIGN KEY (prm_zone_scenario_id, project_prm_zone_scenario_id) REFERENCES
subscenarios_project_prm_zones
(prm_zone_scenario_id, project_prm_zone_scenario_id),
FOREIGN KEY (project_elcc_chars_scenario_id) REFERENCES
subscenarios_project_elcc_chars (project_elcc_chars_scenario_id),
FOREIGN KEY (prm_energy_only_scenario_id) REFERENCES
subscenarios_project_prm_energy_only
(prm_energy_only_scenario_id),
FOREIGN KEY (local_capacity_zone_scenario_id,
project_local_capacity_zone_scenario_id) REFERENCES
subscenarios_project_local_capacity_zones
(local_capacity_zone_scenario_id, project_local_capacity_zone_scenario_id),
FOREIGN KEY (project_local_capacity_chars_scenario_id) REFERENCES
subscenarios_project_local_capacity_chars
(project_local_capacity_chars_scenario_id),
FOREIGN KEY (project_existing_capacity_scenario_id) REFERENCES
subscenarios_project_existing_capacity (project_existing_capacity_scenario_id),
FOREIGN KEY (project_existing_fixed_cost_scenario_id) REFERENCES
subscenarios_project_existing_fixed_cost
(project_existing_fixed_cost_scenario_id),
FOREIGN KEY (project_new_cost_scenario_id) REFERENCES
subscenarios_project_new_cost (project_new_cost_scenario_id),
FOREIGN KEY (project_new_potential_scenario_id) REFERENCES
subscenarios_project_new_potential (project_new_potential_scenario_id),
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
FOREIGN KEY (transmission_hurdle_rate_scenario_id) REFERENCES
subscenarios_transmission_hurdle_rates (transmission_hurdle_rate_scenario_id),
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
FOREIGN KEY (regulation_up_scenario_id) REFERENCES
subscenarios_system_regulation_up (regulation_up_scenario_id),
FOREIGN KEY (regulation_down_scenario_id) REFERENCES
subscenarios_system_regulation_down (regulation_down_scenario_id),
FOREIGN KEY (frequency_response_scenario_id) REFERENCES
subscenarios_system_frequency_response (frequency_response_scenario_id),
FOREIGN KEY (rps_target_scenario_id) REFERENCES
subscenarios_system_rps_targets (rps_target_scenario_id),
FOREIGN KEY (carbon_cap_target_scenario_id) REFERENCES
subscenarios_system_carbon_cap_targets (carbon_cap_target_scenario_id),
FOREIGN KEY (prm_requirement_scenario_id) REFERENCES
subscenarios_system_prm_requirement (prm_requirement_scenario_id),
FOREIGN KEY (prm_zone_scenario_id, elcc_surface_scenario_id) REFERENCES
subscenarios_system_elcc_surface
(prm_zone_scenario_id, elcc_surface_scenario_id),
FOREIGN KEY (local_capacity_requirement_scenario_id) REFERENCES
subscenarios_system_local_capacity_requirement
(local_capacity_requirement_scenario_id),
FOREIGN KEY (tuning_scenario_id) REFERENCES subscenarios_tuning
(tuning_scenario_id)
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
CREATE TABLE results_project_capacity_all (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
technology VARCHAR(32),
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
capacity_mw FLOAT,
energy_capacity_mwh FLOAT,
PRIMARY KEY (scenario_id, project, period)
);

DROP TABLE IF EXISTS results_project_capacity_new_build_generator;
CREATE TABLE results_project_capacity_new_build_generator (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
technology VARCHAR(32),
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
new_build_mw FLOAT,
PRIMARY KEY (scenario_id, project, period)
);

DROP TABLE IF EXISTS results_project_capacity_new_build_storage;
CREATE TABLE results_project_capacity_new_build_storage (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
technology VARCHAR(32),
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
new_build_mw FLOAT,
new_build_mwh FLOAT,
PRIMARY KEY (scenario_id, project, period)
);

DROP TABLE IF EXISTS results_project_capacity_linear_economic_retirement;
CREATE TABLE results_project_capacity_linear_economic_retirement (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
technology VARCHAR(32),
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
retired_mw FLOAT,
PRIMARY KEY (scenario_id, project, period)
);

DROP TABLE IF EXISTS results_project_capacity_binary_economic_retirement;
CREATE TABLE results_project_capacity_binary_economic_retirement (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
technology VARCHAR(32),
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
retired_mw FLOAT,
PRIMARY KEY (scenario_id, project, period)
);

DROP TABLE IF EXISTS results_project_dispatch_all;
CREATE TABLE results_project_dispatch_all (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
power_mw FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_dispatch_variable;
CREATE TABLE results_project_dispatch_variable (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
power_mw FLOAT,
scheduled_curtailment_mw FLOAT,
subhourly_curtailment_mw FLOAT,
subhourly_energy_delivered_mw FLOAT,
total_curtailment_mw FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_dispatch_hydro_curtailable;
CREATE TABLE results_project_dispatch_hydro_curtailable (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
power_mw FLOAT,
scheduled_curtailment_mw FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_dispatch_capacity_commit;
CREATE TABLE results_project_dispatch_capacity_commit (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
power_mw FLOAT,
committed_mw FLOAT,
committed_units FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_lf_reserves_up;
CREATE TABLE results_project_lf_reserves_up (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
lf_reserves_up_ba VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
reserve_provision_mw FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_lf_reserves_down;
CREATE TABLE results_project_lf_reserves_down (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
lf_reserves_down_ba VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
reserve_provision_mw FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_regulation_up;
CREATE TABLE results_project_regulation_up (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
regulation_up_ba VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
reserve_provision_mw FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_regulation_down;
CREATE TABLE results_project_regulation_down (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
regulation_down_ba VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
reserve_provision_mw FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_frequency_response;
CREATE TABLE results_project_frequency_response (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
frequency_response_ba VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
reserve_provision_mw FLOAT,
partial INTEGER,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_spinning_reserves;
CREATE TABLE results_project_spinning_reserves (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
spinning_reserves_ba VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
reserve_provision_mw FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_prm_deliverability;
CREATE TABLE results_project_prm_deliverability (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
prm_zone VARCHAR(32),
technology VARCHAR(32),
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
capacity_mw FLOAT,
deliverable_capacity_mw FLOAT,
energy_only_capacity_mw FLOAT,
PRIMARY KEY (scenario_id, project, period)
);

DROP TABLE IF EXISTS
results_project_prm_deliverability_group_capacity_and_costs;
CREATE TABLE results_project_prm_deliverability_group_capacity_and_costs (
scenario_id INTEGER,
deliverability_group VARCHAR(64),
period INTEGER,
deliverability_group_no_cost_deliverable_capacity_mw FLOAT,
deliverability_group_deliverability_cost_per_mw FLOAT,
total_capacity_mw FLOAT,
deliverable_capacity_mw FLOAT,
energy_only_capacity_mw FLOAT,
deliverable_capacity_cost FLOAT,
PRIMARY KEY (scenario_id, deliverability_group, period)
);

DROP TABLE IF EXISTS results_project_elcc_simple;
CREATE TABLE results_project_elcc_simple (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
prm_zone VARCHAR(32),
technology VARCHAR(32),
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
capacity_mw FLOAT,
elcc_eligible_capacity_mw FLOAT,
energy_only_capacity_mw FLOAT,
elcc_simple_contribution_fraction FLOAT,
elcc_mw FLOAT,
PRIMARY KEY (scenario_id, project, period)
);

DROP TABLE IF EXISTS results_project_elcc_surface;
CREATE TABLE results_project_elcc_surface (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
prm_zone VARCHAR(32),
facet INTEGER,
technology VARCHAR(32),
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
capacity_mw FLOAT,
elcc_eligible_capacity_mw FLOAT,
energy_only_capacity_mw FLOAT,
elcc_surface_coefficient FLOAT,
elcc_mw FLOAT,
PRIMARY KEY (scenario_id, project, period, facet)
);

-- Local capacity
DROP TABLE IF EXISTS results_project_local_capacity;
CREATE TABLE results_project_local_capacity (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
local_capacity_zone VARCHAR(32),
technology VARCHAR(32),
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
capacity_mw FLOAT,
local_capacity_fraction FLOAT,
local_capacity_contribution_mw FLOAT,
PRIMARY KEY (scenario_id, project, period)
);


-- Capacity costs
DROP TABLE IF EXISTS results_project_costs_capacity;
CREATE TABLE results_project_costs_capacity (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
technology VARCHAR(32),
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
annualized_capacity_cost FLOAT,
PRIMARY KEY (scenario_id, project, period)
);


DROP TABLE IF EXISTS results_project_costs_operations_variable_om;
CREATE TABLE results_project_costs_operations_variable_om (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
variable_om_cost FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_costs_operations_fuel;
CREATE TABLE results_project_costs_operations_fuel (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
fuel_cost FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_costs_operations_startup;
CREATE TABLE results_project_costs_operations_startup (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
startup_cost FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_costs_operations_shutdown;
CREATE TABLE results_project_costs_operations_shutdown (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
shutdown_cost FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_fuel_burn;
CREATE TABLE results_project_fuel_burn (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
fuel VARCHAR(32),
fuel_burn_mmbtu FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);


DROP TABLE IF EXISTS results_project_carbon_emissions;
CREATE TABLE results_project_carbon_emissions (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
carbon_emission_tons FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_project_rps;
CREATE TABLE results_project_rps (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
scheduled_rps_energy_mw FLOAT,
scheduled_curtailment_mw FLOAT,
subhourly_rps_energy_delivered_mw FLOAT,
subhourly_curtailment_mw FLOAT,
PRIMARY KEY (scenario_id, project, timepoint)
);

DROP TABLE IF EXISTS results_transmission_capacity;
CREATE TABLE results_transmission_capacity (
scenario_id INTEGER,
tx_line VARCHAR(64),
period INTEGER,
load_zone_from VARCHAR(32),
load_zone_to VARCHAR(32),
min_mw FLOAT,
max_mw FLOAT,
PRIMARY KEY (scenario_id, tx_line, period)
);

DROP TABLE IF EXISTS results_transmission_costs_capacity;
CREATE TABLE results_transmission_costs_capacity (
scenario_id INTEGER,
tx_line VARCHAR(64),
period INTEGER,
load_zone_from VARCHAR(32),
load_zone_to VARCHAR(32),
annualized_capacity_cost FLOAT,
PRIMARY KEY (scenario_id, tx_line, period)
);

DROP TABLE IF EXISTS results_transmission_imports_exports;
CREATE TABLE results_transmission_imports_exports (
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

DROP TABLE IF EXISTS results_transmission_operations;
CREATE TABLE results_transmission_operations (
scenario_id INTEGER,
transmission_line VARCHAR(64),
load_zone_from VARCHAR(64),
load_zone_to VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
transmission_flow_mw FLOAT,
PRIMARY KEY (scenario_id, transmission_line, timepoint)
);

DROP TABLE IF EXISTS results_transmission_hurdle_costs;
CREATE TABLE results_transmission_hurdle_costs (
scenario_id INTEGER,
transmission_line VARCHAR(64),
load_zone_from VARCHAR(64),
load_zone_to VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
hurdle_cost_positive_direction FLOAT,
hurdle_cost_negative_direction FLOAT,
PRIMARY KEY (scenario_id, transmission_line, timepoint)
);

DROP TABLE IF EXISTS results_transmission_carbon_emissions;
CREATE TABLE results_transmission_carbon_emissions (
scenario_id INTEGER,
tx_line VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
carbon_emission_imports_tons FLOAT,
carbon_emission_imports_tons_degen FLOAT,
PRIMARY KEY (scenario_id, tx_line, timepoint)
);


DROP TABLE IF EXISTS results_system_load_balance;
CREATE TABLE results_system_load_balance (
scenario_id INTEGER,
load_zone VARCHAR(32),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
overgeneration_mw FLOAT,
unserved_energy_mw FLOAT,
dual FLOAT,
marginal_price_per_mw FLOAT,
PRIMARY KEY (scenario_id, load_zone, timepoint)
);

DROP TABLE IF EXISTS results_system_lf_reserves_up_balance;
CREATE TABLE results_system_lf_reserves_up_balance (
scenario_id INTEGER,
lf_reserves_up_ba VARCHAR(32),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
violation_mw FLOAT,
dual FLOAT,
marginal_price_per_mw FLOAT,
PRIMARY KEY (scenario_id, lf_reserves_up_ba, timepoint)
);

DROP TABLE IF EXISTS results_system_lf_reserves_down_balance;
CREATE TABLE results_system_lf_reserves_down_balance (
scenario_id INTEGER,
lf_reserves_down_ba VARCHAR(32),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
violation_mw FLOAT,
dual FLOAT,
marginal_price_per_mw FLOAT,
PRIMARY KEY (scenario_id, lf_reserves_down_ba, timepoint)
);

DROP TABLE IF EXISTS results_system_regulation_up_balance;
CREATE TABLE results_system_regulation_up_balance (
scenario_id INTEGER,
regulation_up_ba VARCHAR(32),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
violation_mw FLOAT,
dual FLOAT,
marginal_price_per_mw FLOAT,
PRIMARY KEY (scenario_id, regulation_up_ba, timepoint)
);

DROP TABLE IF EXISTS results_system_regulation_down_balance;
CREATE TABLE results_system_regulation_down_balance (
scenario_id INTEGER,
regulation_down_ba VARCHAR(32),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
violation_mw FLOAT,
dual FLOAT,
marginal_price_per_mw FLOAT,
PRIMARY KEY (scenario_id, regulation_down_ba, timepoint)
);

DROP TABLE IF EXISTS results_system_frequency_response_balance;
CREATE TABLE results_system_frequency_response_balance (
scenario_id INTEGER,
frequency_response_ba VARCHAR(32),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
violation_mw FLOAT,
dual FLOAT,
marginal_price_per_mw FLOAT,
PRIMARY KEY (scenario_id, frequency_response_ba, timepoint)
);

-- TODO: frequency_response_partial_ba is the same as frequency_response_ba
-- _partial included to simplify results import
DROP TABLE IF EXISTS results_system_frequency_response_partial_balance;
CREATE TABLE results_system_frequency_response_partial_balance (
scenario_id INTEGER,
frequency_response_partial_ba VARCHAR(32),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
violation_mw FLOAT,
dual FLOAT,
marginal_price_per_mw FLOAT,
PRIMARY KEY (scenario_id, frequency_response_partial_ba, timepoint)
);

DROP TABLE IF EXISTS results_system_spinning_reserves_balance;
CREATE TABLE results_system_spinning_reserves_balance (
scenario_id INTEGER,
spinning_reserves_ba VARCHAR(32),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
horizon_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
violation_mw FLOAT,
dual FLOAT,
marginal_price_per_mw FLOAT,
PRIMARY KEY (scenario_id, spinning_reserves_ba, timepoint)
);

-- Carbon emissions
DROP TABLE IF EXISTS results_system_carbon_emissions;
CREATE TABLE results_system_carbon_emissions (
scenario_id INTEGER,
carbon_cap_zone VARCHAR(64),
period INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
carbon_cap_mmt FLOAT,
in_zone_project_emissions_mmt FLOAT,
import_emissions_mmt FLOAT,
total_emissions_mmt FLOAT,
import_emissions_mmt_degen FLOAT,
total_emissions_mmt_degen FLOAT,
dual FLOAT,
carbon_cap_marginal_cost_per_mmt FLOAT,
PRIMARY KEY (scenario_id, carbon_cap_zone, period)
);

-- RPS balance
DROP TABLE IF EXISTS results_system_rps;
CREATE TABLE  results_system_rps (
scenario_id INTEGER,
rps_zone VARCHAR(64),
period INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
rps_target_mwh FLOAT,
delivered_rps_energy_mwh FLOAT,
curtailed_rps_energy_mwh FLOAT,
total_rps_energy_mwh FLOAT,
fraction_of_rps_target_met FLOAT,
fraction_of_rps_energy_curtailed FLOAT,
dual FLOAT,
rps_marginal_cost_per_mwh FLOAT,
PRIMARY KEY (scenario_id, rps_zone, period)
);


-- PRM balance
DROP TABLE IF EXISTS results_system_prm;
CREATE TABLE  results_system_prm (
scenario_id INTEGER,
prm_zone VARCHAR(64),
period INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
prm_requirement_mw FLOAT,
elcc_simple_mw FLOAT,
elcc_surface_mw FLOAT,
elcc_total_mw FLOAT,
dual FLOAT,
prm_marginal_cost_per_mw FLOAT,
PRIMARY KEY (scenario_id, prm_zone, period)
);

-- Local capacity balance
DROP TABLE IF EXISTS results_system_local_capacity;
CREATE TABLE  results_system_local_capacity (
scenario_id INTEGER,
local_capacity_zone VARCHAR(64),
period INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
local_capacity_requirement_mw FLOAT,
local_capacity_provision_mw FLOAT,
dual FLOAT,
local_capacity_marginal_cost_per_mw FLOAT,
PRIMARY KEY (scenario_id, local_capacity_zone, period)
);
