import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import crud, schemas
from app.models import User
from app.auth import get_current_user
from app.s3 import get_file_url


router = APIRouter()

@router.get("/my", response_model=list[schemas.ChatListOut])
async def get_my_chats(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    chats = await crud.get_user_chats(db, current_user.id)

    result = []
    for chat in chats:
        messages = await crud.get_chat_messages(db, chat.id, limit=1)
        last_message = messages[0].text if messages else None

        kwork_photo = None
        if chat.kwork and chat.kwork.photo_ids:
            try:
                photo_ids = json.loads(chat.kwork.photo_ids)
                if photo_ids:
                    kwork_photo = get_file_url(photo_ids[0])
            except (ValueError, TypeError):
                pass

        result.append({
            "id": chat.id,
            "initiator_id": chat.initiator_id,
            "receiver_id": chat.receiver_id,
            "kwork_id": chat.kwork_id,
            "kwork_title": chat.kwork.title if chat.kwork else None,
            "kwork_photo": kwork_photo,
            "created_at": chat.created_at,
            "last_message": last_message
        })

    return result


@router.get("/{chat_id}", response_model=schemas.ChatOut)
async def get_chat(
        chat_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    chat = await crud.get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    if chat.initiator_id != current_user.id and chat.receiver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat"
        )

    return chat