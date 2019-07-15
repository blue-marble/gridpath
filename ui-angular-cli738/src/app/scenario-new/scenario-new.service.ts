import { Injectable } from '@angular/core';

import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';


@Injectable({
  providedIn: 'root'
})
export class ScenarioNewService {

  constructor(private http: HttpClient)
    { }

  private scenarioSettingsBaseURL = 'http://127.0.0.1:8080/scenario-settings';

  getSettingTemporal(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/temporal`
    )
  }

  getSettingLoadZones(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/load-zones`
    )
  }

  getSettingProjectLoadZones(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-load-zones`
    )
  }

  getSettingTransmissionLoadZones(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/tx-load-zones`
    )
  }

  getSettingSystemLoad(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/system-load`
    )
  }

  getSettingProjectPortfolio(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-portfolio`
    )
  }

  getSettingProjectExistingCapacity(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-existing-capacity`
    )
  }

  getSettingProjectExistingFixedCost(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-existing-fixed-cost`
    )
  }

  getSettingProjectNewCost(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-new-cost`
    )
  }

  getSettingProjectNewPotential(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-new-potential`
    )
  }

  getSettingProjectAvailability(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-availability`
    )
  }

  getSettingProjectOpChar(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-opchar`
    )
  }

  getSettingFuels(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/fuels`
    )
  }

  getSettingFuelPrices(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/fuel-prices`
    )
  }

  getSettingTransmissionPortfolio(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/transmission-portfolio`
    )
  }

  getSettingTransmissionExistingCapacity(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/transmission-existing-capacity`
    )
  }
}


export class Setting {
  id: number;
  name: string;
}
