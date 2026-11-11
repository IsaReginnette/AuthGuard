
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import User
from app.schemas import UserCreate, UserResponse
from app.security import hash_password

Base.metadata.create_all(bind=engine)

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
