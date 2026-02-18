"""
Matches API Module

Provides endpoints for creating, browsing matches previously created.
"""

import re
import html
import logging

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from database import get_db
from models import Match, Teacher, MatchSetting


# Pydantic Models


class MatchCreate(BaseModel):
    title: str = Field(..., description="Title of the match")
    match_set_id: int = Field(..., description="ID of the parent Match Setting")
    creator_id: int = Field(..., description="ID of the teacher creating this match")
    difficulty_level: int = Field(..., description="Difficulty level", ge=0, le=10)
    review_number: int = Field(..., description="Number of reviews", ge=1, le=100)
    duration_phase1: int = Field(..., description="Estimated duration of phase 1 in minutes", ge=1)
    duration_phase2: int = Field(..., description="Estimated duration of phase 2 in minutes", ge=1)

class MatchResponse(BaseModel):
    match_id: int = Field(..., description="Unique identifier for the match")
    title: str = Field(..., description="Title of the match")
    match_set_id: int = Field(..., description="ID of the parent Match Setting")
    creator_id: int = Field(..., description="ID of the teacher")
    difficulty_level: int = Field(..., description="Difficulty level")
    review_number: int = Field(..., description="Number of reviews")
    duration_phase1: int = Field(..., description="Estimated duration of phase 1 in minutes")
    duration_phase2: int = Field(..., description="Estimated duration of phase 2 in minutes")


# Router


router = APIRouter(prefix="/api", tags=["matches"])

# Endpoints


@router.post(
    "/matches",
    response_model=MatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new match",
    description="Allows a teacher to create a new match based on a match setting.",
)
async def create_match(
    match: MatchCreate, db: Session = Depends(get_db)
) -> MatchResponse:
    """
    Create a new match resource in the database.

    Args:
        match: The request body containing match data.
        db: The SQLAlchemy database session.

    Returns:
        The newly created match object.

    Raises:
        HTTPException (400): If the 'creator_id' or 'match_set_id' does not exist.
        HTTPException (500): On database operation failure.
    """

    # Check if the creator (teacher) exists
    teacher = db.query(Teacher).filter(Teacher.teacher_id == match.creator_id).first()
    # Check if the match setting exists
    setting = (
        db.query(MatchSetting)
        .filter(MatchSetting.match_set_id == match.match_set_id)
        .first()
    )

    if not teacher or not setting:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid creator_id or match_set_id.",
        )

    try:
        # Create a new ORM object
        new_match = Match(**match.model_dump())

        # Add to the session and commit
        db.add(new_match)
        db.commit()

        # Refresh the object to get the new 'match_id' from the DB
        db.refresh(new_match)

        return new_match

    except Exception as e:
        db.rollback()

        logging.error(f"Failed to create match: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while creating the match.",
        )


@router.get(
    "/matches",
    response_model=List[MatchResponse],
    summary="Browse all matches",
    description="Retrieve all available matches.",
)
async def get_matches(db: Session = Depends(get_db)) -> List[MatchResponse]:
    """
    Browse all available matches from the database.
    """
    return db.query(Match).all()


@router.get(
    "/matches/{match_id}",
    response_model=MatchResponse,
    summary="Get a single match",
    description="Retrieve a single match by its ID.",
)
async def get_match(match_id: int, db: Session = Depends(get_db)) -> MatchResponse:
    """
    Retrieve a single match by ID.
    """
    match = db.query(Match).filter(Match.match_id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found.",
        )
    return match


@router.put(
    "/matches/{match_id}",
    response_model=MatchResponse,
    summary="Update a match",
    description="Update an existing match.",
)
async def update_match(
    match_id: int, match: MatchCreate, db: Session = Depends(get_db)
) -> MatchResponse:
    """
    Update an existing match.
    """
    existing = db.query(Match).filter(Match.match_id == match_id).first()
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found.",
        )

    teacher = db.query(Teacher).filter(Teacher.teacher_id == match.creator_id).first()
    setting = (
        db.query(MatchSetting)
        .filter(MatchSetting.match_set_id == match.match_set_id)
        .first()
    )
    if not teacher or not setting:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid creator_id or match_set_id.",
        )

    try:
        for key, value in match.model_dump().items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to update match: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while updating the match.",
        )


@router.delete(
    "/matches/{match_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a match",
    description="Delete an existing match.",
)
async def delete_match(match_id: int, db: Session = Depends(get_db)):
    """
    Delete an existing match.
    """
    existing = db.query(Match).filter(Match.match_id == match_id).first()
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found.",
        )

    try:
        db.delete(existing)
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to delete match: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while deleting the match.",
        )


@router.post(
    "/matches/{match_id}/clone",
    response_model=MatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone a match",
    description="Clone an existing match.",
)
async def clone_match(match_id: int, db: Session = Depends(get_db)) -> MatchResponse:
    """
    Clone an existing match.
    """
    original = db.query(Match).filter(Match.match_id == match_id).first()
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found.",
        )

    try:
        cloned = Match(
            title=f"{original.title} (Clone)",
            match_set_id=original.match_set_id,
            creator_id=original.creator_id,
            difficulty_level=original.difficulty_level,
            review_number=original.review_number,
            duration_phase1=original.duration_phase1,
            duration_phase2=original.duration_phase2,
        )
        db.add(cloned)
        db.commit()
        db.refresh(cloned)
        return cloned
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to clone match: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while cloning the match.",
        )

