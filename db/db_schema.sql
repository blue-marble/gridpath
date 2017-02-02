-- -- SCENARIOS -- --
-- TODO: what will be varied?

DROP TABLE IF EXISTS scenarios;
CREATE TABLE scenarios(
scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
period_scenario_id INTEGER,
horizon_scenario_id INTEGER,
timepoint_scenario_id INTEGER,
load_zone_scenario_id INTEGER,
lf_reserves_up_ba_scenario_id INTEGER,
lf_reserves_down_ba_scenario_id INTEGER,
rps_zone_scenario_id INTEGER,
existing_project_scenario_id INTEGER,
new_project_scenario_id INTEGER,
project_load_zone_scenario_id INTEGER,
project_lf_reserves_up_ba_scenario_id INTEGER,
project_lf_reserves_down_ba_scenario_id INTEGER,
project_rps_zone_scenario_id INTEGER,
existing_project_capacity_scenario_id INTEGER,
new_project_cost_scenario_id INTEGER,
fuel_scenario_id INTEGER,
project_operational_chars_scenario_id INTEGER,
hydro_operational_chars_scenario_id INTEGER,
variable_generator_profiles_scenario_id INTEGER,
load_scenario_id INTEGER,
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id),
FOREIGN KEY (period_scenario_id, horizon_scenario_id) REFERENCES
subscenarios_horizons (period_scenario_id, horizon_scenario_id),
FOREIGN KEY (period_scenario_id, horizon_scenario_id,
timepoint_scenario_id) REFERENCES subscenarios_timepoints
(period_scenario_id, horizon_scenario_id, timepoint_scenario_id),
FOREIGN KEY (load_zone_scenario_id) REFERENCES subscenarios_load_zones
(load_zone_scenario_id),
FOREIGN KEY (lf_reserves_up_ba_scenario_id) REFERENCES
subscenarios_lf_reserves_up_bas (lf_reserves_up_ba_scenario_id),
FOREIGN KEY (lf_reserves_down_ba_scenario_id) REFERENCES
subscenarios_lf_reserves_down_bas (lf_reserves_down_ba_scenario_id),
FOREIGN KEY (rps_zone_scenario_id) REFERENCES subscenarios_rps_zones
(rps_zone_scenario_id),
FOREIGN KEY (existing_project_scenario_id) REFERENCES
subscenarios_existing_projects (existing_project_scenario_id),
FOREIGN KEY (new_project_scenario_id) REFERENCES subscenarios_new_projects
(new_project_scenario_id),
FOREIGN KEY (load_zone_scenario_id, existing_project_scenario_id, 
new_project_scenario_id, project_load_zone_scenario_id) 
REFERENCES subscenarios_project_load_zones 
(load_zone_scenario_id, existing_project_scenario_id, 
new_project_scenario_id, project_load_zone_scenario_id),
FOREIGN KEY (lf_reserves_up_ba_scenario_id, existing_project_scenario_id, 
new_project_scenario_id, project_lf_reserves_up_ba_scenario_id) REFERENCES 
subscenarios_project_lf_reserves_up_bas
(lf_reserves_up_ba_scenario_id, existing_project_scenario_id, 
new_project_scenario_id, project_lf_reserves_up_ba_scenario_id),
FOREIGN KEY (lf_reserves_down_ba_scenario_id, existing_project_scenario_id, 
new_project_scenario_id, project_lf_reserves_down_ba_scenario_id) REFERENCES 
subscenarios_project_lf_reserves_down_bas
(lf_reserves_down_ba_scenario_id, existing_project_scenario_id, 
new_project_scenario_id, project_lf_reserves_down_ba_scenario_id),
FOREIGN KEY (rps_zone_scenario_id, existing_project_scenario_id, 
new_project_scenario_id, project_rps_zone_scenario_id) 
REFERENCES subscenarios_project_rps_zones 
(rps_zone_scenario_id, existing_project_scenario_id, 
new_project_scenario_id, project_rps_zone_scenario_id),
FOREIGN KEY (existing_project_scenario_id, period_scenario_id,
existing_project_capacity_scenario_id) REFERENCES
subscenarios_existing_project_capacity (existing_project_scenario_id,
period_scenario_id, existing_project_capacity_scenario_id),
FOREIGN KEY (new_project_scenario_id,
period_scenario_id, new_project_cost_scenario_id) REFERENCES
subscenarios_new_project_cost (new_project_scenario_id,
period_scenario_id, new_project_cost_scenario_id),
FOREIGN KEY (fuel_scenario_id) REFERENCES subscenarios_fuels
(fuel_scenario_id),
FOREIGN KEY (existing_project_scenario_id, new_project_scenario_id,
period_scenario_id, horizon_scenario_id,
hydro_operational_chars_scenario_id) REFERENCES
subscenarios_hydro_operational_chars (existing_project_scenario_id,
new_project_scenario_id, period_scenario_id, horizon_scenario_id,
hydro_operational_chars_scenario_id),
FOREIGN KEY (existing_project_scenario_id, new_project_scenario_id,
project_operational_chars_scenario_id) REFERENCES
subscenarios_project_operational_chars (existing_project_scenario_id,
new_project_scenario_id, project_operational_chars_scenario_id),
FOREIGN KEY (existing_project_scenario_id,
new_project_scenario_id,
project_operational_chars_scenario_id, period_scenario_id, horizon_scenario_id,
timepoint_scenario_id, variable_generator_profiles_scenario_id) REFERENCES
subscenarios_variable_generator_profiles (existing_project_scenario_id,
new_project_scenario_id, project_operational_chars_scenario_id,
period_scenario_id, horizon_scenario_id, timepoint_scenario_id,
variable_generator_profiles_scenario_id),
FOREIGN KEY (period_scenario_id, horizon_scenario_id, timepoint_scenario_id,
load_zone_scenario_id, load_zone_scenario_id) REFERENCES subscenarios_loads
(period_scenario_id, horizon_scenario_id, timepoint_scenario_id,
load_zone_scenario_id, load_zone_scenario_id)
);

-- -- SUB-SCENARIOS -- --
-- Geography
DROP TABLE IF EXISTS subscenarios_load_zones;
CREATE TABLE subscenarios_load_zones(
load_zone_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
load_zone_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS subscenarios_lf_reserves_up_bas;
CREATE TABLE subscenarios_lf_reserves_up_bas(
lf_reserves_up_ba_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
lf_reserves_up_ba_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS subscenarios_lf_reserves_down_bas;
CREATE TABLE subscenarios_lf_reserves_down_bas(
lf_reserves_down_ba_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
lf_reserves_down_ba_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS subscenarios_regulation_up_bas;
CREATE TABLE subscenarios_regulation_up_bas(
regulation_up_ba_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
regulation_up_ba_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS subscenarios_regulation_down_bas;
CREATE TABLE subscenarios_regulation_down_bas(
regulation_down_ba_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
regulation_down_ba_scenario_name VARCHAR(32),
description VARCHAR(128)
);

-- Temporal
DROP TABLE IF EXISTS subscenarios_periods;
CREATE TABLE subscenarios_periods(
period_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
period_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS subscenarios_horizons;
CREATE TABLE subscenarios_horizons(
period_scenario_id INTEGER,
horizon_scenario_id INTEGER,
horizon_scenario_name VARCHAR(32),
horizon_scenario_description VARCHAR(128),
PRIMARY KEY (period_scenario_id, horizon_scenario_id),
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id)
);


DROP TABLE IF EXISTS subscenarios_timepoints;
CREATE TABLE subscenarios_timepoints(
period_scenario_id INTEGER,
horizon_scenario_id INTEGER,
timepoint_scenario_id INTEGER,
timepoint_scenario_name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (period_scenario_id, horizon_scenario_id, timepoint_scenario_id),
FOREIGN KEY (period_scenario_id, horizon_scenario_id) REFERENCES
subscenarios_horizons (period_scenario_id, horizon_scenario_id)
);

-- Project
DROP TABLE IF EXISTS subscenarios_existing_projects;
CREATE TABLE subscenarios_existing_projects(
existing_project_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
existing_project_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS subscenarios_existing_project_capacity;
CREATE TABLE subscenarios_existing_project_capacity(
existing_project_scenario_id INTEGER,
period_scenario_id INTEGER,
existing_project_capacity_scenario_id INTEGER,
existing_project_capacity_scenario_name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (existing_project_scenario_id, period_scenario_id,
existing_project_capacity_scenario_id),
FOREIGN KEY (existing_project_scenario_id) REFERENCES
subscenarios_existing_projects (existing_project_scenario_id),
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_new_projects;
CREATE TABLE subscenarios_new_projects(
new_project_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
new_project_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS subscenarios_project_operational_chars;
CREATE TABLE subscenarios_project_operational_chars(
existing_project_scenario_id INTEGER,
new_project_scenario_id INTEGER,
project_operational_chars_scenario_id INTEGER,
project_operational_chars_scenario_name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (existing_project_scenario_id, new_project_scenario_id,
project_operational_chars_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_new_project_cost;
CREATE TABLE subscenarios_new_project_cost(
new_project_scenario_id INTEGER,
period_scenario_id INTEGER,
new_project_cost_scenario_id INTEGER,
new_project_cost_scenario_name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (new_project_scenario_id, period_scenario_id,
new_project_cost_scenario_id),
FOREIGN KEY (new_project_scenario_id) REFERENCES subscenarios_new_projects
(new_project_scenario_id),
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id)
);

-- TODO: this needs to have a foreign key to a operational chars scenario
DROP TABLE IF EXISTS subscenarios_fuels;
CREATE TABLE subscenarios_fuels(
fuel_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
fuel_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS subscenarios_hydro_operational_chars;
CREATE TABLE subscenarios_hydro_operational_chars(
existing_project_scenario_id INTEGER,
new_project_scenario_id INTEGER,
period_scenario_id INTEGER,
horizon_scenario_id INTEGER,
hydro_operational_chars_scenario_id INTEGER,
hydro_operational_chars_scenario_name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (existing_project_scenario_id,
new_project_scenario_id, period_scenario_id, horizon_scenario_id,
hydro_operational_chars_scenario_id)
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id),
FOREIGN KEY (period_scenario_id, horizon_scenario_id) REFERENCES
subscenarios_horizons (period_scenario_id, horizon_scenario_id),
FOREIGN KEY (existing_project_scenario_id) REFERENCES
subscenarios_existing_projects (existing_project_scenario_id),
FOREIGN KEY (new_project_scenario_id) REFERENCES
subscenarios_new_projects (new_project_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_variable_generator_profiles;
CREATE TABLE subscenarios_variable_generator_profiles(
existing_project_scenario_id INTEGER,
new_project_scenario_id INTEGER,
project_operational_chars_scenario_id INTEGER,
period_scenario_id INTEGER,
horizon_scenario_id INTEGER,
timepoint_scenario_id INTEGER,
variable_generator_profiles_scenario_id INTEGER,
variable_generator_profiles_scenario_name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (existing_project_scenario_id,
new_project_scenario_id,
project_operational_chars_scenario_id, period_scenario_id, horizon_scenario_id,
timepoint_scenario_id, variable_generator_profiles_scenario_id)
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id),
FOREIGN KEY (period_scenario_id, horizon_scenario_id) REFERENCES
subscenarios_horizons (period_scenario_id, horizon_scenario_id),
FOREIGN KEY (period_scenario_id, horizon_scenario_id, timepoint_scenario_id)
REFERENCES subscenarios_timepoints (period_scenario_id, horizon_scenario_id,
 timepoint_scenario_id),
FOREIGN KEY (existing_project_scenario_id) REFERENCES
subscenarios_existing_projects (existing_project_scenario_id),
FOREIGN KEY (new_project_scenario_id) REFERENCES
subscenarios_new_projects (new_project_scenario_id),
FOREIGN KEY (existing_project_scenario_id, new_project_scenario_id,
project_operational_chars_scenario_id) REFERENCES
subscenarios_project_operational_chars (existing_project_scenario_id,
new_project_scenario_id, project_operational_chars_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_load_zones;
CREATE TABLE subscenarios_project_load_zones(
load_zone_scenario_id INTEGER,
existing_project_scenario_id INTEGER,
new_project_scenario_id INTEGER,
project_load_zone_scenario_id INTEGER,
description VARCHAR(128),
PRIMARY KEY (load_zone_scenario_id, existing_project_scenario_id,
new_project_scenario_id, project_load_zone_scenario_id),
FOREIGN KEY (load_zone_scenario_id) REFERENCES subscenarios_load_zones
(load_zone_scenario_id),
FOREIGN KEY (existing_project_scenario_id) REFERENCES
subscenarios_existing_projects (existing_project_scenario_id),
FOREIGN KEY (new_project_scenario_id) REFERENCES subscenarios_new_projects
(new_project_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_lf_reserves_up_bas;
CREATE TABLE subscenarios_project_lf_reserves_up_bas(
lf_reserves_up_ba_scenario_id INTEGER,
existing_project_scenario_id INTEGER,
new_project_scenario_id INTEGER,
project_lf_reserves_up_ba_scenario_id INTEGER,
description VARCHAR(128),
PRIMARY KEY (lf_reserves_up_ba_scenario_id, existing_project_scenario_id,
new_project_scenario_id, project_lf_reserves_up_ba_scenario_id),
FOREIGN KEY (lf_reserves_up_ba_scenario_id) REFERENCES
subscenarios_lf_reserves_up_bas (lf_reserves_up_ba_scenario_id),
FOREIGN KEY (existing_project_scenario_id) REFERENCES
subscenarios_existing_projects (existing_project_scenario_id),
FOREIGN KEY (new_project_scenario_id) REFERENCES subscenarios_new_projects
(new_project_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_lf_reserves_down_bas;
CREATE TABLE subscenarios_project_lf_reserves_down_bas(
lf_reserves_down_ba_scenario_id INTEGER,
existing_project_scenario_id INTEGER,
new_project_scenario_id INTEGER,
project_lf_reserves_down_ba_scenario_id INTEGER,
description VARCHAR(128),
PRIMARY KEY (lf_reserves_down_ba_scenario_id, existing_project_scenario_id,
new_project_scenario_id, project_lf_reserves_down_ba_scenario_id),
FOREIGN KEY (lf_reserves_down_ba_scenario_id) REFERENCES
subscenarios_lf_reserves_down_bas (lf_reserves_down_ba_scenario_id),
FOREIGN KEY (existing_project_scenario_id) REFERENCES
subscenarios_existing_projects (existing_project_scenario_id),
FOREIGN KEY (new_project_scenario_id) REFERENCES subscenarios_new_projects
(new_project_scenario_id)
);

DROP TABLE IF EXISTS subscenarios_project_rps_zones;
CREATE TABLE subscenarios_project_rps_zones(
rps_zone_scenario_id INTEGER,
existing_project_scenario_id INTEGER,
new_project_scenario_id INTEGER,
project_rps_zone_scenario_id INTEGER,
description VARCHAR(128),
PRIMARY KEY (rps_zone_scenario_id, existing_project_scenario_id,
new_project_scenario_id, project_rps_zone_scenario_id),
FOREIGN KEY (rps_zone_scenario_id) REFERENCES subscenarios_rps_zones
(rps_zone_scenario_id),
FOREIGN KEY (existing_project_scenario_id) REFERENCES
subscenarios_existing_projects (existing_project_scenario_id),
FOREIGN KEY (new_project_scenario_id) REFERENCES subscenarios_new_projects
(new_project_scenario_id)
);

-- Loads
DROP TABLE IF EXISTS subscenarios_loads;
CREATE TABLE subscenarios_loads(
period_scenario_id INTEGER,
horizon_scenario_id INTEGER,
timepoint_scenario_id INTEGER,
load_zone_scenario_id INTEGER,
load_scenario_id INTEGER,
load_scenario_name VARCHAR(32),
description VARCHAR(128),
PRIMARY KEY (period_scenario_id, horizon_scenario_id, timepoint_scenario_id,
load_zone_scenario_id, load_zone_scenario_id),
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id),
FOREIGN KEY (period_scenario_id, horizon_scenario_id) REFERENCES
subscenarios_horizons (period_scenario_id, horizon_scenario_id),
FOREIGN KEY (period_scenario_id, horizon_scenario_id, timepoint_scenario_id)
REFERENCES subscenarios_timepoints (period_scenario_id, horizon_scenario_id,
 timepoint_scenario_id),
FOREIGN KEY (load_zone_scenario_id) REFERENCES subscenarios_load_zones
(load_zone_scenario_id)
);


-- Ancillary services
DROP TABLE IF EXISTS subscenarios_lf_reserves_up;
CREATE TABLE subscenarios_lf_reserves_up(
lf_reserves_up_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
lf_reserves_up_scenario_name VARCHAR(32),
description VARCHAR(128)
);
DROP TABLE IF EXISTS subscenarios_lf_reserves_down;
CREATE TABLE subscenarios_lf_reserves_down(
lf_reserves_down_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
lf_reserves_down_scenario_name VARCHAR(32),
description VARCHAR(128)
);
DROP TABLE IF EXISTS subscenarios_regulation_up;
CREATE TABLE subscenarios_regulation_up(
regulation_up_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
regulation_up_scenario_name VARCHAR(32),
description VARCHAR(128)
);
DROP TABLE IF EXISTS subscenarios_regulation_down;
CREATE TABLE subscenarios_regulation_down(
regulation_down_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
regulation_down_scenario_name VARCHAR(32),
description VARCHAR(128)
);
DROP TABLE IF EXISTS subscenarios_spinning_reserves;
CREATE TABLE subscenarios_spinning_reserves(
spinning_reserves_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
spinning_reserves_scenario_name VARCHAR(32),
description VARCHAR(128)
);
DROP TABLE IF EXISTS subscenarios_frequency_response;
CREATE TABLE subscenarios_frequency_response(
frequency_response_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
frequency_response_scenario_name VARCHAR(32),
description VARCHAR(128)
);

-- Policy
DROP TABLE IF EXISTS subscenarios_rps_zones;
CREATE TABLE subscenarios_rps_zones(
rps_zone_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
rps_zone_scenario_name VARCHAR(32),
description VARCHAR(128)
);


-- -- INPUTS -- --
-- GEOGRAPHY --
-- Load zones
DROP TABLE IF EXISTS load_zones;
CREATE TABLE load_zones(
load_zone_scenario_id INTEGER,
load_zone VARCHAR(32),
overgeneration_penalty_per_mw FLOAT,
unserved_energy_penalty_per_mw FLOAT,
PRIMARY KEY (load_zone_scenario_id, load_zone_name),
UNIQUE (load_zone_scenario_id, load_zone)
);

-- Balancing areas
-- Load-following up
DROP TABLE IF EXISTS lf_reserves_up_bas;
CREATE TABLE lf_reserves_up_bas(
lf_reserves_up_ba_scenario_id INTEGER,
lf_reserves_up_ba_id INTEGER,
lf_reserves_up_ba VARCHAR(32),
lf_reserves_up_violation_penalty_per_mw FLOAT,
PRIMARY KEY (lf_reserves_up_ba_scenario_id, lf_reserves_up_ba_id),
UNIQUE (lf_reserves_up_ba_scenario_id, lf_reserves_up_ba)
);

-- Load-following down
DROP TABLE IF EXISTS lf_reserves_down_bas;
CREATE TABLE lf_reserves_down_bas(
lf_reserves_down_ba_scenario_id INTEGER,
lf_reserves_down_ba_id INTEGER,
lf_reserves_down_ba VARCHAR(32),
lf_reserves_down_violation_penalty_per_mw FLOAT,
PRIMARY KEY (lf_reserves_down_ba_scenario_id, lf_reserves_down_ba_id),
UNIQUE (lf_reserves_down_ba_scenario_id, lf_reserves_down_ba)
);

-- Regulation up
DROP TABLE IF EXISTS regulation_up_bas;
CREATE TABLE regulation_up_bas(
regulation_up_ba_scenario_id INTEGER,
regulation_up_ba_id INTEGER,
regulation_up_ba VARCHAR(32),
regulation_up_violation_penalty_per_mw FLOAT,
PRIMARY KEY (regulation_up_ba_scenario_id, regulation_up_ba_id),
UNIQUE (regulation_up_ba_scenario_id, regulation_up_ba)
);

-- Regulation down
DROP TABLE IF EXISTS regulation_down_bas;
CREATE TABLE regulation_down_bas(
regulation_down_ba_scenario_id INTEGER,
regulation_down_ba_id INTEGER,
regulation_down_ba VARCHAR(32),
regulation_down_violation_penalty_per_mw FLOAT,
PRIMARY KEY (regulation_down_ba_scenario_id, regulation_down_ba_id),
UNIQUE (regulation_down_ba_scenario_id, regulation_down_ba)
);

-- POLICY --
-- RPS zones
DROP TABLE IF EXISTS rps_zones;
CREATE TABLE rps_zones(
rps_zone_scenario_id INTEGER,
rps_zone_id INTEGER,
rps_zone VARCHAR(32),
PRIMARY KEY (rps_zone_scenario_id, rps_zone_id),
UNIQUE (rps_zone_scenario_id, rps_zone)
);

-- TEMPORAL --

-- Investment
-- Periods
DROP TABLE IF EXISTS periods;
CREATE TABLE periods(
period_scenario_id INTEGER,
period INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
PRIMARY KEY (period_scenario_id, period),
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id)
);

-- Operations
-- Horizons
DROP TABLE IF EXISTS horizon_boundary_types;
CREATE TABLE horizon_boundary_types(
horizon_boundary_type VARCHAR(16) PRIMARY KEY,
description VARCHAR(128)
);
-- TODO: add descriptions
INSERT INTO horizon_boundary_types (horizon_boundary_type)
VALUES ('circular'), ('linear');

DROP TABLE IF EXISTS horizons;
CREATE TABLE horizons(
period_scenario_id INTEGER,
horizon_scenario_id INTEGER,
horizon INTEGER,
period INTEGER,
horizon_description VARCHAR(32),
boundary VARCHAR(16),
horizon_weight FLOAT,
PRIMARY KEY (period_scenario_id, horizon_scenario_id, horizon),
FOREIGN KEY (period_scenario_id, horizon_scenario_id) REFERENCES
subscenarios_horizons (period_scenario_id, horizon_scenario_id),
FOREIGN KEY (boundary) REFERENCES horizon_boundary_types
(horizon_boundary_type)
);

-- Timepoints
DROP TABLE IF EXISTS timepoints;
CREATE TABLE timepoints(
period_scenario_id INTEGER,
horizon_scenario_id INTEGER,
timepoint_scenario_id INTEGER,
timepoint INTEGER,
period INTEGER,
horizon INTEGER,
number_of_hours_in_timepoint INTEGER,
PRIMARY KEY (period_scenario_id, horizon_scenario_id, timepoint_scenario_id,
timepoint),
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id),
FOREIGN KEY (horizon_scenario_id) REFERENCES subscenarios_horizons
(horizon_scenario_id)
FOREIGN KEY (timepoint_scenario_id) REFERENCES subscenarios_timepoints
(timepoint_scenario_id)
);


-- PROJECT --
DROP TABLE IF EXISTS capacity_types;
CREATE TABLE capacity_types(
capacity_type VARCHAR(32) PRIMARY KEY,
description VARCHAR(128)
);

-- TODO: add descriptions
INSERT INTO capacity_types (capacity_type)
VALUES ('existing_gen_linear_economic_retirement'),
('existing_gen_no_economic_retirement'), ('new_build_generator'),
('new_build_storage'), ('storage_specified_no_economic_retirement');

DROP TABLE IF EXISTS operational_types;
CREATE TABLE operational_types(
operational_type VARCHAR(32) PRIMARY KEY,
description VARCHAR(128)
);

INSERT INTO operational_types (operational_type)
VALUES ('dispatchable_binary_commit'), ('dispatchable_capacity_commit'),
('dispatchable_continuous_commit'), ('dispatchable_no_commit'),
('hydro_conventional'), ('must_run'), ('storage_generic'), ('variable');

-- TODO: link to operational chars scenarios when implemented
-- TODO: fuel price should vary by year and maybe month
DROP TABLE IF EXISTS fuels;
CREATE TABLE fuels(
fuel_scenario_id INTEGER,
fuel VARCHAR(32),
fuel_price_per_mmbtu FLOAT,
co2_intensity_tons_per_mmbtu FLOAT,
PRIMARY KEY (fuel_scenario_id, fuel),
FOREIGN KEY (fuel_scenario_id) REFERENCES subscenarios_fuels (fuel_scenario_id)
);

-- TODO: capacity type characteristcs should probably be their own subscenario
-- Existing projects
DROP TABLE IF EXISTS existing_projects;
CREATE TABLE existing_projects(
existing_project_scenario_id INTEGER,
project VARCHAR(64),
capacity_type VARCHAR(32),
PRIMARY KEY (existing_project_scenario_id, project),
FOREIGN KEY (capacity_type) REFERENCES capacity_types(capacity_type)
);

-- New projects
DROP TABLE IF EXISTS new_projects;
CREATE TABLE new_projects(
new_project_scenario_id INTEGER,
project VARCHAR(64),
capacity_type VARCHAR(32),
PRIMARY KEY (new_project_scenario_id, project),
FOREIGN KEY (capacity_type) REFERENCES capacity_types (capacity_type),
CHECK (capacity_type = 'new_build_generator' OR capacity_type =
'new_build_storage')
);

-- All projects (existing and new)
DROP TABLE IF EXISTS all_projects;
CREATE TABLE all_projects(
existing_project_scenario_id INTEGER,
new_project_scenario_id INTEGER,
project VARCHAR(64),
capacity_type VARCHAR(32),
PRIMARY KEY (existing_project_scenario_id, new_project_scenario_id, project),
FOREIGN KEY (existing_project_scenario_id) REFERENCES
subscenarios_existing_projects (existing_project_scenario_id),
FOREIGN KEY (new_project_scenario_id) REFERENCES
subscenarios_new_projects (new_project_scenario_id)
);

-- Project operational characteristics
DROP TABLE IF EXISTS project_operational_chars;
CREATE TABLE project_operational_chars(
existing_project_scenario_id INTEGER,
new_project_scenario_id INTEGER,
project_operational_chars_scenario_id INTEGER,
project VARCHAR(64),
operational_type VARCHAR(32),
technology VARCHAR(32),
fuel VARCHAR(32),
minimum_input_mmbtu_per_hr FLOAT,
inc_heat_rate_mmbtu_per_mwh FLOAT,
min_stable_level FLOAT,
unit_size_mw FLOAT,
startup_cost FLOAT,
shutdown_cost FLOAT,
charging_efficiency FLOAT,
discharging_efficiency FLOAT,
PRIMARY KEY (existing_project_scenario_id, new_project_scenario_id,
project_operational_chars_scenario_id, project),
FOREIGN KEY (existing_project_scenario_id, new_project_scenario_id, project)
 REFERENCES all_projects (existing_project_scenario_id,
 new_project_scenario_id, project),
FOREIGN KEY (existing_project_scenario_id, new_project_scenario_id,
project_operational_chars_scenario_id) REFERENCES
subscenarios_project_operational_chars (existing_project_scenario_id,
new_project_scenario_id, project_operational_chars_scenario_id),
FOREIGN KEY (operational_type) REFERENCES operational_types (operational_type)
);

DROP TABLE IF EXISTS hydro_operational_chars;
CREATE TABLE hydro_operational_chars(
existing_project_scenario_id INTEGER,
new_project_scenario_id INTEGER,
period_scenario_id INTEGER,
horizon_scenario_id INTEGER,
hydro_operational_chars_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
average_power_mwa FLOAT,
min_power_mw FLOAT,
max_power_mw FLOAT,
PRIMARY KEY (existing_project_scenario_id, new_project_scenario_id,
period_scenario_id,  horizon_scenario_id,
hydro_operational_chars_scenario_id, project, period, horizon),
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id),
FOREIGN KEY (period_scenario_id, period) REFERENCES periods
(period_scenario_id, period),
FOREIGN KEY (existing_project_scenario_id) REFERENCES
subscenarios_existing_projects (existing_project_scenario_id),
FOREIGN KEY (existing_project_scenario_id, new_project_scenario_id, project)
REFERENCES all_projects (existing_project_scenario_id,
new_project_scenario_id, project),
FOREIGN KEY (existing_project_scenario_id, project) REFERENCES
existing_projects (existing_project_scenario_id, project),
FOREIGN KEY (new_project_scenario_id, project) REFERENCES
new_projects (new_project_scenario_id, project),
FOREIGN KEY (period_scenario_id, horizon_scenario_id) REFERENCES
subscenarios_horizons (period_scenario_id, horizon_scenario_id),
FOREIGN KEY (period_scenario_id, horizon_scenario_id, horizon) REFERENCES
horizons (period_scenario_id, horizon_scenario_id, horizon),
FOREIGN KEY (existing_project_scenario_id,
new_project_scenario_id, period_scenario_id, horizon_scenario_id,
hydro_operational_chars_scenario_id) REFERENCES
subscenarios_hydro_operational_chars (existing_project_scenario_id,
new_project_scenario_id, period_scenario_id, horizon_scenario_id,
hydro_operational_chars_scenario_id)
);

DROP TABLE IF EXISTS variable_generator_profiles;
CREATE TABLE variable_generator_profiles(
existing_project_scenario_id INTEGER,
new_project_scenario_id INTEGER,
project_operational_chars_scenario_id INTEGER,
period_scenario_id INTEGER,
horizon_scenario_id INTEGER,
timepoint_scenario_id INTEGER,
variable_generator_profiles_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
horizon INTEGER,
timepoint INTEGER,
cap_factor FLOAT,
PRIMARY KEY (existing_project_scenario_id, new_project_scenario_id,
project_operational_chars_scenario_id,
period_scenario_id,  horizon_scenario_id, timepoint_scenario_id,
variable_generator_profiles_scenario_id, project, period, horizon, timepoint),
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id),
FOREIGN KEY (period_scenario_id, period) REFERENCES periods
(period_scenario_id, period),
FOREIGN KEY (existing_project_scenario_id) REFERENCES
subscenarios_existing_projects (existing_project_scenario_id),
FOREIGN KEY (existing_project_scenario_id, new_project_scenario_id, project)
REFERENCES all_projects (existing_project_scenario_id,
new_project_scenario_id, project),
FOREIGN KEY (existing_project_scenario_id, project) REFERENCES
existing_projects (existing_project_scenario_id, project),
FOREIGN KEY (new_project_scenario_id, project) REFERENCES
new_projects (new_project_scenario_id, project),
FOREIGN KEY (period_scenario_id, horizon_scenario_id) REFERENCES
subscenarios_horizons (period_scenario_id, horizon_scenario_id),
FOREIGN KEY (period_scenario_id, horizon_scenario_id, horizon) REFERENCES
horizons (period_scenario_id, horizon_scenario_id, horizon),
FOREIGN KEY (period_scenario_id, horizon_scenario_id, timepoint_scenario_id) 
REFERENCES subscenarios_timepoints (period_scenario_id, horizon_scenario_id,
 timepoint_scenario_id),
FOREIGN KEY (period_scenario_id, horizon_scenario_id, timepoint_scenario_id, 
timepoint) REFERENCES timepoints (period_scenario_id, horizon_scenario_id, 
timepoint_scenario_id, timepoint),
FOREIGN KEY (existing_project_scenario_id,
new_project_scenario_id, project_operational_chars_scenario_id,
period_scenario_id, horizon_scenario_id,
timepoint_scenario_id, variable_generator_profiles_scenario_id) REFERENCES
subscenarios_variable_generator_profiles (existing_project_scenario_id,
new_project_scenario_id, project_operational_chars_scenario_id,
period_scenario_id, horizon_scenario_id,
timepoint_scenario_id, variable_generator_profiles_scenario_id)
);



-- Project-load zones
DROP TABLE IF EXISTS project_load_zones;
CREATE TABLE project_load_zones(
load_zone_scenario_id INTEGER,
existing_project_scenario_id INTEGER,
new_project_scenario_id INTEGER,
project_load_zone_scenario_id INTEGER,
project VARCHAR(64),
load_zone VARCHAR(32),
PRIMARY KEY (load_zone_scenario_id, existing_project_scenario_id,
new_project_scenario_id, project_load_zone_scenario_id, project),
FOREIGN KEY (existing_project_scenario_id, new_project_scenario_id, project)
 REFERENCES all_projects (existing_project_scenario_id,
 new_project_scenario_id,
  project),
FOREIGN KEY (load_zone_scenario_id) REFERENCES subscenarios_load_zones
(load_zone_scenario_id)
);

-- Project-LF_Up BAs
DROP TABLE IF EXISTS project_lf_reserves_up_bas;
CREATE TABLE project_lf_reserves_up_bas(
lf_reserves_up_ba_scenario_id INTEGER,
existing_project_scenario_id INTEGER,
new_project_scenario_id INTEGER,
project_lf_reserves_up_ba_scenario_id INTEGER,
project VARCHAR(64),
lf_reserves_up_ba VARCHAR(32),
PRIMARY KEY (lf_reserves_up_ba_scenario_id, existing_project_scenario_id,
new_project_scenario_id, project_lf_reserves_up_ba_scenario_id, project),
FOREIGN KEY (existing_project_scenario_id, new_project_scenario_id, project)
 REFERENCES all_projects (existing_project_scenario_id,
 new_project_scenario_id,
  project),
FOREIGN KEY (lf_reserves_up_ba_scenario_id) REFERENCES
subscenarios_lf_reserves_up_bas (lf_reserves_up_ba_scenario_id)
);

-- Project-LF_Down BAs
DROP TABLE IF EXISTS project_lf_reserves_down_bas;
CREATE TABLE project_lf_reserves_down_bas(
lf_reserves_down_ba_scenario_id INTEGER,
existing_project_scenario_id INTEGER,
new_project_scenario_id INTEGER,
project_lf_reserves_down_ba_scenario_id INTEGER,
project VARCHAR(64),
lf_reserves_down_ba VARCHAR(32),
PRIMARY KEY (lf_reserves_down_ba_scenario_id, existing_project_scenario_id,
new_project_scenario_id, project_lf_reserves_down_ba_scenario_id, project),
FOREIGN KEY (existing_project_scenario_id, new_project_scenario_id, project)
 REFERENCES all_projects (existing_project_scenario_id,
 new_project_scenario_id,
  project),
FOREIGN KEY (lf_reserves_down_ba_scenario_id) REFERENCES
subscenarios_lf_reserves_down_bas (lf_reserves_down_ba_scenario_id)
);

-- Project-RPS zones
DROP TABLE IF EXISTS project_rps_zones;
CREATE TABLE project_rps_zones(
rps_zone_scenario_id INTEGER,
existing_project_scenario_id INTEGER,
new_project_scenario_id INTEGER,
project_rps_zone_scenario_id INTEGER,
project VARCHAR(64),
rps_zone VARCHAR(32),
PRIMARY KEY (rps_zone_scenario_id, existing_project_scenario_id,
new_project_scenario_id, project_rps_zone_scenario_id, project),
FOREIGN KEY (existing_project_scenario_id, new_project_scenario_id, project)
 REFERENCES all_projects (existing_project_scenario_id,
 new_project_scenario_id,
  project),
FOREIGN KEY (rps_zone_scenario_id) REFERENCES subscenarios_rps_zones
(rps_zone_scenario_id)
);


-- Project capacity/availability

-- Existing projects
-- TODO: implement check that ALL project from a certain
-- existing_project_scenario_id from the existing_projects table are included
-- here under the same existing_project_scenario_id
DROP TABLE IF EXISTS existing_project_capacity;
CREATE TABLE existing_project_capacity(
existing_project_scenario_id INTEGER,
period_scenario_id INTEGER,
existing_project_capacity_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
capacity_type VARCHAR(32),
existing_capacity_mw FLOAT,
existing_capacity_mwh FLOAT,
annual_fixed_cost_per_mw_year FLOAT,
annual_fixed_cost_per_mwh_year FLOAT,
PRIMARY KEY (existing_project_scenario_id, period_scenario_id, project, period,
existing_project_capacity_scenario_id),
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id),
FOREIGN KEY (period_scenario_id, period) REFERENCES periods
(period_scenario_id, period),
FOREIGN KEY (existing_project_scenario_id, project) REFERENCES
existing_projects (existing_project_scenario_id, project)
--CHECK (existing_capacity_mwh IS NULL and capacity_type !=
--'storage_specified_no_economic_retirement'),
--CHECK (existing_capacity_mwh IS NOT NULL and capacity_type =
--'storage_specified_no_economic_retirement'),
--CHECK (annual_fixed_cost_per_mwh_year IS NULL and capacity_type !=
--'storage_specified_no_economic_retirement'),
--CHECK (annual_fixed_cost_per_mwh_year IS NOT NULL and capacity_type =
--'storage_specified_no_economic_retirement')
);

-- New projects
-- TODO: consolidate new generation and new storage into single table
DROP TABLE IF EXISTS new_project_cost;
CREATE TABLE new_project_cost(
new_project_scenario_id INTEGER,
period_scenario_id INTEGER,
new_project_cost_scenario_id INTEGER,
project VARCHAR(64),
period INTEGER,
capacity_type VARCHAR(32),
lifetime_yrs INTEGER,
annualized_real_cost_per_kw_yr FLOAT,
annualized_real_cost_per_kwh_yr FLOAT,  -- storage only
PRIMARY KEY (new_project_scenario_id, period_scenario_id,
new_project_cost_scenario_id, project, period),
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id),
FOREIGN KEY (period_scenario_id, period) REFERENCES periods
(period_scenario_id, period),
FOREIGN KEY (new_project_scenario_id, project) REFERENCES
new_projects (new_project_scenario_id, project)
--CHECK (annualized_real_cost_per_mwh_yr IS NULL AND capacity_type !=
--'new_build_storage'),
--CHECK (annualized_real_cost_per_mwh_yr IS NOT NULL AND capacity_type =
--'new_build_storage')
);


-- SYSTEM --
-- Load
DROP TABLE IF EXISTS loads;
CREATE TABLE loads(
period_scenario_id INTEGER,
horizon_scenario_id INTEGER,
timepoint_scenario_id INTEGER,
load_zone_scenario_id INTEGER,
load_scenario_id INTEGER,
load_zone VARCHAR(32),
timepoint INTEGER,
load_mw FLOAT,
PRIMARY KEY (period_scenario_id, horizon_scenario_id, timepoint_scenario_id,
load_zone_scenario_id, load_scenario_id, load_zone, timepoint),
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id),
FOREIGN KEY (period_scenario_id, horizon_scenario_id) REFERENCES
subscenarios_horizons (period_scenario_id, horizon_scenario_id),
FOREIGN KEY (period_scenario_id, horizon_scenario_id, timepoint_scenario_id)
REFERENCES subscenarios_timepoints (period_scenario_id, horizon_scenario_id,
 timepoint_scenario_id),
FOREIGN KEY (load_zone_scenario_id) REFERENCES subscenarios_load_zones
(load_zone_scenario_id),
FOREIGN KEY (period_scenario_id, horizon_scenario_id, timepoint_scenario_id,
load_zone_scenario_id, load_scenario_id) REFERENCES subscenarios_loads
(period_scenario_id, horizon_scenario_id, timepoint_scenario_id,
load_zone_scenario_id, load_scenario_id)
);

DROP TABLE IF EXISTS lf_reserves_up;
CREATE TABLE lf_reserves_up(
lf_reserves_up_zone_scenario_id INTEGER,
period_scenario_id INTEGER,
timepoint_scenario_id INTEGER,
lf_reserves_up_scenario_id INTEGER,
lf_reserves_up_scenario_name INTEGER,
lf_reserves_up_zone_id INTEGER,
lf_reserves_up_zone VARCHAR(32),
timepoint INTEGER,
lf_reserves_up_mw FLOAT,
PRIMARY KEY (lf_reserves_up_zone_scenario_id, period_scenario_id,
timepoint_scenario_id, lf_reserves_up_scenario_id, lf_reserves_up_zone_id),
UNIQUE (lf_reserves_up_zone_scenario_id, period_scenario_id, timepoint_scenario_id,
lf_reserves_up_scenario_id, lf_reserves_up_zone),
UNIQUE (lf_reserves_up_zone_scenario_id, period_scenario_id, timepoint_scenario_id,
lf_reserves_up_scenario_name, lf_reserves_up_zone),
FOREIGN KEY (lf_reserves_up_zone_scenario_id) REFERENCES subscenarios_lf_reserves_up
(lf_reserves_up_zone_scenario_id),
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id),
FOREIGN KEY (timepoint_scenario_id) REFERENCES subscenarios_timepoints
(timepoint_scenario_id)
);

DROP TABLE IF EXISTS lf_reserves_down;
CREATE TABLE lf_reserves_down(
lf_reserves_down_zone_scenario_id INTEGER,
period_scenario_id INTEGER,
timepoint_scenario_id INTEGER,
lf_reserves_down_scenario_id INTEGER,
lf_reserves_down_scenario_name INTEGER,
lf_reserves_down_zone_id INTEGER,
lf_reserves_down_zone VARCHAR(32),
timepoint INTEGER,
lf_reserves_down_mw FLOAT,
PRIMARY KEY (lf_reserves_down_zone_scenario_id, period_scenario_id,
timepoint_scenario_id, lf_reserves_down_scenario_id, lf_reserves_down_zone_id),
UNIQUE (lf_reserves_down_zone_scenario_id, period_scenario_id, timepoint_scenario_id,
lf_reserves_down_scenario_id, lf_reserves_down_zone),
UNIQUE (lf_reserves_down_zone_scenario_id, period_scenario_id, timepoint_scenario_id,
lf_reserves_down_scenario_name, lf_reserves_down_zone),
FOREIGN KEY (lf_reserves_down_zone_scenario_id) REFERENCES subscenarios_lf_reserves_down
(lf_reserves_down_zone_scenario_id),
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id),
FOREIGN KEY (timepoint_scenario_id) REFERENCES subscenarios_timepoints
(timepoint_scenario_id)
);


DROP TABLE IF EXISTS regulation_up;
CREATE TABLE regulation_up(
regulation_up_zone_scenario_id INTEGER,
period_scenario_id INTEGER,
timepoint_scenario_id INTEGER,
regulation_up_scenario_id INTEGER,
regulation_up_scenario_name INTEGER,
regulation_up_zone_id INTEGER,
regulation_up_zone VARCHAR(32),
timepoint INTEGER,
regulation_up_mw FLOAT,
PRIMARY KEY (regulation_up_zone_scenario_id, period_scenario_id,
timepoint_scenario_id, regulation_up_scenario_id, regulation_up_zone_id),
UNIQUE (regulation_up_zone_scenario_id, period_scenario_id, timepoint_scenario_id,
regulation_up_scenario_id, regulation_up_zone),
UNIQUE (regulation_up_zone_scenario_id, period_scenario_id, timepoint_scenario_id,
regulation_up_scenario_name, regulation_up_zone),
FOREIGN KEY (regulation_up_zone_scenario_id) REFERENCES subscenarios_regulation_up
(regulation_up_zone_scenario_id),
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id),
FOREIGN KEY (timepoint_scenario_id) REFERENCES subscenarios_timepoints
(timepoint_scenario_id)
);

DROP TABLE IF EXISTS regulation_down;
CREATE TABLE regulation_down(
regulation_down_zone_scenario_id INTEGER,
period_scenario_id INTEGER,
timepoint_scenario_id INTEGER,
regulation_down_scenario_id INTEGER,
regulation_down_scenario_name INTEGER,
regulation_down_zone_id INTEGER,
regulation_down_zone VARCHAR(32),
timepoint INTEGER,
regulation_down_mw FLOAT,
PRIMARY KEY (regulation_down_zone_scenario_id, period_scenario_id,
timepoint_scenario_id, regulation_down_scenario_id, regulation_down_zone_id),
UNIQUE (regulation_down_zone_scenario_id, period_scenario_id, timepoint_scenario_id,
regulation_down_scenario_id, regulation_down_zone),
UNIQUE (regulation_down_zone_scenario_id, period_scenario_id, timepoint_scenario_id,
regulation_down_scenario_name, regulation_down_zone),
FOREIGN KEY (regulation_down_zone_scenario_id) REFERENCES subscenarios_regulation_down
(regulation_down_zone_scenario_id),
FOREIGN KEY (period_scenario_id) REFERENCES subscenarios_periods
(period_scenario_id),
FOREIGN KEY (timepoint_scenario_id) REFERENCES subscenarios_timepoints
(timepoint_scenario_id)
);


-- TRANSMISSION --
DROP TABLE IF EXISTS transmission_lines;
CREATE TABLE transmission_lines(
load_zone_scenario_id INTEGER,
transmission_scenario_id INTEGER,
transmission_line VARCHAR(64),
tx_capacity_type VARCHAR(32),
load_zone_from VARCHAR(32),
load_zone_to VARCHAR(32),
PRIMARY KEY (load_zone_scenario_id, transmission_scenario_id,
transmission_line)
);

DROP TABLE IF EXISTS transmission_line_capacities;
CREATE TABLE transmission_line_capacities(
period_scenario_id INTEGER,
load_zone_scenario_id INTEGER,
transmission_scenario_id INTEGER,
transmission_line VARCHAR(64),
period INTEGER,
capacity_mw FLOAT,
PRIMARY KEY (period_scenario_id, load_zone_scenario_id,
transmission_scenario_id, transmission_line, period)
);

-- POLICY --
DROP TABLE IF EXISTS rps_targets;
CREATE TABLE rps_targets(
period_scenario_id INTEGER,
rps_zone_scenario_id INTEGER,
rps_target_scenario_id INTEGER,
rps_zone VARCHAR(32),
period INTEGER,
rps_target_mwh FLOAT,
PRIMARY KEY (period_scenario_id, rps_zone_scenario_id,
rps_target_scenario_id, rps_zone, period)
);
