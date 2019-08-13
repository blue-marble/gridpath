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

  getSettingTemporal(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/temporal`
    );
  }

  getSettingLoadZones(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/load-zones`
    );
  }

  getSettingSystemLoad(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/system-load`
    );
  }

  getSettingProjectPortfolio(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/project-capacity`
    );
  }

  getSettingProjectOpChar(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/project-opchar`
    );
  }

  getSettingFuels(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/fuels`
    );
  }

  getSettingTransmissionPortfolio(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/transmission-capacity`
    );
  }

  getSettingTransmissionOpChar(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/transmission-opchar`
    );
  }

  getSettingTransmissionHurdleRates(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/transmission-hurdle-rates`
    );
  }

  getSettingTransmissionSimFlowLimits(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/transmission-simflow-limits`
    );
  }

  getSettingLFReservesUpBAs(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/lf-reserves-up`
    );
  }

  getSettingLFReservesDownBAs(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/lf-reserves-down`
    );
  }

  getSettingRegulationUpBAs(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/regulation-up`
    );
  }

  getSettingRegulationDownBAs(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/regulation-down`
    );
  }

  getSettingSpinningReservesBAs(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/spin`
    );
  }

  getSettingFrequencyResponseBAs(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/freq-resp`
    );
  }

  getSettingRPSAreas(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/rps`
    );
  }

  getSettingCarbonCapAreas(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/carbon-cap`
    );
  }

  getSettingPRMAreas(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/prm`
    );
  }

  getSettingLocalCapacityAreas(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/local-capacity`
    );
  }

  getSettingTuning(): Observable<SettingsTable> {
    return this.http.get<SettingsTable>(
      `${this.scenarioSettingsBaseURL}/tuning`
    );
  }
}
