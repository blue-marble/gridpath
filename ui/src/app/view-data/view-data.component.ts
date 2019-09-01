import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';

import { ViewDataService } from './view-data.service';
import { ViewDataTable } from './view-data';
import { ScenarioDetailService } from '../scenario-detail/scenario-detail.service';

@Component({
  selector: 'app-view-data',
  templateUrl: './view-data.component.html',
  styleUrls: ['./view-data.component.css']
})
export class ViewDataComponent implements OnInit {

  // To get the right route
  scenarioID: number;
  private sub: any;

  // The scenario name
  scenarioName: string;

  // Key for which table to show
  dataToShow: string;

  // All tables
  allTables: ViewDataTable[];

  // TODO: too slow with ngIf? Perhaps need separate route for each table
  //  or groups of tables
  // Input data tables
  timepointsTemporalTable: ViewDataTable;
  geographyLoadZonesTable: ViewDataTable;
  projectLoadZonesTable: ViewDataTable;
  transmissionLoadZonesTable: ViewDataTable;
  systemLoadTable: ViewDataTable;
  projectPortfolioTable: ViewDataTable;
  projectExistingCapacityTable: ViewDataTable;
  projectExistingFixedCostTable: ViewDataTable;
  projectNewPotentialTable: ViewDataTable;
  projectNewCostTable: ViewDataTable;
  projectAvailabilityTable: ViewDataTable;
  projectOpCharTable: ViewDataTable;
  fuelsTable: ViewDataTable;
  fuelPricesTable: ViewDataTable;
  transmissionPortfolioTable: ViewDataTable;
  transmissionExistingCapacityTable: ViewDataTable;
  transmissionOpCharTable: ViewDataTable;
  transmissionHurdleRatesTable: ViewDataTable;
  transmissionSimFlowLimitsTable: ViewDataTable;
  transmissionSimFlowLimitLineGroupsTable: ViewDataTable;
  lfUpBAsTable: ViewDataTable;
  projectLFUpBAsTable: ViewDataTable;
  lfUpReqTable: ViewDataTable;
  lfDownBAsTable: ViewDataTable;
  projectLFDownBAsTable: ViewDataTable;
  lfDownReqTable: ViewDataTable;
  regUpBAsTable: ViewDataTable;
  projectRegUpBAsTable: ViewDataTable;
  regUpReqTable: ViewDataTable;
  regDownBAsTable: ViewDataTable;
  projectRegDownBAsTable: ViewDataTable;
  regDownReqTable: ViewDataTable;
  spinBAsTable: ViewDataTable;
  projectSpinBAsTable: ViewDataTable;
  spinReqTable: ViewDataTable;
  freqRespBAsTable: ViewDataTable;
  projectFreqRespBAsTable: ViewDataTable;
  freqRespReqTable: ViewDataTable;
  rpsBAsTable: ViewDataTable;
  projectRPSBAsTable: ViewDataTable;
  rpsReqTable: ViewDataTable;
  carbonCapBAsTable: ViewDataTable;
  projectCarbonCapBAsTable: ViewDataTable;
  transmissionCarbonCapBAsTable: ViewDataTable;
  carbonCapReqTable: ViewDataTable;
  prmBAsTable: ViewDataTable;
  projectPRMBAsTable: ViewDataTable;
  prmReqTable: ViewDataTable;
  projectELCCCharsTable: ViewDataTable;
  elccSurfaceTable: ViewDataTable;
  energyOnlyTable: ViewDataTable;
  localCapacityBAsTable: ViewDataTable;
  projectLocalCapacityBAsTable: ViewDataTable;
  localCapacityReqTable: ViewDataTable;
  projectLocalCapacityCharsTable: ViewDataTable;
  tuningTable: ViewDataTable;
  validationTable: ViewDataTable;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private location: Location,
    private viewDataService: ViewDataService,
    private scenarioDetailService: ScenarioDetailService
  ) { }

  ngOnInit() {
    // The ActivatedRoute service provides a params Observable which we can
    // subscribe to in order to get the route parameters
    this.sub = this.route.params.subscribe(params => {
       this.scenarioID = +params.id;
       console.log(`Scenario ID in view-data is ${this.scenarioID}`);
    });

    // Get the scenario name
    this.getScenarioName(this.scenarioID);

    this.allTables = [];

    // Get flag for which table/s to show
    this.getDataToShow();
    console.log('Received data to show, ', this.dataToShow);

    // Temporal timepoints input data table
    if (this.dataToShow === 'temporal-temporal') {
      console.log('calling temporal timepoints');
      this.getTemporalTimepoints();
    }
    if (this.dataToShow === 'load_zones-load_zones') {
      this.getGeographyLoadZones();
    }
    if (this.dataToShow === 'load_zones-project_load_zones') {
      this.getProjectLoadZones();
    }
    if (this.dataToShow === 'load_zones-transmission_load_zones') {
      this.getTransmissionLoadZones();
    }
    if (this.dataToShow === 'load_profile') {
      this.getSystemLoad();
    }
    if (this.dataToShow === 'project_capacity-portfolio') {
      this.getProjectPortfolio();
    }
    if (this.dataToShow === 'project_capacity-specified_capacity') {
      this.getProjectExistingCapacity();
    }
    if (this.dataToShow === 'project_capacity-specified_fixed_cost') {
      this.getProjectExistingFixedCost();
    }
    if (this.dataToShow === 'project_capacity-new_potential') {
      this.getProjectNewPotential();
    }
    if (this.dataToShow === 'project_capacity-new_cost') {
      this.getProjectNewCost();
    }
    if (this.dataToShow === 'project_capacity-availability') {
      this.getProjectAvailability();
    }
    if (this.dataToShow === 'project_opchar-opchar') {
      this.getProjectOpChar();
    }
    if (this.dataToShow === 'fuels-fuels') {
      this.getFuels();
    }
    if (this.dataToShow === 'fuels-fuel_prices') {
      this.getFuelPrices();
    }
    if (this.dataToShow === 'transmission_capacity-portfolio') {
      this.getTransmissionPortfolio();
    }
    if (this.dataToShow === 'transmission_capacity-specified_capacity') {
      this.getTransmissionExistingCapacity();
    }
    if (this.dataToShow === 'transmission_opchar-opchar') {
      this.getTransmissionOpChar();
    }
    if (this.dataToShow === 'transmission_hurdle_rates-hurdle_rates') {
      this.getTransmissionHurdleRates();
    }
    if (this.dataToShow === 'transmission_sim_flow_limits-limits') {
      this.getTransmissionSimFlowLimits();
    }
    if (this.dataToShow ===
      'transmission_sim_flow_limits-groups') {
      this.getTransmissionSimFlowLimitsLineGroups();
    }
    if (this.dataToShow === 'load_following_up-bas') {
      this.getLFUpBAs();
    }
    if (this.dataToShow === 'load_following_up-projects') {
      this.getProjectLFUpBAs();
    }
    if (this.dataToShow === 'load_following_up-req') {
      this.getLFUpReq();
    }
    if (this.dataToShow === 'load_following_down-bas') {
      this.getLFDownBAs();
    }
    if (this.dataToShow === 'load_following_down-projects') {
      this.getProjectLFDownBAs();
    }
    if (this.dataToShow === 'load_following_down-req') {
      this.getLFDownReq();
    }
    if (this.dataToShow === 'regulation_up-bas') {
      this.getRegUpBAs();
    }
    if (this.dataToShow === 'regulation_up-projects') {
      this.getProjectRegUpBAs();
    }
    if (this.dataToShow === 'regulation_up-req') {
      this.getRegUpReq();
    }
    if (this.dataToShow === 'regulation_down-bas') {
      this.getRegDownBAs();
    }
    if (this.dataToShow === 'regulation_down-projects') {
      this.getProjectRegDownBAs();
    }
    if (this.dataToShow === 'regulation_down-req') {
      this.getRegDownReq();
    }
    if (this.dataToShow === 'spinning_reserves-bas') {
      this.getSpinBAs();
    }
    if (this.dataToShow === 'spinning_reserves-projects') {
      this.getProjectSpinBAs();
    }
    if (this.dataToShow === 'spinning_reserves-req') {
      this.getSpinReq();
    }
    if (this.dataToShow === 'frequency_response-bas') {
      this.getFreqRespBAs();
    }
    if (this.dataToShow === 'frequency_response-projects') {
      this.getProjectFreqRespBAs();
    }
    if (this.dataToShow === 'frequency_response-req') {
      this.getFreqRespReq();
    }
    if (this.dataToShow === 'rps-bas') {
      this.getRPSBAs();
    }
    if (this.dataToShow === 'rps-projects') {
      this.getProjectRPSBAs();
    }
    if (this.dataToShow === 'rps-req') {
      this.getRPSReq();
    }
    if (this.dataToShow === 'carbon_cap-bas') {
      this.getCarbonCapBAs();
    }
    if (this.dataToShow === 'carbon_cap-projects') {
      this.getProjectCarbonCapBAs();
    }
    if (this.dataToShow === 'carbon_cap-transmission') {
      this.getTransmissionCarbonCapBAs();
    }
    if (this.dataToShow === 'carbon_cap-req') {
      this.getCarbonCapReq();
    }
    if (this.dataToShow === 'prm-bas') {
      this.getPRMBAs();
    }
    if (this.dataToShow === 'prm-projects') {
      this.getProjectPRMBAs();
    }
    if (this.dataToShow === 'prm-req') {
      this.getPRMReq();
    }
    if (this.dataToShow === 'prm-project_elcc') {
      this.getProjectELCCChars();
    }
    if (this.dataToShow === 'prm-elcc') {
      this.getELCCSurface();
    }
    if (this.dataToShow === 'prm-energy_only') {
      this.getEnergyOnly();
    }
    if (this.dataToShow === 'local_capacity-bas') {
      this.getLocalCapacityBAs();
    }
    if (this.dataToShow === 'local_capacity-projects') {
      this.getProjectLocalCapacityBAs();
    }
    if (this.dataToShow === 'local_capacity-req') {
      this.getLocalCapacityReq();
    }
    if (this.dataToShow === 'local_capacity-project_chars') {
      this.getProjectLocalCapacityChars();
    }
    if (this.dataToShow === 'tuning-tuning') {
      this.getTuning();
    }
    if (this.dataToShow === 'validation') {
      this.getValidation();
    }

  }

  getDataToShow(): void {
    this.viewDataService.dataToViewSubject
      .subscribe((dataToShow: string) => {
        this.dataToShow = dataToShow;
      });
  }

  getTemporalTimepoints(): void {
    this.viewDataService.getTemporalTimepoints(this.scenarioID)
      .subscribe(inputTableRows => {
        this.timepointsTemporalTable = inputTableRows;
        this.allTables.push(this.timepointsTemporalTable);
      });
  }

  getGeographyLoadZones(): void {
    this.viewDataService.getGeographyLoadZones(this.scenarioID)
      .subscribe(inputTableRows => {
        this.geographyLoadZonesTable = inputTableRows;
        this.allTables.push(this.geographyLoadZonesTable);
      });
  }

  getProjectLoadZones(): void {
    this.viewDataService.getProjectLoadZones(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectLoadZonesTable = inputTableRows;
        this.allTables.push(this.projectLoadZonesTable);
      });
  }

  getTransmissionLoadZones(): void {
    this.viewDataService.getTransmissionLoadZones(this.scenarioID)
      .subscribe(inputTableRows => {
        this.transmissionLoadZonesTable = inputTableRows;
        this.allTables.push(this.transmissionLoadZonesTable);
      });
  }

  getSystemLoad(): void {
    this.viewDataService.getSystemLoad(this.scenarioID)
      .subscribe(inputTableRows => {
        this.systemLoadTable = inputTableRows;
        this.allTables.push(this.systemLoadTable);
      });
  }

  getProjectPortfolio(): void {
    this.viewDataService.getProjectPortfolio(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectPortfolioTable = inputTableRows;
        this.allTables.push(this.projectPortfolioTable);
      });
  }

  getProjectExistingCapacity(): void {
    this.viewDataService.getProjectExistingCapacity(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectExistingCapacityTable = inputTableRows;
        this.allTables.push(this.projectExistingCapacityTable);
      });
  }

  getProjectExistingFixedCost(): void {
    this.viewDataService.getProjectExistingFixedCost(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectExistingFixedCostTable = inputTableRows;
        this.allTables.push(this.projectExistingFixedCostTable);
      });
  }

  getProjectNewPotential(): void {
    this.viewDataService.getProjectNewPotential(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectNewPotentialTable = inputTableRows;
        this.allTables.push(this.projectNewPotentialTable);
      });
  }

  getProjectNewCost(): void {
    this.viewDataService.getProjectNewCost(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectNewCostTable = inputTableRows;
        this.allTables.push(this.projectNewCostTable);
      });
  }

  getProjectAvailability(): void {
    this.viewDataService.getProjectAvailability(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectAvailabilityTable = inputTableRows;
        this.allTables.push(this.projectAvailabilityTable);
      });
  }

  getProjectOpChar(): void {
    this.viewDataService.getProjectOpChar(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectOpCharTable = inputTableRows;
        this.allTables.push(this.projectOpCharTable);
      });
  }

  getFuels(): void {
    this.viewDataService.getFuels(this.scenarioID)
      .subscribe(inputTableRows => {
        this.fuelsTable = inputTableRows;
        this.allTables.push(this.fuelsTable);
      });
  }

  getFuelPrices(): void {
    this.viewDataService.getFuelPrices(this.scenarioID)
      .subscribe(inputTableRows => {
        this.fuelPricesTable = inputTableRows;
        this.allTables.push(this.fuelPricesTable);
      });
  }

  getTransmissionPortfolio(): void {
    this.viewDataService.getTransmissionPortfolio(this.scenarioID)
      .subscribe(inputTableRows => {
        this.transmissionPortfolioTable = inputTableRows;
        this.allTables.push(this.transmissionPortfolioTable);
      });
  }

  getTransmissionExistingCapacity(): void {
    this.viewDataService.getTransmissionExistingCapacity(this.scenarioID)
      .subscribe(inputTableRows => {
        this.transmissionExistingCapacityTable = inputTableRows;
        this.allTables.push(this.transmissionExistingCapacityTable);
      });
  }

  getTransmissionOpChar(): void {
    this.viewDataService.getTransmissionOpChar(this.scenarioID)
      .subscribe(inputTableRows => {
        this.transmissionOpCharTable = inputTableRows;
        this.allTables.push(this.transmissionOpCharTable);
      });
  }

  getTransmissionHurdleRates(): void {
    this.viewDataService.getTransmissionHurdleRates(this.scenarioID)
      .subscribe(inputTableRows => {
        this.transmissionHurdleRatesTable = inputTableRows;
        this.allTables.push(this.transmissionHurdleRatesTable);
      });
  }

  getTransmissionSimFlowLimits(): void {
    this.viewDataService.getTransmissionSimFlowLimits(this.scenarioID)
      .subscribe(inputTableRows => {
        this.transmissionSimFlowLimitsTable = inputTableRows;
        this.allTables.push(this.transmissionSimFlowLimitsTable);
      });
  }

  getTransmissionSimFlowLimitsLineGroups(): void {
    this.viewDataService.getTransmissionSimFlowLimitsLineGroups(this.scenarioID)
      .subscribe(inputTableRows => {
        this.transmissionSimFlowLimitLineGroupsTable = inputTableRows;
        this.allTables.push(this.transmissionSimFlowLimitLineGroupsTable);
      });
  }

  getLFUpBAs(): void {
    this.viewDataService.getLFUpBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.lfUpBAsTable = inputTableRows;
        this.allTables.push(this.lfUpBAsTable);
      });
  }

  getProjectLFUpBAs(): void {
    this.viewDataService.getProjectLFUpBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectLFUpBAsTable = inputTableRows;
        this.allTables.push(this.projectLFUpBAsTable);
      });
  }

  getLFUpReq(): void {
    this.viewDataService.getLFUpReq(this.scenarioID)
      .subscribe(inputTableRows => {
        this.lfUpReqTable = inputTableRows;
        this.allTables.push(this.lfUpReqTable);
      });
  }

  getLFDownBAs(): void {
    this.viewDataService.getLFDownBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.lfDownBAsTable = inputTableRows;
        this.allTables.push(this.lfDownBAsTable);
      });
  }

  getProjectLFDownBAs(): void {
    this.viewDataService.getProjectLFDownBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectLFDownBAsTable = inputTableRows;
        this.allTables.push(this.projectLFDownBAsTable);
      });
  }

  getLFDownReq(): void {
    this.viewDataService.getLFDownReq(this.scenarioID)
      .subscribe(inputTableRows => {
        this.lfDownReqTable = inputTableRows;
        this.allTables.push(this.lfDownReqTable);
      });
  }

  getRegUpBAs(): void {
    this.viewDataService.getRegUpBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.regUpBAsTable = inputTableRows;
        this.allTables.push(this.regUpBAsTable);
      });
  }

  getProjectRegUpBAs(): void {
    this.viewDataService.getProjectRegUpBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectRegUpBAsTable = inputTableRows;
        this.allTables.push(this.projectRegUpBAsTable);
      });
  }

  getRegUpReq(): void {
    this.viewDataService.getRegUpReq(this.scenarioID)
      .subscribe(inputTableRows => {
        this.regUpReqTable = inputTableRows;
        this.allTables.push(this.regUpReqTable);
      });
  }

  getRegDownBAs(): void {
    this.viewDataService.getRegDownBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.regDownBAsTable = inputTableRows;
        this.allTables.push(this.regDownBAsTable);
      });
  }

  getProjectRegDownBAs(): void {
    this.viewDataService.getProjectRegDownBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectRegDownBAsTable = inputTableRows;
        this.allTables.push(this.projectRegDownBAsTable);
      });
  }

  getRegDownReq(): void {
    this.viewDataService.getRegDownReq(this.scenarioID)
      .subscribe(inputTableRows => {
        this.regDownReqTable = inputTableRows;
        this.allTables.push(this.regDownReqTable);
      });
  }

  getSpinBAs(): void {
    this.viewDataService.getSpinBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.spinBAsTable = inputTableRows;
        this.allTables.push(this.spinBAsTable);
      });
  }

  getProjectSpinBAs(): void {
    this.viewDataService.getProjectSpinBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectSpinBAsTable = inputTableRows;
        this.allTables.push(this.projectSpinBAsTable);
      });
  }

  getSpinReq(): void {
    this.viewDataService.getSpinReq(this.scenarioID)
      .subscribe(inputTableRows => {
        this.spinReqTable = inputTableRows;
        this.allTables.push(this.spinReqTable);
      });
  }

  getFreqRespBAs(): void {
    this.viewDataService.getFreqRespBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.freqRespBAsTable = inputTableRows;
        this.allTables.push(this.freqRespBAsTable);
      });
  }

  getProjectFreqRespBAs(): void {
    this.viewDataService.getProjectFreqRespBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectFreqRespBAsTable = inputTableRows;
        this.allTables.push(this.projectFreqRespBAsTable);
      });
  }

  getFreqRespReq(): void {
    this.viewDataService.getFreqRespReq(this.scenarioID)
      .subscribe(inputTableRows => {
        this.freqRespReqTable = inputTableRows;
        this.allTables.push(this.freqRespReqTable);
      });
  }

  getRPSBAs(): void {
    this.viewDataService.getRPSBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.rpsBAsTable = inputTableRows;
        this.allTables.push(this.rpsBAsTable);
      });
  }

  getProjectRPSBAs(): void {
    this.viewDataService.getProjectRPSBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectRPSBAsTable = inputTableRows;
        this.allTables.push(this.projectRPSBAsTable);
      });
  }

  getRPSReq(): void {
    this.viewDataService.getRPSReq(this.scenarioID)
      .subscribe(inputTableRows => {
        this.rpsReqTable = inputTableRows;
        this.allTables.push(this.rpsReqTable);
      });
  }

  getCarbonCapBAs(): void {
    this.viewDataService.getCarbonCapBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.carbonCapBAsTable = inputTableRows;
        this.allTables.push(this.carbonCapBAsTable);
      });
  }

  getProjectCarbonCapBAs(): void {
    this.viewDataService.getProjectCarbonCapBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectCarbonCapBAsTable = inputTableRows;
        this.allTables.push(this.projectCarbonCapBAsTable);
      });
  }

  getTransmissionCarbonCapBAs(): void {
    this.viewDataService.getTransmissionCarbonCapBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.transmissionCarbonCapBAsTable = inputTableRows;
        this.allTables.push(this.transmissionCarbonCapBAsTable);
      });
  }

  getCarbonCapReq(): void {
    this.viewDataService.getCarbonCapReq(this.scenarioID)
      .subscribe(inputTableRows => {
        this.carbonCapReqTable = inputTableRows;
        this.allTables.push(this.carbonCapReqTable);
      });
  }

  getPRMBAs(): void {
    this.viewDataService.getPRMBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.prmBAsTable = inputTableRows;
        this.allTables.push(this.prmBAsTable);
      });
  }

  getProjectPRMBAs(): void {
    this.viewDataService.getProjectPRMBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectPRMBAsTable = inputTableRows;
        this.allTables.push(this.projectPRMBAsTable);
      });
  }

  getPRMReq(): void {
    this.viewDataService.getPRMReq(this.scenarioID)
      .subscribe(inputTableRows => {
        this.prmReqTable = inputTableRows;
        this.allTables.push(this.prmReqTable);
      });
  }

  getProjectELCCChars(): void {
    this.viewDataService.getProjectELCCChars(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectELCCCharsTable = inputTableRows;
        this.allTables.push(this.projectELCCCharsTable);
      });
  }

  getELCCSurface(): void {
    this.viewDataService.getELCCSurface(this.scenarioID)
      .subscribe(inputTableRows => {
        this.elccSurfaceTable = inputTableRows;
        this.allTables.push(this.elccSurfaceTable);
      });
  }

  getEnergyOnly(): void {
    this.viewDataService.getEnergyOnly(this.scenarioID)
      .subscribe(inputTableRows => {
        this.energyOnlyTable = inputTableRows;
        this.allTables.push(this.energyOnlyTable);
      });
  }

  getLocalCapacityBAs(): void {
    this.viewDataService.getLocalCapacityBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.localCapacityBAsTable = inputTableRows;
        this.allTables.push(this.localCapacityBAsTable);
      });
  }

  getProjectLocalCapacityBAs(): void {
    this.viewDataService.getProjectLocalCapacityBAs(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectLocalCapacityBAsTable = inputTableRows;
        this.allTables.push(this.projectLocalCapacityBAsTable);
      });
  }

  getLocalCapacityReq(): void {
    this.viewDataService.getLocalCapacityReq(this.scenarioID)
      .subscribe(inputTableRows => {
        this.localCapacityReqTable = inputTableRows;
        this.allTables.push(this.localCapacityReqTable);
      });
  }

  getProjectLocalCapacityChars(): void {
    this.viewDataService.getProjectLocalCapacityChars(this.scenarioID)
      .subscribe(inputTableRows => {
        this.projectLocalCapacityCharsTable = inputTableRows;
        this.allTables.push(this.projectLocalCapacityCharsTable);
      });
  }

  getTuning(): void {
    this.viewDataService.getTuning(this.scenarioID)
      .subscribe(inputTableRows => {
        this.tuningTable = inputTableRows;
        this.allTables.push(this.tuningTable);
      });
  }

  getValidation(): void {
    this.viewDataService.getValidation(this.scenarioID)
      .subscribe(inputTableRows => {
        this.validationTable = inputTableRows;
        this.allTables.push(this.validationTable);
      });
  }

  getScenarioName(scenarioID): void {
    this.scenarioDetailService.getScenarioDetailAPI(scenarioID)
      .subscribe(scenarioDetailAPI => {
        this.scenarioName = scenarioDetailAPI.scenarioName;
      });
  }

  goBack(): void {
    this.location.back();
  }

}
