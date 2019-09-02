import { TestBed } from '@angular/core/testing';

import { ScenarioInputsService } from './scenario-inputs.service';

describe('ViewDataService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: ScenarioInputsService = TestBed.get(ScenarioInputsService);
    expect(service).toBeTruthy();
  });
});
