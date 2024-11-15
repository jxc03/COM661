import { Component } from '@angular/core';
import { RouterOutlet, ActivatedRoute } from '@angular/router';
import { DataService } from './data.service';
import { CommonModule} from '@angular/common';
import { GoogleMapsModule } from '@angular/google-maps';

@Component({
  selector: 'business',
  standalone: true,
  imports: [RouterOutlet, CommonModule, GoogleMapsModule],
  providers: [DataService],
  templateUrl: './business.component.html',
  styleUrl: './business.component.css'
})

export class BusinessComponent {
  business_list: any;
  business_lat: any;
  business_lng: any;
  map_options: google.maps.MapOptions = {};
  map_locations: any[] = [];

  constructor(public dataService: DataService, 
              private route: ActivatedRoute) {}

ngOnInit() {
    this.business_list = this.dataService.getBusiness(
                            this.route.snapshot.paramMap.get('id')
                          );
    this.business_lat = this.business_list[0].location.coordinates[0]; 
    this.business_lng = this.business_list[0].location.coordinates[1];
    this.map_locations.push({
      lat: this.business_lat, lng: this.business_lng
    });
    this.map_options = {
      mapId: "DEMO_MAP_ID",
      center: {
        lat: this.business_lat,
        lng: this.business_lng
      },
      zoom: 13,
    };
  }
}
