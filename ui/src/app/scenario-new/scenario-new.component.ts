import {Component, NgZone, OnInit} from '@angular/core';
import {Router, ActivatedRoute, NavigationExtras} from '@angular/router';
import {Location} from '@angular/common';
import {FormControl, FormGroup} from '@angular/forms';
import {ScenarioNewService} from './scenario-new.service';
import {Scenario} from '../scenarios/scenarios.component';
import {ScenariosService} from '../scenarios/scenarios.service';
import {ScenarioDetailService} from '../scenario-detail/scenario-detail.service';
import {ViewDataService} from '../view-data/view-data.service';
import {ScenarioNewAPI} from './scenario-new';
import {StartingValues} from '../scenario-detail/scenario-detail';

const io = ( window as any ).require('socket.io-client');

@Component({
  selector: 'app-scenario-new',
  templateUrl: './scenario-new.component.html',
  styleUrls: ['./scenario-new.component.css']
})


export class ScenarioNewComponent implements OnInit {

  // To get the right route for the starting values
  scenarioID: number;
  private sub: any;

  // The final structure we'll iterate over
  scenarioNewAPI: ScenarioNewAPI;

  // Some options depending on whether we're editing a scenario,
  // populating from an existing scenario, etc.
  hideScenarioName: boolean;
  inactiveScenarioName: boolean;

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
              private viewDataService: ViewDataService,
              private router: Router,
              private route: ActivatedRoute,
              private zone: NgZone,
              private location: Location) {

    const navigation = this.router.getCurrentNavigation();
    const state = navigation.extras.state as {
      hideScenarioName: boolean,
      inactiveScenarioName: boolean
    };
  }

  ngOnInit() {
    // Need to get the navigation extras from history (as the state is only
    // available during navigation)
    this.hideScenarioName = history.state.hideScenarioName;
    this.inactiveScenarioName = history.state.inactiveScenarioName;

    // Disable the scenarioName form control if the navigation extras
    // requested it
    if (this.inactiveScenarioName) {
      this.newScenarioForm.controls.scenarioName.disable();
    }

    // The ActivatedRoute service provides a params Observable which we can
    // subscribe to in order to get the route parameters
    this.sub = this.route.params.subscribe(params => {
       this.scenarioID = +params.id;
       console.log(`Scenario ID is ${this.scenarioID}`);
    });

    // Get the scenarios list for the 'populate from scenario' functionality
    this.getScenarios();

    // Make the scenario-new view
    this.getScenarioNewAPI();

    // Set the starting form state (from the ScenarioEditService
    // StartingValueSubject)
    this.setStartingValues();
  }

  getScenarioNewAPI(): void {
    // Get the settings
    this.scenarioNewService.getScenarioNewAPI()
      .subscribe(
        scenarioNewAPI => {
          this.scenarioNewAPI = scenarioNewAPI;
        }
      );
  }

  // Get all scenarios
  getScenarios(): void {
      this.scenariosService.getScenarios()
        .subscribe(scenarios => { this.allScenarios = scenarios; console.log(this.allScenarios)} );
  }

  // Set the starting values directly based on a user-selected scenario name
  getStartingValuesFromScenario(): void {
    // Get from form
    const scenarioID = this.fromScenarioForm.value.populateFromScenarioID;
    console.log(scenarioID);

    // When populating from a scenario, we'll hide the scenario name to
    // avoid accidental overwriting
    const navigationExtras: NavigationExtras = {
      state: {hideScenarioName: true, inactiveScenarioName: false}
    };
    this.router.navigate(['/scenario-new', scenarioID], navigationExtras)
      .then(r => this.ngOnInit());
  }

  setStartingValues(): void {
    // Get starting values: empty if we're in scenario-new/0 route;
    // otherwise, get the starting values based on the scenario ID
    if (this.scenarioID === 0) {
      this.startingValues = emptyStartingValues;
      console.log('Starting values: ', this.startingValues);
      // Set the values; the scenario name first, then the rest of the rows
      // based on their identifiers
      this.newScenarioForm.controls.scenarioName.setValue(
          this.startingValues.scenario_name, {onlySelf: true}
        );

      const allRowsIdentifiers = this.scenarioNewAPI.allRowIdentifiers;
      for (const row of allRowsIdentifiers) {
        this.newScenarioForm.controls[row].setValue(
          this.startingValues[row], {onlySelf: true}
        );
      }
    } else {
      console.log('caught scenario id ', this.scenarioID);
      this.scenarioDetailService.getScenarioDetailAPI(this.scenarioID)
        .subscribe(
          scenarioDetail => {
            this.startingValues = scenarioDetail.editScenarioValues;
            console.log('Starting values: ', this.startingValues);
            // Set the values; the scenario name first, then the rest of the rows
            // based on their identifiers
            // If requeste, 'hide' the scenario name
            if (this.hideScenarioName) {
              this.newScenarioForm.controls.scenarioName.setValue(
                '', {onlySelf: true}
              );
            } else {
              this.newScenarioForm.controls.scenarioName.setValue(
                this.startingValues.scenario_name, {onlySelf: true}
              );
            }

            const allRowsIdentifiers = this.scenarioNewAPI.allRowIdentifiers;
            for (const row of allRowsIdentifiers) {
              this.newScenarioForm.controls[row].setValue(
                this.startingValues[row], {onlySelf: true}
              );
            }
          }
        );
    }
  }

  // // Set the starting values based on the scenario that the user has
  // // requested to edit (on navigate from scenario-detail to scenario-new)
  // setStartingFormStateOnInit(): void {
  //   this.scenarioEditService.startingValuesSubject
  //     .subscribe((startingValues: StartingValues) => {
  //       this.startingValues = startingValues;
  //       this.setStartingValues();
  //     });
  // }

  viewData(tableNameInDB, rowNameInDB): void {
    const dataToView = `${tableNameInDB}-${rowNameInDB}`;
    // Send the table name to the view-data service that view-data component
    // uses to determine which tables to show
    this.viewDataService.changeDataToView(dataToView);
    console.log('Sending data to view, ', dataToView);
    // Switch to the new scenario view, with 0 as argument (show all data)
    this.router.navigate(['/view-data', 0]);
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
  }

  goBack(): void {
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
