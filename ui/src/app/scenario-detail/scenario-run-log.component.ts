import {
  Component,
  OnInit,
  OnDestroy,
  ViewChild,
  ElementRef,
  AfterViewInit
} from '@angular/core';
import {Location} from '@angular/common';

const fs = ( window as any ).require('fs');

@Component({
  selector: 'app-scenario-run-log',
  templateUrl: './scenario-run-log.component.html',
  styleUrls: ['./scenario-run-log.component.css']
})


export class ScenarioRunLogComponent implements OnInit, AfterViewInit, OnDestroy {

  logFilePath: string;
  scenarioLog: string;
  refreshLog: any;

  @ViewChild('logDiv') logDiv: ElementRef;

  constructor(
    private location: Location
  ) { }

  ngOnInit() {
    // Need to get the navigation extras from history (as the state is only
    // available during navigation); we'll use these to change the behavior
    // of the scenario name field
    this.logFilePath = history.state.pathToLogFile;

    console.log(this.logFilePath);

    this.scenarioLog = fs.readFileSync(this.logFilePath, 'utf8');
    this.refreshLog = setInterval(() => {
        const logDiv = document.getElementById('logDiv');
        const isScrolledToBottom = logDiv.scrollHeight - logDiv.clientHeight <= logDiv.scrollTop + 1;
        console.log(logDiv.scrollHeight - logDiv.clientHeight,  logDiv.scrollTop + 1);
        this.scenarioLog = fs.readFileSync(
          this.logFilePath, 'utf8'
        );
        if (!isScrolledToBottom) {
          logDiv.scrollTop = logDiv.scrollHeight - logDiv.clientHeight;
        }
        // const logDiv = document.getElementById('logDiv');
        // logDiv.scrollTop = logDiv.scrollHeight;
        // setTimeout(() => {
        //   const logDiv = document.getElementById('main-div');
        //   logDiv.scrollTop = logDiv.scrollHeight;
        // }, 0);
    }, 200);
  }

  ngAfterViewInit() {
    setTimeout(() => {
      this.logDiv.nativeElement.scrollTop = 9999999999;
      }, 0
    );
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
