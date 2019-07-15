import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ScenarioNewComponent } from './scenario-new.component';

describe('ScenarioNewComponent', () => {
  let component: ScenarioNewComponent;
  let fixture: ComponentFixture<ScenarioNewComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ScenarioNewComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ScenarioNewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
