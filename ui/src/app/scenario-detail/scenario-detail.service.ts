import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ScenarioDetail } from './scenario-detail';

@Injectable({
  providedIn: 'root'
})
export class ScenarioDetailService {

  constructor(
    private http: HttpClient
  ) { }

  private scenariosBaseURL = 'http://127.0.0.1:8080/scenarios/';

  getScenarioName(scenarioID: number): Observable<string> {
    return this.http.get<string>(
      `${this.scenariosBaseURL}${scenarioID}/name`
    );
  }

  getScenarioDetailAPI(scenarioID: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${scenarioID}`
    );
  }
}
