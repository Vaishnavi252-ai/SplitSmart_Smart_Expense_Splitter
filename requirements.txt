import os

from flask import Flask, jsonify, render_template, request
from pydantic import ValidationError

from db import init_app as init_db_app
from db import init_db, seed_db
from errors import ApiError
from routes.ai import ai_bp
from routes.expenses import expenses_bp
from routes.groups import groups_bp
from routes.pages import pages_bp
from routes.users import users_bp


def create_app(test_config=None):
    app = Flask(__name__, static_folder="../client/static", template_folder="../client/templates")

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)

    app.config.from_mapping(
        DATABASE=os.path.join(data_dir, "expense_splitter.db"),
        OPENAI_MODEL=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    )

    if test_config:
        app.config.update(test_config)

    init_db_app(app)

    app.register_blueprint(pages_bp)
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(groups_bp, url_prefix="/api/groups")
    app.register_blueprint(expenses_bp, url_prefix="/api/groups/<int:group_id>")
    app.register_blueprint(ai_bp, url_prefix="/api/groups/<int:group_id>/ai")

    @app.errorhandler(ApiError)
    def handle_api_error(error):
        payload = {"error": error.message}
        if error.details is not None:
            payload["details"] = error.details
        return jsonify(payload), error.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return jsonify(
            {
                "error": "Validation failed.",
                "details": error.errors(include_url=False, include_context=False),
            }
        ), 400

    @app.errorhandler(404)
    def handle_not_found(_error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found."}), 404
        return render_template("index.html")

    @app.errorhandler(500)
    def handle_server_error(_error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Unexpected server error."}), 500
        return jsonify({"error": "Unexpected server error."}), 500

    with app.app_context():
        init_db()
        seed_db()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "1") == "1", port=int(os.getenv("PORT", "5000")))
