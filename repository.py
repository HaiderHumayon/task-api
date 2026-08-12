import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
    )


def initialize_database():
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT FALSE
            )
            """
        )

        cursor.execute("SELECT COUNT(*) AS count FROM tasks")
        task_count = cursor.fetchone()["count"]

        if task_count == 0:
            cursor.executemany(
                "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                [
                    ("Learn HTTP", False),
                    ("Build a CRUD API", False),
                    ("Test with Swagger UI", True),
                ],
            )

    connection.commit()
    connection.close()


def get_tasks():
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, title, done FROM tasks ORDER BY id"
        )
        tasks = cursor.fetchall()

    connection.close()
    return tasks


def get_task(task_id):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, title, done FROM tasks WHERE id = %s",
            (task_id,),
        )
        task = cursor.fetchone()

    connection.close()
    return task


def create_task(title):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO tasks (title, done)
            VALUES (%s, %s)
            RETURNING id, title, done
            """,
            (title, False),
        )
        task = cursor.fetchone()

    connection.commit()
    connection.close()

    return task


def update_task(task_id, title, done):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE tasks
            SET title = %s, done = %s
            WHERE id = %s
            RETURNING id, title, done
            """,
            (title, done, task_id),
        )

        task = cursor.fetchone()

    connection.commit()
    connection.close()

    return task


def delete_task(task_id):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM tasks
            WHERE id = %s
            RETURNING id
            """,
            (task_id,),
        )

        deleted_task = cursor.fetchone()

    connection.commit()
    connection.close()

    return deleted_task is not None