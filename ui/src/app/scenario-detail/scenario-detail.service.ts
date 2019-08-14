import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ScenarioDetailAPI } from './scenario-detail';

@Injectable({
  providedIn: 'root'
})
export class ScenarioDetailService {

  constructor(
    private http: HttpClient
  ) { }

  private scenariosBaseURL = 'http://127.0.0.1:8080/scenarios/';

  getScenarioDetailAPI(scenarioID: number): Observable<ScenarioDetailAPI> {
    return this.http.get<ScenarioDetailAPI>(
      `${this.scenariosBaseURL}${scenarioID}`
    );
  }
}
