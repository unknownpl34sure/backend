from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import get_current_user
from app.models import User
from app.s3 import upload_file_to_s3, get_file_url, delete_file_from_s3
from app import crud
from app.schemas import UserUpdate
from app.database import get_db

router = APIRouter()

@router.post("/upload/avatar")
async def upload_avatar(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    if file.content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, GIF, WEBP images are allowed"
        )

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 5MB"
        )

    if current_user.avatar_id:
        await delete_file_from_s3(current_user.avatar_id)

    file_id = await upload_file_to_s3(file, "avatars")

    await crud.update_user(
        db,
        current_user.id,
        UserUpdate(avatar_id=file_id)
    )

    return {
        "avatar_id": file_id,
        "url": await get_file_url(file_id)
    }

@router.get("/avatar/{user_id}")
async def get_avatar_url(
        user_id: int,
        db: AsyncSession = Depends(get_db)
):
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.avatar_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )

    return {
        "avatar_id": user.avatar_id,
        "url": await get_file_url(user.avatar_id)
    }