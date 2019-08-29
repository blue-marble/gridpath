import {Component, OnInit} from '@angular/core';
import {ScenariosService} from './scenarios.service';


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
