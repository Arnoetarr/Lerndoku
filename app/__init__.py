from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

db = SQLAlchemy()
migrate = Migrate()

from app.models import Lernfeld  # Für den Kontextprozessor

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile("config.py")

    db.init_app(app)
    migrate.init_app(app, db)

    # ── Hier die Blueprints importieren und registrieren ──
    from .routes.personen    import bp as personen_bp
    from .routes.freiarbeit  import bp as freiarbeit_bp
    from .routes.kurse       import bp as kurse_bp       # neu
    from .routes.lernfelder  import bp as lernfelder_bp
    from .routes.leistung import bp as leistung_bp

    app.register_blueprint(personen_bp)
    app.register_blueprint(freiarbeit_bp)
    app.register_blueprint(kurse_bp)       # neu
    app.register_blueprint(lernfelder_bp)
    app.register_blueprint(leistung_bp)

    # Kontextprozessor für Lernfelder in Templates
    @app.context_processor
    def inject_lernfelder():
        return dict(lernfelder=Lernfeld.query.order_by(Lernfeld.name).all())

    return app


