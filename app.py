from data.projects import PROJECTS

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from config import Config
from utils.database import create_tables

import os
import smtplib

from email.message import EmailMessage


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    with app.app_context():
        create_tables()

    @app.route("/")
    def home():
        return render_template(
            "index.html",
            PROJECTS=PROJECTS
        )

    return app


app = create_app()


# =========================================================
# PROJECT ROUTES
# =========================================================

@app.route("/projects")
def projects():

    category = request.args.get(
        "category",
        "all"
    ).lower()

    if category == "all":
        filtered_projects = PROJECTS

    else:
        filtered_projects = [
            project
            for project in PROJECTS
            if project["category_slug"] == category
        ]

    categories = []

    for project in PROJECTS:

        if project["category_slug"] not in [
            item["slug"]
            for item in categories
        ]:

            categories.append({
                "name": project["category"],
                "slug": project["category_slug"]
            })

    return render_template(
        "projects.html",
        projects=filtered_projects,
        categories=categories,
        active_category=category
    )


@app.route("/project/<project_id>")
def project_detail(project_id):

    project = next(
        (
            project
            for project in PROJECTS
            if project["id"] == project_id
        ),
        None
    )

    if project is None:
        return "Project not found", 404

    return render_template(
        "project-detail.html",
        project=project
    )


# =========================================================
# ELOC TECHNOLOGY LAB
# TECHNOLOGY PAGE
# =========================================================

@app.route("/technology")
def technology():
    return render_template(
        "technology.html"
    )


# =========================================================
# ELOC TECHNOLOGY LAB
# CONTACT PAGE
# =========================================================

@app.route(
    "/contact",
    methods=["GET", "POST"]
)
def contact():

    if request.method == "POST":

        # -------------------------------------------------
        # GET FORM DATA
        # -------------------------------------------------

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        subject = request.form.get(
            "subject",
            ""
        ).strip()

        message = request.form.get(
            "message",
            ""
        ).strip()


        # -------------------------------------------------
        # BASIC VALIDATION
        # -------------------------------------------------

        if not name or not email or not subject or not message:

            flash(
                "Please complete all required fields.",
                "error"
            )

            return render_template(
                "contact.html"
            )


        # -------------------------------------------------
        # LENGTH PROTECTION
        # -------------------------------------------------

        if len(name) > 100:

            flash(
                "Your name is too long.",
                "error"
            )

            return render_template(
                "contact.html"
            )


        if len(email) > 254:

            flash(
                "Please enter a valid email address.",
                "error"
            )

            return render_template(
                "contact.html"
            )


        if len(subject) > 150:

            flash(
                "The selected subject is invalid.",
                "error"
            )

            return render_template(
                "contact.html"
            )


        if len(message) > 10000:

            flash(
                "Your message is too long. Please keep it under 10,000 characters.",
                "error"
            )

            return render_template(
                "contact.html"
            )


        # -------------------------------------------------
        # EMAIL CONFIGURATION
        #
        # These values MUST be stored in Render
        # Environment Variables.
        # -------------------------------------------------

        smtp_host = os.getenv(
            "SMTP_HOST",
            "smtp.gmail.com"
        )

        smtp_port = int(
            os.getenv(
                "SMTP_PORT",
                "587"
            )
        )

        smtp_email = os.getenv(
            "SMTP_EMAIL"
        )

        smtp_password = os.getenv(
            "SMTP_PASSWORD"
        )

        destination_email = os.getenv(
            "CONTACT_EMAIL",
            "elearningonecreativity@gmail.com"
        )


        # -------------------------------------------------
        # MAKE SURE SMTP IS CONFIGURED
        # -------------------------------------------------

        if not smtp_email or not smtp_password:

            app.logger.error(
                "SMTP_EMAIL or SMTP_PASSWORD is not configured."
            )

            flash(
                "The message service is temporarily unavailable. Please contact us by email directly.",
                "error"
            )

            return render_template(
                "contact.html"
            )


        # -------------------------------------------------
        # CREATE EMAIL
        # -------------------------------------------------

        email_message = EmailMessage()

        email_message["Subject"] = (
            f"ELOC Technology Lab — {subject}"
        )

        email_message["From"] = smtp_email

        email_message["To"] = destination_email

        email_message["Reply-To"] = email


        email_message.set_content(
            f"""
ELOC TECHNOLOGY LAB
NEW WEBSITE CONTACT MESSAGE
========================================

Name:
{name}

Email:
{email}

Subject:
{subject}

----------------------------------------
MESSAGE
----------------------------------------

{message}

----------------------------------------

This message was submitted through the
ELOC Technology Lab website contact form.
"""
        )


        # -------------------------------------------------
        # SEND EMAIL
        # -------------------------------------------------

        try:

            with smtplib.SMTP(
                smtp_host,
                smtp_port,
                timeout=20
            ) as server:

                server.starttls()

                server.login(
                    smtp_email,
                    smtp_password
                )

                server.send_message(
                    email_message
                )


            flash(
                "Your message has been sent successfully. We will get back to you soon.",
                "success"
            )

            return redirect(
                url_for("contact")
            )


        except Exception as error:

            app.logger.exception(
                "Contact form email failed: %s",
                error
            )

            flash(
                "We could not send your message right now. Please try again or contact us directly by email.",
                "error"
            )

            return render_template(
                "contact.html"
            )


    # -----------------------------------------------------
    # NORMAL GET REQUEST
    #
    # This is what was missing.
    # It allows /contact to open normally.
    # -----------------------------------------------------

    return render_template(
        "contact.html"
    )

# =========================================================
# APPLICATION START
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )