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

  allScenarios: {id: number, name: string}[];

  form: FormGroup;
  orders = [
    { id: 100, name: 'order 1' },
    { id: 200, name: 'order 2' },
    { id: 300, name: 'order 3' },
    { id: 400, name: 'order 4' }
  ];

  baseScenarioForm: FormGroup;
  scenariosToCompareForm: FormGroup;
  scenarios: {id: number, name: string}[];

  constructor(
    private location: Location,
    private router: Router,
    private formBuilder: FormBuilder,
    private scenariosService: ScenariosService
  ) {

    // this.baseScenarioForm = this.formBuilder.group({
    //   scenariosListRadio: new FormArray([])
    // });
    //
    // this.getScenarios();

    this.form = this.formBuilder.group({
      orders: new FormArray([])
    });

    // this.baseScenarioForm = this.formBuilder.group({
    //   scenarios: new FormArray([])
    // });
    this.scenariosToCompareForm = this.formBuilder.group({
      scenarios: new FormArray([]),
      baseScenario: new FormControl()
    });

    // this.addCheckboxes();
    this.scenarios = [];
    this.getScenarios();
  }

  ngOnInit() {

    // this.allScenarios = [];

  }

  getScenarios(): void {
    this.scenariosService.getScenarios()
      .subscribe(scenarios => {

        for (const scenario of scenarios) {
          this.scenarios.push(
            {id: scenario.id, name: scenario.name}
          );
        }

        this.scenarios.map((o, i) => {
          const controlCompare = new FormControl();
          (this.scenariosToCompareForm.controls.scenarios as FormArray).push(controlCompare);
        });
    });
  }

  // private addCheckboxes() {
  //   this.orders.map((o, i) => {
  //     const control = new FormControl(i === 0); // if first item set to true, else false
  //     (this.form.controls.orders as FormArray).push(control);
  //   });
  // }
  //
  // private addScenarioCheckboxes() {
  //   this.scenarios.map((o, i) => {
  //     const control = new FormControl(i === 0); // if first item set to true, else false
  //     (this.scenariosToCompareForm.controls.scenarios as FormArray).push(control);
  //   });
  // }

  submit() {
    const selectedOrderIds = this.form.value.orders
      .map((v, i) => v ? this.orders[i].id : null)
      .filter(v => v !== null);
    console.log(selectedOrderIds);
  }

  compareScenarioInputs(): void {
    const selectedScenarioIDs = this.scenariosToCompareForm.value.scenarios
      .map((v, i) => v ? this.scenarios[i].id : null)
      .filter(v => v !== null);
    const baseScenarioIDToCompare = this.scenariosToCompareForm.value.baseScenario;
    console.log(selectedScenarioIDs);
    console.log('Base ', baseScenarioIDToCompare);

    // Switch to the scenario-comparison view with the given base scenario
    // and list of scenarios to compare
    const navigationExtras: NavigationExtras = {
      state: {
        baseScenarioID: baseScenarioIDToCompare,
        scenariosIDsToCompare: selectedScenarioIDs
      }
    };
    this.router.navigate(['/scenario-comparison'], navigationExtras);
  }

  compareScenarioResults(): void {

  }

  goBack(): void {
    this.location.back();
  }
}
