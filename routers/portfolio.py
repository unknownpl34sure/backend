from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import crud, schemas
from app.models import User
from app.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.PortfolioOut)
async def create_portfolio_item(
        portfolio_data: schemas.PortfolioCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    new_item = await crud.create_portfolio(db, portfolio_data, current_user.id)
    return new_item

@router.get("/my", response_model=list[schemas.PortfolioOut])
async def get_my_portfolio(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    items = await crud.get_user_portfolio(db, current_user.id)
    return items

@router.get("/user/{user_id}", response_model=list[schemas.PortfolioOut])
async def get_user_portfolio(
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    items = await crud.get_user_portfolio(db, user_id, skip, limit)
    return items

@router.get("/{portfolio_id}", response_model=schemas.PortfolioOut)
async def get_portfolio_item(
        portfolio_id: int,
        db: AsyncSession = Depends(get_db)
):
    item = await crud.get_portfolio_by_id(db, portfolio_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio item not found"
        )
    return item

@router.delete("/{portfolio_id}")
async def delete_portfolio_item(
        portfolio_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    item = await crud.get_portfolio_by_id(db, portfolio_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio item not found"
        )

    if item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own portfolio items"
        )

    await crud.delete_portfolio(db, portfolio_id)
    return {"message": "Portfolio item deleted successfully"}