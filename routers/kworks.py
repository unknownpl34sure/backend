from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import crud, schemas
from app.models import User
from app.auth import get_current_user
from app.s3 import delete_file_from_s3
import json


router = APIRouter()

@router.post("/", response_model=schemas.KworkCreatedResponse)
async def create_kwork(
    kwork_data: schemas.KworkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_kwork = await crud.create_kwork(db, kwork_data, current_user.id)
    return {"id": new_kwork.id}

@router.get("/", response_model=list[schemas.KworkOut])
async def get_kworks(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    return await crud.get_kworks(db, skip, limit)

@router.get("/{kwork_id}", response_model=schemas.KworkOut)
async def get_kwork(
    kwork_id: int,
    db: AsyncSession = Depends(get_db)
):
    kwork = await crud.get_kwork_by_id(db, kwork_id)
    if not kwork:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kwork not found"
        )
    return kwork

@router.patch("/{kwork_id}/status", response_model=schemas.KworkOut)
async def update_kwork_status(
        kwork_id: int,
        status_data: schemas.KworkStatusUpdate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    kwork = await crud.get_kwork_by_id(db, kwork_id)
    if not kwork:
        raise HTTPException(status_code=404, detail="Kwork not found")

    if kwork.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only update your own kworks"
        )

    if status_data.client_id:
        client = await crud.get_user_by_id(db, status_data.client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

    updated_kwork = await crud.update_kwork_status(
        db,
        kwork_id,
        status_data.status,
        status_data.client_id
    )
    return updated_kwork

@router.post("/{kwork_id}/complete", response_model=schemas.KworkOut)
async def complete_kwork(
        kwork_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Создатель объявления подтверждает выполнение: стоимость списывается с его баланса."""
    kwork = await crud.get_kwork_by_id(db, kwork_id)
    if not kwork:
        raise HTTPException(status_code=404, detail="Kwork not found")

    if kwork.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Только создатель объявления может подтвердить выполнение"
        )

    if kwork.status == schemas.KworkStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Объявление уже выполнено")

    if kwork.client_id is None:
        raise HTTPException(
            status_code=400,
            detail="У задания ещё нет исполнителя — некому переводить оплату"
        )

    if (current_user.balance or 0) < kwork.price:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Недостаточно средств. Нужно {kwork.price} ₽, "
                f"на балансе {current_user.balance or 0} ₽. Пополните баланс."
            )
        )

    updated_kwork, error = await crud.complete_kwork_with_payment(db, kwork, current_user)

    if error == "no_worker":
        raise HTTPException(
            status_code=400,
            detail="У задания ещё нет исполнителя — некому переводить оплату"
        )
    if error == "insufficient":
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Недостаточно средств. Нужно {kwork.price} ₽, "
                f"на балансе {current_user.balance or 0} ₽. Пополните баланс."
            )
        )

    return updated_kwork


@router.post("/{kwork_id}/order")
async def order_kwork(
        kwork_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    kwork = await crud.get_kwork_by_id(db, kwork_id)
    if not kwork:
        raise HTTPException(status_code=404, detail="Kwork not found")

    if kwork.user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot order your own kwork"
        )

    if kwork.client_id is not None:
        raise HTTPException(
            status_code=400,
            detail="This kwork is already taken"
        )

    updated_kwork, chat = await crud.order_kwork(db, kwork_id, current_user.id)

    return {
        "kwork_id": updated_kwork.id,
        "status": updated_kwork.status.value,
        "client_id": updated_kwork.client_id,
        "chat_id": chat.id if chat else None,
    }


@router.delete("/{kwork_id}")
async def delete_kwork(
        kwork_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    kwork = await crud.get_kwork_by_id(db, kwork_id)
    if not kwork:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kwork not found"
        )

    if kwork.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own kworks"
        )

    if kwork.photo_ids:
        try:
            photo_ids = json.loads(kwork.photo_ids) if isinstance(kwork.photo_ids, str) else kwork.photo_ids
            for photo_id in photo_ids:
                await delete_file_from_s3(photo_id)

        except:
            pass

    await crud.delete_kwork(db, kwork_id)

    return {"message": "Kwork deleted successfully"}