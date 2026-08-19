# =========================================================
# ELOC TECHNOLOGY LAB
# MAIN APPLICATION
# =========================================================


from data.projects import PROJECTS


from flask import (
    Flask,
    render_template,
    request
)


from config import Config
from utils.database import create_tables


# =========================================================
# APPLICATION FACTORY
# =========================================================

def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)


    # =====================================================
    # DATABASE INITIALIZATION
    # =====================================================

    with app.app_context():

        create_tables()


    # =====================================================
    # HOME ROUTE
    # =====================================================

    @app.route("/")
    def home():

        return render_template(
            "index.html",
            PROJECTS=PROJECTS
        )


    return app


# =========================================================
# CREATE APPLICATION
# =========================================================

app = create_app()


# =========================================================
# PROJECT ROUTES
# =========================================================


@app.route("/projects")
def projects():

    # -----------------------------------------------------
    # GET CATEGORY FILTER
    # -----------------------------------------------------

    category = request.args.get(
        "category",
        "all"
    ).lower()


    # -----------------------------------------------------
    # FILTER PROJECTS
    # -----------------------------------------------------

    if category == "all":

        filtered_projects = PROJECTS

    else:

        filtered_projects = [
            project
            for project in PROJECTS
            if project.get("category_slug") == category
        ]


    # -----------------------------------------------------
    # BUILD CATEGORY LIST
    # -----------------------------------------------------

    categories = []

    existing_slugs = set()


    for project in PROJECTS:

        slug = project.get(
            "category_slug",
            ""
        )

        if slug not in existing_slugs:

            categories.append({
                "name": project.get(
                    "category",
                    "Other"
                ),

                "slug": slug
            })

            existing_slugs.add(slug)


    # -----------------------------------------------------
    # RENDER PROJECTS PAGE
    # -----------------------------------------------------

    return render_template(
        "projects.html",

        projects=filtered_projects,

        categories=categories,

        active_category=category
    )


# =========================================================
# INDIVIDUAL PROJECT ROUTE
# =========================================================


@app.route("/project/<project_id>")
def project_detail(project_id):

    # -----------------------------------------------------
    # FIND PROJECT
    # -----------------------------------------------------

    project = next(
        (
            project
            for project in PROJECTS
            if project.get("id") == project_id
        ),
        None
    )


    # -----------------------------------------------------
    # PROJECT NOT FOUND
    # -----------------------------------------------------

    if project is None:

        return "Project not found", 404


    # -----------------------------------------------------
    # RENDER PROJECT DETAIL PAGE
    # -----------------------------------------------------

    return render_template(
        "project-detail.html",
        project=project
    )


# =========================================================
# ABOUT PAGE
# =========================================================


@app.route("/about")
def about():

    return render_template(
        "about.html"
    )


# =========================================================
# TECHNOLOGY PAGE
# =========================================================


@app.route("/technology")
def technology():

    return render_template(
        "technology.html"
    )


# =========================================================
# CONTACT PAGE
# =========================================================


@app.route("/contact")
def contact():

    return render_template(
        "contact.html"
    )


# =========================================================
# APPLICATION ENTRY POINT
# =========================================================


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )