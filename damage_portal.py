
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from database import get_db


damage_bp = Blueprint(
    "damage",
    __name__,
    url_prefix="/admin/damage"
)


def damage_admin_required():
    return bool(session.get("admin_id"))


@damage_bp.route("/settings", methods=["GET", "POST"])
def payment_settings():

    if not damage_admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db()

    try:
        with conn.cursor() as cur:

            if request.method == "POST":

                payments_enabled = (
                    "payments_enabled" in request.form
                )

                paystack_enabled = (
                    "paystack_enabled" in request.form
                )

                bank_transfer_enabled = (
                    "bank_transfer_enabled" in request.form
                )

                preferred_method = request.form.get(
                    "preferred_method", "paystack"
                )

                if preferred_method not in ("paystack", "bank_transfer"):
                    preferred_method = "paystack"

                bank_name = request.form.get(
                    "bank_name", ""
                ).strip()

                account_name = request.form.get(
                    "account_name", ""
                ).strip()

                account_number = request.form.get(
                    "account_number", ""
                ).strip()

                transfer_instructions = request.form.get(
                    "transfer_instructions", ""
                ).strip()

                if preferred_method == "paystack" and not paystack_enabled:
                    flash(
                        "Enable Paystack or select Bank Transfer.",
                        "danger"
                    )
                    return redirect(url_for("damage.payment_settings"))

                if preferred_method == "bank_transfer" and not bank_transfer_enabled:
                    flash(
                        "Enable Bank Transfer or select Paystack.",
                        "danger"
                    )
                    return redirect(url_for("damage.payment_settings"))

                if bank_transfer_enabled and (
                    not bank_name or not account_name or not account_number
                ):
                    flash(
                        "Enter the bank name, account name and account number.",
                        "danger"
                    )
                    return redirect(url_for("damage.payment_settings"))

                cur.execute("""
                    UPDATE damage_payment_settings
                    SET
                        payments_enabled = %s,
                        paystack_enabled = %s,
                        bank_transfer_enabled = %s,
                        preferred_method = %s,
                        bank_name = %s,
                        account_name = %s,
                        account_number = %s,
                        transfer_instructions = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, (
                    payments_enabled,
                    paystack_enabled,
                    bank_transfer_enabled,
                    preferred_method,
                    bank_name,
                    account_name,
                    account_number,
                    transfer_instructions
                ))

                conn.commit()

                flash(
                    "Damage payment settings saved successfully.",
                    "success"
                )

                return redirect(url_for("damage.payment_settings"))

            cur.execute("""
                SELECT *
                FROM damage_payment_settings
                WHERE id = 1
            """)

            settings = cur.fetchone()

            return render_template(
                "damage_payment_settings.html",
                settings=settings
            )

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# =========================================================
# WORKER DAMAGE REPORT PORTAL
# =========================================================

damage_worker_bp = Blueprint(
    "damage_worker",
    __name__,
    url_prefix="/damage"
)


@damage_worker_bp.route("/report", methods=["GET", "POST"])
def worker_report_damage():

    applicant_id = session.get("applicant_id")

    if not session.get("applicant_logged_in") or not applicant_id:
        return redirect(url_for("applicant_login"))

    conn = get_db()

    try:
        with conn.cursor() as cur:

            # Confirm that this is an approved applicant
            # whose portal is still active.
            cur.execute("""
                SELECT id, first_name, last_name, status, portal_active
                FROM applications
                WHERE id = %s
                LIMIT 1
            """, (applicant_id,))

            applicant = cur.fetchone()

            if (
                not applicant
                or applicant["status"] != "Approved"
                or not applicant["portal_active"]
            ):
                flash(
                    "You are not currently authorised to submit damage reports.",
                    "danger"
                )
                return redirect(url_for("applicant_portal"))

            if request.method == "POST":

                title = request.form.get("title", "").strip()
                description = request.form.get("description", "").strip()
                damage_date_text = request.form.get("damage_date", "").strip()
                category_id = request.form.get("category_id", "").strip()

                if not all([title, description, damage_date_text, category_id]):
                    flash("Please complete all the required fields.", "danger")
                    return redirect(url_for("damage_worker.worker_report_damage"))

                try:
                    damage_date = datetime.strptime(
                        damage_date_text, "%Y-%m-%d"
                    ).date()
                    category_id = int(category_id)
                except (ValueError, TypeError):
                    flash("Please enter a valid date and category.", "danger")
                    return redirect(url_for("damage_worker.worker_report_damage"))

                cur.execute("""
                    SELECT id, category_name, default_amount
                    FROM damage_categories
                    WHERE id = %s
                    AND is_active = TRUE
                    LIMIT 1
                """, (category_id,))

                category = cur.fetchone()

                if not category:
                    flash("Please select a valid damage category.", "danger")
                    return redirect(url_for("damage_worker.worker_report_damage"))

                amount = category["default_amount"]

                cur.execute("""
                    INSERT INTO damage_reports (
                        application_id,
                        title,
                        description,
                        damage_date,
                        category_id,
                        amount,
                        status,
                        payment_status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, 'Pending', 'Unpaid')
                """, (
                    applicant_id,
                    title,
                    description,
                    damage_date,
                    category_id,
                    amount
                ))

                conn.commit()

                flash(
                    "Your damage report has been submitted for admin review.",
                    "success"
                )

                return redirect(
                    url_for("damage_worker.worker_report_damage")
                )

            cur.execute("""
                SELECT id, category_name, default_amount, description
                FROM damage_categories
                WHERE is_active = TRUE
                ORDER BY category_name ASC
            """)

            categories = cur.fetchall()

            return render_template(
                "damage_worker_report.html",
                applicant=applicant,
                categories=categories
            )

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
            
