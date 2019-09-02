import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { ScenarioInputsTable } from './scenario-inputs';

@Injectable({
  providedIn: 'root'
})
export class ScenarioInputsService {

  private viewDataBaseURL = 'http://127.0.0.1:8080/scenarios/';

  constructor(private http: HttpClient) { }

  getScenarioInputs(scenarioID: number, table: string, row: string): Observable<ScenarioInputsTable> {
    return this.http.get<ScenarioInputsTable>(
      `${this.viewDataBaseURL}${scenarioID}/inputs/${table}/${row}`
    );
  }

  getValidation(scenarioID: number): Observable<ScenarioInputsTable> {
    return this.http.get<ScenarioInputsTable>(
      `${this.viewDataBaseURL}validation/${scenarioID}`
    );
  }

}
