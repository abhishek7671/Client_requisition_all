"""Testcases for All API's"""

import pytest
from fastapi.testclient import TestClient
from main import app,get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def db():
    """Database Setup"""
    db = get_db()
    yield db
    # Teardown
    db.close()


def test_signup():
    """ Provide valid student data"""
    student_data = {
        "lname": "Areti",
        "fname": "Venkatesh",
        "email": "venkatesh@gmail.com",
        "password": "venkatesh123"
    }

    try:
        response = client.post("/students/", json=student_data)
        assert response.status_code == 200
        assert response.json() == {"message": "User created successfully"}
    except Exception as e:
        print(e)


access_token = None
def test_login():
    """ Provide valid login credentials"""
    login_data = {
        "email": "venkatesh@gmail.com",
        "password": "venkatesh123"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()

    global access_token
    access_token = response.json()["access_token"]
    print("Access Token:", access_token)


def test_logout():
    """Ensure the access token is available"""
    assert access_token is not None

    # Use the stored access token for logout
    response = client.post("/logout", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "Logout Successfully"}



def test_get_students():
    """get all details"""
    response = client.get("/students/all")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_change_password():
    """Ensure the access token is available"""
    assert access_token is not None
    
    #Provide valid change password data and use the access token
    change_password_data = {
        "email": "venkatesh@gmail.com",
        "old_password": "venkatesh123",
        "new_password": "venkatesh123"
    }
    response = client.post("/changepassword", json=change_password_data, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "Password changed successfully"}



def test_signup_existing_email():
    """Provide student data with an existing email"""
    student_data = {
        "lname": "Areti",
        "fname": "Venkatesh",
        "email": "venkatesh@gmail.com",
        "password": "venkatesh123"
    }
    response = client.post("/students/", json=student_data)
    assert response.status_code == 200
    assert response.json() == {"message": "Email already exists"}

def test_login_incorrect_email():
    """Provide incorrect login credentials"""
    login_data = {
        "email": "invalid.email@example.com",
        "password": "password123"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect email"}

def test_login_incorrect_password():
    """Provide incorrect login credentials"""
    login_data = {
        "email": "venkatesh@gmail.com",
        "password": "invalidpassword"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect password"}



def test_change_password_user_not_found():
    """Ensure the access token is available"""
    assert access_token is not None
    
    #Non-existent user data and use the access token
    request_payload = {
        "email": "sai12@gmail.com",
        "old_password": "Sai123",
        "new_password": "Sai456"
    }
    response = client.post("/changepassword", json=request_payload, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_change_password_incorrect_old_password():
    """Ensure the access token is available"""
    assert access_token is not None
    
    #Existing user but incorrect old password data and use the access token
    request_payload = {
        "email": "venkatesh@gmail.com",
        "old_password": "Venkatesh123",
        "new_password": "venkatesh123"
    }
    response = client.post("/changepassword", json=request_payload, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect old password"}


def test_logout_unauthorized():
    """Send the request without an access token"""
    response = client.post("/logout")
    assert response.status_code == 403
    assert response.json() == {"detail": "Not authenticated"}
