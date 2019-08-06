import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { ScenarioResultsService} from './scenario-results.service';
import { ScenarioResults, ResultsButton } from './scenario-results';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-scenario-results',
  templateUrl: './scenario-results.component.html',
  styleUrls: ['./scenario-results.component.css']
})
export class ScenarioResultsComponent implements OnInit {

  // Key for which results table to show
  resultsToShow: string;

  // All results buttons
  allResultsButtons: ResultsButton[];

  // All tables
  allTables: ScenarioResults[];

  // Results tables
  projectResultsCapacity: ScenarioResults;
  projectResultsRetirements: ScenarioResults;

  // To get the right route
  scenarioID: number;
  private sub: any;

  constructor(
    private route: ActivatedRoute,
    private scenarioResultsService: ScenarioResultsService,
    private location: Location,

  ) { }

  ngOnInit() {

    // The ActivatedRoute service provides a params Observable which we can
    // subscribe to in order to get the route parameters
    this.sub = this.route.params.subscribe(params => {
       this.scenarioID = +params.id;
       console.log(`Scenario ID is ${this.scenarioID}`);
    });

    // Make the results buttons
    this.allResultsButtons = [];
    this.makeResultsButtons();

    // Initiate the array of all tables
    this.allTables = [];

    // Get the key for which table to show
    this.getResultsToShow();

    // Get data
    if (this.resultsToShow === 'results-project-capacity') {
      console.log('Getting project capacity results');
      this.getResultsProjectCapacity(this.scenarioID);
    }

    if (this.resultsToShow === 'results-project-retirements') {
      console.log('Getting project retirements results');
      this.getResultsProjectRetirements(this.scenarioID);
    }

  }

  getResultsToShow(): void {
    this.scenarioResultsService.resultsToViewSubject
      .subscribe((resultsToShow: string) => {
        this.resultsToShow = resultsToShow;
      });
  }

  getResultsProjectCapacity(scenarioID): void {
    this.scenarioResultsService.getResultsProjectCapacity(scenarioID)
      .subscribe(inputTableRows => {
        this.projectResultsCapacity = inputTableRows;
        this.allTables.push(this.projectResultsCapacity);
      });
  }

  getResultsProjectRetirements(scenarioID): void {
    this.scenarioResultsService.getResultsProjectRetirements(scenarioID)
      .subscribe(inputTableRows => {
        this.projectResultsRetirements = inputTableRows;
        this.allTables.push(this.projectResultsRetirements);
      });
  }

  makeResultsButtons(): void {
    const projectCapacityButton = {
      name: 'showResultsProjectCapacityButton',
      ngIfKey: 'results-project-capacity',
      caption: 'Project Capacity'
    };
    this.allResultsButtons.push(projectCapacityButton);

    const projectRetirementsButton = {
      name: 'showResultsProjectRetirementsButton',
      ngIfKey: 'results-project-retirements',
      caption: 'Project Retirements'
    };
    this.allResultsButtons.push(projectRetirementsButton);
  }

  showResults(resultsToShow): void {
    // Send value for show project capacity table
    this.scenarioResultsService.changeResultsToView(resultsToShow);
    // Refresh the view
    this.ngOnInit();
  }

  goBack(): void {
    this.location.back();
    // The the resultsToView to '', so that we start with no tables visible
    // when we visit the results page again
    this.scenarioResultsService.changeResultsToView('');
  }

}
