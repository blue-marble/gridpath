import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ScenarioInputsComponent } from './scenario-inputs.component';

describe('ViewDataComponent', () => {
  let component: ScenarioInputsComponent;
  let fixture: ComponentFixture<ScenarioInputsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ScenarioInputsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ScenarioInputsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
