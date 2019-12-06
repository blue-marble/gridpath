import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { HomeComponent } from './home/home.component';
import { ScenariosComponent } from './scenarios/scenarios.component';
import { ScenarioDetailComponent } from './scenario-detail/scenario-detail.component';
import { ScenarioResultsComponent } from './scenario-results/scenario-results.component';
import { ScenarioInputsComponent } from './scenario-inputs/scenario-inputs.component';
import { ScenarioNewComponent } from './scenario-new/scenario-new.component';
import { SettingsComponent } from './settings/settings.component';
import { ViewDataComponent } from './view-data/view-data.component';
import { ScenarioComparisonSelectComponent } from './scenario-comparison/scenario-comparison-select.component';
import { ScenarioComparisonInputsComponent } from './scenario-comparison/scenario-comparison-inputs.component';
import { ScenarioComparisonResultsComponent } from './scenario-comparison/scenario-comparison-results.component';

const appRoutes: Routes = [
  { path: 'home', component: HomeComponent },
  { path: 'scenarios', component: ScenariosComponent },
  { path: 'scenario/:id', component: ScenarioDetailComponent },
  { path: 'scenario/:id/results', component: ScenarioResultsComponent },
  { path: 'scenario-inputs/:id', component: ScenarioInputsComponent },
  { path: 'scenario-comparison/select', component: ScenarioComparisonSelectComponent },
  { path: 'scenario-comparison/inputs', component: ScenarioComparisonInputsComponent },
  { path: 'scenario-comparison/results', component: ScenarioComparisonResultsComponent },
  { path: 'view-data/:id', component: ViewDataComponent },
  { path: 'scenario-new/:id', component: ScenarioNewComponent },
  { path: 'settings', component: SettingsComponent },
  { path: '',
    redirectTo: '/home',
    pathMatch: 'full'
  },
];

@NgModule({
  imports: [
    RouterModule.forRoot(
      appRoutes,
      { enableTracing: true } // <-- debugging purposes only
    )
  ],
  exports: [RouterModule]
})

export class AppRoutingModule { }
