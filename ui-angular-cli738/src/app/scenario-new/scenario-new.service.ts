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

  getSettingTransmissionOpChar(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/transmission-opchar`
    )
  }

  getSettingTransmissionHurdleRates(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/transmission-hurdle-rates`
    )
  }

  getSettingTransmissionSimFlowLimits(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/transmission-simflow-limits`
    )
  }

  getSettingTransmissionSimFlowLimitGroups(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/transmission-simflow-limit-groups`
    )
  }

  getSettingLFReservesUpBAs(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/lf-reserves-up-bas`
    )
  }

  getSettingProjectLFReservesUpBAs(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-lf-reserves-up-bas`
    )
  }

  getSettingLFReservesUpRequirement(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/lf-reserves-up-req`
    )
  }

  getSettingLFReservesDownBAs(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/lf-reserves-down-bas`
    )
  }

  getSettingProjectLFReservesDownBAs(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-lf-reserves-down-bas`
    )
  }

  getSettingLFReservesDownRequirement(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/lf-reserves-down-req`
    )
  }

  getSettingRegulationUpBAs(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/regulation-up-bas`
    )
  }

  getSettingProjectRegulationUpBAs(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-regulation-up-bas`
    )
  }

  getSettingRegulationUpRequirement(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/regulation-up-req`
    )
  }

  getSettingRegulationDownBAs(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/regulation-down-bas`
    )
  }

  getSettingProjectRegulationDownBAs(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-regulation-down-bas`
    )
  }

  getSettingRegulationDownRequirement(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/regulation-down-req`
    )
  }

  getSettingSpinningReservesBAs(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/spin-bas`
    )
  }

  getSettingProjectSpinningReservesBAs(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-spin-bas`
    )
  }

  getSettingSpinningReservesRequirement(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/spin-req`
    )
  }

  getSettingFrequencyResponseBAs(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/freq-resp-bas`
    )
  }

  getSettingProjectFrequencyResponseBAs(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-freq-resp-bas`
    )
  }

  getSettingFrequencyResponseRequirement(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/freq-resp-req`
    )
  }

  getSettingRPSAreas(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/rps-areas`
    )
  }

  getSettingProjectRPSAreas(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-rps-areas`
    )
  }

  getSettingRPSRequirement(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/rps-req`
    )
  }
  
  getSettingCarbonCapAreas(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/carbon-cap-areas`
    )
  }

  getSettingProjectCarbonCapAreas(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-carbon-cap-areas`
    )
  }

  getSettingTransmissionCarbonCapAreas(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/transmission-carbon-cap-areas`
    )
  }

  getSettingCarbonCapRequirement(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/carbon-cap-req`
    )
  }

  getSettingPRMAreas(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/prm-areas`
    )
  }

  getSettingProjectPRMAreas(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-prm-areas`
    )
  }

  getSettingPRMRequirement(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/prm-req`
    )
  }

  getSettingELCCSurface(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/elcc-surface`
    )
  }

  getSettingProjectELCCChars(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-elcc-chars`
    )
  }

  getSettingProjectEnergyOnly(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-energy-only`
    )
  }

  getSettingLocalCapacityAreas(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/local-capacity-areas`
    )
  }

  getSettingProjectLocalCapacityAreas(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-local-capacity-areas`
    )
  }

  getSettingLocalCapacityRequirement(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/local-capacity-req`
    )
  }

  getSettingProjectLocalCapacityChars(): Observable<Setting[]> {
    return this.http.get<Setting[]>(
      `${this.scenarioSettingsBaseURL}/project-local-capacity-chars`
    )
  }
}


export class Setting {
  id: number;
  name: string;
}
