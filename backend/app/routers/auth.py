"""Auth router: register, login (step 1 + MFA step 2), MFA setup, refresh."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.database import get_db
from app.models.models import User
from app.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    create_mfa_temp_token, decode_token, check_lockout, record_failed_attempt,
    clear_failed_attempts, generate_totp_secret, get_totp_uri, generate_qr_code_b64,
    verify_totp, generate_backup_codes, generate_sms_code, verify_sms_code,
    send_sms_code, validate_password_strength, get_current_user
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_admin: bool = False


class LoginRequest(BaseModel):
    username: str
    password: str


class MFAVerifyRequest(BaseModel):
    temp_token: str
    code: str
    method: str = "totp"  # "totp" or "sms"


class SetupTOTPRequest(BaseModel):
    code: str  # Verify user scanned QR correctly


class SetupSMSRequest(BaseModel):
    phone: str


@router.post("/register", status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check existing
    for field, val in [("username", payload.username), ("email", payload.email)]:
        r = await db.execute(select(User).where(getattr(User, field) == val))
        if r.scalar_one_or_none():
            raise HTTPException(400, f"{field.capitalize()} already taken")

    ok, msg = validate_password_strength(payload.password)
    if not ok:
        raise HTTPException(400, msg)

    user = User(
        username=payload.username, email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name, phone=payload.phone,
        is_admin=payload.is_admin,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "username": user.username, "message": "Account created"}


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Step 1: Validate credentials. Returns either tokens or mfa_required."""
    check_lockout(payload.username)

    r = await db.execute(select(User).where(User.username == payload.username))
    user = r.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        record_failed_attempt(payload.username)
        raise HTTPException(401, "Invalid username or password")

    if not user.is_active:
        raise HTTPException(403, "Account disabled")

    clear_failed_attempts(payload.username)

    # If MFA enabled, return temp token
    if user.mfa_enabled:
        temp_token = create_mfa_temp_token(user.id)
        # If SMS MFA, send code
        if user.mfa_type == "sms" and user.phone:
            code = generate_sms_code(user.id)
            await send_sms_code(user.phone, code)
        return {
            "mfa_required": True,
            "mfa_type": user.mfa_type,
            "temp_token": temp_token,
            "message": "MFA verification required"
        }

    # No MFA — issue full tokens
    from datetime import datetime
    user.last_login = datetime.utcnow()
    await db.commit()

    return {
        "mfa_required": False,
        "access_token": create_access_token({"sub": str(user.id)}),
        "refresh_token": create_refresh_token({"sub": str(user.id)}),
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "full_name": user.full_name, "is_admin": user.is_admin}
    }


@router.post("/mfa/verify")
async def verify_mfa(payload: MFAVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Step 2: Verify MFA code, return full tokens."""
    token_data = decode_token(payload.temp_token)
    if token_data.get("type") != "mfa_pending":
        raise HTTPException(401, "Invalid temp token")

    user_id = int(token_data["sub"])
    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    verified = False
    if payload.method == "totp" and user.totp_secret:
        verified = verify_totp(user.totp_secret, payload.code)
    elif payload.method == "sms":
        verified = verify_sms_code(user.id, payload.code)
    # Check backup codes
    elif len(payload.code) == 8 and user.backup_codes:
        from app.core.security import verify_password
        for i, bc in enumerate(user.backup_codes):
            if verify_password(payload.code, bc):
                user.backup_codes.pop(i)
                verified = True
                break

    if not verified:
        raise HTTPException(401, "Invalid MFA code")

    from datetime import datetime
    user.last_login = datetime.utcnow()
    await db.commit()

    return {
        "access_token": create_access_token({"sub": str(user.id)}),
        "refresh_token": create_refresh_token({"sub": str(user.id)}),
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "full_name": user.full_name, "is_admin": user.is_admin}
    }


@router.post("/mfa/setup/totp")
async def setup_totp(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Generate TOTP secret and QR code for user to scan."""
    secret = generate_totp_secret()
    uri = get_totp_uri(secret, current_user.username)
    qr_b64 = generate_qr_code_b64(uri)
    current_user.totp_secret = secret
    current_user.totp_verified = False
    await db.commit()
    return {"qr_code": f"data:image/png;base64,{qr_b64}", "secret": secret, "uri": uri}


@router.post("/mfa/setup/totp/confirm")
async def confirm_totp(
    payload: SetupTOTPRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """User submits first code to confirm TOTP setup."""
    if not current_user.totp_secret:
        raise HTTPException(400, "TOTP not initialized. Call /mfa/setup/totp first.")
    if not verify_totp(current_user.totp_secret, payload.code):
        raise HTTPException(400, "Invalid code")

    backup_codes_plain = generate_backup_codes()
    current_user.totp_verified = True
    current_user.mfa_enabled = True
    current_user.mfa_type = "totp"
    current_user.backup_codes = [hash_password(c) for c in backup_codes_plain]
    await db.commit()
    return {"message": "TOTP MFA enabled", "backup_codes": backup_codes_plain}


@router.post("/mfa/setup/sms")
async def setup_sms(
    payload: SetupSMSRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send SMS verification code to confirm phone number."""
    code = generate_sms_code(current_user.id)
    await send_sms_code(payload.phone, code)
    current_user.phone = payload.phone
    await db.commit()
    return {"message": f"Verification code sent to {payload.phone}"}


@router.post("/mfa/setup/sms/confirm")
async def confirm_sms(
    payload: MFAVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_sms_code(current_user.id, payload.code):
        raise HTTPException(400, "Invalid or expired code")
    current_user.mfa_enabled = True
    current_user.mfa_type = "sms"
    await db.commit()
    return {"message": "SMS MFA enabled"}


@router.post("/mfa/disable")
async def disable_mfa(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.mfa_enabled = False
    current_user.mfa_type = "none"
    current_user.totp_secret = None
    current_user.totp_verified = False
    current_user.backup_codes = None
    await db.commit()
    return {"message": "MFA disabled"}


@router.post("/refresh")
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid refresh token")
    user_id = int(payload["sub"])
    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(401, "User not found")
    return {"access_token": create_access_token({"sub": str(user_id)}), "token_type": "bearer"}


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id, "username": current_user.username,
        "email": current_user.email, "full_name": current_user.full_name,
        "phone": current_user.phone, "is_admin": current_user.is_admin,
        "mfa_enabled": current_user.mfa_enabled, "mfa_type": current_user.mfa_type,
        "last_login": current_user.last_login,
    }
