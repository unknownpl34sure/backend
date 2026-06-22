from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import crud, schemas
from app.models import User
from app.auth import get_current_user

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