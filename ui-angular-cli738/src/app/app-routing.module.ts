import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { ScenariosComponent } from './scenarios/scenarios.component';
import { SettingsComponent } from './settings/settings.component';

const appRoutes: Routes = [
  { path: 'scenarios', component: ScenariosComponent },
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
