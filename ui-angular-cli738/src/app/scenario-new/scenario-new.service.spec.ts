import { TestBed } from '@angular/core/testing';

import { ScenarioNewService } from './scenario-new.service';

describe('ScenarioNewService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: ScenarioNewService = TestBed.get(ScenarioNewService);
    expect(service).toBeTruthy();
  });
});
