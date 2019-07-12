import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ScenarioDetail } from "./scenario-detail";

@Injectable({
  providedIn: 'root'
})
export class ScenarioDetailService {

  constructor(
    private http: HttpClient
  ) { }

  private scenariosBaseURL = 'http://127.0.0.1:8080/scenarios/';

  getScenarioDetailAll(id: number): Observable<ScenarioDetail[]> {
    console.log(`${this.scenariosBaseURL}${id}`);
    return this.http.get<ScenarioDetail[]>(`${this.scenariosBaseURL}${id}`)
  }

  getScenarioDetailFeatures(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/features`
    )
  }

  getScenarioDetailTemporal(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/temporal`
    )
  }

  getScenarioDetailGeographyLoadZones(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/geography-load-zones`
    )
  }

  getScenarioDetailProjectCapacity(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/project-capacity`
    )
  }

  getScenarioDetailProjectOpChars(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/project-opchars`
    )
  }

  getScenarioDetailFuels(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/fuels`
    )
  }

  getScenarioDetailTransmissionCapacity(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/transmission-capacity`
    )
  }

  getScenarioDetailTransmissionOpChars(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/transmission-opchars`
    )
  }

  getScenarioDetailTransmissionHurdleRates(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/transmission-hurdle-rates`
    )
  }

  getScenarioDetailTransmissionSimFlow(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/transmission-sim-flow`
    )
  }

  getScenarioDetailLoad(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/load`
    )
  }

  getScenarioDetailLFUp(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/lf-up`
    )
  }

  getScenarioDetailLFDown(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/lf-down`
    )
  }

  getScenarioDetailRegUp(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/reg-up`
    )
  }

  getScenarioDetailRegDown(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/reg-down`
    )
  }

  getScenarioDetailSpin(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/spin`
    )
  }

  getScenarioDetailFreqResp(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/freq-resp`
    )
  }

  getScenarioDetailRPS(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/rps`
    )
  }

  getScenarioDetailCarbonCap(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/carbon-cap`
    )
  }

  getScenarioDetailPRM(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/prm`
    )
  }

  getScenarioDetailLocalCapacity(id: number): Observable<ScenarioDetail[]> {
    return this.http.get<ScenarioDetail[]>(
      `${this.scenariosBaseURL}${id}/local-capacity`
    )
  }
}
