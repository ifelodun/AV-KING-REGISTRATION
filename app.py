import os

from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
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


# ============================================================
# APPLICATION FORM
# ============================================================

@app.route(
    "/apply",
    methods=["GET", "POST"]
)
def apply():

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
    # SAFE FILE NAMES
    # ========================================================

    passport_filename = None

    cv_filename = None

    qualification_filename = None


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

                    'Pending'

                )
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
                    qualification_filename

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

    return redirect(
        url_for(
            "application_success",
            application_number=application_number
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
# INITIALIZE DATABASE
# ============================================================

with app.app_context():

    init_db()


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
