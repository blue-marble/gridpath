-- -- SCENARIOS -- --
-- TODO: what will be varied?

DROP TABLE IF EXISTS scenarios;
CREATE TABLE scenarios(
scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
load_zone_scenario_id INTEGER,
FOREIGN KEY (load_zone_scenario_id) REFERENCES load_zone_scenarios
(load_zone_scenario_id)
);

-- -- SUB-SCENARIOS -- --
DROP TABLE IF EXISTS load_zone_scenarios;
CREATE TABLE load_zone_scenarios(
load_zone_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
load_zone_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS timepoint_scenarios;
CREATE TABLE timepoint_scenarios(
timepoint_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
timepoint_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS project_scenarios;
CREATE TABLE project_scenarios(
project_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
project_scenario_name VARCHAR(32),
description VARCHAR(128)
);

-- -- INPUTS -- --
-- GEOGRAPHY --
-- Load zones
DROP TABLE IF EXISTS load_zones;
CREATE TABLE load_zones(
load_zone_scenario_id INTEGER,
load_zone_id INTEGER,
load_zone VARCHAR(32),
overgeneration_penalty_per_mw FLOAT,
unserved_energy_penalty_per_mw FLOAT,
PRIMARY KEY (load_zone_scenario_id, load_zone_id),
UNIQUE (load_zone_scenario_id, load_zone)
);

-- Balancing areas
-- Load-following up
DROP TABLE IF EXISTS load_following_up_bas;
CREATE TABLE load_following_up_bas(
load_following_up_ba_scenario_id INTEGER,
load_following_up_ba_id INTEGER,
load_following_up_ba VARCHAR(32),
load_following_up_violation_penalty_per_mw FLOAT,
PRIMARY KEY (load_following_up_ba_scenario_id, load_following_up_ba_id),
UNIQUE (load_following_up_ba_scenario_id, load_following_up_ba)
);

-- Load-following down
DROP TABLE IF EXISTS load_following_down_bas;
CREATE TABLE load_following_down_bas(
load_following_down_ba_scenario_id INTEGER,
load_following_down_ba_id INTEGER,
load_following_down_ba VARCHAR(32),
load_following_down_violation_penalty_per_mw FLOAT,
PRIMARY KEY (load_following_down_ba_scenario_id, load_following_down_ba_id),
UNIQUE (load_following_down_ba_scenario_id, load_following_down_ba)
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


-- TEMPORAL --
-- Timepoints
DROP TABLE IF EXISTS timepoints;
CREATE TABLE timepoints(
timepoint_scenario_id INTEGER,
timepoint INTEGER,
period INTEGER,
horizon INTEGER,
number_of_hours_in_timepoint INTEGER,
PRIMARY KEY (timepoint_scenario_id, timepoint)
);

-- Periods
DROP TABLE IF EXISTS periods;
CREATE TABLE periods(
timepoint_scenario_id INTEGER,
period INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
PRIMARY KEY (timepoint_scenario_id, period)
);

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
timepoint_scenario_id INTEGER,
horizon INTEGER,
horizon_description VARCHAR(32),
boundary VARCHAR(16),
horizon_weight FLOAT,
PRIMARY KEY (timepoint_scenario_id, horizon),
FOREIGN KEY (boundary) REFERENCES horizon_boundary_types
(horizon_boundary_type)
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

DROP TABLE IF EXISTS projects;
CREATE TABLE projects(
project_scenario_id INTEGER,
project VARCHAR(32),
capacity_type VARCHAR(32),
operational_type VARCHAR(32),
technology VARCHAR(32),
load_zone VARCHAR(32),
fuel VARCHAR(32),
minimum_input_mmbtu_per_hr FLOAT,
inc_heat_rate_mmbtu_per_mwh FLOAT,
min_stable_level FLOAT,
unit_size_mw FLOAT,
startup_cost FLOAT,
shutdown_cost FLOAT,
charging_efficiency FLOAT,
discharging_efficiency FLOAT,
FOREIGN KEY (project_scenario_id) REFERENCES project_scenarios
(project_scenario_id)
-- Data checks --
-- Operational types
-- Fuel
CHECK (operational_type = 'dispatchable_binary_commit' AND fuel IS NOT NULL),
CHECK (operational_type = 'dispatchable_capacity_commit' AND fuel IS NOT NULL),
CHECK (operational_type = 'dispatchable_continuous_commit' AND fuel IS NOT
NULL),
CHECK (operational_type = 'dispatchable_no_commit' AND fuel IS NOT NULL),
CHECK (operational_type = 'hydro_conventional' AND fuel IS NULL)
CHECK (operational_type = 'must_run' AND fuel IS NULL),
CHECK (operational_type = 'storage_generic' AND fuel IS NULL),
CHECK (operational_type = 'variable' AND fuel IS NULL),
-- Minimum input
CHECK (operational_type = 'dispatchable_binary_commit'
AND minimum_input_mmbtu_per_hr IS NOT NULL),
CHECK (operational_type = 'dispatchable_capacity_commit'
AND minimum_input_mmbtu_per_hr IS NOT NULL),
CHECK (operational_type = 'dispatchable_continuous_commit'
AND minimum_input_mmbtu_per_hr IS NOT NULL),
CHECK (operational_type = 'dispatchable_no_commit'
AND minimum_input_mmbtu_per_hr = 0),
CHECK (operational_type = 'hydro_conventional'
AND minimum_input_mmbtu_per_hr IS NULL),
CHECK (operational_type = 'must_run' AND minimum_input_mmbtu_per_hr IS NULL),
CHECK (operational_type = 'storage_generic'
AND minimum_input_mmbtu_per_hr IS NULL),
CHECK (operational_type = 'variable' AND minimum_input_mmbtu_per_hr IS NULL),
-- Incremental heat rate
CHECK (operational_type = 'dispatchable_binary_commit'
AND inc_heat_rate_mmbtu_per_mwh IS NOT NULL),
CHECK (operational_type = 'dispatchable_capacity_commit'
AND inc_heat_rate_mmbtu_per_mwh IS NOT NULL),
CHECK (operational_type = 'dispatchable_continuous_commit'
AND inc_heat_rate_mmbtu_per_mwh IS NOT NULL),
CHECK (operational_type = 'dispatchable_no_commit'
AND inc_heat_rate_mmbtu_per_mwh IS NOT NULL),
CHECK (operational_type = 'hydro_conventional'
AND inc_heat_rate_mmbtu_per_mwh IS NULL),
CHECK (operational_type = 'must_run' AND inc_heat_rate_mmbtu_per_mwh IS NULL),
CHECK (operational_type = 'storage_generic'
AND inc_heat_rate_mmbtu_per_mwh IS NULL),
CHECK (operational_type = 'variable' AND inc_heat_rate_mmbtu_per_mwh IS NULL),
-- Minimum stable level
CHECK (operational_type = 'dispatchable_binary_commit' AND min_stable_level
>= 0 AND min_stable_level <= 1),
CHECK (operational_type = 'dispatchable_capacity_commit' AND min_stable_level
>= 0 AND min_stable_level <= 1),
CHECK (operational_type = 'dispatchable_continuous_commit' AND min_stable_level
>= 0 AND min_stable_level <= 1),
CHECK (operational_type = 'dispatchable_no_commit' AND min_stable_level IS
NULL),
CHECK (operational_type = 'hydro_conventional' AND min_stable_level IS NULL),
CHECK (operational_type = 'must_run' AND min_stable_level IS NULL),
CHECK (operational_type = 'storage_generic' AND min_stable_level IS NULL),
CHECK (operational_type = 'variable' AND min_stable_level IS NULL),
-- Unit size
CHECK (operational_type = 'dispatchable_binary_commit' AND unit_size_mw IS
NOT NULL),
CHECK (operational_type = 'dispatchable_capacity_commit' AND unit_size_mw IS
 NOT NULL),
CHECK (operational_type = 'dispatchable_continuous_commit' AND unit_size_mw
IS NULL),
CHECK (operational_type = 'dispatchable_no_commit' AND unit_size_mw IS
NULL),
CHECK (operational_type = 'hydro_conventional' AND unit_size_mw IS NULL),
CHECK (operational_type = 'must_run' AND unit_size_mw IS NULL),
CHECK (operational_type = 'storage_generic' AND unit_size_mw IS NULL),
CHECK (operational_type = 'variable' AND unit_size_mw IS NULL),
-- Startup cost
CHECK (operational_type = 'dispatchable_binary_commit' 
AND startup_cost IS NOT NULL),
CHECK (operational_type = 'dispatchable_capacity_commit'
AND startup_cost IS NOT NULL),
CHECK (operational_type = 'dispatchable_continuous_commit'
AND startup_cost IS NOT NULL),
CHECK (operational_type = 'dispatchable_no_commit'
AND startup_cost IS NULL),
CHECK (operational_type = 'hydro_conventional'
AND startup_cost IS NULL),
CHECK (operational_type = 'must_run' AND startup_cost IS NULL),
CHECK (operational_type = 'storage_generic'
AND startup_cost IS NULL),
-- Shutdown cost
CHECK (operational_type = 'dispatchable_binary_commit'
AND shutdown_cost IS NOT NULL),
CHECK (operational_type = 'dispatchable_capacity_commit'
AND shutdown_cost IS NOT NULL),
CHECK (operational_type = 'dispatchable_continuous_commit'
AND shutdown_cost IS NOT NULL),
CHECK (operational_type = 'dispatchable_no_commit'
AND shutdown_cost IS NULL),
CHECK (operational_type = 'hydro_conventional'
AND shutdown_cost IS NULL),
CHECK (operational_type = 'must_run' AND shutdown_cost IS NULL),
CHECK (operational_type = 'storage_generic'
AND shutdown_cost IS NULL),
-- Charging efficiency
CHECK (operational_type = 'dispatchable_binary_commit'
AND charging_efficiency IS NULL),
CHECK (operational_type = 'dispatchable_capacity_commit'
AND charging_efficiency IS NULL),
CHECK (operational_type = 'dispatchable_continuous_commit'
AND charging_efficiency IS NULL),
CHECK (operational_type = 'dispatchable_no_commit'
AND charging_efficiency IS NULL),
CHECK (operational_type = 'hydro_conventional'
AND charging_efficiency IS NULL),
CHECK (operational_type = 'must_run' AND charging_efficiency IS NULL),
CHECK (operational_type = 'storage_generic'
AND charging_efficiency IS NOT NULL AND charging_efficiency >= 0 AND charging_efficiency <= 1),
-- Discharging efficiency
CHECK (operational_type = 'dispatchable_binary_commit'
AND discharging_efficiency IS NULL),
CHECK (operational_type = 'dispatchable_capacity_commit'
AND discharging_efficiency IS NULL),
CHECK (operational_type = 'dispatchable_continuous_commit'
AND discharging_efficiency IS NULL),
CHECK (operational_type = 'dispatchable_no_commit'
AND discharging_efficiency IS NULL),
CHECK (operational_type = 'hydro_conventional'
AND discharging_efficiency IS NULL),
CHECK (operational_type = 'must_run' AND discharging_efficiency IS NULL),
CHECK (operational_type = 'storage_generic'
AND discharging_efficiency IS NOT NULL and discharging_efficiency >= 0 AND
discharging_efficiency <= 1)
);



-- SYSTEM --
-- Load
DROP TABLE IF EXISTS loads;
CREATE TABLE loads(
load_zone_scenario_id INTEGER,
timepoint_scenario_id INTEGER,
load_scenario_id INTEGER,
load_scenario_name INTEGER,
load_zone_id INTEGER,
load_zone VARCHAR(32),
timepoint INTEGER,
load_mw FLOAT,
PRIMARY KEY (load_zone_scenario_id, timepoint_scenario_id, load_scenario_id,
load_zone_id),
UNIQUE (load_zone_scenario_id, timepoint_scenario_id, load_scenario_id,
load_zone),
UNIQUE (load_zone_scenario_id, timepoint_scenario_id, load_scenario_name,
load_zone),
FOREIGN KEY (load_zone_scenario_id) REFERENCES load_zone_scenarios
(load_zone_scenario_id),
FOREIGN KEY (timepoint_scenario_id) REFERENCES time
);