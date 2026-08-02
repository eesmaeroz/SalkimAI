def test_register_user(client):
    response = client.post("/api/v1/auth/register", json={
        "phone": "5551234567",
        "name": "New User",
        "password": "strongpassword123"
    })
    assert response.status_code == 201

def test_login_user(client):
    client.post("/api/v1/auth/register", json={
        "phone": "5559876543",
        "name": "Login User",
        "password": "loginpassword"
    })
    
    response = client.post("/api/v1/auth/token", json={
        "phone": "5559876543",
        "password": "loginpassword"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_delete_me(client, test_user):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.delete("/api/v1/auth/me", headers=headers)
    assert response.status_code == 204
    
    # Verify user is deleted by trying to delete again
    response2 = client.delete("/api/v1/auth/me", headers=headers)
    assert response2.status_code == 401
