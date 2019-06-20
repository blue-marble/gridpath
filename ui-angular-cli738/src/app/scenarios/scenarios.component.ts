import { Component, OnInit } from '@angular/core';
import { Scenario } from './scenario';
import { ScenariosService} from "./scenarios.service";

@Component({
  selector: 'app-scenarios',
  templateUrl: './scenarios.component.html',
  styleUrls: ['./scenarios.component.css']
})
export class ScenariosComponent implements OnInit {

  scenarios: Scenario[];
  selectedScenario: Scenario;

  constructor(private scenariosService: ScenariosService) { }

  ngOnInit() {
    this.getScenarios()
  }

  onSelect(scenario: Scenario): void {
    this.selectedScenario = scenario;
  }

  getScenarios(): void {
    this.scenariosService.getScenarios()
      .subscribe(scenarios => this.scenarios = scenarios);
    }

}


