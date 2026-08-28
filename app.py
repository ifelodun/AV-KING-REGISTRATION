import os
import os
import requests
from datetime import datetime
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

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

def generate_application_number():

    conn = get_db()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id
                FROM applications
                ORDER BY id DESC
                LIMIT 1
                """
            )

            row = cur.fetchone()

            if row:

                next_number = row["id"] + 1

            else:

                next_number = 1

        return f"AV-APP-{next_number:05d}"

    finally:

        conn.close()


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
# ============================================================
# APPLICATION FORM
# ============================================================

@app.route(
    "/apply",
    methods=["GET", "POST"]
)
def apply():

    # ========================================================
    # DISPLAY APPLICATION FORM
    # ========================================================

    if request.method == "GET":

        return render_template(
            "apply.html"
        )


    # ========================================================
    # PERSONAL INFORMATION
    # ========================================================

    first_name = (
        request.form.get(
            "first_name",
            ""
        ).strip()
    )

    middle_name = (
        request.form.get(
            "middle_name",
            ""
        ).strip()
    )

    last_name = (
        request.form.get(
            "last_name",
            ""
        ).strip()
    )

    gender = (
        request.form.get(
            "gender",
            ""
        ).strip()
    )

    date_of_birth = (
        request.form.get(
            "date_of_birth",
            ""
        ).strip()
    )


    # ========================================================
    # CONTACT INFORMATION
    # ========================================================

    phone = (
        request.form.get(
            "phone",
            ""
        ).strip()
    )

    email = (
        request.form.get(
            "email",
            ""
        ).strip()
        .lower()
    )

    address = (
        request.form.get(
            "address",
            ""
        ).strip()
    )

    state = (
        request.form.get(
            "state",
            ""
        ).strip()
    )

    lga = (
        request.form.get(
            "lga",
            ""
        ).strip()
    )


    # ========================================================
    # APPLICATION INFORMATION
    # ========================================================

    position_applied = (
        request.form.get(
            "position_applied",
            ""
        ).strip()
    )


    # ========================================================
    # EDUCATION
    # ========================================================

    highest_qualification = (
        request.form.get(
            "highest_qualification",
            ""
        ).strip()
    )

    course_of_study = (
        request.form.get(
            "course_of_study",
            ""
        ).strip()
    )

    institution = (
        request.form.get(
            "institution",
            ""
        ).strip()
    )

    graduation_year = (
        request.form.get(
            "graduation_year",
            ""
        ).strip()
    )


    # ========================================================
    # WORK EXPERIENCE
    # ========================================================

    work_experience = (
        request.form.get(
            "work_experience",
            ""
        ).strip()
    )

    previous_employer = (
        request.form.get(
            "previous_employer",
            ""
        ).strip()
    )

    previous_position = (
        request.form.get(
            "previous_position",
            ""
        ).strip()
    )


    # ========================================================
    # ADDITIONAL INFORMATION
    # ========================================================

    reason_for_applying = (
        request.form.get(
            "reason_for_applying",
            ""
        ).strip()
    )

    additional_information = (
        request.form.get(
            "additional_information",
            ""
        ).strip()
    )


    # ========================================================
    # APPLICANT PORTAL PASSWORD
    # ========================================================

    portal_password = (
        request.form.get(
            "portal_password",
            ""
        ).strip()
    )

    confirm_portal_password = (
        request.form.get(
            "confirm_portal_password",
            ""
        ).strip()
    )


    # ========================================================
    # DECLARATION
    # ========================================================

    declaration = request.form.get(
        "declaration"
    )


    # ========================================================
    # REQUIRED FIELD VALIDATION
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
    # APPLICATION NUMBER
    # ========================================================

    application_number = (
        generate_application_number()
    )


    # ========================================================
    # HASH APPLICANT PASSWORD
    # ========================================================

    password_hash = generate_password_hash(
        portal_password
    )


    # ========================================================
    # SAFE FILE NAMES
    # ========================================================

    passport_filename = None

    cv_filename = None

    qualification_filename = None


    # ========================================================
    # SAVE PASSPORT
    # ========================================================

    if passport and passport.filename:

        original = secure_filename(
            passport.filename
        )

        passport_filename = (
            f"{application_number}_passport_{original}"
        )

        passport.save(
            os.path.join(
                UPLOAD_FOLDER,
                passport_filename
            )
        )


    # ========================================================
    # SAVE CV
    # ========================================================

    if cv and cv.filename:

        original = secure_filename(
            cv.filename
        )

        cv_filename = (
            f"{application_number}_cv_{original}"
        )

        cv.save(
            os.path.join(
                UPLOAD_FOLDER,
                cv_filename
            )
        )


    # ========================================================
    # SAVE QUALIFICATION
    # ========================================================

    if qualification and qualification.filename:

        original = secure_filename(
            qualification.filename
        )

        qualification_filename = (
            f"{application_number}_qualification_{original}"
        )

        qualification.save(
            os.path.join(
                UPLOAD_FOLDER,
                qualification_filename
            )
        )


    # ========================================================
    # SAVE APPLICATION
    # ========================================================

    conn = get_db()

    try:

        with conn.cursor() as cur:

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


        conn.commit()


    except Exception:

        conn.rollback()

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

    if not admin_required():
        return redirect(url_for("admin_login"))

    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    position = request.args.get("position", "").strip()

    conn = get_db()

    try:
        with conn.cursor() as cur:

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
                    submitted_at
                FROM applications
                WHERE 1=1
            """

            params = []

            # ------------------------------------------------
            # SEARCH
            # ------------------------------------------------

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

            # ------------------------------------------------
            # STATUS FILTER
            # ------------------------------------------------

            if status:

                query += """
                    AND status = %s
                """

                params.append(status)

            # ------------------------------------------------
            # POSITION FILTER
            # ------------------------------------------------

            if position:

                query += """
                    AND position_applied = %s
                """

                params.append(position)

            # ------------------------------------------------
            # ORDER
            # ------------------------------------------------

            query += """
                ORDER BY submitted_at DESC
            """

            cur.execute(
                query,
                params
            )

            applications = cur.fetchall()

    finally:

        conn.close()

    return render_template(
        "admin_applications.html",
        applications=applications,
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

@app.route("/admin/settings", methods=["GET", "POST"])
def admin_settings():

    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db()

    try:

        with conn.cursor() as cur:

            # ==================================================
            # GET CURRENT SETTINGS
            # ==================================================

            cur.execute(
                """
                SELECT *
                FROM company_settings
                ORDER BY id ASC
                LIMIT 1
                """
            )

            settings = cur.fetchone()


            # ==================================================
            # SAVE SETTINGS
            # ==================================================

            if request.method == "POST":

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


                # ==============================================
                # UPDATE EXISTING SETTINGS
                # ==============================================

                if settings:

                    cur.execute(
                        """
                        UPDATE company_settings
                        SET
                            company_name = %s,
                            company_email = %s,
                            company_phone = %s,
                            company_address = %s,
                            company_website = %s,
                            footer_text = %s
                        WHERE id = %s
                        """,
                        (
                            company_name,
                            company_email,
                            company_phone,
                            company_address,
                            company_website,
                            footer_text,
                            settings["id"]
                        )
                    )


                # ==============================================
                # CREATE SETTINGS IF NONE EXIST
                # ==============================================

                else:

                    cur.execute(
                        """
                        INSERT INTO company_settings
                        (
                            company_name,
                            company_email,
                            company_phone,
                            company_address,
                            company_website,
                            footer_text
                        )
                        VALUES
                        (
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
                            footer_text
                        )
                    )


                conn.commit()


                flash(
                    "Company settings updated successfully.",
                    "success"
                )


                return redirect(
                    url_for("admin_settings")
                )


    except Exception:

        conn.rollback()

        app.logger.exception(
            "Error updating company settings"
        )

        flash(
            "Unable to update company settings.",
            "error"
        )

    finally:

        conn.close()


    return render_template(
        "admin_settings.html",
        settings=settings
    )

@app.route(
    "/admin/applications/<int:application_id>/download/<file_type>"
)
def admin_download_file(application_id, file_type):

    # --------------------------------------------------------
    # CHECK ADMIN LOGIN
    # --------------------------------------------------------

    if not admin_required():
        return redirect(url_for("admin_login"))


    # --------------------------------------------------------
    # ALLOWED FILE TYPES
    # --------------------------------------------------------

    if file_type not in ["cv", "passport"]:
        flash(
            "Invalid document requested.",
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

            cur.execute(
                """
                SELECT
                    id,
                    cv_filename,
                    passport_filename
                FROM applications
                WHERE id = %s
                LIMIT 1
                """,
                (application_id,)
            )

            application = cur.fetchone()

    finally:

        conn.close()


    # --------------------------------------------------------
    # APPLICATION NOT FOUND
    # --------------------------------------------------------

    if not application:

        flash(
            "Application not found.",
            "error"
        )

        return redirect(
            url_for("admin_applications")
        )


    # --------------------------------------------------------
    # GET FILE NAME
    # --------------------------------------------------------

    if file_type == "cv":

        filename = application["cv_filename"]

    else:

        filename = application["passport_filename"]


    # --------------------------------------------------------
    # FILE DOES NOT EXIST IN DATABASE
    # --------------------------------------------------------

    if not filename:

        flash(
            "This applicant has not uploaded this document.",
            "error"
        )

        return redirect(
            url_for(
                "admin_application_details",
                application_id=application_id
            )
        )


    # --------------------------------------------------------
    # UPLOAD DIRECTORY
    # --------------------------------------------------------

    upload_folder = os.path.join(
        app.root_path,
        "uploads"
    )


    # --------------------------------------------------------
    # REMOVE POSSIBLE PATH INFORMATION
    # --------------------------------------------------------

    filename = os.path.basename(filename)


    # --------------------------------------------------------
    # CHECK ACTUAL FILE
    # --------------------------------------------------------

    file_path = os.path.join(
        upload_folder,
        filename
    )

    if not os.path.isfile(file_path):

        flash(
            "The document could not be found on the server.",
            "error"
        )

        return redirect(
            url_for(
                "admin_application_details",
                application_id=application_id
            )
        )


    # --------------------------------------------------------
    # DOWNLOAD FILE
    # --------------------------------------------------------

    return send_from_directory(
        upload_folder,
        filename,
        as_attachment=True
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
