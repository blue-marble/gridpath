import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { FormGroup, FormBuilder } from '@angular/forms';

import { ScenarioResultsService } from './scenario-results.service';
import { ScenarioResults, ResultsForm, PlotAPI } from './scenario-results';

const Bokeh = ( window as any ).require('bokehjs');


@Component({
  selector: 'app-scenario-results',
  templateUrl: './scenario-results.component.html',
  styleUrls: ['./scenario-results.component.css']
})

export class ScenarioResultsComponent implements OnInit {

  formGroups: FormGroup[];

  // Key for which results table to show
  resultsToShow: string;

  // All results buttons (for the tables)
  allResultsButtons: {ngIfKey: string, caption: string}[];
  // All results forms (for the plots)
  allResultsForms: ResultsForm[];

  // Results tables; includedTables is used to know which buttons to show
  includedTables: {name: string; caption: string}[];
  resultsTable: ScenarioResults;

  // Results plots; includedPlots is used to know which forms to show
  includedPlots: {};
  resultsPlot: PlotAPI;

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
    console.log('Initializing with results to show', this.resultsToShow);

    this.formGroups = [];
    this.makeResultsPlotForms(this.scenarioID);

    // The ActivatedRoute service provides a params Observable which we can
    // subscribe to in order to get the route parameters
    this.sub = this.route.params.subscribe(params => {
       this.scenarioID = +params.id;
       console.log(`Scenario ID is ${this.scenarioID}`);
    });

    // Make the results buttons
    this.allResultsButtons = [];
    this.allResultsForms = [];
    this.makeResultsTableButtons();
    // this.makeResultsPlotForms(this.scenarioID);

    // Results tables
    this.includedTables = [];
    this.resultsTable = {} as ScenarioResults;

    // Get the key for which table to show
    this.getResultsToShow();

    // Get data
    this.getResultsTable(this.scenarioID, this.resultsToShow);
    // this.getResultsPlot(
    //   this.scenarioID, this.resultsPlot, this.loadZoneOption,
    //   this.periodOption, this.horizonOption, this.timepointOption,
    //   this.yMaxOption);

  }

  // Subscribe to the resultsToShow BehaviorSubject, which tells us which
  // results table the user is requesting
  getResultsToShow(): void {
    this.scenarioResultsService.resultsToViewSubject
      .subscribe((resultsToShow: string) => {
        this.resultsToShow = resultsToShow;
      });
  }

  // When a results button is pressed, change the value of resultsToShow to
  // that of the respective results table and refresh the view
  showResults(resultsToShow): void {
    // Send value for show project capacity table
    this.scenarioResultsService.changeResultsToView(resultsToShow);
    // Refresh the view
    this.ngOnInit();
  }

  // getResultsDispatchPlot(scenarioID): void {
  //   // Get the plot options
  //   const loadZone = this.dispatchPlotOptionsForm.value.dispatchPlotLoadZone;
  //   const horizon = this.dispatchPlotOptionsForm.value.dispatchPlotHorizon;
  //   let yMax = this.dispatchPlotOptionsForm.value.dispatchPlotYMax;
  //   if (yMax === null) { yMax = 'default'; }
  //
  //   // Change the plot name for the HTML
  //   this.dispatchPlotHTMLName = `dispatchPlot-${loadZone}-${horizon}`;
  //
  //   // Get the JSON object, convert to plot, and embed (the target of the
  //   // JSON object will match the HTML name above)
  //   this.scenarioResultsService.getResultsDispatchPlot(
  //     scenarioID, loadZone, horizon, yMax
  //   ).subscribe(dispatchPlotAPI => {
  //       this.dispatchPlotJSON = dispatchPlotAPI.plotJSON;
  //       Bokeh.embed.embed_item(this.dispatchPlotJSON);
  //     });
  // }

  getResultsTable(scenarioID, table): void {
    this.scenarioResultsService.getResultsTable(scenarioID, table)
      .subscribe(inputTableRows => {
        this.resultsTable = inputTableRows;
      });
  }

  makeResultsTableButtons(): void {
    this.scenarioResultsService.getResultsIncludedTables()
      .subscribe(includedTables => {
        this.allResultsButtons = includedTables;
      });
  }

  getResultsPlot(scenarioID, plot, loadZone, period, horizon, timepoint, ymax): void {
    this.scenarioResultsService.getResultsPlot(scenarioID, plot, loadZone, period, horizon, timepoint, ymax)
      .subscribe(resultsPlot => {
        this.resultsPlot = resultsPlot;
        Bokeh.embed.embed_item(this.resultsPlot);
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
            yMax: ''
          });
          this.formGroups.push(form);
        }
      });
    // for (const blah of ['dispatch', 'capacity']) {
    //   const form = this.formBuilder.group({
    //     plotType: blah,
    //     caption: '',
    //     loadZone: [],
    //     period: [],
    //     horizon: [],
    //     timepoint: 'default',
    //     stage: [],
    //     yMax: ''
    //   });
    //   this.formGroups.push(form);
    // }
  }

  testFormGroups(formGroup): void {
    console.log(formGroup.value);
  }


  goBack(): void {
    this.location.back();
    // The the resultsToView to '', so that we start with no tables visible
    // when we visit the results page again
    this.scenarioResultsService.changeResultsToView('');
  }

}
