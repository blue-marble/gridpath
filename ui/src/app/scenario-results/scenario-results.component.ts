import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { FormGroup, FormBuilder } from '@angular/forms';

import { ScenarioResultsService } from './scenario-results.service';
import {
  ScenarioResultsTable,
  ResultsOptions
} from './scenario-results-table';

const Bokeh = ( window as any ).require('bokehjs');


@Component({
  selector: 'app-scenario-results',
  templateUrl: './scenario-results.component.html',
  styleUrls: ['./scenario-results.component.css']
})

export class ScenarioResultsComponent implements OnInit {

  // Which results to show
  resultsToShow: string;

  allFormGroups: FormGroup[];

  // Key for which results table to show
  tableToShow: string;

  // All results buttons (for the tables)
  allResultsButtons: {ngIfKey: string, caption: string}[];

  // Results tables; includedTables is used to know which buttons to show
  includedTables: {name: string; caption: string}[];
  resultsTable: ScenarioResultsTable;

  // Results plots; includedPlots is used to know which forms to show
  currentFormValue: {};

  // TODO: add type
  formOptions: ResultsOptions;
  plotHTMLTarget: string;
  resultsPlot: any;

  // To get the right route
  scenarioID: number;
  private sub: any;

  constructor(
    private route: ActivatedRoute,
    private scenarioResultsService: ScenarioResultsService,
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

    // Make the results buttons
    this.allResultsButtons = [];
    this.makeResultsTableButtons();

    // Make the forms
    this.getFormOptions(this.scenarioID);
    this.allFormGroups = [];
    this.makeResultsPlotForms(this.scenarioID);

    // Results tables
    this.includedTables = [];
    this.resultsTable = {} as ScenarioResultsTable;

    // // Get the key for which table to show
    // this.getResultsToShow();

    // Get data
    this.getResultsTable(this.scenarioID, this.tableToShow);
    this.getResultsPlot(this.scenarioID, this.currentFormValue);


  }

  // // Subscribe to the resultsToShow BehaviorSubject, which tells us which
  // // results table the user is requesting
  // getResultsToShow(): void {
  //   this.scenarioResultsService.resultsToViewSubject
  //     .subscribe((resultsToShow: string) => {
  //       this.tableToShow = resultsToShow;
  //     });
  // }

  // When a results button is pressed, change the value of resultsToShow to
  // that of the respective results table and refresh the view

  makeResultsTableButtons(): void {
    this.scenarioResultsService.getResultsIncludedTables()
      .subscribe(includedTables => {
        this.allResultsButtons = includedTables;
      });
  }

  showTable(tableToShow): void {
    // Set the values needed for ngOnInit
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

  // Plots
  getFormOptions(scenarioID): void {
    this.scenarioResultsService.getOptions(scenarioID).subscribe(options => {
      this.formOptions = options;
    });
  }

  makeResultsPlotForms(scenarioID): void {
    this.scenarioResultsService.getResultsIncludedPlots(scenarioID)
      .subscribe(includedPlots => {
        for (const plot of includedPlots) {
          const form = this.formBuilder.group({
            plotType: plot.plotType,
            caption: plot.caption,
            loadZone: plot.loadZone,
            period: plot.period,
            horizon: plot.horizon,
            timepoint: plot.timepoint,
            stage: plot.stage,
            project: plot.project,
            yMax: null
          });
          this.allFormGroups.push(form);
        }
      });
  }

  showPlot(formGroup): void {
    // We need to set the currentFormValue and plotHTMLTarget before
    // calling ngOnInit
    this.currentFormValue = formGroup;

    const plotType = formGroup.value.plotType;
    const loadZone = formGroup.value.loadZone;
    const period = formGroup.value.period;
    const horizon = formGroup.value.horizon;
    const timepoint = formGroup.value.timepoint;
    const stage = formGroup.value.stage;
    const project = formGroup.value.project;
    let yMax = formGroup.value.yMax;
    if (yMax === null) { yMax = 'default'; }

    this.scenarioResultsService.getResultsPlot(
      this.scenarioID, plotType, loadZone, period, horizon, timepoint, stage, project, yMax
    ).subscribe(resultsPlot => {
        this.plotHTMLTarget = resultsPlot.plotJSON['target_id'];
        this.resultsToShow = resultsPlot.plotJSON['target_id'];
        this.ngOnInit();
      });
  }

  getResultsPlot(scenarioID, formGroup): void {
    console.log(formGroup.value);

    const plotType = formGroup.value.plotType;
    const loadZone = formGroup.value.loadZone;
    const period = formGroup.value.period;
    const horizon = formGroup.value.horizon;
    const timepoint = formGroup.value.timepoint;
    const stage = formGroup.value.stage;
    const project = formGroup.value.project;
    let yMax = formGroup.value.yMax;
    if (yMax === null) { yMax = 'default'; }

    this.scenarioResultsService.getResultsPlot(
      scenarioID, plotType, loadZone, period, horizon, timepoint, stage, project, yMax
    ).subscribe(resultsPlot => {
        this.resultsPlot = resultsPlot.plotJSON;
        Bokeh.embed.embed_item(this.resultsPlot);
      });
  }

  clearPlots(): void {
    this.resultsToShow = null;
    this.ngOnInit();
  }

  goBack(): void {
    this.location.back();
    // The the resultsToView to '', so that we start with no tables visible
    // when we visit the results page again
    this.scenarioResultsService.changeResultsToView('');
  }

}
