import {Component, OnInit, OnDestroy} from '@angular/core';
import {ScenariosService} from './scenarios.service';
import {Router} from '@angular/router';


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

export class ScenariosComponent implements OnInit, OnDestroy {

  scenarios: Scenario[];
  refreshScenarios: any;

  constructor(
    private scenariosService: ScenariosService,
    private router: Router
  ) {
    console.log('Constructing scenarios...');
  }

  ngOnInit() {
    console.log('Initializing scenarios...');
    this.getScenarios();
    this.refreshScenarios = setInterval(() => {
        this.getScenarios();
    }, 5000);
  }

  ngOnDestroy() {
    // Clear view refresh intervals (stop refreshing) on component destroy
    clearInterval(this.refreshScenarios);
  }

  getScenarios(): void {
    console.log('Getting scenarios...');
    this.scenariosService.getScenarios()
      .subscribe(scenarios => this.scenarios = scenarios);
  }

  updateScenarios(): void {
    console.log('Updating scenarios...');
    this.getScenarios();
  }

  navigateToScenario(scenario): void {
    this.router.navigate(['/scenario/', scenario]);
  }

}
