import { TestBed } from '@angular/core/testing';

import { ScenarioResultsService } from './scenario-results.service';

describe('ScenarioResultsService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: ScenarioResultsService = TestBed.get(ScenarioResultsService);
    expect(service).toBeTruthy();
  });
});
