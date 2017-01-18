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

DROP TABLE IF EXISTS lf_reserves_up_zone_scenarios;
CREATE TABLE lf_reserves_up_zone_scenarios(
lf_reserves_up_zone_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
lf_reserves_up_zone_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS lf_reserves_down_zone_scenarios;
CREATE TABLE lf_reserves_down_zone_scenarios(
lf_reserves_down_zone_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
lf_reserves_down_zone_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS regulation_up_zone_scenarios;
CREATE TABLE regulation_up_zone_scenarios(
regulation_up_zone_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
regulation_up_zone_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS regulation_down_zone_scenarios;
CREATE TABLE regulation_down_zone_scenarios(
regulation_down_zone_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
regulation_down_zone_scenario_name VARCHAR(32),
description VARCHAR(128)
);


DROP TABLE IF EXISTS period_scenarios;
CREATE TABLE period_scenarios(
period_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
period_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS timepoint_scenarios;
CREATE TABLE timepoint_scenarios(
timepoint_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
timepoint_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS existing_project_scenarios;
CREATE TABLE existing_project_scenarios(
existing_project_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
existing_project_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS existing_project_capacity_scenarios;
CREATE TABLE existing_project_capacity_scenarios(
existing_project_capacity_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
existing_project_capacity_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS new_project_scenarios;
CREATE TABLE new_project_scenarios(
new_project_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
new_project_scenario_name VARCHAR(32),
description VARCHAR(128)
);

DROP TABLE IF EXISTS new_project_cost_scenarios;
CREATE TABLE new_project_cost_scenarios(
new_project_cost_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
new_project_cost_scenario_name VARCHAR(32),
description VARCHAR(128)
);


-- Loads
DROP TABLE IF EXISTS load_scenarios;
CREATE TABLE load_scenarios(
load_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
load_scenario_name VARCHAR(32),
description VARCHAR(128)
);


-- Ancillary services
DROP TABLE IF EXISTS lf_reserves_up_scenarios;
CREATE TABLE lf_reserves_up_scenarios(
lf_reserves_up_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
lf_reserves_up_scenario_name VARCHAR(32),
description VARCHAR(128)
);
DROP TABLE IF EXISTS lf_reserves_down_scenarios;
CREATE TABLE lf_reserves_down_scenarios(
lf_reserves_down_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
lf_reserves_down_scenario_name VARCHAR(32),
description VARCHAR(128)
);
DROP TABLE IF EXISTS regulation_up_scenarios;
CREATE TABLE regulation_up_scenarios(
regulation_up_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
regulation_up_scenario_name VARCHAR(32),
description VARCHAR(128)
);
DROP TABLE IF EXISTS regulation_down_scenarios;
CREATE TABLE regulation_down_scenarios(
regulation_down_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
regulation_down_scenario_name VARCHAR(32),
description VARCHAR(128)
);
DROP TABLE IF EXISTS spinning_reserves_scenarios;
CREATE TABLE spinning_reserves_scenarios(
spinning_reserves_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
spinning_reserves_scenario_name VARCHAR(32),
description VARCHAR(128)
);
DROP TABLE IF EXISTS frequency_response_scenarios;
CREATE TABLE frequency_response_scenarios(
frequency_response_scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
frequency_response_scenario_name VARCHAR(32),
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

-- Investment
-- Periods
DROP TABLE IF EXISTS periods;
CREATE TABLE periods(
period_scenario_id INTEGER,
period INTEGER,
discount_factor FLOAT,
number_years_represented FLOAT,
PRIMARY KEY (period_scenario_id, period),
FOREIGN KEY (period_scenario_id) REFERENCES period_scenarios
(period_scenario_id)
);

-- Operations
-- Timepoints
DROP TABLE IF EXISTS timepoints;
CREATE TABLE timepoints(
period_scenario_id INTEGER,
timepoint_scenario_id INTEGER,
timepoint INTEGER,
period INTEGER,
horizon INTEGER,
number_of_hours_in_timepoint INTEGER,
PRIMARY KEY (period_scenario_id, timepoint_scenario_id, timepoint),
FOREIGN KEY (period_scenario_id) REFERENCES period_scenarios
(period_scenario_id),
FOREIGN KEY (timepoint_scenario_id) REFERENCES timepoint_scenarios
(timepoint_scenario_id)
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
horizon_scenario_id INTEGER,
horizon INTEGER,
horizon_description VARCHAR(32),
boundary VARCHAR(16),
horizon_weight FLOAT,
PRIMARY KEY (timepoint_scenario_id, horizon_scenario_id, horizon),
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

DROP TABLE IF EXISTS operational_types;
CREATE TABLE operational_types(
operational_type VARCHAR(32) PRIMARY KEY,
description VARCHAR(128)
);

INSERT INTO operational_types (operational_type)
VALUES ('dispatchable_binary_commit'), ('dispatchable_capacity_commit'),
('dispatchable_continuous_commit'), ('dispatchable_no_commit'),
('hydro_conventional'), ('must_run'), ('storage_generic'), ('variable');

-- All projects
-- Probably won't be changing this much
-- TODO: figure out how to handle sensitivities
DROP TABLE IF EXISTS project_operational_chars_default;
CREATE TABLE project_operational_chars_default(
project VARCHAR(64) PRIMARY KEY,
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
FOREIGN KEY (operational_type) REFERENCES operational_types (operational_type)
-- TODO: add checks
);

DROP TABLE IF EXISTS fuels;
CREATE TABLE fuels(
fuel_scenario_id INTEGER,
fuel VARCHAR(32),
fuel_price_per_mmbtu FLOAT,
co2_intensity_tons_per_mmbtu FLOAT,
PRIMARY KEY (fuel_scenario_id, fuel)
);

DROP TABLE IF EXISTS hydro_operational_chars;
CREATE TABLE hydro_operational_chars(
timepoint_scenario_id INTEGER,
hydro_operational_chars_scenario_id INTEGER,
project VARCHAR(64),
horizon INTEGER,
average_power_mwa FLOAT,
min_power_mw FLOAT,
max_power_mw FLOAT,
PRIMARY KEY (timepoint_scenario_id, hydro_operational_chars_scenario_id,
project, horizon),
FOREIGN KEY (timepoint_scenario_id) REFERENCES timepoint_scenarios
(timepoint_scenario_id)
);

-- TODO: add check that load_zone is one of the load zones of the
-- appropriate load_zone_scenario_id (can't be done in sqlite, so do in
-- python or write function when we move to postgresql)
-- Load zones and ancillary service balancing areas
DROP TABLE IF EXISTS project_load_zones;
CREATE TABLE project_load_zones(
load_zone_scenario_id INTEGER,
project_load_zone_scenario_id INTEGER,
project VARCHAR(64),
load_zone VARCHAR(32),
PRIMARY KEY (load_zone_scenario_id, project_load_zone_scenario_id)
FOREIGN KEY (load_zone_scenario_id) REFERENCES load_zone_scenarios
(load_zone_scenario_id)
);

DROP TABLE IF EXISTS project_lf_reserve_up_bas;
CREATE TABLE project_lf_reserve_up_bas(
lf_reserves_up_ba_scenario_id INTEGER,
project_lf_reserves_up_ba_scenario_id INTEGER,
project VARCHAR(64),
lf_reserves_up_ba VARCHAR(32),
PRIMARY KEY (lf_reserves_up_ba_scenario_id,
project_lf_reserves_up_ba_scenario_id)
FOREIGN KEY (lf_reserves_up_ba_scenario_id) REFERENCES
lf_reserves_up_ba_scenarios (lf_reserves_up_ba_scenario_id)
);

DROP TABLE IF EXISTS project_lf_reserve_down_bas;
CREATE TABLE project_lf_reserve_down_bas(
lf_reserves_down_ba_scenario_id INTEGER,
project_lf_reserves_down_ba_scenario_id INTEGER,
project VARCHAR(64),
lf_reserves_down_ba VARCHAR(32),
PRIMARY KEY (lf_reserves_down_ba_scenario_id,
project_lf_reserves_down_ba_scenario_id)
FOREIGN KEY (lf_reserves_down_ba_scenario_id) REFERENCES
lf_reserves_down_ba_scenarios (lf_reserves_down_ba_scenario_id)
);

DROP TABLE IF EXISTS project_lf_reserve_up_bas;
CREATE TABLE project_lf_reserve_up_bas(
regulation_up_ba_scenario_id INTEGER,
project_regulation_up_ba_scenario_id INTEGER,
project VARCHAR(64),
regulation_up_ba VARCHAR(32),
PRIMARY KEY (regulation_up_ba_scenario_id,
project_regulation_up_ba_scenario_id)
FOREIGN KEY (regulation_up_ba_scenario_id) REFERENCES
regulation_up_ba_scenarios (regulation_up_ba_scenario_id)
);

DROP TABLE IF EXISTS project_lf_reserve_down_bas;
CREATE TABLE project_lf_reserve_down_bas(
regulation_down_ba_scenario_id INTEGER,
project_regulation_down_ba_scenario_id INTEGER,
project VARCHAR(64),
regulation_down_ba VARCHAR(32),
PRIMARY KEY (regulation_down_ba_scenario_id,
project_regulation_down_ba_scenario_id)
FOREIGN KEY (regulation_down_ba_scenario_id) REFERENCES
regulation_down_ba_scenarios (regulation_down_ba_scenario_id)
);

DROP TABLE IF EXISTS project_rps_zones;
CREATE TABLE project_rps_zones(
rps_scenario_id INTEGER,
project_rps_scenario_id INTEGER,
project VARCHAR(64),
rps_zone VARCHAR(32),
PRIMARY KEY (rps_scenario_id, project_rps_scenario_id)
FOREIGN KEY (rps_scenario_id) REFERENCES
rps_zone_scenarios (rps_scenario_id)
);


-- Existing projects
DROP TABLE IF EXISTS existing_projects;
CREATE TABLE existing_projects(
existing_project_scenario_id INTEGER,
project VARCHAR(64),
capacity_type VARCHAR(32),
PRIMARY KEY (existing_project_scenario_id, project),
FOREIGN KEY (project) REFERENCES projects_all_defaults(project),
FOREIGN KEY (capacity_type) REFERENCES capacity_types(capacity_type)
);

-- New projects
DROP TABLE IF EXISTS new_projects;
CREATE TABLE new_projects(
new_project_scenario_id INTEGER,
project VARCHAR(64),
capacity_type VARCHAR(32),
PRIMARY KEY (new_project_scenario_id, project),
FOREIGN KEY (project) REFERENCES project_operational_chars_default (project),
FOREIGN KEY (capacity_type) REFERENCES capacity_types (capacity_type),
CHECK (capacity_type = 'new_build_generator' OR capacity_type =
'new_build_storage')
);

-- Project capacity/availability

-- Existing projects
-- TODO: implement check that ALL project from a certain
-- existing_project_scenario_id from the existing_projects table are included
-- here under the same existing_project_scenario_id
DROP TABLE IF EXISTS existing_project_capacity;
CREATE TABLE existing_project_capacity(
existing_project_scenario_id INTEGER,
project VARCHAR(64),
existing_project_capacity_scenario_id INTEGER,
capacity_type VARCHAR(32),
period INTEGER,
existing_capacity_mw FLOAT,
existing_capacity_mwh FLOAT,
annual_fixed_cost_per_mw_year FLOAT,
annual_fixed_cost_per_mwh_year FLOAT,
PRIMARY KEY (existing_project_scenario_id, project, period,
existing_project_capacity_scenario_id),
FOREIGN KEY (project) REFERENCES project_operational_chars_default (project),
FOREIGN KEY (existing_project_scenario_id, project) REFERENCES
existing_projects (existing_project_scenario_id, project),
CHECK (existing_capacity_mwh IS NULL and capacity_type !=
'storage_specified_no_economic_retirement'),
CHECK (existing_capacity_mwh IS NOT NULL and capacity_type =
'storage_specified_no_economic_retirement'),
CHECK (annual_fixed_cost_per_mwh_year IS NULL and capacity_type !=
'storage_specified_no_economic_retirement'),
CHECK (annual_fixed_cost_per_mwh_year IS NOT NULL and capacity_type =
'storage_specified_no_economic_retirement')
);

-- New projects
-- TODO: consolidate new generation and new storage into single table
DROP TABLE IF EXISTS new_project_costs;
CREATE TABLE new_project_costs(
new_project_scenario_id INTEGER,
project VARCHAR(64),
new_project_cost_scenario_id INTEGER,
capacity_type VARCHAR(32),
vintage INTEGER,
annualized_real_cost_per_mw_yr FLOAT,
annualized_real_cost_per_mwh_yr FLOAT,  -- storage only
PRIMARY KEY (new_project_scenario_id, project,
new_project_cost_scenario_id),
FOREIGN KEY (new_project_scenario_id, project) REFERENCES new_projects
(new_project_scenario_id, project),
CHECK (annualized_real_cost_per_mwh_yr IS NULL AND capacity_type !=
'new_build_storage'),
CHECK (annualized_real_cost_per_mwh_yr IS NOT NULL AND capacity_type =
'new_build_storage')
);








--------------------------------
DROP TABLE IF EXISTS projects;
--CREATE TABLE projects(
--project_scenario_id INTEGER,
--project VARCHAR(64),
--capacity_type VARCHAR(32),
--operational_type VARCHAR(32),
--technology VARCHAR(32),
--load_zone VARCHAR(32),
--lf_reserves_up_zone VARCHAR(32),
--lf_reserves_down_zone VARCHAR(32),
--regulation_up_zone VARCHAR(32),
--regulation_down_zone VARCHAR(32),
--rps_zone VARCHAR(32),
--fuel VARCHAR(32),
--minimum_input_mmbtu_per_hr FLOAT,
--inc_heat_rate_mmbtu_per_mwh FLOAT,
--min_stable_level FLOAT,
--unit_size_mw FLOAT,
--startup_cost FLOAT,
--shutdown_cost FLOAT,
--charging_efficiency FLOAT,
--discharging_efficiency FLOAT,
--FOREIGN KEY (project_scenario_id) REFERENCES project_scenarios
--(project_scenario_id)
---- Data checks --
---- Operational types
---- Fuel
--CHECK (operational_type = 'dispatchable_binary_commit' AND fuel IS NOT NULL),
--CHECK (operational_type = 'dispatchable_capacity_commit' AND fuel IS NOT NULL),
--CHECK (operational_type = 'dispatchable_continuous_commit' AND fuel IS NOT
--NULL),
--CHECK (operational_type = 'dispatchable_no_commit' AND fuel IS NOT NULL),
--CHECK (operational_type = 'hydro_conventional' AND fuel IS NULL)
--CHECK (operational_type = 'must_run' AND fuel IS NULL),
--CHECK (operational_type = 'storage_generic' AND fuel IS NULL),
--CHECK (operational_type = 'variable' AND fuel IS NULL),
---- Minimum input
--CHECK (operational_type = 'dispatchable_binary_commit'
--AND minimum_input_mmbtu_per_hr IS NOT NULL),
--CHECK (operational_type = 'dispatchable_capacity_commit'
--AND minimum_input_mmbtu_per_hr IS NOT NULL),
--CHECK (operational_type = 'dispatchable_continuous_commit'
--AND minimum_input_mmbtu_per_hr IS NOT NULL),
--CHECK (operational_type = 'dispatchable_no_commit'
--AND minimum_input_mmbtu_per_hr = 0),
--CHECK (operational_type = 'hydro_conventional'
--AND minimum_input_mmbtu_per_hr IS NULL),
--CHECK (operational_type = 'must_run' AND minimum_input_mmbtu_per_hr IS NULL),
--CHECK (operational_type = 'storage_generic'
--AND minimum_input_mmbtu_per_hr IS NULL),
--CHECK (operational_type = 'variable' AND minimum_input_mmbtu_per_hr IS NULL),
---- Incremental heat rate
--CHECK (operational_type = 'dispatchable_binary_commit'
--AND inc_heat_rate_mmbtu_per_mwh IS NOT NULL),
--CHECK (operational_type = 'dispatchable_capacity_commit'
--AND inc_heat_rate_mmbtu_per_mwh IS NOT NULL),
--CHECK (operational_type = 'dispatchable_continuous_commit'
--AND inc_heat_rate_mmbtu_per_mwh IS NOT NULL),
--CHECK (operational_type = 'dispatchable_no_commit'
--AND inc_heat_rate_mmbtu_per_mwh IS NOT NULL),
--CHECK (operational_type = 'hydro_conventional'
--AND inc_heat_rate_mmbtu_per_mwh IS NULL),
--CHECK (operational_type = 'must_run' AND inc_heat_rate_mmbtu_per_mwh IS NULL),
--CHECK (operational_type = 'storage_generic'
--AND inc_heat_rate_mmbtu_per_mwh IS NULL),
--CHECK (operational_type = 'variable' AND inc_heat_rate_mmbtu_per_mwh IS NULL),
---- Minimum stable level
--CHECK (operational_type = 'dispatchable_binary_commit' AND min_stable_level
-->= 0 AND min_stable_level <= 1),
--CHECK (operational_type = 'dispatchable_capacity_commit' AND min_stable_level
-->= 0 AND min_stable_level <= 1),
--CHECK (operational_type = 'dispatchable_continuous_commit' AND min_stable_level
-->= 0 AND min_stable_level <= 1),
--CHECK (operational_type = 'dispatchable_no_commit' AND min_stable_level IS
--NULL),
--CHECK (operational_type = 'hydro_conventional' AND min_stable_level IS NULL),
--CHECK (operational_type = 'must_run' AND min_stable_level IS NULL),
--CHECK (operational_type = 'storage_generic' AND min_stable_level IS NULL),
--CHECK (operational_type = 'variable' AND min_stable_level IS NULL),
---- Unit size
--CHECK (operational_type = 'dispatchable_binary_commit' AND unit_size_mw IS
--NOT NULL),
--CHECK (operational_type = 'dispatchable_capacity_commit' AND unit_size_mw IS
-- NOT NULL),
--CHECK (operational_type = 'dispatchable_continuous_commit' AND unit_size_mw
--IS NULL),
--CHECK (operational_type = 'dispatchable_no_commit' AND unit_size_mw IS
--NULL),
--CHECK (operational_type = 'hydro_conventional' AND unit_size_mw IS NULL),
--CHECK (operational_type = 'must_run' AND unit_size_mw IS NULL),
--CHECK (operational_type = 'storage_generic' AND unit_size_mw IS NULL),
--CHECK (operational_type = 'variable' AND unit_size_mw IS NULL),
---- Startup cost
--CHECK (operational_type = 'dispatchable_binary_commit'
--AND startup_cost IS NOT NULL),
--CHECK (operational_type = 'dispatchable_capacity_commit'
--AND startup_cost IS NOT NULL),
--CHECK (operational_type = 'dispatchable_continuous_commit'
--AND startup_cost IS NOT NULL),
--CHECK (operational_type = 'dispatchable_no_commit'
--AND startup_cost IS NULL),
--CHECK (operational_type = 'hydro_conventional'
--AND startup_cost IS NULL),
--CHECK (operational_type = 'must_run' AND startup_cost IS NULL),
--CHECK (operational_type = 'storage_generic'
--AND startup_cost IS NULL),
---- Shutdown cost
--CHECK (operational_type = 'dispatchable_binary_commit'
--AND shutdown_cost IS NOT NULL),
--CHECK (operational_type = 'dispatchable_capacity_commit'
--AND shutdown_cost IS NOT NULL),
--CHECK (operational_type = 'dispatchable_continuous_commit'
--AND shutdown_cost IS NOT NULL),
--CHECK (operational_type = 'dispatchable_no_commit'
--AND shutdown_cost IS NULL),
--CHECK (operational_type = 'hydro_conventional'
--AND shutdown_cost IS NULL),
--CHECK (operational_type = 'must_run' AND shutdown_cost IS NULL),
--CHECK (operational_type = 'storage_generic'
--AND shutdown_cost IS NULL),
---- Charging efficiency
--CHECK (operational_type = 'dispatchable_binary_commit'
--AND charging_efficiency IS NULL),
--CHECK (operational_type = 'dispatchable_capacity_commit'
--AND charging_efficiency IS NULL),
--CHECK (operational_type = 'dispatchable_continuous_commit'
--AND charging_efficiency IS NULL),
--CHECK (operational_type = 'dispatchable_no_commit'
--AND charging_efficiency IS NULL),
--CHECK (operational_type = 'hydro_conventional'
--AND charging_efficiency IS NULL),
--CHECK (operational_type = 'must_run' AND charging_efficiency IS NULL),
--CHECK (operational_type = 'storage_generic'
--AND charging_efficiency IS NOT NULL AND charging_efficiency >= 0 AND charging_efficiency <= 1),
---- Discharging efficiency
--CHECK (operational_type = 'dispatchable_binary_commit'
--AND discharging_efficiency IS NULL),
--CHECK (operational_type = 'dispatchable_capacity_commit'
--AND discharging_efficiency IS NULL),
--CHECK (operational_type = 'dispatchable_continuous_commit'
--AND discharging_efficiency IS NULL),
--CHECK (operational_type = 'dispatchable_no_commit'
--AND discharging_efficiency IS NULL),
--CHECK (operational_type = 'hydro_conventional'
--AND discharging_efficiency IS NULL),
--CHECK (operational_type = 'must_run' AND discharging_efficiency IS NULL),
--CHECK (operational_type = 'storage_generic'
--AND discharging_efficiency IS NOT NULL and discharging_efficiency >= 0 AND
--discharging_efficiency <= 1)
--);



-- SYSTEM --
-- Load
DROP TABLE IF EXISTS loads;
CREATE TABLE loads(
load_zone_scenario_id INTEGER,
period_scenario_id INTEGER,
timepoint_scenario_id INTEGER,
load_scenario_id INTEGER,
load_scenario_name INTEGER,
load_zone_id INTEGER,
load_zone VARCHAR(32),
timepoint INTEGER,
load_mw FLOAT,
PRIMARY KEY (load_zone_scenario_id, period_scenario_id, timepoint_scenario_id,
load_scenario_id, load_zone_id),
UNIQUE (load_zone_scenario_id, period_scenario_id, timepoint_scenario_id,
load_scenario_id, load_zone),
UNIQUE (load_zone_scenario_id, period_scenario_id, timepoint_scenario_id,
load_scenario_name, load_zone),
FOREIGN KEY (load_zone_scenario_id) REFERENCES load_zone_scenarios
(load_zone_scenario_id),
FOREIGN KEY (period_scenario_id) REFERENCES period_scenarios
(period_scenario_id),
FOREIGN KEY (timepoint_scenario_id) REFERENCES timepoint_scenarios
(timepoint_scenario_id)
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
FOREIGN KEY (lf_reserves_up_zone_scenario_id) REFERENCES lf_reserves_up_zone_scenarios
(lf_reserves_up_zone_scenario_id),
FOREIGN KEY (period_scenario_id) REFERENCES period_scenarios
(period_scenario_id),
FOREIGN KEY (timepoint_scenario_id) REFERENCES timepoint_scenarios
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
FOREIGN KEY (lf_reserves_down_zone_scenario_id) REFERENCES lf_reserves_down_zone_scenarios
(lf_reserves_down_zone_scenario_id),
FOREIGN KEY (period_scenario_id) REFERENCES period_scenarios
(period_scenario_id),
FOREIGN KEY (timepoint_scenario_id) REFERENCES timepoint_scenarios
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
FOREIGN KEY (regulation_up_zone_scenario_id) REFERENCES regulation_up_zone_scenarios
(regulation_up_zone_scenario_id),
FOREIGN KEY (period_scenario_id) REFERENCES period_scenarios
(period_scenario_id),
FOREIGN KEY (timepoint_scenario_id) REFERENCES timepoint_scenarios
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
FOREIGN KEY (regulation_down_zone_scenario_id) REFERENCES regulation_down_zone_scenarios
(regulation_down_zone_scenario_id),
FOREIGN KEY (period_scenario_id) REFERENCES period_scenarios
(period_scenario_id),
FOREIGN KEY (timepoint_scenario_id) REFERENCES timepoint_scenarios
(timepoint_scenario_id)
);
