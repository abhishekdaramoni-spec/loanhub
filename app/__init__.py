import os
from flask import Flask, render_template
from app.utils.extensions import db, login_manager, mail, csrf, migrate
from app.models.user import User
from app.routes import auth_bp, main_bp, admin_bp

def create_app(config_name=None):
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'development')

    from config import config_by_name
    config_class = config_by_name.get(config_name, config_by_name['default'])

    app = Flask(__name__,
                template_folder=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates'),
                static_folder=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static'))

    app.config.from_object(config_class)

    # Normalize DATABASE_URL for PostgreSQL if set as postgres:// (Render/Heroku convention)
    uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    if uri and uri.startswith('postgres://'):
        uri = uri.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = uri

    # Verify connection to remote MySQL/PostgreSQL, fallback to SQLite if connection fails or is unset
    if uri and not uri.startswith('sqlite'):
        from sqlalchemy import create_engine
        try:
            # Use connect_timeout to prevent hanging if remote DB is down
            engine = create_engine(uri, connect_args={'connect_timeout': 5} if 'mysql' in uri or 'postgresql' in uri else {})
            conn = engine.connect()
            conn.close()
            print("Connected to remote database successfully.")
        except Exception as e:
            fallback_db = app.config.get('SQLITE_FALLBACK_PATH')
            print(f"Remote check failed ({e}). Falling back to local SQLite: {fallback_db}")
            os.makedirs(os.path.dirname(fallback_db), exist_ok=True)
            app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{fallback_db}"
    elif not uri:
        fallback_db = app.config.get('SQLITE_FALLBACK_PATH')
        print(f"DATABASE_URL is not set. Falling back to local SQLite: {fallback_db}")
        os.makedirs(os.path.dirname(fallback_db), exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{fallback_db}"

    # Clean up SQLite incompatible engine options
    uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    if uri and uri.startswith('sqlite'):
        engine_opts = dict(app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {}))
        engine_opts.pop('pool_size', None)
        engine_opts.pop('max_overflow', None)
        engine_opts.pop('pool_recycle', None)
        engine_opts.pop('pool_pre_ping', None)
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_opts

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    return app

# Setup User Loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
