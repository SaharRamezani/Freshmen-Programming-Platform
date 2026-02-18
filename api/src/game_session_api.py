"""
Game sessions API Module

Provides endpoints for handling game sessions.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import re

# Import the database dependency and ORM models
from database import get_db
from models import Match, GameSession, MatchesForGame, Teacher, StudentJoinGame, StudentTest, StudentSolution, StudentSolutionTest, StudentAssignedReview, StudentReviewVote, StudentBadge

# ============================================================================
# Pydantic Models
# ============================================================================

class GameSessionCreate(BaseModel):
    match_id: List[int] = Field(..., description="List of the Match Ids to insert in the Game Session")
    name: str = Field(..., description="Name of the Game Session")
    creator_id: int = Field(..., description="Id of the Teacher that creates the Game Session")
    start_date: datetime = Field(..., description="Start date of the Game Session")
    duration_phase1: int = Field(..., description="Duration of the first phase")
    duration_phase2: int = Field(..., description="Duration of the second phase")

class GameSessionResponse(BaseModel):
    game_id: int = Field(..., description="Id of the newly added Game Session")
    
class GameSessionDetail(BaseModel):
    game_id: int = Field(..., description="Id of the Game Session")
    name: str = Field(..., description="Name of the Game Session")
    creator_id: int = Field(..., description="Id of the Teacher that created the Game Session")
    start_date: datetime = Field(..., description="Start date of the Game Session")
    match_id: List[int] = Field(..., description="List of Match Ids associated with the Game Session")
    duration_phase1: int = Field(..., description="Duration of the first phase")
    duration_phase2: int = Field(..., description="Duration of the sewcond phase")

class GameSessionUpdate(BaseModel):
    match_id: Optional[List[int]] = Field(
        None, description="List of the Match Ids to insert in the Game Session"
    )
    name: Optional[str] = Field(
        None, description="Name of the Game Session"
    )
    start_date: Optional[datetime] = Field(
        None, description="Start date of the Game Session"
    )
    duration_phase1: int = Field(..., description="Duration of the first phase")
    duration_phase2: int = Field(..., description="Duration of the sewcond phase")



# ============================================================================
# Helpers
# ============================================================================

def _generate_clone_name(original_name: str, creator_id: int, db: Session) -> str:
    copy_pattern = re.compile(r'^(.*) - Copy (\d+)$')
    match = copy_pattern.match(original_name)

    if match:
        base_name = match.group(1)
    else:
        base_name = original_name

    # get all session names for this creator
    existing_sessions = (
        db.query(GameSession.name)
        .filter(GameSession.creator_id == creator_id)
        .all()
    )

    # db.query(GameSession.name).all() returns list of tuples like [("Name",), ...]
    existing_names = [row[0] for row in existing_sessions]

    # find the highest copy number
    max_copy_num = 0
    escaped_base = re.escape(base_name)
    copy_check_pattern = re.compile(rf'^{escaped_base} - Copy (\d+)$')

    for name in existing_names:
        m = copy_check_pattern.match(name)
        if m:
            num = int(m.group(1))
            if num > max_copy_num:
                max_copy_num = num

    # if there are no existing " - Copy N" instances, return "base_name - Copy 1"
    return f"{base_name} - Copy {max_copy_num + 1}"

def _replace_game_session_matches(
    game_id: int,
    match_ids: List[int],
    db: Session
) -> None:
    """
    Replace all MatchesForGame links for a game session with the given match_ids.
    - First deletes all existing links for the game_id.
    - Then creates new links for each match_id.
    - Does NOT commit; caller is responsible for commit/rollback.
    For the deletion-only cases, pass an empty list for match_ids.
    """
    # delete existing links
    db.query(MatchesForGame).filter(
        MatchesForGame.game_id == game_id
    ).delete(synchronize_session=False)

    # add new links
    for mid in match_ids:
        link = MatchesForGame(
            game_id=game_id,
            match_id=mid
        )
        db.add(link)


# ============================================================================
# Router
# ============================================================================

router = APIRouter(
    prefix="/api",
    tags=["game_session"]
)

# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/game_session",
    response_model=GameSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new game session",
    description="Allows a teacher to create a new game session based on a set of match settings."
)
async def create_game_session(
    game_session_data: GameSessionCreate,
    db: Session = Depends(get_db)
    ) -> GameSessionResponse:

    if len(game_session_data.match_id) <= 0:

        print("Error: at least one match setting is required")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request error, at least one match setting is required"
        )


    teacher = db.query(Teacher).filter(Teacher.teacher_id == game_session_data.creator_id).first()
    print(teacher)
    print(game_session_data.creator_id)
    if not teacher:
        print("Error: teacher not found")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request error"
        )
    
    matches = db.query(Match).filter(Match.match_id.in_(game_session_data.match_id)).all()
    
    if len(matches) != len(game_session_data.match_id):
        print("Error: match not found")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request error"
        )
    print("game session data duration phase1: ", game_session_data.duration_phase1)
    new_game_session = GameSession(creator_id=game_session_data.creator_id, name=game_session_data.name, start_date=game_session_data.start_date, duration_phase1=game_session_data.duration_phase1, duration_phase2=game_session_data.duration_phase2) 
    db.add(new_game_session)
    
    db.flush() 

    for match in matches:
        match_link = MatchesForGame(
            game_id=new_game_session.game_id,
            match_id=match.match_id
        )
        db.add(match_link)

    try:
        db.commit()
        db.refresh(new_game_session)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error"
        )

    return GameSessionResponse(game_id=new_game_session.game_id)

@router.get(
    "/game_session/by_creator/{creator_id}",
    response_model=List[GameSessionDetail],
    status_code=status.HTTP_200_OK,
    summary="List game sessions by creator",
    description="Retrieve all game sessions created by a specific creator."
)
async def list_game_sessions_by_creator(
    creator_id: int,
    db: Session = Depends(get_db)
) -> List[GameSessionDetail]:
    """
    List all game sessions created by a specific creator (teacher).
    """
    
    # check that the creator (teacher) exists
    teacher = db.query(Teacher).filter(Teacher.teacher_id == creator_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Creator with id {creator_id} does not exist"
        )
        
    # retrieve game sessions created by the specified creator
    game_sessions = db.query(GameSession).filter(GameSession.creator_id == creator_id).all()
    
    if not game_sessions:
        # return empty list if no game sessions found
        return []
    
    # collect all game ids
    game_ids = [gs.game_id for gs in game_sessions]
    
    # get all match links for these game sessions
    match_links = db.query(MatchesForGame).filter(MatchesForGame.game_id.in_(game_ids)).all()
    
    # build a mapping from game_id to list of match_ids
    match_map = {gid: [] for gid in game_ids}
    for link in match_links:
        match_map[link.game_id].append(link.match_id)
        
    # build the response list
    response: List[GameSessionDetail] = []

    for gs in game_sessions:
        print(gs)
        response.append(
            GameSessionDetail(
                game_id=gs.game_id,
                name=gs.name,
                creator_id=gs.creator_id,
                start_date=gs.start_date,
                match_id=match_map.get(gs.game_id, []),
                duration_phase1 = gs.duration_phase1,
                duration_phase2 = gs.duration_phase2
            )
        )
        
    return response

@router.delete(
    "/game_session/{game_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a game session",
    description="Deletes a game session and its associated match links."
)
async def delete_game_session(
    game_id: int,
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a game session and its associated match links.
    """
    
    # check that the game session exists
    game_session = db.query(GameSession).filter(GameSession.game_id == game_id).first()
    
    if not game_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game session with id {game_id} not found"
        )
        
    try:
        # Get all matches_for_game IDs for this game session
        match_for_game_ids = [
            mfg.match_for_game_id for mfg in 
            db.query(MatchesForGame).filter(MatchesForGame.game_id == game_id).all()
        ]
        
        if match_for_game_ids:
            # Get all solution IDs for these matches
            solution_ids = [
                s.solution_id for s in 
                db.query(StudentSolution).filter(StudentSolution.match_for_game_id.in_(match_for_game_ids)).all()
            ]
            
            # Get all student test IDs for these matches
            student_test_ids = [
                t.test_id for t in 
                db.query(StudentTest).filter(StudentTest.match_for_game_id.in_(match_for_game_ids)).all()
            ]
            
            # Delete review votes first (references assigned reviews)
            if solution_ids:
                # Get assigned review IDs that reference these solutions
                assigned_review_ids = [
                    r.student_assigned_review_id for r in
                    db.query(StudentAssignedReview).filter(StudentAssignedReview.assigned_solution_id.in_(solution_ids)).all()
                ]
                
                if assigned_review_ids:
                    # Delete review votes
                    db.query(StudentReviewVote).filter(
                        StudentReviewVote.student_assigned_review_id.in_(assigned_review_ids)
                    ).delete(synchronize_session=False)
                
                # Delete assigned reviews
                db.query(StudentAssignedReview).filter(
                    StudentAssignedReview.assigned_solution_id.in_(solution_ids)
                ).delete(synchronize_session=False)
            
            # Delete student_solution_tests (references both solutions and student_tests)
            if solution_ids:
                db.query(StudentSolutionTest).filter(
                    StudentSolutionTest.solution_id.in_(solution_ids)
                ).delete(synchronize_session=False)
            
            # Delete student solutions
            db.query(StudentSolution).filter(
                StudentSolution.match_for_game_id.in_(match_for_game_ids)
            ).delete(synchronize_session=False)
            
            # Delete student tests
            db.query(StudentTest).filter(
                StudentTest.match_for_game_id.in_(match_for_game_ids)
            ).delete(synchronize_session=False)
        
        # Delete student join records
        db.query(StudentJoinGame).filter(StudentJoinGame.game_id == game_id).delete(synchronize_session=False)
        
        # Delete matches_for_game records
        db.query(MatchesForGame).filter(MatchesForGame.game_id == game_id).delete(synchronize_session=False)
        
        # Delete student badges earned in this game session
        db.query(StudentBadge).filter(StudentBadge.game_session_id == game_id).delete(synchronize_session=False)
        
        # Delete the game session
        db.delete(game_session)
        db.commit()
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error while deleting game session: {str(e)}"
        )
        
    
@router.post(
    "/game_session/{game_id}/clone",
    response_model=GameSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone a game session",
    description="Creates a clone of an existing game session with the same matches."
)
async def clone_game_session(
    game_id: int,
    db: Session = Depends(get_db)
) -> GameSessionResponse:
    """
    Clone an existing game session along with its associated matches.
    """
    
    # find original game session
    original_game_session = db.query(GameSession).filter(GameSession.game_id == game_id).first()
    
    if not original_game_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game session with id {game_id} not found"
        )
        
    # get all matches linked to the original game session
    original_matches_links = db.query(MatchesForGame).filter(MatchesForGame.game_id == game_id).all()
    
    # create cloned game session
    cloned_name = _generate_clone_name(original_game_session.name, original_game_session.creator_id, db)
    new_game_session = GameSession(creator_id=original_game_session.creator_id, name=cloned_name, start_date=original_game_session.start_date, duration_phase1 = original_game_session.duration_phase1, duration_phase2=original_game_session.duration_phase2)
    db.add(new_game_session)
    db.flush()
    
    # clone all match links to the new game session
    for link in original_matches_links:
        new_link = MatchesForGame(
            game_id=new_game_session.game_id,
            match_id=link.match_id
        )
        db.add(new_link)
        
    try:
        db.commit()
        db.refresh(new_game_session)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error while cloning game session"
        )
        
    return GameSessionResponse(game_id=new_game_session.game_id)
    
@router.put(
    "/game_session/{game_id}",
    status_code=status.HTTP_200_OK,
    response_model=GameSessionDetail,
    summary="Update a game session",
    description="Updates the details of an existing game session."
)
async def update_game_session(
    game_id: int,
    game_session_data: GameSessionUpdate,
    db: Session = Depends(get_db)
) -> GameSessionDetail:
    """
    Update the details of an existing game session.
    """
    # check that the game session exists
    game_session = db.query(GameSession).filter(GameSession.game_id == game_id).first()
    if not game_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game session with id {game_id} not found"
        )

    # update simple fields if provided
    if game_session_data.name is not None:
        if not game_session_data.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game session name cannot be empty"
            )
        game_session.name = game_session_data.name

    if game_session_data.start_date is not None:
        if game_session_data.start_date < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be in the past"
            )
        game_session.start_date = game_session_data.start_date

    # update matches only if match_id is provided
    if game_session_data.match_id is not None:
        if len(game_session_data.match_id) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request error, at least one match setting is required"
            )

        # validate matches exist
        matches = db.query(Match).filter(
            Match.match_id.in_(game_session_data.match_id)
        ).all()

        if len(matches) != len(game_session_data.match_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request error, one or more match IDs do not exist"
            )

        # replace match links
        try:
            _replace_game_session_matches(
                game_id=game_id,
                match_ids=[m.match_id for m in matches],
                db=db,
            )

        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server error while updating game session matches"
            )
    game_session.duration_phase1 = game_session_data.duration_phase1
    game_session.duration_phase2 = game_session_data.duration_phase2
    # commit everything 
    try:
        db.commit()
        db.refresh(game_session)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error while updating game session"
        )

    # get current match ids for response
    current_links = db.query(MatchesForGame).filter(
        MatchesForGame.game_id == game_id
    ).all()
    match_ids = [link.match_id for link in current_links]

    return GameSessionDetail(
        game_id=game_session.game_id,
        name=game_session.name,
        creator_id=game_session.creator_id,
        start_date=game_session.start_date,
        match_id=match_ids,
        duration_phase1 = game_session.duration_phase1,
        duration_phase2 = game_session.duration_phase2,
    )
   
@router.get(
    "/game_session/{game_id}",
    response_model=GameSessionDetail,
    status_code=status.HTTP_200_OK,
    summary="Get game session details from ID",
    description="Retrieve the details and match IDs of a game session from its ID."
)
async def get_game_session_from_id(
    game_id: int,
    db: Session = Depends(get_db)
) -> GameSessionDetail:

    """
    Get the details of a game session by its ID.
    """
    
    # find the game session
    game_session = db.query(GameSession).filter(GameSession.game_id == game_id).first()
    if not game_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game session with id {game_id} not found"
        )
        
    # get all match links for this game session
    match_links = db.query(MatchesForGame).filter(MatchesForGame.game_id == game_id).all()
    match_ids = [link.match_id for link in match_links]
    
    return GameSessionDetail(
        game_id=game_session.game_id,
        name=game_session.name,
        creator_id=game_session.creator_id,
        start_date=game_session.start_date,
        match_id=match_ids,
        duration_phase1 = game_session.duration_phase1,
        duration_phase2 = game_session.duration_phase2,
    )