import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';

const io = ( window as any ).require('socket.io-client');

import { ScenarioDetail, ScenarioDetailTableRow } from './scenario-detail';
import { ScenarioDetailService } from './scenario-detail.service';
import { ScenarioEditService } from './scenario-edit.service';
import { ViewDataService } from '../view-data/view-data.service';
import { StartingValues } from '../scenario-new/scenario-new.component';


@Component({
  selector: 'app-scenario-detail',
  templateUrl: './scenario-detail.component.html',
  styleUrls: ['./scenario-detail.component.css']
})

export class ScenarioDetailComponent implements OnInit {

  // The final table structure we'll iterate over
  scenarioDetailStructure: ScenarioDetail[];

  scenarioName: string;

  // For editing a scenario
  startingValues: StartingValues;

  // To get the right route
  scenarioID: number;
  private sub: any;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private scenarioDetailService: ScenarioDetailService,
    private scenarioEditService: ScenarioEditService,
    private viewDataService: ViewDataService,
    private location: Location) {
  }

  ngOnInit(): void {
    // The ActivatedRoute service provides a params Observable which we can
    // subscribe to in order to get the route parameters
    this.sub = this.route.params.subscribe(params => {
       this.scenarioID = +params.id;
       console.log(`Scenario ID is ${this.scenarioID}`);
    });

    // Get the scenario detail data
    this.getScenarioName(this.scenarioID);
    this.getScenarioDetailAPI(this.scenarioID);

    // We may need this if the user decides to edit the scenario
    // TODO: only run this on scenario edit?
    this.getScenarioStartingSettings(this.scenarioID);

  }

  getScenarioName(scenarioID): void {

    this.scenarioDetailService.getScenarioName(scenarioID)
      .subscribe(
        scenarioDetail => {
          this.scenarioName = scenarioDetail;
        }
      );

  }

  getScenarioDetailAPI(scenarioID): void {
    const settingsTable = new ScenarioDetail();

    this.scenarioDetailService.getScenarioDetailAPI(scenarioID)
      .subscribe(
        scenarioDetail => {
            this.scenarioDetailStructure = scenarioDetail;
        }
      );
  }

  getScenarioStartingSettings(scenarioID): void {
    this.scenarioEditService.getScenarioDetailAll(scenarioID)
      .subscribe(startingValues => {
        this.startingValues = startingValues;
      });
  }


  goBack(): void {
    this.location.back();
  }

  runScenario(scenarioID): void {
    console.log(
      `Running scenario ${this.scenarioName}, scenario_id ${scenarioID}`
    );

    // TODO: refactor server-connection code to be reused
    const socket = io.connect('http://127.0.0.1:8080/');
    socket.on('connect', () => {
        console.log(`Connection established: ${socket.connected}`);
    });

    socket.emit(
            'launch_scenario_process',
            {scenario: scenarioID}
        );
    // Keep track of process ID for this scenario run
    socket.on('scenario_already_running', (msg) => {
        console.log('in scenario_already_running');
        console.log (msg);
    });
  }

  editScenario(): void {
    // Send init setting values to the scenario edit service that the
    // scenario-new component uses to set initial setting values
    this.scenarioEditService.changeStartingScenario(this.startingValues);
    // Switch to the new scenario view
    this.router.navigate(['/scenario-new/']);
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

}
