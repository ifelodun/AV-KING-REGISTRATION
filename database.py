import os

import psycopg2
from psycopg2.extras import RealDictCursor


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():

    database_url = os.getenv("DATABASE_URL")

    if not database_url:

        raise RuntimeError(
            "DATABASE_URL is not configured."
        )

    return psycopg2.connect(
        database_url,
        cursor_factory=RealDictCursor
    )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():

    conn = get_db()

    try:

        with conn.cursor() as cur:

            # =================================================
            # APPLICATIONS TABLE
            # =================================================

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

                    -- =========================================
                    -- APPLICATION STATUS
                    -- =========================================

                    status VARCHAR(50)
                        NOT NULL DEFAULT 'Pending',

                    admin_notes TEXT,

                    -- =========================================
                    -- APPLICANT PORTAL
                    -- =========================================

                    password_hash TEXT,

                    portal_active BOOLEAN
                        NOT NULL DEFAULT TRUE,

                    last_login TIMESTAMP,

                    -- =========================================
                    -- SHORTLISTING
                    -- =========================================

                    shortlisted_at TIMESTAMP,

                    -- =========================================
                    -- INTERVIEW
                    -- =========================================

                    interview_date TIMESTAMP,

                    interview_location TEXT,

                    interview_notes TEXT,

                    interview_status VARCHAR(50)
                        NOT NULL DEFAULT 'Not Scheduled',

                    -- =========================================
                    -- WHATSAPP NOTIFICATION
                    -- =========================================

                    notification_sent BOOLEAN
                        NOT NULL DEFAULT FALSE,

                    notification_sent_at TIMESTAMP,

                    -- =========================================
                    -- TIMESTAMPS
                    -- =========================================

                    submitted_at TIMESTAMP
                        NOT NULL DEFAULT CURRENT_TIMESTAMP,

                    updated_at TIMESTAMP
                        NOT NULL DEFAULT CURRENT_TIMESTAMP

                )
                """
            )


            # =================================================
            # MIGRATION FOR EXISTING DATABASES
            # =================================================
            #
            # These ensure older PostgreSQL databases receive
            # columns that were added after the first deployment.
            #
            # =================================================


            # -------------------------------------------------
            # APPLICANT PORTAL
            # -------------------------------------------------

            cur.execute(
                """
                ALTER TABLE applications

                ADD COLUMN IF NOT EXISTS
                password_hash TEXT
                """
            )


            cur.execute(
                """
                ALTER TABLE applications

                ADD COLUMN IF NOT EXISTS
                portal_active BOOLEAN
                NOT NULL DEFAULT TRUE
                """
            )


            cur.execute(
                """
                ALTER TABLE applications

                ADD COLUMN IF NOT EXISTS
                last_login TIMESTAMP
                """
            )


            # -------------------------------------------------
            # SHORTLISTING
            # -------------------------------------------------

            cur.execute(
                """
                ALTER TABLE applications

                ADD COLUMN IF NOT EXISTS
                shortlisted_at TIMESTAMP
                """
            )


            # -------------------------------------------------
            # INTERVIEW
            # -------------------------------------------------

            cur.execute(
                """
                ALTER TABLE applications

                ADD COLUMN IF NOT EXISTS
                interview_date TIMESTAMP
                """
            )


            cur.execute(
                """
                ALTER TABLE applications

                ADD COLUMN IF NOT EXISTS
                interview_location TEXT
                """
            )


            cur.execute(
                """
                ALTER TABLE applications

                ADD COLUMN IF NOT EXISTS
                interview_notes TEXT
                """
            )


            cur.execute(
                """
                ALTER TABLE applications

                ADD COLUMN IF NOT EXISTS
                interview_status VARCHAR(50)
                NOT NULL DEFAULT 'Not Scheduled'
                """
            )


            # -------------------------------------------------
            # WHATSAPP NOTIFICATION
            # -------------------------------------------------

            cur.execute(
                """
                ALTER TABLE applications

                ADD COLUMN IF NOT EXISTS
                notification_sent BOOLEAN
                NOT NULL DEFAULT FALSE
                """
            )


            cur.execute(
                """
                ALTER TABLE applications

                ADD COLUMN IF NOT EXISTS
                notification_sent_at TIMESTAMP
                """
            )


            # =================================================
            # ADMIN USERS
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS admin_users (

                    id SERIAL PRIMARY KEY,

                    username VARCHAR(100)
                        UNIQUE NOT NULL,

                    password_hash TEXT
                        NOT NULL,

                    full_name VARCHAR(150),

                    created_at TIMESTAMP
                        NOT NULL DEFAULT CURRENT_TIMESTAMP,

                    last_login TIMESTAMP

                )
                """
            )


            # =================================================
            # APPLICANT PORTAL MESSAGES
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS applicant_messages (

                    id SERIAL PRIMARY KEY,

                    application_id INTEGER
                        NOT NULL
                        REFERENCES applications(id)
                        ON DELETE CASCADE,

                    subject VARCHAR(200)
                        NOT NULL,

                    message TEXT
                        NOT NULL,

                    message_type VARCHAR(50)
                        NOT NULL DEFAULT 'General',

                    is_read BOOLEAN
                        NOT NULL DEFAULT FALSE,

                    created_at TIMESTAMP
                        NOT NULL DEFAULT CURRENT_TIMESTAMP

                )
                """
            )

        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS applicant_messages (
                    id SERIAL PRIMARY KEY,
                    application_id INTEGER NOT NULL,
                    subject VARCHAR(255),
                    message TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                ALTER TABLE applicant_messages
                ADD COLUMN IF NOT EXISTS
                message_type VARCHAR(50)
                DEFAULT 'General'
            """)

            # =================================================
            # INDEXES
            # =================================================

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


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_applications_application_number

                ON applications(application_number)
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_applicant_messages_application

                ON applicant_messages(application_id)
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_applicant_messages_read

                ON applicant_messages(is_read)
                """
            )
            cur.execute("""
                CREATE TABLE IF NOT EXISTS company_settings (
                    id SERIAL PRIMARY KEY,
                    company_name VARCHAR(255),
                    company_email VARCHAR(255),
                    company_phone VARCHAR(100),
                    company_address TEXT,
                    company_website VARCHAR(255),
                    footer_text TEXT,
                    logo VARCHAR(255)
                )
            """)

        # =====================================================
        # COMMIT
        # =====================================================

        conn.commit()


    except Exception:

        conn.rollback()

        raise


    finally:

        conn.close()
