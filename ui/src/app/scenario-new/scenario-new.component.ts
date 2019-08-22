import {Component, NgZone, OnInit} from '@angular/core';
import {Router} from '@angular/router';
import {Location} from '@angular/common';
import {FormControl, FormGroup} from '@angular/forms';
import {ScenarioNewService} from './scenario-new.service';
import {Scenario} from '../scenarios/scenarios.component';
import {ScenariosService} from '../scenarios/scenarios.service';
import {ScenarioDetailService} from '../scenario-detail/scenario-detail.service';
import {ScenarioEditService} from '../scenario-detail/scenario-edit.service';
import {ViewDataService} from '../view-data/view-data.service';
import {SettingsTable} from './scenario-new';
import {StartingValues} from '../scenario-detail/scenario-detail';

const io = ( window as any ).require('socket.io-client');


@Component({
  selector: 'app-scenario-new',
  templateUrl: './scenario-new.component.html',
  styleUrls: ['./scenario-new.component.css']
})


export class ScenarioNewComponent implements OnInit {

  // The final structure we'll iterate over
  scenarioNewStructure: SettingsTable[];

  // If editing scenario, we'll give starting values for settings
  message: string;
  startingValues: StartingValues;

  // We can also start with an empty view and then feed it the values of a
  // given scenario
  allScenarios: Scenario[];
  fromScenarioForm = new FormGroup({
    populateFromScenarioID: new FormControl()
  });

  // Create the form
  newScenarioForm = new FormGroup({
    scenarioName: new FormControl(),
    scenarioDescription: new FormControl(),
    features$fuels: new FormControl(),
    features$transmission: new FormControl(),
    features$transmission_hurdle_rates: new FormControl(),
    features$transmission_sim_flow: new FormControl(),
    features$load_following_up: new FormControl(),
    features$load_following_down: new FormControl(),
    features$regulation_up: new FormControl(),
    features$regulation_down: new FormControl(),
    features$spinning_reserves: new FormControl(),
    features$frequency_response: new FormControl(),
    features$rps: new FormControl(),
    features$carbon_cap: new FormControl(),
    features$track_carbon_imports: new FormControl(),
    features$prm: new FormControl(),
    features$elcc_surface: new FormControl(),
    features$local_capacity: new FormControl(),
    temporal$temporal: new FormControl(),
    load_zones$load_zones: new FormControl(),
    load_zones$project_load_zones: new FormControl(),
    load_zones$transmission_load_zones: new FormControl(),
    system_load$system_load: new FormControl(),
    project_capacity$portfolio: new FormControl(),
    project_capacity$specified_capacity: new FormControl(),
    project_capacity$specified_fixed_cost: new FormControl(),
    project_capacity$new_cost: new FormControl(),
    project_capacity$new_potential: new FormControl(),
    project_capacity$availability: new FormControl(),
    project_opchar$opchar: new FormControl(),
    fuels$fuels: new FormControl(),
    fuels$fuel_prices: new FormControl(),
    transmission_capacity$portfolio: new FormControl(),
    transmission_capacity$specified_capacity: new FormControl(),
    transmission_opchar$opchar: new FormControl(),
    transmission_hurdle_rates$hurdle_rates: new FormControl(),
    transmission_sim_flow_limits$limits: new FormControl(),
    transmission_sim_flow_limits$groups: new FormControl(),
    load_following_up$bas: new FormControl(),
    load_following_up$req: new FormControl(),
    load_following_up$projects: new FormControl(),
    load_following_down$bas: new FormControl(),
    load_following_down$req: new FormControl(),
    load_following_down$projects: new FormControl(),
    regulation_up$bas: new FormControl(),
    regulation_up$req: new FormControl(),
    regulation_up$projects: new FormControl(),
    regulation_down$bas: new FormControl(),
    regulation_down$req: new FormControl(),
    regulation_down$projects: new FormControl(),
    spinning_reserves$bas: new FormControl(),
    spinning_reserves$req: new FormControl(),
    spinning_reserves$projects: new FormControl(),
    frequency_response$bas: new FormControl(),
    frequency_response$req: new FormControl(),
    frequency_response$projects: new FormControl(),
    rps$bas: new FormControl(),
    rps$req: new FormControl(),
    rps$projects: new FormControl(),
    carbon_cap$bas: new FormControl(),
    carbon_cap$req: new FormControl(),
    carbon_cap$projects: new FormControl(),
    carbon_cap$transmission: new FormControl(),
    prm$bas: new FormControl(),
    prm$req: new FormControl(),
    prm$projects: new FormControl(),
    prm$project_elcc: new FormControl(),
    prm$elcc: new FormControl(),
    prm$energy_only: new FormControl(),
    local_capacity$bas: new FormControl(),
    local_capacity$req: new FormControl(),
    local_capacity$projects: new FormControl(),
    local_capacity$project_chars: new FormControl(),
    tuning$tuning: new FormControl()
    });

  constructor(private scenarioNewService: ScenarioNewService,
              private scenariosService: ScenariosService,
              private scenarioDetailService: ScenarioDetailService,
              private scenarioEditService: ScenarioEditService,
              private viewDataService: ViewDataService,
              private router: Router,
              private zone: NgZone,
              private location: Location) {
  }

  ngOnInit() {
    // Get the scenarios list for the 'populate from scenario' functionality
    this.getScenarios();

    // Set the starting form state (if editing or copying a scenario)
    this.setStartingFormStateFromEditScenario();

    // Make the scenario-new view
    this.getScenarioNewAPI();
  }

  getScenarioNewAPI(): void {
    // Get the settings
    this.scenarioNewService.getScenarioNewAPI()
      .subscribe(
        scenarioSetting => {
          this.scenarioNewStructure = scenarioSetting;
        }
      );
  }

  // Get all scenarios
  getScenarios(): void {
      this.scenariosService.getScenarios()
        .subscribe(scenarios => { this.allScenarios = scenarios; } );
    }
  // Set the starting values directly based on a user-selected scenario name
  getStartingValuesFromScenario(): void {
    // Get from form
    const scenarioID = this.fromScenarioForm.value.populateFromScenarioID;
    console.log(scenarioID);
    this.scenarioDetailService.getScenarioDetailAPI(scenarioID)
      .subscribe(
        scenarioDetail => {
            this.startingValues = scenarioDetail.editScenarioValues;
            this.newScenarioForm.controls.scenarioName.setValue(
              this.startingValues.scenario_name, {onlySelf: true}
            );
            this.newScenarioForm.controls.features$fuels.setValue(
              this.startingValues.features$fuels, {onlySelf: true}
            );
            this.newScenarioForm.controls.features$transmission.setValue(
              this.startingValues.features$transmission, {onlySelf: true}
            );
            this.newScenarioForm.controls.features$transmission_hurdle_rates.setValue(
              this.startingValues.features$transmission_hurdle_rates, {onlySelf: true}
            );
            this.newScenarioForm.controls.features$transmission_sim_flow.setValue(
              this.startingValues.features$transmission_sim_flow, {onlySelf: true}
            );
            this.newScenarioForm.controls.features$load_following_up.setValue(
              this.startingValues.features$load_following_up, {onlySelf: true}
            );
            this.newScenarioForm.controls.features$load_following_down.setValue(
              this.startingValues.features$load_following_down, {onlySelf: true}
            );
            this.newScenarioForm.controls.features$regulation_up.setValue(
              this.startingValues.features$regulation_up, {onlySelf: true}
            );
            this.newScenarioForm.controls.features$regulation_down.setValue(
              this.startingValues.features$regulation_down, {onlySelf: true}
            );
            this.newScenarioForm.controls.features$spinning_reserves.setValue(
              this.startingValues.features$spinning_reserves, {onlySelf: true}
            );
            this.newScenarioForm.controls.features$frequency_response.setValue(
              this.startingValues.features$frequency_response, {onlySelf: true}
            );
            this.newScenarioForm.controls.features$rps.setValue(
              this.startingValues.features$rps, {onlySelf: true}
            );
            this.newScenarioForm.controls.features$carbon_cap.setValue(
              this.startingValues.features$carbon_cap, {onlySelf: true}
            );
            this.newScenarioForm.controls.features$track_carbon_imports.setValue(
              this.startingValues.features$track_carbon_imports, {onlySelf: true}
            );
            this.newScenarioForm.controls.features$prm.setValue(
              this.startingValues.features$prm, {onlySelf: true}
            );
            this.newScenarioForm.controls.features$elcc_surface.setValue(
              this.startingValues.features$elcc_surface, {onlySelf: true}
            );
            this.newScenarioForm.controls.features$local_capacity.setValue(
              this.startingValues.features$local_capacity, {onlySelf: true}
            );
            this.newScenarioForm.controls.temporal$temporal.setValue(
              this.startingValues.temporal$temporal, {onlySelf: true}
            );
            this.newScenarioForm.controls.load_zones$load_zones.setValue(
              this.startingValues.load_zones$load_zones, {onlySelf: true}
            );
            this.newScenarioForm.controls.load_zones$project_load_zones.setValue(
              this.startingValues.load_zones$project_load_zones, {onlySelf: true}
            );
            this.newScenarioForm.controls.load_zones$transmission_load_zones.setValue(
              this.startingValues.load_zones$transmission_load_zones, {onlySelf: true}
            );
            this.newScenarioForm.controls.system_load$system_load.setValue(
              this.startingValues.system_load$system_load, {onlySelf: true}
            );
            this.newScenarioForm.controls.project_capacity$portfolio.setValue(
              this.startingValues.project_capacity$portfolio, {onlySelf: true}
            );
            this.newScenarioForm.controls.project_capacity$specified_capacity.setValue(
              this.startingValues.project_capacity$specified_capacity, {onlySelf: true}
            );
            this.newScenarioForm.controls.project_capacity$specified_fixed_cost.setValue(
              this.startingValues.project_capacity$specified_fixed_cost, {onlySelf: true}
            );
            this.newScenarioForm.controls.project_capacity$new_cost.setValue(
              this.startingValues.project_capacity$new_cost, {onlySelf: true}
            );
            this.newScenarioForm.controls.project_capacity$new_potential.setValue(
              this.startingValues.project_capacity$new_potential, {onlySelf: true}
            );
            this.newScenarioForm.controls.project_capacity$availability.setValue(
              this.startingValues.project_capacity$availability, {onlySelf: true}
            );
            this.newScenarioForm.controls.project_opchar$opchar.setValue(
              this.startingValues.project_opchar$opchar, {onlySelf: true}
            );
            this.newScenarioForm.controls.fuels$fuels.setValue(
              this.startingValues.fuels$fuels, {onlySelf: true}
            );
            this.newScenarioForm.controls.fuels$fuel_prices.setValue(
              this.startingValues.fuels$fuel_prices, {onlySelf: true}
            );
            this.newScenarioForm.controls.transmission_capacity$portfolio.setValue(
              this.startingValues.transmission_capacity$portfolio, {onlySelf: true}
            );
            this.newScenarioForm.controls.transmission_capacity$specified_capacity.setValue(
              this.startingValues.transmission_capacity$specified_capacity, {onlySelf: true}
            );
            this.newScenarioForm.controls.transmission_opchar$opchar.setValue(
              this.startingValues.transmission_opchar$opchar, {onlySelf: true}
            );
            this.newScenarioForm.controls.transmission_hurdle_rates$hurdle_rates.setValue(
              this.startingValues.transmission_hurdle_rates$hurdle_rates, {onlySelf: true}
            );
            this.newScenarioForm.controls.transmission_sim_flow_limits$limits.setValue(
              this.startingValues.transmission_sim_flow_limits$limits, {onlySelf: true}
            );
            this.newScenarioForm.controls.transmission_sim_flow_limits$groups.setValue(
              this.startingValues.transmission_sim_flow_limits$groups, {onlySelf: true}
            );
            this.newScenarioForm.controls.load_following_up$bas.setValue(
              this.startingValues.load_following_up$bas, {onlySelf: true}
            );
            this.newScenarioForm.controls.load_following_up$req.setValue(
              this.startingValues.load_following_up$req, {onlySelf: true}
            );
            this.newScenarioForm.controls.load_following_up$projects.setValue(
              this.startingValues.load_following_up$projects, {onlySelf: true}
            );
            this.newScenarioForm.controls.load_following_down$bas.setValue(
              this.startingValues.load_following_down$bas, {onlySelf: true}
            );
            this.newScenarioForm.controls.load_following_down$req.setValue(
              this.startingValues.load_following_down$req, {onlySelf: true}
            );
            this.newScenarioForm.controls.load_following_down$projects.setValue(
              this.startingValues.load_following_down$projects, {onlySelf: true}
            );
            this.newScenarioForm.controls.regulation_up$bas.setValue(
              this.startingValues.regulation_up$bas, {onlySelf: true}
            );
            this.newScenarioForm.controls.regulation_up$req.setValue(
              this.startingValues.regulation_up$req, {onlySelf: true}
            );
            this.newScenarioForm.controls.regulation_up$projects.setValue(
              this.startingValues.regulation_up$projects, {onlySelf: true}
            );
            this.newScenarioForm.controls.regulation_down$bas.setValue(
              this.startingValues.regulation_down$bas, {onlySelf: true}
            );
            this.newScenarioForm.controls.regulation_down$req.setValue(
              this.startingValues.regulation_down$req, {onlySelf: true}
            );
            this.newScenarioForm.controls.regulation_down$projects.setValue(
              this.startingValues.regulation_down$projects, {onlySelf: true}
            );
            this.newScenarioForm.controls.spinning_reserves$bas.setValue(
              this.startingValues.spinning_reserves$bas, {onlySelf: true}
            );
            this.newScenarioForm.controls.spinning_reserves$req.setValue(
              this.startingValues.spinning_reserves$req, {onlySelf: true}
            );
            this.newScenarioForm.controls.spinning_reserves$projects.setValue(
              this.startingValues.spinning_reserves$projects, {onlySelf: true}
            );
            this.newScenarioForm.controls.frequency_response$bas.setValue(
              this.startingValues.frequency_response$bas, {onlySelf: true}
            );
            this.newScenarioForm.controls.frequency_response$req.setValue(
              this.startingValues.frequency_response$req, {onlySelf: true}
            );
            this.newScenarioForm.controls.frequency_response$projects.setValue(
              this.startingValues.frequency_response$projects, {onlySelf: true}
            );
            this.newScenarioForm.controls.rps$bas.setValue(
              this.startingValues.rps$bas, {onlySelf: true}
            );
            this.newScenarioForm.controls.rps$req.setValue(
              this.startingValues.rps$req, {onlySelf: true}
            );
            this.newScenarioForm.controls.rps$projects.setValue(
              this.startingValues.rps$projects, {onlySelf: true}
            );
            this.newScenarioForm.controls.carbon_cap$bas.setValue(
              this.startingValues.carbon_cap$bas, {onlySelf: true}
            );
            this.newScenarioForm.controls.carbon_cap$req.setValue(
              this.startingValues.carbon_cap$req, {onlySelf: true}
            );
            this.newScenarioForm.controls.carbon_cap$projects.setValue(
              this.startingValues.carbon_cap$projects, {onlySelf: true}
            );
            this.newScenarioForm.controls.carbon_cap$transmission.setValue(
              this.startingValues.carbon_cap$transmission, {onlySelf: true}
            );
            this.newScenarioForm.controls.prm$bas.setValue(
              this.startingValues.prm$bas, {onlySelf: true}
            );
            this.newScenarioForm.controls.prm$req.setValue(
              this.startingValues.prm$req, {onlySelf: true}
            );
            this.newScenarioForm.controls.prm$projects.setValue(
              this.startingValues.prm$projects, {onlySelf: true}
            );
            this.newScenarioForm.controls.prm$project_elcc.setValue(
              this.startingValues.prm$project_elcc, {onlySelf: true}
            );
            this.newScenarioForm.controls.prm$elcc.setValue(
              this.startingValues.prm$elcc, {onlySelf: true}
            );
            this.newScenarioForm.controls.prm$energy_only.setValue(
              this.startingValues.prm$energy_only, {onlySelf: true}
            );
            this.newScenarioForm.controls.local_capacity$bas.setValue(
              this.startingValues.local_capacity$bas, {onlySelf: true}
            );
            this.newScenarioForm.controls.local_capacity$req.setValue(
              this.startingValues.local_capacity$req, {onlySelf: true}
            );
            this.newScenarioForm.controls.local_capacity$projects.setValue(
              this.startingValues.local_capacity$projects, {onlySelf: true}
            );
            this.newScenarioForm.controls.local_capacity$project_chars.setValue(
              this.startingValues.local_capacity$project_chars, {onlySelf: true}
            );
            this.newScenarioForm.controls.tuning$tuning.setValue(
              this.startingValues.tuning$tuning, {onlySelf: true}
            );
        }
      );
  }

  // Set the starting values based on the scenario that the user has
  // requested to edit (on navigate from scenario-detail to scenario-new)
  setStartingFormStateFromEditScenario(): void {
    this.scenarioEditService.startingValuesSubject
      .subscribe((startingValues: StartingValues) => {
        this.startingValues = startingValues;

        this.newScenarioForm.controls.scenarioName.setValue(
          this.startingValues.scenario_name, {onlySelf: true}
        );
        this.newScenarioForm.controls.features$fuels.setValue(
          this.startingValues.features$fuels, {onlySelf: true}
        );
        this.newScenarioForm.controls.features$transmission.setValue(
          this.startingValues.features$transmission, {onlySelf: true}
        );
        this.newScenarioForm.controls.features$transmission_hurdle_rates.setValue(
          this.startingValues.features$transmission_hurdle_rates, {onlySelf: true}
        );
        this.newScenarioForm.controls.features$transmission_sim_flow.setValue(
          this.startingValues.features$transmission_sim_flow, {onlySelf: true}
        );
        this.newScenarioForm.controls.features$load_following_up.setValue(
          this.startingValues.features$load_following_up, {onlySelf: true}
        );
        this.newScenarioForm.controls.features$load_following_down.setValue(
          this.startingValues.features$load_following_down, {onlySelf: true}
        );
        this.newScenarioForm.controls.features$regulation_up.setValue(
          this.startingValues.features$regulation_up, {onlySelf: true}
        );
        this.newScenarioForm.controls.features$regulation_down.setValue(
          this.startingValues.features$regulation_down, {onlySelf: true}
        );
        this.newScenarioForm.controls.features$spinning_reserves.setValue(
          this.startingValues.features$spinning_reserves, {onlySelf: true}
        );
        this.newScenarioForm.controls.features$frequency_response.setValue(
          this.startingValues.features$frequency_response, {onlySelf: true}
        );
        this.newScenarioForm.controls.features$rps.setValue(
          this.startingValues.features$rps, {onlySelf: true}
        );
        this.newScenarioForm.controls.features$carbon_cap.setValue(
          this.startingValues.features$carbon_cap, {onlySelf: true}
        );
        this.newScenarioForm.controls.features$track_carbon_imports.setValue(
          this.startingValues.features$track_carbon_imports, {onlySelf: true}
        );
        this.newScenarioForm.controls.features$prm.setValue(
          this.startingValues.features$prm, {onlySelf: true}
        );
        this.newScenarioForm.controls.features$elcc_surface.setValue(
          this.startingValues.features$elcc_surface, {onlySelf: true}
        );
        this.newScenarioForm.controls.features$local_capacity.setValue(
          this.startingValues.features$local_capacity, {onlySelf: true}
        );
        this.newScenarioForm.controls.temporal$temporal.setValue(
          this.startingValues.temporal$temporal, {onlySelf: true}
        );
        this.newScenarioForm.controls.load_zones$load_zones.setValue(
          this.startingValues.load_zones$load_zones, {onlySelf: true}
        );
        this.newScenarioForm.controls.load_zones$project_load_zones.setValue(
          this.startingValues.load_zones$project_load_zones, {onlySelf: true}
        );
        this.newScenarioForm.controls.load_zones$transmission_load_zones.setValue(
          this.startingValues.load_zones$transmission_load_zones, {onlySelf: true}
        );
        this.newScenarioForm.controls.system_load$system_load.setValue(
          this.startingValues.system_load$system_load, {onlySelf: true}
        );
        this.newScenarioForm.controls.project_capacity$portfolio.setValue(
          this.startingValues.project_capacity$portfolio, {onlySelf: true}
        );
        this.newScenarioForm.controls.project_capacity$specified_capacity.setValue(
          this.startingValues.project_capacity$specified_capacity, {onlySelf: true}
        );
        this.newScenarioForm.controls.project_capacity$specified_fixed_cost.setValue(
          this.startingValues.project_capacity$specified_fixed_cost, {onlySelf: true}
        );
        this.newScenarioForm.controls.project_capacity$new_cost.setValue(
          this.startingValues.project_capacity$new_cost, {onlySelf: true}
        );
        this.newScenarioForm.controls.project_capacity$new_potential.setValue(
          this.startingValues.project_capacity$new_potential, {onlySelf: true}
        );
        this.newScenarioForm.controls.project_capacity$availability.setValue(
          this.startingValues.project_capacity$availability, {onlySelf: true}
        );
        this.newScenarioForm.controls.project_opchar$opchar.setValue(
          this.startingValues.project_opchar$opchar, {onlySelf: true}
        );
        this.newScenarioForm.controls.fuels$fuels.setValue(
          this.startingValues.fuels$fuels, {onlySelf: true}
        );
        this.newScenarioForm.controls.fuels$fuel_prices.setValue(
          this.startingValues.fuels$fuel_prices, {onlySelf: true}
        );
        this.newScenarioForm.controls.transmission_capacity$portfolio.setValue(
          this.startingValues.transmission_capacity$portfolio, {onlySelf: true}
        );
        this.newScenarioForm.controls.transmission_capacity$specified_capacity.setValue(
          this.startingValues.transmission_capacity$specified_capacity, {onlySelf: true}
        );
        this.newScenarioForm.controls.transmission_opchar$opchar.setValue(
          this.startingValues.transmission_opchar$opchar, {onlySelf: true}
        );
        this.newScenarioForm.controls.transmission_hurdle_rates$hurdle_rates.setValue(
          this.startingValues.transmission_hurdle_rates$hurdle_rates, {onlySelf: true}
        );
        this.newScenarioForm.controls.transmission_sim_flow_limits$limits.setValue(
          this.startingValues.transmission_sim_flow_limits$limits, {onlySelf: true}
        );
        this.newScenarioForm.controls.transmission_sim_flow_limits$groups.setValue(
          this.startingValues.transmission_sim_flow_limits$groups, {onlySelf: true}
        );
        this.newScenarioForm.controls.load_following_up$bas.setValue(
          this.startingValues.load_following_up$bas, {onlySelf: true}
        );
        this.newScenarioForm.controls.load_following_up$req.setValue(
          this.startingValues.load_following_up$req, {onlySelf: true}
        );
        this.newScenarioForm.controls.load_following_up$projects.setValue(
          this.startingValues.load_following_up$projects, {onlySelf: true}
        );
        this.newScenarioForm.controls.load_following_down$bas.setValue(
          this.startingValues.load_following_down$bas, {onlySelf: true}
        );
        this.newScenarioForm.controls.load_following_down$req.setValue(
          this.startingValues.load_following_down$req, {onlySelf: true}
        );
        this.newScenarioForm.controls.load_following_down$projects.setValue(
          this.startingValues.load_following_down$projects, {onlySelf: true}
        );
        this.newScenarioForm.controls.regulation_up$bas.setValue(
          this.startingValues.regulation_up$bas, {onlySelf: true}
        );
        this.newScenarioForm.controls.regulation_up$req.setValue(
          this.startingValues.regulation_up$req, {onlySelf: true}
        );
        this.newScenarioForm.controls.regulation_up$projects.setValue(
          this.startingValues.regulation_up$projects, {onlySelf: true}
        );
        this.newScenarioForm.controls.regulation_down$bas.setValue(
          this.startingValues.regulation_down$bas, {onlySelf: true}
        );
        this.newScenarioForm.controls.regulation_down$req.setValue(
          this.startingValues.regulation_down$req, {onlySelf: true}
        );
        this.newScenarioForm.controls.regulation_down$projects.setValue(
          this.startingValues.regulation_down$projects, {onlySelf: true}
        );
        this.newScenarioForm.controls.spinning_reserves$bas.setValue(
          this.startingValues.spinning_reserves$bas, {onlySelf: true}
        );
        this.newScenarioForm.controls.spinning_reserves$req.setValue(
          this.startingValues.spinning_reserves$req, {onlySelf: true}
        );
        this.newScenarioForm.controls.spinning_reserves$projects.setValue(
          this.startingValues.spinning_reserves$projects, {onlySelf: true}
        );
        this.newScenarioForm.controls.frequency_response$bas.setValue(
          this.startingValues.frequency_response$bas, {onlySelf: true}
        );
        this.newScenarioForm.controls.frequency_response$req.setValue(
          this.startingValues.frequency_response$req, {onlySelf: true}
        );
        this.newScenarioForm.controls.frequency_response$projects.setValue(
          this.startingValues.frequency_response$projects, {onlySelf: true}
        );
        this.newScenarioForm.controls.rps$bas.setValue(
          this.startingValues.rps$bas, {onlySelf: true}
        );
        this.newScenarioForm.controls.rps$req.setValue(
          this.startingValues.rps$req, {onlySelf: true}
        );
        this.newScenarioForm.controls.rps$projects.setValue(
          this.startingValues.rps$projects, {onlySelf: true}
        );
        this.newScenarioForm.controls.carbon_cap$bas.setValue(
          this.startingValues.carbon_cap$bas, {onlySelf: true}
        );
        this.newScenarioForm.controls.carbon_cap$req.setValue(
          this.startingValues.carbon_cap$req, {onlySelf: true}
        );
        this.newScenarioForm.controls.carbon_cap$projects.setValue(
          this.startingValues.carbon_cap$projects, {onlySelf: true}
        );
        this.newScenarioForm.controls.carbon_cap$transmission.setValue(
          this.startingValues.carbon_cap$transmission, {onlySelf: true}
        );
        this.newScenarioForm.controls.prm$bas.setValue(
          this.startingValues.prm$bas, {onlySelf: true}
        );
        this.newScenarioForm.controls.prm$req.setValue(
          this.startingValues.prm$req, {onlySelf: true}
        );
        this.newScenarioForm.controls.prm$projects.setValue(
          this.startingValues.prm$projects, {onlySelf: true}
        );
        this.newScenarioForm.controls.prm$project_elcc.setValue(
          this.startingValues.prm$project_elcc, {onlySelf: true}
        );
        this.newScenarioForm.controls.prm$elcc.setValue(
          this.startingValues.prm$elcc, {onlySelf: true}
        );
        this.newScenarioForm.controls.prm$energy_only.setValue(
          this.startingValues.prm$energy_only, {onlySelf: true}
        );
        this.newScenarioForm.controls.local_capacity$bas.setValue(
          this.startingValues.local_capacity$bas, {onlySelf: true}
        );
        this.newScenarioForm.controls.local_capacity$req.setValue(
          this.startingValues.local_capacity$req, {onlySelf: true}
        );
        this.newScenarioForm.controls.local_capacity$projects.setValue(
          this.startingValues.local_capacity$projects, {onlySelf: true}
        );
        this.newScenarioForm.controls.local_capacity$project_chars.setValue(
          this.startingValues.local_capacity$project_chars, {onlySelf: true}
        );
        this.newScenarioForm.controls.tuning$tuning.setValue(
          this.startingValues.tuning$tuning, {onlySelf: true}
        );
      });
  }

  viewData(tableNameInDB, rowNameInDB): void {
    const dataToView = `${tableNameInDB}-${rowNameInDB}`;
    // Send the table name to the view-data service that view-data component
    // uses to determine which tables to show
    this.viewDataService.changeDataToView(dataToView);
    console.log('Sending data to view, ', dataToView);
    // Switch to the new scenario view
    this.router.navigate(['/view-data']);
  }

  saveNewScenario() {
    const socket = io.connect('http://127.0.0.1:8080/');
    socket.on('connect', () => {
        console.log(`Connection established: ${socket.connected}`);
    });
    socket.emit('add_new_scenario', this.newScenarioForm.value);

    socket.on('return_new_scenario_id', (newScenarioID) => {
      console.log('New scenario ID is ', newScenarioID);
      this.zone.run(
        () => {
          this.router.navigate(['/scenario/', newScenarioID]);
        }
      );
    });

    // Change the edit scenario starting values to null when navigating away
    // TODO: set up an event when this happens
    this.scenarioEditService.changeStartingScenario(emptyStartingValues);
  }

  goBack(): void {
    // Change the edit scenario starting values to null when navigating away
    // TODO: set up an event when this happens
    // TODO: use .reset instead?
    this.scenarioEditService.changeStartingScenario(emptyStartingValues);
    this.location.back();
  }

}

// TODO: need to set on navigation away from this page, not just button clicks
export const emptyStartingValues = {
  // tslint:disable:variable-name
  scenario_id: null,
  scenario_name: null,
  features$fuels: false,
  features$transmission: false,
  features$transmission_hurdle_rates: false,
  features$transmission_sim_flow: false,
  features$load_following_up: false,
  features$load_following_down: false,
  features$regulation_up: false,
  features$regulation_down: false,
  features$spinning_reserves: false,
  features$frequency_response: false,
  features$rps: false,
  features$carbon_cap: false,
  features$track_carbon_imports: false,
  features$prm: false,
  features$elcc_surface: false,
  features$local_capacity: false,
  temporal$temporal: null,
  load_zones$load_zones: null,
  load_zones$project_load_zones: null,
  load_zones$transmission_load_zones: null,
  system_load$system_load: null,
  project_capacity$portfolio: null,
  project_capacity$specified_capacity: null,
  project_capacity$specified_fixed_cost: null,
  project_capacity$new_cost: null,
  project_capacity$new_potential: null,
  project_capacity$availability: null,
  project_opchar$opchar: null,
  fuels$fuels: null,
  fuels$fuel_prices: null,
  transmission_capacity$portfolio: null,
  transmission_capacity$specified_capacity: null,
  transmission_opchar$opchar: null,
  transmission_hurdle_rates$hurdle_rates: null,
  transmission_sim_flow_limits$limits: null,
  transmission_sim_flow_limits$groups: null,
  load_following_up$bas: null,
  load_following_up$req: null,
  load_following_up$projects: null,
  load_following_down$bas: null,
  load_following_down$req: null,
  load_following_down$projects: null,
  regulation_up$bas: null,
  regulation_up$req: null,
  regulation_up$projects: null,
  regulation_down$bas: null,
  regulation_down$req: null,
  regulation_down$projects: null,
  spinning_reserves$bas: null,
  spinning_reserves$req: null,
  spinning_reserves$projects: null,
  frequency_response$bas: null,
  frequency_response$req: null,
  frequency_response$projects: null,
  rps$bas: null,
  rps$req: null,
  rps$projects: null,
  carbon_cap$bas: null,
  carbon_cap$req: null,
  carbon_cap$projects: null,
  carbon_cap$transmission: null,
  prm$bas: null,
  prm$req: null,
  prm$projects: null,
  prm$project_elcc: null,
  prm$elcc: null,
  prm$energy_only: null,
  local_capacity$bas: null,
  local_capacity$req: null,
  local_capacity$projects: null,
  local_capacity$project_chars: null,
  tuning$tuning: null
};
