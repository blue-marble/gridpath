import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import {Scenario} from './scenarios.component';


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
    return this.http.get<Scenario[]>(this.scenariosURL);
  }

}
