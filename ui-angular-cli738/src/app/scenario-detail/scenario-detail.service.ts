import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {Scenario} from "../scenarios/scenario";

@Injectable({
  providedIn: 'root'
})
export class ScenarioDetailService {

  constructor(
    private http: HttpClient
  ) { }

  private scenariosBaseURL = 'http://127.0.0.1:8080/scenarios/';

  getScenarioDetail(id: number): Observable<Scenario> {
    console.log(`${this.scenariosBaseURL}${id}`);
    return this.http.get<Scenario>(`${this.scenariosBaseURL}${id}`)
  }
}
