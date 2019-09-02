import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';
import { ScenarioDetailService } from '../scenario-detail/scenario-detail.service';
import { ViewDataService } from './view-data.service';
import { ViewDataTable } from './view-data';

@Component({
  selector: 'app-view-data',
  templateUrl: './view-data.component.html',
  styleUrls: ['./view-data.component.css']
})
export class ViewDataComponent implements OnInit {

  // To get the right route
  scenarioID: number;
  private sub: any;

  // Navigation extras (will tell us which database table to show)
  table: string;

  // The scenario name
  scenarioName: string;

  // Object we'll populate with the data for the table to show
  // TODO: add type
  tableToShow: ViewDataTable;

  constructor(
    private route: ActivatedRoute,
    private location: Location,
    private viewDataService: ViewDataService,
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

    // Get the scenario name
    this.getScenarioName(this.scenarioID);

    // Get the data
    this.tableToShow = {} as ViewDataTable;
    this.getData(this.scenarioID, this.table);
  }

  getData(scenarioID, table): void {
    this.viewDataService.getTable(scenarioID, table)
      .subscribe(inputTableRows => {
        this.tableToShow = inputTableRows;
      });
  }

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
