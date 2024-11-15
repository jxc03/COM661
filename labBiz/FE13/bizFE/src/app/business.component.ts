import { Component } from '@angular/core';
import { RouterOutlet, ActivatedRoute } from '@angular/router';
import { DataService } from './data.service';

@Component({
  selector: 'business',
  standalone: true,
  imports: [RouterOutlet],
  providers: [DataService],
  templateUrl: './business.component.html',
  styleUrl: './business.component.css'
})

export class BusinessComponent {
  business_list: any;

  constructor(public dataService: DataService, 
              private route: ActivatedRoute) {}

  ngOnInit() {
    this.business_list = this.dataService.getBusiness(
                            this.route.snapshot.paramMap.get('id')
                          );
  }
}