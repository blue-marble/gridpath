export class ScenarioDetailAPI {
  scenarioName: string;
  editScenarioValues: StartingValues;
  scenarioDetailTables: ScenarioDetailTable[];
}

export class ScenarioDetailTable {
  scenarioName: string;
  uiTableNameInDB: string;
  scenarioDetailTableCaption: string;
  scenarioDetailTableRows: ScenarioDetailTableRow[];
}

export class ScenarioDetailTableRow {
  uiRowNameInDB: string;
  rowCaption: string;
  rowValue: string;
}

export class StartingValues {
  // tslint:disable:variable-name
  scenario_id: number;
  scenario_name: string;
  feature_fuels: string;
  feature_transmission: string;
  feature_transmission_hurdle_rates: string;
  feature_simultaneous_flow_limits: string;
  feature_load_following_up: string;
  feature_load_following_down: string;
  feature_regulation_up: string;
  feature_regulation_down: string;
  feature_frequency_response: string;
  feature_spinning_reserves: string;
  feature_rps: string;
  feature_carbon_cap: string;
  feature_track_carbon_imports: string;
  feature_prm: string;
  feature_elcc_surface: string;
  feature_local_capacity: string;
  temporal: string;
  geography_load_zones: string;
  geography_lf_up_bas: string;
  geography_lf_down_bas: string;
  geography_reg_up_bas: string;
  geography_reg_down_bas: string;
  geography_spin_bas: string;
  geography_freq_resp_bas: string;
  geography_rps_areas: string;
  carbon_cap_areas: string;
  prm_areas: string;
  local_capacity_areas: string;
  project_portfolio: string;
  project_operating_chars: string;
  project_availability: string;
  project_fuels: string;
  fuel_prices: string;
  project_load_zones: string;
  project_lf_up_bas: string;
  project_lf_down_bas: string;
  project_reg_up_bas: string;
  project_reg_down_bas: string;
  project_spin_bas: string;
  project_freq_resp_bas: string;
  project_rps_areas: string;
  project_carbon_cap_areas: string;
  project_prm_areas: string;
  project_elcc_chars: string;
  project_prm_energy_only: string;
  project_local_capacity_areas: string;
  project_local_capacity_chars: string;
  project_existing_capacity: string;
  project_existing_fixed_cost: string;
  project_new_cost: string;
  project_new_potential: string;
  transmission_portfolio: string;
  transmission_load_zones: string;
  transmission_existing_capacity: string;
  transmission_operational_chars: string;
  transmission_hurdle_rates: string;
  transmission_carbon_cap_zones: string;
  transmission_simultaneous_flow_limits: string;
  transmission_simultaneous_flow_limit_line_groups: string;
  load_profile: string;
  load_following_reserves_up_profile: string;
  load_following_reserves_down_profile: string;
  regulation_up_profile: string;
  regulation_down_profile: string;
  spinning_reserves_profile: string;
  frequency_response_profile: string;
  rps_target: string;
  carbon_cap: string;
  prm_requirement: string;
  elcc_surface: string;
  local_capacity_requirement: string;
  tuning: string;
}
