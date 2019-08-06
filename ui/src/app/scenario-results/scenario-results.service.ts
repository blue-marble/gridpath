import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { ScenarioResults } from './scenario-results';

@Injectable({
  providedIn: 'root'
})
export class ScenarioResultsService {

  resultsToViewSubject = new BehaviorSubject(null);

  private scenariosBaseURL = 'http://127.0.0.1:8080/scenarios/';

  constructor(
    private http: HttpClient
  ) { }

  changeResultsToView(resultsToShow: string) {
    this.resultsToViewSubject.next(resultsToShow);
    console.log('Results to show changed to, ', resultsToShow);
  }

  getResultsProjectCapacity(scenarioID: number): Observable<ScenarioResults> {
    return this.http.get<ScenarioResults>(
      `${this.scenariosBaseURL}${scenarioID}/results-project-capacity`
    );
  }

  getResultsProjectRetirements(scenarioID: number): Observable<ScenarioResults> {
    return this.http.get<ScenarioResults>(
      `${this.scenariosBaseURL}${scenarioID}/results-project-retirements`
    );
  }
}
