import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { HttpClient } from '@angular/common/http';

import {StartingValues} from './scenario-detail';

@Injectable({
  providedIn: 'root'
})
export class ScenarioEditService {

  startingValuesSubject = new BehaviorSubject(null);

  private scenariosBaseURL = 'http://127.0.0.1:8080/scenarios/';

  constructor(private http: HttpClient) {}

  // TODO: https://stackoverflow.com/questions/39950743/angular-2-rxjs-observable-skipping-subscribe-on-first-call
  changeStartingScenario(startingValues: StartingValues) {
    this.startingValuesSubject.next(startingValues);
    console.log(startingValues);
  }
}
