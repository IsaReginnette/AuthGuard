"""Bloqueio persistente por identificador, com incremento atômico no SQLite."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from sqlalchemy import and_, case, text
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models import LoginLockout

MAX_FAILURES = 3
LOCK_MINUTES = 10


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def email_key(email: str) -> str:
    return sha256(email.strip().casefold().encode("utf-8")).hexdigest()


def begin_login_transaction(db: Session) -> None:
    """Serializa logins no banco SQLite para evitar corrida no bloqueio."""
    db.execute(text("BEGIN IMMEDIATE"))


def is_locked(db: Session, email: str) -> bool:
    state = db.get(LoginLockout, email_key(email))
    return bool(state and state.locked_until and state.locked_until > utcnow())


def record_failed_login(db: Session, email: str) -> bool:
    """UPSERT atômico; a terceira falha inicia 10 minutos de bloqueio."""
    now = utcnow()
    table = LoginLockout.__table__
    active = table.c.locked_until > now
    expired = and_(table.c.locked_until.is_not(None), table.c.locked_until <= now)
    next_count = case(
        (active, table.c.failed_attempts),
        (expired, 1),
        else_=table.c.failed_attempts + 1,
    )
    next_locked_until = case(
        (active, table.c.locked_until),
        (next_count >= MAX_FAILURES, now + timedelta(minutes=LOCK_MINUTES)),
        else_=None,
    )
    statement = sqlite_insert(table).values(
        email_key=email_key(email), failed_attempts=1, locked_until=None,
    ).on_conflict_do_update(
        index_elements=[table.c.email_key],
        set_={"failed_attempts": next_count, "locked_until": next_locked_until},
    )
    db.execute(statement)
    # A transação já foi iniciada com BEGIN IMMEDIATE no endpoint de login.
    state = db.get(LoginLockout, email_key(email), populate_existing=True)
    blocked = bool(state and state.locked_until and state.locked_until > now)
    db.commit()
    return blocked


def clear_failed_logins(db: Session, email: str) -> None:
    # O commit fica com create_session, mantendo reset e sessão na mesma transação.
    db.query(LoginLockout).filter(LoginLockout.email_key == email_key(email)).delete()
