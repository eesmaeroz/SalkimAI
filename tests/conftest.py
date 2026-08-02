import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

from apps.api.main import app
from apps.api.database import get_db, Base
from apps.api.models.user import User
from apps.api.models.greenhouse import Greenhouse
from apps.api.models.sensor_reading import SensorReading
from apps.api.models.image import Image
from apps.api.models.analysis import Analysis
from apps.api.models.prediction import HarvestPrediction

# SQLITE for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(client, db):
    # Register user
    user_data = {
        "phone": "5550001111",
        "name": "Test User",
        "password": "testpassword123"
    }
    reg_resp = client.post("/api/v1/auth/register", json=user_data)
    user_id = reg_resp.json().get("user_id") if reg_resp.status_code == 201 else "00000000-0000-0000-0000-000000000000"

    # Login
    login_data = {"phone": "5550001111", "password": "testpassword123"}
    resp = client.post("/api/v1/auth/token", json=login_data)
    token = resp.json().get("access_token") if resp.status_code == 200 else ""
    
    return {
        "phone": "5550001111",
        "token": token,
        "user_id": user_id
    }
