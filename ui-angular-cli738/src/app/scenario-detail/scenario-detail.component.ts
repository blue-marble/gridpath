import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';

import { Scenario } from '../scenarios/scenario'
import { ScenariosService } from '../scenarios/scenarios.service'

@Component({
  selector: 'app-scenario-detail',
  templateUrl: './scenario-detail.component.html',
  styleUrls: ['./scenario-detail.component.css']
})

export class ScenarioDetailComponent implements OnInit {

  scenarioDetail: Scenario;
  id: number;
  private sub: any;

  constructor(private route: ActivatedRoute,
    private scenariosService: ScenariosService,
    private location: Location) {
  }

  ngOnInit(): void {
    // The ActivatedRoute service provides a params Observable which we can
    // subscribe to to get the route parameters
    this.sub = this.route.params.subscribe(params => {
       this.id = +params['id'];
       console.log(this.id)
    });
    this.getScenarioDetail(this.id)
  }

  getScenarioDetail(id): void {
    console.log(`Getting scenario detail for scenario ${id}`);
    this.scenariosService.getScenarioDetail(id)
      .subscribe(scenarioDetail => this.scenarioDetail = scenarioDetail);
    console.log(this.scenarioDetail);
  }

  goBack(): void {
    this.location.back();
  }

}
