from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, LoginRequest, LoginResponse
from app.security import hash_password, verify_password
from app.session_auth import create_session, get_session_user, SESSION_TTL_SECONDS
from app.lockout import (
    active_lockout,
    clear_failed_attempts,
    register_failed_attempt,
    retry_after_seconds,
)

# Hash dummy com o mesmo algoritmo/custo para evitar diferença de tempo
# entre e-mail cadastrado e não cadastrado.
DUMMY_PASSWORD_HASH = hash_password("AuthGuard-dummy-password-never-used")

Base.metadata.create_all(bind=engine)

bearer_scheme = HTTPBearer(auto_error=False)

app = FastAPI(
    title="AuthGuard API",
    description="API de autenticação e cadastro seguro de usuários",
    version="1.0.0"
)


@app.get("/")
def home():
    return {"message": "AuthGuard API está funcionando!"}


@app.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível realizar o cadastro."
        )

    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    lockout = active_lockout(db, credentials.email)
    if lockout is not None:
        retry_after = retry_after_seconds(lockout)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Conta temporariamente bloqueada. Tente novamente após o período de bloqueio.",
            headers={"Retry-After": str(retry_after)},
        )

    user = db.query(User).filter(User.email == credentials.email).first()
    if user is None:
        # Executa Argon2 também para usuários inexistentes, reduzindo
        # a possibilidade de inferir a existência do e-mail pelo tempo.
        verify_password(credentials.password, DUMMY_PASSWORD_HASH)
        register_failed_attempt(db, credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(credentials.password, user.hashed_password):
        register_failed_attempt(db, credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    clear_failed_attempts(db, credentials.email)
    token = create_session(db, user)
    return LoginResponse(access_token=token, expires_in=SESSION_TTL_SECONDS)


@app.get("/me", response_model=UserResponse)
def me(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    user = get_session_user(db, credentials.credentials) if credentials else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
