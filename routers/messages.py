from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import crud, schemas
from app.models import User
from app.auth import get_current_user

router = APIRouter()

@router.post("/{chat_id}", response_model=schemas.MessageOut)
async def send_message(
        chat_id: int,
        message_data: schemas.MessageCreate,
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

    message = await crud.create_message(db, chat_id, current_user.id, message_data.text)
    return message

@router.get("/{chat_id}", response_model=list[schemas.MessageOut])
async def get_messages(
        chat_id: int,
        limit: int = 50,
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

    messages = await crud.get_chat_messages(db, chat_id, limit)
    return messages