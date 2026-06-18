import pytest
from fastapi.testclient import TestClient
from main import app
from models.database import get_db, Base, engine
from sqlalchemy.orm import sessionmaker

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "KisanAI Risk Intelligence V2 running"

def test_register_and_login():
    response = client.post("/api/auth/register", json={"email": "test@example.com", "password": "pass"})
    assert response.status_code == 200
    
    response = client.post("/api/auth/login", data={"username": "test@example.com", "password": "pass"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_plot_crud():
    # Login
    response = client.post("/api/auth/login", data={"username": "test@example.com", "password": "pass"})
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create plot
    plot_data = {
        "name": "Test Plot",
        "crop_type": "Wheat",
        "location": "Pune",
        "growth_stage": "Vegetative",
        "sowing_date": "2023-01-01"
    }
    response = client.post("/api/plots", json=plot_data, headers=headers)
    assert response.status_code == 200
    plot_id = response.json()["id"]
    
    # Get plots
    response = client.get("/api/plots", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["latest_risk"] is None
    
    # Update plot
    response = client.patch(f"/api/plots/{plot_id}", json={"growth_stage": "Flowering"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["growth_stage"] == "Flowering"
    
    # Don't delete so we can test risk generation manually if needed
    
