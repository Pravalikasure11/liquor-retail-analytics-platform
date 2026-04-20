"""
Security core: JWT tokens, password hashing, TOTP MFA, SMS MFA, rate limiting.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import secrets
import pyotp
import qrcode
import io
import base64
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import get_settings
from app.database import get_db

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()

# Failed login tracking (in production use Redis)
_failed_attempts: dict = {}
_lockouts: dict = {}


# ── Passwords ─────────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Enforce strong passwords."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, "OK"


# ── JWT Tokens ────────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def create_mfa_temp_token(user_id: int) -> str:
    """Short-lived token issued after password check, before MFA verification."""
    expire = datetime.utcnow() + timedelta(minutes=10)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "mfa_pending"},
        settings.secret_key, algorithm="HS256"
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ── Rate limiting / lockout ────────────────────────────────────────────────────
def check_lockout(username: str):
    if username in _lockouts:
        if datetime.utcnow() < _lockouts[username]:
            remaining = (_lockouts[username] - datetime.utcnow()).seconds // 60
            raise HTTPException(status_code=429, detail=f"Account locked. Try again in {remaining} minutes.")
        else:
            del _lockouts[username]
            _failed_attempts.pop(username, None)


def record_failed_attempt(username: str):
    _failed_attempts[username] = _failed_attempts.get(username, 0) + 1
    if _failed_attempts[username] >= settings.max_login_attempts:
        _lockouts[username] = datetime.utcnow() + timedelta(minutes=settings.lockout_minutes)
        raise HTTPException(status_code=429, detail=f"Too many failed attempts. Account locked for {settings.lockout_minutes} minutes.")


def clear_failed_attempts(username: str):
    _failed_attempts.pop(username, None)
    _lockouts.pop(username, None)


# ── TOTP MFA ──────────────────────────────────────────────────────────────────
def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_totp_uri(secret: str, username: str) -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=settings.mfa_issuer)


def generate_qr_code_b64(uri: str) -> str:
    """Generate QR code as base64 PNG for frontend display."""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def generate_backup_codes() -> list[str]:
    """Generate 8 one-time backup codes."""
    return [secrets.token_hex(4).upper() for _ in range(8)]


# ── SMS MFA ───────────────────────────────────────────────────────────────────
_sms_codes: dict = {}


def generate_sms_code(user_id: int) -> str:
    code = str(secrets.randbelow(900000) + 100000)
    _sms_codes[user_id] = {"code": code, "expires": datetime.utcnow() + timedelta(minutes=10)}
    return code


def verify_sms_code(user_id: int, code: str) -> bool:
    entry = _sms_codes.get(user_id)
    if not entry:
        return False
    if datetime.utcnow() > entry["expires"]:
        del _sms_codes[user_id]
        return False
    if entry["code"] == code:
        del _sms_codes[user_id]
        return True
    return False


async def send_sms_code(phone: str, code: str):
    """Send SMS via Twilio."""
    if not settings.twilio_account_sid:
        print(f"[DEV] SMS code for {phone}: {code}")
        return
    try:
        from twilio.rest import Client
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        client.messages.create(
            body=f"Zach's Liquor Store login code: {code}. Valid 10 minutes.",
            from_=settings.twilio_phone_number,
            to=phone
        )
    except Exception as e:
        print(f"SMS send failed: {e}")


# ── Auth dependency ────────────────────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    from app.models.models import User
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


async def get_admin_user(current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
