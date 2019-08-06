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

  getResultsProjectNewBuild(scenarioID: number): Observable<ScenarioResults> {
    return this.http.get<ScenarioResults>(
      `${this.scenariosBaseURL}${scenarioID}/results-project-new-build`
    );
  }

  getResultsProjectDispatch(scenarioID: number): Observable<ScenarioResults> {
    return this.http.get<ScenarioResults>(
      `${this.scenariosBaseURL}${scenarioID}/results-project-dispatch`
    );
  }

  getResultsProjectCarbon(scenarioID: number): Observable<ScenarioResults> {
    return this.http.get<ScenarioResults>(
      `${this.scenariosBaseURL}${scenarioID}/results-project-carbon`
    );
  }

  getResultsTransmissionCapacity(scenarioID: number): Observable<ScenarioResults> {
    return this.http.get<ScenarioResults>(
      `${this.scenariosBaseURL}${scenarioID}/results-transmission-capacity`
    );
  }

  getResultsTransmissionFlows(scenarioID: number): Observable<ScenarioResults> {
    return this.http.get<ScenarioResults>(
      `${this.scenariosBaseURL}${scenarioID}/results-transmission-flows`
    );
  }

  getResultsImportsExports(scenarioID: number): Observable<ScenarioResults> {
    return this.http.get<ScenarioResults>(
      `${this.scenariosBaseURL}${scenarioID}/results-imports-exports`
    );
  }

  getResultsSystemLoadBalance(scenarioID: number): Observable<ScenarioResults> {
    return this.http.get<ScenarioResults>(
      `${this.scenariosBaseURL}${scenarioID}/results-system-load-balance`
    );
  }

  getResultsSystemRPS(scenarioID: number): Observable<ScenarioResults> {
    return this.http.get<ScenarioResults>(
      `${this.scenariosBaseURL}${scenarioID}/results-system-rps`
    );
  }

  getResultsSystemCarbonCap(scenarioID: number): Observable<ScenarioResults> {
    return this.http.get<ScenarioResults>(
      `${this.scenariosBaseURL}${scenarioID}/results-system-carbon-cap`
    );
  }

  getResultsSystemPRM(scenarioID: number): Observable<ScenarioResults> {
    return this.http.get<ScenarioResults>(
      `${this.scenariosBaseURL}${scenarioID}/results-system-prm`
    );
  }
}
