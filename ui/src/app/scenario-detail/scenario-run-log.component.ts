import {Component, OnInit, OnDestroy} from '@angular/core';
import {Location} from '@angular/common';

const fs = ( window as any ).require('fs');

@Component({
  selector: 'app-scenario-run-log',
  templateUrl: './scenario-run-log.component.html',
  styleUrls: ['./scenario-run-log.component.css']
})


export class ScenarioRunLogComponent implements OnInit, OnDestroy {

  scenarioLog: string;
  refreshLog: any;

  constructor(
    private location: Location
  ) { }

  ngOnInit() {
    this.scenarioLog = fs.readFileSync('/Users/ana/dev/gridpath_dev/scenarios/blah/test_log.log', 'utf8');

    this.refreshLog = setInterval(() => {
        this.scenarioLog = fs.readFileSync('/Users/ana/dev/gridpath_dev/scenarios/blah/test_log.log', 'utf8');;
    }, 5000);
  }

  ngOnDestroy() {
    // Clear scenario detail refresh intervals (stop refreshing) on component
    // destroy
    clearInterval(this.refreshLog);
  }

  goBack(): void {
    this.location.back();
  }

}
