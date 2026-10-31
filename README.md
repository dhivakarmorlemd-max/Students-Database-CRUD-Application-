# Students Database CRUD Application

A small REST API for managing student records, built with Python, FastAPI, and SQLite. It uses dummy data only; do not add real student information to demonstrations or the checked-in database.

## Features

- Create, list, filter, retrieve, update, and delete students.
- Unique student IDs; date and email validation; at least one of email or phone is required.
- Optional course and address fields.
- SQLite database stored at `data/students.db` by default.
- Interactive API documentation at `/docs`.

## Setup

Python 3.10 or newer is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; OpenAPI docs are at `http://127.0.0.1:8000/docs`.

## Endpoints

| Method | Path | Behavior |
| --- | --- | --- |
| POST | `/students` | Create a student (201); duplicate ID returns 409 |
| GET | `/students` | List students; optional `name` and `course` substring filters |
| GET | `/students/{student_id}` | Retrieve one student; missing ID returns 404 |
| PUT | `/students/{student_id}` | Replace editable fields; missing ID returns 404 |
| DELETE | `/students/{student_id}` | Delete a student; returns 204 or 404 |

A student object has this shape:

```json
{
  "student_id": "STU-1001",
  "name": "Asha Kumar",
  "date_of_birth": "2004-05-12",
  "email": "asha@example.test",
  "phone": null,
  "course": "Computer Science",
  "address": "12 Demo Street"
}
```

## Example requests and responses

Create a dummy student:

```powershell
curl.exe -X POST http://127.0.0.1:8000/students -H "Content-Type: application/json" -d '{"student_id":"STU-1001","name":"Asha Kumar","date_of_birth":"2004-05-12","email":"asha@example.test","course":"Computer Science"}'
```

The response is `201 Created` with the student object above (phone and address are `null` when omitted).

List, optionally filter, or retrieve:

```powershell
curl.exe "http://127.0.0.1:8000/students?course=Computer"
curl.exe http://127.0.0.1:8000/students/STU-1001
```

Update (PUT replaces the editable fields; include email and/or phone):

```powershell
curl.exe -X PUT http://127.0.0.1:8000/students/STU-1001 -H "Content-Type: application/json" -d '{"name":"Asha Kumar","date_of_birth":"2004-05-12","email":"asha@example.test","phone":"+1-555-0100","course":"Data Science","address":"12 Demo Street"}'
```

The response is `200 OK` with the updated student object. Delete:

```powershell
curl.exe -i -X DELETE http://127.0.0.1:8000/students/STU-1001
```

A successful delete returns `204 No Content`. Missing records return a JSON `{"detail":"Student not found"}` with status 404; invalid fields return 422; duplicate IDs return 409.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use temporary SQLite databases and dummy student information.
