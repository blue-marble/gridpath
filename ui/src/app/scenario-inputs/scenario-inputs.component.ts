import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';

const electron = ( window as any ).require('electron');

import { ScenarioInputsService } from './scenario-inputs.service';
import { ScenarioInputsTable } from './scenario-inputs';
import { ScenarioDetailService } from '../scenario-detail/scenario-detail.service';
import { socketConnect } from '../app.component';

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
  type: string;
  table: string;
  row: string;

  // The scenario name
  scenarioName: string;

  // Object we'll populate with the data for the table to show
  tableToShow: ScenarioInputsTable;

  constructor(
    private route: ActivatedRoute,
    private location: Location,
    private scenarioInputsService: ScenarioInputsService,
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
    this.type = history.state.type;
    this.table = history.state.table;
    this.row = history.state.row;

    // Get the scenario name
    this.getScenarioName(this.scenarioID);

    // Get the data
    this.tableToShow = {} as ScenarioInputsTable;
    this.getScenarioInputs(this.scenarioID, this.type, this.table, this.row);

  }

  getScenarioInputs(scenarioID, type, table, row): void {
    this.scenarioInputsService.getScenarioInputs(scenarioID, type, table, row)
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

  downloadTableData(): void {
    electron.remote.dialog.showSaveDialog(
      { title: 'untitled.csv', defaultPath: 'table.csv',
        filters: [{extensions: ['csv']}]
      }, (targetPath) => {
        const socket = socketConnect();

        socket.emit(
            'save_table_data',
            { downloadPath: targetPath,
              tableName: null,  // not needed for inputs
              scenarioID: this.scenarioID,
              otherScenarios: [],
              tableType: this.type,
              uiTableNameInDB: this.table,
              uiRowNameInDB: this.row

            }
        );
      }
    );
  }

  goBack(): void {
    this.location.back();
  }

}
