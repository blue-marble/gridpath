import { Component, OnInit } from '@angular/core';
import { Scenario } from '../scenario';
import { SCENARIOS } from '../mock-scenarios';

@Component({
  selector: 'app-scenarios',
  templateUrl: './scenarios.component.html',
  styleUrls: ['./scenarios.component.css']
})
export class ScenariosComponent implements OnInit {

  scenarios = SCENARIOS;

  selectedScenario: Scenario;

  constructor() { }

  ngOnInit() {
  }

  onSelect(scenario: Scenario): void {
    this.selectedScenario = scenario;
  }

}


