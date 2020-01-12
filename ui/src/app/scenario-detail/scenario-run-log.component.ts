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

  // Will temporarily pause go-to-bottom-of-log functionality when scrolling
  scrollingFlag: boolean;
  scrollingFlagTimeout: number;

  // User can enable/disable go-to-bottom-of-log functionality
  goToBottomEnabled: boolean;

  constructor(
    private location: Location
  ) { }

  ngOnInit() {
    // Need to get the navigation extras from history (as the state is only
    // available during navigation); we'll use these to change the behavior
    // of the scenario name field
    this.logFilePath = history.state.pathToLogFile;

    this.goToBottomEnabled = true;

    this.scrollingFlag = false;
    const logDiv = document.getElementById('logDiv');

    this.scenarioLog = fs.readFileSync(this.logFilePath, 'utf8');
    this.refreshLog = setInterval(() => {
      // Automatic scroll to bottom based on:
      // https://stackoverflow.com/questions/18614301/keep-overflow-div-scrolled-to-bottom-unless-user-scrolls-up

      const isScrolledToBottom = logDiv.scrollHeight - logDiv.clientHeight > logDiv.scrollTop;
      console.log(logDiv.scrollHeight - logDiv.clientHeight,  logDiv.scrollTop);

      // Update log data
      this.scenarioLog = fs.readFileSync(
        this.logFilePath, 'utf8'
      );

      // Scroll to bottom if not currently scrolling (scrolling flag times out
      // after a certain time (whether due to user scroll or programmatic
      // scroll)
      if (isScrolledToBottom && !this.scrollingFlag && this.goToBottomEnabled) {
        logDiv.scrollTop = logDiv.scrollHeight - logDiv.clientHeight;
        this.scrollingFlag = false;
      }
    }, 200);
  }

  ngOnDestroy() {
    // Clear log file refresh intervals (stop refreshing) on componen destroy
    clearInterval(this.refreshLog);
  }

  goBack(): void {
    this.location.back();
  }

  // Temporarily set the scrollingFlag to true while scrolling
  onScroll(): void {
    this.scrollingFlag = true;
    clearTimeout(this.scrollingFlagTimeout);
    this.scrollingFlagTimeout = setTimeout( () => {
      this.scrollingFlag = false;
    }, 200);
  }

  // User can enable/disable to auto-go-to-bottom-of-log functionality
  enableGoToBottom(flag): void {
    this.goToBottomEnabled = flag;
  }
}
