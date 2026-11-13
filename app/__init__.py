import os

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(config=None):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['PAGE_SIZE'] = 20
    app.config.update(config or {})
    
    db.init_app(app)
    
    from .routes import bp
    
    app.register_blueprint(bp, url_prefix="/api/v1")

    @app.get("/health/")
    def health():
        """Simple endpoint for load balancer / container health checks."""
        return jsonify(status="ok")

    @app.errorhandler(404)
    def not_found(_):
        return jsonify(error="not found"), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify(error="method not allowed"), 405

    with app.app_context():
        db.create_all()

    return app
