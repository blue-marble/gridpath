import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, of } from 'rxjs';

import { Scenario } from './scenario'


@Injectable({
  providedIn: 'root'
})

export class ScenariosService {

  constructor(
    private http: HttpClient
  ) { }

  private scenariosURL = 'http://127.0.0.1:8080/scenarios/';

  getScenarios(): Observable<Scenario[]> {
    console.log(this.http.get<Scenario[]>(this.scenariosURL));
    return this.http.get<Scenario[]>(this.scenariosURL)
  }

  getScenarioDetail(id: number): Observable<Scenario> {
    console.log(`${this.scenariosURL}${id}`);
    return this.http.get<Scenario>(`${this.scenariosURL}${id}`)
  }
}
