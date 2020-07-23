import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable} from 'rxjs';
import {
  ResultsOptions,
  ScenarioResultsPlot,
  ScenarioResultsTable,
  IncludedPlotFormBuilderAPI
} from './scenario-results';

@Injectable({
  providedIn: 'root'
})
export class ScenarioResultsService {
  // Base URL
  private scenariosBaseURL = 'http://127.0.0.1:8080/scenarios/';

  constructor(
    private http: HttpClient
  ) { }

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
    rpsZone: string,
    carbonCapZone: string,
    period: number,
    horizon: number,
    startTimepoint: number,
    endTimepoint: number,
    subproblem: number,
    stage: number,
    project: string,
    commitProject: string,
    yMax: number
  ): Observable<ScenarioResultsPlot> {
    return this.http.get<ScenarioResultsPlot>(`${this.scenariosBaseURL}${scenarioID}/results/${plotType}/${loadZone}/${rpsZone}/${carbonCapZone}/${period}/${horizon}/${startTimepoint}/${endTimepoint}/${subproblem}/${stage}/${project}/${commitProject}/${yMax}`
    );
  }

  getResultsIncludedPlots(): Observable<IncludedPlotFormBuilderAPI[]> {
    return this.http.get<[]>(
      `${this.scenariosBaseURL}results/plots`
    );
  }

  getResultsTable(scenarioID: number, table: string): Observable<ScenarioResultsTable> {
    return this.http.get<ScenarioResultsTable>(
      `${this.scenariosBaseURL}${scenarioID}/results/${table}`
    );
  }

  getResultsIncludedTables(): Observable<{table: string; caption: string}[]> {
    return this.http.get<{table: string; caption: string}[]>(
      `${this.scenariosBaseURL}results/tables`
    );
  }
}
