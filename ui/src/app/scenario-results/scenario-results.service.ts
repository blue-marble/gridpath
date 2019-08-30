import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {BehaviorSubject, Observable} from 'rxjs';
import { ResultsOptions, PlotAPI, ScenarioResults} from './scenario-results';

@Injectable({
  providedIn: 'root'
})
export class ScenarioResultsService {

  // We will subscribe to this in scenario-results.component.ts and will
  // use its value to know which table to show and which results to fetch
  resultsToViewSubject = new BehaviorSubject(null);

  // Base URL
  private scenariosBaseURL = 'http://127.0.0.1:8080/scenarios/';

  constructor(
    private http: HttpClient
  ) { }

  // Change the value of resultsToViewSubject
  changeResultsToView(resultsToShow: string) {
    this.resultsToViewSubject.next(resultsToShow);
    console.log('Results to show changed to ', resultsToShow);
  }

  // API subscriptions
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

  getOptions(scenarioID: number): Observable<ResultsOptions> {
    return this.http.get<ResultsOptions>(
      `${this.scenariosBaseURL}${scenarioID}/scenario-results-options`
    );
  }

  getResultsDispatchPlot(
    scenarioID: number, loadZone: string, horizon: number, ymax: number
  ): Observable<PlotAPI> {
    return this.http.get<PlotAPI>(
      `${this.scenariosBaseURL}${scenarioID}/results-dispatch-plot/${loadZone}/${horizon}/${ymax}`
    );
  }

  getResultsCapacityNewPlot(scenarioID: number, loadZone: string, ymax: number
  ): Observable<PlotAPI> {
    return this.http.get<PlotAPI>(
      `${this.scenariosBaseURL}${scenarioID}/results-capacity-plot/new/${loadZone}/${ymax}`
    );
  }

  getResultsCapacityRetiredPlot(scenarioID: number, loadZone: string, ymax: number
  ): Observable<PlotAPI> {
    return this.http.get<PlotAPI>(
      `${this.scenariosBaseURL}${scenarioID}/results-capacity-plot/retired/${loadZone}/${ymax}`
    );
  }

  getResultsCapacityTotalPlot(scenarioID: number, loadZone: string, ymax: number
  ): Observable<PlotAPI> {
    return this.http.get<PlotAPI>(
      `${this.scenariosBaseURL}${scenarioID}/results-capacity-plot/total/${loadZone}/${ymax}`
    );
  }

  getResultsEnergyPlot(scenarioID: number, loadZone: string, stage: number, ymax: number
  ): Observable<PlotAPI> {
    return this.http.get<PlotAPI>(
      `${this.scenariosBaseURL}${scenarioID}/results-energy-plot/${loadZone}/${stage}/${ymax}`
    );
  }

  getResultsCostPlot(scenarioID: number, loadZone: string, stage: number, ymax: number
  ): Observable<PlotAPI> {
    return this.http.get<PlotAPI>(
      `${this.scenariosBaseURL}${scenarioID}/results-cost-plot/${loadZone}/${stage}/${ymax}`
    );
  }

  getResultsCapacityFactorPlot(scenarioID: number, loadZone: string, stage: number, ymax: number
  ): Observable<PlotAPI> {
    return this.http.get<PlotAPI>(
      `${this.scenariosBaseURL}${scenarioID}/results-capacity-factor-plot/${loadZone}/${stage}/${ymax}`
    );
  }

  getResultsTable(scenarioID: number, table: string): Observable<ScenarioResults> {
    return this.http.get<ScenarioResults>(
      `${this.scenariosBaseURL}${scenarioID}/results/${table}`
    );
  }
}
