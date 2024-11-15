import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import jsonData from '../assets/data/bizDB.biz.json';
import { BusinessesComponent } from './businesses.component';
import { NavComponent } from './nav.component'

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, BusinessesComponent, NavComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'bizFE';
  ngOnInit() {
    console.log(jsonData);
  }
}
