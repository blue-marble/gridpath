import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';


@Injectable({
  providedIn: 'root'
})
export class HomeService {

  constructor(private http: HttpClient) { }

  private serverStatusURL = 'http://127.0.0.1:8080/server-status';
  private runStatusURL = 'http://127.0.0.1:8080/run-status';
  private validationStatusURL = 'http://127.0.0.1:8080/validation-status';

  getServerStatus(): Observable<string> {
    return(this.http.get<string>(this.serverStatusURL));
  }

  getRunStatus(): Observable<[][]> {
    return(this.http.get<[][]>(this.runStatusURL));
  }

  getValidationStatus(): Observable<[][]> {
    return(this.http.get<[][]>(this.validationStatusURL));
  }
}
