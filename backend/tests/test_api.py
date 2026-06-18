import pytest
from fastapi.testclient import TestClient
from main import app
from models.database import get_db, User, Base, engine
from sqlalchemy.orm import sessionmaker

# Use a separate test database
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module")
def setup_user():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.username == "testuser").first()
    if not user:
        from utils.helpers import get_password_hash
        user = User(
            username="testuser",
            email="testuser@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("testpassword123")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    yield user
    db.close()

@pytest.fixture(scope="module")
def auth_token(setup_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testpassword123"}
    )
    return response.json()["access_token"]

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "KisanAI API server running"

def test_auth_required_for_crops():
    response = client.get("/api/v1/crops")
    assert response.status_code == 401

def test_get_crops_authenticated(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/v1/crops", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_add_crop_authenticated(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post(
        "/api/v1/crops/add",
        json={"crop": "Wheat", "plot": "Plot A"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["crop"] == "Wheat"
