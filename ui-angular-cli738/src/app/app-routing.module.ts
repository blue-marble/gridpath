import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { ScenariosComponent } from './scenarios/scenarios.component';
import { ScenarioDetailComponent }
  from './scenario-detail/scenario-detail.component';
import { SettingsComponent } from './settings/settings.component';

const appRoutes: Routes = [
  { path: 'scenarios', component: ScenariosComponent },
  { path: 'scenario/:id', component: ScenarioDetailComponent },
  { path: 'settings', component: SettingsComponent },
  { path: '',
    redirectTo: '/scenarios',
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
