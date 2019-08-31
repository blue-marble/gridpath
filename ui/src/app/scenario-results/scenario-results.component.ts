import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import {
  FormControl,
  FormGroup,
  FormBuilder,
  ControlContainer,
  Form
} from '@angular/forms';

import { ScenarioResultsService } from './scenario-results.service';
import {
  ScenarioResults,
  ResultsForm,
  PlotAPI
} from './scenario-results';

const Bokeh = ( window as any ).require('bokehjs');


@Component({
  selector: 'app-sub-form',
  template: `
    <ng-container [formGroup]="controlContainer.control">
      <input type=text formControlName=foo>
      <input type=text formControlName=bar>
    </ng-container>
  `,
})
export class SubFormComponent {
  constructor(public controlContainer: ControlContainer) {
  }
}

@Component({
  selector: 'app-scenario-results',
  templateUrl: './scenario-results.component.html',
  styleUrls: ['./scenario-results.component.css']
})
export class ScenarioResultsComponent implements OnInit {

  formGroups: FormGroup[];

  // Key for which results table to show
  resultsToShow: string;

  // All results buttons
  allResultsButtons: {ngIfKey: string, caption: string}[];
  // All results forms
  allResultsForms: ResultsForm[];

  // Results tables
  includedTables: {name: string; caption: string}[];
  resultsTable: ScenarioResults;

  // Results plots
  resultsPlot: PlotAPI;

  // Plots
  // Dispatch plot (form with plot options, JSON object, and plot name)
  dispatchPlotOptionsForm = new FormGroup({
    dispatchPlotLoadZone: new FormControl(),
    dispatchPlotHorizon: new FormControl(),
    dispatchPlotYMax: new FormControl()
  });
  dispatchPlotJSON: object;
  dispatchPlotHTMLName: string;

  // Capacity plots (form with plot options, JSON object, and plot name)
  capacityNewPlotOptionsForm = new FormGroup({
    capacityNewPlotLoadZone: new FormControl(),
    capacityNewPlotYMax: new FormControl()
  });
  capacityNewPlotJSON: object;
  capacityNewPlotHTMLName: string;

  capacityRetiredPlotOptionsForm = new FormGroup({
    capacityRetiredPlotLoadZone: new FormControl(),
    capacityRetiredPlotYMax: new FormControl()
  });
  capacityRetiredPlotJSON: object;
  capacityRetiredPlotHTMLName: string;

  capacityTotalPlotOptionsForm = new FormGroup({
    capacityTotalPlotLoadZone: new FormControl(),
    capacityTotalPlotYMax: new FormControl()
  });
  capacityTotalPlotJSON: object;
  capacityTotalPlotHTMLName: string;

  // Energy plot
  energyPlotOptionsForm = new FormGroup({
    energyPlotLoadZone: new FormControl(),
    energyPlotStage: new FormControl(),
    energyPlotYMax: new FormControl()
  });
  energyPlotJSON: object;
  energyPlotHTMLName: string;

  // Cost plot
  costPlotOptionsForm = new FormGroup({
    costPlotLoadZone: new FormControl(),
    costPlotStage: new FormControl(),
    costPlotYMax: new FormControl()
  });
  costPlotJSON: object;
  costPlotHTMLName: string;

  // Capacity factor plot
  capacityFactorPlotOptionsForm = new FormGroup({
    capacityFactorPlotLoadZone: new FormControl(),
    capacityFactorPlotStage: new FormControl(),
    capacityFactorPlotYMax: new FormControl()
  });
  capacityFactorPlotJSON: object;
  capacityFactorPlotHTMLName: string;

  // To get the right route
  scenarioID: number;
  private sub: any;

  constructor(
    private route: ActivatedRoute,
    private scenarioResultsService: ScenarioResultsService,
    private location: Location,
    private fb: FormBuilder

  ) { }

  ngOnInit() {
    console.log('Initializing with results to show', this.resultsToShow);

    this.formGroups = [];
    this.createFormGroups();

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

  getResultsDispatchPlot(scenarioID): void {
    // Get the plot options
    const loadZone = this.dispatchPlotOptionsForm.value.dispatchPlotLoadZone;
    const horizon = this.dispatchPlotOptionsForm.value.dispatchPlotHorizon;
    let yMax = this.dispatchPlotOptionsForm.value.dispatchPlotYMax;
    if (yMax === null) { yMax = 'default'; }

    // Change the plot name for the HTML
    this.dispatchPlotHTMLName = `dispatchPlot-${loadZone}-${horizon}`;

    // Get the JSON object, convert to plot, and embed (the target of the
    // JSON object will match the HTML name above)
    this.scenarioResultsService.getResultsDispatchPlot(
      scenarioID, loadZone, horizon, yMax
    ).subscribe(dispatchPlotAPI => {
        this.dispatchPlotJSON = dispatchPlotAPI.plotJSON;
        Bokeh.embed.embed_item(this.dispatchPlotJSON);
      });
  }

  getResultsCapacityNewPlot(scenarioID): void {
    // Get the plot options
    const loadZone = this.capacityNewPlotOptionsForm.value.capacityNewPlotLoadZone;

    // Change the plot name for the HTML
    this.capacityNewPlotHTMLName = `newCapacityPlot-${loadZone}`;
    let yMax = this.capacityNewPlotOptionsForm.value.capacityNewPlotYMax;
    if (yMax === null) { yMax = 'default'; }

    // Get the JSON object, convert to plot, and embed (the target of the
    // JSON object will match the HTML name above)
    this.scenarioResultsService.getResultsCapacityNewPlot(
      scenarioID, loadZone, yMax
    ).subscribe(plotAPI => {
        this.capacityNewPlotJSON = plotAPI.plotJSON;
        Bokeh.embed.embed_item(this.capacityNewPlotJSON);
      });
  }

  getResultsCapacityRetiredPlot(scenarioID): void {
    // Get the plot options
    const loadZone = this.capacityRetiredPlotOptionsForm.value.capacityRetiredPlotLoadZone;
    let yMax = this.capacityRetiredPlotOptionsForm.value.capacityRetiredPlotYMax;
    if (yMax === null) { yMax = 'default'; }

    // Change the plot name for the HTML
    this.capacityRetiredPlotHTMLName = `retiredCapacityPlot-${loadZone}`;

    // Get the JSON object, convert to plot, and embed (the target of the
    // JSON object will match the HTML name above)
    this.scenarioResultsService.getResultsCapacityRetiredPlot(
      scenarioID, loadZone, yMax
    ).subscribe(plotAPI => {
        this.capacityRetiredPlotJSON = plotAPI.plotJSON;
        Bokeh.embed.embed_item(this.capacityRetiredPlotJSON);
      });
  }

  getResultsCapacityTotalPlot(scenarioID): void {
    // Get the plot options
    const loadZone = this.capacityTotalPlotOptionsForm.value.capacityTotalPlotLoadZone;
    let yMax = this.capacityTotalPlotOptionsForm.value.capacityTotalPlotYMax;
    if (yMax === null) { yMax = 'default'; }

    // Change the plot name for the HTML
    this.capacityTotalPlotHTMLName = `allCapacityPlot-${loadZone}`;

    // Get the JSON object, convert to plot, and embed (the target of the
    // JSON object will match the HTML name above)
    this.scenarioResultsService.getResultsCapacityTotalPlot(
      scenarioID, loadZone, yMax
    ).subscribe(plotAPI => {
        this.capacityTotalPlotJSON = plotAPI.plotJSON;
        Bokeh.embed.embed_item(this.capacityTotalPlotJSON);
      });
  }

  getResultsEnergyPlot(scenarioID): void {
    // Get the plot options
    const loadZone = this.energyPlotOptionsForm.value.energyPlotLoadZone;
    const stage = this.energyPlotOptionsForm.value.energyPlotStage;
    let yMax = this.energyPlotOptionsForm.value.energyPlotYMax;
    if (yMax === null) { yMax = 'default'; }

    // Change the plot name for the HTML
    // TODO: make name 'energyPlot' in python file and here
    this.energyPlotHTMLName = `EnergyPlot-${loadZone}-${stage}`;

    // Get the JSON object, convert to plot, and embed (the target of the
    // JSON object will match the HTML name above)
    this.scenarioResultsService.getResultsEnergyPlot(
      scenarioID, loadZone, stage, yMax
    ).subscribe(energyPlotAPI => {
        this.energyPlotJSON = energyPlotAPI.plotJSON;
        Bokeh.embed.embed_item(this.energyPlotJSON);
      });
  }

  getResultsCostPlot(scenarioID): void {
    // Get the plot options
    const loadZone = this.costPlotOptionsForm.value.costPlotLoadZone;
    const stage = this.costPlotOptionsForm.value.costPlotStage;
    let yMax = this.costPlotOptionsForm.value.costPlotYMax;
    if (yMax === null) { yMax = 'default'; }

    // Change the plot name for the HTML
    // TODO: make name 'costPlot' in python file and here?
    this.costPlotHTMLName = `CostPlot-${loadZone}-${stage}`;

    // Get the JSON object, convert to plot, and embed (the target of the
    // JSON object will match the HTML name above)
    this.scenarioResultsService.getResultsCostPlot(
      scenarioID, loadZone, stage, yMax
    ).subscribe(costPlotAPI => {
        this.costPlotJSON = costPlotAPI.plotJSON;
        Bokeh.embed.embed_item(this.costPlotJSON);
      });
  }

  getResultsCapacityFactorPlot(scenarioID): void {
    // Get the plot options
    const loadZone = this.capacityFactorPlotOptionsForm.value.capacityFactorPlotLoadZone;
    const stage = this.capacityFactorPlotOptionsForm.value.capacityFactorPlotStage;
    let yMax = this.capacityFactorPlotOptionsForm.value.capacityFactorPlotYMax;
    if (yMax === null) { yMax = 'default'; }

    // Change the plot name for the HTML
    // TODO: make name 'capFactorPlot' in python file and here?
    this.capacityFactorPlotHTMLName = `CapFactorPlot-${loadZone}-${stage}`;

    // Get the JSON object, convert to plot, and embed (the target of the
    // JSON object will match the HTML name above)
    this.scenarioResultsService.getResultsCapacityFactorPlot(
      scenarioID, loadZone, stage, yMax
    ).subscribe(capacityFactorPlotAPI => {
        this.capacityFactorPlotJSON = capacityFactorPlotAPI.plotJSON;
        Bokeh.embed.embed_item(this.capacityFactorPlotJSON);
      });
  }

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
    this.scenarioResultsService.getResultsIncludedPlots(scenarioID).subscribe(
      resultsForms => {
        const dispatchPlotFormStructure = {
          formGroup: this.dispatchPlotOptionsForm,
          selectForms: resultsForms['dispatchPlotOptionsForm']['resultsForms'],
          yMaxFormControlName: resultsForms['dispatchPlotOptionsForm']['dispatchPlotYMax'],
          button: resultsForms['dispatchPlotOptionsForm']['button']
        };
        this.allResultsForms.push(dispatchPlotFormStructure);
      }
    );
  }

  createFormGroups(): void {
    for (const blah of [1, 2]) {
      const form = this.fb.group({
        group: this.fb.group({
          foo: 'oof',
          bar: 'bar',
        }),
        baz: 'baz',
      });
      this.formGroups.push(form);
    }
  }

  goBack(): void {
    this.location.back();
    // The the resultsToView to '', so that we start with no tables visible
    // when we visit the results page again
    this.scenarioResultsService.changeResultsToView('');
  }

}
