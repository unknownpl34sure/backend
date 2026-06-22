from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import crud, schemas
from app.models import User
from app.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.ReviewOut)
async def create_review(
        review_data: schemas.ReviewCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    if review_data.target_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot review yourself"
        )

    target_user = await crud.get_user_by_id(db, review_data.target_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    existing_reviews = await crud.get_user_reviews(db, current_user.id)
    for review in existing_reviews:
        if review.target_id == review_data.target_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already reviewed this user"
            )

    new_review = await crud.create_review(db, review_data, current_user.id)
    return new_review

@router.get("/my", response_model=list[schemas.ReviewOut])
async def get_my_reviews(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    reviews = await crud.get_user_reviews(db, current_user.id)
    return reviews

@router.get("/user/{user_id}", response_model=list[schemas.ReviewOut])
async def get_user_reviews(
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

    reviews = await crud.get_reviews_for_user(db, user_id, skip, limit)
    return reviews

@router.get("/user/{user_id}/rating")
async def get_user_rating(
        user_id: int,
        db: AsyncSession = Depends(get_db)
):
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    stats = await crud.get_user_rating_stats(db, user_id)
    return {
        "user_id": user_id,
        "total_reviews": stats["total"],
        "positive": stats["positive"],
        "negative": stats["negative"],
        "rating_percent": stats["rating_percent"],
        "rating_display": f"{stats['rating_percent']}% positive"
    }