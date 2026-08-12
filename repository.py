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