package com.apiportal.backend.service;

import com.apiportal.backend.models.VaultApiInfo;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.vault.core.VaultKeyValueOperations;
import org.springframework.vault.core.VaultKeyValueOperationsSupport;
import org.springframework.vault.core.VaultOperations;
import org.springframework.vault.core.VaultTemplate;
import org.springframework.vault.support.VaultResponse;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClientException;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;

@Service
public class VaultService {
    @Autowired
    VaultTemplate vaultTemplate;

    @Autowired
    ApiKeyService apiKeyService;

    @Value("${apisix.keyName}")
    private String keyName;

    @Value("${vault.path}")
    private String vaultPath;

    public String saveUserToVault(String userName) {
        String generatedApiKey = apiKeyService.generateMD5Hashvalue(userName);
        VaultOperations operations = vaultTemplate;
        VaultKeyValueOperations keyValueOperations = operations.opsForKeyValue(vaultPath,
                VaultKeyValueOperationsSupport.KeyValueBackend.unversioned());

        Map vaultValues = new HashMap<>();
        vaultValues.put(keyName,generatedApiKey);
        vaultValues.put("date",getDate());

        try {
            keyValueOperations.put(userName, vaultValues);
        } catch (Exception e) {
            System.out.println("vault error " +e);
            throw e;
        }
        return generatedApiKey;
    }

    public void deleteUserFromVault(String userName) {
        //String generatedApiKey = apiKeyService.generateMD5Hashvalue(userName);
        VaultOperations operations = vaultTemplate;
        operations.delete(vaultPath + userName);
//        VaultKeyValueOperations keyValueOperations = operations.opsForKeyValue(vaultPath,
//                VaultKeyValueOperationsSupport.KeyValueBackend.unversioned());
//
//        Map vaultValues = new HashMap<>();
//        vaultValues.put(keyName,generatedApiKey);
//        vaultValues.put("date",getDate());
//
//        try {
//            keyValueOperations.put(userName, vaultValues);
//        } catch (Exception e) {
//            System.out.println("vault error " +e);
//            throw e;
//        }
//        return generatedApiKey;
    }

    public VaultResponse getUserinfoFromVault(String username) {
        VaultOperations operations = vaultTemplate;

        VaultResponse read = null;
        try {
            read = operations.read(vaultPath +"/" +username);
        } catch (HttpStatusCodeException e) {
            System.out.println("vault error: " +e);
            throw e;
        } catch (RestClientException e) {
            System.out.println("vault error: " +e);
            throw e;
        } catch (NoSuchMethodError e) {
            System.out.println("vault error: " +e);
            return null;
        }
        return read;
    }

    public VaultApiInfo checkIfUserExists(String userName) {
        VaultResponse vaultResponse = getUserinfoFromVault(userName);
        //check if user exists
        if (vaultResponse == null) {
            return null;
        }
        VaultApiInfo vaultApiInfo = new VaultApiInfo();
        vaultApiInfo.setApiKey(vaultResponse.getData().get(keyName).toString());
        vaultApiInfo.setDate(vaultResponse.getData().get("date").toString());
        return vaultApiInfo;
    }

    private String getDate() {
        DateTimeFormatter dtf = DateTimeFormatter.ofPattern("yyyy/MM/dd HH:mm:ss");
        LocalDateTime now = LocalDateTime.now();
        String dateString = dtf.format(now);
        return dateString;
    }

}
