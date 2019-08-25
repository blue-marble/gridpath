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

  getTemporalTimepoints(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}temporal-timepoints/${scenarioID}`
    );
  }

  getGeographyLoadZones(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-load-zones/${scenarioID}`
    );
  }

  getProjectLoadZones(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-load-zones/${scenarioID}`
    );
  }

  getTransmissionLoadZones(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}transmission-load-zones/${scenarioID}`
    );
  }

  getSystemLoad(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-load/${scenarioID}`
    );
  }

  getProjectPortfolio(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-portfolio/${scenarioID}`
    );
  }

  getProjectExistingCapacity(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-existing-capacity/${scenarioID}`
    );
  }

  getProjectExistingFixedCost(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-fixed-cost/${scenarioID}`
    );
  }

  getProjectNewPotential(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-new-potential/${scenarioID}`
    );
  }

  getProjectNewCost(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-new-cost/${scenarioID}`
    );
  }

  getProjectAvailability(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-availability/${scenarioID}`
    );
  }

  getProjectOpChar(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-opchar/${scenarioID}`
    );
  }

  getFuels(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}fuels/${scenarioID}`
    );
  }

  getFuelPrices(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}fuel-prices/${scenarioID}`
    );
  }

  getTransmissionPortfolio(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}transmission-portfolio/${scenarioID}`
    );
  }

  getTransmissionExistingCapacity(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}transmission-existing-capacity/${scenarioID}`
    );
  }

  getTransmissionOpChar(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}transmission-opchar/${scenarioID}`
    );
  }

  getTransmissionHurdleRates(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}transmission-hurdle-rates/${scenarioID}`
    );
  }

  getTransmissionSimFlowLimits(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}transmission-sim-flow-limits/${scenarioID}`
    );
  }

  getTransmissionSimFlowLimitsLineGroups(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}transmission-sim-flow-limit-line-groups/${scenarioID}`
    );
  }

  getLFUpBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-lf-up-bas/${scenarioID}`
    );
  }

  getProjectLFUpBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-lf-up-bas/${scenarioID}`
    );
  }

  getLFUpReq(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-lf-up-req/${scenarioID}`
    );
  }

  getLFDownBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-lf-down-bas/${scenarioID}`
    );
  }

  getProjectLFDownBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-lf-down-bas/${scenarioID}`
    );
  }

  getLFDownReq(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-lf-down-req/${scenarioID}`
    );
  }

  getRegUpBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-reg-up-bas/${scenarioID}`
    );
  }

  getProjectRegUpBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-reg-up-bas/${scenarioID}`
    );
  }

  getRegUpReq(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-reg-up-req/${scenarioID}`
    );
  }

  getRegDownBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-reg-down-bas/${scenarioID}`
    );
  }

  getProjectRegDownBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-reg-down-bas/${scenarioID}`
    );
  }

  getRegDownReq(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-reg-down-req/${scenarioID}`
    );
  }

  getSpinBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-spin-bas/${scenarioID}`
    );
  }

  getProjectSpinBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-spin-bas/${scenarioID}`
    );
  }

  getSpinReq(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-spin-req/${scenarioID}`
    );
  }

  getFreqRespBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-freq-resp-bas/${scenarioID}`
    );
  }

  getProjectFreqRespBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-freq-resp-bas/${scenarioID}`
    );
  }

  getFreqRespReq(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-freq-resp-req/${scenarioID}`
    );
  }

  getRPSBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-rps-bas/${scenarioID}`
    );
  }

  getProjectRPSBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-rps-bas/${scenarioID}`
    );
  }

  getRPSReq(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-rps-req/${scenarioID}`
    );
  }

  getCarbonCapBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-carbon-cap-bas/${scenarioID}`
    );
  }

  getProjectCarbonCapBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-carbon-cap-bas/${scenarioID}`
    );
  }

  getTransmissionCarbonCapBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}transmission-carbon-cap-bas/${scenarioID}`
    );
  }

  getCarbonCapReq(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-carbon-cap-req/${scenarioID}`
    );
  }

  getPRMBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-prm-bas/${scenarioID}`
    );
  }

  getProjectPRMBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-prm-bas/${scenarioID}`
    );
  }

  getPRMReq(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}system-prm-req/${scenarioID}`
    );
  }

  getProjectELCCChars(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-elcc-chars/${scenarioID}`
    );
  }

  getELCCSurface(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-elcc-surface/${scenarioID}`
    );
  }

  getEnergyOnly(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-energy-only/${scenarioID}`
    );
  }

  getLocalCapacityBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}geography-local-capacity-bas/${scenarioID}`
    );
  }

  getProjectLocalCapacityBAs(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-local-capacity-bas/${scenarioID}`
    );
  }

  getLocalCapacityReq(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}local-capacity-req/${scenarioID}`
    );
  }

  getProjectLocalCapacityChars(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}project-local-capacity-chars/${scenarioID}`
    );
  }

  getTuning(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}tuning/${scenarioID}`
    );
  }

  getValidation(scenarioID: number): Observable<ViewDataTable> {
    return this.http.get<ViewDataTable>(
      `${this.viewDataBaseURL}validation/${scenarioID}`
    );
  }

}
