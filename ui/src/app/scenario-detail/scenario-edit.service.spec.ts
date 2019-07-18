import { TestBed } from '@angular/core/testing';

import { ScenarioEditService } from './scenario-edit.service';

describe('ScenarioEditService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: ScenarioEditService = TestBed.get(ScenarioEditService);
    expect(service).toBeTruthy();
  });
});
