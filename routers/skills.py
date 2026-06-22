from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import crud, schemas
from app.models import User
from app.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.SkillOut)
async def create_skill(
        skill_data: schemas.SkillCreate,
        db: AsyncSession = Depends(get_db)
):
    existing = await crud.get_skill_by_name(db, skill_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill already exists"
        )

    new_skill = await crud.create_skill(db, skill_data.name)
    return new_skill

@router.get("/", response_model=list[schemas.SkillOut])
async def get_all_skills(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    skills = await crud.get_all_skills(db, skip, limit)
    return skills

@router.get("/my", response_model=list[schemas.SkillOut])
async def get_my_skills(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    skills = await crud.get_user_skills(db, current_user.id)
    return skills

@router.post("/my", response_model=list[schemas.SkillOut])
async def add_skills_to_me(
        skill_data: schemas.UserSkillAdd,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    all_skills = await crud.get_all_skills(db)
    existing_ids = {s.id for s in all_skills}

    for skill_id in skill_data.skill_ids:
        if skill_id not in existing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill with id {skill_id} not found"
            )

    await crud.add_skills_to_user(db, current_user.id, skill_data.skill_ids)

    skills = await crud.get_user_skills(db, current_user.id)
    return skills

@router.delete("/my/{skill_id}")
async def remove_skill_from_me(
        skill_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    success = await crud.remove_skill_from_user(db, current_user.id, skill_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found for this user"
        )
    return {"message": "Skill removed successfully"}

@router.get("/user/{user_id}", response_model=list[schemas.SkillOut])
async def get_user_skills_by_id(
        user_id: int,
        db: AsyncSession = Depends(get_db)
):
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    skills = await crud.get_user_skills(db, user_id)
    return skills