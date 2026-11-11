"""Sessões bearer opacas com expiração, sem segredo estático no código."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe

from sqlalchemy.orm import Session

from app.models import User, UserSession

SESSION_TTL_SECONDS = 3600


def utcnow() -> datetime:
    """UTC ingênuo para compatibilidade com DateTime do SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_session(db: Session, user: User) -> str:
    token = token_urlsafe(32)
    db.add(UserSession(
        token_hash=sha256(token.encode("utf-8")).hexdigest(),
        user_id=user.id,
        expires_at=utcnow() + timedelta(seconds=SESSION_TTL_SECONDS),
    ))
    db.commit()
    return token


def get_session_user(db: Session, token: str) -> User | None:
    digest = sha256(token.encode("utf-8")).hexdigest()
    session = db.query(UserSession).filter(
        UserSession.token_hash == digest,
        UserSession.expires_at > utcnow(),
    ).first()
    if session is None:
        return None
    return db.query(User).filter(User.id == session.user_id).first()
