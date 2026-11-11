"""Bloqueio temporário após tentativas consecutivas de login inválidas."""
from datetime import datetime, timedelta, timezone
from math import ceil

from sqlalchemy.orm import Session

from app.models import LoginAttempt

MAX_FAILED_ATTEMPTS = 3
LOCKOUT_DURATION = timedelta(minutes=10)


def utcnow() -> datetime:
    """Retorna UTC sem timezone para compatibilidade com SQLite DateTime."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def active_lockout(db: Session, email: str) -> LoginAttempt | None:
    attempt = db.query(LoginAttempt).filter(LoginAttempt.email == email).first()
    if attempt is None or attempt.locked_until is None:
        return None

    if attempt.locked_until > utcnow():
        return attempt

    # O período terminou: uma nova sequência de tentativas pode começar.
    attempt.failed_attempts = 0
    attempt.locked_until = None
    db.commit()
    return None


def register_failed_attempt(db: Session, email: str) -> None:
    attempt = db.query(LoginAttempt).filter(LoginAttempt.email == email).first()
    if attempt is None:
        attempt = LoginAttempt(email=email, failed_attempts=0)
        db.add(attempt)

    attempt.failed_attempts += 1
    if attempt.failed_attempts >= MAX_FAILED_ATTEMPTS:
        attempt.locked_until = utcnow() + LOCKOUT_DURATION
    db.commit()


def clear_failed_attempts(db: Session, email: str) -> None:
    attempt = db.query(LoginAttempt).filter(LoginAttempt.email == email).first()
    if attempt is not None:
        db.delete(attempt)
        db.commit()


def retry_after_seconds(attempt: LoginAttempt) -> int:
    remaining = attempt.locked_until - utcnow()
    return max(1, ceil(remaining.total_seconds()))
