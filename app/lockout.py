"""Bloqueio temporário após tentativas consecutivas de login inválidas."""
from datetime import datetime, timedelta, timezone
from math import ceil

from sqlalchemy import case
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
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
    """Incrementa atomicamente para não perder falhas concorrentes no SQLite."""
    now = utcnow()
    next_count = LoginAttempt.failed_attempts + 1
    statement = sqlite_insert(LoginAttempt).values(
        email=email,
        failed_attempts=1,
        locked_until=None,
    )
    statement = statement.on_conflict_do_update(
        index_elements=[LoginAttempt.email],
        set_={
            "failed_attempts": next_count,
            "locked_until": case(
                (next_count >= MAX_FAILED_ATTEMPTS, now + LOCKOUT_DURATION),
                else_=LoginAttempt.locked_until,
            ),
        },
    )
    db.execute(statement)
    db.commit()


def clear_failed_attempts(db: Session, email: str) -> None:
    db.query(LoginAttempt).filter(LoginAttempt.email == email).delete()
    db.commit()


def retry_after_seconds(attempt: LoginAttempt) -> int:
    remaining = attempt.locked_until - utcnow()
    return max(1, ceil(remaining.total_seconds()))
