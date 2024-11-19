import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { BusinessesComponent } from './businesses.component';
import jsonData from '../assets/data/foodPlacesDB.foodPlaces.json'


@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, BusinessesComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'foodPlacesFE';
  ngOnInit() {
    console.log(jsonData);
  }
}
