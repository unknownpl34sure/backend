from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, AsyncSessionLocal
from app import crud, schemas
from app.models import User
from app.auth import get_current_user, get_user_from_token
from app.ws_manager import manager


router = APIRouter()


def _serialize_message(message) -> dict:
    return {
        "id": message.id,
        "chat_id": message.chat_id,
        "sender_id": message.sender_id,
        "text": message.text,
        "image_id": message.image_id,
        "image_url": message.image_url,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


@router.websocket("/ws/{chat_id}")
async def chat_websocket(websocket: WebSocket, chat_id: int, token: str | None = None):
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    async with AsyncSessionLocal() as db:
        user = await get_user_from_token(token, db)
        if user is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        chat = await crud.get_chat_by_id(db, chat_id)
        if not chat or (
            chat.initiator_id != user.id and chat.receiver_id != user.id
        ):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await manager.connect(chat_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            text = (data.get("text") or "").strip() or None
            image_id = data.get("image_id") or None
            if not text and not image_id:
                continue

            try:
                async with AsyncSessionLocal() as db:
                    message = await crud.create_message(
                        db, chat_id, user.id, text, image_id
                    )
                    payload = _serialize_message(message)
            except Exception as e:
                print(f"Ошибка сохранения сообщения: {e}")
                await websocket.send_json({"error": "Не удалось сохранить сообщение"})
                continue

            await manager.broadcast(chat_id, payload)
    except WebSocketDisconnect:
        manager.disconnect(chat_id, websocket)
    except Exception as e:
        print(f"Ошибка WebSocket: {e}")
        manager.disconnect(chat_id, websocket)

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

    text = (message_data.text or "").strip() or None
    if not text and not message_data.image_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message must contain text or an image"
        )

    message = await crud.create_message(
        db, chat_id, current_user.id, text, message_data.image_id
    )
    await manager.broadcast(chat_id, _serialize_message(message))
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