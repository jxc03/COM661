import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { DataService } from './data.service';

@Component({
    selector: 'businesses',
    standalone: true,
    imports: [RouterOutlet],
    providers: [DataService],
    templateUrl: './businesses.component.html',
    styleUrl: './businesses.component.css'
})

export class BusinessesComponent {
    business_list: any;
    constructor(private dataService: DataService) { }
    ngOnInit() {
    this.business_list = this.dataService.getBusinesses();
    }
}