from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.main import create_app


@pytest.fixture
def client(tmp_path: Path):
    app = create_app(tmp_path / "students.sqlite3")
    with TestClient(app) as test_client:
        yield test_client


SAMPLE = {
    "student_id": "STU-1001",
    "name": "Asha Kumar",
    "date_of_birth": "2004-05-12",
    "email": "asha@example.test",
    "phone": None,
    "course": "Computer Science",
    "address": "12 Demo Street",
}


def test_create_list_get_and_persist(client: TestClient):
    created = client.post("/students", json=SAMPLE)
    assert created.status_code == 201
    assert created.json()["student_id"] == SAMPLE["student_id"]
    assert client.get("/students").json() == [created.json()]
    assert client.get("/students/STU-1001").json() == created.json()
    assert client.get("/students", params={"name": "asha", "course": "science"}).json() == [created.json()]


def test_duplicate_student_id_returns_conflict(client: TestClient):
    assert client.post("/students", json=SAMPLE).status_code == 201
    duplicate = {**SAMPLE, "name": "Another Student"}
    response = client.post("/students", json=duplicate)
    assert response.status_code == 409
    assert response.json()["detail"] == "A student with this ID already exists"


def test_update_and_delete(client: TestClient):
    client.post("/students", json=SAMPLE)
    updated = {**{key: value for key, value in SAMPLE.items() if key != "student_id"}, "name": "Asha Updated"}
    response = client.put("/students/STU-1001", json=updated)
    assert response.status_code == 200
    assert response.json()["name"] == "Asha Updated"
    assert client.delete("/students/STU-1001").status_code == 204
    assert client.get("/students/STU-1001").status_code == 404


def test_missing_student_returns_404(client: TestClient):
    assert client.get("/students/NO-SUCH-STUDENT").status_code == 404
    payload = {key: value for key, value in SAMPLE.items() if key != "student_id"}
    assert client.put("/students/NO-SUCH-STUDENT", json=payload).status_code == 404
    assert client.delete("/students/NO-SUCH-STUDENT").status_code == 404


@pytest.mark.parametrize("changes", [
    {"email": None, "phone": None},
    {"date_of_birth": "not-a-date"},
    {"email": "invalid-email"},
    {"name": ""},
])
def test_invalid_inputs_return_validation_errors(client: TestClient, changes: dict):
    response = client.post("/students", json={**SAMPLE, **changes})
    assert response.status_code == 422


def test_database_persistence_across_app_restarts(tmp_path: Path):
    db_path = tmp_path / "persistent.sqlite3"
    with TestClient(create_app(db_path)) as first_client:
        response = first_client.post("/students", json=SAMPLE)
        assert response.status_code == 201

    with TestClient(create_app(db_path)) as restarted_client:
        persisted = restarted_client.get("/students/STU-1001")
        assert persisted.status_code == 200
        assert persisted.json()["name"] == "Asha Kumar"
