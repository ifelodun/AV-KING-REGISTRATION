import os
import random
import os
import uuid
from datetime import datetime
from urllib.parse import quote
from io import BytesIO
import requests
from datetime import datetime
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak
)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import mm
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

import io
import os

from datetime import datetime

from flask import (
    send_file,
    redirect,
    url_for
)

from openpyxl import Workbook
from openpyxl.styles import (
    Font,
    Alignment,
    Border,
    Side,
    PatternFill
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins

from openpyxl.drawing.image import Image as XLImage
from flask import send_from_directory
import os
from datetime import datetime

current_time = datetime.now()

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from dotenv import load_dotenv

from werkzeug.utils import secure_filename

from database import get_db, init_db


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# APPLICATION
# ============================================================

app = Flask(__name__)


app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "development-secret-key"
)


# ============================================================
# UPLOAD CONFIGURATION
# ============================================================

UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "static",
    "uploads"
)


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


ALLOWED_IMAGE_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp"
}


ALLOWED_DOCUMENT_EXTENSIONS = {
    "pdf",
    "doc",
    "docx"
}


# ============================================================
# COMPANY INFORMATION
# ============================================================

COMPANY_NAME = "AV KING VET DRUG VENTURE"

COMPANY_MOTTO = "Your Needs, Our Priority"

COMPANY_EMAIL = "avkingvetdrug@gmail.com"

COMPANY_PHONE = "09058842501"

COMPANY_ADDRESS = (
    "NO11, HALLELUJAH SHOPPING COMPLEX, "
    "OPPOSITE POULTRY ASSOCIATION, "
    "EGBEDA, IYANA-AJIA, IBADAN"
)


# ============================================================
# AVAILABLE POSITIONS
# ============================================================

POSITIONS = [

    "Sales Representative",

    "Veterinary Drug Sales Assistant",

    "Store Assistant",

    "Account / Cashier",

    "Administrative Assistant",

    "Field Sales Representative",

    "Other"

]


# ============================================================
# GLOBAL TEMPLATE VARIABLES
# ============================================================

@app.context_processor
def inject_company_details():

    return {

        "company_name": COMPANY_NAME,

        "company_motto": COMPANY_MOTTO,

        "company_email": COMPANY_EMAIL,

        "company_phone": COMPANY_PHONE,

        "company_address": COMPANY_ADDRESS,

        "positions": POSITIONS

    }


# ============================================================
# FILE VALIDATION
# ============================================================

def allowed_file(filename, allowed_extensions):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = (
        filename.rsplit(".", 1)[1]
        .lower()
    )

    return extension in allowed_extensions


# ============================================================
# APPLICATION NUMBER
# ============================================================

# =========================================================
# GENERATE RANDOM APPLICATION NUMBER
# =========================================================

def generate_application_number(conn):

    while True:

        random_number = random.randint(
            1000,
            9999
        )

        application_number = (
            f"AV-APP-{random_number}"
        )

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id
                FROM applications
                WHERE application_number = %s
                LIMIT 1
                """,
                (application_number,)
            )

            existing = cur.fetchone()

        if not existing:

            return application_number


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "home.html"
    )

@app.context_processor
def utility_processor():

    def endpoint_exists(endpoint):

        return endpoint in app.view_functions

    return {
        "endpoint_exists": endpoint_exists
    }
    
@app.route("/setup-admin")
def setup_admin():

    username = "admin"
    password = "AVKing@2026"
    full_name = "AV KING Administrator"

    password_hash = generate_password_hash(password)

    conn = get_db()

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id
                FROM admin_users
                WHERE username = %s
                LIMIT 1
                """,
                (username,)
            )

            existing = cur.fetchone()

            if existing:
                return "Admin account already exists."

            cur.execute(
                """
                INSERT INTO admin_users (
                    username,
                    password_hash,
                    full_name
                )
                VALUES (%s, %s, %s)
                """,
                (
                    username,
                    password_hash,
                    full_name
                )
            )

        conn.commit()

        return """
        <h2>Admin account created successfully.</h2>
        <p>Username: admin</p>
        <p>Password: AVKing@2026</p>
        <p>You can now go to /admin/login</p>
        """

    except Exception as e:

        conn.rollback()

        return f"Error: {e}", 500

    finally:
        conn.close()

@app.route("/admin/interviews")
def admin_interviews():

    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db()

    try:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM applications
                WHERE interview_date IS NOT NULL
                ORDER BY interview_date ASC
            """)

            interviews = cur.fetchall()

    finally:
        conn.close()

    return render_template(
        "admin_interviews.html",
        interviews=interviews
    )

# ============================================================
# APPLICATION FORM
# ============================================================
@app.route(
    "/apply",
    methods=["GET", "POST"]
)
def apply():

    # ========================================================
    # CHECK APPLICATION SETTINGS
    # ========================================================

    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    application_status,
                    application_deadline
                FROM company_settings
                ORDER BY id ASC
                LIMIT 1
                """
            )

            settings = cur.fetchone()

    except Exception:

        app.logger.exception(
            "Error checking application settings"
        )

        settings = None

    finally:

        conn.close()


    # ========================================================
    # DEFAULT SETTINGS
    # ========================================================

    application_status = "Closed"
    application_deadline = None

    if settings:

        application_status = (
            settings["application_status"]
            or "Closed"
        ).strip().capitalize()

        application_deadline = (
            settings["application_deadline"]
        )


    # ========================================================
    # APPLICATIONS MANUALLY CLOSED
    # ========================================================

    if application_status == "Closed":

        return render_template(
            "applications_closed.html"
        ), 403


    # ========================================================
    # CHECK APPLICATION DEADLINE
    # ========================================================

    if application_deadline:

        try:

            if hasattr(
                application_deadline,
                "date"
            ):

                deadline_date = (
                    application_deadline.date()
                )

            elif isinstance(
                application_deadline,
                str
            ):

                deadline_date = datetime.strptime(
                    application_deadline,
                    "%Y-%m-%d"
                ).date()

            else:

                deadline_date = application_deadline


            if datetime.now().date() > deadline_date:

                return render_template(
                    "applications_closed.html"
                ), 403


        except Exception:

            app.logger.exception(
                "Error checking application deadline"
            )

            return render_template(
                "applications_closed.html"
            ), 403


    # ========================================================
    # DISPLAY APPLICATION FORM
    # ========================================================

    if request.method == "GET":

        conn = get_db()

        try:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        id,
                        position_name
                    FROM available_positions
                    WHERE is_active = TRUE
                    ORDER BY position_name ASC
                    """
                )

                positions = cur.fetchall()

        except Exception:

            app.logger.exception(
                "Error loading available positions"
            )

            positions = []

        finally:

            conn.close()


        return render_template(
            "apply.html",
            positions=positions
        )


    # ========================================================
    # POST APPLICATION
    # ========================================================

    first_name = request.form.get(
        "first_name",
        ""
    ).strip()

    middle_name = request.form.get(
        "middle_name",
        ""
    ).strip()

    last_name = request.form.get(
        "last_name",
        ""
    ).strip()

    gender = request.form.get(
        "gender",
        ""
    ).strip()

    date_of_birth = request.form.get(
        "date_of_birth",
        ""
    ).strip()


    # ========================================================
    # CONTACT INFORMATION
    # ========================================================

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    address = request.form.get(
        "address",
        ""
    ).strip()

    state = request.form.get(
        "state",
        ""
    ).strip()

    lga = request.form.get(
        "lga",
        ""
    ).strip()


    # ========================================================
    # APPLICATION INFORMATION
    # ========================================================

    position_applied = request.form.get(
        "position_applied",
        ""
    ).strip()


    # ========================================================
    # EDUCATION
    # ========================================================

    highest_qualification = request.form.get(
        "highest_qualification",
        ""
    ).strip()

    course_of_study = request.form.get(
        "course_of_study",
        ""
    ).strip()

    institution = request.form.get(
        "institution",
        ""
    ).strip()

    graduation_year = request.form.get(
        "graduation_year",
        ""
    ).strip()


    # ========================================================
    # WORK EXPERIENCE
    # ========================================================

    work_experience = request.form.get(
        "work_experience",
        ""
    ).strip()

    previous_employer = request.form.get(
        "previous_employer",
        ""
    ).strip()

    previous_position = request.form.get(
        "previous_position",
        ""
    ).strip()


    # ========================================================
    # ADDITIONAL INFORMATION
    # ========================================================

    reason_for_applying = request.form.get(
        "reason_for_applying",
        ""
    ).strip()

    additional_information = request.form.get(
        "additional_information",
        ""
    ).strip()


    # ========================================================
    # APPLICANT PORTAL PASSWORD
    # ========================================================

    portal_password = request.form.get(
        "portal_password",
        ""
    ).strip()

    confirm_portal_password = request.form.get(
        "confirm_portal_password",
        ""
    ).strip()


    # ========================================================
    # DECLARATION
    # ========================================================

    declaration = request.form.get(
        "declaration"
    )


    # ========================================================
    # FILES
    # ========================================================

    passport = request.files.get(
        "passport"
    )

    cv = request.files.get(
        "cv"
    )

    qualification = request.files.get(
        "qualification"
    )


    # ========================================================
    # BASIC VALIDATION
    # ========================================================

    if not first_name:

        flash(
            "Please enter your first name.",
            "error"
        )

        return render_template(
            "apply.html"
        )


    if not last_name:

        flash(
            "Please enter your last name.",
            "error"
        )

        return render_template(
            "apply.html"
        )


    if not phone:

        flash(
            "Please enter your phone number.",
            "error"
        )

        return render_template(
            "apply.html"
        )


    if not position_applied:

        flash(
            "Please select the position you are applying for.",
            "error"
        )

        return render_template(
            "apply.html"
        )


    # ========================================================
    # PASSWORD VALIDATION
    # ========================================================

    if not portal_password:

        flash(
            "Please create a password for your applicant portal.",
            "error"
        )

        return render_template(
            "apply.html"
        )


    if len(portal_password) < 6:

        flash(
            "Your portal password must contain at least 6 characters.",
            "error"
        )

        return render_template(
            "apply.html"
        )


    if portal_password != confirm_portal_password:

        flash(
            "The portal passwords do not match.",
            "error"
        )

        return render_template(
            "apply.html"
        )


    # ========================================================
    # DECLARATION VALIDATION
    # ========================================================

    if not declaration:

        flash(
            "You must accept the declaration before submitting.",
            "error"
        )

        return render_template(
            "apply.html"
        )


    # ========================================================
    # PASSPORT VALIDATION
    # ========================================================

    if not passport or not passport.filename:

        flash(
            "Please upload your passport photograph.",
            "error"
        )

        return render_template(
            "apply.html"
        )


    if not allowed_file(
        passport.filename,
        ALLOWED_IMAGE_EXTENSIONS
    ):

        flash(
            "Passport must be JPG, JPEG, PNG or WEBP.",
            "error"
        )

        return render_template(
            "apply.html"
        )


    # ========================================================
    # CV VALIDATION
    # ========================================================

    if cv and cv.filename:

        if not allowed_file(
            cv.filename,
            ALLOWED_DOCUMENT_EXTENSIONS
        ):

            flash(
                "CV must be PDF, DOC or DOCX.",
                "error"
            )

            return render_template(
                "apply.html"
            )


    # ========================================================
    # QUALIFICATION VALIDATION
    # ========================================================

    if qualification and qualification.filename:

        if not allowed_file(
            qualification.filename,
            ALLOWED_DOCUMENT_EXTENSIONS
        ):

            flash(
                "Qualification document must be PDF, DOC or DOCX.",
                "error"
            )

            return render_template(
                "apply.html"
            )


    # ========================================================
    # DATABASE CONNECTION
    # ========================================================

    conn = get_db()

    try:

        with conn.cursor() as cur:

            # ==================================================
            # FINAL APPLICATION STATUS CHECK
            # ==================================================

            cur.execute(
                """
                SELECT
                    application_status,
                    application_deadline
                FROM company_settings
                ORDER BY id ASC
                LIMIT 1
                """
            )

            current_settings = cur.fetchone()


            if not current_settings:

                conn.rollback()

                return render_template(
                    "applications_closed.html"
                ), 403


            # ==================================================
            # FINAL STATUS CHECK
            # ==================================================

            current_status = (
                current_settings["application_status"]
                or "Closed"
            ).strip().capitalize()


            if current_status == "Closed":

                conn.rollback()

                return render_template(
                    "applications_closed.html"
                ), 403


            # ==================================================
            # FINAL DEADLINE CHECK
            # ==================================================

            current_deadline = (
                current_settings["application_deadline"]
            )


            if current_deadline:

                if hasattr(
                    current_deadline,
                    "date"
                ):

                    current_deadline_date = (
                        current_deadline.date()
                    )

                elif isinstance(
                    current_deadline,
                    str
                ):

                    current_deadline_date = (
                        datetime.strptime(
                            current_deadline,
                            "%Y-%m-%d"
                        ).date()
                    )

                else:

                    current_deadline_date = (
                        current_deadline
                    )


                if datetime.now().date() > current_deadline_date:

                    conn.rollback()

                    return render_template(
                        "applications_closed.html"
                    ), 403


            # ==================================================
            # GENERATE APPLICATION NUMBER FIRST
            # ==================================================

            application_number = (
                generate_application_number(conn)
            )


            app.logger.info(
                "Generated application number: %s",
                application_number
            )


            # ==================================================
            # HASH PASSWORD
            # ==================================================

            password_hash = generate_password_hash(
                portal_password
            )


            # ==================================================
            # INITIALIZE FILE NAMES
            # ==================================================

            passport_filename = None
            cv_filename = None
            qualification_filename = None


            # ==================================================
            # ENSURE UPLOAD DIRECTORY EXISTS
            # ==================================================

            os.makedirs(
                app.config["UPLOAD_FOLDER"],
                exist_ok=True
            )


            # ==================================================
            # SAVE PASSPORT
            # ==================================================

            if passport and passport.filename:

                original = secure_filename(
                    passport.filename
                )

                passport_filename = (
                    f"{application_number}_passport_{original}"
                )

                passport_path = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    passport_filename
                )

                passport.save(
                    passport_path
                )

                app.logger.info(
                    "PASSPORT SAVED: %s",
                    passport_path
                )


            # ==================================================
            # SAVE CV
            # ==================================================

            if cv and cv.filename:

                original = secure_filename(
                    cv.filename
                )

                cv_filename = (
                    f"{application_number}_cv_{original}"
                )

                cv_path = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    cv_filename
                )

                cv.save(
                    cv_path
                )

                app.logger.info(
                    "CV SAVED: %s",
                    cv_path
                )


            # ==================================================
            # SAVE QUALIFICATION
            # ==================================================

            if qualification and qualification.filename:

                original = secure_filename(
                    qualification.filename
                )

                qualification_filename = (
                    f"{application_number}_qualification_{original}"
                )

                qualification_path = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    qualification_filename
                )

                qualification.save(
                    qualification_path
                )

                app.logger.info(
                    "QUALIFICATION SAVED: %s",
                    qualification_path
                )


            # ==================================================
            # INSERT APPLICATION
            # ==================================================

            cur.execute(
                """
                INSERT INTO applications (

                    application_number,

                    first_name,
                    middle_name,
                    last_name,

                    gender,
                    date_of_birth,

                    phone,
                    email,

                    address,
                    state,
                    lga,

                    position_applied,

                    highest_qualification,
                    course_of_study,
                    institution,
                    graduation_year,

                    work_experience,
                    previous_employer,
                    previous_position,

                    reason_for_applying,
                    additional_information,

                    passport_filename,
                    cv_filename,
                    qualification_filename,

                    password_hash,

                    portal_active,

                    status

                )

                VALUES (

                    %s,

                    %s,
                    %s,
                    %s,

                    %s,
                    %s,

                    %s,
                    %s,

                    %s,
                    %s,
                    %s,

                    %s,

                    %s,
                    %s,
                    %s,
                    %s,

                    %s,
                    %s,
                    %s,

                    %s,
                    %s,

                    %s,
                    %s,
                    %s,

                    %s,

                    TRUE,

                    'Pending'

                )

                RETURNING id
                """,

                (
                    application_number,

                    first_name,
                    middle_name,
                    last_name,

                    gender,
                    date_of_birth or None,

                    phone,
                    email or None,

                    address,
                    state,
                    lga,

                    position_applied,

                    highest_qualification,
                    course_of_study,
                    institution,
                    graduation_year,

                    work_experience,
                    previous_employer,
                    previous_position,

                    reason_for_applying,
                    additional_information,

                    passport_filename,
                    cv_filename,
                    qualification_filename,

                    password_hash
                )
            )

            application = cur.fetchone()


        # ====================================================
        # COMMIT
        # ====================================================

        conn.commit()


        app.logger.info(
            "APPLICATION SUBMITTED SUCCESSFULLY: %s",
            application_number
        )


    except Exception:

        conn.rollback()

        app.logger.exception(
            "Error submitting application"
        )

        raise


    finally:

        conn.close()


    # ========================================================
    # SUCCESS
    # ========================================================

    return redirect(
        url_for(
            "application_success",
            application_number=application_number
        )
    )


@app.route(
    "/admin/application_status",
    methods=["POST"]
)
def admin_application_status():

    if session.get("role") != "admin":
        return redirect("/")

    status = request.form.get(
        "status",
        ""
    ).strip().lower()

    if status not in ["open", "closed"]:

        flash(
            "Invalid application status.",
            "error"
        )

        return redirect(
            url_for("settings")
        )

    applications_open = (
        status == "open"
    )

    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE company_settings
                SET applications_open = %s
                """,
                (applications_open,)
            )

        conn.commit()

        if applications_open:

            flash(
                "Applications are now OPEN.",
                "success"
            )

        else:

            flash(
                "Applications are now CLOSED.",
                "success"
            )

    except Exception:

        conn.rollback()

        app.logger.exception(
            "Error updating application status"
        )

        flash(
            "Unable to update application status.",
            "error"
        )

    finally:

        conn.close()

    return redirect(
        url_for("settings")
    )

# ============================================================
# CREATE INITIAL ADMIN
# ============================================================

def create_initial_admin():

    username = os.getenv(
        "ADMIN_USERNAME"
    )

    password = os.getenv(
        "ADMIN_PASSWORD"
    )

    if not username or not password:
        return

    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id
                FROM admin_users
                WHERE username = %s
                """,
                (username,)
            )

            existing = cur.fetchone()

            if existing:
                return


            password_hash = generate_password_hash(
                password
            )


            cur.execute(
                """
                INSERT INTO admin_users (
                    username,
                    password_hash,
                    full_name
                )

                VALUES (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    username,
                    password_hash,
                    "System Administrator"
                )
            )

        conn.commit()

    finally:

        conn.close()

# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if session.get("admin_id"):

        return redirect(
            url_for("admin_dashboard")
        )


    if request.method == "POST":

        username = (
            request.form.get(
                "username",
                ""
            )
            .strip()
        )

        password = request.form.get(
            "password",
            ""
        )


        if not username or not password:

            flash(
                "Please enter your username and password.",
                "error"
            )

            return render_template(
                "admin_login.html"
            )


        conn = get_db()

        try:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        id,
                        username,
                        password_hash,
                        full_name

                    FROM admin_users

                    WHERE username = %s

                    LIMIT 1
                    """,
                    (username,)
                )

                admin = cur.fetchone()


                if not admin:

                    flash(
                        "Invalid username or password.",
                        "error"
                    )

                    return render_template(
                        "admin_login.html"
                    )


                if not check_password_hash(
                    admin["password_hash"],
                    password
                ):

                    flash(
                        "Invalid username or password.",
                        "error"
                    )

                    return render_template(
                        "admin_login.html"
                    )


                cur.execute(
                    """
                    UPDATE admin_users

                    SET last_login = CURRENT_TIMESTAMP

                    WHERE id = %s
                    """,
                    (admin["id"],)
                )

            conn.commit()


        finally:

            conn.close()


        session.clear()

        session["admin_id"] = admin["id"]

        session["admin_username"] = admin["username"]

        session["admin_name"] = (
            admin["full_name"]
            or admin["username"]
        )


        return redirect(
            url_for("admin_dashboard")
        )


    return render_template(
        "admin_login.html"
    )

# ============================================================
# ADMIN LOGOUT
# ============================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("admin_login")
    )

# ============================================================
# ADMIN AUTHENTICATION
# ============================================================

def admin_required():

    return bool(
        session.get("admin_id")
    )

# ============================================================
# APPLICATIONS MANAGEMENT
# ============================================================
@app.route("/admin/applications")
def admin_applications():

    # ============================================================
    # ADMIN LOGIN CHECK
    # ============================================================

    if not admin_required():
        return redirect(url_for("admin_login"))


    # ============================================================
    # FILTERS
    # ============================================================

    search = request.args.get(
        "search",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip()

    position = request.args.get(
        "position",
        ""
    ).strip()


    # ============================================================
    # DATABASE CONNECTION
    # ============================================================

    conn = get_db()

    try:

        with conn.cursor() as cur:

            # ====================================================
            # APPLICATION QUERY
            # ====================================================

            query = """
                SELECT
                    id,
                    application_number,

                    first_name,
                    middle_name,
                    last_name,

                    phone,
                    email,

                    position_applied,
                    highest_qualification,

                    status,

                    passport_filename,
                    cv_filename,
                    qualification_filename,

                    submitted_at

                FROM applications

                WHERE 1=1
            """

            params = []


            # ====================================================
            # SEARCH
            # ====================================================

            if search:

                query += """
                    AND (
                        application_number ILIKE %s
                        OR first_name ILIKE %s
                        OR middle_name ILIKE %s
                        OR last_name ILIKE %s
                        OR phone ILIKE %s
                        OR email ILIKE %s
                    )
                """

                search_value = f"%{search}%"

                params.extend([
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value
                ])


            # ====================================================
            # STATUS FILTER
            # ====================================================

            if status:

                query += """
                    AND status = %s
                """

                params.append(status)


            # ====================================================
            # POSITION FILTER
            # ====================================================

            if position:

                query += """
                    AND position_applied ILIKE %s
                """

                params.append(
                    f"%{position}%"
                )


            # ====================================================
            # ORDER BY APPLICATION DATE
            # ====================================================

            query += """
                ORDER BY
                    submitted_at DESC NULLS LAST,
                    id DESC
            """


            # ====================================================
            # EXECUTE
            # ====================================================

            cur.execute(
                query,
                params
            )

            applications = cur.fetchall()


            # ====================================================
            # SUMMARY COUNTS
            # ====================================================

            cur.execute(
                """
                SELECT
                    COUNT(*) AS total,

                    COUNT(*) FILTER (
                        WHERE status = 'Pending'
                    ) AS pending,

                    COUNT(*) FILTER (
                        WHERE status = 'Under Review'
                    ) AS under_review,

                    COUNT(*) FILTER (
                        WHERE status = 'Shortlisted'
                    ) AS shortlisted,

                    COUNT(*) FILTER (
                        WHERE status = 'Approved'
                    ) AS approved,

                    COUNT(*) FILTER (
                        WHERE status = 'Rejected'
                    ) AS rejected

                FROM applications
                """
            )

            summary = cur.fetchone()


    except Exception:

        app.logger.exception(
            "Error loading admin applications"
        )

        raise


    finally:

        conn.close()


    # ============================================================
    # SUMMARY VALUES
    # ============================================================

    total = (
        summary["total"]
        if summary
        else 0
    )

    pending = (
        summary["pending"]
        if summary
        else 0
    )

    under_review = (
        summary["under_review"]
        if summary
        else 0
    )

    shortlisted = (
        summary["shortlisted"]
        if summary
        else 0
    )

    approved = (
        summary["approved"]
        if summary
        else 0
    )

    rejected = (
        summary["rejected"]
        if summary
        else 0
    )


    # ============================================================
    # RENDER
    # ============================================================

    return render_template(
        "admin_applications.html",

        applications=applications,

        total=total,
        pending=pending,
        under_review=under_review,
        shortlisted=shortlisted,
        approved=approved,
        rejected=rejected,

        search=search,
        selected_status=status,
        selected_position=position
    )

# ============================================================
# VIEW APPLICATION
# ============================================================

@app.route(
    "/admin/applications/<int:application_id>"
)
def admin_application_details(application_id):

    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *
                FROM applications
                WHERE id = %s
                LIMIT 1
                """,
                (application_id,)
            )

            application = cur.fetchone()

    finally:

        conn.close()

    if not application:

        flash(
            "Application not found.",
            "error"
        )

        return redirect(
            url_for("admin_applications")
        )

    return render_template(
        "admin_application_details.html",
        application=application
    )

# ============================================================
# ADMIN SEND MESSAGE TO APPLICANT
# ============================================================

@app.route(
    "/admin/applications/<int:application_id>/message",
    methods=["POST"]
)
def send_applicant_message(application_id):

    # --------------------------------------------------------
    # CHECK ADMIN LOGIN
    # --------------------------------------------------------

    if not admin_required():
        return redirect(
            url_for("admin_login")
        )


    # --------------------------------------------------------
    # GET FORM DATA
    # --------------------------------------------------------

    subject = (
        request.form.get(
            "subject",
            ""
        )
        .strip()
    )

    message = (
        request.form.get(
            "message",
            ""
        )
        .strip()
    )

    message_type = (
        request.form.get(
            "message_type",
            "General"
        )
        .strip()
    )


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not subject:

        flash(
            "Please enter a message subject.",
            "error"
        )

        return redirect(
            url_for(
                "admin_application_details",
                application_id=application_id
            )
        )


    if not message:

        flash(
            "Please enter the message.",
            "error"
        )

        return redirect(
            url_for(
                "admin_application_details",
                application_id=application_id
            )
        )


    # --------------------------------------------------------
    # SAVE MESSAGE
    # --------------------------------------------------------

    conn = get_db()

    try:

        with conn.cursor() as cur:

            # Check applicant exists

            cur.execute(
                """
                SELECT id
                FROM applications
                WHERE id = %s
                LIMIT 1
                """,
                (application_id,)
            )

            application = cur.fetchone()

            if not application:

                flash(
                    "Application not found.",
                    "error"
                )

                return redirect(
                    url_for("admin_applications")
                )


            # Insert message

            cur.execute(
                """
                INSERT INTO applicant_messages (

                    application_id,
                    subject,
                    message,
                    message_type,
                    is_read,
                    created_at

                )

                VALUES (

                    %s,
                    %s,
                    %s,
                    %s,
                    FALSE,
                    CURRENT_TIMESTAMP

                )
                """,

                (
                    application_id,
                    subject,
                    message,
                    message_type
                )
            )


        conn.commit()


    except Exception:

        conn.rollback()

        raise


    finally:

        conn.close()


    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    flash(
        "Message sent to applicant successfully.",
        "success"
    )

    return redirect(
        url_for(
            "admin_application_details",
            application_id=application_id
        )
    )
# ============================================================
# UPDATE ADMIN NOTES
# ============================================================

@app.route(
    "/admin/applications/<int:application_id>/notes",
    methods=["POST"]
)
def update_application_notes(application_id):

    if not admin_required():
        return redirect(url_for("admin_login"))

    notes = (
        request.form.get(
            "admin_notes",
            ""
        )
        .strip()
    )

    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE applications

                SET
                    admin_notes = %s,
                    updated_at = CURRENT_TIMESTAMP

                WHERE id = %s
                """,
                (
                    notes,
                    application_id
                )
            )

        conn.commit()

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()

    flash(
        "Recruitment notes saved successfully.",
        "success"
    )

    return redirect(
        url_for(
            "admin_application_details",
            application_id=application_id
        )
    )

# ============================================================
# DOWNLOAD APPLICATION DOCUMENT
# ============================================================

# ============================================================
# SECURE APPLICATION DOCUMENT
# ============================================================

@app.route(
    "/admin/application-file/<path:filename>"
)
def admin_application_file(filename):

    if not admin_required():
        return redirect(url_for("admin_login"))

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=False
    )

def send_shortlisted_whatsapp(application):

    phone = (
        application["phone"]
        or ""
    ).strip()

    if not phone:
        raise ValueError(
            "Applicant has no phone number."
        )


    # --------------------------------------------------------
    # COMPANY WHATSAPP NUMBER
    # --------------------------------------------------------

    company_whatsapp = os.getenv(
        "COMPANY_WHATSAPP",
        "2349058842501"
    )


    # --------------------------------------------------------
    # MESSAGE
    # --------------------------------------------------------

    message = f"""
Dear {application["first_name"]},

Congratulations!

We are pleased to inform you that you have been shortlisted for the next stage of the recruitment process at AV KING VET DRUG VENTURE.

Application Number:
{application["application_number"]}

Position:
{application["position_applied"]}

Please monitor your applicant portal for further information regarding the interview.

For enquiries, please contact us on WhatsApp:
+{company_whatsapp}

Thank you.

AV KING VET DRUG VENTURE
Your Needs, Our Priority
""".strip()


    # --------------------------------------------------------
    # TEMPORARY DEVELOPMENT MODE
    # --------------------------------------------------------

    app.logger.info(
        "SHORTLISTED WHATSAPP MESSAGE:\n%s",
        message
    )

    return True

# ============================================================
# ADMIN - SCHEDULE / UPDATE INTERVIEW
# ============================================================

@app.route(
    "/admin/applications/<int:application_id>/interview",
    methods=["POST"]
)
def update_application_interview(application_id):

    # ========================================================
    # ADMIN SECURITY
    # ========================================================

    if not admin_required():
        return redirect(
            url_for("admin_login")
        )


    # ========================================================
    # GET FORM DATA
    # ========================================================

    interview_date = (
        request.form.get(
            "interview_date",
            ""
        ).strip()
    )

    interview_location = (
        request.form.get(
            "interview_location",
            ""
        ).strip()
    )

    interview_notes = (
        request.form.get(
            "interview_notes",
            ""
        ).strip()
    )

    interview_status = (
        request.form.get(
            "interview_status",
            "Scheduled"
        ).strip()
    )


    # ========================================================
    # VALIDATION
    # ========================================================

    allowed_interview_statuses = {
        "Scheduled",
        "Completed",
        "Rescheduled",
        "Cancelled"
    }

    if interview_status not in allowed_interview_statuses:

        flash(
            "Invalid interview status.",
            "error"
        )

        return redirect(
            url_for(
                "admin_application_details",
                application_id=application_id
            )
        )


    # ========================================================
    # INTERVIEW DATE VALIDATION
    # ========================================================

    if interview_date:

        try:

            datetime.strptime(
                interview_date,
                "%Y-%m-%dT%H:%M"
            )

        except ValueError:

            flash(
                "Invalid interview date and time.",
                "error"
            )

            return redirect(
                url_for(
                    "admin_application_details",
                    application_id=application_id
                )
            )


    # ========================================================
    # DATABASE
    # ========================================================

    conn = get_db()

    try:

        with conn.cursor() as cur:

            # ------------------------------------------------
            # CHECK APPLICATION
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    id,
                    first_name,
                    last_name,
                    application_number,
                    status
                FROM applications
                WHERE id = %s
                LIMIT 1
                """,
                (application_id,)
            )

            application = cur.fetchone()


            if not application:

                flash(
                    "Application not found.",
                    "error"
                )

                return redirect(
                    url_for("admin_applications")
                )


            # ------------------------------------------------
            # SAVE INTERVIEW
            # ------------------------------------------------

            cur.execute(
                """
                UPDATE applications

                SET

                    interview_date = %s,

                    interview_location = %s,

                    interview_notes = %s,

                    interview_status = %s,

                    updated_at = CURRENT_TIMESTAMP

                WHERE id = %s
                """,
                (
                    interview_date or None,
                    interview_location or None,
                    interview_notes or None,
                    interview_status,
                    application_id
                )
            )


            # ------------------------------------------------
            # CREATE PORTAL MESSAGE
            # ------------------------------------------------

            if interview_date:

                cur.execute(
                    """
                    INSERT INTO applicant_messages (

                        application_id,

                        subject,

                        message,

                        message_type

                    )

                    VALUES (

                        %s,

                        %s,

                        %s,

                        %s

                    )
                    """,
                    (
                        application_id,

                        "Interview Scheduled",

                        (
                            "Your interview has been scheduled.\n\n"
                            f"Date & Time: {interview_date}\n"
                            f"Location: {interview_location or 'To be confirmed'}\n\n"
                            f"Instructions: "
                            f"{interview_notes or 'Please check your applicant portal for further updates.'}"
                        ),

                        "Interview"
                    )
                )


        conn.commit()


    except Exception:

        conn.rollback()

        raise


    finally:

        conn.close()


    # ========================================================
    # SUCCESS
    # ========================================================

    flash(
        "Interview details saved successfully.",
        "success"
    )


    return redirect(
        url_for(
            "admin_application_details",
            application_id=application_id
        )
    )
@app.route("/applicant/dashboard")
def applicant_dashboard():

    if not session.get("applicant_id"):
        return redirect(url_for("applicant_login"))

    applicant_id = session["applicant_id"]

    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *
                FROM applications
                WHERE id = %s
                LIMIT 1
                """,
                (applicant_id,)
            )

            application = cur.fetchone()

    finally:

        conn.close()


    if not application:

        session.clear()

        return redirect(
            url_for("applicant_login")
        )


    return render_template(
        "applicant_dashboard.html",
        application=application
    )

@app.route(
    "/admin/positions",
    methods=["GET", "POST"]
)
def admin_positions():

    if not admin_required():
        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    try:

        with conn.cursor() as cur:

            # ==================================================
            # ADD POSITION
            # ==================================================

            if request.method == "POST":

                position_name = (
                    request.form.get(
                        "position_name",
                        ""
                    ).strip()
                )

                description = (
                    request.form.get(
                        "description",
                        ""
                    ).strip()
                )

                if not position_name:

                    flash(
                        "Please enter a position name.",
                        "error"
                    )

                else:

                    cur.execute(
                        """
                        INSERT INTO available_positions
                        (
                            position_name,
                            description,
                            is_active
                        )
                        VALUES
                        (
                            %s,
                            %s,
                            TRUE
                        )
                        ON CONFLICT (position_name)
                        DO UPDATE SET
                            description = EXCLUDED.description,
                            is_active = TRUE
                        """,
                        (
                            position_name,
                            description or None
                        )
                    )

                    conn.commit()

                    flash(
                        "Position added successfully.",
                        "success"
                    )

                    return redirect(
                        url_for(
                            "admin_positions"
                        )
                    )


            # ==================================================
            # GET POSITIONS
            # ==================================================

            cur.execute(
                """
                SELECT
                    id,
                    position_name,
                    description,
                    is_active,
                    created_at
                FROM available_positions
                ORDER BY
                    is_active DESC,
                    position_name ASC
                """
            )

            positions = cur.fetchall()


    except Exception:

        conn.rollback()

        app.logger.exception(
            "Error managing available positions"
        )

        flash(
            "Unable to manage positions.",
            "error"
        )

        positions = []


    finally:

        conn.close()


    return render_template(
        "admin_positions.html",
        positions=positions
    )

@app.route(
    "/admin/positions/<int:position_id>/edit",
    methods=["POST"]
)
def admin_edit_position(position_id):

    if not admin_required():
        return redirect(
            url_for("admin_login")
        )

    position_name = (
        request.form.get(
            "position_name",
            ""
        ).strip()
    )

    description = (
        request.form.get(
            "description",
            ""
        ).strip()
    )

    if not position_name:

        flash(
            "Position name is required.",
            "error"
        )

        return redirect(
            url_for("admin_positions")
        )

    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE available_positions

                SET
                    position_name = %s,
                    description = %s

                WHERE id = %s
                """,
                (
                    position_name,
                    description or None,
                    position_id
                )
            )

        conn.commit()

        flash(
            "Position updated successfully.",
            "success"
        )

    except Exception:

        conn.rollback()

        app.logger.exception(
            "Error editing position"
        )

        flash(
            "Unable to update position.",
            "error"
        )

    finally:

        conn.close()

    return redirect(
        url_for("admin_positions")
    )

@app.route(
    "/admin/positions/<int:position_id>/toggle",
    methods=["POST"]
)
def admin_toggle_position(position_id):

    if not admin_required():
        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE available_positions

                SET is_active =
                    NOT is_active

                WHERE id = %s
                """,
                (position_id,)
            )

        conn.commit()

        flash(
            "Position status updated.",
            "success"
        )

    except Exception:

        conn.rollback()

        app.logger.exception(
            "Error changing position status"
        )

        flash(
            "Unable to change position status.",
            "error"
        )

    finally:

        conn.close()

    return redirect(
        url_for("admin_positions")
    )

# ============================================================
# SEND WHATSAPP NOTIFICATION
# ============================================================

@app.route(
    "/admin/applications/<int:application_id>/whatsapp"
)
def send_application_whatsapp(application_id):

    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    first_name,
                    last_name,
                    phone,
                    application_number,
                    position_applied,
                    status
                FROM applications
                WHERE id = %s
                LIMIT 1
                """,
                (application_id,)
            )

            application = cur.fetchone()

    finally:

        conn.close()


    if not application:

        flash(
            "Application not found.",
            "error"
        )

        return redirect(
            url_for("admin_applications")
        )


    # ========================================================
    # ONLY SHORTLISTED APPLICANTS
    # ========================================================

    if application["status"] != "Shortlisted":

        flash(
            "WhatsApp notification is only available "
            "for shortlisted applicants.",
            "error"
        )

        return redirect(
            url_for(
                "admin_application_details",
                application_id=application_id
            )
        )


    phone = (
        application["phone"] or ""
    ).strip()


    if not phone:

        flash(
            "This applicant does not have a valid phone number.",
            "error"
        )

        return redirect(
            url_for(
                "admin_application_details",
                application_id=application_id
            )
        )


    # ========================================================
    # CONVERT NIGERIAN NUMBER TO INTERNATIONAL FORMAT
    # ========================================================

    whatsapp_phone = phone

    if whatsapp_phone.startswith("0"):

        whatsapp_phone = (
            "234"
            + whatsapp_phone[1:]
        )

    elif whatsapp_phone.startswith("+234"):

        whatsapp_phone = whatsapp_phone[1:]


    # ========================================================
    # MESSAGE
    # ========================================================

    applicant_name = (
        f"{application['first_name']} "
        f"{application['last_name']}"
    )


    message = (
        f"Dear {applicant_name},\n\n"

        f"Congratulations!\n\n"

        f"We are pleased to inform you that your "
        f"application for the position of "
        f"{application['position_applied']} at "
        f"{COMPANY_NAME} has been shortlisted "
        f"for the next stage of our recruitment process.\n\n"

        f"Application Number: "
        f"{application['application_number']}\n\n"

        f"Please log in to your Applicant Portal regularly "
        f"to check for further recruitment updates and "
        f"interview information.\n\n"

        f"Regards,\n"
        f"{COMPANY_NAME}\n"
        f"{COMPANY_PHONE}"
    )


    # ========================================================
    # WHATSAPP URL
    # ========================================================

    whatsapp_url = (
        "https://wa.me/"
        + whatsapp_phone
        + "?text="
        + quote(message)
    )


    return redirect(whatsapp_url)
# ============================================================
# UPDATE APPLICATION STATUS
# ============================================================

@app.route(
    "/admin/applications/<int:application_id>/status",
    methods=["POST"]
)
def update_application_status(application_id):

    if not admin_required():
        return redirect(url_for("admin_login"))

    new_status = (
        request.form.get("status", "")
        .strip()
    )

    allowed_statuses = {
        "Pending",
        "Under Review",
        "Shortlisted",
        "Approved",
        "Rejected"
    }

    if new_status not in allowed_statuses:

        flash(
            "Invalid application status.",
            "error"
        )

        return redirect(
            url_for(
                "admin_application_details",
                application_id=application_id
            )
        )

    conn = get_db()

    try:

        with conn.cursor() as cur:

            # =================================================
            # GET APPLICATION
            # =================================================

            cur.execute(
                """
                SELECT
                    id,
                    first_name,
                    last_name,
                    phone,
                    application_number,
                    position_applied,
                    status,
                    notification_sent
                FROM applications
                WHERE id = %s
                LIMIT 1
                """,
                (application_id,)
            )

            application = cur.fetchone()


            if not application:

                flash(
                    "Application not found.",
                    "error"
                )

                return redirect(
                    url_for("admin_applications")
                )


            # =================================================
            # SHORTLISTED
            # =================================================

            if new_status == "Shortlisted":

                cur.execute(
                    """
                    UPDATE applications

                    SET
                        status = %s,

                        shortlisted_at =
                            COALESCE(
                                shortlisted_at,
                                CURRENT_TIMESTAMP
                            ),

                        updated_at =
                            CURRENT_TIMESTAMP

                    WHERE id = %s
                    """,
                    (
                        new_status,
                        application_id
                    )
                )


            # =================================================
            # OTHER STATUSES
            # =================================================

            else:

                cur.execute(
                    """
                    UPDATE applications

                    SET
                        status = %s,

                        updated_at =
                            CURRENT_TIMESTAMP

                    WHERE id = %s
                    """,
                    (
                        new_status,
                        application_id
                    )
                )


        conn.commit()


    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


    # =========================================================
    # SHORTLISTED WHATSAPP NOTIFICATION
    # =========================================================

    if new_status == "Shortlisted":

        applicant_name = (
            f"{application['first_name']} "
            f"{application['last_name']}"
        )

        phone = (
            application["phone"]
            or ""
        ).strip()

        application_number = (
            application["application_number"]
        )

        position = (
            application["position_applied"]
        )


        # -----------------------------------------------------
        # NORMALIZE NIGERIAN PHONE NUMBER
        # -----------------------------------------------------

        whatsapp_phone = phone

        if whatsapp_phone.startswith("0"):

            whatsapp_phone = (
                "234"
                + whatsapp_phone[1:]
            )

        elif whatsapp_phone.startswith("+234"):

            whatsapp_phone = (
                whatsapp_phone[1:]
            )


        # -----------------------------------------------------
        # CREATE WHATSAPP MESSAGE
        # -----------------------------------------------------

        whatsapp_message = (
            f"Dear {applicant_name},\n\n"

            f"Congratulations!\n\n"

            f"We are pleased to inform you that your "
            f"application for the position of "
            f"{position} at {COMPANY_NAME} "
            f"has been shortlisted for the next stage "
            f"of our recruitment process.\n\n"

            f"Application Number: "
            f"{application_number}\n\n"

            f"Please log in to your Applicant Portal "
            f"regularly to check for further recruitment "
            f"updates and interview information.\n\n"

            f"Regards,\n"
            f"{COMPANY_NAME}\n"
            f"{COMPANY_PHONE}"
        )


        # -----------------------------------------------------
        # WHATSAPP LINK
        # -----------------------------------------------------

        from urllib.parse import quote

        whatsapp_url = (
            f"https://wa.me/"
            f"{whatsapp_phone}"
            f"?text="
            f"{quote(whatsapp_message)}"
        )


        # =====================================================
        # RECORD NOTIFICATION STATE
        # =====================================================

        conn = get_db()

        try:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    UPDATE applications

                    SET
                        notification_sent = TRUE,
                        notification_sent_at =
                            CURRENT_TIMESTAMP,

                        updated_at =
                            CURRENT_TIMESTAMP

                    WHERE id = %s
                    """,
                    (application_id,)
                )

            conn.commit()

        except Exception:

            conn.rollback()

            raise

        finally:

            conn.close()


        # =====================================================
        # SHOW ADMIN WHATSAPP ACTION
        # =====================================================

        flash(
            "Applicant shortlisted successfully. "
            "WhatsApp notification is ready to send.",
            "success"
        )

        return redirect(
            url_for(
                "admin_application_details",
                application_id=application_id,
                whatsapp_url=whatsapp_url
            )
        )


    # =========================================================
    # OTHER STATUS
    # =========================================================

    flash(
        "Application status updated successfully.",
        "success"
    )

    return redirect(
        url_for(
            "admin_application_details",
            application_id=application_id
        )
    )

# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
@app.route("/admin/dashboard")
def admin_dashboard():

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )


    conn = get_db()

    try:

        with conn.cursor() as cur:

            # ----------------------------------------------
            # TOTAL APPLICATIONS
            # ----------------------------------------------

            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM applications
                """
            )

            total = cur.fetchone()["total"]


            # ----------------------------------------------
            # PENDING
            # ----------------------------------------------

            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM applications
                WHERE status = 'Pending'
                """
            )

            pending = cur.fetchone()["total"]


            # ----------------------------------------------
            # UNDER REVIEW
            # ----------------------------------------------

            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM applications
                WHERE status = 'Under Review'
                """
            )

            under_review = (
                cur.fetchone()["total"]
            )


            # ----------------------------------------------
            # SHORTLISTED
            # ----------------------------------------------

            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM applications
                WHERE status = 'Shortlisted'
                """
            )

            shortlisted = (
                cur.fetchone()["total"]
            )


            # ----------------------------------------------
            # APPROVED
            # ----------------------------------------------

            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM applications
                WHERE status = 'Approved'
                """
            )

            approved = (
                cur.fetchone()["total"]
            )


            # ----------------------------------------------
            # REJECTED
            # ----------------------------------------------

            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM applications
                WHERE status = 'Rejected'
                """
            )

            rejected = (
                cur.fetchone()["total"]
            )


            # ----------------------------------------------
            # RECENT APPLICATIONS
            # ----------------------------------------------

            cur.execute(
                """
                SELECT

                    id,

                    application_number,

                    first_name,

                    middle_name,

                    last_name,

                    phone,

                    position_applied,

                    status,

                    submitted_at

                FROM applications

                ORDER BY submitted_at DESC

                LIMIT 10
                """
            )

            recent_applications = cur.fetchall()


    finally:

        conn.close()


    return render_template(
        "admin_dashboard.html",

        total=total,

        pending=pending,

        under_review=under_review,

        shortlisted=shortlisted,

        approved=approved,

        rejected=rejected,

        recent_applications=recent_applications
    )



# ============================================================
# MARK WHATSAPP NOTIFICATION AS SENT
# ============================================================

@app.route(
    "/admin/applications/<int:application_id>/whatsapp-sent",
    methods=["POST"]
)
def mark_whatsapp_notification_sent(application_id):

    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    status
                FROM applications
                WHERE id = %s
                LIMIT 1
                """,
                (application_id,)
            )

            application = cur.fetchone()

            if not application:

                flash(
                    "Application not found.",
                    "error"
                )

                return redirect(
                    url_for("admin_applications")
                )


            if application["status"] != "Shortlisted":

                flash(
                    "Only shortlisted applicants can have "
                    "a shortlist notification recorded.",
                    "error"
                )

                return redirect(
                    url_for(
                        "admin_application_details",
                        application_id=application_id
                    )
                )


            cur.execute(
                """
                UPDATE applications

                SET
                    notification_sent = TRUE,

                    notification_sent_at =
                        CURRENT_TIMESTAMP,

                    updated_at =
                        CURRENT_TIMESTAMP

                WHERE id = %s
                """,
                (application_id,)
            )


        conn.commit()


    except Exception:

        conn.rollback()
        raise


    finally:

        conn.close()


    flash(
        "WhatsApp notification marked as sent.",
        "success"
    )


    return redirect(
        url_for(
            "admin_application_details",
            application_id=application_id
        )
    )
# ============================================================
# APPLICATION SUCCESS
# ============================================================

@app.route(
    "/application-success/<application_number>"
)
def application_success(
    application_number
):

    return render_template(
        "application_success.html",
        application_number=application_number
    )

# ============================================================
# APPLICANT AUTHENTICATION
# ============================================================

def applicant_required():

    return bool(
        session.get("applicant_id")
    )

# ============================================================
# APPLICANT PORTAL LOGIN
# ============================================================

@app.route("/applicant/login", methods=["GET", "POST"])
def applicant_login():

    if request.method == "GET":
        return render_template("applicant_login.html")

    application_number = (
        request.form.get("application_number", "")
        .strip()
        .upper()
    )

    password = request.form.get(
        "password",
        ""
    )

    if not application_number or not password:

        flash(
            "Please enter your application number and password.",
            "error"
        )

        return render_template(
            "applicant_login.html"
        )

    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    application_number,
                    first_name,
                    last_name,
                    password_hash,
                    portal_active,
                    status
                FROM applications
                WHERE application_number = %s
                LIMIT 1
                """,
                (application_number,)
            )

            applicant = cur.fetchone()

    finally:

        conn.close()

    if not applicant:

        flash(
            "Invalid application number or password.",
            "error"
        )

        return render_template(
            "applicant_login.html"
        )

    if not applicant["portal_active"]:

        flash(
            "Your applicant portal has been disabled.",
            "error"
        )

        return render_template(
            "applicant_login.html"
        )

    if not applicant["password_hash"]:

        flash(
            "Your applicant portal account has not been activated yet.",
            "error"
        )

        return render_template(
            "applicant_login.html"
        )

    if not check_password_hash(
        applicant["password_hash"],
        password
    ):

        flash(
            "Invalid application number or password.",
            "error"
        )

        return render_template(
            "applicant_login.html"
        )

    # --------------------------------------------------------
    # LOGIN SUCCESS
    # --------------------------------------------------------

    session.clear()

    session["applicant_id"] = applicant["id"]

    session["applicant_application_number"] = (
        applicant["application_number"]
    )

    session["applicant_name"] = (
        applicant["first_name"]
        + " "
        + applicant["last_name"]
    )

    # --------------------------------------------------------
    # UPDATE LAST LOGIN
    # --------------------------------------------------------

    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE applications

                SET
                    last_login = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP

                WHERE id = %s
                """,
                (applicant["id"],)
            )

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()

    return redirect(
        url_for("applicant_portal")
    )



# ============================================================
# APPLICANT LOGOUT
# ============================================================

@app.route("/applicant/logout")
def applicant_logout():

    session.pop(
        "applicant_id",
        None
    )

    session.pop(
        "applicant_application_number",
        None
    )

    session.pop(
        "applicant_name",
        None
    )

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("applicant_login")
    )

# ============================================================
# APPLICANT PORTAL
# ============================================================

@app.route("/applicant/portal")
def applicant_portal():

    # --------------------------------------------------------
    # CHECK APPLICANT LOGIN
    # --------------------------------------------------------

    applicant_id = session.get("applicant_id")

    if not applicant_id:
        return redirect(
            url_for("applicant_login")
        )

    conn = get_db()

    try:

        with conn.cursor() as cur:

            # ------------------------------------------------
            # GET APPLICATION
            # ------------------------------------------------

            cur.execute(
                """
                SELECT *
                FROM applications
                WHERE id = %s
                LIMIT 1
                """,
                (applicant_id,)
            )

            application = cur.fetchone()

            if not application:

                session.pop(
                    "applicant_id",
                    None
                )

                session.pop(
                    "applicant_application_id",
                    None
                )

                flash(
                    "Application account not found.",
                    "error"
                )

                return redirect(
                    url_for("applicant_login")
                )


            # ------------------------------------------------
            # GET APPLICANT MESSAGES
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    id,
                    subject,
                    message,
                    message_type,
                    is_read,
                    created_at

                FROM applicant_messages

                WHERE application_id = %s

                ORDER BY created_at DESC
                """,
                (applicant_id,)
            )

            messages = cur.fetchall()


            # ------------------------------------------------
            # COUNT UNREAD MESSAGES
            # ------------------------------------------------

            cur.execute(
                """
                SELECT COUNT(*) AS unread_count

                FROM applicant_messages

                WHERE application_id = %s

                AND is_read = FALSE
                """,
                (applicant_id,)
            )

            unread_row = cur.fetchone()

            unread_count = int(
                unread_row["unread_count"]
                if unread_row
                else 0
            )


    except Exception:

        raise

    finally:

        conn.close()


    # --------------------------------------------------------
    # RENDER APPLICANT DASHBOARD
    # --------------------------------------------------------

    return render_template(
        "applicant_portal.html",

        application=application,

        messages=messages,

        unread_count=unread_count
            )

# ============================================================
# APPLICANT MESSAGES
# ============================================================

@app.route("/applicant/messages")
def applicant_messages():

    # --------------------------------------------------------
    # CHECK APPLICANT LOGIN
    # --------------------------------------------------------

    if not session.get("applicant_logged_in"):
        return redirect(
            url_for("applicant_login")
        )

    application_id = session.get(
        "applicant_application_id"
    )

    if not application_id:
        flash(
            "Applicant session is invalid. Please login again.",
            "error"
        )

        return redirect(
            url_for("applicant_login")
        )

    conn = get_db()

    try:

        with conn.cursor() as cur:

            # ------------------------------------------------
            # GET ALL MESSAGES
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    id,
                    application_id,
                    subject,
                    message,
                    message_type,
                    is_read,
                    created_at
                FROM applicant_messages
                WHERE application_id = %s
                ORDER BY created_at DESC
                """,
                (application_id,)
            )

            messages = cur.fetchall()


            # ------------------------------------------------
            # COUNT UNREAD MESSAGES
            # ------------------------------------------------

            cur.execute(
                """
                SELECT COUNT(*) AS unread_count
                FROM applicant_messages
                WHERE application_id = %s
                  AND is_read = FALSE
                """,
                (application_id,)
            )

            row = cur.fetchone()

            unread_count = (
                row["unread_count"]
                if row
                else 0
            )


    finally:

        conn.close()


    # --------------------------------------------------------
    # UPDATE SESSION BADGE
    # --------------------------------------------------------

    session["applicant_unread_count"] = unread_count


    return render_template(
        "applicant_messages.html",
        messages=messages,
        unread_count=unread_count
    )

# ============================================================
# VIEW APPLICANT MESSAGE
# ============================================================

@app.route("/applicant/messages/<int:message_id>")
def applicant_message(message_id):

    # --------------------------------------------------------
    # CHECK APPLICANT LOGIN
    # --------------------------------------------------------

    if not session.get("applicant_logged_in"):
        return redirect(
            url_for("applicant_login")
        )

    application_id = session.get(
        "applicant_application_id"
    )

    if not application_id:
        return redirect(
            url_for("applicant_login")
        )

    conn = get_db()

    try:

        with conn.cursor() as cur:

            # ------------------------------------------------
            # IMPORTANT:
            # Make sure the message belongs to THIS applicant
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    id,
                    application_id,
                    subject,
                    message,
                    message_type,
                    is_read,
                    created_at
                FROM applicant_messages
                WHERE id = %s
                  AND application_id = %s
                LIMIT 1
                """,
                (
                    message_id,
                    application_id
                )
            )

            message = cur.fetchone()


            if not message:

                flash(
                    "Message not found.",
                    "error"
                )

                return redirect(
                    url_for("applicant_messages")
                )


            # ------------------------------------------------
            # MARK MESSAGE AS READ
            # ------------------------------------------------

            cur.execute(
                """
                UPDATE applicant_messages
                SET is_read = TRUE
                WHERE id = %s
                  AND application_id = %s
                """,
                (
                    message_id,
                    application_id
                )
            )


        conn.commit()


    except Exception:

        conn.rollback()

        raise


    finally:

        conn.close()


    # --------------------------------------------------------
    # UPDATE UNREAD COUNT
    # --------------------------------------------------------

    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT COUNT(*) AS unread_count
                FROM applicant_messages
                WHERE application_id = %s
                  AND is_read = FALSE
                """,
                (application_id,)
            )

            row = cur.fetchone()

            unread_count = (
                row["unread_count"]
                if row
                else 0
            )

    finally:

        conn.close()


    session["applicant_unread_count"] = unread_count


    return render_template(
        "applicant_message.html",
        message=message,
        unread_count=unread_count
                )

# ============================================================
# ADMIN SETTINGS
# ============================================================
@app.route(
    "/admin/settings",
    methods=["GET", "POST"]
)
def admin_settings():

    # =========================================================
    # ADMIN AUTHENTICATION
    # =========================================================

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )


    conn = get_db()

    try:

        with conn.cursor() as cur:

            # =================================================
            # GET EXISTING SETTINGS
            # =================================================

            cur.execute(
                """
                SELECT *
                FROM company_settings
                ORDER BY id ASC
                LIMIT 1
                """
            )

            existing_settings = cur.fetchone()


            # =================================================
            # POST
            # =================================================

            if request.method == "POST":

                # =================================================
                # COMPANY INFORMATION
                # =================================================

                company_name = (
                    request.form.get(
                        "company_name",
                        ""
                    ).strip()
                )

                company_email = (
                    request.form.get(
                        "company_email",
                        ""
                    ).strip()
                )

                company_phone = (
                    request.form.get(
                        "company_phone",
                        ""
                    ).strip()
                )

                company_address = (
                    request.form.get(
                        "company_address",
                        ""
                    ).strip()
                )

                company_website = (
                    request.form.get(
                        "company_website",
                        ""
                    ).strip()
                )

                footer_text = (
                    request.form.get(
                        "footer_text",
                        ""
                    ).strip()
                )


                # =================================================
                # APPLICATION SETTINGS
                # =================================================

                application_status = (
                    request.form.get(
                        "application_status",
                        "Open"
                    ).strip()
                )

                application_deadline = (
                    request.form.get(
                        "application_deadline",
                        ""
                    ).strip()
                )


                if application_status not in [
                    "Open",
                    "Closed"
                ]:

                    application_status = "Open"


                if not application_deadline:

                    application_deadline = None


                # =================================================
                # ATTENDANCE ENABLED
                # =================================================

                attendance_enabled = (
                    request.form.get(
                        "attendance_enabled"
                    ) == "1"
                )


                # =================================================
                # COMPANY GPS LOCATION
                # =================================================

                latitude_raw = (
                    request.form.get(
                        "company_latitude",
                        ""
                    ).strip()
                )

                longitude_raw = (
                    request.form.get(
                        "company_longitude",
                        ""
                    ).strip()
                )


                try:

                    if latitude_raw:

                        company_latitude = float(
                            latitude_raw
                        )

                    else:

                        company_latitude = None


                    if longitude_raw:

                        company_longitude = float(
                            longitude_raw
                        )

                    else:

                        company_longitude = None


                except (
                    ValueError,
                    TypeError
                ):

                    flash(
                        "Please enter valid company GPS coordinates.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "admin_settings"
                        )
                    )


                # =================================================
                # VALIDATE LATITUDE
                # =================================================

                if company_latitude is not None:

                    if not (
                        -90
                        <= company_latitude
                        <= 90
                    ):

                        flash(
                            "Company latitude must be between -90 and 90.",
                            "error"
                        )

                        return redirect(
                            url_for(
                                "admin_settings"
                            )
                        )


                # =================================================
                # VALIDATE LONGITUDE
                # =================================================

                if company_longitude is not None:

                    if not (
                        -180
                        <= company_longitude
                        <= 180
                    ):

                        flash(
                            "Company longitude must be between -180 and 180.",
                            "error"
                        )

                        return redirect(
                            url_for(
                                "admin_settings"
                            )
                        )


                # =================================================
                # ATTENDANCE RADIUS
                # =================================================

                attendance_radius_raw = (
                    request.form.get(
                        "attendance_radius",
                        "100"
                    ).strip()
                )


                try:

                    attendance_radius = int(
                        attendance_radius_raw
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    flash(
                        "Attendance radius must be a valid number.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "admin_settings"
                        )
                    )


                if attendance_radius < 20:

                    attendance_radius = 20


                if attendance_radius > 5000:

                    attendance_radius = 5000


                # =================================================
                # WORKING HOURS
                # =================================================

                clock_in_start = (
                    request.form.get(
                        "clock_in_start",
                        "06:00"
                    ).strip()
                )

                clock_in_end = (
                    request.form.get(
                        "clock_in_end",
                        "10:00"
                    ).strip()
                )

                clock_out_start = (
                    request.form.get(
                        "clock_out_start",
                        "15:00"
                    ).strip()
                )

                clock_out_end = (
                    request.form.get(
                        "clock_out_end",
                        "23:00"
                    ).strip()
                )


                # =================================================
                # TIME VALIDATION
                # =================================================

                try:

                    datetime.strptime(
                        clock_in_start,
                        "%H:%M"
                    )

                    datetime.strptime(
                        clock_in_end,
                        "%H:%M"
                    )

                    datetime.strptime(
                        clock_out_start,
                        "%H:%M"
                    )

                    datetime.strptime(
                        clock_out_end,
                        "%H:%M"
                    )

                except ValueError:

                    flash(
                        "Please provide valid attendance times.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "admin_settings"
                        )
                    )


                # =================================================
                # LATE THRESHOLD
                # =================================================

                late_after_raw = (
                    request.form.get(
                        "late_after_minutes",
                        "15"
                    ).strip()
                )


                try:

                    late_after_minutes = int(
                        late_after_raw
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    late_after_minutes = 15


                if late_after_minutes < 0:

                    late_after_minutes = 0


                # =================================================
                # EARLY CLOCK-OUT THRESHOLD
                # =================================================

                early_before_raw = (
                    request.form.get(
                        "early_before_minutes",
                        "15"
                    ).strip()
                )


                try:

                    early_before_minutes = int(
                        early_before_raw
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    early_before_minutes = 15


                if early_before_minutes < 0:

                    early_before_minutes = 0


                # =================================================
                # ADMIN ACCOUNT
                # =================================================

                admin_username = (
                    request.form.get(
                        "admin_username",
                        ""
                    ).strip()
                )

                admin_password = (
                    request.form.get(
                        "admin_password",
                        ""
                    ).strip()
                )

                confirm_admin_password = (
                    request.form.get(
                        "confirm_admin_password",
                        ""
                    ).strip()
                )


                # =================================================
                # ADMIN USERNAME VALIDATION
                # =================================================

                if not admin_username:

                    flash(
                        "Admin username cannot be empty.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "admin_settings"
                        )
                    )


                # =================================================
                # ADMIN PASSWORD
                # =================================================

                admin_password_hash = None


                if admin_password:

                    if len(admin_password) < 6:

                        flash(
                            "Admin password must contain at least 6 characters.",
                            "error"
                        )

                        return redirect(
                            url_for(
                                "admin_settings"
                            )
                        )


                    if (
                        admin_password
                        != confirm_admin_password
                    ):

                        flash(
                            "Admin passwords do not match.",
                            "error"
                        )

                        return redirect(
                            url_for(
                                "admin_settings"
                            )
                        )


                    admin_password_hash = (
                        generate_password_hash(
                            admin_password
                        )
                    )


                # =================================================
                # LOGO
                # =================================================

                logo_filename = None

                logo_file = request.files.get(
                    "logo"
                )


                if (
                    logo_file
                    and logo_file.filename
                ):

                    original_filename = (
                        secure_filename(
                            logo_file.filename
                        )
                    )


                    # =================================================
                    # ALLOWED LOGO EXTENSIONS
                    # =================================================

                    allowed_extensions = {
                        "png",
                        "jpg",
                        "jpeg",
                        "webp"
                    }


                    if (
                        "."
                        not in original_filename
                    ):

                        flash(
                            "Invalid logo file.",
                            "error"
                        )

                        return redirect(
                            url_for(
                                "admin_settings"
                            )
                        )


                    extension = (
                        original_filename
                        .rsplit(
                            ".",
                            1
                        )[1]
                        .lower()
                    )


                    if (
                        extension
                        not in allowed_extensions
                    ):

                        flash(
                            "Invalid logo format. "
                            "Please upload PNG, JPG, JPEG or WEBP.",
                            "error"
                        )

                        return redirect(
                            url_for(
                                "admin_settings"
                            )
                        )


                    # =================================================
                    # UPLOAD DIRECTORY
                    # =================================================

                    upload_folder = os.path.join(
                        app.root_path,
                        "static",
                        "uploads"
                    )


                    os.makedirs(
                        upload_folder,
                        exist_ok=True
                    )


                    # =================================================
                    # UNIQUE FILE NAME
                    # =================================================

                    logo_filename = (
                        "company_logo_"
                        + uuid.uuid4().hex
                        + "."
                        + extension
                    )


                    logo_path = os.path.join(
                        upload_folder,
                        logo_filename
                    )


                    # =================================================
                    # SAVE LOGO
                    # =================================================

                    logo_file.save(
                        logo_path
                    )


                    # =================================================
                    # DELETE OLD LOGO
                    # =================================================

                    if existing_settings:

                        old_logo = (
                            existing_settings["logo"]
                        )


                        if old_logo:

                            old_logo_path = os.path.join(
                                upload_folder,
                                old_logo
                            )


                            try:

                                if os.path.exists(
                                    old_logo_path
                                ):

                                    os.remove(
                                        old_logo_path
                                    )

                            except Exception:

                                app.logger.warning(
                                    "Could not delete old company logo.",
                                    exc_info=True
                                )


                # =================================================
                # CREATE SETTINGS
                # =================================================

                if not existing_settings:

                    cur.execute(
                        """
                        INSERT INTO company_settings
                        (
                            company_name,
                            company_email,
                            company_phone,
                            company_address,
                            company_website,
                            footer_text,

                            application_status,
                            application_deadline,

                            logo,

                            admin_username,
                            admin_password_hash,

                            attendance_enabled,

                            company_latitude,
                            company_longitude,

                            attendance_radius,

                            clock_in_start,
                            clock_in_end,

                            clock_out_start,
                            clock_out_end,

                            late_after_minutes,
                            early_before_minutes
                        )

                        VALUES
                        (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,

                            %s,
                            %s,

                            %s,

                            %s,
                            %s,

                            %s,

                            %s,
                            %s,

                            %s,

                            %s,
                            %s,

                            %s,
                            %s,

                            %s,
                            %s
                        )
                        """,
                        (
                            company_name,
                            company_email,
                            company_phone,
                            company_address,
                            company_website,
                            footer_text,

                            application_status,
                            application_deadline,

                            logo_filename,

                            admin_username,
                            admin_password_hash,

                            attendance_enabled,

                            company_latitude,
                            company_longitude,

                            attendance_radius,

                            clock_in_start,
                            clock_in_end,

                            clock_out_start,
                            clock_out_end,

                            late_after_minutes,
                            early_before_minutes
                        )
                    )


                # =================================================
                # UPDATE EXISTING SETTINGS
                # =================================================

                else:

                    settings_id = (
                        existing_settings["id"]
                    )


                    # =================================================
                    # UPDATE COMPANY + ATTENDANCE SETTINGS
                    # =================================================

                    if logo_filename:

                        cur.execute(
                            """
                            UPDATE company_settings
                            SET

                                company_name = %s,
                                company_email = %s,
                                company_phone = %s,
                                company_address = %s,
                                company_website = %s,
                                footer_text = %s,

                                application_status = %s,
                                application_deadline = %s,

                                logo = %s,

                                admin_username = %s,

                                attendance_enabled = %s,

                                company_latitude = %s,
                                company_longitude = %s,

                                attendance_radius = %s,

                                clock_in_start = %s,
                                clock_in_end = %s,

                                clock_out_start = %s,
                                clock_out_end = %s,

                                late_after_minutes = %s,
                                early_before_minutes = %s

                            WHERE id = %s
                            """,
                            (
                                company_name,
                                company_email,
                                company_phone,
                                company_address,
                                company_website,
                                footer_text,

                                application_status,
                                application_deadline,

                                logo_filename,

                                admin_username,

                                attendance_enabled,

                                company_latitude,
                                company_longitude,

                                attendance_radius,

                                clock_in_start,
                                clock_in_end,

                                clock_out_start,
                                clock_out_end,

                                late_after_minutes,
                                early_before_minutes,

                                settings_id
                            )
                        )


                    else:

                        cur.execute(
                            """
                            UPDATE company_settings
                            SET

                                company_name = %s,
                                company_email = %s,
                                company_phone = %s,
                                company_address = %s,
                                company_website = %s,
                                footer_text = %s,

                                application_status = %s,
                                application_deadline = %s,

                                admin_username = %s,

                                attendance_enabled = %s,

                                company_latitude = %s,
                                company_longitude = %s,

                                attendance_radius = %s,

                                clock_in_start = %s,
                                clock_in_end = %s,

                                clock_out_start = %s,
                                clock_out_end = %s,

                                late_after_minutes = %s,
                                early_before_minutes = %s

                            WHERE id = %s
                            """,
                            (
                                company_name,
                                company_email,
                                company_phone,
                                company_address,
                                company_website,
                                footer_text,

                                application_status,
                                application_deadline,

                                admin_username,

                                attendance_enabled,

                                company_latitude,
                                company_longitude,

                                attendance_radius,

                                clock_in_start,
                                clock_in_end,

                                clock_out_start,
                                clock_out_end,

                                late_after_minutes,
                                early_before_minutes,

                                settings_id
                            )
                        )


                    # =================================================
                    # UPDATE ADMIN PASSWORD
                    # =================================================

                    if admin_password_hash:

                        cur.execute(
                            """
                            UPDATE company_settings

                            SET
                                admin_password_hash = %s

                            WHERE id = %s
                            """,
                            (
                                admin_password_hash,
                                settings_id
                            )
                        )


                # =================================================
                # COMMIT
                # =================================================

                conn.commit()


                # =================================================
                # SUCCESS
                # =================================================

                flash(
                    "Settings updated successfully.",
                    "success"
                )


                return redirect(
                    url_for(
                        "admin_settings"
                    )
                )


            # =================================================
            # GET CURRENT SETTINGS
            # =================================================

            cur.execute(
                """
                SELECT *
                FROM company_settings
                ORDER BY id ASC
                LIMIT 1
                """
            )

            settings = cur.fetchone()


    except Exception:

        conn.rollback()

        app.logger.exception(
            "Error updating company settings"
        )

        flash(
            "Unable to update company settings. "
            "Please try again.",
            "error"
        )

        settings = None


    finally:

        conn.close()


    # =========================================================
    # RENDER SETTINGS
    # =========================================================

    return render_template(
        "admin_settings.html",
        settings=settings
    )

@app.route("/admin/download-file/<path:filename>")
def admin_download_file(filename):

    if not admin_required():
        return redirect(
            url_for("admin_login")
        )

    filename = os.path.basename(
        filename
    )

    upload_folder = app.config[
        "UPLOAD_FOLDER"
    ]

    file_path = os.path.join(
        upload_folder,
        filename
    )

    app.logger.info(
        "DOWNLOAD REQUEST: %s",
        file_path
    )

    if not os.path.isfile(file_path):

        app.logger.warning(
            "DOCUMENT NOT FOUND: %s",
            file_path
        )

        flash(
            "The requested document could not be found.",
            "error"
        )

        return redirect(
            url_for("admin_applications")
        )

    return send_from_directory(
        upload_folder,
        filename,
        as_attachment=True
    )


@app.route("/admin/reports/export/pdf")
def export_admin_reports_pdf():

    # =========================================================
    # CHECK ADMIN LOGIN
    # =========================================================

    if not admin_required():
        return redirect(url_for("admin_login"))


    # =========================================================
    # IMPORT PDF COMPONENTS
    # =========================================================

    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        Image,
        PageBreak
    )


    # =========================================================
    # DATABASE
    # =========================================================

    conn = get_db()

    try:

        with conn.cursor() as cur:

            # =====================================================
            # COMPANY SETTINGS
            # =====================================================

            cur.execute(
                """
                SELECT
                    company_name,
                    company_email,
                    company_phone,
                    company_address,
                    company_website,
                    footer_text,
                    logo
                FROM company_settings
                ORDER BY id ASC
                LIMIT 1
                """
            )

            settings = cur.fetchone()


            # =====================================================
            # APPLICATION REPORT
            # =====================================================

            cur.execute(
                """
                SELECT
                    id,
                    application_number,
                    first_name,
                    middle_name,
                    last_name,
                    gender,
                    phone,
                    email,
                    state,
                    lga,
                    position_applied,
                    highest_qualification,
                    status,
                    created_at
                FROM applications
                ORDER BY created_at DESC, id DESC
                """
            )

            applications = cur.fetchall()


    finally:

        conn.close()


    # =========================================================
    # DEFAULT COMPANY INFORMATION
    # =========================================================

    if settings:

        company_name = (
            settings["company_name"]
            or "AV KING VET DRUG VENTURE"
        )

        company_email = (
            settings["company_email"]
            or ""
        )

        company_phone = (
            settings["company_phone"]
            or ""
        )

        company_address = (
            settings["company_address"]
            or ""
        )

        company_website = (
            settings["company_website"]
            or ""
        )

        footer_text = (
            settings["footer_text"]
            or ""
        )

        logo_filename = (
            settings["logo"]
            or ""
        )

    else:

        company_name = "AV KING VET DRUG VENTURE"
        company_email = ""
        company_phone = ""
        company_address = ""
        company_website = ""
        footer_text = ""
        logo_filename = ""


    # =========================================================
    # PDF BUFFER
    # =========================================================

    buffer = BytesIO()


    # =========================================================
    # PDF DOCUMENT
    # =========================================================

    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=15 * mm
    )


    # =========================================================
    # STYLES
    # =========================================================

    styles = getSampleStyleSheet()


    company_name_style = ParagraphStyle(
        "CompanyName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#111827"),
        spaceAfter=4
    )


    company_info_style = ParagraphStyle(
        "CompanyInfo",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#4b5563")
    )


    report_title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#111827"),
        spaceBefore=8,
        spaceAfter=4
    )


    date_style = ParagraphStyle(
        "DateStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#6b7280"),
        spaceAfter=12
    )


    normal_style = ParagraphStyle(
        "NormalReport",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=TA_LEFT
    )


    # =========================================================
    # STORY
    # =========================================================

    story = []


    # =========================================================
    # COMPANY LOGO
    # =========================================================

    if logo_filename:

        logo_path = os.path.join(
            app.root_path,
            "static",
            "uploads",
            logo_filename
        )


        if os.path.exists(logo_path):

            try:

                logo = Image(
                    logo_path,
                    width=25 * mm,
                    height=25 * mm,
                    kind="proportional"
                )

                logo.hAlign = "CENTER"

                story.append(logo)
                story.append(
                    Spacer(1, 4 * mm)
                )

            except Exception:

                app.logger.warning(
                    "Unable to load company logo for PDF.",
                    exc_info=True
                )


    # =========================================================
    # COMPANY NAME
    # =========================================================

    story.append(
        Paragraph(
            company_name,
            company_name_style
        )
    )


    # =========================================================
    # COMPANY ADDRESS
    # =========================================================

    if company_address:

        story.append(
            Paragraph(
                company_address,
                company_info_style
            )
        )


    # =========================================================
    # PHONE + EMAIL
    # CENTERED UNDER ADDRESS
    # =========================================================

    contact_parts = []


    if company_phone:

        contact_parts.append(
            f"Phone: {company_phone}"
        )


    if company_email:

        contact_parts.append(
            f"Email: {company_email}"
        )


    if contact_parts:

        story.append(
            Paragraph(
                " &nbsp;&nbsp; | &nbsp;&nbsp; ".join(
                    contact_parts
                ),
                company_info_style
            )
        )


    # =========================================================
    # WEBSITE
    # =========================================================

    if company_website:

        story.append(
            Paragraph(
                company_website,
                company_info_style
            )
        )


    story.append(
        Spacer(1, 5 * mm)
    )


    # =========================================================
    # DIVIDER
    # =========================================================

    divider = Table(
        [[""]],
        colWidths=[260 * mm],
        rowHeights=[1]
    )

    divider.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#d1d5db")
                )
            ]
        )
    )

    story.append(divider)


    # =========================================================
    # REPORT TITLE
    # =========================================================

    story.append(
        Paragraph(
            "APPLICANT RECRUITMENT REPORT",
            report_title_style
        )
    )


    # =========================================================
    # REPORT DATE
    # =========================================================

    from datetime import datetime

    generated_date = datetime.now().strftime(
        "%d %B %Y, %I:%M %p"
    )


    story.append(
        Paragraph(
            f"Generated on {generated_date}",
            date_style
        )
    )


    # =========================================================
    # SUMMARY
    # =========================================================

    total_applications = len(
        applications
    )

    pending_count = 0
    review_count = 0
    shortlisted_count = 0
    approved_count = 0
    rejected_count = 0


    for application in applications:

        status = (
            application["status"]
            or "Pending"
        )


        if status == "Pending":

            pending_count += 1

        elif status == "Under Review":

            review_count += 1

        elif status == "Shortlisted":

            shortlisted_count += 1

        elif status == "Approved":

            approved_count += 1

        elif status == "Rejected":

            rejected_count += 1


    summary_data = [
        [
            "TOTAL",
            "PENDING",
            "UNDER REVIEW",
            "SHORTLISTED",
            "APPROVED",
            "REJECTED"
        ],
        [
            str(total_applications),
            str(pending_count),
            str(review_count),
            str(shortlisted_count),
            str(approved_count),
            str(rejected_count)
        ]
    ]


    summary_table = Table(
        summary_data,
        colWidths=[
            42 * mm,
            42 * mm,
            42 * mm,
            42 * mm,
            42 * mm,
            42 * mm
        ]
    )


    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#111827")
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER"
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),

                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, 1),
                    colors.HexColor("#f9fafb")
                ),

                (
                    "FONTNAME",
                    (0, 1),
                    (-1, 1),
                    "Helvetica-Bold"
                ),

                (
                    "TEXTCOLOR",
                    (0, 1),
                    (-1, 1),
                    colors.HexColor("#111827")
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#d1d5db")
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                )
            ]
        )
    )


    story.append(
        summary_table
    )

    story.append(
        Spacer(1, 8 * mm)
    )


    # =========================================================
    # APPLICATION TABLE
    # =========================================================

    table_data = [
        [
            "S/N",
            "APPLICATION NO.",
            "APPLICANT NAME",
            "GENDER",
            "PHONE",
            "EMAIL",
            "STATE",
            "LGA",
            "POSITION",
            "QUALIFICATION",
            "STATUS",
            "DATE"
        ]
    ]


    for index, application in enumerate(
        applications,
        start=1
    ):

        first_name = (
            application["first_name"]
            or ""
        )

        middle_name = (
            application["middle_name"]
            or ""
        )

        last_name = (
            application["last_name"]
            or ""
        )


        full_name = " ".join(
            part
            for part in [
                first_name,
                middle_name,
                last_name
            ]
            if part
        )


        created_at = (
            application["created_at"]
        )


        if created_at:

            try:

                created_at = created_at.strftime(
                    "%d/%m/%Y"
                )

            except Exception:

                created_at = str(
                    created_at
                )[:10]

        else:

            created_at = "—"


        table_data.append(
            [
                str(index),

                application["application_number"]
                or "—",

                full_name or "—",

                application["gender"]
                or "—",

                application["phone"]
                or "—",

                application["email"]
                or "—",

                application["state"]
                or "—",

                application["lga"]
                or "—",

                application["position_applied"]
                or "—",

                application["highest_qualification"]
                or "—",

                application["status"]
                or "Pending",

                created_at
            ]
        )


    # =========================================================
    # CONVERT CELLS TO PARAGRAPHS
    # =========================================================

    formatted_table_data = []


    for row_index, row in enumerate(
        table_data
    ):

        formatted_row = []


        for value in row:

            if row_index == 0:

                formatted_row.append(
                    Paragraph(
                        str(value),
                        ParagraphStyle(
                            "HeaderCell",
                            parent=normal_style,
                            fontName="Helvetica-Bold",
                            fontSize=7,
                            leading=8,
                            alignment=TA_CENTER,
                            textColor=colors.white
                        )
                    )
                )

            else:

                formatted_row.append(
                    Paragraph(
                        str(value),
                        ParagraphStyle(
                            "BodyCell",
                            parent=normal_style,
                            fontSize=6.5,
                            leading=8,
                            alignment=TA_LEFT
                        )
                    )
                )


        formatted_table_data.append(
            formatted_row
        )


    # =========================================================
    # APPLICATION TABLE
    # =========================================================

    application_table = Table(
        formatted_table_data,
        repeatRows=1,
        colWidths=[
            9 * mm,    # S/N
            25 * mm,   # Application
            38 * mm,   # Name
            16 * mm,   # Gender
            25 * mm,   # Phone
            38 * mm,   # Email
            20 * mm,   # State
            20 * mm,   # LGA
            28 * mm,   # Position
            28 * mm,   # Qualification
            23 * mm,   # Status
            20 * mm    # Date
        ]
    )


    application_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#111827")
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor("#d1d5db")
                ),

                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#f9fafb")
                    ]
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ]
        )
    )


    story.append(
        application_table
    )


    # =========================================================
    # FOOTER
    # =========================================================

    if footer_text:

        story.append(
            Spacer(1, 7 * mm)
        )

        story.append(
            Paragraph(
                footer_text,
                company_info_style
            )
        )


    # =========================================================
    # BUILD PDF
    # =========================================================

    # =========================================================
    # BUILD PDF
    # =========================================================

    document.build(
        story
    )


    # =========================================================
    # PREPARE PDF FOR DOWNLOAD
    # =========================================================

    buffer.seek(0)


    # =========================================================
    # PDF FILE NAME
    # =========================================================

    filename = (
        "applicant_recruitment_report_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".pdf"
    )


    # =========================================================
    # RETURN PDF
    # =========================================================

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )


@app.route("/admin/reports/export/excel")
def export_admin_reports_excel():

    # =========================================================
    # CHECK ADMIN LOGIN
    # =========================================================

    if not admin_required():
        return redirect(url_for("admin_login"))


    conn = get_db()

    try:

        with conn.cursor() as cur:

            # =================================================
            # COMPANY SETTINGS
            # =================================================

            cur.execute("""
                SELECT
                    company_name,
                    company_address,
                    company_phone,
                    company_email,
                    logo
                FROM company_settings
                ORDER BY id ASC
                LIMIT 1
            """)

            settings = cur.fetchone()


            # =================================================
            # APPLICATIONS
            # =================================================

            cur.execute("""
                SELECT
                    application_number,
                    first_name,
                    middle_name,
                    last_name,
                    position_applied,
                    phone,
                    email,
                    gender,
                    state,
                    lga,
                    highest_qualification,
                    status,
                    submitted_at
                FROM applications
                ORDER BY submitted_at DESC NULLS LAST
            """)

            applications = cur.fetchall()

    finally:

        conn.close()


    # =========================================================
    # COMPANY INFORMATION
    # =========================================================

    company_name = (
        settings["company_name"]
        if settings and settings["company_name"]
        else "AV KING VET DRUG VENTURE"
    )

    company_address = (
        settings["company_address"]
        if settings and settings["company_address"]
        else ""
    )

    company_phone = (
        settings["company_phone"]
        if settings and settings["company_phone"]
        else ""
    )

    company_email = (
        settings["company_email"]
        if settings and settings["company_email"]
        else ""
    )

    company_logo = (
        settings["logo"]
        if settings and settings["logo"]
        else None
    )


    # =========================================================
    # CREATE WORKBOOK
    # =========================================================

    workbook = Workbook()

    worksheet = workbook.active

    worksheet.title = "Applicant Report"


    # =========================================================
    # PAGE SETTINGS
    # =========================================================

    worksheet.page_setup.orientation = "landscape"

    worksheet.page_setup.paperSize = (
        worksheet.PAPERSIZE_A4
    )

    worksheet.page_setup.fitToWidth = 1

    worksheet.page_setup.fitToHeight = 0

    worksheet.sheet_properties.pageSetUpPr.fitToPage = True

    worksheet.page_margins = PageMargins(

        left=0.25,
        right=0.25,
        top=0.5,
        bottom=0.5,
        header=0.2,
        footer=0.2
    )


    # =========================================================
    # COLORS
    # =========================================================

    dark = "111827"

    white = "FFFFFF"

    light_gray = "F3F4F6"

    border_gray = "D1D5DB"

    text_gray = "4B5563"

    green = "059669"

    orange = "EA580C"

    blue = "2563EB"

    red = "DC2626"


    # =========================================================
    # BORDER
    # =========================================================

    thin_border = Border(

        left=Side(
            style="thin",
            color=border_gray
        ),

        right=Side(
            style="thin",
            color=border_gray
        ),

        top=Side(
            style="thin",
            color=border_gray
        ),

        bottom=Side(
            style="thin",
            color=border_gray
        )
    )


    # =========================================================
    # LOGO
    # =========================================================

    current_row = 1

    if company_logo:

        try:

            logo_path = company_logo

            # ---------------------------------------------
            # Convert relative upload path to filesystem path
            # ---------------------------------------------

            if not os.path.isabs(logo_path):

                logo_path = os.path.join(
                    os.getcwd(),
                    logo_path.lstrip("/")
                )


            if os.path.exists(logo_path):

                logo = XLImage(logo_path)

                logo.width = 75

                logo.height = 75

                worksheet.add_image(
                    logo,
                    "A1"
                )

                current_row = 2

        except Exception:

            pass


    # =========================================================
    # COMPANY NAME
    # =========================================================

    worksheet.merge_cells(
        start_row=1,
        start_column=1,
        end_row=1,
        end_column=10
    )

    company_cell = worksheet.cell(
        row=1,
        column=1
    )

    company_cell.value = company_name

    company_cell.font = Font(
        name="Calibri",
        size=20,
        bold=True,
        color=dark
    )

    company_cell.alignment = Alignment(
        horizontal="center",
        vertical="center"
    )

    worksheet.row_dimensions[1].height = 30


    # =========================================================
    # COMPANY ADDRESS
    # =========================================================

    worksheet.merge_cells(
        start_row=2,
        start_column=1,
        end_row=2,
        end_column=10
    )

    address_cell = worksheet.cell(
        row=2,
        column=1
    )

    contact_text = company_address


    if company_phone:

        if contact_text:

            contact_text += "  |  "

        contact_text += (
            "Phone: "
            + str(company_phone)
        )


    if company_email:

        if contact_text:

            contact_text += "  |  "

        contact_text += (
            "Email: "
            + str(company_email)
        )


    address_cell.value = contact_text

    address_cell.font = Font(
        name="Calibri",
        size=10,
        color=text_gray
    )

    address_cell.alignment = Alignment(
        horizontal="center",
        vertical="center",
        wrap_text=True
    )

    worksheet.row_dimensions[2].height = 30


    # =========================================================
    # REPORT TITLE
    # =========================================================

    worksheet.merge_cells(
        start_row=4,
        start_column=1,
        end_row=4,
        end_column=10
    )

    title_cell = worksheet.cell(
        row=4,
        column=1
    )

    title_cell.value = (
        "APPLICANT RECRUITMENT REPORT"
    )

    title_cell.font = Font(
        name="Calibri",
        size=16,
        bold=True,
        color=dark
    )

    title_cell.alignment = Alignment(
        horizontal="center",
        vertical="center"
    )

    worksheet.row_dimensions[4].height = 26


    # =========================================================
    # REPORT SUBTITLE
    # =========================================================

    worksheet.merge_cells(
        start_row=5,
        start_column=1,
        end_row=5,
        end_column=10
    )

    subtitle_cell = worksheet.cell(
        row=5,
        column=1
    )

    subtitle_cell.value = (
        "Complete recruitment application summary"
    )

    subtitle_cell.font = Font(
        name="Calibri",
        size=10,
        italic=True,
        color=text_gray
    )

    subtitle_cell.alignment = Alignment(
        horizontal="center"
    )


    # =========================================================
    # GENERATED DATE
    # =========================================================

    worksheet.merge_cells(
        start_row=6,
        start_column=1,
        end_row=6,
        end_column=10
    )

    generated_cell = worksheet.cell(
        row=6,
        column=1
    )

    generated_cell.value = (
        "Generated: "
        + datetime.now().strftime(
            "%d %B %Y at %I:%M %p"
        )
    )

    generated_cell.font = Font(
        name="Calibri",
        size=9,
        color=text_gray
    )

    generated_cell.alignment = Alignment(
        horizontal="center"
    )


    # =========================================================
    # SUMMARY
    # =========================================================

    total = len(applications)

    pending = sum(
        1
        for row in applications
        if row["status"] == "Pending"
    )

    under_review = sum(
        1
        for row in applications
        if row["status"] == "Under Review"
    )

    shortlisted = sum(
        1
        for row in applications
        if row["status"] == "Shortlisted"
    )

    approved = sum(
        1
        for row in applications
        if row["status"] == "Approved"
    )

    rejected = sum(
        1
        for row in applications
        if row["status"] == "Rejected"
    )


    summary_row = 8


    summary_headers = [

        "TOTAL",
        "PENDING",
        "UNDER REVIEW",
        "SHORTLISTED",
        "APPROVED",
        "REJECTED"

    ]


    summary_values = [

        total,
        pending,
        under_review,
        shortlisted,
        approved,
        rejected

    ]


    summary_columns = [
        1,
        2,
        3,
        4,
        5,
        6
    ]


    for index, column in enumerate(
        summary_columns
    ):

        header = worksheet.cell(
            row=summary_row,
            column=column
        )

        header.value = summary_headers[index]

        header.font = Font(
            name="Calibri",
            size=9,
            bold=True,
            color=white
        )

        header.fill = PatternFill(
            fill_type="solid",
            fgColor=dark
        )

        header.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

        header.border = thin_border


        value = worksheet.cell(
            row=summary_row + 1,
            column=column
        )

        value.value = summary_values[index]

        value.font = Font(
            name="Calibri",
            size=14,
            bold=True,
            color=dark
        )

        value.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

        value.border = thin_border


    worksheet.row_dimensions[
        summary_row
    ].height = 22

    worksheet.row_dimensions[
        summary_row + 1
    ].height = 28


    # =========================================================
    # APPLICATION TABLE
    # =========================================================

    header_row = 11


    headers = [

        "Application Number",
        "Applicant Name",
        "Position Applied",
        "Phone",
        "Email",
        "Gender",
        "State",
        "LGA",
        "Highest Qualification",
        "Status"

    ]


    for column, header_text in enumerate(
        headers,
        start=1
    ):

        cell = worksheet.cell(
            row=header_row,
            column=column
        )

        cell.value = header_text

        cell.font = Font(
            name="Calibri",
            size=10,
            bold=True,
            color=white
        )

        cell.fill = PatternFill(
            fill_type="solid",
            fgColor=dark
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True
        )

        cell.border = thin_border


    worksheet.row_dimensions[
        header_row
    ].height = 32


    # =========================================================
    # APPLICATION DATA
    # =========================================================

    row_number = header_row + 1


    for application in applications:

        full_name = " ".join(

            part

            for part in [

                application["first_name"],
                application["middle_name"],
                application["last_name"]

            ]

            if part
        )


        data = [

            application["application_number"]
            or "—",

            full_name
            or "—",

            application["position_applied"]
            or "—",

            application["phone"]
            or "—",

            application["email"]
            or "—",

            application["gender"]
            or "—",

            application["state"]
            or "—",

            application["lga"]
            or "—",

            application["highest_qualification"]
            or "—",

            application["status"]
            or "Pending"

        ]


        for column, value in enumerate(
            data,
            start=1
        ):

            cell = worksheet.cell(
                row=row_number,
                column=column
            )

            cell.value = value

            cell.font = Font(
                name="Calibri",
                size=9,
                color=dark
            )

            cell.alignment = Alignment(
                vertical="center",
                wrap_text=True
            )

            cell.border = thin_border


            # ---------------------------------------------
            # Status formatting
            # ---------------------------------------------

            if column == 10:

                cell.alignment = Alignment(
                    horizontal="center",
                    vertical="center"
                )

                status = str(value).lower()


                if status == "approved":

                    cell.font = Font(
                        name="Calibri",
                        size=9,
                        bold=True,
                        color=green
                    )


                elif status == "shortlisted":

                    cell.font = Font(
                        name="Calibri",
                        size=9,
                        bold=True,
                        color=green
                    )


                elif status == "rejected":

                    cell.font = Font(
                        name="Calibri",
                        size=9,
                        bold=True,
                        color=red
                    )


                elif status == "under review":

                    cell.font = Font(
                        name="Calibri",
                        size=9,
                        bold=True,
                        color=blue
                    )


                elif status == "pending":

                    cell.font = Font(
                        name="Calibri",
                        size=9,
                        bold=True,
                        color=orange
                    )


        # Alternating row background

        if row_number % 2 == 0:

            for column in range(
                1,
                len(headers) + 1
            ):

                worksheet.cell(
                    row=row_number,
                    column=column
                ).fill = PatternFill(
                    fill_type="solid",
                    fgColor=light_gray
                )


        worksheet.row_dimensions[
            row_number
        ].height = 25


        row_number += 1


    # =========================================================
    # FILTER
    # =========================================================

    if row_number > header_row + 1:

        worksheet.auto_filter.ref = (

            f"A{header_row}:"
            f"J{row_number - 1}"

        )


    # =========================================================
    # FREEZE HEADER
    # =========================================================

    worksheet.freeze_panes = (
        f"A{header_row + 1}"
    )


    # =========================================================
    # COLUMN WIDTHS
    # =========================================================

    widths = {

        "A": 21,
        "B": 28,
        "C": 23,
        "D": 17,
        "E": 30,
        "F": 12,
        "G": 18,
        "H": 20,
        "I": 25,
        "J": 18

    }


    for column, width in widths.items():

        worksheet.column_dimensions[
            column
        ].width = width


    # =========================================================
    # PRINT AREA
    # =========================================================

    if row_number > header_row:

        worksheet.print_area = (
            f"A1:J{row_number - 1}"
        )


    # =========================================================
    # REPEAT HEADER WHEN PRINTING
    # =========================================================

    worksheet.print_title_rows = (
        f"1:{header_row}"
    )


    # =========================================================
    # HEADER / FOOTER
    # =========================================================

    worksheet.oddHeader.center.text = (
        "&B" + company_name
    )

    worksheet.oddFooter.center.text = (
        "Confidential Recruitment Document"
    )

    worksheet.oddFooter.right.text = (
        "Page &P of &N"
    )


    # =========================================================
    # ACTIVE CELL
    # =========================================================

    worksheet.sheet_view.selection[0].activeCell = (
        "A1"
    )

    worksheet.sheet_view.selection[0].sqref = (
        "A1"
    )


    # =========================================================
    # SAVE TO MEMORY
    # =========================================================

    output = io.BytesIO()

    workbook.save(output)

    output.seek(0)


    # =========================================================
    # DOWNLOAD
    # =========================================================

    return send_file(

        output,

        as_attachment=True,

        download_name=(
            "Applicant_Recruitment_Report.xlsx"
        ),

        mimetype=(
            "application/vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet"
        )
    )

@app.route("/admin/reports")
def admin_reports():

    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db()

    try:

        with conn.cursor() as cur:

            # Total applications
            cur.execute("""
                SELECT COUNT(*) AS total
                FROM applications
            """)
            total = cur.fetchone()["total"]


            # Pending
            cur.execute("""
                SELECT COUNT(*) AS total
                FROM applications
                WHERE status = 'Pending'
            """)
            pending = cur.fetchone()["total"]


            # Under Review
            cur.execute("""
                SELECT COUNT(*) AS total
                FROM applications
                WHERE status = 'Under Review'
            """)
            under_review = cur.fetchone()["total"]


            # Shortlisted
            cur.execute("""
                SELECT COUNT(*) AS total
                FROM applications
                WHERE status = 'Shortlisted'
            """)
            shortlisted = cur.fetchone()["total"]


            # Approved
            cur.execute("""
                SELECT COUNT(*) AS total
                FROM applications
                WHERE status = 'Approved'
            """)
            approved = cur.fetchone()["total"]


            # Rejected
            cur.execute("""
                SELECT COUNT(*) AS total
                FROM applications
                WHERE status = 'Rejected'
            """)
            rejected = cur.fetchone()["total"]


            # Applications by position
            cur.execute("""
                SELECT
                    position_applied,
                    COUNT(*) AS total
                FROM applications
                GROUP BY position_applied
                ORDER BY total DESC
            """)

            position_report = cur.fetchall()


            # Applications by gender
            cur.execute("""
                SELECT
                    gender,
                    COUNT(*) AS total
                FROM applications
                GROUP BY gender
                ORDER BY total DESC
            """)

            gender_report = cur.fetchall()


    finally:

        conn.close()


    return render_template(
        "admin_reports.html",

        total=total,
        pending=pending,
        under_review=under_review,
        shortlisted=shortlisted,
        approved=approved,
        rejected=rejected,

        position_report=position_report,
        gender_report=gender_report
        )


def format_date(date_value):

    if not date_value:
        return "Not Available"

    try:

        if isinstance(date_value, datetime):
            return date_value.strftime("%d %B %Y")

        if hasattr(date_value, "strftime"):
            return date_value.strftime("%d %B %Y")

        if isinstance(date_value, str):

            try:
                parsed_date = datetime.fromisoformat(
                    date_value.replace("Z", "+00:00")
                )

                return parsed_date.strftime(
                    "%d %B %Y"
                )

            except ValueError:

                try:
                    parsed_date = datetime.strptime(
                        date_value,
                        "%Y-%m-%d"
                    )

                    return parsed_date.strftime(
                        "%d %B %Y"
                    )

                except ValueError:
                    return date_value

        return str(date_value)

    except Exception:

        app.logger.exception(
            "Error formatting application date"
        )

        return str(date_value)
        
@app.route(
    "/admin/applications/<int:application_id>/biodata/pdf"
)
def download_applicant_biodata(application_id):

    # =========================================================
    # ADMIN LOGIN
    # =========================================================

    if not admin_required():
        return redirect(
            url_for("admin_login")
        )


    # =========================================================
    # REPORTLAB
    # =========================================================

    from reportlab.lib import colors

    from reportlab.lib.enums import (
        TA_CENTER,
        TA_LEFT
    )

    from reportlab.lib.pagesizes import A4

    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle
    )

    from reportlab.lib.units import mm

    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        Image,
        HRFlowable
    )


    # =========================================================
    # DATABASE
    # =========================================================

    conn = get_db()

    try:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # GET APPLICANT
            # -------------------------------------------------

            cur.execute(
                """
                SELECT *
                FROM applications
                WHERE id = %s
                LIMIT 1
                """,
                (application_id,)
            )

            applicant = cur.fetchone()


            # -------------------------------------------------
            # GET COMPANY SETTINGS
            # -------------------------------------------------

            cur.execute(
                """
                SELECT
                    company_name,
                    company_email,
                    company_phone,
                    company_address,
                    company_website,
                    footer_text,
                    logo
                FROM company_settings
                ORDER BY id ASC
                LIMIT 1
                """
            )

            settings = cur.fetchone()


    except Exception:

        app.logger.exception(
            "Error loading applicant biodata"
        )

        flash(
            "Unable to load applicant biodata.",
            "error"
        )

        return redirect(
            url_for("admin_applications")
        )

    finally:

        conn.close()


    # =========================================================
    # APPLICANT NOT FOUND
    # =========================================================

    if not applicant:

        flash(
            "Applicant not found.",
            "error"
        )

        return redirect(
            url_for("admin_applications")
        )


    # =========================================================
    # HELPER
    # =========================================================

    def value(
        field,
        default="—"
    ):

        try:

            result = applicant[field]

        except (
            KeyError,
            TypeError
        ):

            result = None


        if result is None:

            return default


        result = str(
            result
        ).strip()


        if not result:

            return default


        return result


    # =========================================================
    # COMPANY INFORMATION
    # =========================================================

    if settings:

        company_name = (
            settings["company_name"]
            or "AV KING VET DRUG VENTURE"
        )

        company_email = (
            settings["company_email"]
            or ""
        )

        company_phone = (
            settings["company_phone"]
            or ""
        )

        company_address = (
            settings["company_address"]
            or ""
        )

        company_website = (
            settings["company_website"]
            or ""
        )

        footer_text = (
            settings["footer_text"]
            or ""
        )

        logo_value = (
            settings["logo"]
            or ""
        )

    else:

        company_name = (
            "AV KING VET DRUG VENTURE"
        )

        company_email = ""
        company_phone = ""
        company_address = ""
        company_website = ""
        footer_text = ""
        logo_value = ""


    # =========================================================
    # COMPANY LOGO
    # =========================================================

    logo_path = None


    if logo_value:

        logo_value = str(
            logo_value
        ).strip()


        # -----------------------------------------------
        # /static/uploads/logo.png
        # -----------------------------------------------

        if logo_value.startswith(
            "/static/"
        ):

            logo_path = os.path.join(
                app.root_path,
                logo_value.lstrip("/")
            )


        # -----------------------------------------------
        # static/uploads/logo.png
        # -----------------------------------------------

        elif logo_value.startswith(
            "static/"
        ):

            logo_path = os.path.join(
                app.root_path,
                logo_value
            )


        # -----------------------------------------------
        # logo.png
        # -----------------------------------------------

        else:

            logo_path = os.path.join(
                app.root_path,
                "static",
                "uploads",
                os.path.basename(
                    logo_value
                )
            )


        logo_path = os.path.abspath(
            logo_path
        )


        if not os.path.isfile(
            logo_path
        ):

            app.logger.warning(
                "Company logo not found: %s",
                logo_path
            )

            logo_path = None


    # =========================================================
    # APPLICANT PASSPORT
    # =========================================================

    passport_path = None


    passport_filename = (
        applicant["passport_filename"]
        or ""
    )


    if passport_filename:

        passport_filename = str(
            passport_filename
        ).strip()


        # -----------------------------------------------
        # /static/uploads/passport.jpg
        # -----------------------------------------------

        if passport_filename.startswith(
            "/static/"
        ):

            passport_path = os.path.join(
                app.root_path,
                passport_filename.lstrip("/")
            )


        # -----------------------------------------------
        # static/uploads/passport.jpg
        # -----------------------------------------------

        elif passport_filename.startswith(
            "static/"
        ):

            passport_path = os.path.join(
                app.root_path,
                passport_filename
            )


        # -----------------------------------------------
        # filename only
        # -----------------------------------------------

        else:

            passport_path = os.path.join(
                app.root_path,
                "static",
                "uploads",
                os.path.basename(
                    passport_filename
                )
            )


        passport_path = os.path.abspath(
            passport_path
        )


        if not os.path.isfile(
            passport_path
        ):

            app.logger.warning(
                "Applicant passport not found: %s",
                passport_path
            )

            passport_path = None


    # =========================================================
    # PDF BUFFER
    # =========================================================

    buffer = BytesIO()


    # =========================================================
    # PDF DOCUMENT
    # =========================================================

    document = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        rightMargin=15 * mm,

        leftMargin=15 * mm,

        topMargin=12 * mm,

        bottomMargin=18 * mm
    )


    # =========================================================
    # STYLES
    # =========================================================

    styles = getSampleStyleSheet()


    company_style = ParagraphStyle(
        "CompanyStyle",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=15,

        leading=19,

        alignment=TA_CENTER,

        textColor=colors.HexColor(
            "#111827"
        )
    )


    company_info_style = ParagraphStyle(
        "CompanyInfo",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=8,

        leading=11,

        alignment=TA_CENTER,

        textColor=colors.HexColor(
            "#4b5563"
        )
    )


    title_style = ParagraphStyle(
        "TitleStyle",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=15,

        leading=19,

        alignment=TA_CENTER,

        textColor=colors.HexColor(
            "#111827"
        )
    )


    section_style = ParagraphStyle(
        "SectionStyle",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=9,

        leading=11,

        textColor=colors.white
    )


    label_style = ParagraphStyle(
        "LabelStyle",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=7.5,

        leading=10,

        textColor=colors.HexColor(
            "#374151"
        )
    )


    data_style = ParagraphStyle(
        "DataStyle",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=8.5,

        leading=11,

        textColor=colors.HexColor(
            "#111827"
        )
    )


    small_style = ParagraphStyle(
        "SmallStyle",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=7.5,

        leading=10,

        textColor=colors.HexColor(
            "#6b7280"
        )
    )


    # =========================================================
    # STORY
    # =========================================================

    story = []


    # =========================================================
    # COMPANY LOGO
    # =========================================================

    if logo_path:

        try:

            header_logo = Image(

                logo_path,

                width=30 * mm,

                height=30 * mm,

                kind="proportional"
            )

        except Exception:

            header_logo = Paragraph(
                "AV",
                company_style
            )

    else:

        header_logo = Paragraph(
            "AV",
            company_style
        )


    # =========================================================
    # APPLICANT PASSPORT
    # =========================================================

    if passport_path:

        try:

            header_passport = Image(

                passport_path,

                width=30 * mm,

                height=38 * mm,

                kind="proportional"
            )

        except Exception:

            header_passport = Paragraph(
                "PASSPORT<br/>PHOTO",
                small_style
            )

    else:

        header_passport = Paragraph(
            "PASSPORT<br/>PHOTO",
            small_style
        )


    # =========================================================
    # COMPANY INFORMATION
    # =========================================================

    company_details = []


    company_details.append(
        Paragraph(
            str(company_name),
            company_style
        )
    )


    if company_address:

        company_details.append(
            Paragraph(
                str(company_address),
                company_info_style
            )
        )


    if company_phone:

        company_details.append(
            Paragraph(
                f"Phone: {company_phone}",
                company_info_style
            )
        )


    if company_email:

        company_details.append(
            Paragraph(
                f"Email: {company_email}",
                company_info_style
            )
        )


    if company_website:

        company_details.append(
            Paragraph(
                str(company_website),
                company_info_style
            )
        )


    # =========================================================
    # HEADER TABLE
    # =========================================================

    header_table = Table(

        [
            [
                header_logo,
                company_details,
                header_passport
            ]
        ],

        colWidths=[
            40 * mm,
            110 * mm,
            35 * mm
        ]
    )


    header_table.setStyle(
        TableStyle(
            [

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (0, 0),
                    "LEFT"
                ),

                (
                    "ALIGN",
                    (1, 0),
                    (1, 0),
                    "CENTER"
                ),

                (
                    "ALIGN",
                    (2, 0),
                    (2, 0),
                    "RIGHT"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    2
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    2
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2
                )
            ]
        )
    )


    story.append(
        header_table
    )


    story.append(
        Spacer(1, 5 * mm)
    )


    story.append(
        HRFlowable(
            width="100%",

            thickness=1,

            color=colors.HexColor(
                "#d1d5db"
            )
        )
    )


    story.append(
        Spacer(1, 4 * mm)
    )


    # =========================================================
    # TITLE
    # =========================================================

    story.append(
        Paragraph(
            "APPLICANT BIODATA",
            title_style
        )
    )


    story.append(
        Spacer(1, 2 * mm)
    )


    story.append(
        Paragraph(
            (
                "Application No.: "
                f"<b>{value('application_number')}</b>"
            ),

            company_info_style
        )
    )


    story.append(
        Spacer(1, 5 * mm)
    )


    # =========================================================
    # SECTION HEADER
    # =========================================================

    def section_header(title):

        table = Table(

            [
                [
                    Paragraph(
                        title,
                        section_style
                    )
                ]
            ],

            colWidths=[
                180 * mm
            ]
        )


        table.setStyle(
            TableStyle(
                [

                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor(
                            "#111827"
                        )
                    ),

                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        7
                    ),

                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7
                    ),

                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    )
                ]
            )
        )


        story.append(
            table
        )

        story.append(
            Spacer(1, 2 * mm)
        )


    # =========================================================
    # INFORMATION TABLE
    # =========================================================

    def information_table(rows):

        table_data = []


        for label, data in rows:

            table_data.append(
                [
                    Paragraph(
                        str(label),
                        label_style
                    ),

                    Paragraph(
                        str(data),
                        data_style
                    )
                ]
            )


        table = Table(

            table_data,

            colWidths=[
                48 * mm,
                132 * mm
            ]
        )


        table.setStyle(
            TableStyle(
                [

                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor(
                            "#d1d5db"
                        )
                    ),

                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.HexColor(
                            "#f3f4f6"
                        )
                    ),

                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP"
                    ),

                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),

                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),

                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    )
                ]
            )
        )


        story.append(
            table
        )

        story.append(
            Spacer(1, 5 * mm)
        )


    # =========================================================
    # APPLICATION INFORMATION
    # =========================================================
    # =========================================================
    # APPLICATION INFORMATION
    # =========================================================
    section_header(
        "APPLICATION INFORMATION"
    )
    
    information_table(
        [
            (
                "Application Number",
                value("application_number")
            ),
            (
                "Position Applied For",
                value("position_applied")
            ),
            (
                "Application Date",
                format_date(
                    value("created_at")
                )
            ),
            (
                "Application Status",
                value(
                    "status",
                    "Pending"
                )
            )
        ]
    )
    
    # =========================================================
    # PERSONAL INFORMATION
    # =========================================================

    section_header(
        "PERSONAL INFORMATION"
    )

    information_table(
        [
            (
                "Full Name",
                " ".join(
                    str(part).strip()
                    for part in [
                        applicant["first_name"] or "",
                        applicant["middle_name"] or "",
                        applicant["last_name"] or ""
                    ]
                    if str(part).strip()
                )
            ),
            (
                "Gender",
                value("gender")
            ),
            (
                "Date of Birth",
                value("date_of_birth")
            ),
            (
                "Phone Number",
                value("phone")
            ),
            (
                "Email Address",
                value("email")
            ),
            (
                "Residential Address",
                value("address")
            ),
            (
                "State",
                value("state")
            ),
            (
                "Local Government Area",
                value("lga")
            )
        ]
    )
    # =========================================================
    # EDUCATION & QUALIFICATION
    # =========================================================

    section_header(
        "EDUCATION & QUALIFICATION"
    )

    information_table(
        [
            (
                "Highest Qualification",
                value("highest_qualification")
            ),

            (
                "Course of Study",
                value("course_of_study")
            ),

            (
                "Institution",
                value("institution")
            ),

            (
                "Graduation Year",
                value("graduation_year")
            )
        ]
    )


    # =========================================================
    # WORK EXPERIENCE
    # =========================================================

    section_header(
        "WORK EXPERIENCE"
    )

    information_table(
        [
            (
                "Previous Employer",
                value("previous_employer")
            ),

            (
                "Previous Position",
                value("previous_position")
            ),

            (
                "Work Experience",
                value("work_experience")
            )
        ]
    )


    # =========================================================
    # APPLICATION STATEMENT
    # =========================================================

    section_header(
        "APPLICATION STATEMENT"
    )

    information_table(
        [
            (
                "Reason for Applying",
                value("reason_for_applying")
            ),

            (
                "Additional Information",
                value("additional_information")
            )
        ]
    )


    # =========================================================
    # SUBMITTED DOCUMENTS
    # =========================================================

    section_header(
        "SUBMITTED DOCUMENTS"
    )

    information_table(
        [
            (
                "Passport Photograph",
                value("passport_filename")
            ),

            (
                "Curriculum Vitae",
                value("cv_filename")
            ),

            (
                "Qualification Document",
                value("qualification_filename")
            )
        ]
    )


    # =========================================================
    # DECLARATION
    # =========================================================

    section_header(
        "APPLICANT DECLARATION"
    )

    declaration_text = (
        "I confirm that the information provided in this "
        "application is true and correct to the best of my "
        "knowledge. I understand that any false or misleading "
        "information may affect the consideration of my application."
    )

    declaration_table = Table(
        [
            [
                Paragraph(
                    declaration_text,
                    data_style
                )
            ]
        ],
        colWidths=[
            180 * mm
        ]
    )

    declaration_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#d1d5db")
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#f9fafb")
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                )
            ]
        )
    )

    story.append(
        declaration_table
    )

    story.append(
        Spacer(1, 12 * mm)
    )


    # =========================================================
    # ADMIN USE
    # =========================================================

    section_header(
        "FOR OFFICIAL USE ONLY"
    )

    official_use_table = Table(
        [
            [
                Paragraph(
                    "<b>Application Reviewed By:</b>",
                    label_style
                ),
                Paragraph(
                    "________________________________________",
                    data_style
                )
            ],

            [
                Paragraph(
                    "<b>Review Date:</b>",
                    label_style
                ),
                Paragraph(
                    "________________________________________",
                    data_style
                )
            ],

            [
                Paragraph(
                    "<b>Decision:</b>",
                    label_style
                ),
                Paragraph(
                    "☐ Approved     ☐ Shortlisted     "
                    "☐ Rejected     ☐ Pending",
                    data_style
                )
            ],

            [
                Paragraph(
                    "<b>Comments:</b>",
                    label_style
                ),
                Paragraph(
                    "________________________________________"
                    "<br/>"
                    "________________________________________"
                    "<br/>"
                    "________________________________________",
                    data_style
                )
            ]
        ],
        colWidths=[
            48 * mm,
            132 * mm
        ]
    )

    official_use_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#d1d5db")
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#f3f4f6")
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                )
            ]
        )
    )

    story.append(
        official_use_table
    )

    story.append(
        Spacer(1, 10 * mm)
    )


    # =========================================================
    # FOOTER
    # =========================================================

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.7,
            color=colors.HexColor("#d1d5db")
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )


    if footer_text:

        footer_content = footer_text

    else:

        footer_content = (
            f"{company_name} — "
            "Applicant Recruitment Portal"
        )


    story.append(
        Paragraph(
            footer_content,
            company_info_style
        )
    )


    # =========================================================
    # GENERATED INFORMATION
    # =========================================================

    story.append(
        Spacer(1, 2 * mm)
    )

    story.append(
        Paragraph(
            "This document was generated electronically "
            "from the recruitment portal.",
            small_style
        )
    )


    # =========================================================
    # BUILD PDF
    # =========================================================

    document.build(
        story
    )


    # =========================================================
    # PREPARE PDF
    # =========================================================

    buffer.seek(0)


    # =========================================================
    # SAFE APPLICATION NUMBER
    # =========================================================

    safe_application_number = value(
        "application_number",
        f"APP-{application_id}"
    )


    safe_application_number = (
        safe_application_number
        .replace("/", "-")
        .replace("\\", "-")
        .replace(" ", "_")
    )


    # =========================================================
    # FILE NAME
    # =========================================================

    filename = (
        f"{safe_application_number}_"
        f"Applicant_Biodata.pdf"
    )


    # =========================================================
    # RETURN PDF
    # =========================================================

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
)

# ============================================================
# APPLICANT ATTENDANCE
# Applicant clocks in/out from their own portal
# Location must be within the company's configured radius
# ============================================================

from datetime import datetime, date
import math


# ============================================================
# HELPER: DISTANCE BETWEEN TWO GPS COORDINATES
# Returns distance in metres
# ============================================================

def calculate_distance_meters(
    lat1,
    lon1,
    lat2,
    lon2
):

    earth_radius = 6371000

    lat1_rad = math.radians(float(lat1))
    lat2_rad = math.radians(float(lat2))

    delta_lat = math.radians(
        float(lat2) - float(lat1)
    )

    delta_lon = math.radians(
        float(lon2) - float(lon1)
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1_rad)
        *
        math.cos(lat2_rad)
        *
        math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


# ============================================================
# HELPER: GET TODAY'S ATTENDANCE
# ============================================================

def get_today_attendance(
    worker_id
):

    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *
                FROM attendance

                WHERE worker_id = %s
                AND attendance_date = CURRENT_DATE

                LIMIT 1
                """,
                (worker_id,)
            )

            return cur.fetchone()

    finally:

        conn.close()


# ============================================================
# APPLICANT ATTENDANCE PAGE
# ============================================================

@app.route("/applicant/attendance")
def applicant_attendance():

    applicant_id = session.get(
        "applicant_id"
    )

    if not applicant_id:

        return redirect(
            url_for("applicant_login")
        )

    conn = get_db()

    try:

        with conn.cursor() as cur:

            # ------------------------------------------------
            # GET APPLICANT
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    id,
                    application_number,
                    first_name,
                    middle_name,
                    last_name,
                    position_applied,
                    status,
                    portal_active

                FROM applications

                WHERE id = %s

                LIMIT 1
                """,
                (applicant_id,)
            )

            applicant = cur.fetchone()


            if not applicant:

                session.clear()

                flash(
                    "Applicant account not found.",
                    "error"
                )

                return redirect(
                    url_for("applicant_login")
                )


            # ------------------------------------------------
            # ONLY APPROVED APPLICANTS CAN ATTEND
            # ------------------------------------------------

            if applicant["status"] != "Approved":

                flash(
                    "Attendance is available only to approved applicants.",
                    "error"
                )

                return redirect(
                    url_for("applicant_portal")
                )


            # ------------------------------------------------
            # CHECK PORTAL
            # ------------------------------------------------

            if not applicant["portal_active"]:

                flash(
                    "Your applicant portal has been disabled.",
                    "error"
                )

                return redirect(
                    url_for("applicant_login")
                )


            # ------------------------------------------------
            # GET COMPANY SETTINGS
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    attendance_enabled,
                    company_latitude,
                    company_longitude,
                    attendance_radius,
                    clock_in_start,
                    clock_out_end

                FROM company_settings

                ORDER BY id ASC

                LIMIT 1
                """
            )

            settings = cur.fetchone()


            # ------------------------------------------------
            # GET TODAY'S ATTENDANCE
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    id,
                    attendance_date,
                    clock_in,
                    clock_out,
                    total_hours,
                    status,
                    clock_in_location_verified,
                    clock_out_location_verified

                FROM attendance

                WHERE worker_id = %s
                AND attendance_date = CURRENT_DATE

                LIMIT 1
                """,
                (applicant_id,)
            )

            today_attendance = cur.fetchone()


            # ------------------------------------------------
            # RECENT ATTENDANCE
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    id,
                    attendance_date,
                    clock_in,
                    clock_out,
                    total_hours,
                    status

                FROM attendance

                WHERE worker_id = %s

                ORDER BY attendance_date DESC

                LIMIT 30
                """,
                (applicant_id,)
            )

            attendance_history = cur.fetchall()


    finally:

        conn.close()


    return render_template(
        "applicant_attendance.html",

        applicant=applicant,

        settings=settings,

        today_attendance=today_attendance,

        attendance_history=attendance_history
    )


# ============================================================
# APPLICANT CLOCK IN
# ============================================================

@app.route(
    "/applicant/attendance/clock-in",
    methods=["POST"]
)
def applicant_clock_in():

    applicant_id = session.get(
        "applicant_id"
    )

    if not applicant_id:

        return redirect(
            url_for("applicant_login")
        )


    # --------------------------------------------------------
    # GET GPS LOCATION FROM APPLICANT DEVICE
    # --------------------------------------------------------

    try:

        latitude = float(
            request.form.get(
                "latitude",
                ""
            )
        )

        longitude = float(
            request.form.get(
                "longitude",
                ""
            )
        )

    except (
        ValueError,
        TypeError
    ):

        flash(
            "Unable to determine your location. Please allow location access and try again.",
            "error"
        )

        return redirect(
            url_for("applicant_attendance")
        )


    conn = get_db()

    try:

        with conn.cursor() as cur:

            # ------------------------------------------------
            # GET APPLICANT
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    id,
                    status,
                    portal_active

                FROM applications

                WHERE id = %s

                LIMIT 1
                """,
                (applicant_id,)
            )

            applicant = cur.fetchone()


            if not applicant:

                flash(
                    "Applicant account not found.",
                    "error"
                )

                return redirect(
                    url_for("applicant_login")
                )


            # ------------------------------------------------
            # APPROVAL CHECK
            # ------------------------------------------------

            if applicant["status"] != "Approved":

                flash(
                    "Only approved applicants can clock attendance.",
                    "error"
                )

                return redirect(
                    url_for("applicant_attendance")
                )


            # ------------------------------------------------
            # PORTAL CHECK
            # ------------------------------------------------

            if not applicant["portal_active"]:

                flash(
                    "Your applicant portal has been disabled.",
                    "error"
                )

                return redirect(
                    url_for("applicant_login")
                )


            # ------------------------------------------------
            # COMPANY SETTINGS
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    attendance_enabled,
                    company_latitude,
                    company_longitude,
                    attendance_radius,
                    clock_in_start,
                    clock_out_end

                FROM company_settings

                ORDER BY id ASC

                LIMIT 1
                """
            )

            settings = cur.fetchone()


            if not settings:

                flash(
                    "Attendance settings have not been configured by the administrator.",
                    "error"
                )

                return redirect(
                    url_for("applicant_attendance")
                )


            # ------------------------------------------------
            # ATTENDANCE ENABLED
            # ------------------------------------------------

            if not settings["attendance_enabled"]:

                flash(
                    "Attendance is currently disabled by the administrator.",
                    "error"
                )

                return redirect(
                    url_for("applicant_attendance")
                )


            # ------------------------------------------------
            # COMPANY GPS MUST EXIST
            # ------------------------------------------------

            if (
                settings["company_latitude"] is None
                or
                settings["company_longitude"] is None
            ):

                flash(
                    "Company attendance location has not been configured.",
                    "error"
                )

                return redirect(
                    url_for("applicant_attendance")
                )


            # ------------------------------------------------
            # CHECK TODAY'S ATTENDANCE
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    id,
                    clock_in,
                    clock_out

                FROM attendance

                WHERE worker_id = %s
                AND attendance_date = CURRENT_DATE

                LIMIT 1
                """,
                (applicant_id,)
            )

            existing = cur.fetchone()


            if existing and existing["clock_in"]:

                flash(
                    "You have already clocked in today.",
                    "error"
                )

                return redirect(
                    url_for("applicant_attendance")
                )


            # ------------------------------------------------
            # CALCULATE DISTANCE
            # ------------------------------------------------

            distance = calculate_distance_meters(
                latitude,
                longitude,
                settings["company_latitude"],
                settings["company_longitude"]
            )


            radius = int(
                settings["attendance_radius"]
                or 200
            )


            # ------------------------------------------------
            # LOCATION VERIFICATION
            # ------------------------------------------------

            if distance > radius:

                flash(
                    f"You are outside the company attendance area. "
                    f"Distance: {round(distance)} metres. "
                    f"Allowed radius: {radius} metres.",
                    "error"
                )

                return redirect(
                    url_for("applicant_attendance")
                )


            # ------------------------------------------------
            # SAVE CLOCK IN
            # ------------------------------------------------

            if existing:

                cur.execute(
                    """
                    UPDATE attendance

                    SET
                        clock_in = CURRENT_TIMESTAMP,
                        clock_in_latitude = %s,
                        clock_in_longitude = %s,
                        clock_in_location_verified = TRUE,
                        status = 'Present',
                        updated_at = CURRENT_TIMESTAMP

                    WHERE id = %s
                    """,
                    (
                        latitude,
                        longitude,
                        existing["id"]
                    )
                )

            else:

                cur.execute(
                    """
                    INSERT INTO attendance
                    (
                        worker_id,
                        attendance_date,
                        clock_in,
                        clock_in_latitude,
                        clock_in_longitude,
                        clock_in_location_verified,
                        status
                    )

                    VALUES
                    (
                        %s,
                        CURRENT_DATE,
                        CURRENT_TIMESTAMP,
                        %s,
                        %s,
                        TRUE,
                        'Present'
                    )
                    """,
                    (
                        applicant_id,
                        latitude,
                        longitude
                    )
                )


        conn.commit()


        flash(
            "Clock-in recorded successfully.",
            "success"
        )


    except Exception:

        conn.rollback()

        app.logger.exception(
            "Applicant clock-in error"
        )

        flash(
            "Unable to record clock-in. Please try again.",
            "error"
        )


    finally:

        conn.close()


    return redirect(
        url_for("applicant_attendance")
    )


# ============================================================
# APPLICANT CLOCK OUT
# ============================================================

@app.route(
    "/applicant/attendance/clock-out",
    methods=["POST"]
)
def applicant_clock_out():

    applicant_id = session.get(
        "applicant_id"
    )

    if not applicant_id:

        return redirect(
            url_for("applicant_login")
        )


    # --------------------------------------------------------
    # GET GPS LOCATION
    # --------------------------------------------------------

    try:

        latitude = float(
            request.form.get(
                "latitude",
                ""
            )
        )

        longitude = float(
            request.form.get(
                "longitude",
                ""
            )
        )

    except (
        ValueError,
        TypeError
    ):

        flash(
            "Unable to determine your location. Please allow location access and try again.",
            "error"
        )

        return redirect(
            url_for("applicant_attendance")
        )


    conn = get_db()

    try:

        with conn.cursor() as cur:

            # ------------------------------------------------
            # GET SETTINGS
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    attendance_enabled,
                    company_latitude,
                    company_longitude,
                    attendance_radius,
                    clock_in_start,
                    clock_out_end

                FROM company_settings

                ORDER BY id ASC

                LIMIT 1
                """
            )

            settings = cur.fetchone()


            if not settings:

                flash(
                    "Attendance settings have not been configured.",
                    "error"
                )

                return redirect(
                    url_for("applicant_attendance")
                )


            if not settings["attendance_enabled"]:

                flash(
                    "Attendance is currently disabled.",
                    "error"
                )

                return redirect(
                    url_for("applicant_attendance")
                )


            # ------------------------------------------------
            # GET TODAY'S RECORD
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    id,
                    clock_in,
                    clock_out

                FROM attendance

                WHERE worker_id = %s
                AND attendance_date = CURRENT_DATE

                LIMIT 1
                """,
                (applicant_id,)
            )

            attendance = cur.fetchone()


            if not attendance:

                flash(
                    "You have not clocked in today.",
                    "error"
                )

                return redirect(
                    url_for("applicant_attendance")
                )


            if not attendance["clock_in"]:

                flash(
                    "You must clock in before clocking out.",
                    "error"
                )

                return redirect(
                    url_for("applicant_attendance")
                )


            if attendance["clock_out"]:

                flash(
                    "You have already clocked out today.",
                    "error"
                )

                return redirect(
                    url_for("applicant_attendance")
                )


            # ------------------------------------------------
            # COMPANY LOCATION MUST EXIST
            # ------------------------------------------------

            if (
                settings["company_latitude"] is None
                or
                settings["company_longitude"] is None
            ):

                flash(
                    "Company attendance location has not been configured.",
                    "error"
                )

                return redirect(
                    url_for("applicant_attendance")
                )


            # ------------------------------------------------
            # VERIFY LOCATION
            # ------------------------------------------------

            distance = calculate_distance_meters(
                latitude,
                longitude,
                settings["company_latitude"],
                settings["company_longitude"]
            )


            radius = int(
                settings["attendance_radius"]
                or 200
            )


            if distance > radius:

                flash(
                    f"You are outside the company attendance area. "
                    f"Distance: {round(distance)} metres. "
                    f"Allowed radius: {radius} metres.",
                    "error"
                )

                return redirect(
                    url_for("applicant_attendance")
                )


            # ------------------------------------------------
            # CALCULATE TOTAL HOURS
            # ------------------------------------------------

            clock_in_time = (
                attendance["clock_in"]
            )

            clock_out_time = datetime.now(
                clock_in_time.tzinfo
            ) if clock_in_time.tzinfo else datetime.now()


            total_seconds = (
                clock_out_time
                - clock_in_time
            ).total_seconds()


            total_hours = round(
                max(total_seconds, 0) / 3600,
                2
            )


            # ------------------------------------------------
            # SAVE CLOCK OUT
            # ------------------------------------------------

            cur.execute(
                """
                UPDATE attendance

                SET
                    clock_out = CURRENT_TIMESTAMP,

                    clock_out_latitude = %s,

                    clock_out_longitude = %s,

                    clock_out_location_verified = TRUE,

                    total_hours = %s,

                    status = 'Present',

                    updated_at = CURRENT_TIMESTAMP

                WHERE id = %s
                """,
                (
                    latitude,
                    longitude,
                    total_hours,
                    attendance["id"]
                )
            )


        conn.commit()


        flash(
            f"Clock-out recorded successfully. "
            f"Total hours: {total_hours:.2f}.",
            "success"
        )


    except Exception:

        conn.rollback()

        app.logger.exception(
            "Applicant clock-out error"
        )

        flash(
            "Unable to record clock-out. Please try again.",
            "error"
        )


    finally:

        conn.close()


    return redirect(
        url_for("applicant_attendance")
    )


# ============================================================
# APPLICANT ATTENDANCE HISTORY
# ============================================================

@app.route("/applicant/attendance/history")
def applicant_attendance_history():

    applicant_id = session.get(
        "applicant_id"
    )

    if not applicant_id:

        return redirect(
            url_for("applicant_login")
        )


    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    attendance_date,
                    clock_in,
                    clock_out,
                    total_hours,
                    status,
                    clock_in_location_verified,
                    clock_out_location_verified

                FROM attendance

                WHERE worker_id = %s

                ORDER BY attendance_date DESC

                """,
                (applicant_id,)
            )

            attendance_history = cur.fetchall()


    finally:

        conn.close()


    return render_template(
        "applicant_attendance_history.html",

        attendance_history=attendance_history
    )
# ============================================================
# INITIALIZE DATABASE
# ============================================================

with app.app_context():

    init_db()

    create_initial_admin()

# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                5000
            )
        ),
        debug=True
    )
