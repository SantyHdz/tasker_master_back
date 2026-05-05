import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.task import Task
from app.models.priority import Priority
from app.utils.security import hash_password, create_access_token


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestPass123"),
        name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_token(test_user):
    """Create a test JWT token."""
    return create_access_token({"sub": str(test_user.id)})


@pytest.fixture
def test_priority(db_session):
    """Create test priorities."""
    priorities = [
        Priority(id=1, name="Low"),
        Priority(id=2, name="Medium"),
        Priority(id=3, name="High")
    ]
    for priority in priorities:
        db_session.add(priority)
    db_session.commit()
    return priorities


@pytest.fixture
def test_task(db_session, test_user, test_priority):
    """Create a test task."""
    task = Task(
        title="Test Task",
        description="Test Description",
        priority_id=2,
        is_completed=False,
        user_id=test_user.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_register_user(client):
    """Test user registration."""
    response = client.post("/auth/register", json={
        "email": "newuser@example.com",
        "password": "SecurePass123",
        "name": "New User"
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client, test_user):
    """Test registration with duplicate email."""
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123",
        "name": "Test User"
    })
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "TestPass123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data


def test_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials."""
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "WrongPassword"
    })
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_create_task(client, test_token, test_priority):
    """Test creating a task."""
    response = client.post(
        "/tasks/",
        json={
            "title": "New Task",
            "description": "Task description",
            "priority_id": 2,
            "due_date": "2026-05-10T10:00:00Z"
        },
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Task"
    assert data["priority_id"] == 2


def test_create_task_invalid_priority(client, test_token):
    """Test creating a task with invalid priority."""
    response = client.post(
        "/tasks/",
        json={
            "title": "New Task",
            "priority_id": 999,  # Invalid priority
        },
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 400


def test_get_tasks(client, test_token, test_task):
    """Test getting user's tasks."""
    response = client.get(
        "/tasks/",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_task_by_id(client, test_token, test_task):
    """Test getting a specific task."""
    response = client.get(
        f"/tasks/{test_task.id}",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_task.id)
    assert data["title"] == test_task.title


def test_get_task_not_found(client, test_token):
    """Test getting a non-existent task."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(
        f"/tasks/{fake_id}",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 404


def test_update_task(client, test_token, test_task):
    """Test updating a task."""
    response = client.put(
        f"/tasks/{test_task.id}",
        json={
            "title": "Updated Task",
            "is_completed": True
        },
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Task"
    assert data["is_completed"] is True


def test_toggle_task(client, test_token, test_task):
    """Test toggling task completion."""
    response = client.patch(
        f"/tasks/{test_task.id}/toggle",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_completed"] is True


def test_delete_task(client, test_token, test_task):
    """Test deleting a task."""
    response = client.delete(
        f"/tasks/{test_task.id}",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_unauthorized_access(client):
    """Test accessing protected endpoints without token."""
    response = client.get("/tasks/")
    assert response.status_code == 401


def test_search_tasks(client, test_token, test_task):
    """Test searching tasks."""
    response = client.get(
        "/tasks/?search=Test",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_filter_tasks_by_priority(client, test_token, test_task):
    """Test filtering tasks by priority."""
    response = client.get(
        "/tasks/?priority_id=2",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # All returned tasks should have priority_id 2
    for task in data:
        assert task["priority_id"] == 2


def test_pagination(client, test_token, db_session, test_user):
    """Test task pagination."""
    # Create multiple tasks
    for i in range(25):
        task = Task(
            title=f"Task {i}",
            priority_id=1,
            is_completed=False,
            user_id=test_user.id
        )
        db_session.add(task)
    db_session.commit()

    # Test first page
    response = client.get(
        "/tasks/?skip=0&limit=20",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 20

    # Test second page
    response = client.get(
        "/tasks/?skip=20&limit=20",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5  # Remaining tasks