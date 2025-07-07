-- Cumulative generator newly build capacity by scenario, project, an period
SELECT scenario_id, scenario_name, project, period, technology, load_zone,
energy_target_zone, instantaneous_penetration_zone, carbon_cap_zone, new_build_mw
FROM results_project_period
JOIN scenarios USING (scenario_id)
;

-- Cumulative storage newly build capacity by scenario, project, and period
SELECT scenario_id, scenario_name, project, period, technology, load_zone,
energy_target_zone, instantaneous_penetration_zone, carbon_cap_zone, new_build_mw, new_build_stor_mwh
FROM results_project_period
JOIN scenarios USING (scenario_id)
;

-- Cumulative retirements by scenario, project and period
select scenario_id, scenario_name, project, period, technology,
local_capacity_zone,
results_project_period.capacity_mw as remaining_capacity_mw,
retired_mw,
results_project_period.capacity_mw + retired_mw as retirable_mw
from results_project_period
left join results_project_period using (scenario_id, project, period)
left join results_project_local_capacity using (scenario_id, project, period)
left join scenarios using (scenario_id)
;

-- Capacity by scenario, project, and period (new and specified projects)
SELECT scenario_id, scenario_name, project, technology, period, capacity_mw
FROM results_project_period
LEFT JOIN scenarios USING (scenario_id)
--WHERE load_zone = 'CAISO'
;

-- Annual generation by scenario, project, and period
SELECT scenario_id, scenario_name, project, technology, period,
sum(power_mw * timepoint_weight * number_of_hours_in_timepoint ) as annual_mwh
FROM results_project_timepoint
WHERE operational_type = 'gen_commit_cap'
JOIN scenarios USING (scenario_id)
--WHERE load_zone = 'CAISO'
--AND (technology = 'Peaker' OR technology = 'CCGT' OR technology = 'CHP' OR
--technology = 'Steam')
GROUP BY scenario_id, project, technology, period
;

-- Annual generation, capacity, and cap_factor by scenario, project, and
-- period (headers assume period is a year)
SELECT scenario_id, scenario_name, project, technology, period, annual_mwh,
capacity_mw, annual_mwh/(8760*capacity_mw) as cap_factor
FROM
(SELECT scenario_id, scenario_name, project, technology, period,
sum(power_mw * timepoint_weight * number_of_hours_in_timepoint ) as annual_mwh
FROM results_project_timepoint
JOIN scenarios USING (scenario_id)
--WHERE load_zone = 'CAISO'
--AND (technology = 'Peaker' OR technology = 'CCGT' OR technology = 'CHP' OR
--technology = 'Steam' or technology = 'Battery' or technology = 'Hydro' or
--technology = 'Pumped_Storage')
GROUP BY scenario_id, project, technology, period) as energy_table
JOIN
(SELECT scenario_id, scenario_name, project, technology, period, capacity_mw
FROM results_project_period
LEFT JOIN scenarios USING (scenario_id)
--WHERE load_zone = 'CAISO'
) as capacity_table
USING (scenario_id, scenario_name, project, technology, period)
;

-- Project operations (commitment, power, and reserves) -- the commitment
-- column here has capacity_commit projects only but you can add any other
-- operational-type-with-commitment table with a UNION in the on-the-fly
-- 'commitment_table' (like the commented-out example with the
-- results_project_dispatch_hybridized table)
select scenario_id, project, period, horizon, timepoint, timepoint_weight,
commitment, power_mw, spin_mw, reg_up_mw, reg_down_mw, lf_up_mw, lf_down_mw,
 frq_resp_mw
from
(select scenario_id, project, period, horizon, timepoint, timepoint_weight, project, power_mw
from results_project_timepoint
-- where project in ()
) as disp_tbl
left join
(select scenario_id, project, period, horizon, timepoint, committed_units as commitment
from results_project_timepoint
where operational_type = 'gen_commit_cap'
-- UNION ALL
-- select scenario_id, project, period, horizon, timepoint, committed_units as commitment
-- from results_project_dispatch_hybridized
) as commitment_table
USING (scenario_id, project, period, horizon, timepoint)
left join
(select scenario_id, project, period, horizon, timepoint,
reserve_provision_mw as spin_mw from results_project_spinning_reserves) as spin_tbl
USING (scenario_id, project, period, horizon, timepoint)
left join
(select scenario_id, project, period, horizon, timepoint,
reserve_provision_mw as reg_up_mw from results_project_regulation_up) as reg_up_tbl
USING (scenario_id, project, period, horizon, timepoint)
left join
(select scenario_id, project, period, horizon, timepoint,
reserve_provision_mw as reg_down_mw from results_project_regulation_down) as reg_down_tbl
USING (scenario_id, project, period, horizon, timepoint)
left join
(select scenario_id, project, period, horizon, timepoint,
reserve_provision_mw as lf_up_mw from results_project_lf_reserves_up) as lf_up_tbl
USING (scenario_id, project, period, horizon, timepoint)
left join
(select scenario_id, project, period, horizon, timepoint,
reserve_provision_mw as lf_down_mw from results_project_lf_reserves_down) as lf_down_tbl
USING (scenario_id, project, period, horizon, timepoint)
left join
(select scenario_id, project, period, horizon, timepoint,
reserve_provision_mw as frq_resp_mw from results_project_frequency_response) as frq_resp_tbl
USING (scenario_id, project, period, horizon, timepoint)
left join
(select scenario_id, project, period, horizon, timepoint,
reserve_provision_mws as iner_mws from results_project_inertia_reserves) as iner_tbl
USING (scenario_id, project, period, horizon, timepoint)
;

-- Frequency response 'cap factor' by scenario, project, and period -- you
-- can replace the frequency response tables with those for any other
-- reserve to get the respective reserve's 'cap factor'
SELECT scenario_id, scenario_name, project, technology, period, annual_mwh,
capacity_mw, annual_mwh/(8760*capacity_mw) as cap_factor
FROM
(SELECT scenario_id, scenario_name, project, technology, period,
sum(reserve_provision_mw * timepoint_weight * number_of_hours_in_timepoint ) as annual_mwh
FROM results_project_frequency_response
JOIN scenarios USING (scenario_id)
--WHERE load_zone = 'CAISO'
--AND (technology = 'Peaker' OR technology = 'CCGT' OR technology = 'CHP'
--OR technology = 'Steam' or technology = 'Battery' or technology = 'Hydro'
--or technology = 'Pumped_Storage')
GROUP BY scenario_id, project, technology, period) as energy_table
JOIN
(SELECT scenario_id, scenario_name, project, technology, period, capacity_mw
FROM results_project_period
LEFT JOIN scenarios USING (scenario_id)
--WHERE load_zone = 'CAISO'
) as capacity_table
USING (scenario_id, scenario_name, project, technology, period)
;

-- Project startups by scenario project, and horizon (headers assume horizon
-- is a day)
-- NOTE: this is a bit of a hack; we should export plant starts directly
select scenario_id, scenario_name, project, period, horizon, timepoint_weight,
technology, daily_startup_cost, startup_cost_per_mw, capacity_mw,
unit_size_mw,
daily_startup_cost/(startup_cost_per_mw * capacity_mw) as daily_plant_starts,
daily_startup_cost/(startup_cost_per_mw * unit_size_mw) as daily_unit_starts,
timepoint_weight * daily_startup_cost/(startup_cost_per_mw * capacity_mw)
as weighted_plant_starts,
timepoint_weight * daily_startup_cost/(startup_cost_per_mw * unit_size_mw)
as weighted_unit_starts
from
(select scenario_id, project, period, horizon, timepoint_weight, technology,
daily_startup_cost
from (
select scenario_id, project, period, horizon, timepoint_weight, technology,
sum(startup_cost) as daily_startup_cost
from results_project_timepoint
-- where load_zone = 'CAISO'
group by scenario_id, project, period, horizon
) as all_daily_startup_cost_tbl
where daily_startup_cost > 0
) as daily_postive_startup_cost_table
join
(select project, startup_cost_per_mw, unit_size_mw
from inputs_project_operational_chars
where project_operational_chars_scenario_id = 1
) as startup_cost_tbl
using (project)
join
(select scenario_id, project, period, capacity_mw
from results_project_period
) as capacity_tbl
using (scenario_id, project, period)
join scenarios using (scenario_id)
;

-- Generation by scenario, load_zone, period, and technology
SELECT scenario_id, scenario_name, load_zone, period, technology,
sum(timepoint_weight*power_mw) as mwh
FROM results_project_timepoint
LEFT JOIN scenarios USING (scenario_id)
GROUP BY scenario_id, load_zone, period, technology
ORDER BY scenario_id, load_zone, period, technology
;

-- Net imports by scenario, load_zone, and period
select scenario_id, load_zone, period,
sum(timepoint_weight * net_imports_mw) as net imports
from results_system_load_zone_timepoint
--where load_zone = 'CAISO'
group by scenario_id, load_zone, period
;


-- System costs by scenario and period -- by source and total
SELECT scenario_id, scenario_name, period,
capacity_cost/1000000 as capacity_cost_millions,
fuel_cost/1000000 as fuel_cost_millions,
variable_om_cost/1000000 as variable_om_cost_millions,
startup_cost/1000000 as startup_cost_millions,
shutdown_cost/1000000 as shutdown_cost_millions,
hurdle_cost/1000000 as hurdle_cost_millions,
hurdle_cost_by_timepoint/1000000 as hurdle_cost_by_timepoint_millions,
capacity_cost/1000000 + fuel_cost/1000000 + variable_om_cost/1000000 + startup_cost/1000000 + shutdown_cost/1000000 + hurdle_cost/1000000 + hurdle_cost_by_timepoint/1000000 as total_cost_millions
FROM
(SELECT scenario_id, period, sum(capacity_cost) AS capacity_cost
FROM  results_project_period
GROUP BY scenario_id, period) AS cap_costs
JOIN
(SELECT scenario_id, period,
sum(fuel_cost * timepoint_weight * number_of_hours_in_timepoint) AS fuel_cost,
sum(variable_om_cost * timepoint_weight * number_of_hours_in_timepoint) AS
variable_om_cost,
sum(startup_cost * timepoint_weight) AS startup_cost,
sum(shutdown_cost * timepoint_weight) AS shutdown_cost
FROM results_project_timepoint
GROUP BY scenario_id, period) AS operational_costs
USING (scenario_id, period)
JOIN
(SELECT scenario_id, period, sum((hurdle_cost_positive_direction+hurdle_cost_negative_direction) * timepoint_weight * number_of_hours_in_timepoint) AS hurdle_cost
FROM
results_transmission_hurdle_costs
GROUP BY scenario_id, period) AS hurdle_costs
USING (scenario_id, period)
JOIN
(SELECT scenario_id, period, sum((hurdle_cost_by_timepoint_positive_direction+hurdle_cost_by_timepoint_negative_direction) * timepoint_weight * number_of_hours_in_timepoint) AS hurdle_cost_by_timepoint
FROM
results_transmission_hurdle_costs_by_timepoint
GROUP BY scenario_id, period) AS hurdle_cost_by_timepoint
USING (scenario_id, period)
JOIN scenarios
USING (scenario_id)
;

-- Carbon emissions by carbon_cap_zone and period -- in-zone, imported, and
-- total + duals
select scenario_id, scenario_name, carbon_cap_zone, period, carbon_cap,
in_zone_project_emissions, import_emissions, total_emissions,
carbon_cap_marginal_cost_per_emission
from results_system_carbon_cap
join scenarios
using (scenario_id)
;

-- RPS
select scenario_id, scenario_name, energy_target_zone, period, energy_target_mwh,
delivered_energy_target_energy_mwh, curtailed_energy_target_energy_mwh, total_energy_target_energy_mwh,
fraction_of_energy_target_met, fraction_of_energy_target_energy_curtailed,
dual
from results_system_energy_target
join scenarios
using (scenario_id)
order by scenario_id
;

-- instantaneous penetration
select scenario_id, scenario_name, instantaneous_penetration_zone, period,
min_instantaneous_penetration_mwh, max_instantaneous_penetration_mwh,
total_instantaneous_penetration_energy_mwh, dual, instantaneous_penetration_marginal_cost_per_mwh
from results_system_period_instantaneous_penetration
join scenarios
using (scenario_id)
order by scenario_id
;

-- PRM
SELECT scenario_id, scenario_name, period, prm_requirement_mw,
elcc_simple_mw, elcc_surface_mw, elcc_total_mw, prm_marginal_cost_per_mw
FROM results_system_prm
JOIN scenarios USING (scenario_id)
ORDER BY scenario_id, period
;

-- Local capacity requirement, provision, and duals
SELECT scenario_id, scenario_name, local_capacity_zone, period,
local_capacity_requirement_mw, local_capacity_provision_mw,
local_capacity_marginal_cost_per_mw
FROM results_system_local_capacity
JOIN scenarios USING (scenario_id)
ORDER BY scenario_id, local_capacity_zone, period
;
