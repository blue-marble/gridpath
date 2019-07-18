import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ScenarioEditService {

  private scenarioToEditObservable = new Subject();
  currentScenarioToEdit = this.scenarioToEditObservable;

  constructor() {}

  // TODO: https://stackoverflow.com/questions/39950743/angular-2-rxjs-observable-skipping-subscribe-on-first-call
  changeMessage(scenarioToEditID: number) {
    this.scenarioToEditObservable.next(scenarioToEditID);
  }
}
