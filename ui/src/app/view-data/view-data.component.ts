import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';

import { ViewDataService } from './view-data.service';
import { TimepointsTemporalRow } from './view-data';

@Component({
  selector: 'app-view-data',
  templateUrl: './view-data.component.html',
  styleUrls: ['./view-data.component.css']
})
export class ViewDataComponent implements OnInit {

  dataToShow: string;

  // For viewing input table data
  timepointsTemporalRows: TimepointsTemporalRow[];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private location: Location,
    private viewDataService: ViewDataService
  ) { }

  ngOnInit() {
    // Get flag for which table/s to show
    this.getDataToShow();
    console.log('Received data to show, ', this.dataToShow);

    // Temporal timepoints input data table
    this.getTemporalTimepointsData();
  }

  getDataToShow(): void {
    this.viewDataService.dataToViewSubject
      .subscribe((dataToShow: string) => {
        this.dataToShow = dataToShow;
      });
  }

  getTemporalTimepointsData(): void {
    this.viewDataService.getTemporalTimepointsData()
      .subscribe(inputTableRows => {
        this.timepointsTemporalRows = inputTableRows;
      });
  }

  goBack(): void {
    this.location.back();
  }

}
