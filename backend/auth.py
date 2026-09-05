import base64
import hashlib
import hmac
import os
import secrets
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, Request, status


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
SESSION_COOKIE_NAME = "supersonic_admin_session"
SESSION_TTL_SECONDS = 8 * 60 * 60

_sessions: dict[str, tuple[float, str]] = {}
_session_lock = threading.Lock()


def load_project_env() -> None:
    """Load simple KEY=VALUE entries without adding a dotenv dependency."""

    if not ENV_PATH.is_file():
        return
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=64,
    )
    return "scrypt$16384$8$1${}${}".format(
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(derived).decode("ascii"),
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, n_value, r_value, p_value, salt_value, expected_value = (
            encoded_hash.split("$", 5)
        )
        if algorithm != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_value.encode("ascii"))
        expected = base64.urlsafe_b64decode(expected_value.encode("ascii"))
        candidate = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n_value),
            r=int(r_value),
            p=int(p_value),
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, expected)


@dataclass(frozen=True)
class AdminConfig:
    username: str
    password_hash: str
    session_secret: str
    secure_cookie: bool


def get_admin_config() -> AdminConfig | None:
    username = os.getenv("ADMIN_USERNAME", "")
    password_hash = os.getenv("ADMIN_PASSWORD_HASH", "")
    session_secret = os.getenv("SESSION_SECRET", "")
    if not username or not password_hash or len(session_secret) < 32:
        return None
    return AdminConfig(
        username=username,
        password_hash=password_hash,
        session_secret=session_secret,
        secure_cookie=os.getenv("APP_ENV", "development").lower() == "production",
    )


def authenticate_admin(username: str, password: str) -> bool:
    config = get_admin_config()
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication is not configured.",
        )
    username_matches = hmac.compare_digest(username, config.username)
    password_matches = verify_password(password, config.password_hash)
    return username_matches and password_matches


def _signature(token: str, secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        token.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _create_session(role: str) -> str:
    config = get_admin_config()
    if config is None:
        raise RuntimeError("Admin authentication is not configured.")
    token = secrets.token_urlsafe(32)
    with _session_lock:
        _sessions[token] = (time.time() + SESSION_TTL_SECONDS, role)
    return f"{token}.{_signature(token, config.session_secret)}"


def create_admin_session() -> str:
    return _create_session("admin")


def destroy_admin_session(cookie_value: str | None) -> None:
    if not cookie_value or "." not in cookie_value:
        return
    token = cookie_value.rsplit(".", 1)[0]
    with _session_lock:
        _sessions.pop(token, None)


def _session_role(cookie_value: str | None) -> str | None:
    config = get_admin_config()
    if config is None or not cookie_value or "." not in cookie_value:
        return None
    token, supplied_signature = cookie_value.rsplit(".", 1)
    if not hmac.compare_digest(
        supplied_signature,
        _signature(token, config.session_secret),
    ):
        return None
    now = time.time()
    with _session_lock:
        session = _sessions.get(token)
        if session is None or session[0] <= now:
            _sessions.pop(token, None)
            return None
    return session[1]


def is_admin_session(cookie_value: str | None) -> bool:
    return _session_role(cookie_value) == "admin"


def require_admin(request: Request) -> None:
    cookie_value = request.cookies.get(SESSION_COOKIE_NAME)
    role = _session_role(cookie_value)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required.",
        )
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator permission required.",
        )


def clear_sessions_for_tests() -> None:
    with _session_lock:
        _sessions.clear()


load_project_env()
