import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';


@Injectable({
  providedIn: 'root'
})
export class HomeService {

  constructor(private http: HttpClient) { }

  private statusURL = 'http://127.0.0.1:8080/server-status';

  getScenarios(): Observable<string> {
    console.log(this.http.get<string>(this.statusURL));
    return(this.http.get<string>(this.statusURL))
  }
}
