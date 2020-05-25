-- noinspection SqlNoDataSourceInspectionForFile

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

-- Months
DROP TABLE IF EXISTS mod_months;
CREATE TABLE mod_months (
month INTEGER PRIMARY KEY,
description VARCHAR(16)
);

-- Implemented capacity types
DROP TABLE IF EXISTS mod_capacity_types;
CREATE TABLE mod_capacity_types (
capacity_type VARCHAR(32) PRIMARY KEY,
description VARCHAR(128)
);

-- Implemented availability types
DROP TABLE IF EXISTS mod_availability_types;
CREATE TABLE mod_availability_types (
availability_type VARCHAR(32) PRIMARY KEY,
description VARCHAR(128)
);

-- Implemented operational types
DROP TABLE IF EXISTS mod_operational_types;
CREATE TABLE mod_operational_types (
operational_type VARCHAR(32) PRIMARY KEY,
description VARCHAR(128)
);

-- Implemented reserve types
DROP TABLE IF EXISTS mod_reserve_types;
CREATE TABLE mod_reserve_types (
reserve_type VARCHAR(32) PRIMARY KEY,
description VARCHAR(128)
);

-- Implemented transmission operational types
DROP TABLE IF EXISTS mod_tx_operational_types;
CREATE TABLE mod_tx_operational_types (
operational_type VARCHAR(32) PRIMARY KEY,
description VARCHAR(128)
);

-- Implemented transmission capacity types
DROP TABLE IF EXISTS mod_tx_capacity_types;
CREATE TABLE mod_tx_capacity_types (
capacity_type VARCHAR(32) PRIMARY KEY,
description VARCHAR(128)
);

-- Implemented prm types
DROP TABLE IF EXISTS mod_prm_types;
CREATE TABLE mod_prm_types (
prm_type VARCHAR(32) PRIMARY KEY,
description VARCHAR(128)
);

-- Invalid combinations of capacity type and operational type
DROP TABLE IF EXISTS mod_capacity_and_operational_type_invalid_combos;
CREATE TABLE mod_capacity_and_operational_type_invalid_combos (
capacity_type VARCHAR (32),
operational_type VARCHAR (32),
PRIMARY KEY (capacity_type, operational_type),
FOREIGN KEY (capacity_type) REFERENCES mod_capacity_types (capacity_type),
FOREIGN KEY (operational_type) REFERENCES mod_operational_types
(operational_type)
);

-- Invalid combinations of tx capacity type and tx operational type
DROP TABLE IF EXISTS mod_tx_capacity_and_tx_operational_type_invalid_combos;
CREATE TABLE mod_tx_capacity_and_tx_operational_type_invalid_combos (
capacity_type VARCHAR (32),
operational_type VARCHAR (32),
PRIMARY KEY (capacity_type, operational_type),
FOREIGN KEY (capacity_type) REFERENCES mod_tx_capacity_types (capacity_type),
FOREIGN KEY (operational_type) REFERENCES mod_tx_operational_types
(operational_type)
);

DROP TABLE IF EXISTS mod_feature_subscenarios;
CREATE TABLE mod_feature_subscenarios (
feature VARCHAR(32),
subscenario_id VARCHAR(32),
PRIMARY KEY (feature, subscenario_id),
FOREIGN KEY (feature) REFERENCES mod_features (feature)
);

-- Features
DROP TABLE IF EXISTS mod_features;
CREATE TABLE mod_features (
feature VARCHAR(32) PRIMARY KEY,
description VARCHAR(128)
);

-- Subscenarios by feature
DROP TABLE IF EXISTS mod_feature_subscenarios;
CREATE TABLE mod_feature_subscenarios (
feature VARCHAR(32),
subscenario_id VARCHAR(32),
PRIMARY KEY (feature, subscenario_id),
FOREIGN KEY (feature) REFERENCES mod_features (feature)
);

-- Scenario validation status types
DROP TABLE IF EXISTS mod_validation_status_types;
CREATE TABLE mod_validation_status_types (
validation_status_id INTEGER PRIMARY KEY,
validation_status_name VARCHAR(32) UNIQUE
);

-- Units of measurements and their abbreviations
-- Core units will be populated with defaults but can be changed by the user
-- Secondary units are derived from the core units
DROP TABLE IF EXISTS mod_units;
CREATE TABLE mod_units (
metric VARCHAR(32) PRIMARY KEY,
type VARCHAR(32),  -- 'core' or 'secondary'
numerator_core_units VARCHAR(32),
denominator_core_units VARCHAR(32),
unit VARCHAR(32),  -- this will be derived for secondary units
description VARCHAR(128)
);

-- Run status types
DROP TABLE IF EXISTS mod_run_status_types;
CREATE TABLE mod_run_status_types (
run_status_id INTEGER PRIMARY KEY,
run_status_name VARCHAR(32) UNIQUE
);


--------------------
-- -- STATUS -- --
--------------------

-- Validation Results
DROP TABLE IF EXISTS status_validation;
CREATE TABLE status_validation (
scenario_id INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
gridpath_module VARCHAR(64),
db_table VARCHAR(64),
severity VARCHAR(32),
description VARCHAR(64),
time_stamp TEXT,  -- ISO8601 String
FOREIGN KEY (scenario_id) REFERENCES scenarios (scenario_id)
);

-- Scenario results: objective function, solver status
DROP TABLE IF EXISTS results_scenario;
CREATE TABLE results_scenario (
scenario_id INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
objective_function_value FLOAT,
solver_termination_condition VARCHAR(128),
PRIMARY KEY (scenario_id, subproblem_id, stage_id),
FOREIGN KEY (scenario_id) REFERENCES scenarios (scenario_id)
);


-------------------------------------------------------------------------------
---- SUBSCENARIOS AND INPUTS -----
-------------------------------------------------------------------------------

--------------------
-- -- TEMPORAL -- --
--------------------

-- Temporal Scenarios
DROP TABLE IF EXISTS subscenarios_temporal;
CREATE TABLE subscenarios_temporal (
temporal_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Subproblems (for production cost modeling)
DROP TABLE IF EXISTS inputs_temporal_subproblems;
CREATE TABLE inputs_temporal_subproblems (
temporal_scenario_id INTEGER,
subproblem_id INTEGER,
PRIMARY KEY (temporal_scenario_id, subproblem_id),
FOREIGN KEY (temporal_scenario_id) REFERENCES subscenarios_temporal
(temporal_scenario_id)
);

-- Stages (within subproblems; for production cost modeling)
DROP TABLE IF EXISTS inputs_temporal_subproblems_stages;
CREATE TABLE inputs_temporal_subproblems_stages (
temporal_scenario_id INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
PRIMARY KEY (temporal_scenario_id, subproblem_id, stage_id),
FOREIGN KEY (temporal_scenario_id) REFERENCES subscenarios_temporal
(temporal_scenario_id),
-- Make sure subproblem exists in this temporal_scenario_id
FOREIGN KEY (temporal_scenario_id, subproblem_id) REFERENCES
inputs_temporal_subproblems (temporal_scenario_id, subproblem_id)
);

-- Periods
-- These have to be the same for each subproblem
DROP TABLE IF EXISTS inputs_temporal_periods;
CREATE TABLE inputs_temporal_periods (
temporal_scenario_id INTEGER,
period INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
PRIMARY KEY (temporal_scenario_id, period),
FOREIGN KEY (temporal_scenario_id) REFERENCES subscenarios_temporal
(temporal_scenario_id)
);

-- Timepoints
-- Note on linked timepoints: the user can designate timepoints from the last
-- horizon of the subproblem to be linked to the first horizon of the next
-- subproblem -- it is up to the user to ensure that only the last horizon
-- of a subproblem and the first horizon of the next subproblem are linked
-- like this
-- Linked timepoints should be non-positive integers, ordered, and the most
-- recent linked timepoint should be 0, i.e. the linked timepoint indexed 0
-- will be the previous timepoint for the first timepoint of the first
-- horizon of the next subproblem. The previous timepoint for linked
-- timepoint 0 will be -1, and so on.
-- If linked timepoints are specified for a subproblem, GP will use those as
-- the previous timepoints for the first horizon of the next subproblem
-- (subproblem_id + 1) BUT ONLY IF the first horizon of the next subproblem has
-- a 'linked' boundary
DROP TABLE IF EXISTS inputs_temporal;
CREATE TABLE inputs_temporal (
temporal_scenario_id INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
period INTEGER,
number_of_hours_in_timepoint INTEGER,
timepoint_weight FLOAT,
previous_stage_timepoint_map INTEGER,
spinup_or_lookahead INTEGER,
linked_timepoint INTEGER, -- should be non-positive
month INTEGER,
hour_of_day FLOAT,  -- FLOAT to accommodate subhourly timepoints
timestamp DATETIME,
PRIMARY KEY (temporal_scenario_id, subproblem_id, stage_id, timepoint),
FOREIGN KEY (temporal_scenario_id) REFERENCES subscenarios_temporal
(temporal_scenario_id),
-- Make sure subproblem/stage exist in this temporal_scenario_id
FOREIGN KEY (temporal_scenario_id, subproblem_id, stage_id) REFERENCES
inputs_temporal_subproblems_stages (temporal_scenario_id, subproblem_id,
stage_id),
-- Make sure period exists in this temporal_scenario_id
FOREIGN KEY (temporal_scenario_id, period)
    REFERENCES inputs_temporal_periods (temporal_scenario_id, period),
-- Month must be 1-12
FOREIGN KEY (month) REFERENCES mod_months (month)
);

-- Horizons (with balancing types)
-- How timepoints are organized for operational-decision purposes
-- Each timepoint can belong to more than one balancing_type-horizon (e.g.
-- it can be on day 1 of the year, in week 1 of the year, in month 1 of the
-- year, etc.)
-- The balancing_type-horizons can be different by subproblem (e.g. one
-- subproblem can be a week and have days as horizons and another one
-- can be a week and have the week as horizon), but will have to be same for
-- each stage of a subproblem
DROP TABLE IF EXISTS inputs_temporal_horizons;
CREATE TABLE inputs_temporal_horizons (
temporal_scenario_id INTEGER,
subproblem_id INTEGER,
balancing_type_horizon VARCHAR(32),
horizon VARCHAR(32),
boundary VARCHAR(16),
PRIMARY KEY (temporal_scenario_id, subproblem_id, horizon,
             balancing_type_horizon),
FOREIGN KEY (temporal_scenario_id) REFERENCES subscenarios_temporal
(temporal_scenario_id),
-- Make sure boundary type is correct
FOREIGN KEY (boundary) REFERENCES mod_horizon_boundary_types
(horizon_boundary_type),
-- Make sure subproblem_id exists in this temporal_scenario_id
FOREIGN KEY (temporal_scenario_id, subproblem_id) REFERENCES
inputs_temporal_subproblems (temporal_scenario_id, subproblem_id)
);


-- This table is auxiliary for 1) readability and 2) populating the
-- inputs_temporal_horizon_timepoints table if we're using the CSV-to-DB
-- functionality
DROP TABLE IF EXISTS inputs_temporal_horizon_timepoints_start_end;
CREATE TABLE inputs_temporal_horizon_timepoints_start_end (
temporal_scenario_id INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
balancing_type_horizon VARCHAR(32),
horizon VARCHAR(32),
tmp_start INTEGER,
tmp_end INTEGER,
PRIMARY KEY (temporal_scenario_id, subproblem_id, stage_id,
             balancing_type_horizon, horizon),
FOREIGN KEY (temporal_scenario_id) REFERENCES subscenarios_temporal
(temporal_scenario_id),
-- Make sure the start and end timepoints exist in the main timepoints table
FOREIGN KEY (temporal_scenario_id, subproblem_id, stage_id, tmp_start)
    REFERENCES inputs_temporal (temporal_scenario_id, subproblem_id, stage_id,
                                timepoint),
FOREIGN KEY (temporal_scenario_id, subproblem_id, stage_id, tmp_end)
    REFERENCES inputs_temporal (temporal_scenario_id, subproblem_id, stage_id,
                                timepoint)
);

-- This table is what GridPath uses to get inputs
DROP TABLE IF EXISTS inputs_temporal_horizon_timepoints;
CREATE TABLE inputs_temporal_horizon_timepoints (
temporal_scenario_id INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
balancing_type_horizon VARCHAR(32),
horizon VARCHAR(32),
PRIMARY KEY (temporal_scenario_id, subproblem_id, stage_id, timepoint,
             balancing_type_horizon, horizon),
FOREIGN KEY (temporal_scenario_id)
    REFERENCES subscenarios_temporal (temporal_scenario_id),
-- Make sure these are the same timepoints as in the main timepoints table
FOREIGN KEY (temporal_scenario_id, subproblem_id, stage_id, timepoint)
    REFERENCES inputs_temporal (temporal_scenario_id,
                                subproblem_id, stage_id, timepoint),
-- Make sure horizons exist in this temporal_scenario_id and subproblem_id
FOREIGN KEY (temporal_scenario_id, subproblem_id, balancing_type_horizon,
             horizon)
    REFERENCES inputs_temporal_horizons (temporal_scenario_id, subproblem_id,
                                         balancing_type_horizon, horizon)
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
allow_overgeneration INTEGER,
overgeneration_penalty_per_mw FLOAT,
allow_unserved_energy INTEGER,
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
allow_violation INTEGER,
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
allow_violation INTEGER,
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
allow_violation INTEGER,
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
allow_violation INTEGER,
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
allow_violation INTEGER,
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
allow_violation INTEGER,
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
allow_violation INTEGER DEFAULT 0,  -- constraint is hard by default
violation_penalty_per_mwh FLOAT DEFAULT 0,
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
allow_violation INTEGER DEFAULT 0,  -- constraint is hard by default
violation_penalty_per_emission FLOAT DEFAULT 0,
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
allow_violation INTEGER DEFAULT 0,  -- constraint is hard by default
violation_penalty_per_mw FLOAT DEFAULT 0,
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
allow_violation INTEGER DEFAULT 0,  -- constraint is hard by default
violation_penalty_per_mw FLOAT DEFAULT 0,
PRIMARY KEY (local_capacity_zone_scenario_id, local_capacity_zone),
FOREIGN KEY (local_capacity_zone_scenario_id) REFERENCES
subscenarios_geography_local_capacity_zones (local_capacity_zone_scenario_id)
);


-------------------
-- -- PROJECT -- --
-------------------

-- -- Capacity -- --

-- Project portfolios
-- Subsets of projects allowed in a scenario: includes both specified and
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
specified INTEGER,
new_build INTEGER,
capacity_type VARCHAR(32),
PRIMARY KEY (project_portfolio_scenario_id, project),
FOREIGN KEY (project_portfolio_scenario_id) REFERENCES
subscenarios_project_portfolios (project_portfolio_scenario_id),
FOREIGN KEY (capacity_type) REFERENCES mod_capacity_types (capacity_type)
);

-- Existing project capacity and fixed costs
-- The capacity and fixed costs of 'specified' projects, i.e. exogenously
-- specified capacity that is not a variable in the model
-- Retirement can be allowed, in which case the fixed cost will determine
-- whether the economics of retirement are favorable
DROP TABLE IF EXISTS subscenarios_project_specified_capacity;
CREATE TABLE subscenarios_project_specified_capacity (
project_specified_capacity_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_specified_capacity;
CREATE TABLE inputs_project_specified_capacity (
project_specified_capacity_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
specified_capacity_mw FLOAT,
specified_capacity_mwh FLOAT,
PRIMARY KEY (project_specified_capacity_scenario_id, project, period),
FOREIGN KEY (project_specified_capacity_scenario_id) REFERENCES
subscenarios_project_specified_capacity (project_specified_capacity_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_specified_fixed_cost;
CREATE TABLE subscenarios_project_specified_fixed_cost (
project_specified_fixed_cost_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_specified_fixed_cost;
CREATE TABLE inputs_project_specified_fixed_cost (
project_specified_fixed_cost_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
annual_fixed_cost_per_mw_year FLOAT,
annual_fixed_cost_per_mwh_year FLOAT,
PRIMARY KEY (project_specified_fixed_cost_scenario_id, project, period),
FOREIGN KEY (project_specified_fixed_cost_scenario_id) REFERENCES
subscenarios_project_specified_fixed_cost
(project_specified_fixed_cost_scenario_id)
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
vintage INTEGER,
lifetime_yrs INTEGER,
annualized_real_cost_per_mw_yr FLOAT,
annualized_real_cost_per_mwh_yr FLOAT,
levelized_cost_per_mwh FLOAT,  -- useful if available, although not used
supply_curve_scenario_id INTEGER,
PRIMARY KEY (project_new_cost_scenario_id, project, vintage),
FOREIGN KEY (project_new_cost_scenario_id) REFERENCES
subscenarios_project_new_cost (project_new_cost_scenario_id)
);

-- New project binary build size
DROP TABLE IF EXISTS subscenarios_project_new_binary_build_size;
CREATE TABLE subscenarios_project_new_binary_build_size (
project_new_binary_build_size_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_new_binary_build_size;
CREATE TABLE inputs_project_new_binary_build_size (
project_new_binary_build_size_scenario_id INTEGER,
project VARCHAR(64),
binary_build_size_mw FLOAT,
binary_build_size_mwh FLOAT,
PRIMARY KEY (project_new_binary_build_size_scenario_id, project),
FOREIGN KEY (project_new_binary_build_size_scenario_id) REFERENCES
subscenarios_project_new_binary_build_size
(project_new_binary_build_size_scenario_id)
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
min_cumulative_new_build_mw FLOAT,
max_cumulative_new_build_mw FLOAT,
min_cumulative_new_build_mwh FLOAT,
max_cumulative_new_build_mwh FLOAT,
PRIMARY KEY (project_new_potential_scenario_id, project, period),
FOREIGN KEY (project_new_potential_scenario_id) REFERENCES
subscenarios_project_new_potential (project_new_potential_scenario_id)
);


-- Group capacity requirements
-- Requirements
DROP TABLE IF EXISTS subscenarios_project_capacity_group_requirements;
CREATE TABLE subscenarios_project_capacity_group_requirements (
project_capacity_group_requirement_scenario_id INTEGER PRIMARY KEY
    AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_capacity_group_requirements;
CREATE TABLE inputs_project_capacity_group_requirements (
project_capacity_group_requirement_scenario_id INTEGER,
capacity_group VARCHAR(64),
period INTEGER,
capacity_group_new_capacity_min FLOAT,
capacity_group_new_capacity_max FLOAT,
capacity_group_total_capacity_min FLOAT,
capacity_group_total_capacity_max FLOAT,
PRIMARY KEY (project_capacity_group_requirement_scenario_id,
            capacity_group, period),
FOREIGN KEY (project_capacity_group_requirement_scenario_id) REFERENCES
subscenarios_project_capacity_group_requirements
    (project_capacity_group_requirement_scenario_id)
);


-- Group project mapping
DROP TABLE IF EXISTS subscenarios_project_capacity_groups;
CREATE TABLE subscenarios_project_capacity_groups (
project_capacity_group_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_capacity_groups;
CREATE TABLE inputs_project_capacity_groups (
project_capacity_group_scenario_id INTEGER,
capacity_group VARCHAR(64),
project VARCHAR(64),
PRIMARY KEY (project_capacity_group_scenario_id, capacity_group, project),
FOREIGN KEY (project_capacity_group_scenario_id) REFERENCES
subscenarios_project_capacity_groups (project_capacity_group_scenario_id)
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
balancing_type_project VARCHAR(32),
variable_om_cost_per_mwh FLOAT,
fuel VARCHAR(32),
heat_rate_curves_scenario_id INTEGER,  -- determined heat rate curve
variable_om_curves_scenario_id INTEGER,  -- determined variable O&M curve
startup_chars_scenario_id INTEGER,  -- determines startup ramp chars
min_stable_level_fraction FLOAT,
unit_size_mw FLOAT,
startup_cost_per_mw FLOAT,
shutdown_cost_per_mw FLOAT,
startup_fuel_mmbtu_per_mw FLOAT,
startup_plus_ramp_up_rate FLOAT,  -- Not used for gen_commit_lin/bin!
shutdown_plus_ramp_down_rate FLOAT,
ramp_up_when_on_rate FLOAT,
ramp_down_when_on_rate FLOAT,
min_up_time_hours INTEGER,
min_down_time_hours INTEGER,
charging_efficiency FLOAT,
discharging_efficiency FLOAT,
minimum_duration_hours FLOAT,
maximum_duration_hours FLOAT,
aux_consumption_frac_capacity FLOAT,
aux_consumption_frac_power FLOAT,
last_commitment_stage INTEGER,
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
FOREIGN KEY (last_commitment_stage) REFERENCES
inputs_temporal_subproblems_stages (stage_id),
-- Ensure operational characteristics for variable, hydro and heat rates exist
FOREIGN KEY (project, heat_rate_curves_scenario_id) REFERENCES
subscenarios_project_heat_rate_curves
(project, heat_rate_curves_scenario_id),
FOREIGN KEY (project, variable_om_curves_scenario_id) REFERENCES
subscenarios_project_variable_om_curves
(project, variable_om_curves_scenario_id),
FOREIGN KEY (project, variable_generator_profile_scenario_id) REFERENCES
subscenarios_project_variable_generator_profiles
(project, variable_generator_profile_scenario_id),
FOREIGN KEY (project, hydro_operational_chars_scenario_id) REFERENCES
subscenarios_project_hydro_operational_chars
(project, hydro_operational_chars_scenario_id),
FOREIGN KEY (operational_type) REFERENCES mod_operational_types
(operational_type)
);

-- Heat rate curves
-- TODO: see comments variable profiles
DROP TABLE IF EXISTS subscenarios_project_heat_rate_curves;
CREATE TABLE subscenarios_project_heat_rate_curves (
project VARCHAR(32),
heat_rate_curves_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (project, heat_rate_curves_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_heat_rate_curves;
CREATE TABLE inputs_project_heat_rate_curves (
project VARCHAR(64),
heat_rate_curves_scenario_id INTEGER,
period INTEGER, -- 0 means it's the same for all periods
load_point_fraction FLOAT,
average_heat_rate_mmbtu_per_mwh FLOAT,
PRIMARY KEY (project, heat_rate_curves_scenario_id, period,
load_point_fraction),
FOREIGN KEY (project, heat_rate_curves_scenario_id) REFERENCES
subscenarios_project_heat_rate_curves (project, heat_rate_curves_scenario_id)
);

-- Variable O&M curves
-- TODO: see comments variable profiles
DROP TABLE IF EXISTS subscenarios_project_variable_om_curves;
CREATE TABLE subscenarios_project_variable_om_curves (
project VARCHAR(32),
variable_om_curves_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (project, variable_om_curves_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_variable_om_curves;
CREATE TABLE inputs_project_variable_om_curves (
project VARCHAR(64),
variable_om_curves_scenario_id INTEGER,
period INTEGER,  -- 0 means it's the same for all periods
load_point_fraction FLOAT,
average_variable_om_cost_per_mwh FLOAT,
PRIMARY KEY (project, variable_om_curves_scenario_id, period,
load_point_fraction),
FOREIGN KEY (project, variable_om_curves_scenario_id) REFERENCES
subscenarios_project_variable_om_curves (project,
variable_om_curves_scenario_id)
);

-- Startup characteristics
-- TODO: see comments variable profiles
DROP TABLE IF EXISTS subscenarios_project_startup_chars;
CREATE TABLE subscenarios_project_startup_chars (
project VARCHAR(32),
startup_chars_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (project, startup_chars_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_startup_chars;
CREATE TABLE inputs_project_startup_chars (
project VARCHAR(64),
startup_chars_scenario_id INTEGER,
down_time_cutoff_hours FLOAT,
startup_plus_ramp_up_rate FLOAT,
startup_cost_per_mw FLOAT,
PRIMARY KEY (project, startup_chars_scenario_id, down_time_cutoff_hours),
FOREIGN KEY (project, startup_chars_scenario_id) REFERENCES
subscenarios_project_startup_chars (project, startup_chars_scenario_id)
);

-- Variable generator profiles
-- TODO: this is not exactly a subscenario, as a variable profile will be
-- assigned to variable projects in the project_operational_chars table and
-- be passed to scenarios via the project_operational_chars_scenario_id
-- perhaps a better name is needed for this table
DROP TABLE IF EXISTS subscenarios_project_variable_generator_profiles;
CREATE TABLE subscenarios_project_variable_generator_profiles (
project VARCHAR(64),
variable_generator_profile_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (project, variable_generator_profile_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_variable_generator_profiles;
CREATE TABLE inputs_project_variable_generator_profiles (
project VARCHAR(64),
variable_generator_profile_scenario_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
cap_factor FLOAT,
PRIMARY KEY (project, variable_generator_profile_scenario_id, stage_id,
             timepoint),
FOREIGN KEY (project, variable_generator_profile_scenario_id) REFERENCES
subscenarios_project_variable_generator_profiles
(project, variable_generator_profile_scenario_id)
);

-- Hydro operational characteristics
DROP TABLE IF EXISTS subscenarios_project_hydro_operational_chars;
CREATE TABLE subscenarios_project_hydro_operational_chars (
project VARCHAR(64),
hydro_operational_chars_scenario_id,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (project, hydro_operational_chars_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_hydro_operational_chars;
CREATE TABLE inputs_project_hydro_operational_chars (
project VARCHAR(64),
hydro_operational_chars_scenario_id INTEGER,
balancing_type_project VARCHAR(64),
horizon INTEGER,
period INTEGER,
average_power_fraction FLOAT,
min_power_fraction FLOAT,
max_power_fraction FLOAT,
PRIMARY KEY (project, hydro_operational_chars_scenario_id,
             balancing_type_project, horizon),
FOREIGN KEY (project, hydro_operational_chars_scenario_id) REFERENCES
subscenarios_project_hydro_operational_chars
(project, hydro_operational_chars_scenario_id)
);

-- Project availability (e.g. due to planned outages/availability)
-- Subscenarios
DROP TABLE IF EXISTS subscenarios_project_availability;
CREATE TABLE subscenarios_project_availability (
project_availability_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Define availability type and IDs for type characteristics
-- TODO: implement check that there are exogenous IDs only for exogenous
--  types and endogenous IDs only for endogenous types
DROP TABLE IF EXISTS inputs_project_availability;
CREATE TABLE inputs_project_availability (
project_availability_scenario_id INTEGER,
project VARCHAR(64),
availability_type VARCHAR(32),
exogenous_availability_scenario_id INTEGER,
endogenous_availability_scenario_id INTEGER,
PRIMARY KEY (project_availability_scenario_id, project, availability_type)
);

DROP TABLE IF EXISTS subscenarios_project_availability_exogenous;
CREATE TABLE subscenarios_project_availability_exogenous (
project VARCHAR(64),
exogenous_availability_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (project, exogenous_availability_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_availability_exogenous;
CREATE TABLE inputs_project_availability_exogenous (
project VARCHAR(64),
exogenous_availability_scenario_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
availability_derate FLOAT,
PRIMARY KEY (project, exogenous_availability_scenario_id, stage_id, timepoint),
FOREIGN KEY (project, exogenous_availability_scenario_id)
    REFERENCES subscenarios_project_availability_exogenous
        (project, exogenous_availability_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_availability_endogenous;
CREATE TABLE subscenarios_project_availability_endogenous (
project VARCHAR(64),
endogenous_availability_scenario_id INTEGER,
name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (project, endogenous_availability_scenario_id)
);

DROP TABLE IF EXISTS inputs_project_availability_endogenous;
CREATE TABLE inputs_project_availability_endogenous (
project VARCHAR(64),
endogenous_availability_scenario_id INTEGER,
unavailable_hours_per_period FLOAT,
unavailable_hours_per_event_min FLOAT,
available_hours_between_events_min FLOAT,
PRIMARY KEY (project, endogenous_availability_scenario_id),
FOREIGN KEY (project, endogenous_availability_scenario_id)
    REFERENCES subscenarios_project_availability_endogenous
        (project, endogenous_availability_scenario_id)
);


-- Project load zones
-- Where projects are modeled to be physically located
-- Depends on the load_zone_scenario_id, i.e. how geography is modeled
-- (project can be in one zone if modeling a single zone, but a different
-- zone if modeling several zones, etc.)
DROP TABLE IF EXISTS subscenarios_project_load_zones;
CREATE TABLE subscenarios_project_load_zones (
project_load_zone_scenario_id INTEGER PRIMARY KEY,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_load_zones;
CREATE TABLE inputs_project_load_zones (
project_load_zone_scenario_id INTEGER,
project VARCHAR(64),
load_zone VARCHAR(32),
PRIMARY KEY (project_load_zone_scenario_id, project),
FOREIGN KEY (project_load_zone_scenario_id) REFERENCES
 subscenarios_project_load_zones (project_load_zone_scenario_id)
);

-- Project BAs
-- Which projects can contribute to a reserve requirement
-- Depends on how reserve balancing area are specified (xyz_ba_scenario_id)
-- This table can included all project with NULLs for projects not
-- contributing or just the contributing projects
DROP TABLE IF EXISTS subscenarios_project_lf_reserves_up_bas;
CREATE TABLE subscenarios_project_lf_reserves_up_bas (
project_lf_reserves_up_ba_scenario_id INTEGER PRIMARY KEY,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_lf_reserves_up_bas;
CREATE TABLE inputs_project_lf_reserves_up_bas (
project_lf_reserves_up_ba_scenario_id INTEGER,
project VARCHAR(64),
lf_reserves_up_ba VARCHAR(32),
PRIMARY KEY (project_lf_reserves_up_ba_scenario_id, project),
FOREIGN KEY (project_lf_reserves_up_ba_scenario_id)
REFERENCES subscenarios_project_lf_reserves_up_bas
 (project_lf_reserves_up_ba_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_lf_reserves_down_bas;
CREATE TABLE subscenarios_project_lf_reserves_down_bas (
project_lf_reserves_down_ba_scenario_id INTEGER PRIMARY KEY,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_lf_reserves_down_bas;
CREATE TABLE inputs_project_lf_reserves_down_bas (
project_lf_reserves_down_ba_scenario_id INTEGER,
project VARCHAR(64),
lf_reserves_down_ba VARCHAR(32),
PRIMARY KEY (project_lf_reserves_down_ba_scenario_id, project),
FOREIGN KEY (project_lf_reserves_down_ba_scenario_id)
REFERENCES subscenarios_project_lf_reserves_down_bas
 (project_lf_reserves_down_ba_scenario_id)
);


DROP TABLE IF EXISTS subscenarios_project_regulation_up_bas;
CREATE TABLE subscenarios_project_regulation_up_bas (
project_regulation_up_ba_scenario_id INTEGER PRIMARY KEY,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_regulation_up_bas;
CREATE TABLE inputs_project_regulation_up_bas (
project_regulation_up_ba_scenario_id INTEGER,
project VARCHAR(64),
regulation_up_ba VARCHAR(32),
PRIMARY KEY (project_regulation_up_ba_scenario_id, project),
FOREIGN KEY (project_regulation_up_ba_scenario_id)
REFERENCES subscenarios_project_regulation_up_bas
 (project_regulation_up_ba_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_regulation_down_bas;
CREATE TABLE subscenarios_project_regulation_down_bas (
project_regulation_down_ba_scenario_id INTEGER PRIMARY KEY,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_regulation_down_bas;
CREATE TABLE inputs_project_regulation_down_bas (
project_regulation_down_ba_scenario_id INTEGER,
project VARCHAR(64),
regulation_down_ba VARCHAR(32),
PRIMARY KEY (project_regulation_down_ba_scenario_id, project),
FOREIGN KEY (project_regulation_down_ba_scenario_id)
REFERENCES subscenarios_project_regulation_down_bas
 (project_regulation_down_ba_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_frequency_response_bas;
CREATE TABLE subscenarios_project_frequency_response_bas (
project_frequency_response_ba_scenario_id INTEGER PRIMARY KEY,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_frequency_response_bas;
CREATE TABLE inputs_project_frequency_response_bas (
project_frequency_response_ba_scenario_id INTEGER,
project VARCHAR(64),
frequency_response_ba VARCHAR(32),
contribute_to_partial INTEGER,
PRIMARY KEY (project_frequency_response_ba_scenario_id, project),
FOREIGN KEY (project_frequency_response_ba_scenario_id)
REFERENCES subscenarios_project_frequency_response_bas
 (project_frequency_response_ba_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_spinning_reserves_bas;
CREATE TABLE subscenarios_project_spinning_reserves_bas (
project_spinning_reserves_ba_scenario_id INTEGER PRIMARY KEY,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_spinning_reserves_bas;
CREATE TABLE inputs_project_spinning_reserves_bas (
project_spinning_reserves_ba_scenario_id INTEGER,
project VARCHAR(64),
spinning_reserves_ba VARCHAR(32),
PRIMARY KEY (project_spinning_reserves_ba_scenario_id, project),
FOREIGN KEY (project_spinning_reserves_ba_scenario_id)
REFERENCES subscenarios_project_spinning_reserves_bas
 (project_spinning_reserves_ba_scenario_id)
);

-- Project RPS zones
-- Which projects can contribute to RPS requirements
-- Depends on how RPS zones are specified
-- This table can include all project with NULLs for projects not
-- contributing or just the contributing projects
DROP TABLE IF EXISTS subscenarios_project_rps_zones;
CREATE TABLE subscenarios_project_rps_zones (
project_rps_zone_scenario_id INTEGER PRIMARY KEY,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_rps_zones;
CREATE TABLE inputs_project_rps_zones (
project_rps_zone_scenario_id INTEGER,
project VARCHAR(64),
rps_zone VARCHAR(32),
PRIMARY KEY (project_rps_zone_scenario_id, project),
FOREIGN KEY (project_rps_zone_scenario_id) REFERENCES
 subscenarios_project_rps_zones (project_rps_zone_scenario_id)
);

-- Project carbon cap zones
-- Which projects count toward the carbon cap
-- Depends on carbon cap zone geography
-- This table can include all project with NULLs for projects not
-- contributing or just the contributing projects
DROP TABLE IF EXISTS subscenarios_project_carbon_cap_zones;
CREATE TABLE subscenarios_project_carbon_cap_zones (
project_carbon_cap_zone_scenario_id INTEGER PRIMARY KEY,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_carbon_cap_zones;
CREATE TABLE inputs_project_carbon_cap_zones (
project_carbon_cap_zone_scenario_id INTEGER,
project VARCHAR(64),
carbon_cap_zone VARCHAR(32),
PRIMARY KEY (project_carbon_cap_zone_scenario_id, project),
FOREIGN KEY (project_carbon_cap_zone_scenario_id) REFERENCES
 subscenarios_project_carbon_cap_zones (project_carbon_cap_zone_scenario_id)
);


-- Project PRM zones
-- Which projects can contribute to PRM requirements
-- Depends on how PRM zones are specified
-- This table can include all project with NULLs for projects not
-- contributing or just the contributing projects

DROP TABLE IF EXISTS subscenarios_project_prm_zones;
CREATE TABLE subscenarios_project_prm_zones (
project_prm_zone_scenario_id INTEGER PRIMARY KEY,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_prm_zones;
CREATE TABLE inputs_project_prm_zones (
project_prm_zone_scenario_id INTEGER,
project VARCHAR(64),
prm_zone VARCHAR(32),
PRIMARY KEY (project_prm_zone_scenario_id, project),
FOREIGN KEY (project_prm_zone_scenario_id) REFERENCES
 subscenarios_project_prm_zones (project_prm_zone_scenario_id)
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
cap_factor_for_elcc_surface FLOAT,
min_duration_for_full_capacity_credit_hours FLOAT,
deliverability_group VARCHAR(64),  --optional
PRIMARY KEY (project_elcc_chars_scenario_id, project),
FOREIGN KEY (prm_type) REFERENCES mod_prm_types (prm_type),
FOREIGN KEY (project_elcc_chars_scenario_id) REFERENCES
subscenarios_project_elcc_chars (project_elcc_chars_scenario_id)
);

-- ELCC surface
-- Depends on how PRM zones are defined
DROP TABLE IF EXISTS subscenarios_system_prm_zone_elcc_surface;
CREATE TABLE subscenarios_system_prm_zone_elcc_surface (
elcc_surface_scenario_id INTEGER PRIMARY KEY,
name VARCHAR(32),
description VARCHAR(128)
);

-- ELCC surface intercept by PRM zone, period, and facet
DROP TABLE IF EXISTS inputs_system_prm_zone_elcc_surface;
CREATE TABLE inputs_system_prm_zone_elcc_surface (
elcc_surface_scenario_id INTEGER,
prm_zone VARCHAR(32),
period INTEGER,
facet INTEGER,
elcc_surface_intercept FLOAT,
PRIMARY KEY (elcc_surface_scenario_id, prm_zone, period, facet),
FOREIGN KEY (elcc_surface_scenario_id) REFERENCES
    subscenarios_system_prm_zone_elcc_surface (elcc_surface_scenario_id)
);

-- Peak and annual load for ELCC surface by PRM zone and period
DROP TABLE IF EXISTS inputs_system_prm_zone_elcc_surface_prm_load;
CREATE TABLE inputs_system_prm_zone_elcc_surface_prm_load (
elcc_surface_scenario_id INTEGER,
prm_zone VARCHAR(32),
period INTEGER,
prm_peak_load_mw FLOAT,
prm_annual_load_mwh FLOAT,
PRIMARY KEY (elcc_surface_scenario_id, prm_zone, period),
FOREIGN KEY (elcc_surface_scenario_id) REFERENCES
    subscenarios_system_prm_zone_elcc_surface (elcc_surface_scenario_id)
);

-- ELCC coefficients by project, period, and facet
DROP TABLE IF EXISTS inputs_project_elcc_surface;
CREATE TABLE inputs_project_elcc_surface (
elcc_surface_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
facet INTEGER,
elcc_surface_coefficient FLOAT,
PRIMARY KEY (elcc_surface_scenario_id, project, period, facet)
);

-- Project cap factors for the ELCC surface
DROP TABLE IF EXISTS inputs_project_elcc_surface_cap_factors;
CREATE TABLE inputs_project_elcc_surface_cap_factors (
elcc_surface_scenario_id INTEGER,
project VARCHAR(64),
elcc_surface_cap_factor FLOAT,
PRIMARY KEY (elcc_surface_scenario_id, project)
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
project_local_capacity_zone_scenario_id INTEGER PRIMARY KEY,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_project_local_capacity_zones;
CREATE TABLE inputs_project_local_capacity_zones (
project_local_capacity_zone_scenario_id INTEGER,
project VARCHAR(64),
local_capacity_zone VARCHAR(32),
PRIMARY KEY (project_local_capacity_zone_scenario_id, project),
FOREIGN KEY (project_local_capacity_zone_scenario_id) REFERENCES
 subscenarios_project_local_capacity_zones
 (project_local_capacity_zone_scenario_id)
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
(transmission_portfolio_scenario_id),
FOREIGN KEY (capacity_type) REFERENCES mod_tx_capacity_types
(capacity_type)
);

-- Transmission geography
-- Load zones
DROP TABLE IF EXISTS subscenarios_transmission_load_zones;
CREATE TABLE subscenarios_transmission_load_zones (
transmission_load_zone_scenario_id INTEGER PRIMARY KEY,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_transmission_load_zones;
CREATE TABLE inputs_transmission_load_zones (
transmission_load_zone_scenario_id INTEGER,
transmission_line VARCHAR(64),
load_zone_from VARCHAR(32),
load_zone_to VARCHAR(32),
PRIMARY KEY (transmission_load_zone_scenario_id, transmission_line),
FOREIGN KEY (transmission_load_zone_scenario_id) REFERENCES
    subscenarios_transmission_load_zones (transmission_load_zone_scenario_id)
);

-- Carbon cap zones
-- This is needed if the carbon cap module is enabled and we want to track
-- emission imports
DROP TABLE IF EXISTS subscenarios_transmission_carbon_cap_zones;
CREATE TABLE subscenarios_transmission_carbon_cap_zones (
transmission_carbon_cap_zone_scenario_id INTEGER PRIMARY KEY,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_transmission_carbon_cap_zones;
CREATE TABLE inputs_transmission_carbon_cap_zones (
transmission_carbon_cap_zone_scenario_id INTEGER,
transmission_line VARCHAR(64),
carbon_cap_zone VARCHAR(32),
import_direction VARCHAR(8),
tx_co2_intensity_tons_per_mwh FLOAT,
PRIMARY KEY (transmission_carbon_cap_zone_scenario_id, transmission_line),
FOREIGN KEY (transmission_carbon_cap_zone_scenario_id) REFERENCES
    subscenarios_transmission_carbon_cap_zones
        (transmission_carbon_cap_zone_scenario_id)
);

-- Existing transmission capacity
DROP TABLE IF EXISTS subscenarios_transmission_specified_capacity;
CREATE TABLE subscenarios_transmission_specified_capacity (
transmission_specified_capacity_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_transmission_specified_capacity;
CREATE TABLE inputs_transmission_specified_capacity (
transmission_specified_capacity_scenario_id INTEGER,
transmission_line VARCHAR(64),
period INTEGER,
min_mw FLOAT,
max_mw FLOAT,
PRIMARY KEY (transmission_specified_capacity_scenario_id, transmission_line,
period),
FOREIGN KEY (transmission_specified_capacity_scenario_id) REFERENCES
subscenarios_transmission_specified_capacity
(transmission_specified_capacity_scenario_id)
);

-- New transmission cost
DROP TABLE IF EXISTS subscenarios_transmission_new_cost;
CREATE TABLE subscenarios_transmission_new_cost (
transmission_new_cost_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_transmission_new_cost;
CREATE TABLE inputs_transmission_new_cost (
transmission_new_cost_scenario_id INTEGER,
transmission_line VARCHAR(64),
vintage INTEGER,
tx_lifetime_yrs FLOAT,
tx_annualized_real_cost_per_mw_yr FLOAT,
PRIMARY KEY (transmission_new_cost_scenario_id, transmission_line,
vintage),
FOREIGN KEY (transmission_new_cost_scenario_id) REFERENCES
subscenarios_transmission_new_cost
(transmission_new_cost_scenario_id)
);

-- Operational characteristics
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
operational_type VARCHAR(32),
tx_simple_loss_factor FLOAT,
reactance_ohms FLOAT,
PRIMARY KEY (transmission_operational_chars_scenario_id, transmission_line),
FOREIGN KEY (transmission_operational_chars_scenario_id) REFERENCES
subscenarios_transmission_operational_chars
(transmission_operational_chars_scenario_id),
FOREIGN KEY (operational_type) REFERENCES mod_tx_operational_types
(operational_type)
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
-- temporal_scenario_id and load_zone_scenario_id
DROP TABLE IF EXISTS inputs_system_load;
CREATE TABLE inputs_system_load (
load_scenario_id INTEGER,
load_zone VARCHAR(32),
stage_id INTEGER,
timepoint INTEGER,
load_mw FLOAT,
PRIMARY KEY (load_scenario_id, load_zone, stage_id, timepoint),
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
-- temporal_scenario_id and reserves_scenario_id
DROP TABLE IF EXISTS inputs_system_lf_reserves_up;
CREATE TABLE inputs_system_lf_reserves_up (
lf_reserves_up_scenario_id INTEGER,
lf_reserves_up_ba VARCHAR(32),
stage_id INTEGER,
timepoint INTEGER,
lf_reserves_up_mw FLOAT,
PRIMARY KEY (lf_reserves_up_scenario_id, lf_reserves_up_ba, stage_id,
timepoint),
FOREIGN KEY (lf_reserves_up_scenario_id) REFERENCES
subscenarios_system_lf_reserves_up (lf_reserves_up_scenario_id)
);

-- The requirement may be specified as percent of load, in which case we also
-- need to specify which load, i.e. specify a mapping between the reserve BA
-- and the load zones whose load should be part of the requirement
-- calculation (mapping should be one-to-many)
DROP TABLE IF EXISTS inputs_system_lf_reserves_up_percent;
CREATE TABLE inputs_system_lf_reserves_up_percent (
lf_reserves_up_scenario_id INTEGER,
lf_reserves_up_ba VARCHAR(32),
percent_load_req FLOAT,
PRIMARY KEY (lf_reserves_up_scenario_id, lf_reserves_up_ba)
);

DROP TABLE IF EXISTS inputs_system_lf_reserves_up_percent_lz_map;
CREATE TABLE inputs_system_lf_reserves_up_percent_lz_map (
lf_reserves_up_scenario_id INTEGER,
lf_reserves_up_ba VARCHAR(32),
load_zone VARCHAR(32),
PRIMARY KEY (lf_reserves_up_scenario_id, lf_reserves_up_ba, load_zone)
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
-- temporal_scenario_id and reserves_scenario_id
DROP TABLE IF EXISTS inputs_system_lf_reserves_down;
CREATE TABLE inputs_system_lf_reserves_down (
lf_reserves_down_scenario_id INTEGER,
lf_reserves_down_ba VARCHAR(32),
stage_id INTEGER,
timepoint INTEGER,
lf_reserves_down_mw FLOAT,
PRIMARY KEY (lf_reserves_down_scenario_id, lf_reserves_down_ba, stage_id,
timepoint),
FOREIGN KEY (lf_reserves_down_scenario_id) REFERENCES
subscenarios_system_lf_reserves_down (lf_reserves_down_scenario_id)
);

-- The requirement may be specified as percent of load, in which case we also
-- need to specify which load, i.e. specify a mapping between the reserve BA
-- and the load zones whose load should be part of the requirement
-- calculation (mapping should be one-to-many)
DROP TABLE IF EXISTS inputs_system_lf_reserves_down_percent;
CREATE TABLE inputs_system_lf_reserves_down_percent (
lf_reserves_down_scenario_id INTEGER,
lf_reserves_down_ba VARCHAR(32),
percent_load_req FLOAT,
PRIMARY KEY (lf_reserves_down_scenario_id, lf_reserves_down_ba)
);

DROP TABLE IF EXISTS inputs_system_lf_reserves_down_percent_lz_map;
CREATE TABLE inputs_system_lf_reserves_down_percent_lz_map (
lf_reserves_down_scenario_id INTEGER,
lf_reserves_down_ba VARCHAR(32),
load_zone VARCHAR(32),
PRIMARY KEY (lf_reserves_down_scenario_id, lf_reserves_down_ba, load_zone)
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
-- temporal_scenario_id and reserves_scenario_id
DROP TABLE IF EXISTS inputs_system_regulation_up;
CREATE TABLE inputs_system_regulation_up (
regulation_up_scenario_id INTEGER,
regulation_up_ba VARCHAR(32),
stage_id INTEGER,
timepoint INTEGER,
regulation_up_mw FLOAT,
PRIMARY KEY (regulation_up_scenario_id, regulation_up_ba, stage_id, timepoint),
FOREIGN KEY (regulation_up_scenario_id) REFERENCES
subscenarios_system_regulation_up (regulation_up_scenario_id)
);

-- The requirement may be specified as percent of load, in which case we also
-- need to specify which load, i.e. specify a mapping between the reserve BA
-- and the load zones whose load should be part of the requirement
-- calculation (mapping should be one-to-many)
DROP TABLE IF EXISTS inputs_system_regulation_down_percent;
CREATE TABLE inputs_system_regulation_down_percent (
regulation_down_scenario_id INTEGER,
regulation_down_ba VARCHAR(32),
percent_load_req FLOAT,
PRIMARY KEY (regulation_down_scenario_id, regulation_down_ba)
);

DROP TABLE IF EXISTS inputs_system_regulation_down_percent_lz_map;
CREATE TABLE inputs_system_regulation_down_percent_lz_map (
regulation_down_scenario_id INTEGER,
regulation_down_ba VARCHAR(32),
load_zone VARCHAR(32),
PRIMARY KEY (regulation_down_scenario_id, regulation_down_ba, load_zone)
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
-- temporal_scenario_id and reserves_scenario_id
DROP TABLE IF EXISTS inputs_system_regulation_down;
CREATE TABLE inputs_system_regulation_down (
regulation_down_scenario_id INTEGER,
regulation_down_ba VARCHAR(32),
stage_id INTEGER,
timepoint INTEGER,
regulation_down_mw FLOAT,
PRIMARY KEY (regulation_down_scenario_id, regulation_down_ba, stage_id,
timepoint),
FOREIGN KEY (regulation_down_scenario_id) REFERENCES
subscenarios_system_regulation_down (regulation_down_scenario_id)
);

-- The requirement may be specified as percent of load, in which case we also
-- need to specify which load, i.e. specify a mapping between the reserve BA
-- and the load zones whose load should be part of the requirement
-- calculation (mapping should be one-to-many)
DROP TABLE IF EXISTS inputs_system_regulation_up_percent;
CREATE TABLE inputs_system_regulation_up_percent (
regulation_up_scenario_id INTEGER,
regulation_up_ba VARCHAR(32),
percent_load_req FLOAT,
PRIMARY KEY (regulation_up_scenario_id, regulation_up_ba)
);

DROP TABLE IF EXISTS inputs_system_regulation_up_percent_lz_map;
CREATE TABLE inputs_system_regulation_up_percent_lz_map (
regulation_up_scenario_id INTEGER,
regulation_up_ba VARCHAR(32),
load_zone VARCHAR(32),
PRIMARY KEY (regulation_up_scenario_id, regulation_up_ba, load_zone)
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
-- temporal_scenario_id and reserves_scenario_id
DROP TABLE IF EXISTS inputs_system_frequency_response;
CREATE TABLE inputs_system_frequency_response (
frequency_response_scenario_id INTEGER,
frequency_response_ba VARCHAR(32),
stage_id INTEGER,
timepoint INTEGER,
frequency_response_mw FLOAT,
frequency_response_partial_mw FLOAT,
PRIMARY KEY (frequency_response_scenario_id, frequency_response_ba, stage_id,
timepoint),
FOREIGN KEY (frequency_response_scenario_id) REFERENCES
subscenarios_system_frequency_response (frequency_response_scenario_id)
);

-- The requirement may be specified as percent of load, in which case we also
-- need to specify which load, i.e. specify a mapping between the reserve BA
-- and the load zones whose load should be part of the requirement
-- calculation (mapping should be one-to-many)
DROP TABLE IF EXISTS inputs_system_frequency_response_percent;
CREATE TABLE inputs_system_frequency_response_percent (
frequency_response_scenario_id INTEGER,
frequency_response_ba VARCHAR(32),
percent_load_req FLOAT,
PRIMARY KEY (frequency_response_scenario_id, frequency_response_ba)
);

DROP TABLE IF EXISTS inputs_system_frequency_response_percent_lz_map;
CREATE TABLE inputs_system_frequency_response_percent_lz_map (
frequency_response_scenario_id INTEGER,
frequency_response_ba VARCHAR(32),
load_zone VARCHAR(32),
PRIMARY KEY (frequency_response_scenario_id, frequency_response_ba, load_zone)
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
-- temporal_scenario_id and reserves_scenario_id
DROP TABLE IF EXISTS inputs_system_spinning_reserves;
CREATE TABLE inputs_system_spinning_reserves (
spinning_reserves_scenario_id INTEGER,
spinning_reserves_ba VARCHAR(32),
stage_id INTEGER,
timepoint INTEGER,
spinning_reserves_mw FLOAT,
PRIMARY KEY (spinning_reserves_scenario_id, spinning_reserves_ba, stage_id,
timepoint),
FOREIGN KEY (spinning_reserves_scenario_id) REFERENCES
subscenarios_system_spinning_reserves (spinning_reserves_scenario_id)
);

-- The requirement may be specified as percent of load, in which case we also
-- need to specify which load, i.e. specify a mapping between the reserve BA
-- and the load zones whose load should be part of the requirement
-- calculation (mapping should be one-to-many)
DROP TABLE IF EXISTS inputs_system_spinning_reserves_percent;
CREATE TABLE inputs_system_spinning_reserves_percent (
spinning_reserves_scenario_id INTEGER,
spinning_reserves_ba VARCHAR(32),
percent_load_req FLOAT,
PRIMARY KEY (spinning_reserves_scenario_id, spinning_reserves_ba)
);

DROP TABLE IF EXISTS inputs_system_spinning_reserves_percent_lz_map;
CREATE TABLE inputs_system_spinning_reserves_percent_lz_map (
spinning_reserves_scenario_id INTEGER,
spinning_reserves_ba VARCHAR(32),
load_zone VARCHAR(32),
PRIMARY KEY (spinning_reserves_scenario_id, spinning_reserves_ba, load_zone)
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
-- periods and zones will be pulled depending on temporal_scenario_id and
-- rps_zone_scenario_id
DROP TABLE IF EXISTS inputs_system_rps_targets;
CREATE TABLE inputs_system_rps_targets (
rps_target_scenario_id INTEGER,
rps_zone VARCHAR(32),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
rps_target_mwh FLOAT,
rps_target_percentage FLOAT,
PRIMARY KEY (rps_target_scenario_id, rps_zone, period, subproblem_id,
stage_id)
);

-- If the RPS target is specified as percentage of load, we need to also
-- specify which load, i.e. specify a mapping between the RPS zone and the
-- load zones whose load should be part of the target calculation (mapping
-- should be one-to-many)
DROP TABLE IF EXISTS inputs_system_rps_target_load_zone_map;
CREATE TABLE inputs_system_rps_target_load_zone_map (
rps_target_scenario_id INTEGER,
rps_zone VARCHAR(32),
load_zone VARCHAR(64),
PRIMARY KEY (rps_target_scenario_id, rps_zone, load_zone)
);

-- Carbon cap
DROP TABLE IF EXISTS subscenarios_system_carbon_cap_targets;
CREATE TABLE subscenarios_system_carbon_cap_targets (
carbon_cap_target_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include periods and zones other than the ones in a scenario, as correct
-- periods and zones will be pulled depending on temporal_scenario_id and
-- carbon_cap_zone_scenario_id
DROP TABLE IF EXISTS inputs_system_carbon_cap_targets;
CREATE TABLE inputs_system_carbon_cap_targets (
carbon_cap_target_scenario_id INTEGER,
carbon_cap_zone VARCHAR(32),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
carbon_cap FLOAT,
PRIMARY KEY (carbon_cap_target_scenario_id, carbon_cap_zone, period,
subproblem_id, stage_id),
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
-- periods and zones will be pulled depending on temporal_scenario_id and
-- prm_zone_scenario_id
DROP TABLE IF EXISTS inputs_system_prm_requirement;
CREATE TABLE inputs_system_prm_requirement (
prm_requirement_scenario_id INTEGER,
prm_zone VARCHAR(32),
period INTEGER,
prm_requirement_mw FLOAT,
prm_peak_load_mw FLOAT,  -- for ELCC surface
prm_annual_load_mwh FLOAT,  -- for ELCC surface
PRIMARY KEY (prm_requirement_scenario_id, prm_zone, period)
);

-- Local capacity requirements
DROP TABLE IF EXISTS subscenarios_system_local_capacity_requirement;
CREATE TABLE subscenarios_system_local_capacity_requirement (
local_capacity_requirement_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

-- Can include periods and zones other than the ones in a scenario, as correct
-- periods and zones will be pulled depending on temporal_scenario_id and
-- local_capacity_zone_scenario_id
DROP TABLE IF EXISTS inputs_system_local_capacity_requirement;
CREATE TABLE inputs_system_local_capacity_requirement (
local_capacity_requirement_scenario_id INTEGER,
local_capacity_zone VARCHAR(32),
period INTEGER,
local_capacity_requirement_mw FLOAT,
PRIMARY KEY (local_capacity_requirement_scenario_id, local_capacity_zone,
period)
);

-- Case tuning
-- We can apply additional costs in the model to prevent degeneracy
-- Currently this includes:
-- 1) Carbon Imports (see objective.transmission.carbon_imports_tuning_costs
-- module; prevents the carbon imports expression from being set above actual
-- flow x intensity in situations when the carbon cap is non-binding)
-- 2) Ramps (see project.operations.tuning_costs module; applies to
-- hydro and storage operational types only and prevents erratic-looking
-- dispatch for these zero-variable-cost resources in case of degeneracy)
-- 3) Dynamic ELCC (see objective.reliability.prm
-- .dynamic_elcc_tuning_penalties module; ensures that the dynamic ELCC is set
-- to the maximum available in
-- case the PRM constraint is non-binding.
DROP TABLE IF EXISTS subscenarios_tuning;
CREATE TABLE subscenarios_tuning (
tuning_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_tuning;
CREATE TABLE inputs_tuning (
tuning_scenario_id INTEGER PRIMARY KEY,
import_carbon_tuning_cost_per_ton DOUBLE,
ramp_tuning_cost_per_mw DOUBLE,  -- applies to hydro and storage only
dynamic_elcc_tuning_cost_per_mw DOUBLE,
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
scenario_description VARCHAR(256),
validation_status_id INTEGER DEFAULT 0, -- status is 0 on scenario creation
queue_order_id INTEGER UNIQUE DEFAULT NULL,
run_status_id INTEGER DEFAULT 0, -- status is 0 on scenario creation
run_process_id INTEGER DEFAULT NULL,
run_start_time TIME,
run_end_time TIME,
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
of_tuning INTEGER,
temporal_scenario_id INTEGER,
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
project_specified_capacity_scenario_id INTEGER,
project_specified_fixed_cost_scenario_id INTEGER,
fuel_price_scenario_id INTEGER,
project_new_cost_scenario_id INTEGER,
project_new_potential_scenario_id INTEGER,
project_new_binary_build_size_scenario_id INTEGER,
project_capacity_group_requirement_scenario_id INTEGER,
project_capacity_group_scenario_id INTEGER,
transmission_portfolio_scenario_id INTEGER,
transmission_load_zone_scenario_id INTEGER,
transmission_specified_capacity_scenario_id INTEGER,
transmission_new_cost_scenario_id INTEGER,
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
solver_options_id INTEGER,
FOREIGN KEY (validation_status_id) REFERENCES
    mod_validation_status_types (validation_status_id),
FOREIGN KEY (run_status_id) REFERENCES mod_run_status_types (run_status_id),
FOREIGN KEY (temporal_scenario_id) REFERENCES
    subscenarios_temporal (temporal_scenario_id),
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
FOREIGN KEY (project_load_zone_scenario_id) REFERENCES
    subscenarios_project_load_zones (project_load_zone_scenario_id),
FOREIGN KEY (project_lf_reserves_up_ba_scenario_id) REFERENCES
    subscenarios_project_lf_reserves_up_bas
        (project_lf_reserves_up_ba_scenario_id),
FOREIGN KEY (project_lf_reserves_down_ba_scenario_id) REFERENCES
    subscenarios_project_lf_reserves_down_bas
        (project_lf_reserves_down_ba_scenario_id),
FOREIGN KEY (project_regulation_up_ba_scenario_id) REFERENCES
     subscenarios_project_regulation_up_bas
        (project_regulation_up_ba_scenario_id),
FOREIGN KEY (project_regulation_down_ba_scenario_id) REFERENCES
    subscenarios_project_regulation_down_bas
        (project_regulation_down_ba_scenario_id),
FOREIGN KEY (project_frequency_response_ba_scenario_id) REFERENCES
    subscenarios_project_frequency_response_bas
        (project_frequency_response_ba_scenario_id),
FOREIGN KEY (project_spinning_reserves_ba_scenario_id) REFERENCES
    subscenarios_project_spinning_reserves_bas
        (project_spinning_reserves_ba_scenario_id),
FOREIGN KEY (project_rps_zone_scenario_id) REFERENCES
    subscenarios_project_rps_zones
        (project_rps_zone_scenario_id),
FOREIGN KEY (project_carbon_cap_zone_scenario_id) REFERENCES
    subscenarios_project_carbon_cap_zones
        (project_carbon_cap_zone_scenario_id),
FOREIGN KEY (project_prm_zone_scenario_id) REFERENCES
    subscenarios_project_prm_zones (project_prm_zone_scenario_id),
FOREIGN KEY (project_elcc_chars_scenario_id) REFERENCES
    subscenarios_project_elcc_chars (project_elcc_chars_scenario_id),
FOREIGN KEY (prm_energy_only_scenario_id) REFERENCES
    subscenarios_project_prm_energy_only (prm_energy_only_scenario_id),
FOREIGN KEY (project_local_capacity_zone_scenario_id) REFERENCES
    subscenarios_project_local_capacity_zones
        (project_local_capacity_zone_scenario_id),
FOREIGN KEY (project_local_capacity_chars_scenario_id) REFERENCES
    subscenarios_project_local_capacity_chars
        (project_local_capacity_chars_scenario_id),
FOREIGN KEY (project_specified_capacity_scenario_id) REFERENCES
    subscenarios_project_specified_capacity
        (project_specified_capacity_scenario_id),
FOREIGN KEY (project_specified_fixed_cost_scenario_id) REFERENCES
    subscenarios_project_specified_fixed_cost
        (project_specified_fixed_cost_scenario_id),
FOREIGN KEY (project_new_cost_scenario_id) REFERENCES
    subscenarios_project_new_cost (project_new_cost_scenario_id),
FOREIGN KEY (project_new_potential_scenario_id) REFERENCES
    subscenarios_project_new_potential (project_new_potential_scenario_id),
FOREIGN KEY (project_new_binary_build_size_scenario_id) REFERENCES
    subscenarios_project_new_binary_build_size
    (project_new_binary_build_size_scenario_id),
FOREIGN KEY (project_capacity_group_scenario_id) REFERENCES
    subscenarios_project_capacity_groups
    (project_capacity_group_scenario_id),
FOREIGN KEY (project_capacity_group_requirement_scenario_id) REFERENCES
    subscenarios_project_capacity_group_requirements
    (project_capacity_group_requirement_scenario_id),
FOREIGN KEY (transmission_portfolio_scenario_id) REFERENCES
    subscenarios_transmission_portfolios (transmission_portfolio_scenario_id),
FOREIGN KEY (transmission_load_zone_scenario_id)
    REFERENCES subscenarios_transmission_load_zones
        (transmission_load_zone_scenario_id),
FOREIGN KEY (transmission_specified_capacity_scenario_id) REFERENCES
    subscenarios_transmission_specified_capacity
        (transmission_specified_capacity_scenario_id),
FOREIGN KEY (transmission_new_cost_scenario_id) REFERENCES
    subscenarios_transmission_new_cost
        (transmission_new_cost_scenario_id),
FOREIGN KEY (transmission_operational_chars_scenario_id) REFERENCES
    subscenarios_transmission_operational_chars
        (transmission_operational_chars_scenario_id),
FOREIGN KEY (transmission_hurdle_rate_scenario_id) REFERENCES
    subscenarios_transmission_hurdle_rates
        (transmission_hurdle_rate_scenario_id),
FOREIGN KEY (transmission_carbon_cap_zone_scenario_id)
    REFERENCES subscenarios_transmission_carbon_cap_zones
        (transmission_carbon_cap_zone_scenario_id),
FOREIGN KEY (transmission_simultaneous_flow_limit_scenario_id)
    REFERENCES subscenarios_transmission_simultaneous_flow_limits
        (transmission_simultaneous_flow_limit_scenario_id),
FOREIGN KEY (transmission_simultaneous_flow_limit_line_group_scenario_id)
    REFERENCES subscenarios_transmission_simultaneous_flow_limit_line_groups
        (transmission_simultaneous_flow_limit_line_group_scenario_id),
FOREIGN KEY (load_scenario_id) REFERENCES
    subscenarios_system_load (load_scenario_id),
FOREIGN KEY (lf_reserves_up_scenario_id) REFERENCES
    subscenarios_system_lf_reserves_up (lf_reserves_up_scenario_id),
FOREIGN KEY (lf_reserves_down_scenario_id) REFERENCES
    subscenarios_system_lf_reserves_down (lf_reserves_down_scenario_id),
FOREIGN KEY (regulation_up_scenario_id) REFERENCES
    subscenarios_system_regulation_up (regulation_up_scenario_id),
FOREIGN KEY (regulation_down_scenario_id) REFERENCES
    subscenarios_system_regulation_down (regulation_down_scenario_id),
FOREIGN KEY (spinning_reserves_scenario_id) REFERENCES
    subscenarios_system_spinning_reserves (spinning_reserves_scenario_id),
FOREIGN KEY (frequency_response_scenario_id) REFERENCES
    subscenarios_system_frequency_response (frequency_response_scenario_id),
FOREIGN KEY (rps_target_scenario_id) REFERENCES
    subscenarios_system_rps_targets (rps_target_scenario_id),
FOREIGN KEY (carbon_cap_target_scenario_id) REFERENCES
    subscenarios_system_carbon_cap_targets (carbon_cap_target_scenario_id),
FOREIGN KEY (prm_requirement_scenario_id) REFERENCES
    subscenarios_system_prm_requirement (prm_requirement_scenario_id),
FOREIGN KEY (elcc_surface_scenario_id) REFERENCES
    subscenarios_system_prm_zone_elcc_surface (elcc_surface_scenario_id),
FOREIGN KEY (local_capacity_requirement_scenario_id) REFERENCES
    subscenarios_system_local_capacity_requirement
        (local_capacity_requirement_scenario_id),
FOREIGN KEY (tuning_scenario_id) REFERENCES
    subscenarios_tuning (tuning_scenario_id),
FOREIGN KEY (solver_options_id)
    REFERENCES subscenarios_options_solver (solver_options_id)
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

DROP TABLE IF EXISTS results_project_capacity;
CREATE TABLE results_project_capacity (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
capacity_type VARCHAR(64),
technology VARCHAR(32),
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
capacity_mw FLOAT,
energy_capacity_mwh FLOAT,
new_build_mw FLOAT,
new_build_mwh FLOAT,
new_build_binary INTEGER,
retired_mw FLOAT,
retired_binary INTEGER,
PRIMARY KEY (scenario_id, project, period, subproblem_id, stage_id)
);

DROP TABLE IF EXISTS results_project_group_capacity;
CREATE TABLE results_project_group_capacity (
scenario_id INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
capacity_group VARCHAR(64),
period INTEGER,
group_new_capacity FLOAT,
group_total_capacity FLOAT,
capacity_group_new_capacity_min FLOAT,
capacity_group_new_capacity_max FLOAT,
capacity_group_total_capacity_min FLOAT,
capacity_group_total_capacity_max FLOAT,
PRIMARY KEY (scenario_id, subproblem_id, stage_id, capacity_group, period)
);


DROP TABLE IF EXISTS results_project_availability_endogenous;
CREATE TABLE results_project_availability_endogenous (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
availability_type VARCHAR(64),
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
unavailability_decision FLOAT,
start_unavailablity FLOAT,
stop_unavailability FLOAT,
availability_derate FLOAT,
PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_project_dispatch;
CREATE TABLE results_project_dispatch (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
operational_type VARCHAR(64),
balancing_type VARCHAR(64),
horizon INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
power_mw FLOAT,  -- net power in case there's auxiliary consumption
scheduled_curtailment_mw FLOAT,
subhourly_curtailment_mw FLOAT,
subhourly_energy_delivered_mw FLOAT,
total_curtailment_mw FLOAT,
committed_mw FLOAT,
committed_units FLOAT,
started_units INTEGER,
stopped_units INTEGER,
synced_units INTEGER,
active_startup_type INTEGER,
auxiliary_consumption_mw FLOAT,
gross_power_mw FLOAT,
PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_project_curtailment_variable;
CREATE TABLE results_project_curtailment_variable (
scenario_id INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
period INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
month INTEGER,
hour_of_day FLOAT,
load_zone VARCHAR(32),
scheduled_curtailment_mw FLOAT,
PRIMARY KEY (scenario_id, subproblem_id, stage_id, timepoint, load_zone)
);

DROP TABLE IF EXISTS results_project_curtailment_hydro;
CREATE TABLE results_project_curtailment_hydro (
scenario_id INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
period INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
month INTEGER,
hour_of_day FLOAT,
load_zone VARCHAR(32),
scheduled_curtailment_mw FLOAT,
PRIMARY KEY (scenario_id, subproblem_id, stage_id, timepoint, load_zone)
);

DROP TABLE IF EXISTS results_project_dispatch_by_technology;
CREATE TABLE results_project_dispatch_by_technology (
scenario_id INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
period INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
technology VARCHAR(32),
power_mw FLOAT,
PRIMARY KEY (scenario_id, subproblem_id, stage_id, timepoint, load_zone,
technology)
);


DROP TABLE IF EXISTS results_project_lf_reserves_up;
CREATE TABLE results_project_lf_reserves_up (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
balancing_type_project VARCHAR(64),
horizon INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
lf_reserves_up_ba VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
reserve_provision_mw FLOAT,
PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_project_lf_reserves_down;
CREATE TABLE results_project_lf_reserves_down (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
balancing_type_project VARCHAR(64),
horizon INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
lf_reserves_down_ba VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
reserve_provision_mw FLOAT,
PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_project_regulation_up;
CREATE TABLE results_project_regulation_up (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
balancing_type_project VARCHAR(64),
horizon INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
regulation_up_ba VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
reserve_provision_mw FLOAT,
PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_project_regulation_down;
CREATE TABLE results_project_regulation_down (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
balancing_type_project VARCHAR(64),
horizon INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
regulation_down_ba VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
reserve_provision_mw FLOAT,
PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_project_frequency_response;
CREATE TABLE results_project_frequency_response (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
balancing_type_project VARCHAR(64),
horizon INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
frequency_response_ba VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
reserve_provision_mw FLOAT,
partial INTEGER,
PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_project_spinning_reserves;
CREATE TABLE results_project_spinning_reserves (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
balancing_type_project VARCHAR(64),
horizon INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
spinning_reserves_ba VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
reserve_provision_mw FLOAT,
PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_project_prm_deliverability;
CREATE TABLE results_project_prm_deliverability (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
prm_zone VARCHAR(32),
technology VARCHAR(32),
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
capacity_mw FLOAT,
deliverable_capacity_mw FLOAT,
energy_only_capacity_mw FLOAT,
PRIMARY KEY (scenario_id, project, period, subproblem_id, stage_id)
);

DROP TABLE IF EXISTS
results_project_prm_deliverability_group_capacity_and_costs;
CREATE TABLE results_project_prm_deliverability_group_capacity_and_costs (
scenario_id INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
deliverability_group VARCHAR(64),
period INTEGER,
deliverability_group_no_cost_deliverable_capacity_mw FLOAT,
deliverability_group_deliverability_cost_per_mw FLOAT,
total_capacity_mw FLOAT,
deliverable_capacity_mw FLOAT,
energy_only_capacity_mw FLOAT,
deliverable_capacity_cost FLOAT,
PRIMARY KEY (scenario_id, deliverability_group, period, subproblem_id, stage_id)
);

DROP TABLE IF EXISTS results_project_elcc_simple;
CREATE TABLE results_project_elcc_simple (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
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
PRIMARY KEY (scenario_id, project, period, subproblem_id, stage_id)
);

DROP TABLE IF EXISTS results_project_elcc_surface;
CREATE TABLE results_project_elcc_surface (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
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
PRIMARY KEY (scenario_id, project, period, subproblem_id, stage_id, facet)
);

-- Local capacity
DROP TABLE IF EXISTS results_project_local_capacity;
CREATE TABLE results_project_local_capacity (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
local_capacity_zone VARCHAR(32),
technology VARCHAR(32),
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
capacity_mw FLOAT,
local_capacity_fraction FLOAT,
local_capacity_contribution_mw FLOAT,
PRIMARY KEY (scenario_id, project, period, subproblem_id, stage_id)
);


-- Capacity costs
DROP TABLE IF EXISTS results_project_costs_capacity;
CREATE TABLE results_project_costs_capacity (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
technology VARCHAR(32),
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
annualized_capacity_cost FLOAT,
PRIMARY KEY (scenario_id, project, period, subproblem_id, stage_id)
);

DROP TABLE IF EXISTS results_project_costs_operations;
CREATE TABLE results_project_costs_operations (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
balancing_type_project VARCHAR(64),
horizon INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
variable_om_cost FLOAT,
fuel_cost FLOAT,
startup_cost FLOAT,
shutdown_cost FLOAT,
PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_project_fuel_burn;
CREATE TABLE results_project_fuel_burn (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
balancing_type_project VARCHAR(64),
horizon INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
fuel VARCHAR(32),
operations_fuel_burn_mmbtu FLOAT,
startup_fuel_burn_mmbtu FLOAT,
total_fuel_burn_mmbtu FLOAT,
PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
);


DROP TABLE IF EXISTS results_project_carbon_emissions;
CREATE TABLE results_project_carbon_emissions (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
balancing_type_project VARCHAR(64),
horizon INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
carbon_emission_tons FLOAT,
PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_project_rps;
CREATE TABLE results_project_rps (
scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
balancing_type_project VARCHAR(64),
horizon INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_zone VARCHAR(32),
rps_zone VARCHAR(32),
carbon_cap_zone VARCHAR(32),
technology VARCHAR(32),
scheduled_rps_energy_mw FLOAT,
scheduled_curtailment_mw FLOAT,
subhourly_rps_energy_delivered_mw FLOAT,
subhourly_curtailment_mw FLOAT,
PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_transmission_capacity;
CREATE TABLE results_transmission_capacity (
scenario_id INTEGER,
tx_line VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
load_zone_from VARCHAR(32),
load_zone_to VARCHAR(32),
min_mw FLOAT,
max_mw FLOAT,
PRIMARY KEY (scenario_id, tx_line, period, subproblem_id, stage_id)
);

DROP TABLE IF EXISTS results_transmission_capacity_new_build;
CREATE TABLE results_transmission_capacity_new_build (
scenario_id INTEGER,
transmission_line VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
load_zone_from VARCHAR(32),
load_zone_to VARCHAR(32),
new_build_transmission_capacity_mw FLOAT,
PRIMARY KEY (scenario_id, transmission_line, period, subproblem_id, stage_id)
);

-- TODO: add table for costs new build?
DROP TABLE IF EXISTS results_transmission_costs_capacity;
CREATE TABLE results_transmission_costs_capacity (
scenario_id INTEGER,
tx_line VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
load_zone_from VARCHAR(32),
load_zone_to VARCHAR(32),
annualized_capacity_cost FLOAT,
PRIMARY KEY (scenario_id, tx_line, period, subproblem_id, stage_id)
);

DROP TABLE IF EXISTS results_transmission_imports_exports;
CREATE TABLE results_transmission_imports_exports (
scenario_id INTEGER,
load_zone VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
imports_mw FLOAT,
exports_mw FLOAT,
net_imports_mw FLOAT,
PRIMARY KEY (scenario_id, load_zone, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_transmission_operations;
CREATE TABLE results_transmission_operations (
scenario_id INTEGER,
transmission_line VARCHAR(64),
load_zone_from VARCHAR(64),
load_zone_to VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
transmission_flow_mw FLOAT,
transmission_losses_lz_from FLOAT,
transmission_losses_lz_to FLOAT,
PRIMARY KEY (scenario_id, transmission_line, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_transmission_hurdle_costs;
CREATE TABLE results_transmission_hurdle_costs (
scenario_id INTEGER,
transmission_line VARCHAR(64),
load_zone_from VARCHAR(64),
load_zone_to VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
hurdle_cost_positive_direction FLOAT,
hurdle_cost_negative_direction FLOAT,
PRIMARY KEY (scenario_id, transmission_line, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_transmission_carbon_emissions;
CREATE TABLE results_transmission_carbon_emissions (
scenario_id INTEGER,
tx_line VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
carbon_emission_imports_tons FLOAT,
carbon_emission_imports_tons_degen FLOAT,
PRIMARY KEY (scenario_id, tx_line, subproblem_id, stage_id, timepoint)
);


DROP TABLE IF EXISTS results_system_load_balance;
CREATE TABLE results_system_load_balance (
scenario_id INTEGER,
load_zone VARCHAR(32),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
load_mw FLOAT,
overgeneration_mw FLOAT,
unserved_energy_mw FLOAT,
dual FLOAT,
marginal_price_per_mw FLOAT,
PRIMARY KEY (scenario_id, load_zone, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_system_lf_reserves_up_balance;
CREATE TABLE results_system_lf_reserves_up_balance (
scenario_id INTEGER,
lf_reserves_up_ba VARCHAR(32),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
violation_mw FLOAT,
dual FLOAT,
marginal_price_per_mw FLOAT,
PRIMARY KEY (scenario_id, lf_reserves_up_ba, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_system_lf_reserves_down_balance;
CREATE TABLE results_system_lf_reserves_down_balance (
scenario_id INTEGER,
lf_reserves_down_ba VARCHAR(32),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
violation_mw FLOAT,
dual FLOAT,
marginal_price_per_mw FLOAT,
PRIMARY KEY (scenario_id, lf_reserves_down_ba, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_system_regulation_up_balance;
CREATE TABLE results_system_regulation_up_balance (
scenario_id INTEGER,
regulation_up_ba VARCHAR(32),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
violation_mw FLOAT,
dual FLOAT,
marginal_price_per_mw FLOAT,
PRIMARY KEY (scenario_id, regulation_up_ba, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_system_regulation_down_balance;
CREATE TABLE results_system_regulation_down_balance (
scenario_id INTEGER,
regulation_down_ba VARCHAR(32),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
violation_mw FLOAT,
dual FLOAT,
marginal_price_per_mw FLOAT,
PRIMARY KEY (scenario_id, regulation_down_ba, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_system_frequency_response_balance;
CREATE TABLE results_system_frequency_response_balance (
scenario_id INTEGER,
frequency_response_ba VARCHAR(32),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
violation_mw FLOAT,
dual FLOAT,
marginal_price_per_mw FLOAT,
PRIMARY KEY (scenario_id, frequency_response_ba, subproblem_id, stage_id, timepoint)
);

-- TODO: frequency_response_partial_ba is the same as frequency_response_ba
-- _partial included to simplify results import
DROP TABLE IF EXISTS results_system_frequency_response_partial_balance;
CREATE TABLE results_system_frequency_response_partial_balance (
scenario_id INTEGER,
frequency_response_partial_ba VARCHAR(32),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
violation_mw FLOAT,
dual FLOAT,
marginal_price_per_mw FLOAT,
PRIMARY KEY (scenario_id, frequency_response_partial_ba, subproblem_id, stage_id, timepoint)
);

DROP TABLE IF EXISTS results_system_spinning_reserves_balance;
CREATE TABLE results_system_spinning_reserves_balance (
scenario_id INTEGER,
spinning_reserves_ba VARCHAR(32),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
timepoint INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
timepoint_weight FLOAT,
number_of_hours_in_timepoint FLOAT,
violation_mw FLOAT,
dual FLOAT,
marginal_price_per_mw FLOAT,
PRIMARY KEY (scenario_id, spinning_reserves_ba, subproblem_id, stage_id, timepoint)
);

-- Carbon emissions
DROP TABLE IF EXISTS results_system_carbon_emissions;
CREATE TABLE results_system_carbon_emissions (
scenario_id INTEGER,
carbon_cap_zone VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
carbon_cap FLOAT,
in_zone_project_emissions FLOAT,
import_emissions FLOAT,
total_emissions FLOAT,
carbon_cap_overage FLOAT,
import_emissions_degen FLOAT,
total_emissions_degen FLOAT,
dual FLOAT,
carbon_cap_marginal_cost_per_emission FLOAT,
PRIMARY KEY (scenario_id, carbon_cap_zone, subproblem_id, stage_id, period)
);

-- RPS balance
DROP TABLE IF EXISTS results_system_rps;
CREATE TABLE  results_system_rps (
scenario_id INTEGER,
rps_zone VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
rps_target_mwh FLOAT,
delivered_rps_energy_mwh FLOAT,
curtailed_rps_energy_mwh FLOAT,
total_rps_energy_mwh FLOAT,
fraction_of_rps_target_met FLOAT,
fraction_of_rps_energy_curtailed FLOAT,
rps_shortage_mwh FLOAT,
dual FLOAT,
rps_marginal_cost_per_mwh FLOAT,
PRIMARY KEY (scenario_id, rps_zone, period, subproblem_id, stage_id)
);


-- PRM balance
DROP TABLE IF EXISTS results_system_prm;
CREATE TABLE  results_system_prm (
scenario_id INTEGER,
prm_zone VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
prm_requirement_mw FLOAT,
elcc_simple_mw FLOAT,
elcc_surface_mw FLOAT,
elcc_total_mw FLOAT,
prm_shortage_mw FLOAT,
dual FLOAT,
prm_marginal_cost_per_mw FLOAT,
PRIMARY KEY (scenario_id, prm_zone, period, subproblem_id, stage_id)
);

-- Local capacity balance
DROP TABLE IF EXISTS results_system_local_capacity;
CREATE TABLE  results_system_local_capacity (
scenario_id INTEGER,
local_capacity_zone VARCHAR(64),
period INTEGER,
subproblem_id INTEGER,
stage_id INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
local_capacity_requirement_mw FLOAT,
local_capacity_provision_mw FLOAT,
local_capacity_shortage_mw FLOAT,
dual FLOAT,
local_capacity_marginal_cost_per_mw FLOAT,
PRIMARY KEY (scenario_id, local_capacity_zone, period, subproblem_id, stage_id)
);

---------------
--- OPTIONS ---
---------------

DROP TABLE IF EXISTS subscenarios_options_solver;
CREATE TABLE subscenarios_options_solver (
    solver_options_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(32),
    description VARCHAR(128)
);

DROP TABLE IF EXISTS inputs_options_solver;
CREATE TABLE inputs_options_solver (
    solver_options_id INTEGER,
    solver VARCHAR(32),
    solver_option_name VARCHAR(32),
    solver_option_value FLOAT,
    PRIMARY KEY (solver_options_id, solver, solver_option_name),
    FOREIGN KEY (solver_options_id)
        REFERENCES subscenarios_options_solver (solver_options_id)
);

-- Views
DROP VIEW IF EXISTS scenarios_view;
CREATE VIEW scenarios_view
AS
SELECT
scenario_id,
scenario_name,
scenario_description,
mod_validation_status_types.validation_status_name as validation_status,
mod_run_status_types.run_status_name as run_status,
CASE WHEN of_transmission THEN 'yes' ELSE 'no' END AS feature_transmission,
CASE WHEN of_transmission_hurdle_rates=1 THEN 'yes' ELSE 'no' END
    AS feature_transmission_hurdle_rates,
CASE WHEN of_simultaneous_flow_limits THEN 'yes' ELSE 'no' END
    AS feature_simultaneous_flow_limits,
CASE WHEN of_lf_reserves_up THEN 'yes' ELSE 'no' END
    AS feature_load_following_up,
CASE WHEN of_lf_reserves_down THEN 'yes' ELSE 'no' END
    AS feature_load_following_down,
CASE WHEN of_regulation_up THEN 'yes' ELSE 'no' END
    AS feature_regulation_up,
CASE WHEN of_regulation_down THEN 'yes' ELSE 'no' END
    AS feature_regulation_down,
CASE WHEN of_frequency_response THEN 'yes' ELSE 'no' END
    AS feature_frequency_response,
CASE WHEN of_spinning_reserves THEN 'yes' ELSE 'no' END
    AS feature_spinning_reserves,
CASE WHEN of_rps THEN 'yes' ELSE 'no' END AS feature_rps,
CASE WHEN of_carbon_cap THEN 'yes' ELSE 'no' END
    AS feature_carbon_cap,
CASE WHEN of_track_carbon_imports THEN 'yes' ELSE 'no' END
    AS feature_track_carbon_imports,
CASE WHEN of_prm THEN 'yes' ELSE 'no' END AS feature_prm,
CASE WHEN of_elcc_surface THEN 'yes' ELSE 'no' END
    AS feature_elcc_surface,
CASE WHEN of_local_capacity THEN 'yes' ELSE 'no' END
    AS feature_local_capacity,
CASE WHEN of_tuning THEN 'yes' ELSE 'no' END
    AS feature_tuning,
subscenarios_temporal.name AS temporal,
subscenarios_geography_load_zones.name AS geography_load_zones,
subscenarios_geography_lf_reserves_up_bas.name AS geography_lf_up_bas,
subscenarios_geography_lf_reserves_down_bas.name AS geography_lf_down_bas,
subscenarios_geography_regulation_up_bas.name AS geography_reg_up_bas,
subscenarios_geography_regulation_down_bas.name AS geography_reg_down_bas,
subscenarios_geography_spinning_reserves_bas.name AS geography_spin_bas,
subscenarios_geography_frequency_response_bas.name AS geography_freq_resp_bas,
subscenarios_geography_rps_zones.name AS geography_rps_areas,
subscenarios_geography_carbon_cap_zones.name AS carbon_cap_areas,
subscenarios_geography_prm_zones.name AS prm_areas,
subscenarios_geography_local_capacity_zones.name AS local_capacity_areas,
subscenarios_project_portfolios.name AS project_portfolio,
subscenarios_project_operational_chars.name AS project_operating_chars,
subscenarios_project_availability.name AS project_availability,
subscenarios_project_fuels.name AS project_fuels,
subscenarios_project_fuel_prices.name AS fuel_prices,
subscenarios_project_load_zones.name AS project_load_zones,
subscenarios_project_lf_reserves_up_bas.name AS project_lf_up_bas,
subscenarios_project_lf_reserves_down_bas.name AS project_lf_down_bas,
subscenarios_project_regulation_up_bas.name AS project_reg_up_bas,
subscenarios_project_regulation_down_bas.name AS project_reg_down_bas,
subscenarios_project_spinning_reserves_bas.name AS project_spin_bas,
subscenarios_project_frequency_response_bas.name AS project_freq_resp_bas,
subscenarios_project_rps_zones.name AS project_rps_areas,
subscenarios_project_carbon_cap_zones.name AS project_carbon_cap_areas,
subscenarios_project_prm_zones.name AS project_prm_areas,
subscenarios_project_elcc_chars.name AS project_elcc_chars,
subscenarios_project_prm_energy_only.name AS project_prm_energy_only,
subscenarios_project_local_capacity_zones.name AS project_local_capacity_areas,
subscenarios_project_local_capacity_chars.name AS project_local_capacity_chars,
subscenarios_project_specified_capacity.name AS project_specified_capacity,
subscenarios_project_specified_fixed_cost.name AS project_specified_fixed_cost,
subscenarios_project_new_cost.name AS project_new_cost,
subscenarios_project_new_potential.name AS project_new_potential,
subscenarios_project_new_binary_build_size.name AS project_new_binary_build_size,
subscenarios_transmission_portfolios.name AS transmission_portfolio,
subscenarios_transmission_load_zones.name AS transmission_load_zones,
subscenarios_transmission_specified_capacity.name
    AS transmission_specified_capacity,
subscenarios_transmission_new_cost.name
    AS transmission_new_cost,
subscenarios_transmission_operational_chars.name
    AS transmission_operational_chars,
subscenarios_transmission_hurdle_rates.name AS transmission_hurdle_rates,
subscenarios_transmission_carbon_cap_zones.name
    AS transmission_carbon_cap_zones,
subscenarios_transmission_simultaneous_flow_limits.name
    AS transmission_simultaneous_flow_limits,
subscenarios_transmission_simultaneous_flow_limit_line_groups.name AS
    transmission_simultaneous_flow_limit_line_groups,
subscenarios_system_load.name AS load_profile,
subscenarios_system_lf_reserves_up.name AS load_following_reserves_up_profile,
subscenarios_system_lf_reserves_down.name
    AS load_following_reserves_down_profile,
subscenarios_system_regulation_up.name AS regulation_up_profile,
subscenarios_system_regulation_down.name AS regulation_down_profile,
subscenarios_system_spinning_reserves.name AS spinning_reserves_profile,
subscenarios_system_frequency_response.name AS frequency_response_profile,
subscenarios_system_rps_targets.name AS rps_target,
subscenarios_system_carbon_cap_targets.name AS carbon_cap,
subscenarios_system_prm_requirement.name AS prm_requirement,
subscenarios_system_prm_zone_elcc_surface.name AS elcc_surface,
subscenarios_system_local_capacity_requirement.name
    AS local_capacity_requirement,
subscenarios_tuning.name AS tuning,
subscenarios_options_solver.name as solver
FROM scenarios
LEFT JOIN mod_validation_status_types USING (validation_status_id)
LEFT JOIN mod_run_status_types USING (run_status_id)
LEFT JOIN subscenarios_temporal USING (temporal_scenario_id)
LEFT JOIN subscenarios_geography_load_zones USING (load_zone_scenario_id)
LEFT JOIN subscenarios_geography_lf_reserves_up_bas
    USING (lf_reserves_up_ba_scenario_id)
LEFT JOIN subscenarios_geography_lf_reserves_down_bas
    USING (lf_reserves_down_ba_scenario_id)
LEFT JOIN subscenarios_geography_regulation_up_bas
    USING (regulation_up_ba_scenario_id)
LEFT JOIN subscenarios_geography_regulation_down_bas
    USING (regulation_down_ba_scenario_id)
LEFT JOIN subscenarios_geography_spinning_reserves_bas
    USING (spinning_reserves_ba_scenario_id)
LEFT JOIN subscenarios_geography_frequency_response_bas
    USING (frequency_response_ba_scenario_id)
LEFT JOIN subscenarios_geography_rps_zones USING (rps_zone_scenario_id)
LEFT JOIN subscenarios_geography_carbon_cap_zones
    USING (carbon_cap_zone_scenario_id)
LEFT JOIN subscenarios_geography_prm_zones USING (prm_zone_scenario_id)
LEFT JOIN subscenarios_geography_local_capacity_zones
    USING (local_capacity_zone_scenario_id)
LEFT JOIN subscenarios_project_portfolios USING (project_portfolio_scenario_id)
LEFT JOIN subscenarios_project_operational_chars
    USING (project_operational_chars_scenario_id)
LEFT JOIN subscenarios_project_availability
    USING (project_availability_scenario_id)
LEFT JOIN subscenarios_project_fuels USING (fuel_scenario_id)
LEFT JOIN subscenarios_project_fuel_prices USING (fuel_price_scenario_id)
LEFT JOIN subscenarios_project_load_zones
    USING (project_load_zone_scenario_id)
LEFT JOIN subscenarios_project_lf_reserves_up_bas
    USING (project_lf_reserves_up_ba_scenario_id)
LEFT JOIN subscenarios_project_lf_reserves_down_bas
    USING (project_lf_reserves_down_ba_scenario_id)
LEFT JOIN subscenarios_project_regulation_up_bas
    USING (project_regulation_up_ba_scenario_id)
LEFT JOIN subscenarios_project_regulation_down_bas
    USING (project_regulation_down_ba_scenario_id)
LEFT JOIN subscenarios_project_spinning_reserves_bas
    USING (project_spinning_reserves_ba_scenario_id)
LEFT JOIN subscenarios_project_frequency_response_bas
    USING (project_frequency_response_ba_scenario_id)
LEFT JOIN subscenarios_project_rps_zones
    USING (project_rps_zone_scenario_id)
LEFT JOIN subscenarios_project_carbon_cap_zones
    USING (project_carbon_cap_zone_scenario_id)
LEFT JOIN subscenarios_project_prm_zones
    USING (project_prm_zone_scenario_id)
LEFT JOIN subscenarios_project_elcc_chars
    USING (project_elcc_chars_scenario_id)
LEFT JOIN subscenarios_project_prm_energy_only
    USING (prm_energy_only_scenario_id)
LEFT JOIN subscenarios_project_local_capacity_zones
    USING (project_local_capacity_zone_scenario_id)
LEFT JOIN subscenarios_project_local_capacity_chars
    USING (project_local_capacity_chars_scenario_id)
LEFT JOIN subscenarios_project_specified_capacity
    USING (project_specified_capacity_scenario_id)
LEFT JOIN subscenarios_project_specified_fixed_cost
    USING (project_specified_fixed_cost_scenario_id)
LEFT JOIN subscenarios_project_new_cost USING (project_new_cost_scenario_id)
LEFT JOIN subscenarios_project_new_potential
    USING (project_new_potential_scenario_id)
LEFT JOIN subscenarios_project_new_binary_build_size
    USING (project_new_binary_build_size_scenario_id)
LEFT JOIN subscenarios_transmission_portfolios
    USING (transmission_portfolio_scenario_id)
LEFT JOIN subscenarios_transmission_load_zones
    USING (transmission_load_zone_scenario_id)
LEFT JOIN subscenarios_transmission_specified_capacity
    USING (transmission_specified_capacity_scenario_id)
LEFT JOIN subscenarios_transmission_new_cost
    USING (transmission_new_cost_scenario_id)
LEFT JOIN subscenarios_transmission_operational_chars
    USING (transmission_operational_chars_scenario_id)
LEFT JOIN subscenarios_transmission_hurdle_rates
    USING (transmission_hurdle_rate_scenario_id)
LEFT JOIN subscenarios_transmission_carbon_cap_zones
    USING (transmission_carbon_cap_zone_scenario_id)
LEFT JOIN subscenarios_transmission_simultaneous_flow_limits
    USING (transmission_simultaneous_flow_limit_scenario_id)
LEFT JOIN subscenarios_transmission_simultaneous_flow_limit_line_groups
    USING (transmission_simultaneous_flow_limit_line_group_scenario_id)
LEFT JOIN subscenarios_system_load USING (load_scenario_id)
LEFT JOIN subscenarios_system_lf_reserves_up
    USING (lf_reserves_up_scenario_id)
LEFT JOIN subscenarios_system_lf_reserves_down
    USING (lf_reserves_down_scenario_id)
LEFT JOIN subscenarios_system_regulation_up
    USING (regulation_up_scenario_id)
LEFT JOIN subscenarios_system_regulation_down
    USING (regulation_down_scenario_id)
LEFT JOIN subscenarios_system_spinning_reserves
    USING (spinning_reserves_scenario_id)
LEFT JOIN subscenarios_system_frequency_response
    USING (frequency_response_scenario_id)
LEFT JOIN subscenarios_system_rps_targets USING (rps_target_scenario_id)
LEFT JOIN subscenarios_system_carbon_cap_targets
    USING (carbon_cap_target_scenario_id)
LEFT JOIN subscenarios_system_prm_requirement
    USING (prm_requirement_scenario_id)
LEFT JOIN subscenarios_system_prm_zone_elcc_surface
    USING (elcc_surface_scenario_id)
LEFT JOIN subscenarios_system_local_capacity_requirement
    USING (local_capacity_requirement_scenario_id)
LEFT JOIN subscenarios_tuning USING (tuning_scenario_id)
LEFT JOIN subscenarios_options_solver USING (solver_options_id)
;


-------------------------------------------------------------------------------
------------------------------ User Interface ---------------------------------
-------------------------------------------------------------------------------

-- Tables for scenario-detail and scenario-new
-- TODO: is the ui_table_id needed?
DROP TABLE IF EXISTS ui_scenario_detail_table_metadata;
CREATE TABLE ui_scenario_detail_table_metadata (
ui_table_id INTEGER PRIMARY KEY AUTOINCREMENT,
include INTEGER,
ui_table VARCHAR(32) UNIQUE,
ui_table_caption VARCHAR(64)
);

DROP TABLE IF EXISTS ui_scenario_detail_table_row_metadata;
CREATE TABLE ui_scenario_detail_table_row_metadata (
ui_table VARCHAR(32),
ui_table_row VARCHAR(32),
include INTEGER,
ui_row_caption VARCHAR(64),
ui_row_db_scenarios_view_column VARCHAR(64),
ui_row_db_subscenario_table VARCHAR(128),
ui_row_db_subscenario_table_id_column VARCHAR(128),
ui_row_db_input_table VARCHAR(128),
PRIMARY KEY (ui_table, ui_table_row),
FOREIGN KEY (ui_table) REFERENCES ui_scenario_detail_table_metadata (ui_table)
);

-- Tables for scenario-results
DROP TABLE IF EXISTS ui_scenario_results_table_metadata;
CREATE TABLE ui_scenario_results_table_metadata (
results_table VARCHAR(64),
include INTEGER,
caption VARCHAR(64)
);

DROP TABLE IF EXISTS ui_scenario_results_plot_metadata;
CREATE TABLE ui_scenario_results_plot_metadata (
results_plot VARCHAR(64) PRIMARY KEY,
include INTEGER,
caption VARCHAR(64),
load_zone_form_control INTEGER,
rps_zone_form_control INTEGER,
carbon_cap_zone_form_control INTEGER,
period_form_control INTEGER,
horizon_form_control INTEGER,
subproblem_form_control INTEGER,
stage_form_control INTEGER,
project_form_control INTEGER,
commit_project_form_control INTEGER
);

---------------------
--- VISUALIZATION ---
---------------------

-- Technology colors and plotting order
DROP TABLE IF EXISTS viz_technologies;
CREATE TABLE viz_technologies (
technology VARCHAR(32),
color VARCHAR(32),
plotting_order INTEGER UNIQUE,
PRIMARY KEY (technology)
);
