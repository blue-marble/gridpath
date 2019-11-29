import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { FormGroup, FormBuilder } from '@angular/forms';

const electron = ( window as any ).require('electron');

import { ScenarioResultsService } from './scenario-results.service';
import { ScenarioResultsTable, ResultsOptions } from './scenario-results';
import { ScenarioDetailService } from '../scenario-detail/scenario-detail.service';
import {socketConnect} from '../app.component';

const Bokeh = ( window as any ).require('bokehjs');


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
  resultsToShow: string;

  // //// Tables //// //
  // All table results buttons
  allTableButtons: {table: string, caption: string}[];
  // The results table structure (to create the HTML for the table)
  resultsTable: ScenarioResultsTable;
  // Which results table to show (by running getResultsTable in ngOnInit
  // with tableToShow as argument)
  tableToShow: string;

  // //// Plots //// //
  // All plot forms
  allPlotFormGroups: FormGroup[];
  // The possible options for the forms
  formOptions: ResultsOptions;
  // The value of the submitted plot form
  plotFormValue: {};
  // The target_id of the plot we'll show; we'll get this from the JSON
  // object and set it before embedding the plot
  plotHTMLTarget: string;
  // The JSON plot object
  resultsPlot: any;

  // To get the right route for which scenario to use
  scenarioID: number;
  private sub: any;

  constructor(
    private route: ActivatedRoute,
    private scenarioResultsService: ScenarioResultsService,
    private scenarioDetailService: ScenarioDetailService,
    private location: Location,
    private formBuilder: FormBuilder

  ) { }

  ngOnInit() {
    // The ActivatedRoute service provides a params Observable which we can
    // subscribe to in order to get the route parameters
    this.sub = this.route.params.subscribe(params => {
       this.scenarioID = +params.id;
       console.log(`Scenario ID is ${this.scenarioID}`);
    });

    this.getScenarioName(this.scenarioID);

    // //// Tables //// //
    // Make the results buttons
    this.allTableButtons = [];
    this.makeResultsTableButtons();
    // Initialize the resultsTable
    this.resultsTable = {} as ScenarioResultsTable;
    // Get data
    this.getResultsTable(this.scenarioID, this.tableToShow);

    // //// Plots //// //
    // Make the plot forms
    this.getFormOptions(this.scenarioID);
    this.allPlotFormGroups = [];
    this.makeResultsPlotForms();
    // Get and embed the plot
    this.getResultsPlot(this.scenarioID, this.plotFormValue);
  }

  // //// Tables //// //
  makeResultsTableButtons(): void {
    this.scenarioResultsService.getResultsIncludedTables()
      .subscribe(includedTables => {
        this.allTableButtons = includedTables;
      });
  }

  showTable(tableToShow): void {
    // Set the values needed to display the table after ngOnInit
    this.tableToShow = tableToShow;
    this.resultsToShow = tableToShow;

    // Refresh the view
    this.ngOnInit();
  }

  getResultsTable(scenarioID, table): void {
    this.scenarioResultsService.getResultsTable(scenarioID, table)
      .subscribe(inputTableRows => {
        this.resultsTable = inputTableRows;
      });
  }

  // //// Plots //// //
  getFormOptions(scenarioID): void {
    this.scenarioResultsService.getOptions(scenarioID)
      .subscribe(options => {
        this.formOptions = options;
      });
  }

  makeResultsPlotForms(): void {
    this.scenarioResultsService.getResultsIncludedPlots()
      .subscribe(includedPlots => {
        for (const plot of includedPlots) {
          const form = this.formBuilder.group({
            plotType: plot.plotType,
            caption: plot.caption,
            loadZone: plot.loadZone,
            rpsZone: plot.rpsZone,
            carbonCapZone: plot.carbonCapZone,
            period: plot.period,
            horizon: plot.horizon,
            subproblem: plot.subproblem,
            stage: plot.stage,
            project: plot.project,
            yMax: null
          });
          this.allPlotFormGroups.push(form);
        }
      });
  }

  // This function is called when a user requests a plot; this will change
  // some values, namely the plotHTMLTarget and then call ngOnInit, which
  // in turn calls getResultPlot
  showPlotOrDownloadData(formGroup): void {

    // Figure out which button was pressed
    const buttonName = document.activeElement.getAttribute('Name');
    console.log(buttonName);

    // We need to set the plotFormValue and plotHTMLTarget before
    // calling ngOnInit to be able to embed the plot
    this.plotFormValue = formGroup;

    const formValues = this.getFormGroupValues(formGroup);

    if (buttonName === 'showPlot') {
      this.scenarioResultsService.getResultsPlot(
        this.scenarioID, formValues.plotType, formValues.loadZone,
          formValues.rpsZone, formValues.carbonCapZone, formValues.period,
          formValues.horizon, formValues.subproblem, formValues.stage,
          formValues.project, formValues.yMax
      ).subscribe(resultsPlot => {
        this.plotHTMLTarget = resultsPlot.plotJSON.target_id;
        this.resultsToShow = resultsPlot.plotJSON.target_id;
        this.ngOnInit();
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

  // This function is called in ngOnInit
  getResultsPlot(scenarioID, formGroup): void {

    const formValues = this.getFormGroupValues(formGroup);
    this.scenarioResultsService.getResultsPlot(
      scenarioID, formValues.plotType, formValues.loadZone, formValues.rpsZone,
      formValues.carbonCapZone, formValues.period, formValues.horizon,
      formValues.subproblem, formValues.stage, formValues.project,
      formValues.yMax
    ).subscribe(resultsPlot => {
        this.resultsPlot = resultsPlot.plotJSON;
        Bokeh.embed.embed_item(this.resultsPlot);
      });
  }

  getFormGroupValues(formGroup) {
    const plotType = formGroup.value.plotType;
    const loadZone = formGroup.value.loadZone;
    const carbonCapZone = formGroup.value.carbonCapZone;
    const rpsZone = formGroup.value.rpsZone;
    const period = formGroup.value.period;
    const horizon = formGroup.value.horizon;
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
    let yMax = formGroup.value.yMax;
    if (yMax === null) { yMax = 'default'; }

    return {plotType, loadZone, carbonCapZone, rpsZone, period, horizon,
      subproblem, stage, project, yMax};
  }

  downloadPlotData(targetPath, formGroup): void {
    const formValues = this.getFormGroupValues(formGroup);
    const socket = socketConnect();

    socket.emit(
            'save_plot_data',
            { downloadPath: targetPath,
              scenarioID: this.scenarioID,
              plotType: formValues.plotType,
              loadZone: formValues.loadZone,
              carbonCapZone: formValues.carbonCapZone,
              rpsZone: formValues.rpsZone,
              period: formValues.period,
              horizon: formValues.horizon,
              subproblem: formValues.subproblem,
              stage: formValues.stage,
              project: formValues.project,
              yMax: formValues.yMax}
        );
  }

  clearPlots(): void {
    this.resultsToShow = null;
    this.ngOnInit();
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
