import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import {NavigationExtras, Router} from '@angular/router';
import {FormControl, FormGroup, FormBuilder, FormArray} from '@angular/forms';

import { ScenariosService } from '../scenarios/scenarios.service';
import { Scenario } from '../scenarios/scenarios.component';

@Component({
  selector: 'app-scenario-comparison-select',
  templateUrl: './scenario-comparison-select.component.html',
  styleUrls: ['./scenario-comparison-select.component.css']
})
export class ScenarioComparisonSelectComponent implements OnInit {

  scenariosToCompareForm: FormGroup;
  allScenarios: {id: number, name: string}[];

  constructor(
    private location: Location,
    private router: Router,
    private formBuilder: FormBuilder,
    private scenariosService: ScenariosService
  ) {

    this.scenariosToCompareForm = this.formBuilder.group({
      baseScenario: new FormControl(),
      scenariosToCompare: new FormArray([])
    });

    this.allScenarios = [];
    this.getScenarios();
  }

  ngOnInit() { }

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

    // Switch to the scenario-comparison view with the given base scenario
    // and list of scenarios to compare
    const navigationExtras: NavigationExtras = {
      state: {
        baseScenarioID: baseScenarioIDToCompare,
        scenariosIDsToCompare: selectedScenarioIDs
      }
    };
    this.router.navigate(
      ['/scenario-comparison'], navigationExtras
    );
  }

  compareScenarioResults(): void {

  }

  goBack(): void {
    this.location.back();
  }
}
