import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';

import { ViewDataTable } from './view-data';

@Injectable({
  providedIn: 'root'
})
export class ViewDataService {

  private viewDataBaseURL = 'http://127.0.0.1:8080/scenarios/';

  constructor(private http: HttpClient) { }

  getViewDataAPI(scenarioID: number, table: string, row: string): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}${scenarioID}/view-data/${table}/${row}`
    );
  }

  getValidation(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}validation/${scenarioID}`
    );
  }

}
