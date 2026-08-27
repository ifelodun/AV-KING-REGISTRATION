import os

from flask import Flask, render_template
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "development-secret-key"
)

app.config["DATABASE_URL"] = os.getenv(
    "DATABASE_URL"
)


# ============================================================
# COMPANY BRANDING
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
    }


# ============================================================
# HOME / APPLICATION PORTAL
# ============================================================

@app.route("/")
def home():

    return render_template("home.html")


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=True
    )
