import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { TimepointsTemporalRow } from './view-data';

@Injectable({
  providedIn: 'root'
})
export class ViewDataService {

  constructor(private http: HttpClient) { }

  private viewDataBaseURL = 'http://127.0.0.1:8080/view-data/';

  getTemporalTimepointsData(): Observable<TimepointsTemporalRow[]> {
    return this.http.get<TimepointsTemporalRow[]>(
      `${this.viewDataBaseURL}temporal-timepoints`
    );
  }
}
