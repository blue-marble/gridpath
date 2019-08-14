import { Injectable } from '@angular/core';

import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { SettingsTable } from './scenario-new';

@Injectable({
  providedIn: 'root'
})
export class ScenarioNewService {

  constructor(private http: HttpClient) { }

  private scenarioSettingsBaseURL = 'http://127.0.0.1:8080/scenario-new';

  getScenarioNewAPI(): Observable<SettingsTable[]> {
    return this.http.get<SettingsTable[]>(
      `${this.scenarioSettingsBaseURL}`
    );
  }
}
