from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from models import (
    Badge,
    StudentBadge,
    StudentReviewVote,
    StudentAssignedReview,
    StudentSolution,
    StudentJoinGame,
    MatchesForGame,
    Match,
    Test,
    VoteType
)
from database import get_db
from leaderboard_api import _assign_ranks
from student_results_api import get_game_session_scores_list

router = APIRouter(
    prefix="/api/badges",
    tags=["Badges"]
)

# ============================================================================
# Pydantic Models
# ============================================================================

class BadgeResponse(BaseModel):
    badge_id: int
    name: str
    description: str
    icon_path: Optional[str]
    criteria_type: str
    earned_at: Optional[datetime] = None

class AssignBadgeRequest(BaseModel):
    student_id: int
    badge_name: str
    game_session_id: Optional[int] = None

# ============================================================================
# Endpoints
# ============================================================================

@router.get("/student/{student_id}", response_model=List[BadgeResponse])
def get_student_badges(student_id: int, db: Session = Depends(get_db)):
    """
    Get all badges earned by a student.
    """
    results = db.query(Badge, StudentBadge.earned_at)\
        .join(StudentBadge, Badge.badge_id == StudentBadge.badge_id)\
        .filter(StudentBadge.student_id == student_id)\
        .all()
    
    badges = []
    for badge, earned_at in results:
        badges.append(BadgeResponse(
            badge_id=badge.badge_id,
            name=badge.name,
            description=badge.description,
            icon_path=badge.icon_path,
            criteria_type=badge.criteria_type,
            earned_at=earned_at
        ))
    return badges


@router.post("/assign", status_code=status.HTTP_201_CREATED)
def assign_badge(request: AssignBadgeRequest, db: Session = Depends(get_db)):
    """
    Manually assign a badge to a student (Internal/Admin use).
    """
    badge = db.query(Badge).filter(Badge.name == request.badge_name).first()
    if not badge:
        raise HTTPException(status_code=404, detail=f"Badge '{request.badge_name}' not found")
    
    # Check if already assigned
    existing = db.query(StudentBadge).filter(
        StudentBadge.student_id == request.student_id,
        StudentBadge.badge_id == badge.badge_id
    ).first()
    
    if existing:
        return {"message": "Badge already assigned"}
    
    new_badge = StudentBadge(
        student_id=request.student_id,
        badge_id=badge.badge_id,
        game_session_id=request.game_session_id,
        earned_at=datetime.now(timezone.utc)
    )
    db.add(new_badge)
    db.commit()
    return {"message": f"Badge '{badge.name}' assigned successfully"}


# ============================================================================
# Evaluation Logic
# ============================================================================

def _award_badge_if_not_exists(db: Session, student_id: int, badge_name: str, game_session_id: Optional[int] = None):
    badge = db.query(Badge).filter(Badge.name == badge_name).first()
    if not badge:
        return  # Should probably log this error
    
    exists = db.query(StudentBadge).filter(
        StudentBadge.student_id == student_id,
        StudentBadge.badge_id == badge.badge_id
    ).first()
    
    if not exists:
        try:
            new_badge = StudentBadge(
                student_id=student_id,
                badge_id=badge.badge_id,
                game_session_id=game_session_id,
                earned_at=datetime.now(timezone.utc)
            )
            db.add(new_badge)
            db.flush()  # Flush immediately to catch duplicates early
        except IntegrityError:
            db.rollback()  # Rollback the failed insert, badge already exists


def _count_perfect_sessions(db: Session, student_id: int) -> int:
    """
    Count the number of game sessions where the student passed all teacher's tests.
    A session is "perfect" if the student's passed_test count equals the total
    number of teacher tests (public + private) for the match.
    Note: Each student plays only ONE match per game session.
    """
    # Get all sessions the student participated in with their assigned match
    student_sessions = db.query(StudentJoinGame.game_id, StudentJoinGame.assigned_match_id).filter(
        StudentJoinGame.student_id == student_id,
        StudentJoinGame.assigned_match_id.isnot(None)
    ).all()
    
    perfect_count = 0
    
    for game_id, match_id in student_sessions:
        # Find the match_for_game_id for this match in this game session
        match_for_game = db.query(MatchesForGame.match_for_game_id).filter(
            MatchesForGame.match_id == match_id,
            MatchesForGame.game_id == game_id
        ).first()
        
        if not match_for_game:
            continue
        
        # Get the match to find its match_set_id
        match = db.query(Match).filter(Match.match_id == match_id).first()
        if not match:
            continue
        
        # Count total teacher tests (public + private) for this match_setting
        total_tests = db.query(func.count(Test.test_id)).filter(
            Test.match_set_id == match.match_set_id
        ).scalar() or 0
        
        if total_tests == 0:
            continue
        
        # Get the student's solution and check if passed_test equals total tests
        solution = db.query(StudentSolution).filter(
            StudentSolution.student_id == student_id,
            StudentSolution.match_for_game_id == match_for_game.match_for_game_id
        ).first()
        
        if solution and solution.passed_test >= total_tests:
            perfect_count += 1
    
    return perfect_count


def _count_flawless_sessions(db: Session, student_id: int) -> int:
    """
    Count the number of game sessions where the student finished perfectly without any mistakes.
    A session is "flawless" if:
    1. The student passed all teacher's tests (passed_test equals total tests)
    2. Their solution received no valid "incorrect" votes from reviewers
    Note: Each student plays only ONE match per game session.
    """
    # Get all sessions the student participated in with their assigned match
    student_sessions = db.query(StudentJoinGame.game_id, StudentJoinGame.assigned_match_id).filter(
        StudentJoinGame.student_id == student_id,
        StudentJoinGame.assigned_match_id.isnot(None)
    ).all()
    
    flawless_count = 0
    
    for game_id, match_id in student_sessions:
        # Find the match_for_game_id for this match in this game session
        match_for_game = db.query(MatchesForGame.match_for_game_id).filter(
            MatchesForGame.match_id == match_id,
            MatchesForGame.game_id == game_id
        ).first()
        
        if not match_for_game:
            continue
        
        # Get the match to find its match_set_id
        match = db.query(Match).filter(Match.match_id == match_id).first()
        if not match:
            continue
        
        # Count total teacher tests (public + private) for this match_setting
        total_tests = db.query(func.count(Test.test_id)).filter(
            Test.match_set_id == match.match_set_id
        ).scalar() or 0
        
        if total_tests == 0:
            continue
        
        # Get the student's solution and check if passed_test equals total tests
        solution = db.query(StudentSolution).filter(
            StudentSolution.student_id == student_id,
            StudentSolution.match_for_game_id == match_for_game.match_for_game_id
        ).first()
        
        if not solution or solution.passed_test < total_tests:
            continue
        
        # Check if the student's solution received any valid "incorrect" votes
        # This means reviewers found bugs in their code
        incorrect_vote = db.query(StudentReviewVote).join(StudentAssignedReview).filter(
            StudentAssignedReview.assigned_solution_id == solution.solution_id,
            StudentReviewVote.vote == VoteType.incorrect,
            StudentReviewVote.valid == True
        ).first()
        
        if not incorrect_vote:
            flawless_count += 1
    
    return flawless_count


@router.post("/evaluate/{game_session_id}")
def evaluate_badges(game_session_id: int, db: Session = Depends(get_db)):
    # 1. Hall of Fame (Top-N) - Based on GLOBAL leaderboard position
    scores = get_game_session_scores_list(db, game_session_id)
    ranked_students = _assign_ranks(scores)
    
    for entry in ranked_students:
        student_id = entry.student_id
        rank = entry.rank
        
        if rank == 1:
            _award_badge_if_not_exists(db, student_id, "Champion", game_session_id)
        if rank <= 3:
            _award_badge_if_not_exists(db, student_id, "Podium Master", game_session_id)
        if rank <= 5:
            _award_badge_if_not_exists(db, student_id, "Elite Performer", game_session_id)
        if rank <= 10:
            _award_badge_if_not_exists(db, student_id, "Rising Star", game_session_id)

    # 2. Bug Hunter
    # Count valid 'incorrect' votes (which means reviewer found a bug in someone else's code)
    bug_counts = db.query(
        StudentAssignedReview.student_id,
        func.count(StudentReviewVote.vote)
    ).join(StudentReviewVote)\
    .filter(
        StudentReviewVote.vote == VoteType.incorrect,
        StudentReviewVote.valid == True
    ).group_by(StudentAssignedReview.student_id).all()
    
    for student_id, count in bug_counts:
        if count >= 100:
            _award_badge_if_not_exists(db, student_id, "Bug Whisperer")
        if count >= 50:
            _award_badge_if_not_exists(db, student_id, "Bug Exterminator")
        if count >= 20:
            _award_badge_if_not_exists(db, student_id, "Bug Slayer")
        if count >= 10:
            _award_badge_if_not_exists(db, student_id, "Bug Tracker")
        if count >= 5:
            _award_badge_if_not_exists(db, student_id, "Bug Hunter")

    # 3. Review Master (Cumulative Up-voting correct answers)
    # Count valid 'correct' votes (reviewer correctly identified working code)
    review_counts = db.query(
        StudentAssignedReview.student_id,
        func.count(StudentReviewVote.vote)
    ).join(StudentReviewVote)\
    .filter(
        StudentReviewVote.vote == VoteType.correct,
        StudentReviewVote.valid == True
    ).group_by(StudentAssignedReview.student_id).all()
    
    for student_id, count in review_counts:
        if count >= 100:
            _award_badge_if_not_exists(db, student_id, "Peer Review Master")
        if count >= 50:
            _award_badge_if_not_exists(db, student_id, "Truth Seeker")
        if count >= 20:
            _award_badge_if_not_exists(db, student_id, "Insightful Reviewer")
        if count >= 10:
            _award_badge_if_not_exists(db, student_id, "Quality Checker")
        if count >= 5:
            _award_badge_if_not_exists(db, student_id, "Sharp Eye")

    # 4. Teacher's Tests & 5. Flawless Finish
    # Get all students in the current session
    students_in_session = db.query(StudentJoinGame.student_id).filter(
        StudentJoinGame.game_id == game_session_id
    ).distinct().all()
    student_ids = [s[0] for s in students_in_session]
    
    # For each student, calculate their "Perfect Sessions" count (Teacher's Tests)
    # and "Flawless Sessions" count
    for student_id in student_ids:
        perfect_sessions_count = _count_perfect_sessions(db, student_id)
        flawless_sessions_count = _count_flawless_sessions(db, student_id)
        
        # Award Teacher's Tests badges (1, 5, 10, 15, 20)
        if perfect_sessions_count >= 20:
            _award_badge_if_not_exists(db, student_id, "Teachers Champion", game_session_id)
        if perfect_sessions_count >= 15:
            _award_badge_if_not_exists(db, student_id, "Test Master", game_session_id)
        if perfect_sessions_count >= 10:
            _award_badge_if_not_exists(db, student_id, "Reliable Solver", game_session_id)
        if perfect_sessions_count >= 5:
            _award_badge_if_not_exists(db, student_id, "Consistent Performer", game_session_id)
        if perfect_sessions_count >= 1:
            _award_badge_if_not_exists(db, student_id, "First Pass", game_session_id)
        
        # Award Flawless Finish badges (1, 5, 10, 15, 20)
        if flawless_sessions_count >= 20:
            _award_badge_if_not_exists(db, student_id, "Untouchable", game_session_id)
        if flawless_sessions_count >= 15:
            _award_badge_if_not_exists(db, student_id, "Perfectionist", game_session_id)
        if flawless_sessions_count >= 10:
            _award_badge_if_not_exists(db, student_id, "Precision Player", game_session_id)
        if flawless_sessions_count >= 5:
            _award_badge_if_not_exists(db, student_id, "Clean Run", game_session_id)
        if flawless_sessions_count >= 1:
            _award_badge_if_not_exists(db, student_id, "Flawless Start", game_session_id)
    
    db.commit()
    return {"message": "Badges evaluated"}
