import { Injectable } from '@angular/core';

import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { SettingsTable } from './scenario-new';

@Injectable({
  providedIn: 'root'
})
export class ScenarioNewService {

  constructor(private http: HttpClient) { }

  private scenarioSettingsBaseURL = 'http://127.0.0.1:8080/scenario-new';

  getTableTemporal(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/temporal`
    );
  }

  getTableLoadZones(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/load-zones`
    );
  }

  getTableSystemLoad(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/system-load`
    );
  }

  getTableProjectCapacity(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/project-capacity`
    );
  }

  getTableProjectOpChar(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/project-opchar`
    );
  }

  getTableFuels(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/fuels`
    );
  }

  getTableTransmissionCapacity(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/transmission-capacity`
    );
  }

  getTableTransmissionOpChar(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/transmission-opchar`
    );
  }

  getTableTransmissionHurdleRates(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/transmission-hurdle-rates`
    );
  }

  getTableTransmissionSimFlowLimits(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/transmission-simflow-limits`
    );
  }

  getTableLFReservesUp(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/lf-reserves-up`
    );
  }

  getTableLFReservesDown(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/lf-reserves-down`
    );
  }

  getTableRegulationUp(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/regulation-up`
    );
  }

  getTableRegulationDown(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/regulation-down`
    );
  }

  getTableSpinningReserves(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/spin`
    );
  }

  getTableFrequencyResponse(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/freq-resp`
    );
  }

  getTableRPS(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/rps`
    );
  }

  getTableCarbonCap(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/carbon-cap`
    );
  }

  getTablePRM(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/prm`
    );
  }

  getTableLocalCapacity(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/local-capacity`
    );
  }

  getTableTuning(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/tuning`
    );
  }
}
