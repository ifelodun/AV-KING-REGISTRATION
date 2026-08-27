import os

import psycopg2
from psycopg2.extras import RealDictCursor


def get_db():

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not configured."
        )

    conn = psycopg2.connect(
        database_url,
        cursor_factory=RealDictCursor
    )

    return conn


def init_db():

    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS applications (

                    id SERIAL PRIMARY KEY,

                    application_number VARCHAR(30)
                        UNIQUE NOT NULL,

                    first_name VARCHAR(100)
                        NOT NULL,

                    middle_name VARCHAR(100),

                    last_name VARCHAR(100)
                        NOT NULL,

                    gender VARCHAR(30),

                    date_of_birth DATE,

                    phone VARCHAR(30)
                        NOT NULL,

                    email VARCHAR(150),

                    address TEXT,

                    state VARCHAR(100),

                    lga VARCHAR(100),

                    position_applied VARCHAR(150)
                        NOT NULL,

                    highest_qualification VARCHAR(150),

                    course_of_study VARCHAR(200),

                    institution VARCHAR(250),

                    graduation_year VARCHAR(10),

                    work_experience TEXT,

                    previous_employer VARCHAR(250),

                    previous_position VARCHAR(150),

                    reason_for_applying TEXT,

                    additional_information TEXT,

                    passport_filename VARCHAR(255),

                    cv_filename VARCHAR(255),

                    qualification_filename VARCHAR(255),

                    status VARCHAR(50)
                        NOT NULL DEFAULT 'Pending',

                    admin_notes TEXT,

                    submitted_at TIMESTAMP
                        NOT NULL DEFAULT CURRENT_TIMESTAMP,

                    updated_at TIMESTAMP
                        NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_applications_status
                ON applications(status)
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_applications_submitted_at
                ON applications(submitted_at)
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_applications_phone
                ON applications(phone)
                """
            )

        conn.commit()

    finally:

        conn.close()
