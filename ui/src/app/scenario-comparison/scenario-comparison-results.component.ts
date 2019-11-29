import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-scenario-comparison-results',
  templateUrl: './scenario-comparison-results.component.html',
  styleUrls: ['./scenario-comparison-results.component.css']
})
export class ScenarioComparisonResultsComponent implements OnInit {

  baseScenarioID: number;
  scenariosIDsToCompare: number[];

  // TODO: make a type for the form values
  formValues: {};

  basePlotHTMLTarget: string;
  comparePlotsHTMLTargets: string[];

  constructor(
    private location: Location,
    private router: Router,
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

    console.log(this.baseScenarioID);
    console.log(this.scenariosIDsToCompare);
    console.log(this.formValues);
  }

  goBack(): void {
    this.location.back();
  }

}
