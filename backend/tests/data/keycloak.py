"""
Keycloak test data
"""

from typing import TypedDict


class Credential(TypedDict):
    """
    Keycloak user credential
    """

    type: str
    value: str
    temporary: bool


class KeycloakUser(TypedDict):
    """
    Keycloak user
    """

    username: str
    enabled: bool
    credentials: list[Credential]
    firstName: str
    lastName: str
    email: str


# Admin user name and password needs to be in line with keycloak service
KEYCLOAK_ADMIN_USER_TOKEN_DATA = {
    "client_id": "admin-cli",
    "username": "admin",
    "password": "admin",
    "grant_type": "password",
}

KEYCLOAK_USERS: list[KeycloakUser] = [
    {
        "username": "tester",
        "enabled": True,
        "credentials": [{"type": "password", "value": "tester", "temporary": False}],
        "firstName": "Test",
        "lastName": "User",
        "email": "test-user@example.com",
    },
    {
        "username": "tester2",
        "enabled": True,
        "credentials": [{"type": "password", "value": "tester2", "temporary": False}],
        "firstName": "Test2",
        "lastName": "User2",
        "email": "test-user2@example.com",
    },
    {
        "username": "test_admin",
        "enabled": True,
        "credentials": [{"type": "password", "value": "test_admin", "temporary": False}],
        "firstName": "admin1",
        "lastName": "admin1",
        "email": "admin1@example.com",
    },
    {
        "skip_init_creation": True,  # Skip creation in conftest.py
        "username": "tester3",
        "enabled": True,
        "credentials": [{"type": "password", "value": "tester3", "temporary": False}],
        "firstName": "tester3",
        "lastName": "tester3",
        "email": "tester3@example.com",
    },
]
