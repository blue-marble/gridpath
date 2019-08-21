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
  features$fuels: boolean;
  features$transmission: boolean;
  features$transmission_hurdle_rates: boolean;
  features$transmission_sim_flow: boolean;
  features$load_following_up: boolean;
  features$load_following_down: boolean;
  features$regulation_up: boolean;
  features$regulation_down: boolean;
  features$spinning_reserves: boolean;
  features$frequency_response: boolean;
  features$rps: boolean;
  features$carbon_cap: boolean;
  features$track_carbon_imports: boolean;
  features$prm: boolean;
  features$elcc_surface: boolean;
  features$local_capacity: boolean;
  temporal$temporal: string;
  load_zones$load_zones: string;
  load_zones$project_load_zones: string;
  load_zones$transmission_load_zones: string;
  system_load$system_load: string;
  project_capacity$portfolio: string;
  project_capacity$specified_capacity: string;
  project_capacity$specified_fixed_cost: string;
  project_capacity$new_cost: string;
  project_capacity$new_potential: string;
  project_capacity$availability: string;
  project_opchar$opchar: string;
  fuels$fuels: string;
  fuels$fuel_prices: string;
  transmission_capacity$portfolio: string;
  transmission_capacity$specified_capacity: string;
  transmission_opchar$opchar: string;
  transmission_hurdle_rates$hurdle_rates: string;
  transmission_sim_flow_limits$limits: string;
  transmission_sim_flow_limits$groups: string;
  load_following_up$bas: string;
  load_following_up$req: string;
  load_following_up$projects: string;
  load_following_down$bas: string;
  load_following_down$req: string;
  load_following_down$projects: string;
  regulation_up$bas: string;
  regulation_up$req: string;
  regulation_up$projects: string;
  regulation_down$bas: string;
  regulation_down$req: string;
  regulation_down$projects: string;
  spinning_reserves$bas: string;
  spinning_reserves$req: string;
  spinning_reserves$projects: string;
  frequency_response$bas: string;
  frequency_response$req: string;
  frequency_response$projects: string;
  rps$bas: string;
  rps$req: string;
  rps$projects: string;
  carbon_cap$bas: string;
  carbon_cap$req: string;
  carbon_cap$projects: string;
  carbon_cap$transmission: string;
  prm$bas: string;
  prm$req: string;
  prm$projects: string;
  prm$project_elcc: string;
  prm$elcc: string;
  prm$energy_only: string;
  local_capacity$bas: string;
  local_capacity$req: string;
  local_capacity$projects: string;
  local_capacity$project_chars: string;
  tuning$tuning: string;
}
