import {Component, OnInit} from '@angular/core';
import {ScenariosService} from './scenarios.service';

import {ScenarioEditService} from '../scenario-detail/scenario-edit.service';
import {emptyStartingValues} from '../scenario-new/scenario-new.component';

export class Scenario {
  id: number;
  name: string;
  validationStatus: string;
  runStatus: string;
}

@Component({
  selector: 'app-scenarios',
  templateUrl: './scenarios.component.html',
  styleUrls: ['./scenarios.component.css']
})

export class ScenariosComponent implements OnInit {

  scenarios: Scenario[];

  constructor(
    private scenariosService: ScenariosService,
    private scenarioEditService: ScenarioEditService
  ) {
    console.log('Constructing scenarios...');
  }

  ngOnInit() {
    console.log('Initializing scenarios...');
    this.getScenarios();
  }

  getScenarios(): void {
    console.log('Getting scenarios...');
    this.scenariosService.getScenarios()
      .subscribe(scenarios => this.scenarios = scenarios);
  }

  updateScenarios(event): void {
    console.log('Updating scenarios...');
    this.getScenarios();
  }

}
