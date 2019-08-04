import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';

import { ViewDataService } from './view-data.service';
import { ViewDataTable } from './view-data';

@Component({
  selector: 'app-view-data',
  templateUrl: './view-data.component.html',
  styleUrls: ['./view-data.component.css']
})
export class ViewDataComponent implements OnInit {

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

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private location: Location,
    private viewDataService: ViewDataService
  ) { }

  ngOnInit() {
    this.allTables = [];

    // Get flag for which table/s to show
    this.getDataToShow();
    console.log('Received data to show, ', this.dataToShow);

    // Temporal timepoints input data table
    if (this.dataToShow === 'temporal') {
      this.getTemporalTimepoints();
    }
    if (this.dataToShow === 'geography_load_zones') {
      this.getGeographyLoadZones();
    }
    if (this.dataToShow === 'project_load_zones') {
      this.getProjectLoadZones();
    }
    if (this.dataToShow === 'transmission_load_zones') {
      this.getTransmissionLoadZones();
    }
    if (this.dataToShow === 'load_profile') {
      this.getSystemLoad();
    }
    if (this.dataToShow === 'project_portfolio') {
      this.getProjectPortfolio();
    }
    if (this.dataToShow === 'project_existing_capacity') {
      this.getProjectExistingCapacity();
    }
    if (this.dataToShow === 'project_existing_fixed_cost') {
      this.getProjectExistingFixedCost();
    }
    if (this.dataToShow === 'project_new_potential') {
      this.getProjectNewPotential();
    }
    if (this.dataToShow === 'project_new_cost') {
      this.getProjectNewCost();
    }
    if (this.dataToShow === 'project_availability') {
      this.getProjectAvailability();
    }
    if (this.dataToShow === 'project_operating_chars') {
      this.getProjectOpChar();
    }
    if (this.dataToShow === 'project_fuels') {
      this.getFuels();
    }
    if (this.dataToShow === 'fuel_prices') {
      this.getFuelPrices();
    }
    if (this.dataToShow === 'transmission_portfolio') {
      this.getTransmissionPortfolio();
    }
    if (this.dataToShow === 'transmission_existing_capacity') {
      this.getTransmissionExistingCapacity();
    }
    if (this.dataToShow === 'transmission_operational_chars') {
      this.getTransmissionOpChar();
    }
    if (this.dataToShow === 'transmission_hurdle_rates') {
      this.getTransmissionHurdleRates();
    }
    if (this.dataToShow === 'transmission_simultaneous_flow_limits') {
      this.getTransmissionSimFlowLimits();
    }
    if (this.dataToShow ===
      'transmission_simultaneous_flow_limit_line_groups') {
      this.getTransmissionSimFlowLimitsLineGroups();
    }
    if (this.dataToShow === 'geography_lf_up_bas') {
      this.getLFUpBAs();
    }
    if (this.dataToShow === 'project_lf_up_bas') {
      this.getProjectLFUpBAs();
    }
    if (this.dataToShow === 'load_following_reserves_up_profile') {
      this.getLFUpReq();
    }
    if (this.dataToShow === 'geography_lf_down_bas') {
      this.getLFDownBAs();
    }
    if (this.dataToShow === 'project_lf_down_bas') {
      this.getProjectLFDownBAs();
    }
    if (this.dataToShow === 'load_following_reserves_down_profile') {
      this.getLFDownReq();
    }
    if (this.dataToShow === 'geography_reg_up_bas') {
      this.getRegUpBAs();
    }
    if (this.dataToShow === 'project_reg_up_bas') {
      this.getProjectRegUpBAs();
    }
    if (this.dataToShow === 'regulation_up_profile') {
      this.getRegUpReq();
    }
    if (this.dataToShow === 'geography_reg_down_bas') {
      this.getRegDownBAs();
    }
    if (this.dataToShow === 'project_reg_down_bas') {
      this.getProjectRegDownBAs();
    }
    if (this.dataToShow === 'regulation_down_profile') {
      this.getRegDownReq();
    }
    if (this.dataToShow === 'geography_spin_bas') {
      this.getSpinBAs();
    }
    if (this.dataToShow === 'project_spin_bas') {
      this.getProjectSpinBAs();
    }
    if (this.dataToShow === 'spinning_reserves_profile') {
      this.getSpinReq();
    }
    if (this.dataToShow === 'geography_freq_resp_bas') {
      this.getFreqRespBAs();
    }
    if (this.dataToShow === 'project_freq_resp_bas') {
      this.getProjectFreqRespBAs();
    }
    if (this.dataToShow === 'frequency_response_profile') {
      this.getFreqRespReq();
    }
    if (this.dataToShow === 'geography_rps_areas') {
      this.getRPSBAs();
    }
    if (this.dataToShow === 'rps_target') {
      this.getProjectRPSBAs();
    }
    if (this.dataToShow === 'project_rps_areas') {
      this.getRPSReq();
    }
    if (this.dataToShow === 'carbon_cap_areas') {
      this.getCarbonCapBAs();
    }
    if (this.dataToShow === 'project_carbon_cap_areas') {
      this.getProjectCarbonCapBAs();
    }
    if (this.dataToShow === 'transmission_carbon_cap_zones') {
      this.getTransmissionCarbonCapBAs();
    }
    if (this.dataToShow === 'carbon_cap') {
      this.getCarbonCapReq();
    }
    if (this.dataToShow === 'prm_areas') {
      this.getPRMBAs();
    }
    if (this.dataToShow === 'project_prm_areas') {
      this.getProjectPRMBAs();
    }
    if (this.dataToShow === 'prm_requirement') {
      this.getPRMReq();
    }
    if (this.dataToShow === 'project_elcc_chars') {
      this.getProjectELCCChars();
    }
    if (this.dataToShow === 'elcc_surface') {
      this.getELCCSurface();
    }
    if (this.dataToShow === 'project_prm_energy_only') {
      this.getEnergyOnly();
    }
    if (this.dataToShow === 'local_capacity_areas') {
      this.getLocalCapacityBAs();
    }
    if (this.dataToShow === 'project_local_capacity_areas') {
      this.getProjectLocalCapacityBAs();
    }
    if (this.dataToShow === 'local_capacity_requirement') {
      this.getLocalCapacityReq();
    }
    if (this.dataToShow === 'project_local_capacity_chars') {
      this.getProjectLocalCapacityChars();
    }

  }

  getDataToShow(): void {
    this.viewDataService.dataToViewSubject
      .subscribe((dataToShow: string) => {
        this.dataToShow = dataToShow;
      });
  }

  getTemporalTimepoints(): void {
    this.viewDataService.getTemporalTimepoints()
      .subscribe(inputTableRows => {
        this.timepointsTemporalTable = inputTableRows;
        this.allTables.push(this.timepointsTemporalTable);
      });
  }

  getGeographyLoadZones(): void {
    this.viewDataService.getGeographyLoadZones()
      .subscribe(inputTableRows => {
        this.geographyLoadZonesTable = inputTableRows;
        this.allTables.push(this.geographyLoadZonesTable);
      });
  }

  getProjectLoadZones(): void {
    this.viewDataService.getProjectLoadZones()
      .subscribe(inputTableRows => {
        this.projectLoadZonesTable = inputTableRows;
        this.allTables.push(this.projectLoadZonesTable);
      });
  }

  getTransmissionLoadZones(): void {
    this.viewDataService.getTransmissionLoadZones()
      .subscribe(inputTableRows => {
        this.transmissionLoadZonesTable = inputTableRows;
        this.allTables.push(this.transmissionLoadZonesTable);
      });
  }

  getSystemLoad(): void {
    this.viewDataService.getSystemLoad()
      .subscribe(inputTableRows => {
        this.systemLoadTable = inputTableRows;
        this.allTables.push(this.systemLoadTable);
      });
  }

  getProjectPortfolio(): void {
    this.viewDataService.getProjectPortfolio()
      .subscribe(inputTableRows => {
        this.projectPortfolioTable = inputTableRows;
        this.allTables.push(this.projectPortfolioTable);
      });
  }

  getProjectExistingCapacity(): void {
    this.viewDataService.getProjectExistingCapacity()
      .subscribe(inputTableRows => {
        this.projectExistingCapacityTable = inputTableRows;
        this.allTables.push(this.projectExistingCapacityTable);
      });
  }

  getProjectExistingFixedCost(): void {
    this.viewDataService.getProjectExistingFixedCost()
      .subscribe(inputTableRows => {
        this.projectExistingFixedCostTable = inputTableRows;
        this.allTables.push(this.projectExistingFixedCostTable);
      });
  }

  getProjectNewPotential(): void {
    this.viewDataService.getProjectNewPotential()
      .subscribe(inputTableRows => {
        this.projectNewPotentialTable = inputTableRows;
        this.allTables.push(this.projectNewPotentialTable);
      });
  }

  getProjectNewCost(): void {
    this.viewDataService.getProjectNewCost()
      .subscribe(inputTableRows => {
        this.projectNewCostTable = inputTableRows;
        this.allTables.push(this.projectNewCostTable);
      });
  }

  getProjectAvailability(): void {
    this.viewDataService.getProjectAvailability()
      .subscribe(inputTableRows => {
        this.projectAvailabilityTable = inputTableRows;
        this.allTables.push(this.projectAvailabilityTable);
      });
  }

  getProjectOpChar(): void {
    this.viewDataService.getProjectOpChar()
      .subscribe(inputTableRows => {
        this.projectOpCharTable = inputTableRows;
        this.allTables.push(this.projectOpCharTable);
      });
  }

  getFuels(): void {
    this.viewDataService.getFuels()
      .subscribe(inputTableRows => {
        this.fuelsTable = inputTableRows;
        this.allTables.push(this.fuelsTable);
      });
  }

  getFuelPrices(): void {
    this.viewDataService.getFuelPrices()
      .subscribe(inputTableRows => {
        this.fuelPricesTable = inputTableRows;
        this.allTables.push(this.fuelPricesTable);
      });
  }

  getTransmissionPortfolio(): void {
    this.viewDataService.getTransmissionPortfolio()
      .subscribe(inputTableRows => {
        this.transmissionPortfolioTable = inputTableRows;
        this.allTables.push(this.transmissionPortfolioTable);
      });
  }

  getTransmissionExistingCapacity(): void {
    this.viewDataService.getTransmissionExistingCapacity()
      .subscribe(inputTableRows => {
        this.transmissionExistingCapacityTable = inputTableRows;
        this.allTables.push(this.transmissionExistingCapacityTable);
      });
  }

  getTransmissionOpChar(): void {
    this.viewDataService.getTransmissionOpChar()
      .subscribe(inputTableRows => {
        this.transmissionOpCharTable = inputTableRows;
        this.allTables.push(this.transmissionOpCharTable);
      });
  }

  getTransmissionHurdleRates(): void {
    this.viewDataService.getTransmissionHurdleRates()
      .subscribe(inputTableRows => {
        this.transmissionHurdleRatesTable = inputTableRows;
        this.allTables.push(this.transmissionHurdleRatesTable);
      });
  }

  getTransmissionSimFlowLimits(): void {
    this.viewDataService.getTransmissionSimFlowLimits()
      .subscribe(inputTableRows => {
        this.transmissionSimFlowLimitsTable = inputTableRows;
        this.allTables.push(this.transmissionSimFlowLimitsTable);
      });
  }

  getTransmissionSimFlowLimitsLineGroups(): void {
    this.viewDataService.getTransmissionSimFlowLimitsLineGroups()
      .subscribe(inputTableRows => {
        this.transmissionSimFlowLimitLineGroupsTable = inputTableRows;
        this.allTables.push(this.transmissionSimFlowLimitLineGroupsTable);
      });
  }

  getLFUpBAs(): void {
    this.viewDataService.getLFUpBAs()
      .subscribe(inputTableRows => {
        this.lfUpBAsTable = inputTableRows;
        this.allTables.push(this.lfUpBAsTable);
      });
  }

  getProjectLFUpBAs(): void {
    this.viewDataService.getProjectLFUpBAs()
      .subscribe(inputTableRows => {
        this.projectLFUpBAsTable = inputTableRows;
        this.allTables.push(this.projectLFUpBAsTable);
      });
  }

  getLFUpReq(): void {
    this.viewDataService.getLFUpReq()
      .subscribe(inputTableRows => {
        this.lfUpReqTable = inputTableRows;
        this.allTables.push(this.lfUpReqTable);
      });
  }

  getLFDownBAs(): void {
    this.viewDataService.getLFDownBAs()
      .subscribe(inputTableRows => {
        this.lfDownBAsTable = inputTableRows;
        this.allTables.push(this.lfDownBAsTable);
      });
  }

  getProjectLFDownBAs(): void {
    this.viewDataService.getProjectLFDownBAs()
      .subscribe(inputTableRows => {
        this.projectLFDownBAsTable = inputTableRows;
        this.allTables.push(this.projectLFDownBAsTable);
      });
  }

  getLFDownReq(): void {
    this.viewDataService.getLFDownReq()
      .subscribe(inputTableRows => {
        this.lfDownReqTable = inputTableRows;
        this.allTables.push(this.lfDownReqTable);
      });
  }

  getRegUpBAs(): void {
    this.viewDataService.getRegUpBAs()
      .subscribe(inputTableRows => {
        this.regUpBAsTable = inputTableRows;
        this.allTables.push(this.regUpBAsTable);
      });
  }

  getProjectRegUpBAs(): void {
    this.viewDataService.getProjectRegUpBAs()
      .subscribe(inputTableRows => {
        this.projectRegUpBAsTable = inputTableRows;
        this.allTables.push(this.projectRegUpBAsTable);
      });
  }

  getRegUpReq(): void {
    this.viewDataService.getRegUpReq()
      .subscribe(inputTableRows => {
        this.regUpReqTable = inputTableRows;
        this.allTables.push(this.regUpReqTable);
      });
  }

  getRegDownBAs(): void {
    this.viewDataService.getRegDownBAs()
      .subscribe(inputTableRows => {
        this.regDownBAsTable = inputTableRows;
        this.allTables.push(this.regDownBAsTable);
      });
  }

  getProjectRegDownBAs(): void {
    this.viewDataService.getProjectRegDownBAs()
      .subscribe(inputTableRows => {
        this.projectRegDownBAsTable = inputTableRows;
        this.allTables.push(this.projectRegDownBAsTable);
      });
  }

  getRegDownReq(): void {
    this.viewDataService.getRegDownReq()
      .subscribe(inputTableRows => {
        this.regDownReqTable = inputTableRows;
        this.allTables.push(this.regDownReqTable);
      });
  }

  getSpinBAs(): void {
    this.viewDataService.getSpinBAs()
      .subscribe(inputTableRows => {
        this.spinBAsTable = inputTableRows;
        this.allTables.push(this.spinBAsTable);
      });
  }

  getProjectSpinBAs(): void {
    this.viewDataService.getProjectSpinBAs()
      .subscribe(inputTableRows => {
        this.projectSpinBAsTable = inputTableRows;
        this.allTables.push(this.projectSpinBAsTable);
      });
  }

  getSpinReq(): void {
    this.viewDataService.getSpinReq()
      .subscribe(inputTableRows => {
        this.spinReqTable = inputTableRows;
        this.allTables.push(this.spinReqTable);
      });
  }

  getFreqRespBAs(): void {
    this.viewDataService.getFreqRespBAs()
      .subscribe(inputTableRows => {
        this.freqRespBAsTable = inputTableRows;
        this.allTables.push(this.freqRespBAsTable);
      });
  }

  getProjectFreqRespBAs(): void {
    this.viewDataService.getProjectFreqRespBAs()
      .subscribe(inputTableRows => {
        this.projectFreqRespBAsTable = inputTableRows;
        this.allTables.push(this.projectFreqRespBAsTable);
      });
  }

  getFreqRespReq(): void {
    this.viewDataService.getFreqRespReq()
      .subscribe(inputTableRows => {
        this.freqRespReqTable = inputTableRows;
        this.allTables.push(this.freqRespReqTable);
      });
  }

  getRPSBAs(): void {
    this.viewDataService.getRPSBAs()
      .subscribe(inputTableRows => {
        this.rpsBAsTable = inputTableRows;
        this.allTables.push(this.rpsBAsTable);
      });
  }

  getProjectRPSBAs(): void {
    this.viewDataService.getProjectRPSBAs()
      .subscribe(inputTableRows => {
        this.projectRPSBAsTable = inputTableRows;
        this.allTables.push(this.projectRPSBAsTable);
      });
  }

  getRPSReq(): void {
    this.viewDataService.getRPSReq()
      .subscribe(inputTableRows => {
        this.rpsReqTable = inputTableRows;
        this.allTables.push(this.rpsReqTable);
      });
  }

  getCarbonCapBAs(): void {
    this.viewDataService.getCarbonCapBAs()
      .subscribe(inputTableRows => {
        this.carbonCapBAsTable = inputTableRows;
        this.allTables.push(this.carbonCapBAsTable);
      });
  }

  getProjectCarbonCapBAs(): void {
    this.viewDataService.getProjectCarbonCapBAs()
      .subscribe(inputTableRows => {
        this.projectCarbonCapBAsTable = inputTableRows;
        this.allTables.push(this.projectCarbonCapBAsTable);
      });
  }

  getTransmissionCarbonCapBAs(): void {
    this.viewDataService.getTransmissionCarbonCapBAs()
      .subscribe(inputTableRows => {
        this.transmissionCarbonCapBAsTable = inputTableRows;
        this.allTables.push(this.transmissionCarbonCapBAsTable);
      });
  }

  getCarbonCapReq(): void {
    this.viewDataService.getCarbonCapReq()
      .subscribe(inputTableRows => {
        this.carbonCapReqTable = inputTableRows;
        this.allTables.push(this.carbonCapReqTable);
      });
  }

  getPRMBAs(): void {
    this.viewDataService.getPRMBAs()
      .subscribe(inputTableRows => {
        this.prmBAsTable = inputTableRows;
        this.allTables.push(this.prmBAsTable);
      });
  }

  getProjectPRMBAs(): void {
    this.viewDataService.getProjectPRMBAs()
      .subscribe(inputTableRows => {
        this.projectPRMBAsTable = inputTableRows;
        this.allTables.push(this.projectPRMBAsTable);
      });
  }

  getPRMReq(): void {
    this.viewDataService.getPRMReq()
      .subscribe(inputTableRows => {
        this.prmReqTable = inputTableRows;
        this.allTables.push(this.prmReqTable);
      });
  }

  getProjectELCCChars(): void {
    this.viewDataService.getProjectELCCChars()
      .subscribe(inputTableRows => {
        this.projectELCCCharsTable = inputTableRows;
        this.allTables.push(this.projectELCCCharsTable);
      });
  }

  getELCCSurface(): void {
    this.viewDataService.getELCCSurface()
      .subscribe(inputTableRows => {
        this.elccSurfaceTable = inputTableRows;
        this.allTables.push(this.elccSurfaceTable);
      });
  }

  getEnergyOnly(): void {
    this.viewDataService.getEnergyOnly()
      .subscribe(inputTableRows => {
        this.energyOnlyTable = inputTableRows;
        this.allTables.push(this.energyOnlyTable);
      });
  }

  getLocalCapacityBAs(): void {
    this.viewDataService.getLocalCapacityBAs()
      .subscribe(inputTableRows => {
        this.localCapacityBAsTable = inputTableRows;
        this.allTables.push(this.localCapacityBAsTable);
      });
  }

  getProjectLocalCapacityBAs(): void {
    this.viewDataService.getProjectLocalCapacityBAs()
      .subscribe(inputTableRows => {
        this.projectLocalCapacityBAsTable = inputTableRows;
        this.allTables.push(this.projectLocalCapacityBAsTable);
      });
  }

  getLocalCapacityReq(): void {
    this.viewDataService.getLocalCapacityReq()
      .subscribe(inputTableRows => {
        this.localCapacityReqTable = inputTableRows;
        this.allTables.push(this.localCapacityReqTable);
      });
  }

  getProjectLocalCapacityChars(): void {
    this.viewDataService.getProjectLocalCapacityChars()
      .subscribe(inputTableRows => {
        this.projectLocalCapacityCharsTable = inputTableRows;
        this.allTables.push(this.projectLocalCapacityCharsTable);
      });
  }

  goBack(): void {
    this.location.back();
  }

}
