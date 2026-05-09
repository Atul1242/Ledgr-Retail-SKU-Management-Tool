"""
auth.py — Authentication & Access Control (Brief Part 2B)

Roles: owner / manager / salesman
Multi-store scoping: every query includes store_id filter.
Session timeout: 12h owner/manager, 8h salesman.
CSRF: per-session token, header X-CSRF-Token verified on state-changing
methods (POST/PUT/PATCH/DELETE) for non-multipart requests.
"""
import os
import secrets
import functools
import hmac
from datetime import timedelta
import bcrypt
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

auth_bp = Blueprint('auth', __name__)

# Demo users — passwords are hashed at module load. In production these come
# from the User table; passwords here are seed values for the demo accounts.
_DEMO_PASSWORDS = {
    'owner@sunrise.com':    os.environ.get('DEMO_OWNER_PASSWORD',    'sunrise2024'),
    'manager@sunrise.com':  os.environ.get('DEMO_MANAGER_PASSWORD',  'manager2024'),
    'salesman@sunrise.com': os.environ.get('DEMO_SALESMAN_PASSWORD', 'sales2024'),
}

def _hash(pw: str) -> bytes:
    return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt(rounds=10))

DEMO_USERS = {
    'owner@sunrise.com': {
        'id': 'u-owner-001',
        'email': 'owner@sunrise.com',
        'password_hash': _hash(_DEMO_PASSWORDS['owner@sunrise.com']),
        'role': 'owner',
        'full_name': 'Rajesh Sharma',
        'stores': ['store-pune-001', 'store-nashik-001']
    },
    'manager@sunrise.com': {
        'id': 'u-manager-001',
        'email': 'manager@sunrise.com',
        'password_hash': _hash(_DEMO_PASSWORDS['manager@sunrise.com']),
        'role': 'manager',
        'full_name': 'Priya Deshmukh',
        'stores': ['store-pune-001']
    },
    'salesman@sunrise.com': {
        'id': 'u-salesman-001',
        'email': 'salesman@sunrise.com',
        'password_hash': _hash(_DEMO_PASSWORDS['salesman@sunrise.com']),
        'role': 'salesman',
        'full_name': 'Amit Patil',
        'stores': ['store-nashik-001']
    }
}


class DemoUser:
    """Demo user object for Flask-Login integration."""
    def __init__(self, user_data):
        self.id = user_data['id']
        self.email = user_data['email']
        self.role = user_data['role']
        self.full_name = user_data['full_name']
        self.stores = user_data['stores']

    @property
    def is_authenticated(self):
        return True
    @property
    def is_active(self):
        return True
    @property
    def is_anonymous(self):
        return False
    def get_id(self):
        return self.id

    @property
    def initials(self):
        parts = self.full_name.split()
        return ''.join(p[0].upper() for p in parts[:2])


def init_auth(app):
    """Initialize Flask-Login with the app."""
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access the dashboard.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        for email, data in DEMO_USERS.items():
            if data['id'] == user_id:
                return DemoUser(data)
        return None

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith('/api/'):
            return jsonify({"status": "error", "message": "Authentication required"}), 401
        return redirect(url_for('auth.login', next=request.path))

    @app.before_request
    def set_session_timeout():
        if current_user.is_authenticated:
            session.permanent = True
            if current_user.role == 'salesman':
                app.permanent_session_lifetime = timedelta(hours=8)
            else:
                app.permanent_session_lifetime = timedelta(hours=12)


def role_required(*roles):
    """Decorator to restrict access to specific roles. Returns JSON 403 for
    /api/* paths (Ajax-friendly) and a flash+redirect for HTML pages."""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.path.startswith('/api/'):
                    return jsonify({"status": "error", "message": "Authentication required"}), 401
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                if request.path.startswith('/api/'):
                    return jsonify({
                        "status": "error",
                        "message": f"Forbidden: requires one of {list(roles)} (you are {current_user.role})"
                    }), 403
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_user_store_ids():
    """Return the store_ids the current user can see, or None if not logged in.
    None means no scoping (callers should treat as 'no access')."""
    if not current_user.is_authenticated:
        return None
    return list(getattr(current_user, "stores", []) or [])


# ── CSRF protection (Brief Phase 7 leftover) ──
# Per-session token, lazily created on first GET. JS reads the meta tag and
# sends the value back as X-CSRF-Token on POST/PUT/PATCH/DELETE.
# Routes can opt out via @csrf_exempt (used for /login, /logout, /api/upload-sales).

CSRF_HEADER = "X-CSRF-Token"
CSRF_SESSION_KEY = "_csrf_token"
_CSRF_EXEMPT_ENDPOINTS = set()


def csrf_exempt(view):
    """Decorator marking a view as CSRF-exempt (e.g. /login form, file uploads)."""
    _CSRF_EXEMPT_ENDPOINTS.add(view.__name__)
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        return view(*args, **kwargs)
    wrapped._csrf_exempt = True
    return wrapped


def get_csrf_token():
    """Get or create the CSRF token for this session."""
    tok = session.get(CSRF_SESSION_KEY)
    if not tok:
        tok = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = tok
    return tok


def init_csrf(app):
    """Install before-request CSRF check."""
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    @app.before_request
    def _csrf_check():
        if request.method in SAFE_METHODS:
            return None
        endpoint = request.endpoint or ""
        # Exempt-by-name (the @csrf_exempt registry above)
        view = app.view_functions.get(endpoint)
        if view and getattr(view, "_csrf_exempt", False):
            return None
        # Exempt the login flow and the public service worker (no auth, no state)
        if endpoint in {"auth.login", "auth.logout"}:
            return None
        # Exempt multipart uploads — they get auth via session + endpoint-specific
        # checks. Browsers send these with their own CSRF protection (origin check).
        if request.content_type and request.content_type.startswith("multipart/"):
            return None
        # PWA scan endpoint — bearer token flow per Brief Part 2F.
        if request.path == "/api/sku/scan":
            return None
        # If the user isn't logged in, let the @login_required handler return 401
        # (CSRF only matters for authenticated sessions).
        if not current_user.is_authenticated:
            return None
        sent = request.headers.get(CSRF_HEADER) or (request.form.get("csrf_token") if request.form else None)
        expected = session.get(CSRF_SESSION_KEY)
        if not expected or not sent or not hmac.compare_digest(str(sent), str(expected)):
            if request.path.startswith("/api/"):
                return jsonify({"status": "error", "message": "CSRF token missing or invalid"}), 403
            abort(403)
        return None

    @app.context_processor
    def _inject_csrf():
        return {"csrf_token": get_csrf_token()}


def _verify_password(plain: str, hashed: bytes) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed)
    except Exception:
        return False


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        user_data = DEMO_USERS.get(email)
        if user_data and _verify_password(password, user_data['password_hash']):
            user = DemoUser(user_data)
            login_user(user, remember=True)
            next_page = request.args.get('next')
            if user.role == 'salesman':
                return redirect('/mobile/')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
