import { TestBed } from '@angular/core/testing';

import { TestComponentService } from './test-component.service';

describe('TestComponentService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: TestComponentService = TestBed.get(TestComponentService);
    expect(service).toBeTruthy();
  });
});
