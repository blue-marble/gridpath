import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { NavigationExtras, Router } from '@angular/router';
import { FormControl, FormGroup, FormBuilder, FormArray } from '@angular/forms';

const electron = ( window as any ).require('electron');

import { ScenariosService } from '../scenarios/scenarios.service';
import { ScenarioResultsService } from '../scenario-results/scenario-results.service';
import { ResultsOptions } from '../scenario-results/scenario-results';
import { getFormGroupValues } from '../scenario-results/scenario-results.component';
import { socketConnect } from '../app.component';

@Component({
  selector: 'app-scenario-comparison-select',
  templateUrl: './scenario-comparison-select.component.html',
  styleUrls: ['./scenario-comparison-select.component.css']
})
export class ScenarioComparisonSelectComponent implements OnInit {

  scenariosToCompareForm: FormGroup;
  startingValues: {
    baseScenarioStartingValue: number,
    scenariosToCompareStartingValues: number[],
    showResultsButtonsStartingValue: boolean
  };
  allScenarios: {
    id: number,
    name: string,
    validationStatus: string,
    runStatus: string
  }[];

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
    // Set to history, only if history starting values state is not 'undefined'
    // Otherwise, assume no base scenario and scenarios to compare are selected
    // and show the 'selection' view (no results buttons)
    if (history.state.startingValues) {
      this.startingValues = history.state.startingValues;
    } else {
      this.startingValues = {
        baseScenarioStartingValue: null,
        scenariosToCompareStartingValues: [],
        showResultsButtonsStartingValue: false
      };
    }
    // Set component params to starting values we determined based on history
    this.baseScenario = this.startingValues.baseScenarioStartingValue;
    this.scenariosToCompare = this.startingValues.scenariosToCompareStartingValues;
    this.showResultsButtons = this.startingValues.showResultsButtonsStartingValue;

    // Make the scenarios table (and selection form)
    this.allScenarios = [];
    this.getScenarios();
  }

  ngOnInit() {
    console.log('Starting values: ', this.startingValues);
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
            { id: scenario.id,
              name: scenario.name,
              validationStatus: scenario.validationStatus,
              runStatus: scenario.runStatus }
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
    const selectedValues = this.getScenarioSelectionFormValues();
    const baseScenarioIDToCompare = selectedValues.baseScenarioSelected;
    const selectedScenarioIDs = selectedValues.scenariosToCompareSelected;
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

    const selectedValues = this.getScenarioSelectionFormValues();

    this.baseScenario = selectedValues.baseScenarioSelected;
    this.scenariosToCompare = selectedValues.scenariosToCompareSelected;
    console.log('Base: ', this.baseScenario);
    console.log('Compare: ', this.scenariosToCompare);

    this.ngOnInit();
  }

  getScenarioSelectionFormValues() {
    const baseScenario = this.scenariosToCompareForm.value.baseScenario;
    const scenariosToCompare = this.scenariosToCompareForm.value.scenariosToCompare
      .map((v, i) => v ? this.allScenarios[i].id : null)
        .filter(v => v !== null);

    return {
      baseScenarioSelected: baseScenario,
      scenariosToCompareSelected: scenariosToCompare
    };
  }

  showResultsPlots(formGroup): void {
    // Get selected plot options
    const formValues = getFormGroupValues(formGroup);
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

  downloadTableData(table): void {
    electron.remote.dialog.showSaveDialog(
        { title: 'untitled.csv', defaultPath: 'table.csv',
          filters: [{extensions: ['csv']}]
        }, (targetPath) => {
          const socket = socketConnect();

          const tableActual = table.replace(/-/g, '_');

          socket.emit(
              'save_table_data',
              { downloadPath: targetPath,
                tableName: tableActual,
                scenarioID: this.baseScenario,
                otherScenarios: this.scenariosToCompare,
                tableType: 'result',
                uiTableNameInDB: null,
                uiRowNameInDB: null
              }
          );
        }
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
