import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {BehaviorSubject, Observable} from 'rxjs';
import {
  ResultsOptions,
  PlotAPI,
  ScenarioResultsTable,
  ResultsForm, IncludedPlotAPI
} from './scenario-results-table';

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

  // API Subscriptions
  getOptions(scenarioID: number): Observable<ResultsOptions> {
    return this.http.get<ResultsOptions>(
      `${this.scenariosBaseURL}${scenarioID}/scenario-results-options`
    );
  }

  getResultsPlot(
    scenarioID: number,
    plotType: string,
    loadZone: string,
    period: number,
    horizon: number,
    timepoint: number,
    stage: number,
    project: string,
    yMax: number
  ): Observable<PlotAPI> {
    return this.http.get<PlotAPI>(
      `${this.scenariosBaseURL}${scenarioID}/results/${plotType}/${loadZone}/${period}/${horizon}/${timepoint}/${stage}/${project}/${yMax}`
    );
  }

  getResultsIncludedPlots(scenarioID): Observable<IncludedPlotAPI[]> {
    return this.http.get<[]>(
      `${this.scenariosBaseURL}${scenarioID}/results/plots`
    );
  }

  getResultsTable(scenarioID: number, table: string): Observable<ScenarioResultsTable> {
    return this.http.get<ScenarioResultsTable>(
      `${this.scenariosBaseURL}${scenarioID}/results/${table}`
    );
  }

  getResultsIncludedTables(): Observable<{ngIfKey: string; caption: string}[]> {
    return this.http.get<{ngIfKey: string; caption: string}[]>(
      `${this.scenariosBaseURL}results/tables`
    );
  }
}
