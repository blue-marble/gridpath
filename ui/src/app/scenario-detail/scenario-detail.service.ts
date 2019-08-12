import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ScenarioDetail } from './scenario-detail';

@Injectable({
  providedIn: 'root'
})
export class ScenarioDetailService {

  constructor(
    private http: HttpClient
  ) { }

  private scenariosBaseURL = 'http://127.0.0.1:8080/scenarios/';

  getScenarioDetailFeatures(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/features`
    );
  }

  getScenarioDetailTemporal(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/temporal`
    );
  }

  getScenarioDetailGeographyLoadZones(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/geography-load-zones`
    );
  }

  getScenarioDetailProjectCapacity(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/project-capacity`
    );
  }

  getScenarioDetailProjectOpChars(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/project-opchars`
    );
  }

  getScenarioDetailFuels(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/fuels`
    );
  }

  getScenarioDetailTransmissionCapacity(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/transmission-capacity`
    );
  }

  getScenarioDetailTransmissionOpChars(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/transmission-opchars`
    );
  }

  getScenarioDetailTransmissionHurdleRates(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/transmission-hurdle-rates`
    );
  }

  getScenarioDetailTransmissionSimFlow(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/transmission-sim-flow`
    );
  }

  getScenarioDetailLoad(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/load`
    );
  }

  getScenarioDetailLFUp(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/lf-up`
    );
  }

  getScenarioDetailLFDown(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/lf-down`
    );
  }

  getScenarioDetailRegUp(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/reg-up`
    );
  }

  getScenarioDetailRegDown(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/reg-down`
    );
  }

  getScenarioDetailSpin(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/spin`
    );
  }

  getScenarioDetailFreqResp(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/freq-resp`
    );
  }

  getScenarioDetailRPS(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/rps`
    );
  }

  getScenarioDetailCarbonCap(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/carbon-cap`
    );
  }

  getScenarioDetailPRM(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/prm`
    );
  }

  getScenarioDetailLocalCapacity(scenarioID: number): Observable<ScenarioDetail> {
    return this.http.get<ScenarioDetail>(
      `${this.scenariosBaseURL}${scenarioID}/local-capacity`
    );
  }

  getScenarioName(scenarioID: number): Observable<string> {
    return this.http.get<string>(
      `${this.scenariosBaseURL}${scenarioID}/name`
    );
  }
}
