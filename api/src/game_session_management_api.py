from typing import List, Dict, Any, Annotated
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone

# Import ORM models
from models import (    
    Student,
    GameSession,
    Match,
    MatchesForGame, 
    StudentJoinGame
)


from database import get_db
from authentication.routes.auth_routes import require_teacher

# Import Pydantic models
from models import (
    StudentResponse, #individual student information.
    GameSessionStudentsResponse, #listing all students joined to a game session.
    MatchInfoResponse,  #match information within a game session.
    GameSessionFullDetailResponse,  #full game session details including students and matches.
    StudentMatchAssignment, #individual student-to-match assignment.
    GameSessionStartResponse   #response model for starting a game session.
)


# ============================================================================
# Helper Functions
# ============================================================================

def _distribute_students_to_matches(
    student_ids: List[int],
    match_ids: List[int]
) -> List[Dict[str, int]]:
    """
    Distributes students fairly across matches using round-robin algorithm.
    
    Args:
        student_ids: List of student IDs to assign
        match_ids: List of match IDs available for assignment
        
    Returns:
        List of dicts with student_id and assigned_match_id
    """
    if not match_ids:
        return []
    
    assignments = []
    for idx, student_id in enumerate(student_ids):
        match_index = idx % len(match_ids)
        assignments.append({
            "student_id": student_id,
            "assigned_match_id": match_ids[match_index]
        })
    
    return assignments


# ============================================================================
# Router
# ============================================================================

router = APIRouter(
    prefix="/api",
    tags=["game_session_management"]
)


# ============================================================================
# Endpoints
# ============================================================================

@router.get(
    "/game_session/{game_id}/details",
    response_model=GameSessionFullDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full game session details",
    description="Retrieves complete game session details including joined students, matches, and active status."
)
async def get_game_session_full_details(
    game_id: int, db: Session = Depends(get_db)
) -> GameSessionFullDetailResponse:
    """
    Get full details of a game session including:
    - Basic session info (name, start_date, is_active)
    - List of all joined students with their details
    - List of all matches in the session
    - Total student count
    """
    
    game_session = db.query(GameSession).filter(GameSession.game_id == game_id).first()

    if not game_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game session with id {game_id} not found"
        )
    
    # Get joined students
    joined_records = db.query(Student).join(StudentJoinGame, Student.student_id == StudentJoinGame.student_id).filter(StudentJoinGame.game_id == game_id).all()

    students = []
    for record in joined_records:
        student_data = {
            "student_id": record.student_id,
            "first_name": record.first_name,
            "last_name": record.last_name,
            "email": record.email
        }
        if student_data:
            students.append(StudentResponse(
                student_id=student_data["student_id"],  #should be student_data.student_id
                first_name=student_data["first_name"],  #should be student_data.first_name
                last_name=student_data["last_name"],  #should be student_data.last_name
                email=student_data["email"]  #should be student_data.email
            ))
    
    # Get matches for this game session
    match_ids = db.query(Match).join(MatchesForGame, Match.match_id == MatchesForGame.match_id).filter(MatchesForGame.game_id == game_id).all()
    matches = []

    joined_records = db.query(Student).join(StudentJoinGame, Student.student_id == StudentJoinGame.student_id).filter(StudentJoinGame.game_id == game_id).all()
    students = [
        StudentResponse(
            student_id=record.student_id,
            first_name=record.first_name,
            last_name=record.last_name,
            email=record.email
        ) for record in joined_records
    ]

    # Get matches for this game session
    
    match_ids = db.query(Match).join(MatchesForGame, Match.match_id == MatchesForGame.match_id).filter(MatchesForGame.game_id == game_id).all()
    matches = [
        MatchInfoResponse(
            match_id=m.match_id,
            title=m.title,
            difficulty_level=m.difficulty_level
        ) for m in match_ids
    ]
    
    return GameSessionFullDetailResponse(
        game_id=game_session.game_id,
        name=game_session.name,
        start_date=game_session.start_date,
        creator_id=game_session.creator_id,
        total_students=len(students),   
        students=students,
        matches=matches,
        duration_phase1=game_session.duration_phase1,
        duration_phase2=game_session.duration_phase2,
        actual_start_date=game_session.actual_start_date
    )


@router.get(
    "/game_session/{game_id}/students",
    response_model=GameSessionStudentsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all joined students for a game session",
    description="Retrieves the list of all students who have joined a specific game session."
)
async def get_game_session_students(
    game_id: int, db: Session = Depends(get_db)
) -> GameSessionStudentsResponse:
    """
    Get all students who have joined a specific game session.
    Returns student details including name and email.
    """
    
    game_session = db.query(GameSession).filter(GameSession.game_id == game_id).first()

    if not game_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game session with id {game_id} not found"
        )
    
    # Get joined students
    joined_records =db.query(Student).join(StudentJoinGame, Student.student_id == StudentJoinGame.student_id).filter(StudentJoinGame.game_id == game_id).all()
    
    students = [
        StudentResponse(
            student_id=s.student_id,
            first_name=s.first_name,
            last_name=s.last_name,
            email=s.email
        ) for s in joined_records
    ]
    
    return GameSessionStudentsResponse(
        game_id=game_id,
        total_students=len(students),
        students=students
    )


@router.get(
    "/game_session/{game_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Check if game session has started",
    description="Returns whether the game session has started (actual_start_date is set). Used by students polling in lobby."
)
async def check_game_session_status(
    game_id: int, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check if a game session has started.
    
    Returns:
    - has_started: boolean indicating if actual_start_date is set
    - actual_start_date: the actual start date if started, otherwise None
    """
    game_session = db.query(GameSession).filter(GameSession.game_id == game_id).first()

    if not game_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game session with id {game_id} not found"
        )
    
    return {
        "game_id": game_id,
        "has_started": game_session.actual_start_date is not None,
        "actual_start_date": game_session.actual_start_date
    }


@router.post(
    "/game_session/{game_id}/start",
    response_model=GameSessionStartResponse,
    status_code=status.HTTP_200_OK,
    summary="Start a game session",
    description="Starts a game session by setting actual_start_date and assigning students to matches fairly."
)
async def start_game_session(
    game_id: int,
    current_user: Annotated[dict, Depends(require_teacher)],
    db: Session = Depends(get_db)
) -> GameSessionStartResponse:
    """
    Start a game session:
    1. Validates the game session exists
    2. Checks if the session is not already active
    3. Sets actual_start_date to current time
    4. Assigns students to matches using fair distribution (round-robin)
    5. Returns the assignments
    """

    game_session = db.query(GameSession).filter(GameSession.game_id == game_id).first()

    if not game_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game session with id {game_id} not found"
        )
    
    # Check if already started
    if game_session.actual_start_date is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game session has already been started"
        )

    
    # Get joined students
    joined_records = db.query(StudentJoinGame).filter(StudentJoinGame.game_id == game_id).all()
    if not joined_records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start session: No students have joined"
        )
    
    # Get matches for this game session

    match_ids = db.query(MatchesForGame).filter(MatchesForGame.game_id == game_id).all()
    if not match_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start session: No matches configured for this session"
        )
    
    # Get student IDs
    student_ids = [record.student_id for record in joined_records]

    match_ids = [match.match_id for match in match_ids]
    
    # Distribute students to matches fairly
    raw_assignments = _distribute_students_to_matches(student_ids, match_ids)

    
    
    # Set actual start date (the time the teacher pressed the start button -> needed in order to calculate phase end times)
    game_session.actual_start_date = datetime.now(timezone.utc)

    for assignment in raw_assignments:
        for record in joined_records:
            if record.student_id == assignment["student_id"]:
                record.assigned_match_id = assignment["assigned_match_id"]
                break

    # Build response with full assignment details    
    # Fetch student and match details for response
    student_data = db.query(Student).filter(Student.student_id.in_(student_ids)).all()
    match_data = db.query(Match).filter(Match.match_id.in_(match_ids)).all()

    # Build lookup dictionaries for O(1) access
    student_lookup = {s.student_id: s for s in student_data}
    match_lookup = {m.match_id: m for m in match_data}

    # Build response with full assignment details
    assignments = []
    for assignment in raw_assignments:
        student = student_lookup.get(assignment["student_id"])
        match = match_lookup.get(assignment["assigned_match_id"])
        if student and match:
            assignments.append(StudentMatchAssignment(
                student_id=assignment["student_id"],  
                student_name=f"{student.first_name} {student.last_name}", 
                assigned_match_id=assignment["assigned_match_id"], 
                assigned_match_title=match.title
            ))

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start game session due to a database error: {str(e)}"
        )
    
    return GameSessionStartResponse(
        game_id=game_id,
        message="The game session has started.",
        total_students_assigned=len(assignments),
        assignments=assignments,
        duration_phase1=game_session.duration_phase1,
        duration_phase2=game_session.duration_phase2,
        actual_start_date=game_session.actual_start_date
    )