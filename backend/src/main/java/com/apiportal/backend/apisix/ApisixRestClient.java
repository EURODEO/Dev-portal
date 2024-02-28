package com.apiportal.backend.apisix;


import com.apiportal.backend.apisix.models.Consumer.Consumer;
import com.apiportal.backend.apisix.models.Consumer.KeyAuth;
import com.apiportal.backend.apisix.models.Consumer.Plugins;
import com.apiportal.backend.apisix.models.Route.Routes;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.json.JSONException;
import org.json.JSONObject;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class ApisixRestClient {

    @Value("${apisix.consumersUrl}")
    private String consumersUrl;

    @Value("${apisix.routesUrl}")
    private String routesUrl;

    @Value("${apisix.adminApiKey}")
    private String adminApiKey;

    @Value("${apisix.keyPath}")
    private String keyPath;

    @Value("${apisix.keyName}")
    private String keyName;

    @Value("${apisix.gatewayUrl}")
    private String gatewayUrl;


    public void createConsumer(String username) throws JSONException, JsonProcessingException {

        RestTemplate restTemplate = new RestTemplate();

        ObjectMapper mapper = new ObjectMapper();
        String str = mapper.writeValueAsString(createConsumerObject(username));
        JSONObject jsonObject = new JSONObject(str);


        HttpEntity<String> request = new HttpEntity<String>(jsonObject.toString(), generateHeaders());

        try {
            HttpEntity<String> response = restTemplate.exchange(consumersUrl, HttpMethod.PUT, request, String.class);
        } catch (RestClientException e) {
            throw e;
        }
    }

    public void deleteConsumer(String username) throws JSONException{

        RestTemplate restTemplate = new RestTemplate();

//        ObjectMapper mapper = new ObjectMapper();
//        String str = mapper.writeValueAsString(createConsumerObject(username));
//        JSONObject jsonObject = new JSONObject(str);


        HttpEntity<String> request = new HttpEntity<String>(generateHeaders());

        try {
            HttpEntity<String> response = restTemplate.exchange(consumersUrl + "/"+username, HttpMethod.DELETE, request, String.class);
        } catch (RestClientException e) {
            throw e;
        }
    }

    public List<String> getRoutes() {
        HttpEntity<String> request = new HttpEntity<String>( generateHeaders());
        RestTemplate restTemplate = new RestTemplate();
        try {
            HttpEntity<Routes> response = restTemplate.exchange(routesUrl, HttpMethod.GET, request, Routes.class);
            Routes routes = response.getBody();

            //get all routes that has keyauth plugin. These are the ones using apikey
            routes.setList(routes.getList().stream().filter(x -> x.getValue().getPlugins().getKeyAuth() != null).collect(Collectors.toList()));
            routes.setTotal(routes.getList().size());
            List<String> urlList = new ArrayList<>();
            routes.getList().stream().forEach(x -> urlList.add(gatewayUrl + x.getValue().getUri()));
            return urlList;
        } catch (RestClientException e) {
            throw e;
        }
    }

    public boolean checkIfUserExists(String userName) {
        RestTemplate restTemplate = new RestTemplate();
        HttpEntity<Void> requestEntity = new HttpEntity<>(generateHeaders());
        System.out.println("apisix address: " +consumersUrl);

        ResponseEntity<String> response = restTemplate.exchange(
                consumersUrl+ "/" + userName, HttpMethod.GET, requestEntity, String.class);

        JSONObject jsonObject = new JSONObject(response.getBody());
        System.out.println("apisix json: " +jsonObject);
        JSONObject values = jsonObject.getJSONObject("value");
        String foundUsername = values.get("username").toString();
        if (foundUsername != null) {
            return true;
        }
        else {
            return false;
        }

    }

    private HttpHeaders generateHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("X-API-KEY",adminApiKey);
        return headers;
    }

    private Consumer createConsumerObject(String username) {
        Consumer consumer = new Consumer();
        consumer.setUsername(username);

        KeyAuth keyAuth = new KeyAuth();
        keyAuth.setKey(keyPath+username+"/"+keyName);
        Plugins plugins = new Plugins();
        plugins.setKeyAuth(keyAuth);
        consumer.setPlugins(plugins);
        return consumer;
    }
}
