import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { Router } from '@angular/router';

import { ScenarioResultsService } from '../scenario-results/scenario-results.service';

const Bokeh = ( window as any ).require('bokehjs');


@Component({
  selector: 'app-scenario-comparison-results',
  templateUrl: './scenario-comparison-results.component.html',
  styleUrls: ['./scenario-comparison-results.component.css']
})
export class ScenarioComparisonResultsComponent implements OnInit {

  baseScenarioID: number;
  scenariosIDsToCompare: number[];

  // TODO: make a type for the form values
  formValues: {
    plotType: string,
    caption: string,
    loadZone: string,
    rpsZone: string,
    carbonCapZone: string,
    period: number,
    horizon: number,
    subproblem: number,
    stage: number,
    project: string,
    yMax: number
  };

  basePlotHTMLTarget: string;
  basePlotJSON: any;
  comparePlotsHTMLTargets: string[];
  comparePlotsJSON: any[];

  constructor(
    private location: Location,
    private router: Router,
    private scenarioResultsService: ScenarioResultsService
  ) {
    const navigation = this.router.getCurrentNavigation();
    const state = navigation.extras.state as {
      baseScenarioID: number,
      scenariosIDsToCompare: boolean,
      formValuesToPass: {}
    };
  }

  ngOnInit() {
    // Need to get the navigation extras from history (as the state is only
    // available during navigation); we'll use these to change the behavior
    // of the scenario name field
    this.baseScenarioID = history.state.baseScenarioID;
    this.scenariosIDsToCompare = history.state.scenariosIDsToCompare;
    this.formValues = history.state.formValuesToPass;

    this.embedBasePlot();

    this.comparePlotsHTMLTargets = [];
    this.comparePlotsJSON = [];
    this.embedComparePlots();
  }

  embedBasePlot(): void {
    this.scenarioResultsService.getResultsPlot(
        this.baseScenarioID, this.formValues.plotType, this.formValues.loadZone,
          this.formValues.rpsZone, this.formValues.carbonCapZone, this.formValues.period,
          this.formValues.horizon, this.formValues.subproblem, this.formValues.stage,
          this.formValues.project, this.formValues.yMax
      ).subscribe(resultsPlot => {
        this.basePlotHTMLTarget = resultsPlot.plotJSON.target_id;
        this.basePlotJSON = resultsPlot.plotJSON;
        Bokeh.embed.embed_item(this.basePlotJSON);
      });
  }

  embedComparePlots(): void {
    for (const scenarioIDTOCompare of this.scenariosIDsToCompare) {
      this.scenarioResultsService.getResultsPlot(
        scenarioIDTOCompare, this.formValues.plotType, this.formValues.loadZone,
          this.formValues.rpsZone, this.formValues.carbonCapZone, this.formValues.period,
          this.formValues.horizon, this.formValues.subproblem, this.formValues.stage,
          this.formValues.project, this.formValues.yMax
      ).subscribe(resultsPlot => {
        this.comparePlotsHTMLTargets.push(resultsPlot.plotJSON.target_id);
        this.comparePlotsJSON.push(resultsPlot.plotJSON);
        Bokeh.embed.embed_item(resultsPlot.plotJSON);
      });
    }
  }

  goBack(): void {
    this.location.back();
  }

}
