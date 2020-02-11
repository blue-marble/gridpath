import {Component, OnInit, NgZone, OnDestroy} from '@angular/core';
import { Router, ActivatedRoute, NavigationExtras } from '@angular/router';
import { Location } from '@angular/common';

const electron = ( window as any ).require('electron');
const path = ( window as any ).require('path');

import { ScenarioDetailAPI } from './scenario-detail';
import { ScenarioDetailService } from './scenario-detail.service';
import { ScenarioInputsService } from '../scenario-inputs/scenario-inputs.service';

import {socketConnect} from '../app.component';


@Component({
  selector: 'app-scenario-detail',
  templateUrl: './scenario-detail.component.html',
  styleUrls: ['./scenario-detail.component.css']
})

export class ScenarioDetailComponent implements OnInit, OnDestroy {

  scenarioDetail: ScenarioDetailAPI;
  refreshScenarioDetail: any;

  scenarioLog: string;

  // To disable runScenarioButton on click
  runScenarioClicked: boolean;

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
    // Get the scenario detail data and refresh every 5 seconds
    this.getScenarioDetailAPI(this.scenarioID);
    this.refreshScenarioDetail = setInterval(() => {
        this.getScenarioDetailAPI(this.scenarioID);
    }, 5000);
  }

  ngOnDestroy() {
    // Clear scenario detail refresh intervals (stop refreshing) on component
    // destroy
    clearInterval(this.refreshScenarioDetail);
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

    // Change the run status to blank
    this.scenarioDetail.runStatus = 'launching';

    // Connect to the server and launch the scenario process
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

    // If the scenario is already running, warn the user
    // This shouldn't ever happen, as the Run Scenario button should
    // disappear when status changes to 'running'
    socket.on('scenario_already_running', () => {
      alert(`Scenario ${this.scenarioDetail.scenarioName} already running. You can stop and restart it.`);
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

    // If the process ID does not exist, warn the user that we'll clean up
    // this scenario as a previous process run likely did not exit correctly
    socket.on('process_id_not_found', () => {
      alert('The process ID for this scenario was not found. This is likely ' +
        'the result of a previous system error. Any scenario results will be ' +
        'cleared.');
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

  viewRunLog(): void {

    const logFile = `e2e_${this.scenarioDetail.runStartTime}_pid_${this.scenarioDetail.runPID}.log`;

    // Ask Electron for any the current scenarios setting
    electron.ipcRenderer.send('requestStoredScenarioDirectoryForLog');
    electron.ipcRenderer.on('sendStoredScenarioDirectoryForLog',
      (event, data) => {
        const logFilePath = path.join(
          data.currentScenariosDirectory.value,
          this.scenarioDetail.scenarioName, 'logs', logFile
        );

        console.log(logFilePath);

        const navigationExtras: NavigationExtras = {
          state: {pathToLogFile: logFilePath}
        };

        this.zone.run(
          () => {
            this.router.navigate(
              ['/scenario', this.scenarioID, 'log'],
              navigationExtras
              );
          }
        );
        }
    );
  }

  viewResults(): void {
    this.router.navigate(['/scenario', this.scenarioID, 'results']);
  }

  clearScenario(): void {
    if (confirm(`Are you sure you want to clear all results for scenario ${this.scenarioDetail.scenarioName}?`)) {
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
  }

  deleteScenario(): void {
    if (confirm(`Are you sure you want to delete scenario ${this.scenarioDetail.scenarioName}?`)) {
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
  }

  updateScenarioDetail(): void {
    console.log('Updating view...');
    this.getScenarioDetailAPI(this.scenarioID);
  }


  addScenarioToRunQueue(): void {
      const socket = socketConnect();

      socket.emit(
        'add_scenario_to_queue',
        {scenario: this.scenarioID}
      );
  }

  removeScenarioFromRunQueue(): void {
      const socket = socketConnect();

      socket.emit(
        'remove_scenario_from_queue',
        {scenario: this.scenarioID}
      );
  }
}
