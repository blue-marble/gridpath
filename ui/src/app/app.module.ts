import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms'; // <-- NgModel lives here
import { HttpClientModule } from '@angular/common/http'
import { AppRoutingModule } from './app-routing.module';
import { ReactiveFormsModule } from '@angular/forms';


import { AppComponent } from './app.component';
import { ScenariosComponent } from './scenarios/scenarios.component';
import { SettingsComponent } from './settings/settings.component';
import { ScenarioDetailComponent } from './scenario-detail/scenario-detail.component';
import { ScenarioNewComponent } from './scenario-new/scenario-new.component';
import { HomeComponent } from './home/home.component';
import { ViewDataComponent } from './view-data/view-data.component';


@NgModule({
  declarations: [
    AppComponent,
    ScenariosComponent,
    SettingsComponent,
    ScenarioDetailComponent,
    ScenarioNewComponent,
    HomeComponent,
    ViewDataComponent
  ],
  imports: [
    BrowserModule,
    FormsModule,
    HttpClientModule,
    AppRoutingModule,
    ReactiveFormsModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
