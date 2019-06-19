import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms'; // <-- NgModel lives here


import { AppComponent } from './app.component';
import { ScenariosComponent } from './scenarios/scenarios.component';
import { IPCTestComponent } from './ipctest/ipctest.component';


@NgModule({
  declarations: [
    AppComponent,
    ScenariosComponent,
    IPCTestComponent
  ],
  imports: [
    BrowserModule,
    FormsModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
