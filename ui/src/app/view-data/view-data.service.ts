import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';

import { ViewDataTable } from './view-data';

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

  getTemporalTimepoints(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}temporal-timepoints`
    );
  }

  getGeographyLoadZones(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-load-zones`
    );
  }

  getProjectLoadZones(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-load-zones`
    );
  }

  getTransmissionLoadZones(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}transmission-load-zones`
    );
  }

  getSystemLoad(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-load`
    );
  }

  getProjectPortfolio(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-portfolio`
    );
  }

  getProjectExistingCapacity(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-existing-capacity`
    );
  }

  getProjectExistingFixedCost(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-fixed-cost`
    );
  }

  getProjectNewPotential(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-new-potential`
    );
  }

  getProjectNewCost(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-new-cost`
    );
  }

  getProjectAvailability(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-availability`
    );
  }

  getProjectOpChar(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-opchar`
    );
  }

  getFuels(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}fuels`
    );
  }

  getFuelPrices(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}fuel-prices`
    );
  }

  getTransmissionPortfolio(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}transmission-portfolio`
    );
  }

  getTransmissionExistingCapacity(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}transmission-existing-capacity`
    );
  }

  getTransmissionOpChar(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}transmission-opchar`
    );
  }

  getTransmissionHurdleRates(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}transmission-hurdle-rates`
    );
  }

  getTransmissionSimFlowLimits(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}transmission-sim-flow-limits`
    );
  }

  getTransmissionSimFlowLimitsLineGroups(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}transmission-sim-flow-limit-line-groups`
    );
  }

  getLFUpBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-lf-up-bas`
    );
  }

  getProjectLFUpBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-lf-up-bas`
    );
  }

  getLFUpReq(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-lf-up-req`
    );
  }

  getLFDownBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-lf-down-bas`
    );
  }

  getProjectLFDownBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-lf-down-bas`
    );
  }

  getLFDownReq(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-lf-down-req`
    );
  }

  getRegUpBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-reg-up-bas`
    );
  }

  getProjectRegUpBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-reg-up-bas`
    );
  }

  getRegUpReq(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-reg-up-req`
    );
  }

  getRegDownBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-reg-down-bas`
    );
  }

  getProjectRegDownBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-reg-down-bas`
    );
  }

  getRegDownReq(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-reg-down-req`
    );
  }

  getSpinBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-spin-bas`
    );
  }

  getProjectSpinBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-spin-bas`
    );
  }

  getSpinReq(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-spin-req`
    );
  }

  getFreqRespBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-freq-resp-bas`
    );
  }

  getProjectFreqRespBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-freq-resp-bas`
    );
  }

  getFreqRespReq(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-freq-resp-req`
    );
  }

  getRPSBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-rps-bas`
    );
  }

  getProjectRPSBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-rps-bas`
    );
  }

  getRPSReq(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-rps-req`
    );
  }

  getCarbonCapBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-carbon-cap-bas`
    );
  }

  getProjectCarbonCapBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-carbon-cap-bas`
    );
  }

  getTransmissionCarbonCapBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}transmission-carbon-cap-bas`
    );
  }

  getCarbonCapReq(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-carbon-cap-req`
    );
  }

  getPRMBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-prm-bas`
    );
  }

  getProjectPRMBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-prm-bas`
    );
  }

  getPRMReq(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-prm-req`
    );
  }

  getProjectELCCChars(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-elcc-chars`
    );
  }

  getELCCSurface(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-elcc-surface`
    );
  }

  getEnergyOnly(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-energy-only`
    );
  }

  getLocalCapacityBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-local-capacity-bas`
    );
  }

  getProjectLocalCapacityBAs(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-local-capacity-bas`
    );
  }

  getLocalCapacityReq(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}local-capacity-req`
    );
  }

  getProjectLocalCapacityChars(): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-local-capacity-chars`
    );
  }

}
