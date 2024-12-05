import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';
import { provideAuth0 } from '@auth0/auth0-angular';
import { provideHttpClient } from '@angular/common/http';

bootstrapApplication(AppComponent, {
  providers: [
    provideAuth0({
      domain: 'dev-tnafsghc1wquofma.us.auth0.com',
      clientId: 'Ii0Iz28p8KliUBpRe2CI8xaD49hMgUDE',
      authorizationParams: {
        redirect_uri: window.location.origin
      }
    }),
  ]
});


bootstrapApplication(AppComponent, appConfig)
.catch((err) => console.error(err));



