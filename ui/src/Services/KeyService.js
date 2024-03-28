import axios from "axios"
import { toast } from 'react-toastify';

export const keyApi = {
    getApiKey,
    deleteApiKey
  }
  
  function getApiKey(token) {
    return instance.get('/getapikey', {
      headers: { 'Authorization': bearerAuth(token)}
    }).catch(err => { debugger 
      handleError(err);
      });

    // instance.get('/getapikey', { headers: { 'Authorization': bearerAuth(token)}})
    // .then((response) => {return response.data})
    // .catch((error) => {return error})
  }
  
  function deleteApiKey(token) {
    debugger
    return instance.delete('/apikey',{
      headers: { 'Authorization': bearerAuth(token),"Access-Control-Allow-Origin": "*"}
    }).catch(err => { debugger 
      handleError(err);
      });
  }

  // -- Axios
  const instance = axios.create({
    //baseURL: config.url.API_BASE_URL,
    baseURL: window.REACT_APP_BACKEND_URL,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
  })
  
  instance.interceptors.response.use(response => {
    return response
  }, function (error) {
    if (error.response.status === 404) {
      return { status: error.response.status }
    }
    return Promise.reject(error.response)
  })
  
  // -- Helper functions
  
  function bearerAuth(token) {
    return `Bearer ${token}`
  }

  function showToaster(error) {
    toast.error(error, {
      position: "top-right",
      autoClose: 5000,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      progress: undefined,
      theme: "dark",
      })
  }

  function handleError(error) {
    if (error.status === 500) {
      showToaster('error: 500 are you logged in?'  );
    }
    else {
      if (error.data !== undefined) {
        showToaster('error: ' +error.status + ' message: ' + error.data.message !== undefined ? error.data.message : error.data);
      }
      else
      showToaster('error: ' +error.status + ' message: ' + error.data);
    }
    
  }