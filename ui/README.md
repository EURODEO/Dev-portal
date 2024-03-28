# Ui
first in the project directory you need to install all packages
### `npm install`

Next you need to initialize env config. 

Make sure the generate_env-config.sh file is executable by running ```chmod +x generate_env-config.sh``` in shell. 

Now you can initialize configs by running ``` ./generate_env-config.sh > ./public/env-config.js ```. 

Open generated public/env-config.js file and replace the existing content with:

```javascript
window.REACT_APP_KEYCLOAK_URL="http://localhost:8080/";
window.REACT_APP_LOGOUT_URL="http://localhost:3002";
window.REACT_APP_KEYCLOAK_REALM="test";
window.REACT_APP_KEYCLOAK_CLIENTID="frontend";
window.REACT_APP_BACKEND_URL="http://localhost:8082";
```

In the project directory, you can run:

### `npm run start`

Runs the app in the development mode.\
Open [http://localhost:3002](http://localhost:3002) to view it in your browser.

