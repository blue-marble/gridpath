import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { Router} from '@angular/router';

@Component({
  selector: 'app-scenario-comparison-select',
  templateUrl: './scenario-comparison-select.component.html',
  styleUrls: ['./scenario-comparison-select.component.css']
})
export class ScenarioComparisonSelectComponent implements OnInit {

  constructor(
    private location: Location,
    private router: Router
  ) { }

  ngOnInit() {
  }

  compareScenarioInputs(): void {

    this.router.navigate(['/scenario-comparison']);
  }

  compareScenarioResults(): void {

  }

  goBack(): void {
    this.location.back();
  }
}
