from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import User, UserSession
from app.schemas import UserCreate, UserResponse, LoginRequest, LoginResponse
from app.security import hash_password, verify_password, DUMMY_HASH
from app.session_auth import create_session, get_session_user, SESSION_TTL_SECONDS
from app.lockout import begin_login_transaction, is_locked, record_failed_login, clear_failed_logins

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
    # SQLite: impede condição de corrida entre tentativas simultâneas de login.
    begin_login_transaction(db)
    if is_locked(db, credentials.email):
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de acesso. Tente novamente mais tarde.",
        )

    user = db.query(User).filter(User.email == credentials.email).first()
    stored_hash = user.hashed_password if user is not None else DUMMY_HASH
    password_matches = verify_password(credentials.password, stored_hash)
    if user is None or not password_matches:
        blocked = record_failed_login(db, credentials.email)
        if blocked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas de acesso. Tente novamente mais tarde.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    clear_failed_logins(db, credentials.email)
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
