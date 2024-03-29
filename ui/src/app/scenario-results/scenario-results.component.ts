import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { FormGroup, FormBuilder } from '@angular/forms';
import * as Bokeh from '@bokeh/bokehjs/build/js/lib/embed';

const electron = ( window as any ).require('electron');

import { ScenarioResultsService } from './scenario-results.service';
import { ScenarioResultsTable, ResultsOptions } from './scenario-results';
import { ScenarioDetailService } from '../scenario-detail/scenario-detail.service';
import {socketConnect} from '../app.component';


@Component({
  selector: 'app-scenario-results',
  templateUrl: './scenario-results.component.html',
  styleUrls: ['./scenario-results.component.css']
})

export class ScenarioResultsComponent implements OnInit {

  // Scenario Name
  scenarioName: string;

  // Which results to show; we use an *ngIf in the table <table> and plot
  // <div> definitions to determine whether to show the respective result
  // A particular table is shown if the *ngIf is set to the table name
  // All plots are shown within the same div if resultsToShow is set to
  // 'plotDiv'
  resultsToShow: string;

  // //// Tables //// //
  // All table results buttons
  allTableButtons: {table: string, caption: string}[];
  // The results table structure (to create the HTML for the table)
  resultsTable: ScenarioResultsTable;
  // Which results table to show (by running showResultsTable)
  // with tableToShow as argument)
  tableToShow: string;

  // //// Plots //// //
  // All plot forms
  allPlotFormGroups: FormGroup[];
  // The possible options for the forms
  formOptions: ResultsOptions;

  // To get the right route for which scenario to use
  scenarioID: number;
  private sub: any;

  constructor(
    private route: ActivatedRoute,
    private scenarioResultsService: ScenarioResultsService,
    private scenarioDetailService: ScenarioDetailService,
    private location: Location,
    private formBuilder: FormBuilder

  ) {
    // The ActivatedRoute service provides a params Observable which we can
    // subscribe to in order to get the route parameters
    this.sub = this.route.params.subscribe(params => {
       this.scenarioID = +params.id;
       console.log(`Scenario ID is ${this.scenarioID}`);
    });

    this.getScenarioName(this.scenarioID);

    // //// Tables //// //
    // Make the table results buttons
    this.makeResultsTableButtons();

    // // //// Plots //// //
    // Make the plot forms
    this.makeResultsPlotForms(this.scenarioID);
  }

  ngOnInit() {}

  // //// Tables //// //
  makeResultsTableButtons(): void {
    this.scenarioResultsService.getResultsIncludedTables()
      .subscribe(includedTables => {
        this.allTableButtons = includedTables;
        console.log(this.allTableButtons);
      });
  }

  showResultsTable(scenarioID, table): void {
    this.scenarioResultsService.getResultsTable(scenarioID, table)
      .subscribe(inputTableRows => {
        this.resultsTable = inputTableRows;
        // Set the values needed to display the table after ngOnInit
        this.tableToShow = table;
        this.resultsToShow = this.tableToShow;
      });
  }

  downloadTableData(table): void {
    electron.remote.dialog.showSaveDialog(
        { title: 'untitled.csv', defaultPath: 'table.csv',
          filters: [{extensions: ['csv']}]
        }, (targetPath) => {
          const socket = socketConnect();

          const tableActual = table.replace(/-/g, '_');

          socket.emit(
              'save_table_data',
              { downloadPath: targetPath,
                tableName: tableActual,
                scenarioID: this.scenarioID,
                otherScenarios: [],
                tableType: 'result',
                uiTableNameInDB: null,
                uiRowNameInDB: null
              }
          );
        }
      );
  }

  // //// Plots //// //
  // Make the plot forms; we need to access to formOptions when iterating
  // over the forms, so get those first
  makeResultsPlotForms(scenarioID): void {

    this.allPlotFormGroups = [];

    this.scenarioResultsService.getOptions(scenarioID)
      .subscribe(options => {
        this.formOptions = options;

        this.scenarioResultsService.getResultsIncludedPlots()
        .subscribe(includedPlots => {
          for (const plot of includedPlots) {
            const form = this.formBuilder.group({
              plotType: plot.plotType,
              caption: plot.caption,
              loadZone: plot.loadZone,
              energyTargetZone: plot.energyTargetZone,
              carbonCapZone: plot.carbonCapZone,
              period: plot.period,
              horizon: plot.horizon,
              startTimepoint: plot.startTimepoint,
              endTimepoint: plot.endTimepoint,
              subproblem: plot.subproblem,
              stage: plot.stage,
              project: plot.project,
              commitProject: plot.commitProject,
              yMax: null
            });
            this.allPlotFormGroups.push(form);
          }
        });
      });
  }

  // This function is called when a user requests a plot
  showPlotOrDownloadData(formGroup): void {

    // Figure out which button was pressed
    const buttonName = document.activeElement.getAttribute('Name');
    console.log(buttonName);

    const formValues = getFormGroupValues(formGroup);

    if (buttonName === 'showPlot') {
      this.resultsToShow = 'plotDiv';

      this.scenarioResultsService.getResultsPlot(
        this.scenarioID, formValues.plotType, formValues.loadZone,
          formValues.energyTargetZone, formValues.carbonCapZone,
          formValues.period, formValues.horizon,
          formValues.startTimepoint, formValues.endTimepoint,
          formValues.subproblem, formValues.stage,
          formValues.project, formValues.commitProject, formValues.yMax
      ).subscribe(resultsPlot => {
        // Embed the plot; all plots have 'plotHTMLTarget' as their target_id
        Bokeh.embed_item(resultsPlot.plotJSON);
      });
    }

    if (buttonName === 'downloadData') {
      electron.remote.dialog.showSaveDialog(
        { title: 'untitled.csv', defaultPath: 'plot.csv',
          filters: [{extensions: ['csv']}]
        }, (targetPath) => {
          this.downloadPlotData(targetPath, formGroup);
        }
      );
    }

  }

  downloadPlotData(targetPath, formGroup): void {
    const formValues = getFormGroupValues(formGroup);
    const socket = socketConnect();

    socket.emit(
            'save_plot_data',
            { downloadPath: targetPath,
              scenarioIDList: [this.scenarioID],
              plotType: formValues.plotType,
              loadZone: formValues.loadZone,
              carbonCapZone: formValues.carbonCapZone,
              energyTargetZone: formValues.energyTargetZone,
              period: formValues.period,
              horizon: formValues.horizon,
              startTimepoint: formValues.startTimepoint,
              endTimepoint: formValues.endTimepoint,
              subproblem: formValues.subproblem,
              stage: formValues.stage,
              project: formValues.project,
              commitProject: formValues.commitProject,
              yMax: formValues.yMax}
        );
  }

  clearResults(): void {
    this.resultsToShow = null;

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

export function getFormGroupValues(formGroup) {
    const plotType = formGroup.value.plotType;
    const loadZone = formGroup.value.loadZone;
    const carbonCapZone = formGroup.value.carbonCapZone;
    const energyTargetZone = formGroup.value.energyTargetZone;
    const period = formGroup.value.period;
    const horizon = formGroup.value.horizon;
    const startTimepoint = formGroup.value.startTimepoint;
    const endTimepoint = formGroup.value.endTimepoint;
    // Set subproblem to 'default' if it is null or 'Select Subproblem' (either
    // because the user didn't select a subproblem, selected the prompt, or
    // because we didn't give the subproblem option
    const subproblem = (formGroup.value.subproblem == null) ? 'default'
      : (formGroup.value.subproblem === 'Select Subproblem') ? 'default'
        : formGroup.value.subproblem;
    // Set stage to 'default' if it is null or 'Select Stage' (either
    // because the user didn't select a stage, selected the prompt, or
    // because we didn't give the stage option
    const stage = (formGroup.value.stage == null) ? 'default'
      : (formGroup.value.stage === 'Select Stage') ? 'default'
        : formGroup.value.stage;
    const project = formGroup.value.project;
    const commitProject = formGroup.value.commitProject;
    let yMax = formGroup.value.yMax;
    if (yMax === null) { yMax = 'default'; }

    return {plotType, loadZone, carbonCapZone, energyTargetZone, period, horizon,
    startTimepoint, endTimepoint,
    subproblem, stage, project, commitProject, yMax};
}
