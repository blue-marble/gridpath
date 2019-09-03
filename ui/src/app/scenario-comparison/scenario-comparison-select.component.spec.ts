import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ScenarioComparisonSelectComponent } from './scenario-comparison-select.component';

describe('ScenarioComparisonSelectComponent', () => {
  let component: ScenarioComparisonSelectComponent;
  let fixture: ComponentFixture<ScenarioComparisonSelectComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ScenarioComparisonSelectComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ScenarioComparisonSelectComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
