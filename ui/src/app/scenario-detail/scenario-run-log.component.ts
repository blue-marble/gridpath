import { Component, OnInit, OnDestroy } from '@angular/core';
import {Location} from '@angular/common';

const fs = ( window as any ).require('fs');

@Component({
  selector: 'app-scenario-run-log',
  templateUrl: './scenario-run-log.component.html',
  styleUrls: ['./scenario-run-log.component.css']
})


export class ScenarioRunLogComponent implements OnInit, OnDestroy {

  logFilePath: string;
  scenarioLog: string;
  refreshLog: any;

  scrolling: boolean;
  timeout: number;

  constructor(
    private location: Location
  ) { }

  ngOnInit() {
    // Need to get the navigation extras from history (as the state is only
    // available during navigation); we'll use these to change the behavior
    // of the scenario name field
    this.logFilePath = history.state.pathToLogFile;

    console.log(this.logFilePath);

    this.scrolling = false;
    const logDiv = document.getElementById('logDiv');

    this.scenarioLog = fs.readFileSync(this.logFilePath, 'utf8');
    this.refreshLog = setInterval(() => {
      // Scroll to bottom
      // https://stackoverflow.com/questions/18614301/keep-overflow-div-scrolled-to-bottom-unless-user-scrolls-up

      const isScrolledToBottom = logDiv.scrollHeight - logDiv.clientHeight > logDiv.scrollTop;
      console.log(logDiv.scrollHeight - logDiv.clientHeight,  logDiv.scrollTop);

      // Update data
      this.scenarioLog = fs.readFileSync(
        this.logFilePath, 'utf8'
      );

      // Scroll to bottom if the user is not currently scrolling
      if (isScrolledToBottom && !this.scrolling) {
        logDiv.scrollTop = logDiv.scrollHeight - logDiv.clientHeight;
        this.scrolling = false;
      }
    }, 200);
  }

  ngOnDestroy() {
    // Clear scenario detail refresh intervals (stop refreshing) on component
    // destroy
    clearInterval(this.refreshLog);
  }

  goBack(): void {
    this.location.back();
  }

  onScroll(): void {
    this.scrolling = true;
    clearTimeout(this.timeout);
    this.timeout = setTimeout( () => {
      this.scrolling = false;
    }, 10000);
  }
}
