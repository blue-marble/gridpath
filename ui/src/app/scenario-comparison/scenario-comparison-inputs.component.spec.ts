import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ScenarioComparisonInputsComponent } from './scenario-comparison-inputs.component';

describe('ScenarioComparisonComponent', () => {
  let component: ScenarioComparisonInputsComponent;
  let fixture: ComponentFixture<ScenarioComparisonInputsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ScenarioComparisonInputsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ScenarioComparisonInputsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
