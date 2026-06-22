from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_db
from app import crud, schemas, auth
from app.models import User
from app.hashing import verify_password
from app.schemas import UserUpdate

router = APIRouter()

@router.post("/register", response_model=schemas.UserOut)
async def register_user(
        user_data: schemas.UserCreate,
        db: AsyncSession = Depends(get_db)
):

    existing_user = await crud.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    existing_email = await crud.get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user = await crud.create_user(db, user_data)
    return new_user


@router.post("/login", response_model=schemas.Token)
async def login_user(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    user = await crud.get_user_by_username(db, form_data.username)
    if not user:
        raise HTTPException(401, "Incorrect username or password")

    if not verify_password(
            form_data.password,
            user.password_hash,
            user.password_salt
    ):
        raise HTTPException(401, "Incorrect username or password")

    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserOut)
async def get_current_user_route(
        current_user: User = Depends(auth.get_current_user)
):
    return current_user

@router.patch("/me", response_model=schemas.UserOut)
async def update_profile(
    user_data: UserUpdate,
    current_user: User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated_user = await crud.update_user(db, current_user.id, user_data)
    return updated_user