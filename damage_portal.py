
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
