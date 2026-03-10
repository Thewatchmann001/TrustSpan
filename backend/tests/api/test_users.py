import pytest
from fastapi import status


def test_register_user(client, test_user_data):
    """Test user registration."""
    response = client.post("/api/users/register", json=test_user_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["full_name"] == test_user_data["full_name"]
    assert "id" in data


def test_register_duplicate_email(client, test_user_data):
    """Test registration with duplicate email."""
    client.post("/api/users/register", json=test_user_data)
    response = client.post("/api/users/register", json=test_user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_login_user(client, test_user_data):
    """Test user login."""
    # Register first
    client.post("/api/users/register", json=test_user_data)
    
    # Login
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = client.post("/api/users/login", json=login_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client, test_user_data):
    """Test login with invalid credentials."""
    login_data = {
        "email": test_user_data["email"],
        "password": "wrongpassword"
    }
    response = client.post("/api/users/login", json=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_user(client, test_user_data):
    """Test get user by ID."""
    # Register user
    register_response = client.post("/api/users/register", json=test_user_data)
    reg_data = register_response.json()
    user_id = reg_data["id"]
    token = reg_data["access_token"]
    
    # Get user
    response = client.get(
        f"/api/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == test_user_data["email"]

