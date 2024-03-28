# Dev-portal

# Steps to run whole stack using Docker-compose.yml:
1. navigate to root folder of project and run:
```sh
docker-compose up
This will start all containers requred for dev portal
```
2. run command:
```sh
docker exec -it vault_test sh /vault/config/setup.sh
This will run setup script inside vault container so we can save new entries
```
3. go to keycloak admin console
```sh
http://localhost:8080/
username: admin
password: admin
```
4. Create new realm. This can be done manually or use keycloak\config\realm_export\realm-export.json
if using exported settings. you still need to make user manually.
```sh
realm name: test
```
5. Create new client
```sh
GENERAL SETTINGS
    Client ID: frontend
CAPABILITY CONFIG
    Client authentication: OFF
    Authorization: OFF
    Standard flow: ON
    Direct access grants: ON
LOGIN SETTINGS
    Valid redirect URIs: *
    Valid post logout redirect URIs: *
    Web origins: *
```
6. Create new user. Remember to add credentials also.
7. Create realm role
```sh
role name: ADMIN
```
8. add ADMIN role to default value for testing purposes
```sh
navigate REALM ROLES -> default-roles-test
Assign role -> ADMIN
```
9. Thats it now you can log in from frontend using created users info


# Steps to run whole stack using Docker-compose-full.yml (This includes backend and frontend)

1. run command:
```sh
docker-compose -f docker-compose-full.yml up
This will run whole project
```
2. go to keycloak admin console
```sh
http://localhost:8080/
username: admin
password: admin
```
3. Create new realm. This can be done manually or use keycloak\config\realm_export\realm-export.json
if using exported settings. you still need to make user manually.
```sh
realm name: test
```
4. Create new client
```sh
GENERAL SETTINGS
    Client ID: frontend
CAPABILITY CONFIG
    Client authentication: OFF
    Authorization: OFF
    Standard flow: ON
    Direct access grants: ON
LOGIN SETTINGS
    Valid redirect URIs: *
    Valid post logout redirect URIs: *
    Web origins: *
```
5. run command:
```sh
docker exec -it vault_test sh /vault/config/setup.sh
This will run setup script inside vault container so we can save new entries
```

6. thats it navigate to http://localhost:3002 to see ui