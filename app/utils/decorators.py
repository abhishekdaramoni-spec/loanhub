from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """
    Decorator to restrict access to admin-only routes.
    Aborts with a 403 Forbidden response if authenticated user is not an admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            from app.utils.extensions import login_manager
            return login_manager.unauthorized()
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
