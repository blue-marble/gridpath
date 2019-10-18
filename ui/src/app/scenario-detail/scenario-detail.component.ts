import { Component, OnInit, NgZone } from '@angular/core';
import { Router, ActivatedRoute, NavigationExtras } from '@angular/router';
import { Location } from '@angular/common';

import { ScenarioDetailAPI } from './scenario-detail';
import { ScenarioDetailService } from './scenario-detail.service';
import { ScenarioInputsService } from '../scenario-inputs/scenario-inputs.service';

import {socketConnect} from '../app.component';


@Component({
  selector: 'app-scenario-detail',
  templateUrl: './scenario-detail.component.html',
  styleUrls: ['./scenario-detail.component.css']
})

export class ScenarioDetailComponent implements OnInit {

  scenarioDetail: ScenarioDetailAPI;

  // To get the right route
  scenarioID: number;
  private sub: any;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private scenarioDetailService: ScenarioDetailService,
    private viewDataService: ScenarioInputsService,
    private location: Location,
    private zone: NgZone) {
  }

  ngOnInit(): void {
    // The ActivatedRoute service provides a params Observable which we can
    // subscribe to in order to get the route parameters
    this.sub = this.route.params.subscribe(params => {
       this.scenarioID = +params.id;
       console.log(`Scenario ID is ${this.scenarioID}`);
    });

    this.scenarioDetail = {} as ScenarioDetailAPI;
    // Get the scenario detail data
    this.getScenarioDetailAPI(this.scenarioID);
  }

  getScenarioDetailAPI(scenarioID): void {
    this.scenarioDetailService.getScenarioDetailAPI(scenarioID)
      .subscribe(
        scenarioDetail => {
            this.scenarioDetail = scenarioDetail;
        }
      );
  }

  goBack(): void {
    this.location.back();
  }

  runScenario(): void {
    console.log(
      `Running scenario ${this.scenarioDetail.scenarioName}, scenario_id ${this.scenarioID}`
    );

    const socket = socketConnect();

    socket.emit(
            'launch_scenario_process',
            {scenario: this.scenarioID, solver: this.scenarioDetail.solver,
             skipWarnings: false}
        );

    // Check and update the run status (whole API) when the scenario process is
    // launched
    socket.on('scenario_process_launched', () => {
      console.log('Scenario process launched.');
      // this.zone.run(
      //   () => {
      //     this.getScenarioDetailAPI(this.scenarioID);
      //   }
      // );
      setTimeout(() => {
        this.zone.run(
          () => {
            this.getScenarioDetailAPI(this.scenarioID);
          }
        );
      }, 3000);
    });
  }

  stopScenarioRun(): void {
    console.log(
      `Stopping scenario ${this.scenarioDetail.scenarioName}, scenario_id ${this.scenarioID}`
    );

    const socket = socketConnect();

    socket.emit('stop_scenario_run', {scenario: this.scenarioID});

    // Check and update the run status (whole API) when the scenario process is
    // launched
    socket.on('scenario_stopped', () => {
      this.zone.run(
          () => {
            this.getScenarioDetailAPI(this.scenarioID);
          });
    });
  }

  editScenario(): void {
    // Switch to the new scenario view, disable scenario name field
    const navigationExtras: NavigationExtras = {
      state: {hideScenarioName: false, inactiveScenarioName: true}
    };
    this.router.navigate(['/scenario-new', this.scenarioID], navigationExtras);
  }

  validateScenario(scenarioID): void {
    console.log(
      `Validating scenario ${this.scenarioDetail.scenarioName}, scenario_id ${scenarioID}`
    );

    const socket = socketConnect();

    socket.emit(
            'validate_scenario',
            {scenario: scenarioID}
        );

    socket.on('validation_complete', () => {
      console.log('Validation complete');
      this.zone.run(
        () => {
          this.getScenarioDetailAPI(scenarioID);
        }
      );
    });
  }

  viewDescription(tableNameInDB, rowNameInDB): void {
    const navigationExtras: NavigationExtras = {
      state: {type: 'subscenario', table: tableNameInDB, row: rowNameInDB}
    };
    // Switch to the new scenario view
    this.router.navigate(['/scenario-inputs', this.scenarioID],
      navigationExtras);
  }

  viewInputs(tableNameInDB, rowNameInDB): void {
    const navigationExtras: NavigationExtras = {
      state: {type: 'input', table: tableNameInDB, row: rowNameInDB}
    };
    // Switch to the new scenario view
    this.router.navigate(['/scenario-inputs', this.scenarioID],
      navigationExtras);
  }

  viewValidationErrors(): void {
    const navigationExtras: NavigationExtras = {
      state: {table: 'status_validation'}
    };
    this.router.navigate(['/view-data', this.scenarioID],
      navigationExtras);
  }

  viewResults(): void {
    this.router.navigate(['/scenario', this.scenarioID, 'results']);
  }

  // TODO: add confirmations for clearing and deleting
  clearScenario(): void {
    const socket = socketConnect();

    socket.emit(
            'clear_scenario',
            {scenario: this.scenarioID}
        );

    socket.on('scenario_cleared', () => {
      console.log('Scenario cleared');
      this.zone.run(
        () => {
          this.getScenarioDetailAPI(this.scenarioID);
        }
      );
    });
  }

  deleteScenario(): void {
    const socket = socketConnect();

    socket.emit(
            'delete_scenario',
            {scenario: this.scenarioID}
        );

    socket.on('scenario_deleted', () => {
      console.log('Scenario deleted');
      this.zone.run(
        () => this.router.navigate(['/scenarios'])
      );
    });
  }

  updateScenarioDetail(): void {
    console.log('Updating view...');
    this.getScenarioDetailAPI(this.scenarioID);
  }

}
