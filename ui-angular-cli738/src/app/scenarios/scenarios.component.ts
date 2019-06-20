import { Component, OnInit, NgZone } from '@angular/core';
import { Scenario } from '../scenario';

const electron = (<any>window).require('electron');

@Component({
  selector: 'app-scenarios',
  templateUrl: './scenarios.component.html',
  styleUrls: ['./scenarios.component.css']
})
export class ScenariosComponent implements OnInit {


  scenarios: Scenario[];
  selectedScenario: Scenario;

  // https://stackoverflow.com/questions/41254904/angular-2-change-detection-breaks-down-with-electron
  // Must run with zone: NgZone
  constructor(private zone: NgZone) {
    electron.ipcRenderer.send('get-scenarios');
    electron.ipcRenderer.on('get-scenarios-reply', (event, scenariosList) => {
			console.log(scenariosList);
			zone.run(() => {this.scenarios = scenariosList})
		});
    console.log(this.scenarios)
  }


  ngOnInit() {
  }

  onSelect(scenario: Scenario): void {
    this.selectedScenario = scenario;
  }

}


