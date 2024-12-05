import { Component } from '@angular/core';
import { AuthService } from '@auth0/auth0-angular';

@Component({
    selector: 'auth-button',
    templateUrl: 'authbutton.component.html',
    standalone: true
})

export class AuthButtonComponent {
    constructor(public auth: AuthService) {}
}