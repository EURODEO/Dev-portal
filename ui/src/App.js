import React, { useState } from 'react';
import './App.css';
import "primereact/resources/themes/lara-light-indigo/theme.css";
import "primereact/resources/primereact.min.css";
import '/node_modules/primeflex/primeflex.css'
import { Button } from 'primereact/button';
import { Card } from 'primereact/card';
import { DataTable } from "primereact/datatable";
import {Column} from 'primereact/column';

import Keycloak from 'keycloak-js';
import { keyApi } from './Services/KeyService';

let initOptions = {
  url: process.env.REACT_APP_KEYCLOAK_URL,
  realm: process.env.REACT_APP_KEYCLOAK_REALM,
  clientId: process.env.REACT_APP_KEYCLOAK_CLIENTID,
  onLoad: 'check-sso', // check-sso | login-required
  KeycloakResponseType: 'code id_token token',

  // silentCheckSsoRedirectUri: (window.location.origin + "/silent-check-sso.html")
}

let kc = new Keycloak(initOptions);
let routes = [];
let apiKey ='';
let userName = '';

kc.init({
  onLoad: initOptions.onLoad,
  KeycloakResponseType: 'code id_token token',
  silentCheckSsoRedirectUri: window.location.origin + "/silent-check-sso.html", checkLoginIframe: false,
  pkceMethod: 'S256'
}).then((auth) => {
  if (!auth) {
    window.location.reload();
  } else {
    console.info("Authenticated");
    console.log('auth', auth)
    console.log('Keycloak', kc)
    kc.onTokenExpired = () => {
      console.log('token expired')
    }
  }
}, () => {
  console.error("Authenticated Failed");
});

function App() {

  const [infoMessage, setInfoMessage] = useState('');
  
  

  const  handleApiCall = async (token) => {
    try {
      const response = await keyApi.getApiKey(token);
      debugger
      apiKey = response.data.apiKey;
      routes = response.data.routes;
      userName = response.data.userName;
      return apiKey;

   
    } catch (error) {
      
    } finally {
      
    }
  }

  const  handleUserDelete = async (token, userName) => {
    try {
      debugger
      const response = await keyApi.deleteUser(token,userName);
      debugger

   
    } catch (error) {
      debugger
    } finally {
      
    }
  }

  const handleRoutes = async (routes) => {
    const listItems = routes.map((currElement, index) => {
      return {id:index, route:currElement}
    });
    setInfoMessage(generateTable(listItems));
  };

  function generateTable(routes) {
    debugger
    return(
    <DataTable value={routes}>
    <Column field="route" header="Route"></Column>
    </DataTable>);
  }

  return (
    <div className="App">
      {/* <Auth /> */}
      <div className='grid'>
        <div className='col-12'>
          <h1>Developer portal prototype</h1>
        </div>
        <div className='col-12'>
          <h1 id='app-header-2'>Secured with Keycloak</h1>
        </div>
      </div>
      <div className="grid">
        <div className="col">
        <Button onClick={() => { setInfoMessage(kc.authenticated ? 'Authenticated: TRUE' : 'Authenticated: FALSE') }} className="m-1" label='Is Authenticated' />
         
          <Button onClick={() => { kc.login() }} className='m-1' label='Login' severity="success" />
          <Button onClick={() => { handleApiCall(kc.token).then(response => {setInfoMessage('ApiKey: ' +response)}, (e)=>{setInfoMessage('Are you logged in?')}) }} className='m-1' label='Get ApiKey' severity="success" />
          <Button onClick={() => { handleRoutes(routes) }} className="m-1" label='Show routes' severity="info" />
          <Button onClick={() => { handleUserDelete(kc.token, userName) }} className="m-1" label='Delete user' severity="danger" />
          {/*<Button onClick={() => { setInfoMessage('test' + routes) }} className="m-1" label='Show routes' severity="info" /> */}
          <Button onClick={() => { setInfoMessage(JSON.stringify(kc.tokenParsed)) }} className="m-1" label='Show Parsed Access token' severity="info" />
          <Button onClick={() => { setInfoMessage(kc.isTokenExpired(5).toString()) }} className="m-1" label='Check Token expired' severity="warning" />
          <Button onClick={() => { kc.updateToken(10).then((refreshed)=>{ setInfoMessage('Token Refreshed: ' + refreshed.toString()) }, (e)=>{setInfoMessage('Refresh Error')}) }} className="m-1" label='Update Token' />  {/** 10 seconds */}
          <Button onClick={() => { kc.logout({ redirectUri: process.env.REACT_APP_LOGOUT_URL }) }} className="m-1" label='Logout' severity="danger" />
          
        </div>
      </div>

      {/* <div className='grid'>
      <div className='col'>
        <h2>Is authenticated: {kc.authenticated}</h2>
      </div>
        </div> */}


      <div className='grid'>
        <div className='col-2'></div>
        <div className='col-8'>
        <h3>Info Pane</h3>
          <Card>
   
              {infoMessage}
       
          </Card>
        </div>
        <div className='col-2'></div>
      </div>



    </div>
  );
}


export default App;
