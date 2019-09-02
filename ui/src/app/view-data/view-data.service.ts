import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ViewDataTable } from './view-data';

@Injectable({
  providedIn: 'root'
})
export class ViewDataService {

  private viewDataBaseURL = 'http://127.0.0.1:8080/scenarios/';

  constructor(private http: HttpClient) { }

  getTable(scenarioID: number, table: string): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}${scenarioID}/${table}`
    );
  }

}
