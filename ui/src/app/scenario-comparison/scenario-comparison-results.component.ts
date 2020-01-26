import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import {NavigationExtras, Router} from '@angular/router';

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

  resultType: string;

  // Table comparison
  tableToShow: string;
  tableColumns: string[];
  allRowsData: [];

  // Plots comparison
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
    commitProject: string,
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
    this.tableToShow = history.state.tableToShow;
    this.resultType = history.state.resultType;

    // Create the comparison table to show
    this.allRowsData = [];
    this.getComparisonTableData();

    // Embed the plots to compare
    this.embedBasePlot();
    this.comparePlotsHTMLTargets = [];
    this.comparePlotsJSON = [];
    this.embedComparePlots();
  }

  getComparisonTableData(): void {
    this.scenarioResultsService.getResultsTable(
      this.baseScenarioID, this.tableToShow
    ).subscribe(resultsTable => {
      this.tableColumns = resultsTable.columns;
      this.allRowsData.push.apply(this.allRowsData, resultsTable.rowsData);
    });

    for (const scenarioIDTOCompare of this.scenariosIDsToCompare) {
      this.scenarioResultsService.getResultsTable(
        scenarioIDTOCompare, this.tableToShow
      ).subscribe(resultsTable => {
        this.allRowsData.push.apply(this.allRowsData, resultsTable.rowsData);
      });
    }
  }

  embedBasePlot(): void {
    this.scenarioResultsService.getResultsPlot(
        this.baseScenarioID, this.formValues.plotType, this.formValues.loadZone,
          this.formValues.rpsZone, this.formValues.carbonCapZone, this.formValues.period,
          this.formValues.horizon, this.formValues.subproblem, this.formValues.stage,
          this.formValues.project, this.formValues.commitProject, this.formValues.yMax
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
          this.formValues.project, this.formValues.commitProject, this.formValues.yMax
      ).subscribe(resultsPlot => {
        this.comparePlotsHTMLTargets.push(resultsPlot.plotJSON.target_id);
        this.comparePlotsJSON.push(resultsPlot.plotJSON);
        Bokeh.embed.embed_item(resultsPlot.plotJSON);
      });
    }
  }

  goBack(): void {
    const navigationExtras: NavigationExtras = {
      state: {
        startingValues: {
          baseScenarioStartingValue: this.baseScenarioID,
          scenariosToCompareStartingValues: this.scenariosIDsToCompare,
          showResultsButtonsStartingValue: true
        }
      }
    };

    this.router.navigate(['scenario-comparison/select'], navigationExtras);
  }

}
