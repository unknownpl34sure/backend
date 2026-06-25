from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import get_current_user
from app.models import User
from app.s3 import upload_file_to_s3, get_file_url, delete_file_from_s3
from app import crud
from app.schemas import UserUpdate
from app.database import get_db
import json


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
        "url": get_file_url(file_id)
    }

@router.post("/upload/banner")
async def upload_banner(
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
    if size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 10MB"
        )

    if current_user.banner_id:
        await delete_file_from_s3(current_user.banner_id)

    file_id = await upload_file_to_s3(file, "banners")

    await crud.update_user(
        db,
        current_user.id,
        UserUpdate(banner_id=file_id)
    )

    return {
        "banner_id": file_id,
        "url": get_file_url(file_id)
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
        "url": get_file_url(user.avatar_id)
    }

@router.post("/upload/portfolio/{portfolio_id}")
async def upload_portfolio_image(
        portfolio_id: int,
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    portfolio_item = await crud.get_portfolio_by_id(db, portfolio_id)
    if not portfolio_item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")

    if portfolio_item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your portfolio item")

    if file.content_type not in ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]:
        raise HTTPException(400, "Only JPEG, JPG, PNG, GIF, WEBP images are allowed")

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > 10 * 1024 * 1024:
        raise HTTPException(400, "File size must be less than 10MB")

    if portfolio_item.photo_id:
        await delete_file_from_s3(portfolio_item.photo_id)

    file_id = await upload_file_to_s3(file, "portfolio")

    updated_item = await crud.update_portfolio_photo(db, portfolio_id, file_id)

    return {
        "id": updated_item.id,
        "photo_id": file_id,
        "photo_url": get_file_url(file_id)
    }

@router.post("/upload/chat/{chat_id}")
async def upload_chat_image(
        chat_id: int,
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    chat = await crud.get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if chat.initiator_id != current_user.id and chat.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not a member of this chat")

    if file.content_type not in ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]:
        raise HTTPException(400, "Only JPEG, JPG, PNG, GIF, WEBP images are allowed")

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > 10 * 1024 * 1024:
        raise HTTPException(400, "File size must be less than 10MB")

    file_id = await upload_file_to_s3(file, "chats")

    return {
        "image_id": file_id,
        "image_url": get_file_url(file_id)
    }


@router.post("/upload/kwork/{kwork_id}")
async def upload_kwork_image(
        kwork_id: int,
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    kwork = await crud.get_kwork_by_id(db, kwork_id)
    if not kwork:
        raise HTTPException(status_code=404, detail="Kwork not found")

    if kwork.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only add photos to your own kworks")

    if file.content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        raise HTTPException(400, "Only JPEG, PNG, GIF, WEBP images are allowed")

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > 10 * 1024 * 1024:
        raise HTTPException(400, "File size must be less than 10MB")

    file_id = await upload_file_to_s3(file, "kworks")

    photo_ids = json.loads(kwork.photo_ids) if kwork.photo_ids else []
    photo_ids.append(file_id)

    await crud.update_kwork_photos(db, kwork_id, json.dumps(photo_ids))

    return {
        "photo_id": file_id,
        "photo_url": get_file_url(file_id)
    }