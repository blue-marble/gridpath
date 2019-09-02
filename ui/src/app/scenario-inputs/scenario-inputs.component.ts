import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';

import { ScenarioInputsService } from './scenario-inputs.service';
import { ScenarioInputsTable } from './scenario-inputs';
import { ScenarioDetailService } from '../scenario-detail/scenario-detail.service';

@Component({
  selector: 'app-view-data',
  templateUrl: './scenario-inputs.component.html',
  styleUrls: ['./scenario-inputs.component.css']
})
export class ScenarioInputsComponent implements OnInit {

  // To get the right route
  scenarioID: number;
  private sub: any;

  // Navigation extras (will tell us which database table to show)
  table: string;
  row: string;

  // The scenario name
  scenarioName: string;

  // Object we'll populate with the data for the table to show
  tableToShow: ScenarioInputsTable;

  validationTable: ScenarioInputsTable;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private location: Location,
    private viewDataService: ScenarioInputsService,
    private scenarioDetailService: ScenarioDetailService
  ) { }

  ngOnInit() {
    // The ActivatedRoute service provides a params Observable which we can
    // subscribe to in order to get the route parameters
    this.sub = this.route.params.subscribe(params => {
       this.scenarioID = +params.id;
       console.log(`Scenario ID in view-data is ${this.scenarioID}`);
    });

    // Need to get the navigation extras from history (as the state is only
    // available during navigation); we'll use these to change the behavior
    // of the scenario name field
    this.table = history.state.table;
    this.row = history.state.row;

    // Get the scenario name
    this.getScenarioName(this.scenarioID);

    // Get the data
    this.tableToShow = {} as ScenarioInputsTable;
    this.getScenarioInputs(this.scenarioID, this.table, this.row);


    // TODO: fix validation
    // if (this.dataToShow === 'validation') {
    //   this.getValidation();
    // }

  }

  getScenarioInputs(scenarioID, table, row): void {
    this.viewDataService.getScenarioInputs(scenarioID, table, row)
      .subscribe(inputTableRows => {
        this.tableToShow = inputTableRows;
      });
  }

  // TODO: fix validation
  // getValidation(): void {
  //   this.viewDataService.getValidation(this.scenarioID)
  //     .subscribe(inputTableRows => {
  //       this.validationTable = inputTableRows;
  //       this.allTables.push(this.validationTable);
  //     });
  // }

  getScenarioName(scenarioID): void {
    this.scenarioDetailService.getScenarioDetailAPI(scenarioID)
      .subscribe(scenarioDetailAPI => {
        this.scenarioName = scenarioDetailAPI.scenarioName;
      });
  }

  goBack(): void {
    this.location.back();
  }

}
