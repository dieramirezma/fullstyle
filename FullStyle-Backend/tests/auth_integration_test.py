def test_register_user_success(client):
    response = client.post(
        "/api/register",
        json={"name": "TestUser", "email": "testuser@example.com", "password": "Password123"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert "user" in data
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "testuser@example.com"


def test_register_manager_success(client):
    response = client.post(
        "/api/manager_register",
        json={
            "name": "ManagerUser",
            "email": "manageruser@example.com",
            "password": "Password123",
            "bankaccount": 123456,
            "accounttype": "ahorros",
            "bankentity": "BancoTest",
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert "user" in data
    assert "manager" in data
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "manageruser@example.com"


def test_login_user_success(client, setup_user):
    response = client.post(
        "/api/login", json={"email": setup_user["email"], "password": "Password123"}
    )

    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == setup_user["email"]
