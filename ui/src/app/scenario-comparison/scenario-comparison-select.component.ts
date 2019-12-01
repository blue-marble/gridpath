import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { NavigationExtras, Router } from '@angular/router';
import { FormControl, FormGroup, FormBuilder, FormArray } from '@angular/forms';

import { ScenariosService } from '../scenarios/scenarios.service';
import { ScenarioResultsService } from '../scenario-results/scenario-results.service';
import {ResultsOptions} from '../scenario-results/scenario-results';

@Component({
  selector: 'app-scenario-comparison-select',
  templateUrl: './scenario-comparison-select.component.html',
  styleUrls: ['./scenario-comparison-select.component.css']
})
export class ScenarioComparisonSelectComponent implements OnInit {

  scenariosToCompareForm: FormGroup;
  startingValues: {
    baseScenarioStartingValue: number,
    scenariosToCompareStartingValues: number[]
  };
  allScenarios: {id: number, name: string}[];

  // Will be used to decide which plot options to show
  baseScenario: number;
  scenariosToCompare: number[];

  showResultsButtons: boolean;
  // Results table buttons
  allTableButtons: {table: string, caption: string}[];
  // Results plot forms
  allPlotFormGroups: FormGroup[];
  // The possible options for the forms
  formOptions: ResultsOptions;

  constructor(
    private location: Location,
    private router: Router,
    private formBuilder: FormBuilder,
    private scenariosService: ScenariosService,
    private scenarioResultsService: ScenarioResultsService
  ) {

    // Create the scenario selection form
    // Note that the individual form controls for scenarios to compare are
    // created in getScenarios()
    // Starting values are also set in getScenarios()
    this.scenariosToCompareForm = this.formBuilder.group({
      baseScenario: new FormControl(),
      scenariosToCompare: new FormArray([])
    });

    // Get starting values for scenario selection from history
    const navigation = this.router.getCurrentNavigation();
    const state = navigation.extras.state as {
      startingValues: {
        baseScenarioStartingValue: null,
        scenariosToCompareStartingValues: []
      }
    };
    // Set to history, only if history is not 'undefined'
    if (history.state.startingValues) {
      this.startingValues = history.state.startingValues;
    } else {
      this.startingValues = {
        baseScenarioStartingValue: null,
        scenariosToCompareStartingValues: []
      };
    }

    // Make the scenarios table (and selection form)
    this.allScenarios = [];
    this.getScenarios();

    this.showResultsButtons = false;
  }

  ngOnInit() {
    this.allTableButtons = [];
    this.makeResultsTableButtons();
    this.getFormOptions(this.baseScenario);
    this.allPlotFormGroups = [];
    this.makeResultsPlotForms();
  }

  getScenarios(): void {
    this.scenariosService.getScenarios()
      .subscribe(scenarios => {

        // Get the scenarios
        for (const scenario of scenarios) {
          this.allScenarios.push(
            {id: scenario.id, name: scenario.name}
          );
        }

        // Set base scenario selection starting value
        this.scenariosToCompareForm.controls.baseScenario.setValue(
          this.startingValues.baseScenarioStartingValue, {onlySelf: true}
        );

        // Add form controls for each scenario in the FormArray
        // Set starting values (if any)
        this.allScenarios.map((object, index) => {
          if (this.startingValues.scenariosToCompareStartingValues.includes(object.id)) {
            (this.scenariosToCompareForm.controls.scenariosToCompare as FormArray).push(
              new FormControl([true])
            );
          } else {
            (this.scenariosToCompareForm.controls.scenariosToCompare as FormArray).push(
              new FormControl());
          }
        });
    });
  }

  compareScenarioInputs(): void {
    const selectedScenarioIDs = this.scenariosToCompareForm.value.scenariosToCompare
      .map((v, i) => v ? this.allScenarios[i].id : null)
      .filter(v => v !== null);
    const baseScenarioIDToCompare = this.scenariosToCompareForm.value.baseScenario;
    console.log('Base: ', baseScenarioIDToCompare);
    console.log('Compare: ', selectedScenarioIDs);

    // Switch to the scenario-comparison-inputs view with the given base
    // scenario and list of scenarios to compare
    const navigationExtras: NavigationExtras = {
      state: {
        baseScenarioID: baseScenarioIDToCompare,
        scenariosIDsToCompare: selectedScenarioIDs
      }
    };
    this.router.navigate(
      ['/scenario-comparison/inputs'], navigationExtras
    );
  }

  makeResultsTableButtons(): void {
    this.scenarioResultsService.getResultsIncludedTables()
      .subscribe(includedTables => {
        this.allTableButtons = includedTables;
      });
  }

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

  compareScenarioResults(): void {
    console.log('Comparing scenario results');

    this.showResultsButtons = true;

    // TODO: refactor to consolidate with inputs?
    this.baseScenario = this.scenariosToCompareForm.value.baseScenario;
    this.scenariosToCompare = this.scenariosToCompareForm.value.scenariosToCompare
      .map((v, i) => v ? this.allScenarios[i].id : null)
      .filter(v => v !== null);
    console.log('Base: ', this.baseScenario);
    console.log('Compare: ', this.scenariosToCompare);

    this.ngOnInit();
  }

  showResultsPlots(formGroup): void {
    // Get selected plot options
    const formValues = this.getFormGroupValues(formGroup);
    console.log('Form values: ', formValues);

    // Switch to the scenario-comparison-inputs view with the given base
    // scenario and list of scenarios to compare
    const navigationExtras: NavigationExtras = {
      state: {
        baseScenarioID: this.baseScenario,
        scenariosIDsToCompare: this.scenariosToCompare,
        formValuesToPass: formValues,
        resultType: 'plot'
      }
    };
    this.router.navigate(
      ['/scenario-comparison/results'], navigationExtras
    );
  }

  // TODO: refactor to consolidate with scenario-results.component.ts?
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

  showResultsTable(table): void {
    // Switch to the scenario-comparison-inputs view with the given base
    // scenario and list of scenarios to compare
    const navigationExtras: NavigationExtras = {
      state: {
        baseScenarioID: this.baseScenario,
        scenariosIDsToCompare: this.scenariosToCompare,
        tableToShow: table,
        resultType: 'table'
      }
    };
    this.router.navigate(
      ['/scenario-comparison/results'], navigationExtras
    );
  }

  goBack(): void {
    this.location.back();
  }

  reset(): void {
    this.showResultsButtons = false;
    this.ngOnInit();
  }
}
