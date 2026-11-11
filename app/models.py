from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class UserSession(Base):
    """Sessões opacas: apenas o digest do token fica persistido."""
    __tablename__ = "user_sessions"

    token_hash = Column(String(64), primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)


class LoginLockout(Base):
    """Tentativas por identificador, inclusive quando o e-mail não existe."""
    __tablename__ = "login_lockouts"

    email_key = Column(String(64), primary_key=True)
    failed_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
