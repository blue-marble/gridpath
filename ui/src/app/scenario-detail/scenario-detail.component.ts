import { Component, OnInit, NgZone } from '@angular/core';
import { Router, ActivatedRoute, NavigationExtras } from '@angular/router';
import { Location } from '@angular/common';
import { FormControl, FormGroup } from '@angular/forms';

const io = ( window as any ).require('socket.io-client');

import { ScenarioDetailAPI } from './scenario-detail';
import { ScenarioDetailService } from './scenario-detail.service';
import { ScenarioInputsService } from '../scenario-inputs/scenario-inputs.service';


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

  // Select a solver for the run
  solversForm = new FormGroup ({
    solverFormControl: new FormControl()
  });

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

    const selectedSolver = this.solversForm.value.solverFormControl;

    // TODO: refactor server-connection code to be reused
    const socket = io.connect('http://127.0.0.1:8080/');
    socket.on('connect', () => {
        console.log(`Connection established: ${socket.connected}`);
    });

    socket.emit(
            'launch_scenario_process',
            {scenario: this.scenarioID, solver: selectedSolver}
        );
    // Keep track of process ID for this scenario run
    // TODO: how should we deal with the situation of a scenario already
    //  running?
    socket.on('scenario_already_running', (msg) => {
        console.log('Server says scenario is already running.');
        console.log (msg);
    });

    // Check and update the run status (whole API) when the scenario process is
    // launched
    socket.on('scenario_process_launched', () => {
      console.log('Scenario process launched.');
      this.zone.run(
        () => {
          this.getScenarioDetailAPI(this.scenarioID);
        }
      );
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

    // TODO: refactor server-connection code to be reused
    const socket = io.connect('http://127.0.0.1:8080/');
    socket.on('connect', () => {
        console.log(`Connection established: ${socket.connected}`);
    });

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

  viewInputData(tableNameInDB, rowNameInDB): void {
    const navigationExtras: NavigationExtras = {
      state: {table: tableNameInDB, row: rowNameInDB}
    };
    // Switch to the new scenario view
    this.router.navigate(['/scenario-inputs', this.scenarioID],
      navigationExtras);
  }

  viewValidationErrors(): void {
    const navigationExtras: NavigationExtras = {
      state: {table: 'validation', row: 'status'}
    };
    this.router.navigate(['/scenario-inputs', this.scenarioID],
      navigationExtras);
  }

}
