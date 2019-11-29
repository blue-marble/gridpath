import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import {NavigationExtras, Router} from '@angular/router';
import {FormControl, FormGroup, FormBuilder, FormArray} from '@angular/forms';

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
  allScenarios: {id: number, name: string}[];

  // Will be used to decide which plot options to show
  baseScenario: number;
  scenariosToCompare: number[];

  // Results plots
  showResultsButtons: boolean;
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

    this.scenariosToCompareForm = this.formBuilder.group({
      baseScenario: new FormControl(),
      scenariosToCompare: new FormArray([])
    });

    this.allScenarios = [];
    this.getScenarios();
  }

  ngOnInit() {
    this.getFormOptions(this.baseScenario);
    this.allPlotFormGroups = [];
    this.makeResultsPlotForms();
  }

  getScenarios(): void {
    this.scenariosService.getScenarios()
      .subscribe(scenarios => {

        for (const scenario of scenarios) {
          this.allScenarios.push(
            {id: scenario.id, name: scenario.name}
          );
        }

        // Add form controls for each scenario in the FormArray
        this.allScenarios.map((o, i) => {
          (this.scenariosToCompareForm.controls.scenariosToCompare as FormArray).push(
            new FormControl());
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
    // TODO: need to make sure form is disabled after compareScenarioResults
    //  is run (so that the user doesn't change the scenarios selected)

    // Get selected plot options
    const formValues = this.getFormGroupValues(formGroup);
    console.log('Form values: ', formValues);

    // Switch to the scenario-comparison-inputs view with the given base
    // scenario and list of scenarios to compare
    const navigationExtras: NavigationExtras = {
      state: {
        baseScenarioID: this.baseScenario,
        scenariosIDsToCompare: this.scenariosToCompare,
        formValuesToPass: formValues
      }
    };
    this.router.navigate(
      ['/scenario-comparison/results'], navigationExtras
    );
  }

  // TODO: refactor to consolidate with scenario-resuls.component.ts?
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

  goBack(): void {
    this.location.back();
  }
}
