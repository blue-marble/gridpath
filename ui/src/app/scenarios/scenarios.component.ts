import { Component, OnInit } from '@angular/core';
import { Scenario } from './scenario';
import { ScenariosService} from './scenarios.service';

import { ScenarioEditService } from '../scenario-detail/scenario-edit.service';
import { emptyStartingValues } from '../scenario-new/scenario-new.component';

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

    // TODO: this should happen on navigating away from scenario-new
    this.scenarioEditService.changeStartingScenario(emptyStartingValues);

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
