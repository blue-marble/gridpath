import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { FormGroup, FormBuilder } from '@angular/forms';

import { ScenarioResultsService } from './scenario-results.service';
import { ScenarioResultsTable, ResultsOptions } from './scenario-results';
import { ScenarioDetailService } from '../scenario-detail/scenario-detail.service';

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
            stage: plot.stage,
            project: plot.project,
            yMax: null
          });
          this.allPlotFormGroups.push(form);
        }
      });
  }

  showPlot(formGroup): void {
    // We need to set the plotFormValue and plotHTMLTarget before
    // calling ngOnInit to be able to embed the plot
    this.plotFormValue = formGroup;

    const plotType = formGroup.value.plotType;
    const loadZone = formGroup.value.loadZone;
    const carbonCapZone = formGroup.value.carbonCapZone;
    const rpsZone = formGroup.value.rpsZone;
    const period = formGroup.value.period;
    const horizon = formGroup.value.horizon;
    const stage = formGroup.value.stage;
    const project = formGroup.value.project;
    let yMax = formGroup.value.yMax;
    if (yMax === null) { yMax = 'default'; }

    this.scenarioResultsService.getResultsPlot(
      this.scenarioID, plotType, loadZone, rpsZone, carbonCapZone,
      period, horizon, stage, project, yMax
    ).subscribe(resultsPlot => {
        this.plotHTMLTarget = resultsPlot.plotJSON.target_id;
        this.resultsToShow = resultsPlot.plotJSON.target_id;
        this.ngOnInit();
      });
  }

  getResultsPlot(scenarioID, formGroup): void {
    const plotType = formGroup.value.plotType;
    const loadZone = formGroup.value.loadZone;
    const carbonCapZone = formGroup.value.carbonCapZone;
    const rpsZone = formGroup.value.rpsZone;
    const period = formGroup.value.period;
    const horizon = formGroup.value.horizon;
    const stage = formGroup.value.stage;
    const project = formGroup.value.project;
    let yMax = formGroup.value.yMax;
    if (yMax === null) { yMax = 'default'; }

    this.scenarioResultsService.getResultsPlot(
      scenarioID, plotType, loadZone, rpsZone, carbonCapZone,
      period, horizon, stage, project, yMax
    ).subscribe(resultsPlot => {
        this.resultsPlot = resultsPlot.plotJSON;
        Bokeh.embed.embed_item(this.resultsPlot);
      });
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
