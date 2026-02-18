"""
Leaderboard API Module

Provides endpoints for:
- Getting the global leaderboard with paginated rankings
- Calculating total scores across all game sessions for all students
- Handling tied ranks correctly

Scoring System (after Phase 2):
- 50% implementation (based on tests passed)
- 50% reviews (correct error ID = 2x, correct confirm = 1x, wrong = -1x penalty, skip = 0)
"""

from typing import List, Optional, Dict, Tuple
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, case
from pydantic import BaseModel, Field
from collections import defaultdict

# Import ORM models
from models import (
    Student
)

from database import get_db
from student_results_api import _get_test_status

# ============================================================================
# Pydantic Response Models
# ============================================================================

class LeaderboardEntry(BaseModel):
    rank: int = Field(..., description="Rank position (tied ranks share same number)")
    student_id: int = Field(..., description="ID of the student")
    username: str = Field(..., description="Full name of the student")
    score: float = Field(..., description="Total score across all game sessions")


class CurrentUserRank(BaseModel):
    rank: int = Field(..., description="Current user's rank")
    position: int = Field(..., description="1-based position index in the full sorted leaderboard (accounts for ties)")
    score: float = Field(..., description="Current user's score")
    username: str = Field("", description="Current user's display name")
    student_id: int = Field(0, description="Current user's student ID")
    points_to_next_rank: Optional[float] = Field(None, description="Points needed to reach next rank (null if rank 1)")


class LeaderboardResponse(BaseModel):
    total_students: int = Field(..., description="Total number of students")
    total_pages: int = Field(..., description="Total number of pages")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of entries per page")
    leaderboard: List[LeaderboardEntry] = Field(..., description="Paginated leaderboard entries")
    current_user_rank: Optional[CurrentUserRank] = Field(None, description="Current user's rank info (if student_id provided)")



def _get_all_student_scores_from_db(db: Session) -> List[Tuple[int, str, float]]:
    """
    Get total scores for all students by summing pre-calculated session_scores
    from the student_join_game table.
    
    This is much more efficient than recalculating all scores on each request.
    Session scores should be calculated and saved after Phase 2 ends for each game.
    
    Args:
        db: Database session
    
    Returns:
        List of tuples (student_id, username, total_score) sorted by score descending
    """
    
    
    # Query students with their global score (now stored directly in student table)
    students = db.query(
        Student.student_id,
        Student.first_name,
        Student.last_name,
        Student.score
    ).all()
    
    student_scores = [
        (s.student_id, f"{s.first_name} {s.last_name}", float(s.score))
        for s in students
    ]
    
    # Sort by score descending, then by student_id ascending
    student_scores.sort(key=lambda x: (-x[2], x[0]))
    
    return student_scores


def _assign_ranks(student_scores: List[Tuple[int, str, float]]) -> List[LeaderboardEntry]:
    """
    Assign ranks to students, handling tied scores correctly.
    
    Args:
        student_scores: List of tuples (student_id, username, score) sorted by score
    
    Returns:
        List of LeaderboardEntry with proper rank assignments
    """
    leaderboard = []
    current_rank = 1
    for i, (student_id, username,  score) in enumerate(student_scores):
        # If this is not the first student and score is different from previous, update rank
        if i > 0 and score < student_scores[i - 1][2]:
            current_rank = i + 1
        
        leaderboard.append(LeaderboardEntry(
            rank=current_rank,
            student_id=student_id,
            username=username,
            score=score
        ))
    
    return leaderboard


def _find_points_to_next_rank(current_score: float, leaderboard: List[LeaderboardEntry]) -> Optional[float]:
    """
    Find the minimum points needed to reach the next rank.
    
    Optimized to find the closest higher score efficiently.
    
    Args:
        current_score: Current user's score
        leaderboard: Full leaderboard sorted by score descending
    
    Returns:
        Points needed to reach next rank, or None if already rank 1
    """
    min_diff = None
    
    for entry in leaderboard:
        if entry.score > current_score:
            diff = entry.score - current_score
            if min_diff is None or diff < min_diff:
                min_diff = diff
        else:
            # Leaderboard is sorted descending, no need to continue
            break
    
    return round(min_diff, 2) if min_diff is not None else None


# ============================================================================
# API Router
# ============================================================================

router = APIRouter(
    prefix="/api",
    tags=["Leaderboard"]
)


# ============================================================================
# Endpoint: Get Leaderboard
# ============================================================================

@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the global leaderboard",
    description="""
    Retrieves the global leaderboard showing all students ranked by total score.
    
    Features:
    - Pagination support (default 10 per page)
    - Tied scores share the same rank with proper skip logic
    - Optional current user rank information (always included even if not on current page)
    - Scores calculated from all game sessions
    - Optimized with bulk queries to avoid N+1 query problems
    """
)
def get_leaderboard(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of entries per page"),
    student_id: Optional[int] = Query(None, description="Current user's student ID for personalized rank info"),
    db: Session = Depends(get_db)
) -> LeaderboardResponse:
    """
    Get the global leaderboard with pagination.
    
    PERFORMANCE NOTES:
    - Uses optimized bulk queries to avoid N+1 query problems
    - Single database round-trip for all student data
    - Efficient in-memory aggregation and sorting
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of entries per page
        student_id: Optional student ID for current user rank info
        db: Database session
    
    Returns:
        LeaderboardResponse with paginated leaderboard and optional current user rank
    """
    
    try:
        student_scores = _get_all_student_scores_from_db(db)

        full_leaderboard = _assign_ranks(student_scores)


        # Calculate pagination
        total_students = len(full_leaderboard)
        total_pages = (total_students + page_size - 1) // page_size  # Ceiling division
        
        # Get paginated slice
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_leaderboard = full_leaderboard[start_idx:end_idx]
        
        # Get current user rank info if student_id provided
        current_user_rank_info = None
        if student_id is not None:
            # Find the student in the full leaderboard (O(n) but unavoidable)
            for idx, entry in enumerate(full_leaderboard):
                if entry.student_id == student_id:
                    # Find points to next rank efficiently
                    points_to_next = None
                    if entry.rank > 1:
                        points_to_next = _find_points_to_next_rank(entry.score, full_leaderboard)
                    
                    current_user_rank_info = CurrentUserRank(
                        rank=entry.rank,
                        position=idx + 1,  # 1-based position
                        score=entry.score,
                        username=entry.username,
                        student_id=entry.student_id,
                        points_to_next_rank=points_to_next
                    )
                    break
        
        return LeaderboardResponse(
            total_students=total_students,
            total_pages=total_pages,
            page=page,
            page_size=page_size,
            leaderboard=paginated_leaderboard,
            current_user_rank=current_user_rank_info
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch leaderboard: {str(e)}"
        )
