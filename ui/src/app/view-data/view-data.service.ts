import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';

import { TimepointsTemporalRow } from './view-data';

@Injectable({
  providedIn: 'root'
})
export class ViewDataService {

  dataToViewSubject = new BehaviorSubject(null);

  private viewDataBaseURL = 'http://127.0.0.1:8080/view-data/';

  constructor(private http: HttpClient) { }

  changeDataToView(dataToView: string) {
    this.dataToViewSubject.next(dataToView);
    console.log('Data to view changed to, ', dataToView);
  }

  getTemporalTimepointsData(): Observable<TimepointsTemporalRow[]> {
    return this.http.get<TimepointsTemporalRow[]>(
      `${this.viewDataBaseURL}temporal-timepoints`
    );
  }
}
