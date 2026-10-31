from contextlib import closing
from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException, Query, Response, status

from .database import connect, initialize_database
from .schemas import Student, StudentCreate, StudentUpdate

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "students.db"


def create_app(db_path: Path | str = DEFAULT_DB_PATH) -> FastAPI:
    database_path = Path(db_path)
    initialize_database(database_path)
    app = FastAPI(title="Students Database CRUD Application", version="1.0.0")
    app.state.db_path = database_path

    def get_connection() -> sqlite3.Connection:
        return connect(app.state.db_path)

    @app.post("/students", response_model=Student, status_code=status.HTTP_201_CREATED)
    def create_student(student: StudentCreate) -> Student:
        values = student.model_dump()
        try:
            with closing(get_connection()) as connection:
                connection.execute(
                    """INSERT INTO students
                    (student_id, name, date_of_birth, email, phone, course, address)
                    VALUES (:student_id, :name, :date_of_birth, :email, :phone, :course, :address)""",
                    {**values, "date_of_birth": values["date_of_birth"].isoformat()},
                )
                connection.commit()
        except sqlite3.IntegrityError as error:
            if "students.student_id" in str(error) or "UNIQUE constraint failed" in str(error):
                raise HTTPException(status_code=409, detail="A student with this ID already exists") from error
            raise HTTPException(status_code=422, detail="Student data violates a database constraint") from error
        return Student(**values)

    @app.get("/students", response_model=list[Student])
    def list_students(
        name: str | None = Query(default=None, min_length=1, max_length=200),
        course: str | None = Query(default=None, min_length=1, max_length=200),
    ) -> list[Student]:
        clauses: list[str] = []
        parameters: list[str] = []
        if name:
            clauses.append("name LIKE ? COLLATE NOCASE")
            parameters.append(f"%{name.strip()}%")
        if course:
            clauses.append("course LIKE ? COLLATE NOCASE")
            parameters.append(f"%{course.strip()}%")
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with closing(get_connection()) as connection:
            rows = connection.execute(
                "SELECT * FROM students" + where + " ORDER BY student_id", parameters
            ).fetchall()
        return [Student(**dict(row)) for row in rows]

    @app.get("/students/{student_id}", response_model=Student)
    def get_student(student_id: str) -> Student:
        with closing(get_connection()) as connection:
            row = connection.execute("SELECT * FROM students WHERE student_id = ?", (student_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Student not found")
        return Student(**dict(row))

    @app.put("/students/{student_id}", response_model=Student)
    def update_student(student_id: str, student: StudentUpdate) -> Student:
        values = student.model_dump()
        with closing(get_connection()) as connection:
            cursor = connection.execute(
                """UPDATE students SET name = ?, date_of_birth = ?, email = ?, phone = ?,
                course = ?, address = ? WHERE student_id = ?""",
                (values["name"], values["date_of_birth"].isoformat(), values["email"],
                 values["phone"], values["course"], values["address"], student_id),
            )
            connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Student not found")
        return Student(student_id=student_id, **values)

    @app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_student(student_id: str) -> Response:
        with closing(get_connection()) as connection:
            cursor = connection.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
            connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Student not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = create_app()
