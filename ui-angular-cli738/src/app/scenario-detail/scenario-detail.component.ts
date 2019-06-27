import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';

import { ScenarioDetail } from './scenario-detail'
import { ScenarioDetailService } from './scenario-detail.service'

@Component({
  selector: 'app-scenario-detail',
  templateUrl: './scenario-detail.component.html',
  styleUrls: ['./scenario-detail.component.css']
})

export class ScenarioDetailComponent implements OnInit {

  scenarioDetail: ScenarioDetail[];
  id: number;
  private sub: any;

  constructor(private route: ActivatedRoute,
    private scenarioDetailService: ScenarioDetailService,
    private location: Location) {
  }

  ngOnInit(): void {
    // The ActivatedRoute service provides a params Observable which we can
    // subscribe to in order to get the route parameters
    this.sub = this.route.params.subscribe(params => {
       this.id = +params['id'];
       console.log(`Scenario ID is ${this.id}`)
    });
    this.getScenarioDetail(this.id);
  }

  getScenarioDetail(id): void {
    console.log(`Getting scenario detail for scenario ${id}`);
    this.scenarioDetailService.getScenarioDetail(id)
      .subscribe(scenarioDetail => this.scenarioDetail = scenarioDetail);
  }

  goBack(): void {
    this.location.back();
  }

}
