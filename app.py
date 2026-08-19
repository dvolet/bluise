from data.projects import PROJECTS

from flask import (
    Flask,
    render_template,
    request
)

from config import Config
from utils.database import create_tables


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


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )